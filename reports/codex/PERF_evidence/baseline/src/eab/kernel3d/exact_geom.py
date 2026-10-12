"""Exact rational surface primitives for the coordinates supplied by the caller.

No distance or angular tolerance changes a sign in this module.  A nonplanar
polygon is the deterministic projected-ear triangulation, not a fitted plane.
"""
from __future__ import annotations

from fractions import Fraction as F
from eab import rational3 as _rational3
from functools import lru_cache
from itertools import count
import math


def _iv(x):
    """Outward interval containing an exact scalar (binary64 or Fraction)."""
    try:
        f=float(x)
    except OverflowError:
        return (-math.inf,math.inf)
    if isinstance(x,float):
        return (f,f)
    return (math.nextafter(f,-math.inf),math.nextafter(f,math.inf))


def _ia(a,b):
    return (math.nextafter(a[0]+b[0],-math.inf),math.nextafter(a[1]+b[1],math.inf))


def _is(a,b):
    return (math.nextafter(a[0]-b[1],-math.inf),math.nextafter(a[1]-b[0],math.inf))


def _im(a,b):
    vals=(a[0]*b[0],a[0]*b[1],a[1]*b[0],a[1]*b[1])
    if any(math.isnan(x) for x in vals):
        return (-math.inf,math.inf)
    return (math.nextafter(min(vals),-math.inf),math.nextafter(max(vals),math.inf))


def _id(a,b):
    s=(0.,0.)
    for x,y in zip(a,b):
        s=_ia(s,_im(x,y))
    return s


def _edge_window_filter(p,a,b,tol):
    """Conservative interval squared-distance comparison; None asks Fraction."""
    u=tuple(_is(x,y) for x,y in zip(b,a))
    w=tuple(_is(x,y) for x,y in zip(p,a))
    aa,bb,cc=_id(u,u),_id(w,u),_id(w,w)
    tt=_im(tol,tol)
    if bb[1] <= 0:
        value=_is(cc,tt)
    elif _is(bb,aa)[0] >= 0:
        z=tuple(_is(x,y) for x,y in zip(p,b))
        value=_is(_id(z,z),tt)
    elif bb[0] > 0 and _is(bb,aa)[1] < 0:
        value=_is(_im(aa,_is(cc,tt)),_im(bb,bb))
    else:
        return None
    if value[0] > 0:
        return False
    if value[1] <= 0:
        return True
    return None


def vector(p):
    return _vector_cached(tuple(p))


@lru_cache(maxsize=16384)
def _vector_cached(p):
    return tuple(F(x) for x in p)


def sqrt_rational(value):
    """Convert sqrt(nonnegative Fraction), without overflowing/underflowing its square."""
    if value < 0:
        raise ValueError('square root of negative rational')
    if not value:
        return 0.0
    exponent=(value.numerator.bit_length()-value.denominator.bit_length())//2
    scaled=value/F(2**(2*exponent)) if exponent >= 0 else value*F(2**(-2*exponent))
    try:
        return math.ldexp(math.sqrt(float(scaled)),exponent)
    except OverflowError:
        return math.inf


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def mul(a, s):
    return tuple(x * s for x in a)


def dot(a, b):
    if _rational3.fraction_vectors(a, b):
        return _rational3.dot(a, b)
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    if _rational3.fraction_vectors(a, b):
        return _rational3.cross(a, b)
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def normal(pts):
    """Unnormalised exact Newell vector; callers must not treat a folded face as a plane."""
    o = pts[0]
    n = (F(0), F(0), F(0))
    for a, b in zip(pts, pts[1:] + pts[:1]):
        n = add(n, cross(sub(a, o), sub(b, o)))
    if not any(n):
        raise ValueError('zero-area polygon')
    return n


def orient2(a, b, p):
    return (b[0]-a[0])*(p[1]-a[1]) - (b[1]-a[1])*(p[0]-a[0])


@lru_cache(maxsize=4096)
def _polygon_data(vertices):
    verts=tuple(vector(p) for p in vertices)
    n=normal(list(verts))
    axis=max(range(3),key=lambda i:abs(n[i]))
    return verts,((axis+1)%3,(axis+2)%3),tuple(tuple(_iv(c) for c in p) for p in vertices)


