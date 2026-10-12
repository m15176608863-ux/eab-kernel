from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[2]
name=sys.argv[1]
assert name.replace('_','').replace('-','').isalnum()
command=sys.argv[2:]
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
env['PYTHONPATH']=str(ROOT/'src')+os.pathsep+str(ROOT/'tests')+os.pathsep+env.get('PYTHONPATH','')
t=time.perf_counter(); start=datetime.datetime.now(datetime.timezone.utc).isoformat()
r=subprocess.run(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
out=ROOT/'review/logs';out.mkdir(exist_ok=True)
(out/(name+'.log')).write_bytes(r.stdout)
metadata=dict(command=command,exit_code=r.returncode,start_utc=start,seconds=time.perf_counter()-t,log_sha256=hashlib.sha256(r.stdout).hexdigest())
(out/(name+'.json')).write_text(json.dumps(metadata,indent=2),encoding='utf-8')
print(json.dumps(metadata));print(r.stdout.decode('utf-8',errors='replace'))
raise SystemExit(r.returncode)
