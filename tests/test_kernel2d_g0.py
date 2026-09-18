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
    rep_bad = g0_convex(A_cw, B, samples=300, seed=1)
    assert rep_bad.mismatches or rep_bad.facet_symmetric_diff
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
