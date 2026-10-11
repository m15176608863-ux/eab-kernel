"""WO-E5a exact local-cone and simplex gates.

Independent oracles use analytic orthants/planes and a rational Gordan ray
construction. They do not call the tested closest-point, cone, or arc helpers.
"""

from fractions import Fraction as F
from itertools import combinations
import math
import random

import pytest

from eab.kernel3d.covers3 import (
    _closest_params, closest_point_of_convex_hull_to_origin,
    cone_intersection_margin, cones_intersect_relint, edge_arc_contains,
    vertex_cone_contains, ve3_cover, vv3_cover,
)
from eab.kernel3d.geom3 import Polyhedron, box, tetra


@pytest.mark.parametrize("scale", [1e-9, 1.0, 1e9])
@pytest.mark.parametrize("depth", [0.0, 1e-16, 1e-13, 1e-9])
def test_exact_simplex_never_absorbs_an_exterior_origin(scale, depth):
    """All x >= depth; (depth,0,0) is present, hence the analytic minimizer."""
    x = depth * scale
    pts = [(x, 0., 0.), (scale, 0., 0.), (x, scale, 0.), (x, 0., scale)]
    got = closest_point_of_convex_hull_to_origin(pts)
    assert got == (x, 0., 0.), (pts, got)


@pytest.mark.parametrize("epsilon", [1e-16, 1e-13, 1e-9])
def test_exact_corrective_simplex_does_not_absorb_origin_just_outside_a_face(epsilon):
    # The nearest point is in a triangle interior, not among the input points.
    # The corrective iteration reaches a four-point simplex, so a reintroduced
    # absolute barycentric tolerance is exercised inside the tested path.
    points = [(.5, 0., 0.), (epsilon, -1., -1.),
              (epsilon, 1., -1.), (epsilon, 0., 1.)]
    assert closest_point_of_convex_hull_to_origin(points) == (epsilon, 0., 0.)


@pytest.mark.parametrize("epsilon", [1e-30, 1e-16, 1e-9])
def test_exact_edge_arc_keeps_endpoint_distinct_from_strict_interior(epsilon):
    p = box()
    edge = next(e for e in p.edges()
                if all(p.verts[i][0] == 1 and p.verts[i][2] == 1 for i in e))
    # The normal cone is exactly { (x,0,z): x>=0, z>=0 }.
    assert edge_arc_contains(p, edge, (1., 0., 0.)) == 0
    assert edge_arc_contains(p, edge, (1., 0., epsilon)) == 1
    assert edge_arc_contains(p, edge, (1., 0., -epsilon)) == -1
    assert edge_arc_contains(p, edge, (1., epsilon, 1.)) == -1
    # An explicitly requested window may only expand the closed condition.
    assert edge_arc_contains(p, edge, (1., 0., -epsilon), 2 * epsilon) == 0
    assert edge_arc_contains(p, edge, (1., epsilon, 1.), 2 * epsilon) == 0


@pytest.mark.parametrize("origin", [0., 1e3, 1e6])
def test_exact_vertex_cone_has_no_coordinate_noise_band(origin):
    p = box(center=(origin, -origin, origin))
    assert vertex_cone_contains(p, 6, (1., 1., -1e-30)) == -1
    assert vertex_cone_contains(p, 6, (1., 1., 1e-30)) == 1
    assert vertex_cone_contains(p, 6, (1., 1., 0.)) == 0


@pytest.mark.parametrize("epsilon", [1e-30, 1e-16, 1e-12])
def test_exact_line_parameters_do_not_discard_near_parallel_edges(epsilon):
    p = (0., 0., 0.)
    q = (0., -epsilon / 2, 1.)
    assert _closest_params(p, (1., 0., 0.), q, (1., epsilon, 0.)) == (0.5, 0.5)
    assert _closest_params(p, (1., 0., 0.), q, (1., 0., 0.)) is None


def _roof(h, yaw=0.):
    section = [(-1., -1.), (1., -1.), (1., 0.), (0., h), (-1., 0.)]
    v = [(-2., y, z) for y, z in section] + [(2., y, z) for y, z in section]
    faces = [(4, 3, 2, 1, 0), (5, 6, 7, 8, 9)] + [
        (i, (i + 1) % 5, 5 + (i + 1) % 5, 5 + i) for i in range(5)]
    c, s = math.cos(yaw), math.sin(yaw)
    return Polyhedron([(c*x-s*y, s*x+c*y, z) for x, y, z in v], faces)


