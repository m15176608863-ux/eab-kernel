"""Independent exact box SAT/ray oracle, not sharing eab geometry primitives.

Truth uses Fraction scalar arithmetic and projections of caller-constructed
vertices on face normals/edge crosses computed below. No eab hull, normal,
overlap, closest-point or event primitive participates in the oracle.
"""
from pathlib import Path
from fractions import Fraction as F
import sys, random, json, math, time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron,polyhedra_overlap
from eab.kernel3d.entrance3 import first_entrance3,shortest_exit3
from eab.kernel3d.interlock import escape_height_covers
from eab.margin import body_distance,inflated_membership
from eab.kernel3d.exact_sweep import contact_models

FACES=((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))
SIGNS=((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))
I=((F(1),F(0),F(0)),(F(0),F(1),F(0)),(F(0),F(0),F(1)))
Z=((F(3,5),F(4,5),F(0)),(F(-4,5),F(3,5),F(0)),(F(0),F(0),F(1)))
X=((F(1),F(0),F(0)),(F(0),F(5,13),F(12,13)),(F(0),F(-12,13),F(5,13)))
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def mul(a,q):return tuple(q*x for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def box(center,half,frame=I):
 v=[tuple(F(center[k])+sum(F(s)*F(h)*e[k] for s,h,e in zip(sign,half,frame)) for k in range(3)) for sign in SIGNS]
 return Polyhedron(v,list(FACES)),tuple(frame)
def axes(a,b):
 return [n for n in list(a)+list(b)+[cross(u,v) for u in a for v in b] if any(n)]
def state(av,bv,aa,ba):
 boundary=False
 for n in axes(aa,ba):
  x=[dot(n,p) for p in av];y=[dot(n,p) for p in bv]
  width=min(max(x),max(y))-max(min(x),min(y))
  if width<0:return -1
  boundary |= width==0
 return 0 if boundary else 1
def ray(av,bv,aa,ba,d,cap):
 lower=F(0);upper=cap
 for n in axes(aa,ba):
  x=[dot(n,p) for p in av];y=[dot(n,p) for p in bv];nd=dot(n,d)
  lo=min(y)-max(x);hi=max(y)-min(x)
  if nd==0:
   if lo>0 or hi<0:return None
  else:
   l,u=sorted((lo/nd,hi/nd));lower=max(lower,l);upper=min(upper,u)
 if lower>upper:return None
 return lower
def exit2(av,bv,aa,ba):
 candidates=[]
 for n in axes(aa,ba):
  x=[dot(n,p) for p in av];y=[dot(n,p) for p in bv]
  for depth in (max(x)-min(y),max(y)-min(x)):
   candidates.append(depth**2/dot(n,n))
 return min(candidates)
def equal_rounded_root(q,got):
 if got==0:return q==0
 g=F(got);lo=(F(math.nextafter(got,-math.inf))+g)/2;hi=(g+F(math.nextafter(got,math.inf)))/2
 return lo*lo<=q<=hi*hi

def main():
 r=random.Random(11061);rows=[];errors=[];t=time.time()
 for k in range(80):
  scale=(F(1),F(1,10**9),F(10**8),F(1,10**15))[k%4]
  origin=(F(0),F(0),F(0)) if k%3==0 else (F(10**8),F(-2*10**8),F(3*10**8))
  fa=(I,Z,X)[k%3];fb=(I,Z,X)[(k//3)%3]
  half=tuple(scale*F(r.randrange(1,9),4) for _ in range(3))
  centre=add(origin,tuple(scale*F(r.randrange(-16,17),4) for _ in range(3)))
  A,aa=box(centre,half,fa);B,ba=box(origin,(scale,scale*F(5,4),scale*F(3,4)),fb)
  want=state(A.verts,B.verts,aa,ba);got=polyhedra_overlap(A,B,0)
  row={'case':k,'scale':str(scale),'want_state':want,'got_state':got}
  if want!=got:errors.append(row)
  d=tuple(scale*F(r.randrange(-3,4) or 1) for _ in range(3));cap=F(8)
  if want<=0:
   expected=ray(A.verts,B.verts,aa,ba,d,cap)
   try:
    ent=first_entrance3(A,B,(0,0,0),d,tol=0,t_max=cap)
    row.update(want_t=str(expected),got_kind=ent.kind,got_t=str(ent.exact_t))
    if (expected is None and ent.kind!='none') or (expected is not None and (ent.kind!='entrance' or ent.exact_t!=expected)):errors.append(dict(row,problem='ray'))
   except Exception as e:errors.append(dict(row,problem='ray exception',error=repr(e)))
  else:
   q=exit2(A.verts,B.verts,aa,ba)
   try:
    ex=shortest_exit3(A,B,(0,0,0),tol=0)
    row.update(want_depth2=str(q),got_gap=ex.gap)
    if not equal_rounded_root(q,abs(ex.gap)):errors.append(dict(row,problem='shortest_exit'))
   except Exception as e:errors.append(dict(row,problem='exit exception',error=repr(e)))
  # Independently bound every accepted explicit-window certificate.
  w=scale*F(1,4)
  models=contact_models(A,B,w)
  verdicts=[]
  for name,ca,cb in models:
   st=state(ca.verts,cb.verts,aa,ba);verdicts.append((name,st))
   if name.startswith('core'):
    source,core=(A,ca) if name=='core_A' else (B,cb)
    assert all(dot(sub(p,q),sub(p,q))<=w*w for p,q in zip(source.verts,core.verts)),('radial thickness',name)
   elif name.startswith('shift'):
    assert all(dot(sub(p,q),sub(p,q))==w*w for p,q in zip(A.verts,ca.verts)),('axis length',name)
  if want==1:
   public=inflated_membership(A,B,delta=0,tol=0,contact_window=w)
   accepted=any(st<=0 for _,st in verdicts)
   row.update(window=str(w),window_models=verdicts,window_state=public)
   if public!=(0 if accepted else 1):errors.append(dict(row,problem='window'))
  # Vertical escape infimum for strictly overlapping convex boxes.
  if want==1 and k<25:
   z=(F(0),F(0),F(1));candidates=[]
   for n in axes(aa,ba):
    nd=dot(n,z)
    if nd:
     x=[dot(n,p) for p in A.verts];y=[dot(n,p) for p in B.verts]
     candidates.append((max(y)-min(x))/nd if nd>0 else (min(y)-max(x))/nd)
   expected=min(x for x in candidates if x>=0)
   try:
    esc=escape_height_covers(A,B,(0,0,0),tol=0)
    row.update(want_escape=str(expected),got_escape=str(esc.exact_height))
    if esc.exact_height!=expected:errors.append(dict(row,problem='escape'))
   except Exception as e:errors.append(dict(row,problem='escape exception',error=repr(e)))
  rows.append(row)
 result={'oracle':'self-authored Fraction parallelepiped SAT and exact affine ray clipping','cases':len(rows),'errors':errors,'elapsed_seconds':time.time()-t,'rows':rows}
 path=ROOT/'review/independent_box_pressure.json';path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False,indent=2))
 if errors:raise AssertionError(errors)
if __name__=='__main__':main()
