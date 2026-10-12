"""Independent Fraction product-cell/SAT/distance/line-interval 2D pressure.

No tested geometric primitive, g0_oracle, or existing test oracle is imported.
Source geometries are Cartesian products (L/U unions); rational similarities
preserve the independently known cell union. Both actual float data and exact
rational translated/rotated/unit inputs are checked.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
import random,sys,json,math
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d import geom,exact,covers,g0,entrance

def rectangle(c):
    x0,x1,y0,y1=c;return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
def state(A,cells,x):
    P=[(F(a)+F(x[0]),F(b)+F(x[1])) for a,b in A];statuses=[]
    for Q in cells:
        status=1
        for R in (P,Q):
            for a,b in zip(R,R[1:]+R[:1]):
                nx,ny=F(b[1])-F(a[1]),F(a[0])-F(b[0])
                p=[nx*F(v[0])+ny*F(v[1]) for v in P];q=[nx*F(v[0])+ny*F(v[1]) for v in Q]
                height=min(max(p),max(q))-max(min(p),min(q))
                status=min(status,(height>0)-(height<0))
        statuses.append(status)
    return max(statuses)
def squared_distance(A,B,x):
    P=[(F(a)+F(x[0]),F(b)+F(x[1])) for a,b in A];Q=[tuple(map(F,p)) for p in B]
    values=[]
    for V,W in ((P,Q),(Q,P)):
        for p in V:
            for a,b in zip(W,W[1:]+W[:1]):
                ex,ey=b[0]-a[0],b[1]-a[1];wx,wy=p[0]-a[0],p[1]-a[1]
                length=ex*ex+ey*ey
                t=min(F(1),max(F(0),(wx*ex+wy*ey)/length))
                values.append((wx-t*ex)**2+(wy-t*ey)**2)
    return min(values)
def sqrt_ref(square):
    with localcontext() as ctx:
        ctx.prec=160
        return float((Decimal(square.numerator)/Decimal(square.denominator)).sqrt())
def first_contact(cells,Arect,x,d):
    xmin,xmax,ymin,ymax=Arect;times=[]
    for bx0,bx1,by0,by1 in cells:
        lo,hi=F(0),None
        for c,v,a,b in zip(x,d,(F(bx0)-F(xmax),F(by0)-F(ymax)),(F(bx1)-F(xmin),F(by1)-F(ymin))):
            if not v:
                if not a<=c<=b:lo=None;break
            else:
                l,h=sorted(((a-c)/v,(b-c)/v));lo=max(lo,l);hi=h if hi is None else min(hi,h)
        if lo is not None and (hi is None or lo<=hi):times.append(lo)
    return min(times,default=None)

S=[(F(1,5),F(-1,10)),(F(3,5),F(-1,10)),(F(3,5),F(3,10)),(F(1,5),F(3,10))]
cases=[('L',[(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)],[(0,3,0,1),(0,1,1,3)]),('U',[(-1,-1),(2,-1),(2,2),(1,2),(1,0),(0,0),(0,2),(-1,2)],[(-1,2,-1,0),(-1,0,0,2),(1,2,0,2)])]
rng=random.Random(6182026);counts={'member':0,'geom_overlap':0,'distance':0,'entrance':0,'g0_distance':0,'g0_exit':0,'orient2d':0};issues=[]
for name,baseB,basecells in cases:
    for power in (-600,-30,0,30,600):
        scale=F(2)**power
        for rotated in (False,True):
            for offset in (F(0),F(10**8)):
                def vector(p):
                    x,y=map(F,p)
                    return (scale*(3*x-4*y)/5,scale*(4*x+3*y)/5) if rotated else (scale*x,scale*y)
                def point(p):
                    x,y=vector(p);return (x+offset,y-2*offset)
                A=list(map(point,S));B=list(map(point,baseB));cells=[list(map(point,rectangle(c))) for c in basecells]
                for k in range(12):
                    x=(F(rng.randrange(-32,33),8),F(rng.randrange(-32,33),8));X=vector(x)
                    truth=state(A,cells,X)
                    actual=covers.membership_convex(A,B,X)
                    assert truth==actual,(name,power,rotated,offset,x,truth,actual)
                    counts['member']+=1
                    translated=[(a[0]+X[0],a[1]+X[1]) for a in A]
                    assert geom.polygons_overlap(translated,B)==truth
                    counts['geom_overlap']+=1
                    if truth==-1:
                        square=squared_distance(A,B,X);want=sqrt_ref(square);got=g0.brute_polygon_distance(translated,B)[0]
                        assert got==want,(got,want)
                        counts['distance']+=1
                        d=(F(rng.randrange(-8,9)),F(rng.randrange(-8,9)))
                        if d==(0,0):d=(F(1),F(0))
                        D=vector(d);t=first_contact(basecells,(F(1,5),F(3,5),F(-1,10),F(3,10)),x,d)
                        result=entrance.first_entrance(A,B,X,D)
                        assert (result.kind=='none')==(t is None),(name,x,d,t,result)
                        if t is not None:assert result.kind=='entrance' and result.t_exact==t,(name,x,d,t,result)
                        counts['entrance']+=1
                        if k==0:
                            report=g0.g0_distance_completeness(A,B,[X]);assert report.samples==1 and report.passed,report
                            counts['g0_distance']+=1
                    elif truth==1 and k==0:
                        report=g0.g0_exit_completeness(A,B,[X],[vector((1,-1))]);assert report.samples==1 and report.passed,report
                        counts['g0_exit']+=1
# Actual binary64 orientation stress across range, independently exact determinant.
for i in range(12000):
    power=rng.randrange(-1074,1024)
    s=math.ldexp(1.,power)
    xyz=[(rng.choice([-1.,0.,1.])*s,rng.choice([-1.,0.,1.])*s) for _ in range(3)]
    a,b,c=xyz;det=(F(b[0])-F(a[0]))*(F(c[1])-F(a[1]))-(F(b[1])-F(a[1]))*(F(c[0])-F(a[0]))
    want=(det>0)-(det<0);got=geom.orient2d(*xyz)
    assert want==got,(power,xyz,want,got)
    counts['orient2d']+=1
out={'counts':counts,'issues':issues,'independence':'inline Fraction SAT on independently supplied Cartesian product cells; exact segment projections; motion intervals computed from rectangle sums; no library oracles reused','seed':6182026,'scale_exponents':[-600,-30,0,30,600],'translations':[0,100000000],'rational_rotation':[3,4,5]}
print(json.dumps(out,ensure_ascii=False,indent=2))
(ROOT/'review/agents/geom2/independent_pressure.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
