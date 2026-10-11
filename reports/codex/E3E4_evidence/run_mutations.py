"""Apply one source mutation, run its gates, and restore byte-for-byte in finally.

Run serially, only after all editing/testing agents have stopped touching source.
The manifest contains id/path/old/new/selectors and optional explanation fields.
"""
from __future__ import annotations

import argparse
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


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(spec):
    path = (ROOT / spec['path']).resolve()
    path.relative_to(ROOT)
    original = path.read_bytes()
    eol = '\r\n' if b'\r\n' in original else '\n'
    def encoded(s):
        return s.replace('\r\n', '\n').replace('\n', eol).encode('utf-8')
    old, new = encoded(spec['old']), encoded(spec['new'])
    assert original.count(old) == 1, (spec['id'], 'mutation must match exactly once', original.count(old))
    folder = OUT / 'mutations'
    folder.mkdir(exist_ok=True)
    tmp = OUT / 'tmp' / 'mutation_backups'
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / (spec['id'] + '_' + path.name)).write_bytes(original)
    log_path = folder / (spec['id'] + '.log')
    xml_path = folder / (spec['id'] + '.xml')
    cmd = [sys.executable, '-X', 'utf8', '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
           '--junitxml=' + str(xml_path), *spec['selectors']]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8',
               TEMP=str(OUT / 'tmp'), TMP=str(OUT / 'tmp'))
    result = dict(id=spec['id'], path=spec['path'], command=cmd,
                  original_sha256=sha(original), original_backup=str(tmp.relative_to(ROOT)),
                  patch_old=spec['old'], patch_new=spec['new'])
    try:
        mutant = original.replace(old, new, 1)
        path.write_bytes(mutant)
        result['mutant_sha256'] = sha(mutant)
        started = time.perf_counter()
        with log_path.open('w', encoding='utf-8', newline='') as log:
            p = subprocess.run(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        result['elapsed_seconds'] = time.perf_counter() - started
        result['returncode'] = p.returncode
        result['failures'] = []
        if xml_path.exists():
            for case in ET.parse(xml_path).iter('testcase'):
                for tag in ('failure', 'error'):
                    el = case.find(tag)
                    if el is not None:
                        result['failures'].append(dict(classname=case.get('classname'), name=case.get('name'),
                                                       kind=tag, message=el.get('message'), text=el.text))
        lines = log_path.read_text(encoding='utf-8').splitlines()
        result['last_line'] = lines[-1] if lines else ''
    finally:
        path.write_bytes(original)
        result['restored_sha256'] = sha(path.read_bytes())
        result['byte_restored'] = result['restored_sha256'] == result['original_sha256']
        (folder / (spec['id'] + '_result.json')).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        assert result['byte_restored']
    print(json.dumps({k: result[k] for k in ('id', 'returncode', 'last_line', 'byte_restored')}, ensure_ascii=False), flush=True)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('manifest', type=Path)
    ap.add_argument('--ids', nargs='*')
    args = ap.parse_args()
    specs = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    if isinstance(specs, dict):
        specs = specs['mutations']
    for spec in specs:
        if 'path' not in spec:
            spec['path'] = spec['file']
        if 'selectors' not in spec:
            spec['selectors'] = spec['pytest']
    results = [run(s) for s in specs if args.ids is None or s['id'] in args.ids]
    (OUT / 'mutations' / (args.manifest.stem + '_results.json')).write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
