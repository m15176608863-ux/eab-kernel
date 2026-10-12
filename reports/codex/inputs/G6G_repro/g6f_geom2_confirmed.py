from pathlib import Path
from fractions import Fraction as F
import sys,json,math
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d import covers as C, geom as G,g0,entrance as E
S=[(0.,0.),(1.,0.),(1.,1.),(0.,1.)]
def move(dx):return [(x+dx,y) for x,y in S]
def independent_square_state(A,B):
 # Exact axis-aligned rectangle intervals: no production primitives.
 sx=max(min(F(p[0]) for p in A)-max(F(p[0]) for p in B),min(F(p[0]) for p in B)-max(F(p[0]) for p in A))
 sy=max(min(F(p[1]) for p in A)-max(F(p[1]) for p in B),min(F(p[1]) for p in B)-max(F(p[1]) for p in A))
 return -1 if max(sx,sy)>0 else (0 if max(sx,sy)==0 else 1)
results={}
# G2D-01: actual local-cover validity path defect, not output postprocessing.
gap=2.**-44;Ao,Ai=move(1+gap),move(1-gap)
assert independent_square_state(Ao,S)==-1 and independent_square_state(Ai,S)==1
original_side,original_vv=C._ve_side,C.vv_cover
C._ve_side=lambda *a,**k:-1;C.vv_cover=lambda *a,**k:None
try:
 assert C.enumerate_covers(Ao,S,window=math.inf)==[]
 dr=g0.g0_distance_completeness(Ao,S,[(0.,0.)]);er=g0.g0_exit_completeness(Ai,S,[(0.,0.)],[(1.,0.)])
 assert dr.passed and dr.samples==0 and er.passed and er.samples==0
 results['G2D-01']={'gap':gap,'exact_states':[-1,1],'distance':{'passed':dr.passed,'samples':dr.samples,'touching':dr.touching},'exit':{'passed':er.passed,'samples':er.samples,'touching':er.touching}}
finally:C._ve_side,C.vv_cover=original_side,original_vv
# G2D-02: promised first exit is 0 while initial strict-overlap precondition holds.
A=move(1-2.**-39);truth=1-F(A[0][0]);got=g0.brute_ray_exit(A,S,(1.,0.))
assert G.polygons_overlap(A,S)==1 and independent_square_state(A,S)==1
assert got==0 and truth>0
results['G2D-02']={'true':str(truth),'true_float':float(truth),'got':got,'initial_state':1,'state_at_got':1}
# G2D-03: closed segment projection squares underflow, wrong independent oracle.
s=2.**-600;B=[(0.,0.),(s,0.),(s,s),(0.,s)];A=[(x+1.5*s,y+.5*s) for x,y in B]
assert independent_square_state(A,B)==-1
true=s/2;got=g0.brute_polygon_distance(A,B)[0];rep=g0.g0_distance_completeness(A,B,[(0.,0.)])
assert got>1.4*true and not rep.passed and rep.failures[0][1]==true
results['G2D-03']={'scale':s,'true':true,'got':got,'gate_false_red':not rep.passed,'correct_cover':rep.failures[0][1]}
# G2D-04: exact signed gap magnitude is representable, sqrt(float(square)) loses it.
r=E.shortest_exit(B,B,(s/2,0.))
assert r.kind=='exit' and r.gap==0 and true!=0
results['G2D-04']={'scale':s,'true_gap':-true,'got_gap':r.gap,'kind':r.kind,'label':r.label}
print(json.dumps(results,ensure_ascii=False,indent=2))
(ROOT/'review/notes/geom2_confirmed_outputs.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
