"""E5a2 exact integer arithmetic against the pre-optimization Fraction formulas.

The arithmetic reference below uses Fraction multiply/add/subtract directly; it
imports neither rational3 nor a tested geometry dot/cross for its answers.
SAT equivalence keeps the independent oracle's original hull/axis construction
and original five-column Fraction projections, then compares every query. This
is an optimization-equivalence gate, not a new independent geometric oracle.
"""

from fractions import Fraction as F
import math
import random

import pytest

from eab import rational3
from eab.dual import Dual
from eab.kernel3d import exact_geom, geom3, g03_exact, covers3


def _dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def _cases():
    rng = random.Random(51002)
    for scale, offset in ((1., 0.), (1e-9, 1e6), (1e3, -1e5),
                          (1e-200, 0.), (1e200, 0.)):
        for _ in range(120):
            a = tuple(F(offset + scale*rng.uniform(-2, 2)) for _ in range(3))
            b = tuple(F(offset + scale*rng.uniform(-2, 2)) for _ in range(3))
            yield a, b
            yield a, a  # Exactly parallel and all cancellation channels.
    for _ in range(160):
        yield (tuple(F(rng.randrange(-10**8, 10**8), rng.randrange(1, 1000)) for _ in range(3)),
               tuple(F(rng.randrange(-10**8, 10**8), rng.randrange(1, 1000)) for _ in range(3)))
    tiny, huge = F(math.ulp(0.)), F(float.fromhex('0x1.fffffffffffffp+1023'))
    for a in ((tiny, tiny, tiny), (huge, huge, huge), (F(0), tiny, huge)):
        for b in ((tiny, -tiny, F(0)), (huge, -huge, tiny), (F(0), F(0), F(0))):
            yield a, b


@pytest.mark.parametrize('module', [rational3, geom3, exact_geom])
def test_common_denominator_operations_equal_pure_fraction_every_coordinate(module):
    cases = list(_cases())
    assert len(cases) == 1369
    for a, b in cases:
        assert module.dot(a, b) == _dot(a, b), (a, b, 'dot')
        assert module.cross(a, b) == _cross(a, b), (a, b, 'cross')


@pytest.mark.parametrize('module', [geom3, exact_geom])
def test_common_denominator_path_preserves_float_mixed_and_dual_expressions(module):
    for a, b in (((0.1, -2., 1e5), (7., 1e-9, -0.25)),
                 ((F(1, 3), 2, F(5, 7)), (1, F(2, 3), 4)),
                 ((Dual.seed(0., 2, 0), Dual.seed(1., 2, 1), Dual.const(4., 2)),
                  (Dual.const(1., 2), Dual.const(2., 2), Dual.const(3., 2)))):
        assert module.dot(a, b) == _dot(a, b)
        assert module.cross(a, b) == _cross(a, b)


@pytest.mark.parametrize('module', [geom3, exact_geom])
def test_fraction_geometry_operations_really_dispatch_to_integer_arithmetic(module, monkeypatch):
    calls = []
    old_dot, old_cross = rational3.dot, rational3.cross
    def traced_dot(a, b):
        calls.append('dot')
        return old_dot(a, b)
    def traced_cross(a, b):
        calls.append('cross')
        return old_cross(a, b)
    monkeypatch.setattr(rational3, 'dot', traced_dot)
    monkeypatch.setattr(rational3, 'cross', traced_cross)
    a, b = (F(1, 3), F(2, 7), F(5, 11)), (F(13, 17), F(19, 23), F(29, 31))
    assert module.dot(a, b) == _dot(a, b)
    assert module.cross(a, b) == _cross(a, b)
    assert calls == ['dot', 'cross']


def test_integer_angular_band_comparison_equals_fraction_at_and_near_thresholds():
    for a, b in _cases():
        value = _dot(a, b)
        for tol in (0., 1e-12, 0.25, 1., F(1, 3)):
            expected = value > 0 and (tol <= 0 or value*value > F(tol)**2*_dot(a, a)*_dot(b, b))
            assert covers3._outside_dot_band(value, a, b, tol) == expected
    for delta in (-F(1, 2**60), F(0), F(1, 2**60)):
        a, b = (F(1), F(0), F(0)), (F(1), F(0), F(0))
        value = F(1) + delta
        assert covers3._outside_dot_band(value, a, b, F(1)) == (delta > 0)


