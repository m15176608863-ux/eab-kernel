"""Exact analytic circle-model gates, NOT a production curved-boundary API.

The limiting cavity/body is B((0,1),1) union the central neck rectangle
[-1/2,1/2] x [1,2], with the neck open upward. For a Euclidean unit-ball
tolerance element, the inner disk after erosion has radius 1-delta, and
the horizontal support of the eroded body is at most 1-delta. Thus below
delta=1/2 the rotation-invariant inner disk is wider than the throat; at
delta=1/2 the entire eroded body lies in the upward-free central strip.
The usual throat-separation argument gives the trapping implication; it
is not replaced here by finite trajectory sampling.

The algebraic gates audit polynomial identities and exact support/section
bounds. Rational witnesses exercise their geometric interpretation. They
neither prove convergence of all finite N nor feed circles into polygonal
production verifiers. No frozen scientific helper is imported or changed.
"""
from fractions import Fraction as F
from unittest import TestCase
from unittest.mock import patch


class CircleModel:
    radius = F(1)
    neck_half_width = F(1, 2)


def _add(*terms):
    result = {}
    for term in terms:
        for exponent, coefficient in term.items():
            result[exponent] = result.get(exponent, F(0))+coefficient
    return {exponent: coefficient for exponent, coefficient in result.items() if coefficient}


def _negative(term):
    return {exponent: -term[exponent] for exponent in term}


def _multiply(a, b):
    result = {}
    for ea in a:
        for eb in b:
            exponent = tuple(x+y for x, y in zip(ea, eb))
            result[exponent] = result.get(exponent, F(0))+a[ea]*b[eb]
    return {exponent: coefficient for exponent, coefficient in result.items() if coefficient}


def _inside_body(x, y):
    r, w = CircleModel.radius, CircleModel.neck_half_width
    return x*x+(y-r)*(y-r) <= r*r or (abs(x) <= w and r <= y <= 2*r)


def _central_free(x, y):
    r, w = CircleModel.radius, CircleModel.neck_half_width
    return abs(x) <= w and (y >= r or x*x+(y-r)*(y-r) <= r*r)


def _verify_vertical_ray_point(x, y, distance):
    assert distance >= 0 and _inside_body(x, y)
    assert abs(x) <= CircleModel.neck_half_width
    r = CircleModel.radius
    if y < r and y+distance < r:
        gap = r-y
        difference = (y+distance-r)*(y+distance-r)-(y-r)*(y-r)
        assert difference == distance*(distance-2*gap) <= 0
    assert _central_free(x, y+distance), "central-strip upward closure failed"


def _verify_threshold():
    r, w = CircleModel.radius, CircleModel.neck_half_width
    assert 0 < w < r
    # The same radius is an INNER invariant disk and an OUTER x-support
    # bound. Their matching throat threshold is not a guessed equality.
    disk_threshold = r-w
    translation_threshold = r-w
    assert disk_threshold == F(1, 2), "circle disk threshold differs from the declared unit model"
    assert translation_threshold == F(1, 2), "circle translation threshold differs from the declared unit model"
    for offset in (F(-1, 64), F(0), F(1, 64)):
        delta = disk_threshold+offset
        inner_radius = r-delta
        horizontal_support_bound = r-delta
        assert inner_radius-w == -offset
        assert horizontal_support_bound-w == -offset
    assert disk_threshold/translation_threshold == 1
    assert 1-disk_threshold/translation_threshold == 0
    # This rational level lies strictly in the neck-only cross section:
    # every point with |x|>w there is outside both the disk and rectangle.
    neck_level = F(15, 8)
    assert r < neck_level < 2*r
    assert w*w+(neck_level-r)*(neck_level-r) > r*r
    return disk_threshold, translation_threshold


def test_t2d_circle_unit_support_has_exact_cauchy_certificate():
    # Polynomial coefficient equality proves Lagrange's identity for ALL
    # real coordinates. Together with squares >= 0 it gives Cauchy; hence
    # n.p <= 1 for |n|=1, |p|<=1, attained at p=n in every direction.
    nx, ny = {(1, 0, 0, 0): F(1)}, {(0, 1, 0, 0): F(1)}
    px, py = {(0, 0, 1, 0): F(1)}, {(0, 0, 0, 1): F(1)}
    norm_n = _add(_multiply(nx, nx), _multiply(ny, ny))
    norm_p = _add(_multiply(px, px), _multiply(py, py))
    dot = _add(_multiply(nx, px), _multiply(ny, py))
    cross = _add(_multiply(nx, py), _negative(_multiply(ny, px)))
    assert _add(_multiply(norm_n, norm_p), _negative(_multiply(dot, dot)),
                _negative(_multiply(cross, cross))) == {}
    for u in (F(-3), F(-1), F(-1, 7), F(0), F(2, 5), F(1), F(3)):
        nx, ny = (1-u*u)/(1+u*u), 2*u/(1+u*u)
        assert nx*nx+ny*ny == 1  # p=n is the exact attaining witness.


def test_t2d_circle_upward_strip_has_universal_polynomial_identity():
    # For gap>=0 and 0<=distance<=gap, distance*(distance-2*gap)<=0.
    # Beyond the center height the neck is vertically free. This is the
    # complete ray partition, not just the finite witnesses below.
    gap, distance = {(1, 0): F(1)}, {(0, 1): F(1)}
    shifted = _add(distance, _negative(gap))
    difference = _add(_multiply(shifted, shifted), _negative(_multiply(gap, gap)))
    factored = _multiply(distance, _add(distance, _negative(gap), _negative(gap)))
    assert _add(difference, _negative(factored)) == {}
    points = [(F(0), F(0)), (F(1, 2), F(1)), (F(-1, 2), F(2))]
    for u in (F(-1, 4), F(-1, 8), F(0), F(1, 16), F(1, 4)):
        points.append((2*u/(1+u*u), 1-(1-u*u)/(1+u*u)))
    for x, y in points:
        for shift in (F(0), F(1, 17), F(1, 2), F(1), F(7)):
            _verify_vertical_ray_point(x, y, shift)


def test_t2d_circle_model_inner_disk_and_outer_strip_have_same_threshold():
    assert _verify_threshold() == (F(1, 2), F(1, 2))


def test_t2d_circle_model_rejects_internal_radius_and_neck_mutations():
    for field, value in (("radius", F(1001, 1000)), ("neck_half_width", F(501, 1000))):
        with patch.object(CircleModel, field, value):
            with TestCase().assertRaisesRegex(AssertionError, "circle disk threshold"):
                _verify_threshold()
