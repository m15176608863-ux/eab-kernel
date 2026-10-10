"""二维凸入口块的精确层（kernel2d/exact.py）：自身对独立精确 oracle 零错，并量出浮点路径 membership_convex 的静默错判。

纪律 A：`membership_exact`（经 Minkowski 和）与 `convex_overlap_exact`（分离轴、不经 Minkowski 和）零共用，全部 Fraction。
"""

from __future__ import annotations

import math
import random
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.kernel2d.exact import (convex_overlap_exact, entrance_block_exact, is_convex_exact,  # noqa: E402
                                membership_exact)
from eab.kernel2d.geom import translate  # noqa: E402


def _rand_convex(rng, n, r=1.0, c=(0.0, 0.0)):
    angs = sorted(rng.uniform(0, 2 * math.pi) for _ in range(n))
    P = [(c[0] + r * math.cos(t), c[1] + r * math.sin(t)) for t in angs]
    return P if is_convex_exact(P) else None


def _rigid(P, th, t):
    cs, sn = math.cos(th), math.sin(th)
    return [(cs * x - sn * y + t[0], sn * x + cs * y + t[1]) for x, y in P]


def _probe_points(eb, rng, k):
    """E 的顶点（恰相触）、facet 中点（恰相触）、以及随机平移。"""
    pts = []
    for v in eb.vertices:
        pts.append((float(v[0]), float(v[1])))
    for f in eb.facets:
        m = (f.start[0] + f.direction[0] / 2, f.start[1] + f.direction[1] / 2)
        pts.append((float(m[0]), float(m[1])))
    xs = [float(v[0]) for v in eb.vertices]
    ys = [float(v[1]) for v in eb.vertices]
    for _ in range(k):
        pts.append((rng.uniform(min(xs) - 0.2, max(xs) + 0.2), rng.uniform(min(ys) - 0.2, max(ys) + 0.2)))
    return pts


@pytest.mark.parametrize("seed", range(12))
@pytest.mark.parametrize("t", (0.0, 1e3, 1e6))
def test_exact_membership_equals_exact_separating_axis_oracle(seed, t):
    rng = random.Random(seed)
    A = B = None
    while A is None:
        A = _rand_convex(rng, rng.randint(3, 7), 0.5)
    while B is None:
        B = _rand_convex(rng, rng.randint(3, 7), 0.8)
    th = rng.uniform(0, 2 * math.pi)
    A, B = _rigid(A, th, (t, -0.7 * t)), _rigid(B, th, (t, -0.7 * t))
    if not (is_convex_exact(A) and is_convex_exact(B)):
        pytest.skip("rounding made a vertex reflex")
    eb = entrance_block_exact(A, B)
    for x in _probe_points(eb, rng, 60):
        assert membership_exact(A, B, x, eb) == convex_overlap_exact(A, B, x), x


def test_exact_parallel_edges_merge_into_ff_and_nothing_else_does():
    """精确平行同向才合并：方块对方块 4 条 FF；把一条边偏 1 ulp 的方向就不再并（各成一条 facet）。"""
    S = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    eb = entrance_block_exact(S, S)
    assert sorted(f.label[0] for f in eb.facets) == ["FF"] * 4
    T = [(0.0, 0.0), (1.0, math.ulp(1.0)), (1.0, 1.0), (0.0, 1.0)]
    eb2 = entrance_block_exact(T, S)
    assert sum(f.label[0] == "FF" for f in eb2.facets) == 3 and len(eb2.facets) == 5


def test_reviewer_round5_chamfer_example_is_answered_exactly():
    """G6 第五轮 critical 例一：单位方块削出 1e-14 的倒角边，对边长 0.5 的正三角形（−A 有 60° 边）。
    x = (1.1, 0.5) 处 A+x 实际压入 B（Fraction 凸包判内部），浮点路径 membership_convex 答 −1。精确层答 1。"""
    h = 1e-14
    B = [(0.0, 0.0), (1.0 - h, 0.0), (1.0, h), (1.0, 1.0), (0.0, 1.0)]
    Q = [(0.0, 0.0), (0.25, 0.25 * math.sqrt(3)), (-0.25, 0.25 * math.sqrt(3))]
    A = [(-p[0], -p[1]) for p in Q]
    assert membership_exact(A, B, (1.1, 0.5)) == 1 == convex_overlap_exact(A, B, (1.1, 0.5))


