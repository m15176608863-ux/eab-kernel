from pathlib import Path
import zipfile,io,subprocess,json,os,sys,hashlib,ast
ROOT=Path(__file__).resolve().parents[2]; COPY=ROOT/'review/copies/docs_oracle_canonical'
COPY.mkdir(parents=True,exist_ok=True)
data=subprocess.check_output(['git','archive','--format=zip','HEAD','src','tests','tools/osteomorphic.py','pyproject.toml'],cwd=ROOT)
zipfile.ZipFile(io.BytesIO(data)).extractall(COPY)
old=subprocess.check_output(['git','show','b6126cf:tests/test_invariance_geom.py'],cwd=ROOT).decode('utf-8')
a=ast.parse(old);node=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='test_cover_labels_and_strictness_are_invariant')
oldfunc=ast.get_source_segment(old,node).replace('def test_cover_labels_and_strictness_are_invariant(','def old_gate(')
(COPY/'old_gate.py').write_text(oldfunc,encoding='utf-8')
runner="""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path[:0]=[str(R/'src'),str(R/'tests'),str(R/'tools')]
import test_invariance_geom as T
scope=dict(vars(T));exec((R/'old_gate.py').read_text(encoding='utf-8'),scope)
rows=[]
for name in ['tetra_box_vv','generic','ve3_wedge']:
 args=(name,0,1000.,1.)
 try:T.test_cover_labels_and_strictness_are_invariant(*args);new='PASS'
 except Exception as e:new=f'{type(e).__name__}: {e}'
 try:scope['old_gate'](*args);old='PASS'
 except Exception as e:old=f'{type(e).__name__}: {e}'
 rows.append({'args':args,'new_gate':new,'old_gate':old})
print(json.dumps(rows,ensure_ascii=False,indent=2))
"""
(COPY/'audit_runner.py').write_text(runner,encoding='utf-8')
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'}
cmd=[sys.executable,'-X','utf8',str(COPY/'audit_runner.py')]
baseline=subprocess.run(cmd,cwd=COPY,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
print('BASELINE',baseline.stdout,baseline.stderr)
p=COPY/'src/eab/kernel3d/geom3.py'; raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();source=raw.decode('utf-8-sig')
anchor='        P._convex_view = P\n        return P\n    order ='
replacement='''        P._convex_view = P
        if max(abs(x) for v in P.verts for x in v) > 100:
            bad = Polyhedron(list(P.verts), list(P.faces[1:])+list(P.faces[:1]))
            bad._sync_geometry_cache()
            bad._convex_view = bad
            P._convex_view = (tuple(bad.verts), tuple(bad.faces), bad.source_vertices, bad.source_faces)
            return bad
        return P
    order ='''
assert source.count(anchor)==1
p.write_text(source.replace(anchor,replacement),encoding='utf-8',newline='')
mutant=subprocess.run(cmd,cwd=COPY,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
p.write_bytes(raw);assert hashlib.sha256(p.read_bytes()).hexdigest()==h
assert baseline.returncode == mutant.returncode == 0
assert all(r['new_gate']=='PASS' and r['old_gate']=='PASS' for r in json.loads(baseline.stdout))
assert all(r['new_gate'].startswith('AssertionError:') and r['old_gate'].startswith('AssertionError:') for r in json.loads(mutant.stdout))
print('MUTANT',mutant.stdout,mutant.stderr)
result={'baseline':baseline.stdout+baseline.stderr,'mutant':mutant.stdout+mutant.stderr,'copy':str(COPY),'mutation':'only preserve-numbering exact_convex_view branch; cyclic face permutation after finite translation; geometry unchanged','sha256_before_restored':h}
(ROOT/'review/agents/docs_gates/canonical_oracle_mutation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'review/logs/docs_canonical_oracle_mutation.log').write_text('BASELINE\n'+result['baseline']+'\nMUTANT\n'+result['mutant'],encoding='utf-8')
