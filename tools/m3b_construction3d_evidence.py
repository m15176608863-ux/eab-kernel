"""M3b rerunnable semantic mutants and isolated before/after microbenchmarks.

Only the stdlib orchestrates subprocesses. Existing pytest test modules supply
raw fixtures and their named assertions; no hash/static gate runs in children.
Set PYTHONDONTWRITEBYTECODE=1, TEMP/TMP within M3b_evidence/tmp before running.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'reports/codex/M3b_evidence'


def _write(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def _load_baseline(folder):
    import eab.kernel3d
    for leaf in ('global_entrance', 'interlock'):
        name = 'eab.kernel3d.'+leaf
        spec = importlib.util.spec_from_file_location(name, folder/f'{leaf}.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        setattr(eab.kernel3d, leaf, module)


def mutation(name):
    import inspect
    import textwrap
    import test_m3b_construction3d as T
    G = T.G
    if name == 'self_intersection':
        check = T._crossing_assertion
        function, before, after = G._validate_embedded, 'meeting = _triangle_meeting(a, b)', 'meeting = set()'
    elif name == 'spatial_omission':
        check = T._candidate_assertion
        function, before, after = G._line_candidate, 'return True', 'return b.interior[2] < 2'
    else:
        base = ((T.F(0),)*3, (T.F(2), T.F(0), T.F(0)), (T.F(0), T.F(2), T.F(0)))
        parts = tuple(G.convex_decomposition(T.geom3.tetra(*base, apex))[0]
                      for apex in ((T.F(0), T.F(0), T.F(1)), (T.F(4), T.F(4), T.F(-1))))
        def check():
            model = G.GlobalEntrance3D(G.convex_decomposition(T.geom3.box(half=(T.F(1, 16),)*3)),
                                      G._merge_parts(parts))
            assert model.classify((T.F(2), T.F(2), 0)) == -1, 'full-facet nonconvex merge filled independently excluded region'
        before = ('                if any(_dot(n, _sub(p, q)) > 0 for n, q in planes for p in vertices):\n'
                  '                    continue\n'
                  '                parts[i] = _part(faces)')
        function, after = G._merge_parts, '                parts[i] = _box_part(vertices)'
    check()
    print('BASELINE_SEMANTIC_ASSERTION_PASS', flush=True)
    source = textwrap.dedent(inspect.getsource(function))
    assert source.count(before) == 1
    namespace = dict(vars(G))
    exec(compile(source.replace(before, after), '<M3b semantic-only mutant>', 'exec'), namespace)
    setattr(G, function.__name__, namespace[function.__name__])
    G._decompose.cache_clear()
    G._line_sections.cache_clear()
    check()  # Deliberately uncaught: child must exit red at the semantic assertion.


def mutations():
    rows = []
    for name, expected in [('self_intersection', 'overlapping coplanar shells must be rejected before decomposition'),
                           ('spatial_omission', 'all exact box candidates are retained'),
                           ('nonconvex_merge', 'full-facet nonconvex merge filled independently excluded region')]:
        result = subprocess.run([sys.executable, '-X', 'utf8', __file__, '--mutation', name],
                                cwd=ROOT, text=True, encoding='utf-8', capture_output=True)
        transcript = result.stdout+result.stderr
        path = EVIDENCE/f'construction3d_mutation_{name}.log'
        path.write_text(transcript, encoding='utf-8')
        assert result.returncode != 0 and 'BASELINE_SEMANTIC_ASSERTION_PASS' in transcript
        assert 'AssertionError: '+expected in transcript, transcript
        rows.append({'name': name, 'returncode': result.returncode, 'baseline_passed': True,
                     'expected_assertion': expected, 'hash_gate_executed': False,
                     'log': path.relative_to(ROOT).as_posix()})
    _write(EVIDENCE/'construction3d_mutations.json', {'complete': True, 'rows': rows})


def microbench(folder):
    if folder:
        _load_baseline(folder)
    from fractions import Fraction as F
    from eab.kernel3d import global_entrance as G, interlock as I
    from eab.kernel3d.geom3 import box
    from test_interlock_exact import _wall
    from osteomorphic import interlocking_pair
    jobs = [('box', box(), box(), (F(1, 7), F(1, 11), F(1, 13))),
            ('wall', *_wall(16), (F(0),)*3),
            ('TIA', *interlocking_pair(nx=3, ny=1, amp=.2), (F(1, 5), F(1, 7), F(0)))]
    rows = []
    for name, a, b, offset in jobs:
        cold, warm, answer = [], [], None
        for repeat in range(5):
            # Clear all global model/section caches for a reproducible cold run.
            for module in (G, I):
                for value in vars(module).values():
                    if getattr(value, '__module__', None) == module.__name__ and hasattr(value, 'cache_clear'):
                        value.cache_clear()
            start = time.perf_counter()
            result = I.escape_height_covers(a, b, offset)
            cold.append(time.perf_counter()-start)
            exact = (str(result.exact_height), tuple(map(str, result.exact_offset)), result.nonpenetrating_state)
            assert answer is None or answer == exact
            answer = exact
            start = time.perf_counter()
            for k in range(100):
                assert I._nonpenetrating_at(a, b, offset, F(k, 103)) in (-1, 0, 1)
            warm.append((time.perf_counter()-start)/100)
        rows.append({'case': name, 'exact': answer, 'cold_seconds': cold, 'warm_query_seconds': warm,
                     'cold_median': statistics.median(cold), 'warm_median': statistics.median(warm)})
    print(json.dumps({'implementation': 'baseline' if folder else 'current', 'rows': rows}))


def compare(baseline, current, output):
    baseline, current, output = (path.resolve() for path in (baseline, current, output))
    old, new = [json.loads(path.read_text(encoding='utf-8')) for path in (baseline, current)]
    assert old['complete'] and new['complete']
    a, b = [{row['case']: row for row in item['rows']} for item in (old, new)]
    assert a.keys() == b.keys() and len(a) == 392
    fields = ('input_sha256', 'exact_height', 'exact_offset', 'state')
    mismatches = [name for name in a if any(a[name][field] != b[name][field] for field in fields)]
    assert not mismatches and all(row['brute_calls'] == 0 for row in b.values())
    _write(output, {'complete': True, 'count': len(a), 'equal_fields': len(a)*len(fields),
                    'mismatches': mismatches, 'current_brute_calls': new['brute_calls'],
                    'baseline_seconds': old['seconds'], 'current_seconds': new['seconds'],
                    'baseline_over_current': old['seconds']/new['seconds'],
                    'timing_caveat': 'long replay ran concurrently with other audits; use isolated cold/warm microbenchmarks for attribution',
                    'files': [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                              for p in (baseline, current)]})


if __name__ == '__main__':
    sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests'), str(ROOT/'tools')]
    parser = argparse.ArgumentParser()
    parser.add_argument('--mutation', choices=['self_intersection', 'spatial_omission', 'nonconvex_merge'])
    parser.add_argument('--mutations', action='store_true')
    parser.add_argument('--microbench', action='store_true')
    parser.add_argument('--baseline-folder', type=Path)
    parser.add_argument('--compare', nargs=3, type=Path)
    args = parser.parse_args()
    if args.mutation:
        mutation(args.mutation)
    elif args.mutations:
        mutations()
    elif args.microbench:
        microbench(args.baseline_folder)
    elif args.compare:
        compare(*args.compare)
