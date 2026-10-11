"""Small fixed six-sample before/after comparison; never edits source or tests."""
import sys,time,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools'),str(ROOT/'tests')]
from osteomorphic import interlocking_pair
from eab.kernel3d.g03 import g0_distance_completeness3
from eab.kernel3d import exact_geom as G
from test_e5b_triangle_near import _full_feature_reference
A,B=interlocking_pair(nx=4,ny=2,amp=.25)
deployed=G._triangles_near
rows=[]
try:
    for name,fun in [('old_full_feature',_full_feature_reference),('deployed_exact_plane_bound',deployed),('old_full_feature_repeat',_full_feature_reference),('deployed_exact_plane_bound_repeat',deployed)]:
        G._triangles_near=fun
        start=time.perf_counter()
        result=g0_distance_completeness3(A,B,radius=.35,samples=6,seed=0,atol=1e-9)
        rows.append(dict(mode=name,seconds=time.perf_counter()-start,samples=result.samples,skipped_intersecting=result.skipped_intersecting,worst_abs_error=result.worst_abs_error,failures=result.failures))
finally:
    G._triangles_near=deployed
assert len({(r['samples'],r['skipped_intersecting'],r['worst_abs_error'],str(r['failures'])) for r in rows})==1
manifest={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('src/eab/kernel3d/exact_geom.py','tests/test_e5b_triangle_near.py')}
result={'rows':rows,'frozen_sha256':manifest,'note':'Fixed six-sample microprobe only; concurrent diagnostic full-suite activity means this is not an isolated full-suite performance claim.'}
Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
