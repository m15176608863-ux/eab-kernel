"""WO-G6O lens4 selected old/new assertion bodies and real in-memory faults.

Old assertion bodies are read from the root migration inventory and verified
against git show b6126cf (read-only). They execute against CURRENT helpers/SUT;
this is deliberately not mislabelled an archival whole-suite execution.
Mutants modify actual production function internals, not emitted test data.
"""
from pathlib import Path
import ast,sys,json,subprocess,inspect,traceback,linecache
from contextlib import contextmanager
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'tools')]
import test_invariance_2d as t2
import test_invariance_interlock as ti
import test_kernel2d_review as tr
import test_near_parallel_edges as tn
from eab.kernel2d import covers as C
from eab.kernel3d import interlock as I

NAMES=[('tests/test_invariance_2d.py','test_cover_enumeration_is_invariant'),('tests/test_invariance_2d.py','test_convex_g0_is_invariant'),('tests/test_kernel2d_review.py','test_hull_defect_threshold_is_pinned_on_an_edge_away_from_the_start'),('tests/test_invariance_interlock.py','test_brute_oracle_is_exact_zero_at_rest_and_scales'),('tests/test_near_parallel_edges.py','test_near_parallel_ridge_edges_match_the_exact_rational_distance')]
inventory=json.loads((ROOT/'review/evidence/test_migration_inventory.json').read_text(encoding='utf-8'))
diff=(ROOT/'review/evidence/tests_diff_b6126cf.txt').read_text(encoding='utf-8')
rows=[]
def node_source(source,name):
    nodes=[n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name==name]
    assert len(nodes)==1;node=nodes[0]
    return node,ast.get_source_segment(source,node)
for file,name in NAMES:
    rec=next(x for x in inventory if x['file']==file and x['function']==name)
    old=subprocess.check_output(['git','show','b6126cf:'+file],cwd=ROOT).decode('utf-8-sig')
    new=(ROOT/file).read_text(encoding='utf-8-sig')
    on,os=node_source(old,name);nn,ns=node_source(new,name)
    assert os==rec['old']['source'];assert ns==rec['new']['source']
    hits=[i for i,line in enumerate(diff.splitlines()) if 'def '+name+'(' in line]
    rows.append({'file':file,'function':name,'old_span':[on.lineno,on.end_lineno],'new_span':[nn.lineno,nn.end_lineno],'old_assertions':[{'line':x.lineno,'text':ast.get_source_segment(old,x)} for x in ast.walk(on) if isinstance(x,ast.Assert)],'new_assertions':[{'line':x.lineno,'text':ast.get_source_segment(new,x)} for x in ast.walk(nn) if isinstance(x,ast.Assert)],'old_source':os,'new_source':ns,'diff_match_lines_1based':[i+1 for i in hits],'removed_assertion_count':len(rec.get('removed_assertion_asts',[]))})
(ROOT/'review/evidence/geometry_migration_assertions.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')

def old_body(module,name):
    row=next(r for r in rows if r['function']==name);ns=dict(vars(module));filename='old:'+row['file']+'@b6126cf';linecache.cache[filename]=(len(row['old_source']),None,row['old_source'].splitlines(True),filename);exec(compile(row['old_source'],filename,'exec'),ns);return ns[name]
def mutant(module,function,before,after):
    source=inspect.getsource(getattr(module,function));assert source.count(before)==1
    ns=dict(vars(module));exec(compile(source.replace(before,after),'mutant:'+module.__name__+'::'+function,'exec'),ns);return ns[function]
@contextmanager
def patched(changes):
    originals=[(module,name,getattr(module,name)) for module,name,fn in changes]
    try:
        for module,name,fn in changes:setattr(module,name,fn)
        yield
    finally:
        for module,name,fn in originals:setattr(module,name,fn)
def invoke(fn,args):
    try:fn(*args);return {'status':'PASS'}
    except Exception as e:
        tb=traceback.extract_tb(e.__traceback__)[-1]
        return {'status':'FAIL','exception':type(e).__name__,'message':str(e),'assert_file':tb.filename,'assert_line':tb.lineno,'assert_text':tb.line}

case=next(x for x in t2.COVER_CASES if x[0]=='star_pair_generic');motion=next(m for m in t2.MOTIONS if m[2:]==(1.0,0.0))
selected=[(t2,'test_cover_enumeration_is_invariant',(case,motion)),(t2,'test_convex_g0_is_invariant',(t2.CONVEX_CASES[0],motion)),(tr,'test_hull_defect_threshold_is_pinned_on_an_edge_away_from_the_start',(0.5,)),(ti,'test_brute_oracle_is_exact_zero_at_rest_and_scales',('z0.7',1e5,1.0)),(tn,'test_near_parallel_ridge_edges_match_the_exact_rational_distance',(1e-9,1e-6,.3,3))]
baseline=[]
for module,name,args in selected:
    baseline.append({'function':name,'parameters':str(args[:1]) if name!='test_cover_enumeration_is_invariant' else 'star_pair_generic; s=1,t=0,nonaxis rotation','new':invoke(getattr(module,name),args)})

experiments=[]
fault=mutant(C,'_ve_side_directions','return 1 if c1 > 0 and c2 > 0 else 0','return 0 if c1 > 0 and c2 > 0 else 0')
with patched([(C,'_ve_side_directions',fault)]):
    experiments.append({'mutation':'VE/EV exact strict cone survivor is incorrectly labelled boundary inside _ve_side_directions','old_assertion_body_on_current_helpers':invoke(old_body(t2,'test_cover_enumeration_is_invariant'),(case,motion)),'new_assertion_body':invoke(t2.test_cover_enumeration_is_invariant,(case,motion))})

fault=mutant(C,'membership_convex','s = entrance_membership_exact(A, B, x)','s = entrance_membership_exact(A, B, x)\n    if s == 0: return -1')
with patched([(C,'membership_convex',fault)]):
    experiments.append({'mutation':'Nonconvex exact boundary is misclassified exterior in live membership_convex branch','new_assertion_body':invoke(tr.test_hull_defect_threshold_is_pinned_on_an_edge_away_from_the_start,(0.5,))})

fault=mutant(I,'escape_height_covers','root,event,proof,state,events,name=min(solved,key=lambda row:row[0])','root,event,proof,state,events,name=min(solved,key=lambda row:row[0])\n    if 0 < root < F(1,10**8): root=F(0)')
with patched([(I,'escape_height_covers',fault),(ti,'escape_height_covers',fault)]):
    experiments.append({'mutation':'Real tiny positive exact escape roots below 1e-8 are clipped to zero inside public solver','old_assertion_body_on_current_helpers':invoke(old_body(ti,'test_brute_oracle_is_exact_zero_at_rest_and_scales'),('z0.7',1e5,1.0)),'new_assertion_body':invoke(ti.test_brute_oracle_is_exact_zero_at_rest_and_scales,('z0.7',1e5,1.0))})

result={'head':'03a41b5','scope':'Five selected migration functions, same current helpers with frozen old/new assertion bodies. Not all 157 functions and not old full-suite runtime.','baseline_current_selected':baseline,'real_internal_mutations':experiments,'old_catches_new_escapes_found':False,'production_functions_restored':True}
(ROOT/'review/evidence/geometry_migration_probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
assert all(x['new']['status']=='PASS' for x in baseline)
assert all(x['new_assertion_body']['status']=='FAIL' and x['new_assertion_body']['exception']=='AssertionError' for x in experiments)
