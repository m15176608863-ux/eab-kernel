
import sys; from math import sin, cos; sys.path.insert(0,'src')
from eab.limit import LimitContact, wrench, limit_load
from eab.limit_multi import BodyContact, LimitBody, limit_load_multi
O2=(0.0,0.0)
def run(f):
    try: r=f(); return (r.status, r.alpha, r.uncertainty)
    except RuntimeError as e: return ('raise', str(e)[:60])
for v in (1e-6,1e-8):
    ct=LimitContact((1.0,0.0),(sin(1.2),cos(1.2)),1.0)
    body=LimitBody(wrench((0.0,-1.0),(0.0,0.7),O2,2),wrench((-1.0,v),(0.0,0.0),O2,2))
    print(v,'single',run(lambda: limit_load([ct],body.dead,body.live,dim=2)))
    for D in (None,1e2,1e4,1e6):
        bodies,bcs=[body],[BodyContact(ct,0,None)]
        if D is not None:
            bodies=bodies+[LimitBody(wrench((0.0,-10.0),(D,0.5),O2,2),[0.0]*3)]
            bcs=bcs+[BodyContact(LimitContact((D+sx,0.0),(0.0,1.0),0.5),1,None) for sx in (-0.5,0.5)]
        print('   far block D=',D,run(lambda: limit_load_multi(bodies,bcs,dim=2)))