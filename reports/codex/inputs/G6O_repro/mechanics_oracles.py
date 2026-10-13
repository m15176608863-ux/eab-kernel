"""WO-G6O own Fraction audit oracles, no production primitive for expected answers.
All outputs confined to review. LP oracle enumerates all BFS after row rank
filter, exact signs/certificates checked separately. Friction oracle uses cross
products. Force oracle sums certificate*model directions exactly (model input
only; no production summation, moment, construction, or LP helper).
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
import json, math, random, sys, copy
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'));sys.dont_write_bytecode=True
import eab.lp as LP
import eab.limit as L
import eab.limit_multi as M
OUT=[]
def view(x):
 try:return float(x)
 except OverflowError:return math.copysign(math.inf,-1 if x<0 else 1)
def linear_solution(a,b):
 size=len(b); mat=[list(map(F,row))+[F(rhs)] for row,rhs in zip(a,b)]
 for col in range(size):
  viable=[r for r in range(col,size) if mat[r][col]]
  if not viable:return None
  rr=viable[0];mat[col],mat[rr]=mat[rr],mat[col]
  lead=mat[col][col];mat[col]=[v/lead for v in mat[col]]
  for row in range(size):
   if row==col:continue
   factor=mat[row][col];mat[row]=[v-factor*w for v,w in zip(mat[row],mat[col])]
 return [row[-1] for row in mat]
def dot(a,b):return sum((F(x)*F(y) for x,y in zip(a,b)),F(0))
def cube(n,g):
 if len(n)==2:return (F(n[0])*F(g[1])-F(n[1])*F(g[0]),)
 n,g=list(map(F,n)),list(map(F,g));return (n[1]*g[2]-n[2]*g[1],n[2]*g[0]-n[0]*g[2],n[0]*g[1]-n[1]*g[0])
def lp_checks():
 rng=random.Random(1517001);t=0
 for case in range(450):
  m=rng.choice([1,2,3]);n=m+rng.choice([2,3,4])
  A=[[F(1)]*n]+[[F(rng.randint(-5,5)) for _ in range(n)] for _ in range(m-1)]
  x0=[F(rng.randrange(4)) for _ in range(n)];x0[0]+=1
  b=[dot(row,x0) for row in A];c=[F(rng.randint(-6,6)) for _ in range(n)]
  rs=[F(2)**rng.choice([-1400,-1075,-1074,-900,-400,-1,0,400,1023,1300]) for _ in range(m)]
  cs=[F(2)**rng.choice([-1400,-1075,-400,-1,0,400,1023,1400]) for _ in range(n)]
  A=[[v*rs[i]*cs[j] for j,v in enumerate(row)] for i,row in enumerate(A)];b=[v*rs[i] for i,v in enumerate(b)];c=[v*cs[j] for j,v in enumerate(c)]
  objectives=[]
  for indices in combinations(range(n),m):
   v=linear_solution([[row[j] for j in indices] for row in A],b)
   if v is not None and all(q>=0 for q in v):objectives.append(sum(c[j]*q for j,q in zip(indices,v)))
  if not objectives:continue # rank-deficient candidate not covered by BFS oracle
  expected=min(objectives)
  r=LP.solve([[view(v) for v in row] for row in A],[view(v) for v in b],[view(v) for v in c],exact=(A,b,c),max_iter=1 if case%3==0 else 20000)
  assert r.status=='optimal',(case,r.status)
  x,y=r.exact_x,r.exact_y
  assert all(v>=0 for v in x) and all(dot(row,x)==rhs for row,rhs in zip(A,b)),case
  assert dot(c,x)==expected==dot(b,y),(case,r.obj,view(expected))
  assert all(c[j]-sum(y[i]*A[i][j] for i in range(m))>=0 for j in range(n)),case
  assert r.x==list(map(view,x)) and r.y==list(map(view,y)) and r.obj==view(expected),case
  t+=1
 print('LP_BFS',t,'independent exact vertex + primal/dual + RN views PASS',flush=True)
 OUT.append(dict(test='LP_BFS',cases=t,pass_=True))
 # Add infeasible and unbounded families using explicit rational proof.
 statuses=[]
 for exp in [-1400,-1075,-400,0,400,1400]:
  s=F(2)**exp
  # x1+x2=-s impossible; minimizing -s*x1 with x1-x2=s unbounded.
  for A,b,c,status in [([[s,s]],[-s],[0,0],'infeasible'),([[s,-s]],[s],[-s,0],'unbounded')]:
   r=LP.solve([[view(v) for v in row] for row in A],list(map(view,b)),list(map(view,c)),exact=(A,b,c))
   assert r.status==status;(statuses.append([exp,status]))
 print('LP_STATUS',statuses,'PASS',flush=True);OUT.append(dict(test='LP_STATUS',cases=statuses,pass_=True))
def filter_checks():
 rng=random.Random(1517002);checked=0
 # raw reduced-sign fast filter must equal exact answer even when y,A,c
 # individually underflow, overflow or cancel at mixed scales.
 for i in range(7000):
  m=rng.randrange(1,7)
  A=[[F(rng.randint(-9,9))*F(2)**rng.choice([-2000,-1075,-1074,-900,-400,-1,0,400,900,1023,2000])] for _ in range(m)]
  y=[F(rng.randint(-9,9))*F(2)**rng.choice([-2000,-1075,-1074,-900,-400,-1,0,400,900,1023,2000]) for _ in range(m)]
  prod=sum(yj*row[0] for yj,row in zip(y,A))
  delta=F(rng.choice([-1,0,1]))*F(2)**rng.choice([-3000,-1075,-1074,-900,-400,-1,0,400,2000])
  cost=[prod+delta]
  oracle=(delta>0)-(delta<0)
  X=LP._Exact([[0.]]*m,[0.]*m,[0.],exact=(A,[F(0)]*m,cost))
  sg,_=X.reduced_sign(cost,list(map(view,cost)),y,list(map(view,y)),0)
  assert sg==oracle,(i,A,y,cost,sg,oracle)
  checked+=1
 print('LP_FILTER',checked,'raw exact signs PASS',flush=True);OUT.append(dict(test='LP_FILTER',cases=checked,pass_=True))
def cone_checks():
 rng=random.Random(1517003);checked=errors=0
 for i in range(1000):
  dim=rng.choice([2,3]);raw=tuple(rng.randint(-1000000,1000000) for _ in range(dim))
  if not any(raw):continue
  mu=rng.choice([F(0),F(1,2**1074),F(1,2**400),F(1,2**50),F(1,2),F(9,5),F(2**20)])
  k=rng.choice([3,4,5,8,11,16])
  try:
   ct=L.LimitContact((0,)*dim,raw,mu)
   gs=L.friction_generators(ct.normal,mu,dim,k)
   for g in gs:
    p=dot(ct.normal,g);cross=cube(ct.normal,g)
    assert p>0 and dot(cross,cross)<=mu*mu*p*p,(i,raw,mu,g)
    checked+=1
   dirs=L._cohesion_directions(ct.normal,dim,k)
   assert all(dot(ct.normal,d)==0 and dot(d,d)<=1 for d in dirs),(i,raw)
  except L.ConstructionDomainError:errors+=1
 print('CONE',checked,'physical cross-product certificates PASS; named domain rejections',errors,flush=True)
 OUT.append(dict(test='CONE',directions=checked,named_domain_rejections=errors,pass_=True))
def force_checks():
 discrepancies=[]
 for W in [F(1),F(2)**100,F(2)**400,F(2)**700]:
  for mu in [F(1,3),F(1,2),F(1),F(3,2)]:
   ct=L.LimitContact((0,0),(0,1),mu)
   # horizontal dead component set small relative to gravity, load is vertical
   # and negative. Only zero live load yields unbounded; choose horizontal drive.
   dead=[F(1),-W,F(0)];live=[F(1),F(0),F(0)]
   r=L.limit_load([ct],dead,live,dim=2,tol=0)
   if r.status!='optimal':continue
   gs=L.friction_generators(ct.normal,ct.mu,2)
   expected=tuple(sum(r.lambdas[j].exact*F(gs[j][a]) for j in range(2)) for a in range(2))
   actual=r.contact_forces[0]
   rn=tuple(view(v) for v in expected)
   if actual!=rn:discrepancies.append(dict(W=str(W),mu=str(mu),exact=list(map(str,expected)),actual=list(actual),RN=list(rn),alpha=float(r.alpha)))
 print('FORCE_VIEW',len(discrepancies),'non RN reports',flush=True)
 OUT.append(dict(test='FORCE_VIEW',discrepancies=discrepancies))
if __name__=='__main__':
 lp_checks();filter_checks();cone_checks();force_checks()
 (ROOT/'review/evidence/mechanics_oracles.json').write_text(json.dumps(OUT,ensure_ascii=False,indent=2),encoding='utf-8')
 print('MECHANICS_ORACLES_DONE',flush=True)
