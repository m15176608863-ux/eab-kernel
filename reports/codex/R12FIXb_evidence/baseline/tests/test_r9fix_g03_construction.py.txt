"""G03 invalid-display reporting: mutate inside enumeration, never append output."""
import inspect
import math
import re

import pytest

from eab.kernel3d import covers3 as C, g03 as G
from eab.kernel3d.geom3 import box


def _bad_witness_report(monkeypatch, payload):
    source = inspect.getsource(C.enumerate_covers3)
    source, count = re.subn(r'(?m)^([ ]*)out.append\(c\)$',
        lambda match: match[1]+'if len(out) == 1:\n'+match[1]+'    c.point_a = '+payload+'\n'+match[0], source)
    assert count > 0
    namespace = dict(vars(C))
    exec(compile(source, '<r9-g03-invalid-witness>', 'exec'), namespace)
    monkeypatch.setattr(C, 'enumerate_covers3', namespace['enumerate_covers3'])
    try:
        report = G.g0_distance_completeness3(box(), box(center=(3, 0, 0)), radius=0, samples=1, tol=0)
    except (ArithmeticError, ValueError) as error:
        raise AssertionError(f'g03-invalid-display-recorded: {error}') from error
    assert not report.passed and report.construction_failures, 'g03-invalid-display-recorded'
    assert not report.completeness_failures, 'invalid-display-does-not-change-exact-completeness'
    assert report.samples == 1
    return report


@pytest.mark.parametrize('payload', ["(float('nan'),)*3", "(float('inf'),)*3", "(float('-inf'),)*3", 'None'])
def test_g03_invalid_display_is_reported_without_calling_finite_constructor(monkeypatch, payload):
    _bad_witness_report(monkeypatch, payload)


def test_g03_display_validation_removal_mutant_is_caught(monkeypatch):
    source = inspect.getsource(G._display_witness_distance)
    needle = 'if point_a is None or point_b is None or not all('
    assert source.count(needle) == 1
    namespace = dict(vars(G))
    source = source.replace(needle, 'if False and (point_a is None or point_b is None or not all(')
    source = source.replace('for x in (*point_a, *point_b)):', 'for x in (*point_a, *point_b))):')
    exec(compile(source, '<r9-g03-no-display-validation>', 'exec'), namespace)
    monkeypatch.setattr(G, '_display_witness_distance', namespace['_display_witness_distance'])
    with pytest.raises(AssertionError, match='g03-invalid-display-recorded'):
        _bad_witness_report(monkeypatch, "(float('nan'),)*3")
