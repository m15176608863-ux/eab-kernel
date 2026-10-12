"""Read-only git history, process-local internal mutations, reproducible gate comparison."""
from pathlib import Path
import ast, hashlib, inspect, json, subprocess, sys, traceback
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'tools')]
import pytest
import test_r8fix_gate_teeth as R
import test_invariance_geom as T
from eab.kernel3d import geom3 as G, g03, covers3 as C
import eab.margin as M
OUT=Path(__file__).resolve().parent
rows=[]

def historical(file,name,module):
    text=subprocess.check_output(['git','show','b6126cf:'+file],cwd=ROOT).decode('utf-8-sig')
    node=next(n for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
    source=ast.get_source_segment(text,node)
    scope=dict(vars(module));scope.update(polyhedra_overlap=G.polyhedra_overlap,brute_feature_distance=G.brute_feature_distance)
    exec(compile(source,'b6126cf:'+file,'exec'),scope)
    return scope[name],source

def outcome(fn,args=()):
    try:
        value=fn(*args)
        if hasattr(value,'passed'):
            return {'result':'PASS' if value.passed else 'REJECT','samples':value.samples,'failures':str(value.failures)}
        return {'result':'PASS'}
    except Exception as e:
        stack=traceback.extract_tb(e.__traceback__)
        return {'result':type(e).__name__,'message':str(e),'assertion':str(stack[-1])}

def compare(family,name,args,fault):
    old,source=historical('tests/test_invariance_geom.py',name,T)
    new=getattr(T,name)
    row={'family':family,'gate':name,'args':args,'fault':fault,'old_sha256':hashlib.sha256(source.encode()).hexdigest()}
    row['baseline']={'old':outcome(old,args),'new':outcome(new,args)}
    with pytest.MonkeyPatch.context() as patch:
        R.convex_view_mutant(patch,fault)
        row['mutant']={'old':outcome(old,args),'new':outcome(new,args)}
    rows.append(row)

for fault,names in [('drop_vertex',['tetra_box_vv','generic']),('source_faces',['tetra_box_vv','generic','ve3_wedge'])]:
    for name in names:compare('G6H-05','test_cover_labels_and_strictness_are_invariant',(name,0,1000.,1.),fault)
for gate,args in [('test_support_gaps_scale_and_membership_is_invariant',('generic',0,1000.,1.)),
                  ('test_g0_three_votes_are_invariant',('generic',0,1000.,1.)),
                  ('test_vote_two_ambiguity_band_is_pinned_on_the_generic_cells',(1e5,0,0,39))]:
    for fault in ('drop_vertex','source_faces'):compare('same-family convex oracle',gate,args,fault)
old,_=historical('src/eab/kernel3d/g03.py','g0_distance_completeness3',g03)
for t in (0.,1e3,1e8):
    a,b,q=R.interval_union_pair(t)
    def run(fn):return fn(a,b,radius=0,samples=1,tol=0,atol=0)
    row={'family':'G6H-06','translation':t,'baseline':{'old':outcome(lambda:run(old)),'new':outcome(lambda:run(g03.g0_distance_completeness3))}}
    with pytest.MonkeyPatch.context() as patch:
        R.reject_z_inside_cone_filter(patch)
        row['mutant']={'old':outcome(lambda:run(old)),'new':outcome(lambda:run(g03.g0_distance_completeness3))}
    rows.append(row)
# Other documented migrations: use the actual active predicate inside the kernel,
# but compare the unchanged historical/current assertion bodies against its output.
import test_g2_bdda3d as G2
old,_=historical('tests/test_g2_bdda3d.py','_assert_g2_gate',G2)
for name in ('_qvertex_contains','_qedge_contains'):
    for case in G2.CASES:
        baseline=G2.compare(case)
        row={'family':'migrated G2 active predicate','gate':str(case),'fault':name+' returns boundary',
             'baseline':{'old':outcome(old,(baseline,)),'new':outcome(G2._assert_g2_gate,(baseline,))}}
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(C,name,lambda *a,**k:0)
            result=G2.compare(case)
            row['mutant']={'old':outcome(old,(result,)),'new':outcome(G2._assert_g2_gate,(result,))}
        rows.append(row)
import test_kernel3d_covers as K
old,_=historical('tests/test_kernel3d_covers.py','_position_independence_violations',K)
for fault in ('absolute edge','missing displacement'):
    a,b=K._canon_pairs()['generic' if fault=='absolute edge' else 'tetra_box_A3']
    def gate(fn):
        violations=fn(a,b)
        assert not violations,violations[:2]
    row={'family':'migrated position-independence','fault':fault,'baseline':{'old':outcome(lambda:gate(old)),'new':outcome(lambda:gate(K._position_independence_violations))}}
    with pytest.MonkeyPatch.context() as patch:
        if fault=='absolute edge':patch.setattr(C,'_qedge',lambda body,e:C._qvector(body.verts[e[1]]))
        else:
            orig=C.facet_gap3
            patch.setattr(C,'facet_gap3',lambda a,b,label,x:orig(a,b,label,(0.,0.,0.) if label[0]=='VF' else x))
        C._local_facets_cached.cache_clear();C._support_planes_cached.cache_clear()
        row['mutant']={'old':outcome(lambda:gate(old)),'new':outcome(lambda:gate(K._position_independence_violations))}
    C._local_facets_cached.cache_clear();C._support_planes_cached.cache_clear()
    rows.append(row)
(OUT/'old_gate_comparison.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
for row in rows:
    print(row['family'],row.get('gate',row.get('translation',row.get('fault'))),
          'baseline',tuple(r['result'] for r in row['baseline'].values()),
          'mutant',tuple(r['result'] for r in row['mutant'].values()))
assert all(row['baseline']['new']['result']=='PASS' for row in rows)
assert all(row['mutant']['new']['result'] not in ('PASS',) for row in rows)
assert not any(row['baseline']['old']['result']=='PASS' and row['mutant']['old']['result']!='PASS'
               and row['mutant']['new']['result']=='PASS' for row in rows)
