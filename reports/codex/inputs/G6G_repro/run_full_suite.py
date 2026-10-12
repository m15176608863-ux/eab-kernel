import os, sys, json, hashlib, subprocess, time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / 'review'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'
tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf8').split('\0')
baseline = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked if p}
(REVIEW/'baseline_hashes.json').write_text(json.dumps(baseline, indent=2), encoding='utf8')
head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
cmd=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider','tests','--basetemp='+str(REVIEW/'tmp_full_suite')]
meta={'command':subprocess.list2cmdline(cmd),'head':head,'started_utc':datetime.now(timezone.utc).isoformat()}
(REVIEW/'logs'/'full_suite.json').write_text(json.dumps(meta, indent=2),encoding='utf8')
t=time.monotonic()
with (REVIEW/'logs'/'full_suite.log').open('w',encoding='utf8',newline='') as f:
    result=subprocess.run(cmd,cwd=ROOT,env=os.environ,stdout=f,stderr=subprocess.STDOUT)
meta.update(exit_code=result.returncode,elapsed_seconds=time.monotonic()-t,finished_utc=datetime.now(timezone.utc).isoformat())
meta['tracked_sha256_changed']=[p for p,h in baseline.items() if not (ROOT/p).exists() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
meta['summary']='\n'.join((REVIEW/'logs'/'full_suite.log').read_text(encoding='utf8').splitlines()[-3:])
(REVIEW/'logs'/'full_suite.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
print(json.dumps(meta,indent=2),flush=True)
