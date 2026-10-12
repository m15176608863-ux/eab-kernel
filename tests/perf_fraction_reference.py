"""Unoptimized c194dbb Fraction expressions, preserved for PERF equivalence.

No new integer helper is used. This is an equivalence reference, not the
independent geometric oracle; independent closed-form cases are in the gates.
"""
from fractions import Fraction as F
from eab.kernel3d.exact_geom import (vector, sub, add, mul, dot, cross,
    triangle_locate, point_segment_distance_squared, _direction_key)

def segment_distance_squared(p1,p2,q1,q2):
    p1,p2,q1,q2=(vector(_mapped_value) for _mapped_value in (p1,p2,q1,q2))
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
