"""Checked floating constructions from exact scalars, not branch predicates."""
from fractions import Fraction
import math
import struct


def sqrt_rational(value, *, allow_underflow=False):
    """Correctly round an exact nonnegative square without rounding it first.

    Power-of-two scaling supplies a candidate, then exact adjacent midpoints
    choose round-to-nearest, ties-to-even. A nonzero result outside the finite
    nonzero binary64 range raises rather than silently returning zero/infinity.
    allow_underflow is only for displays accompanied by an exact certificate.
    Gate: test_r6fix_construction::test_rational_sqrt_rounds_only_the_final_root.
    """
    value = Fraction(value)
    if value < 0:
        raise ValueError("square root of negative rational")
    if not value:
        return 0.0
    exponent = (value.numerator.bit_length()-value.denominator.bit_length())//2
    scaled = value / (Fraction(2)**(2*exponent))
    candidate = math.ldexp(math.sqrt(float(scaled)), exponent)
    if not math.isfinite(candidate):
        raise OverflowError("exact root is outside finite binary64 range")
    # Bracket the root by adjacent floats; the scaled candidate is within a
    # couple of ulps, including gradual underflow at the final conversion.
    while Fraction(candidate)**2 > value:
        candidate = math.nextafter(candidate, -math.inf)
    upper = math.nextafter(candidate, math.inf)
    while math.isfinite(upper) and Fraction(upper)**2 <= value:
        candidate, upper = upper, math.nextafter(upper, math.inf)
    if not math.isfinite(upper):
        if Fraction(candidate)**2 == value:
            return candidate
        raise OverflowError("exact root exceeds largest finite binary64")
    midpoint2 = ((Fraction(candidate)+Fraction(upper))/2)**2
    even = not (struct.unpack(">Q", struct.pack(">d", candidate))[0] & 1)
    result = candidate if value < midpoint2 or (value == midpoint2 and even) else upper
    if result == 0 and not allow_underflow:
        raise ArithmeticError("nonzero exact root is below binary64 output range")
    return result
