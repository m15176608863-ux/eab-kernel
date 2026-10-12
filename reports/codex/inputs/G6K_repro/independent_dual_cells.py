"""Full-cell Fraction certificates for Dual sqrt/atan2 derivatives.

No eab construction routine is the oracle. Correctly rounded irrational
derivatives are checked against *both* neighboring binary64 squared midpoints;
ties also require the even-significand representative.
"""
from pathlib import Path
from fractions import Fraction as F
import random,math,struct,sys,json,time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.dual import Dual,sqrt,atan2
U=math.ulp(0.0);MAX=sys.float_info.max
def even(x):return int.from_bytes(struct.pack('>d',x),'big')&1==0
def root_cell(x,q):
 x=abs(x)
 if not math.isfinite(x):return False
 if x==0:return q==0
 lo=(F(math.nextafter(x,0))+F(x))/2
 hi=(F(x)+F(math.nextafter(x,math.inf)))/2 if x<MAX else F(MAX)+F(2)**970
 return (lo*lo<q<hi*hi) or (q in (lo*lo,hi*hi) and even(x))
def ranges(q):
 return q < (F(U)/2)**2 or q >= (F(MAX)+F(2)**970)**2
def main():
 rng=random.Random(11065);out=[];errors=[];start=time.time()
 exps=(-1074,-1070,-1000,-716,-600,-428,-200,-1,0,1,200,600,1000,1023)
 for k in range(420):
  e=exps[k%len(exps)];v=math.ldexp(rng.uniform(1,1.5),e)
  if not v or not math.isfinite(v):continue
  seed=math.ldexp(rng.uniform(.75,1.25),exps[(k//len(exps))%len(exps)])
  if not math.isfinite(seed):continue
  if k%2:seed=-seed
  square=F(seed)**2/(4*F(v));row=dict(case=k,op='sqrt',value=v.hex(),seed=seed.hex())
  try:
   got=sqrt(Dual(v,(seed,0))).e
   if not root_cell(got[0],square) or got[1]!=0 or (got[0]>0)!=(seed>0):errors.append(dict(row,got=repr(got),problem='derivative cell'))
   row['derivative']=got[0].hex()
  except ArithmeticError as error:
   if not ranges(square):errors.append(dict(row,problem='representable derivative rejected',error=repr(error)))
   row['exception']=type(error).__name__
  out.append(row)
 # Every atan2 answer must be a one-round rational final derivative.
 for k in range(240):
  e=exps[k%len(exps)]
  y,x,dy,dx=[math.ldexp(rng.uniform(.5,1),e) for _ in range(4)]
  if k%2:dx=-dx
  if not all(math.isfinite(q) for q in (x,y,dx,dy)):continue
  q=(F(x)*F(dy)-F(y)*F(dx))/(F(x)**2+F(y)**2)
  try:
   got=atan2(Dual(y,(dy,)),Dual(x,(dx,))).e[0]
   expected=float(q)
   if got!=expected:errors.append(dict(case=k,op='atan2',actual=got.hex(),expected=expected.hex()))
  except ArithmeticError as error:
   try:expected=float(q)
   except OverflowError:expected=math.inf
   if expected and math.isfinite(expected):errors.append(dict(case=k,op='atan2',problem='representable rejected',error=repr(error)))
  out.append(dict(case=k,op='atan2'))
 result=dict(cases=len(out),errors=errors,elapsed_seconds=time.time()-start,rows=out)
 (ROOT/'review/independent_dual_cells.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False,indent=2))
 if errors:raise AssertionError(errors)
if __name__=='__main__':main()
