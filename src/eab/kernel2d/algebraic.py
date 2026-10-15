"""Exact degree-at-most-five real roots for the M5a trajectory contract.

Coefficients are rational and ordered from constant to leading coefficient.
Squarefree Sturm isolation, gcd equality and rational interval signs implement
the proofs in docs/m5a_se2_design.md, section 4. No floating value participates
in a predicate. The only binary64 output is ``RealAlgebraic.time``, through
the checked construction boundary. Gates: tests/test_m5a_algebraic.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache
from math import comb, gcd, lcm

from ..construction import scalar_algebraic


def _rational(value):
    if not isinstance(value, (int, F)) or isinstance(value, bool):
        raise ValueError("polynomial coefficients and isolation bounds must be exact rationals")
    return F(value)


def _poly(coefficients):
    coefficients = tuple(_rational(x) for x in coefficients)
    if not coefficients:
        return (F(0),)
    end = len(coefficients)
    while end > 1 and not coefficients[end-1]:
        end -= 1
    return coefficients[:end]


def p_add(a, b):
    a, b = _poly(a), _poly(b)
    return _poly(tuple((a[i] if i < len(a) else 0)+(b[i] if i < len(b) else 0)
                       for i in range(max(len(a), len(b)))))


def p_scale(a, scalar):
    scalar = _rational(scalar)
    return _poly(tuple(x*scalar for x in _poly(a)))


def p_sub(a, b):
    return p_add(a, p_scale(b, -1))


def p_mul(a, b):
    a, b = _poly(a), _poly(b)
    result = [F(0)]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i+j] += x*y
    return _poly(result)


def _evaluate(poly, value):
    result = F(0)
    for coefficient in reversed(poly):
        result = result*value+coefficient
    return result


def p_eval(poly, value):
    return _evaluate(_poly(poly), _rational(value))


def p_derivative(poly):
    poly = _poly(poly)
    return _poly(tuple(i*poly[i] for i in range(1, len(poly))))


def p_divmod(dividend, divisor):
    a, b = _poly(dividend), _poly(divisor)
    if b == (F(0),):
        raise ZeroDivisionError("polynomial division by zero")
    if len(a) < len(b):
        return (F(0),), a
    remainder = list(a)
    quotient = [F(0)]*(len(a)-len(b)+1)
    while len(remainder) >= len(b) and any(remainder):
        shift = len(remainder)-len(b)
        factor = remainder[-1]/b[-1]
        quotient[shift] = factor
        for i, coefficient in enumerate(b):
            remainder[i+shift] -= factor*coefficient
        while len(remainder) > 1 and not remainder[-1]:
            remainder.pop()
    return _poly(quotient), _poly(remainder)


def _primitive(poly):
    """Clear denominators by a positive factor without changing signs."""
    denominator = lcm(*(x.denominator for x in poly))
    integers = tuple(x.numerator*(denominator//x.denominator) for x in poly)
    divisor = gcd(*integers)
    return tuple(F(x//divisor) for x in integers) if divisor else (F(0),)


def p_gcd(a, b):
    a, b = _poly(a), _poly(b)
    while b != (F(0),):
        a, b = b, _primitive(p_divmod(a, b)[1])
    return p_scale(a, 1/a[-1]) if any(a) else a


@lru_cache(maxsize=4096)
def _squarefree(poly):
    if len(poly) < 2:
        return poly
    divisor = p_gcd(poly, p_derivative(poly))
    quotient, remainder = p_divmod(poly, divisor)
    if any(remainder):
        raise ArithmeticError("nonexact squarefree polynomial division")
    return p_scale(quotient, 1/quotient[-1])


@lru_cache(maxsize=4096)
def _sturm(poly):
    sequence = [_primitive(poly), _primitive(p_derivative(poly))]
    while any(sequence[-1]):
        remainder = p_divmod(sequence[-2], sequence[-1])[1]
        if not any(remainder):
            break
        sequence.append(_primitive(p_scale(remainder, -1)))
    return tuple(sequence)


def _sign(value):
    return (value > 0)-(value < 0)


def _variations(poly, value):
    signs = [_sign(_evaluate(member, value)) for member in _sturm(poly)]
    signs = [sign for sign in signs if sign]
    return sum(a != b for a, b in zip(signs, signs[1:]))


def _root_count(poly, lower, upper):
    """Distinct roots in a CLOSED interval, including endpoint roots once."""
    if lower > upper or len(poly) < 2:
        return 0
    if lower == upper:
        return int(not _evaluate(poly, lower))
    return _variations(poly, lower)-_variations(poly, upper)+int(not _evaluate(poly, lower))


def _bisect_root(poly, lower, upper):
    if lower == upper:
        return lower, upper
    middle = (lower+upper)/2
    value = _evaluate(poly, middle)
    if not value:
        return middle, middle
    if _sign(value) == _sign(_evaluate(poly, lower)):
        return middle, upper
    return lower, middle


def _interval_value(poly, lower, upper):
    lo = hi = F(0)
    for coefficient in reversed(poly):
        products = (lo*lower, lo*upper, hi*lower, hi*upper)
        lo, hi = min(products)+coefficient, max(products)+coefficient
    return lo, hi


def _bernstein_sign(poly, lower, upper):
    """Strict sign certified by nonnegative Bernstein weights on [0,1].

    p(lower+(upper-lower)*y)=sum b_i*C(n,i)*y**i*(1-y)**(n-i).
    Nonnegative b_i with positive endpoints imply strict positivity everywhere;
    the negative case is symmetric. Zero means UNKNOWN, never a root claim.
    """
    degree, width = len(poly)-1, upper-lower
    shifted = tuple(width**j*sum(poly[k]*comb(k, j)*lower**(k-j)
                                  for k in range(j, degree+1)) for j in range(degree+1))
    bernstein = tuple(sum(shifted[j]*F(comb(i, j), comb(degree, j)) for j in range(i+1))
                      for i in range(degree+1))
    if bernstein[0] > 0 and bernstein[-1] > 0 and all(x >= 0 for x in bernstein):
        return 1
    if bernstein[0] < 0 and bernstein[-1] < 0 and all(x <= 0 for x in bernstein):
        return -1
    return 0


@dataclass(frozen=True, eq=False)
class RealAlgebraic:
    """One real root with a verified closed rational isolating interval.

    Equality is algebraic, not equality of certificates. Instances are
    deliberately unhashable because a reducible defining polynomial need not
    be minimal. Integer/Fraction and finite binary64 operands compare exactly
    at their numeric value. Constructor coefficients/bounds require rationals.
    """
    polynomial: tuple
    lower: F
    upper: F
    __hash__ = None

    def __post_init__(self):
        polynomial = _poly(self.polynomial)
        lower, upper = _rational(self.lower), _rational(self.upper)
        if not 1 <= len(polynomial)-1 <= 5:
            raise ValueError("defining polynomial degree must be between one and five")
        polynomial = _squarefree(polynomial)
        if lower > upper or _root_count(polynomial, lower, upper) != 1:
            raise ValueError("interval must isolate exactly one real root")
        if not _evaluate(polynomial, lower):
            upper = lower
        elif not _evaluate(polynomial, upper):
            lower = upper
        elif len(polynomial) == 2:
            lower = upper = -polynomial[0]/polynomial[1]
        object.__setattr__(self, "polynomial", polynomial)
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)

    @staticmethod
    def from_rational(value):
        value = _rational(value)
        return RealAlgebraic((-value, F(1)), value, value)

    @property
    def rational(self):
        return self.lower if self.lower == self.upper else None

    def refine(self):
        """Return the same root with one exact bisection of its certificate."""
        lower, upper = _bisect_root(self.polynomial, self.lower, self.upper)
        return RealAlgebraic(self.polynomial, lower, upper)

    def _compare_rational(self, other):
        if self.rational is not None:
            return _sign(self.rational-other)
        if other <= self.lower:
            return 1
        if other >= self.upper:
            return -1
        value = _evaluate(self.polynomial, other)
        if not value:
            return 0
        return 1 if _sign(value) == _sign(_evaluate(self.polynomial, self.lower)) else -1

    def compare(self, other):
        """Exact sign(self-other), suitable for the construction comparator."""
        if not isinstance(other, RealAlgebraic):
            if not isinstance(other, (int, F, float)):
                raise TypeError("real algebraic ordering requires a supported finite number")
            try:
                other = F(other)
            except (ValueError, OverflowError):
                raise TypeError("real algebraic ordering requires a supported finite number") from None
            return self._compare_rational(other)
        if self.rational is not None:
            return -other._compare_rational(self.rational)
        if other.rational is not None:
            return self._compare_rational(other.rational)
        lower, upper = max(self.lower, other.lower), min(self.upper, other.upper)
        if lower <= upper:
            common = p_gcd(self.polynomial, other.polynomial)
            if _root_count(common, lower, upper):
                return 0
        alo, ahi, blo, bhi = self.lower, self.upper, other.lower, other.upper
        while True:
            if ahi <= blo:
                return -1
            if bhi <= alo:
                return 1
            if ahi-alo >= bhi-blo:
                alo, ahi = _bisect_root(self.polynomial, alo, ahi)
            else:
                blo, bhi = _bisect_root(other.polynomial, blo, bhi)

    def __eq__(self, other):
        try:
            return self.compare(other) == 0
        except TypeError:
            return False

    def __lt__(self, other):
        return self.compare(other) < 0

    def __le__(self, other):
        return self.compare(other) <= 0

    def __gt__(self, other):
        return self.compare(other) > 0

    def __ge__(self, other):
        return self.compare(other) >= 0

    def sign_polynomial(self, *coefficients):
        return sign_at(coefficients, self)

    @property
    def time(self):
        """Correctly rounded display; not a decision input."""
        return scalar_algebraic(self.compare, allow_underflow=True)

    @property
    def certificate(self):
        return {"polynomial": [str(x) for x in self.polynomial],
                "interval": [str(self.lower), str(self.upper)],
                "rational": None if self.rational is None else str(self.rational)}


def roots_interval(poly, lower=0, upper=1):
    """All DISTINCT real roots in the closed interval, in exact order.

    An identically zero polynomial has infinitely many roots and is rejected;
    persistent event constraints must be handled explicitly by their caller.
    A nonzero constant has no roots. The unprocessed input degree is <=5.
    """
    poly, lower, upper = _poly(poly), _rational(lower), _rational(upper)
    if not any(poly):
        raise ValueError("zero polynomial has infinitely many roots")
    if len(poly) > 6:
        raise ValueError("root isolation supports polynomial degree at most five")
    if lower > upper:
        raise ValueError("root isolation interval is reversed")
    if len(poly) == 1:
        return ()
    interval_lower, interval_upper = _interval_value(poly, lower, upper)
    if interval_lower > 0 or interval_upper < 0:
        return ()
    if _bernstein_sign(poly, lower, upper):
        return ()
    poly = _squarefree(poly)
    if lower == upper:
        return (RealAlgebraic.from_rational(lower),) if not _evaluate(poly, lower) else ()
    roots = []
    for endpoint in (lower, upper):
        if not _evaluate(poly, endpoint):
            roots.append(RealAlgebraic.from_rational(endpoint))
            poly = p_divmod(poly, (-endpoint, F(1)))[0]
    pending = [(poly, lower, upper)]
    while pending:
        current, lo, hi = pending.pop()
        count = _root_count(current, lo, hi)
        if not count:
            continue
        if count == 1:
            roots.append(RealAlgebraic(current, lo, hi))
            continue
        middle = (lo+hi)/2
        if not _evaluate(current, middle):
            roots.append(RealAlgebraic.from_rational(middle))
            current = p_divmod(current, (-middle, F(1)))[0]
        pending.append((current, middle, hi))
        pending.append((current, lo, middle))
    return tuple(sorted(roots))


def sign_at(poly, time):
    """Exact sign of any rational polynomial at a supported algebraic root."""
    poly = _poly(poly)
    if not isinstance(time, RealAlgebraic):
        return _sign(_evaluate(poly, _rational(time)))
    if time.rational is not None:
        return _sign(_evaluate(poly, time.rational))
    lo, hi = _interval_value(poly, time.lower, time.upper)
    if lo > 0 or hi < 0:
        return 1 if lo > 0 else -1
    remainder = p_divmod(poly, time.polynomial)[1]
    if len(remainder) == 1:
        return _sign(remainder[0])
    lo, hi = _interval_value(remainder, time.lower, time.upper)
    if lo > 0 or hi < 0:
        return 1 if lo > 0 else -1
    common = p_gcd(time.polynomial, remainder)
    if _root_count(common, time.lower, time.upper):
        return 0
    lower, upper = time.lower, time.upper
    while True:
        lower, upper = _bisect_root(time.polynomial, lower, upper)
        lo, hi = _interval_value(remainder, lower, upper)
        if lo > 0 or hi < 0:
            return 1 if lo > 0 else -1
