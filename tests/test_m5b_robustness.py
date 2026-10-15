"""Independent closed forms for tube certificates; no geometry oracle imports.

Oracle imports: fractions.Fraction, itertools.product, math.comb only. Production
imports below are exclusively the subject under test; no root/overlap/projection
primitive is used to compute expected answers. Mutation support only edits code.
"""
from fractions import Fraction as F
from itertools import product
from math import comb

import pytest
from mutation_support import replace_module_callable
from m5c_teeth_oracle import translation_first_events
from eab.kernel2d import model_robustness as rob


def _example():
    a = ((-2, 0), (-1, F(-1, 2)), (0, 0), (-1, F(1, 2)))
    b = ((1, -2), (3, -2), (3, 2), (1, 2))
    return a, tuple((x+2, y) for x, y in a), b


def test_bernstein_independent_oracle():
    # Independent polynomial identity: explicitly expand every Bernstein basis
    # term, then compare the production enclosure with its convex hull.
    for b in ((F(2), F(-1), F(3)), tuple(F(k*k-7) for k in range(7))):
        n = len(b)-1
        coefficients = tuple(sum(b[i]*comb(n, i)*comb(n-i, k-i)*(-1)**(k-i)
                                 for i in range(k+1)) for k in range(n+1))
        assert rob.polynomial_range(coefficients, 0, 1) == (min(b), max(b))
        for s in (F(0), F(1, 7), F(1, 2), F(1)):
            expected = sum(b[i]*comb(n, i)*s**i*(1-s)**(n-i) for i in range(n+1))
            lo, hi = rob.polynomial_range(coefficients, s, s)
            assert lo == hi == expected, "Bernstein expansion exact value mismatch"


def test_no_contact_requires_strict_margin_and_covers_whole_window():
    a = ((0, 0), (1, 0), (0, 1))
    b = ((3, 0), (4, 0), (3, 1))
    aa, bb = rob.chord_paths(a, a), rob.chord_paths(b, b)
    assert rob.separation_certificate(aa, bb, F(1, 2), F(1, 2))["gap_lower"] == 2
    assert rob.separation_certificate(aa, bb, 1, 1) is None, "strict tube gap required"
    assert rob.swept_axis_bounds(aa) == ((F(0), F(1)), (F(0), F(1)))
    # Endpoints identical, but x(s)=x+16s(1-s) meets the other solid inside.
    bulge = tuple(((F(x), F(16), F(-16)), (F(y),), (F(1),)) for x, y in a)
    assert rob.separation_certificate(bulge, bb, panels=8) is None
    assert rob.swept_axis_bounds(bulge)[0][1] >= 5


def test_single_cover_certificate_has_independent_closed_form_oracle():
    a, end, b = _example()
    aa, bb = rob.chord_paths(a, end), rob.chord_paths(b, b)
    result = rob.single_cover_certificate(aa, bb, ("VE", 2, 3), (F(2, 5), F(3, 5)), F(1, 100), F(1, 100))
    assert result and result["label"] == ("VE", 2, 3)
    assert result["derivative_lower"] == 8
    # Closed-form oracle, independent of all production predicates: rightmost
    # diamond vertex x=2s+da meets the wall x=1+db, away from both wall endpoints.
    for da, db in product((F(-1, 100), F(0), F(1, 100)), repeat=2):
        shifted_a = tuple((x+da, y) for x, y in a)
        shifted_b = tuple((x+db, y) for x, y in b)
        t, labels = translation_first_events(shifted_a, shifted_b, (2, 0))
        assert t == (1+db-da)/2
        assert labels == (result["label"],), "independent oracle checks production label"
        assert result["bracket"][0] < t < result["bracket"][1], "independent oracle checks production bracket"
    reverse = rob.single_cover_certificate(bb, aa, ("EV", 3, 2), (F(2, 5), F(3, 5)), F(1, 100), F(1, 100))
    assert reverse and reverse["label"] == ("EV", 3, 2)


def test_single_cover_rejects_endpoint_uncertainty_and_competing_tie():
    a, end, b = _example()
    aa, bb = rob.chord_paths(a, end), rob.chord_paths(b, b)
    assert rob.single_cover_certificate(aa, bb, ("VE", 2, 3), (F(2, 5), F(51, 100)), F(1, 40), F(1, 40)) is None, \
        "a crossing not guaranteed inside the tube cannot be certified"
    # Vertical front edge: two simultaneous endpoint events cannot be stable as
    # an exact first-cover set under arbitrary positive coordinate perturbation.
    square = ((-1, -1), (0, -1), (0, 1), (-1, 1))
    moved = tuple((x+2, y) for x, y in square)
    assert rob.single_cover_certificate(rob.chord_paths(square, moved), bb, ("VE", 1, 3),
                                        (F(2, 5), F(3, 5)), F(1, 1000), F(1, 1000)) is None


@pytest.mark.parametrize("scale,offset,u", (
    (F(1), (0, 0), F(0)),
    (F(1, 2**120), (10**5, -10**6), F(2, 7)),
    (F(2**100), (-10**3, 10**5), F(-3, 8)),
))
def test_certificates_are_covariant_under_rotation_translation_and_units(scale, offset, u):
    a, end, b = _example()
    c, s = (1-u*u)/(1+u*u), 2*u/(1+u*u)
    def transform(ring):
        return tuple((offset[0]+scale*(c*x-s*y), offset[1]+scale*(s*x+c*y)) for x, y in ring)
    aa = rob.chord_paths(transform(a), transform(end))
    bb = rob.chord_paths(transform(b), transform(b))
    # Transform the original L-infinity tube conservatively as well as geometry.
    radius = scale*(abs(c)+abs(s))/10000
    result = rob.single_cover_certificate(aa, bb, ("VE", 2, 3), (F(49, 100), F(51, 100)),
                                          radius, radius, panels=8)
    assert result is not None and result["label"] == ("VE", 2, 3)
    assert result["derivative_lower"] > 0


def test_tube_margin_mutation_dies_on_semantics_not_hash(monkeypatch):
    replace_module_callable(monkeypatch, rob, "separation_certificate", [("gap > ra+rb", "gap >= ra+rb")])
    with pytest.raises(AssertionError, match="strict tube gap required"):
        test_no_contact_requires_strict_margin_and_covers_whole_window()


def test_crossing_error_mutation_dies_on_semantics_not_hash(monkeypatch):
    replace_module_callable(monkeypatch, rob, "single_cover_certificate", [("end[0][0] > end[3]", "end[0][0] > -end[3]")])
    with pytest.raises(AssertionError, match="crossing not guaranteed"):
        test_single_cover_rejects_endpoint_uncertainty_and_competing_tie()


@pytest.mark.parametrize("value", (0.5, True, "1/2"))
def test_robustness_inputs_reject_nonexact_numbers(value):
    with pytest.raises(ValueError, match="exact rationals"):
        rob.polynomial_range((value, 1), 0, 1)


def test_robustness_does_not_accept_invalid_windows_denominators_or_radii():
    a, end, b = _example()
    aa, bb = rob.chord_paths(a, end), rob.chord_paths(b, b)
    with pytest.raises(ValueError):
        rob.separation_certificate(aa, bb, -1)
    with pytest.raises(ValueError):
        rob.separation_certificate(aa, bb, hi=2)
    bad = tuple((p[0], p[1], (F(1), F(-2))) for p in aa)
    with pytest.raises(ValueError, match="positive denominator"):
        rob.separation_certificate(bad, bb)
