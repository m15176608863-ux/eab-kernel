"""WO-G6L new oracle: nested Cartesian shells, interval-products only.
Truth uses no eab vector, hull, triangle, event, surface or cover primitive.
Affine input transform has an explicit rational orthogonal inverse.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import product
import json,sys,time,math,random
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron,polyhedra_overlap,point_in_polyhedron
from eab.kernel3d.entrance3 import first_entrance3
from eab.kernel3d.interlock import escape_height_covers
from eab.margin import body_distance
R=((F(-2,3),F(2,15),F(11,15)),(F(2,3),F(-1,3),F(2,3)),(F(1,3),F(14,15),F(2,15)))
# Rows obtained from exact quaternion (1,2,3,4)/sqrt(30).
assert all(sum(R[i][k]*R[j][k] for k in range(3))==(i==j) for i in range(3) for j in range(3))
I=((F(1),F(0),F(0)),(F(0),F(1),F(0)),(F(0),F(0),F(1)))
SIGNS=((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))
FACES=((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))
def pose(v,s,o,r):return tuple(o[i]+s*sum(r[i][j]*v[j] for j in range(3)) for i in range(3))
def boxcoords(bounds):return [tuple(bounds[i][(a[i]+1)//2] for i in range(3)) for a in SIGNS]
def shape(shells,s,o,r):
 verts=[];faces=[]
 for h,sign in shells:
  begin=len(verts);verts.extend(pose(v,s,o,r) for v in boxcoords(tuple((-h,h) for _ in range(3))))
  faces.extend(tuple(begin+i for i in (f if sign==1 else tuple(reversed(f)))) for f in FACES)
 return Polyhedron(verts,faces)
def box(bounds,s,o,r):return Polyhedron([pose(v,s,o,r) for v in boxcoords(bounds)],FACES)
def slabs(outer,inner):
 return [tuple((-outer,-inner) if i==ax and side==0 else (inner,outer) if i==ax else (-outer,outer) for i in range(3)) for ax in range(3) for side in range(2)]
def pair(a,b):
 widths=[min(x[1],y[1])-max(x[0],y[0]) for x,y in zip(a,b)]
 return -1 if min(widths)<0 else 0 if min(widths)==0 else 1
def state(a,cells):return max(pair(a,b) for b in cells)
def topology(a,cells):
 e=[tuple((b[i][0]-a[i][1],b[i][1]-a[i][0]) for i in range(3)) for b in cells]
 if not any(all(lo<=0<=hi for lo,hi in b) for b in e):return -1
 return 1 if all(any(all(lo<=0<=hi and (hi>0 if sign>0 else lo<0) for (lo,hi),sign in zip(b,signs)) for b in e) for signs in product((-1,1),repeat=3)) else 0
def ray(a,cells,d,cap):
 roots=[]
 for b in cells:
  lo,hi=F(0),cap
  for i,v in enumerate(d):
   lower,upper=b[i][0]-a[i][1],b[i][1]-a[i][0]
   if v:
    l,h=sorted((lower/v,upper/v));lo=max(lo,l);hi=min(hi,h)
   elif lower>0 or upper<0:lo,hi=F(1),F(0);break
  if lo<=hi:roots.append(lo)
 return min(roots,default=None)
def dist2(a,cells):return min(sum(max(y[0]-x[1],x[0]-y[1],F(0))**2 for x,y in zip(a,b)) for b in cells)
def good_sqrt(q,g):
 if q==0:return g==0
 z=F(g);lo=(F(math.nextafter(g,-math.inf))+z)/2;hi=(F(math.nextafter(g,math.inf))+z)/2
 return lo*lo<=q<=hi*hi
def main():
 rng=random.Random(120503);rows=[];errors=[];started=time.perf_counter()
 families=[('hollow',[(F(3),1),(F(1),-1)],slabs(F(3),F(1))),('nested4',[(F(4),1),(F(3),-1),(F(2),1),(F(1),-1)],slabs(F(4),F(3))+slabs(F(2),F(1)))]
 for k in range(48):
  name,shells,cells=families[k%2];s=(F(1),F(1,10**9),F(10**8))[k%3];o=(F(10**8),F(-10**8),F(10**8)) if k%4 else (F(0),F(0),F(0));r=I if k%2 else R
  c=tuple(F(rng.randrange(-48,49),8) for _ in range(3));h=tuple(F(rng.randrange(1,17),8) for _ in range(3));a=tuple((x-y,x+y) for x,y in zip(c,h))
  # Tight fits and one-rational-step penetrations, not just generic random input.
  if k in (0,1):a=tuple((F(-1),F(1)) for _ in range(3))
  if k in (2,3):a=((F(-1)+F(1,10**15),F(1)+F(1,10**15)),(F(-1),F(1)),(F(-1),F(1)))
  A=box(a,s,o,r);B=shape(shells,s,o,r);want=state(a,cells);want_e=topology(a,cells)
  row=dict(case=k,shape=name,scale=str(s),bounds=repr(a),state=want,topology=want_e)
  try:
   got=polyhedra_overlap(A,B,0);row['got_state']=got
   if got!=want:errors.append(dict(row,problem='overlap'))
   for j,p in enumerate((c,tuple(x[0] for x in a),tuple(x[1] for x in a))):
    q=tuple((v,v) for v in p);expected=state(q,cells);point=pose(p,s,o,r);ps=point_in_polyhedron(point,B,0)
    # Degenerate point-vs-cell product yields state 0 whenever contained. Use
    # Cartesian interior directly, independent of surface query.
    expected=1 if any(all(lo<v<hi for (lo,hi),v in zip(b,p)) for b in cells) else expected
    if ps!=expected:errors.append(dict(row,problem='point',point=repr(p),want=expected,got=ps))
   if want==-1:
    distance,label=body_distance(A,B,tol=0);expected_q=dist2(a,cells)*s*s;row['distance']=distance
    if not good_sqrt(expected_q,distance):errors.append(dict(row,problem='distance',want_squared=str(expected_q),got=distance,label=label))
   direction=tuple(F(rng.randrange(-2,3) or 1) for _ in range(3));d=pose(direction,s,(F(0),)*3,r);root=ray(a,cells,direction,F(8));ent=first_entrance3(A,B,(0,0,0),d,tol=0,t_max=8)
   row.update(want_t=str(root),got_t=str(ent.exact_t),kind=ent.kind)
   if want_e==1:
    if ent.kind!='exit':errors.append(dict(row,problem='initial-int-E'))
   elif (root is None and ent.kind!='none') or (root is not None and (ent.kind!='entrance' or ent.exact_t!=root)):errors.append(dict(row,problem='first-entrance'))
  except Exception as e:errors.append(dict(row,problem='exception',error=repr(e)))
  rows.append(row);print(k,name,want,want_e,row.get('kind'),flush=True)
  result=dict(cases=len(rows),errors=errors,rows=rows,elapsed_seconds=time.perf_counter()-started);(ROOT/'review/geometry/nested_shell_pressure.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False,indent=2))
 if errors:raise AssertionError(errors)
if __name__=='__main__':main()
