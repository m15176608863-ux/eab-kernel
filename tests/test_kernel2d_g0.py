"""G0 自证门（凸情形逐样本恒等 + 局部法锥规则 = 全局 Minkowski facet 结构）。"""

import random

import pytest

from eab.kernel2d.covers import (convex_entrance_block, enumerate_covers, first_entrance_for_vertex,
                                 membership_convex)
from eab.kernel2d.g0 import g0_convex, random_convex_polygon
from eab.kernel2d.geom import ensure_ccw, is_convex, polygons_overlap, signed_area, translate

SQUARE = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
TRI = [(0.0, 0.0), (2.0, 0.0), (0.5, 1.5)]


@pytest.mark.parametrize("seed", range(12))
def test_g0_random_convex_pairs(seed):
    rng = random.Random(seed)
    A = random_convex_polygon(rng, rng.randint(4, 10), scale=rng.uniform(0.5, 2.0))
    B = random_convex_polygon(rng, rng.randint(4, 10), scale=rng.uniform(0.5, 2.0))
    assert is_convex(A) and is_convex(B)
    rep = g0_convex(A, B, samples=1500, seed=seed)
    assert rep.facet_symmetric_diff == [], rep.facet_symmetric_diff
    assert rep.facet_local == rep.facet_global == len(A) + len(B)
    assert rep.samples > 800
    assert rep.mismatches == [], rep.mismatches[:3]


def test_entrance_block_area_is_minkowski_area():
    # |B ⊕ (−A)| 对两个单位正方形 = (1+1)^2 = 4；四对平行边 → 四条 FF 退化 facet
    eb = convex_entrance_block(SQUARE, SQUARE, tol=1e-12)
    assert abs(signed_area(eb.vertices) - 4.0) < 1e-12
    assert sum(1 for f in eb.facets if f[0] == "FF") == 4


def test_degenerate_parallel_edges_membership_still_exact():
    rng = random.Random(7)
    eb = convex_entrance_block(SQUARE, SQUARE, tol=1e-12)
    for _ in range(500):
        x = (rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5))
        m = membership_convex(SQUARE, SQUARE, x, 1e-9, eb)
        b = polygons_overlap(translate(SQUARE, x), SQUARE, 1e-12)
        if m == 0 or b == 0:
            continue
        assert m == b, (x, m, b)


def test_gate_has_teeth_wrong_orientation_is_caught():
    # 门要有牙：把多边形朝向弄反（等价于外法向反向）的"坏输入"必须被 G0 抓住
    rng = random.Random(3)
    A = random_convex_polygon(rng, 7)
    B = random_convex_polygon(rng, 7)
    A_cw = list(reversed(A))
    # CW 输入的边角序单调下降 → 合并器拒绝（审查 r4c 后：不再静默 +2π 吞掉）
    with pytest.raises(ValueError):
        g0_convex(A_cw, B, samples=300, seed=1)
    A_ok, flipped = ensure_ccw(A_cw)
    assert flipped
    assert g0_convex(A_ok, B, samples=300, seed=1).passed


def test_first_entrance_picks_shallowest_penetration():
    # 三角形顶点 (0.5,1.5) 平移到正方形内 (0.5,0.3)：离底边 0.3、离左边 0.5，两条边都是有效 VE 盖
    A = translate(TRI, (0.0, -1.2))
    covs = enumerate_covers(A, SQUARE, window=10.0, tol=1e-12)
    ve_for_apex = [c for c in covs if c.kind == "VE" and c.a_index == 2]
    assert ve_for_apex, "apex must have valid VE covers"
    fe = first_entrance_for_vertex(A, 2, SQUARE, window=10.0, tol=1e-12)
    assert fe is not None and fe.kind == "VE"
    assert fe.gap == max(c.gap for c in ve_for_apex)
    assert abs(fe.gap + 0.3) < 1e-12 and fe.b_index == 0     # 底边 y=0，侵入 0.3


# ---------------------------------------------------------------- 凹块 G0：距离完备性（审查盲区 1，2026-09-24）

from math import cos, hypot, pi, sin  # noqa: E402

from eab.kernel2d.g0 import brute_polygon_distance, g0_distance_completeness  # noqa: E402

THIN_L = [(0.0, 0.0), (3.0, 0.0), (3.0, 0.1), (0.1, 0.1), (0.1, 3.0), (0.0, 3.0)]


def _star(rng, n, scale=1.0, off=(0.0, 0.0)):
    """一般位置的星形简单多边形（CCW，通常凹）：极角排序的随机半径。"""
    angs = sorted(rng.uniform(0.0, 2 * pi) for _ in range(n))
    return [(off[0] + scale * r * cos(a), off[1] + scale * r * sin(a))
            for a, r in ((a, rng.uniform(0.35, 1.0)) for a in angs)]


