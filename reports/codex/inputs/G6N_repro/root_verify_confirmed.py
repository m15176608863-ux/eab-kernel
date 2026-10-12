"""Primary reviewer reruns every confirmed unmodified-production counterexample.

The scripts' assertions are the mathematical checks. This driver only preserves
fresh stdout, exit codes and script hashes; a green suite is not its oracle.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
cases = [
    ('N01', 'support_dual_power.py'),
    ('N02_inside', 'root_trig_exact_argument.py'),
    ('N02_outside', 'support_dual_trig_domain.py'),
    ('N03_records', 'root_records_domain.py'),
    ('N03_reader', 'support_json_reader.py'),
    ('N04', 'limit_cone_safety.py'),
    ('N05', 'support_cone_interlock_relative_bound.py'),
]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
results = []
for case, name in cases:
    script = ROOT / 'review/repro' / name
    start = datetime.now(timezone.utc).isoformat()
    run = subprocess.run([sys.executable, '-X', 'utf8', str(script)], cwd=ROOT,
                         env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding='utf-8', errors='strict')
    log = ROOT / 'review/logs' / f'primary_final_{case}.txt'
    log.write_text(run.stdout, encoding='utf-8')
    results.append({'case': case, 'script': script.relative_to(ROOT).as_posix(),
                    'script_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
                    'started_utc': start,
                    'ended_utc': datetime.now(timezone.utc).isoformat(),
                    'exit_code': run.returncode, 'log': log.relative_to(ROOT).as_posix(),
                    'verified_output': run.stdout})
    print(f'{case}: exit={run.returncode}; {log.relative_to(ROOT).as_posix()}', flush=True)
    assert run.returncode == 0, (case, run.stdout)
(ROOT / 'review/evidence/primary_confirmation.json').write_text(
    json.dumps({'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
               cwd=ROOT, text=True).strip(), 'results': results,
               'all_reproduced': all(r['exit_code'] == 0 for r in results)},
               ensure_ascii=False, indent=2), encoding='utf-8')
print('PRIMARY_CONFIRMED: all 5 findings personally reproduced; 7 entry-path scripts')
