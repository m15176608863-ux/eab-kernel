"""Independent exact pressure for filters and LP certificates. Finite grids, no theorem claim.
Oracle does not import production vector/sign/linear-algebra helpers.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,random,math,itertools,json,copy
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab import predicates as P,lp,construction as C,rational3 as R
from eab.kernel2d.geom import orient2d
import eab.limit as L
import eab.limit_multi as M
rng=random.Random(120312)
def sg(x):return (x>0)-(x<0)
def fdisplay(q):
 try:return float(q)
 except OverflowError:return math.copysign(math.inf,sg(q))
def det3(points):
 a,b,c,p=points
 v=[[F(t[i])-F(a[i]) for i in range(3)] for t in (b,c,p)]
 u,v,w=v
 return u[0]*(v[1]*w[2]-v[2]*w[1])-u[1]*(v[0]*w[2]-v[2]*w[0])+u[2]*(v[0]*w[1]-v[1]*w[0])
counts={'cross':0,'dot':0,'orient2d':0,'orient3d':0,'lp_reduced':0,'rational3':0,'sqrt_midpoint':0,'lp_solve':0,'lp_lying_float_candidates':0,'selfcheck_injections':0}
exps=[-1200,-1074,-1073,-1022,-700,-540,-500,-200,-1,0,1,200,500,700,1000,1023,1200]
def qrand():return F(rng.randint(-16,16),rng.choice([1,3,7]))*F(2)**rng.choice(exps)
for i in range(6000):
 a=tuple(qrand() for _ in range(2));b=tuple(qrand() for _ in range(2))
 typ=rng.randrange(3)
 if typ==0 and all(math.isfinite(fdisplay(v)) for v in (*a,*b)):a,b=tuple(map(fdisplay,a)),tuple(map(fdisplay,b))
 if typ==1:a=tuple(fdisplay(v) if math.isfinite(fdisplay(v)) else v for v in a)
 assert P.cross2_sign(a,b)==sg(F(a[0])*F(b[1])-F(a[1])*F(b[0])),(a,b,'cross')
 assert P.dot2_sign(a,b)==sg(F(a[0])*F(b[0])+F(a[1])*F(b[1])),(a,b,'dot')
 counts['cross']+=1;counts['dot']+=1
for i in range(3500):
 points=[tuple(qrand() for _ in range(3)) for k in range(4)]
 if i%3==0 and all(math.isfinite(fdisplay(v)) for p in points for v in p):points=[tuple(map(fdisplay,p)) for p in points]
 elif i%3==1:points=[tuple(fdisplay(v) if math.isfinite(fdisplay(v)) else v for v in p) for p in points]
 assert P.orient3d(*points)==sg(det3(points)),points
 counts['orient3d']+=1
 a,b,c=[p[:2] for p in points[:3]];want=(F(b[0])-F(a[0]))*(F(c[1])-F(a[1]))-(F(b[1])-F(a[1]))*(F(c[0])-F(a[0]))
 assert orient2d(a,b,c)==sg(want),(a,b,c)
 counts['orient2d']+=1
for i in range(3500):
 m=rng.randint(1,10);A=[[qrand()] for _ in range(m)];y=[qrand() for _ in range(m)];cost=[qrand()]
 X=lp._Exact([[fdisplay(v) for v in row] for row in A],[0.]*m,[fdisplay(cost[0])],exact=(A,[0]*m,cost))
 want=cost[0]-sum(yi*row[0] for yi,row in zip(y,A));got=X.reduced_sign(X.c,X.cf,y,[fdisplay(v) for v in y],0)[0]
 assert got==sg(want),(A,y,cost,got,want);counts['lp_reduced']+=1
for i in range(1000):
 a=tuple(qrand() for _ in range(3));b=tuple(qrand() for _ in range(3))
 assert R.dot(a,b)==sum(x*y for x,y in zip(a,b))
 assert R.cross(a,b)==(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]);counts['rational3']+=1
for i in range(1200):
 q=abs(qrand())
 try:v=C.sqrt_rational(q,allow_underflow=True)
 except OverflowError:
  maxf=F(float.fromhex('0x1.fffffffffffffp+1023'));assert q>=((maxf+F(2)**1024)/2)**2;continue
 if v==0:assert q<=(F(math.ulp(0.))/2)**2
 else:
  lo=math.nextafter(v,-math.inf);hi=math.nextafter(v,math.inf);l=(F(lo)+F(v))/2;h=(F(hi)+F(v))/2 if math.isfinite(hi) else (F(2)**1024+F(v))/2
  assert l*l<=q<=h*h,(q,v)
 counts['sqrt_midpoint']+=1
# independent standard form one-row LP oracle: finite positive coefficients reduce
# to choosing smallest ratio c_j/A_j; negative rhs is infeasible; zero row is free.
base_cases=[]
for i in range(90):
 n=rng.randint(1,7);a=[abs(qrand())+F(1,3) for _ in range(n)];c=[qrand() for _ in range(n)];b=abs(qrand());want=b*min(cj/aj for cj,aj in zip(c,a));base_cases.append((a,b,c,want))
for a,b,c,want in base_cases:
 res=lp.solve([[fdisplay(v) for v in a]],[fdisplay(b)],[fdisplay(v) for v in c],exact=([a],[b],c));assert res.status=='optimal' and sum(F(ci)*xi for ci,xi in zip(c,res.exact_x))==want
 assert res.obj==fdisplay(want) and res.x==[fdisplay(v) for v in res.exact_x] and res.y==[fdisplay(v) for v in res.exact_y]
 assert sum(F(v)*x for v,x in zip(a,res.exact_x))==b
 assert all(F(cj)-res.exact_y[0]*F(aj)>=0 for cj,aj in zip(c,a));counts['lp_solve']+=1
real=lp._float_solve
for status,basis,e in [('optimal',[0],-1),('infeasible',[3],-1),('unbounded',[0],2),('optimal',[999],-1),('optimal',[0,0],-1)]:
 lp._float_solve=lambda *args,_out=(status,basis,e,0),**kw:_out
 # A=(1,1,1), b=1, min=(0,-1,-2) has unique optimum (0,0,1), -2.
 r=lp.solve([[1.,1.,1.]],[1.],[0.,-1.,-2.]);assert r.status=='optimal' and r.exact_x==(F(0),F(0),F(1)) and r.obj==-2
 counts['lp_lying_float_candidates']+=1
lp._float_solve=real
# Exact certificate fields individually poisoned with representable rational changes.
cs=[L.LimitContact((x,0.),(0.,1.),.6,cohesion=.1,area=3.) for x in (-1.,1.)];dead=[0.,-10.,0.];live=[1.,0.,-3.]
r=L.limit_load(cs,dead,live,dim=2)
for field in ['alpha','lambdas','mechanism','row_duals']:
 bad=copy.deepcopy(r)
 if field=='alpha':bad.alpha=bad.alpha.exact+F(1,10**100)
 else:
  seq=list(getattr(bad,field));seq[0]=seq[0].exact+F(1,10**100);setattr(bad,field,seq)
 assert not L.check_duality(bad,cs,dead,live,dim=2)['ok'],field
 counts['selfcheck_injections']+=1
print(json.dumps({'counts':counts,'wrong':0,'random_seed':120312,'finite_pressure_only':True},indent=2))
