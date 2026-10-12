"""Full collection on four workers; record immutable tested inputs and raw log."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
name = sys.argv[1] if len(sys.argv) > 1 else 'full_suite'
assert name.replace('_', '').isalnum()
(OUT/'tmp').mkdir(parents=True, exist_ok=True)
deps = ROOT/'reports/codex/R7FIX_evidence/verification_deps'
assert (deps/'xdist').is_dir(), 'Use the existing workspace-local verification dependencies'
files = sorted({p for folder in ('src', 'tests', 'tools', 'docs', 'fixtures')
                for p in (ROOT/folder).rglob('*') if p.is_file()
                and '__pycache__' not in p.parts}) + [ROOT/'README.md', ROOT/'AGENTS.md', ROOT/'pyproject.toml']
snapshot = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(OUT/(name+'_snapshot.json')).write_text(json.dumps(snapshot, indent=2), encoding='utf-8')
command = [sys.executable, '-X', 'utf8', '-u', '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
           '-p','r8fix_live_failures',
           '--durations=25', '-n', '4', '--basetemp='+str(OUT/'tmp'/name),
           '--junitxml='+str(OUT/(name+'.junit.xml'))]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
env['PYTHONPATH'] = str(deps)+os.pathsep+str(OUT)+os.pathsep+env.get('PYTHONPATH', '')
env['R8FIX_LIVE_FAILURES'] = str(OUT/(name+'_failures.jsonl'))
Path(env['R8FIX_LIVE_FAILURES']).write_text('',encoding='utf-8')
start = datetime.datetime.now(datetime.timezone.utc).isoformat()
t = time.perf_counter()
with (OUT/(name+'.log')).open('wb') as stream:
    result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
seconds = time.perf_counter()-t
log = (OUT/(name+'.log')).read_bytes()
drift = [f for f, digest in snapshot.items() if not (ROOT/f).is_file()
         or hashlib.sha256((ROOT/f).read_bytes()).hexdigest() != digest]
metadata = dict(command=command, cwd=str(ROOT), start_utc=start,
                end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                env={k:env[k] for k in ('PYTHONPATH','PYTHONDONTWRITEBYTECODE','PYTHONIOENCODING')},
                elapsed_seconds=seconds, exit_code=result.returncode,
                last_line=log.decode('utf-8', errors='replace').strip().splitlines()[-1],
                log_sha256=hashlib.sha256(log).hexdigest(), tested_file_drift=drift)
(OUT/(name+'.json')).write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(metadata, ensure_ascii=False, indent=2))
raise SystemExit(result.returncode or bool(drift))
