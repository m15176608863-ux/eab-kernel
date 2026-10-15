"""The checked boundary from exact scalars/vectors to binary64 constructions.

Every result is rounded once, to nearest with ties to even. Exact nonzero
results that round to zero raise unless ``allow_underflow=True`` explicitly
marks a display backed by an exact certificate. Finite overflow always raises.
These constructors never decide geometry. Fraction midpoint certificates in
``test_r9fix_construction_rounding`` independently verify the boundary.
Support domains and named failures: docs/exact_predicates_plan.md (R13FIXb).
"""
from fractions import Fraction
import math
import struct
from .numeric_domain import ConstructionDomainError, exact_input


def scalar_rational(value, *, allow_underflow=False, quantity="scalar_rational result"):
    """Correctly rounded rational scalar, with explicit output-range checks."""
    exact = exact_input(value, quantity)
    try:
        result = float(exact)
    except OverflowError:
        raise ConstructionDomainError(quantity, "exact scalar is outside finite binary64 range") from None
    if not math.isfinite(result):
        raise ConstructionDomainError(quantity, "exact scalar is outside finite binary64 range")
    if exact and result == 0 and not allow_underflow:
        raise ConstructionDomainError(quantity, "nonzero exact scalar is below binary64 output range")
    return result


def scalar_algebraic(compare, *, allow_underflow=False):
    """Round a real given an exact rational comparison callback, once.

    ``compare(q)`` is sign(real-q). Binary64 bit search brackets the real;
    exact rational half-cell comparison implements round-to-nearest-even.
    No floating approximation is used to choose the root or decide geometry.
    Gate: test_m5a_algebraic.py (independent rational midpoint certificates).
    """
    sign = compare(Fraction(0))
    if not sign:
        return 0.0
    if sign < 0:
        return -scalar_algebraic(lambda q: -compare(-q), allow_underflow=allow_underflow)

    def from_bits(bits):
        return struct.unpack(">d", struct.pack(">Q", bits))[0]

    lo, hi = 0, 0x7fefffffffffffff
    maximum = from_bits(hi)
    if compare(Fraction(maximum)) > 0:
        midpoint = (Fraction(maximum)+Fraction(2)**1024)/2
        if compare(midpoint) >= 0:
            raise ConstructionDomainError("scalar_algebraic result", "exact real exceeds finite binary64 range")
        return maximum
    while lo < hi:
        middle = (lo+hi+1)//2
        if compare(Fraction(from_bits(middle))) >= 0:
            lo = middle
        else:
            hi = middle-1
    lower = from_bits(lo)
    if not compare(Fraction(lower)):
        return lower
    upper = from_bits(lo+1)
    order = compare((Fraction(lower)+Fraction(upper))/2)
    result = lower if order < 0 or (order == 0 and lo % 2 == 0) else upper
    if not result and not allow_underflow:
        raise ConstructionDomainError("scalar_algebraic result", "nonzero exact real is below binary64 output range")
    return result


def ratio_rational(numerator, denominator, *, allow_underflow=False):
    """Divide exact inputs before the sole final scalar conversion."""
    return scalar_rational(exact_input(numerator, "ratio numerator")/exact_input(denominator, "ratio denominator"),
                           allow_underflow=allow_underflow, quantity="ratio_rational result")


def vector_rational(values, *, allow_underflow=False):
    """Round final coordinates only; not an intermediate to norm/unit."""
    return tuple(scalar_rational(x, allow_underflow=allow_underflow,
                                quantity=f"vector_rational component[{i}]") for i, x in enumerate(values))


