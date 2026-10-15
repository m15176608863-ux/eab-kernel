"""Explicit 3D boundary/exit gates with independent source-surface oracle.

Oracle imports: g03_surface_oracle (fractions, functools, math,
kernel2d.g0_oracle.sqrt_display), and geom3.polyhedra_overlap -> exact_geom.
Neither imports boundary/global_entrance or their hull, clipping, BSP or SAT.
Cartesian box-union closed occupancy is an additional independent analytic
oracle.  Production geom3 constructs fixtures only, not expected geometry.
"""
from fractions import Fraction as F
import inspect
import textwrap
from itertools import product

import pytest

from eab.kernel3d import boundary as B
from eab.kernel3d import global_entrance as G
from eab.kernel3d import geom3, g03
from eab.kernel3d import g03_surface_oracle as O
from test_m3_global3d import _prism, _combine


def pairs():
    small = geom3.box(half=(F(1, 4),)*3)
    ell = _prism([(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2)])
    pin = geom3.box(center=(F(3, 2), F(3, 2), 0), half=(F(1, 2), F(1, 2), F(1, 4)))
    pocket = _prism([(0, 0), (3, 0), (3, 3), (2, 3), (2, 1), (1, 1), (1, 3), (0, 3)])
    return [('L', small, ell), ('tight', pin, pocket)]


def oracle_state(A, C, point):
    moved = geom3.Polyhedron([tuple(F(p[k])+point[k] for k in range(3)) for p in A.verts], A.faces)
    return geom3.polyhedra_overlap(moved, C, 0)


def oracle_cover_union(patch, covers):
    """Independent projected planar arrangement; imports only Fraction.

    Uses its own signed 2D determinant, linear interpolation and convex
    membership. No B/G helper or production polygon primitive is called.
    """
    normal = patch.normal
    axes = tuple(k for k in range(3) if k != max(range(3), key=lambda k: abs(normal[k])))
    def project(p):
        return tuple(p[k] for k in axes)
    def det(a, b, p):
        return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
    def contains(poly, point):
        values = [det(a, b, point) for a, b in zip(poly, poly[1:]+poly[:1])]
        return min(values) >= 0 or max(values) <= 0
    coplanar = [tuple(project(v) for v in cover.polygon) for cover in covers
                if all(sum(normal[k]*(v[k]-patch.polygon[0][k]) for k in range(3)) == 0 for v in cover.polygon)]
    pieces = [tuple(project(v) for v in patch.polygon)]
    for cover in coplanar:
        for a, b in zip(cover, cover[1:]+cover[:1]):
            refined = []
            for piece in pieces:
                values = [det(a, b, p) for p in piece]
                if not min(values) < 0 < max(values):
                    refined.append(piece)
                    continue
                for sign in (-1, 1):
                    row = []
                    for i, p in enumerate(piece):
                        q = piece[(i+1) % len(piece)]
                        u, v = sign*values[i], sign*values[(i+1) % len(piece)]
                        if u >= 0:
                            row.append(p)
                        if u*v < 0:
                            row.append(tuple((u*q[k]-v*p[k])/(u-v) for k in range(2)))
                    refined.append(tuple(row))
            pieces = refined
    for piece in pieces:
        centre = tuple(sum(p[k] for p in piece)/len(piece) for k in range(2))
        assert any(contains(cover, centre) for cover in coplanar), 'strong completeness closed local cover union'
    return len(pieces)


def audit(name, A, C):
    model = G.global_entrance(A, C)
    boundary = B.explicit_boundary(model)
    counts = {}
    for kind, points in boundary.probes().items():
        counts[kind] = len(points)
        for point in points:
            expected = oracle_state(A, C, point)
            assert model.classify(point) == expected, ('all arrangement probes zero mismatch', name, kind, point)
    for patch in boundary.arrangement:
        centre = tuple(sum(p[k] for p in patch.polygon)/len(patch.polygon) for k in range(3))
        truth = tuple(oracle_state(A, C, point) >= 0 for point in patch.side_points)
        assert boundary.contains(centre) == (truth[0] != truth[1]), 'closed occupancy boundary not physical 0/1 seam'
    candidates = B.local_cover_candidates(A, C)
    clipped = B.clip_local_covers(boundary, candidates)
    # Every retained local polygon is a subset of the explicit boundary.
    for patch in clipped:
        centre = tuple(sum(p[k] for p in patch.polygon)/len(patch.polygon) for k in range(3))
        assert boundary.contains(centre), 'local cover clipping removes buried polygons'
    # Area comparison is stronger than checking only face centroids: within
    # each global patch, split by every local-cover edge line; each atomic
    # centroid must have a retained local label.
    checked = 0
    for patch in boundary.patches:
        checked += oracle_cover_union(patch, clipped)
    return boundary, dict(counts, arranged=len(boundary.arrangement), exposed=len(boundary.patches), local_atomic=checked)


