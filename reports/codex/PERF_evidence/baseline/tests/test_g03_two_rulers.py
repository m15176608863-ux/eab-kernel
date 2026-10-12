"""G6 第四轮两把尺反例的保留回归集。

E5a 的凸 G0 已删除所有分辨带/细条/low_e 豁免，按给定坐标精确比较；
本文件旧参数和断言均保留。新增零豁免和第五轮原始输入门见 test_g03_e5a。
本文件还调用未全量精确迁移的一般相交入口，其通过不等于该入口已精确。
"""

from __future__ import annotations

import math
import random

import pytest

from eab.kernel3d.g03 import g0_convex3
from eab.kernel3d.geom3 import Polyhedron, box, convex_hull_3d, merge_coplanar, polyhedra_overlap, tetra
from eab.margin import INSIDE, PENETRATING, body_distance, contact_resolution, effective_geom_tol, inflated_membership


def _quat(seed: int):
    rng = random.Random(9100 + seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def _move(P: Polyhedron, R, t=(0.0, 0.0, 0.0), s: float = 1.0) -> Polyhedron:
    return Polyhedron([tuple(t[i] + s * sum(R[i][j] * p[j] for j in range(3)) for i in range(3)) for p in P.verts], list(P.faces))


I3 = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def _yaw(P: Polyhedron, th: float) -> Polyhedron:
    c, s = math.cos(th), math.sin(th)
    return Polyhedron([(c * x - s * y, s * x + c * y, z) for x, y, z in P.verts], list(P.faces))


def _prism(section_yz, x0: float, x1: float) -> Polyhedron:
    n = len(section_yz)
    verts = [(x0, y, z) for y, z in section_yz] + [(x1, y, z) for y, z in section_yz]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    P = Polyhedron(verts, faces)
    if P.volume() < 0.0:
        P = Polyhedron(verts, [tuple(reversed(f)) for f in faces])
    assert P.manifold_issues() == []
    return P


def _ridge_pair(h: float):
    """展示算例的脊 + 尖锥，脊高 h 一路扫到坐标舍入以下。"""
    sec = [(-1.0, -1.0), (1.0, -1.0), (1.0, 0.0), (0.0, h), (-1.0, 0.0)]
    B = _prism(sec, -2.0, 2.0)
    A = convex_hull_3d([(0.3, 0.0, h + 0.05)] + [(0.3 + 0.3 * math.cos(t), 0.3 * math.sin(t), h + 1.05)
                                                 for t in (0.1, 2.1943951, 4.2887902)])
    return A, B


def _ok(r, where):
    assert r.passed, (where, r.hull_vertex_mismatch, r.hull_vertices, r.e_vertices, r.e_vertices_ambiguous,
                      r.facet_symmetric_diff[:3], r.facet_ambiguous, r.facet_local_dropped, r.mismatches[:2])


@pytest.mark.parametrize("h", [1e-3, 1e-6, 1e-9, 1e-10, 3e-11, 1e-11, 5e-12, 2e-12, 1e-12, 5e-13, 1e-13])
def test_ridge_height_below_the_hull_tolerance_is_ambiguous_not_a_mismatch(h):
    """脊高 h 在 (fl, 1e-12·L) 之间：局部锥规则证实的两个真 E 顶点被凸包按 1e-12·L 压平——旧版只豁免凸包侧多出的顶点，
    局部侧多出的记失配（passed=False）；现在两边对称地按"高出凸包 ≤ 4·ptol"记说不清。h 大时没有歧义。"""
    A, B = _ridge_pair(h)
    r = g0_convex3(A, B, samples=12, seed=1)
    _ok(r, h)
    if h >= 1e-6:
        assert r.e_vertices_ambiguous == 0 and r.facet_ambiguous == 0, (h, r.e_vertices_ambiguous, r.facet_ambiguous)


@pytest.mark.parametrize("yaw", [0.0, 3e-6, 1e-5])
def test_roof_prisms_ridge_over_ridge_with_a_tiny_yaw(yaw):
    """两个凸屋脊棱柱（截面 (−1,−1),(1,−1),(1,0),(0,0.3),(−1,0)，长 4）：B 固定，A 翻转后脊对脊悬在 0.01 上方、偏航 yaw，原点、单位尺度。
    偏航把 A 端面坡棱挪动 ~7e-12（低于凸包的 eps_d 9e-12 又高于 4·fl）：旧版支撑带按 4·fl 判 → hull_anomaly / local_only；
    说不清的宽种子集只丢局部标签不丢凸包侧的孪生三角 → hull_only。正确的凸对上门必须通过。"""
    sec = [(-1.0, -1.0), (1.0, -1.0), (1.0, 0.0), (0.0, 0.3), (-1.0, 0.0)]
    B = _prism(sec, -2.0, 2.0)
    A0 = Polyhedron([(x, y, -z + 0.3 + 0.01 + 0.3) for x, y, z in B.verts], [tuple(reversed(f)) for f in B.faces])
    assert A0.volume() > 0.0 and A0.manifold_issues() == []
    A = _yaw(A0, yaw) if yaw else A0
    r = g0_convex3(A, B, samples=12, seed=3)
    _ok(r, yaw)


def _chamfered_box(e: float) -> Polyhedron:
    pts = [p for p in box(half=(0.5, 0.5, 0.5)).verts if p != (0.5, 0.5, 0.5)]
    pts += [(0.5 - e, 0.5, 0.5), (0.5, 0.5 - e, 0.5), (0.5, 0.5, 0.5 - e)]
    return merge_coplanar(convex_hull_3d(pts))


@pytest.mark.parametrize("tmag", [0.0, 100.0, 1e3])
def test_a_micro_chamfer_facet_is_not_mistaken_for_a_sliver_under_translation(tmag):
    """单位方块截去一角（倒角三角边 1.4e-6，7 个面）+ 四面体尖端在该角外 0.1：原点通过；旧版平移到 |t| ≥ 100 后凸包的倒角三角
    面积 1.7e-12 低于全局 area_tol（2·fl·L）被当碎片跳过 → local_only VF，相邻三角再凑出 E 上没有的 facet → hull_only。
    细条判据改按三角自己的高，平面拟合基点改取最远点对。"""
    B0 = _chamfered_box(1e-6)
    assert len(B0.faces) == 7
    r3 = 1.0 / math.sqrt(3.0)
    apex = (0.5 + 0.1 * r3, 0.5 + 0.1 * r3, 0.5 + 0.1 * r3)
    A0 = tetra(apex, (apex[0] + 0.6, apex[1] + 0.1, apex[2] + 0.2), (apex[0] + 0.1, apex[1] + 0.7, apex[2] + 0.3),
               (apex[0] + 0.2, apex[1] + 0.2, apex[2] + 0.8))
    t = (0.6 * tmag, -0.48 * tmag, 0.64 * tmag)
    A, B = _move(A0, I3, t), _move(B0, I3, t)
    assert polyhedra_overlap(A, B) == -1
    r = g0_convex3(A, B, samples=12, seed=2)
    _ok(r, tmag)
    # 平移后凸包侧允许把倒角三角（1.4 µm，法向噪声 fl·周长/面积 ≈ 3e-5 rad @ 1e3）记为说不清，但不许丢：清楚 + 说不清 + 退化
    # 的 facet 数不少于原点的严格 facet 数减一（细条判据按三角自己的高之后，倒角三角不再被当碎片跳过——该修补与按 eps 的
    # 支撑带互为冗余：只撤细条判据时门仍绿，如实记）
    r0 = g0_convex3(A0, B0, samples=12, seed=2)
    assert r0.facet_ambiguous == 0 and r0.facet_global == 20, (r0.facet_global, r0.facet_ambiguous)
    assert r.facet_global + r.facet_ambiguous + r.facet_degenerate >= r0.facet_global - 1,         (tmag, r.facet_global, r.facet_ambiguous, r.facet_degenerate)


@pytest.mark.parametrize("yaw,rot", [(1e-9, 7), (5e-12, 0), (1e-9, 0), (1e-7, 11)])
def test_stacked_unit_boxes_with_a_sub_resolution_yaw_pass_or_say_ambiguous(yaw, rot):
    """两个 1 m 方块叠放（间隙 0.1）、偏航 1e-9 … 5e-12、一般旋转、原点：真顶点高 θ/2 ≫ 1e-12·L 却低于凸包放大后的 1e-10·L，
    被压平——旧版票三把局部侧多出的 8 个顶点记失配（同一对平移到 1e3 却通过：刚体运动不变性破）。现在记说不清。"""
    A0 = _yaw(box(center=(0.0, 0.0, 1.1), half=(0.5, 0.5, 0.5)), yaw)
    B0 = box(half=(1.0, 1.0, 0.5))
    R = _quat(rot) if rot else I3
    r = g0_convex3(_move(A0, R), _move(B0, R), samples=12, seed=0)
    _ok(r, (yaw, rot))


def _truncated_cube(e: float) -> Polyhedron:
    pts = [p for p in box(half=(0.5, 0.5, 0.5)).verts if p != (0.5, 0.5, -0.5)]
    pts += [(0.5 - e, 0.5, -0.5), (0.5, 0.5 - e, -0.5), (0.5, 0.5, -0.5 + e)]
    return merge_coplanar(convex_hull_3d(pts))


@pytest.mark.parametrize("rot,tmag,s", [(0, 0.0, 1.0), (0, 1e5, 1.0), (7, 1e3, 1.0), (0, 1e5, 1e3)])
def test_truncated_corner_cube_yawed_on_a_box_is_invariant(rot, tmag, s):
    """单位方块截去底角（三条 1.4 µm 的棱）、偏航 1e-3、叠在单位方块上方 0.1：原点处三票全绿；旧版平移到 1e5（或 R7 + 1e3、×1e3 后 1e5）
    报 local_only EE——含 EE 棱的凸包 facet 的种子集成了小三角或五边形面，棱×棱候选只取一根最远点对、真 EE 的候选没生成。
    现在候选取种子集内全部棱对、且必须落在三角法向的噪声内。"""
    A0 = _yaw(_truncated_cube(1e-6), 1e-3).translated((0.0, 0.0, 1.1))
    B0 = box(half=(1.0, 1.0, 0.5))
    R = _quat(rot) if rot else I3
    t = (0.6 * tmag, -0.48 * tmag, 0.64 * tmag)
    r = g0_convex3(_move(A0, R, t, s), _move(B0, R, t, s), samples=12, seed=5)
    _ok(r, (rot, tmag, s))


def test_small_box_just_outside_the_corner_of_a_huge_box_is_separated_not_a_sentinel():
    """1 m 方块放在 1 km 方块顶面角点之外：角点离顶面平面 0.8·gtol、面内越出棱 0.8·gtol，真间距 1.13·gtol > ctol——
    谓词"起点在面平面上"的捷径曾用盒带（平面距 ≤ eps_t 且面内 ≤ tol）答相触、裕度层升成哨兵（三个入口答"已违约"）；
    现在按欧氏带答分离，body_distance 给出真实间距。"""
    B = box(half=(500.0, 500.0, 500.0))
    A0 = box(center=(500.0 + 0.5, 0.0, 500.0 + 0.5), half=(0.5, 0.5, 0.5))
    g = effective_geom_tol(A0, B)
    A = A0.translated((0.8 * g, 0.0, 0.8 * g))
    ctol = contact_resolution(A, B)
    truth = math.hypot(0.8 * g, 0.8 * g)
    assert truth > ctol
    assert polyhedra_overlap(A, B, g) == -1
    d, lab = body_distance(A, B)
    assert lab != (PENETRATING,) and d == pytest.approx(truth, rel=1e-6), (d, lab, truth, ctol)
    assert inflated_membership(A, B, delta=0.0) != INSIDE


def test_a_plate_thinner_than_the_coordinate_resolution_fails_loudly_with_the_reason():
    """The original thin engineering-coordinate plate is now exactly decidable.

    Independent integer tetra SAT proves separation; the legacy expected noise-
    resolution exception is replaced by the strictly stronger correct answer.
    Origin and engineering-coordinate inputs remain unchanged.
    """
    A0 = _yaw(box(center=(0.0, 0.0, 1e-3 + 1e-6 + 0.5e-9), half=(0.7e-3, 0.6e-3, 0.5e-9)), 0.3)
    B0 = box(half=(1e-3, 1e-3, 1e-3))
    R = _quat(3)
    t = (0.6e5, -0.48e5, 0.64e5)
    A, B = _move(A0, R, t), _move(B0, R, t)
    from e5a2_surface_oracle import star_overlap
    assert star_overlap(A,B)==-1
    assert polyhedra_overlap(A,B)==-1
    d, lab=body_distance(A,B)
    assert d > 0 and lab != (PENETRATING,)
    # 同一几何在原点处正常：分离 1e-6
    assert polyhedra_overlap(A0, B0) == -1
    d, _ = body_distance(A0, B0)
    assert d == pytest.approx(1e-6, rel=1e-6)
