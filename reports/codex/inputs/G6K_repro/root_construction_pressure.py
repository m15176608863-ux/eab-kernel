from pathlib import Path
import sys,json,math,random,struct,time
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.construction import sqrt_rational,norm_rational,unit_rational,normalized_difference_rational
r=random.Random(11013);t0=time.time();counts={};errors=[]
def even(f): return not (struct.unpack('>Q',struct.pack('>d',f))[0]&1)
def root_cell(q,f):
 if f==0: return q<=F(2)**-2150
 low=math.nextafter(f,-math.inf);high=math.nextafter(f,math.inf)
 lo=(F(low)+F(f))/2;hi=(F(f)+(F(high) if math.isfinite(high) else F(2)**1024))/2
 return lo*lo <= q <= hi*hi and (q not in (lo*lo,hi*hi) or even(f))
def algebraic_cmp(c,nn,target):
 c,nn,target=F(c),F(nn),F(target)
 if c>=0>target:return 1
 if c<0<=target:return -1
 d=c*c-target*target*nn;sg=(d>0)-(d<0)
 return -sg if c<0 else sg
for e in (-1074,-1073,-1022,-1000,-550,-500,-53,-1,0,53,500,1000,1023):
 for j in range(40):
  f=math.ldexp(r.uniform(.5,1),e)
  q=(F(f)+F(math.nextafter(f,math.inf)))/2
  for square in (F(f)**2,q*q,(q*q+F(f)**2)/2):
   got=sqrt_rational(square,allow_underflow=True)
   if not root_cell(square,got):errors.append(('sqrt',str(square),got))
   counts['sqrt']=counts.get('sqrt',0)+1
for j in range(1200):
 e=r.choice([-1200,-1074,-1000,-500,0,500,1000,1200]);v=[F(r.randrange(-20,21))*F(2)**e for _ in range(3)]
 q=sum(x*x for x in v)
 try:got=norm_rational(v,allow_underflow=True)
 except OverflowError:
  assert q >= ((F(float.fromhex('0x1.fffffffffffffp1023'))+F(2)**1024)/2)**2
 else:
  if not root_cell(q,got):errors.append(('norm',str(v),got))
 counts['norm']=counts.get('norm',0)+1
 if q:
  u=unit_rational(v,allow_underflow=True)
  for x,f in zip(v,u):
   if not root_cell(x*x/q,abs(f)):errors.append(('unit',str(v),f))
  counts['unit_components']=counts.get('unit_components',0)+3
for j in range(1000):
 nn=F(r.randrange(1,50));c=F(r.randrange(-100,101))*F(2)**r.choice([-1000,-500,0,500,1000]);off=F(math.ldexp(r.uniform(-1,1),r.choice([-1000,-500,0,500,1000])))
 try:f=normalized_difference_rational(c,nn,off,allow_underflow=True)
 except OverflowError:continue
 if math.isfinite(f):
  low=math.nextafter(f,-math.inf);high=math.nextafter(f,math.inf)
  if not (math.isfinite(low) and math.isfinite(high)):continue
  l=(F(low)+F(f))/2;h=(F(f)+F(high))/2
  cl=algebraic_cmp(c,nn,off+l);ch=algebraic_cmp(c,nn,off+h)
  if cl<0 or ch>0 or (0 in (cl,ch) and not even(f)):errors.append(('difference',str(c),str(nn),str(off),f,cl,ch))
 counts['difference']=counts.get('difference',0)+1
result={'counts':counts,'errors':errors,'seed':11013,'elapsed_seconds':time.time()-t0};(ROOT/'review/logs/root_construction_pressure.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result));assert not errors
