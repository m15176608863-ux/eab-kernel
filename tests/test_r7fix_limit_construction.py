"""R7 same-family limit normalization: independent exact midpoint oracles."""
from fractions import Fraction as F
import inspect
import math
import sys
import textwrap

import pytest

from eab.limit import LimitContact
import eab.limit as limit_module


@pytest.mark.parametrize('sign', [-1, 1])
def test_limit_contact_normal_retains_final_subnormal_component(sign):
    q = F(2)**-1074
    vector = (3., 3., sign*float(7*q))
    square = sum(F(v)**2 for v in vector)
    component_square = (7*q)**2/square
    # Unique nearest floating output is 2q. No production helper is shared.
    assert (F(3, 2)*q)**2 < component_square < (F(5, 2)*q)**2
    result = LimitContact((0., 0., 0.), vector)
    assert result.normal[2] == sign*float(2*q), 'normal component rounded before final normalization'


def test_limit_norm_retains_final_representable_root_before_rounding():
    q = F(2)**-1074
    vector = (F(149, 100)*q, F(49, 100)*q)
    square = sum(v*v for v in vector)
    assert (F(3, 2)*q)**2 < square < (F(5, 2)*q)**2
    assert limit_module._norm(vector) == float(2*q)


def test_limit_norm_finite_input_unrepresentable_result_fails_loud():
    with pytest.raises((ArithmeticError, OverflowError)):
        limit_module._norm((sys.float_info.max, sys.float_info.max))


def test_limit_normal_nonzero_unrepresentable_component_fails_loud():
    with pytest.raises((ArithmeticError, OverflowError)):
        LimitContact((0., 0., 0.), (sys.float_info.max, 1., 2.**-1074))


def test_limit_normal_early_rounding_mutation_is_caught(monkeypatch):
    source = textwrap.dedent(inspect.getsource(LimitContact.__post_init__))
    begin = source.index('    exact = tuple(map(Fraction, self.normal))')
    end = source.index('    # G6 第四轮 minor', begin)
    source = source[:begin] + ('    n = sum((v/m)**2 for v in self.normal)**.5\n'
                              '    self.normal = tuple(v/m/n for v in self.normal)\n') + source[end:]
    scope = dict(vars(limit_module))
    exec(compile(source, '<internal LimitContact normalization mutant>', 'exec'), scope)
    monkeypatch.setattr(LimitContact, '__post_init__', scope['__post_init__'])
    with pytest.raises(AssertionError, match='normal component rounded before final normalization'):
        test_limit_contact_normal_retains_final_subnormal_component(1)


def test_limit_norm_early_scaling_mutation_is_caught(monkeypatch):
    def old_norm(v):
        m = max(abs(x) for x in v)
        return m*sum((x/m)**2 for x in v)**.5
    monkeypatch.setattr(limit_module, '_norm', old_norm)
    with pytest.raises(AssertionError):
        test_limit_norm_retains_final_representable_root_before_rounding()
