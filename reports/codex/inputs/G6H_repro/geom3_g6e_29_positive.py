import sys
sys.path[:0]=['src','tests']
import math, random, sys
sys.path.insert(0,'src')
from eab.kernel3d.geom3 import Polyhedron, box
from eab.kernel3d.g03 import g0_convex3
def rot(seed):
    if seed==0: return ((1,0,0),(0,1,0),(0,0,1))
    rng=random.Random(9100+seed); q=[rng.gauss(0,1) for _ in range(4)]; n=math.sqrt(sum(c*c for c in q)); w,x,y,z=(c/n for c in q)
    return ((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),(2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),(2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))
def xf(P,R,t=(0,0,0)): return Polyhedron([tuple(t[i]+sum(R[i][j]*p[j] for j in range(3)) for i in range(3)) for p in P.verts],list(P.faces))
def pair(ratio,th):
    H=ratio/2; c,s=math.cos(th),math.sin(th); A=box(center=(0,0,H+0.6),half=(0.5,0.5,0.5))
    return Polyhedron([(c*x-s*y,s*x+c*y,z) for x,y,z in A.verts],list(A.faces)), box(half=(H,H,H))
for ratio,th,r in ((1000,1e-6,7),(100,1e-7,7),(10,1e-8,3),(100,1e-7,11)):
    A,B=pair(ratio,th); R=rot(r); rep=g0_convex3(xf(A,R),xf(B,R),samples=0)
    assert rep.passed and rep.facet_symmetric_diff==[]
    assert rep.facet_ambiguous==rep.facet_local_dropped==rep.e_vertices_ambiguous==0
    print(ratio,th,r,rep.passed,[d[0] for d in rep.facet_symmetric_diff])