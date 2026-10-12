"""WO-G6I: raw rectangle-union oracle; never calls eab geometry for truth."""
from pathlib import Path
from fractions import Fraction as F
import sys,random,json,math
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'src'), str(ROOT/'tests')]
from test_r9fix_entrance_domain import _assert_contact_labels
from eab.kernel2d.exact import entrance_membership_exact, polygons_overlap_exact
from eab.kernel2d.covers import membership_convex,enumerate_covers
from eab.kernel2d.entrance import first_entrance

def ring(cells):
    edges=set()
    for x,y in cells:
        corners=((x,y),(x+1,y),(x+1,y+1),(x,y+1))
        for a,b in zip(corners,corners[1:]+corners[:1]):
            if (b,a) in edges: edges.remove((b,a))
            else:edges.add((a,b))
    nxt={}
    for a,b in edges:
        if a in nxt:return None
        nxt[a]=b
    out=[];cur=min(nxt)
    while cur not in out:
        out.append(cur);cur=nxt[cur]
    if cur!=out[0] or len(out)!=len(edges):return None
    # Keep flat vertices deliberately: triangulation and topological cells use them.
    return out

def gen(rng):
    for _ in range(100):
        cells={(0,0)}
        for _ in range(rng.randrange(1,8)):
            x,y=rng.choice(sorted(cells));dx,dy=rng.choice(((1,0),(-1,0),(0,1),(0,-1)))
            cells.add((x+dx,y+dy))
        P=ring(cells)
        if P is not None:return cells,P
    raise AssertionError('random generator exhausted')

def products(A,B):
    # conv([a,a+1]^2) differences are exactly [b-a-1,b-a+1]^2.
    return [(F(bx-ax-1),F(bx-ax+1),F(by-ay-1),F(by-ay+1))
            for ax,ay in A for bx,by in B]

def state(E,x):
    # A finite product-cell union covers a neighborhood iff all 4 quadrant sectors do.
    containing=[r for r in E if r[0]<=x[0]<=r[1] and r[2]<=x[1]<=r[3]]
    if not containing:return -1
    inside=all(any((r[0]<x[0] if dx<0 else x[0]<r[1]) and
                   (r[2]<x[1] if dy<0 else x[1]<r[3]) for r in containing)
               for dx in (-1,1) for dy in (-1,1))
    return 1 if inside else 0

def body_state(A,B,x):
    touch=False
    for ax,ay in A:
        for bx,by in B:
            widths=(min(ax+1+x[0],bx+1)-max(ax+x[0],bx),
                    min(ay+1+x[1],by+1)-max(ay+x[1],by))
            if min(widths)>0:return 1
            if min(widths)==0:touch=True
    return 0 if touch else -1

def earliest(E,x,d):
    hits=[]
    for lo,hi,bot,top in E:
        tlo=F(0);thi=None
        for a,b,p,v in ((lo,hi,x[0],d[0]),(bot,top,x[1],d[1])):
            if not v:
                if not a<=p<=b:break
            else:
                ts=sorted(((a-p)/v,(b-p)/v));tlo=max(tlo,ts[0]);thi=ts[1] if thi is None else min(thi,ts[1])
        else:
            if thi is None or tlo<=thi:hits.append(tlo)
    return min(hits) if hits else None

def transform(P,s,c,t):
    co,si=c
    return [(s*(co*x-si*y)+t[0],s*(si*x+co*y)+t[1]) for x,y in P]

def product_distance2(A,B,x):
    values=[]
    for ax,ay in A:
        for bx,by in B:
            dx=max(F(bx)-F(ax+1)-x[0],F(ax)+x[0]-F(bx+1),F(0))
            dy=max(F(by)-F(ay+1)-x[1],F(ay)+x[1]-F(by+1),F(0))
            values.append(dx*dx+dy*dy)
    return min(values)

def segment2(p,a,b):
    ex,ey=b[0]-a[0],b[1]-a[1];wx,wy=p[0]-a[0],p[1]-a[1]
    parameter=min(F(1),max(F(0),(wx*ex+wy*ey)/(ex*ex+ey*ey)))
    return (wx-parameter*ex)**2+(wy-parameter*ey)**2

