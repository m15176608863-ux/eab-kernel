"""三维几何原语与暴力 oracle 的门（二维版审查的三条教训在此复检）。"""
from construction_oracle import scalar_exact

import random
import math
from fractions import Fraction

import pytest

from eab.kernel3d.geom3 import (Polyhedron, add, box, convex_hull_3d, dot, merge_coplanar, mul, norm,
                                point_in_polyhedron, polyhedra_overlap, sub, tetra, unit)


def l_block() -> Polyhedron:
    """L 形棱柱（凹）：底面 L 形，沿 z 拉伸。用于凹块测试。"""
    base = [(0.0, 0.0), (3.0, 0.0), (3.0, 1.0), (1.0, 1.0), (1.0, 3.0), (0.0, 3.0)]
    n = len(base)
    v = [(x, y, 0.0) for x, y in base] + [(x, y, 1.0) for x, y in base]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    return Polyhedron(v, faces)


def test_box_topology_and_volume():
    b = box(half=(1.0, 2.0, 3.0))
    assert len(b.verts) == 8 and len(b.faces) == 6
    assert len(b.edges()) == 12
    assert abs(b.volume() - 2 * 4 * 6) < 1e-12
    assert b.is_convex()
    assert b.reflex_edges() == []
    for e in b.edges():
        assert len(b.edge_faces(e)) == 2


def test_l_block_is_concave_with_one_reflex_edge():
    L = l_block()
    assert abs(L.volume() - 5.0) < 1e-12        # L 面积 5，高 1
    assert not L.is_convex()
    assert len(L.reflex_edges()) == 1


def test_interior_point_works_on_concave_body_where_centroid_may_not():
    L = l_block()
    p = L.interior_point()
    assert point_in_polyhedron(p, L, 0.0) == 1
    # 拉长的 L：体心落到缺口里
    base = [(0.0, 0.0), (8.0, 0.0), (8.0, 0.4), (0.4, 0.4), (0.4, 8.0), (0.0, 8.0)]
    n = len(base)
    v = [(x, y, 0.0) for x, y in base] + [(x, y, 0.5) for x, y in base]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    thin = Polyhedron(v, faces)
    assert point_in_polyhedron(thin.centroid(), thin, 0.0) == -1     # 体心在体外
    assert point_in_polyhedron(thin.interior_point(), thin, 0.0) == 1


def test_point_in_polyhedron_basic():
    b = box(half=(1.0, 1.0, 1.0))
    assert point_in_polyhedron((0.0, 0.0, 0.0), b) == 1
    assert point_in_polyhedron((2.0, 0.0, 0.0), b) == -1
    assert point_in_polyhedron((1.0, 0.0, 0.0), b, 1e-9) == 0
    assert point_in_polyhedron((1.0, 1.0, 1.0), b, 1e-9) == 0


def test_overlap_separated_touching_intersecting():
    a = box(center=(0.0, 0.0, 0.0), half=(1.0, 1.0, 1.0))
    assert polyhedra_overlap(a, box(center=(3.0, 0.0, 0.0)), 1e-12) == -1
    assert polyhedra_overlap(a, box(center=(2.0, 0.0, 0.0)), 1e-9) == 0
    assert polyhedra_overlap(a, box(center=(1.5, 0.0, 0.0)), 1e-12) == 1
    # 包含
    assert polyhedra_overlap(box(half=(0.3, 0.3, 0.3)), a, 1e-12) == 1
    # 全等
    assert polyhedra_overlap(a, box(half=(1.0, 1.0, 1.0)), 1e-12) == 1


def test_overlap_concave_notch_is_not_a_false_positive():
    # 小块完全落在 L 的缺口里（不相交），这是二维版审查 r6 的三维对应
    L = l_block()
    S = box(center=(2.0, 2.0, 0.5), half=(0.4, 0.4, 0.3))
    assert polyhedra_overlap(L, S, 1e-12) == -1
    assert polyhedra_overlap(S, L, 1e-12) == -1


