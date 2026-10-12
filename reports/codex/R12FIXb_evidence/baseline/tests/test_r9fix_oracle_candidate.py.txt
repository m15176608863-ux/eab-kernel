"""Independent reference construction protocol and certified-candidate gates.

Expected roots are checked only against Fraction binary64 midpoint cells;
the tests import no production construction or geometry primitive.
"""
from fractions import Fraction as F
import math

import pytest

from eab import oracle_construction as oracle
from test_r9fix_construction_rounding import _certificate, CELLS


@pytest.fixture(autouse=True)
def _fresh_oracle_candidate_cache():
    oracle._round_positive.cache_clear()
    yield
    oracle._round_positive.cache_clear()


def test_r9_oracle_scalar_removes_float_subclass_witness():
    class WitnessFloat(float):
        exact = F(10, 3)
    value = WitnessFloat(10/3)
    result = oracle.scalar_exact(value)
    assert type(result) is float, "oracle scalar must return a plain display, not retain an exact-witness subclass"
    assert not hasattr(result, "exact"), "a scalar display cannot retain the source witness"
    assert F(result) == F(value) and F(result) != value.exact


@pytest.mark.parametrize("root", CELLS)
def test_r9_oracle_candidate_respects_each_exact_midpoint_cell(root):
    maximum = F(float.fromhex('0x1.fffffffffffffp1023'))
    overflow = (maximum+F(2)**1024)/2
    for value, power, constructor in ((root,1,oracle.scalar_exact),
                                      (root*root,2,oracle.sqrt_exact)):
        if root >= overflow:
            with pytest.raises(OverflowError):
                constructor(value,allow_underflow=True)
        else:
            _certificate(constructor(value,allow_underflow=True),value,power)


@pytest.mark.parametrize("exponent", [-1074,-1022,-600,0,600,1023])
@pytest.mark.parametrize("side", [-1,0,1])
def test_r9_decimal_unresolved_midpoint_sides_still_have_exact_answers(exponent,side):
    lower = math.ldexp(1.,exponent)
    upper = math.nextafter(lower,math.inf)
    middle = (F(lower)+F(upper))/2
    square = middle*middle+side*F(2)**(2*exponent-5000)
    _certificate(oracle.sqrt_exact(square,allow_underflow=True),square,2)


@pytest.mark.parametrize("bad", [0.,1.,math.inf,math.nan,None])
def test_r9_bad_oracle_candidate_falls_back_to_bit_search(monkeypatch,bad):
    calls=[]
    def wrong_candidate(value,power):
        calls.append((value,power))
        return bad
    monkeypatch.setattr(oracle,'_candidate_positive',wrong_candidate)
    actual=oracle.sqrt_exact(F(9,4))
    assert actual == 1.5, "bad candidate rejected by Fraction midpoint certificate"
    assert calls == [(F(9,4),2)]
    _certificate(actual,F(9,4),2)


def test_r9_decimal_midpoint_ambiguity_really_takes_fallback(monkeypatch):
    middle = (F(1)+F(math.nextafter(1.,math.inf)))/2
    square = middle*middle+F(2)**-5000
    candidate=oracle._candidate_positive(square,2)
    assert not oracle._candidate_is_certified(square,2,candidate)
    calls=[]
    real=oracle._from_bits
    def bits_spy(bits):
        calls.append(bits)
        return real(bits)
    monkeypatch.setattr(oracle,'_from_bits',bits_spy)
    result=oracle.sqrt_exact(square)
    assert calls, "unresolved Decimal80 midpoint must invoke reference bit search"
    assert result == math.nextafter(1.,math.inf)
    _certificate(result,square,2)


def test_r9_oracle_candidate_certificate_gate_has_teeth(monkeypatch):
    monkeypatch.setattr(oracle,'_candidate_is_certified',lambda *args:True)
    with pytest.raises(AssertionError,match='bad candidate rejected by Fraction midpoint certificate') as caught:
        test_r9_bad_oracle_candidate_falls_back_to_bit_search(monkeypatch,1.)
    print('oracle candidate unchecked-return mutant:',caught.value)


def test_r9_oracle_candidate_preserves_default_underflow_errors():
    with pytest.raises(ArithmeticError,match='below binary64'):
        oracle.scalar_exact(F(2)**-1080)
    with pytest.raises(ArithmeticError,match='below binary64'):
        oracle.sqrt_exact(F(2)**-2160)
