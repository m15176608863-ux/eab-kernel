"""Exact rational surface primitives for the coordinates supplied by the caller.

No distance or angular tolerance changes a sign in this module.  A nonplanar
polygon is the deterministic projected-ear triangulation, not a fitted plane.
"""
from __future__ import annotations

from fractions import Fraction as F
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
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
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


def triangle_locate(p, a, b, c):
    """-1 outside, 0 on an edge, 1 in the relative interior, including plane check."""
    n = cross(sub(b, a), sub(c, a))
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


def point_in_surface(p,P):
    """Exact parity for a closed triangle surface; never guesses a boundary result.

    Directions (1,k,k*k) eventually avoid the finite set of bad edge/vertex
    directions: each plane gives a degree <=2 polynomial in k.
    """
    p = vector(p)
    tris = triangles(P)
    for _,tri in tris:
        if triangle_locate(p,*tri) >= 0:
            return 0
    for k in count(1):
        d=(F(1),F(k),F(k*k))
        hits=0
        degenerate=False
        for _,(a,b,c) in tris:
            n=cross(sub(b,a),sub(c,a))
            den=dot(n,d)
            if den == 0:
                if dot(n,sub(a,p)) == 0:
                    degenerate=True
                    break
                continue
            t=dot(n,sub(a,p))/den
            if t <= 0:
                continue
            x=add(p,mul(d,t))
            loc=triangle_locate(x,a,b,c)
            if loc == 0:
                degenerate=True
                break
            hits += loc == 1
        if not degenerate:
            return 1 if hits%2 else -1


def segment_crosses(p,q,P,fi):
    p,q=vector(p),vector(q)
    for face,tri in triangles(P):
        if face != fi:
            continue
        hit=segment_triangle(p,q,tri)
        if hit is not None and 0 < hit[1] < 1:
            # Internal triangulation edges belong to the face interior too.
            x=hit[0]
            verts=[vector(P.verts[i]) for i in P.faces[fi]]
            on_boundary=False
            for a,b in zip(verts,verts[1:]+verts[:1]):
                u,w=sub(b,a),sub(x,a)
                if not any(cross(u,w)) and 0 <= dot(u,w) <= dot(u,u):
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
