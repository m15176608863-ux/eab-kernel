from pathlib import Path
from fractions import Fraction as F
import sys,itertools,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
import eab.limit as L
for mu,h in itertools.product([.2,.3,.6,1e-5],[.5,3.,1000.]):
 cs=[L.LimitContact((x,0.),(0.,1.),mu) for x in (-1.,1.)];dead=[0.,-10.,0.];live=[1.,0.,-h];r=L.limit_load(cs,dead,live,dim=2)
 for ct in cs:
  for g in L.friction_generators(ct.normal,ct.mu,2):
   exact=sum(x.exact*w for x,w in zip(r.mechanism,(F(g[0]),F(g[1]),F(ct.point[0])*F(g[1])-F(ct.point[1])*F(g[0]))))
   got=L.mechanism_power(r.mechanism,ct,g,(0.,0.),2)
   if (got>0)-(got<0)!=(exact>0)-(exact<0): print(mu,h,[repr(x) for x in r.mechanism],g,'got',got,'want',exact)
