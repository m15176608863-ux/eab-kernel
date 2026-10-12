"""In-memory mutations of production functions, no working-file swap."""
from pathlib import Path
import inspect, math, sys, textwrap
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
import pytest
import eab.dual as D
import eab.kernel3d.frozen as Z
mode=sys.argv[1]
if mode=='power':
    fn=D.Dual.__pow__; scope=dict(vars(D))
    source=textwrap.dedent(inspect.getsource(fn))
    old='    value = self.v ** p\n'
    new=old+('    if _ordinary(self.v, p, *self.e):\n'
             '        c = p * self.v ** (p - 1.0)\n'
             '        return Dual(value, tuple(c * a for a in self.e))\n')
    target='tests/test_r7fix_dual.py::test_g6g07_minimal_representable_derivative_survives'
else:
    fn=Z._unit_jet; scope=dict(vars(Z));scope['math']=math
    source=textwrap.dedent(inspect.getsource(fn))
    old='        magnitude = sqrt_rational(c * c / nn)'
    if mode=='frozen_value':
        new='        magnitude = abs(float(c / max(map(abs,n)))) / math.hypot(*(float(x / max(map(abs,n))) for x in n))'
        target='tests/test_r7fix_frozen.py::test_frozen_unit_component_rounds_after_final_normalization'
    else:
        new='        magnitude = abs(_derivative_float(c / Fraction(math.sqrt(float(nn)))))'
        target='tests/test_r7fix_frozen.py::test_frozen_unit_derivative_rounds_after_exact_normalization'
assert source.count(old)==1
exec(compile(source.replace(old,new),fn.__code__.co_filename,'exec'),scope)
if mode=='power': D.Dual.__pow__=scope[fn.__name__]
else: Z._unit_jet=scope[fn.__name__]
raise SystemExit(pytest.main(['-q','-p','no:cacheprovider',str(ROOT/target.split('::')[0])+'::'+target.split('::')[1], '--basetemp='+str(ROOT/'reports/codex/R7FIX_evidence/tmp'/('mut_'+mode))]))
