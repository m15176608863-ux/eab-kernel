"""Common-denominator 3D arithmetic; no approximation, cache, or float filter.

Each operation evaluates the same rational polynomial as Fraction arithmetic,
but normalises only its final result rather than every product and partial sum.
The callers retain their historical expressions for float / Dual / mixed data.
"""

from fractions import Fraction
from math import gcd, lcm


def fraction_vectors(a, b):
    """True only for the six builtin Fraction coordinates used by the fast path."""
    return (len(a) == 3 and len(b) == 3
            and type(a[0]) is Fraction and type(a[1]) is Fraction and type(a[2]) is Fraction
            and type(b[0]) is Fraction and type(b[1]) is Fraction and type(b[2]) is Fraction)


def dot(a, b):
    d0 = a[0].denominator * b[0].denominator
    d1 = a[1].denominator * b[1].denominator
    d2 = a[2].denominator * b[2].denominator
    den = lcm(d0, d1, d2)
    num = (a[0].numerator * b[0].numerator * (den // d0)
           + a[1].numerator * b[1].numerator * (den // d1)
           + a[2].numerator * b[2].numerator * (den // d2))
    return Fraction(num, den)


def _product_difference(a, b, c, d):
    first = a.denominator * b.denominator
    second = c.denominator * d.denominator
    common = gcd(first, second)
    num = (a.numerator * b.numerator * (second // common)
           - c.numerator * d.numerator * (first // common))
    return Fraction(num, first * (second // common))


def cross(a, b):
    return (_product_difference(a[1], b[2], a[2], b[1]),
            _product_difference(a[2], b[0], a[0], b[2]),
            _product_difference(a[0], b[1], a[1], b[0]))
