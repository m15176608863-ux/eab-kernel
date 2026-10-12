"""Exact affine surface events and exact translations for linear motion.

Triangles are the supplied deterministic surface; no feature is discarded for
being nearly vertical. Between consecutive VF/FV/EE (including persistent-plane
VE) events the strict interior-intersection Boolean cannot change.
"""
from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache
from . import exact_geom as G
from .geom3 import Polyhedron


@dataclass(frozen=True, slots=True)
class SurfaceEvent:
    time: F
    label: tuple
    normal: tuple


def translate_exact(P, offset):
    """Translate the exact supplied coordinate values, without float subtraction."""
    q=tuple(F(x) for x in offset)
    return Polyhedron([tuple(F(x)+d for x,d in zip(p,q)) for p in P.verts], P.faces)


def _descriptor(vertices, faces, fi, tri):
    ring=faces[fi]
    n=G.cross(G.sub(vertices[tri[1]],vertices[tri[0]]),G.sub(vertices[tri[2]],vertices[tri[0]]))
    if all(G.dot(n,G.sub(vertices[i],vertices[tri[0]])) == 0 for i in ring):
        return ('face',fi)
    return ('face',fi,'triangle',*tri)


def _point_edge_time(p, velocity, a, b):
    e=G.sub(b,a); w=G.sub(a,p); n=G.cross(velocity,e); nn=G.dot(n,n)
    if not nn:
        return ()
    if G.dot(n,w):
        return ()
    t=G.dot(G.cross(w,e),n)/nn
    s=G.dot(G.cross(w,velocity),n)/nn
    return (t,) if 0 <= s <= 1 else ()


def surface_events(A,B,direction=(0,0,1),start=(0,0,0),t_min=0,t_max=None):
    """All exact boundary-contact event times, with source-feature witnesses.

    t_min/t_max only restrict returned times. Parallel persistent-plane edge
    pairs add endpoint-on-edge events; exactly parallel endpoint coincidence is
    included too. A caller may classify each open interval at one exact point.
    """
    av=tuple(tuple(F(x)+F(y) for x,y in zip(p,start)) for p in A.verts)
    bv=tuple(G.vector(p) for p in B.verts)
    d=G.vector(direction)
    return _events_cached(av,tuple(A.faces),bv,tuple(B.faces),d,F(t_min),None if t_max is None else F(t_max))


@lru_cache(maxsize=256)
def _events_cached(av,af,bv,bf,d,t_min,t_max):
    at=G.triangulate(av,af); bt=G.triangulate(bv,bf)
    # Exact static-coordinate intervals: a moving contact cannot occur if the
    # source features are disjoint along an axis with zero velocity. Inclusive
    # endpoints preserve every tangent/degenerate event; no float filter is used.
    static_axes=tuple(k for k,x in enumerate(d) if not x)
    minus_d=G.mul(d,F(-1))
    events={}
    def put(t,label,n):
        if t >= t_min and (t_max is None or t <= t_max):
            events[(t,label)]=SurfaceEvent(t,label,n)
    for verts,tris,other,faces,velocity,kind in ((av,bt,bv,bf,d,'VF'),(bv,at,av,af,minus_d,'FV')):
        for fi,indices in tris:
            a,b,c=(other[i] for i in indices)
            n=G.cross(G.sub(b,a),G.sub(c,a)); den=G.dot(n,velocity)
            if not den:
                continue
            descriptor=_descriptor(other,faces,fi,indices)
            bounds=tuple((k,min(a[k],b[k],c[k]),max(a[k],b[k],c[k])) for k in static_axes)
            for vi,p in enumerate(verts):
                if any(p[k]<lo or p[k]>hi for k,lo,hi in bounds):
                    continue
                t=G.dot(n,G.sub(a,p))/den
                if t < t_min or (t_max is not None and t>t_max):
                    continue
                q=G.add(p,G.mul(velocity,t))
                if G.triangle_locate(q,a,b,c,n) < 0:
                    continue
                label=(kind,('vertex',vi),descriptor) if kind=='VF' else (kind,descriptor,('vertex',vi))
                put(t,label,n if kind=='VF' else G.mul(n,F(-1)))
    ae=sorted({tuple(sorted(e)) for _,tri in at for e in zip(tri,tri[1:]+tri[:1])})
    be=sorted({tuple(sorted(e)) for _,tri in bt for e in zip(tri,tri[1:]+tri[:1])})
    def edges(vertices,indices):
        return tuple((i,j,vertices[i],G.sub(vertices[j],vertices[i]),
                      tuple((min(vertices[i][k],vertices[j][k]),
                             max(vertices[i][k],vertices[j][k])) for k in static_axes))
                     for i,j in indices)
    edges_b=edges(bv,be)
    for ai,aj,a,u,ab in edges(av,ae):
        for bi,bj,b,v,bb in edges_b:
            if any(ahi<blo or bhi<alo for (alo,ahi),(blo,bhi) in zip(ab,bb)):
                continue
            n=G.cross(u,v); den=G.dot(n,d)
            label=('EE',('edge',ai,aj),('edge',bi,bj))
            if den:
                t=G.dot(n,G.sub(b,a))/den
                if t<t_min or (t_max is not None and t>t_max):
                    continue
                w=G.sub(b,G.add(a,G.mul(d,t))); nn=G.dot(n,n)
                s=G.dot(G.cross(w,v),n)/nn; r=G.dot(G.cross(w,u),n)/nn
                if 0<=s<=1 and 0<=r<=1:
                    put(t,label,n)
            elif not G.dot(n,G.sub(b,a)):
                # Both segments stay in the same plane; an overlap starts or
                # ends when an endpoint crosses the other finite segment.
                for p in (a,av[aj]):
                    for t in _point_edge_time(p,d,b,bv[bj]):
                        put(t,label,n)
                for p in (b,bv[bj]):
                    for t in _point_edge_time(p,minus_d,a,av[aj]):
                        put(t,label,n)
                if not any(n):
                    k=next((k for k,x in enumerate(d) if x),None)
                    if k is not None:
                        for p in (a,av[aj]):
                            for q in (b,bv[bj]):
                                t=(q[k]-p[k])/d[k]
                                if G.add(p,G.mul(d,t))==q:
                                    put(t,label,n)
    return tuple(sorted(events.values(),key=lambda e:(e.time,e.label)))

