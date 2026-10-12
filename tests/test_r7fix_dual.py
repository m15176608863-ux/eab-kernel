"""G6G-07: exact power-of-two oracles, no production Dual/scaling primitives.

The review's complete 876 representable exponent cells are retained. Fraction
powers provide exact derivatives; no finite-difference or geometric helper is shared.
"""
from fractions import Fraction as F
import inspect
import math
import textwrap

import pytest

from eab.dual import Dual
import eab.dual as dual_module


def _power_cases():
    cases = []
    for exponent in (-200, -180, -160, -140, 140, 160, 180, 200):
        for seed_exp in (-200, -100, 0, 100, 200):
            for p in (F(k, 2) for k in range(-16, 17) if k):
                q = p * F(2) ** int(exponent * (p - 1)) * F(2) ** seed_exp
                try:
                    expected = float(q)
                    primal = float(F(2) ** int(exponent * p))
                except OverflowError:
                    continue
                if not expected or not primal or not math.isfinite(primal):
                    continue
                cases.append((exponent, seed_exp, float(p), primal, expected))
    assert len(cases) == 876
    assert len({c[-1] for c in cases}) > 400
    return cases


@pytest.mark.parametrize("exponent,seed_exp,p,primal,expected", _power_cases())
def test_g6g07_derived_power_range_not_just_inputs(exponent, seed_exp, p, primal, expected):
    result = Dual(math.ldexp(1., exponent), (math.ldexp(1., seed_exp),)) ** p
    assert result.v == primal
    assert result.e == (expected,), "representable power derivative lost before seed multiplication"


def test_g6g07_minimal_representable_derivative_survives():
    x = 2. ** 200
    expected = float(F(-5) * F(x) ** -6 * F(x))
    result = Dual(x, (x, -x, 0.0)) ** -5
    assert result.v == 2. ** -1000
    assert result.e == (expected, -expected, 0.0), "nonzero derivative must not become signed zero"


def test_g6g07_input_only_fast_path_mutation_is_caught(monkeypatch):
    # Reintroduce the defective branch INSIDE __pow__, before any real output.
    source = textwrap.dedent(inspect.getsource(Dual.__pow__))
    marker = "    value = self.v ** p\n"
    assert source.count(marker) == 1
    injected = marker + ("    if _ordinary(self.v, p, *self.e):\n"
                         "        c = p * self.v ** (p - 1.0)\n"
                         "        return Dual(value, tuple(c * a for a in self.e))\n")
    scope = dict(vars(dual_module))
    exec(compile(source.replace(marker, injected), __file__, "exec"), scope)
    monkeypatch.setattr(Dual, "__pow__", scope["__pow__"])
    with pytest.raises(AssertionError, match="nonzero derivative must not become signed zero"):
        test_g6g07_minimal_representable_derivative_survives()
