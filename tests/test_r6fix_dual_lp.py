"""R6FIX-07/11/12: independent rational derivative and LP certificate oracles.

The oracle uses only Fraction and the defining algebra, not production scaling,
Dual arithmetic, simplex bases or certificate helpers.
"""

from fractions import Fraction as F
import inspect
import math
import textwrap

import pytest

from eab.dual import Dual, atan2
import eab.dual as dual_module
import eab.lp as lp


@pytest.mark.parametrize("scale", [math.ldexp(1.0, e) for e in
                                  (-1074, -1000, -665, -300, 0, 300, 665, 1000, 1023)])
def test_r6fix07_division_and_reverse_preserve_representable_derivatives(scale):
    """Every input/result is finite, including the smallest subnormal scale."""
    direct = Dual(scale, (scale, -scale, 0.0)) / scale
    reverse = scale / Dual(scale, (scale, -scale, 0.0))
    assert direct.v == reverse.v == 1.0
    assert direct.e == (1.0, -1.0, 0.0), (scale, direct)
    assert reverse.e == (-1.0, 1.0, 0.0), (scale, reverse)


@pytest.mark.parametrize("y,x,dy,dx", [
    (1e200, 1e200, 0.0, 1.0),
    (1e-200, 1e-200, 0.0, 1.0),
    (1e-300, 1e300, 1e300, 1e-300),
    (1e300, 1e-300, 1e300, 1e-300),
    (3e-200, -2e-200, 7e-200, 1e-200),
    (3e200, -2e200, 7e200, 1e200),
    (math.ulp(0.0), math.ulp(0.0), math.ulp(0.0), -math.ulp(0.0)),
])
def test_r6fix07_atan2_matches_independent_fraction_derivative(y, x, dy, dx):
    q = (F(x) * F(dy) - F(y) * F(dx)) / (F(x) ** 2 + F(y) ** 2)
    got = atan2(Dual(y, (dy,)), Dual(x, (dx,)))
    assert got.v == math.atan2(y, x)
    assert got.e == (float(q),), (got.e, float(q))


@pytest.mark.parametrize("u,v,du,dv", [
    (1e300, 1e300, 1e300, math.nextafter(1e300, math.inf)),
    (1e-300, 1e-300, 1e-300, math.nextafter(1e-300, math.inf)),
    (1e-300, 1e300, 1e300, 1e300),
    (3e200, -2e200, 7e200, 1e200),
    (3e-200, -2e-200, 7e-200, 1e-200),
])
def test_r6fix07_quotient_with_two_active_inputs_matches_fraction(u, v, du, dv):
    q = (F(du) * F(v) - F(u) * F(dv)) / F(v) ** 2
    got = Dual(u, (du,)) / Dual(v, (dv,))
    assert got.v == u / v
    assert got.e == (float(q),), (got.e, float(q))


@pytest.mark.parametrize("u,v,du,dv", [
    (1e150, 1e150, 1e160, -1e160),
    (1e150, 1e150, 1e160, -math.nextafter(1e160, math.inf)),
    (2.0 ** -600, 2.0 ** -600, 2.0 ** -475, 2.0 ** -475),
])
def test_r6fix07_related_product_derivative_avoids_intermediate_range_loss(u, v, du, dv):
    expected = float(F(du) * F(v) + F(u) * F(dv))
    r = Dual(u, (du,)) * Dual(v, (dv,))
    assert r.e == (expected,), (r, expected)


@pytest.mark.parametrize("base,seed", [(1e-200, 1e-200), (-1e-200, 1e-200)])
def test_r6fix07_related_inverse_power_derivative_is_representable(base, seed):
    r = Dual(base, (seed,)) ** -1
    assert r.e == (float(-F(seed) / F(base) ** 2),)


@pytest.mark.parametrize("base,power,seed,expected", [
    (2.0 ** -1000, -0.5, 2.0 ** -1000, -(2.0 ** 499)),
    (2.0 ** 1000, -0.5, 2.0 ** 1000, -(2.0 ** -501)),
    (2.0 ** 1000, -1.5, 2.0 ** 1000, -(3 * F(2) ** -1501)),
    (2.0 ** 1000, -0.5, 2.0 ** -20, -(F(2) ** -1521)),
])
def test_r6fix07_fractional_power_never_loses_a_representable_derivative(base, power, seed, expected):
    # Half-integer powers of powers of two have independent exact rational derivatives.
    expected = F(expected)
    if float(expected) == 0.0:
        with pytest.raises((FloatingPointError, OverflowError, ArithmeticError)):
            Dual(base, (seed,)) ** power
    else:
        result = Dual(base, (seed,)) ** power
        assert result.e == (float(expected),)


