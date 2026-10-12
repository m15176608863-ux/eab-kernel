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
    events={}
    def put(t,label,n):
        if t >= t_min and (t_max is None or t <= t_max):
            events[(t,label)]=SurfaceEvent(t,label,n)
    for verts,tris,other,faces,velocity,kind in ((av,bt,bv,bf,d,'VF'),(bv,at,av,af,G.mul(d,F(-1)),'FV')):
        for fi,indices in tris:
            a,b,c=(other[i] for i in indices)
            n=G.cross(G.sub(b,a),G.sub(c,a)); den=G.dot(n,velocity)
            if not den:
                continue
            descriptor=_descriptor(other,faces,fi,indices)
            for vi,p in enumerate(verts):
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
    for ai,aj in ae:
        a=av[ai]; u=G.sub(av[aj],a)
        for bi,bj in be:
            b=bv[bi]; v=G.sub(bv[bj],b); n=G.cross(u,v); den=G.dot(n,d)
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
                    for t in _point_edge_time(p,G.mul(d,F(-1)),a,av[aj]):
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
    """Exact inner homothetic core with removed shell thickness at most window.

    A certified star centre lies behind every oriented surface triangle. Rays
    from that centre give a radial boundary parametrisation. Each removed radial
    segment is no longer than window (L1 is a rational upper bound on L2), so
    nonintersection of the core proves purely local shallow penetration.
    None means no such certificate was found, not that the body is non-star.
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
    """Shared finite rational contact-window certificate geometries.

    A supplied window is a nonnegative Euclidean displacement/shell *upper
    bound*, not an implicit tolerance. Membership is exact OR over the original
    pair, each available star core, and six exact coordinate-axis translations
    of A by +/-window. The same list is used by static margin and kinetic escape.
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
