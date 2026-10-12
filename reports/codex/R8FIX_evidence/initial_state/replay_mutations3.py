"""Process-only internal topology mutations; no source is edited."""
from pathlib import Path
import hashlib
import inspect
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
import pytest
from eab.kernel3d import entrance3, entrance_topology as topology
from eab.kernel3d.geom3 import polyhedra_overlap

def hashes():
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
            ('src/eab/kernel3d/entrance_topology.py','src/eab/kernel3d/entrance3.py','src/eab/margin.py')}

mode = sys.argv[1]
before = hashes()
path = str(ROOT/'tests/test_r8fix_initial_state3.py')
args = []
if mode == 'entrance3':
    entrance3.entrance_membership3 = polyhedra_overlap
    args = [path,'-k','initial_topological']
elif mode == 'margin3':
    topology.entrance_membership3 = polyhedra_overlap
    args = [path+'::test_zero_margin_membership_classifies_tight_fit_int_E_not_body_contact']
elif mode == 'chamber3':
    original = topology._chamber_directions
    def omitted(normals):
        for d in original(normals):
            if not (d[0] > 0 and d[1] > 0):
                yield d
    topology._chamber_directions = omitted
    args = [path+'::test_3d_topology_keeps_narrow_exterior_chamber[0]']
elif mode == 'step3':
    source = inspect.getsource(topology.entrance_membership3)
    needle = 'step = min(step,h/(2*abs(slope)))'
    assert source.count(needle) == 1
    namespace = dict(vars(topology))
    exec(source.replace(needle,'step = F(1)'),namespace)
    topology.entrance_membership3 = namespace['entrance_membership3']
    entrance3.entrance_membership3 = namespace['entrance_membership3']
    args = [path+'::test_3d_tight_fit_initial_topological_interior_uses_exit[False-offset0-scale0]']
else:
    raise ValueError(mode)
code = pytest.main(['-q','-p','no:cacheprovider',*args,
                   '--basetemp='+str(ROOT/'reports/codex/R8FIX_evidence/tmp'/('mut_'+mode))])
after = hashes()
assert before == after
(Path(__file__).parent/('mutation_'+mode+'.json')).write_text(
    json.dumps(dict(mode=mode,pytest_exit_code=code,source_sha_before=before,source_sha_after=after),indent=2)+'\n',encoding='utf-8')
raise SystemExit(code)
