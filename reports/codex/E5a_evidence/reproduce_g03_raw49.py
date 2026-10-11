"""Reproduce raw finding 49 only in archived initial-HEAD source copies."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / 'reports/codex/E5a_evidence'
ARCHIVE = EVIDENCE / 'tmp/pre_e5a.zip'
WORK = EVIDENCE / 'tmp/g03_raw49'
PROBE = r'''
import json
from test_g03_two_rulers import _yaw,_truncated_cube,_move,_quat,box,g0_convex3
a0=_yaw(_truncated_cube(1e-6),1e-3).translated((0.,0.,1.1))
b0=box(half=(1.,1.,.5))
r=g0_convex3(_move(a0,_quat(7),(600.,-480.,640.)),_move(b0,_quat(7),(600.,-480.,640.)),samples=12,seed=5)
print(json.dumps({k:getattr(r,k) for k in ('passed','facet_local','facet_global','facet_degenerate','facet_ambiguous','facet_local_dropped','e_vertices_ambiguous','hull_vertex_mismatch')}))
'''
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
results = {}
log = []
with ZipFile(ARCHIVE) as archive:
    original = archive.read('src/eab/kernel3d/g03.py')
    for variant in ('baseline', 'width400_mutant'):
        target = WORK / variant
        for entry in archive.namelist():
            if entry.startswith('src/') or entry == 'tests/test_g03_two_rulers.py':
                dest = target / entry
                assert dest.resolve().is_relative_to(WORK.resolve())
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(archive.read(entry))
        source = target / 'src/eab/kernel3d/g03.py'
        if variant == 'width400_mutant':
            old = b'low = [h for h in miss_h if _vertex_height(hull, h, max(tol, fl / L)) <= 4.0 * ptol]'
            new = old.replace(b'4.0 * ptol', b'400.0 * ptol')
            assert original.count(old) == 1
            source.write_bytes(original.replace(old,new))
        env['PYTHONPATH'] = os.pathsep.join((str(target/'src'),str(target/'tests')))
        start = time.perf_counter()
        proc = subprocess.run([sys.executable,'-X','utf8','-c',PROBE],cwd=target,env=env,text=True,capture_output=True,encoding='utf-8')
        log.append(f'== {variant} probe ==\n{proc.stdout}{proc.stderr}')
        assert proc.returncode == 0, proc.stderr
        counts = json.loads(proc.stdout.strip().splitlines()[-1])
        xml = EVIDENCE / f'g03_raw49_{variant}.xml'
        cmd = [sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider','-o',f'pythonpath={(target/"src").as_posix()}', 'tests/test_g03_two_rulers.py::test_truncated_corner_cube_yawed_on_a_box_is_invariant',f'--junitxml={xml}']
        gate = subprocess.run(cmd,cwd=target,env=env,text=True,capture_output=True,encoding='utf-8')
        log.append(f'== {variant} original four-cell gate ==\n{gate.stdout}{gate.stderr}')
        results[variant] = {'g03_sha256':hashlib.sha256(source.read_bytes()).hexdigest(), 'counts':counts,'gate_exit':gate.returncode,'gate_last_line':gate.stdout.strip().splitlines()[-1], 'seconds_probe_and_gate':time.perf_counter()-start}
results.update({'finding_index_zero_based':49,'archive':str(ARCHIVE.relative_to(ROOT)),'archive_sha256':hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(), 'initial_source_g03_sha256':hashlib.sha256(original).hexdigest(), 'scope':'Only original truncated-corner four-cell gate; no claim about the historical full 2955-test group.', 'mutation':'Archived g03.py hull-side low-vertex allowance <= 4.0 * ptol changed to <= 400.0 * ptol once; production source not modified.'})
(EVIDENCE/'g03_raw49_baseline.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(EVIDENCE/'g03_raw49_baseline.log').write_text('\n'.join(log),encoding='utf-8')
print(json.dumps(results,indent=2,ensure_ascii=False))
