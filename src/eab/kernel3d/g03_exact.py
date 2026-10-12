"""Independent G0 coordinate oracle; no geom3/covers3 predicates are imported.

All determinants, planar hulls, support sets and SAT projections below are
inline rational arithmetic. The incremental hull is independent of the tested
geometry implementation; only the input coordinate values are shared.
Support-domain policy: docs/exact_predicates_plan.md (R13FIXb). Exact rational
outputs remain unrestricted; final float displays reject unrepresentable values.
"""
from fractions import Fraction as F
from functools import lru_cache
from itertools import combinations
from math import gcd, lcm


def qpoint(p):
    return tuple(F(c) for c in p)


def _lift_binary64(values):
    return tuple(F(x) if isinstance(x,float) else x for x in values) if any(isinstance(x,float) for x in values) else values


def minus(a, b):
    a,b=_lift_binary64(a),_lift_binary64(b)
    return tuple(x-y for x,y in zip(a,b))


def scalar(a,b):
    a,b=_lift_binary64(a),_lift_binary64(b)
    return sum(x*y for x,y in zip(a,b))


def wedge(a,b):
    a,b=_lift_binary64(a),_lift_binary64(b)
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def volume(a,b,c,d):
    return scalar(wedge(minus(b,a),minus(c,a)),minus(d,a))


def dimension(points):
    o=points[0]
    dirs=[minus(p,o) for p in points[1:]]
    u=next((d for d in dirs if any(d)),None)
    if u is None:return 0
    n=next((wedge(u,d) for d in dirs if any(wedge(u,d))),None)
    if n is None:return 1
    return 3 if any(scalar(n,d) for d in dirs) else 2


