"""Draft gate: all normalized-difference inputs must enter the exact boundary.

Independent oracle is Fraction midpoint certification of c**2/nn, not a
production square root. Float/Fraction equivalence is an additional check.
"""
from fractions import Fraction as F
import inspect

import pytest

from eab import construction as production
from eab.oracle_construction import assert_sqrt_rounding


@pytest.mark.parametrize("exponent", [-200,200])
def test_normalized_difference_rationalizes_float_normal_squared(exponent):
    value = 10.**exponent
    exact = F(value)
    result = production.normalized_difference_rational(value,value,0.)
    reference = production.normalized_difference_rational(exact,exact,F(0))
    assert result == reference and result > 0, "normalized difference preserves representable root from float nn"
    assert_sqrt_rounding(result,exact,"normalized difference exact input midpoint certificate")


@pytest.mark.parametrize("nn", [0.,-1.,F(0),F(-1)])
@pytest.mark.parametrize("offset", [0.,1.])
def test_normalized_difference_rejects_nonpositive_normal_squared(nn,offset):
    with pytest.raises(ValueError,match="normal squared length must be positive"):
        production.normalized_difference_rational(0,nn,offset)


def test_normalized_difference_float_nn_mutant_hits_target_assertion(monkeypatch):
    source=inspect.getsource(production.normalized_difference_rational)
    # Match the named exact boundary now used by the production constructor.
    old='exact_input(nn, "normalized difference square")'
    assert source.count(old)==1
    namespace=dict(vars(production))
    exec(compile(source.replace(old,"nn"),
                 "<R9 normalized nn rationalization removed>","exec"),namespace)
    monkeypatch.setattr(production,"normalized_difference_rational",
                        namespace["normalized_difference_rational"])
    with pytest.raises(AssertionError,match="normalized difference preserves representable root from float nn") as caught:
        test_normalized_difference_rationalizes_float_normal_squared(-200)
    print("normalized nn internal mutant:",caught.value)
