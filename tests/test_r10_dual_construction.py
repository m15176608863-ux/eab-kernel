"""G6J-J04: final derivative construction and range contracts.

Oracle: raw Fraction midpoint squares, with no production geometry or
construction helpers. Trigonometric tests retain the documented libm
coefficient model; they assert that a nonzero channel is not silently erased.
"""
from fractions import Fraction as F
from construction_oracle import scalar_exact, assert_sqrt_rounding
import inspect
import math
import textwrap

import pytest

import eab.dual as dual


@pytest.mark.parametrize("units", [3, 7, 11, 15])
@pytest.mark.parametrize("sign", [-1, 1])
@pytest.mark.parametrize("exponent", [0, 600])
def test_r10_sqrt_derivative_rounds_the_complete_expression(units, sign, exponent):
    u = math.ulp(0.0)
    value = math.ldexp(math.nextafter(1.0, math.inf), exponent)
    seed = math.ldexp(units*u, exponent//2)
    expected = (units//2)*u
    squared = F(seed)**2/(4*F(value))
    lower = (F(math.nextafter(expected, 0.0))+F(expected))/2
    upper = (F(expected)+F(math.nextafter(expected, math.inf)))/2
    assert lower**2 < squared < upper**2, "independent squared-midpoint certificate"
    result = dual.sqrt(dual.Dual(value, (sign*seed, 0.0)))
    assert result.e == (sign*expected, 0.0), "complete sqrt derivative final rounding"


@pytest.mark.parametrize("value,seed,error", [
    (2.0**1022, 2.0**-600, ArithmeticError),
    (math.ulp(0.0), 2.0**1023, OverflowError),
])
@pytest.mark.parametrize("sign", [-1, 1])
def test_r10_sqrt_derivative_out_of_range_fails_loudly(value, seed, error, sign):
    with pytest.raises(error):
        dual.sqrt(dual.Dual(value, (sign*seed,)))


@pytest.mark.parametrize("function,value", [("sin", 1.5), ("cos", 0.25)])
@pytest.mark.parametrize("sign", [-1, 1])
def test_r10_trigonometric_nonzero_derivative_cannot_underflow_silently(function, value, sign):
    seed = sign*math.ulp(0.0)
    coefficient = math.cos(value) if function == "sin" else -math.sin(value)
    exact_product = F(coefficient)*F(seed)
    assert 0 < abs(exact_product) < F(math.ulp(0.0))/2
    with pytest.raises(ArithmeticError):
        getattr(dual, function)(dual.Dual(value, (seed,)))


@pytest.mark.parametrize("function,value", [("sin", 0.25), ("cos", 1.5)])
def test_r10_trigonometric_representable_subnormal_and_zero_channels(function, value):
    seed = 3*math.ulp(0.0)
    coefficient = math.cos(value) if function == "sin" else -math.sin(value)
    expected = scalar_exact(F(coefficient)*F(seed))
    assert expected != 0
    result = getattr(dual, function)(dual.Dual(value, (seed, -seed, 0.0)))
    assert result.e == (expected, -expected, 0.0)


@pytest.mark.parametrize("p", [2.0, 2.5])
def test_r10_power_primal_underflow_without_an_exact_channel_fails_loudly(p):
    with pytest.raises(ArithmeticError):
        dual.Dual(2.0**-600, (0.0,)) ** p


@pytest.mark.parametrize("operation", [
    lambda: dual.Dual(2.0, (math.ulp(0.0),)) ** -2,
    lambda: dual.Dual(math.ulp(0.0), (2.0**1023,)) ** -1,
    lambda: dual.atan2(dual.Dual(1.0, (math.ulp(0.0),)), 2.0**1023),
    lambda: dual.atan2(dual.Dual(math.ulp(0.0), (1.0,)), math.ulp(0.0)),
])
def test_r10_existing_power_and_atan2_derivative_range_contract(operation):
    with pytest.raises(ArithmeticError):
        operation()


def test_r10_sqrt_source_rounded_primal_mutation_is_caught(monkeypatch):
    source = inspect.getsource(dual.sqrt)
    needle = "return Dual(s, tuple(_sqrt_derivative(x.v, a) for a in x.e))"
    assert source.count(needle) == 1
    mutant = source.replace(needle, "return Dual(s, tuple((0.5 / s) * a for a in x.e))")
    namespace = dict(vars(dual))
    exec(compile(mutant, "<r10-rounded-primal-sqrt>", "exec"), namespace)
    monkeypatch.setattr(dual, "sqrt", namespace["sqrt"])
    with pytest.raises(AssertionError, match="complete sqrt derivative final rounding"):
        test_r10_sqrt_derivative_rounds_the_complete_expression(3, 1, 0)


@pytest.mark.parametrize("function,value", [("sin", 1.5), ("cos", 0.25)])
def test_r10_trig_source_unchecked_product_mutation_is_caught(monkeypatch, function, value):
    source = inspect.getsource(getattr(dual, function))
    needle = "_derivative_float(Fraction(c) * Fraction(a))"
    assert source.count(needle) == 1
    namespace = dict(vars(dual))
    exec(compile(source.replace(needle, "c * a"), "<r10-unchecked-trig>", "exec"), namespace)
    monkeypatch.setattr(dual, function, namespace[function])
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_r10_trigonometric_nonzero_derivative_cannot_underflow_silently(function, value, 1)


@pytest.mark.parametrize("exponent,p,seed_hex", [
    (0, 0.5, "0x0.0000000000005p-1022"),
    (-716, 1.5, "0x1.8000000000000p-715"),
    (0, -0.5, "-0x0.0000000000005p-1022"),
    (0, -1.5, "-0x0.0000000000003p-1022"),
    (-428, 2.5, "0x1.0000000000000p-432"),
])
@pytest.mark.parametrize("sign", [-1, 1])
def test_r10_half_integer_power_derivative_keeps_exact_subnormal_ties(exponent, p, seed_hex, sign):
    seed = sign*float.fromhex(seed_hex)
    exact = F(p)*F(2)**(exponent*int(2*(p-1))//2)*F(seed)
    expected = scalar_exact(exact)
    assert abs(exact) / F(math.ulp(0.0)) in (F(5, 2), F(9, 2))
    result = dual.Dual(math.ldexp(1.0, exponent), (seed,)) ** p
    assert result.e == (expected,), "half-integer derivative exact tie must round to even"


@pytest.mark.parametrize("exponent", [-100, 0, 100])
def test_r10_atan2_derivative_uses_one_final_rational_rounding(exponent):
    y, x, dy, dx = (math.ldexp(t, exponent) for t in
                    (1.4280518937982691, -1.422218906497708,
                     1.5618260226894076, -5.878035357209965))
    exact = (F(x)*F(dy)-F(y)*F(dx))/(F(x)**2+F(y)**2)
    expected = scalar_exact(exact)
    result = dual.atan2(dual.Dual(y, (dy,)), dual.Dual(x, (dx,)))
    assert result.e == (expected,), "atan2 derivative exact rational final rounding"


@pytest.mark.parametrize("value,seed", [
    (2.0, 3.0), (3.0, 1.0),
    (math.ulp(0.0), math.ulp(0.0)),
    (1.0, 3*math.ulp(0.0)), (1.0, 5*math.ulp(0.0)),
    (2.0**1000, 2.0**1023),
])
def test_r10_sqrt_derivative_full_cell_certificate(value, seed):
    result = dual.sqrt(dual.Dual(value, (seed,)))
    assert_sqrt_rounding(result.e[0], F(seed)**2/(4*F(value)),
                         "full analytic sqrt derivative cell")


def test_r10_half_power_source_decimal_fallback_mutation_is_caught(monkeypatch):
    source = textwrap.dedent(inspect.getsource(dual.Dual.__pow__))
    needle = "if Fraction(p).denominator == 2:"
    assert source.count(needle) == 1
    namespace = dict(vars(dual))
    exec(compile(source.replace(needle, "if False:"), "<r10-decimal-half-power>", "exec"), namespace)
    monkeypatch.setattr(dual.Dual, "__pow__", namespace["__pow__"])
    with pytest.raises(AssertionError, match="half-integer derivative exact tie must round to even"):
        test_r10_half_integer_power_derivative_keeps_exact_subnormal_ties(-716, 1.5, "0x1.8p-715", 1)


def test_r10_atan2_source_float_fast_path_mutation_is_caught(monkeypatch):
    source = inspect.getsource(dual._ratio_derivative)
    needle = "u, v, a, b = (Fraction(q) for q in (u, v, a, b))"
    assert source.count(needle) == 1
    namespace = dict(vars(dual))
    exec(compile(source.replace(needle, "u, v, a, b = (float(q) for q in (u, v, a, b))"),
                 "<r10-angular-float-path>", "exec"), namespace)
    monkeypatch.setattr(dual, "_ratio_derivative", namespace["_ratio_derivative"])
    with pytest.raises(AssertionError, match="atan2 derivative exact rational final rounding"):
        test_r10_atan2_derivative_uses_one_final_rational_rounding(0)


def test_r10_power_source_removed_range_check_mutation_is_caught(monkeypatch):
    source = textwrap.dedent(inspect.getsource(dual.Dual.__pow__))
    needle = "if value == 0.0 and self.v != 0.0:"
    assert source.count(needle) == 1
    namespace = dict(vars(dual))
    mutated = source.replace(needle, "if False:")
    # R13FIXb added a second checked boundary for exact integer primals.
    # Restore the same silent-primal-underflow defect through both guards.
    exact_primal = 'scalar_rational(Fraction(self.v) ** int(p), quantity="Dual integer power")'
    assert mutated.count(exact_primal) == 1
    mutated = mutated.replace(exact_primal, 'float(Fraction(self.v) ** int(p))')
    exec(compile(mutated, "<r10-unchecked-power-primal>", "exec"), namespace)
    monkeypatch.setattr(dual.Dual, "__pow__", namespace["__pow__"])
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_r10_power_primal_underflow_without_an_exact_channel_fails_loudly(2.0)