def polygon_locate(p,vertices,tol=0):
    """Exact projected winding and caller-requested Euclidean edge window.

    As in the public API, p must already be in/projected onto the face. A positive
    tol widens the boundary set; no implementation noise floor is introduced.
    """
    verts,axes,intervals=_polygon_data(tuple(vertices))
    pi=tuple(_iv(c) for c in p);ti=_iv(tol)
    p=vector(p);tol=F(tol)
    if tol < 0:
        raise ValueError('polygon extent tolerance must be nonnegative')
    for k,(a,b) in enumerate(zip(verts,verts[1:]+verts[:1])):
        ai,bi=intervals[k],intervals[(k+1)%len(verts)]
        # A segment's Euclidean tol-neighbourhood is inside its expanded AABB.
        # This necessary-condition filter avoids most distance polynomials;
        # nextafter includes rounding and subnormal absolute errors.
        if any(pi[j][1] < math.nextafter(min(ai[j][0],bi[j][0])-ti[1],-math.inf)
               or pi[j][0] > math.nextafter(max(ai[j][1],bi[j][1])+ti[1],math.inf)
               for j in range(3)):
            continue
        decision=_edge_window_filter(pi,ai,bi,ti)
        if decision is True:
            return 0
        if decision is False:
            continue
        d,w=sub(b,a),sub(p,a);dd=dot(d,d)
        t=max(F(0),min(F(1),dot(w,d)/dd)) if dd else F(0)
        delta=sub(w,mul(d,t))
        if dot(delta,delta) <= tol*tol:
            return 0
    i,j=axes
    x=(p[i],p[j]);wn=0
    for k,(a,b) in enumerate(zip(verts,verts[1:]+verts[:1])):
        ai,bi=intervals[k],intervals[(k+1)%len(verts)]
        determinant=_is(_im(_is(bi[i],ai[i]),_is(pi[j],ai[j])),
                        _im(_is(pi[i],ai[i]),_is(bi[j],ai[j])))
        a,b=(a[i],a[j]),(b[i],b[j])
        o=1 if determinant[0] > 0 else (-1 if determinant[1] < 0 else orient2(a,b,x))
        if a[1] <= x[1]:
            if b[1] > x[1] and o > 0:
                wn+=1
        elif b[1] <= x[1] and o < 0:
            wn-=1
    return 1 if wn else -1


def polygon_locate_fraction(p,vertices,tol=0):
    """Unfiltered rational reference for the interval-filter equivalence gate."""
    verts,axes,_=_polygon_data(tuple(vertices))
    p=vector(p);tol=F(tol)
    if tol < 0:
        raise ValueError('polygon extent tolerance must be nonnegative')
    for a,b in zip(verts,verts[1:]+verts[:1]):
        d,w=sub(b,a),sub(p,a);dd=dot(d,d)
        t=max(F(0),min(F(1),dot(w,d)/dd)) if dd else F(0)
        delta=sub(w,mul(d,t))
        if dot(delta,delta) <= tol*tol:
            return 0
    i,j=axes;x=(p[i],p[j]);wn=0
    for a,b in zip(verts,verts[1:]+verts[:1]):
        a,b=(a[i],a[j]),(b[i],b[j]);o=orient2(a,b,x)
        if a[1] <= x[1]:
            if b[1] > x[1] and o > 0:
                wn+=1
        elif b[1] <= x[1] and o < 0:
            wn-=1
    return 1 if wn else -1


def triangle_locate(p, a, b, c, known_normal=None):
    """-1 outside, 0 on an edge, 1 in the relative interior, including plane check."""
    n = known_normal if known_normal is not None else cross(sub(b, a), sub(c, a))
    if not any(n) or dot(n, sub(p, a)) != 0:
        return -1
    vals = [dot(n, cross(sub(v, u), sub(p, u)))
            for u, v in ((a,b),(b,c),(c,a))]
    if min(vals) < 0:
        return -1
    return 0 if min(vals) == 0 else 1