def sqrt_rational(value, *, allow_underflow=False):
    """Round an exact nonnegative square using integer square root/midpoints.

    No floating square, intermediate root, scale factor or component is ever
    constructed. ``isqrt(floor(n/d))`` is the exact lower integer root. The
    midpoint test is ``4*n`` versus ``d*(2*k+1)**2``; parity resolves ties.
    The final ``ldexp`` sees an exactly representable integer significand.
    Gate: test_rational_sqrt_rounds_only_the_final_root and the R9 midpoint grid.
    """
    value = exact_input(value, "sqrt_rational radicand")
    if value < 0:
        raise ValueError("square root of negative rational")
    if not value:
        return 0.0
    numerator, denominator = value.numerator, value.denominator
    exponent = numerator.bit_length() - denominator.bit_length()
    if (numerator < denominator << exponent if exponent >= 0
            else numerator << -exponent < denominator):
        exponent -= 1
    root_exponent = exponent // 2
    if root_exponent > 1023:
        raise ConstructionDomainError("sqrt_rational result", "exact root is outside finite binary64 range")
    quantum = max(root_exponent - 52, -1074)
    if quantum >= 0:
        denominator <<= 2*quantum
    else:
        numerator <<= -2*quantum
    lower = math.isqrt(numerator // denominator)
    comparison = 4*numerator - denominator*(2*lower+1)**2
    significand = lower + (comparison > 0 or (comparison == 0 and lower % 2 == 1))
    if not significand and not allow_underflow:
        raise ConstructionDomainError("sqrt_rational result", "nonzero exact root is below binary64 output range")
    try:
        result = math.ldexp(float(significand), quantum)
    except OverflowError:
        raise ConstructionDomainError("sqrt_rational result", "exact root is outside finite binary64 range") from None
    if not math.isfinite(result):
        raise ConstructionDomainError("sqrt_rational result", "exact root is outside finite binary64 range")
    return result


def norm_rational(values, *, allow_underflow=False):
    """Exact sum of squares followed by one correctly rounded root."""
    return sqrt_rational(sum(exact_input(x, "norm_rational component")**2 for x in values),
                         allow_underflow=allow_underflow)


def unit_rational(values, *, allow_underflow=False):
    """Round each exact unit component; the unscaled norm need not fit a float."""
    exact = tuple(exact_input(x, "unit_rational component") for x in values)
    squared = sum(x*x for x in exact)
    if not squared:
        raise ZeroDivisionError("unit of zero vector")
    return tuple((-1 if x < 0 else 1)*sqrt_rational(x*x/squared,
                 allow_underflow=allow_underflow) for x in exact)


def normalized_difference_rational(c, nn, offset, *, allow_underflow=False):
    """Round c/sqrt(nn)-offset once; exact comparisons certify float midpoints.

    The usual adjacent-float candidate is constant work. Severe cancellation,
    including a nonrepresentable intermediate gap, falls back to a bounded
    63-step binary64 search, never a precision guess or an absolute threshold.
    allow_underflow is only for displays carrying a separate exact certificate.
    Gates: test_frozen_margin_irrational_cancellation_has_exact_midpoint_certificate,
    test_frozen_margin_rounds_after_subtracting_the_margin_parameter.
    """
    c, nn, offset = (exact_input(c, "normalized difference numerator"),
                     exact_input(nn, "normalized difference square"),
                     exact_input(offset, "normalized difference offset"))
    if nn <= 0:
        raise ValueError("normal squared length must be positive")
    if not offset:
        magnitude = sqrt_rational(c*c/nn, allow_underflow=allow_underflow)
        return -magnitude if c < 0 else magnitude

    def compare_root(r):
        if c >= 0 > r:
            return 1
        if c < 0 <= r:
            return -1
        difference = c*c-r*r*nn
        order = (difference > 0)-(difference < 0)
        return -order if c < 0 else order

    sign = compare_root(offset)
    if not sign:
        return 0.0
    if sign < 0:
        return -normalized_difference_rational(-c, nn, -offset, allow_underflow=allow_underflow)

    def compare(value):
        return compare_root(offset + Fraction(value))

    def from_bits(bits):
        return struct.unpack(">d", struct.pack(">Q", bits))[0]

    try:
        root = sqrt_rational(c*c/nn, allow_underflow=True)
        candidate = (-root if c < 0 else root)-scalar_rational(offset, allow_underflow=True)
    except (ArithmeticError, OverflowError):
        candidate = math.inf
    lower = None
    if math.isfinite(candidate) and candidate >= 0:
        order = compare(candidate)
        if not order:
            return candidate
        if order > 0:
            upper = math.nextafter(candidate, math.inf)
            if math.isfinite(upper) and compare(upper) <= 0:
                lower = candidate
        else:
            below = math.nextafter(candidate, -math.inf)
            if below >= 0 and compare(below) >= 0:
                lower, upper = below, candidate
    if lower is None:
        lo, hi = 0, 0x7fefffffffffffff
        maximum = from_bits(hi)
        if compare(maximum) > 0:
            # RN-even has a finite cell above max. Its upper neighbour is the
            # conceptual exact 2**1024, not Fraction(infinity).
            overflow_midpoint = (Fraction(maximum)+Fraction(2)**1024)/2
            if compare(overflow_midpoint) >= 0:
                raise ConstructionDomainError("normalized_difference_rational result", "exact frozen difference exceeds finite binary64 range")
            return maximum
        while lo < hi:
            mid = (lo+hi+1)//2
            if compare(from_bits(mid)) >= 0:
                lo = mid
            else:
                hi = mid-1
        lower = from_bits(lo)
        if not compare(lower):
            return lower
        upper = from_bits(lo+1)
    midpoint = (Fraction(lower)+Fraction(upper))/2
    order = compare(midpoint)
    even = not (struct.unpack(">Q", struct.pack(">d", lower))[0] & 1)
    result = lower if order < 0 or (not order and even) else upper
    if not result and not allow_underflow:
        raise ConstructionDomainError("normalized_difference_rational result", "nonzero exact frozen difference is below binary64 output range")
    return result
