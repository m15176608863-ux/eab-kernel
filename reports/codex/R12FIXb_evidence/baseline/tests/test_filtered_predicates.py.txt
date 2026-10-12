"""Filters versus an independent pure-Fraction expansion; no shared primitives.

The oracle expands coordinate differences about a (production expands about p)
and never calls a production sign/vector/determinant helper.  Every generated
case is checked, including exact zeros and subnormal/overflow intermediates.
"""

from fractions import Fraction as F
import math
import random

from eab import predicates as pred


def _orientation(a, b, c, p):
    u = [F(b[k]) - F(a[k]) for k in range(3)]
    v = [F(c[k]) - F(a[k]) for k in range(3)]
    w = [F(p[k]) - F(a[k]) for k in range(3)]
    d = ((u[1] * v[2] - u[2] * v[1]) * w[0]
         + (u[2] * v[0] - u[0] * v[2]) * w[1]
         + (u[0] * v[1] - u[1] * v[0]) * w[2])
    return (d > 0) - (d < 0)


# Generated with Random(54031), draw 21.  A 0.1*Shewchuk bound accepts -1,
# although the determinant for these exact binary64 inputs is positive.
SHRUNK_BOUND_WITNESS = (
    (-0.8912983977775468, -0.7882294486878267, -0.8329292498683749),
    (0.7030062716913941, 0.4470157166494193, 1.0641196902903194),
    (1.371703294522026, -1.0703963362466453, -0.9415752128350756),
    (-1.178918572957056, 0.8367847723865847, 1.3679508826678572),
)


def test_orient3d_filter_vs_fraction_shrunken_bound_witness():
    assert _orientation(*SHRUNK_BOUND_WITNESS) == 1
    assert pred.orient3d(*SHRUNK_BOUND_WITNESS) == 1


def test_orient3d_filter_vs_fraction_random_degenerate_engineering():
    rng = random.Random(502231)
    counts = {-1: 0, 0: 0, 1: 0}
    for scale in (1e-100, 1e-3, 1.0, 1e3, 1e100):
        for offset in (0.0, 1e3, 1e5, 1e6):
            for k in range(250):
                pts = [tuple(offset + scale * rng.uniform(-3, 3) for _ in range(3)) for _ in range(4)]
                if k % 3 == 0:
                    u, v = rng.uniform(-2, 2), rng.uniform(-2, 2)
                    pts[3] = tuple(pts[0][j] + u * (pts[1][j] - pts[0][j])
                                   + v * (pts[2][j] - pts[0][j]) for j in range(3))
                if k % 17 == 0:
                    pts[3] = pts[1]
                truth = _orientation(*pts)
                assert pred.orient3d(*pts) == truth, pts
                counts[truth] += 1
    assert sum(counts.values()) == 5000 and min(counts.values()) > 0


def test_orient3d_filter_vs_fraction_underflow_and_overflow():
    rng = random.Random(77689)
    count = 0
    for scales in ((1e-160, 1e-160, 1e300), (1e-200, 1e-200, 1e200),
                   (1e-110,) * 3, (1e150,) * 3, (1e300,) * 3,
                   (math.ulp(0.0), 1e100, 1e200)):
        for k in range(250):
            pts = [tuple(rng.uniform(-2, 2) * s for s in scales) for _ in range(4)]
            if k % 2:
                pts[3] = tuple(pts[0][j] + .4 * (pts[1][j] - pts[0][j])
                               + .7 * (pts[2][j] - pts[0][j]) for j in range(3))
            assert pred.orient3d(*pts) == _orientation(*pts), pts
            count += 1
    assert count == 1500


def test_orient3d_filter_preserves_rational_derived_coordinates():
    rng = random.Random(29225)
    count = 0
    for scale in (F(1, 10**400), F(1, 10**100), F(1), F(10**100), F(10**400)):
        for k in range(160):
            pts = [tuple(F(rng.randrange(-100, 101), rng.randrange(1, 50)) * scale for _ in range(3)) for _ in range(4)]
            if k % 2:
                pts[3] = tuple((pts[0][j] + pts[1][j] + pts[2][j]) / 3 for j in range(3))
                if k % 5:
                    pts[3] = (pts[3][0], pts[3][1], pts[3][2] + scale / 10**100)
            assert pred.orient3d(*pts) == _orientation(*pts), pts
            count += 1
    assert count == 800


def test_bilinear_filters_vs_fraction_all_cases():
    rng = random.Random(69407)
    count = 0
    for scale in (1e-300, 1e-160, 1e-3, 1., 1e5, 1e150, 1e300):
        for k in range(350):
            a = tuple(F(rng.uniform(-2, 2) * scale) for _ in range(2))
            b = tuple(F(rng.uniform(-2, 2) * scale) for _ in range(2))
            if k % 3 == 0:
                b = a
            elif k % 3 == 1:
                b = (a[0] / 3, a[1] / 3 + F(scale) / 10**100)
            cross = a[0] * b[1] - a[1] * b[0]
            dot = a[0] * b[0] + a[1] * b[1]
            assert pred.cross2_sign(a, b) == (cross > 0) - (cross < 0)
            assert pred.dot2_sign(a, b) == (dot > 0) - (dot < 0)
            count += 1
    # Input conversion underflow amplified by a very large other operand.
    for a, b in (((F(1, 10**400), F(1, 10**401)), (F(10**300), F(10**301))),
                 ((F(10**400), F(10**400)), (F(1), F(-1)))):
        cross = a[0] * b[1] - a[1] * b[0]
        dot = a[0] * b[0] + a[1] * b[1]
        assert pred.cross2_sign(a, b) == (cross > 0) - (cross < 0)
        assert pred.dot2_sign(a, b) == (dot > 0) - (dot < 0)
    assert count == 2450


def test_orient3d_filter_has_a_real_fast_path(monkeypatch):
    def forbidden(*args):
        raise AssertionError("well-separated determinant must be certified without Fraction arithmetic")
    monkeypatch.setattr(pred, "orient3d_fraction", forbidden)
    for ctor in (float, F):
        pts = [tuple(map(ctor, q)) for q in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))]
        assert pred.orient3d(*pts) == 1
