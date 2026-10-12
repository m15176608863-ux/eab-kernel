"""PERF exact-integer equivalence and independent analytic guards.

The old Fraction expressions are a secondary implementation comparison, not
an independent G0 oracle. The primary analytic segment/plane/box constructions
below use only rational arithmetic and no production geometric primitives.
"""
from construction_oracle import scalar_exact
from fractions import Fraction as F
import inspect
import random

import pytest

from eab.kernel3d import exact_geom as G
from eab.kernel3d.geom3 import Polyhedron, box
import perf_fraction_reference as old


def distance_cases():
    rng = random.Random(190124)
    cases = []
    for k in range(150):
        pts = [tuple(F(rng.randrange(-100, 101), rng.choice((1, 3, 8, 13)))
                     for _ in range(3)) for _ in range(4)]
        if k % 5 == 0:
            pts[1] = pts[0]  # zero-length segment
        if k % 7 == 0:
            pts[3] = tuple(pts[2][j] + pts[1][j] - pts[0][j] for j in range(3))
        t = (0, 10**3, 10**6)[k % 3]
        s = (F(1, 10**9), F(1), F(10**4))[k % 3]
        pts = [tuple(s*x+(j+1)*t for j, x in enumerate(p)) for p in pts]
        if k % 4 == 0:
            pts = [tuple(scalar_exact(x) for x in p) for p in pts]
        cases.append(tuple(pts))
    # Near-parallel, exact crossing, subnormal, and enormous original inputs.
    for s in (F(1, 2**1074), F(1, 2**500), F(1), F(2**500)):
        for d in (F(0), F(1, 2**80), F(1)):
            cases.append(((0, 0, 0), (s, 0, 0), (0, 0, s*d), (s, s*d, s*d)))
    return cases


def test_perf_integer_distances_match_unoptimized_fraction_on_all_input_classes():
    """Point/segment active sets; no rounded approximate equality is accepted."""
    outcomes = set()
    for index, pts in enumerate(distance_cases()):
        got = G.segment_distance_squared(*pts)
        assert got == old.segment_distance_squared(*pts), ('segment exact value', index)
        outcomes.add(got == 0)
        p, *tri = map(G.vector, pts)
        # Independently form the area components only to reject invalid triangles.
        a, b, c = tri
        u = tuple(b[j]-a[j] for j in range(3))
        v = tuple(c[j]-a[j] for j in range(3))
        area = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
        if any(area):
            assert G.point_triangle_distance_squared(p, tri) == old.point_triangle_distance_squared(p, tri), ('triangle exact value', index)
        else:
            with pytest.raises(ValueError, match='nondegenerate'):
                G.point_triangle_distance_squared(p, tri)
    assert outcomes == {False, True}, 'nonidentical products across degeneracies'


@pytest.mark.parametrize('s', [F(1, 2**1074), F(1, 7), F(1), F(1024)])
@pytest.mark.parametrize('t', [F(0), F(1000), F(10**6)])
def test_perf_integer_distance_scale_is_fixed_by_independent_orthogonal_construction(s, t):
    """Oracle is h² for perpendicular projection within a segment/triangle."""
    a, b = (t, t, t), (t+4*s, t, t)
    p, q = (t+s, t-2*s, t+3*s), (t+s, t+2*s, t+3*s)
    assert G.segment_distance_squared(a, b, p, q) == 9*s*s, 'squared scale restoration'
    tri = (a, b, (t, t+4*s, t))
    assert G.point_triangle_distance_squared((t+s, t+s, t+3*s), tri) == 9*s*s, 'plane projection scale'
    assert G.point_triangle_distance_squared((t-s, t, t), tri) == s*s, 'edge active set'


def _move(P, t, s, rounded=False):
    points = []
    for x, y, z in P.verts:
        # Independently constructed rational rotation, breaking axis alignment.
        x, y = F(3, 5)*x-F(4, 5)*y, F(4, 5)*x+F(3, 5)*y
        y, z = F(5, 13)*y-F(12, 13)*z, F(12, 13)*y+F(5, 13)*z
        p = (s*x+t, s*y-2*t, s*z+3*t)
        points.append(tuple(scalar_exact(component) for component in p) if rounded else p)
    return Polyhedron(points, list(P.faces))


