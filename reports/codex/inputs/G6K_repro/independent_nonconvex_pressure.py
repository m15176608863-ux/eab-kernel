"""Self-authored Cartesian union oracle for L/U prisms and box probes.

The oracle is a prescribed union of Cartesian products, transformed by an
explicit rational orthogonal frame. It does not triangulate, call eab SAT,
surface predicates, Minkowski construction, covers or event helpers.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,random,math,time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron,polyhedra_overlap
from eab.kernel3d.entrance3 import first_entrance3
from eab.kernel3d.interlock import escape_height_covers
from eab.margin import body_distance,inflated_membership
from eab.kernel3d.exact_sweep import contact_models

Z=((F(3,5),F(-4,5),F(0)),(F(4,5),F(3,5),F(0)),(F(0),F(0),F(1)))
I=((F(1),F(0),F(0)),(F(0),F(1),F(0)),(F(0),F(0),F(1)))
FACES=((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))
S=((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))
def pose(v,scale,origin,frame):
 return tuple(F(origin[k])+scale*sum(frame[k][j]*F(v[j]) for j in range(3)) for k in range(3))
def inverse(v,scale,origin,frame):
 return tuple(sum(frame[k][j]*(F(v[k])-origin[k]) for k in range(3))/scale for j in range(3))
def prism(poly):
 n=len(poly);verts=[(F(x),F(y),F(z)) for z in (-1,1) for x,y in poly]
 faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 return Polyhedron(verts,faces)
def transformed(P,scale,origin,frame):return Polyhedron([pose(p,scale,origin,frame) for p in P.verts],P.faces)
def box(center,half):return Polyhedron([tuple(F(c)+s*F(h) for c,s,h in zip(center,sign,half)) for sign in S],list(FACES))
def intervals(P,scale,origin,frame):
 p=[inverse(p,scale,origin,frame) for p in P.verts]
 return tuple((min(p[k] for p in p),max(p[k] for p in p)) for k in range(3))
def pair(a,b):
 width=[min(x[1],y[1])-max(x[0],y[0]) for x,y in zip(a,b)]
 return -1 if min(width)<0 else (0 if min(width)==0 else 1)
def state(a,bs):return max(pair(a,b) for b in bs)
def dist2(a,bs):return min(sum(max(y[0]-x[1],x[0]-y[1],F(0))**2 for x,y in zip(a,b)) for b in bs)
def ray(a,bs,d,cap):
 roots=[]
 for b in bs:
  lo=F(0);hi=cap
  for x,y,v in zip(a,b,d):
   lower,upper=y[0]-x[1],y[1]-x[0]
   if not v:
    if lower>0 or upper<0:lo,hi=1,0;break
   else:
    l,h=sorted((lower/v,upper/v));lo=max(lo,l);hi=min(hi,h)
  if lo<=hi:roots.append(lo)
 return min(roots,default=None)
def roundroot(q,g):
 if not q:return g==0
 x=F(g);l=(F(math.nextafter(g,-math.inf))+x)/2;h=(x+F(math.nextafter(g,math.inf)))/2
 return l*l<=q<=h*h
def main():
 shapes=[('L',[(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)],[((0,3),(0,1),(-1,1)),((0,1),(1,3),(-1,1))]),('U',[(0,0),(3,0),(3,3),(2,3),(2,1),(1,1),(1,3),(0,3)],[((0,3),(0,1),(-1,1)),((0,1),(1,3),(-1,1)),((2,3),(1,3),(-1,1))])]
 rng=random.Random(11062);errors=[];rows=[];started=time.time()
 for k in range(120):
  name,p,bounds=shapes[k%2];bs=[tuple((F(x),F(y)) for x,y in r) for r in bounds]
  scale=(F(1),F(1,10**9),F(10**8))[k%3]
  origin=(F(0),F(0),F(0)) if k%4==0 else (F(10**8),F(-10**8),F(10**8))
  frame=I if k%3==0 else Z
  centre=tuple(F(rng.randrange(-4,33),8) for _ in range(3));half=tuple(F(rng.randrange(1,9),8) for _ in range(3))
  a=tuple((x-h,x+h) for x,h in zip(centre,half))
  A=transformed(box(centre,half),scale,origin,frame);B=transformed(prism(p),scale,origin,frame)
  want=state(a,bs);got=polyhedra_overlap(A,B,0)
  row=dict(case=k,shape=name,scale=str(scale),want=want,got=got)
  if got!=want:errors.append(dict(row,problem='overlap'))
  if want==-1:
   q=dist2(a,bs)*scale*scale
   try:
    g,label=body_distance(A,B,tol=0)
    if not roundroot(q,g):errors.append(dict(row,problem='distance',want_squared=str(q),got_distance=g,label=label))
   except Exception as e:errors.append(dict(row,problem='distance exception',error=repr(e)))
   d0=tuple(F(rng.randrange(-2,3) or 1) for _ in range(3));d=pose(d0,scale,(0,0,0),frame);root=ray(a,bs,d0,F(8))
   try:
    ent=first_entrance3(A,B,(0,0,0),d,tol=0,t_max=8)
    row.update(want_t=str(root),got_t=str(ent.exact_t),kind=ent.kind)
    if (root is None and ent.kind!='none') or (root is not None and (ent.kind!='entrance' or ent.exact_t!=root)):errors.append(dict(row,problem='entrance'))
   except Exception as e:errors.append(dict(row,problem='entrance exception',error=repr(e)))
  if want==1:
   xy=[b for b in bs if pair(a[:2],b[:2])==1]
   h=max(b[2][1]-a[2][0] for b in xy)*scale
   try:
    esc=escape_height_covers(A,B,(0,0,0),tol=0)
    row.update(want_escape=str(h),got_escape=str(esc.exact_height))
    if h!=esc.exact_height:errors.append(dict(row,problem='escape'))
   except Exception as e:errors.append(dict(row,problem='escape exception',error=repr(e)))
   w=scale*F(1,8);cert=[]
   for label,ca,cb in contact_models(A,B,w):
    if label=='core_B':
     # A nonconvex prism kernel homothety preserves the complete prescribed
     # rectangle union; derive the factor and centre from corresponding verts.
     old=[inverse(v,scale,origin,frame) for v in B.verts];new=[inverse(v,scale,origin,frame) for v in cb.verts]
     alpha=(new[1][0]-new[0][0])/(old[1][0]-old[0][0]);c=tuple((new[0][j]-alpha*old[0][j])/(1-alpha) for j in range(3))
     cbounds=[tuple((c[j]+alpha*(lo-c[j]),c[j]+alpha*(hi-c[j])) for j,(lo,hi) in enumerate(b)) for b in bs]
    else:cbounds=bs
    ai=intervals(ca,scale,origin,frame);cert.append((label,state(ai,cbounds)))
   try:
    public=inflated_membership(A,B,delta=0,tol=0,contact_window=w)
    if public!=(0 if any(s<=0 for _,s in cert) else 1):errors.append(dict(row,problem='window',cert=cert,public=public))
   except Exception as e:errors.append(dict(row,problem='window exception',error=repr(e)))
  rows.append(row)
 result=dict(cases=len(rows),errors=errors,elapsed_seconds=time.time()-started,rows=rows)
 (ROOT/'review/independent_nonconvex_pressure.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False,indent=2))
 if errors:raise AssertionError(errors)
if __name__=='__main__':main()
