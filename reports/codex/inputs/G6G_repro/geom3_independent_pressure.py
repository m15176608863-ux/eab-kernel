"""G6G new independent exact pressure, coordinate-product oracles only.
No oracle calls any eab geometry/SAT/triangulation/normal primitive. Fraction
scalar determinant, dot/cross expressions, interval products and Decimal final
root are independently written here. Production is imported only for results.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
from itertools import product
import sys,random,json,math,time
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.predicates import orient3d,cross2_sign,dot2_sign
from eab.kernel3d.geom3 import Polyhedron,point_in_polyhedron,polyhedra_overlap
from eab.kernel3d.exact_geom import polygon_locate
from eab.kernel3d.entrance3 import first_entrance3
from eab.kernel3d.interlock import escape_height_covers
from eab.kernel3d.exact_sweep import contact_models
from eab.margin import body_distance,inflated_membership
rng=random.Random(706071)
counts={}
t0=time.perf_counter()
def hit(name):counts[name]=counts.get(name,0)+1
def sign(x):return (x>0)-(x<0)
def orient(a,b,c,p):
 u=[F(b[k])-F(a[k]) for k in range(3)];v=[F(c[k])-F(a[k]) for k in range(3)];w=[F(p[k])-F(a[k]) for k in range(3)]
 return sign(u[0]*(v[1]*w[2]-v[2]*w[1])-u[1]*(v[0]*w[2]-v[2]*w[0])+u[2]*(v[0]*w[1]-v[1]*w[0]))
def scalar():
 q=F(rng.choice([-17,-7,-1,0,1,3,13]),rng.choice([1,3,7]))*F(2)**rng.choice([-1100,-1074,-1000,-600,-100,0,100,600,1000,1100])
 if rng.randrange(3)==0:
  try:return float(q)
  except OverflowError:pass
 return q
for i in range(1500):
 pts=[tuple(scalar() for _ in range(3)) for _ in range(4)]
 assert orient3d(*pts)==orient(*pts),('orient',pts);hit('orient_extreme_mixed')
for i in range(2000):
 a,b=[tuple(scalar() for _ in range(2)) for _ in range(2)]
 assert cross2_sign(a,b)==sign(F(a[0])*F(b[1])-F(a[1])*F(b[0]));hit('cross_extreme_mixed')
 assert dot2_sign(a,b)==sign(F(a[0])*F(b[0])+F(a[1])*F(b[1]));hit('dot_extreme_mixed')
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
signs=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
# R=Rz(3/5,4/5)*Rx(5/13,12/13), exact non-axis rotation.
R=((F(3,5),-F(4,13),F(48,65)),(F(4,5),F(3,13),-F(36,65)),(F(0),F(12,13),F(5,13)))
assert all(sum(R[k][i]*R[k][j] for k in range(3))==(i==j) for i in range(3) for j in range(3))
def pose(p,s,T):return tuple(F(T[k])+s*sum(R[k][j]*F(p[j]) for j in range(3)) for k in range(3))
def box(center,s,T,half=(1,1,1)):
 return Polyhedron([pose(tuple(F(center[k])+v[k]*F(half[k]) for k in range(3)),s,T) for v in signs],faces.copy())
def root(q):
 with localcontext() as c:
  c.prec=1800
  return float((Decimal(q.numerator)/Decimal(q.denominator)).sqrt())
for s,T in product((F(1,2**300),F(1),F(2**300)),((0,0,0),(10**3,-3*10**3,2*10**3),(10**8,-3*10**8,2*10**8))):
 P=box((0,0,0),s,T)
 for p,state in [((0,0,0),1),((1,0,0),0),((1+F(1,10**15),0,0),-1),((1-F(1,10**15),0,0),1)]:
  assert point_in_polyhedron(pose(p,s,T),P)==state;hit('point_product_rotation_units')
 for center,state in [((0,0,0),1),((2,0,0),0),((2+F(1,10**15),0,0),-1),((2-F(1,10**15),0,0),1)]:
  Q=box(center,s,T)
  assert polyhedra_overlap(P,Q)==state;hit('overlap_product_rotation_units')
 for center in ((3,0,0),(3,4,0),(3,4,5)):
  Q=box(center,s,T);square=s*s*sum(max(F(abs(x))-2,0)**2 for x in center)
  assert body_distance(P,Q,tol=0)[0]==root(square);hit('distance_product_rotation_units')
 d=tuple(-s*R[k][0] for k in range(3));x=tuple(4*s*R[k][0] for k in range(3))
 result=first_entrance3(P,P,x,d,tol=0,t_max=3)
 assert result.kind=='entrance' and result.exact_t==2;hit('first_entrance_product_rotation_units')
 # Polygon tests in a planar square; interval-product point-to-boundary oracle.
 poly=[pose(p,s,T) for p in ((-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0))]
 for p in ((0,0),(1,0),(F(11,10),0),(F(11,10),F(11,10)),(F(99,100),0)):
  inside=max(abs(p[0]),abs(p[1]))<1
  boundary=max(abs(p[0]),abs(p[1]))==1 and min(abs(p[0]),abs(p[1]))<=1
  d2=(s*min(1-abs(p[0]),1-abs(p[1])))**2 if inside else s*s*sum(max(abs(F(x))-1,0)**2 for x in p)
  for tol in (F(0),s/10,s/9):
   expected=0 if d2<=tol*tol else (1 if inside else -1)
   assert polygon_locate(pose((*p,0),s,T),poly,tol)==expected;hit('polygon_interval_filter_rotation_units')
 # Lift velocity projected to local coordinates=(0,12/13,5/13).
 # Unit half lengths imply earliest y separation26s/12 (before z separation).
 if s!=F(2**300):
  e=escape_height_covers(P,P,(0,0,0),tol=0)
  assert e.exact_height==F(13,6)*s;hit('escape_product_full_rotation_units')
# New window sweep verifies independent certificates on uneven anisotropic boxes.
for axis,sgn in product(range(3),(-1,1)):
 s=F(3,7);w=s/F(13);half=(F(1),F(3,2),F(5,4));T=(F(10**6),F(-3*10**6),F(7))
 # Axis-aligned constructor is separate from rotated pressure boxes.
 def aligned(c):return Polyhedron([tuple(T[k]+s*(F(c[k])+v[k]*half[k]) for k in range(3)) for v in signs],faces.copy())
 c=tuple(-sgn*(2*half[k]-w/s) if k==axis else F(0) for k in range(3))
 A,B=aligned((0,0,0)),aligned(c)
 def state(U,V):
  widths=[min(max(p[k] for p in U.verts),max(p[k] for p in V.verts))-max(min(p[k] for p in U.verts),min(p[k] for p in V.verts)) for k in range(3)]
  return -1 if min(widths)<0 else (0 if min(widths)==0 else 1)
 accepted=[name for name,U,V in contact_models(A,B,w) if state(U,V)<=0]
 assert f'shift_{axis}_{sgn}' in accepted
 # Any accepted shift exactly moves a distance w and therefore certifies PD<=w.
 for name,U,V in contact_models(A,B,w):
  if state(U,V)<=0 and name.startswith('shift'):
   disp=tuple(U.verts[0][k]-A.verts[0][k] for k in range(3));assert sum(x*x for x in disp)==w*w
 assert inflated_membership(A,B,delta=0,contact_window=w)==0;hit('independent_sixaxis_soundness_new_grid')
print(json.dumps(dict(result='PASS',counts=counts,total=sum(counts.values()),seconds=time.perf_counter()-t0),indent=2))
