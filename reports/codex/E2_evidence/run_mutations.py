"""WO-E2 one-at-a-time source mutations, isolated pytest subprocesses, byte-for-byte restoration.

Run from this worktree only, with PYTHONDONTWRITEBYTECODE=1 python -X utf8.
Do not run concurrently with tests or source edits. No git writes are performed.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / 'mutations'
OUT.mkdir(exist_ok=True)
EXACT = 'src/eab/kernel2d/exact.py'
COVERS = 'src/eab/kernel2d/covers.py'
ENTRANCE = 'src/eab/kernel2d/entrance.py'
TEST = 'tests/test_kernel2d_exact.py::'

# (id, path, enclosing function, unique old/new source, focused behavioral gate)
MUTATIONS = [
    ('M01_angle_cross_reverse', EXACT, '_angle_less', 'return _cross(u, v) > 0', 'return _cross(u, v) < 0',
     [TEST + 'test_angle_order_is_the_exact_cyclic_order_in_both_halfplanes']),
    ('M02_parallel_take_b', EXACT, 'entrance_block_exact',
     '''            jb, db = eb[i]
            ka, da = ea[j]
            d = (db[0] + da[0], db[1] + da[1])
            facets.append(ExactFacet(("FF", ka, jb), v, d))
            cur_b, cur_a = (jb + 1) % nb, (ka + 1) % na
            i += 1
            j += 1''',
     '''            jb, d = eb[i]
            facets.append(ExactFacet(("VE", cur_a, jb), v, d))
            cur_b = (jb + 1) % nb
            i += 1''', [TEST + 'test_exact_parallel_edges_merge_into_ff_and_nothing_else_does']),
    ('M03_no_foldback_check', EXACT, 'convexity_violation',
     'if c == 0 and _dot(E[i - 1], E[i]) < 0:', 'if False:',
     [TEST + 'test_convexity_rejection_names_the_first_foldback_and_winding_defect',
      'tests/test_kernel2d_lever.py::test_a_polygon_that_folds_back_on_itself_is_rejected_loudly']),
    ('M04_no_winding_check', EXACT, 'convexity_violation', 'if descents != 1:', 'if False:',
     [TEST + 'test_star_pentagon_and_fold_back_are_not_convex', TEST + 'test_convexity_rejection_names_the_first_foldback_and_winding_defect']),
    ('M05_flat_cone_wrong_direction', EXACT, 'vertex_side_exact',
     'if turn == 0 and _dot(d_edge, e_prev) >= 0:', 'if False:',
     [TEST + 'test_flat_vertex_cone_is_one_ray_not_a_line']),
    ('M06_cone_boundary_strict', EXACT, 'vertex_side_exact',
     'return 1 if (c1 > 0 and c2 > 0) else 0', 'return 1 if (c1 >= 0 and c2 >= 0) else 0',
     [TEST + 'test_corner_cone_boundary_is_not_strict']),
    ('M07_membership_boundary_inside', EXACT, 'membership_exact', 'return worst', 'return 1 if worst == 0 else worst',
     [TEST + 'test_exact_membership_boundary_is_not_the_interior']),
    ('M08_strict_vertices_keep_collinear', EXACT, 'strict_vertices',
     'return [k for k in range(n) if _cross(eb.facets[k - 1].direction, eb.facets[k].direction) != 0]',
     'return list(range(n))', [TEST + 'test_strict_vertices_discard_flat_chain_subdivision_vertices']),
    ('M09_hull_keep_collinear', EXACT, 'hull_exact_fr',
     '_cross(_sub(out[-1], out[-2]), _sub(p, out[-2])) <= 0',
     '_cross(_sub(out[-1], out[-2]), _sub(p, out[-2])) < 0',
     [TEST + 'test_exact_hull_discards_collinear_boundary_points']),
    ('M10_polygon_touch_separate', EXACT, 'polygons_overlap_exact',
     'return 0 if touch else -1', 'return -1', [TEST + 'test_exact_overlap_on_a_concave_l_shape']),
    ('M11_triangle_touch_separate', EXACT, '_tri_overlap_exact',
     'if qmin > pmax:', 'if qmin >= pmax:', [TEST + 'test_triangle_exact_touch_is_not_separation']),
    ('M12_nonconvex_forced_convex', COVERS, 'membership_convex',
     's = polygons_overlap_exact(A, B, x)', 's = membership_exact(A, B, x)',
     [TEST + 'test_membership_nonexact_convex_input_uses_the_simple_polygon_path']),
    ('M13_first_entrance_tolerant_selector', ENTRANCE, 'first_entrance',
     'if convexity_violation(A) is None and convexity_violation(B) is None:',
     'if __import__("eab.kernel2d.geom", fromlist=["is_convex"]).is_convex(A, r) and __import__("eab.kernel2d.geom", fromlist=["is_convex"]).is_convex(B, r):',
     [TEST + 'test_first_entrance_routes_rounded_reflex_input_away_from_the_convex_path']),
]

def mutate(data, function, old, new):
    # Preserve every original newline. Match a single enclosing function only.
    lines = data.decode('utf-8').splitlines(keepends=True)
    begin = next(i for i, line in enumerate(lines) if line.startswith('def ' + function + '('))
    end = next((i for i in range(begin + 1, len(lines)) if lines[i].startswith('def ')), len(lines))
    body = ''.join(lines[begin:end])
    nl = '\r\n' if '\r\n' in body else '\n'
    old, new = old.replace('\n', nl), new.replace('\n', nl)
    assert body.count(old) == 1, (function, 'source mutation must hit exactly once')
    return (''.join(lines[:begin]) + body.replace(old, new) + ''.join(lines[end:])).encode('utf-8')

def digest(data):
    return hashlib.sha256(data).hexdigest()

env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8',
           TEMP=str(OUT.parent / 'tmp'), TMP=str(OUT.parent / 'tmp'))
results = []
for ident, relative, function, old, new, tests in MUTATIONS:
    p = ROOT / relative
    original = p.read_bytes()
    bad = mutate(original, function, old, new)
    (OUT / (ident + '.original')).write_bytes(original)
    (OUT / (ident + '.mutation.txt')).write_text(new, encoding='utf-8')
    command = [sys.executable, '-X', 'utf8', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *tests,
               '--junitxml=' + str(OUT / (ident + '.xml'))]
    started = time.perf_counter()
    try:
        p.write_bytes(bad)
        proc = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=90)
        output = (proc.stdout + proc.stderr).decode('utf-8', errors='replace').replace('\r\n', '\n')
        code = proc.returncode
    except subprocess.TimeoutExpired as err:
        output = 'TIMEOUT\n' + (err.stdout or b'').decode('utf-8', errors='replace')
        code = -1
    finally:
        p.write_bytes(original)
        assert p.read_bytes() == original, 'MUTANT NOT RESTORED'
    (OUT / (ident + '.log')).write_text(output, encoding='utf-8')
    failures = []
    xml = OUT / (ident + '.xml')
    if xml.exists():
        for case in ET.parse(xml).iter('testcase'):
            for failure in case.findall('failure') + case.findall('error'):
                failures.append({'test': case.attrib.get('name'), 'message': failure.attrib.get('message'),
                                 'traceback': failure.text})
    row = dict(id=ident, path=relative, function=function, tests=tests, returncode=code,
               outcome='CAUGHT' if code == 1 and failures else ('ESCAPED' if code == 0 else 'INVALID_RUN'),
               seconds=time.perf_counter() - started, original_sha256=digest(original),
               mutated_sha256=digest(bad), restored_sha256=digest(p.read_bytes()), failures=failures)
    results.append(row)
    (OUT / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(ident, row['outcome'], len(failures), 'failures', flush=True)
assert all(row['outcome'] == 'CAUGHT' for row in results), 'Review escaped/invalid mutants'
