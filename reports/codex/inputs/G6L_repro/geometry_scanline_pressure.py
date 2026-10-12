"""WO-G6L new Fraction scanline-arrangement oracle for arbitrary simple rings.
Overlap truth uses horizontal open slabs split at all vertex and pairwise edge
crossing heights, not production triangulation, SAT, Minkowski or cover rules.
First-entrance truth enumerates raw point/line and parallel endpoint events.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
import random,json,sys,time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d.geom import polygons_overlap
from eab.kernel2d.covers import membership_convex,enumerate_covers
from eab.kernel2d.entrance import first_entrance

def edges(p):return list(zip(p,p[1:]+p[:1]))
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def sub(a,b):return (a[0]-b[0],a[1]-b[1])
def inside_segments(p,y):
 xs=sorted(a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]) for a,b in edges(p) if min(a[1],b[1])<y<max(a[1],b[1]))
 assert len(xs)%2==0
 return list(zip(xs[::2],xs[1::2]))
def on(p,a,b):return cross(sub(b,a),sub(p,a))==0 and all(min(a[i],b[i])<=p[i]<=max(a[i],b[i]) for i in (0,1))
def meet(a,b,c,d):
 u,v,w=sub(b,a),sub(d,c),sub(c,a);det=cross(u,v)
 if det:
  t,s=cross(w,v)/det,cross(w,u)/det
  return (a[0]+t*u[0],a[1]+t*u[1]) if 0<=t<=1 and 0<=s<=1 else None
 return next((p for p in (a,b) if on(p,c,d)),next((p for p in (c,d) if on(p,a,b)),None))
def state(a,b):
 heights=set(p[1] for p in a+b);touch=False
 for e,f in ((e,f) for e in edges(a) for f in edges(b)):
  p=meet(*e,*f)
  if p is not None:touch=True;heights.add(p[1])
 hs=sorted(heights)
 for lo,hi in zip(hs,hs[1:]):
  y=(lo+hi)/2
  if any(max(x,u)<min(z,v) for x,z in inside_segments(a,y) for u,v in inside_segments(b,y)):return 1
 return 0 if touch else -1

def ray(a,b,d,cap):
 times={F(0)}
 for moving,stationary,velocity in ((a,b,d),(b,a,(-d[0],-d[1]))):
  for p in moving:
   for u,v in edges(stationary):
    edge=sub(v,u);gap=cross(edge,sub(p,u));speed=cross(edge,velocity)
    if speed:times.add(-gap/speed)
    elif gap==0:
     for k in (0,1):
      if velocity[k]:times.update(((u[k]-p[k])/velocity[k],(v[k]-p[k])/velocity[k]))
 for t in sorted(x for x in times if 0<=x<=cap):
  moved=[(p[0]+t*d[0],p[1]+t*d[1]) for p in a]
  if state(moved,b)>=0:return t
 return None

def square_distance(a,b):
 def ps(p,x,y):
  e,w=sub(y,x),sub(p,x);z=e[0]*e[0]+e[1]*e[1];t=max(F(0),min(F(1),(w[0]*e[0]+w[1]*e[1])/z));q=(w[0]-t*e[0],w[1]-t*e[1]);return q[0]*q[0]+q[1]*q[1]
 return min(ps(p,x,y) for pset,eset in ((a,b),(b,a)) for p in pset for x,y in edges(eset))
def pose(p,s,o,c,d):return (o[0]+s*(c*p[0]-d*p[1]),o[1]+s*(d*p[0]+c*p[1]))
def ring(rng,n):
 bottom=[(F(k),F(rng.randrange(-20,0),8)) for k in range(n)];top=[(F(k),F(rng.randrange(1,21),8)) for k in range(n)]
 return bottom+top[::-1]
def main():
 rng=random.Random(120505);rows=[];errors=[];start=time.perf_counter()
 for k in range(240):
  a=ring(rng,3+k%5);b=ring(rng,3+(k+2)%5);offset=(F(rng.randrange(-50,51),8),F(rng.randrange(-50,51),8));a=[(p[0]+offset[0],p[1]+offset[1]) for p in a]
  s=(F(1),F(1,10**9),F(10**8),F(1,10**15))[k%4];o=(F(0),F(0)) if k%3==0 else (F(10**8),F(-10**8));c,d=(F(3,5),F(4,5)) if k%2 else (F(1),F(0))
  A=[pose(p,s,o,c,d) for p in a];B=[pose(p,s,o,c,d) for p in b];want=state(A,B);got=polygons_overlap(A,B,0);mem=membership_convex(A,B,(0,0),0)
  row=dict(case=k,want=want,got=got,membership=mem,scale=str(s),vertices=(len(A),len(B)))
  if got!=want or want!=0 and mem!=want:errors.append(dict(row,problem='membership'))
  if want==-1:
   velocity=(F(rng.randrange(-4,5) or 1),F(rng.randrange(-4,5) or 1));D=pose(velocity,s,(0,0),c,d);root=ray(A,B,D,F(8))
   try:
    ent=first_entrance(A,B,(0,0),D,tol=0,t_max=8);row.update(want_t=str(root),got_t=str(ent.t_exact),kind=ent.kind)
    if (root is None and ent.kind!='none') or root is not None and (ent.kind!='entrance' or ent.t_exact!=root):errors.append(dict(row,problem='entrance'))
    want2=square_distance(A,B);covers=enumerate_covers(A,B,window=float('inf'));values=[]
    for cover in covers:
     kind,ia,ib=cover.label()
     if kind=='VV':
      w=sub(A[ia],B[ib]);q=w[0]*w[0]+w[1]*w[1]
     elif kind in ('VE','EV'):
      vertex,poly,index=(A[ia],B,ib) if kind=='VE' else (B[ib],A,ia)
      x,y=poly[index],poly[(index+1)%len(poly)];u,w=sub(y,x),sub(vertex,x);ll=u[0]*u[0]+u[1]*u[1];z=w[0]*u[0]+w[1]*u[1]
      assert 0<=z<=ll, 'enumeration must retain only finite feature projection'
      q=(w[0]*w[0]+w[1]*w[1])-z*z/ll
     else:raise AssertionError(('unanticipated cover kind',kind))
     values.append(q)
    row['distance_exact_candidates']=len(values)
    if not values or min(values)!=want2:errors.append(dict(row,problem='distance',want_squared=str(want2),got_squared=str(min(values,default=None))))
   except Exception as e:errors.append(dict(row,problem='exception',error=repr(e)))
  rows.append(row)
 result=dict(cases=len(rows),errors=errors,elapsed_seconds=time.perf_counter()-start,rows=rows);(ROOT/'review/geometry/scanline_pressure.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False,indent=2))
 if errors:raise AssertionError(errors)
if __name__=='__main__':main()
