"""M3c independent 3D adjacency, coverage, exit and closed-EE regression gates.

Oracle imports: m3c_oracle3d -> fractions.Fraction, itertools.product only.
oracle_cover_union -> test-owned 2D determinant/interpolation/membership only.
Production imports B/G/Polyhedron construct the SUT and raw input containers;
none is called to obtain expected points, occupancy, events or distances.
Mutants replace real function bodies in isolated namespaces, not outputs;
source-hash/static-review tripwires are not involved in these semantic checks.
"""
from fractions import Fraction as F
import inspect
import random
import textwrap

import pytest

from eab.kernel3d import boundary as B
from eab.kernel3d import global_entrance as G
from eab.kernel3d.geom3 import Polyhedron
import m3c_oracle3d as O
from test_m3b_boundary3d import oracle_cover_union, assert_clipped_polygons_nondegenerate
from tools.m3c_mutation_support import mutate as _mutate


FACES = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))


def _box(low, high):
    x, y, z = (F(x) for x in low)
    X, Y, Z = (F(x) for x in high)
    return Polyhedron(((x, y, z), (X, y, z), (X, Y, z), (x, Y, z),
                       (x, y, Z), (X, y, Z), (X, Y, Z), (x, Y, Z)), FACES)


def _prism(profile):
    n = len(profile)
    points = tuple((F(x), F(y), z) for z in (F(-1, 2), F(1, 2)) for x, y in profile)
    faces = (tuple(range(n-1, -1, -1)), tuple(range(n, 2*n)))
    faces += tuple((i, (i+1) % n, (i+1) % n+n, i+n) for i in range(n))
    return Polyhedron(points, faces)


def _mapped(point, scale, matrix, shift):
    return tuple(scale*x+shift[k] for k, x in enumerate(O.rotate(point, matrix)))


def _unmapped(point, scale, matrix, shift):
    return O.inverse(tuple((point[k]-shift[k])/scale for k in range(3)), matrix)


def _fixture(name):
    matrix, scale, shift = O.IDENTITY, F(1), (F(0),)*3
    if name == 'rotated_narrow_pocket':
        matrix, scale, shift = O.ROTATION, F(2), (F(10**6), F(-3), F(7))
    if name == 'cavity':
        half = (F(1, 4),)*3
        outer, inner = _box((-1,)*3, (1,)*3), _box((F(-1, 2),)*3, (F(1, 2),)*3)
        body = Polyhedron(outer.verts+inner.verts,
                          outer.faces+tuple(tuple(i+8 for i in reversed(face)) for face in inner.faces))
        raw_boxes = []
        # Six disjoint-interior slabs are an independently declared shell.
        for k in range(3):
            for sign in (-1, 1):
                lo, hi = [F(-1)]*3, [F(1)]*3
                for j in range(k):
                    lo[j], hi[j] = F(-1, 2), F(1, 2)
                if sign < 0:
                    hi[k] = F(-1, 2)
                else:
                    lo[k] = F(1, 2)
                raw_boxes.append((tuple(lo), tuple(hi)))
        queries = ((F(0), F(0), F(1, 2)), (F(1, 3), F(1, 7), F(0)))
    elif name == 'L':
        half = (F(1, 4), F(1, 3), F(1, 5))
        body = _prism(((0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3)))
        raw_boxes = [((0, 0, F(-1, 2)), (1, 3, F(1, 2))),
                     ((1, 0, F(-1, 2)), (3, 1, F(1, 2)))]
        queries = ((F(1), F(1), F(0)), (F(1, 2), F(2), F(0)))
    else:
        half = (F(1, 2) if name == 'tight' else F(7, 16), F(1, 4), F(1, 5))
        body = _prism(((0, 0), (3, 0), (3, 3), (2, 3), (2, 1), (1, 1), (1, 3), (0, 3)))
        raw_boxes = [((0, 0, F(-1, 2)), (1, 3, F(1, 2))),
                     ((1, 0, F(-1, 2)), (2, 1, F(1, 2))),
                     ((2, 0, F(-1, 2)), (3, 3, F(1, 2)))]
        queries = ((F(1)+half[0]-F(1, 32), F(2), F(0)),
                   (F(3, 2), F(1, 2), F(0)))
        if name == 'tight':
            queries += ((F(3, 2), F(2), F(0)),)
    little = _box(tuple(-x for x in half), half)
    boxes = tuple((tuple(F(low[k])-half[k] for k in range(3)),
                   tuple(F(high[k])+half[k] for k in range(3))) for low, high in raw_boxes)
    # Only B is shifted: the independently transformed E has the same shift.
    a = Polyhedron(tuple(tuple(scale*x for x in O.rotate(p, matrix)) for p in little.verts), little.faces)
    b = Polyhedron(tuple(_mapped(p, scale, matrix, shift) for p in body.verts), body.faces)
    return a, b, boxes, queries, scale, matrix, shift