@pytest.mark.parametrize("operation", [
    lambda: Dual(1.0, (1e300,)) / 1e-300,
    lambda: Dual(1.0, (1e-300,)) / 1e300,
    lambda: atan2(Dual(math.ulp(0.0), (1.0,)), Dual(math.ulp(0.0), (0.0,))),
])
def test_r6fix07_unrepresentable_derivatives_fail_loudly(operation):
    with pytest.raises((OverflowError, FloatingPointError)):
        operation()


@pytest.mark.parametrize("base", [0.0, -0.0, 2.0, -3.0, 1e-300, 1e300])
@pytest.mark.parametrize("width", [0, 1, 3])
@pytest.mark.parametrize("exponent", [0, 0.0, -0.0])
def test_r6fix11_zero_power_is_constant_one_with_same_width(base, width, exponent):
    r = Dual(base, tuple(float(i + 1) for i in range(width))) ** exponent
    assert r.v == 1.0 and r.e == (0.0,) * width


def _assert_exact_optimal_certificate(r, A, b, c, maximize):
    """Independent standard-form primal/dual feasibility and strong duality."""
    assert r.status == lp.OPTIMAL
    assert r.exact_x is not None, "optimal result must carry exact_x"
    assert r.exact_y is not None, "optimal result must carry exact_y"
    x, y = r.exact_x, r.exact_y
    assert len(x) == len(c) and len(y) == len(b)
    assert all(isinstance(t, F) for t in x + y)
    assert all(t >= 0 for t in x)
    assert all(sum(F(a) * t for a, t in zip(row, x)) == F(rhs)
               for row, rhs in zip(A, b))
    reduced = [F(cj) - sum(F(A[i][j]) * y[i] for i in range(len(A)))
               for j, cj in enumerate(c)]
    assert all(t <= 0 if maximize else t >= 0 for t in reduced)
    assert sum(F(ci) * xi for ci, xi in zip(c, x)) == sum(F(bi) * yi for bi, yi in zip(b, y))


@pytest.mark.parametrize("maximize", [False, True])
@pytest.mark.parametrize("mode", ["normal", "forced_exact"])
@pytest.mark.parametrize("A,b,c", [
    ([], [], []),
    ([], [], [0.0, 1.0]),
    ([[]], [0.0], []),
    ([[1.0]], [0.0], [1.0]),
    ([[1.0, 1.0], [2.0, 2.0]], [1.0, 2.0], [1.0, 2.0]),
    ([[F(3)]], [F(1)], [F(1)]),
])
def test_r6fix12_every_optimal_path_has_complete_exact_witnesses(monkeypatch, maximize, mode, A, b, c):
    if mode == "forced_exact":
        def no_float(*args, **kw):
            raise RuntimeError("force exact simplex path")
        monkeypatch.setattr(lp, "_float_solve", no_float)
    target = [-t for t in c] if maximize else c
    fn = lp.maximize if maximize else lp.solve
    r = fn([[float(t) for t in row] for row in A], [float(t) for t in b],
           [float(t) for t in target], exact=(A, b, target))
    _assert_exact_optimal_certificate(r, A, b, target, maximize)


def _mutant_function(function, old, new, namespace):
    """Compile a mutation *inside* the tested function; do not alter its outputs."""
    source = textwrap.dedent(inspect.getsource(function))
    assert source.count(old) == 1
    scope = dict(namespace)
    exec(compile(source.replace(old, new), function.__code__.co_filename, "exec"), scope)
    return scope[function.__name__]


def test_r6fix07_mutation_reinstated_unscaled_quotient_is_caught(monkeypatch):
    def legacy(self, o):
        ov, oe = self._pair(o)
        inv = 1.0 / ov
        return Dual(self.v * inv, tuple((a * ov - self.v * b) * inv * inv
                                        for a, b in zip(self.e, oe)))
    monkeypatch.setattr(Dual, "__truediv__", legacy)
    with pytest.raises(AssertionError):
        test_r6fix07_division_and_reverse_preserve_representable_derivatives(1e200)


def test_r6fix11_mutation_removed_constant_power_branch_is_caught(monkeypatch):
    mutant = _mutant_function(Dual.__pow__,
                              "    if p == 0.0:\n        return Dual(1.0, (0.0,) * self.width)\n",
                              "", vars(dual_module))
    monkeypatch.setattr(Dual, "__pow__", mutant)
    with pytest.raises(ZeroDivisionError):
        test_r6fix11_zero_power_is_constant_one_with_same_width(0.0, 1, 0.0)


def test_r6fix12_mutation_removed_empty_problem_witness_is_caught(monkeypatch):
    mutant = _mutant_function(lp.solve,
                              "exact_x=(Fraction(0),) * n, exact_y=()",
                              "exact_x=None, exact_y=None", vars(lp))
    monkeypatch.setattr(lp, "solve", mutant)
    with pytest.raises(AssertionError, match="optimal result must carry exact_x"):
        _assert_exact_optimal_certificate(lp.solve([], [], [0.0, 1.0]), [], [], [0.0, 1.0], False)
