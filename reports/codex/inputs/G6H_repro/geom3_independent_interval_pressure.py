"""Independent exact orthogonal interval-product oracle for 3D stress.
Only interval endpoints and a proved rational orthogonal matrix define truth;
no production normal, hull, SAT, surface, distance or triangulation is reused.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
import sys,json,math
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
from eab.kernel3d.geom3 import Polyhedron,point_in_polyhedron,polyhedra_overlap,brute_feature_distance
from eab.kernel3d.entrance3 import first_entrance3,shortest_exit3
from eab.margin import body_distance,margin_contacts,inflated_membership
from eab.kernel3d.covers3 import membership_convex3
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
I=((F(1),F(0),F(0)),(F(0),F(1),F(0)),(F(0),F(0),F(1)))
R=((F(3,5),-F(4,5),F(0)),(F(4,5),F(3,5),F(0)),(F(0),F(0),F(1)))
S=((F(3,5),F(0),F(4,5)),(F(0),F(1),F(0)),(-F(4,5),F(0),F(3,5)))
def make(Q,T,x,y,z):
 v=[(x[0],y[0],z[0]),(x[1],y[0],z[0]),(x[1],y[1],z[0]),(x[0],y[1],z[0]),(x[0],y[0],z[1]),(x[1],y[0],z[1]),(x[1],y[1],z[1]),(x[0],y[1],z[1])]
 return Polyhedron([tuple(T+sum(Q[k][j]*p[j] for j in range(3)) for k in range(3)) for p in v],faces.copy())
rows=[]
for Q in (I,R,S):
 assert all(sum(Q[k][i]*Q[k][j] for k in range(3))==int(i==j) for i in range(3) for j in range(3))
 for scale in (F(1,10**9),F(1),F(10**9)):
  for T in (F(0),F(1000),F(10**6),F(10**8)):
   gap=scale/F(10**6)
   A=make(Q,T,(scale+gap,2*scale+gap),(scale/4,3*scale/4),(scale/4,3*scale/4))
   B=make(Q,T,(F(0),scale),(F(0),scale),(F(0),scale))
   d,lab=body_distance(A,B,tol=0)
   assert d==float(gap) and polyhedra_overlap(A,B)==-1
   assert brute_feature_distance(A,B)==float(gap)
   assert inflated_membership(A,B,delta=gap/2,tol=0)==-1
   assert inflated_membership(A,B,delta=gap,tol=0)==0
   assert inflated_membership(A,B,delta=2*gap,tol=0)==1
   contacts=margin_contacts(A,B,delta=2*gap,tol=0)
   assert contacts and min(c.exact_distance_squared for c in contacts)==gap*gap
   expected=tuple(float(Q[k][0]) for k in range(3))
   assert all(c.normal==expected for c in contacts if c.exact_distance_squared==gap*gap)
   ray=tuple(-Q[k][0] for k in range(3))
   entry=first_entrance3(A,B,(0,0,0),ray,tol=0)
   assert entry.kind=='entrance' and entry.exact_t==gap
   displacement=tuple(-(gap+scale/4)*Q[k][0] for k in range(3))
   exit=shortest_exit3(A,B,displacement,tol=0)
   assert exit.gap==-float(scale/4)
   # The origin is outside E; shifted to the exact touch slab it is boundary.
   assert membership_convex3(A,B,(0,0,0))==-1
   assert membership_convex3(A,B,tuple(-gap*Q[k][0] for k in range(3)))==0
   centre=tuple(T+sum(Q[k][j]*scale/2 for j in range(3)) for k in range(3))
   assert point_in_polyhedron(centre,B)==1
   rows.append(dict(scale=str(scale),translation=str(T),rotation=('I' if Q==I else ('Rxy' if Q==R else 'Rxz')),gap=str(gap),exact_entry=str(entry.exact_t),passed=True))
print(json.dumps(dict(result='PASS',cases=len(rows),independence='rational orthogonal interval products only',rows=rows),indent=2))
