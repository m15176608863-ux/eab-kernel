"""WO-G6O confirmed G6O-GEOM-01: finite escape published as infinity.

Only a production function is tested. The reference is Cartesian interval
arithmetic: A=[-1/8,1/8]^2 x [0,H/2], B=[-1/4,1/4]^2 x [-1/4,H].
Along +z, strict overlap persists iff 0 <= h < H; the exact first
nonpenetrating root is H. Every input is a finite rational; all corners and
outward face rings are directly constructed, not from production geometry.
The API promises an upward finite height display or a named support-domain
error. At H=max_binary64+1, RN-even is finite but upward rounding has no finite
representation; current code publishes inf instead of rejecting.
"""
from pathlib import Path
from fractions import Fraction as Q
from itertools import product
import sys,math,json,time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron,polyhedra_overlap
from eab.kernel3d.interlock import escape_height_covers
from eab.numeric_domain import ConstructionDomainError
from eab.construction import scalar_rational
FACES=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def model(bounds):
    (x0,x1),(y0,y1),(z0,z1)=bounds
    vertices=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    assert all(lo<hi for lo,hi in bounds)
    assert set(vertices)==set(product(*bounds))
    # Six signed planes and outward ring traversal are known directly from
    # this source order. Verify closed edges independently, without eab.
    directed=[(ring[i],ring[(i+1)%4]) for ring in FACES for i in range(4)]
    assert len(set(directed))==24 and all((b,a) in directed for a,b in directed)
    return Polyhedron(vertices,list(FACES))
def interval_state(aa,bb,z):
    spans=[min(hi+z if k==2 else hi,Bhi)-max(lo+z if k==2 else lo,Blo) for k,((lo,hi),(Blo,Bhi)) in enumerate(zip(aa,bb))]
    return -1 if min(spans)<0 else (0 if min(spans)==0 else 1)
def run():
    maximum=Q(sys.float_info.max);threshold=maximum+Q(2)**970
    cases=[('max_minus_1',maximum-1),('max',maximum),('max_plus_1',maximum+1),('max_plus_2p969',maximum+Q(2)**969),('overflow_midpoint_minus_1',threshold-1),('overflow_midpoint',threshold)]
    rows=[];start=time.time()
    for name,target in cases:
        aa=((Q(-1,8),Q(1,8)),(Q(-1,8),Q(1,8)),(Q(0),target/2))
        bb=((Q(-1,4),Q(1,4)),(Q(-1,4),Q(1,4)),(Q(-1,4),target))
        a,b=model(aa),model(bb)
        assert interval_state(aa,bb,0)==1
        assert interval_state(aa,bb,target)==0
        assert interval_state(aa,bb,target-1)==1
        assert interval_state(aa,bb,target+1)==-1
        row={'case':name,'exact_root_minus_max':str(target-maximum),'exact_input_finite':True,'expected_upward_finite_or_named_error':True,'independent_initial':1,'independent_endpoint':0}
        try:row['RN_finite']=math.isfinite(scalar_rational(target))
        except ConstructionDomainError:row['RN_finite']=False
        try:
            out=escape_height_covers(a,b,(0,0,0),tol=0)
            row.update({'returned_height':repr(out.height),'height_finite':math.isfinite(out.height),'exact_height_matches_interval_root':out.exact_height==target,'nonpenetrating_state':out.nonpenetrating_state,'n_candidates':out.n_candidates,'silent_nonfinite':not math.isfinite(out.height)})
            assert out.exact_height==target and out.nonpenetrating_state==0
        except ConstructionDomainError as e:row.update({'named_exception':str(e),'silent_nonfinite':False})
        rows.append(row)
    result={'head':'03a41b5','file_line':'src/eab/kernel3d/interlock.py:308-310','rows':rows,'silent_nonfinite_count':sum(r['silent_nonfinite'] for r in rows),'seconds':round(time.time()-start,3)}
    (ROOT/'review/evidence/geometry_escape_nonfinite.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    assert not result['silent_nonfinite_count'],'finite rational escape height must not be silently published as inf; use a named support-domain failure'
if __name__=='__main__':run()
