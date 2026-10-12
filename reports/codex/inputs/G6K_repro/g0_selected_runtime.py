"""Selected public G0 three-vote runtime; not a new independent oracle."""
from pathlib import Path
from fractions import Fraction as F
import sys, json, dataclasses, time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(Path(__file__).parent)]
import independent_box_pressure as P
from eab.kernel3d.g03 import g0_convex3
from eab.kernel2d.g0 import g0_convex
out=[];t=time.time()
for s,shift,frame in [(F(1),(0,0,0),P.I),(F(1,10**9),(10**8,-10**8,10**8),P.Z),(F(10**8),(10**8,-10**8,10**8),P.X)]:
 A,_=P.box(shift,(s,s*F(5,4),s*F(3,4)),frame);B,_=P.box(P.add(shift,(s/4,s/8,s/2)),(s,s,s),P.I)
 r=g0_convex3(A,B,samples=30,seed=11,tol=0,band=0)
 assert not r.mismatches and not r.facet_symmetric_diff and r.hull_vertex_mismatch==0 and r.band_skipped==0
 print('3D',s,r);out.append(dict(dim=3,scale=str(s),report=dataclasses.asdict(r)))
 a=[(0,0),(2,0),(2,1),(0,1)];b=[(0,0),(1,0),(1,2),(0,2)]
 def pose(p):return (F(shift[0])+s*(F(3,5)*p[0]-F(4,5)*p[1]),F(shift[1])+s*(F(4,5)*p[0]+F(3,5)*p[1]))
 r=g0_convex(list(map(pose,a)),list(map(pose,b)),samples=40,seed=11,tol=0,band=0)
 assert not r.mismatches and not r.facet_symmetric_diff and r.hull_vertex_mismatch==0 and r.band_skipped==0
 print('2D',s,r);out.append(dict(dim=2,scale=str(s),report=dataclasses.asdict(r)))
(ROOT/'review/g0_selected_runtime.json').write_text(json.dumps(dict(seconds=time.time()-t,rows=out),ensure_ascii=False,indent=2,default=str),encoding='utf-8')