def test_all_boundary_arrangement_vertices_edges_faces_and_sides_have_zero_mismatch():
    name, A, C = pairs()[0]
    boundary, counts = audit(name, A, C)
    assert counts['vertex'] >= 16 and counts['side'] >= 20, 'all probes counted'
    assert boundary.arranged_patches > len(boundary.patches), 'buried candidates actually exercised'


def test_removing_local_clipping_is_killed_by_buried_polygon_assertion(monkeypatch):
    name, A, C = pairs()[0]
    boundary = B.explicit_boundary(G.global_entrance(A, C))
    candidates = B.local_cover_candidates(A, C)
    def check():
        for patch in B.clip_local_covers(boundary, candidates):
            assert boundary.contains(G._mean(patch.polygon)), 'local cover clipping removes buried polygons'
    check()
    source = textwrap.dedent(inspect.getsource(B.clip_local_covers))
    assert 'out = []' in source
    namespace = dict(vars(B))
    exec(compile(source.replace('out = []', 'return tuple(candidates)\n    out = []'), '<semantic clipping mutation>', 'exec'), namespace)
    monkeypatch.setattr(B, 'clip_local_covers', namespace['clip_local_covers'])
    with pytest.raises(AssertionError, match='local cover clipping removes buried polygons'):
        check()


def test_using_physical_zero_one_as_exterior_is_killed_on_tight_seam(monkeypatch):
    name, A, C = pairs()[1]
    model = G.global_entrance(A, C)
    # The incorrect 0/1 rule compares physical on-patch contact to penetrating
    # neighbours, rather than comparing the two closed occupancy labels.
    boundary = B.explicit_boundary(model)
    assert not boundary.contains((F(0), F(0), F(0))), 'tight interior seam is not boundary'
    source = textwrap.dedent(inspect.getsource(B.explicit_boundary))
    before = '_closed_side(side_states[0]) == _closed_side(side_states[1])'
    assert before in source
    namespace = dict(vars(B))
    exec(compile(source.replace(before, 'model.classify(G._mean(piece)) != 0'), '<semantic physical 0/1 mutation>', 'exec'), namespace)
    monkeypatch.setattr(B, 'explicit_boundary', namespace['explicit_boundary'])
    mutant = B.explicit_boundary(model)
    # All retained facets must have an actually separated open side.
    with pytest.raises(AssertionError, match='closed occupancy boundary not physical 0/1 seam'):
        for patch in mutant.patches:
            truth = [oracle_state(A, C, p) >= 0 for p in patch.side_points]
            assert truth[0] != truth[1], 'closed occupancy boundary not physical 0/1 seam'


def test_intersecting_exit_is_checked_and_skip_mutation_is_killed(monkeypatch):
    def _check_intersecting_exit():
        cube = geom3.box()
        rep = g03.g0_distance_completeness3(cube, cube, radius=0, samples=1)
        assert rep.samples == 1 and rep.skipped_intersecting == 0, 'intersecting exit sample must execute'
        assert rep.passed, 'independent intersecting exit zero mismatch'
    _check_intersecting_exit()
    source = textwrap.dedent(inspect.getsource(g03.g0_distance_completeness3))
    before = 'if truth2 is None:'
    assert before in source
    namespace = dict(vars(g03))
    exec(compile(source.replace(before, before+'\n            rep.skipped_intersecting += 1\n            continue'), '<semantic exit skip mutation>', 'exec'), namespace)
    monkeypatch.setattr(g03, 'g0_distance_completeness3', namespace['g0_distance_completeness3'])
    with pytest.raises(AssertionError, match='intersecting exit sample must execute'):
        _check_intersecting_exit()


