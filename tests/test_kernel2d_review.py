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


_CHANNEL = [(0.0, 0.0), (3.0, 0.0), (3.0, 1.0), (1.0, 1.0), (1.0, 1.8), (3.0, 1.8), (3.0, 2.8), (0.0, 2.8)]
_WEDGE = [(0.0, 0.0), (0.6, 0.2), (0.2, 0.75)]          # 楔尖在原点，56.7°，CCW


@pytest.mark.parametrize("scale,off", [(1.0, (0.0, 0.0)), (1e-3, (10.0, -3.0)), (1e3, (1e7, -3e6))],
                         ids=["x1", "x1e-3_far", "x1e3_far"])
@pytest.mark.parametrize("dx,dy", [(0.05, 0.05), (0.02, 0.08), (0.08, 0.03), (0.01, 0.01), (0.1, 0.1)])
def test_gap0_sign_of_min_gap_false_negative_wedge_in_channel(dx, dy, scale, off):
    """旧 bb52 G0 投票的**另一半**也是假的（2026-09-24）：相交判成分离。

    C 形槽（反射角在 (1,1)）+ 楔块，楔尖压进槽角 (dx, dy)（一般位置：对称/非对称、浅/深；尺度 ×1e-3、×1e3
    并远离原点）。暴力谓词判相交。楔尖对槽底上沿（边 2）、槽左壁（边 3）的 VE 盖法锥有效、间隙 −dy / −dx，
    但投影参数 1 + dx/2 / −dy/0.8 出界，被边内筛选剔除；窗口 D0 内只剩楔顶对槽顶（边 4）的 VE 盖，
    间隙 0.05 + dy > 0 → 投票判分离。同一位形上出口完备性为绿（盖系统没错，错的是投票规则）。
    """
    from eab.kernel2d.g0 import g0_exit_completeness
    from eab.kernel2d.geom import translate
    C = [(off[0] + scale * x, off[1] + scale * y) for x, y in _CHANNEL]
    x = (off[0] + scale * (1.0 - dx), off[1] + scale * (1.0 - dy))
    W = [(scale * a, scale * b) for a, b in _WEDGE]
    A = translate(W, x)
    d0 = 0.19687500000000002 * scale
    assert polygons_overlap(A, C, 1e-12 * scale) == 1                   # 真值：相交
    covs = [c for c in enumerate_covers(A, C, window=d0, tol=1e-9 * scale) if c.kind != "VV"]
    assert [(c.kind, c.a_index, c.b_index) for c in covs] == [("VE", 2, 4)]
    assert abs(covs[0].gap / scale - (0.05 + dy)) < 1e-9                 # 唯一入窗盖：正间隙
    tip = {c.b_index: c for c in enumerate_covers(A, C, window=d0, tol=1e-9 * scale, require_in_segment=False)
           if c.kind == "VE" and c.a_index == 0}
    assert set(tip) == {2, 3}
    assert abs(tip[2].gap / scale + dy) < 1e-9 and abs(tip[3].gap / scale + dx) < 1e-9     # 负间隙……
    assert abs(tip[2].param - (1.0 + dx / 2.0)) < 1e-9 and abs(tip[3].param + dy / 0.8) < 1e-9   # ……但出界
    vote = 1 if min(c.gap for c in covs) < 0 else -1
    assert vote == -1                                                   # 旧投票：分离（错）
    u = (-0.6, 0.8)
    rep = g0_exit_completeness(W, C, [x], [u], tol=1e-9 * scale)
    assert rep.samples == 1 and rep.passed, rep.failures


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


# ---------------------------------------------------------------- G6 major 12（2026-09-24）：interior_point 与 polygons_overlap

from fractions import Fraction as _Fr  # noqa: E402


def _fr_cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _fr_poly(P):
    Q = [(_Fr(x), _Fr(y)) for x, y in P]
    a2 = sum(_fr_cross((0, 0), Q[i], Q[(i + 1) % len(Q)]) for i in range(len(Q)))
    return Q if a2 > 0 else Q[::-1]


