from fractions import Fraction as F
from pathlib import Path
import sys, random, math, json
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d import geom as G, covers as C, entrance as E
from eab import predicates as P

def determinant(a,b,c):
    return (F(b[0])-F(a[0]))*(F(c[1])-F(a[1]))-(F(b[1])-F(a[1]))*(F(c[0])-F(a[0]))
def sign(x):return (x>0)-(x<0)
def hull(points):
    pts=sorted(set(map(tuple,points)))
    if len(pts)<3:return pts
    cur=start=pts[0];out=[]
    while True:
        out.append(cur);nxt=next(p for p in pts if p!=cur)
        for p in pts:
            z=determinant(cur,nxt,p)
            if z<0 or z==0 and sum((F(p[k])-F(cur[k]))**2 for k in (0,1))>sum((F(nxt[k])-F(cur[k]))**2 for k in (0,1)):nxt=p
        cur=nxt
        if cur==start:return out

def state(A,B,x=(0,0)):
    A=[(F(a[0])+F(x[0]),F(a[1])+F(x[1])) for a in A];B=[tuple(map(F,b)) for b in B]
    touch=False
    for S,T in ((A,B),(B,A)):
        for j,p in enumerate(S):
            q=S[(j+1)%len(S)];n=(q[1]-p[1],p[0]-q[0])
            pa=[n[0]*a[0]+n[1]*a[1] for a in S];pb=[n[0]*b[0]+n[1]*b[1] for b in T]
            gap=max(min(pa)-max(pb),min(pb)-max(pa))
            if gap>0:return -1
            if gap==0:touch=True
    return 0 if touch else 1

def ray(A,B,x,d,tmax):
    X,D=tuple(map(F,x)),tuple(map(F,d));times={F(0)}
    for S,T,v in ((A,B,D),(B,A,(-D[0],-D[1]))):
        for p in S:
            for j,q in enumerate(T):
                r=T[(j+1)%len(T)];ex=F(r[0])-F(q[0]);ey=F(r[1])-F(q[1])
                wx=F(q[0])-F(p[0])+(-X[0] if S is A else X[0]);wy=F(q[1])-F(p[1])+(-X[1] if S is A else X[1])
                den=v[0]*ey-v[1]*ex
                if den:
                    t=(wx*ey-wy*ex)/den;s=(wx*v[1]-wy*v[0])/den
                    if t>=0 and t<=F(tmax) and 0<=s<=1:times.add(t)
    for t in sorted(times):
        if state(A,B,(X[0]+t*D[0],X[1]+t*D[1]))>=0:return t
    return None

rng=random.Random(260612061)
summary={'predicate_cases':0,'hulls':0,'member_cases':0,'ray_cases':0,'mismatches':[]}
for k in range(20000):
    es=[rng.randint(-1074,1022) for _ in range(4)]
    vals=[math.ldexp(rng.uniform(-1,1),e) for e in es]
    a=vals[:2];b=vals[2:]
    dc=F(a[0])*F(b[1])-F(a[1])*F(b[0]);dd=F(a[0])*F(b[0])+F(a[1])*F(b[1])
    assert P.cross2_sign(a,b)==sign(dc),(a,b,'cross')
    assert P.dot2_sign(a,b)==sign(dd),(a,b,'dot')
    pts=[tuple(math.ldexp(rng.uniform(-1,1),rng.randint(-1074,1022)) for _ in range(2)) for _ in range(3)]
    assert G.orient2d(*pts)==sign(determinant(*pts)),pts
    summary['predicate_cases']+=1
for s in (1e-9,1e-3,1,1e3,1e100):
  for off in (0,1e8):
    if s==1e-9 and off:continue # rounded data have zero edges
    for k in range(16):
      A=hull([(off+s*rng.uniform(-3,3),-off+s*rng.uniform(-3,3)) for _ in range(8)])
      B=hull([(off+s*rng.uniform(-3,3),-off+s*rng.uniform(-3,3)) for _ in range(8)])
      assert set(G.convex_hull(A+B))==set(hull(A+B))
      summary['hulls']+=1
      for j in range(10):
        x=(s*rng.uniform(-8,8),s*rng.uniform(-8,8));truth=state(A,B,x);got=C.membership_convex(A,B,x)
        assert got==truth,(s,off,A,B,x,got,truth)
        summary['member_cases']+=1
      x=(8*s,8*s);d=(-s,-s*math.nextafter(1,2));tm=30
      truth=ray(A,B,x,d,tm);got=E.first_entrance(A,B,x,d,t_max=tm)
      assert got.kind==('none' if truth is None else 'entrance'),(s,off,A,B,x,d,truth,got)
      assert got.t_exact==truth,(s,off,A,B,x,d,truth,got)
      summary['ray_cases']+=1
# Cache content snapshots must track new coordinate tuples and avoid alias staleness.
A=[(0.,0.),(1.,0.),(1.,1.),(0.,1.)]; B=list(A)
first=C.ve_cover(A,0,B,2)
A[3]=(-1.,.5)
warm=C.ve_cover(A,0,B,2);C._raw_cone_ring.cache_clear();C._fr.cache_clear();C._ve_side_directions.cache_clear();cold=C.ve_cover(A,0,B,2)
assert (warm is None)==(cold is None)
if warm:assert warm==cold
summary['cache_replacement']='warm equals cleared-cache result'
# Dual input must fail loudly instead of reusing a primal-only cache entry.
from eab.dual import Dual
try:C._fr((Dual(0.,(1.,)),0.))
except TypeError:summary['dual_cache']='TypeError (no silent primal cache hit)'
else:raise AssertionError('Dual input accepted and derivative lost')
print(json.dumps(summary,ensure_ascii=False,indent=2))
(ROOT/'review/notes/geom_independent_scan.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
