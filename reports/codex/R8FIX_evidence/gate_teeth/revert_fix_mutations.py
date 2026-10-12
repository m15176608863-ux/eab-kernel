from pathlib import Path
import ast,hashlib,inspect,json,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'tools')]
import pytest
import test_r8fix_gate_teeth as R
import test_invariance_geom as T
from eab.kernel3d import g03
import eab.margin as M
OUT=Path(__file__).resolve().parent
rows=[]
files=['tests/test_invariance_geom.py','src/eab/kernel3d/g03.py','src/eab/margin.py']
before={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
def observe(id,fn):
    try:fn();result={'result':'UNCAUGHT'}
    except BaseException as exc:
        result={'result':type(exc).__name__,'message':str(exc),'traceback':''.join(traceback.format_exception(exc))}
    rows.append({'id':id,**result})
with pytest.MonkeyPatch.context() as patch:
    source=subprocess.check_output(['git','show','HEAD:tests/test_invariance_geom.py'],cwd=ROOT).decode('utf-8-sig')
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='test_cover_labels_and_strictness_are_invariant')
    scope=dict(vars(T));exec(compile(ast.get_source_segment(source,node),'HEAD:test_invariance_geom.py','exec'),scope)
    patch.setattr(T,node.name,scope[node.name])
    observe('G6H-05 restore shared tested convex-view oracle',lambda:R.test_g6h05_migrated_facet_gate_rejects_internal_convex_view_fault(patch,'drop_vertex','generic'))
with pytest.MonkeyPatch.context() as patch:
    source=inspect.getsource(g03.g0_distance_completeness3)
    assert source.count('incomplete = minimum2 != truth2')==1
    scope=dict(vars(g03));exec(compile(source.replace('incomplete = minimum2 != truth2','incomplete = False'),'<g0 exact vote omitted>','exec'),scope)
    patch.setattr(g03,'g0_distance_completeness3',scope['g0_distance_completeness3'])
    observe('G6H-06 omit G0 exact-completeness vote',lambda:R.test_g6h06_g0_detects_internal_missing_cover_without_coordinate_floor(patch,1e8,1))
with pytest.MonkeyPatch.context() as patch:
    source=inspect.getsource(M._resolve)
    assert source.count('minimum2 != truth2 or ')==1
    scope=dict(vars(M));exec(compile(source.replace('minimum2 != truth2 or ',''),'<margin exact vote omitted>','exec'),scope)
    patch.setattr(M,'_resolve',scope['_resolve'])
    observe('G6H-06 omit margin exact-completeness vote',lambda:R.test_g6h06_margin_detects_internal_missing_cover_without_coordinate_floor(patch,1e8,1))
after={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
assert before==after
assert all(row['result'] in ('AssertionError','Failed') for row in rows),rows
(OUT/'revert_fix_mutations.json').write_text(json.dumps({'rows':rows,'tracked_sha_before':before,'tracked_sha_after':after},ensure_ascii=False,indent=2),encoding='utf-8')
for row in rows:print(row['id'],row['result'],row['message'])
