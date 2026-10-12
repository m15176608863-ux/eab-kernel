"""Mutate a production internal branch only in an isolated review copy."""
from pathlib import Path
import hashlib,shutil,subprocess,sys,json,os
ROOT=Path(__file__).resolve().parents[2]
COPY=ROOT/'review/copies/geom2_overlap_no_interior'
COPY.mkdir(parents=True,exist_ok=True)
for part in ('src','tests','fixtures','tools'):
    if not (COPY/part).exists():shutil.copytree(ROOT/part,COPY/part)
for name in ('pyproject.toml','pytest.ini','conftest.py'):
    if (ROOT/name).exists():shutil.copyfile(ROOT/name,COPY/name)
path=COPY/'src/eab/kernel2d/geom.py'
raw=(ROOT/'src/eab/kernel2d/geom.py').read_bytes()
old=b'return 1 if _interiors_overlap(A, B, t) else 0'
assert raw.count(old)==1
path.write_bytes(raw.replace(old,b'return 0  # review mutant: erase coincident-interior branch'))
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
command=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider',
         'tests/test_invariance_2d.py::test_polygons_overlap_is_invariant',
         '--basetemp='+str(COPY/'tmp')]
p=subprocess.run(command,cwd=COPY,env=env,capture_output=True,text=True,encoding='utf8',errors='replace')
(ROOT/'review/logs/g6g_geom2_migration_mutation_pytest.log').write_text(p.stdout+p.stderr,encoding='utf8')
path.write_bytes(raw);assert hashlib.sha256(path.read_bytes()).hexdigest()==hashlib.sha256(raw).hexdigest()
# Wrong overlapping identical-ring result must be caught by migrated assertion,
# not import/collection/runtime errors. This is the core migrated exact-data door.
assert p.returncode==1 and 'FAILED tests/test_invariance_2d.py::test_polygons_overlap_is_invariant' in p.stdout
assert 'assert polygons_overlap(At, Bt, 0) == truth' in p.stdout or 'assert polygons_overlap(translate(A, x), B, tau) == want' in p.stdout
out={'copy':str(COPY),'mutated_internal_branch':old.decode(),'command':command,
     'returncode':p.returncode,'pytest_last_line':p.stdout.strip().splitlines()[-1],
     'guarding_assertion':'polygons_overlap equals independent exact clipping/overlap truth or original identity state',
     'restored_sha256':hashlib.sha256(raw).hexdigest(),'result':'MIGRATED_GATE_HAS_TEETH'}
print(json.dumps(out,indent=2))
