"""Independent exhaustive BFS/ray oracle; no production algebra helpers used."""
import sys,random,itertools,json,math
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
import eab.lp as LP

def solve_square(M,b):
 m=len(b);T=[list(row)+[v] for row,v in zip(M,b)]
 for j in range(m):
  k=next((k for k in range(j,m) if T[k][j]),None)
  if k is None:return None
  T[j],T[k]=T[k],T[j];v=T[j][j];T[j]=[x/v for x in T[j]]
  for i in range(m):
   if i!=j:
    v=T[i][j];T[i]=[a-v*z for a,z in zip(T[i],T[j])]
 return [r[-1] for r in T]

def vertices(A,b,n):
 m=len(A)
 for basis in itertools.combinations(range(n),m):
  x=solve_square([[r[j] for j in basis] for r in A],b)
  if x is not None and all(t>=0 for t in x):
   full=[F(0)]*n
   for j,t in zip(basis,x):full[j]=t
   yield full

def oracle(A,b,c):
 n=len(c);xs=list(vertices(A,b,n))
 if not xs:return 'infeasible',None
 for d in vertices(A+[[F(1)]*n],[F(0)]*len(A)+[F(1)],n):
  if sum(a*v for a,v in zip(c,d))<0:return 'unbounded',None
 return 'optimal',min(sum(a*v for a,v in zip(c,x)) for x in xs)

def disp(v):
 try:return float(v)
 except OverflowError:return math.copysign(float('inf'),1 if v>0 else -1)

rng=random.Random(611071);rows=[];mismatches=[]
scales=[F(1,2**1050),F(1,2**600),F(1),F(2**600),F(2**1000)]
for case in range(600):
 m=1+case%3;n=m+2
 A=[[F(int(i==j)) for j in range(m)]+[F(rng.randint(-5,5)),F(rng.randint(-5,5))] for i in range(m)]
 b=[F(rng.randint(-5,7)) for _ in range(m)];c=[F(rng.randint(-5,5)) for _ in range(n)]
 # Row and variable rescaling preserves exact math but exercises under/overflow candidates.
 rs=[rng.choice(scales) for _ in range(m)];vs=[rng.choice(scales) for _ in range(n)]
 A=[[v*r*s for v,s in zip(row,vs)] for row,r in zip(A,rs)];b=[v*r for v,r in zip(b,rs)];c=[v*s for v,s in zip(c,vs)]
 st,obj=oracle(A,b,c)
 try:r=LP.solve([[disp(v) for v in row] for row in A],[disp(v) for v in b],[disp(v) for v in c],exact=(A,b,c))
 except Exception as e:mismatches.append([case,'exception',repr(e)]);continue
 err=[]
 if r.status!=st:err.append(['status',st,r.status])
 if st=='optimal' and r.status=='optimal':
  xe,ye=r.exact_x,r.exact_y
  if sum(v*x for v,x in zip(c,xe))!=obj:err.append(['obj',str(obj),str(sum(v*x for v,x in zip(c,xe)))])
  if any(sum(a*x for a,x in zip(row,xe))!=bi for row,bi in zip(A,b)):err.append('primal')
  if any(x<0 for x in xe):err.append('nonnegative')
  if any(cj-sum(A[i][j]*ye[i] for i in range(m))<0 for j,cj in enumerate(c)):err.append('dual')
  if any(v!=disp(e) for v,e in zip(r.x,xe)) or any(v!=disp(e) for v,e in zip(r.y,ye)) or r.obj!=disp(obj):err.append('float-view')
 if err:mismatches.append([case,err])
 rows.append(dict(case=case,status=st))
# Deliberately lying float layer; exact status and optimum must still follow oracle.
real=LP._float_solve;lies=[]
for claim in ['optimal','unbounded','infeasible']:
 for A,b,c in [([[F(1),F(1)]],[F(1)],[F(-1),F(0)]),([[F(-1),F(-1)]],[F(1)],[F(1),F(0)]),([[F(1),F(-1)]],[F(0)],[F(-1),F(0)])]:
  LP._float_solve=lambda *a,**kw:(claim,[0],1,0)
  expected=oracle(A,b,c);r=LP.solve(A,b,c)
  ok=r.status==expected[0] and (r.status!='optimal' or sum(v*x for v,x in zip(c,r.exact_x))==expected[1]);lies.append([claim,expected[0],r.status,ok])
LP._float_solve=real
result=dict(cases=len(rows),status_counts={st:sum(x['status']==st for x in rows) for st in ['optimal','unbounded','infeasible']},mismatches=mismatches,lying_float_candidate=lies)
print(json.dumps(result,indent=2));(ROOT/'review/agents/lp_independent_result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
assert not mismatches and all(x[-1] for x in lies)
