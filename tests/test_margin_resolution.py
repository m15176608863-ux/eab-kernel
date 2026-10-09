"""M0.3 三维几何组的门（G6 第二轮，2026-09-27）：裕度层在"特征尺度 ≪ 坐标量级 / 块体尺度"处的正确性。

G6 第二轮对 814fdea 的两条 critical + 一条 major，都在 M0.2 元门格子够不着的角落（|t| ≤ 1e5、间隙 ≥ 1e-7、棱长比 ≤ 34）：
  · covers3 的角度噪声底 c·eps·C/ℓ 取**整对物体**的最短棱：一条极短的棱（或一个平缓的棱脊）让所有特征的角容差
    变大，真实凸棱被判平、EE/VE3 盖被丢，body_distance 报远处的 VF（2.055 vs 真值 0.05），答"安全"；
  · 裕度层把无量纲的盖容差 1e-9 传进 enumerate_covers3，`_pair_tols` 当作**绝对长度**用：块体 < 1 m 时间隙
    ≤ 1e-9 的真最近 VE3 被丢，报 1.1e-3（真值 1e-9）；
  · VE3/EV3/EE 的棱参数带 −ang ≤ s ≤ 1 + ang 把长度容差当无量纲带用：大块体角点附近见证点越出棱端 ang·|棱|，
    距离少报 40%、标签 VE3（应为 VV3）、冻结梯度方向错、成员判定反；等尺寸时 2e-9 的间隙报 0。
oracle：`brute_feature_distance`（全部特征对取最小，不经任何法锥或容差）。
"""

from __future__ import annotations

import math

import pytest

import eab.margin as M
from eab.dual import Dual
from eab.kernel3d.geom3 import Polyhedron, box, brute_feature_distance, convex_hull_3d, merge_coplanar, tetra
from eab.kernel3d.geom3 import polyhedra_overlap
from eab.margin import (INSIDE, ON_BOUNDARY, OUTSIDE, PENETRATING, body_distance, contact_resolution, effective_geom_tol,
                        inflated_membership, margin_contacts, margin_gap_from_frozen_cover, rounding_floor)


def _roof(h, t):
    """4 × 2 × 1 的块，顶面是两个面在高 h 的棱脊处相交（二面转角 ≈ 2h）。"""
    sec = [(-1.0, -1.0), (1.0, -1.0), (1.0, 0.0), (0.0, h), (-1.0, 0.0)]
    V = [(t[0] - 2.0, t[1] + y, t[2] + z) for y, z in sec] + [(t[0] + 2.0, t[1] + y, t[2] + z) for y, z in sec]
    F = [(4, 3, 2, 1, 0), (5, 6, 7, 8, 9)] + [(i, (i + 1) % 5, 5 + (i + 1) % 5, 5 + i) for i in range(5)]
    P = Polyhedron(V, F)
    assert P.manifold_issues() == []
    return P


def _needle(tip, r, H):
    x, y, z = tip
    return convex_hull_3d([tip] + [(x + r * math.cos(a), y + r * math.sin(a), z + H) for a in (0.1, 2.1943951, 4.2887902)])


def _blunt_needle(tip, r, H, e):
    """尖端截成边长 ~e 的小三角的针：物体上有三条极短的棱。"""
    x, y, z = tip
    return convex_hull_3d([(x + e * math.cos(a), y + e * math.sin(a), z) for a in (0.3, 2.3, 4.3)]
                          + [(x + r * math.cos(a), y + r * math.sin(a), z + H) for a in (0.1, 2.1943951, 4.2887902)])


def _expected(A, B):
    """真值与裕度层的相触分辨率约定：真实间距 ≤ geom_tol_eff 报 0。"""
    bd = brute_feature_distance(A, B)
    return (0.0 if bd <= effective_geom_tol(A, B) else bd), bd


def _assert_distance(A, B, kind=None):
    want, bd = _expected(A, B)
    d, lab = body_distance(A, B)
    assert d == pytest.approx(want, rel=1e-8, abs=4 * rounding_floor(A, B)), (d, bd, lab)
    if kind is not None:
        assert lab[0] == kind, (lab, d, bd)
    return d, lab, bd


