"""Read-only tracked-byte audit; the evidence output is review-local."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
initial = json.loads((ROOT/'review/evidence/initial_tracked_sha256.json').read_text('utf-8-sig'))
names = subprocess.check_output(['git','ls-files','-z'], cwd=ROOT).decode('utf-8').split('\0')[:-1]
final = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}
changed = [name for name in initial.keys() & final.keys() if initial[name] != final[name]]
result = {'checked_utc': datetime.now(timezone.utc).isoformat(),
          'head': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
          'tracked_count': len(final), 'changed': sorted(changed),
          'missing_paths': sorted(initial.keys()-final.keys()),
          'new_tracked_paths': sorted(final.keys()-initial.keys()),
          'git_status_short': subprocess.check_output(['git','status','--short'], cwd=ROOT, text=True).strip(),
          'python': sys.version, 'platform': platform.platform(),
          'initial_sha256': 'review/evidence/initial_tracked_sha256.json',
          'final_sha256': final}
result['tracked_bytes_unchanged'] = not (changed or result['missing_paths'] or result['new_tracked_paths'])
assert result['head'] == '878d4f0a260cc703eab7d883ab574fddc2ec2f3d'
assert result['tracked_bytes_unchanged'], result
(ROOT/'review/evidence/final_integrity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('TRACKED_INTEGRITY_OK', result['tracked_count'], 'files; changed=0; HEAD=878d4f0')
