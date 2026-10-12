"""New independent tetrahedral SAT/ray oracle; raw Fraction projection only.
The tetrahedra are affine images of known tetrahedra; no tested hull, normals,
planes, triangulation, events or support-cone primitives define oracle truth.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
import json,random,sys,time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron,polyhedra_overlap
from eab.kernel3d.covers3 import membership_convex3
from eab.kernel3d.entrance3 import first_entrance3
FACE=((0,2,1),(0,1,3),(0,3,2),(1,2,3))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def rows(a,b):
 axes=[cross(sub(p[j],p[i]),sub(p[k],p[i])) for p in (a,b) for i,j,k in FACE]
 axes += [cross(sub(a[j],a[i]),sub(b[l],b[k])) for i,j in combinations(range(4),2) for k,l in combinations(range(4),2)]
 return [(n,min(dot(n,p) for p in b)-max(dot(n,p) for p in a),max(dot(n,p) for p in b)-min(dot(n,p) for p in a)) for n in axes if any(n)]
def state(data,x=(0,0,0)):
 values=[(lo,dot(n,x),hi) for n,lo,hi in data]
 return -1 if any(v<lo or v>hi for lo,v,hi in values) else 0 if any(v in (lo,hi) for lo,v,hi in values) else 1
def ray(data,d,cap):
 lo,hi=F(0),cap
 for n,l,h in data:
  v=dot(n,d)
  if v:
   low,high=sorted((l/v,h/v));lo=max(lo,low);hi=min(hi,high)
  elif l>0 or h<0:return None
 return lo if lo<=hi else None

def main():
 rng=random.Random(120501);records=[];errors=[];start=time.perf_counter()
 for k in range(96):
  thin=(F(1),F(1,10**15),F(1,10**9))[k%3];s=(F(1),F(1,10**9),F(10**8))[k%3];o=(F(10**8),F(-10**8),F(10**8)) if k%4 else (F(0),)*3
  base=[(F(0),F(0),F(0)),(F(2),F(0),F(0)),(F(0),F(3),F(0)),(F(0),F(0),thin)]
  def motion(p,which):
   x,y,z=p
   if which:out=((3*x-4*y)/5,(4*x+3*y)/5,z)
   else:out=(x+z/3,y+x/7,z)
   return tuple(o[j]+s*out[j] for j in range(3))
  a=[motion(p,0) for p in base];shift=tuple(s*F(rng.randrange(-24,25),8)*(thin if j==2 else 1) for j in range(3));b=[tuple(motion(p,1)[j]+shift[j] for j in range(3)) for p in base]
  data=rows(a,b);want=state(data);A,B=Polyhedron(a,FACE),Polyhedron(b,FACE);row=dict(case=k,thin=str(thin),scale=str(s),want=want)
  try:
   g=polyhedra_overlap(A,B,0);m=membership_convex3(A,B,(0,0,0),0);row.update(overlap=g,membership=m)
   if (g,m)!=(want,want):errors.append(dict(row,problem='state'))
   if want==-1:
    d=(s*F(rng.randrange(-2,3) or 1),s*F(rng.randrange(-2,3) or 1),s*thin*F(rng.randrange(-2,3) or 1));root=ray(data,d,F(8));ent=first_entrance3(A,B,(0,0,0),d,tol=0,t_max=8);row.update(want_t=str(root),got_t=str(ent.exact_t),kind=ent.kind)
    if (root is None and ent.kind!='none') or root is not None and (ent.kind!='entrance' or ent.exact_t!=root):errors.append(dict(row,problem='entrance'))
  except Exception as e:errors.append(dict(row,problem='exception',error=repr(e)))
  records.append(row)
 result=dict(cases=len(records),errors=errors,elapsed_seconds=time.perf_counter()-start,rows=records);(ROOT/'review/geometry/tetra_pressure.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False,indent=2))
 if errors:raise AssertionError(errors)
if __name__=='__main__':main()
