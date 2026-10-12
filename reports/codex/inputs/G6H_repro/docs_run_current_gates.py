from pathlib import Path
import os,sys,json,subprocess,time
ROOT=Path(__file__).resolve().parents[2]
nodes=['tests/test_r7fix_docs.py','tests/test_perf_contact_window.py','tests/test_r7fix_margin_oracle.py','tests/test_margin_penetration.py','tests/test_interlock_e5a.py','tests/test_r6fix_frozen_construction.py','tests/test_doc_pointers.py']
cmd=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider','--basetemp='+str(ROOT/'review/agents/docs_gates/tmp/current'),*nodes]
t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'},capture_output=True,text=True,encoding='utf-8',errors='replace');out=p.stdout+p.stderr
(ROOT/'review/logs/docs_current_gates.log').write_text(out,encoding='utf-8');(ROOT/'review/agents/docs_gates/current_gates.json').write_text(json.dumps({'command':cmd,'exit_code':p.returncode,'seconds':time.perf_counter()-t,'verified_output':out},ensure_ascii=False,indent=2),encoding='utf-8');print(out)
