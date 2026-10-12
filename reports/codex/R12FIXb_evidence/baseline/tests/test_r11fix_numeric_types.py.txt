"""R11 K02: exact answers must not depend on numeric representation.

The oracles use only Python Fraction arithmetic: a shoelace determinant about
the first vertex, a three-column determinant, and analytic axis-aligned boxes.
They do not use production sign/vector/SAT/triangulation primitives.  Every
one of the reviewer's 3072 mixed-integer cases is checked, including zeros.
"""
from fractions import Fraction as F
import inspect
import itertools
import math

import pytest

from eab import predicates as pred
from eab.kernel2d import geom as g2
from eab.kernel3d import exact_geom as g3
from eab.kernel3d import geom3 as solid


def _sign(value):
    return (value > 0) - (value < 0)


def _area2(a, b, c):
    x, y = F(b[0]) - F(a[0]), F(b[1]) - F(a[1])
    u, v = F(c[0]) - F(a[0]), F(c[1]) - F(a[1])
    return x * v - y * u


def _det3(a, b, c, p):
    u = tuple(F(b[k]) - F(a[k]) for k in range(3))
    v = tuple(F(c[k]) - F(a[k]) for k in range(3))
    w = tuple(F(p[k]) - F(a[k]) for k in range(3))
    return (u[0] * (v[1] * w[2] - v[2] * w[1])
            - u[1] * (v[0] * w[2] - v[2] * w[0])
            + u[2] * (v[0] * w[1] - v[1] * w[0]))


def _review_cases():
    for exponent in (53, 54, 55, 60):
        for ax, bx in itertools.product(range(1, 17), repeat=2):
            for ay, by in ((3., 4.), (1., 2.), (7., 11.)):
                yield ((2**exponent + ax, ay), (2**exponent + bx, by),
                       (math.ldexp(1., exponent), 0.))


def test_mixed_integer_orientation_keeps_exact_negative_sign():
    n = 2**53
    points = ((n + 3, 3.), (n + 5, 4.), (2.**53, 0.))
    assert _area2(*points) == -3
    assert g2.orient2d(*points) == -1, 'mixed input must preserve the exact negative determinant'


def test_mixed_integer_orientation_keeps_exact_zero():
    n = 2**53
    points = ((n + 3, 3.), (n + 4, 4.), (2.**53, 0.))
    assert _area2(*points) == 0
    assert g2.orient2d(*points) == 0, 'mixed input must preserve exact collinearity'


def test_all_3072_review_integer_float_orientations_have_exact_signs():
    cases = list(_review_cases())
    assert len(cases) == 3072
    truths = [_sign(_area2(*points)) for points in cases]
    assert set(truths) == {-1, 0, 1}
    wrong = [(points, want, g2.orient2d(*points)) for points, want in zip(cases, truths)
             if g2.orient2d(*points) != want]
    assert not wrong, {'wrong': len(wrong), 'sign_reversals': sum(w != 0 for _, w, _ in wrong),
                       'exact_zero_errors': sum(w == 0 for _, w, _ in wrong), 'first': wrong[:3]}


def test_mixed_nondegenerate_triangle_is_not_silently_triangulated_to_empty():
    n = 2**53
    polygon = [(n + 2, 7.), (n + 3, 11.), (2.**53, 0.)]
    assert _area2(*polygon) == 1
    triangles = g2.triangulate(polygon)
    assert triangles == [(0, 1, 2)], 'a nonzero-area triangle must survive the actual ear-cut path'
    assert sum(_area2(*(polygon[i] for i in tri)) for tri in triangles) == 1


@pytest.mark.parametrize('exponent', [53, 55, 60, 1024, 4096])
@pytest.mark.parametrize('scale', [F(1, 10**400), F(1), F(10**400)])
def test_orientation_nonfloat_coordinates_need_not_fit_binary64(exponent, scale):
    n = 2**exponent
    # For scale==1 the x coordinates remain Python integers of arbitrary size.
    points = [(n + 3, 3.), (n + 5, 4.), (n, 0.)]
    if scale != 1:
        points = [tuple(F(v) * scale for v in p) for p in points]
    for a, b, c in itertools.permutations(points):
        assert g2.orient2d(a, b, c) == _sign(_area2(a, b, c))
    lifted = [(*p, 0) for p in points] + [(n, 0., scale)]
    for vertices in itertools.permutations(lifted):
        assert pred.orient3d(*vertices) == _sign(_det3(*vertices))


def test_orient3d_all_review_mixed_type_lifts_match_independent_determinants():
    counts = {-1: 0, 0: 0, 1: 0}
    for points in _review_cases():
        tetrahedron = [(*p, 0.) for p in points] + [(*points[2], 1.)]
        truth = _sign(_det3(*tetrahedron))
        counts[truth] += 1
        assert pred.orient3d(*tetrahedron) == truth, tetrahedron
    assert sum(counts.values()) == 3072 and min(counts.values()) > 0


