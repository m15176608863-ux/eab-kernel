"""Same inputs, filtered versus pure Fraction; a benchmark, not a time gate."""
from fractions import Fraction as F
from pathlib import Path
import json
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from eab import predicates as p

rng = random.Random(828192)
rows = []
for name, n in [('float_generic', 20000), ('float_near_plane', 5000), ('rational_generic', 5000)]:
    data = []
    for k in range(n):
        pts = [tuple(rng.uniform(-5, 5) for _ in range(3)) for _ in range(4)]
        if name == 'float_near_plane':
            pts[3] = tuple((pts[0][j] + pts[1][j] + pts[2][j]) / 3 for j in range(3))
        elif name == 'rational_generic':
            pts = [tuple(F(v) / 3 for v in q) for q in pts]
        data.append(pts)
    started = time.perf_counter()
    exact = [p.orient3d_fraction(*pts) for pts in data]
    pure_seconds = time.perf_counter() - started
    old = p.orient3d_fraction
    fallback_count = [0]
    def tracked(*args):
        fallback_count[0] += 1
        return old(*args)
    p.orient3d_fraction = tracked
    started = time.perf_counter()
    filtered = [p.orient3d(*pts) for pts in data]
    filtered_seconds = time.perf_counter() - started
    p.orient3d_fraction = old
    assert filtered == exact
    rows.append(dict(name=name, cases=n, mismatches=0, pure_fraction_seconds=pure_seconds,
                     filtered_seconds=filtered_seconds, speedup=pure_seconds/filtered_seconds,
                     exact_fallbacks=fallback_count[0]))
out = dict(command='PYTHONDONTWRITEBYTECODE=1 python -X utf8 reports/codex/E5a_evidence/benchmark_filters.py',
           python=sys.version, total_cases=sum(r['cases'] for r in rows), rows=rows)
path = Path(__file__).with_name('filters_benchmark.json')
path.write_text(json.dumps(out, indent=2), encoding='utf-8')
print(json.dumps(out, indent=2))
