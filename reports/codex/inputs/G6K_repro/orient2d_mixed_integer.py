from pathlib import Path
import sys,json
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d.geom import orient2d,triangulate
N=2**53
a=(N+3,3.0);b=(N+4,4.0);c=(float(N),0.0)
def exact(a,b,c):
 q=lambda x:F(x)
 d=(q(a[0])-q(c[0]))*(q(b[1])-q(c[1]))-(q(a[1])-q(c[1]))*(q(b[0])-q(c[0]))
 return (d>0)-(d<0),str(d)
print('mixed inputs',a,b,c,'got',orient2d(a,b,c),'exact',exact(a,b,c))
print('Fraction inputs',orient2d(tuple(map(F,a)),tuple(map(F,b)),tuple(map(F,c))))
a=(N+3,3.0);b=(N+5,4.0);c=(float(N),0.0)
print('sign reversal',a,b,c,'got',orient2d(a,b,c),'exact',exact(a,b,c))
assert exact(a,b,c)==(-1,'-3') and orient2d(a,b,c)==1
rows=[]
for e in (53,54,55,60):
 for ax in range(1,17):
  for bx in range(1,17):
   for ay,by in ((3.,4.),(1.,2.),(7.,11.)):
    a=(2**e+ax,ay);b=(2**e+bx,by);c=(float(2**e),0.)
    truth,d=exact(a,b,c); got=orient2d(a,b,c)
    if got!=truth:rows.append({'exponent':e,'a':a,'b':b,'c':c,'got':got,'expected':truth,'det':d})
print('wrong',len(rows));print(json.dumps(rows[:8]))
print('sign reversals',sum(x['expected']!=0 for x in rows),'exact-zero errors',sum(x['expected']==0 for x in rows))
assert len(rows)==102
assert sum(x['expected']!=0 for x in rows)==82
Path(ROOT/'review/logs/orient2d_mixed_integer_results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
assert rows and orient2d((N+3,3.),(N+4,4.),(float(N),0.)) == 1
assert exact((N+3,3.),(N+4,4.),(float(N),0.))[0] == 0

P=[(2**53+2,7.),(2**53+3,11.),(float(2**53),0.)]
assert exact(*P)==(1,'1')
print('nondegenerate triangle area2=1: raw',triangulate(P),'exact-input',triangulate([tuple(map(F,p)) for p in P]))
assert triangulate(P)==[]
assert triangulate([tuple(map(F,p)) for p in P])==[(0,1,2)]
