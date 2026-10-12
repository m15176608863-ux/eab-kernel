"""R12FIXb 三道可维护性门的独立内部变异：副本内运行目标门。"""
from pathlib import Path
import hashlib,shutil,subprocess,sys,os,json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review/static_logs'
originals={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('tools/check_exact_construction.py','tools/exact_construction_subset.py','tools/exact_construction_policy.json')}
results=[]
for name,nodeid in (
('pin_hash_ignored','tests/test_r12fixb_maintenance.py::test_reviewed_function_body_change_invalidates_only_its_sites'),
('default_accept_with_policy','tests/test_r12fixb_maintenance.py::test_new_forbidden_function_is_not_admitted_by_existing_local_reviews'),
('global_unrelated_dependency','tests/test_r12fixb_maintenance.py::test_unrelated_source_comment_keeps_real_repository_gate_green')):
 copy=ROOT/'review/copies'/('static_teeth_'+name);copy.mkdir(parents=True,exist_ok=True)
 for folder in ('src','tests','tools'):
  shutil.copytree(ROOT/folder,copy/folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
 p=copy/'tools/exact_construction_subset.py';s=p.read_text(encoding='utf-8')
 if name=='pin_hash_ignored':
  old='contexts.get(fn) != row["context"] or row["node"] not in nodes';assert s.count(old)==1;s=s.replace(old,'row["node"] not in nodes')
  old='and contexts.get(r["function"]) == r["context"]';assert s.count(old)==1;s=s.replace(old,'')
 elif name=='default_accept_with_policy':
  old='if not apply_waivers or key not in waivers:';assert s.count(old)==1;s=s.replace(old,'if not apply_waivers:')
 else:
  # Reintroduce an all-site dependency pin, without modifying or fabricating
  # diagnostics: normal source hashes when dependency intact; all local pins
  # incorporate changed unrelated dependency when its bytes change.
  old='return hashlib.sha256(text.encode("utf-8")).hexdigest()';assert s.count(old)==1;s=s.replace(old,'return hashlib.sha256((text + globals().get("REVIEW_GLOBAL_SALT", "")).encode("utf-8")).hexdigest()')
  checker=copy/'tools/check_exact_construction.py';c=checker.read_text(encoding='utf-8');old='def scan_repository(root=ROOT):\n';assert c.count(old)==1
  digest=hashlib.sha256((copy/'src/eab/__init__.py').read_bytes()).hexdigest()
  injected='def scan_repository(root=ROOT):\n    import hashlib\n    dependency = hashlib.sha256((root / "src/eab/__init__.py").read_bytes()).hexdigest()\n    _subset.REVIEW_GLOBAL_SALT = "" if dependency == '+repr(digest)+' else dependency\n'
  checker.write_text(c.replace(old,injected),encoding='utf-8')
 p.write_text(s,encoding='utf-8')
 temp=copy/'reviewtmp';temp.mkdir(exist_ok=True)
 cmd=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider',nodeid,'--basetemp='+str(temp/'test')]
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
 r=subprocess.run(cmd,cwd=copy,env=env,text=True,encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (OUT/('maintenance_tooth_'+name+'.log')).write_text(r.stdout,encoding='utf-8')
 assert r.returncode==1,(name,r.returncode,r.stdout)
 assert 'FAILED '+nodeid in r.stdout.replace(chr(92),'/'),(name,r.stdout)
 targets={'pin_hash_ignored':'R12FIXb only the edited function\'s sites may expire','default_accept_with_policy':'assert issues and {row[2] for row in issues} == {"new_forbidden"}','global_unrelated_dependency':'R12FIXb unrelated comment must not invalidate any review'}
 assert targets[name] in r.stdout,(name,targets[name],r.stdout)
 results.append({'mutation':name,'nodeid':nodeid,'returncode':r.returncode,'failed_target_assertion':targets[name],'output_log':'review/static_logs/maintenance_tooth_'+name+'.log','last_line':r.stdout.strip().splitlines()[-1]})
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in originals.items())
output={'confirmed_all_three_have_teeth':True,'results':results,'root_hashes_unchanged':originals}
(OUT/'maintenance_teeth.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(output,ensure_ascii=False,indent=2))
