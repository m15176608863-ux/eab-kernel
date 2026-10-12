"""Fresh G6I exponent sweep; oracles expand raw Fraction expressions only."""
from pathlib import Path
from fractions import Fraction as F
import sys,random,math,itertools,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
import eab.predicates as P
import eab.dual as D
R=random.Random(9101226); exps=[-1074,-1050,-1000,-600,-250,-200,-1,0,1,200,250,500,900,1000]
def value():
 return math.ldexp(R.choice([-1.,1.])*R.choice([.5,.75,1.]),R.choice(exps))
def sign(v):return (v>0)-(v<0)
orient=0
for mode in ('float','mixed'):
 for k in range(5000):
  a,b,c,d=[tuple(value() for _ in range(3)) for __ in range(4)]
  if mode=='mixed':
   a=tuple(F(x)+F(2)**R.choice([-1200,-1080,-400,0]) for x in a)
  vectors=[[F(v[i])-F(a[i]) for i in range(3)] for v in (b,c,d)]
  det=F(0)
  for perm in itertools.permutations(range(3)):
   parity=sum(perm[i]>perm[j] for i in range(3) for j in range(i+1,3))
   det+=(-1)**parity*vectors[0][perm[0]]*vectors[1][perm[1]]*vectors[2][perm[2]]
  assert P.orient3d(a,b,c,d)==sign(det),(mode,k,a,b,c,d)
  orient+=1
bilinear=dual=refusals=0
for k in range(10000):
 a,b=tuple(value() for _ in range(2)),tuple(value() for _ in range(2))
 cr=F(a[0])*F(b[1])-F(a[1])*F(b[0]);dt=sum(F(x)*F(y) for x,y in zip(a,b))
 assert P.cross2_sign(a,b)==sign(cr) and P.dot2_sign(a,b)==sign(dt)
 bilinear+=1
 u,v,aa,bb=value(),value(),value(),value()
 if v==0:v=2.**-1074
 for name,expected,fun in [('mul',F(aa)*F(v)+F(u)*F(bb),lambda:D.Dual(u,(aa,))*D.Dual(v,(bb,))),
    ('div',(F(aa)*F(v)-F(u)*F(bb))/(F(v)*F(v)),lambda:D.Dual(u,(aa,))/D.Dual(v,(bb,))),
    ('atan2',(F(aa)*F(v)-F(u)*F(bb))/(F(u)*F(u)+F(v)*F(v)),lambda:D.atan2(D.Dual(u,(aa,)),D.Dual(v,(bb,))))]:
  try: target=float(expected)
  except OverflowError:continue
  if expected and not target:continue
  try:r=fun()
  except (ArithmeticError,ValueError):
   # Primal outside binary64 can legitimately fail. Do not call these wrong.
   refusals+=1;continue
  actual=r.e[0]
  # Ordinary fast arithmetic promises approximate constructions, not globally
  # correctly-rounded derivatives. Reject wrong zero/sign or material error.
  assert (not expected and actual==0) or (expected and actual!=0 and sign(actual)==sign(expected))
  assert math.isclose(actual,target,rel_tol=5e-13,abs_tol=math.ulp(target)),(name,u,v,aa,bb,actual,target)
  dual+=1
print(json.dumps(dict(new_seed=9101226,orient3d_cases=orient,bilinear_cases=bilinear,dual_cases=dual,loud_refusals=refusals,all_equal=True),indent=2))
