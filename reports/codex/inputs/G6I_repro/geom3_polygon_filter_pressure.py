"""Own Fraction edge-distance/winding oracle for the 3D polygon filter.
No production arithmetic, normals, projection or helper enters expected().
"""
from pathlib import Path
from fractions import Fraction as F
import sys,random,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.exact_geom import polygon_locate
rng=random.Random(991831)
def expected(p,vs,tol):
 for a,b in zip(vs,vs[1:]+vs[:1]):
  u=(b[0]-a[0],b[1]-a[1]);w=(p[0]-a[0],p[1]-a[1])
  length=u[0]**2+u[1]**2
  z=max(F(0),min(F(1),(w[0]*u[0]+w[1]*u[1])/length)) if length else F(0)
  v=(w[0]-z*u[0],w[1]-z*u[1])
  if v[0]**2+v[1]**2<=tol**2:return 0
 n=0
 for a,b in zip(vs,vs[1:]+vs[:1]):
  cross=(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
  if a[1]<=p[1]<b[1] and cross>0:n+=1
  if b[1]<=p[1]<a[1] and cross<0:n-=1
 return 1 if n else -1
poly=[(F(0),F(0)),(F(3),F(0)),(F(3),F(1)),(F(1),F(1)),(F(1),F(4)),(F(0),F(4))]
scales=[F(2)**k for k in (-1074,-1050,-600,-300,-50,0,50,300,600,1000)]
translations=[F(0),F(10**8),F(2)**1000]
rows=[];count=0
for scale in scales:
 for translate in translations:
  for k in range(75):
   pp=(F(rng.randrange(-10,40),10),F(rng.randrange(-10,50),10))
   band=F(0) if k%3 else F(rng.randrange(0,5),10)
   vv=[(translate+scale*x,-translate+scale*y,F(0)) for x,y in poly]
   p=(translate+scale*pp[0],-translate+scale*pp[1],F(0))
   truth=expected(pp,poly,band);got=polygon_locate(p,tuple(vv),scale*band)
   assert got==truth,(scale,translate,pp,band,truth,got)
   count+=1
  rows.append(dict(scale=str(scale),translation=str(translate),cases=75))
print(json.dumps(dict(result='PASS',cases=count,oracle='own Fraction edge-distance and winding, all scales incl subnormal, supernormal Fraction derived differences',grid=rows),indent=2))
