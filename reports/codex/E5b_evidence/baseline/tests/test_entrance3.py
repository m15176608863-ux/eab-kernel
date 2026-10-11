"""M2 · 三维首入（命题 7）的门：闭式真值 + 不经盖的 oracle（纪律 A）+ 刚体运动不变（纪律 F）+ 集值点如实报出。"""

from __future__ import annotations

import math
import random
from fractions import Fraction as F

import pytest

from eab.kernel3d.entrance3 import first_entrance3, first_entrance_brute, merge_degenerate, shortest_exit3
from eab.kernel3d.geom3 import Polyhedron, box, convex_hull_3d, dot, polyhedra_overlap, sub

Z = (0.0, 0.0, 1.0)


def _rot(P: Polyhedron, R) -> Polyhedron:
    return Polyhedron([tuple(sum(R[i][j] * p[j] for j in range(3)) for i in range(3)) for p in P.verts], list(P.faces))


def _rx(th):
    c, s = math.cos(th), math.sin(th)
    return ((1.0, 0.0, 0.0), (0.0, c, -s), (0.0, s, c))


def _ry(th):
    c, s = math.cos(th), math.sin(th)
    return ((c, 0.0, s), (0.0, 1.0, 0.0), (-s, 0.0, c))


def _mat(R1, R2):
    return tuple(tuple(sum(R1[i][k] * R2[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def _quat(seed: int):
    rng = random.Random(seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def _apply(R, v):
    return tuple(sum(R[i][j] * v[j] for j in range(3)) for i in range(3))


SLAB = box(half=(1.0, 1.0, 0.5))                 # B：顶面 z = 0.5


# ---------------------------------------------------------------- 闭式：面-面、棱-面、顶点-面

@pytest.mark.parametrize("speed", [1.0, 2.0, 0.25])
def test_box_dropping_onto_a_face_is_a_face_face_entrance_with_four_members(speed):
    """A 的底面平行于 B 的顶面、从 0.3 上方沿 −z 下落：t* = 0.3/speed，法向 +z，退化族 FF 展开成 4 个 VF（DDA 的 4 个 np 入口）。"""
    A = box(center=(0.2, 0.1, 1.3), half=(0.5, 0.5, 0.5))
    e = first_entrance3(A, SLAB, (0.0, 0.0, 0.0), (0.0, 0.0, -speed))
    assert e.kind == "entrance"
    assert e.t == pytest.approx(0.3 / speed, abs=1e-12)
    assert e.normal == pytest.approx(Z, abs=1e-12)
    assert e.label[0] == "FF" and len(e.members) == 4 and all(m[0] == "VF" for m in e.members), (e.label, e.members)
    assert e.point_b[2] == pytest.approx(0.5, abs=1e-12) and abs(e.gap) <= 1e-12
    assert set(e.members) <= set(e.tied_labels)
    bt = first_entrance_brute(A, SLAB, (0.0, 0.0, 0.0), (0.0, 0.0, -speed), t_max=2.0 / speed)
    assert bt == pytest.approx(e.t, abs=1e-8)


def test_a_tilted_box_lands_on_its_lowest_edge_then_its_lowest_corner():
    """绕 x 转 0.3 rad：最低的是一条棱 → FE（棱平行于面），两个 VF 成员；再绕 y 转 0.2 rad：最低的是一个顶点 → 单个 VF。
    t* 的闭式 = (A 最低顶点的 z − 0.5)/|d_z|，法向都是 +z。"""
    A0 = box(center=(0.0, 0.0, 0.0), half=(0.5, 0.5, 0.5))
    for R, kind, n_members in ((_rx(0.3), "FE", 2), (_mat(_ry(0.2), _rx(0.3)), "VF", 1)):
        A = _rot(A0, R).translated((0.1, -0.2, 2.0))
        zmin = min(p[2] for p in A.verts)
        d = (0.05, 0.02, -1.0)
        e = first_entrance3(A, SLAB, (0.0, 0.0, 0.0), d)
        assert e.kind == "entrance"
        assert e.t == pytest.approx((zmin - 0.5) / 1.0, abs=1e-12)
        assert e.normal == pytest.approx(Z, abs=1e-12)
        assert e.label[0] == kind and len(e.members) == n_members, (kind, e.label, e.members, e.tied_labels)
        bt = first_entrance_brute(A, SLAB, (0.0, 0.0, 0.0), d, t_max=3.0)
        assert bt == pytest.approx(e.t, abs=1e-8)


def test_corner_onto_corner_is_a_set_valued_point_and_is_reported_as_such():
    """A 的一个底角正落到 B 的一个顶角上：VF（A 顶点, B 顶面）与 FV（A 底面, B 顶点）在同一时刻同时在程（法向都是 +z），
    另有两条交叉棱的 EE 边界态；并列集必须如实报出，代表盖由枚举序裁决。"""
    A = box(center=(1.5, 1.5, 1.3), half=(0.5, 0.5, 0.5))      # 底角 (1, 1, 0.8) 在 B 顶角 (1, 1, 0.5) 正上方
    e = first_entrance3(A, SLAB, (0.0, 0.0, 0.0), (0.0, 0.0, -1.0))
    assert e.kind == "entrance" and e.t == pytest.approx(0.3, abs=1e-12)
    assert e.normal == pytest.approx(Z, abs=1e-12)
    kinds = {lab[0] for lab in e.tied_labels}
    assert {"VF", "FV"} <= kinds, e.tied_labels
    assert e.point_a == pytest.approx((1.0, 1.0, 0.5), abs=1e-12) or e.point_b == pytest.approx((1.0, 1.0, 0.5), abs=1e-12)


def test_ray_that_misses_gives_none_and_t_max_is_honoured():
    A = box(center=(0.2, 0.1, 1.3), half=(0.5, 0.5, 0.5))
    assert first_entrance3(A, SLAB, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)).kind == "none"
    assert first_entrance3(A, SLAB, (0.0, 0.0, 0.0), (0.0, 0.0, -1.0), t_max=0.2).kind == "none"
    assert first_entrance3(A, SLAB, (0.0, 0.0, 0.0), (0.0, 0.0, -1.0), t_max=0.3).kind == "entrance"


# ---------------------------------------------------------------- 已侵入：最短出口

def test_penetrating_start_takes_the_shallowest_exit():
    """A 从上方压进 B 0.1：最浅出口是 +z（FF，4 个 VF），深度 0.1；侧向的 facet 间隙 −0.5 / −1.9 不是最短出口。"""
    A = box(center=(0.0, 0.0, 0.9), half=(0.5, 0.5, 0.5))
    e = first_entrance3(A, SLAB, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    assert e.kind == "exit" and e.t == 0.0
    assert e.normal == pytest.approx(Z, abs=1e-12) and e.gap == pytest.approx(-0.1, abs=1e-12)
    assert e.label[0] == "FF" and len(e.members) == 4
    # 沿出口法向退 |gap| 恰好分离；退一半仍相交
    assert polyhedra_overlap(A.translated((0.0, 0.0, -e.gap)), SLAB) <= 0
    assert polyhedra_overlap(A.translated((0.0, 0.0, -0.5 * e.gap)), SLAB) == 1
    assert shortest_exit3(A, SLAB, (0.0, 0.0, 0.0)).label == e.label


# ---------------------------------------------------------------- 随机凸对 × 随机射线：对不经盖的 oracle

@pytest.mark.parametrize("seed", range(24))
def test_first_entrance_agrees_with_the_predicate_only_oracle_on_random_convex_pairs(seed):
    """Original 24 seeds / 800-step supporting oracle remain. E5a2 additionally
    proves the continuous exact entry time by independent all-axis integer SAT.
    The returned floating translation need not land exactly on that boundary;
    its actual input-coordinate state is checked independently instead of
    silently thickening a separated rounded endpoint into contact.
    """
    from e5a2_entrance_oracle import assert_supporting_surface, convex_overlap, convex_ray_interval
    rng = random.Random(900 + seed)
    A = convex_hull_3d([(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(8)])
    B = convex_hull_3d([(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(8)])
    start = tuple(rng.uniform(-1, 1) + 4.0 * c for c in (rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)))
    d = tuple(-c / 4.0 + 0.1 * rng.gauss(0, 1) for c in start)        # 大致指向 B
    e = first_entrance3(A, B, start, d, t_max=8.0)
    bt = first_entrance_brute(A, B, start, d, t_max=8.0, steps=800)
    assert_supporting_surface(A.verts, A.faces)
    assert_supporting_surface(B.verts, B.faces)
    interval = convex_ray_interval(A.verts, B.verts, start, d, 8.0)
    if bt is None:
        assert interval is None, interval
        assert e.kind == "none", (e.kind, e.t, e.label)
        return
    assert e.kind == "entrance", (bt, e.kind, e.n_candidates)
    assert e.t == pytest.approx(bt, abs=2e-8), (e.t, bt, e.label)
    assert abs(e.gap) <= 1e-9
    assert interval is not None and interval[0] > 0
    exact_time = interval[0]
    assert e.t == pytest.approx(float(exact_time), abs=2e-8)
    rounded = A.translated(e.x)
    assert_supporting_surface(rounded.verts, rounded.faces)
    assert polyhedra_overlap(rounded, B) == convex_overlap(rounded.verts, B.verts)
    exact_shift = tuple(F(start[k])+exact_time*F(d[k]) for k in range(3))
    boundary = Polyhedron([tuple(F(p[k])+exact_shift[k] for k in range(3)) for p in A.verts], list(A.faces))
    assert convex_overlap(boundary.verts, B.verts) == 0
    assert polyhedra_overlap(boundary, B) == 0
    assert dot(e.normal, d) < 0.0                                       # 前进方向合上这个 facet


# ---------------------------------------------------------------- 纪律 F：刚体运动不变

@pytest.mark.parametrize("rot,tmag", [(3, 0.0), (3, 1e3), (5, 1e5), (0, 1e6)])
def test_first_entrance_is_invariant_under_rigid_motion(rot, tmag):
    A0 = _rot(box(half=(0.5, 0.5, 0.5)), _mat(_ry(0.2), _rx(0.3))).translated((0.1, -0.2, 2.0))
    d0 = (0.05, 0.02, -1.0)
    e0 = first_entrance3(A0, SLAB, (0.0, 0.0, 0.0), d0)
    R = _quat(rot) if rot else ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    T = tuple(tmag * c for c in (0.6, -0.48, 0.64))
    mv = lambda P: Polyhedron([tuple(T[i] + _apply(R, p)[i] for i in range(3)) for p in P.verts], list(P.faces))
    e = first_entrance3(mv(A0), mv(SLAB), (0.0, 0.0, 0.0), _apply(R, d0))
    assert e.kind == e0.kind == "entrance"
    assert abs(e.t - e0.t) <= 1e-9 * (1.0 + tmag * 1e-3), (e.t, e0.t)
    assert e.label == e0.label and e.members == e0.members, (e.label, e0.label)
    assert e.normal == pytest.approx(_apply(R, e0.normal), abs=1e-9)


# ---------------------------------------------------------------- 退化族合并本身

def test_merge_degenerate_keeps_unrelated_covers_apart():
    """两组不同法向的 VF 不许并成一个；同一 B 面上只有一个 VF 时不升格。"""
    from eab.kernel3d.covers3 import enumerate_covers3
    A = box(center=(0.2, 0.1, 1.0), half=(0.5, 0.5, 0.5))             # 正好贴在 B 顶面上
    covs = [c for c in enumerate_covers3(A, SLAB, window=1e-9, tol=1e-9) if c.kind in ("VF", "FV", "EE")]
    merged = merge_degenerate(A, SLAB, covs)
    reps = [m[0] for m in merged]
    assert sum(r[0] == "FF" for r in reps) == 1
    ff = next(m for m in merged if m[0][0] == "FF")
    assert len(ff[1]) == 4 and all(l[0] == "VF" for l in ff[1])


# ---------------------------------------------------------------- 自校验的牙：候选集漏了更早的首入必须抛错，不静默

def test_missing_candidate_is_detected_not_silently_skipped(monkeypatch):
    """把盖枚举里 B 顶面的全部 VF 删掉（模拟候选集不完备）：下落的方块真正的首入在 t = 0.3，剩下的候选最早是侧面（t 更大）——
    在它之前一个分辨步处两体已相交，first_entrance3 必须抛 RuntimeError，不许把更晚的候选当首入返回。"""
    import eab.kernel3d.entrance3 as E
    A = box(center=(0.2, 0.1, 1.3), half=(0.5, 0.5, 0.5))
    real = E.enumerate_covers3

    def dropped(At, B, **kw):
        return [c for c in real(At, B, **kw) if not (c.kind == "VF" and abs(c.normal[2] - 1.0) < 1e-9)]
    monkeypatch.setattr(E, "enumerate_covers3", dropped)
    with pytest.raises(RuntimeError, match="missed an earlier entrance"):
        first_entrance3(A, SLAB, (0.0, 0.0, 0.0), (0.0, 0.0, -1.0))
