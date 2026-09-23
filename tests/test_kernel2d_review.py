"""对抗审查（2026-09-18）抓到的反例，固化为回归门。每条对应审查报告一项。"""

import random
from math import radians, sin

import pytest

from eab.kernel2d.covers import (convex_entrance_block, enumerate_covers, normal_cone, ve_cover, vv_cover)
from eab.kernel2d.g0 import g0_convex, random_convex_polygon
from eab.kernel2d.geom import centroid, interior_point, is_convex, point_in_polygon, polygons_overlap, signed_area


def test_r1_narrow_crevice_is_reflex_even_with_legacy_tolerance():
    # A：底边有一条 178°（开口 2°）的窄缝；缝底顶点是反射顶点，3° 容差不得放行
    A = [(0.0, 0.0), (4.0, 0.0), (4.0, 2.0), (2.0 + 0.0349, 2.0), (2.0, 0.2), (2.0 - 0.0349, 2.0), (0.0, 2.0)]
    # 缝底顶点 index 4；转角 ≈ -178°
    assert normal_cone(A, 4, sin(radians(3.0))) is None
    B = [(0.0, 3.0), (4.0, 3.0), (4.0, 4.0), (0.0, 4.0)]
    assert ve_cover(A, 4, B, 0, 1e-9, sin(radians(3.0))) is None


def test_r3_numerically_collinear_vertex_yields_no_vv():
    # 顶点 1 数值共线（叉积 ~ -1e-16）：法锥退化为单射线，不能成为 E 的顶点
    P = [(0.0, 0.0), (1.0, 1e-16), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
    B = [(1.0, -2.0), (2.0, -2.0), (2.0, -1.0), (1.0, -1.0)]
    assert vv_cover(P, 1, B, 3, 1e-12) is None
    # legacy 容差下微凹（-1°，底边中点向内凹进）顶点同样不产生 VV
    Q = [(0.0, 0.0), (1.0, 0.0175), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
    from eab.kernel2d.geom import turn_angle
    assert -radians(3.0) < turn_angle(Q, 1) < 0.0
    assert vv_cover(Q, 1, B, 3, 1e-12, sin(radians(3.0))) is None
    covs = [c for c in enumerate_covers(Q, B, window=5.0, tol=1e-9, cone_tol=sin(radians(3.0))) if c.kind == "VV"]
    assert all(c.a_index != 1 for c in covs)


def test_r6_concave_centroid_outside_does_not_fake_overlap():
    # C 形（3×3 去掉右侧缺口），小方块完全在缺口里：不相交
    C = [(0.0, 0.0), (3.0, 0.0), (3.0, 1.0), (1.0, 1.0), (1.0, 2.0), (3.0, 2.0), (3.0, 3.0), (0.0, 3.0)]
    S = [(1.5, 1.25), (2.5, 1.25), (2.5, 1.75), (1.5, 1.75)]
    assert point_in_polygon(centroid(C), C) == -1          # 形心确实在自身外
    assert point_in_polygon(interior_point(C), C) == 1     # 保证内点在内
    assert polygons_overlap(C, S, 1e-12) == -1
    assert polygons_overlap(S, C, 1e-12) == -1
    rng = random.Random(1)
    for _ in range(200):
        x0, y0 = rng.uniform(1.05, 2.6), rng.uniform(1.05, 1.6)
        w, h = rng.uniform(0.05, 2.9 - x0), rng.uniform(0.05, 1.9 - y0)
        T = [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)]
        assert polygons_overlap(C, T, 1e-12) == -1


def test_r5c_far_offset_small_polygon_area_and_centroid():
    off = (1e4, 1e4)
    T = [(off[0], off[1]), (off[0] + 1e-4, off[1]), (off[0], off[1] + 1e-4)]
    # 输入坐标 1e4+1e-4 本身只有 ~1e-8 的相对精度（ulp(1e4)≈1.8e-12），算法误差不可能低于它
    assert abs(signed_area(T) - 0.5e-8) < 1e-15
    c = centroid(T)
    assert abs(c[0] - (off[0] + 1e-4 / 3)) < 1e-9 and abs(c[1] - (off[1] + 1e-4 / 3)) < 1e-9
    big = [(off[0] - 1, off[1] - 1), (off[0] + 1, off[1] - 1), (off[0] + 1, off[1] + 1), (off[0] - 1, off[1] + 1)]
    # 小三角在大方块外（平移出去）：不能因形心跳飞而误判
    Tout = [(p[0] + 5.0, p[1]) for p in T]
    assert polygons_overlap(Tout, big, 1e-12) == -1


def test_r4c_micro_concave_input_is_rejected_not_silently_mangled():
    # 尺度 1e-3、一个 4e-7 rad 内凹：旧实现 +2π 级联给出非凸 E；现在应抛错
    P = [(0.0, 0.0), (1e-3, 0.0), (1e-3, 1e-3), (0.5e-3, 1e-3 - 2e-10), (0.0, 1e-3)]
    assert not is_convex(P, 1e-12)
    with pytest.raises(ValueError):
        convex_entrance_block(P, [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)], tol=1e-12)


