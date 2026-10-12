"""Independent integer/Fraction arithmetic checks; no production geometry oracle.

Run from repository root with PYTHONDONTWRITEBYTECODE=1 python -X utf8.
The finite deterministic grid is not a formal proof of every error bound.
"""
from pathlib import Path
from fractions import Fraction as F
import itertools
import json
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from eab.predicates import cross2_sign, dot2_sign, orient3d
from eab.kernel2d.geom import orient2d
from eab.kernel3d.exact_geom import polygon_locate, _iv
from eab.lp import _Exact, _fl

def sign(x):
    return (x > 0) - (x < 0)

def determinant3(a, b, c, p):
    u, v, w = [tuple(F(x)-F(y) for x,y in zip(q,a)) for q in (b,c,p)]
    return sign(u[0]*(v[1]*w[2]-v[2]*w[1])
                - u[1]*(v[0]*w[2]-v[2]*w[0])
                + u[2]*(v[0]*w[1]-v[1]*w[0]))

def locate_xy(p, vertices, tol):
    p = tuple(map(F,p)); vertices = [tuple(map(F,v)) for v in vertices]; tol=F(tol)
    winding=0
    for a,b in zip(vertices,vertices[1:]+vertices[:1]):
        u=tuple(y-x for x,y in zip(a,b)); w=tuple(x-y for x,y in zip(p,a))
        uu=sum(x*x for x in u); wu=sum(x*y for x,y in zip(w,u))
        t=max(F(0),min(F(1),wu/uu)) if uu else F(0)
        d2=sum((w[i]-t*u[i])**2 for i in range(3))
        if d2 <= tol*tol: return 0
        cross=u[0]*w[1]-u[1]*w[0]
        if a[1] <= p[1] < b[1] and cross > 0: winding+=1
        if b[1] <= p[1] < a[1] and cross < 0: winding-=1
    return 1 if winding else -1

def main():
    start=time.perf_counter(); rng=random.Random(11002); counts={}; failures=[]
    def record(kind, inp, got, expected):
        counts[kind]=counts.get(kind,0)+1
        if got != expected and len(failures)<30:
            failures.append(dict(kind=kind,input=repr(inp),got=got,expected=expected))
    # Ordinary int, float, rational and mixtures, with cancellation near 2**53.
    for exponent in (0, 53, 54, 100, 500, 1000, 2000):
        N=2**exponent
        for _ in range(400):
            values=[N+rng.randrange(-16,17),rng.randrange(-16,17),F(N)+F(rng.randrange(-16,17),3),F(rng.randrange(-16,17),7)]
            for i in range(4):
                if rng.randrange(2) and abs(values[i]) < 2**1023: values[i]=float(values[i])
            a,b=values[:2],values[2:]
            record('cross2',values,cross2_sign(a,b),sign(F(a[0])*F(b[1])-F(a[1])*F(b[0])))
            record('dot2',values,dot2_sign(a,b),sign(F(a[0])*F(b[0])+F(a[1])*F(b[1])))
        for dx,dy in itertools.product(range(1,9),repeat=2):
            a=(N+dx,3.0);b=(N+dy,4.0);c=(F(N),0.0) if exponent>1023 else (float(N),0.0)
            det=(F(b[0])-F(a[0]))*(F(c[1])-F(a[1]))-(F(b[1])-F(a[1]))*(F(c[0])-F(a[0]))
            record('orient2d',(a,b,c),orient2d(a,b,c),sign(det))
            points=(a+(0.0,), b+(0,), c+(0,), (N,0.0,1.0))
            record('orient3d',points,orient3d(*points),determinant3(*points))
    # Interval endpoints must enclose the exact supplied value, including overflow/underflow.
    values=[0,1,-1,2**53+1,2**2000,F(1,2**2000),F(-1,2**2000),F(2**54+1,3),5e-324]
    for x in values:
        lo,hi=_iv(x)
        record('interval',x,lo <= x <= hi,True)
    # XY polygon tests at large mixed-type coordinates, independent squared distance/winding.
    for e in (0,53,54,100,500,1000,2000):
        N=2**e
        vertices=[(N,0.,0),(N+7,F(0),0.),(N+9,11,0),(N,12.,0)]
        for dx,dy,tol in itertools.product(range(-1,11),range(-1,14),(0,F(1,3))):
            p=(N+dx,F(dy,1),0.)
            record('polygon_locate',(e,p,tol),polygon_locate(p,vertices,tol),locate_xy(p,vertices,tol))
    # Reduced-cost filter: constructor rationalizes inputs first; compare direct exact arithmetic.
    exponents=(-1100,-1074,-1000,-53,0,53,1000,1100)
    for _ in range(1000):
        m=3
        A=[[F(rng.randrange(-7,8))*F(2)**rng.choice(exponents)] for i in range(m)]
        y=[F(rng.randrange(-7,8))*F(2)**rng.choice(exponents) for i in range(m)]
        c=[sum(y[i]*A[i][0] for i in range(m))+F(rng.randrange(-1,2))*F(2)**rng.choice(exponents)]
        model=_Exact(A,[1]*m,c)
        got=model.reduced_sign(c,[_fl(v) for v in c],y,[_fl(v) for v in y],0)[0]
        record('reduced_sign',(A,y,c),got,sign(c[0]-sum(y[i]*A[i][0] for i in range(m))))
    result={'counts':counts,'failures':failures,'elapsed_seconds':time.perf_counter()-start,
            'oracle':'independent Fraction determinant, bilinear expression, squared distance/winding and reduced cost; interval enclosure directly compared to exact supplied scalar'}
    output=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('numeric_probe_results.json')
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return bool(failures)

if __name__=='__main__':
    raise SystemExit(main())