def _exact_parity(pt, P) -> int:
    """独立 oracle ①：Fraction 精确射线奇偶（1 严格在内 / 0 边界 / −1 外）。不调 geom 的任何原语。"""
    px, py = _Fr(pt[0]), _Fr(pt[1])
    Q = [(_Fr(x), _Fr(y)) for x, y in P]
    inside = False
    for i in range(len(Q)):
        (ax, ay), (bx, by) = Q[i], Q[(i + 1) % len(Q)]
        if _fr_cross((ax, ay), (bx, by), (px, py)) == 0 and min(ax, bx) <= px <= max(ax, bx) \
                and min(ay, by) <= py <= max(ay, by):
            return 0
        if (ay > py) != (by > py) and px < ax + (py - ay) * (bx - ax) / (by - ay):
            inside = not inside
    return 1 if inside else -1


def _exact_ear_clip(P):
    """Fraction 精确耳切（简单多边形）→ 三角形列表（CCW）。"""
    Q = _fr_poly(P)
    idx = list(range(len(Q)))
    tris = []
    while len(idx) > 3:
        n = len(idx)
        for k in range(n):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % n]
            a, b, c = Q[i0], Q[i1], Q[i2]
            if _fr_cross(a, b, c) <= 0:
                continue
            if any(_fr_cross(a, b, Q[j]) >= 0 and _fr_cross(b, c, Q[j]) >= 0 and _fr_cross(c, a, Q[j]) >= 0
                   for j in idx if j not in (i0, i1, i2)):
                continue
            tris.append((a, b, c))
            idx.pop(k)
            break
        else:                                               # 只剩平直顶点可删
            k = next(k for k in range(n) if _fr_cross(Q[idx[k - 1]], Q[idx[k]], Q[idx[(k + 1) % n]]) == 0)
            idx.pop(k)
    a, b, c = (Q[i] for i in idx)
    if _fr_cross(a, b, c) > 0:
        tris.append((a, b, c))
    return tris


def _clip_area(T, U):
    """独立 oracle ②：Sutherland–Hodgman 精确裁剪（凸 T 被凸 U 裁），返回交集面积（Fraction）。与 SAT 不同路。"""
    out = list(T)
    for i in range(3):
        a, b = U[i], U[(i + 1) % 3]
        inp, out = out, []
        if not inp:
            break
        for j in range(len(inp)):
            p, q = inp[j - 1], inp[j]
            sp, sq = _fr_cross(a, b, p), _fr_cross(a, b, q)
            if sq >= 0:
                if sp < 0:
                    t = sp / (sp - sq)
                    out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
                out.append(q)
            elif sp >= 0:
                t = sp / (sp - sq)
                out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    if len(out) < 3:
        return _Fr(0)
    return sum(_fr_cross((0, 0), out[i], out[(i + 1) % len(out)]) for i in range(len(out))) / 2


def _exact_overlap(A, B) -> bool:
    """内部相交 ⟺ 两份精确耳切里某对三角形的精确交集面积 > 0。"""
    return any(_clip_area(T, U) > 0 for T in _exact_ear_clip(A) for U in _exact_ear_clip(B))


def _exact_proper_cross(p1, p2, q1, q2):
    d1, d2 = _fr_cross(p1, p2, q1), _fr_cross(p1, p2, q2)
    d3, d4 = _fr_cross(q1, q2, p1), _fr_cross(q1, q2, p2)
    return d1 * d2 < 0 and d3 * d4 < 0


def _random_simple_polygon(rng, n):
    """2-opt 解缠：随机点列，反复把一对真相交的边反转，直到无相交（精确谓词）。一般位置，不在测试里挑形状。"""
    P = [(rng.uniform(0.0, 1.0), rng.uniform(0.0, 1.0)) for _ in range(n)]
    F = [(_Fr(x), _Fr(y)) for x, y in P]
    for _ in range(5000):
        hit = None
        for i in range(n):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                if _exact_proper_cross(F[i], F[(i + 1) % n], F[j], F[(j + 1) % n]):
                    hit = (i, j)
                    break
            if hit:
                break
        if hit is None:
            return P
        i, j = hit
        P[i + 1:j + 1] = reversed(P[i + 1:j + 1])
        F[i + 1:j + 1] = reversed(F[i + 1:j + 1])
    return None


