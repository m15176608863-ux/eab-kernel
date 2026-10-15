"""Real numeric-field mutation reds; does not edit src, tests or tools.

Run from the worktree with PYTHONDONTWRITEBYTECODE=1 python -X utf8 <this file>.
Each child patches one executed function body and calls the independent
Cartesian all-field test at scale 1 and |translation|=100000. Source-hash
tripwire tests are not invoked. Parent hashes only certify run stability.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import random
from dataclasses import asdict
from fractions import Fraction as F


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCES = ('src/eab/kernel3d/boundary.py', 'src/eab/kernel3d/global_entrance.py',
           'src/eab/kernel3d/covers3.py', 'tests/test_m3b_boundary3d_fields.py',
           'reports/codex/M3b_evidence/boundary3d_numeric_mutations.py')


def hashes():
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def parameter_fingerprints():
    """Actual public outputs, not filenames or parameters, must be distinct."""
    sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
    from eab.kernel3d import boundary as boundary_api
    from eab.kernel3d import global_entrance as global_api
    import test_m3b_boundary3d_fields as reference
    rows = []
    for translation in (0, 10**3, 10**5, 10**6):
        rng = random.Random(3109+translation)
        quaternion = tuple(rng.randrange(1, 8) for _ in range(4))
        while any(value == 0 for axis in range(3) for value in
                  reference._rotation(tuple(F(k == axis) for k in range(3)), quaternion)):
            quaternion = tuple(rng.randrange(1, 8) for _ in range(4))
        ta = (F(3*translation, 13), F(4*translation, 13), F(12*translation, 13))
        tb = tuple(ta[k]+(5, 7, -11)[k] for k in range(3))
        for exponent in (-400, 0, 400):
            scale = F(2)**exponent
            av = [reference._transform(p, scale, ta, quaternion) for p in reference._corners(reference.ALO, reference.AHI)]
            bv = [reference._transform(p, scale, tb, quaternion) for p in reference._corners(reference.BLO, reference.BHI)]
            A = reference.Polyhedron(av, list(reference.FACES))
            B = reference.Polyhedron(bv, list(reference.FACES))
            boundary = boundary_api.explicit_boundary(global_api.global_entrance(A, B))
            local = boundary_api.local_cover_candidates(A, B)
            payload = dict(planes=boundary.planes, patches=[asdict(p) for p in boundary.patches],
                           arrangement=[asdict(p) for p in boundary.arrangement], probes=boundary.probes(),
                           local=[asdict(p) for p in local],
                           clipped=[asdict(p) for p in boundary_api.clip_local_covers(boundary, local)])
            # Deliberately exclude inputs, model storage, parameter tags and
            # source paths: only the genuinely constructed output fields hash.
            digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode('utf-8')).hexdigest()
            rows.append(dict(exponent=exponent, translation_magnitude=translation,
                             quaternion=quaternion, actual_output_sha256=digest))
    assert len(rows) == len({row['actual_output_sha256'] for row in rows}) == 12, 'parameterized construction outputs must be distinct'
    return rows


def main():
    temporary = OUT/'tmp/boundary_numeric_mutations'
    temporary.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', TEMP=str(temporary), TMP=str(temporary))
    cases = (
        ('side_step_third', '_sides', 'step = min(events)/2', 'step = min(events)/3',
         'independent exact canonical-plane side points'),
        ('ee_normal_double', 'local_cover_candidates', 'exact_normal = tuple(F(x) for x in normal)',
         'exact_normal = tuple(2*F(x) for x in normal)',
         'independent every local VF/FV/EE label coordinate normal'),
    )
    before = hashes()
    rows = []
    for name, function, old, new, expected in cases:
        child = f'''import inspect, sys, textwrap
from pathlib import Path
sys.path[:0] = [str(Path.cwd()/'src'), str(Path.cwd()/'tests')]
from eab.kernel3d import boundary as B
import test_m3b_boundary3d_fields as T
source = textwrap.dedent(inspect.getsource(getattr(B, {function!r})))
assert source.count({old!r}) == 1
namespace = dict(vars(B))
exec(compile(source.replace({old!r}, {new!r}), '<internal numeric construction mutation>', 'exec'), namespace)
setattr(B, {function!r}, namespace[{function!r}])
T.test_all_boundary_fields_have_independent_cartesian_values(exponent=0, translation=100000)
'''
        result = subprocess.run([sys.executable, '-X', 'utf8', '-c', child], cwd=ROOT, env=environment,
                                capture_output=True, text=True, encoding='utf-8', errors='replace')
        log = OUT/('boundary3d_numeric_mutation_'+name+'.txt')
        log.write_text(result.stdout+result.stderr, encoding='utf-8')
        assert result.returncode != 0 and 'AssertionError: '+expected in result.stderr, (name, result.stderr)
        rows.append(dict(name=name, internal_function=function, before=old, after=new,
                         returncode=result.returncode, expected_assertion=expected,
                         log=log.relative_to(ROOT).as_posix(), source_hash_tripwire_executed=False))
        print(name+': RED at '+expected, flush=True)
    parameters = parameter_fingerprints()
    assert hashes() == before, 'source changed during mutation run; rerun whole evidence'
    (OUT/'boundary3d_numeric_mutations.json').write_text(
        json.dumps(dict(status='COMPLETE', mutations=rows, source_sha256=before,
                        parameter_outputs_distinct=True, parameter_output_count=12,
                        parameter_output_fingerprints=parameters,
                        source_unchanged_during_run=True), indent=2)+'\n', encoding='utf-8')
    print('parameter_outputs_distinct: 12/12 actual constructed-field fingerprints', flush=True)


if __name__ == '__main__':
    main()
