"""First exit of a moving square grazing the reflex corner of an L ring."""
from pathlib import Path
from fractions import Fraction as F
import json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d import g0,covers

# B is the disjoint-interior union of bottom and left arms; the exact
# rectangular cell oracle uses only coordinate inequalities, not production
# winding, events, triangulation, normal cones, or G0 primitives.
B=[(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)]
A=[(F(1,2),F(3,2)),(1,F(3,2)),(1,2),(F(1,2),2)]
cells=[(0,3,0,1),(0,1,1,3)]
def exact_state(t,transverse=0):
    ax0,ax1=F(1,2)+t+transverse,F(1)+t+transverse
    ay0,ay1=F(3,2)-t+transverse,F(2)-t+transverse
    overlaps=[(min(ax1,x1)-max(ax0,x0),min(ay1,y1)-max(ay0,y0))
              for x0,x1,y0,y1 in cells]
    return 1 if any(dx>0 and dy>0 for dx,dy in overlaps) else (0 if any(dx>=0 and dy>=0 for dx,dy in overlaps) else -1)

truth=F(1,2)
probes=[F(0),truth-F(1,1000),truth,truth+F(1,1000),F(2)]
assert [exact_state(t) for t in probes]==[1,1,0,1,0]
got=g0.brute_ray_exit(A,B,(1,-1))
assert got==F(2) and got!=truth
# A genuine topological E boundary needs off-ray separation, not just a zero
# body-interior intersection at one time (a filled Minkowski seam would not do).
# For every eps>0 here, min(A.x)=min(A.y)=1+eps, so neither the bottom nor left
# B cell intersects A. This proves the t=1/2 event really is on boundary E.
epsilon_probes=[F(1,100),F(1,1000),F(1,2**50)]
assert all(exact_state(truth,e)==-1 for e in epsilon_probes)
baseline=g0.g0_exit_completeness(A,B,[(0,0)],[(1,-1)])

# Defect is injected inside the cone-validity path, before cover construction.
# It removes all facets specifically at the first boundary event and not at the
# incorrectly selected later boundary event. No output is patched or extended.
saved_side,saved_vv=covers._ve_side,covers.vv_cover
def invalid_at_earlier_boundary(P,ia,Q,jb,*args,**kwargs):
    if min(x for x,y in P)==1 or min(x for x,y in Q)==1:return -1
    return saved_side(P,ia,Q,jb,*args,**kwargs)
def vv_invalid_at_earlier_boundary(P,ia,Q,jb,*args,**kwargs):
    if min(x for x,y in P)==1 or min(x for x,y in Q)==1:return None
    return saved_vv(P,ia,Q,jb,*args,**kwargs)
covers._ve_side,covers.vv_cover=invalid_at_earlier_boundary,vv_invalid_at_earlier_boundary
try:
    actual_first=[(x+truth,y-truth) for x,y in A]
    assert covers.enumerate_covers(actual_first,B,window=float('inf'))==[]
    mutant=g0.g0_exit_completeness(A,B,[(0,0)],[(1,-1)])
    assert mutant.samples==1 and mutant.passed
finally:
    covers._ve_side,covers.vv_cover=saved_side,saved_vv
out={'expected_first_exit':str(truth),'actual_return':str(got),
     'independent_states':[{ 't':str(t),'state':exact_state(t)} for t in probes],
     'topological_boundary_certificate':'for every eps>0: A translated by (1/2+eps,-1/2+eps) has min(x)=min(y)=1+eps, strictly disjoint from both B rectangles',
     'transverse_probes':[{'eps':str(e),'state':exact_state(truth,e)} for e in epsilon_probes],
     'baseline_gate':{'samples':baseline.samples,'passed':baseline.passed},
     'internal_cone_mutant':{'first_boundary_covers':0,'samples':mutant.samples,'passed':mutant.passed}}
print(json.dumps(out,indent=2))
