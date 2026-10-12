"""Own Fraction Fourier-Motzkin strict-feasibility oracle for every sign cell.
No production geometry primitive/LP solver is used to enumerate expected cells.
A sign chamber exists iff signed normals admit dot(n,x)>=1 simultaneously;
homogeneous strict inequalities can always be scaled to RHS 1.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import product
import sys,json,random
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.entrance_topology import _chamber_directions

def feasible(normals,signs):
 rows=[(tuple(F(s)*F(c) for c in n),F(1)) for n,s in zip(normals,signs)]
 for k in range(3):
  pos=[];neg=[];zero=[]
  for a,b in rows:
   if not any(a):
    if b>0:return False
    continue
   if a[-1]>0:pos.append((a,b))
   elif a[-1]<0:neg.append((a,b))
   else:zero.append((a[:-1],b))
  new=zero
  for p,pb in pos:
   for n,nb in neg:
    new.append((tuple(-n[-1]*x+p[-1]*y for x,y in zip(p[:-1],n[:-1])), -n[-1]*pb+p[-1]*nb))
  # Identical lhs only retains strongest rhs; exact positive rescaling helps.
  unique={}
  for a,b in new:
   if not any(a):
    if b>0:return False
    continue
   factor=abs(next(x for x in a if x));a=tuple(x/factor for x in a);b/=factor
   unique[a]=max(unique.get(a,b),b)
  rows=list(unique.items())
 return all(b<=0 for a,b in rows)

r=random.Random(8831)
cases=[[(1,0,0)],[(1,0,0),(0,1,0),(1,1,0)],[(1,0,0),(0,1,0),(0,0,1),(1,1,1)],
 [(1,0,0),(1,F(2)**-200,0),(1,0,F(2)**-200)],
 [(1,k,0) for k in range(5)]]
for _ in range(20):
 normals=[]
 while len(normals)<5:
  n=tuple(F(r.randrange(-3,4)) for _ in range(3))
  if not any(n):continue
  pivot=next(x for x in n if x);n=tuple(x/pivot for x in n)
  if n not in normals:normals.append(n)
 cases.append(normals)
rows=[]
for i,normals in enumerate(cases):
 normals=tuple(tuple(map(F,n)) for n in normals)
 expected={sign for sign in product((-1,1),repeat=len(normals)) if feasible(normals,sign)}
 got=set()
 for d in _chamber_directions(normals):
  values=[sum(c*x for c,x in zip(n,d)) for n in normals]
  assert all(values)
  sig=tuple(1 if x>0 else -1 for x in values)
  assert sig not in got
  got.add(sig)
 assert got==expected,(i,expected-got,got-expected)
 rows.append(dict(case=i,planes=len(normals),chambers=len(got),oracle_chambers=len(expected)))
print(json.dumps(dict(result='PASS',cases=len(cases),oracle='independent exact Fourier-Motzkin on all strict sign patterns',rows=rows),indent=2))