def plane_key(n,h):
    # Primitive integer plane coefficients avoid large rational denominators
    # in subsequent SAT dot products. This is exact rescaling, not a filter.
    values=tuple(F(c) for c in (*n,h))
    den=lcm(*(c.denominator for c in values))
    ints=tuple(int(c*den) for c in values)
    common=gcd(*ints)
    return tuple(c//common for c in ints[:3]),ints[3]//common


def planar_ring(points, indices, n):
    drop=next(i for i,c in enumerate(n) if c)
    axes=[i for i in range(3) if i!=drop]
    ordered=sorted(indices,key=lambda k:(points[k][axes[0]],points[k][axes[1]]))
    def turn(i,j,k):
        a,b,c=points[i],points[j],points[k]
        return ((b[axes[0]]-a[axes[0]])*(c[axes[1]]-a[axes[1]])
                -(b[axes[1]]-a[axes[1]])*(c[axes[0]]-a[axes[0]]))
    low=[]
    for i in ordered:
        while len(low)>1 and turn(low[-2],low[-1],i)<=0:low.pop()
        low.append(i)
    high=[]
    for i in reversed(ordered):
        while len(high)>1 and turn(high[-2],high[-1],i)<=0:high.pop()
        high.append(i)
    ring=low[:-1]+high[:-1]
    if scalar(wedge(minus(points[ring[1]],points[ring[0]]),minus(points[ring[2]],points[ring[0]])),n)<0:
        ring.reverse()
    return tuple(ring)


@lru_cache(maxsize=256)
def hull(raw):
    """Return (unique input points, extreme facet rings, exact planes)."""
    p=tuple(sorted(set(qpoint(_mapped_value) for _mapped_value in raw)))
    if len(p)<4:raise ValueError('G0 oracle needs a solid hull')
    original=p
    den=lcm(*(c.denominator for v in p for c in v))
    p=tuple(tuple(int(c*den) for c in v) for v in p)
    i=0
    j=max((scalar(minus(p[k],p[i]),minus(p[k],p[i])), -_rank_index, k) for _rank_index, k in enumerate(range(1,len(p))))[2]
    k=max((scalar(wedge(minus(p[j],p[i]),minus(p[k],p[i])),wedge(minus(p[j],p[i]),minus(p[k],p[i]))), -_rank_index, k) for _rank_index, k in enumerate(range(len(p))))[2]
    l=max((abs(volume(p[i],p[j],p[k],p[l])), -_rank_index, l) for _rank_index, l in enumerate(range(len(p))))[2]
    if volume(p[i],p[j],p[k],p[l])==0:raise ValueError('G0 oracle: coplanar input')
    seed=(i,j,k,l)
    center=tuple(F(sum(p[v][a] for v in seed),4) for a in range(3))
    def orient(tri):
        a,b,c=tri
        return (a,c,b) if volume(p[a],p[b],p[c],center)>0 else tri
    tris=[orient(t) for t in combinations(seed,3)]
    for v in range(len(p)):
        if v in seed:continue
        visible=[t for t in tris if volume(*(p[x] for x in t),p[v])>0]
        if not visible:continue
        rim=set()
        for a,b,c in visible:
            for e in ((a,b),(b,c),(c,a)):
                if (e[1],e[0]) in rim:rim.remove((e[1],e[0]))
                else:rim.add(e)
        bad=set(visible)
        tris=[t for t in tris if t not in bad]
        tris.extend(orient((a,b,v)) for a,b in sorted(rim))
    planes={}
    for a,b,c in tris:
        n=wedge(minus(p[b],p[a]),minus(p[c],p[a]))
        if not any(n):raise AssertionError('oracle generated a zero triangle')
        h=scalar(n,p[a]); key=plane_key(n,h)
        # This check is a theorem assertion, never a tolerance exemption.
        assert all(scalar(n,x)<=h for x in p)
        planes[key]=tuple(q for q,x in enumerate(p) if scalar(n,x)==h)
    ordered=sorted(planes)
    rings=tuple(planar_ring(p,planes[key],key[0]) for key in ordered)
    return original,rings,tuple(plane_key(n,F(h,den)) for n,h in ordered)


@lru_cache(maxsize=256)
def difference_hull(av,bv):
    a,b=tuple(qpoint(_mapped_value) for _mapped_value in av),tuple(qpoint(_mapped_value) for _mapped_value in bv)
    return hull(tuple(minus(y,x) for x in a for y in b))


@lru_cache(maxsize=256)
def sat_model(av,bv):
    """Independent exact SAT, with integer translation-interval certificates.

    A row stores n and the rational lower/upper bounds bmin-amax, bmax-amin.
    This is only an exact algebraic rearrangement of the previous projections;
    both face normals and every true hull-edge cross axis remain present.
    """
    a,fa,pa=hull(av);b,fb,pb=hull(bv)
    def edges(faces):
        return {tuple(sorted((f[i],f[(i+1)%len(f)]))) for f in faces for i in range(len(f))}
    axes={n for n,_ in pa}|{n for n,_ in pb}
    for i,j in edges(fa):
        for k,l in edges(fb):
            n=wedge(minus(a[j],a[i]),minus(b[l],b[k]))
            if any(n):axes.add(plane_key(n,F(0))[0])
    rows=[]
    for n in sorted(axes):
        aa=[scalar(n,p) for p in a];bb=[scalar(n,p) for p in b]
        low,high=min(bb)-max(aa),max(bb)-min(aa)
        rows.append((n,low.numerator,low.denominator,high.numerator,high.denominator))
    return tuple(rows)


def overlap(av,bv,x):
    """A+x versus B; translation is rational, with no rounded A.translated()."""
    x=qpoint(x);boundary=False
    den=lcm(*(v.denominator for v in x))
    xi=tuple(v.numerator*(den//v.denominator) for v in x)
    for n,ln,ld,hn,hd in sat_model(av,bv):
        shift=n[0]*xi[0]+n[1]*xi[1]+n[2]*xi[2]
        low,high=shift*ld-ln*den,shift*hd-hn*den
        if low<0 or high>0:return -1
        if low==0 or high==0:boundary=True
    return 0 if boundary else 1


def boundary_probes(av,bv):
    points,faces,_=difference_hull(av,bv)
    vertices={i for f in faces for i in f}
    edges={tuple(sorted((f[i],f[(i+1)%len(f)]))) for f in faces for i in range(len(f))}
    out=[points[i] for i in sorted(vertices)]
    out += [tuple((points[i][k]+points[j][k])/2 for k in range(3)) for i,j in sorted(edges)]
    out += [tuple(sum(points[i][k] for i in f)/len(f) for k in range(3)) for f in faces]
    return out,(len(vertices),len(edges),len(faces))


def support_labels(av,af,bv,bf):
    """Independent exact strict labels on the supplied canonical convex views."""
    a,b=tuple(qpoint(_mapped_value) for _mapped_value in av),tuple(qpoint(_mapped_value) for _mapped_value in bv)
    _,_,planes=difference_hull(av,bv)
    amap={frozenset(f):i for i,f in enumerate(af)}
    bmap={frozenset(f):i for i,f in enumerate(bf)}
    out=set();degenerate=0
    for n,_ in planes:
        aa=[scalar(n,p) for p in a];bb=[scalar(n,p) for p in b]
        amin,bmax=min(aa),max(bb)
        ia=frozenset(i for i,x in enumerate(aa) if x==amin)
        ib=frozenset(i for i,x in enumerate(bb) if x==bmax)
        da,db=dimension([a[i] for i in ia]),dimension([b[i] for i in ib])
        if (da,db)==(0,2):out.add(('VF',('vertex',next(iter(ia))),('face',bmap[ib])))
        elif (da,db)==(2,0):out.add(('FV',('face',amap[ia]),('vertex',next(iter(ib)))))
        elif (da,db)==(1,1):out.add(('EE',('edge',*sorted(ia)),('edge',*sorted(ib))))
        else:degenerate+=1
    return out,degenerate