def _assert_margin_consistent(A, B, delta, bd):
    """间距 bd 与 δ 的关系决定三个入口的回答：bd < δ ⇒ 成员 INSIDE、裕度接触非空且含最近者。"""
    m = inflated_membership(A, B, delta=delta)
    mc = margin_contacts(A, B, delta=delta)
    if bd < delta:
        assert m == INSIDE and mc and min(c.distance for c in mc) == pytest.approx(
            _expected(A, B)[0], rel=1e-8, abs=4 * rounding_floor(A, B)), (m, [(c.label, c.distance) for c in mc])
    else:
        assert m == OUTSIDE and mc == [], (m, mc)


# ---------------------------------------------------------------- critical：一处短棱 / 平缓棱脊毒化全体特征

@pytest.mark.parametrize("t", [(0.0, 0.0, 0.0), (6e5, -4.8e5, 6.4e5)], ids=["origin", "t1e6"])
def test_a_gentle_ridge_is_not_treated_as_flat(t):
    """棱脊高 1e-6（二面转角 2e-6 rad），针尖（底棱 ~1.7 mm）悬在它上方 0.05。最近特征对是针尖 × 棱脊（VE3）。"""
    B = _roof(1e-6, t)
    A = _needle((t[0] + 0.3, t[1], t[2] + 1e-6 + 0.05), 0.001, 1.0)
    _, lab, bd = _assert_distance(A, B, "VE3")
    assert lab[2] == ("edge", 3, 8), lab
    _assert_margin_consistent(A, B, 0.1, bd)


@pytest.mark.parametrize("tmag,e", [(0.0, 1e-8), (1e5, 1e-8), (1e3, 1e-10), (1e6, 1e-7), (1e6, 1e-9)])
def test_a_tiny_edge_elsewhere_does_not_drop_real_ridges(tmag, e):
    """针尖截成 e 大小的小三角（三条极短棱），棱脊二面转角 0.01 rad、针尖在其上方 0.05。旧版的角容差取整对最短棱：
    e = 1e-8 放在 1e5 处 → 0.054 rad > 0.01，真棱脊被判平，报 2.055、答"安全"。"""
    t = (0.6 * tmag, -0.48 * tmag, 0.64 * tmag)
    B = _roof(5e-3, t)
    A = _blunt_needle((t[0] + 0.3, t[1], t[2] + 5e-3 + 0.05), 0.1, 1.0, e)
    _, _, bd = _assert_distance(A, B)
    _assert_margin_consistent(A, B, 0.1, bd)


def _roof_with_tiny_corner(h, t, e):
    """同一个物体上既有二面转角 ≈ 2h 的缓棱脊、又有一个被削掉 e 的小角（三条 ~e 长的棱）。"""
    sec = [(-1.0, -1.0), (1.0, -1.0), (1.0, 0.0), (0.0, h), (-1.0, 0.0)]
    pts = [(t[0] - 2.0, t[1] + y, t[2] + z) for y, z in sec] + [(t[0] + 2.0, t[1] + y, t[2] + z) for y, z in sec]
    pts[0] = (t[0] - 2.0 + e, t[1] - 1.0, t[2] - 1.0)                   # 角点 (−2,−1,−1) 削成三个相距 e 的点
    pts += [(t[0] - 2.0, t[1] - 1.0 + e, t[2] - 1.0), (t[0] - 2.0, t[1] - 1.0, t[2] - 1.0 + e)]
    P = merge_coplanar(convex_hull_3d(pts))
    assert P.manifold_issues() == [] and P.metrics()[2] <= 1.5 * e
    return P


@pytest.mark.parametrize("tmag,e", [(1e5, 1e-8), (1e6, 1e-7)])
def test_a_tiny_edge_on_the_same_body_does_not_flatten_its_ridge(tmag, e):
    """短棱与缓棱脊在**同一个**物体上：角度噪声若按该物体的最短棱取（c·eps·C/e ≈ 0.1 rad），0.01 rad 的棱脊被判平。
    逐特征的噪声（棱脊的两相邻面各自的法向噪声）与 e 无关。"""
    t = (0.6 * tmag, -0.48 * tmag, 0.64 * tmag)
    B = _roof_with_tiny_corner(5e-3, t, e)
    A = _needle((t[0] + 0.3, t[1], t[2] + 5e-3 + 0.05), 0.001, 1.0)
    _, lab, bd = _assert_distance(A, B, "VE3")
    assert bd == pytest.approx(0.05, rel=1e-6)
    _assert_margin_consistent(A, B, 0.1, bd)


