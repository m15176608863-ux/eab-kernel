"""Pure Fraction reference versus integer bilinear signs, no shared primitives.

The reference multiplies/subtracts Fraction values directly; the production
integer numerator and the existing floating filter are never used as oracles.
Every generated operand pair is tested, including zero, cancellation, rational
non-dyadic values, engineering coordinates and subnormal/overflow-sized data.
"""
from fractions import Fraction as F
import inspect
import math
import random

import pytest

from eab import predicates as P


def operand_pairs():
    rng = random.Random(52002)
    for scale, offset in ((1., 0.), (1e-9, 1e6), (1e3, -1e5),
                          (1e-200, 0.), (1e200, 0.)):
        for _ in range(160):
            a = tuple(F(offset + scale * rng.uniform(-2, 2)) for _ in range(2))
            b = tuple(F(offset + scale * rng.uniform(-2, 2)) for _ in range(2))
            yield a, b
            yield a, a
            yield a, (-a[1], a[0])
    for _ in range(200):
        yield (tuple(F(rng.randrange(-10**9, 10**9), rng.randrange(1, 1000)) for _ in range(2)),
               tuple(F(rng.randrange(-10**9, 10**9), rng.randrange(1, 1000)) for _ in range(2)))
    tiny, huge = F(math.ulp(0.)), F(float.fromhex('0x1.fffffffffffffp+1023'))
    for a in ((tiny, tiny), (huge, huge), (tiny, huge), (F(0), F(0))):
        for b in ((tiny, -tiny), (huge, -huge), (huge, tiny), (F(0), F(0))):
            yield a, b


def test_integer_bilinear_signs_equal_fraction_on_every_pair():
    cases = list(operand_pairs())
    assert len(cases) == 2616
    for a, b in cases:
        cross = a[0] * b[1] - a[1] * b[0]
        dot = a[0] * b[0] + a[1] * b[1]
        assert P.cross2_sign(a, b) == (cross > 0) - (cross < 0), (a, b, 'cross')
        assert P.dot2_sign(a, b) == (dot > 0) - (dot < 0), (a, b, 'dot')


def test_integer_bilinear_path_never_approximates_fraction_operands(monkeypatch):
    def forbidden_float_conversion(value):
        raise AssertionError('integer path must not call the floating filter')
    monkeypatch.setattr(P, '_float_value', forbidden_float_conversion)
    test_integer_bilinear_signs_equal_fraction_on_every_pair()


@pytest.mark.parametrize('name,old,new,channel', [
    ('cross2_sign', '- a[1].numerator', '+ a[1].numerator', 'cross'),
    ('dot2_sign', '+ a[1].numerator', '- a[1].numerator', 'dot'),
])
def test_integer_bilinear_gate_kills_internal_arithmetic_mutation(monkeypatch, name, old, new, channel):
    source = inspect.getsource(getattr(P, name))
    assert source.count(old) == 1
    namespace = dict(P.__dict__)
    exec(compile(source.replace(old, new), '<E5a2 integer bilinear mutant>', 'exec'), namespace)
    monkeypatch.setattr(P, name, namespace[name])
    with pytest.raises(AssertionError) as failure:
        test_integer_bilinear_signs_equal_fraction_on_every_pair()
    assert channel in str(failure.value)
