"""三维盖枚举与 G0 三票自证门。"""

import random

import pytest

from eab.kernel3d.covers3 import (edge_arc_contains, ee_cover, enumerate_covers3, fv_cover,
                                  local_facets3, membership_convex3, vertex_cone_contains, vf_cover)
from eab.kernel3d.g03 import g0_convex3
from eab.kernel3d.geom3 import (box, convex_hull_3d, neg, norm, polyhedra_overlap, sub, tetra, unit)


def test_vertex_cone_of_box_corner():
    b = box(half=(1.0, 1.0, 1.0))
    # 顶点 6 = (+1,+1,+1)：法锥是第一象限方向
    assert vertex_cone_contains(b, 6, unit((1.0, 1.0, 1.0))) == 1
    assert vertex_cone_contains(b, 6, (1.0, 0.0, 0.0)) == 0          # 锥的面上（棱方向垂直）
    assert vertex_cone_contains(b, 6, unit((-1.0, 1.0, 1.0))) == -1


def test_edge_arc_of_box_edge():
    b = box(half=(1.0, 1.0, 1.0))
    # 棱 (5,6) = x=+1, y 从 -1 到 +1? 取一条 +x/+z 交界的棱
    for e in b.edges():
        fs = b.edge_faces(e)
        ns = [b.face_normal(f) for f in fs]
        bis = unit(tuple(ns[0][i] + ns[1][i] for i in range(3)))
        assert edge_arc_contains(b, e, bis) == 1, (e, bis)
        assert edge_arc_contains(b, e, ns[0]) == 0                    # 弧端点
        assert edge_arc_contains(b, e, neg(bis)) == -1


def test_stacked_boxes_give_four_vf_covers_like_bdda3d_cb2():
    """bdda3d 的 cb2：上块坐落下块顶面。上块四个底角各一个 VF 盖，间隙 = 间距。

    轴对齐使 −n_f 恰好落在顶点法锥的**边界**上 → strict=False，这是命题 4 的 FF 退化情形
    （面-面接触），不是缺陷；DDA/bdda3d 正是用这 4 个 n-p 入口表达面-面接触。
    """
    lower = box(center=(0.0, 0.0, -1.0), half=(2.0, 2.0, 1.0))      # 顶面 z=0
    gap = 0.05
    upper = box(center=(0.0, 0.0, 1.0 + gap), half=(1.0, 1.0, 1.0))  # 底面 z=gap
    covs = [c for c in enumerate_covers3(upper, lower, window=1.0, tol=1e-12) if c.in_extent]
    vf = [c for c in covs if c.kind == "VF"]
    assert len(vf) == 4, [c.label() for c in covs]
    assert {c.a_feature[1] for c in vf} == {0, 1, 2, 3}              # 上块四个底角
    for c in vf:
        assert abs(c.gap - gap) < 1e-12
        assert c.normal is not None and abs(c.normal[2] - 1.0) < 1e-12   # 法向 +z（B→A）
        assert not c.strict                                          # 退化：法向在锥边界上
    assert not [c for c in covs if c.kind in ("EE", "FV")]


def test_tilted_vertex_face_cover_is_strict():
    """把上块绕两轴转一点，顶点-面就成为真正的严格 facet 盖（相对内部条件成立）。"""
    from math import cos, sin
    lower = box(center=(0.0, 0.0, -1.0), half=(3.0, 3.0, 1.0))
    t = tetra((0.0, 0.0, 0.35), (0.9, 0.1, 1.2), (-0.3, 0.95, 1.15), (-0.25, -0.5, 1.3))
    covs = [c for c in enumerate_covers3(t, lower, window=1.0, tol=1e-12) if c.in_extent]
    strict_vf = [c for c in covs if c.kind == "VF" and c.strict]
    assert len(strict_vf) == 1, [(c.kind, c.strict, round(c.gap, 4)) for c in covs]
    c = strict_vf[0]
    assert abs(c.gap - 0.35) < 1e-12 and abs(c.normal[2] - 1.0) < 1e-12


def test_crossing_edge_edge_cover():
    """两根互相垂直的杆交叉：facet 盖全是交叉棱-棱，间隙 = 竖向间距。

    杆轴对齐 → 候选法向 ±ẑ 落在两条棱弧的端点上（strict=False，平行棱-棱退化族）。
    转一个角度后同一对棱给出严格盖，见下一个测试。
    """
    lower = box(center=(0.0, 0.0, -0.5), half=(3.0, 0.2, 0.5))      # 沿 x，顶面 z=0
    upper = box(center=(0.0, 0.0, 0.5 + 0.1), half=(0.2, 3.0, 0.5))  # 沿 y，底面 z=0.1
    covs = [c for c in enumerate_covers3(upper, lower, window=0.5, tol=1e-12) if c.in_extent]
    ee = [c for c in covs if c.kind == "EE"]
    assert len(ee) == 4, [(c.kind, round(c.gap, 4)) for c in covs]
    assert all(abs(c.gap - 0.1) < 1e-12 for c in ee)
    assert not any(c.strict for c in ee)


