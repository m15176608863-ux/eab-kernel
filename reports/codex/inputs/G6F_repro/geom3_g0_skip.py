from pathlib import Path
from fractions import Fraction as F
import sys,json,math
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d import covers3 as C,geom3 as G,g03
vertices=[(0.,0.,0.),(1.,0.,0.),(1.,1.,0.),(0.,1.,0.),(0.,0.,1.),(1.,0.,1.),(1.,1.,1.),(0.,1.,1.)]
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
gap=2.**-44
B=G.Polyhedron(vertices,faces);A=G.Polyhedron([(x+1+gap,y,z) for x,y,z in vertices],faces)
true_gap=min(F(p[0]) for p in A.verts)-max(F(p[0]) for p in B.verts)
assert true_gap>0 and G.polyhedra_overlap(A,B,0)==-1
normal=g03.g0_distance_completeness3(A,B,radius=0,samples=1)
original_vertex,original_edge=C._qvertex_contains,C._qedge_contains
C._qvertex_contains=lambda *a,**k:-1;C._qedge_contains=lambda *a,**k:-1
try:
 assert C.enumerate_covers3(A,B,window=math.inf)==[]
 r=g03.g0_distance_completeness3(A,B,radius=0,samples=1)
 assert r.passed and r.samples==0 and r.skipped_intersecting==1
 out={'true_gap':str(true_gap),'exact_state':-1,'baseline':{'passed':normal.passed,'samples':normal.samples,'skipped_intersecting':normal.skipped_intersecting},'internal_mutant':{'covers':0,'passed':r.passed,'samples':r.samples,'skipped_intersecting':r.skipped_intersecting}}
finally:C._qvertex_contains,C._qedge_contains=original_vertex,original_edge
print(json.dumps(out,ensure_ascii=False,indent=2))
(ROOT/'review/notes/geom3_g0_skip_outputs.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