def _fraction_rows(av, bv):
    # Original independent SAT formulas, deliberately no tested scalar/wedge.
    a, fa, pa = g03_exact.hull(av)
    b, fb, pb = g03_exact.hull(bv)
    def edges(faces):
        return {tuple(sorted((f[i], f[(i+1) % len(f)])))
                for f in faces for i in range(len(f))}
    axes = {n for n, _ in pa} | {n for n, _ in pb}
    for i, j in edges(fa):
        for k, l in edges(fb):
            n = _cross(tuple(a[j][q]-a[i][q] for q in range(3)),
                       tuple(b[l][q]-b[k][q] for q in range(3)))
            if any(n):
                axes.add(n)
    return [(_n, min(aa), max(aa), min(bb), max(bb))
            for _n in axes
            for aa in [[_dot(_n, p) for p in a]]
            for bb in [[_dot(_n, p) for p in b]]]


def _fraction_overlap(rows, x):
    boundary = False
    for n, amin, amax, bmin, bmax in rows:
        shift = _dot(n, x)
        low, high = amin+shift, amax+shift
        if low > bmax or bmin > high:
            return -1
        boundary |= low == bmax or bmin == high
    return 0 if boundary else 1


@pytest.mark.parametrize('scale,offset', [(1., 0.), (1e-6, 1e6), (1e3, -1e5), (1e-150, 0.)])
def test_integer_sat_rows_equal_original_fraction_for_random_boundary_engineering(scale, offset):
    rng = random.Random(51003)
    # Boundary contact, equal axes, general position, tiny exact perturbation.
    for skew in (0., 0.23, math.ulp(1.)):
        av = tuple(tuple(F(offset+scale*c) for c in p)
                   for p in ((0., 0., 0.), (1., 0., 0.),
                             (skew, 1., 0.), (0., 0., 1.)))
        bv = tuple(tuple(F(offset+scale*c) for c in p)
                   for p in ((0., 0., 0.), (0.7, 0., 0.),
                             (0., 0.9, 0.), (0., 0., 1.3)))
        rows = _fraction_rows(av, bv)
        queries = [tuple(F(scale*rng.uniform(-2, 2)) for _ in range(3)) for _ in range(80)]
        queries += [(F(0),)*3]
        queries += [tuple(b[k]-a[k] for k in range(3)) for a in av for b in bv]
        assert len(queries) == 97
        for x in queries:
            assert g03_exact.overlap(av, bv, x) == _fraction_overlap(rows, x), (skew, x)


def _eager_ee(A, ea, B, eb, tol=0., extent_tol=0.):
    """Old eager evaluation order, using pure Fraction dot/cross expressions."""
    c = covers3
    pa0, pb0 = c._qvector(A.verts[ea[0]]), c._qvector(B.verts[eb[0]])
    dA, dB = c._qedge(A, ea), c._qedge(B, eb)
    normal = _cross(dB, dA)
    if not any(normal):
        return None
    n = _cross(dA, dB)
    nn = _dot(n, n)
    w = c.sub(pb0, pa0)
    s, t = _dot(_cross(w, dB), n)/nn, _dot(_cross(w, dA), n)/nn
    for candidate in (normal, c.neg(normal)):
        sb, sa = c._qedge_contains(B, eb, candidate, tol), c._qedge_contains(A, ea, c.neg(candidate), tol)
        if sb < 0 or sa < 0:
            continue
        qa, qb = c.add(pa0, c.mul(dA, s)), c.add(pb0, c.mul(dB, t))
        unit_normal = c._qunit(candidate)
        gap = _dot(unit_normal, c._float_vector(c.sub(qa, qb)))
        inside = c._qparameter_in_extent(s, dA, extent_tol) and c._qparameter_in_extent(t, dB, extent_tol)
        if not 0 <= s <= 1:
            qa = c.add(pa0, c.mul(dA, c._qclamp(s)))
            qb = c.add(pb0, c.mul(dB, c._qclamp(_dot(c.sub(qa, pb0), dB)/_dot(dB, dB))))
        elif not 0 <= t <= 1:
            qb = c.add(pb0, c.mul(dB, c._qclamp(t)))
            qa = c.add(pa0, c.mul(dA, c._qclamp(_dot(c.sub(qb, pa0), dA)/_dot(dA, dA))))
        return c.Cover3('EE', ('edge', *ea), ('edge', *eb), unit_normal, gap,
                        c._float_vector(qa), c._float_vector(qb), (float(s), float(t)),
                        None, sb == 1 and sa == 1, inside)
    return None


