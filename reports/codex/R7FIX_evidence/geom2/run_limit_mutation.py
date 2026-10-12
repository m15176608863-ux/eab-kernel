"""Limit same-family internal-source mutants; red must hit midpoint equality."""
import inspect
from pathlib import Path
import sys
import textwrap
import pytest
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
import eab.limit as limit
kind=sys.argv[1]
if kind=='normal':
    source=textwrap.dedent(inspect.getsource(limit.LimitContact.__post_init__))
    begin=source.index('    exact = tuple(map(Fraction, self.normal))')
    end=source.index('    # G6 第四轮 minor',begin)
    source=source[:begin]+('    n = sum((v/m)**2 for v in self.normal)**.5\n'
                          '    self.normal = tuple(v/m/n for v in self.normal)\n')+source[end:]
    scope=dict(vars(limit));exec(compile(source,'<internal limit normal mutant>','exec'),scope)
    limit.LimitContact.__post_init__=scope['__post_init__']
    selected='test_limit_contact_normal_retains_final_subnormal_component[1]'
else:
    exec('def _norm(v):\n    m=max(abs(x) for x in v)\n    return m*sum((x/m)**2 for x in v)**.5\n',vars(limit))
    selected='test_limit_norm_retains_final_representable_root_before_rounding'
code=pytest.main(['-q','-p','no:cacheprovider',str(ROOT/'tests/test_r7fix_limit_construction.py')+'::'+selected])
print('mutation',kind,'pytest_exit',code,'expected_red',code==1)
raise SystemExit(0 if code==1 else 1)
