"""Reproduce WO-PERF interlock equivalence microbenchmarks and cProfile.

Run: PYTHONPATH=src python -X utf8 tools/perf_interlock_benchmark.py
All compared timings use the same current arithmetic primitives, so they isolate
these two optimizations rather than folding in parallel exact-geometry changes.
"""
import cProfile
import json
from pathlib import Path
import pstats
from statistics import median
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from osteomorphic import interlocking_pair
from perf_sweep_reference import reference_events
from eab.kernel3d import exact_sweep as S
from eab.adapters import tia3d as I
from eab.kernel3d.geom3 import Polyhedron

OUT = ROOT / 'reports/codex/PERF_evidence/interlock'
OUT.mkdir(parents=True, exist_ok=True)


def timed(fn, repeats=3):
    runs = []
    for _ in range(repeats):
        t = perf_counter()
        fn()
        runs.append(perf_counter() - t)
    return median(runs)


def main():
    A, B = interlocking_pair(nx=5, ny=2, amp=.3, phase=1.)
    rows = []
    for name, shift, scale, offset in (
            ('general', 0., 1., (.23, .07, 0.)),
            ('degenerate', 0., 1., (.4, 0., 0.)),
            ('engineering', 1e6, 1e-3, (.00023, .00007, 0.))):
        def transformed(P):
            return Polyhedron([tuple(shift + scale*x for x in p) for p in P.verts], list(P.faces))
        a, b = transformed(A), transformed(B)
        args = a, b, offset, 1e-9, 1e-9
        expected = I._candidates_uncached(*args)
        I._candidates_cached.cache_clear()
        assert I._candidates(*args) == expected
        before = timed(lambda: I._candidates_uncached(*args))
        after = timed(lambda: I._candidates(*args))
        rows.append(dict(optimization='candidate_content_cache_warm', case=name,
                         before_seconds=before, after_seconds=after, speedup=before/after))
        av = tuple(tuple(S.F(x) + S.F(y) for x, y in zip(p, offset)) for p in a.verts)
        eargs = av, tuple(a.faces), tuple(map(S.G.vector, b.verts)), tuple(b.faces), (S.F(0), S.F(0), S.F(1)), S.F(0), None
        expected = reference_events(*eargs)
        assert S._events_cached.__wrapped__(*eargs) == expected
        before = timed(lambda: reference_events(*eargs))
        after = timed(lambda: S._events_cached.__wrapped__(*eargs))
        rows.append(dict(optimization='exact_static_axis_pruning', case=name,
                         before_seconds=before, after_seconds=after, speedup=before/after,
                         events=len(expected)))
    (OUT/'microbench.json').write_text(json.dumps(rows, indent=2), encoding='utf8')
    I._candidates_cached.cache_clear()
    I._exact_escape_cached.cache_clear()
    S._events_cached.cache_clear()
    p = cProfile.Profile()
    p.enable()
    for off in ((.23,.07,0.),(-.41,-.12,0.)):
        I.escape_height_covers(A,B,off)
        I.escape_candidates(A,B,off)
    p.disable()
    p.dump_stats(str(OUT/'after.pstats'))
    with (OUT/'after_top20.txt').open('w',encoding='utf8') as f:
        pstats.Stats(p,stream=f).strip_dirs().sort_stats('cumulative').print_stats(20)
        pstats.Stats(p,stream=f).strip_dirs().sort_stats('tottime').print_stats(20)
    print(json.dumps(rows, indent=2))
    print((OUT/'after_top20.txt').read_text(encoding='utf8'))


if __name__ == '__main__':
    main()
