from pathlib import Path
import sys,random,math,json,time
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.predicates import cross2_sign,dot2_sign,orient3d
from eab.kernel2d.geom import orient2d
r=random.Random(11012); rows=[];t0=time.time()
def sign(x):return (x>0)-(x<0)
def det3(A):
 A=[[F(x) for x in q] for q in A]
 return A[0][0]*(A[1][1]*A[2][2]-A[1][2]*A[2][1])-A[0][1]*(A[1][0]*A[2][2]-A[1][2]*A[2][0])+A[0][2]*(A[1][0]*A[2][1]-A[1][1]*A[2][0])
def val(e=None):
 e=r.choice([-1074,-1050,-1022,-750,-550,-510,-200,-1,0,30,200,500,750,1000]) if e is None else e
 return math.ldexp(r.choice([-1,1])*r.uniform(.5,1.),e)
counts={'cross2':0,'dot2':0,'orient2d':0,'orient3d':0}
for i in range(12000):
 a=tuple(val() for _ in range(2));b=tuple(val() for _ in range(2))
 if i%3==0:
  a=tuple(F(x) for x in a);b=tuple(F(x)+F(2)**r.choice([-1200,-1074,-700,-100]) for x in a)
 ex=sign(F(a[0])*F(b[1])-F(a[1])*F(b[0]));dx=sign(F(a[0])*F(b[0])+F(a[1])*F(b[1]))
 for name,got,truth in [('cross2',cross2_sign(a,b),ex),('dot2',dot2_sign(a,b),dx)]:
  counts[name]+=1
  if got!=truth:rows.append((name,i,repr(a),repr(b),got,truth))
for i in range(8000):
 p=[tuple(val() for _ in range(2)) for _ in range(3)]
 if i%3==0:
  e=r.choice([-1074,-1000,-750,-550,-510,-200,0,30,500,1000]); p=[tuple(val(e) for _ in range(2)) for _ in range(3)]
 if i%5==0:p[2]=tuple(float((F(p[0][k])+F(p[1][k]))/2) for k in range(2))
 a,b,c=p;truth=sign((F(a[0])-F(c[0]))*(F(b[1])-F(c[1]))-(F(a[1])-F(c[1]))*(F(b[0])-F(c[0])))
 got=orient2d(a,b,c);counts['orient2d']+=1
 if got!=truth:rows.append(('orient2d',i,repr(p),got,truth))
for i in range(7000):
 p=[tuple(val() for _ in range(3)) for _ in range(4)]
 if i%3==0:
  e=r.choice([-1074,-1000,-750,-550,-510,-200,0,30,500,1000]);p=[tuple(val(e) for _ in range(3)) for _ in range(4)]
 if i%5==0:p[3]=tuple(float((F(p[0][k])+F(p[1][k])+F(p[2][k]))/3) for k in range(3))
 if i%7==0:p[0]=tuple(F(v)+F(2)**-1200 for v in p[0])
 a,b,c,d=p;truth=sign(det3([[F(q[k])-F(a[k]) for k in range(3)] for q in (b,c,d)]))
 got=orient3d(a,b,c,d);counts['orient3d']+=1
 if got!=truth:rows.append(('orient3d',i,repr(p),got,truth))
result={'counts':counts,'wrong':rows,'elapsed_seconds':time.time()-t0,'seed':11012}
(ROOT/'review/logs/root_predicate_pressure.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
assert not rows
