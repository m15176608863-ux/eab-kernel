from pathlib import Path
from fractions import Fraction as F
import sys,json,math
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d import covers as C,geom as G,g0,entrance as E
from eab.kernel3d import covers3 as C3,geom3 as G3,g03
S=[(0.,0.),(1.,0.),(1.,1.),(0.,1.)]
def move(dx):return [(x+dx,y) for x,y in S]
out={};gap=2.**-44
orig_side,orig_vv=C._ve_side,C.vv_cover
C._ve_side=lambda *a,**k:-1;C.vv_cover=lambda *a,**k:None
try:
    dr=g0.g0_distance_completeness(move(1+gap),S,[(0,0)])
    er=g0.g0_exit_completeness(move(1-gap),S,[(0,0)],[(1,0)])
    assert not dr.passed and not er.passed and dr.samples==er.samples==1
    out['G6F04_2D']={'status':'已修','distance':{'passed':dr.passed,'samples':dr.samples,'got':str(dr.failures[0][1])},'exit':{'passed':er.passed,'samples':er.samples,'got':str(er.failures[0][3])}}
finally:C._ve_side,C.vv_cover=orig_side,orig_vv
verts=[(x,y,z) for z in (0.,1.) for x,y in S]
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
B3=G3.Polyhedron(verts,faces);A3=G3.Polyhedron([(x+1+gap,y,z) for x,y,z in verts],faces)
orig_v,orig_e=C3._qvertex_contains,C3._qedge_contains
C3._qvertex_contains=lambda *a,**k:-1;C3._qedge_contains=lambda *a,**k:-1
try:
    r=g03.g0_distance_completeness3(A3,B3,radius=0,samples=1)
    assert not r.passed and r.samples==1 and r.skipped_intersecting==0
    out['G6F04_3D']={'status':'已修','passed':r.passed,'samples':r.samples,'skipped_intersecting':r.skipped_intersecting,'got':str(r.failures[0][1])}
finally:C3._qvertex_contains,C3._qedge_contains=orig_v,orig_e
A=move(1-2.**-39);want=1-F(A[0][0]);got=g0.brute_ray_exit(A,S,(1,0))
assert got==want
out['G6F05_first_exit']={'status':'原始输入已修；同类瞬时边界漏网另记','want':str(want),'got':str(got)}
s=2.**-600;B=[(0,0),(s,0),(s,s),(0,s)];A=[(x+1.5*s,y+.5*s) for x,y in B]
got=g0.brute_polygon_distance(A,B)[0];r=g0.g0_distance_completeness(A,B,[(0,0)])
assert got==s/2 and r.passed and r.samples==1
out['G6F05_distance']={'status':'已修','want':s/2,'got':got,'passed':r.passed,'samples':r.samples}
r=E.shortest_exit(B,B,(s/2,0));assert r.kind=='exit' and r.gap==-s/2
out['G6F06']={'status':'原始输入已修；VV同类漏网另记','want':-s/2,'got':r.gap,'kind':r.kind,'label':r.label,'normal':r.normal}
print(json.dumps(out,ensure_ascii=False,indent=2))
(ROOT/'review/notes/g6f_geom2_replay.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
