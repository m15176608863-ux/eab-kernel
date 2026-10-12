"""Independent reference boundary for G0 and test-owned exact oracles.

This module imports neither production constructions nor geometry. Decimal /
float arithmetic supplies candidates only; Fraction midpoint cells certify
every answer. Uncertified candidates fall back to ordered binary64 bit-pattern
search, unlike the production integer-significand/isqrt construction. This
independent reference path is shared by oracles, not the implementation tested.
Support contract: docs/exact_predicates_plan.md, R13FIXb. This exact boundary
retains its full representable-output domain; no +/-400 input restriction.
"""
from decimal import Decimal, DecimalException, localcontext
from fractions import Fraction
from functools import lru_cache
import math
import struct

from .numeric_domain import ConstructionDomainError


_MAX_BITS = 0x7fefffffffffffff
_SUCCESSOR_OF_MAX = Fraction(2)**1024


def _from_bits(bits):
    return struct.unpack(">d", struct.pack(">Q", bits))[0]


def _bits(value):
    return struct.unpack(">Q", struct.pack(">d", value))[0]


def _candidate_positive(value, power):
    """Approximation only; _candidate_is_certified must approve every return."""
    try:
        if power == 1:
            return float(value)
        with localcontext() as context:
            context.prec = 80
            return float((Decimal(value.numerator)/Decimal(value.denominator)).sqrt())
    except (OverflowError, ValueError, DecimalException):
        return None


def _candidate_is_certified(value, power, result):
    """Prove the candidate's full RN-even cell using only exact comparisons."""
    if result is None or not math.isfinite(result) or result < 0:
        return False
    even = _bits(result) % 2 == 0
    center = Fraction(result)
    if result:
        lower = ((Fraction(math.nextafter(result, 0.0))+center)/2)**power
        if value < lower or (value == lower and not even):
            return False
    upper_float = math.nextafter(result, math.inf)
    upper = ((center+(Fraction(upper_float) if math.isfinite(upper_float)
                     else _SUCCESSOR_OF_MAX))/2)**power
    return value < upper or (value == upper and even)


@lru_cache(maxsize=8192)
def _round_positive(value, power, allow_underflow):
    # Candidates do not decide the answer. A failed exact midpoint certificate
    # resumes the original independent bit search, including range checks.
    candidate = _candidate_positive(value, power)
    if _candidate_is_certified(value, power, candidate):
        if value and candidate == 0 and not allow_underflow:
            raise ConstructionDomainError("oracle construction", "nonzero value is below binary64 output range")
        return candidate
    lower, upper = 0, _MAX_BITS
    while lower < upper:
        middle = (lower+upper+1)//2
        if Fraction(_from_bits(middle))**power <= value:
            lower = middle
        else:
            upper = middle-1
    low = _from_bits(lower)
    high_exact = (Fraction(_from_bits(lower+1)) if lower < _MAX_BITS
                  else _SUCCESSOR_OF_MAX)
    midpoint = (Fraction(low)+high_exact)/2
    boundary = midpoint**power
    go_up = value > boundary or (value == boundary and lower % 2)
    if go_up and lower == _MAX_BITS:
        raise ConstructionDomainError("oracle construction", "exact value exceeds finite binary64 range")
    answer = _from_bits(lower+1) if go_up else low
    if value and answer == 0 and not allow_underflow:
        raise ConstructionDomainError("oracle construction", "nonzero value is below binary64 output range")
    return answer


def scalar_exact(value, *, allow_underflow=False):
    # A supplied binary64 is already an exact representable value, so this
    # identity path needs no search; non-finite inputs still fail loudly.
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("oracle scalar input must be finite")
        return value
    value = Fraction(value)
    result = _round_positive(abs(value), 1, allow_underflow)
    return -result if value < 0 else result


def ratio_exact(numerator, denominator, *, allow_underflow=False):
    return scalar_exact(Fraction(numerator)/Fraction(denominator),
                        allow_underflow=allow_underflow)


def vector_exact(values, *, allow_underflow=False):
    return tuple(scalar_exact(x, allow_underflow=allow_underflow) for x in values)


def sqrt_exact(value, *, allow_underflow=False):
    value = Fraction(value)
    if value < 0:
        raise ValueError("square root of negative rational")
    return _round_positive(value, 2, allow_underflow)


def norm_exact(values, *, allow_underflow=False):
    return sqrt_exact(sum(Fraction(x)**2 for x in values),
                      allow_underflow=allow_underflow)


def unit_exact(values, *, allow_underflow=False):
    values = tuple(Fraction(x) for x in values)
    squared = sum(x*x for x in values)
    if not squared:
        raise ZeroDivisionError("unit of zero vector")
    return tuple((-1 if x < 0 else 1)*sqrt_exact(x*x/squared,
                 allow_underflow=allow_underflow) for x in values)


def assert_sqrt_rounding(actual, squared, message="exact root midpoint certificate"):
    """Certify a returned float directly, without constructing an expected root."""
    squared = Fraction(squared)
    assert math.isfinite(actual) and actual >= 0 and squared >= 0, message
    even = _bits(actual) % 2 == 0
    if actual:
        lower = (Fraction(math.nextafter(actual, 0.0))+Fraction(actual))/2
        assert squared > lower*lower or (even and squared == lower*lower), message
    above = math.nextafter(actual, math.inf)
    upper = (Fraction(actual)+(Fraction(above) if math.isfinite(above)
                               else _SUCCESSOR_OF_MAX))/2
    assert squared < upper*upper or (even and squared == upper*upper), message

