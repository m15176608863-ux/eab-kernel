import sys, copy
import eab.limit as LM
from eab.limit import LimitContact, limit_load, check_duality, wrench
O=(0.0,0.0)
def slide(mu, W=10.0):
    cts=[LimitContact((-1.0,0.0),(0.0,1.0),mu), LimitContact((1.0,0.0),(0.0,1.0),mu)]
    return cts, wrench((0.0,-W),(0.0,0.5),O,2), wrench((1.0,0.0),(0.0,0.5),O,2)
real=LM.maximize
def skew(A,b,c,**kw):
    res=real(A,b,c,**kw)
    if res.status=='optimal':
        ia=[j for j,cj in enumerate(c) if cj!=0.0][0]; res.x=list(res.x); res.x[ia]*=0.999
    return res
LM.maximize=skew
for mu in (0.4,1e-3,1e-4,1e-5):
    try: print(mu, 'RETURNED', limit_load(*slide(mu), dim=2).alpha, 'true', mu*10)
    except RuntimeError: print(mu, 'raised')
LM.maximize=real
cts=[LimitContact((-1.0,0.0),(0.0,1.0),0.0,cohesion=5.0,area=1.0), LimitContact((1.0,0.0),(0.0,1.0),0.0,cohesion=5.0,area=1.0)]
dead=wrench((0.0,-1e6),(0.0,0.5),O,2); live=wrench((1.0,0.0),(0.0,0.5),O,2)
r=limit_load(cts,dead,live,dim=2)
for f in (0.999,0.99,0.9):
    rr=copy.copy(r); rr.alpha=r.alpha*f; d=check_duality(rr,cts,dead,live,dim=2); print('cA=10,W=1e6 factor',f,'ok=',d['ok'], d['static_residual_rel'], d['duality_gap_rel'])