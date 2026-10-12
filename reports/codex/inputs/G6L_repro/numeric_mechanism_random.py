from pathlib import Path
from fractions import Fraction as F
import sys,random,math,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
import eab.limit as L
rng=random.Random(1202)
for k in range(100):
 cs=[L.LimitContact((x,rng.random()/10.),(rng.random()/5.,1.),.2+rng.random()) for x in (-1.,1.)];dead=[0.,-10.,0.];live=[1.,0.,-.5];r=L.limit_load(cs,dead,live,dim=2)
 if r.status!='optimal':continue
 for ct in cs:
  for g in L.friction_generators(ct.normal,ct.mu,2):
   wx=(F(g[0]),F(g[1]),F(ct.point[0])*F(g[1])-F(ct.point[1])*F(g[0]));exact=sum(x.exact*w for x,w in zip(r.mechanism,wx));got=L.mechanism_power(r.mechanism,ct,g,(0.,0.),2)
   if (got>0)-(got<0)!=(exact>0)-(exact<0):
    print(json.dumps({'case':k,'cts':[(c.point,c.normal,c.mu) for c in cs],'mechanism_float':list(r.mechanism),'mechanism_exact':[str(x.exact) for x in r.mechanism],'g':g,'got':got,'want':str(exact)},indent=2));sys.exit(0)
