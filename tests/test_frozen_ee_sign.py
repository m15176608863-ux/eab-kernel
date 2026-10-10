"""冻结路径的 EE 朝向与近平行 EE 的棱内判定（G6 第五轮，2026-10-10）。

两条缺陷都是"判据要加被测量自己的噪声"一族：
  · frozen_ee_sign 判候选法向落不落在 B 棱弧里只用调用方 tol，没加候选 unit(t_B × t_A) 自身的方向噪声
    (n_A + n_B)/sinθ——而 covers3.ee_cover 与 facet_normal3 都加了（同一个量两把尺）。偏航的叠放方块一经一般旋转并
    平移到工程坐标，朝向判反，margin_gap_from_frozen_cover 对 body_distance 自己选出的 EE 标签给出 −d。
  · ee_cover 的棱内判定（交点参数 s、t 落在 [0, 1] 带内）对近平行棱病态：交点位置的噪声是 rfl/sinθ（位置噪声）
    + |g|·(n_A + n_B)/sin²θ（方向噪声经间隙杠杆），原式只有 sinθ ≈ 1 时的那一项。偏航 1e-5 的叠放方块
    （棱长 1e-3、坐标 1e5）交点从 s = 0.5 漂到 3.29，8 条真并列的 EE 丢 4 条。
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.kernel3d.covers3 import ee_cover, facet_normal3  # noqa: E402
from eab.kernel3d.frozen import ee_normal_generic, frozen_ee_sign  # noqa: E402
from eab.kernel3d.geom3 import Polyhedron, box, dot  # noqa: E402
from eab.margin import body_distance, inflated_membership, margin_gap_from_frozen_cover, OUTSIDE  # noqa: E402


def _rot_z(th):
    c, s = math.cos(th), math.sin(th)
    return ((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0))


def _rot3(seed):
    rng = random.Random(seed)
    q = [rng.gauss(0, 1) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def _app(R, v):
    return tuple(R[i][0] * v[0] + R[i][1] * v[1] + R[i][2] * v[2] for i in range(3))


def _xf(P, R, t, s=1.0):
    return Polyhedron([tuple(a + b for a, b in zip(_app(R, tuple(s * c for c in p)), t)) for p in P.verts], list(P.faces))


def _stack(yaw, gap, seed, t, s=1.0):
    """偏航 yaw 的单位方块叠在单位方块上方 gap，整对做种子 seed 的一般旋转、按 s 缩放、平移到 |t|（方向 (0.6, −0.48, 0.64)）。"""
    tv = (t * 0.6, -t * 0.48, t * 0.64)
    top = _xf(box(center=(0.0, 0.0, 1.0 + gap), half=(0.5, 0.5, 0.5)), _rot_z(yaw), (0.0, 0.0, 0.0))
    A = _xf(top, _rot3(seed), tv, s)
    B = _xf(box(half=(0.5, 0.5, 0.5)), _rot3(seed), tv, s)
    return A, B


GRID = [(yaw, gap, seed, t) for yaw in (1e-4, 1e-5) for gap in (1e-3, 1e-6) for seed in (4, 6, 9) for t in (0.0, 1e3, 1e5, 1e6)]


@pytest.mark.parametrize("yaw,gap,seed,t", GRID)
def test_frozen_gap_on_the_label_body_distance_chose_is_the_distance(yaw, gap, seed, t):
    """文档工作流：body_distance 选标签 → frozen_ee_sign 定朝向 → margin_gap_from_frozen_cover。分离的一对，冻结间隙必须是 +d
    （修前 96 个 EE 位形里 19 个给 −d：分离判成闭合），δ = 0.5d 时冻结间隙 0.5d 且 inflated_membership 答 OUTSIDE。"""
    A, B = _stack(yaw, gap, seed, t)
    d, lab = body_distance(A, B)
    if lab[0] != "EE":
        pytest.skip(f"nearest label is {lab[0]}, not EE")
    ea, eb = (lab[1][1], lab[1][2]), (lab[2][1], lab[2][2])
    sgn = frozen_ee_sign(A, B, ea, eb)
    tol = 1e-9 * max(1.0, d) + 4096 * 2.220446049250313e-16 * max(1.0, t)
    g = margin_gap_from_frozen_cover(A, B, lab, (0.0, 0.0, 0.0), 0.0, ee_sign=sgn)
    assert abs(g - d) <= tol, (d, g, sgn)
    g5 = margin_gap_from_frozen_cover(A, B, lab, (0.0, 0.0, 0.0), 0.5 * d, ee_sign=sgn)
    assert abs(g5 - 0.5 * d) <= tol, (d, g5)
    assert inflated_membership(A, B, delta=0.5 * d) == OUTSIDE


@pytest.mark.parametrize("yaw,seed,t", [(y, sd, t) for y in (1e-3, 1e-5) for sd in (4, 6) for t in (0.0, 1e3, 1e6)])
def test_frozen_ee_orientation_agrees_with_ee_cover_and_facet_normal3_on_every_ee_pair(yaw, seed, t):
    """同一个量一把尺：每一对交叉棱（ee_cover 给出盖的），冻结朝向 = ee_cover 选的法向 = facet_normal3 的法向。"""
    A, B = _stack(yaw, 1e-3, seed, t)
    n_cov = 0
    for ea in A.edges():
        for eb in B.edges():
            cov = ee_cover(A, ea, B, eb, 1e-9)
            if cov is None:
                continue
            n_cov += 1
            nf = ee_normal_generic(A, ea, B, eb, frozen_ee_sign(A, B, ea, eb))
            lab = ("EE", ("edge", ea[0], ea[1]), ("edge", eb[0], eb[1]))
            assert dot(cov.normal, nf) > 0.5, (ea, eb, cov.normal, nf)
            assert dot(cov.normal, facet_normal3(A, B, lab)) > 0.5, (ea, eb)
    assert n_cov >= 8


@pytest.mark.parametrize("seed", (4, 6))
@pytest.mark.parametrize("t,s", [(1e5, 1e-3), (1e6, 1e-2), (1e3, 1.0)])
def test_near_parallel_crossing_edges_stay_in_extent_in_engineering_coordinates(seed, t, s):
    """偏航 1e-5 的叠放方块：8 条最近 EE 是真并列（4 条近平行棱在棱中点交叉、4 条近正交棱在角点交叉），刚体运动后
    必须 8 条都在程——近平行那 4 条的交点参数在 C/L = 1e8 时被舍入推出好几个棱长，带要按 1/sinθ、1/sin²θ 放大。"""
    A0, B0 = _stack(1e-5, 0.06, seed, 0.0)
    A, B = _stack(1e-5, 0.06, seed, t, s)
    near = []
    for ea in A.edges():
        for eb in B.edges():
            c0 = ee_cover(A0, ea, B0, eb, 1e-9)
            if c0 is None or not c0.in_extent or abs(c0.gap - 0.06) > 1e-9:
                continue
            near.append((ea, eb))
            c = ee_cover(A, ea, B, eb, 1e-9)
            assert c is not None and c.in_extent, (ea, eb, None if c is None else c.params)
            assert abs(c.gap - 0.06 * s) <= 1e-9 * s + 4096 * 2.220446049250313e-16 * t
    assert len(near) == 8
    assert body_distance(A, B)[1] == body_distance(A0, B0)[1]          # 并列按枚举序裁决，不随刚体运动改变


def _corner_pair(yaw, gap, x0=0.3):
    """单位方块 A 的角点 (x0, −0.5) 绕过该点的竖轴偏航 yaw，坐在单位方块 B 上方 gap：A 的底棱 (0, 1) 与 B 的顶棱 (4, 5)
    夹角 yaw、交点恰在 A 棱的端点（s = 1）、B 棱的 0.8 处——近平行、相触（gap = 0）、端点上的边界态。"""
    top = box(center=(x0 - 0.5, 0.0, 1.0 + gap), half=(0.5, 0.5, 0.5))
    c, s = math.cos(yaw), math.sin(yaw)
    V = [(x0 + c * (x - x0) - s * (y + 0.5), -0.5 + s * (x - x0) + c * (y + 0.5), z) for x, y, z in top.verts]
    return Polyhedron(V, list(top.faces)), box(half=(0.5, 0.5, 0.5))


@pytest.mark.parametrize("seed", (4, 6, 9, 11, 13, 17))
@pytest.mark.parametrize("t,s", [(1e4, 1e-3), (1e5, 1e-3), (1e6, 1e-2)])
def test_touching_near_parallel_edges_crossing_at_an_endpoint_stay_in_extent(seed, t, s):
    """间隙为零时间隙杠杆项为零，只剩位置噪声：交点沿棱移 rfl/sinθ（坐标舍入 ~ulp 挪动棱的横向位置，夹角 θ = 1e-5 把它放大
    1e5 倍）。旧带只有 rfl/|e|（9e-7），54 个变换格里交点漂出 1e-5 … 6e-4，端点上的相触接触随坐标消失。"""
    A0, B0 = _corner_pair(1e-5, 0.0)
    c0 = ee_cover(A0, (0, 1), B0, (4, 5), 1e-9)
    assert c0 is not None and c0.in_extent and abs(c0.gap) < 1e-12
    assert abs(c0.params[0] - 1.0) < 1e-9 and abs(c0.params[1] - 0.8) < 1e-9
    tv = (t * 0.6, -t * 0.48, t * 0.64)
    A, B = _xf(A0, _rot3(seed), tv, s), _xf(B0, _rot3(seed), tv, s)
    c = ee_cover(A, (0, 1), B, (4, 5), 1e-9)
    assert c is not None and c.in_extent, (None if c is None else c.params)
    assert abs(c.gap) <= 4096 * 2.220446049250313e-16 * t


# ---------------------------------------------------------------- 第五轮另两路审查者的 critical 位形（同一缺陷，换了几何）

sys.path.insert(0, str(ROOT / "tests"))


def _ridge_pair(theta, g, y0=0.5):
    """四面体的水平脊棱悬在方块顶角上方 g，与一条顶棱近平行（夹角 θ）、与另一条交叉。"""
    from eab.kernel3d.geom3 import tetra
    B = box(half=(1.0, 1.0, 1.0))
    c, s = math.cos(theta), math.sin(theta)
    at = lambda u: (1.0 - u * s, y0 + u * c, 1.0 + g)                  # noqa: E731
    P0, P1 = at(-1.5), at(1.5 / c)
    mid = at(0.5 * (-1.5 + 1.5 / c))
    perp = (c, s, 0.0)
    Q0 = (mid[0] + 0.5 * perp[0], mid[1] + 0.5 * perp[1], mid[2] + 1.0)
    Q1 = (mid[0] - 0.5 * perp[0], mid[1] - 0.5 * perp[1], mid[2] + 1.0)
    return tetra(P0, P1, Q0, Q1), B


def _wedge_pair(k, g=0.1):
    """楔形（凸包）的底棱悬在方块上方 g、与方块顶棱夹角 2^-k·1.5 量级，镜像后编号让 EE 成为 body_distance 的标签。"""
    from eab.kernel3d.geom3 import convex_hull_3d
    d = 2.0 ** -k
    p0 = (-1.5, -1 - 1.5 * d, 0.5 + g)
    p1 = (1.5, -1 + 1.5 * d, 0.5 + g)
    u = (-d * 0.3, 0.3, 0.0)
    pts = [p0, p1] + [(p[0] + sg * u[0], p[1] + sg * u[1], p[2] + 1.0) for p in (p0, p1) for sg in (1, -1)]
    mirror = lambda P: Polyhedron([(-v[0], v[1], v[2]) for v in P.verts], [tuple(reversed(f)) for f in P.faces])  # noqa: E731
    return mirror(convex_hull_3d(pts)), mirror(box(half=(1.0, 1.0, 0.5)))


def _frozen_gap_of_chosen_label(A, B):
    d, lab = body_distance(A, B)
    sgn = frozen_ee_sign(A, B, (lab[1][1], lab[1][2]), (lab[2][1], lab[2][2])) if lab[0] == "EE" else 1.0
    return d, lab, float(margin_gap_from_frozen_cover(A, B, lab, (0.0, 0.0, 0.0), 0.0, ee_sign=sgn))


@pytest.mark.parametrize("theta", (1e-3, 1e-4))
@pytest.mark.parametrize("t", (1e3, 1e5, 1e6))
def test_frozen_gap_on_a_ridge_nearly_parallel_to_a_top_edge(theta, t):
    """审查者位形一：脊棱与顶棱近平行（θ = 1e-3 / 1e-4），20 个姿态 × 工程坐标；修前 θ = 1e-4、|t| = 1e5 时 8/20 给 −d。"""
    from test_invariance_geom import Motion
    for r in range(1, 21):
        M = Motion(r, t, 1.0)
        A, B = (M.poly(P) for P in _ridge_pair(theta, 0.01))
        d, lab, g = _frozen_gap_of_chosen_label(A, B)
        assert abs(g - d) <= 1e-6, (r, lab, d, g)


@pytest.mark.parametrize("rot,t", [(7, 1e6), (10, 1e5), (15, 1e5)])
def test_frozen_gap_on_a_nearly_parallel_wedge(rot, t):
    """审查者位形二：楔形底棱与顶棱近平行（2^-10），修前三格都给 −0.1。"""
    from test_invariance_geom import Motion
    A0, B0 = _wedge_pair(10)
    M = Motion(rot, t, 1.0)
    d, lab, g = _frozen_gap_of_chosen_label(M.poly(A0), M.poly(B0))
    assert lab[0] == "EE" and abs(d - 0.1) <= 1e-9 and abs(g - d) <= 1e-9, (lab, d, g)
