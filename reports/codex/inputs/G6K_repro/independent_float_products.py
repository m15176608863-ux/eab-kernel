"""Float inputs are reinterpreted by a raw Fraction Cartesian-product oracle.

Near-subnormal, huge and mixed coordinate scales; production geometry is never
called to calculate truth. Boxes are generated as exact product corners after
all input conversion, so no rounded-rotation/ideal-body ambiguity is present.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,math,time,random,itertools
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron,polyhedra_overlap
from eab.kernel3d.entrance3 import first_entrance3
from eab.margin import body_distance
from eab.kernel2d.geom import polygons_overlap
FACES=((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))
INDEX=((0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1))
def solid(bounds):return Polyhedron([tuple(bounds[k][ind[k]] for k in range(3)) for ind in INDEX],list(FACES))
def polygon(bounds):return [(bounds[0][i],bounds[1][j]) for i,j in ((0,0),(1,0),(1,1),(0,1))]
def relation(a,b):
 widths=[min(x[1],y[1])-max(x[0],y[0]) for x,y in zip(a,b)]
 return -1 if min(widths)<0 else (0 if min(widths)==0 else 1)
def roots(a,b,v,cap):
 lo=F(0);hi=cap
 for x,y,d in zip(a,b,v):
  l,h=y[0]-x[1],y[1]-x[0]
  if not d:
   if l>0 or h<0:return None
  else:
   low,high=sorted((l/d,h/d));lo=max(lo,low);hi=min(hi,high)
 return lo if lo<=hi else None
def rounded_sqrt(q,g):
 if not q:return g==0
 x=F(g);l=(F(math.nextafter(g,-math.inf))+x)/2;h=(x+F(math.nextafter(g,math.inf)))/2
 return l*l<=q<=h*h
def main():
 r=random.Random(11064);errors=[];rows=[];started=time.time()
 scales=[math.ulp(0)*16,1e-300,1e-160,1e-9,1.,1e8,1e160,1e300]
 for k in range(128):
  s=scales[k%len(scales)]
  spans=(s,s,s) if k<80 else (s,1.,1e160)
  A=tuple((float(r.randrange(-8,8))*u,float(r.randrange(8,16))*u) for u in spans)
  B=tuple((float(r.randrange(-16,8))*u,float(r.randrange(8,17))*u) for u in spans)
  # Purposeful separation/contact as well as strict overlap.
  axis=k%3
  if k%4==0:B=tuple((A[j][1],A[j][1]+4*spans[j]) if j==axis else b for j,b in enumerate(B))
  if k%4==1:B=tuple((A[j][1]+spans[j],A[j][1]+5*spans[j]) if j==axis else b for j,b in enumerate(B))
  aq=tuple(tuple(map(F,x)) for x in A);bq=tuple(tuple(map(F,x)) for x in B)
  pa,pb=solid(A),solid(B);want=relation(aq,bq);got=polyhedra_overlap(pa,pb,0)
  row=dict(case=k,scale=s,want=want,got=got)
  if got!=want:errors.append(dict(row,problem='3d overlap'))
  two_want=relation(aq[:2],bq[:2]);two_got=polygons_overlap(polygon(A),polygon(B),0)
  if two_want!=two_got:errors.append(dict(row,problem='2d overlap',want_2d=two_want,got_2d=two_got))
  if want==-1:
   q=sum(max(y[0]-x[1],x[0]-y[1],F(0))**2 for x,y in zip(aq,bq))
   try:
    distance,label=body_distance(pa,pb,tol=0)
    if not rounded_sqrt(q,distance):errors.append(dict(row,problem='distance',q=str(q),distance=distance))
   except Exception as e:errors.append(dict(row,problem='distance exception',error=repr(e)))
  if want<=0 and k<80:
   d=tuple(-float(r.randrange(1,5))*u for u in spans);root=roots(aq,bq,tuple(map(F,d)),F(8))
   try:
    ent=first_entrance3(pa,pb,(0,0,0),d,tol=0,t_max=8)
    if (root is None and ent.kind!='none') or (root is not None and (ent.kind!='entrance' or ent.exact_t!=root)):errors.append(dict(row,problem='first entrance',want_t=str(root),got_kind=ent.kind,got_t=str(ent.exact_t)))
   except Exception as e:errors.append(dict(row,problem='entrance exception',error=repr(e)))
  rows.append(row)
 result=dict(cases=len(rows),errors=errors,elapsed_seconds=time.time()-started,rows=rows)
 (ROOT/'review/independent_float_products.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False,indent=2))
 if errors:raise AssertionError(errors)
if __name__=='__main__':main()
