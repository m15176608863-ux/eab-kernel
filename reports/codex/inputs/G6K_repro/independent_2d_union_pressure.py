"""Independent Fraction rectangle-union E topology and closed-ray oracle.

No production geometry helpers participate in truth. A rectangular probe and
an explicit Cartesian union L/U polygon yield E as a union of interval products.
For a boundary point, all four infinitesimal quadrant germs decide int(E).
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,random,time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d.covers import membership_convex
from eab.kernel2d.entrance import first_entrance
from eab.kernel2d.geom import polygons_overlap
def pose(p,s,o,c,d):return (o[0]+s*(c*p[0]-d*p[1]),o[1]+s*(d*p[0]+c*p[1]))
def pair(a,b):
 w=[min(x[1],y[1])-max(x[0],y[0]) for x,y in zip(a,b)]
 return -1 if min(w)<0 else (0 if min(w)==0 else 1)
def body(a,bs):return max(pair(a,b) for b in bs)
def eboxes(a,bs):return [tuple((y[0]-x[1],y[1]-x[0]) for x,y in zip(a,b)) for b in bs]
def topology(ebs):
 if not any(all(lo<=0<=hi for lo,hi in b) for b in ebs):return -1
 for sx,sy in ((-1,-1),(-1,1),(1,-1),(1,1)):
  if not any(all(lo<=0<=hi and (hi>0 if sign>0 else lo<0) for (lo,hi),sign in zip(b,(sx,sy))) for b in ebs):return 0
 return 1
def ray(ebs,v,cap):
 roots=[]
 for b in ebs:
  lo,hi=F(0),cap
  for (l,h),d in zip(b,v):
   if not d:
    if l>0 or h<0:lo,hi=F(1),F(0);break
   else:
    low,high=sorted((l/d,h/d));lo=max(lo,low);hi=min(hi,high)
  if lo<=hi:roots.append(lo)
 return min(roots,default=None)
def main():
 shapes=[('L',[(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)],[((0,3),(0,1)),((0,1),(1,3))]),('U',[(0,0),(3,0),(3,3),(2,3),(2,1),(1,1),(1,3),(0,3)],[((0,3),(0,1)),((0,1),(1,3)),((2,3),(1,3))])]
 rng=random.Random(11063);rows=[];errors=[];start=time.time()
 for k in range(600):
  name,p,bs=shapes[k%2];bs=[tuple((F(lo),F(hi)) for lo,hi in b) for b in bs]
  center=tuple(F(rng.randrange(-8,33),8) for _ in range(2));half=tuple(F(rng.randrange(1,9),8) for _ in range(2))
  a=tuple((x-h,x+h) for x,h in zip(center,half))
  ap=[(a[0][0],a[1][0]),(a[0][1],a[1][0]),(a[0][1],a[1][1]),(a[0][0],a[1][1])]
  s=(F(1),F(1,10**9),F(10**8),F(1,10**15))[k%4];o=(F(0),F(0)) if k%3==0 else (F(10**8),F(-10**8))
  c,d=(F(1),F(0)) if k%3==0 else (F(3,5),F(4,5))
  A=[pose(q,s,o,c,d) for q in ap];B=[pose(tuple(map(F,q)),s,o,c,d) for q in p]
  want=topology(eboxes(a,bs));got=membership_convex(A,B,(0,0),tol=0)
  wbody=body(a,bs);gbody=polygons_overlap(A,B,0)
  row=dict(case=k,shape=name,scale=str(s),want_topology=want,got_topology=got,want_body=wbody,got_body=gbody)
  if want!=got or wbody!=gbody:errors.append(dict(row,problem='membership'))
  v=(F(rng.randrange(-3,4) or 1),F(rng.randrange(-3,4) or 1));world=pose(v,s,(0,0),c,d);cap=F(4)
  root=ray(eboxes(a,bs),v,cap)
  try:
   result=first_entrance(A,B,(0,0),world,tol=0,t_max=cap)
   row.update(kind=result.kind,want_t=str(root),got_t=str(result.t_exact))
   if want==1:
    if result.kind!='exit':errors.append(dict(row,problem='initial exit'))
   elif (root is None and result.kind!='none') or (root is not None and (result.kind!='entrance' or result.t_exact!=root)):errors.append(dict(row,problem='first entrance'))
  except Exception as e:errors.append(dict(row,problem='first entrance exception',error=repr(e)))
  rows.append(row)
 result=dict(cases=len(rows),errors=errors,elapsed_seconds=time.time()-start,rows=rows)
 (ROOT/'review/independent_2d_union_pressure.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False,indent=2))
 if errors:raise AssertionError(errors)
if __name__=='__main__':main()
