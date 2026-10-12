"""G6E24 original rounded input, independent integer radial-tetrahedron SAT.
Fixed outward box face interpolation is enumerated manually, not by production.
Only coordinate values and the old Motion input generator are shared.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,math,itertools
sys.path[:0]=[str(Path(__file__).resolve().parents[2]/'src'),str(Path(__file__).resolve().parents[2]/'tests')]
from eab.kernel3d.geom3 import box,polyhedra_overlap
from test_invariance_geom import Motion
TRIS=((1,0,3),(3,2,1),(7,4,5),(5,6,7),(4,0,1),(1,5,4),(5,1,2),(2,6,5),(6,2,3),(3,7,6),(7,3,0),(0,4,7))
def minus(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def model(P):
 pts=[tuple(F(c) for c in p) for p in P.verts]
 c=tuple(sum(p[k] for p in pts)/8 for k in range(3))
 assert all(dot(cross(minus(pts[j],pts[i]),minus(pts[k],pts[i])),minus(c,pts[i]))<0 for i,j,k in TRIS)
 return [(c,pts[i],pts[j],pts[k]) for i,j,k in TRIS]
def relation(A,B):
 aa,bb=model(A),model(B);den=math.lcm(*(x.denominator for tet in aa+bb for p in tet for x in p))
 def lift(seq):return [tuple(tuple(int(x*den) for x in p) for p in tet) for tet in seq]
 aa,bb=lift(aa),lift(bb)
 def payload(t):
  es=[minus(t[j],t[i]) for i,j in itertools.combinations(range(4),2)]
  ns=[cross(minus(t[j],t[i]),minus(t[k],t[i])) for i,j,k in itertools.combinations(range(4),3)]
  return t,es,ns
 aa,bb=list(map(payload,aa)),list(map(payload,bb));touch=False
 for p,ep,np in aa:
  for q,eq,nq in bb:
   axes=[*np,*nq,*(cross(e,f) for e in ep for f in eq)];border=False;sep=False
   for n in axes:
    if not any(n):continue
    x,y=[dot(n,v) for v in p],[dot(n,v) for v in q]
    overlap=min(max(x),max(y))-max(min(x),min(y))
    if overlap<0:sep=True;break
    border|=overlap==0
   if not sep and not border:return 1
   touch|=not sep
 return 0 if touch else -1
A=box(center=(0,0,1.1),half=(.25,5,.1));B=box(half=(10,.01,1))
rows=[]
for t in (1e6,4e6):
 counts={-1:0,0:0,1:0}
 for seed in range(1,41):
  M=Motion(seed,t,1.);a,b=M.poly(A),M.poly(B)
  truth=relation(a,b);actual=polyhedra_overlap(a,b)
  assert actual==truth,(t,seed,actual,truth)
  counts[truth]+=1
 rows.append(dict(translation=t,original_rounded_inputs=40,independent_exact_state_counts=counts,mismatches=0))
print(json.dumps(dict(result='PASS original G6E24 ideal-touch premise not true after vertex rounding',rows=rows),indent=2))
