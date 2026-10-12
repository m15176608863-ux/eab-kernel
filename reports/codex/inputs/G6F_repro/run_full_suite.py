import os, sys, subprocess, json, time, pathlib, hashlib
root=pathlib.Path.cwd(); review=root/'review'
baseline=json.loads((review/'baseline_hashes.json').read_text(encoding='utf-8'))
changed=[p for p,h in baseline.items() if not (root/p).is_file() or hashlib.sha256((root/p).read_bytes()).hexdigest()!=h]
assert not changed, changed
start=time.time(); cmd=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider','tests','--basetemp='+str(review/'tmp_full_suite_resume')]
env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
with (review/'logs/full_suite_resume.log').open('w',encoding='utf-8',newline='') as f:
 f.write('COMMAND: '+subprocess.list2cmdline(cmd)+'\n'); f.flush()
 p=subprocess.run(cmd,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT)
elapsed=time.time()-start
result=dict(command=subprocess.list2cmdline(cmd),exit_code=p.returncode,elapsed_seconds=elapsed,head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),tracked_baseline_unchanged_at_start=not changed)
(review/'notes/full_suite_resume.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False)); print((review/'logs/full_suite_resume.log').read_text(encoding='utf-8')[-1600:])
