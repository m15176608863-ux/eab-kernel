"""Exercise the actual three rewritten sorting loops against their old contract.

Read-only source extraction; no production patch or policy generation. The
test deliberately retains an old cmp_to_key reference only as an independent
ordering contract in this evidence script, outside production source.
"""
import ast
import copy
from fractions import Fraction as F
from functools import cmp_to_key
import importlib
import json
from pathlib import Path
import random
import sys
import time


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'src'))


def make_probe(path, function_name, argument, comparator_name):
    source = (ROOT/path).read_text(encoding='utf-8-sig')
    tree = ast.parse(source)
    parent = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == function_name)
    # Capture the real `ordered=[]; for ...: ... ordered.insert(...)` statements,
    # even when they are nested in the outer chamber loop.
    pair = None
    for n in ast.walk(parent):
        for _, body in ast.iter_fields(n):
            if not isinstance(body, list):
                continue
            for a, b in zip(body, body[1:]):
                if (isinstance(a, ast.Assign) and isinstance(a.targets[0], ast.Name)
                        and a.targets[0].id == 'ordered' and isinstance(a.value, ast.List)
                        and isinstance(b, ast.For)):
                    pair = [copy.deepcopy(a), copy.deepcopy(b)]
    assert pair is not None, path
    comparator = next((n for n in parent.body if isinstance(n, ast.FunctionDef) and n.name == comparator_name), None)
    helpers = [copy.deepcopy(n) for n in parent.body if isinstance(n, ast.FunctionDef)
               and n.name in {'compare', 'half'}]
    module_name = path.removeprefix('src/').removesuffix('.py').replace('/', '.')
    namespace = vars(importlib.import_module(module_name)).copy()
    if comparator is not None:
        helper_module = ast.fix_missing_locations(ast.Module(body=copy.deepcopy(helpers), type_ignores=[]))
        exec(compile(helper_module, path, 'exec'), namespace)
    comparator_fn = namespace[comparator_name]
    wrapper = ast.FunctionDef(
        name='_actual_loop',
        args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=argument)],vararg=None,
                           kwonlyargs=[],kw_defaults=[],kwarg=None,defaults=[]),
        body=helpers+pair+[ast.Return(ast.Name(id='ordered',ctx=ast.Load()))],
        decorator_list=[],
    )
    module = ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[]))
    exec(compile(module,path,'exec'),namespace)
    before = (HERE/'final_dynamic_before'/Path(path+'.txt')).read_text(encoding='utf-8-sig')
    old_tree = ast.parse(before)
    old_comparator = next(n for n in ast.walk(old_tree) if isinstance(n,ast.FunctionDef) and n.name==comparator_name)
    current_comparator = next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==comparator_name)
    assert ast.dump(old_comparator)==ast.dump(current_comparator), 'Comparator changed'
    return namespace['_actual_loop'], comparator_fn


def main():
    specs = [
        ('src/eab/kernel2d/exact.py','entrance_membership_exact','rays','compare'),
        ('src/eab/kernel2d/g0_oracle.py','boundary_has_exterior','rays','compare'),
        ('src/eab/kernel3d/entrance_topology.py','_chamber_directions','lines','_angular_compare'),
    ]
    start=time.perf_counter()
    results=[]
    # Distinct objects for equal-angle data check stability, not merely values.
    values=[(F(x,7),F(y,11)) for x in range(-4,5) for y in range(-4,5) if x or y]
    values += [(F(2*x,7),F(2*y,11)) for x in range(-3,4) for y in range(-3,4) if x or y]
    for path,scope,arg,cmp in specs:
        probe,compare=make_probe(path,scope,arg,cmp)
        rng=random.Random(12012)
        for seed in range(50):
            xs=list(values);rng.shuffle(xs)
            expected=sorted(xs,key=cmp_to_key(compare))
            actual=probe(xs)
            assert len(actual)==len(expected)
            assert all(a is b for a,b in zip(actual,expected)), (path,seed)
        results.append({'path':path,'function':scope,'shuffles':50,
                        'elements_per_shuffle':len(values),
                        'comparator_AST_unchanged':True,
                        'value_and_stable_identity_order_equal':True})
    payload={'results':results,'total_source_loop_cases':150,'wall_seconds':time.perf_counter()-start,
             'writes':'Only this JSON evidence, under the worktree; source and tests are read-only.'}
    (HERE/'dynamic_final_sort_equivalence.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
