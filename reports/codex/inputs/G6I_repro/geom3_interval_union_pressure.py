"""Own Fraction interval-products/union oracle, no production primitive in truth.
Exact rational orthogonal frames preserve distances; topology uses eight local
coordinate orthants. Production constructors are not used in the oracle.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import product
import sys,random,json,math
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import Polyhedron,polyhedra_overlap
from eab.kernel3d.entrance_topology import entrance_membership3
from eab.margin import body_distance,inflated_membership
FACES=((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))
IDX=((0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1))
I=((F(1),F(0),F(0)),(F(0),F(1),F(0)),(F(0),F(0),F(1)))
Q=((F(3,5),F(-4,5),F(0)),(F(4,5),F(3,5),F(0)),(F(0),F(0),F(1)))
def geometry(boxes,Q,s,T):
 verts=[];faces=[]
 for b in boxes:
  k=len(verts)
  for choice in IDX:
   p=tuple(s*b[i][choice[i]] for i in range(3))
   verts.append(tuple(sum(Q[i][j]*p[j] for j in range(3))+T[i] for i in range(3)))
  faces.extend(tuple(k+i for i in f) for f in FACES)
 return Polyhedron(verts,faces)
def physical(a,b):
 states=[]
 for A in a:
  for B in b:
   ds=[min(A[i][1],B[i][1])-max(A[i][0],B[i][0]) for i in range(3)]
   states.append(1 if min(ds)>0 else 0 if min(ds)==0 else -1)
 return max(states)
def distance2(a,b):
 return min(sum(max(F(0),A[i][0]-B[i][1],B[i][0]-A[i][1])**2 for i in range(3)) for A in a for B in b)
def estate(a,b):
 E=[tuple((B[i][0]-A[i][1],B[i][1]-A[i][0]) for i in range(3)) for A in a for B in b]
 def contained(x):return any(all(lo<=v<=hi for v,(lo,hi) in zip(x,box)) for box in E)
 if not contained((0,0,0)):return -1
 positive=[abs(x) for box in E for pair in box for x in pair if x]
 h=min(positive,default=F(1))/2
 return 1 if all(contained(tuple(k*h for k in sign)) for sign in product((-1,1),repeat=3)) else 0
rng=random.Random(63091);cases=[]
# Valid surfaces: each body's components are strictly disjoint on x.
for k in range(32):
 aa=[];bb=[]
 for out,n in [(aa,1+rng.randrange(2)),(bb,1+rng.randrange(2))]:
  for j in range(n):
   x=8*j+rng.randrange(-3,4)
   out.append(((F(x),F(x+2)),(F(rng.randrange(-3,3)),F(rng.randrange(3,7))),(F(-1),F(1))))
 cases.append((aa,bb))
# Minkowski-union tight-fit interior seam: A has 2 far disjoint parts;
# B one long part. Difference cells meet along x=0 and cover both sides.
cases.extend([([((-3,-1),(-1,1),(-1,1)),((1,3),(-1,1),(-1,1))],[((-1,1),(-2,2),(-2,2))])])
rows=[]
for k,(a,b) in enumerate(cases):
 a=[tuple(tuple(map(F,p)) for p in box) for box in a];b=[tuple(tuple(map(F,p)) for p in box) for box in b]
 frame=I if k%2 else Q
 scale=(F(1),F(1,10**9),F(10**8),F(1,10**100))[k%4]
 T=(F(0),F(0),F(0)) if k%3 else (F(10**8),F(-10**8),F(10**8))
 A,B=geometry(a,frame,scale,T),geometry(b,frame,scale,T)
 p=physical(a,b);e=estate(a,b);d2=distance2(a,b)*scale*scale
 got=polyhedra_overlap(A,B,0);top=entrance_membership3(A,B)
 assert got==p,(k,'physical',p,got)
 assert top==e,(k,'E topology',e,top)
 inf=inflated_membership(A,B,delta=0,tol=0)
 assert inf==e,(k,'margin E topology',e,inf)
 dist,lab=body_distance(A,B,tol=0)
 if p<0:
  # Binary64 distance squared can differ by roundoff; validate independent sqrt
  # using math.hypot of exact interval gaps for the selected minimizer.
  ds=[tuple(max(F(0),A[i][0]-B[i][1],B[i][0]-A[i][1])*scale for i in range(3)) for A in a for B in b]
  nearest=min(ds,key=lambda d:sum(x*x for x in d))
  expected=math.hypot(*(float(x) for x in nearest))
  assert dist==expected,(k,'distance',dist,expected,lab)
 else:assert dist==0,(k,dist,lab)
 rows.append(dict(case=k,physical=p,topology=e,actual_physical=got,actual_topology=top,actual_inflated=inf,distance=dist,scale=str(scale),translation=list(map(str,T))))
print(json.dumps(dict(result='PASS',cases=len(rows),oracle='independent Fraction interval-unions and rational orthogonal maps',rows=rows),indent=2))
