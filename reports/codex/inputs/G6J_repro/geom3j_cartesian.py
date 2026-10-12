"""Independent Cartesian-union Fraction audit; does not call production oracle.
Exact rational rotations/large shifts preserve these interval facts; not random proof.
"""
import sys,json,itertools,time
from pathlib import Path
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron,polyhedra_overlap,point_in_polyhedron,brute_feature_distance
from eab.kernel3d.g03_surface_oracle import separated_distance
from eab.margin import body_distance
FACE=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
CORNER=list(itertools.product((0,1),repeat=3))
def cube(lo,hi):
 x,y,z=lo;X,Y,Z=hi
 return [(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]
def mesh(cells):
 # Outward voxel square boundary, only removing exact duplicate interior faces.
 records={};verts=[];ids={}
 for lo,hi in cells:
  vs=cube(lo,hi)
  for face in FACE:
   points=tuple(vs[i] for i in face);key=frozenset(points)
   if key in records:del records[key]
   else:records[key]=points
 faces=[]
 for points in records.values():
  idx=[]
  for pt in points:
   if pt not in ids:ids[pt]=len(verts);verts.append(pt)
   idx.append(ids[pt])
  faces.append(tuple(idx))
 return Polyhedron(verts,faces)
def state(a,b):
 gap=max(max(a[0][i]-b[1][i],b[0][i]-a[1][i]) for i in range(3))
 return -1 if gap>0 else (0 if gap==0 else 1)
def distance2(a,b):
 return sum(max(F(0),a[0][i]-b[1][i],b[0][i]-a[1][i])**2 for i in range(3))
R=((F(-10,15),F(2,15),F(11,15)),(F(10,15),F(-5,15),F(10,15)),(F(5,15),F(14,15),F(2,15)))
assert all(sum(R[i][k]*R[j][k] for k in range(3))==int(i==j) for i in range(3) for j in range(3))
def xf(P,s,shift,rot):
 return Polyhedron([tuple(F(shift[i])+s*(sum(R[i][j]*p[j] for j in range(3)) if rot else p[i]) for i in range(3)) for p in P.verts],list(P.faces))
shapes={'L':[(x,y,0) for x in range(3) for y in range(3) if x==0 or y==0],
'U':[(x,y,0) for x in range(3) for y in range(3) if x in (0,2) or y==0],
'separated':[(0,0,0),(4,0,0)]}
results=[];count=0;start=time.perf_counter()
for name,voxels in shapes.items():
 cells=[(tuple(map(F,p)),tuple(F(c+1) for c in p)) for p in voxels]
 B=mesh(cells)
 cases=[(F(x,2),F(y,2),F(z,2)) for x,y,z in itertools.product((-1,0,1,3,5,7),(0,1,3,5),(-1,1,3))]
 # Micro classification probes straddle an exact x face, no implicit band.
 cases += [(F(3)+sgn*F(2)**-80,F(1,4),F(1,4)) for sgn in (-1,0,1)]
 for s,shift,rot in ((F(1),(0,0,0),False),(F(1,2**30),(10**8,-2*10**8,3*10**8),True),(F(2**30),(0,0,0),True)):
  b=xf(B,s,shift,rot)
  assert b.manifold_issues(0)==[]
  for q in cases:
   half=F(1,8); a_cell=(tuple(c-half for c in q),tuple(c+half for c in q))
   A=mesh([a_cell]);a=xf(A,s,shift,rot)
   want=max(state(a_cell,cell) for cell in cells)
   got=polyhedra_overlap(a,b)
   assert got==want,('overlap',name,q,s,shift,rot,want,got)
   # Point membership at q: exact Cartesian union, boundary handled separately.
   point_cell=(q,q)
   vals=[-1 if any(q[i]<cell[0][i] or q[i]>cell[1][i] for i in range(3)) else
         (1 if all(cell[0][i]<q[i]<cell[1][i] for i in range(3)) else 0) for cell in cells]
   # Union interior at shared voxel faces is not simply max(open cube states);
   # choose only points avoiding every grid plane for this oracle.
   if all(v.denominator!=1 for v in q):
    world=xf(Polyhedron([q],[]),s,shift,rot).verts[0]
    assert point_in_polyhedron(world,b)==max(vals),('point',name,q)
   if want==-1:
    d2=min(distance2(a_cell,c) for c in cells)*s*s
    truth=brute_feature_distance(a,b,squared=True)
    oracle=separated_distance(a.verts,a.faces,b.verts,b.faces,squared=True)
    assert truth==oracle==d2,('distance',name,q,truth,oracle,d2)
    # Only bounded subset feeds potentially expensive cover enumeration.
    if count%13==0:
     d,label=body_distance(a,b,tol=0)
     # exact square bracketing supplies independent RN-even midpoint certificate.
     import math,struct
     lower=(F(math.nextafter(d,-math.inf))+F(d))/2
     upper=(F(d)+F(math.nextafter(d,math.inf)))/2
     bits=struct.unpack('>Q',struct.pack('>d',d))[0]
     assert lower*lower<=d2<=upper*upper
     assert (d2!=lower*lower and d2!=upper*upper) or bits%2==0
   count+=1
  results.append({'shape':name,'scale':str(s),'rotation':rot,'shift':shift,'cases':len(cases)})
print('CARTESIAN_FRACTION_PASS',count,'body-relation cases;',len(results),'model transforms; wall_s=',round(time.perf_counter()-start,3))
(ROOT/'review/logs/geom3j_cartesian.json').write_text(json.dumps({'cases':count,'transforms':results},indent=2),encoding='utf-8')
