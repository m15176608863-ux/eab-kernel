"""G6F independent exact stress: own interval-product/2D winding oracles.

No production geometry primitive appears on the oracle side. Inputs are valid
outward embedded surfaces; no repository files are modified.
"""
from fractions import Fraction as F
from pathlib import Path
import itertools, json, math, random, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import Polyhedron, polyhedra_overlap, point_in_polyhedron
from eab.kernel3d.exact_geom import polygon_locate
from eab.kernel3d.exact_sweep import contact_models
from eab.margin import inflated_membership

FACES=((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))
SIGNS=((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))
def make_box(intervals):
    return Polyhedron([tuple(intervals[k][int(s[k]>0)] for k in range(3)) for s in SIGNS], list(FACES))
def prism(ring):
    n=len(ring)
    vertices=[(F(x),F(y),F(z)) for z in (-1,1) for x,y in ring]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n))
    return Polyhedron(vertices,faces)
def state_boxes(a,b):
    widths=[min(x[1],y[1])-max(x[0],y[0]) for x,y in zip(a,b)]
    return -1 if min(widths)<0 else 0 if min(widths)==0 else 1
def state_union(a,rectangles):
    return max(state_boxes(a,b) for b in rectangles)
def transform(P, permutation, scale, origin):
    # Even cyclic permutations are proper rotations; all arithmetic is exact.
    return Polyhedron([tuple(origin[k]+scale*F(p[permutation[k]]) for k in range(3)) for p in P.verts],P.faces)
def interval_vertices(P):
    rows=tuple((min(p[k] for p in P.verts),max(p[k] for p in P.verts)) for k in range(3))
    assert set(map(tuple,P.verts)) == set(itertools.product(*rows))
    return rows

def surface_grid():
    l=prism([(0,0),(2,0),(2,1),(1,1),(1,2),(0,2)])
    lu=[((F(0),F(2)),(F(0),F(1)),(F(-1),F(1))),((F(0),F(1)),(F(1),F(2)),(F(-1),F(1)))]
    o=make_box(((-2,2),)*3); i=make_box(((-1,1),)*3)
    shell=Polyhedron(o.verts+i.verts,o.faces+[tuple(j+8 for j in reversed(f)) for f in i.faces])
    shellboxes=[((-2,-1),(-2,2),(-2,2)),((1,2),(-2,2),(-2,2)),((-1,1),(-2,-1),(-2,2)),((-1,1),(1,2),(-2,2)),((-1,1),(-1,1),(-2,-1)),((-1,1),(-1,1),(1,2))]
    rng=random.Random(6076)
    queries=[((-F(1),F(1)),)*3,((F(-1,2),F(1,2)),)*3,((F(1),F(3,2)),)*3,((F(1),F(2)),)*3]
    for _ in range(18):
        center=[F(rng.randrange(-24,25),8) for _ in range(3)]
        half=[F(rng.choice([1,2,4,8]),16) for _ in range(3)]
        queries.append(tuple((c-h,c+h) for c,h in zip(center,half)))
    n=0
    for p,rectangles in ((l,lu),(shell,shellboxes)):
        for q in queries:
            expected=state_union(q,rectangles)
            for permutation,scale,origin in [((0,1,2),F(1),(0,0,0)),((1,2,0),F(1,10**9),(10**8,-10**8,10**8)),((2,0,1),F(10**8),(-17,31,7))]:
                a=transform(make_box(q),permutation,scale,origin); b=transform(p,permutation,scale,origin)
                got=polyhedra_overlap(a,b,0)
                assert got==expected,(n,q,expected,got)
                n+=1
    return n

