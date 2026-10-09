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
from eab.margin import (INSIDE, OUTSIDE, body_distance, effective_geom_tol, inflated_membership, margin_contacts,
                        margin_gap_from_frozen_cover, rounding_floor)


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
