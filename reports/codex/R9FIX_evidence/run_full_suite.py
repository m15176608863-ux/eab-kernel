"""Complete module shards, with exact node coverage and final source SHA freeze."""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'reports/codex/R9FIX_evidence'
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8',
           PYTHONPATH=str(ROOT/'src'))
BASE = [sys.executable, '-X', 'utf8', '-m', 'pytest', '-q', '-p', 'no:cacheprovider']


def snapshot():
    paths = [ROOT/'pyproject.toml']
    for folder in ('src', 'tests', 'tools', 'fixtures', 'docs'):
        paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts)
    paths.append(ROOT/'README.md')
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths}


def main():
    t0 = time.perf_counter()
    before = snapshot()
    (OUT/'full_source_freeze.json').write_text(json.dumps(before, indent=2), encoding='utf8')
    result = subprocess.run(BASE+['--collect-only', 'tests'], cwd=ROOT, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (OUT/'full_collection.log').write_bytes(result.stdout)
    nodes = [line for line in result.stdout.decode('utf8').splitlines()
             if line.startswith('tests/') and '::' in line]
    assert result.returncode == 0 and len(nodes) >= 10100
    assert len(nodes) == len(set(nodes)), 'duplicate collected test node'
    counts = collections.Counter(node.split('::')[0] for node in nodes)
    # Empirical first-run module timings balance heavy geometry independently
    # of node count. Every module/node remains assigned exactly once.
    weights = collections.defaultdict(float)
    for history in (OUT/'attempt1').glob('full_*.xml'):
        for case in ET.parse(history).getroot().findall('.//testcase'):
            module = case.get('classname').replace('.', '/') + '.py'
            weights[module] += float(case.get('time', '0'))
    groups, loads, seconds = [[] for _ in range(4)], [0]*4, [0.0]*4
    estimated = {m: max(weights.get(m, n*0.01), 0.001) for m,n in counts.items()}
    for module, count in sorted(counts.items(), key=lambda item:(-estimated[item[0]], item[0])):
        shard = seconds.index(min(seconds))
        groups[shard].append(module)
        loads[shard] += count
        seconds[shard] += estimated[module]
    flat = [module for group in groups for module in group]
    assert collections.Counter(flat) == collections.Counter({module:1 for module in counts})
    commands, streams, processes = [], [], []
    for i, group in enumerate(groups):
        cmd = BASE+group+['--basetemp='+str(OUT/'tmp'/f'full_{i}'),
                          '--junitxml='+str(OUT/f'full_{i}.xml'), '--durations=15']
        stream = (OUT/f'full_{i}.log').open('wb')
        streams.append(stream)
        commands.append(cmd)
        processes.append(subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT))
    rows = []
    for i, process in enumerate(processes):
        code = process.wait()
        streams[i].close()
        log = (OUT/f'full_{i}.log').read_text(encoding='utf8', errors='replace')
        tests = ET.parse(OUT/f'full_{i}.xml').getroot().findall('.//testcase')
        row = dict(shard=i, expected=loads[i], tests=len(tests), exit_code=code,
                   skipped=sum(t.find('skipped') is not None for t in tests),
                   failures=sum(t.find('failure') is not None for t in tests),
                   errors=sum(t.find('error') is not None for t in tests),
                   last_line=log.strip().splitlines()[-1])
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    after = snapshot()
    drift = [p for p in set(before)|set(after) if before.get(p) != after.get(p)]
    metadata = dict(mode='4 independent processes, complete module shards; no xdist or cross-module order claim',
                    head=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
                    collected=len(nodes), nodes=nodes, module_counts=counts, commands=commands,
                    estimated_seconds=seconds, weight_source="attempt1 JUnit per-module seconds",
                    results=rows, seconds=time.perf_counter()-t0, source_drift=sorted(drift),
                    end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (OUT/'full_suite.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf8')
    okay = not drift and all(r['exit_code']==0 and r['expected']==r['tests'] and
                            not(r['failures'] or r['errors'] or r['skipped']) for r in rows)
    print(f"FULL_SUITE {'PASS' if okay else 'FAIL'}: {sum(r['tests'] for r in rows)} tests, "
          f"0 unassigned modules, {len(drift)} source drift, {metadata['seconds']:.2f}s", flush=True)
    return not okay


if __name__ == '__main__':
    raise SystemExit(main())