# ---------------------------------------------------------------- critical：无量纲 tol 被当绝对长度

def _small_pair(g, s):
    B = merge_coplanar(convex_hull_3d([(x, y, z) for x in (-2.0, 2.0) for (y, z) in ((0.0, 0.0), (-1.0, -1.0), (1.0, -1.0))]))
    c, sn = math.cos(0.5), math.sin(0.5)
    A = convex_hull_3d([(0.3, 0.0, g)] + [(0.3 + c * x - sn * y, sn * x + c * y, g + 0.1)
                                          for x, y in ((1.0, 0.0), (-0.5, 0.85), (-0.5, -0.85))])
    sc = lambda P: Polyhedron([tuple(s * v for v in p) for p in P.verts], list(P.faces))
    return sc(A), sc(B)


@pytest.mark.parametrize("s", [1.0, 1e-2, 1e-3, 1e-5])
def test_small_models_keep_their_nearest_low_dimensional_pair(s):
    """同一构形按 s 缩放：针尖到棱的间隙 1e-6·s。s = 1e-3 时间隙 1e-9（仍是 geom_tol_eff 的 ~600 倍），旧版
    `_pair_tols` 把盖容差 1e-9 当绝对长度，这个 VE3 被丢，报 1.1e-3。"""
    A, B = _small_pair(1e-6, s)
    _, _, bd = _assert_distance(A, B, "VE3")
    _assert_margin_consistent(A, B, 1e-4 * s, bd)


# ---------------------------------------------------------------- major：棱参数带的量纲

def _corner_tetra(half, p):
    ap = (half + 0.8 * p, half + 0.5 * p, half + 0.33 * p)
    return tetra(ap, (ap[0] + 1.0, ap[1] + 0.3, ap[2] + 0.2), (ap[0] + 0.2, ap[1] + 1.0, ap[2] + 0.4),
                 (ap[0] + 0.3, ap[1] + 0.1, ap[2] + 1.0)), ap


@pytest.mark.parametrize("half", [500.0, 5000.0])
@pytest.mark.parametrize("p", [1e-7, 1e-6, 1e-5, 1e-4])
def test_the_corner_of_a_large_block_is_a_vertex_contact(half, p):
    """1 m 的四面体尖顶悬在 1000 m / 10000 m 方块的角点外 p：最近特征对是顶点-顶点（VV3）。旧版棱参数带
    −ang ≤ s ≤ 1 + ang 让见证点越出棱端 ang·|棱|，报 VE3、距离少 40%、冻结梯度方向错、成员判定反。"""
    B = box((0.0, 0.0, 0.0), (half, half, half))
    A, ap = _corner_tetra(half, p)
    _, lab, bd = _assert_distance(A, B, "VV3")
    _assert_margin_consistent(A, B, 0.9 * bd, bd)
    x = tuple(Dual.seed(0.0, 3, i) for i in range(3))
    g = margin_gap_from_frozen_cover(A, B, lab, x, 0.0)
    v = [a - half for a in ap]                 # 实际浮点坐标下的方向（1e-7 放在 5000 处，理想方向只准到 ~1e-5）
    want = [c / math.hypot(*v) for c in v]
    assert g.e == pytest.approx(want, abs=1e-9), (g.e, want)


def _tA(p):
    return tetra((0.0, 0.0, p), (1.0, 0.2, 1.3 + p), (-0.4, 1.0, 1.1 + p), (-0.5, -0.9, 1.2 + p))


def _tB():
    return tetra((0.0, 0.0, 0.0), (0.9, -0.3, -1.2), (-0.3, 0.8, -1.0), (-0.6, -0.7, -1.1))


