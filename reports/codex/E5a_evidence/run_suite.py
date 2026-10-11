"""UTF-8, no-bytecode, workspace-scoped reproducible pytest evidence runner."""
import glob
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
label=sys.argv[1]
assert label.replace('_','').isalnum(),label
args=[]
for arg in sys.argv[2:]:
    args.extend(glob.glob(arg) if '*' in arg else [arg])
args=args or ['tests']
env=os.environ.copy()
env['PYTHONDONTWRITEBYTECODE']='1'
env['PYTHONIOENCODING']='utf-8'
env['TEMP']=env['TMP']=str(OUT/'tmp')
cmd=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider',*args,
     f'--basetemp={OUT/"tmp"/(label+"_pytest")}',
     '--tb=short','--durations=20',f'--junitxml={OUT/label}.xml']
def state():
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ['src','tests','tools'] for p in (ROOT/folder).rglob('*.py')}
before=state();start=time.perf_counter()
with (OUT/f'{label}.log').open('wb') as log:
    run=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
elapsed=time.perf_counter()-start
after=state();lines=(OUT/f'{label}.log').read_text(encoding='utf-8',errors='replace').splitlines()
record=dict(command=cmd,returncode=run.returncode,wall_seconds=elapsed,
            last_line=next((s for s in reversed(lines) if s.strip()),''),
            changed_during_run=[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)],
            source_test_sha256=after)
(OUT/f'{label}.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print('\n'.join(lines[-45:]))
print(f'wall_seconds={elapsed:.3f}; source_drift={record["changed_during_run"]}')
sys.exit(run.returncode)
