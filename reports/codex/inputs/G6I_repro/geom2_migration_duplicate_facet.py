"""One same-input old/new migration tooth check; no tracked file is edited."""
from pathlib import Path
import ast,inspect,sys,json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
import eab.kernel2d.covers as cv
import test_invariance_2d as gate
original=cv.convex_entrance_block
before=hashlib.sha256((ROOT/'src/eab/kernel2d/covers.py').read_bytes()).hexdigest()
oldtext=subprocess.check_output(['git','show','b6126cf:tests/test_invariance_2d.py'],cwd=ROOT).decode('utf-8-sig')
scope=dict(vars(gate))
for name in ('_facet_set','test_convex_g0_is_invariant'):
    node=next(n for n in ast.parse(oldtext).body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(ast.get_source_segment(oldtext,node),scope)
case=gate.CONVEX_CASES[-1]
motion=gate.MOTIONS[4]
scope['test_convex_g0_is_invariant'](case,motion)
gate.test_convex_g0_is_invariant(case,motion)
source=inspect.getsource(original)
old='return EntranceBlock(verts, [f.label for f in ex.facets], list(ex.pairs))'
new='''labels = [f.label for f in ex.facets]
    if max(abs(p[0]) for P in (A, B) for p in P) > 100:
        labels.append(labels[0])
    return EntranceBlock(verts, labels, list(ex.pairs))'''
assert source.count(old)==1
namespace=dict(vars(cv));exec(compile(source.replace(old,new),__file__,'exec'),namespace)
mutant=namespace['convex_entrance_block']
saved=gate.convex_entrance_block
try:
    cv.convex_entrance_block=gate.convex_entrance_block=mutant
    scope['convex_entrance_block']=mutant
    try:scope['test_convex_g0_is_invariant'](case,motion)
    except AssertionError as error:old_status='AssertionError: '+str(error)
    else:old_status='PASS'
    gate.test_convex_g0_is_invariant(case,motion)
    assert old_status!='PASS'
    _,_,poly=gate._T(motion[1],motion[2],motion[3]);out=mutant(poly(case[1]),poly(case[2]))
    assert len(out.facets)==len(out.vertices)+1
    print(json.dumps({'result':'CONFIRMED_LOCAL_GATE_WEAKENING','old_baseline':'PASS','new_baseline':'PASS',
                      'old_mutant':old_status,'new_mutant':'PASS','input_case':case[0],'motion':motion,
                      'mutation':'duplicate first displayed facet only at coordinate magnitude >100',
                      'mutant_facets':out.facets,'mutant_vertices_count':len(out.vertices),
                      'limitation':'this establishes one migrated gate lost multiplicity sensitivity; does not claim entire current suite allows this mutation'},indent=2))
finally:
    cv.convex_entrance_block=original;gate.convex_entrance_block=saved
assert hashlib.sha256((ROOT/'src/eab/kernel2d/covers.py').read_bytes()).hexdigest()==before
