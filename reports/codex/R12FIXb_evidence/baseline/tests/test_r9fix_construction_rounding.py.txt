"""Independent Fraction midpoint certificates for both construction groups.

The oracle below only compares exact scalars against adjacent binary64 cells.
It calls neither tested constructor nor any geometry primitive to certify a
result; sqrt tests square the rational cell boundaries instead of taking a root.
"""
from fractions import Fraction as F
import math
import struct
import sys

import pytest

from eab import construction as actual
from eab import oracle_construction as reference


def _certificate(result, value, power=1):
    assert math.isfinite(result), "constructor finite range"
    if power == 1:
        assert result == 0 or (result > 0) == (value > 0), "constructor sign"
    else:
        assert result >= 0 and value >= 0
    result, value = abs(result), abs(F(value))
    even = struct.unpack(">Q", struct.pack(">d", result))[0] % 2 == 0
    center = F(result)
    if result:
        lower = (F(math.nextafter(result, 0.0))+center)/2
        assert value > lower**power or (even and value == lower**power), "lower Fraction midpoint certificate"
    next_float = math.nextafter(result, math.inf)
    upper = (center+(F(next_float) if math.isfinite(next_float) else F(2)**1024))/2
    assert value < upper**power or (even and value == upper**power), "upper Fraction midpoint certificate"


def _rounding_cells():
    anchors = [0.0, math.ulp(0.0), 2*math.ulp(0.0),
               math.nextafter(sys.float_info.min, 0.0), sys.float_info.min,
               math.ldexp(1., -600), 1., math.nextafter(1., math.inf),
               3/7, math.ldexp(1., 600),
               math.nextafter(sys.float_info.max, 0.0), sys.float_info.max]
    cells = []
    for anchor in anchors:
        low = F(anchor)
        nxt = math.nextafter(anchor, math.inf)
        high = F(nxt) if math.isfinite(nxt) else F(2)**1024
        middle, jitter = (low+high)/2, (high-low)/16
        cells.extend([low, middle-jitter, middle, middle+jitter])
    return cells


CELLS = _rounding_cells()


@pytest.mark.parametrize("value", CELLS)
def test_r9_scalar_ratio_are_certified_at_binary64_midpoints(value):
    overflow = (F(sys.float_info.max)+F(2)**1024)/2
    for scalar, ratio in ((actual.scalar_rational, actual.ratio_rational),
                          (reference.scalar_exact, reference.ratio_exact)):
        for sign in (1, -1):
            q = sign*value
            if value >= overflow:
                with pytest.raises(OverflowError):
                    scalar(q, allow_underflow=True)
                continue
            result = scalar(q, allow_underflow=True)
            _certificate(result, q)
            assert ratio(7*q, 7, allow_underflow=True) == result


@pytest.mark.parametrize("root", CELLS)
def test_r9_exact_sqrt_is_certified_at_binary64_midpoints(root):
    overflow = (F(sys.float_info.max)+F(2)**1024)/2
    for constructor in (actual.sqrt_rational, reference.sqrt_exact):
        if root >= overflow:
            with pytest.raises(OverflowError):
                constructor(root*root, allow_underflow=True)
        else:
            result = constructor(root*root, allow_underflow=True)
            _certificate(result, root*root, 2)


@pytest.mark.parametrize("m", range(1, 25))
def test_r9_exact_sqrt_non_square_subnormal_certificates(m):
    square = F(m*m, 3)*F(2)**-2148
    for constructor in (actual.sqrt_rational, reference.sqrt_exact):
        _certificate(constructor(square), square, 2)


@pytest.mark.parametrize("vector", [
    (F(2)**-1074,)*3,
    (F(2)**-1075,)*3,
    (F(2)**-600, -F(2)**-601, F(2)**-602),
    (F(3), F(-4), F(12)),
    (F(2)**600, F(2)**599, -F(2)**598),
    (F(sys.float_info.max),)*2,
    (F(2)**2000, -F(2)**2000, F(2)**926),
    (F(1), F(2)**-1075, -F(2)**-1074),
])
def test_r9_norm_and_unit_round_exact_final_components(vector):
    squared = sum(x*x for x in vector)
    for norm, unit in ((actual.norm_rational, actual.unit_rational),
                       (reference.norm_exact, reference.unit_exact)):
        if squared >= ((F(sys.float_info.max)+F(2)**1024)/2)**2:
            with pytest.raises(OverflowError):
                norm(vector)
        else:
            _certificate(norm(vector), squared, 2)
        direction = unit(vector, allow_underflow=True)
        for value, component in zip(vector, direction):
            assert component == 0 or (component > 0) == (value > 0)
            _certificate(abs(component), value*value/squared, 2)


def test_r9_constructor_range_policy_is_explicit():
    for scalar, root, unit, vector in (
        (actual.scalar_rational, actual.sqrt_rational, actual.unit_rational, actual.vector_rational),
        (reference.scalar_exact, reference.sqrt_exact, reference.unit_exact, reference.vector_exact),
    ):
        with pytest.raises(ArithmeticError, match="below binary64"):
            scalar(F(2)**-1076)
        with pytest.raises(ArithmeticError, match="below binary64"):
            root(F(2)**-2152)
        with pytest.raises(ArithmeticError, match="below binary64"):
            unit((1, F(2)**-1076))
        with pytest.raises(ArithmeticError, match="below binary64"):
            vector((1, F(2)**-1076))
        with pytest.raises(ValueError):
            root(-1)
        with pytest.raises(ZeroDivisionError):
            unit((0, 0))
        assert vector((1, F(2)**-1076), allow_underflow=True) == (1., 0.)
