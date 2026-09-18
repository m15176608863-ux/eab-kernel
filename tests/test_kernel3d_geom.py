"""三维几何原语与暴力 oracle 的门（二维版审查的三条教训在此复检）。"""

import random

import pytest

from eab.kernel3d.geom3 import (Polyhedron, add, box, convex_hull_3d, dot, mul, norm,
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
