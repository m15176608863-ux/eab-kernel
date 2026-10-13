"""Rerunnable M3 large scan / frozen HEAD replay; standard library orchestrator.

Run from the worktree with PYTHONDONTWRITEBYTECODE=1 and -X utf8. Heavy scans
are evidence, not silently skipped pytest tests. Source-tree selection must
point to the frozen baseline or current root explicitly.
"""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import random
import sys
import time


def write(path, payload):
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def replay(root, output):
    sys.path[:0] = [str(root/'src'), str(root/'tests'), str(root/'tools')]
    from eab.kernel3d import interlock as I
    from eab.kernel3d.geom3 import box, Polyhedron
    from eab.margin import effective_geom_tol
    from osteomorphic import interlocking_pair
    import test_interlock_walls as W
    import test_interlock_escape as E
    import test_invariance_interlock as V
    jobs = []
    for clearance in (0, 1e-6):
        for translation, ulps in ((1e5, 4), (1e4, 1), (1e3, 4), (0., 0)):
            for seed in range(20):
                rng = random.Random(seed)
                A = W._place(W._key(clearance), .7, translation, rng, ulps)
                B = W._place(W._prism_xz(W.U_PROF, -1., 1.), .7, translation, rng, ulps)
                label = f'wall/{clearance}/{translation}/{ulps}/{seed}'
                jobs.append((label, A, B, (0, 0, 0), {}))
                if not clearance:
                    jobs.append((label+'/window', A, B, (0, 0, 0),
                                 {'contact_window': effective_geom_tol(A, B, None)}))
    for name, kw in E.BLOCKS.items():
        A, B = interlocking_pair(**kw)
        for k, off in enumerate(E._offsets(7, 25)):
            jobs.append((f'TIA/{name}/{k}', A, B, off, {}))
    for scale in (1e-2, 1e2):
        A, B = interlocking_pair(nx=5, ny=2, amp=.3*scale, phase=1.,
                                lx=2*scale, ly=scale, lz=scale)
        for k, off in enumerate(E._offsets(7, 8, scale)):
            jobs.append((f'TIA/scale/{scale}/{k}', A, B, off, {}))
    A, B = interlocking_pair(nx=5, ny=2, amp=.3, phase=1.)
    for k, off in enumerate(((0, 0, 0), (.4, 0, 0), (-.4, .25, 0), (.2, -.3, 0),
                             (-.5247287610704319, -.2386957665910207, 0))):
        jobs.append((f'TIA/grid_audit/{k}', A, B, off, {}))
    A, B = interlocking_pair(nx=4, ny=2, amp=.25)
    for delta in (.2, .4, .6):
        jobs.append((f'TIA/local_counterexample/{delta}', A, B, (delta, 0, 0), {}))
    for rotation in V.ROT_Z:
        for translation in V.TS:
            for scale in V.SS:
                A, B = V._ilock(rotation, translation, scale)
                for k, off in enumerate(V.OFFSETS):
                    jobs.append((f'invariance/{rotation}/{translation}/{scale}/{k}', A, B,
                                 V._vec(V.ROT_Z[rotation], scale, off), {}))
    for scale, shift in ((F(1), F(0)), (F(1, 1024), F(10**6)), (F(1024), F(-10**5))):
        A = box(center=(shift, 0, shift), half=(scale/2,)*3)
        lower = box(center=(shift, 0, shift), half=(scale,)*3)
        upper = box(center=(shift, 0, shift+3*scale), half=(scale/2,)*3)
        B = Polyhedron(list(lower.verts)+list(upper.verts),
                       list(lower.faces)+[tuple(i+8 for i in f) for f in upper.faces])
        jobs.append((f'reentry/{scale}/{shift}', A, B, (0, 0, 0), {}))
        A = box(center=(shift, 0, shift+F(7, 4)*scale), half=(scale/2,)*3)
        B = box(center=(shift, 0, shift+scale), half=(scale/2,)*3)
        jobs.append((f'window_shift/{scale}/{shift}', A, B, (0, 0, 0), {'contact_window': scale/16}))
    rows = []
    calls = [0]
    original = I.polyhedra_overlap
    def counted(*args, **kwargs):
        calls[0] += 1
        return original(*args, **kwargs)
    I.polyhedra_overlap = counted
    start = time.perf_counter()
    for i, (name, A, B, off, kwargs) in enumerate(jobs):
        before = calls[0]
        t0 = time.perf_counter()
        sol = I.escape_height_covers(A, B, off, **kwargs)
        shape = repr((tuple(tuple(str(F(x)) for x in p) for p in A.verts), tuple(A.faces),
                      tuple(tuple(str(F(x)) for x in p) for p in B.verts), tuple(B.faces),
                      tuple(str(F(x)) for x in off), sorted((k, str(F(v))) for k, v in kwargs.items())))
        rows.append({'case': name, 'input_sha256': hashlib.sha256(shape.encode()).hexdigest(),
                     'exact_height': str(sol.exact_height), 'exact_offset': list(map(str, sol.exact_offset)),
                     'state': sol.nonpenetrating_state, 'brute_calls': calls[0]-before,
                     'seconds': time.perf_counter()-t0})
        if (i+1) % 20 == 0:
            print(f'{i+1}/{len(jobs)} {time.perf_counter()-start:.3f}s', flush=True)
            write(output, {'complete': False, 'rows': rows})
    write(output, {'complete': True, 'source_root': str(root), 'count': len(rows),
                   'seconds': time.perf_counter()-start, 'brute_calls': calls[0], 'rows': rows})