@pytest.mark.parametrize('scale,offset', [(1., 0.), (1e-6, 1e6), (1e3, -1e5)])
@pytest.mark.parametrize('skew', [0., 0.23, math.ulp(1.)])
def test_deferred_edge_parameters_preserve_every_eager_fraction_cover(scale, offset, skew):
    base = geom3.box()
    def transform(p, second=False):
        x, y, z = p
        return tuple(offset + scale*c for c in (x+skew*y+(0.7 if second else 0.),
                                               y+skew*z+(0.2 if second else 0.), z))
    a = geom3.Polyhedron([transform(p) for p in base.verts], list(base.faces))
    b = geom3.Polyhedron([transform(p, True) for p in base.verts], list(base.faces))
    for ea in a.edges():
        for eb in b.edges():
            for tol in (0., 1e-7):
                assert covers3.ee_cover(a, ea, b, eb, tol) == _eager_ee(a, ea, b, eb, tol), (ea, eb, tol)


def _fraction_membership(a, b, point, tol):
    a, b = geom3.exact_convex_view(a), geom3.exact_convex_view(b)
    facets = covers3.local_facets3(a, b)
    point = tuple(map(F, point))
    tol2 = F(tol)**2 if tol > 0 else F(0)
    boundary = outside = near = False
    for n, p in covers3._planes(a, b, facets):
        value = _dot(n, tuple(x-y for x, y in zip(point, p)))
        if value > 0:
            outside = True
            if not tol2 or value*value > tol2*_dot(n, n):
                return -1
        elif value == 0:
            boundary = True
        if tol2 and value*value <= tol2*_dot(n, n):
            near = True
    if outside:
        points = tuple(tuple(F(y[k])-F(x[k])-point[k] for k in range(3))
                       for x in a.verts for y in b.verts)
        nearest = covers3._qclosest_hull(points)
        return 0 if _dot(nearest, nearest) <= tol2 else -1
    return 0 if boundary or near else 1


@pytest.mark.parametrize('scale,offset', [(1., 0.), (1e-6, 1e6), (1e3, -1e5)])
def test_integer_membership_rows_equal_fraction_random_boundary_and_corner_band(scale, offset):
    rng = random.Random(51004)
    a = geom3.box(center=(offset, offset, offset), half=(scale, scale, scale))
    b = geom3.box(center=(offset, offset, offset), half=(scale, scale, scale))
    queries = [tuple(F(scale*rng.uniform(-3, 3)) for _ in range(3)) for _ in range(80)]
    queries += [tuple(F(scale*c) for c in p)
                for p in ((0, 0, 0), (2, 0, 0), (2, 2, 2),
                          (2.1, 2.1, 0), (2.15, 2.15, 0), (1.9, 1.9, 0))]
    for x in queries:
        for tol in (0., scale*0.03, scale*0.2):
            assert covers3.membership_convex3(a, b, x, tol) == _fraction_membership(a, b, x, tol), (x, tol)


def test_extended_existing_plane_cache_tracks_objects_and_mutable_coordinates():
    a, b = geom3.box(), geom3.box()
    c = geom3.box(center=(10., -7., 3.))
    assert covers3.membership_convex3(a, b, (0., 0., 0.)) == 1
    assert covers3.membership_convex3(a, c, (0., 0., 0.)) == -1
    assert covers3.membership_convex3(a, c, (10., -7., 3.)) == 1
    # The existing cache is content-addressed, so no object identity is needed:
    # mutating an exactly canonical box changes the original key and its rows.
    c.verts[:] = [tuple(p[k]-[10., -7., 3.][k] for k in range(3)) for p in c.verts]
    assert covers3.membership_convex3(a, c, (0., 0., 0.)) == 1
    assert covers3.membership_convex3(a, c, (10., -7., 3.)) == -1
