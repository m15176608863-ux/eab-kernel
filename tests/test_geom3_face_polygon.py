"""面多边形内点判定统一为 `geom3.point_in_face_polygon`——审查 C6（扇形三角化）≡ C7（半平面核）。

两个缺陷是同一件事：面允许非凸（geom3 模块文档），而五处"点在面内"的实现只对凸面正确——
  covers3._point_inside_face、geom3._point_face_distance     用半平面核（kernel ≠ interior）；
  geom3._point_on_face、segment_crosses_face、射线奇偶         从 f[0] 扇形三角化（三角溢出多边形）。
后果：L 块臂上的 VF 盖 in_extent=False 被丢、`brute_feature_distance` 高估；细杆穿过 L 的凹口
被判相交；凹口里落在底面平面上的点被判"边界"；`merge_coplanar` 归并出的十边形侧面前方探针无盖。

**纪律 A（写明共用与风险）**：修复后 covers3 的 in_extent 与 geom3 的暴力谓词（G0 的 oracle）
**共用同一个** `point_in_face_polygon`。它若错，盖路径与 oracle 会一起错而 G0 看不见。
所以本文件对它本身用**独立 oracle**：
  · 轴对齐矩形并集（L / U / E 形）的闭式成员判定；
  · 随机星形多边形的**极坐标射线**判定（以星心出发的射线与唯一一条边求交，比较半径）；
两者都在测试里用纯算术写成，不调 geom3 任何原语；多边形再经随机旋转、平移、缩放嵌入三维。
其余行为门（点在体内、相交、距离、盖）的真值也全是闭式：L 棱柱 = 两个轴对齐方块之并，
距离 = 轴对齐方块间距的最小值，骨形块侧面十边形 = 分段线性上下边界之间的区域。

纪律 B：分界点（棱上、顶点上、反射顶点上、tol 内外各一侧）、一般位置（随机旋转、非对称
星形多边形）、尺度 ×1e-3 / ×1 / ×1e3。
"""

import math
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from osteomorphic import osteomorphic_block  # noqa: E402

from eab.kernel3d import geom3  # noqa: E402
from eab.kernel3d.covers3 import enumerate_covers3, vf_cover  # noqa: E402
from eab.kernel3d.geom3 import (Polyhedron, brute_feature_distance, merge_coplanar,  # noqa: E402
                                point_in_polyhedron, polyhedra_overlap, segment_crosses_face)

SCALES = [1e-3, 1.0, 1e3]


# ================================================================ 独立的几何脚手架（纯算术）