def cover2(c,A,B):
    if c.kind=='VE':return segment2(A[c.a_index],B[c.b_index],B[(c.b_index+1)%len(B)])
    if c.kind=='EV':return segment2(B[c.b_index],A[c.a_index],A[(c.a_index+1)%len(A)])
    return sum((A[c.a_index][k]-B[c.b_index][k])**2 for k in (0,1))

def run():
    rng=random.Random(930193)
    counts={'pairs':0,'members':0,'body':0,'entrance':0,'distance':0,'cache':0}
    nonmatches=[]
    for case in range(150):
        Ac,A=gen(rng);Bc,B=gen(rng);E=products(Ac,Bc);counts['pairs']+=1
        scales=(F(1),F(1,10**9),F(10**8)) if case<15 else (F(1),)
        for s in scales:
            # Rational transformations preserve the original exact geometry, unlike float-motion comparisons.
            c=(F(3,5),F(4,5)) if case%2 else (F(1),F(0));t=(F(10**8),F(-10**8)) if case%3 else (F(0),F(0))
            At,Bt=transform(A,s,c,t),transform(B,s,c,t)
            for j in range(12):
                x=(F(rng.randrange(-8,9),2),F(rng.randrange(-8,9),2));xt=transform([x],s,c,(F(0),F(0)))[0]
                expected=state(E,x);actual=entrance_membership_exact(At,Bt,xt)
                assert expected==actual,('E-membership',case,Ac,Bc,x,expected,actual)
                assert membership_convex(At,Bt,xt)==expected
                counts['members']+=2
                bs=body_state(Ac,Bc,x)
                assert polygons_overlap_exact(At,Bt,xt)==bs
                counts['body']+=1
                if bs==-1:
                    shifted=[(p[0]+xt[0],p[1]+xt[1]) for p in At]
                    covers=enumerate_covers(shifted,Bt,window=float('inf'))
                    exact_min=min((cover2(cc,shifted,Bt) for cc in covers),default=None)
                    expected_min=s*s*product_distance2(Ac,Bc,x)
                    assert exact_min==expected_min,('distance-completeness',case,x,expected_min,exact_min)
                    counts['distance']+=1
                d=(F(rng.randrange(-2,3)),F(rng.randrange(-2,3)))
                if d==(0,0):d=(F(1),F(0))
                dt=transform([d],s,c,(F(0),F(0)))[0]
                try:out=first_entrance(At,Bt,xt,dt)
                except ArithmeticError as err:
                    if 'face witness has no segment overlap' not in str(err):raise
                    nonmatches.append({'case':case,'exception':str(err),'A':A,'B':B,'x':str(x),'d':str(d)})
                    continue
                if expected==1:
                    assert out.kind=='exit',('policy',case,x,out)
                else:
                    et=earliest(E,x,d)
                    assert (out.kind=='none')==(et is None),('entrance-kind',case,Ac,Bc,x,d,et,out)
                    if et is not None:
                        assert out.kind=='entrance' and out.t_exact==et,('entrance-time',case,x,d,et,out)
                        _assert_contact_labels(At,Bt,tuple(xt[i]+et*dt[i] for i in (0,1)),out)
                counts['entrance']+=1
    # Point-content caches cannot be poisoned by source list mutation or aliases.
    A=[(F(0),F(0)),(F(1),F(0)),(F(1),F(1)),(F(0),F(1))]
    B=[(F(3),F(0)),(F(4),F(0)),(F(4),F(1)),(F(3),F(1))]
    enumerate_covers(A,B,window=float('inf'))
    A[1]=(F(2),F(0))
    mutated=enumerate_covers(A,B,window=float('inf'))
    fresh=enumerate_covers(list(A),list(B),window=float('inf'))
    assert [repr(z) for z in mutated]==[repr(z) for z in fresh]
    # Return Cover objects are not reused by caches.
    mutated[0].gap=999
    repeat=enumerate_covers(A,B,window=float('inf'))
    assert all(z.gap!=999 for z in repeat)
    counts['cache']+=2
    assert not nonmatches, ('no remaining finite-domain exceptions', nonmatches)
    return {'counts':counts,'known_finite_facet_domain_errors':nonmatches}

if __name__=='__main__':
    out=run();print(json.dumps({'status':'SEARCH_COMPLETE','counts':out},indent=2))
