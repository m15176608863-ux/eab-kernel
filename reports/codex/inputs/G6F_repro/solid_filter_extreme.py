import sys,math,random,json
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.predicates import orient3d,cross2_sign,dot2_sign
from eab.kernel3d.exact_geom import polygon_locate
rng=random.Random(61121)
def sgn(v):return (v>0)-(v<0)
def orient(q):
    a,b,c,p=[[F(x) for x in v] for v in q]
    u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)];w=[p[i]-a[i] for i in range(3)]
    return sgn(u[0]*(v[1]*w[2]-v[2]*w[1])+u[1]*(v[2]*w[0]-v[0]*w[2])+u[2]*(v[0]*w[1]-v[1]*w[0]))
def scalar():
    exp=rng.choice([-1074,-1070,-1022,-600,-200,-50,0,50,200,600,1020])
    return math.ldexp(rng.choice([-1,1])*rng.uniform(.5,1),exp)
cross_bad=dot_bad=orient_bad=0
for i in range(12000):
    a,b=[(scalar(),scalar()) for _ in range(2)]
    cross_bad += cross2_sign(a,b)!=sgn(F(a[0])*F(b[1])-F(a[1])*F(b[0]))
    dot_bad += dot2_sign(a,b)!=sgn(F(a[0])*F(b[0])+F(a[1])*F(b[1]))
    q=[tuple(scalar() for _ in range(3)) for _ in range(4)]
    orient_bad += orient3d(*q)!=orient(q)
print(json.dumps({'samples':12000,'cross_bad':cross_bad,'dot_bad':dot_bad,'orient_bad':orient_bad}))