def _ray_oracle(A, ia, B, ib):
    """Independent exact Gordan witness from feasible extreme rays."""
    def edges(P, i, sign):
        neighbors = {f[(k + delta) % len(f)] for f in P.faces
                     for k, v in enumerate(f) if v == i for delta in (-1, 1)}
        return [tuple(sign * (F(P.verts[j][k])-F(P.verts[i][k])) for k in range(3))
                for j in neighbors]
    def cp(u, v):
        return (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    def dp(u, v):
        return sum(x*y for x, y in zip(u, v))
    constraints = edges(A, ia, -1) + edges(B, ib, 1)
    rays = []
    for a, b in combinations(constraints, 2):
        c = cp(a, b)
        for r in (c, tuple(-x for x in c)):
            if any(r) and all(dp(r, q) <= 0 for q in constraints):
                rays.append(tuple(x / max(abs(y) for y in r) for x in r))
    witness = tuple(sum(r[k] for r in rays) for k in range(3))
    return bool(rays) and all(dp(witness, g) < 0 for g in constraints)


@pytest.mark.parametrize("ia,ib", [(3, 9), (4, 8), (7, 3), (8, 2)])
@pytest.mark.parametrize("yaw", [-2.297344991164547e-9, -2**-44])
def test_g6e_simplex_barycentric_noise_cannot_delete_a_true_e_vertex(ia, ib, yaw):
    B, A = _roof(.3), _roof(.3, yaw)
    A = Polyhedron([(x, y, -z + .61) for x, y, z in A.verts],
                   [tuple(reversed(f)) for f in A.faces])
    assert _ray_oracle(A, ia, B, ib)
    assert cones_intersect_relint(A, ia, B, ib)
    # Passing a large legacy tol cannot change this theorem-level decision.
    assert cones_intersect_relint(A, ia, B, ib, tol=1.)
    assert vv3_cover(A, ia, B, ib) is not None
    assert cone_intersection_margin(A, ia, B, ib)[0] > 0


def test_exact_ve_extent_does_not_gain_a_rounding_floor():
    B = box()
    edge = next(e for e in B.edges()
                if all(B.verts[i][1] == 1 and B.verts[i][2] == 1 for i in e))
    apex = (1. + 2**-50, 1.1, 1.1)
    A = tetra(apex, (2., 2., 2.), (2., 2.2, 1.9), (2., 1.8, 2.3))
    ia = A.verts.index(apex)
    c = ve3_cover(A, ia, B, edge)
    assert c is not None and not c.in_extent
    extended = ve3_cover(A, ia, B, edge, extent_tol=2**-49)
    assert extended is not None and extended.in_extent


def _brute_gram_minimum(points):
    """Independent affine least-squares oracle, exact Gauss-Jordan elimination.

    No tested vector, determinant, projection or simplex primitive is called.
    The bordered Gram system imposes sum(weights)=1; feasible subsets up to
    four points suffice by Caratheodory. Singular subsets have smaller support.
    """
    def solve(matrix, rhs):
        rows = [list(row) + [value] for row, value in zip(matrix, rhs)]
        for j in range(len(rows)):
            pivot = next((i for i in range(j, len(rows)) if rows[i][j]), None)
            if pivot is None:
                return None
            rows[j], rows[pivot] = rows[pivot], rows[j]
            den = rows[j][j]
            rows[j] = [x / den for x in rows[j]]
            for i in range(len(rows)):
                if i != j:
                    value = rows[i][j]
                    rows[i] = [x - value*y for x, y in zip(rows[i], rows[j])]
        return [row[-1] for row in rows]
    candidates = []
    for size in range(1, min(4, len(points)) + 1):
        for subset in combinations(points, size):
            gram = [[sum(x*y for x, y in zip(a, b)) for b in subset] + [F(1)]
                    for a in subset] + [[F(1)] * size + [F(0)]]
            weights = solve(gram, [F(0)] * size + [F(1)])
            if weights is not None and all(w >= 0 for w in weights[:-1]):
                p = tuple(sum(w*v[k] for w, v in zip(weights[:-1], subset)) for k in range(3))
                candidates.append((sum(x*x for x in p), p))
    return min(candidates)[1]


@pytest.mark.parametrize("seed", range(12))
@pytest.mark.parametrize("scale", [1e-9, 1., 1e9])
def test_exact_corrective_hull_matches_independent_gram_enumeration(seed, scale):
    from eab.kernel3d.covers3 import _qclosest_hull
    rng = random.Random(5011 + seed)
    points = [tuple(F(scale * rng.uniform(-1, 1)) for _ in range(3)) for _ in range(6)]
    # A duplicated point and a nearly coplanar family exercise affine rank.
    if seed % 3 == 0:
        points[-1] = points[0]
    elif seed % 3 == 1:
        points = [tuple(p[:2]) + (F(scale * 1e-16),) for p in points]
    assert _qclosest_hull(tuple(points)) == _brute_gram_minimum(points)