def test_r7_third_vote_hull_vertices_match_and_catch_sign_flip(monkeypatch):
    rng = random.Random(11)
    A = random_convex_polygon(rng, 7)
    B = random_convex_polygon(rng, 6)
    rep = g0_convex(A, B, samples=300, seed=2)
    assert rep.passed and rep.hull_vertex_mismatch == 0
    # 整体反号 outward_normal：标签集检验盲，但 G0 采样与第三票至少一个要红
    import eab.kernel2d.covers as cv
    orig = cv.outward_normal
    monkeypatch.setattr(cv, "outward_normal", lambda poly, i: tuple(-x for x in orig(poly, i)))
    bad = g0_convex(A, B, samples=300, seed=2)
    assert not bad.passed


def test_gap0_sign_of_min_gap_is_not_a_concave_membership_rule():
    """审查盲区 1（2026-09-21）的反例，钉成门：细臂 L 块（臂厚 0.1）+ 凹槽内悬浮 0.5×0.05 方块。

    暴力谓词判分离；旧 bb52 G0 的投票 sign(min gap over 非 VV 盖) 判相交——方块顶角对 L 块**外**底边
    （y=0）的 VE 盖法锥有效（非严格：+y 在方块顶角法锥边界上）、投影在边内、gap ≈ −0.16，落在 bb52 的
    窗口 D0 = 0.196875 内。16 个偏移全部失配。这条门断言的是"那条规则是假的"，所以它永远该绿；
    若哪天它红了，说明盖的有效性判据变了，得重新审视。
    """
    from eab.kernel2d.geom import translate
    L = [(0.0, 0.0), (3.0, 0.0), (3.0, 0.1), (0.1, 0.1), (0.1, 3.0), (0.0, 3.0)]
    S = [(0.0, 0.0), (0.5, 0.0), (0.5, 0.05), (0.0, 0.05)]
    d0 = 0.19687500000000002
    mismatches = 0
    for ox in (0.15, 0.2, 0.3, 0.5):
        for oy in (0.105, 0.11, 0.12, 0.13):
            A = translate(S, (ox, oy))
            assert polygons_overlap(A, L, 1e-12) == -1                 # 真值：分离
            covs = enumerate_covers(A, L, window=d0, tol=1e-9)
            pen = min(c.gap for c in covs if c.kind != "VV")
            culprit = [c for c in covs if c.kind == "VE" and c.b_index == 0 and c.gap < 0]
            assert culprit and not any(c.strict for c in culprit)      # 非严格 VE 盖对外底边
            assert abs(pen - (-(oy + 0.05))) < 1e-12                   # gap = −(方块顶 y)
            mismatches += (1 if pen < 0 else -1) != -1
    assert mismatches == 16


# ---------------------------------------------------------------- 审查 C19（2026-09-21）：零长边

SQ = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
FAR = [(2.0, 0.0), (3.0, 0.0), (3.0, 1.0), (2.0, 1.0)]


_IRR = [(1e4 + 1e-3 * x, -2e4 + 1e-3 * y) for x, y in
        [(0.0, 0.0), (1.3, -0.2), (1.7, 0.9), (0.6, 1.4), (0.6, 1.4), (-0.4, 0.8)]]   # 非对称、×1e-3、远离原点


@pytest.mark.parametrize("poly,where", [
    ([(0.0, 0.0), (1.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)], "interior"),
    ([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)], "cyclic_wrap"),
    ([(0.0, 0.0), (1.0, 0.0), (1.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)], "triple"),
    (_IRR, "irregular_scaled_far"),
])
def test_c19_zero_length_edge_is_a_clear_error_not_zerodivision(poly, where):
    """零长边（连续重复顶点）进内核：必须清晰报 ValueError('zero-length edge ...')，不许 ZeroDivisionError，
    也不许 convex_entrance_block 报出误导的 "not convex ... drops by 3.142 rad"。"""
    i = next(k for k in range(len(poly)) if poly[k] == poly[(k + 1) % len(poly)])
    for call in (lambda: normal_cone(poly, i), lambda: normal_cone(poly, (i + 1) % len(poly)),
                 lambda: enumerate_covers(poly, FAR, window=5.0, tol=1e-9),
                 lambda: enumerate_covers(FAR, poly, window=5.0, tol=1e-9),
                 lambda: convex_entrance_block(poly, FAR, tol=1e-12)):
        with pytest.raises(ValueError, match="zero-length edge"):
            call()


def _verts_csv(rows):
    return "step,block,vidx,x,y\n" + "".join(f"1,{b},{v},{x!r},{y!r}\n" for b, v, x, y in rows)


