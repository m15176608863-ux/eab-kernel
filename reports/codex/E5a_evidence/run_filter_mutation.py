"""Run a source-level filter mutant in an isolated package, never in the worktree."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent
TMP = EVIDENCE / 'tmp' / 'filter_mutant'
PACKAGE = TMP / 'eab'
PACKAGE.mkdir(parents=True, exist_ok=True)
(PACKAGE / '__init__.py').write_text('', encoding='utf-8')
SOURCE = ROOT / 'src/eab/predicates.py'
before = SOURCE.read_bytes()
old = '_O3D_ERR = (7.0 + 56.0 * _U) * _U'
new = '_O3D_ERR = ((7.0 + 56.0 * _U) * _U) / 10.0'
text = before.decode('utf-8')
assert text.count(old) == 1
(PACKAGE / 'predicates.py').write_text(text.replace(old, new), encoding='utf-8')
cmd = [sys.executable, '-X', 'utf8', '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
       '-o', f'pythonpath={TMP.as_posix()}',
       f'--basetemp={TMP / "pytest"}',
       'tests/test_filtered_predicates.py::test_orient3d_filter_vs_fraction_shrunken_bound_witness',
       f'--junitxml={EVIDENCE / "filters_mutation.xml"}']
env = os.environ.copy()
env['PYTHONDONTWRITEBYTECODE'] = '1'
env['TEMP'] = env['TMP'] = str(EVIDENCE / 'tmp')
run = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
(EVIDENCE / 'filters_mutation.log').write_text(run.stdout + run.stderr, encoding='utf-8')
assert SOURCE.read_bytes() == before, 'the live source must never be changed'
record = dict(id='F01', mutation='orient3d float filter bound divided by ten',
              command=cmd, returncode=run.returncode,
              expected_assertion='assert -1 == 1',
              killed=run.returncode == 1 and 'assert -1 == 1' in run.stdout,
              source_sha256=hashlib.sha256(before).hexdigest(),
              mutant_sha256=hashlib.sha256((PACKAGE / 'predicates.py').read_bytes()).hexdigest(),
              source_unchanged=True, isolated_package=str(PACKAGE))
(EVIDENCE / 'filters_mutation.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(run.stdout)
assert record['killed'], record