def test_shortest_closed_exit_uses_exposed_boundary_not_internal_contact_seam():
    """Independent Cartesian formula: pocket+pin gives a single closed box.

    No expected-answer import uses a tested geometric primitive.  Closed E is
    [-2,2] x [-2,2] x [-3/4,3/4]; its central physical seam is not an exit.
    """
    name, A, C = pairs()[1]
    boundary = B.explicit_boundary(G.global_entrance(A, C))
    assert boundary.model.classify((0, 0, 0)) == 0
    for point in ((F(0), F(0), F(0)), (F(7, 4), F(0), F(0)), (F(0), F(0), F(1, 8))):
        low, high = (F(-2), F(-2), F(-3, 4)), (F(2), F(2), F(3, 4))
        rows = []
        for k in range(3):
            for bound in (low[k], high[k]):
                p = list(point)
                p[k] = bound
                rows.append(((bound-point[k])**2, tuple(p)))
        expected = min(row[0] for row in rows)
        got = boundary.shortest_exit(point)
        assert got.squared == expected, 'closed-E shortest exit ignores tight seam'
        assert set(got.tied_exact_points) == {p for square, p in rows if square == expected}, 'all tied exact exit witnesses'


def test_local_cover_constructor_rejects_self_intersecting_shells_and_ignores_unused_buffer():
    cube = geom3.box()
    crossing = _combine(cube, geom3.box(center=(F(1, 3), F(1, 4), F(1, 5))))
    with pytest.raises(ValueError, match='intersect|embedded'):
        B.local_cover_candidates(crossing, cube)
    buffered = geom3.Polyhedron(cube.verts+[(F(100), F(200), F(300))], cube.faces)
    assert B.local_cover_candidates(buffered, cube) == B.local_cover_candidates(cube, cube), 'unused buffer is not a geometric feature'


def test_independent_distance_and_exit_oracle_ignore_unreferenced_buffer_rows():
    cube = geom3.box(half=(1, 1, 1))
    other = geom3.box(center=(5, 0, 0), half=(1, 1, 1))
    buffered = geom3.Polyhedron(cube.verts+[(5, 0, 0)], cube.faces)
    for a, b in ((cube, other), (buffered, other), (other, buffered)):
        assert O.separated_distance(a.verts, a.faces, b.verts, b.faces, squared=True) == 9, 'independent face-defined oracle ignores spare buffer'
        report = g03.g0_distance_completeness3(a, b, radius=0, samples=1)
        assert report.passed and report.samples == 1 and report.skipped_intersecting == 0, 'face-defined G0 gate is buffer invariant'


@pytest.mark.parametrize('scale,translation', [(F(1, 2**400), 10**6), (F(1), 1000), (F(2**400), 0)])
def test_boundary_fraction_constructions_transform_under_exact_rotation_units_translation(scale, translation):
    # Rational non-axis-aligned orthogonal matrix, asymmetric separate origins.
    def rotate(p):
        p = tuple(F(x) for x in p)
        return (F(3, 5)*p[0]-F(4, 5)*p[1], F(4, 5)*p[0]+F(3, 5)*p[1], p[2])
    def transform(P, shift):
        return geom3.Polyhedron([tuple(scale*x+shift[k] for k, x in enumerate(rotate(p))) for p in P.verts], P.faces)
    A, C = geom3.box(half=(F(1, 4), F(1, 3), F(1, 5))), geom3.box(center=(2, 3, 4))
    ta, tb = (F(translation), F(-3), F(2)), (F(translation+5), F(7), F(-11))
    transformed = B.explicit_boundary(G.global_entrance(transform(A, ta), transform(C, tb)))
    # Independent Cartesian support of box difference, not baseline output.
    bounds = tuple((min(F(p[k]) for p in C.verts)-max(F(p[k]) for p in A.verts),
                    max(F(p[k]) for p in C.verts)-min(F(p[k]) for p in A.verts)) for k in range(3))
    corners = tuple(product(*bounds))
    faces = [tuple(p for p in corners if p[axis] == bound) for axis in range(3) for bound in bounds[axis]]
    expected = {tuple(sorted(tuple(scale*x+tb[k]-ta[k] for k, x in enumerate(rotate(p))) for p in face)) for face in faces}
    assert {tuple(sorted(p.polygon)) for p in transformed.patches} == expected, 'all boundary Fraction coordinates covariant'
    point = tuple((low+high)/2+F(k+1, 17) for k, (low, high) in enumerate(bounds))
    query = tuple(scale*x+tb[k]-ta[k] for k, x in enumerate(rotate(point)))
    candidates = []
    for k in range(3):
        for bound in bounds[k]:
            p = tuple(bound if j == k else point[j] for j in range(3))
            candidates.append(((bound-point[k])**2,
                               tuple(scale*x+tb[j]-ta[j] for j, x in enumerate(rotate(p)))))
    smallest = min(square for square, p in candidates)
    result = transformed.shortest_exit(query)
    assert result.squared == smallest*scale*scale, 'independent three-scale exact squared exit'
    assert set(result.tied_exact_points) == {p for square, p in candidates if square == smallest}, 'independent three-scale exact exit coordinates'
