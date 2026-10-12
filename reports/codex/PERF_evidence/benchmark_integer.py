"""Rerun exact outputs and median timings, unoptimized Fraction vs integers."""
from pathlib import Path
import json
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
from eab.kernel3d import exact_geom as G
import perf_fraction_reference as old
import test_perf_integer_geometry as gates


def measure(fn, items):
    start = time.perf_counter()
    values = [fn(*args) for args in items]
    return time.perf_counter()-start, values


def main():
    segments = gates.distance_cases()
    triangles = []
    for pts in segments:
        p, *tri = map(G.vector, pts)
        a, b, c = tri
        if any(G.cross(G.sub(b, a), G.sub(c, a))):
            triangles.append((p, tri))
    sat = [gates._sat_input(A, B) for A, B in gates.sat_cases()]
    rows = []
    for name, inputs in [('segment_distance_squared', segments),
                         ('point_triangle_distance_squared', triangles),
                         ('_convex_surface_sat', sat)]:
        before, after = [], []
        for _ in range(5):
            tb, vb = measure(getattr(old, name), inputs)
            ta, va = measure(getattr(G, name), inputs)
            assert va == vb, name
            before.append(tb); after.append(ta)
        rows.append(dict(function=name, cases=len(inputs), repeats=5,
                         before_seconds=before, after_seconds=after,
                         median_before=statistics.median(before),
                         median_after=statistics.median(after),
                         speedup=statistics.median(before)/statistics.median(after),
                         exact_equal=True))
    out = Path(__file__).with_name('integer_benchmark.json')
    out.write_text(json.dumps(rows, indent=2)+'\n', encoding='utf8')
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
