"""Frozen exhaustive small-family 3D boundary evidence, no skipped probes.

Run with PYTHONDONTWRITEBYTECODE=1 python -X utf8 tools/m3b_boundary3d_evidence.py.
Only the completed final JSON is evidence; progress is overwritten per run.
"""
import json
import sys
import time
import hashlib
import subprocess
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
from test_m3b_boundary3d import audit, pairs
from test_m3_global3d import _combine
from eab.kernel3d import geom3


def fingerprints():
    names = ['src/eab/kernel3d/'+name+'.py' for name in
             ('boundary', 'global_entrance', 'covers3', 'geom3', 'exact_geom', 'g03', 'g03_exit_oracle', 'g03_surface_oracle')]
    names += ['src/eab/kernel2d/g0_oracle.py', 'src/eab/construction.py', 'src/eab/oracle_construction.py',
              'tests/test_m3b_boundary3d.py', 'tests/test_m3_global3d.py', 'tools/m3b_boundary3d_evidence.py']
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}


def mutations():
    prefix = '''import sys, inspect, textwrap
from pathlib import Path
sys.path[:0] = [str(Path.cwd()/'src'),str(Path.cwd()/'tests')]
from test_m3b_boundary3d import *
'''
    cases = [
        ('remove_clipping', 'local cover clipping removes buried polygons', '''
s=textwrap.dedent(inspect.getsource(B.clip_local_covers)); ns=dict(vars(B))
exec(compile(s.replace('out = []', 'return tuple(candidates)\\n    out = []'), '<inside clipping mutation>', 'exec'),ns)
B.clip_local_covers=ns['clip_local_covers']
audit(*pairs()[0])
'''),
        ('physical_zero_one_seam', 'closed occupancy boundary not physical 0/1 seam', '''
s=textwrap.dedent(inspect.getsource(B.explicit_boundary)); ns=dict(vars(B))
exec(compile(s.replace('_closed_side(side_states[0]) == _closed_side(side_states[1])','model.classify(G._mean(piece)) != 0'), '<inside side label mutation>', 'exec'),ns)
B.explicit_boundary=ns['explicit_boundary']
_,A,C=pairs()[1]
boundary=B.explicit_boundary(G.global_entrance(A,C))
for patch in boundary.patches:
 truth=tuple(oracle_state(A,C,p)>=0 for p in patch.side_points)
 assert truth[0]!=truth[1], 'closed occupancy boundary not physical 0/1 seam'
'''),
        ('restore_intersecting_skip', 'intersecting exit sample must execute', '''
s=textwrap.dedent(inspect.getsource(g03.g0_distance_completeness3)); ns=dict(vars(g03))
exec(compile(s.replace('if truth2 is None:', 'if truth2 is None:\\n            rep.skipped_intersecting += 1\\n            continue'), '<inside skip mutation>', 'exec'),ns)
g03.g0_distance_completeness3=ns['g0_distance_completeness3']
cube=geom3.box(); rep=g03.g0_distance_completeness3(cube,cube,radius=0,samples=1)
assert rep.samples==1 and rep.skipped_intersecting==0, 'intersecting exit sample must execute'
''')]
    hashes = fingerprints()
    rows = []
    for name, expected, body in cases:
        run = subprocess.run([sys.executable, '-X', 'utf8', '-c', prefix+body], cwd=ROOT,
                             text=True, encoding='utf-8', errors='replace', capture_output=True)
        log = ROOT/'reports/codex/M3b_evidence'/('boundary3d_mutation_'+name+'.txt')
        log.write_text(run.stdout+run.stderr, encoding='utf-8')
        assert run.returncode != 0 and 'AssertionError: '+expected in run.stderr, (name, run.stderr)
        rows.append(dict(name=name, returncode=run.returncode, expected_assertion=expected,
                         log=str(log.relative_to(ROOT)).replace('\\','/'), source_hash_gate=False))
    assert fingerprints() == hashes, 'source changed during mutation evidence; invalidate and rerun'
    (ROOT/'reports/codex/M3b_evidence/boundary3d_mutations.json').write_text(
        json.dumps({'status':'COMPLETE','mutations':rows,'source_sha256':hashes},indent=2)+'\n',encoding='utf-8')


def main():
    hashes = fingerprints()
    destination = ROOT/'reports/codex/M3b_evidence/boundary3d_scan.json'
    progress = ROOT/'reports/codex/M3b_evidence/boundary3d_progress.json'
    rows = []
    cases = pairs()
    outer, inner = geom3.box(half=(2,)*3), geom3.box(half=(F(1, 2),)*3)
    cavity = _combine(outer, geom3.Polyhedron(inner.verts, [tuple(reversed(face)) for face in inner.faces]))
    cases.append(('cavity', inner, cavity))
    A = geom3.tetra((0, 0, 0), (2, 0, 0), (0, 3, 0), (0, 0, 4))
    C = geom3.tetra((1, 1, 1), (3, 2, 1), (0, 4, 2), (2, 0, 5))
    cases.append(('general_tetra', A, C))
    progress.write_text(json.dumps({'status': 'RUNNING', 'completed': []}), encoding='utf-8')
    for name, A, C in cases:
        start = time.perf_counter()
        boundary, counts = audit(name, A, C)
        row = dict(name=name, counts=counts, pairs=len(boundary.model.parts_a)*len(boundary.model.parts_b),
                   candidate_facets=boundary.candidate_facets, arranged_with_multiplicity=boundary.arranged_patches,
                   elapsed_seconds=time.perf_counter()-start, mismatches=0, skipped=0)
        rows.append(row)
        progress.write_text(json.dumps({'status': 'RUNNING', 'completed': rows}, indent=2), encoding='utf-8')
        print(json.dumps(row), flush=True)
    result = {'status': 'COMPLETE', 'families': rows,
              'total_probe_checks': sum(sum(row['counts'][k] for k in ('vertex', 'edge', 'face', 'side')) for row in rows),
              'mismatches': 0, 'skipped': 0,
              'scope': 'complete pair-facet plane arrangement; closed local cover atomic overlay; finite families only',
              'source_sha256': hashes}
    assert fingerprints() == hashes, 'source changed during complete scan; invalidate and rerun'
    destination.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    progress.write_text(json.dumps({'status': 'COMPLETE', 'completed': rows}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    mutations() if '--mutations' in sys.argv else main()
