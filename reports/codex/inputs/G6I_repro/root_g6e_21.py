
import sys, copy; sys.path.insert(0,'src')
from eab.limit import LimitContact, wrench
from eab.limit_multi import BodyContact, LimitBody, limit_load_multi, check_duality_multi
O2=(0.0,0.0)
for WD in (10.0,1e6,1e9):
    b=[LimitBody(wrench((0.0,-30.0),(0.0,0.5),O2,2),[0.0]*3), LimitBody(wrench((0.0,-10.0),(0.0,1.5),O2,2),wrench((1.0,0.0),(0.0,2.0),O2,2)), LimitBody(wrench((0.0,-WD),(5.0,0.5),O2,2),[0.0]*3)]
    bcs=[BodyContact(LimitContact((sx,0.0),(0.0,1.0),1.2),0,None) for sx in (-1.0,1.0)]+[BodyContact(LimitContact((sx,1.0),(0.0,1.0),1.2),1,0) for sx in (-1.0,1.0)]+[BodyContact(LimitContact((5.0+sx,0.0),(0.0,1.0),1.2),2,None) for sx in (-1.0,1.0)]
    r=limit_load_multi(b,bcs,dim=2)
    lam0=[]
    for n in (20.0,20.0,5.0,5.0,WD/2,WD/2): lam0+=[n/2,n/2]   # dead-only equilibrium, n.g=1 on both cone edges
    rr=copy.copy(r); rr.alpha=0.999*r.alpha; rr.lambdas=[0.999*a+0.001*c for a,c in zip(r.lambdas,lam0)]
    d=check_duality_multi(rr,b,bcs,dim=2)
    print(WD, rr.alpha, d['ok'], d['static_residual_rel'], d['duality_gap_rel'], d['complementarity'], d['upper_bound'])