"""Record the exact requested full-suite command, UTF-8 log, elapsed time and source hashes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8',
           TEMP=str(HERE / 'tmp'), TMP=str(HERE / 'tmp'), GIT_OPTIONAL_LOCKS='0')
command = [sys.executable, '-X', 'utf8', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests']
paths = [p for base in ('src', 'tests') for p in (ROOT / base).rglob('*.py')]
snapshot = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
start = time.perf_counter()
with (HERE / 'final_full.log').open('wb') as log:
    result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
elapsed = time.perf_counter() - start
changed = [name for name, digest in snapshot.items() if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest]
lines = (HERE / 'final_full.log').read_text(encoding='utf-8').splitlines()
record = dict(command='python -X utf8 -m pytest -q -p no:cacheprovider tests',
              returncode=result.returncode, wall_seconds=elapsed, last_line=lines[-1],
              source_changed_during_run=changed, source_sha256=snapshot)
(HERE / 'final_full_result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(record['last_line'])
print('wall_seconds=', elapsed, 'source_changed_during_run=', changed)
sys.exit(result.returncode or bool(changed))
