"""M2 首入的第二批门：凹体（台阶）上的首入与"更早已相触"自校验的牙、退化族平面簇与并列集容差的牙、"平面已在身后"筛选的牙。
这些门对应首批 11 个突变体里逃逸的 6 个（见 72bb3b9 提交说明）——每颗牙的突变体在 scratchpad/m03/mut_m2b.py 里复跑。"""

from __future__ import annotations

import math
from fractions import Fraction as F

import pytest

from eab.kernel3d.entrance3 import first_entrance3, first_entrance_brute, merge_degenerate
from eab.kernel3d.geom3 import Polyhedron, box, convex_hull_3d, polyhedra_overlap

SLAB = box(half=(1.0, 1.0, 0.5))


def _prism(section_xz, y0: float, y1: float) -> Polyhedron:
    """把 (x, z) 平面上的简单多边形沿 y 拉伸成棱柱（可以凹）。面朝向按体积符号统一成外法向。"""
    n = len(section_xz)
    verts = [(x, y0, z) for x, z in section_xz] + [(x, y1, z) for x, z in section_xz]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]          # 两端盖与侧面绕向一致（每条棱被两张面反向遍历）
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    P = Polyhedron(verts, faces)
    if P.volume() < 0.0:
        P = Polyhedron(verts, [tuple(reversed(f)) for f in faces])
    assert P.volume() > 0.0 and P.manifold_issues() == [], P.manifold_issues()
    return P


# 台阶：下踏面 z = 0.5（x ∈ [1, 2]）、竖板 x = 1（z ∈ [0.5, 1]）、上踏面 z = 1（x ∈ [0, 1]）；y ∈ [−1, 1]
STEP = _prism([(0.0, 0.0), (2.0, 0.0), (2.0, 0.5), (1.0, 0.5), (1.0, 1.0), (0.0, 1.0)], -1.0, 1.0)


def test_step_prism_is_concave_and_closed():
    assert STEP.volume() == pytest.approx(2.0 * 2.0 - 1.0 * 0.5 * 2.0, rel=1e-12)
    assert not STEP.is_convex()


def test_box_sliding_into_the_step_first_touches_the_riser():
    """方块从台阶右上方沿 (−1, 0, −0.5) 滑入：前缘左下角 (1.4, ·, 0.9) 在 t = 0.4 到达竖板 x = 1（z = 0.7 ∈ [0.5, 1]），
    比下踏面（t = 0.8，且届时 x = 0.6 已越过踏面）早。首入 = 面-面（A 的左面平行于竖板，两个下顶点在程），法向 +x。
    凹体上靠谓词裁决；oracle 是不经盖的 first_entrance_brute。"""
    A = box(center=(1.9, 0.0, 1.4), half=(0.5, 0.5, 0.5))
    d = (-1.0, 0.0, -0.5)
    e = first_entrance3(A, STEP, (0.0, 0.0, 0.0), d, t_max=3.0)
    assert e.kind == "entrance" and e.t == pytest.approx(0.4, abs=1e-12), (e.kind, e.t, e.label)
    assert e.normal == pytest.approx((1.0, 0.0, 0.0), abs=1e-12)
    assert e.label[0] == "FF" and len(e.members) == 2 and all(m[0] == "VF" for m in e.members), (e.label, e.members)
    bt = first_entrance_brute(A, STEP, (0.0, 0.0, 0.0), d, t_max=3.0, steps=600)
    assert bt == pytest.approx(e.t, abs=1e-8)


def test_an_earlier_entrance_missed_by_the_covers_is_detected_on_the_concave_step(monkeypatch):
    """"更早已相触"自校验的牙：把竖板上的全部盖（B 侧特征都落在 x = 1 平面上的 VF / EE）从枚举里删掉，剩下最早的在程候选是
    方块左上角在 t = 1.8 到达上踏面 z = 1（x = −0.4 ∈ [0, 1]）；它之前一个分辨步处两体早已相交（t = 0.4 起），
    first_entrance3 必须抛 RuntimeError，不许把 t = 1.8 当首入返回。凸对上不会出现这种位形（凸 E 的进入时刻是全部
    进入型 facet 时刻的最大者），所以这颗牙只能长在凹体上。"""
    import eab.kernel3d.entrance3 as E
    A = box(center=(1.9, 0.0, 1.4), half=(0.5, 0.5, 0.5))
    real = E.enumerate_covers3

    def on_riser(c, B):
        f = c.b_feature
        idx = [f[1]] if f[0] == "vertex" else (list(B.faces[f[1]]) if f[0] == "face" else [f[1], f[2]])
        return all(abs(B.verts[i][0] - 1.0) < 1e-12 for i in idx)

    def dropped(At, B, **kw):
        return [c for c in real(At, B, **kw) if not on_riser(c, B)]
    monkeypatch.setattr(E, "enumerate_covers3", dropped)
    with pytest.raises(RuntimeError, match="missed an earlier entrance"):
        first_entrance3(A, STEP, (0.0, 0.0, 0.0), (-1.0, 0.0, -0.5), t_max=3.0)