def test_wedge_on_wedge_gives_strict_crossing_edge_cover():
    """两个楔形交叉：下楔顶棱沿 y、上楔底棱沿 x，坡面 45° → ẑ 严格落在两条棱弧内部。

    轴对齐的杆-杆交叉给不出严格 EE（两棱都水平 ⇒ 叉积恒为 ±ẑ，正好是弧端点）；
    要让 EE 严格，必须让棱的相邻面把候选法向夹在中间。
    """
    h = 0.17
    lower = convex_hull_3d([(0.0, -1.0, 0.0), (0.0, 1.0, 0.0),          # 顶棱沿 y
                            (-1.0, -1.0, -1.0), (1.0, -1.0, -1.0),
                            (-1.0, 1.0, -1.0), (1.0, 1.0, -1.0)])
    upper = convex_hull_3d([(-1.0, 0.0, h), (1.0, 0.0, h),              # 底棱沿 x
                            (-1.0, -1.0, h + 1.0), (-1.0, 1.0, h + 1.0),
                            (1.0, -1.0, h + 1.0), (1.0, 1.0, h + 1.0)])
    covs = [c for c in enumerate_covers3(upper, lower, window=0.6, tol=1e-12) if c.in_extent]
    ee = [c for c in covs if c.kind == "EE" and c.strict]
    assert ee, [(c.kind, c.strict, round(c.gap, 4)) for c in covs]
    assert min(abs(c.gap - h) for c in ee) < 1e-12
    best = min(ee, key=lambda c: abs(c.gap - h))
    assert abs(best.normal[2] - 1.0) < 1e-12                            # 法向 +z（B→A）
    assert abs(best.params[0] - 0.5) < 1e-9 and abs(best.params[1] - 0.5) < 1e-9   # 两棱中点相碰


def test_facet_count_matches_minkowski_theory_for_boxes():
    # 两个轴对齐方块：E 是方块，六个 facet，全是 FF 退化（平行面）→ 严格 facet 集合应为空
    a, b = box(half=(1.0, 1.0, 1.0)), box(half=(2.0, 2.0, 2.0))
    assert local_facets3(a, b, 1e-12) == set()
    # 一般位置：四面体 vs 方块，facet 数 = VF + FV + EE 的严格计数，应等于 E 的面数
    t = tetra((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    facets = local_facets3(t, b, 1e-12)
    hull = convex_hull_3d([sub(bb, aa) for aa in t.verts for bb in b.verts])
    assert hull.is_convex(1e-9)
    # hull 是三角化的：把共面三角按法向归并后，面数应等于"严格 facet + 退化 facet"之和。
    # 四面体 vs 轴对齐方块里退化项来自方块三对平行面 → 严格数 = 归并面数 − 退化数。
    norms = set()
    for fi in range(len(hull.faces)):
        n = hull.face_normal(fi)
        norms.add(tuple(round(x, 7) + 0.0 for x in n))
    # 退化数独立地数：方块面法向 n 与四面体某面法向反平行（FF）的个数。
    tn = {tuple(round(x, 7) + 0.0 for x in t.face_normal(fi)) for fi in range(len(t.faces))}
    bn = {tuple(round(x, 7) + 0.0 for x in b.face_normal(fi)) for fi in range(len(b.faces))}
    degenerate = {n for n in bn if tuple(-x + 0.0 for x in n) in tn}
    assert len(norms) == 10 and len(degenerate) == 3
    # 审查 C23：原先只断言 6 <= len <= 10，丢一个 facet 也绿。改成注释里写的恒等式。
    assert len(facets) == len(norms) - len(degenerate) == 7


@pytest.mark.parametrize("seed", range(6))
def test_g0_convex3_random_pairs(seed):
    rng = random.Random(seed)

    def rnd_hull(n: int, s: float):
        pts = [(rng.uniform(-s, s), rng.uniform(-s, s), rng.uniform(-s, s)) for _ in range(n)]
        return convex_hull_3d(pts)

    A = rnd_hull(7, rng.uniform(0.5, 1.5))
    B = rnd_hull(7, rng.uniform(0.5, 1.5))
    rep = g0_convex3(A, B, samples=140, seed=seed)
    assert rep.samples > 60, rep
    assert rep.hull_vertex_mismatch == 0, (rep.hull_vertices, rep.e_vertices)
    assert rep.mismatches == [], rep.mismatches[:3]
    # 票二（审查 C23/C27：此前只存计数、从不比较）
    assert rep.facet_symmetric_diff == [], rep.facet_symmetric_diff[:3]
    assert rep.facet_local == rep.facet_global
    assert rep.passed


def test_g0_gate_has_teeth_flipped_normals_are_caught(monkeypatch):
    rng = random.Random(3)
    A = convex_hull_3d([(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(8)])
    B = box(half=(0.7, 0.9, 1.1))
    assert g0_convex3(A, B, samples=120, seed=1).passed
    import eab.kernel3d.covers3 as cv
    orig = cv.Polyhedron.face_normal
    monkeypatch.setattr(cv.Polyhedron, "face_normal", lambda self, fi: neg(orig(self, fi)))
    assert not g0_convex3(A, B, samples=120, seed=1).passed
