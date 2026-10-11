import contextlib, hashlib, inspect, json, pathlib, sys, time
sys.path.insert(0,str(pathlib.Path('src').resolve()))
from eab.kernel3d import exact_geom as E
import pytest
out=pathlib.Path('reports/codex/E5a2_evidence/a1')
source=inspect.getsource(E._surface_interior_witness)
namespace=dict(E.__dict__)
exec(source.replace('elif loc == 0:','elif False and loc == 0:'),namespace)
E._surface_interior_witness=namespace['_surface_interior_witness']
t=time.perf_counter()
with (out/'mutation_coplanar.log').open('w',encoding='utf-8') as stream, contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
    code=pytest.main(['-q','tests/test_e5a2_surface.py::test_general_surface_exact_overlap_coplanar_and_common_edge_certificates','-p','no:cacheprovider','--basetemp=reports/codex/E5a2_evidence/tmp/a1_mutation','--tb=short'])
log=(out/'mutation_coplanar.log').read_text(encoding='utf-8')
record={'mutation':'remove actual arrangement coplanar branch','changed_source':'elif loc == 0: -> elif False and loc == 0:','function_sha256':hashlib.sha256(source.encode()).hexdigest(),'pytest_exit':int(code),'seconds':time.perf_counter()-t,'target_assertion':'assert G.polyhedra_overlap(a,a)==1','target_assertion_in_log':'assert G.polyhedra_overlap(a,a)==1' in log,'source_changed_on_disk':False}
(out/'mutation_coplanar.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record))
assert code==1 and record['target_assertion_in_log']
