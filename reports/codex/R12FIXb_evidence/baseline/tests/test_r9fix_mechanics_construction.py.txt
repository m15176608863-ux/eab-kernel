"""R9 same-family mechanics constructions: analytic axes and scalar powers only.

Expected frames are the 3-4-5 identity; no production tangent/norm/root primitive
constructs the oracle. Exact powers of two certify the large-integer sqrt range.
"""
from fractions import Fraction as F
import inspect
import math

import pytest

import eab.dual as dual
import eab.limit as limit


@pytest.mark.parametrize('exponent', [-600, 0, 600])
@pytest.mark.parametrize('rational', [False, True])
def test_r9_tangent_frame_is_invariant_to_representable_direction_scale(exponent, rational):
    s = F(2)**exponent if rational else math.ldexp(1., exponent)
    try:
        result = limit._tangents((0., 0., 1.), 3, (3*s, 4*s, 5*s))
    except (ArithmeticError, ValueError) as error:
        raise AssertionError(f'tangent-scale-invariant-frame-construction: {error}') from error
    assert result == [(0.6, 0.8, 0.), (-0.8, 0.6, 0.)], 'tangent-scale-invariant-frame-construction'


@pytest.mark.parametrize('s', [1e-200, 1., 1e200])
def test_r9_friction_generators_do_not_reject_resolvable_axis_tangent(s):
    contact = limit.LimitContact((0., 0., 0.), (0., 0., 1.), .5, tangent=(s, 0., 0.))
    generators = limit.friction_generators(contact.normal, contact.mu, 3, tangent=contact.tangent)
    assert generators[0] == (.5, 0., 1.), 'axis-tangent-is-resolvable'


@pytest.mark.parametrize('exponent', [-600, 0, 600])
def test_r9_tangent_near_parallel_guard_remains_relative_at_extreme_scale(exponent):
    s = math.ldexp(1., exponent)
    n = (1/math.sqrt(3),)*3
    with pytest.raises(ValueError, match='within rounding'):
        limit._tangents(n, 3, (s, s, s*(1+2.**-50)))


@pytest.mark.parametrize('exponent', [0, 1000, 1200, 2046])
def test_r9_dual_primal_sqrt_large_integer_keeps_representable_root(exponent):
    try:
        value = dual.sqrt(2**exponent)
    except (ArithmeticError, ValueError) as error:
        raise AssertionError(f'large-integer-final-root: {error}') from error
    assert value == math.ldexp(1., exponent//2), 'large-integer-final-root'


def test_r9_dual_primal_sqrt_range_failure_is_only_for_the_final_root():
    with pytest.raises(OverflowError):
        dual.sqrt(2**2048)
    assert dual.sqrt(F(1, 2**1200)) == math.ldexp(1., -600)


def test_r9_dual_sqrt_derivative_normal_domain_is_unchanged():
    assert dual.sqrt(dual.Dual(4., (2., -3.))) == dual.Dual(2., (.5, -.75))


def test_r9_tangent_intermediate_norm_mutant_is_caught(monkeypatch):
    source = inspect.getsource(limit._tangents)
    needle = 't1 = unit_rational(t1)'
    assert source.count(needle) == 1
    mutant = 'length = math.sqrt(scalar_rational(sum(v*v for v in t1)))\n    t1 = tuple(v / length for v in t1)'
    namespace = dict(vars(limit))
    exec(compile(source.replace(needle, mutant), '<r9-tangent-intermediate-norm>', 'exec'), namespace)
    monkeypatch.setattr(limit, '_tangents', namespace['_tangents'])
    with pytest.raises(AssertionError, match='tangent-scale-invariant-frame-construction'):
        test_r9_tangent_frame_is_invariant_to_representable_direction_scale(-600, False)


def test_r9_dual_sqrt_implicit_float_mutant_is_caught(monkeypatch):
    source = inspect.getsource(dual.sqrt)
    needle = 'return sqrt_rational(x)'
    assert source.count(needle) == 1
    namespace = dict(vars(dual))
    exec(compile(source.replace(needle, 'return math.sqrt(x)'), '<r9-implicit-root-float>', 'exec'), namespace)
    monkeypatch.setattr(dual, 'sqrt', namespace['sqrt'])
    with pytest.raises(AssertionError, match='large-integer-final-root'):
        test_r9_dual_primal_sqrt_large_integer_keeps_representable_root(1200)
