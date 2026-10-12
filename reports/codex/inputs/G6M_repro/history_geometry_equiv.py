"""Rechecks legacy invariance cases against the actual given binary coordinates.
Independent integer SAT on tetrahedral centroid fans, only used for boxes.
No kernel exact helper, geometry helper or hull builder in the oracle.
"""
import sys,math,itertools,json,random
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from eab.kernel3d.geom3 import Polyhedron,box,polyhedra_overlap
from test_invariance_geom import Motion

def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def fan(P):
 v=[tuple(map(F,p)) for p in P.verts];cen=tuple(sum(p[i] for p in v)/len(v) for i in range(3));ts=[]
 for f in P.faces:
  assert len(f)==4
  for tri in [(f[3],f[0],f[1]),(f[1],f[2],f[3])]:ts.append((cen,)+tuple(v[i] for i in tri))
 return ts

def oracle(A,B):
 ta,tb=fan(A),fan(B);D=1
 for t in ta+tb:
  for p in t:
   for v in p:D=math.lcm(D,v.denominator)
 ta=[tuple(tuple(int(v*D) for v in p) for p in t) for t in ta];tb=[tuple(tuple(int(v*D) for v in p) for p in t) for t in tb]
 def data(t):
  es=[sub(t[j],t[i]) for i,j in itertools.combinations(range(4),2)]
  ns=[cross(sub(t[j],t[i]),sub(t[k],t[i])) for i,j,k in itertools.combinations(range(4),3)]
  return es,ns
 aa=[data(t) for t in ta];bb=[data(t) for t in tb];touch=False
 for a,(ae,an) in zip(ta,aa):
  for b,(be,bn) in zip(tb,bb):
   zero=False;sep=False
   for n in itertools.chain(an,bn,(cross(e,f) for e in ae for f in be)):
    if not any(n):continue
    pa=[dot(n,p) for p in a];pb=[dot(n,p) for p in b]
    gap=max(min(pa)-max(pb),min(pb)-max(pa))
    if gap>0:sep=True;break
    if gap==0:zero=True
   if not sep:
    if not zero:return 1
    touch=True
 return 0 if touch else -1

rows=[]
B=box(half=(10.0,.01,1.));A=box(center=(0.,0.,1.1),half=(.25,5.,.1))
for T in (1e6,4e6):
 for r in range(1,41):
  M=Motion(r,T,1);a,b=M.poly(A),M.poly(B);expected=oracle(a,b);got=polyhedra_overlap(a,b,0.0)
  rows.append(dict(id=24,T=T,r=r,expected=expected,got=got))
# Preserve actual exact contact under rational rotation and translation, rather than rounding an ideal contact.
def motion(P):
 def rot(p):
  x,y,z=map(F,p);return ((3*x-4*y)/5,(12*x+9*y-20*z)/25,(16*x+12*y+15*z)/25)
 return Polyhedron([tuple(v+F(t) for v,t in zip(rot(p),(600000,-480000,640000))) for p in P.verts],list(P.faces))
a,b=motion(A),motion(B);rows.append(dict(id=24,case='Fraction rigid motion',expected=oracle(a,b),got=polyhedra_overlap(a,b,0.0)))
result=dict(total=len(rows),original_state_counts={s:sum(q['expected']==s for q in rows[:-1]) for s in [-1,0,1]},mismatches=[q for q in rows if q['expected']!=q['got']],exact_motion=rows[-1]);print(json.dumps(result,indent=2));(ROOT/'review/logs/history_legacy_geom_result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');assert not result['mismatches']