@pytest.mark.parametrize("p", [2e-9, 3e-9, 3.5e-9, 1e-8])
def test_apex_to_apex_gap_above_the_resolution_is_reported_exactly(p):
    """等尺寸四面体尖对尖，间隙 p 高于 geom_tol_eff（1.53e-9）：旧版 2e-9 报 0、3e-9 报 1.585e-9（EE 越出棱端）。"""
    A, B = _tA(p), _tB()
    assert p > effective_geom_tol(A, B)
    _, _, bd = _assert_distance(A, B, "VV3")
    _assert_margin_consistent(A, B, 0.5 * p, bd)


# ---------------------------------------------------------------- 自校验：盖路径漏掉最近特征对时必须抛错

def test_body_distance_refuses_to_return_a_distance_the_covers_cannot_certify(monkeypatch):
    """裕度层的距离由盖给出，再与"全部特征对、不经法锥"的暴力距离对账：对不上就抛错，不许静默报远处的盖。
    注入：盖枚举丢掉全部低维盖（旧版在短棱 / 小模型 / 远坐标下正是这样丢的）。"""
    real = M.enumerate_covers3
    monkeypatch.setattr(M, "enumerate_covers3", lambda A, B, **kw: real(A, B, **{**kw, "include_low_dim": False}))
    A, B = _small_pair(1e-6, 1.0)
    for call in (lambda: body_distance(A, B), lambda: margin_contacts(A, B, delta=1e-4),
                 lambda: inflated_membership(A, B, delta=1e-4)):
        with pytest.raises(RuntimeError, match="self-check"):
            call()


def test_body_distance_refuses_witnesses_that_are_not_on_the_bodies(monkeypatch):
    """另一侧：见证点越出特征（旧版的棱参数带），盖路径的距离比真值小——同样必须抛错。"""
    real = M.enumerate_covers3

    def shrink(A, B, **kw):
        out = real(A, B, **kw)
        for c in out:
            if c.point_a is not None and c.point_b is not None:
                c.point_a = tuple(b + 0.5 * (a - b) for a, b in zip(c.point_a, c.point_b))
        return out
    monkeypatch.setattr(M, "enumerate_covers3", shrink)
    A, B = _small_pair(1e-3, 1.0)
    with pytest.raises(RuntimeError, match="self-check"):
        body_distance(A, B)


# ---------------------------------------------------------------- G6 第三轮：相触分辨率只有一把尺

