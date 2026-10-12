import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
import math, sys
sys.path.insert(0,'src'); sys.path.insert(0,'tests')
from eab.kernel3d.geom3 import Polyhedron, box, convex_hull_3d, merge_coplanar, sub, add, mul, polyhedra_overlap
from eab.kernel3d.covers3 import local_facets3, membership_convex3, facet_gap3
from eab.kernel3d.g03 import g0_convex3
from test_invariance_geom import Motion
e, yaw = 1e-6, 1e-3
pts=[(x,y,z) for x in (0.,1.) for y in (0.,1.) for z in (0.,1.)]; pts.remove((1.,1.,0.)); pts+=[(1-e,1.,0.),(1.,1-e,0.),(1.,1.,e)]
A0=merge_coplanar(convex_hull_3d(pts)); c,s=math.cos(yaw),math.sin(yaw)
A0=Polyhedron([(0.5+c*(x-0.5)-s*(y-0.5),0.5+s*(x-0.5)+c*(y-0.5),z+1.1) for x,y,z in A0.verts],list(A0.faces))
B0=box(center=(0.5,0.5,0.5),half=(0.5,0.5,0.5)); bad=('EE',('edge',1,9),('edge',0,3))
for rot,T in ((0,0.0),(0,1e5),(11,1e5)):
    M=Motion(rot,T,1.0); A,B=M.poly(A0),M.poly(B0); F=local_facets3(A,B,1e-12)
    diffs=[sub(b,a) for a in A.verts for b in B.verts]; cen=mul([sum(p[i] for p in diffs) for i in range(3)],1/len(diffs)); v=sub(B.verts[0],A.verts[4])
    print(rot,T,'false label',bad in F,'G0 passed',g0_convex3(A,B,samples=200).passed)
    for k in (1e-4,5e-4,1e-3,1.5e-3):
        x=add(v,mul(sub(cen,v),k)); print('  brute',polyhedra_overlap(A.translated(x),B,3.5e-12),'membership',membership_convex3(A,B,x,1e-7,F),'gap',facet_gap3(A,B,bad,x))