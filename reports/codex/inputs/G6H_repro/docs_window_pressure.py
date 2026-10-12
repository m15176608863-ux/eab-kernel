"""Independent exact product-solid window pressure: no eab geometry in oracle."""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import sys,json,random
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron
from eab.kernel3d.exact_sweep import contact_models
from eab.margin import inflated_membership
FACE=((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))
SIGN=((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))
def box(c,h):return Polyhedron([tuple(c[k]+s[k]*h[k] for k in range(3)) for s in SIGN],list(FACE))
def bounds(P):
 v=[tuple(map(F,p)) for p in P.verts];b=tuple((min(p[k] for p in v),max(p[k] for p in v)) for k in range(3))
 assert set(v)==set(product(*b))
 return b
def state(A,B):
 v=[min(a[1],b[1])-max(a[0],b[0]) for a,b in zip(bounds(A),bounds(B))]
 return -1 if min(v)<0 else 0 if min(v)==0 else 1
def distance2(A,B):return sum(max(F(0),a[0]-b[1],b[0]-a[1])**2 for a,b in zip(bounds(A),bounds(B)))
def core_check(P,K,w):
 v=tuple(tuple(map(F,p)) for p in P.verts);c=tuple(sum(p[k] for p in v)/len(v) for k in range(3))
 alpha=next((F(p[k])-F(q[k]))/(F(p[k])-c[k]) for p,q in zip(P.verts,K.verts) for k in range(3) if F(p[k])!=c[k])
 assert F(0)<alpha<=F(1,2)
 assert all(tuple(c[k]+(1-alpha)*(F(p[k])-c[k]) for k in range(3))==tuple(q) for p,q in zip(P.verts,K.verts))
 assert max(sum((F(p[k])-F(q[k]))**2 for k in range(3)) for p,q in zip(P.verts,K.verts))<=w*w
 assert all(a[0]<=b[0]<b[1]<=a[1] for a,b in zip(bounds(P),bounds(K)))
 # The radial surface is a union of convex face rectangles: each norm <= largest corner.
rng=random.Random(6128);rows=[]
for i in range(96):
 s=F(2)**((-80,0,40)[i%3]);t=F(10**8) if i%4==0 else F(0)
 ac=tuple(t+F(rng.randrange(-8,9),8)*s for _ in range(3));ah=tuple(F(rng.randrange(1,17),8)*s for _ in range(3))
 bc=tuple(ac[k]+F(rng.randrange(-24,25),8)*s for k in range(3));bh=tuple(F(rng.randrange(1,17),8)*s for _ in range(3))
 A,B=box(ac,ah),box(bc,bh);w=F(rng.randrange(1,9),16)*s
 strict=state(A,B);models=contact_models(A,B,w)
 accepted=[]
 for name,a,b in models:
  value=state(a,b)
  if name=='core_A':core_check(A,a,w)
  if name=='core_B':core_check(B,b,w)
  if name.startswith('shift'):
   d=tuple(F(a.verts[0][k])-F(A.verts[0][k]) for k in range(3))
   assert sum(x*x for x in d)==w*w
   assert all(tuple(F(p[k])+d[k] for k in range(3))==tuple(q) for p,q in zip(A.verts,a.verts))
  if value<=0:accepted.append(name)
 if strict==1:expected=0 if accepted else 1
 elif strict==0:expected=0
 else:expected=0 if distance2(A,B)<=w*w else -1
 actual=inflated_membership(A,B,delta=0,contact_window=w)
 assert actual==expected,(i,strict,w,accepted,actual,expected)
 assert inflated_membership(A,B,delta=0)==strict
 rows.append({'i':i,'strict':strict,'window':str(w),'accepted':accepted,'expected':expected,'actual':actual})
print(json.dumps({'passed':len(rows),'independent_primitives':'Fraction interval products and vertex convex-norm maximum; no production oracle calls','states':{s:sum(r['strict']==s for r in rows) for s in [-1,0,1]}},ensure_ascii=False,indent=2))
(ROOT/'review/agents/docs_gates/window_pressure.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