def _rotq(seed):
    import random
    rng = random.Random(9100 + seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def _motion(P, R, t):
    return Polyhedron([tuple(t[i] + sum(R[i][j] * p[j] for j in range(3)) for i in range(3)) for p in P.verts], list(P.faces))


@pytest.mark.parametrize("tmag", [0.0, 1e5, 1e6])
def test_penetration_answers_are_monotone_through_the_resolution_window(tmag):
    """G6 第三轮 critical：|t| = 1e6 时舍入地板 ≈ geom_tol_eff，旧版把贯入深度落在 (geom_tol, geom_tol + 舍入] 的一对当
    **正间距**报出、答 OUTSIDE（fail-unsafe）。现在钳零与哨兵用同一把尺 ctol：深度 ≤ ctol 答 0 / ON_BOUNDARY，更深给哨兵，
    任何深度都不许答正间距或 OUTSIDE，且随深度单调。"""
    R = _rotq(7)
    t = tuple(tmag * c for c in (0.6, -0.48, 0.64))
    B = _motion(box((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)), R, t)
    A0 = _motion(box((1.51, 0.5, 0.5), (0.51, 0.3, 0.5)), R, t)
    gt = effective_geom_tol(A0, B)
    ct = contact_resolution(A0, B)
    seen = []
    for k in (0.5, 1.2, 1.5, 3.0, 10.0, 30.0):
        p = k * gt
        A = _motion(box((1.51 - p, 0.5, 0.5), (0.51, 0.3, 0.5)), R, t)      # A 咬进 B 深 p
        d, lab = body_distance(A, B)
        m0 = inflated_membership(A, B, delta=0.0)
        mc = margin_contacts(A, B, delta=1e-8)
        assert d == 0.0, (tmag, k, d, lab)                                   # 绝不报正间距
        assert m0 in (ON_BOUNDARY, INSIDE), (tmag, k, m0)
        assert mc and all(c.closed for c in mc), (tmag, k, mc)                # δ = 1e-8 下必有已闭合的接触
        seen.append(1 if lab == (PENETRATING,) else 0)
        if p > 2.5 * ct:
            assert lab == (PENETRATING,), (tmag, k, lab)
    assert seen == sorted(seen), seen                                        # 单调：相触 … 哨兵


@pytest.mark.parametrize("rot", [0.0, 0.3, 1.1])
@pytest.mark.parametrize("gap", [1e-10, 1e-8, 1e-6])
def test_a_tiny_block_near_a_huge_block_is_judged_the_same_in_every_orientation(rot, gap):
    """G6 第三轮 major：1 cm 方块悬在 200 m 方块顶面上方 gap。谓词的"在表面上"带是被测体的 1e-12·diag（3.5e-10），大于
    小块给出的 geom_tol_eff（1.7e-11）；旧版未旋转时报 1e-10 的间距，转 0.3 rad 后答 PENETRATING。现在相触分辨率
    ctol 含谓词自己的分辨率：gap 低于它两种朝向都答相触（0 / ON_BOUNDARY），高于它都答出 gap。"""
    def rotx(P, a):
        c, s = math.cos(a), math.sin(a)
        return Polyhedron([(x, c * y - s * z, s * y + c * z) for x, y, z in P.verts], list(P.faces))
    B = rotx(box((0.0, 0.0, 0.0), (100.0, 100.0, 100.0)), rot)
    A = rotx(box((30.0, 20.0, 100.0 + 0.005 + gap), (0.005, 0.005, 0.005)), rot)
    ct = contact_resolution(A, B)
    d, lab = body_distance(A, B)
    m = inflated_membership(A, B, delta=0.0)
    assert lab != (PENETRATING,), (rot, gap, lab)
    if gap <= ct:
        assert d == 0.0 and m == ON_BOUNDARY, (rot, gap, d, m, ct)
    else:
        assert d == pytest.approx(gap, rel=1e-6) and m == OUTSIDE, (rot, gap, d, m, ct)


@pytest.mark.parametrize("S", [10.0, 100.0])
@pytest.mark.parametrize("g", [2e-9, 1e-8, 1e-7])
def test_a_corner_on_the_floor_plane_but_outside_the_face_is_separated(S, g):
    """G6 第三轮 major：方块转 45° 坐在四面体底面所在的 z = 0 平面上，最近角点在面内离底边 g（块共用地板：DDA 最普通的位形）。
    旧版把顶点"落在对方面平面上、面内在多边形外 ≤ 1e-9·diag"判成边界，谓词答相触，裕度层再升成 PENETRATING / INSIDE
    （S = 100 时 g 到 58 倍 geom_tol_eff 都如此）。"""
    r2 = math.sqrt(0.5)
    B = tetra((0.0, 0.0, 0.0), (S, 0.0, 0.0), (0.0, S, 0.0), (0.0, 0.0, S))
    c = ((S + r2 + g * math.sqrt(2.0)) / 2,) * 2 + (0.5,)
    P = box(half=(0.5, 0.5, 0.5))
    A = Polyhedron([(c[0] + r2 * x - r2 * y, c[1] + r2 * x + r2 * y, c[2] + z) for x, y, z in P.verts], list(P.faces))
    ct = contact_resolution(A, B)
    bd = brute_feature_distance(A, B)
    assert bd == pytest.approx(g, rel=1e-6)
    d, lab = body_distance(A, B)
    assert lab != (PENETRATING,), (S, g, lab)
    if g > ct:
        assert polyhedra_overlap(A, B, effective_geom_tol(A, B)) == -1
        assert d == pytest.approx(g, rel=1e-6) and inflated_membership(A, B, delta=0.0) == OUTSIDE
    else:
        assert d == 0.0


@pytest.mark.parametrize("k", [2.5, 3.0, 10.0, 20.0])
def test_a_thin_sliver_penetration_is_detected_above_twice_the_resolution(k):
    """G6 第三轮 major：接触锥证人旧版只按 10 倍阶梯试探，一般朝向下深 (tol, ~20·tol) 的薄片贯入一个探针都落不进去、答"相触"。
    现在沿切锥内部方向走到交集最深处：凸体上深于 2 倍分辨率的贯入一定判 1。"""
    R = _rotq(7)
    B = _motion(box((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)), R, (0.0, 0.0, 0.0))
    A0 = _motion(box((1.51, 0.5, 0.5), (0.51, 0.3, 0.5)), R, (0.0, 0.0, 0.0))
    gt = effective_geom_tol(A0, B)
    A = _motion(box((1.51 - k * gt, 0.5, 0.5), (0.51, 0.3, 0.5)), R, (0.0, 0.0, 0.0))
    assert polyhedra_overlap(A, B, gt) == 1, (k, gt)


# ---------------------------------------------------------------- G6 第三轮 major：近平行棱

@pytest.mark.parametrize("theta,gap", [(1e-5, 1e-3), (1e-6, 0.1), (1e-7, 1e-3), (1e-8, 1e-8), (3e-4, 0.02)])
def test_nearly_parallel_edges_give_the_exact_distance(theta, gap):
    """B 的顶棱沿 x，A 的底棱在 z = gap、绕 z 转 θ：真最近对是两棱内部点、距离恰为 gap。旧版 EE 见证点的 s、t 独立求、
    各带 ~eps/sin²θ 的误差，两点沿棱错位，见证距离偏大（θ = 1e-8 时偏 0.4），自校验误抛。"""
    B = tetra((-1.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, -0.8, -1.5), (0.0, 0.9, -1.4))
    c, s, x0 = math.cos(theta), math.sin(theta), 0.1
    A = tetra((x0 - 0.7 * c, -0.7 * s, gap), (x0 + 0.7 * c, 0.7 * s, gap), (x0 - 0.1, -0.7, 1.3 + gap), (x0 + 0.2, 0.8, 1.2 + gap))
    bd = brute_feature_distance(A, B)
    assert bd == pytest.approx(gap, rel=1e-9)
    d, lab = body_distance(A, B)
    assert lab != (PENETRATING,) and d == pytest.approx(gap, rel=1e-9), (theta, gap, d, lab)
    assert inflated_membership(A, B, delta=2 * gap) == INSIDE and inflated_membership(A, B, delta=0.5 * gap) == OUTSIDE


# ---------------------------------------------------------------- G6 第三轮 minor：零长棱 / 零面积面要清晰报错

def test_zero_length_edges_are_a_clear_error_in_three_d():
    """面环里插入重复顶点（网格导出常见）：manifold_issues 要报出零长棱；盖枚举与裕度层抛带棱号的 ValueError，
    不是 ZeroDivisionError。"""
    from eab.kernel3d.covers3 import enumerate_covers3
    b = box()
    v = list(b.verts) + [b.verts[1]]
    faces = []
    for f in b.faces:
        f = list(f)
        if 1 in f:
            f.insert(f.index(1) + 1, 8)
        faces.append(tuple(f))
    P = Polyhedron(v, faces)
    assert any("zero length" in m for m in P.manifold_issues()), P.manifold_issues()
    with pytest.raises(ValueError, match="zero-length edge"):
        enumerate_covers3(P, box((3.0, 0.0, 0.0)), window=float("inf"))
    with pytest.raises(ValueError, match="zero-length edge"):
        body_distance(P, box((3.0, 0.0, 0.0)))


def test_edges_that_round_to_duplicates_at_engineering_coordinates_are_rejected_loudly():
    """1e-8 的短棱在 1e6 处按 1e-3 缩放后低于 eps·C，顶点舍入成重合：manifold_issues 必须报出来，裕度层抛 ValueError。"""
    A = _blunt_needle((0.3, 0.0, 5e-3 + 0.05), 0.1, 1.0, 1e-8)
    B = _roof(5e-3, (0.0, 0.0, 0.0))
    R = _rotq(7)
    t = (6e5, -4.8e5, 6.4e5)
    s = 1e-3
    mv = lambda P: Polyhedron([tuple(t[i] + s * sum(R[i][j] * p[j] for j in range(3)) for i in range(3)) for p in P.verts], list(P.faces))
    As, Bs = mv(A), mv(B)
    if any(As.verts[e[0]] == As.verts[e[1]] for e in As.edges()):
        assert As.manifold_issues()
        with pytest.raises(ValueError):
            body_distance(As, Bs)


# ---------------------------------------------------------------- G6 第三轮 major：G0 门在工程坐标上要分清"分辨不了"与"不一致"

@pytest.mark.parametrize("rot,tmag", [(7, 0.0), (7, 1e3), (7, 1e5), (7, 1e6), (0, 1e6)])
def test_g0_three_votes_on_the_ridge_pair_at_engineering_coordinates(rot, tmag):
    """针底 1.7 mm 的短棱在 1e3 处的方向噪声 5e-9 rad，而两个真 E 顶点的锥相交裕度只有 1e-9：旧版票三一刀切成"不是顶点"、
    凸包侧按长度容差保留它们，报失配；票二在 1e6 处把法向只差 2e-9 rad 的两个 EE facet 并成退化 facet 而不报歧义。
    现在：说不清的顶点对与 facet 两边都不计并如实报出，门必须通过；原点处没有任何歧义。"""
    from eab.kernel3d.g03 import g0_convex3
    B0 = _roof(1e-6, (0.0, 0.0, 0.0))
    A0 = _needle((0.3, 0.0, 1e-6 + 0.05), 0.001, 1.0)
    R = _rotq(rot) if rot else ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    t = tuple(tmag * c for c in (0.6, -0.48, 0.64))
    A, B = _motion(A0, R, t), _motion(B0, R, t)
    rep = g0_convex3(A, B, samples=12, seed=1)
    assert rep.passed, (tmag, rep)
    if tmag == 0.0:
        assert rep.facet_ambiguous == 0 and rep.e_vertices_ambiguous == 0 and rep.e_vertices == 22, rep
    else:
        # 两个"针尖级"E 顶点（锥相交裕度 ~1e-9）在工程坐标上或被记为说不清、或两边都认为低于分辨率
        assert 20 <= rep.e_vertices + rep.e_vertices_ambiguous <= 22, rep
        assert rep.facet_ambiguous <= 2 and rep.e_vertices_ambiguous <= 4 and rep.facet_local_dropped <= 4, rep


def test_margin_self_check_catches_a_relative_1e_6_witness_error(monkeypatch):
    """G6 第三轮 minor：自校验阈值（4·舍入）要有牙——注入相对 1e-6 的见证距离误差必须抛错。"""
    real = M.enumerate_covers3

    def skew(A, B, **kw):
        out = real(A, B, **kw)
        for c in out:
            if c.point_a is not None and c.point_b is not None:
                c.point_a = tuple(b + (1.0 + 1e-6) * (a - b) for a, b in zip(c.point_a, c.point_b))
        return out
    monkeypatch.setattr(M, "enumerate_covers3", skew)
    A, B = _small_pair(1e-3, 1.0)
    with pytest.raises(RuntimeError, match="self-check"):
        body_distance(A, B)


# ---------------------------------------------------------------- G6 第三轮 minor：自校验阈值 4·rnd 没有牙

@pytest.mark.parametrize("rel", [1e-6, -1e-6, 0.0])
def test_margin_self_check_catches_sub_ppm_witness_errors(monkeypatch, rel):
    """把盖路径的见证距离整体乘 (1 ± 1e-6)——远高于舍入地板 ~1e-14、远低于现有粗错的门——三个入口都必须抛 RuntimeError
    （旧版把阈值放宽到相对 1e-3，1639 例照绿）；只偏 1·rnd（rel = 0 这格）不许抛，锁住阈值的下限。"""
    import eab.margin as M
    from eab.margin import margin_contacts
    A, B = box(center=(0.0, 0.0, 1.6), half=(0.5, 0.5, 0.5)), box(half=(1.0, 1.0, 0.5))      # 间隙 0.6
    rnd = M.rounding_floor(A, B)
    real = M.cover_witness

    def skew(c):
        w = real(c)
        if w is None:
            return None
        f = (1.0 + rel) if rel else (1.0 + rnd / w[0] if w[0] > 0.0 else 1.0)
        return (w[0] * f, w[1])
    monkeypatch.setattr(M, "cover_witness", skew)
    for call in (lambda: body_distance(A, B), lambda: margin_contacts(A, B, delta=0.3),
                 lambda: inflated_membership(A, B, delta=0.3)):
        if rel:
            with pytest.raises(RuntimeError, match="self-check"):
                call()
        else:
            call()
