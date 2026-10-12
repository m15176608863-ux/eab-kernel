"""Cold-cache independent oracle benchmark and complete-output comparison."""
from pathlib import Path
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests'), str(ROOT / 'tools')]
import e5a_cover_oracle as fast
import e5a_escape_oracle as fast_escape
import perf_cover_oracle_reference as slow
import perf_escape_oracle_reference as slow_escape
from test_invariance_interlock import _ilock, _vec, ROT_Z, OFFSETS


def measure(cover, escape, A, B, offset):
    cover.model.cache_clear()
    cover.strict_cone.cache_clear()
    escape.geometry_noise.cache_clear()
    escape._candidates.cache_clear()
    start = time.perf_counter()
    result = escape.candidates(A, B, offset)
    return time.perf_counter()-start, result


rows = []
for rotation, translation, scale in [('I', 0., .001), ('z0.7', 0., 1.), ('z0.7', 1e5, 1000.)]:
    A, B = _ilock(rotation, translation, scale)
    for base_offset in OFFSETS[:2]:
        offset = _vec(ROT_Z[rotation], scale, base_offset)
        before, expected = measure(slow, slow_escape, A, B, offset)
        after, actual = measure(fast, fast_escape, A, B, offset)
        assert actual == expected
        rows.append(dict(rotation=rotation, translation=translation, scale=scale,
                         offset=base_offset, before_seconds=before, after_seconds=after,
                         speedup=before/after, candidates=len(actual[0]), complete_output_equal=True))
data = dict(rows=rows, before_total_seconds=sum(r['before_seconds'] for r in rows),
            after_total_seconds=sum(r['after_seconds'] for r in rows),
            cold_caches=True, reference='tests/perf_escape_oracle_reference.py')
path = Path(__file__).with_name('oracle_benchmark.json')
path.write_text(json.dumps(data, indent=2), encoding='utf-8')
print(json.dumps(data, indent=2))
