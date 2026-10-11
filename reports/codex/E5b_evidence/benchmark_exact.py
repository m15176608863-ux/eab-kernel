"""Rerunnable E5b exact boolean/positive-certificate equivalence benchmark."""
from pathlib import Path
from fractions import Fraction as F
import hashlib
import json
import sys
import time
import types

ROOT=Path(__file__).resolve().parents[3]
EVIDENCE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'tools')]
from eab.kernel3d import exact_geom as current, geom3 as G
from test_e5b_triangle_boolean import _pairs
from test_e5a2_surface import l_block, placed
from osteomorphic import interlocking_pair

old=types.ModuleType('eab.kernel3d._e5b_baseline_exact_geom')
old.__package__='eab.kernel3d'
source=EVIDENCE/'baseline/src/eab/kernel3d/exact_geom.py'
exec(compile(source.read_text(encoding='utf-8-sig'),str(source),'exec'),old.__dict__)

def measured(call):
    start=time.perf_counter(); cpu=time.process_time(); value=call()
    return value,{'wall_seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu}

pairs=list(_pairs())
before,before_time=measured(lambda:[bool(old.triangle_intersection(a,b)) for a,b in pairs])
after,after_time=measured(lambda:[current._triangles_intersect_prepared(current._triangle_data(a),current._triangle_data(b)) for a,b in pairs])
assert before==after
rows=[dict(kind='triangle boolean',inputs=len(pairs),before=before_time,after=after_time,all_equal=True)]
a,b=interlocking_pair(nx=4,ny=2,amp=.25)
for shift in ((0.,0.,0.),(.05,0.,.025),(.05,0.,.025000000001),(.05,0.,.03),(.05,0.,.024)):
    at,bt=current.triangles(a.translated(shift)),current.triangles(b)
    for tol in (F(0),F(1e-8)):
        x,tx=measured(lambda:old._triangles_near(at,bt,tol))
        y,ty=measured(lambda:current._triangles_near(at,bt,tol))
        assert x==y
        rows.append(dict(kind='surface near',shift=shift,tol=str(tol),before=tx,after=ty,all_equal=True,state=x))
for scale,translation in ((F(1),F(0)),(F(1,1000),F(10**6)),(F(1000),F(10**5))):
    a=l_block(); b=G.box(center=(F(3,2),F(3,2),F(1,2)),half=(F(3,10),F(2),F(1,5)))
    a,b=placed(a,scale,translation),placed(b,scale,translation)
    x,tx=measured(lambda:old.surface_overlap(a,b))
    y,ty=measured(lambda:current.surface_overlap(a,b))
    assert x==y==1
    rows.append(dict(kind='surface transverse',scale=str(scale),translation=str(translation),before=tx,after=ty,all_equal=True,state=x))
result=dict(baseline_head='35667084fd2b6d3c89bd3d284534feea2d5771a5',
            baseline_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            current_sha256=hashlib.sha256(Path(current.__file__).read_bytes()).hexdigest(),
            warning='Microbenchmark; concurrent development may affect wall times. Not full-suite performance acceptance.',rows=rows)
(EVIDENCE/'optimization_benchmarks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(result,indent=2))