def sat_cases():
    rng = random.Random(50017)
    offsets = [(F(2)+d, F(0), F(0)) for d in (-F(1, 2**80), F(0), F(1, 2**80))]
    offsets += [(F(2), F(2), F(0)), (F(2), F(2), F(2))]
    offsets += [tuple(F(rng.randrange(-24, 25), 8) for _ in range(3)) for _ in range(10)]
    for t in (F(0), F(1000), F(10**6)):
        for k, offset in enumerate(offsets):
            s = (F(1, 10**8), F(1), F(1000))[k % 3]
            A = box((F(0),)*3, (F(1),)*3)
            B = box(offset, (F(1),)*3)
            yield _move(A, t, s), _move(B, t, s)
            yield _move(A, t, s, True), _move(B, t, s, True)
    # Valid outward surface with an inward top fold: certificate must decline.
    A = box((F(0),)*3, (F(1),)*3)
    A.verts[6] = (F(1), F(1), F(-1, 2))
    yield A, box((F(0),)*3, (F(1),)*3)


def _sat_input(A, B):
    av, bv = tuple(G.vector(point) for point in A.verts), tuple(G.vector(point) for point in B.verts)
    at, bt = G.triangles(A), G.triangles(B)
    return av, bv, at, bt, G._planes(at), G._planes(bt)


def test_perf_integer_convex_sat_matches_unoptimized_random_degenerate_engineering():
    states = set()
    for index, (A, B) in enumerate(sat_cases()):
        args = _sat_input(A, B)
        got = G._convex_surface_sat(*args)
        assert got == old._convex_surface_sat(*args), ('convex certificate and SAT', index)
        states.add(got)
    assert states == {-1, 0, 1, None}, 'all states and refusal are exercised'


@pytest.mark.parametrize('t', [F(0), F(10**6)])
def test_perf_integer_sat_closed_boundary_and_thin_penetration_have_independent_box_oracle(t):
    """Oracle: unrotated intervals touch iff offset=2, penetrate iff offset<2."""
    states = []
    for d in (-F(1, 2**100), F(0), F(1, 2**100)):
        A = _move(box((F(0),)*3, (F(1),)*3), t, F(1, 17))
        B = _move(box((F(2)+d, F(0), F(0)), (F(1),)*3), t, F(1, 17))
        got = G._convex_surface_sat(*_sat_input(A, B))
        assert got == (1 if d < 0 else -1 if d > 0 else 0), 'independent box state'
        states.append(got)
    assert states == [1, 0, -1]


def test_perf_integer_distance_scale_mutation_has_teeth(monkeypatch):
    source = inspect.getsource(G.segment_distance_squared)
    assert source.count('min(values)/(den*den)') == 1
    namespace = dict(G.__dict__)
    exec(source.replace('min(values)/(den*den)', 'min(values)/den'), namespace)
    monkeypatch.setattr(G, 'segment_distance_squared', namespace['segment_distance_squared'])
    with pytest.raises(AssertionError, match='squared scale restoration'):
        test_perf_integer_distance_scale_is_fixed_by_independent_orthogonal_construction(F(1, 7), F(10**6))


def test_perf_integer_sat_boundary_mutation_has_teeth(monkeypatch):
    source = inspect.getsource(G._convex_surface_sat)
    assert source.count('if gap > 0:') == 2
    namespace = dict(G.__dict__)
    exec(source.replace('if gap > 0:', 'if gap >= 0:'), namespace)
    monkeypatch.setattr(G, '_convex_surface_sat', namespace['_convex_surface_sat'])
    with pytest.raises(AssertionError, match='independent box state'):
        test_perf_integer_sat_closed_boundary_and_thin_penetration_have_independent_box_oracle(F(10**6))
