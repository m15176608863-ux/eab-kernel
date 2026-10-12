"""Primary reviewer reruns coverage evidence, preserving exit and real stdout.

Old geometry snippets are mostly print-based. They require semantic inspection
of their stdout; return code zero alone is deliberately not labeled a proof.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
indices = [6,25,26,27,28,29,30,33,36,37,39,40,41,42,43]
items = [(f'raw0_{i:02}', f'geometry_g6e_{i:02}.py', 'manual_stdout_semantic_review') for i in indices]
items += [('limit_replay', 'limit_regression.py', 'assertion_checked'),
          ('geometry_stress', 'geometry_stress.py', 'independent_oracle_assertions'),
          ('geometry_union', 'geometry_union.py', 'independent_oracle_assertions'),
          ('geometry_distance', 'geometry_distances.py', 'independent_oracle_assertions'),
          ('geometry_window', 'geometry_window.py', 'independent_oracle_assertions')]
results = []
for name, script_name, kind in items:
    path = ROOT / 'review/repro' / script_name
    started = time.perf_counter()
    run = subprocess.run([sys.executable, '-X', 'utf8', str(path)], cwd=ROOT, env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         encoding='utf-8', errors='strict')
    log = ROOT / 'review/logs' / f'primary_coverage_{name}.txt'
    log.write_text(run.stdout, encoding='utf-8')
    results.append({'name': name, 'script': path.relative_to(ROOT).as_posix(),
                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'verification_kind': kind, 'exit_code': run.returncode,
                    'seconds': round(time.perf_counter()-started, 3),
                    'log': log.relative_to(ROOT).as_posix(), 'stdout': run.stdout})
    print(name, 'exit=', run.returncode, flush=True)
    assert run.returncode == 0, (name, run.stdout)
(ROOT/'review/evidence/primary_coverage_replay.json').write_text(
    json.dumps({'raw_indices_zero_based': indices,
                'limit_raw_indices_one_based': [2,9,10,11,20,21,22,23,45,47],
                'distinct_old_findings': 25,
                'warning': 'Geometry old snippets need manual stdout inspection, not just exit zero.',
                'results': results}, ensure_ascii=False, indent=2), encoding='utf-8')
print('PRIMARY_COVERAGE_RERUN_DONE 25 distinct legacy cases plus independent geometry families')