@pytest.mark.parametrize('exponent', [1024, 4096])
def test_mixed_integer_float_subtraction_does_not_require_binary64_range(exponent):
    points = ((2**exponent, 1.), (0., 2.), (1., 0.))
    assert g2.orient2d(*points) == _sign(_area2(*points))


def _mixed_bilinear_cases():
    for n in (2**53, 2**60, 2**1024, 2**4096):
        for delta in (-1, 0, 1):
            for small in (1., math.ulp(0.), F(1, 10**400), F(10**400)):
                yield (n + delta, small), (n, small)
                yield (n + delta, small), (small, -n)
    yield (0, 0.), (F(1, 3), 2**4096)


def test_bilinear_predicates_preserve_all_mixed_numeric_types():
    cases = list(_mixed_bilinear_cases())
    assert len(cases) == 97
    signs = set()
    for a, b in cases:
        cross = F(a[0]) * F(b[1]) - F(a[1]) * F(b[0])
        dot = F(a[0]) * F(b[0]) + F(a[1]) * F(b[1])
        signs.update((_sign(cross), _sign(dot)))
        assert pred.cross2_sign(a, b) == _sign(cross), (a, b, 'cross')
        assert pred.dot2_sign(a, b) == _sign(dot), (a, b, 'dot')
    assert signs == {-1, 0, 1}


@pytest.mark.parametrize('offset', [2**53, 2**60, 2**1024, 2**4096])
@pytest.mark.parametrize('scale', [F(1, 10**400), F(1), F(10**400)])
def test_polygon_membership_interval_filters_and_sat_keep_mixed_values(offset, scale):
    # Exact analytic rectangle; x deliberately remains int when scale==1.
    x0, x1 = offset, offset + 8
    if scale != 1:
        x0, x1 = F(x0) * scale, F(x1) * scale
    y0, y1 = (0., 4.) if scale == 1 else (F(0), 4 * scale)
    polygon = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    for x, y, want in ((F(x0) - scale, 2 * scale, -1),
                       (F(x0) + 4 * scale, 2 * scale, 1),
                       (F(x0), 2 * scale, 0),
                       (F(x1), F(y1), 0)):
        assert g2.point_in_polygon((x, y), polygon) == want
        assert g3.polygon_locate((x, y, 0.), [(*p, 0) for p in polygon]) == want
    # Analytic overlap with boxes: strict, touching, separated.
    for step, want in ((7, 1), (8, 0), (9, -1)):
        shifted = [(F(x) + step * scale, y) for x, y in polygon]
        assert g2.polygons_overlap(polygon, shifted) == want
    assert g2._triangles_overlap(polygon[:3], polygon[:3], 0, polygon[0])


@pytest.mark.parametrize('offset', [2**53, 2**60, 2**1024, 2**4096])
def test_interval_conversion_contains_arbitrary_integer_and_rational_values(offset):
    for value in (offset - 1, offset, offset + 1, F(offset) + F(1, 3),
                  F(1, 10**400), -F(1, 10**400)):
        lower, upper = g3._iv(value)
        assert math.isinf(lower) or F(lower) <= F(value)
        assert math.isinf(upper) or F(value) <= F(upper)


@pytest.mark.parametrize('offset', [2**53, 2**4096])
@pytest.mark.parametrize('scale', [F(1, 10**400), F(1), F(10**400)])
def test_3d_separating_axes_and_hull_keep_mixed_numeric_values(offset, scale):
    vertices = [(offset + x, y, z) for x in (0, 8) for y in (0., 4.) for z in (0, 2)]
    if scale != 1:
        vertices = [tuple(F(v) * scale for v in p) for p in vertices]
    body = solid.Polyhedron(vertices, [])
    for delta, want in ((7, 1), (8, 0), (9, -1)):
        shifted = solid.Polyhedron([(F(x) + delta * scale, y, z) for x, y, z in vertices], [])
        assert solid.exact_convex_overlap(body, shifted) == want
    for x, want in ((offset - 1, -1), (offset + 4, 1), (offset, 0)):
        assert solid.exact_point_in_convex_polyhedron((F(x) * scale, scale, scale), body) == want


def test_numeric_type_gate_kills_reinstated_fraction_only_shortcut(monkeypatch):
    source = inspect.getsource(g2.orient2d)
    repaired = 'any(type(v) is not float for p in (a, b, c) for v in p)'
    assert source.count(repaired) == 1
    namespace = dict(g2.__dict__)
    mutant = source.replace(repaired, 'any(isinstance(v, Fraction) for p in (a, b, c) for v in p)')
    exec(compile(mutant, '<R11 K02 old Fraction-only type gate>', 'exec'), namespace)
    monkeypatch.setattr(g2, 'orient2d', namespace['orient2d'])
    with pytest.raises(AssertionError, match='exact negative determinant'):
        test_mixed_integer_orientation_keeps_exact_negative_sign()
    with pytest.raises(AssertionError, match='nonzero-area triangle'):
        test_mixed_nondegenerate_triangle_is_not_silently_triangulated_to_empty()
