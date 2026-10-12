"""New G6J exact product-union stress oracle; no eab truth helpers.

Each simple grid ring is the boundary of an independently retained union of
closed unit squares. Difference-set membership, body state, first entrance and
distance are inline interval-product formulas. Affine shears/rotations are
exact, so transformed Fraction data keep the same mathematical geometry.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
import sys, random, json
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d import covers as C, entrance as E, exact as X, g0_oracle as O

def grid_ring(cells):
    lines=set()
    for x,y in cells:
        corners=((x,y),(x+1,y),(x+1,y+1),(x,y+1))
        for a,b in zip(corners,corners[1:]+corners[:1]):
            if (b,a) in lines:lines.remove((b,a))
            else:lines.add((a,b))
    nxt={}
    for a,b in lines:
        if a in nxt:return None
        nxt[a]=b
    start=min(nxt);cur=start;out=[]
    while cur not in out:
        out.append(cur);cur=nxt[cur]
    return out if cur==start and len(out)==len(lines) else None

def specimen(rng):
    while True:
        cells={(0,0)}
        for _ in range(rng.randrange(1,10)):
            x,y=rng.choice(sorted(cells));dx,dy=rng.choice(((1,0),(-1,0),(0,1),(0,-1)))
            cells.add((x+dx,y+dy))
        ring=grid_ring(cells)
        if ring:return cells,ring

def rectangles(a,b):
    return [(F(qx-px-1),F(qx-px+1),F(qy-py-1),F(qy-py+1))
            for px,py in a for qx,qy in b]

def union_state(rects,p):
    near=[r for r in rects if r[0]<=p[0]<=r[1] and r[2]<=p[1]<=r[3]]
    if not near:return -1
    return 1 if all(any((r[0]<p[0] if dx<0 else p[0]<r[1]) and
                        (r[2]<p[1] if dy<0 else p[1]<r[3]) for r in near)
                   for dx in (-1,1) for dy in (-1,1)) else 0

def body_state(a,b,p):
    widths=[(min(px+1+p[0],qx+1)-max(px+p[0],qx),
             min(py+1+p[1],qy+1)-max(py+p[1],qy))
            for px,py in a for qx,qy in b]
    if any(x>0 and y>0 for x,y in widths):return 1
    return 0 if any(x>=0 and y>=0 for x,y in widths) else -1

def ray(rects,p,d,cap):
    hits=[]
    for r in rects:
        lo=F(0);hi=cap
        for mn,mx,x,v in ((r[0],r[1],p[0],d[0]),(r[2],r[3],p[1],d[1])):
            if v==0:
                if x<mn or x>mx:break
            else:
                s,t=sorted(((mn-x)/v,(mx-x)/v));lo=max(lo,s);hi=min(hi,t)
        else:
            if lo<=hi:hits.append(lo)
    return min(hits) if hits else None

def finite_contact(A,B,x,label):
    aa=[(a+x[0],b+x[1]) for a,b in A]
    def on(p,a,b):
        return (b[0]-a[0])*(p[1]-a[1])==(b[1]-a[1])*(p[0]-a[0]) and all(min(a[k],b[k])<=p[k]<=max(a[k],b[k]) for k in (0,1))
    kind,i,j=label
    if kind=='VE':return on(aa[i],B[j],B[(j+1)%len(B)])
    if kind=='EV':return on(B[j],aa[i],aa[(i+1)%len(aa)])
    a,b=aa[i],aa[(i+1)%len(aa)];c,d=B[j],B[(j+1)%len(B)]
    return any((on(a,c,d),on(b,c,d),on(c,a,b),on(d,a,b)))

def point_segment_square(p,a,b):
    ex,ey=b[0]-a[0],b[1]-a[1];wx,wy=p[0]-a[0],p[1]-a[1]
    t=min(F(1),max(F(0),(wx*ex+wy*ey)/(ex*ex+ey*ey)))
    return (wx-t*ex)**2+(wy-t*ey)**2

def squared_feature(A,B,label):
    kind,i,j=label
    if kind=='VE':return point_segment_square(A[i],B[j],B[(j+1)%len(B)])
    if kind=='EV':return point_segment_square(B[j],A[i],A[(i+1)%len(A)])
    assert kind=='VV'
    return (A[i][0]-B[j][0])**2+(A[i][1]-B[j][1])**2

def boundary_distance_square(A,B):
    return min(point_segment_square(p,q,Q[(j+1)%len(Q)])
               for P,Q in ((A,B),(B,A)) for p in P for j,q in enumerate(Q))

def pose(p,scale,shear,rotation,offset):
    x,y=map(F,p);x=x+shear*y;c,s=rotation
    return (scale*(c*x-s*y)+offset[0],scale*(s*x+c*y)+offset[1])

def main():
    rng=random.Random(10910919)
    counts=dict(pairs=0,membership=0,body=0,independent_g0_oracle=0,entrance=0,finite_labels=0,distance=0,cache=0)
    for case in range(100):
        a,A=specimen(rng);b,B=specimen(rng);rects=rectangles(a,b);counts['pairs']+=1
        transforms=[(F(1),F(0),(F(1),F(0)),(0,0))]
        if case<20:
            transforms += [(F(1,10**9),F(0),(F(3,5),F(4,5)),(10**8,-10**8)),
                           (F(10**8),F(0),(F(3,5),F(4,5)),(10**8,-10**8)),
                           (F(1),F(2**40),(F(1),F(0)),(10**8,-10**8))]
        for scale,shear,rotation,offset in transforms:
            at=[pose(p,scale,shear,rotation,offset) for p in A]
            bt=[pose(p,scale,shear,rotation,offset) for p in B]
            for _ in range(10):
                p=(F(rng.randrange(-10,11),2),F(rng.randrange(-10,11),2))
                d=(F(rng.randrange(-2,3)),F(rng.randrange(-2,3)))
                if d==(0,0):d=(F(1),F(0))
                cap=F(rng.choice((0,1,2,8)))
                pt=pose(p,scale,shear,rotation,(0,0));dt=pose(d,scale,shear,rotation,(0,0))
                want=union_state(rects,p);want_body=body_state(a,b,p)
                assert X.entrance_membership_exact(at,bt,pt)==C.membership_convex(at,bt,pt)==want,('E state',case,p,shear)
                counts['membership']+=2
                assert X.polygons_overlap_exact(at,bt,pt)==want_body,('body state',case,p,shear)
                counts['body']+=1
                shifted=[(x+pt[0],y+pt[1]) for x,y in at]
                assert O.overlap(shifted,bt)==want_body,('independent production G0 oracle',case,p,shear)
                counts['independent_g0_oracle']+=1
                if want_body==-1:
                    expected_square=boundary_distance_square(shifted,bt)
                    covs=C.enumerate_covers(shifted,bt,window=float('inf'))
                    squares=[squared_feature(shifted,bt,v.label()) for v in covs]
                    assert min(squares)==expected_square,('exact distance completeness',case,p,shear,expected_square,min(squares))
                    with localcontext() as decimal_context:
                        decimal_context.prec=1000
                        for cover,square in zip(covs,squares):
                            expected=float((Decimal(square.numerator)/Decimal(square.denominator)).sqrt())
                            assert abs(cover.gap)==expected,('final distance construction',case,cover.label(),cover.gap,expected)
                    counts['distance']+=1
                got=E.first_entrance(at,bt,pt,dt,t_max=cap)
                if want==1:
                    assert got.kind=='exit',('initial int E',case,p,got)
                else:
                    time=ray(rects,p,d,cap)
                    assert (got.kind=='none')==(time is None),('ray kind',case,p,d,cap,time,got)
                    if time is not None:
                        assert got.kind=='entrance' and got.t_exact==time,('ray root',case,p,d,cap,time,got)
                        q=(pt[0]+time*dt[0],pt[1]+time*dt[1])
                        for label in got.tied_labels:
                            assert finite_contact(at,bt,q,label),('finite exact tie',case,p,d,label)
                            counts['finite_labels']+=1
                        assert got.point_a==got.point_b,('coincident final witness',case,got)
                counts['entrance']+=1
    A=[(0,0),(1,0),(1,1),(0,1)];B=[(3,0),(4,0),(4,1),(3,1)]
    C.enumerate_covers(A,B,window=10)
    A[1]=(F(5,4),0)
    old=C.enumerate_covers(A,B,window=10);fresh=C.enumerate_covers(list(A),list(B),window=10)
    assert old==fresh
    old[0].gap=999
    assert all(v.gap!=999 for v in C.enumerate_covers(A,B,window=10))
    counts['cache']=2
    print(json.dumps({'status':'PASS','seed':10910919,'counts':counts,'zero_confirmed_disagreements':True},indent=2))

if __name__=='__main__':main()