def _semantic_checks(boundary, fixture, mode='all'):
    a, b, boxes, queries, scale, matrix, shift = fixture
    polygons = tuple(tuple(_unmapped(p, scale, matrix, shift) for p in patch.polygon) for patch in boundary.patches)
    if mode in ('all', 'sides'):
        for patch in boundary.arrangement:
            polygon = tuple(_unmapped(p, scale, matrix, shift) for p in patch.polygon)
            sides = tuple(_unmapped(p, scale, matrix, shift) for p in patch.side_points)
            O.adjacent_sides(boxes, polygon, sides)
        for patch, polygon in zip(boundary.patches, polygons):
            sides = tuple(_unmapped(p, scale, matrix, shift) for p in patch.side_points)
            truth = tuple(O.occupied(boxes, p) for p in sides)
            assert truth[0] != truth[1], 'independent exposed patch has one occupied and one exterior side'
            assert tuple(x >= 0 for x in patch.side_states) == truth, 'independent exposed-side occupancy labels'
    if mode in ('all', 'coverage'):
        rng = random.Random(3103)
        count = 0
        for start in queries:
            for _ in range(12):
                direction = tuple(F(rng.choice(tuple(range(-9, 0))+tuple(range(1, 10)))) for k in range(3))
                for interval in O.ray_sections(boxes, start, direction):
                    for time in interval:
                        point = tuple(start[k]+time*direction[k] for k in range(3))
                        assert any(O.in_polygon(point, p) for p in polygons), 'independent ray boundary point has an exposed polygon'
                        count += 1
        assert count >= 48, 'independent ray boundary coverage actually executed'
    if mode in ('all', 'exit'):
        rectangles = O.boundary_rectangles(boxes)
        for point in queries:
            square, witnesses = O.shortest_exit(rectangles, point)
            result = B.ExplicitBoundary3D.shortest_exit(boundary, _mapped(point, scale, matrix, shift))
            assert result.squared == square*scale*scale, 'independent Cartesian-union shortest closed exit'
            assert result.tied_exact_points == tuple(sorted(_mapped(p, scale, matrix, shift) for p in witnesses)), 'independent all tied shortest exit witnesses'


def test_independent_3d_all_support_adjacency_ray_boundary_and_shortest_exit():
    products = set()
    for name in ('L', 'narrow_pocket', 'tight', 'cavity', 'rotated_narrow_pocket'):
        fixture = _fixture(name)
        boundary = B.explicit_boundary(G.global_entrance(*fixture[:2]))
        _semantic_checks(boundary, fixture)
        products.add(tuple((p.polygon, p.side_points) for p in boundary.patches))
    assert len(products) == 5, 'five geometry families have distinct actual boundary products'


def test_source_pair_only_side_events_die_at_three_independent_semantic_assertions(monkeypatch):
    fixture = _fixture('narrow_pocket')
    model = G.global_entrance(*fixture[:2])
    _semantic_checks(B.explicit_boundary(model), fixture)
    _mutate(monkeypatch, B, B.explicit_boundary,
            '_sides(model, piece, normal, planes)',
            '_sides(model, piece, normal, tuple(_plane(n, h) for i, j in sources '
            'for n, lo, hi in G._pair_slabs(model.parts_a[i], model.parts_b[j]) for h in (lo, hi)))')
    mutant = B.explicit_boundary(model)
    for mode, message in (('sides', 'independent adjacent-open-cell side probe crossed a support event'),
                          ('coverage', 'independent ray boundary point has an exposed polygon'),
                          ('exit', 'independent Cartesian-union shortest closed exit')):
        with pytest.raises(AssertionError, match=message):
            _semantic_checks(mutant, fixture, mode)
    monkeypatch.undo()
    _semantic_checks(B.explicit_boundary(model), fixture)


