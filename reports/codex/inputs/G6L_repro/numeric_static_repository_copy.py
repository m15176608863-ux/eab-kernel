from pathlib import Path
import shutil,hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('gate',ROOT/'tools/check_exact_construction.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
COPY=ROOT/'review/copies/numeric_static_map'
COPY.mkdir(parents=True,exist_ok=True)
for folder in ('src','tests'):
 for source in (ROOT/folder).rglob('*'):
  if source.is_file() and source.suffix=='.py':
   dest=COPY/source.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes())
source=ROOT/'src/eab/kernel3d/covers3.py';baseline=hashlib.sha256(source.read_bytes()).hexdigest();dest=COPY/source.relative_to(ROOT);data=dest.read_bytes();old=b'return norm_rational(p), noise';new=b'return tuple(map(norm_rational, [vector_rational(p, allow_underflow=True)]))[0], noise';assert data.count(old)==1;dest.write_bytes(data.replace(old,new))
issues=g.scan_repository(COPY)
assert issues==[],issues
assert hashlib.sha256(source.read_bytes()).hexdigest()==baseline
print(json.dumps({'whole_repository_static_scan_copy':str(COPY),'gate_issues':issues,'python_file_count':sum(1 for folder in ('src','tests') for f in (COPY/folder).rglob('*.py')),'changed_copy_file':str(dest.relative_to(COPY)),'original_tracked_source_unchanged':True},indent=2))
