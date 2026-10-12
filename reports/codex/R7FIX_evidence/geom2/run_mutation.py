"""In-memory source mutation: execute modified tested function, never patch output."""
import ast
import importlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'src'))
kind = sys.argv[1]
if kind == 'G6G-01':
    mod = importlib.import_module('eab.kernel2d.g0_oracle')
    name = 'ray_exit'
    source = Path(mod.__file__).read_text(encoding='utf-8-sig')
    source = source.replace('if overlap(Ah, B) == 0 and boundary_has_exterior(Ah, B):',
                            'if False:  # mutation: ignore exact event itself')
    selected = 'test_g6g01_first_exit_checks_isolated_true_boundary_event'
elif kind == 'G6G-02':
    mod = importlib.import_module('eab.kernel2d.covers')
    name = 'vv_cover'
    source = Path(mod.__file__).read_text(encoding='utf-8-sig')
    source = source.replace('return Cover("VV", ia, jb, unit(d), norm(d), None, a, active, a, b, expanded)',
                            'd = tuple(map(float, d))\n    return Cover("VV", ia, jb, unit(d), norm(d), None, a, active, a, b, expanded)')
    selected = 'test_g6g02_vv_uses_exact_difference_and_independent_unit_normal[True]'
else:
    mod = importlib.import_module('eab.kernel2d.g0')
    name = '_construction_error_exceeds'
    source = '''def _construction_error_exceeds(error, length2, truth, atol, *polys):
    L = max(math.hypot(max(p[0] for p in P)-min(p[0] for p in P),
                      max(p[1] for p in P)-min(p[1] for p in P)) for P in polys)
    C = max(abs(v) for P in polys for p in P for v in p)
    return error > atol*max(L,truth)+64*math.ulp(1.0)*C
'''
    selected = 'test_g6g03_unrepresentable_diameter_does_not_disable_missing_cover_gate[distance]'
node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)
exec(compile(ast.Module(body=[node], type_ignores=[]), '<R7 internal mutation '+kind+'>', 'exec'), mod.__dict__)
code = pytest.main(['-q','-p','no:cacheprovider',str(ROOT/'tests/test_r7fix_geom2.py')+'::'+selected,
                    '--basetemp='+str(ROOT/'reports/codex/R7FIX_evidence/tmp'/('mutant_'+kind))])
print(json.dumps({'mutation':kind,'internal_function':name,'test':selected,'pytest_exit':int(code),
                  'expected_red':code==1}))
raise SystemExit(0 if code == 1 else 1)
