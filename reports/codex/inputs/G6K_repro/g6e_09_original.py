import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
import sys, math; sys.path.insert(0,'src')
from eab.limit import LimitContact, limit_load, wrench, _tangents
O=(0.0,0.0,0.0); n=tuple(v/math.sqrt(3) for v in (1.0,1.0,1.0)); e1=tuple(v/math.sqrt(2) for v in (1.0,-1.0,0.0))
e2=(n[1]*e1[2]-n[2]*e1[1], n[2]*e1[0]-n[0]*e1[2], n[0]*e1[1]-n[1]*e1[0])
pt=lambda a,b,h=0.0: tuple(a*e1[i]+b*e2[i]+h*n[i] for i in range(3))
bad=(1.0,1.0,1.0+2**-50)
try:
 t1,t2=_tangents(n,3,bad)
 print('UNEXPECTED bad tangent accepted',sum(a*b for a,b in zip(n,t1)))
 raise AssertionError('bad tangent must be rejected')
except ValueError:
 print('bad tangent rejected')
push=tuple(math.cos(math.radians(270))*e1[i]+math.sin(math.radians(270))*e2[i] for i in range(3))
for name,tg in (('valid',e1),('bad',bad)):
    cts=[LimitContact(pt(sx,0.6*sy), n, 1.0, tangent=tg) for sx in (-1.0,1.0) for sy in (-1.0,1.0)]
    dead=wrench(tuple(-10.0*v for v in n), pt(0,0,0.5), O, 3); live=wrench(push, pt(0,0,0.2), O, 3)
    try:
        r=limit_load(cts, dead, live, dim=3, k=8); print(name, r.status, r.alpha, 'exact cone = 10.0')
    except ValueError:
        assert name=='bad';print(name,'rejected')