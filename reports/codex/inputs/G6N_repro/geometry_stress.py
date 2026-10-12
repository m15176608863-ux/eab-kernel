"""G6N exact geometry/filters adversarial stress; independent Fraction reference.
No tested geometry primitives, hulls or SAT helpers occur in reference functions.
"""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import random,math,json,sys,time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.predicates import cross2_sign,dot2_sign,orient3d
from eab.kernel2d.geom import orient2d
from eab.kernel2d.covers import membership_convex
from eab.kernel3d.geom3 import convex_hull_3d
from eab.kernel3d.exact_geom import polygon_locate

def det3(a,b,c):return a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0])
def sgn(x):return int(x>0)-int(x<0)
def ori2(a,b,c):return (F(b[0])-F(a[0]))*(F(c[1])-F(a[1]))-(F(b[1])-F(a[1]))*(F(c[0])-F(a[0]))
def hull2(raw):
    p=sorted(set(raw));s=[];t=[]
    for a in p:
      while len(s)>1 and ori2(s[-2],s[-1],a)<=0:s.pop()
      s.append(a)
    for a in reversed(p):
      while len(t)>1 and ori2(t[-2],t[-1],a)<=0:t.pop()
      t.append(a)
    return s[:-1]+t[:-1]
def state_hull2(raw,p):
    ring=hull2(raw);v=[ori2(a,b,p) for a,b in zip(ring,ring[1:]+ring[:1])]
    return -1 if min(v)<0 else (0 if min(v)==0 else 1)
