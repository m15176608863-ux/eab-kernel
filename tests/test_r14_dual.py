"""R14 N01/N02 input fidelity: parity and lossless libm parameter gates.

Oracle: integer parity and rational numerator/denominator properties; no
production conversion, power, trigonometry, or geometry computes references.
"""
from fractions import Fraction as F
import inspect
import math
import textwrap

import pytest

from eab import dual
from eab.numeric_domain import ConstructionDomainError


@pytest.mark.parametrize("exponent", [2**54+1, -(2**54+1), 2**400+1])
@pytest.mark.parametrize("wrapper", [int, F])
def test_r14_integer_power_keeps_exact_parity(exponent, wrapper):
    result = dual.Dual(-1.0, (1.0, -1.0, 0.0)) ** wrapper(exponent)
    assert result.v == -1.0, "exact odd exponent must retain negative primal"
    assert result.e == (float(exponent), -float(exponent), 0.0), "exact odd exponent derivative sign"


@pytest.mark.parametrize("function", ["sin", "cos"])
@pytest.mark.parametrize("value", [2**54+1, F(3*2**54+1, 3), F(2)**-1075, F(2)**-2000])
@pytest.mark.parametrize("as_dual", [False, True])
def test_r14_trig_rejects_lossy_exact_parameters(function, value, as_dual):
    argument = dual.Dual(value, (value,)) if as_dual else value
    with pytest.raises(ConstructionDomainError, match=function):
        getattr(dual, function)(argument)


@pytest.mark.parametrize("value", [2**54+1, F(1, 3), F(2)**-1075, F(2)**-2000])
@pytest.mark.parametrize("as_dual", [False, True])
def test_r14_atan2_rejects_lossy_exact_parameters(value, as_dual):
    y = dual.Dual(value, (value,)) if as_dual else value
    x = dual.Dual(value, (0.0,)) if as_dual else value
    with pytest.raises(ConstructionDomainError, match="atan2"):
        dual.atan2(y, x)


@pytest.mark.parametrize("exponent", [-1074, -600, 0, 600, 1023])
def test_r14_atan2_retains_full_finite_binary64_parameters(exponent):
    value = math.ldexp(1.0, exponent)
    got = dual.atan2(dual.Dual(value, (value,)), dual.Dual(value, (0.0,)))
    # Integral representation pi/4 = integral_0^1 1/(1+t*t) dt lies in (1/2,1).
    assert 0.5 < got.v < 1.0, "same positive coordinates have a nonzero first-quadrant angle"
    assert got.e == (0.5,), "homogeneous tiny/tiny derivative remains one half"


@pytest.mark.parametrize("value", [0.0, math.ulp(0.0), -math.ulp(0.0), 2.0**54, 2.0**400])
def test_r14_trig_lossless_binary64_arguments_remain_supported(value):
    assert dual.sin(F(value)) == math.sin(value)
    assert dual.cos(F(value)) == math.cos(value)


@pytest.mark.parametrize("value", [F(1, 3), F(2)**-1075, F(3*2**54+1, 3)])
def test_r14_noninteger_power_rejects_lossy_exact_exponent(value):
    with pytest.raises(ConstructionDomainError, match="exponent"):
        dual.Dual(1.0, (0.0,)) ** value


@pytest.mark.parametrize("exponent", [F(2**55+1, 2), -F(2**55+1, 2)])
def test_r14_half_integer_power_keeps_exact_fraction(exponent):
    got = dual.Dual(1.0, (1.0,)) ** exponent
    assert got.v == 1.0
    assert got.e == (float(exponent),), "half-integer coefficient retains exact rational exponent"


def _mutated_function(function, old, new):
    source = textwrap.dedent(inspect.getsource(function))
    assert source.count(old) == 1
    namespace = dict(vars(dual))
    exec(compile(source.replace(old, new), "<r14-internal-mutation>", "exec"), namespace)
    return namespace[function.__name__]


def test_r14_integer_power_early_float_mutation_is_caught(monkeypatch):
    mutant = _mutated_function(dual.Dual.__pow__,
                              'p = exact_input(p, "Dual power exponent")',
                              'p = F(float(p))'.replace('F(', 'Fraction('))
    monkeypatch.setattr(dual.Dual, "__pow__", mutant)
    with pytest.raises(AssertionError, match="exact odd exponent must retain negative primal"):
        test_r14_integer_power_keeps_exact_parity(2**54+1, int)


def test_r14_trig_removed_lossless_check_mutation_is_caught(monkeypatch):
    # Mutate the converter used inside the actual production sin/cos/atan2 path.
    monkeypatch.setattr(dual, "_lossless_libm_input", lambda value, quantity: float(value))
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_r14_trig_rejects_lossy_exact_parameters("sin", 2**54+1, False)


@pytest.mark.parametrize("as_dual", [False, True])
def test_r14_atan2_nonzero_output_underflow_is_named(as_dual):
    y = dual.Dual(math.ulp(0.0), (math.ulp(0.0),)) if as_dual else math.ulp(0.0)
    with pytest.raises(ConstructionDomainError, match="atan2 result"):
        dual.atan2(y, 2.0)


def test_r14_exact_power_resource_limit_is_named_without_losing_trivial_bases():
    with pytest.raises(ConstructionDomainError, match="resource domain"):
        dual.Dual(2.0, (1.0,)) ** (2**54+1)
    with pytest.raises(ConstructionDomainError, match="resource domain"):
        dual.Dual(2.0, (1.0,)) ** F(2**55+1, 2)
    test_r14_integer_power_keeps_exact_parity(2**400+1, int)
    test_r14_half_integer_power_keeps_exact_fraction(F(2**55+1, 2))


@pytest.mark.parametrize("value", [F(1, 3), F(2)**-1075, F(2**54+1)])
def test_r14_noninteger_power_base_cannot_be_silently_rounded(value):
    with pytest.raises(ConstructionDomainError, match="base"):
        dual.Dual(value, (0.0,)) ** 0.25


def test_r14_atan2_removed_exact_output_cell_mutation_is_caught(monkeypatch):
    mutant = _mutated_function(dual.atan2,
        "if xv > 0 and yv != 0 and 2*abs(Fraction(yv)) <= Fraction(xv)*Fraction(math.ulp(0.0)):",
        "if False:")
    monkeypatch.setattr(dual, "atan2", mutant)
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_r14_atan2_nonzero_output_underflow_is_named(False)
