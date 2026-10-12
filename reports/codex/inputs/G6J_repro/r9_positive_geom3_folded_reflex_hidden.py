"""Independent Fraction folded-top convexity/reflex counterexample.
Declared projected-ear surface of the top source ring (4,5,6,7) is the
union of triangles (7,4,5) and (5,6,7). The solid in local coordinates is
0<=x,y<=1 and 0<=z<=1+h*max(0,x+y-1). With h>0, endpoints
v4=(0,0,1), v6=(1,1,1+h) are in the solid but their midpoint
(.5,.5,1+h/2) is outside: the surface height at x+y=1 is exactly 1.
This is an explicit convexity-definition violation; no tested normal, hull,
triangulator, membership or cone primitive enters that oracle. Source rings
form one closed embedded outward-oriented surface, not an invalid input.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,math
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import Polyhedron,exact_surface,point_in_polyhedron
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
I=((1,0,0),(0,1,0),(0,0,1))
Q=((F(3,5),F(-4,5),0),(F(4,5),F(3,5),0),(0,0,1))
rows=[]
for h in (F(1,2),F(1,2**80)):
 for scale in (F(1),F(1,2**30),F(2**30)):
  for translation in ((0,0,0),(10**8,-2*10**8,3*10**8)):
   for R in (I,Q):
    raw=[(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1+h),(0,1,1)]
    midpoint=(F(1,2),F(1,2),1+h/2)
    def in_solid(p):
     x,y,z=p
     return 0<=x<=1 and 0<=y<=1 and 0<=z<=1+h*max(F(0),x+y-1)
    assert in_solid(raw[4]) and in_solid(raw[6]) and not in_solid(midpoint)
    # The oriented triangulated top has a real negative dihedral at diagonal
    # traversed 5->7 in first triangle: normals n1=(0,0,1),n2=(-h,-h,1).
    # (n1 x n2) dot ((-1,1,0)) = -2*h < 0, independently exact.
    expected_reflex_triple=-2*h
    assert expected_reflex_triple<0
    transform=lambda p:tuple(F(translation[i])+scale*sum(F(R[i][j])*F(p[j]) for j in range(3)) for i in range(3))
    P=Polyhedron(list(map(transform,raw)),faces.copy())
    got_convex=P.is_convex(tol=0);got_reflex=P.reflex_edges(tol=0)
    assert got_convex is False and (5,7) in got_reflex,(h,scale,translation,got_convex,got_reflex)
    actual=exact_surface(P)
    assert actual.manifold_issues(tol=0)==[],actual.manifold_issues(tol=0)
    assert actual.is_convex(tol=0) is False and (5,7) in actual.reflex_edges(tol=0)
    source_angle=P.dihedral_turn((4,5)); surface_angle=actual.dihedral_turn((4,5))
    assert surface_angle==math.pi/2
    assert source_angle==math.pi/2
    membership=point_in_polyhedron(transform(midpoint),P,0)
    assert membership==-1
    rows.append(dict(h=str(h),scale=str(scale),translation=translation,rotated=R==Q,
      actual_is_convex=got_convex,expected_is_convex=False,actual_reflex_edges=got_reflex,
      expected_reflex_edge=(5,7),surface_reflex_edges=actual.reflex_edges(tol=0),
      midpoint_state=membership,expected_reflex_triple=str(expected_reflex_triple),
      actual_dihedral_4_5=source_angle,expected_dihedral_4_5=math.pi/2))
print(json.dumps(dict(result='FIXED',cases=len(rows),summary='exact local convexity API silently ignores a real folded-face concave diagonal',rows=rows),indent=2))