def _ring(rng, n, radius):
    """半径 radius 的一圈随机平移（多数分离、少数相交）。"""
    return [(radius * cos(t), radius * sin(t)) for t in (rng.uniform(0, 2 * pi) for _ in range(n))]


def test_brute_polygon_distance_matches_dense_boundary_sampling():
    """oracle 自检，用与它无关的第三条路：两边界各密采 400 点取点对最小距离（只会偏大，误差 ≤ 边长/400）。"""
    rng = random.Random(5)
    A = _star(rng, 7)
    B = [(p[0] + 2.6, p[1] + 0.3) for p in _star(rng, 9)]
    d, _ = brute_polygon_distance(A, B)

    def dense(P, k=400):
        out = []
        for i in range(len(P)):
            (ax, ay), (bx, by) = P[i], P[(i + 1) % len(P)]
            out += [(ax + (bx - ax) * s / k, ay + (by - ay) * s / k) for s in range(k)]
        return out
    ds = min(hypot(p[0] - q[0], p[1] - q[1]) for p in dense(A, 60) for q in dense(B, 60))
    assert d <= ds + 1e-12
    assert ds - d < 2.0 / 60        # 采样只会偏大，偏大量受采样步长约束


@pytest.mark.parametrize("scale", [1.0, 1e-3, 1e3], ids=["x1", "x1e-3", "x1e3"])
@pytest.mark.parametrize("seed", range(6))
def test_distance_completeness_general_position_concave(seed, scale):
    """纪律 B：一般位置（随机星形凹多边形，非对称）× 尺度变化（×1e-3 / ×1e3，外加远离原点的偏移）。"""
    rng = random.Random(100 + seed)
    off = (1e4 * scale, -3e3 * scale) if seed % 2 else (0.0, 0.0)
    A = _star(rng, rng.randint(5, 11), scale)
    B = _star(rng, rng.randint(5, 11), scale, off)
    xs = [(off[0] + p[0], off[1] + p[1]) for p in _ring(rng, 80, 1.6 * scale)]
    rep = g0_distance_completeness(A, B, xs, tol=1e-9 * scale, atol=1e-9)
    assert rep.samples >= 40, (rep.samples, rep.overlapping)
    assert rep.passed, rep.failures[:3]


DIAMOND = [(0.0, -0.5), (0.5, 0.0), (0.0, 0.5), (-0.5, 0.0)]


@pytest.mark.parametrize("A,x,kind", [
    (SQUARE, (1.3, 0.0), "parallel_edges_FF"),          # 两条平行边对峙：距离在整段上实现（退化 FF）
    (SQUARE, (0.4, 1.25), "parallel_edges_offset"),     # 平行边部分重叠对峙
    (SQUARE, (1.3, 1.3), "vertex_vertex_diagonal"),     # 角对角，分离方向落在两锥内部
    (SQUARE, (1.3, 1.0), "vertex_vertex_on_cone_edge"),  # 角对角，分离方向恰在锥边界上（分界点）
    (DIAMOND, (0.4, 1.7), "vertex_edge_interior"),      # 菱形下角对方块顶边内部：唯一的顶点-边实现
])
def test_distance_completeness_boundary_cases(A, x, kind):
    rep = g0_distance_completeness(A, SQUARE, [x], tol=1e-12, atol=1e-12)
    assert rep.samples == 1, kind
    assert rep.passed, (kind, rep.failures)


def test_distance_completeness_thin_arm_L_notch():
    """审查的反例几何上盖系统是完备的（错的是旧投票规则，见 test_kernel2d_review）。"""
    box = [(0.0, 0.0), (0.5, 0.0), (0.5, 0.05), (0.0, 0.05)]
    xs = [(ox, oy) for ox in (0.15, 0.2, 0.3, 0.5, 1.7) for oy in (0.105, 0.11, 0.12, 0.13, 0.9)]
    rep = g0_distance_completeness(box, THIN_L, xs, tol=1e-9)
    assert rep.samples == len(xs) and rep.passed, rep.failures[:3]


def test_distance_completeness_has_teeth(monkeypatch):
    """门要有牙：丢掉零维 VV 盖 → 角对角实现的距离漏掉 → 必红；丢掉 VE 盖 → 顶点-边实现漏掉 → 必红。"""
    import eab.kernel2d.covers as cv
    monkeypatch.setattr(cv, "vv_cover", lambda *a, **k: None)
    assert not g0_distance_completeness(SQUARE, SQUARE, [(1.3, 1.3)], tol=1e-12).passed
    monkeypatch.undo()
    monkeypatch.setattr(cv, "ve_cover", lambda *a, **k: None)
    assert not g0_distance_completeness(DIAMOND, SQUARE, [(0.4, 1.7)], tol=1e-12).passed
