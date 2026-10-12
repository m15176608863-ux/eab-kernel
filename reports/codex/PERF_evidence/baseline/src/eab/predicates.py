"""Certified sign filters; an inconclusive float calculation falls back to Fraction.

The filters change only the amount of exact work, never the answer.  All bounds
include an absolute gradual-underflow term.  Overflow/non-finite intermediates
make a filter inconclusive.  Fraction inputs remain exact input data (in
particular, an exact Minkowski difference is never replaced by its float view).
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from math import isfinite

_U = 2.0 ** -53
_TINY = 2.0 ** -1074
_O3D_ERR = (7.0 + 56.0 * _U) * _U
_BILINEAR_ERR = 16.0 * _U


def _sign(x):
    return (x > 0) - (x < 0)


@lru_cache(maxsize=16384)
def _float_value(x):
    try:
        return float(x)
    except OverflowError:
        return float("inf") if x > 0 else -float("inf")


def cross2_sign(a, b) -> int:
    """Exact sign of a.x*b.y-a.y*b.x, including arbitrary rational inputs.

    For rounded rational operands, |x-fx| <= u/(1-u)*|fx| + tiny.
    Expanding both products, then their subtraction, uses less than 8u times
    the product permanent.  16u also covers rounding the computed bound;
    8*tiny*(1+sum|operand|) bounds operand/product/sum underflow propagation.
    The spare factor is numerical certification, not a geometric tolerance.
    Already-rational operands use the exact common-denominator numerator
    directly; this is integer algebra, not an additional floating filter.
    """
    if (type(a[0]) is Fraction and type(a[1]) is Fraction
            and type(b[0]) is Fraction and type(b[1]) is Fraction):
        numerator = (a[0].numerator * b[1].numerator * a[1].denominator * b[0].denominator
                     - a[1].numerator * b[0].numerator * a[0].denominator * b[1].denominator)
        return _sign(numerator)
    ax, ay, bx, by = map(_float_value, (a[0], a[1], b[0], b[1]))
    p, q = ax * by, ay * bx
    d = p - q
    bound = _BILINEAR_ERR * (abs(p) + abs(q)) + 8.0 * _TINY * (1.0 + abs(ax) + abs(ay) + abs(bx) + abs(by))
    if isfinite(d) and abs(d) > bound:
        return _sign(d)
    return _sign(Fraction(a[0]) * Fraction(b[1]) - Fraction(a[1]) * Fraction(b[0]))


def dot2_sign(a, b) -> int:
    """Exact two-dimensional dot-product sign, using cross2_sign's bound."""
    if (type(a[0]) is Fraction and type(a[1]) is Fraction
            and type(b[0]) is Fraction and type(b[1]) is Fraction):
        numerator = (a[0].numerator * b[0].numerator * a[1].denominator * b[1].denominator
                     + a[1].numerator * b[1].numerator * a[0].denominator * b[0].denominator)
        return _sign(numerator)
    ax, ay, bx, by = map(_float_value, (a[0], a[1], b[0], b[1]))
    p, q = ax * bx, ay * by
    d = p + q
    bound = _BILINEAR_ERR * (abs(p) + abs(q)) + 8.0 * _TINY * (1.0 + abs(ax) + abs(ay) + abs(bx) + abs(by))
    if isfinite(d) and abs(d) > bound:
        return _sign(d)
    return _sign(Fraction(a[0]) * Fraction(b[0]) + Fraction(a[1]) * Fraction(b[1]))


def orient3d_fraction(a, b, c, p) -> int:
    """Pure rational reference: det[b-a,c-a,p-a]; unit tetrahedron is +1."""
    ax, ay, az = (Fraction(a[k]) - Fraction(p[k]) for k in range(3))
    bx, by, bz = (Fraction(b[k]) - Fraction(p[k]) for k in range(3))
    cx, cy, cz = (Fraction(c[k]) - Fraction(p[k]) for k in range(3))
    d = az * (bx * cy - cx * by) + bz * (cx * ay - ax * cy) + cz * (ax * by - bx * ay)
    return -_sign(d)


def orient3d(a, b, c, p) -> int:
    """Exact orientation with a certified binary64 fast path.

    Float-only inputs use Shewchuk's (7+56u)u permanent bound.  A difference
    of binary64 numbers cannot incur inexact underflow: any subnormal result
    is an exactly representable multiple of tiny.  The six pair products can
    underflow, and those errors are multiplied by the z differences.  Adding
    16*tiny*(1+sum|z|) bounds these errors, the triple products and final sums.

    Rational inputs have an additional correctly-rounded conversion.  For
    each difference, M=|float(endpoint)|+|float(p)| bounds cancellation-free
    input magnitude.  Its absolute conversion/difference error is bounded by
    4u*M+4*tiny.  Expanding the six degree-three monomials gives less than
    32u times their M-permanent; 64u includes bound evaluation rounding.  The
    pairwise M products in the absolute term cover a tiny conversion error
    amplified by two large factors.  This less sharp filter is still exact.
    """
    exact_inputs = any(not isinstance(v, float) for q in (a, b, c, p) for v in q)
    if exact_inputs:
        af, bf, cf, pf = (tuple(_float_value(v) for v in q) for q in (a, b, c, p))
    else:
        af, bf, cf, pf = a, b, c, p
    adx, ady, adz = (af[k] - pf[k] for k in range(3))
    bdx, bdy, bdz = (bf[k] - pf[k] for k in range(3))
    cdx, cdy, cdz = (cf[k] - pf[k] for k in range(3))
    bdxcdy, cdxbdy = bdx * cdy, cdx * bdy
    cdxady, adxcdy = cdx * ady, adx * cdy
    adxbdy, bdxady = adx * bdy, bdx * ady
    det = adz * (bdxcdy - cdxbdy) + bdz * (cdxady - adxcdy) + cdz * (adxbdy - bdxady)
    if exact_inputs:
        ma, mb, mc = (tuple(abs(q[k]) + abs(pf[k]) for k in range(3)) for q in (af, bf, cf))
        perm = (ma[2] * (mb[0] * mc[1] + mc[0] * mb[1])
                + mb[2] * (mc[0] * ma[1] + ma[0] * mc[1])
                + mc[2] * (ma[0] * mb[1] + mb[0] * ma[1]))
        # Sum all products is conservative, including mixed-coordinate ones.
        sa, sb, sc = sum(ma), sum(mb), sum(mc)
        bound = 64.0 * _U * perm + 128.0 * _TINY * (1.0 + sa + sb + sc + sa * sb + sa * sc + sb * sc)
    else:
        perm = ((abs(bdxcdy) + abs(cdxbdy)) * abs(adz)
                + (abs(cdxady) + abs(adxcdy)) * abs(bdz)
                + (abs(adxbdy) + abs(bdxady)) * abs(cdz))
        bound = _O3D_ERR * perm + 16.0 * _TINY * (1.0 + abs(adz) + abs(bdz) + abs(cdz))
    if isfinite(det) and abs(det) > bound:
        return -_sign(det)
    return orient3d_fraction(a, b, c, p)