def _closed_ee_case(scale, matrix, shift):
    a = _box((-2, F(-1, 4), F(-1, 2)), (2, F(1, 4), F(1, 2)))
    b = _box((F(-1, 3), -3, F(-1, 2)), (F(1, 3), 3, F(1, 2)))
    a = Polyhedron(tuple(tuple(scale*x for x in O.rotate(p, matrix)) for p in a.verts), a.faces)
    b = Polyhedron(tuple(_mapped(p, scale, matrix, shift) for p in b.verts), b.faces)
    boundary = B.explicit_boundary(G.global_entrance(a, b))
    clipped = B.clip_local_covers(boundary, B.local_cover_candidates(a, b))
    for sign in (-1, 1):
        # Crossed thin bars: face/vertex covers form perimeter strips only;
        # the central face area requires nonparallel EE on the face cone rim.
        point = _mapped((F(1, 7), F(1, 11), F(sign)), scale, matrix, shift)
        covering = [p for p in clipped if O.in_polygon(point, p.polygon)]
        assert covering, 'T3L closed-only EE covers the independent exposed-face interior'
        assert all(p.label[0] == 'EE' for p in covering), 'T3L sample genuinely requires EE rather than VF or FV'
        for cover in covering:
            for body, feature in ((a, cover.label[1]), (b, cover.label[2])):
                edge = set(feature[1:])
                normals = []
                for face in body.faces:
                    if edge <= set(face):
                        p, q, r = (body.verts[i] for i in face[:3])
                        normals.append(O.cross(O.sub(q, p), O.sub(r, p)))
                assert len(normals) == 2
                assert any(not any(O.cross(n, cover.normal)) for n in normals), 'EE normal is on a closed cone rim, not strictly valid'
    for patch in boundary.patches:
        oracle_cover_union(patch, clipped)
    return tuple((p.polygon, p.label) for p in clipped)


def test_t3l_coverage_requires_closed_but_not_strict_ee_family():
    products = set()
    for scale, matrix, shift in (
            (F(1), O.IDENTITY, (F(0),)*3),
            (F(1, 8), O.ROTATION, (F(10**6), F(-3), F(2))),
            (F(8), O.ROTATION, (F(-5), F(7), F(-11)))):
        products.add(_closed_ee_case(scale, matrix, shift))
    assert len(products) == 3, 'three closed-only EE cases have distinct actual clipped products'


def test_strict_only_ee_mutant_dies_at_t3l_semantic_coverage(monkeypatch):
    arguments = (F(1), O.IDENTITY, (F(0),)*3)
    _closed_ee_case(*arguments)
    source = textwrap.dedent(inspect.getsource(B._edge_closed))
    assert source.count('>= 0') == 2
    namespace = dict(vars(B))
    exec(compile(source.replace('>= 0', '> 0'), '<M3c strict EE mutation>', 'exec'), namespace)
    monkeypatch.setattr(B, '_edge_closed', namespace['_edge_closed'])
    with pytest.raises(AssertionError, match='T3L closed-only EE covers the independent exposed-face interior'):
        _closed_ee_case(*arguments)
    monkeypatch.undo()
    _closed_ee_case(*arguments)


def test_noncoplanar_clip_mutant_dies_at_explicit_degenerate_polygon_assertion(monkeypatch):
    cube = _box((-1,)*3, (1,)*3)
    boundary = B.explicit_boundary(G.global_entrance(cube, cube))
    candidates = B.local_cover_candidates(cube, cube)
    assert_clipped_polygons_nondegenerate(B.clip_local_covers(boundary, candidates))
    _mutate(monkeypatch, B, B.clip_local_covers,
            '            if any(G._dot(n, G._sub(p, patch.polygon[0])) for p in candidate.polygon):\n'
            '                continue\n', '')
    with pytest.raises(AssertionError, match='clipped local cover must be a nondegenerate planar polygon'):
        assert_clipped_polygons_nondegenerate(B.clip_local_covers(boundary, candidates))
    monkeypatch.undo()
    assert_clipped_polygons_nondegenerate(B.clip_local_covers(boundary, candidates))
