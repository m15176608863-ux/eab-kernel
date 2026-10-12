"""Frozen c194dbb exact-sweep algorithm for WO-PERF value-for-value checks.

This is an equivalence reference, NOT an independent geometry oracle. Its
Fraction arithmetic helpers are shared deliberately; event enumeration, ordering,
labels and normal magnitudes must all remain identical to the unpruned algorithm.
"""
from fractions import Fraction as F
from eab.kernel3d import exact_geom as G
from eab.kernel3d.exact_sweep import SurfaceEvent

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


def reference_events(av,af,bv,bf,d,t_min,t_max):
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