def _rotation(seed: int):
    """seed=0 → 单位阵；否则由随机单位四元数给出一般位置的旋转。"""
    if seed == 0:
        return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    rng = random.Random(1000 + seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


class Frame:
    """局部坐标 → 世界坐标：w = o + s·R·p。"""

    def __init__(self, seed: int, scale: float):
        self.R = _rotation(seed)
        self.s = scale
        rng = random.Random(2000 + seed)
        self.o = tuple(scale * rng.uniform(-3.0, 3.0) for _ in range(3)) if seed else (0.0, 0.0, 0.0)

    def __call__(self, p):
        R, s, o = self.R, self.s, self.o
        return tuple(o[i] + s * (R[i][0] * p[0] + R[i][1] * p[1] + R[i][2] * p[2]) for i in range(3))

    def poly(self, verts, faces):
        return Polyhedron([self(p) for p in verts], [tuple(f) for f in faces])


FRAMES = [(seed, s) for seed in (0, 1, 2) for s in SCALES]


def _shoelace(ring):
    return 0.5 * sum(ring[i][0] * ring[(i + 1) % len(ring)][1] - ring[(i + 1) % len(ring)][0] * ring[i][1]
                     for i in range(len(ring)))


def _in_rects(q, rects) -> bool:
    return any(x0 < q[0] < x1 and y0 < q[1] < y1 for (x0, x1, y0, y1) in rects)


# 轴对齐矩形并集：环（CCW）+ 构成它的矩形（闭式 oracle）
SHAPES = {
    "L": ([(0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3)],
          [(0, 3, 0, 1), (0, 1, 0, 3)]),
    "U": ([(0, 0), (3, 0), (3, 3), (2, 3), (2, 1), (1, 1), (1, 3), (0, 3)],
          [(0, 3, 0, 1), (0, 1, 0, 3), (2, 3, 0, 3)]),
    "E": ([(0, 0), (4, 0), (4, 1), (1, 1), (1, 2), (3, 2), (3, 3), (1, 3), (1, 4), (4, 4), (4, 5), (0, 5)],
          [(0, 1, 0, 5), (0, 4, 0, 1), (0, 3, 2, 3), (0, 4, 4, 5)]),
}


def _face_poly(ring2d, fr: Frame) -> Polyhedron:
    return fr.poly([(float(x), float(y), 0.0) for x, y in ring2d], [tuple(range(len(ring2d)))])


# ================================================================ point_in_face_polygon 本身

@pytest.mark.parametrize("seed,scale", FRAMES)
@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_point_in_face_polygon_matches_rect_union(shape, seed, scale):
    from eab.kernel3d.geom3 import point_in_face_polygon
    ring, rects = SHAPES[shape]
    assert _shoelace(ring) > 0                                  # 前提：环 CCW
    fr = Frame(seed, scale)
    F = _face_poly(ring, fr)
    tol = 1e-9 * scale
    xs = [-0.63 + 0.25 * k for k in range(int(4 * (max(p[0] for p in ring) + 1.3)))]
    ys = [-0.63 + 0.25 * k for k in range(int(4 * (max(p[1] for p in ring) + 1.3)))]
    n_in = n_out = 0
    for x in xs:
        for y in ys:
            want = _in_rects((x, y), rects)
            got = point_in_face_polygon(fr((x, y, 0.0)), F, 0, tol)
            assert got == want, (shape, x, y, want)
            n_in += want
            n_out += not want
    assert n_in > 10 and n_out > 10


@pytest.mark.parametrize("seed,scale", FRAMES)
@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_point_in_face_polygon_boundary_band_is_tol(shape, seed, scale):
    """边界语义：到任一棱段距离 ≤ tol 即"在面内"（含反射顶点）；外推 3·tol 即不在。"""
    from eab.kernel3d.geom3 import face_polygon_locate, point_in_face_polygon
    ring, _ = SHAPES[shape]
    fr = Frame(seed, scale)
    F = _face_poly(ring, fr)
    tol = 1e-9 * scale
    k = len(ring)
    for i in range(k):
        (ax, ay), (bx, by) = ring[i], ring[(i + 1) % k]
        L = math.hypot(bx - ax, by - ay)
        ox, oy = (by - ay) / L, -(bx - ax) / L                   # CCW 环的外法向（右侧）
        for t in (0.0, 0.3, 0.5):
            px, py = ax + t * (bx - ax), ay + t * (by - ay)
            assert point_in_face_polygon(fr((px, py, 0.0)), F, 0, tol), (shape, i, t)
            assert face_polygon_locate(fr((px, py, 0.0)), F, 0, tol) == 0
            if t > 0.0:
                q_in = fr((px + 0.5 * tol / scale * ox, py + 0.5 * tol / scale * oy, 0.0))
                q_out = fr((px + 3.0 * tol / scale * ox, py + 3.0 * tol / scale * oy, 0.0))
                q_deep = fr((px - 3.0 * tol / scale * ox, py - 3.0 * tol / scale * oy, 0.0))
                assert point_in_face_polygon(q_in, F, 0, tol)
                assert not point_in_face_polygon(q_out, F, 0, tol), (shape, i, t)
                assert face_polygon_locate(q_deep, F, 0, tol) == 1, (shape, i, t)


def _star(seed: int, n: int):
    rng = random.Random(seed)
    th = sorted((2 * math.pi * (i + rng.uniform(-0.35, 0.35)) / n) % (2 * math.pi) for i in range(n))
    r = [rng.uniform(0.25, 1.0) for _ in range(n)]
    return [(r[i] * math.cos(th[i]), r[i] * math.sin(th[i])) for i in range(n)], th


def _star_inside(q, ring, th):
    """独立 oracle：星心在核内，射线 t·(cosφ, sinφ) 与唯一一条边 P_i P_{i+1} 相交于半径 t*。"""
    n = len(ring)
    phi = math.atan2(q[1], q[0]) % (2 * math.pi)
    ths = th + [th[0] + 2 * math.pi]
    if phi < th[0]:
        phi += 2 * math.pi
    i = max(j for j in range(n) if ths[j] <= phi)
    P, Q = ring[i % n], ring[(i + 1) % n]
    d = (math.cos(phi), math.sin(phi))
    e = (Q[0] - P[0], Q[1] - P[1])
    tstar = (P[0] * e[1] - P[1] * e[0]) / (d[0] * e[1] - d[1] * e[0])
    rho = math.hypot(q[0], q[1])
    return rho < tstar, abs(rho - tstar)


@pytest.mark.parametrize("seed,scale", FRAMES)
@pytest.mark.parametrize("n", [7, 11])
def test_point_in_face_polygon_matches_star_polar_oracle(n, seed, scale):
    from eab.kernel3d.geom3 import point_in_face_polygon
    ring, th = _star(seed * 31 + n, n)
    assert _shoelace(ring) > 0
    fr = Frame(seed, scale)
    F = fr.poly([(x, y, 0.0) for x, y in ring], [tuple(range(n))])
    rng = random.Random(seed + 77)
    n_in = n_out = 0
    for _ in range(400):
        q = (rng.uniform(-1.1, 1.1), rng.uniform(-1.1, 1.1))
        want, margin = _star_inside(q, ring, th)
        if margin < 1e-6:
            continue
        assert point_in_face_polygon(fr((q[0], q[1], 0.0)), F, 0, 1e-9 * scale) == want, (q, want)
        n_in += want
        n_out += not want
    assert n_in > 40 and n_out > 40


def test_all_five_call_sites_route_through_the_single_helper(monkeypatch):
    """纪律 C："唯一实现、五处全部换用"要有门：把 geom3.face_polygon_locate 换成恒答"外部"，
    五处（vf/fv 的 in_extent、_point_face_distance、边界判定、射线奇偶、segment_crosses_face）必须全部跟着变。
    旧的私有实现不得残留。"""
    import eab.kernel3d.covers3 as cv
    assert not hasattr(cv, "_point_inside_face")
    assert not hasattr(geom3, "_point_on_face") and not hasattr(geom3, "_tri_ray_hit")
    B = geom3.box(half=(1.0, 1.0, 1.0))                                     # 顶面 z = 1
    A = geom3.box(center=(0.2, 0.1, 1.5), half=(0.3, 0.3, 0.3))            # 底角投影落在 B 顶面内
    top = 1
    upper = geom3.box(center=(0.0, 0.0, 3.0), half=(1.0, 1.0, 1.0))        # 底面 z = 2，FV 的 A
    bottom = 0

    def fv_in_extent():
        return [c.in_extent for c in (cv.fv_cover(upper, bottom, A, ib, 1e-9) for ib in range(4, 8))
                if c is not None]

    assert vf_cover(A, 0, B, top, 1e-9).in_extent                          # 基线
    assert fv_in_extent() == [True] * 4
    assert geom3._point_face_distance((0.2, 0.1, 1.5), B, top) == pytest.approx(0.5)
    assert point_in_polyhedron((0.2, 0.1, 1.0), B, 1e-9) == 0
    assert point_in_polyhedron((0.2, 0.1, 0.3), B, 1e-9) == 1
    assert segment_crosses_face((0.2, 0.1, 0.5), (0.2, 0.1, 1.5), B, top, 0.0)
    monkeypatch.setattr(geom3, "face_polygon_locate", lambda x, P, fi, tol=0.0: -1)
    assert not vf_cover(A, 0, B, top, 1e-9).in_extent
    assert fv_in_extent() == [False] * 4
    assert geom3._point_face_distance((0.2, 0.1, 1.5), B, top) is None
    assert point_in_polyhedron((0.2, 0.1, 1.0), B, 1e-9) != 0                # 边界判定走它
    assert point_in_polyhedron((0.2, 0.1, 0.3), B, 1e-9) == -1               # 射线奇偶走它（零交点）
    assert not segment_crosses_face((0.2, 0.1, 0.5), (0.2, 0.1, 1.5), B, top, 0.0)


# ================================================================ L 棱柱：点在体内 / 线段穿面 / 相交

L_BASE = [(0.0, 0.0), (3.0, 0.0), (3.0, 1.0), (1.0, 1.0), (1.0, 3.0), (0.0, 3.0)]
L_RECTS = [(0, 3, 0, 1), (0, 1, 0, 3)]


def _prism(base, h=1.0):
    n = len(base)
    v = [(x, y, 0.0) for x, y in base] + [(x, y, h) for x, y in base]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    return v, faces


def _box_local(c, h):
    (cx, cy, cz), (hx, hy, hz) = c, h
    v = [(cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz), (cx + hx, cy + hy, cz - hz),
         (cx - hx, cy + hy, cz - hz), (cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz),
         (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return v, f


def test_point_on_face_plane_in_concave_notch_is_outside():
    """审查原例：(1.5, 1.4, 0) 在底面平面上、落在 L 的凹口里 → 体外，不是"边界"。"""
    L = Polyhedron(*_prism(L_BASE))
    for tol in (1e-9, 0.0):
        assert point_in_polyhedron((1.5, 1.4, 0.0), L, tol) == -1, tol
        assert point_in_polyhedron((1.5, 1.4, 1.0), L, tol) == -1, tol
    assert point_in_polyhedron((2.0, 0.5, 0.0), L, 1e-9) == 0      # 正对照：臂上的底面点
    assert point_in_polyhedron((0.5, 2.5, 1.0), L, 1e-9) == 0
    assert point_in_polyhedron((1.0, 1.0, 0.0), L, 1e-9) == 0      # 反射顶点


@pytest.mark.parametrize("seed,scale", FRAMES)
def test_point_in_polyhedron_matches_closed_form_L_prism(seed, scale):
    fr = Frame(seed, scale)
    L = fr.poly(*_prism(L_BASE))
    tol = 1e-9 * scale
    grid = [-0.63 + 0.5 * k for k in range(9)]
    for x in grid:
        for y in grid:
            inside2d = _in_rects((x, y), L_RECTS)
            for z in (-0.38, 0.37, 0.62, 1.37):
                want = 1 if (inside2d and 0.0 < z < 1.0) else -1
                assert point_in_polyhedron(fr((x, y, z)), L, tol) == want, (x, y, z)
            for z in (0.0, 1.0):                               # 恰在顶/底面平面上
                want = 0 if inside2d else -1
                assert point_in_polyhedron(fr((x, y, z)), L, tol) == want, (x, y, z)


@pytest.mark.parametrize("seed,scale", FRAMES)
def test_rod_through_concave_notch_is_separated(seed, scale):
    """审查原例：细杆竖穿 L 的凹口（x, y > 1），与 L 分离；扇形三角把它判成相交。"""
    fr = Frame(seed, scale)
    L = fr.poly(*_prism(L_BASE))
    rod = fr.poly(*_box_local((1.5, 1.4, 0.5), (0.05, 0.05, 1.0)))
    arm = fr.poly(*_box_local((2.0, 0.5, 0.5), (0.05, 0.05, 1.0)))   # 正对照：穿过臂
    tol = 1e-12 * scale
    assert polyhedra_overlap(rod, L, tol) == -1
    assert polyhedra_overlap(L, rod, tol) == -1
    assert polyhedra_overlap(arm, L, tol) == 1
    assert polyhedra_overlap(L, arm, tol) == 1


def test_segment_crosses_face_respects_concavity():
    L = Polyhedron(*_prism(L_BASE))
    bottom = 0
    assert not segment_crosses_face((1.5, 1.4, -0.5), (1.5, 1.4, 0.5), L, bottom, 0.0)
    assert segment_crosses_face((2.0, 0.5, -0.5), (2.0, 0.5, 0.5), L, bottom, 0.0)
    assert segment_crosses_face((0.5, 2.5, -0.5), (0.5, 2.5, 0.5), L, bottom, 0.0)
    # 恰好穿过棱（不是面内部）→ False
    assert not segment_crosses_face((2.0, 1.0, -0.5), (2.0, 1.0, 0.5), L, bottom, 1e-12)


# ================================================================ 距离 oracle 与盖

def _box_box_distance(lo1, hi1, lo2, hi2):
    return math.sqrt(sum(max(0.0, lo2[i] - hi1[i], lo1[i] - hi2[i]) ** 2 for i in range(3)))


def _dist_box_to_L(c, h):
    lo, hi = tuple(c[i] - h[i] for i in range(3)), tuple(c[i] + h[i] for i in range(3))
    return min(_box_box_distance(lo, hi, (0, 0, 0), (3, 1, 1)),
               _box_box_distance(lo, hi, (0, 0, 0), (1, 3, 1)))


def test_brute_distance_and_vf_cover_over_the_L_arm():
    """审查原例：小方块悬在 L 臂上方 0.5。半平面核把臂判成"面外"→ VF 盖丢、距离报 0.673。"""
    L = Polyhedron(*_prism(L_BASE))
    S = Polyhedron(*_box_local((2.5, 0.5, 1.55), (0.05, 0.05, 0.05)))
    assert abs(brute_feature_distance(S, L) - 0.5) < 1e-12
    top = 1
    for ia in range(4):                                         # S 的四个底角
        c = vf_cover(S, ia, L, top, 1e-9)
        assert c is not None and abs(c.gap - 0.5) < 1e-12
        assert c.in_extent, ia
    covs = [c for c in enumerate_covers3(S, L, window=float("inf"), tol=1e-9) if c.in_extent]
    assert sum(1 for c in covs if c.kind == "VF") >= 4
    assert abs(min(geom3.norm(geom3.sub(c.point_a, c.point_b)) for c in covs) - 0.5) < 1e-12


@pytest.mark.parametrize("seed,scale", FRAMES)
def test_brute_distance_matches_closed_form_around_L(seed, scale):
    fr = Frame(seed, scale)
    L = fr.poly(*_prism(L_BASE))
    rng = random.Random(seed * 7 + 3)
    n = 0
    while n < 25:
        c = (rng.uniform(-1.0, 4.0), rng.uniform(-1.0, 4.0), rng.uniform(-1.0, 2.0))
        h = (rng.uniform(0.02, 0.2), rng.uniform(0.02, 0.2), rng.uniform(0.02, 0.2))
        truth = _dist_box_to_L(c, h)
        if truth < 0.05:
            continue                                           # 只测分离的
        S = fr.poly(*_box_local(c, h))
        got = brute_feature_distance(S, L)
        assert abs(got - truth * scale) <= 1e-9 * scale, (c, h, got / scale, truth)
        n += 1


# ================================================================ merge_coplanar 归并出的凹十边形侧面

def _zb(x: float) -> float:
    """osteomorphic_block(nx=4, ny=2, amp=0.25) 的底边界（x∈[−1,1] 分段线性）；顶边界 = zb + 1。"""
    xs = [-1.0, -0.5, 0.0, 0.5, 1.0]
    zs = [-0.5, -0.25, -0.5, -0.75, -0.5]
    for i in range(4):
        if xs[i] <= x <= xs[i + 1]:
            return zs[i] + (zs[i + 1] - zs[i]) * (x - xs[i]) / (xs[i + 1] - xs[i])
    raise ValueError(x)


def _footprint_inside_side_face(x0, z0, hp, margin=1e-6):
    if x0 - hp <= -1.0 + margin or x0 + hp >= 1.0 - margin:
        return False
    xs = [x0 - hp, x0 + hp] + [b for b in (-0.5, 0.0, 0.5) if x0 - hp < b < x0 + hp]
    return all(_zb(x) + margin < z0 - hp and z0 + hp < _zb(x) + 1.0 - margin for x in xs)


def test_probe_in_front_of_merged_concave_side_face_has_a_face_cover():
    """审查原例：骨形块归并后 y=−0.5 侧面是凹十边形；探针在它正前方 0.3。
    旧实现：盖路径 0 个盖（距离 inf），oracle 报 0.3384。真值 0.3（闭式）。"""
    mer = merge_coplanar(osteomorphic_block(nx=4, ny=2, amp=0.25))
    assert max(len(f) for f in mer.faces) == 10
    S2 = Polyhedron(*_box_local((0.0, -0.85, -0.25), (0.05, 0.05, 0.05)))
    assert abs(brute_feature_distance(S2, mer) - 0.3) < 1e-12
    covs = [c for c in enumerate_covers3(S2, mer, window=float("inf"), tol=1e-9) if c.in_extent]
    vf = [c for c in covs if c.kind == "VF" and abs(geom3.norm(geom3.sub(c.point_a, c.point_b)) - 0.3) < 1e-12]
    assert len(vf) == 4, [(c.kind, c.label()) for c in covs]


@pytest.mark.parametrize("merged", [False, True])
@pytest.mark.parametrize("side", [-1, 1])
def test_probes_in_front_of_osteomorphic_side_faces(side, merged):
    """在 y = ±0.5 侧面正前方随机放探针（足迹落在十边形内，由分段线性边界闭式判定），
    盖路径的最小见证距离与 brute_feature_distance 都必须等于闭式真值 g。"""
    P = osteomorphic_block(nx=4, ny=2, amp=0.25)
    if merged:
        P = merge_coplanar(P)
    rng = random.Random(10 * side + merged)
    n = 0
    while n < 12:
        hp, g = rng.uniform(0.02, 0.08), rng.uniform(0.05, 0.4)
        x0, z0 = rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)
        if not _footprint_inside_side_face(x0, z0, hp):
            continue
        S = Polyhedron(*_box_local((x0, side * (0.5 + g + hp), z0), (hp, hp, hp)))
        covs = [c for c in enumerate_covers3(S, P, window=float("inf"), tol=1e-9) if c.in_extent]
        got = min((geom3.norm(geom3.sub(c.point_a, c.point_b)) for c in covs), default=float("inf"))
        assert abs(got - g) < 1e-9, (x0, z0, hp, g, got)
        assert abs(brute_feature_distance(S, P) - g) < 1e-9
        assert any(c.kind == "VF" for c in covs)
        n += 1