# V 形缺口六边形：最左顶点 v=(0,0)，三角 (p, v, q) 里有两个顶点——缺口尖 t=(2,0)（离直线 pq 最远）与缺口下沿
# a=(6,0.6)（离 v 最远）。旧规则取 a、返回 v–a 中点 (3, 0.3)，它落在缺口里（体外）。O'Rourke 规则取 t。
NOTCH = [(0.0, 0.0), (8.0, -4.0), (9.0, 0.0), (6.0, 0.6), (2.0, 0.0), (8.0, 4.0)]
NOTCH_BOX = [(2.9, 0.25), (3.1, 0.25), (3.1, 0.4), (2.9, 0.4)]            # 悬在缺口里，与 NOTCH 分离
C_SHAPE = [(0.0, 0.0), (3.0, 0.0), (3.0, 1.0), (1.0, 1.0), (1.0, 2.0), (3.0, 2.0), (3.0, 3.0), (0.0, 3.0)]


def test_g6_12_notch_hexagon_interior_point_is_inside():
    from eab.kernel2d.geom import is_ccw
    assert is_ccw(NOTCH) and _exact_parity((3.0, 0.3), NOTCH) == -1        # 旧规则的返回值确在体外
    ip = interior_point(NOTCH)
    assert _exact_parity(ip, NOTCH) == 1, ip


def test_g6_12_notch_hexagon_box_in_the_notch_is_separated():
    assert not _exact_overlap(NOTCH, NOTCH_BOX)
    assert polygons_overlap(NOTCH, NOTCH_BOX, 1e-12) == -1
    assert polygons_overlap(NOTCH_BOX, NOTCH, 1e-12) == -1


def test_g6_12_c_shape_shifted_down_two_overlaps_on_the_arms():
    """C 与 C 平移 (0,−2)：底臂与顶臂重合（面积 3），没有顶点严格在对方体内、没有边横截相交——旧谓词判 0（接触）。"""
    from eab.kernel2d.geom import translate
    D = translate(C_SHAPE, (0.0, -2.0))
    assert _exact_overlap(C_SHAPE, D)
    assert _exact_parity((2.0, 0.5), C_SHAPE) == 1 and _exact_parity((2.0, 0.5), D) == 1
    assert polygons_overlap(C_SHAPE, D, 1e-12) == 1
    assert polygons_overlap(D, C_SHAPE, 1e-12) == 1


def test_g6_12_interior_point_on_random_simple_polygons():
    """2-opt 随机简单多边形（5–10 顶点，固定种子）：interior_point 必须严格在内（精确射线奇偶 oracle）。
    旧规则在 0.1–0.25% 的多边形上返回体外点（G6 实测 7/5000、49/20000）。"""
    rng = random.Random(7)
    bad, n_ok = [], 0
    while n_ok < 3000:
        P = _random_simple_polygon(rng, rng.randint(5, 10))
        if P is None:
            continue
        n_ok += 1
        if _exact_parity(interior_point(P), P) != 1:
            bad.append(P)
    assert bad == [], (len(bad), bad[:1])


def test_g6_12_polygons_overlap_against_exact_ear_clip_area_oracle():
    """polygons_overlap 对精确 oracle（精确耳切 + Sutherland–Hodgman 精确面积，与库的判据不同路）：
    随机 2-opt 多边形 P × 小方块 Q，Q 的中心取 P 的包围盒内随机点**以及 interior_point(P)**（旧实现的软肋），
    方块边长 1e-3——大量样本落在"分离但离得很近"与"真相交"的边界两侧。"""
    rng = random.Random(12)
    wrong, n = [], 0
    while n < 600:
        P = _random_simple_polygon(rng, rng.randint(5, 9))
        if P is None:
            continue
        n += 1
        centres = [interior_point(P)] + [(rng.uniform(0, 1), rng.uniform(0, 1)) for _ in range(3)]
        for cx, cy in centres:
            h = 5e-4
            Q = [(cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h)]
            truth = _exact_overlap(P, Q)
            got = polygons_overlap(P, Q, 0.0)
            if (got == 1) != truth:
                wrong.append((P, (cx, cy), got, truth))
    assert wrong == [], (len(wrong), wrong[:1])