def test_degenerate_merge_keeps_parallel_planes_at_different_heights_apart():
    """平面簇容差的牙：宽方块坐在上踏面上、同时悬在下踏面上方 0.5——四个底顶点对两张同法向（+z）的踏面各给两个 VF，
    必须收成**两个** FF（各 2 个成员），不许把相距 0.5 的两张平面并成一张（旧突变体 ×1e6 就会并）。"""
    from eab.kernel3d.covers3 import enumerate_covers3
    A = box(center=(1.0, 0.0, 1.5), half=(1.0, 0.5, 0.5))          # 底面 z = 1：x ∈ [0, 1] 贴上踏面，x ∈ [1, 2] 悬在下踏面上方
    covs = [c for c in enumerate_covers3(A, STEP, window=float("inf"), tol=1e-9)
            if c.kind == "VF" and c.normal[2] > 0.5 and c.in_extent]
    assert len(covs) == 4, [(c.label(), round(c.gap, 6)) for c in covs]
    merged = merge_degenerate(A, STEP, covs)
    reps = sorted((rep, len(mem)) for rep, mem in merged)
    assert [r[0][0] for r in reps] == ["FF", "FF"] and [r[1] for r in reps] == [2, 2], reps


def test_tie_set_is_judged_at_the_predicate_resolution_not_wider():
    """并列集容差的牙：方块绕 x 转 1e-4 rad 下落，最低的一条棱先触地，另一条棱晚 ~1e-4 到——远超分辨率（~1e-9），
    并列集只许含那条棱的两个 VF（FE，2 个成员）；旧突变体把并列集放宽 1e6 倍就会把四个顶点都收进来、报成 FF。"""
    c, s = math.cos(1e-4), math.sin(1e-4)
    A0 = box(half=(0.5, 0.5, 0.5))
    A = Polyhedron([(x, c * y - s * z, s * y + c * z) for x, y, z in A0.verts], list(A0.faces)).translated((0.1, -0.2, 2.0))
    e = first_entrance3(A, SLAB, (0.0, 0.0, 0.0), (0.0, 0.0, -1.0))
    assert e.kind == "entrance" and e.label[0] == "FE", (e.label, e.members)
    assert len(e.members) == 2 and len(e.tied_labels) == 2, (e.members, e.tied_labels)


def test_a_facet_plane_already_behind_the_start_is_not_an_entrance():
    """"平面已在身后"筛选与"t* 处谓词须相触"核验的牙（两处互为冗余，同时撤回才会错）：倒置的方台（顶面大、底面小），小方块
    在顶面平面之下、顶面投影之内、斜侧面之外，沿 (−1, 0, −0.3) 向内下方运动。顶面 facet 的 n·d < 0 但其平面已在身后
    （gap = −0.6）：不筛掉就成了 t = 0 的候选、投影又落在顶面之内——只有谓词核验能拦住它。真首入在斜侧面上（t > 0），对 oracle。"""
    B = convex_hull_3d([(sx * 0.5, sy * 0.5, 0.0) for sx in (-1, 1) for sy in (-1, 1)]
                       + [(sx * 1.0, sy * 1.0, 1.0) for sx in (-1, 1) for sy in (-1, 1)])
    A = box(center=(0.95, 0.0, 0.3), half=(0.1, 0.1, 0.1))
    assert polyhedra_overlap(A, B) == -1
    d = (-1.0, 0.0, -0.3)
    e = first_entrance3(A, B, (0.0, 0.0, 0.0), d, t_max=2.0)
    bt = first_entrance_brute(A, B, (0.0, 0.0, 0.0), d, t_max=2.0, steps=800)
    assert e.kind == "entrance" and bt is not None and e.t == pytest.approx(bt, abs=1e-8), (e.kind, e.t, bt, e.label)
    assert e.t > 0.05 and e.normal[0] > 0.5, (e.t, e.normal)