@lru_cache(maxsize=1024)
def triangulate(vertices, faces):
    """Deterministic exact projected ear clipping, returned as (input face, triangle)."""
    verts = tuple(vector(p) for p in vertices)
    out = []
    for fi, face in enumerate(faces):
        if len(face) == 3:
            a,b,c=(verts[i] for i in face)
            if not any(cross(sub(b,a),sub(c,a))):
                raise ValueError('zero-area triangle in input surface')
            out.append((fi, face))
            continue
        n = normal([verts[i] for i in face])
        axis = max(range(3), key=lambda i: abs(n[i]))
        axes = [(axis+1)%3, (axis+2)%3]
        p2 = {i: tuple(verts[i][k] for k in axes) for i in face}
        area = sum(p2[a][0]*p2[b][1]-p2[b][0]*p2[a][1]
                   for a,b in zip(face,face[1:]+face[:1]))
        sign = 1 if area > 0 else -1
        ring = list(face)
        while len(ring) > 3:
            for k,b in enumerate(ring):
                a,c = ring[k-1],ring[(k+1)%len(ring)]
                if sign*orient2(p2[a],p2[b],p2[c]) <= 0:
                    continue
                if any(all(sign*orient2(p2[u],p2[v],p2[j]) >= 0
                           for u,v in ((a,b),(b,c),(c,a)))
                       for j in ring if j not in (a,b,c)):
                    continue
                out.append((fi,(a,b,c)))
                ring.pop(k)
                break
            else:
                # Collinear boundary vertices carry no area and can be removed.
                k = next((k for k,b in enumerate(ring)
                          if orient2(p2[ring[k-1]],p2[b],p2[ring[(k+1)%len(ring)]]) == 0),None)
                if k is None:
                    raise ValueError('polygon projection is not a simple polygon')
                a,b,c=ring[k-1],ring[k],ring[(k+1)%len(ring)]
                if any(cross(sub(verts[b],verts[a]),sub(verts[c],verts[a]))):
                    out.append((fi,(a,b,c)))
                ring.pop(k)
        out.append((fi,tuple(ring)))
    return tuple(out)


def triangles(P):
    verts = tuple(vector(p) for p in P.verts)
    return [(fi, tuple(verts[i] for i in tri))
            for fi,tri in triangulate(tuple(P.verts),tuple(P.faces))]


def segment_triangle(p, q, tri):
    """Intersection point and exact segment parameter, or None; coplanar is separate."""
    a,b,c = tri
    n = cross(sub(b,a),sub(c,a))
    dp,dq = dot(n,sub(p,a)),dot(n,sub(q,a))
    if dp == dq or (dp > 0 and dq > 0) or (dp < 0 and dq < 0):
        return None
    t = dp/(dp-dq)
    x = add(p,mul(sub(q,p),t))
    if triangle_locate(x,a,b,c) < 0:
        return None
    return x,t


def point_in_surface(p,P,tol=0):
    """Exact parity for a closed triangle surface; never guesses a boundary result.

    Directions (1,k,k*k) eventually avoid the finite set of bad edge/vertex
    directions: each plane gives a degree <=2 polynomial in k.
    """
    p = vector(p)
    tris = triangles(P)
    tol=F(tol)
    if tol < 0:
        raise ValueError('surface tolerance must be nonnegative')
    if tol and any(point_triangle_distance_squared(p,tri) <= tol*tol for _,tri in tris
                   if all(min(v[i] for v in tri)-tol <= p[i] <= max(v[i] for v in tri)+tol
                          for i in range(3))):
        return 0
    return _point_in_triangles(p,tris)


def _triangle_bounds(tris):
    return tuple((min(v[i] for _,tri in tris for v in tri),
                  max(v[i] for _,tri in tris for v in tri)) for i in range(3))


def _int_dot(a,b):
    return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]


