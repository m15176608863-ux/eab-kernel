"""Equivalent rational rigid-motion probes preserving legacy exact boundaries."""
import sys,json
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron,box,convex_hull_3d
from eab.kernel3d.interlock import escape_height_covers
from eab.kernel3d.covers3 import enumerate_covers3
from eab.margin import margin_contacts

def rot(P,T=(0,0,0),xyonly=False):
 def apply(p):
  x,y,z=map(F,p)
  v=((3*x-4*y)/5,(4*x+3*y)/5,z) if xyonly else ((3*x-4*y)/5,(12*x+9*y-20*z)/25,(16*x+12*y+15*z)/25)
  return tuple(a+F(b) for a,b in zip(v,T))
 return Polyhedron([apply(p) for p in P.verts],list(P.faces))

def prism(prof,y0,y1):
 n=len(prof);v=[(F(x),F(y0),F(z)) for x,z in prof]+[(F(x),F(y1),F(z)) for x,z in prof]
 fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 # This profile is clockwise in x/z -> written orientation matches legacy volume correction.
 P=Polyhedron(v,fs)
 return P if P.volume()>0 else Polyhedron(v,[tuple(reversed(f)) for f in fs])
prof=[(-2,0),(2,0),(2,1),(1,1),(1,0),(-1,0),(-1,1),(-2,1)]
# Actual U uses floor z=-1 so explicit solid union is floor [-2,2]x[-1,1]x[-1,0] and two walls.
prof=[(-2,-1),(2,-1),(2,1),(1,1),(1,0),(-1,0),(-1,1),(-2,1)]
U=prism(prof,-1,1);A=box(center=(0,0,F(3,10)),half=(1,F(1,2),F(1,2)))
rows=[]
for t in [0,1000000]:
 a,u=rot(A,(F(3*t,5),F(-12*t,25),F(16*t,25)),True),rot(U,(F(3*t,5),F(-12*t,25),F(16*t,25)),True)
 r=escape_height_covers(a,u,(0,0,0));expected=F(1,5)
 rows.append(dict(id=34,t=t,expected=str(expected),exact_height=str(r.exact_height),height=r.height,kind=r.kind if hasattr(r,'kind') else None));assert r.exact_height==expected
# Fifth-round 36 endpoint case; do not confuse a rounded rigid motion with a rigid motion of binary data.
d=F(1,2**10);B=box(half=(1,1,F(1,2)));pts=[(F(0),-1-d,F(3,5)),(F(2),-1+d,F(3,5)),(F(2),1+d,F(3,5)),(F(0),1-d,F(3,5))]
A=convex_hull_3d(pts+[(x,y,F(8,5)) for x,y,_ in pts])
labels=lambda a,b:{(c.label(),c.strict) for c in enumerate_covers3(a,b,window=float('inf'),tol=0) if c.in_extent}
base=labels(A,B);am,bm=rot(A,(600000,-480000,640000)),rot(B,(600000,-480000,640000));moved=labels(am,bm)
row=dict(id=36,base_count=len(base),moved_count=len(moved),lost=sorted(map(str,base-moved)),extra=sorted(map(str,moved-base)));rows.append(row);assert base==moved
print(json.dumps(rows,indent=2));(ROOT/'review/logs/history_legacy_boundary_result.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
