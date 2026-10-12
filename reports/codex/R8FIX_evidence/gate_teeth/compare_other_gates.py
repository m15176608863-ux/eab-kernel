from pathlib import Path
import ast,hashlib,inspect,json,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'tools')]
import pytest
import test_r8fix_gate_teeth as R
import test_covers3_g0_vote2 as V
import test_frozen_ee_sign as F
OUT=Path(__file__).resolve().parent
rows=[]
def get(commit,file,name,module):
 result=subprocess.run(['git','show',commit+':'+file],cwd=ROOT,capture_output=True)
 if result.returncode:return None,{'unavailable':result.stderr.decode('utf-8','replace')}
 text=result.stdout.decode('utf-8-sig');node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
 source=ast.get_source_segment(text,node);scope=dict(vars(module));exec(compile(source,commit+':'+file,'exec'),scope)
 return scope[name],{'sha256':hashlib.sha256(source.encode()).hexdigest()}
def outcome(fn,args):
 if fn is None:return {'result':'UNAVAILABLE'}
 try:fn(*args);return {'result':'PASS'}
 except Exception as exc:
  return {'result':type(exc).__name__,'message':str(exc),'assertion':str(traceback.extract_tb(exc.__traceback__)[-1])}
for module,file,name,args,fault in [
 (V,'tests/test_covers3_g0_vote2.py','test_yawed_stack_passes_g0_under_random_rotations',(1e-3,1),'permute_canonical'),
 (F,'tests/test_frozen_ee_sign.py','test_frozen_ee_orientation_agrees_with_ee_cover_and_facet_normal3_on_every_ee_pair',(1e-3,4,1e3),'drop_all')]:
 old,meta=get('HEAD',file,name,module);historical,hmeta=get('b6126cf',file,name,module);new=getattr(module,name)
 row={'gate':name,'args':args,'fault':fault,'HEAD_metadata':meta,'b6126cf_metadata':hmeta,
      'baseline':{'HEAD':outcome(old,args),'b6126cf':outcome(historical,args),'new':outcome(new,args)}}
 with pytest.MonkeyPatch.context() as patch:
  R.all_branch_convex_view_mutant(patch,fault)
  row['mutant']={'HEAD':outcome(old,args),'b6126cf':outcome(historical,args),'new':outcome(new,args)}
 rows.append(row)
assert all(r['baseline']['HEAD']['result']==r['baseline']['new']['result']=='PASS' for r in rows)
assert all(r['mutant']['HEAD']['result']=='PASS' and r['mutant']['new']['result']=='AssertionError' for r in rows)
(OUT/'other_gate_comparison.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
for r in rows:print(r['gate'],{k:v['result'] for k,v in r['baseline'].items()},{k:v['result'] for k,v in r['mutant'].items()})