# 两级踏面只差 1e-4 的台阶：下踏面 z = 1（x ∈ [1, 2]）、上踏面 z = 1 + 1e-4（x ∈ [0, 1]）
TINY_STEP = _prism([(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (1.0, 1.0), (1.0, 1.0 + 1e-4), (0.0, 1.0 + 1e-4)], -1.0, 1.0)


def test_tie_set_on_a_tiny_step_is_judged_at_the_predicate_resolution():
    """并列集容差的牙（第二颗）：宽方块跨在两级踏面上方下落，先触上踏面（两个 VF），下踏面的两个 VF 晚 1e-4 到——远超分辨率
    （~2e-9），并列集只许含上踏面的两个；把并列集放宽 1e6 倍就会把下踏面的也收进来。退化族平面簇也不许把相差 1e-4 的两张踏面并成一张。"""
    A = box(center=(1.0, 0.0, 2.0), half=(1.0, 0.5, 0.5))
    e = first_entrance3(A, TINY_STEP, (0.0, 0.0, 0.0), (0.0, 0.0, -1.0), t_max=3.0)
    assert e.kind == "entrance" and e.t == pytest.approx(0.5 - 1e-4, abs=1e-12), (e.kind, e.t)      # 底面 1.5 → 上踏面 1.0001
    assert e.label[0] == "FF" and len(e.members) == 2, (e.label, e.members)
    # 并列集 = 上踏面的两个 VF + A 底棱与上踏面两条 y 向棱交叉的四个边界态 EE（同一接触平面）；下踏面的 VF 不许进来
    vf = [lab for lab in e.tied_labels if lab[0] == "VF"]
    assert len(vf) == 2 and {lab[2] for lab in vf} == {e.members[0][2]}, e.tied_labels
    assert all(lab[0] in ("VF", "EE") for lab in e.tied_labels), e.tied_labels


# V 形浅槽：两坡面坡度 0.5，法向夹 2·atan(0.5) ≈ 0.927 rad（< 1 rad）；槽底 z = 1.0，两侧台面 z = 1.5
TROUGH = _prism([(-2.0, 0.0), (2.0, 0.0), (2.0, 1.5), (1.0, 1.5), (0.0, 1.0), (-1.0, 1.5), (-2.0, 1.5)], -1.0, 1.0)


def test_degenerate_merge_keeps_two_trough_slopes_apart():
    """法向分组的门：方块坐在 V 形浅槽里，两条底棱各贴一个坡面（四个底顶点各在自己的坡面上、间隙 0），两坡面法向夹 0.927 rad，
    必须收成**两个** FE（A 的底棱平行于各自的坡面，各 2 个成员），不是一个 FF。注：把法向分组容差放宽到 1 rad 的突变体在这里
    仍给两个 FE——两张不平行的面沿同一法向的平面偏移几乎总是不同，平面簇这一步把它们分开了；分组容差与平面簇互为冗余，
    这一点如实记在 merge_degenerate 的文档里。"""
    from eab.kernel3d.covers3 import enumerate_covers3
    A = box(center=(0.0, 0.0, 1.45), half=(0.3, 0.3, 0.3))              # 底角 (±0.3, ±0.3, 1.15) 恰在坡面上
    # The original binary64 bottom 1.15 is strictly below 1+Fraction(.3)/2.
    # Independent slope inequalities certify real interior overlap, not a
    # zero-band contact. Preserve this original input and all cover/merge gates.
    half = F(A.verts[1][0])
    bottom = F(A.verts[0][2])
    depth = F(1)+half/2-bottom
    assert depth > 0
    wx, wz = half-depth, bottom+depth/4
    assert -half < wx < half and bottom < wz < F(A.verts[4][2])
    assert 0 < wx < 1 and 0 < wz < 1+wx/2  # y=0 is interior to both prisms
    assert polyhedra_overlap(A, TROUGH) == 1
    # Keep the former analytic exact-contact proposition as an extra track.
    contact = Polyhedron([(F(x), F(y), F(z)+depth) for x, y, z in A.verts], list(A.faces))
    assert min(p[2] for p in contact.verts) == 1+half/2
    assert polyhedra_overlap(contact, TROUGH) == 0
    covs = [c for c in enumerate_covers3(A, TROUGH, window=1e-9, tol=1e-9) if c.kind == "VF" and c.in_extent]
    assert len(covs) == 4, [(c.label(), round(c.gap, 6)) for c in covs]
    merged = merge_degenerate(A, TROUGH, covs)
    kinds = sorted((rep[0], len(mem)) for rep, mem in merged)
    assert kinds == [("FE", 2), ("FE", 2)], merged
    e = first_entrance3(A.translated((0.0, 0.0, 0.2)), TROUGH, (0.0, 0.0, 0.0), (0.0, 0.0, -1.0))
    assert e.kind == "entrance" and e.t == pytest.approx(0.2, abs=1e-12) and e.label[0] == "FE" and len(e.members) == 2
    assert len(e.tied_labels) == 4, e.tied_labels                         # 两坡面同时触及：并列集含四个 VF