def normal3(a,b,c):
    u=[F(b[k])-F(a[k]) for k in range(3)];v=[F(c[k])-F(a[k]) for k in range(3)]
    return (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
def extreme3(raw):
    p=sorted(set(raw));active={a:[] for a in p}
    for a,b,c in combinations(p,3):
      n=normal3(a,b,c)
      if not any(n):continue
      vals=[sum(n[k]*(x[k]-a[k]) for k in range(3)) for x in p]
      if min(vals)<0<max(vals):continue
      for x,v in zip(p,vals):
        if v==0:active[x].append(n)
    return {p for p,ns in active.items() if any(det3(a,b,c)!=0 for a,b,c in combinations(ns,3))}
def scalar(rng,exp=None):
    exp=rng.choice([-1100,-1074,-1030,-900,-550,-400,-160,-30,0,30,160,400,550,900,1020,1100]) if exp is None else exp
    value=F(rng.randint(-2**15,2**15),2**15)*(F(2)**exp)
    if rng.random()<.5:
      try:
        z=float(value)
        if math.isfinite(z):return z
      except OverflowError:pass
    return value

def run():
    rng=random.Random(1402);stats={};fail=[];errors=[];start=time.time()
    def check(k,a,e,case):
      stats[k]=stats.get(k,0)+1
      if a!=e:fail.append({'kind':k,'actual':str(a),'expected':str(e),'case':str(case)});print('FAIL',fail[-1],flush=True)
    for i in range(8000):
      a=tuple(scalar(rng) for _ in range(3));b=tuple(scalar(rng) for _ in range(3));c=tuple(scalar(rng) for _ in range(3));d=tuple(scalar(rng) for _ in range(3))
      if i%3==0:
        c=tuple(F(a[k])+F(rng.randint(-7,7),8)*(F(b[k])-F(a[k])) for k in range(3))
        if i%2==0:c=list(c);c[i%3]+=F(2)**-1400;c=tuple(c)
      check('cross2',cross2_sign(a[:2],b[:2]),sgn(F(a[0])*F(b[1])-F(a[1])*F(b[0])),(a,b))
      check('dot2',dot2_sign(a[:2],b[:2]),sgn(F(a[0])*F(b[0])+F(a[1])*F(b[1])),(a,b))
      check('orient2',orient2d(a[:2],b[:2],c[:2]),sgn(ori2(a[:2],b[:2],c[:2])),(a,b,c))
      u=[F(b[k])-F(a[k]) for k in range(3)];v=[F(c[k])-F(a[k]) for k in range(3)];w=[F(d[k])-F(a[k]) for k in range(3)]
      check('orient3',orient3d(a,b,c,d),sgn(det3(u,v,w)),(a,b,c,d))
    for i in range(20000):
      if i%2:
        exponents=rng.choice([(-1074,-1074,1000),(-600,-600,1000),(-400,-400,-400),(400,400,400),(1000,1000,1000),(0,0,0)])
      else:
        exponents=tuple(rng.choice([-1074,-1000,-500,-160,0,500,1000]) for _ in range(3))
      pts=[tuple(math.ldexp(rng.uniform(-1,1),e) for e in exponents) for _ in range(4)]
      if i%7==0:pts[3]=pts[1]
      if exponents==(0,0,0) and i%3==0:
        pts[3]=tuple(pts[0][k]+.25*(pts[1][k]-pts[0][k])+.75*(pts[2][k]-pts[0][k]) for k in range(3))
      a,b,c,d=pts
      u=[F(b[k])-F(a[k]) for k in range(3)];v=[F(c[k])-F(a[k]) for k in range(3)];w=[F(d[k])-F(a[k]) for k in range(3)]
      check('orient3_float',orient3d(a,b,c,d),sgn(det3(u,v,w)),pts)
      check('orient2_float',orient2d(a[:2],b[:2],c[:2]),sgn(ori2(a[:2],b[:2],c[:2])),pts[:3])
    print('PREDICATES',stats,'seconds',round(time.time()-start,2),flush=True)
    for i in range(120):
      scale=F(2)**rng.choice([-1100,-500,-30,0,30,500,1100]);trans=(F(2)**rng.choice([0,30,1000]),-F(2)**rng.choice([0,30,1000]))
      a=hull2([(F(rng.randint(-10,10)),F(rng.randint(-10,10))) for _ in range(8)])
      b=hull2([(F(rng.randint(-10,10)),F(rng.randint(-10,10))) for _ in range(8)])
      if len(a)<3 or len(b)<3:continue
      a=[(x*scale+trans[0],y*scale+trans[1]) for x,y in a];b=[(x*scale+trans[0],y*scale+trans[1]) for x,y in b]
      differences=[(bx-ax,by-ay) for ax,ay in a for bx,by in b]
      probes=[(F(rng.randint(-25,25))*scale,F(rng.randint(-25,25))*scale) for _ in range(9)]+differences[:3]
      for x in probes:check('membership2',membership_convex(a,b,x),state_hull2(differences,x),(i,x))
    print('MEMBER2',stats,'seconds',round(time.time()-start,2),flush=True)
    for i in range(110):
      # Exact near-planar slivers plus random point clouds, duplicate points and
      # deliberately inserted non-extreme edge/facet points. No production hull oracle.
      scale=F(2)**rng.choice([-1100,-400,0,400,1100]);thin=F(2)**rng.choice([-1300,-500,-53,-20,0]);t=F(2)**rng.choice([0,30,1000])
      p=[(F(rng.randint(-3,3))*scale+t,F(rng.randint(-3,3))*scale-t,F(rng.randint(-3,3))*scale*thin+t) for _ in range(10)]
      p+=[tuple((p[0][k]+p[1][k])/2 for k in range(3)),tuple((p[1][k]+p[2][k]+p[3][k])/3 for k in range(3)),p[0]]
      expected=extreme3(p)
      if len(expected)<4:continue
      try:actual=set(tuple(F(x) for x in v) for v in convex_hull_3d(p).verts);check('hull3_extremes',actual,expected,i)
      except Exception as e:errors.append({'kind':'hull3','case':i,'error':repr(e)})
    print('HULL3',stats,'errors',len(errors),'seconds',round(time.time()-start,2),flush=True)
    for i in range(600):
      # A 3D parallelogram, query lies in its exact plane; inverse coordinates
      # provide an oracle independent of projected winding/filter implementation.
      scale=F(2)**rng.choice([-1200,-1074,-600,-400,0,400,600,1100]);t=F(2)**rng.choice([0,30,1000])
      u=(scale,2*scale,3*scale);v=(4*scale,-scale,2*scale);base=(t,-t,t)
      vertices=[tuple(base[k]+a*u[k]+b*v[k] for k in range(3)) for a,b in [(0,0),(1,0),(1,1),(0,1)]]
      a,b=rng.choice([F(-1,10),F(0),F(1,100),F(1,2),F(1),F(11,10)]),rng.choice([F(0),F(1,2),F(1),F(3,2)])
      p=tuple(base[k]+a*u[k]+b*v[k] for k in range(3))
      expected=-1 if min(a,b)<0 or max(a,b)>1 else (0 if a in (0,1) or b in (0,1) else 1)
      check('polygon_filter',polygon_locate(p,vertices),expected,(i,a,b,scale,t))
    result={'stats':stats,'failures':fail,'errors':errors,'seconds':round(time.time()-start,3)}
    (ROOT/'review/evidence/geometry_stress_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':run()
