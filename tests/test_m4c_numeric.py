"""Independent midpoint certificates for the public quadratic display.

Oracle imports: fractions.Fraction and math.nextafter/inf only. Hand-derived
x*x+a*x-a*a is evaluated at exact binary64 rounding-cell midpoints; it never
calls the tested radical sign, root enumeration or construction machinery.
These are scalar display tests, not a geometry or earliest-event oracle.
"""
from fractions import Fraction as F
from math import inf, nextafter

import pytest

from eab.kernel2d.motion import QuadraticTime
from eab.numeric_domain import ConstructionDomainError


@pytest.mark.parametrize("exponent", (-1070, 0, 1022))
@pytest.mark.parametrize("branch", (-1, 1))
def test_quadratic_display_has_independent_midpoint_certificate_at_three_output_tiers(exponent, branch):
    a = F(2)**exponent
    value = QuadraticTime(None, a, -a*a, branch)
    displayed = value.time
    lo = (F(nextafter(displayed, -inf))+F(displayed))/2
    hi = (F(nextafter(displayed, inf))+F(displayed))/2
    # The positive root has increasing P; the negative root decreasing P.
    assert branch*(lo*lo+a*lo-a*a) < 0, "algebraic output below upper half-cell"
    assert branch*(hi*hi+a*hi-a*a) > 0, "algebraic output above lower half-cell"
    assert value.certificate == {"rational": None, "polynomial": [str(-a*a), str(a), "1"], "branch": branch}


def test_quadratic_display_underflow_remains_backed_by_exact_certificate_and_overflow_is_loud():
    tiny = F(2)**-1200
    value = QuadraticTime(None, tiny, -tiny*tiny, 1)
    assert value.time == 0.0 and value.rational is None
    half_subnormal = F(1, 2**1075)
    assert -tiny*tiny < 0 < half_subnormal**2+tiny*half_subnormal-tiny*tiny
    huge = F(2)**1025
    with pytest.raises(ConstructionDomainError):
        QuadraticTime(None, huge, -huge*huge, 1).time
    # Binary64-exact rational values have their own final-construction path.
    for exponent in (-1074, 0, 1023):
        rational = F(2)**exponent
        result = QuadraticTime(rational)
        assert F(result.time) == rational
        assert result.certificate == {"rational": str(rational), "polynomial": None, "branch": 0}
