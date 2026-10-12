
import sys, copy, math; sys.path.insert(0,'src')
from eab.limit import LimitContact, wrench
from eab.limit_multi import BodyContact, LimitBody, limit_load_multi, check_duality_multi, mechanism_is_admissible_multi
O2=(0.0,0.0); D=10.0
b=[LimitBody(wrench((0.0,-30.0),(0.0,0.5),O2,2),[0.0]*3), LimitBody(wrench((0.0,-10.0),(0.0,1.5),O2,2),wrench((1.0,0.0),(0.0,2.0),O2,2)), LimitBody(wrench((0.0,-10.0),(D,0.5),O2,2),[0.0]*3)]
bcs=[BodyContact(LimitContact((sx,0.0),(0.0,1.0),1.2),0,None) for sx in (-1.0,1.0)]+[BodyContact(LimitContact((sx,1.0),(0.0,1.0),1.2),1,0) for sx in (-1.0,1.0)]+[BodyContact(LimitContact((D+sx,0.0),(0.0,1.0),0.0),2,None) for sx in (-1.0,1.0)]
r=limit_load_multi(b,bcs,dim=2); y=r.mechanisms[1]
sp=max(math.hypot(y[0]-y[2]*p[1],y[1]+y[2]*p[0]) for p in ((-1.0,1.0),(1.0,1.0)))
for VD in (0.0,1e3,1e5):
    m=[list(v) for v in r.mechanisms]; m[1][1]-=1e-3*sp; m[2]=[VD*sp,0.0,0.0]
    rr=copy.copy(r); rr.mechanisms=m; d=check_duality_multi(rr,b,bcs,dim=2)
    print(VD, mechanism_is_admissible_multi(m,bcs,dim=2), d['ok'], d['worst_power_rel'])