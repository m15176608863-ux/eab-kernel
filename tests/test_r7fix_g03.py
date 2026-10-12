"""R7 same-family G0 acceptance audit; no fabricated post-enumeration data."""
import inspect
import math
import pytest
from eab.kernel3d import covers3 as C, g03 as G
from eab.kernel3d.geom3 import box


def test_g03_missing_covers_never_pass_an_overflowed_acceptance_bound(monkeypatch):
    A,B=box(),box(center=(3,0,0))
    control=G.g0_distance_completeness3(A,B,radius=0,samples=1,tol=0,atol=1e308)
    assert control.samples == 1 and control.passed
    source=inspect.getsource(C.enumerate_covers3)
    assert 'out.append(c)' in source
    scope=dict(vars(C))
    exec(compile(source.replace('out.append(c)','pass'),__file__,'exec'),scope)
    monkeypatch.setattr(C,'enumerate_covers3',scope['enumerate_covers3'])
    report=G.g0_distance_completeness3(A,B,radius=0,samples=1,tol=0,atol=1e308)
    assert report.samples == 1 and not report.passed, 'nonfinite error must independently reject missing covers'
    assert math.isinf(report.failures[0][1])


@pytest.mark.parametrize('atol',[math.nan,math.inf,-1.])
def test_g03_acceptance_tolerance_must_be_finite_nonnegative(atol):
    with pytest.raises(ValueError, match='atol'):
        G.g0_distance_completeness3(box(),box(center=(3,0,0)),radius=0,samples=1,atol=atol)


def test_g03_a_finite_minimum_cannot_hide_a_nonfinite_candidate(monkeypatch):
    import re
    source=inspect.getsource(C.enumerate_covers3)
    source=re.sub(r'(?m)^([ ]*)out.append\(c\)$',
                  lambda m:m[1]+"if len(out) == 1:\n"+m[1]+"    c.point_a = (float('nan'),)*3\n"+m[0], source)
    scope=dict(vars(C))
    exec(compile(source,__file__,'exec'),scope)
    monkeypatch.setattr(C,'enumerate_covers3',scope['enumerate_covers3'])
    A,B=box(),box(center=(3,0,0))
    real=C.enumerate_covers3(A,B,window=math.inf,tol=0)
    # The injected coordinate already is a binary64 NaN, not an exact quantity
    # to be constructed. Inspect it directly before asking the report to fail.
    assert any(c.in_extent and math.isnan(c.point_a[0]) for c in real)
    report=G.g0_distance_completeness3(A,B,radius=0,samples=1,tol=0)
    assert not report.passed, 'finite minimum must not hide an invalid constructed witness'
