"""Fresh, single-invocation 392 replay with complete producer byte freeze.

The old construction3d_frozen_replay artifacts remain unchanged history.
This wrapper copies all producer src/tests/tools bytes plus the unchanged M3
driver into a new workspace-local directory, then runs that driver exactly
once.  The child records actual imported local files after completion.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import time


WORKSPACE = Path(__file__).resolve().parents[3]
EVIDENCE = WORKSPACE/'reports/codex/M3b_evidence'
PREFIX = 'construction3d_frozen_r4'
DRIVER = 'reports/codex/M3_evidence/three_d_scan.py'


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root):
    paths = {p for folder in ('src', 'tests', 'tools') for p in (root/folder).rglob('*')
             if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    paths.add(root/DRIVER)
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(paths)}


def run_child(root, output):
    # Execute the frozen historical driver unchanged.  No row filtering,
    # checkpoint loading, resume, concatenation or retry is implemented here.
    driver = root/DRIVER
    sys.argv = [str(driver), 'replay', '--root', str(root), '--output', str(output)]
    runpy.run_path(str(driver), run_name='__main__')
    imported = {}
    for name, module in sorted(sys.modules.items()):
        filename = getattr(module, '__file__', None)
        if filename:
            path = Path(filename).resolve()
            if root in path.parents and path.is_file():
                imported[name] = {'path': path.relative_to(root).as_posix(), 'sha256': sha(path)}
    write(EVIDENCE/(PREFIX+'_actual_imports.json'), {
        'complete': True, 'source_root': str(root), 'driver': {'path': DRIVER, 'sha256': sha(driver)},
        'modules': imported, 'module_count': len(imported),
    })


def main(root):
    root = root.resolve()
    assert WORKSPACE in root.parents and not root.exists(), 'fresh root must be absent and inside workspace'
    before_copy = snapshot(WORKSPACE)
    root.mkdir(parents=True)
    for name in before_copy:
        destination = root/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(WORKSPACE/name, destination)
    frozen = snapshot(root)
    assert before_copy == snapshot(WORKSPACE) == frozen, 'producer changed while making byte freeze; invalidate'
    temporary = EVIDENCE/'tmp/construction3d/frozen_r4_replay'
    temporary.mkdir(parents=True, exist_ok=True)
    output = EVIDENCE/(PREFIX+'_replay.json')
    metadata = EVIDENCE/(PREFIX+'_replay_attestation.json')
    assert not output.exists() and not metadata.exists(), 'do not overwrite a prior run or splice output'
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', TEMP=str(temporary), TMP=str(temporary))
    command = [sys.executable, '-X', 'utf8', str(Path(__file__).resolve()),
               '--child', '--root', str(root)]
    attestation = {
        'complete': False, 'started_utc': datetime.now(timezone.utc).isoformat(),
        'invocations': 1, 'resume_or_splice': False, 'command': command,
        'driver_command': [str(root/DRIVER), 'replay', '--root', str(root), '--output', str(output)],
        'cwd': str(root), 'TEMP': str(temporary), 'TMP': str(temporary),
        'source_file_count': len(frozen), 'before_sha256': frozen,
        'wrapper_before_sha256': sha(Path(__file__)),
        'copied_bytes_equal_workspace_before_and_after_copy': True,
        'supersedes': 'construction3d_frozen_replay_attestation.json',
        'reason': '2D production correction changed complete source manifest; no relabeling of historical results',
    }
    write(metadata, attestation)
    start = time.perf_counter()
    with (EVIDENCE/(PREFIX+'_replay.log')).open('w', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    after = snapshot(root)
    attestation.update(ended_utc=datetime.now(timezone.utc).isoformat(),
                       seconds=time.perf_counter()-start, exit_code=result.returncode,
                       after_sha256=after, source_unchanged=frozen == after,
                       wrapper_after_sha256=sha(Path(__file__)))
    if result.returncode == 0 and frozen == after:
        payload = json.loads(output.read_text(encoding='utf-8'))
        imports = json.loads((EVIDENCE/(PREFIX+'_actual_imports.json')).read_text(encoding='utf-8'))
        attestation['complete'] = (
            payload['complete'] is True and payload['count'] == len(payload['rows']) == 392
            and len({row['case'] for row in payload['rows']}) == 392
            and payload['brute_calls'] == 0 and all(row['brute_calls'] == 0 for row in payload['rows'])
            and attestation['wrapper_before_sha256'] == attestation['wrapper_after_sha256']
            and all(frozen[row['path']] == row['sha256'] for row in imports['modules'].values()))
        attestation['output_sha256'] = sha(output)
        attestation['actual_imports_sha256'] = sha(EVIDENCE/(PREFIX+'_actual_imports.json'))
    write(metadata, attestation)
    assert attestation['complete'], 'single frozen full replay did not complete with stable source and zero brute calls'
    print(json.dumps({k: attestation[k] for k in ('complete', 'invocations', 'source_file_count', 'source_unchanged', 'seconds')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--child', action='store_true')
    args = parser.parse_args()
    if args.child:
        run_child(args.root.resolve(), EVIDENCE/(PREFIX+'_replay.json'))
    else:
        main(args.root)
