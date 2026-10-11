"""Same-process exact-sign before/after benchmark; not a full-suite timing."""
from pathlib import Path
import hashlib
import json
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
from eab import predicates as current
from test_e5a2_bilinear_integer import operand_pairs

old_path = EVIDENCE / 'tmp/profile_baseline/src/eab/predicates.py'
old_source = old_path.read_text(encoding='utf-8')
old = {}
exec(compile(old_source, str(old_path), 'exec'), old)
pairs = list(operand_pairs())
for a, b in pairs:
    for name in ('cross2_sign', 'dot2_sign'):
        assert old[name](a, b) == getattr(current, name)(a, b)

records = []
for name in ('cross2_sign', 'dot2_sign'):
    measurements = {'before': [], 'after': []}
    for repeat in range(5):
        sequence = ('before', 'after') if repeat % 2 == 0 else ('after', 'before')
        for version in sequence:
            fn = old[name] if version == 'before' else getattr(current, name)
            cpu, wall = time.process_time(), time.perf_counter()
            checksum = 0
            for _ in range(20):
                for a, b in pairs:
                    checksum += fn(a, b)
            measurements[version].append(dict(cpu_seconds=time.process_time()-cpu,
                                               wall_seconds=time.perf_counter()-wall,
                                               checksum=checksum))
    assert {row['checksum'] for rows in measurements.values() for row in rows}.__len__() == 1
    records.append(dict(function=name, pairs_per_repeat=len(pairs)*20, measurements=measurements,
                        median_cpu_before=statistics.median(r['cpu_seconds'] for r in measurements['before']),
                        median_cpu_after=statistics.median(r['cpu_seconds'] for r in measurements['after'])))
output = dict(records=records, exact_equality_pairs=len(pairs),
              baseline_sha256=hashlib.sha256(old_source.encode()).hexdigest(),
              current_sha256=hashlib.sha256((ROOT/'src/eab/predicates.py').read_bytes()).hexdigest(),
              timing_boundary='Other baseline profilers were active; alternating same-process CPU medians are diagnostic, not exclusive whole-suite timing.')
(EVIDENCE/'bilinear_benchmark.json').write_text(json.dumps(output, indent=2)+'\n', encoding='utf-8')
print(json.dumps([{k:v for k,v in row.items() if k!='measurements'} for row in records], indent=2))