def scan(root, output):
    sys.path[:0] = [str(root/'src'), str(root/'tests'), str(root/'tools')]
    import test_m3_global3d as T
    from eab.kernel3d import global_entrance as G
    from eab.kernel3d.geom3 import Polyhedron, box, polyhedra_overlap
    from osteomorphic import interlocking_pair
    families = list(T._families())
    families.append(('TIA_nx3', *interlocking_pair(nx=3, ny=1, amp=.2)))
    small = box(half=(F(1, 3), F(1, 4), F(1, 5)))
    families.append(('twisted_prism', small, T._twisted_prism()))
    for seed in (7, 23):
        for scale in (F(1, 1024), F(1), F(1024)):
            def scaled(P):
                return Polyhedron([tuple(F(x)*scale for x in p) for p in P.verts], P.faces)
            families.append((f'random_concave_{seed}_scale_{scale}', scaled(small), scaled(T._random_concave(seed))))
    rows = []
    overall = time.perf_counter()
    for name, A, B in families:
        start = time.perf_counter()
        model = G.global_entrance(A, B)
        construction_seconds = time.perf_counter()-start
        probes = T._cell_probes(model)
        mismatches = []
        for q in probes:
            state = model.classify(q)
            oracle = polyhedra_overlap(T._raw_shift(A, q), B, 0)
            if state != oracle:
                mismatches.append({'q': list(map(str, q)), 'actual': state, 'oracle': oracle})
        row = {'family': name, 'parts_a': len(model.parts_a), 'parts_b': len(model.parts_b),
               'probe_count': len(probes), 'mismatch_count': len(mismatches), 'mismatches': mismatches,
               'construction_seconds': construction_seconds, 'seconds': time.perf_counter()-start,
               'probe_sha256': hashlib.sha256(repr(probes).encode()).hexdigest()}
        rows.append(row)
        print(name, row['probe_count'], row['mismatch_count'], row['seconds'], flush=True)
        write(output, {'complete': False, 'rows': rows})
    write(output, {'complete': True, 'rows': rows, 'total_probes': sum(r['probe_count'] for r in rows),
                   'total_mismatches': sum(r['mismatch_count'] for r in rows),
                   'seconds': time.perf_counter()-overall,
                   'probe_contract': 'all lazy convex-pair vertex candidates/edge midpoints/support-face barycentres/exact sides; not explicit 3D overlay',
                   'oracle_imports': ['eab.kernel3d.geom3.polyhedra_overlap', 'eab.kernel3d.exact_geom'],
                   'oracle_has_no_global_entrance_import': True})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['scan', 'replay', 'compare'])
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--old', type=Path)
    parser.add_argument('--new', type=Path)
    args = parser.parse_args()
    if args.mode == 'scan':
        scan(args.root.resolve(), args.output)
    elif args.mode == 'replay':
        replay(args.root.resolve(), args.output)
    else:
        old, new = json.loads(args.old.read_text()), json.loads(args.new.read_text())
        assert old['complete'] and new['complete']
        a, b = ({row['case']: row for row in result['rows']} for result in (old, new))
        assert set(a) == set(b), 'replay input case sets differ'
        fields = ('input_sha256', 'exact_height', 'exact_offset', 'state')
        wrong = [{'case': key, 'field': field, 'old': a[key][field], 'new': b[key][field]}
                 for key in a for field in fields if a[key][field] != b[key][field]]
        write(args.output, {'count': len(a), 'mismatch_count': len(wrong), 'mismatches': wrong,
                            'compared_fields': list(fields), 'field_comparison_count': len(a)*len(fields),
                            'rows': [{'case': key, 'fields_equal': {field: a[key][field] == b[key][field]
                                                                   for field in fields}} for key in a],
                            'new_brute_calls': new['brute_calls'], 'old_brute_calls': old['brute_calls'],
                            'old_seconds': old['seconds'], 'new_seconds': new['seconds']})
        assert not wrong and new['brute_calls'] == 0
