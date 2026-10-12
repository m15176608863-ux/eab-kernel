"""WO-G6M independent exact numeric/filtered-face pressure oracle.

Oracle has its own Fraction determinant expansion, scalar dot, line distance
and horizontal-ray winding. No production oracle/helper is used for truth.
Seeds are G6M-specific; arbitrary rationals and mixed huge ints are retained.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,random,math,json,time
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT/'src'))
from eab.predicates import cross2_sign,dot2_sign,orient3d
from eab.kernel2d.geom import orient2d
from eab.kernel3d.exact_geom import polygon_locate
from eab import predicates as P
FALLBACK_COUNTS={'float_only':0,'mixed_exact':0}
_original_o3_fraction=P.orient3d_fraction
def _observed_o3_fallback(*points):
    key='float_only' if all(type(v) is float for p in points for v in p) else 'mixed_exact'
    FALLBACK_COUNTS[key]+=1
    return _original_o3_fraction(*points)
P.orient3d_fraction=_observed_o3_fallback

def sg(x):return (x>0)-(x<0)
def determinant(a,b,c,p):
    rows=[[F(q[k])-F(a[k]) for k in range(3)] for q in (b,c,p)]
    x,y,z=rows
    return x[0]*(y[1]*z[2]-y[2]*z[1])-x[1]*(y[0]*z[2]-y[2]*z[0])+x[2]*(y[0]*z[1]-y[1]*z[0])
def face_truth(query,points,tol):
    # Horizontal-ray polygon oracle on a declared z=constant simple ring.
    q=tuple(F(x) for x in query);pts=[tuple(F(x) for x in p) for p in points];t=F(tol)
    hits=0
    for a,b in zip(pts,pts[1:]+pts[:1]):
        vx,vy=b[0]-a[0],b[1]-a[1];wx,wy=q[0]-a[0],q[1]-a[1]
        length=vx*vx+vy*vy;h=max(F(0),min(F(1),(wx*vx+wy*vy)/length)) if length else F(0)
        distance=(wx-h*vx)**2+(wy-h*vy)**2+(q[2]-a[2])**2
        if distance<=t*t:return 0
        if (a[1]>q[1])!=(b[1]>q[1]):
            x=a[0]+(q[1]-a[1])*(b[0]-a[0])/(b[1]-a[1])
            if x>q[0]:hits+=1
    return 1 if hits%2 else -1
def main():
    rng=random.Random(130502);counts={};errors=[];started=time.perf_counter()
    exponents=[-1074,-1073,-1050,-1022,-1000,-700,-540,-537,-512,-160,-30,0,30,512,700,1000,1023]
    def scalar():
        e=rng.choice(exponents);sign=rng.choice((-1,1));v=math.ldexp(rng.randrange(1,9)/8,e)*sign
        if rng.randrange(4)==0:return F(v)+F(sign,2**rng.randrange(20,1200))
        if rng.randrange(12)==0:return rng.choice((-1,1))*2**rng.randrange(54,1500)+rng.randrange(-9,10)
        return v
    def check(api,want,args):
        counts[api.__name__]=counts.get(api.__name__,0)+1
        got=api(*args)
        if got!=want:errors.append(dict(api=api.__name__,input=repr(args),expected=want,got=got))
    for k in range(18000):
        a,b=[tuple(scalar() for _ in range(2)) for _ in range(2)]
        check(cross2_sign,sg(F(a[0])*F(b[1])-F(a[1])*F(b[0])),(a,b))
        check(dot2_sign,sg(F(a[0])*F(b[0])+F(a[1])*F(b[1])),(a,b))
        c=tuple(scalar() for _ in range(2))
        q=(F(a[0])-F(c[0]))*(F(b[1])-F(c[1]))-(F(a[1])-F(c[1]))*(F(b[0])-F(c[0]))
        check(orient2d,sg(q),(a,b,c))
        if k<9000:
            pts=[tuple(scalar() for _ in range(3)) for _ in range(4)]
            check(orient3d,sg(determinant(*pts)),tuple(pts))
    # Correlated cancellation and subnormal differences; ordinary float filter.
    for k in range(9000):
        e=rng.randrange(-1070,1000);base=math.ldexp(rng.randrange(1,9)/8,e)
        a=(base,math.nextafter(base,math.inf));b=(math.nextafter(base,0),base)
        check(cross2_sign,sg(F(a[0])*F(b[1])-F(a[1])*F(b[0])),(a,b))
        if k<3000:
            pts=[(base,base,base),(math.nextafter(base,math.inf),base,base),(base,math.nextafter(base,0),base),(base,base,math.nextafter(base,math.inf))]
            check(orient3d,sg(determinant(*pts)),tuple(pts))
    # The projected plane window has different arithmetic from sign filters.
    shape=[(F(0),F(0)),(F(4),F(0)),(F(4),F(1)),(F(1),F(1)),(F(1),F(4)),(F(0),F(4))]
    for k in range(3600):
        scale=F(2)**rng.choice(exponents);ox=F(2)**rng.choice((0,30,512,1000));oy=-ox;z=F(1,7)
        ring=[(ox+scale*x,oy+scale*y,z) for x,y in shape]
        x,y=F(rng.randrange(-8,41),8),F(rng.randrange(-8,41),8)
        if k%6==0:x=F(1)+F(1,2**100)
        query=(ox+scale*x,oy+scale*y,z);tol=scale*rng.choice((F(0),F(1,16),F(1,4)))
        check(polygon_locate,face_truth(query,ring,tol),(query,ring,tol))
    out=dict(seed=130502,counts=counts,total=sum(counts.values()),orient3d_fallback_counts=FALLBACK_COUNTS,
        orient3d_accepted_fast_filter=counts['orient3d']-sum(FALLBACK_COUNTS.values()),errors=errors,seconds=time.perf_counter()-started,
        oracle='independent Fraction expanded determinants; independent horizontal-ray parity and closed-edge projection distance')
    path=ROOT/'review/geometry/numeric_pressure.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
    assert not errors,errors[:3]
if __name__=='__main__':main()
