"""Rerunnable final verification with bytecode disabled and scoped temp/cache."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'reports/codex/R7FIX_evidence'
(OUT/'tmp').mkdir(parents=True,exist_ok=True)
command=[sys.executable,'-X','utf8','-u','-m','pytest','-q','-p','no:cacheprovider','--durations=25','-n','4',
         '--basetemp='+str(OUT/'tmp/full_final'), '--junitxml='+str(OUT/'full_suite.junit.xml')]
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
env['PYTHONPATH']=str(OUT/'verification_deps')+os.pathsep+env.get('PYTHONPATH','')
start=datetime.datetime.now(datetime.timezone.utc).isoformat(); t=time.perf_counter()
with (OUT/'full_suite.log').open('w',encoding='utf-8',newline='') as stream:
    result=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
seconds=time.perf_counter()-t
log=(OUT/'full_suite.log').read_text(encoding='utf-8')
meta={'command':command,'cwd':str(ROOT),'env':{k:env[k] for k in ['PYTHONDONTWRITEBYTECODE','PYTHONIOENCODING','PYTHONPATH']},
      'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'elapsed_seconds':seconds,'exit_code':result.returncode,'last_line':log.strip().splitlines()[-1],
      'log_sha256':hashlib.sha256((OUT/'full_suite.log').read_bytes()).hexdigest()}
(OUT/'full_suite.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(meta,ensure_ascii=False,indent=2),flush=True)
raise SystemExit(result.returncode)