def test_overlap_edge_crossing_without_vertex_inside():
    # 细长杆穿过方块中央：没有任何顶点在对方内部，只能靠棱穿面抓到
    a = box(half=(1.0, 1.0, 1.0))
    rod = box(center=(0.0, 0.0, 0.0), half=(5.0, 0.2, 0.2))
    assert all(point_in_polyhedron(p, a, 1e-12) == -1 for p in rod.verts)
    assert polyhedra_overlap(rod, a, 1e-12) == 1


def test_volume_and_centroid_far_from_origin():
    off = (1e4, 1e4, 1e4)
    small = box(center=off, half=(1e-3, 1e-3, 1e-3))
    # 输入坐标本身在 1e4 处只有 ~1.8e-9 的相对精度（ulp(1e4)/1e-3），算法误差不可能低于它
    assert abs(small.volume() - 8e-9) / 8e-9 < 1e-8
    c = small.centroid()
    assert max(abs(c[i] - off[i]) for i in range(3)) < 1e-8


def test_convex_hull_3d_matches_box():
    b = box(half=(1.0, 1.0, 1.0))
    h = convex_hull_3d(b.verts)
    assert len(h.verts) == 8
    assert abs(h.volume() - 8.0) < 1e-12
    assert h.is_convex()


@pytest.mark.parametrize("seed", range(5))
def test_convex_hull_random_points_is_convex(seed):
    rng = random.Random(seed)
    pts = [(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(14)]
    h = convex_hull_3d(pts)
    assert h.volume() > 0
    assert h.is_convex(1e-9)
    for p in pts:
        assert point_in_polyhedron(p, h, 1e-9) in (0, 1)


# ================================================================ G6 GAP3：共面交叉（L0 ✔ 的依据此前只有"顶点在内"与"杆穿面"）
#
# 这三例都没有任何顶点严格在对方体内、也没有棱严格穿过对方面的内部（棱都躺在对方的面平面里）：
# 只有 G6 补上的精确证人（棱-棱交点、共面同向面的重叠，沿两体内向锥的方向微推）抓得到。
# oracle：全部轴对齐，交集是闭式长方体 ∏ [max lo, min hi]——体积 > 0 ⇒ 1，退化 ⇒ 0，空 ⇒ −1。

def _aabb_truth(lo1, hi1, lo2, hi2) -> int:
    ext = [min(hi1[i], hi2[i]) - max(lo1[i], lo2[i]) for i in range(3)]
    if all(e > 0.0 for e in ext):
        return 1
    return 0 if all(e >= 0.0 for e in ext) else -1


COPLANAR_CASES = [
    # (名称, A lo, A hi, B lo, B hi)
    ("plus_cross", (-2.0, -0.1, -0.5), (2.0, 0.1, 0.5), (-0.1, -2.0, -0.5), (0.1, 2.0, 0.5)),
    ("t_cross_offcentre", (-2.0, -0.1, -0.5), (2.0, 0.1, 0.5), (1.3, -0.05, -0.5), (1.45, 2.0, 0.5)),
    ("corner_bite", (-2.0, -0.1, -0.5), (2.0, 0.1, 0.5), (1.95, 0.05, -0.5), (3.0, 2.0, 0.5)),
    ("side_by_side_sliver", (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0.999, 0.2, 0.0), (2.0, 0.8, 1.0)),
    ("plus_lifted_touch", (-2.0, -0.1, -0.5), (2.0, 0.1, 0.5), (-0.1, -2.0, 0.5), (0.1, 2.0, 1.5)),
    ("plus_lifted_gap", (-2.0, -0.1, -0.5), (2.0, 0.1, 0.5), (-0.1, -2.0, 0.5001), (0.1, 2.0, 1.5)),
]


def _box_lohi(lo, hi):
    return box(center=tuple(0.5 * (lo[i] + hi[i]) for i in range(3)),
               half=tuple(0.5 * (hi[i] - lo[i]) for i in range(3)))


@pytest.mark.parametrize("name,alo,ahi,blo,bhi", COPLANAR_CASES, ids=[c[0] for c in COPLANAR_CASES])
def test_overlap_coplanar_face_crossing_without_vertex_inside(name, alo, ahi, blo, bhi):
    want = _aabb_truth(alo, ahi, blo, bhi)
    A, B = _box_lohi(alo, ahi), _box_lohi(blo, bhi)
    assert all(point_in_polyhedron(p, B, 1e-12) != 1 for p in A.verts)
    assert all(point_in_polyhedron(p, A, 1e-12) != 1 for p in B.verts)
    for tol in (0.0, 1e-12, 1e-9):
        assert polyhedra_overlap(A, B, tol) == want, (name, tol)
        assert polyhedra_overlap(B, A, tol) == want, (name, tol)


def test_overlap_coplanar_crossing_gate_has_teeth(monkeypatch):
    """The same original X crossing detects an internal certified-SAT corruption.

    The old contact-cone heuristic is no longer called. The mutation is injected
    into the actual SAT state computation, never appended to its output.
    """
    import math
    from eab.kernel3d import geom3

    def slab(th, c):
        ct, st = math.cos(th), math.sin(th)
        P = box(half=(1.0, 0.1, 0.5))
        return Polyhedron([(c[0] + ct * x - st * y, c[1] + st * x + ct * y, z) for x, y, z in P.verts],
                          list(P.faces))
    A = slab(0.7123231161619232, (-0.08666247398702509, -0.28261190955518073))
    B = slab(2.3208944052154075, (0.0, 0.0))
    assert polyhedra_overlap(A, B, 1e-9) == 1
    import inspect
    from eab.kernel3d import exact_geom
    source=inspect.getsource(exact_geom._convex_surface_sat)
    namespace=dict(exact_geom.__dict__)
    exec(source.replace('return 0 if boundary else 1','return 0 if boundary else -1'),namespace)
    monkeypatch.setattr(exact_geom,'_convex_surface_sat',namespace['_convex_surface_sat'])
    assert polyhedra_overlap(A,B,0.0)==-1


# ================================================================ G6 major 27：convex_hull_3d 在旋转 ×1e3 的退化点集上
#
# 缺陷（geom3.py:607）：三处绝对容差（基四面体体积 ~ s³、重复点距离与可见性 ~ s），首四个非退化点
# 随手取。box/box 的 Minkowski 差点大量共面共线；旋转 + ×1e3 后凸包非流形（体积 1387 vs 144）
# 或 face_normal 除零，entrance_block_convex 静默返回坏 E，G0 票二/三假红。
# oracle：E(A, B) = B ⊕ (−A) 仍是方块，半宽 (1+2, 1+0.5, 1+3) ⇒ 体积 6·3·8 = 144（闭式）。

def _g6_rot(seed: int):
    rng = random.Random(seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    n = sum(c * c for c in q) ** 0.5
    w, x, y, z = (c / n for c in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def _placed(P, R, s, t=(0.0, 0.0, 0.0)):
    return Polyhedron([tuple(t[i] + s * (R[i][0] * p[0] + R[i][1] * p[1] + R[i][2] * p[2]) for i in range(3))
                       for p in P.verts], list(P.faces))


def _placed_exact(P, R, s, t=(0.0, 0.0, 0.0)):
    """同一存储矩阵精确仿射变换，保留共面/共线前提；不替换原浮点输入。"""
    F = Fraction
    return Polyhedron([tuple(F(t[i]) + F(s) * sum(F(R[i][j]) * F(p[j]) for j in range(3))
                             for i in range(3)) for p in P.verts], list(P.faces))


@pytest.mark.parametrize("scale", [1e-3, 1.0, 1e3])
@pytest.mark.parametrize("seed", [2, 4, 7])
def test_entrance_block_of_rotated_box_pair_is_a_clean_box(seed, scale):
    """保留原浮点格：精确支持/极点；额外精确保共面的格仍须为八顶点盒。

    oracle 用 test_hull_robustness 的独立 Fraction 行列式/法向秩证书，
    不用生产 orient3d、法锥、成员原语或 G0 的内部 oracle。
    """
    from eab.kernel3d.g03 import g0_convex3
    from eab.margin import entrance_block_convex
    from test_hull_robustness import _assert_exact_hull
    R = _g6_rot(seed)
    A, B = _placed(box(half=(1.0, 1.0, 1.0)), R, scale), _placed(box(half=(2.0, 0.5, 3.0)), R, scale)
    E = entrance_block_convex(A, B)
    assert E.manifold_issues() == [], E.manifold_issues()[:3]
    assert E.volume() == pytest.approx(144.0 * scale ** 3, rel=1e-9)
    assert E.is_convex(1e-9)
    # E5b: lift the original data before subtraction; certify the actual exact E.
    _assert_exact_hull(E, [tuple(Fraction(b[i]) - Fraction(a[i]) for i in range(3))
                           for a in A.verts for b in B.verts])
    rep = g0_convex3(A, B, samples=40, seed=seed)
    assert rep.passed, (rep.facet_symmetric_diff[:3], rep.hull_vertices, rep.e_vertices, rep.mismatches[:2])
    exact_diffs = [tuple(Fraction(b[i]) - Fraction(a[i]) for i in range(3))
                   for a in A.verts for b in B.verts]
    H = convex_hull_3d(exact_diffs)
    assert H.manifold_issues() == [], H.manifold_issues()[:3]
    _assert_exact_hull(H, exact_diffs)
    assert rep.hull_vertices == rep.e_vertices == len(H.verts)

    # 原“同旋转的两盒之差是八顶点盒”解析门不删：把共面前提精确实现。
    Aq = _placed_exact(box(half=(1.0, 1.0, 1.0)), R, scale)
    Bq = _placed_exact(box(half=(2.0, 0.5, 3.0)), R, scale)
    Eq = entrance_block_convex(Aq, Bq)
    assert Eq.manifold_issues() == [], Eq.manifold_issues()[:3]
    assert Eq.volume() == pytest.approx(144.0 * scale ** 3, rel=1e-9)
    _assert_exact_hull(Eq, [tuple(b[i] - a[i] for i in range(3)) for a in Aq.verts for b in Bq.verts])
    assert len(Eq.verts) == 8 and len(merge_coplanar(Eq).faces) == 6
    repq = g0_convex3(Aq, Bq, samples=40, seed=seed)
    assert repq.passed, repq
    assert repq.hull_vertices == repq.e_vertices == 8


LATTICE = [(scalar_exact(i), scalar_exact(j), scalar_exact(k)) for i in range(3) for j in range(3) for k in range(3)]


@pytest.mark.parametrize("seed,scale,t", [(0, 1.0, 0.0), (1, 1e-5, 0.0), (2, 1e3, 0.0), (3, 1.0, 1e5),
                                          (4, 1e3, 1e5), (5, 1e-3, 1e3)])
def test_convex_hull_is_similarity_invariant_on_degenerate_and_generic_sets(seed, scale, t):
    """原浮点输入的支持/极点精确；同系数有理仿射输入另保留理想拓扑门。

    oracle 为独立 Fraction 支持行列式与顶点法向秩，不共用生产几何谓词。
    3×3×3 格点在精确保共线/共面变换下只有八极点；逐坐标舍入可产生微脊。
    所有旧 volume/manifold 断言、原 seed/scale/t 和随机一般点集均保留。
    """
    from test_hull_robustness import _assert_exact_hull, _fr_orient
    R = _g6_rot(100 + seed)
    tv = tuple(t * c for c in (0.6, -0.48, 0.64))
    rng = random.Random(seed)
    cloud = [(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(14)]
    for pts, vol0 in ((LATTICE, 8.0), (cloud, convex_hull_3d(cloud).volume())):
        W = [tuple(tv[i] + scale * (R[i][0] * p[0] + R[i][1] * p[1] + R[i][2] * p[2]) for i in range(3))
             for p in pts]
        H = convex_hull_3d(W)
        assert H.manifold_issues() == [], H.manifold_issues()[:3]
        assert H.volume() == pytest.approx(vol0 * scale ** 3, rel=1e-7)
        _assert_exact_hull(H, W)
        M = merge_coplanar(H)
        _assert_exact_hull(M, W)
        assert all(_fr_orient(*(M.verts[i] for i in f[:3]), M.verts[j]) == 0
                   for f in M.faces for j in f)

        Wq = _placed_exact(Polyhedron(pts, []), R, scale, tv).verts
        Hq = convex_hull_3d(Wq)
        assert Hq.manifold_issues() == [], Hq.manifold_issues()[:3]
        assert Hq.volume() == pytest.approx(vol0 * scale ** 3, rel=1e-7)
        _assert_exact_hull(Hq, Wq)
        assert len(Hq.verts) == len(convex_hull_3d(pts).verts)
        if pts is LATTICE:
            assert len(merge_coplanar(Hq).faces) == 6
            assert len(Hq.verts) == 8                # 精确共面/共线格点不成为凸包顶点


# ================================================================ G6 minor 7：面接触在旋转 / 工程坐标下仍是"相触"

@pytest.mark.parametrize("seed", range(1, 9))
@pytest.mark.parametrize("t", [0.0, 1e3, 1e5, 1e7])
def test_face_touching_stack_is_touching_under_rigid_motion(seed, t):
    """Original rounded cells use independent integer tetra-union SAT/distance.

    All original seeds, translations and float construction remain. Additional
    rational-affine cells retain the ideal zero-contact assertions. The oracle
    uses no production geometric primitive and does not convexify the surface.
    """
    from eab.kernel3d.interlock import escape_height_brute
    R = _g6_rot(200 + seed)
    tv = tuple(t * c for c in (0.6, -0.48, 0.64))
    A = _placed(box((0.1, -0.2, 0.5), (1.0, 1.0, 0.5)), R, 1.0, tv)
    B = _placed(box((0.0, 0.0, -0.5), (2.0, 2.0, 0.5)), R, 1.0, tv)
    from e5a2_surface_oracle import star_overlap, star_relation
    want=star_overlap(A,B)
    assert polyhedra_overlap(A,B)==want
    assert polyhedra_overlap(B,A)==want
    assert polyhedra_overlap(A,B,1e-12)==star_relation(A,B,1e-12)
    # The original rounded solids need not touch: zero-band semantics uses their
    # exact stored coordinates. Preserve the escape check under its real state.
    if want <= 0:
        assert escape_height_brute(A,B,(0.,0.,0.),hi=1.) == 0.
    elif star_overlap(A.translated((0.,0.,1.)),B) == 1:
        with pytest.raises(ValueError,match='still intruding'):
            escape_height_brute(A,B,(0.,0.,0.),hi=1.)
    else:
        from e5b_wall_oracle import earliest_star_escape
        from eab.kernel3d.interlock import escape_height_covers
        truth=earliest_star_escape(A,B)
        sol=escape_height_covers(A,B,(0.,0.,0.))
        z=escape_height_brute(A,B,(0.,0.,0.),hi=1.)
        assert sol.exact_height == truth > 0
        assert Fraction(z) >= truth and Fraction(z)-truth <= Fraction(math.ulp(z))
        # A binary64 display reapplied with float arithmetic is different data.
        # Preserve the nonpenetration assertion on the exact affine endpoint.
        exact_A=Polyhedron([(Fraction(x),Fraction(y),Fraction(v)+truth) for x,y,v in A.verts],list(A.faces))
        assert z > 0 and star_overlap(exact_A,B) <= 0
    # Original ideal contact property remains tested separately with the same
    # input matrix/offset applied rationally (no coordinate-rounding fiction).
    Aq=_placed_exact(box((0.1,-0.2,0.5),(1.,1.,.5)),R,1.,tv)
    Bq=_placed_exact(box((0.,0.,-.5),(2.,2.,.5)),R,1.,tv)
    assert star_overlap(Aq,Bq)==0
    assert polyhedra_overlap(Aq,Bq)==polyhedra_overlap(Bq,Aq)==0
    assert polyhedra_overlap(Aq,Bq,1e-12)==0
