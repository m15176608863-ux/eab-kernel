"""PD fast-query gates.

Primary oracle imports only fractions.Fraction: the exact Cartesian obstacle
of two rectangles is [Bx_min-Ax_max,Bx_max-Ax_min] times the analogous y
interval.  Its side projections and the tight-slot rectangular union below
are calculated directly, without production cross/dot/clip/decomposition,
point-in-polygon, segment-distance, boundary or normal-cone primitives.
GlobalEntrance2 comparisons are consistency evidence, not primary oracles.
"""
from fractions import Fraction as F

import pytest

from eab.kernel2d.global_entrance import GlobalEntrance2
from eab.kernel2d import motion_exit as module
from eab.kernel2d.motion_exit import shortest_exit_fast


SQUARE = ((0, 0), (1, 0), (1, 1), (0, 1))
L = ((0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3))
U = ((-1, -1), (2, -1), (2, 2), (1, 2), (1, 0), (0, 0), (0, 2), (-1, 2))
PIN = ((0, F(1, 2)), (1, F(1, 2)), (1, F(3, 2)), (0, F(3, 2)))
TIERS = (F(2)**-400, F(1), F(2)**397)


def rectangle(x0, y0, x1, y1):
    return ((F(x0), F(y0)), (F(x1), F(y0)), (F(x1), F(y1)), (F(x0), F(y1)))


def scale(poly, factor):
    return tuple((factor*x, factor*y) for x, y in poly)


def rectangle_answer(bounds, x):
    lo, bottom, hi, top = bounds
    choices = ((lo, x[1]), (hi, x[1]), (x[0], bottom), (x[0], top))
    distances = [((p[0]-x[0])**2+(p[1]-x[1])**2, p) for p in choices]
    best = min(value for value, point in distances)
    return best, tuple(sorted({point for value, point in distances if value == best}))


@pytest.mark.parametrize("factor", TIERS)
def test_fast_exit_matches_independent_rectangle_and_tight_seam_formulas(factor):
    """Three scales; zero/two/four-way ties and an asymmetric reference."""
    A, B = scale(rectangle(0, 0, 2, 1), factor), scale(rectangle(-1, 0, 2, 3), factor)
    bounds = tuple(factor*v for v in (-3, -1, 2, 3))
    for x in ((F(0), F(0)), (factor*F(1, 3), factor*F(1, 7)), (2*factor, 0)):
        got = shortest_exit_fast(A, B, x)
        square, points = rectangle_answer(bounds, x)
        assert got.squared == square, "Cartesian closed-form squared distance"
        assert got.tied_exact_points == points, "Cartesian closed-form complete minimizers"
        assert got.exact_point == points[0]
    got = shortest_exit_fast(scale(PIN, factor), scale(U, factor))
    assert got.squared == F(9, 4)*factor*factor, "tight seam is not exterior boundary"
    assert got.tied_exact_points == ((F(0), F(3, 2)*factor),)
    assert F(got.distance) == F(3, 2)*factor
    assert tuple(F(c) for c in got.point) == (F(0), F(3, 2)*factor)


@pytest.mark.parametrize("A,B", ((SQUARE, SQUARE), (SQUARE, L), (PIN, U),
                               (((0, 0), (2, 0), (1, 2)), ((-1, 0), (1, -1), (2, 2)))))
def test_fast_exit_equals_m3_complete_ties(A, B):
    model = GlobalEntrance2(A, B)
    for x in ((F(0), F(0)), (F(1, 10), F(1, 5))):
        assert model.membership(x) >= 0, "every constructed consistency case must exercise PD"
        old = model.shortest_exit(x)
        got = shortest_exit_fast(model, x=x)
        assert got.squared == old.squared, "M3 exact squared distance"
        assert got.tied_exact_points == old.tied_exact_points, "M3 complete nearest set"
        assert got.exact_point == old.exact_point


def test_closed_outward_coverage_removes_seams_full_cover_and_isolated_gaps():
    a, b = (F(0), F(0)), (F(2), F(0))
    same_side = rectangle(0, 0, 2, 1)
    opposite_side = rectangle(0, -1, 2, 0)
    assert tuple(module._exposed_parameters(a, b, (same_side,))) == ((0, 1),)
    assert tuple(module._exposed_parameters(a, b, (same_side, opposite_side))) == ()
    assert tuple(module._exposed_parameters(a, b, (rectangle(-1, -1, 3, 1),))) == ()
    left, right = rectangle(0, -1, 1, 0), rectangle(1, -1, 2, 0)
    assert tuple(module._exposed_parameters(a, b, (left, right))) == (), "isolated parameter gap is not an exposed segment"
    assert tuple(module._exposed_parameters(a, b, (left,))) == ((F(1, 2), F(1)),)


@pytest.mark.parametrize("factor", (F(1, 10**9), F(1), F(10**8)))
@pytest.mark.parametrize("translation", (0, 10**3, 10**5, 10**6))
def test_fast_exit_is_rigid_and_unit_covariant(factor, translation):
    baseline = shortest_exit_fast(SQUARE, SQUARE)
    for cosine, sine in ((F(0), F(1)), (F(3, 5), F(4, 5))):
        def linear(p):
            return factor*(cosine*p[0]-sine*p[1]), factor*(sine*p[0]+cosine*p[1])
        def affine(poly):
            return tuple((linear(p)[0]+translation, linear(p)[1]-3*translation) for p in poly)
        got = shortest_exit_fast(affine(SQUARE), affine(SQUARE))
        assert got.squared == factor*factor*baseline.squared
        assert set(got.tied_exact_points) == {linear(p) for p in baseline.tied_exact_points}, "set-valued rigid/unit covariance"


def _seam_guard():
    assert shortest_exit_fast(PIN, U).squared == F(9, 4), "tight seam is not exterior boundary"


def _tie_guard():
    got = shortest_exit_fast(SQUARE, SQUARE)
    assert set(got.tied_exact_points) == {(-1, 0), (1, 0), (0, -1), (0, 1)}, "all tied minimizers must survive lower-bound pruning"


@pytest.mark.parametrize("defect", ("ignore_closed_outward", "prune_equal_bound"))
def test_fast_exit_internal_defects_fail_the_intended_assertion(monkeypatch, defect):
    if defect == "ignore_closed_outward":
        guard, message = _seam_guard, "tight seam is not exterior boundary"
        guard()
        monkeypatch.setattr(module, "_covers_outward_parallel", lambda orient, slope: orient > 0)
    else:
        guard, message = _tie_guard, "all tied minimizers must survive lower-bound pruning"
        guard()
        monkeypatch.setattr(module, "_strictly_worse", lambda bound, best: best is not None and bound >= best)
    with pytest.raises(AssertionError, match=message):
        guard()


def test_fast_exit_invalid_domain_fails_loudly_and_does_not_build_arrangement(monkeypatch):
    with pytest.raises(ValueError, match="point of E"):
        shortest_exit_fast(SQUARE, rectangle(5, 5, 6, 6))
    with pytest.raises(ValueError, match="both A and B"):
        shortest_exit_fast(SQUARE)
    model = GlobalEntrance2(SQUARE, SQUARE)
    with pytest.raises(ValueError, match="B must be omitted"):
        shortest_exit_fast(model, SQUARE)
    def forbidden(self):
        raise AssertionError("full arrangement must not be constructed")
    monkeypatch.setattr(GlobalEntrance2, "boundary", property(forbidden))
    _tie_guard()