@lru_cache(maxsize=256)
def _integer_surface(tris):
    """Same exact planes/edge halfspaces, positive common-denominator integers."""
    points={p for _,tri in tris for p in tri}
    den=math.lcm(*(F(x).denominator for p in points for x in p))
    lift={p:tuple(F(x).numerator*(den//F(x).denominator) for x in p) for p in points}
    payload=[]
    for _,tri in tris:
        a,b,c=(lift[p] for p in tri)
        n=cross(sub(b,a),sub(c,a))
        edges=[]
        for u,v in ((a,b),(b,c),(c,a)):
            inward=cross(n,sub(v,u))
            edges.append((inward,_int_dot(inward,u)))
        payload.append((n,_int_dot(n,a),tuple(edges)))
    return den,tuple(payload)


def _point_in_triangles(p,tris,planes=None,bounds=None):
    # Exactly the Fraction parity algorithm, clearing only positive denominators.
    # planes remains a compatible precomputation argument; no approximate value
    # is consumed. Tests compare every state to the previous rational path.
    bounds=_triangle_bounds(tris) if bounds is None else bounds
    if any(p[i] < lo or p[i] > hi for i,(lo,hi) in enumerate(bounds)):
        return -1
    den,payload=_integer_surface(tuple(tris))
    scaled=tuple(F(x)*den for x in p)
    multiplier=math.lcm(*(x.denominator for x in scaled))
    point=tuple(x.numerator*(multiplier//x.denominator) for x in scaled)
    rows=[]
    for n,h,edges in payload:
        offset=h*multiplier-_int_dot(n,point)
        edge_values=tuple((_int_dot(v,point)-h*multiplier,v) for v,h in edges)
        if offset == 0 and all(value >= 0 for value,_ in edge_values):
            return 0
        rows.append((n,offset,edge_values))
    for k in count(1):
        direction=(1,k,k*k); hits=0; degenerate=False
        for n,offset,edges in rows:
            divisor=_int_dot(n,direction)
            if divisor == 0:
                if offset == 0:
                    degenerate=True
                    break
                continue
            if offset*divisor <= 0:
                continue
            edge_signs=[value*divisor+_int_dot(v,direction)*offset for value,v in edges]
            if divisor < 0:
                edge_signs=[-value for value in edge_signs]
            if min(edge_signs) < 0:
                continue
            if min(edge_signs) == 0:
                degenerate=True
                break
            hits+=1
        if not degenerate:
            return 1 if hits%2 else -1



def _transverse_fold_crossing(p,q,t,tris):
    """Resolve an internal triangle-edge hit by exact one-sided solid states."""
    d=sub(q,p); cuts={F(0),F(1)}
    for n,o in _planes(tris):
        den=dot(n,d)
        if den:
            u=dot(n,sub(o,p))/den
            if 0 < u < 1:
                cuts.add(u)
    before=max(u for u in cuts if u < t)
    after=min(u for u in cuts if u > t)
    left=add(p,mul(d,(before+t)/2));right=add(p,mul(d,(t+after)/2))
    return _point_in_triangles(left,tris)*_point_in_triangles(right,tris) == -1


def segment_crosses(p,q,P,fi,tol=0):
    p,q=vector(p),vector(q)
    tol=F(tol)
    if tol < 0:
        raise ValueError('segment tolerance must be nonnegative')
    tris=triangles(P)
    for face,tri in tris:
        if face != fi:
            continue
        hit=segment_triangle(p,q,tri)
        if hit is not None and 0 < hit[1] < 1:
            n=cross(sub(tri[1],tri[0]),sub(tri[2],tri[0]))
            if tol and (dot(n,sub(p,tri[0]))**2 <= tol*tol*dot(n,n)
                        or dot(n,sub(q,tri[0]))**2 <= tol*tol*dot(n,n)):
                continue
            # Internal triangulation edges belong to the face interior too.
            x=hit[0]
            if triangle_locate(x,*tri) == 0 and not _transverse_fold_crossing(p,q,hit[1],tris):
                continue
            verts=[vector(P.verts[i]) for i in P.faces[fi]]
            on_boundary=False
            for a,b in zip(verts,verts[1:]+verts[:1]):
                u,w=sub(b,a),sub(x,a)
                if point_segment_distance_squared(x,a,b) <= tol*tol:
                    on_boundary=True
                    break
            if not on_boundary:
                return True
    return False


def segment_distance_squared(p1,p2,q1,q2):
    p1,p2,q1,q2=map(vector,(p1,p2,q1,q2))
    u,v,w=sub(p2,p1),sub(q2,q1),sub(q1,p1)
    a,c=dot(u,u),dot(v,v)
    candidates=[]
    n=cross(u,v);nn=dot(n,n)
    if nn:
        s,t=dot(cross(w,v),n)/nn,dot(cross(w,u),n)/nn
        if 0 <= s <= 1 and 0 <= t <= 1:
            candidates.append((s,t))
    for s in (F(0),F(1)):
        t=dot(sub(add(p1,mul(u,s)),q1),v)/c if c else F(0)
        candidates.append((s,max(F(0),min(F(1),t))))
    for t in (F(0),F(1)):
        s=dot(sub(add(q1,mul(v,t)),p1),u)/a if a else F(0)
        candidates.append((max(F(0),min(F(1),s)),t))
    values=[]
    for s,t in candidates:
        delta=sub(add(p1,mul(u,s)),add(q1,mul(v,t)))
        values.append(dot(delta,delta))
    return min(values)


def triangle_intersection(first, second):
    """Exact intersection vertices of two closed triangles, including coplanarity.

    The returned set is unordered.  A point, segment, or coplanar polygon can
    result; the empty tuple means disjoint. No fitting plane is used.
    """
    first=tuple(map(vector,first));second=tuple(map(vector,second))
    for tri in (first,second):
        if not any(cross(sub(tri[1],tri[0]),sub(tri[2],tri[0]))):
            raise ValueError('triangle intersection requires nondegenerate triangles')
    out=set()
    for tri,other in ((first,second),(second,first)):
        for p in tri:
            if triangle_locate(p,*other) >= 0:
                out.add(p)
        for p,q in zip(tri,tri[1:]+tri[:1]):
            hit=segment_triangle(p,q,other)
            if hit is not None:
                out.add(hit[0])
    n=cross(sub(first[1],first[0]),sub(first[2],first[0]))
    if all(dot(n,sub(p,first[0])) == 0 for p in second):
        axis=max(range(3),key=lambda i:abs(n[i]))
        axes=((axis+1)%3,(axis+2)%3)
        for p,q in zip(first,first[1:]+first[:1]):
            u=sub(q,p)
            for a,b in zip(second,second[1:]+second[:1]):
                v=sub(b,a);w=sub(a,p)
                i,j=axes
                den=u[i]*v[j]-u[j]*v[i]
                if den:
                    s=(w[i]*v[j]-w[j]*v[i])/den
                    t=(w[i]*u[j]-w[j]*u[i])/den
                    if 0 <= s <= 1 and 0 <= t <= 1:
                        out.add(add(p,mul(u,s)))
                # Parallel collinear intersection endpoints were included above.
    return tuple(sorted(out))


def point_segment_distance_squared(p,a,b):
    d,w=sub(b,a),sub(p,a)
    dd=dot(d,d)
    t=max(F(0),min(F(1),dot(w,d)/dd)) if dd else F(0)
    r=sub(w,mul(d,t))
    return dot(r,r)


def point_triangle_distance_squared(p,tri):
    """Exact Euclidean distance squared, including edge/vertex minimisers."""
    p=vector(p)
    a,b,c=tri
    n=cross(sub(b,a),sub(c,a)); nn=dot(n,n)
    if not nn:
        raise ValueError('distance requires a nondegenerate triangle')
    h=dot(n,sub(p,a)); q=sub(p,mul(n,h/nn))
    if triangle_locate(q,a,b,c) >= 0:
        return h*h/nn
    return min(point_segment_distance_squared(p,u,v)
               for u,v in ((a,b),(b,c),(c,a)))


def _planes(tris):
    return [(cross(sub(b,a),sub(c,a)),a) for _,(a,b,c) in tris]


def _direction_key(n):
    i=next((i for i,x in enumerate(n) if x),None)
    return tuple(x/n[i] for x in n) if i is not None else None


def _convex_surface_sat(av,bv,at,bt,ap,bp):
    """SAT only if every given triangle has every vertex on its inner side.

    The input must be a valid outward-oriented closed embedded surface. This
    certificate proves that the original surface, not its hull replacement,
    bounds a convex solid. None means the general surface path is required.
    """
    for verts,planes in ((av,ap),(bv,bp)):
        if any(dot(n,sub(v,o)) > 0 for n,o in planes for v in verts):
            return None
    axes={_direction_key(n) for n,_ in ap+bp}
    ae={_direction_key(sub(b,a)) for _,tri in at
        for a,b in zip(tri,tri[1:]+tri[:1])}
    be={_direction_key(sub(b,a)) for _,tri in bt
        for a,b in zip(tri,tri[1:]+tri[:1])}
    axes.update(_direction_key(cross(a,b)) for a in ae for b in be)
    boundary=False
    for axis in axes:
        if axis is None:
            continue
        x=[dot(axis,p) for p in av]; y=[dot(axis,p) for p in bv]
        gap=max(min(x)-max(y),min(y)-max(x))
        if gap > 0:
            return -1
        boundary |= gap == 0
    return 0 if boundary else 1


def _split_polygon(poly,n,o):
    """Split a convex polygon by an exact plane, preserving only 2D cells."""
    ds=[dot(n,sub(p,o)) for p in poly]
    if min(ds) >= 0 or max(ds) <= 0:
        return [poly]
    sides=[[],[]]
    for i,p in enumerate(poly):
        q=poly[(i+1)%len(poly)]; a=ds[i]; b=ds[(i+1)%len(poly)]
        if a >= 0:
            sides[0].append(p)
        if a <= 0:
            sides[1].append(p)
        if a*b < 0:
            x=add(p,mul(sub(q,p),a/(a-b)))
            sides[0].append(x); sides[1].append(x)
    return sides


def _inward_sample(p,n,planes):
    """An exact half-first-plane-intercept step; not a sampled epsilon ladder."""
    d=mul(n,F(-1)); steps=[]
    for m,o in planes:
        den=dot(m,d); num=dot(m,sub(o,p))
        if den and num/den > 0:
            steps.append(num/den)
    t=min(steps)/2 if steps else F(1)
    return add(p,mul(d,t))


def _coplanar_interior_witness(p,n,at,bt,planes,ap,bp,ab,bb):
    """Certify same-side solid overlap at a 2D coplanar arrangement cell."""
    w=_inward_sample(p,n,planes)
    return w if _point_in_triangles(w,at,ap,ab) == _point_in_triangles(w,bt,bp,bb) == 1 else None


def _surface_interior_witness(at,bt,ap,bp):
    """Finite complete boundary-patch certificate for valid closed surfaces.

    Each input triangle is split by every other triangle's plane, and by edge
    lines of triangles coplanar with it. Membership is constant on every open
    2D cell. A nonempty bounded 3D intersection has an open boundary patch on
    one input surface: either that patch is inside the other solid, or the
    two boundaries coincide there and their inward sides agree. Thus these
    cells exhaust the possibilities, including common-edge and coplanar cases.
    Rational points strictly inside both solids are the returned certificates.
    """
    planes=ap+bp
    for pt,qt,pp,qp in ((at,bt,ap,bp),(bt,at,bp,ap)):
        pb,qb=_triangle_bounds(pt),_triangle_bounds(qt)
        for (_,tri),(n,o) in zip(pt,pp):
            cuts=list(qp)
            for (_,other),(m,a) in zip(qt,qp):
                if not any(cross(n,m)) and dot(n,sub(a,o)) == 0:
                    cuts.extend((cross(n,sub(v,u)),u)
                                for u,v in zip(other,other[1:]+other[:1]))
            # Repeated supporting planes cannot refine the arrangement again.
            unique={}
            for m,a in cuts:
                key=_direction_key(m)
                if key is not None:
                    unique[(key,dot(key,a))]=(m,a)
            cells=[list(tri)]
            for m,a in unique.values():
                cells=[part for cell in cells for part in _split_polygon(cell,m,a)]
            for cell in cells:
                p=tuple(sum(v[i] for v in cell)/len(cell) for i in range(3))
                loc=_point_in_triangles(p,qt,qp,qb)
                if loc == 1:
                    w=_inward_sample(p,n,planes)
                    if _point_in_triangles(w,pt,pp,pb) == _point_in_triangles(w,qt,qp,qb) == 1:
                        return w
                elif loc == 0:
                    witness=_coplanar_interior_witness(p,n,pt,qt,planes,pp,qp,pb,qb)
                    if witness is not None:
                        return witness
    return None


def _triangle_data(tri):
    """Exact plane and bounds, reused within one boolean distance query."""
    n=cross(sub(tri[1],tri[0]),sub(tri[2],tri[0]))
    if not any(n):
        raise ValueError('triangle intersection requires nondegenerate triangles')
    return tri,n,tuple((min(p[i] for p in tri),max(p[i] for p in tri)) for i in range(3))


def _cut_interval(tri,values,axis):
    points=[p[axis] for p,d in zip(tri,values) if d == 0]
    for k,p in enumerate(tri):
        j=(k+1)%3; q=tri[j]; a,b=values[k],values[j]
        if a < 0 < b or b < 0 < a:
            points.append((p[axis]*b-q[axis]*a)/(b-a))
    return min(points),max(points)


def _triangles_intersect_prepared(first,second):
    """Closed boolean intersection; exact cuts / projected coplanar SAT.

    This avoids constructing intersection vertices only for a bool consumer.
    Public triangle_intersection's point-set contract remains unchanged.
    """
    a,n,ab=first; b,m,bb=second
    if any(hi < low or upper < lo for (lo,hi),(low,upper) in zip(ab,bb)):
        return False
    da=[dot(m,sub(p,b[0])) for p in a]
    if min(da) > 0 or max(da) < 0:
        return False
    db=[dot(n,sub(p,a[0])) for p in b]
    if min(db) > 0 or max(db) < 0:
        return False
    line=cross(n,m)
    if any(line):
        axis=next(i for i,c in enumerate(line) if c)
        lo,hi=_cut_interval(a,da,axis); left,right=_cut_interval(b,db,axis)
        return max(lo,left) <= min(hi,right)
    # Parallel planes remaining after same-side rejection coincide exactly.
    drop=next(i for i,c in enumerate(n) if c)
    i,j=(k for k in range(3) if k != drop)
    for tri in (a,b):
        for k,p in enumerate(tri):
            q=tri[(k+1)%3]; dx,dy=q[i]-p[i],q[j]-p[j]
            x=[dx*v[j]-dy*v[i] for v in a]; y=[dx*v[j]-dy*v[i] for v in b]
            if max(x) < min(y) or max(y) < min(x):
                return False
    return True


def _transverse_interior_witness(at,bt,ap,bp):
    """Sufficient strict-interior certificate; failure retains full arrangement.

    For nonparallel n,m the constructed d has n.d = m.d =
    (n.m)^2-(n.n)(m.m) < 0. The finite exact plane intercept step is still
    verified against both original surfaces; no epsilon or convexity assumed.
    """
    aa=[_triangle_data(a) for _,a in at]; bb=[_triangle_data(b) for _,b in bt]
    abounds,bbounds=_triangle_bounds(at),_triangle_bounds(bt)
    for a,n,ab in aa:
        for b,m,bounds in bb:
            if any(hi < low or upper < lo for (lo,hi),(low,upper) in zip(ab,bounds)):
                continue
            ds=[dot(m,sub(p,b[0])) for p in a]
            es=[dot(n,sub(p,a[0])) for p in b]
            if not min(ds) < 0 < max(ds) or not min(es) < 0 < max(es):
                continue
            line=cross(n,m)
            if not any(line):
                continue
            k=next(i for i,c in enumerate(line) if c)
            lo,hi=_cut_interval(a,ds,k); left,right=_cut_interval(b,es,k)
            low,high=max(lo,left),min(hi,right)
            if not low < high:
                continue
            points=[p for p,d in zip(a,ds) if d == 0]
            for j,p in enumerate(a):
                q=a[(j+1)%3]; s,t=ds[j],ds[(j+1)%3]
                if s < 0 < t or t < 0 < s:
                    points.append(add(p,mul(sub(q,p),s/(s-t))))
            u,v=min(points,key=lambda p:p[k]),max(points,key=lambda p:p[k])
            p=add(u,mul(sub(v,u),((low+high)/2-u[k])/(v[k]-u[k])))
            if triangle_locate(p,*a,n) != 1 or triangle_locate(p,*b,m) != 1:
                continue
            nn,nm,mm=dot(n,n),dot(n,m),dot(m,m)
            d=add(mul(n,nm-mm),mul(m,nm-nn))
            w=_inward_sample(p,mul(d,F(-1)),ap+bp)
            if _point_in_triangles(w,at,ap,abounds) == _point_in_triangles(w,bt,bp,bbounds) == 1:
                return w
    return None


def _triangle_plane_outside_window(normal,origin,other,window_squared):
    """Certified distance lower bound; equality belongs to the closed window.

    Distance to the supporting plane cannot exceed distance to its triangle.
    When every vertex of the other triangle lies strictly on one side, its
    minimum plane distance is attained at a vertex. Squaring preserves the
    exact comparison without constructing a unit normal or a square root.
    Gate: test_triangle_near_window_preserves_closed_exact_threshold_rigid_motion_and_units.
    """
    distances=[dot(normal,sub(p,origin)) for p in other]
    lo,hi=min(distances),max(distances)
    gap=lo if lo>0 else (-hi if hi<0 else F(0))
    return bool(gap and gap*gap > window_squared*dot(normal,normal))


def _triangles_near(at,bt,tol):
    """Exact closed-surface distance <= tol, using all feature minimisers."""
    tt=tol*tol
    aa=[_triangle_data(a) for _,a in at]; bb=[_triangle_data(b) for _,b in bt]
    for first in aa:
        a,n,ab=first
        for second in bb:
            b,m,bounds=second
            if any(hi+tol < low or upper+tol < lo for (lo,hi),(low,upper) in zip(ab,bounds)):
                continue
            if tol and (_triangle_plane_outside_window(n,a[0],b,tt)
                        or _triangle_plane_outside_window(m,b[0],a,tt)):
                continue
            if _triangles_intersect_prepared(first,second):
                return True
            if tol:
                if any(point_triangle_distance_squared(p,b) <= tt for p in a):
                    return True
                if any(point_triangle_distance_squared(p,a) <= tt for p in b):
                    return True
                if any(segment_distance_squared(p,q,u,v) <= tt
                       for p,q in zip(a,a[1:]+a[:1]) for u,v in zip(b,b[1:]+b[:1])):
                    return True
    return False


@lru_cache(maxsize=256)
def _star_tetrahedra(vertices,faces):
    """Certified radial tetrahedralisation, or None (never an assumed hull).

    An outward embedded closed surface with a point strictly behind every
    triangle is star-shaped about that point. Coning its triangles partitions
    the solid. This sufficient certificate is checked on the supplied surface.
    """
    verts=tuple(map(vector,vertices))
    centre=tuple(sum(p[k] for p in verts)/len(verts) for k in range(3))
    out=[]
    for _,indices in triangulate(vertices,faces):
        a,b,c=(verts[i] for i in indices)
        n=cross(sub(b,a),sub(c,a))
        if dot(n,sub(centre,a)) >= 0:
            return None
        out.append((centre,a,b,c))
    return tuple(out)


def _integer_tetrahedron(points):
    """Integer-only SAT payload; no rounded projection or angular threshold."""
    edges=[sub(points[j],points[i]) for i in range(4) for j in range(i+1,4)]
    normals=[cross(sub(points[j],points[i]),sub(points[k],points[i]))
             for i,j,k in ((0,1,2),(0,1,3),(0,2,3),(1,2,3))]
    bounds=tuple((min(p[k] for p in points),max(p[k] for p in points)) for k in range(3))
    return points,edges,normals,bounds


def _integer_tetrahedron_overlap(a,b):
    av,ae,an,ab=a; bv,be,bn,bb=b
    if any(hi < low or upper < lo for (lo,hi),(low,upper) in zip(ab,bb)):
        return -1
    boundary=False
    # Face axes first usually separate without constructing all edge products.
    for axes in (an+bn,(cross(u,v) for u in ae for v in be)):
        for n in axes:
            if not any(n):
                continue
            x=[n[0]*p[0]+n[1]*p[1]+n[2]*p[2] for p in av]
            y=[n[0]*p[0]+n[1]*p[1]+n[2]*p[2] for p in bv]
            gap=max(min(x)-max(y),min(y)-max(x))
            if gap > 0:
                return -1
            boundary |= gap == 0
    return 0 if boundary else 1


def _star_union_overlap(A,B):
    """Complete three-state overlap only after both radial certificates pass."""
    aa=_star_tetrahedra(tuple(A.verts),tuple(A.faces))
    bb=_star_tetrahedra(tuple(B.verts),tuple(B.faces))
    if aa is None or bb is None:
        return None
    points={p for tet in aa+bb for p in tet}
    denominator=math.lcm(*(x.denominator for p in points for x in p))
    lift={p:tuple(x.numerator*(denominator//x.denominator) for x in p) for p in points}
    aa,bb=([_integer_tetrahedron(tuple(lift[p] for p in tet)) for tet in seq] for seq in (aa,bb))
    boundary=False
    for a in aa:
        for b in bb:
            state=_integer_tetrahedron_overlap(a,b)
            if state == 1:
                return 1
            boundary |= state == 0
    return 0 if boundary else -1


def surface_overlap(A,B,tol=0):
    """Exact supplied-surface three-state relation; see geom3.polyhedra_overlap."""
    tol=F(tol)
    if tol < 0:
        raise ValueError('surface tolerance must be nonnegative')
    av=tuple(map(vector,A.verts)); bv=tuple(map(vector,B.verts))
    if any(max(p[i] for p in av)+tol < min(p[i] for p in bv)
           or max(p[i] for p in bv)+tol < min(p[i] for p in av) for i in range(3)):
        return -1
    at,bt=triangles(A),triangles(B); ap,bp=_planes(at),_planes(bt)
    sat=_convex_surface_sat(av,bv,at,bt,ap,bp)
    if sat is None:
        sat=_star_union_overlap(A,B)
    if sat is not None:
        return 0 if sat == -1 and tol and _triangles_near(at,bt,tol) else sat
    for verts,tris,ps in ((av,bt,bp),(bv,at,ap)):
        bounds=_triangle_bounds(tris)
        if any(_point_in_triangles(p,tris,ps,bounds) == 1 for p in verts):
            return 1
    # Disjoint boundaries imply constant membership on each connected surface
    # component; the preceding vertex checks have excluded containment.
    if not _triangles_near(at,bt,F(0)):
        return 0 if tol and _triangles_near(at,bt,tol) else -1
    if _transverse_interior_witness(at,bt,ap,bp) is not None:
        return 1
    if _surface_interior_witness(at,bt,ap,bp) is not None:
        return 1
    return 0 if _triangles_near(at,bt,tol) else -1
