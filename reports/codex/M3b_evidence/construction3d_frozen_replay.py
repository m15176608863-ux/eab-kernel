"""Run all 392 escape cases once in an explicit frozen source export.

Records pre/post hashes of every source/test/tool Python file and the replay
driver. No resume or record concatenation is implemented. Stdlib only.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def write(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def snapshot(root, driver):
    paths = {p for folder in ('src', 'tests', 'tools') for p in (root/folder).rglob('*.py')}
    paths.add(driver)
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def main(root, output):
    workspace = Path(__file__).resolve().parents[3]
    root, output = root.resolve(), output.resolve()
    assert workspace in root.parents and workspace in output.parents, 'both paths must remain in this worktree'
    driver = root/'reports/codex/M3_evidence/three_d_scan.py'
    evidence = output.parent
    temporary = workspace/'reports/codex/M3b_evidence/tmp/construction3d/frozen_replay'
    temporary.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', TEMP=str(temporary), TMP=str(temporary))
    command = [sys.executable, '-X', 'utf8', str(driver), 'replay', '--root', str(root), '--output', str(output)]
    before = snapshot(root, driver)
    attestation = {'complete': False, 'started_utc': datetime.now(timezone.utc).isoformat(),
                   'invocations': 1, 'resume_or_splice': False, 'command': command,
                   'cwd': str(root), 'TEMP': str(temporary), 'TMP': str(temporary),
                   'source_file_count': len(before), 'before_sha256': before}
    metadata = evidence/'construction3d_frozen_replay_attestation.json'
    write(metadata, attestation)
    start = time.perf_counter()
    with (evidence/'construction3d_frozen_replay.log').open('w', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    after = snapshot(root, driver)
    attestation.update(ended_utc=datetime.now(timezone.utc).isoformat(),
                       seconds=time.perf_counter()-start, exit_code=result.returncode,
                       after_sha256=after, source_unchanged=before == after)
    if result.returncode == 0 and before == after:
        payload = json.loads(output.read_text(encoding='utf-8'))
        attestation['complete'] = (payload['complete'] is True and payload['count'] == len(payload['rows']) == 392
                                   and payload['brute_calls'] == 0)
        attestation['output_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
    write(metadata, attestation)
    assert attestation['complete'], 'frozen full replay did not complete with stable source and zero brute calls'
    print(json.dumps({key: attestation[key] for key in ('complete', 'invocations', 'source_file_count', 'source_unchanged', 'seconds')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    main(args.root, args.output)