def star_core(P, window):
    """Exact inner homothetic core for a local radial-thickness certificate.

    A certified star centre lies behind every oriented surface triangle. Rays
    from that centre give a radial boundary parametrisation. Each removed radial
    segment is no longer than window (L1 is a rational upper bound on L2), so
    nonintersection of the core proves purely local shallow penetration.
    None means no such certificate was found, not that the body is non-star.
    This is not a bound on the whole-body shortest separating translation (PD).
    """
    w=F(window)
    if w<0:
        raise ValueError('contact_window must be nonnegative')
    if not w:
        return P
    verts=tuple(G.vector(v) for v in P.verts)
    centre=tuple(sum(v[k] for v in verts)/len(verts) for k in range(3))
    for _,tri in G.triangles(P):
        a,b,c=tri; n=G.cross(G.sub(b,a),G.sub(c,a))
        if G.dot(n,G.sub(centre,a))>=0:
            return None
    radius=max(sum(abs(x-y) for x,y in zip(p,centre)) for p in verts)
    alpha=min(w/radius,F(1,2))
    return Polyhedron([G.add(centre,G.mul(G.sub(p,centre),1-alpha)) for p in verts],P.faces)

def contact_models(A,B,window):
    """Local penetration-thickness window certificate geometries (not PD).

    A nonnegative explicit window is a reporting policy, never a hidden tolerance.
    For overlapping inputs, a nonpenetrating +/-window coordinate-axis translation
    proves rigid-body Euclidean penetration depth PD <= window. A nonpenetrating
    certified star core proves every overlap region lies in that body's radial
    shell, whose Euclidean thickness is <= window; it does not bound whole-body PD.
    The original pair, available star cores and all six translations are ORed by
    margin and kinetic escape. Rejection does not imply PD > window. Six-axis
    sampling and the L1-radius shell are coordinate dependent: shorter oblique
    escapes can be missed and rotation invariance is not guaranteed.
    """
    w=F(window)
    if w<0:
        raise ValueError('contact_window must be nonnegative')
    if not w:
        return (('exact',A,B),)
    choices=[]
    ca,cb=star_core(A,w),star_core(B,w)
    if ca is not None:choices.append(('core_A',ca,B))
    if cb is not None:choices.append(('core_B',A,cb))
    choices.append(('exact',A,B))
    for axis in range(3):
        for sign in (-1,1):
            offset=tuple(w*sign if k==axis else F(0) for k in range(3))
            choices.append((f'shift_{axis}_{sign}',translate_exact(A,offset),B))
    return tuple(choices)