def _ring_rows(block, vid0, pts):
    return [(block, vid0 + k, x, y) for k, (x, y) in enumerate(pts)]


def _cases():
    s, o = 1e-3, (1e4, -2e4)
    small = [(o[0] + s * x, o[1] + s * y) for x, y in SQ]
    df_wrap = SQ + [SQ[0], SQ[1]]                                  # df 的两点回绕尾巴
    return [
        # (名字, 块 1 的原始点列, 期望的干净环, 期望 alias（局部下标 -> 局部下标）)
        ("interior", [SQ[0], SQ[1], SQ[1], SQ[2], SQ[3]], SQ, {2: 1}),
        ("first_equals_second", [SQ[0], SQ[0], SQ[1], SQ[2], SQ[3]], SQ, {1: 0}),
        ("triple_chain", [SQ[0], SQ[1], SQ[1], SQ[1], SQ[2], SQ[3]], SQ, {2: 1, 3: 1}),
        ("single_wrap_tail", SQ + [SQ[0]], SQ, {4: 0}),
        ("df_wrap_plus_interior", [SQ[0], SQ[1], SQ[2], SQ[2], SQ[3], SQ[0], SQ[1]], SQ, {3: 2, 5: 0, 6: 1}),
        ("clockwise_interior", [SQ[0], SQ[3], SQ[3], SQ[2], SQ[1]], SQ, {2: 1}),
        ("scaled_far_offset", [small[0], small[1], small[2], small[2], small[3]], small, {3: 2}),
    ]


def _load_both(tmp_path, monkeypatch, rows):
    """两个生产读取器同读一份 verts.csv：readers/bdda_geom 与 tools/bb52_g0（后者经 FIX 重定向）。"""
    import sys as _sys
    from pathlib import Path as _P
    _sys.path.insert(0, str(_P(__file__).resolve().parents[1] / "tools"))
    import bb52_g0
    from eab.readers.bdda_geom import load_step_geometries
    (tmp_path / "bdda_debug_verts.csv").write_text(_verts_csv(rows), encoding="utf-8")
    sg = load_step_geometries(tmp_path / "bdda_debug_verts.csv")[1]
    monkeypatch.setattr(bb52_g0, "FIX", tmp_path)
    blocks, alias = bb52_g0.load_blocks(1)
    return [("bdda_geom", sg.blocks[1].poly, sg.blocks[1].vidx, sg.alias),
            ("bb52_g0", blocks[1]["poly"], blocks[1]["vidx"], alias)]


def _same_cycle(P, Q):
    n = len(P)
    return n == len(Q) and any(all(P[(k + i) % n] == Q[i] for i in range(n)) for k in range(n))


@pytest.mark.parametrize("name,raw,clean,want_alias", _cases(), ids=[c[0] for c in _cases()])
def test_c19_loaders_strip_every_cyclic_consecutive_duplicate(tmp_path, monkeypatch, name, raw, clean, want_alias):
    """读取器在边界上剥除**所有**循环意义下的连续重复点，并把被剥的顶点号登记为 alias；
    剥完的多边形与干净多边形逐点同环、无零长边，盖枚举结果与干净多边形相同（按全局顶点号比）。"""
    vid0 = 100
    shift = 2.0 * abs(clean[1][0] - clean[0][0])
    nbr = [(x + shift, y) for x, y in clean]                       # 块 2：右侧的干净邻块
    rows = _ring_rows(1, vid0, raw) + _ring_rows(2, 200, nbr)
    want = {vid0 + k: vid0 + v for k, v in want_alias.items()}
    ref = sorted((c.kind, round(c.gap / shift, 12)) for c in enumerate_covers(clean, nbr, window=5.0, tol=1e-12))
    for who, poly, vidx, alias in _load_both(tmp_path, monkeypatch, rows):
        assert all(poly[k] != poly[(k + 1) % len(poly)] for k in range(len(poly))), (who, poly)
        assert _same_cycle(poly, clean), (who, poly)                # CCW、与干净环同一循环序
        assert {k: v for k, v in alias.items() if k < 200} == want, (who, alias)
        assert len(vidx) == len(poly) and not set(vidx) & set(want), (who, vidx)
        assert set(alias.values()) <= set(vidx) | set(range(200, 204)), (who, alias)   # alias 只指向保留的顶点
        got = sorted((c.kind, round(c.gap / shift, 12)) for c in enumerate_covers(poly, nbr, window=5.0, tol=1e-12))
        assert got == ref and ref, (who, got, ref)


def test_c19_ring_with_fewer_than_three_distinct_points_is_refused():
    from eab.readers.bdda_geom import strip_duplicate_vertices
    with pytest.raises(ValueError, match="block 9"):
        strip_duplicate_vertices([1, 2, 3, 4], [(0.0, 0.0), (1.0, 0.0), (1.0, 0.0), (0.0, 0.0)], block=9)