def test_rounded_flat_vertex_is_refused_by_the_convex_path():
    """T 形顶点（三点共线）经刚体运动后常被舍入成微凹：精确凸性如实说"不凸"，不许走凸路径。"""
    B = [(0.0, 0.0), (0.4, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    assert is_convex_exact(B)
    refused = 0
    for k in range(40):
        Bk = _rigid(B, 0.1 + 0.07 * k, (1e3, 2e3))
        if not is_convex_exact(Bk):
            refused += 1
            with pytest.raises(ValueError, match="exactly convex"):
                entrance_block_exact(Bk, Bk)
    assert refused > 0


@pytest.mark.parametrize("seed", range(10))
def test_exact_cone_validity_reproduces_the_exact_minkowski_facets(seed):
    """命题 5 的精确形：凸对的 E 的每条 VE / EV facet，其法锥判据精确地 ≥ 0；而且严格有效（= 1）的 VE / EV 恰好是 E 的非 FF facet。"""
    from eab.kernel2d.exact import ev_side_exact, ve_side_exact
    rng = random.Random(100 + seed)
    A = B = None
    while A is None:
        A = _rand_convex(rng, rng.randint(3, 7), 0.5)
    while B is None:
        B = _rand_convex(rng, rng.randint(3, 7), 0.8)
    eb = entrance_block_exact(A, B)
    facets = {f.label for f in eb.facets if f.label[0] != "FF"}
    strict = {("VE", i, j) for i in range(len(A)) for j in range(len(B)) if ve_side_exact(A, i, B, j) == 1}
    strict |= {("EV", k, i) for k in range(len(A)) for i in range(len(B)) if ev_side_exact(A, k, B, i) == 1}
    assert strict == facets, (sorted(strict ^ facets))


L_SHAPE = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (1.0, 1.0), (1.0, 2.0), (0.0, 2.0)]


@pytest.mark.parametrize("x,want", [((1.0, 1.0), 0),        # 方块角恰好卡进 L 的内角：只相触
                                     ((0.9, 0.9), 1),        # 压进去
                                     ((1.0 + 2 ** -40, 1.0 + 2 ** -40), -1),   # 离开 2^-40：精确分离（容差谓词会说"相触"）
                                     ((1.0, 1.0 - 2 ** -40), 1),                # 竖直压进 2^-40：精确相交
                                     ((2.0, 0.0), 0), ((2.5, 0.0), -1)])
def test_exact_overlap_on_a_concave_l_shape(x, want):
    sq = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    from eab.kernel2d.exact import polygons_overlap_exact
    assert polygons_overlap_exact(sq, L_SHAPE, x) == want


@pytest.mark.parametrize("seed", range(8))
def test_exact_overlap_agrees_with_the_convex_oracle_on_convex_pairs(seed):
    from eab.kernel2d.exact import polygons_overlap_exact
    rng = random.Random(500 + seed)
    A = B = None
    while A is None:
        A = _rand_convex(rng, rng.randint(3, 7), 0.5)
    while B is None:
        B = _rand_convex(rng, rng.randint(3, 7), 0.8)
    eb = entrance_block_exact(A, B)
    for x in _probe_points(eb, rng, 40):
        assert polygons_overlap_exact(A, B, x) == convex_overlap_exact(A, B, x), x


def test_star_pentagon_and_fold_back_are_not_convex():
    from eab.kernel2d.exact import convexity_violation
    star = [(math.cos(math.pi / 2 + 4 * math.pi * k / 5), math.sin(math.pi / 2 + 4 * math.pi * k / 5)) for k in range(5)]
    assert "winds 2 times" in convexity_violation(star)
    spike = [(0.0, 0.0), (2.0, 0.0), (1.0, 0.0), (1.0, 1.0)]          # 沿底边折回
    assert convexity_violation(spike) is not None


@pytest.mark.parametrize("seed", range(10))
def test_exact_hull_of_differences_equals_the_strict_vertices_of_e(seed):
    """票三的精确形：conv{b − a} 的顶点集 = E 的严格凸顶点集（两边都在 Fraction 上，零容差）。"""
    from eab.kernel2d.exact import _fr, hull_exact, strict_vertices
    rng = random.Random(900 + seed)
    A = B = None
    while A is None:
        A = _rand_convex(rng, rng.randint(3, 7), 0.5)
    while B is None:
        B = _rand_convex(rng, rng.randint(3, 7), 0.8)
    eb = entrance_block_exact(A, B)
    diffs = []
    from fractions import Fraction as Fr
    H = set()
    # 差点 b − a 必须精确：直接在 Fraction 上构造凸包（hull_exact 收浮点，这里另写一份 Fraction 输入的单调链作 oracle）
    pts = sorted({(Fr(b[0]) - Fr(a[0]), Fr(b[1]) - Fr(a[1])) for a in A for b in B})

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1]) - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out
    H = set(half(pts)[:-1] + half(list(reversed(pts)))[:-1])
    E = {eb.vertices[k] for k in strict_vertices(eb)}
    assert E == H