def polygon_oracle(p,vertices,tol):
    p=tuple(map(F,p)); vertices=[tuple(map(F,v)) for v in vertices]; tol=F(tol)
    for a,b in zip(vertices,vertices[1:]+vertices[:1]):
        u=tuple(b[k]-a[k] for k in range(3)); d=tuple(p[k]-a[k] for k in range(3))
        uu=sum(x*x for x in u); t=max(F(0),min(F(1),sum(x*y for x,y in zip(u,d))/uu)) if uu else F(0)
        if sum((d[k]-t*u[k])**2 for k in range(3))<=tol*tol:return 0
    wn=0
    for a,b in zip(vertices,vertices[1:]+vertices[:1]):
        cross=(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        if a[1]<=p[1]<b[1] and cross>0:wn+=1
        elif b[1]<=p[1]<a[1] and cross<0:wn-=1
    return 1 if wn else -1
def filter_grid():
    rng=random.Random(634112); n=0
    for exponent in (-2000,-1074,-1022,-600,-100,0,100,600,1020,2000):
        scale=F(2)**exponent
        for tmag in (F(0),F(10**8)):
            for j in range(45):
                vertices=[(tmag+scale*x,-tmag+scale*y,F(0)) for x,y in [(0,0),(2,0),(2,1),(1,1),(1,2),(0,2)]]
                p=(tmag+scale*F(rng.randrange(-8,24),8),-tmag+scale*F(rng.randrange(-8,24),8),F(0))
                tol=scale*F(rng.choice([0,1,2]),32)
                expected=polygon_oracle(p,vertices,tol); got=polygon_locate(p,vertices,tol)
                assert got==expected,(exponent,p,tol,expected,got)
                n+=1
    return n

def window_grid():
    """All model votes independently by exact products; check actual core shell.

    For axis-aligned boxes, box intervals ARE the solid. For each emitted core,
    homothetic vertex ratios and a convex squared-norm bound verify every radial
    shell segment, not a finite set of candidate overlaps. Rotation limitations
    are intentional and are not counted as failures.
    """
    rng=random.Random(6332); n=0; accepted=0
    for scale,origin in [(F(1),(0,0,0)),(F(1,10**9),(10**8,-10**8,10**8)),(F(10**8),(3,-2,5))]:
        for _ in range(25):
            halves=[F(rng.choice([1,2,4,8]),4) for _ in range(3)]
            ac=[F(rng.randrange(-3,4),4) for _ in range(3)]
            bc=[ac[k]+halves[k]*F(rng.randrange(-7,8),8) for k in range(3)]
            a=transform(make_box(tuple((ac[k]-halves[k],ac[k]+halves[k]) for k in range(3))),(0,1,2),scale,origin)
            b=transform(make_box(tuple((bc[k]-halves[k],bc[k]+halves[k]) for k in range(3))),(0,1,2),scale,origin)
            w=scale*F(rng.choice([1,2,4,8]),16)
            ai=interval_vertices(a); bi=interval_vertices(b)
            assert state_boxes(ai,bi)==1
            votes=[]
            for name,ca,cb in contact_models(a,b,w):
                ci=interval_vertices(ca);di=interval_vertices(cb); vote=state_boxes(ci,di); votes.append(vote)
                if vote<=0:
                    accepted+=1
                    if name.startswith('shift'):
                        d=tuple(ca.verts[0][k]-a.verts[0][k] for k in range(3));assert sum(x*x for x in d)==w*w
                    elif name.startswith('core'):
                        body,core=(a,ca) if name=='core_A' else (b,cb)
                        center=tuple(sum(F(p[k]) for p in body.verts)/8 for k in range(3))
                        ratio=next((F(core.verts[j][k])-center[k])/(F(body.verts[j][k])-center[k]) for j in range(8) for k in range(3) if body.verts[j][k]!=center[k])
                        assert 0<ratio<1
                        assert all(F(core.verts[j][k])==center[k]+ratio*(F(body.verts[j][k])-center[k]) for j in range(8) for k in range(3))
                        assert max(sum((F(core.verts[j][k])-F(body.verts[j][k]))**2 for k in range(3)) for j in range(8))<=w*w
            expected=0 if min(votes)<=0 else 1
            got=inflated_membership(a,b,delta=0,contact_window=w)
            assert got==expected,(w,votes,got)
            n+=1
    return n,accepted

if __name__=='__main__':
    n=surface_grid();print('SURFACE_PRODUCT_ORACLE',json.dumps({'queries':n,'mismatches':0}),flush=True)
    n=filter_grid();print('INTERVAL_FILTER_INDEPENDENT_ORACLE',json.dumps({'queries':n,'mismatches':0}),flush=True)
    n,a=window_grid();print('WINDOW_PRODUCT_AND_RADIAL_ORACLE',json.dumps({'queries':n,'accepted_models':a,'mismatches':0}),flush=True)
