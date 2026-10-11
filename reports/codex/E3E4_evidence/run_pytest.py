"""WO-E3E4 repeatable pytest capture; writes only into this evidence directory."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def hashes():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('src', 'tests') for p in sorted((ROOT / folder).rglob('*.py'))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('label')
    parser.add_argument('selectors', nargs='*', default=['tests'])
    args = parser.parse_args()
    if not args.label.replace('_', '').replace('-', '').isalnum():
        parser.error('label must be a simple filename stem')
    tmp = OUT / 'tmp'
    tmp.mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8',
               TEMP=str(tmp), TMP=str(tmp))
    xml = OUT / (args.label + '.xml')
    cmd = [sys.executable, '-X', 'utf8', '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
           '--junitxml=' + str(xml), *(args.selectors or ['tests'])]
    before = hashes()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    t0 = time.perf_counter()
    with (OUT / (args.label + '.log')).open('w', encoding='utf-8', newline='') as log:
        completed = subprocess.run(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    elapsed = time.perf_counter() - t0
    lines = (OUT / (args.label + '.log')).read_text(encoding='utf-8').splitlines()
    failures = []
    if xml.exists():
        for case in ET.parse(xml).iter('testcase'):
            for kind in ('failure', 'error', 'skipped'):
                node = case.find(kind)
                if node is not None:
                    failures.append(dict(classname=case.get('classname'), name=case.get('name'),
                                         kind=kind, message=node.get('message'), text=node.text))
    result = dict(command=cmd, cwd=str(ROOT), started_utc=started,
                  elapsed_seconds=elapsed, returncode=completed.returncode,
                  last_line=lines[-1] if lines else '',
                  source_unchanged=before == hashes(), sha256_before=before,
                  failures=failures)
    (OUT / (args.label + '_result.json')).write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('returncode', 'elapsed_seconds', 'last_line',
                                          'source_unchanged')}, ensure_ascii=False))
    return completed.returncode


if __name__ == '__main__':
    raise SystemExit(main())
