"""Process-local mutation: conflate old rounded image with exact affine data."""
from pathlib import Path
from fractions import Fraction
import inspect,sys
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools'),str(ROOT/'tests')]
import test_bb52_g1 as test
source=inspect.getsource(test._rounded_distance_audit)
needle='rounded = translate(A, x)'
assert needle in source
namespace=dict(test.__dict__,Fraction=Fraction)
exec(source.replace(needle,'rounded = [tuple(Fraction(p[i]) + Fraction(x[i]) for i in range(2)) for p in A]'),namespace)
test._rounded_distance_audit=namespace['_rounded_distance_audit']
import pytest
raise SystemExit(pytest.main(['-q','-p','no:cacheprovider',str(ROOT/'tests/test_bb52_g1.py')+'::test_g0_exit_completeness_has_teeth[drop_VE_subset]',
'--basetemp',str(ROOT/'reports/codex/R6FIX_evidence/tmp/g0_bb52_mutant')]))
