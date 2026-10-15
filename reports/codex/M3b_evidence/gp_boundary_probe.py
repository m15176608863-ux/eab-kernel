"""Independent exact sufficient-GP supplement; not part of the 6733 scan.

Run: PYTHONDONTWRITEBYTECODE=1 python -X utf8
     reports/codex/M3b_evidence/gp_boundary_probe.py

GP oracle imports only Fraction/itertools/random and the elementary operations
below.  No production normal, cross, dot, determinant or predicate constructs
its expected values.  The frozen boundary audit retains its separate original-
surface and planar atomic-overlay oracles.  Production Polyhedron is only an
input container.  Searching for an input is not dropping any audit probe.
"""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import hashlib
import importlib.util
import json
import random
import sys
import time


ROOT = Path(__file__).resolve().parents[3]
DEST = Path(__file__).with_suffix('.json')
SEED = 314159265
EDGES = tuple(combinations(range(4), 2))
FACES = tuple(combinations(range(4), 3))


def subtract(a, b):
    return tuple(F(a[k])-F(b[k]) for k in range(3))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def dot(a, b):
    return sum(a[k]*b[k] for k in range(3))


def determinant(vertices):
    a, b, c, d = vertices
    return dot(subtract(b, a), cross(subtract(c, a), subtract(d, a)))


def gp_checks(a, b):
    directions = [[subtract(v[j], v[i]) for i, j in EDGES] for v in (a, b)]
    normals = [[cross(subtract(v[j], v[i]), subtract(v[k], v[i]))
                for i, j, k in FACES] for v in (a, b)]
    checks = {
        'full_dimension': [dict(body=name, value=determinant(v))
                           for name, v in (('A', a), ('B', b))],
        'cross_face_face_nonparallel': [
            dict(a_face=i, b_face=j, value=cross(n, m))
            for i, n in enumerate(normals[0]) for j, m in enumerate(normals[1])],
        'a_edge_b_face_transverse': [
            dict(a_edge=i, b_face=j, value=dot(d, n))
            for i, d in enumerate(directions[0]) for j, n in enumerate(normals[1])],
        'b_edge_a_face_transverse': [
            dict(b_edge=i, a_face=j, value=dot(d, n))
            for i, d in enumerate(directions[1]) for j, n in enumerate(normals[0])],
        'cross_edge_edge_nonparallel': [
            dict(a_edge=i, b_edge=j, value=cross(d, e))
            for i, d in enumerate(directions[0]) for j, e in enumerate(directions[1])],
    }
    for rows in checks.values():
        for row in rows:
            value = row['value']
            row['passed'] = any(value) if isinstance(value, tuple) else value != 0
    return checks


def source_hashes():
    names = sorted(str(path.relative_to(ROOT)).replace('\\', '/')
                   for path in (ROOT/'src/eab').rglob('*.py'))
    names += ['tests/test_m3b_boundary3d.py', 'tests/test_m3_global3d.py',
              'tools/m3b_boundary3d_evidence.py',
              str(Path(__file__).relative_to(ROOT)).replace('\\', '/')]
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            for name in names}


def main():
    start = time.perf_counter()
    before = source_hashes()
    rng = random.Random(SEED)
    for attempts in range(1, 10001):
        a, b = [tuple(tuple(F(rng.randint(-5, 5)) for k in range(3))
                      for i in range(4)) for body in range(2)]
        checks = gp_checks(a, b)
        if all(row['passed'] for rows in checks.values() for row in rows):
            break
    else:
        raise AssertionError('deterministic GP input search exhausted')
    assert {k: len(v) for k, v in checks.items()} == {
        'full_dimension': 2, 'cross_face_face_nonparallel': 16,
        'a_edge_b_face_transverse': 24, 'b_edge_a_face_transverse': 24,
        'cross_edge_edge_nonparallel': 36,
    }, 'all sufficient GP conditions enumerated, without exclusions'
    spec = importlib.util.spec_from_file_location(
        'frozen_boundary_evidence', ROOT/'tools/m3b_boundary3d_evidence.py')
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    for name, value in frozen.fingerprints().items():
        assert before[name] == value, 'source changed before audit import'

    def make_tetra(vertices):
        faces = [(0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)]
        if determinant(vertices) < 0:
            faces = [tuple(reversed(face)) for face in faces]
        # A full-dimensional tetrahedron has exactly these four outward faces.
        for i, j, k in faces:
            opposite = next(q for q in range(4) if q not in (i, j, k))
            normal = cross(subtract(vertices[j], vertices[i]),
                           subtract(vertices[k], vertices[i]))
            assert dot(normal, subtract(vertices[opposite], vertices[i])) < 0
        return frozen.geom3.Polyhedron(list(vertices), faces)

    pa, pb = make_tetra(a), make_tetra(b)
    boundary, counts = frozen.audit('independently_certified_GP_tetra', pa, pb)
    assert all(counts[k] > 0 for k in ('vertex', 'edge', 'face', 'side', 'local_atomic'))
    after = source_hashes()
    assert before == after, 'source changed during supplement; invalidate and rerun'
    result = {
        'status': 'COMPLETE',
        'scope': 'separate exact sufficient-GP supplement; not merged into original 6733-probe scan',
        'input_search': {'seed': SEED, 'attempts': attempts,
                         'integer_range': [-5, 5],
                         'note': 'input selection only; every probe of selected pair is audited'},
        'inputs': {'A': {'verts': pa.verts, 'faces': pa.faces},
                   'B': {'verts': pb.verts, 'faces': pb.faces}},
        'gp_feature_indexing': {'edges': EDGES, 'faces': FACES},
        'gp_conditions': {name: {'count': len(rows),
                                'passed': sum(row['passed'] for row in rows),
                                'exact_witnesses': rows}
                          for name, rows in checks.items()},
        'gp_total_conditions': sum(len(rows) for rows in checks.values()),
        'counts': counts,
        'total_probe_checks': sum(counts[k] for k in ('vertex', 'edge', 'face', 'side')),
        'pairs': len(boundary.model.parts_a)*len(boundary.model.parts_b),
        'candidate_facets': boundary.candidate_facets,
        'arranged_with_multiplicity': boundary.arranged_patches,
        'mismatches': 0, 'skipped': 0,
        'source_sha256_before': before, 'source_sha256_after': after,
        'source_unchanged': True,
        'oracle_imports': {
            'gp': ['fractions.Fraction', 'itertools.combinations', 'random.Random (input selection only)'],
            'audit_driver': 'tools/m3b_boundary3d_evidence.py:audit imported from tests/test_m3b_boundary3d.py',
            'membership': 'geom3.polyhedra_overlap -> exact_geom; does not import boundary/global_entrance',
            'local_atomic': 'oracle_cover_union uses self-held Fraction 2D determinant/interpolation/membership',
        },
        'elapsed_seconds': time.perf_counter()-start,
        'limitations': 'one finite GP pair; not a universal proof or G6 sign-off',
    }
    DEST.write_text(json.dumps(result, indent=2, default=str)+'\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('status', 'gp_total_conditions', 'counts',
                       'total_probe_checks', 'mismatches', 'skipped', 'elapsed_seconds')}))


if __name__ == '__main__':
    main()
