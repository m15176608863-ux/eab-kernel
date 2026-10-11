"""Independent integer tetrahedral-union oracle for star-shaped ring surfaces.

Only raw coordinates/face indices are consumed. No production normal, hull,
triangulation, ray, distance, SAT, or arrangement primitive is imported. Float
coordinates are lifted exactly to a common integer denominator before SAT.
"""
from fractions import Fraction as F
from itertools import combinations
from math import lcm


def _minus(a,b):
    return tuple(a[i]-b[i] for i in range(3))


def _times(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])


def _scalar(a,b):
    return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]


def _ring_triangles(vertices,face):
    if len(face)==3:
        return [tuple(vertices[i] for i in face)]
    normal=(0,0,0)
    for i,j in zip(face,face[1:]+face[:1]):
        c=_times(_minus(vertices[i],vertices[face[0]]),_minus(vertices[j],vertices[face[0]]))
        normal=tuple(normal[k]+c[k] for k in range(3))
    drop=max(range(3),key=lambda k:abs(normal[k]));axes=((drop+1)%3,(drop+2)%3)
    v={i:tuple(vertices[i][k] for k in axes) for i in face}
    def orient(a,b,c):
        return (v[b][0]-v[a][0])*(v[c][1]-v[a][1])-(v[b][1]-v[a][1])*(v[c][0]-v[a][0])
    area=sum(v[i][0]*v[j][1]-v[i][1]*v[j][0] for i,j in zip(face,face[1:]+face[:1]))
    sign=1 if area>0 else -1
    ring=list(face);out=[]
    while len(ring)>3:
        for k,i in enumerate(ring):
            prev,nxt=ring[k-1],ring[(k+1)%len(ring)]
            if sign*orient(prev,i,nxt)<=0:
                continue
            if any(all(sign*orient(a,b,j)>=0 for a,b in ((prev,i),(i,nxt),(nxt,prev)))
                   for j in ring if j not in (prev,i,nxt)):
                continue
            out.append(tuple(vertices[j] for j in (prev,i,nxt)))
            ring.pop(k)
            break
        else:
            raise AssertionError('oracle requires a simple nondegenerate ring')
    out.append(tuple(vertices[j] for j in ring))
    return out


def _tetrahedra(P):
    v=[tuple(map(F,p)) for p in P.verts]
    center=tuple(sum(p[k] for p in v)/len(v) for k in range(3))
    triangles=[tri for f in P.faces for tri in _ring_triangles(v,f)]
    planes=[(_times(_minus(b,a),_minus(c,a)),a) for a,b,c in triangles]
    def visible(p):
        return all(_scalar(n,_minus(p,a))<0 for n,a in planes)
    if not visible(center):
        original=center
        candidates=[tuple((3*sum(p[k] for p in tri)/3+original[k])/4 for k in range(3)) for tri in triangles]
        center=next((p for p in candidates if visible(p)),None)
        if center is None:
            for ids in combinations(range(len(v)),4):
                p=tuple(sum(v[i][k] for i in ids)/4 for k in range(3))
                if visible(p):
                    center=p
                    break
        assert center is not None, 'oracle requires a star-shaped closed surface'
    return [(center,*tri) for tri in triangles]


def _sat(a,b):
    boundary=False
    axes=[]
    for t in (a,b):
        axes.extend(_times(_minus(t[j],t[i]),_minus(t[k],t[i]))
                    for i,j,k in combinations(range(4),3))
    ae=[_minus(q,p) for p,q in combinations(a,2)]
    be=[_minus(q,p) for p,q in combinations(b,2)]
    axes.extend(_times(u,v) for u in ae for v in be)
    for n in axes:
        if n == (0,0,0):
            continue
        x=[_scalar(n,p) for p in a];y=[_scalar(n,p) for p in b]
        gap=max(min(x)-max(y),min(y)-max(x))
        if gap > 0:
            return -1
        boundary |= gap == 0
    return 0 if boundary else 1


def star_overlap(A,B):
    aa,bb=_tetrahedra(A),_tetrahedra(B)
    denominator=lcm(*(x.denominator for tet in aa+bb for p in tet for x in p))
    aa,bb=([tuple(tuple(int(x*denominator) for x in p) for p in tet) for tet in seq] for seq in (aa,bb))
    contact=False
    for a in aa:
        for b in bb:
            if any(max(p[i] for p in a) < min(p[i] for p in b)
                   or max(p[i] for p in b) < min(p[i] for p in a) for i in range(3)):
                continue
            value=_sat(a,b)
            if value == 1:
                return 1
            contact |= value == 0
    return 0 if contact else -1


def _point_edge_sq(p,a,b):
    u,w=_minus(b,a),_minus(p,a);uu=_scalar(u,u)
    t=max(F(0),min(F(1),_scalar(w,u)/uu)) if uu else F(0)
    r=tuple(w[i]-t*u[i] for i in range(3))
    return _scalar(r,r)


def _point_tri_sq(p,tri):
    a,b,c=tri;n=_times(_minus(b,a),_minus(c,a));nn=_scalar(n,n)
    h=_scalar(n,_minus(p,a));q=tuple(p[i]-h*n[i]/nn for i in range(3))
    if all(_scalar(n,_times(_minus(v,u),_minus(q,u)))>=0 for u,v in ((a,b),(b,c),(c,a))):
        return h*h/nn
    return min(_point_edge_sq(p,u,v) for u,v in ((a,b),(b,c),(c,a)))


def _edge_edge_sq(p,q,a,b):
    u,v,w=_minus(q,p),_minus(b,a),_minus(a,p)
    n=_times(u,v); nn=_scalar(n,n)
    values=[_point_edge_sq(x,c,d) for x,c,d in ((p,a,b),(q,a,b),(a,p,q),(b,p,q))]
    if nn:
        s,t=_scalar(_times(w,v),n)/nn,_scalar(_times(w,u),n)/nn
        if 0 <= s <= 1 and 0 <= t <= 1:
            r=tuple(p[i]+s*u[i]-a[i]-t*v[i] for i in range(3))
            values.append(_scalar(r,r))
    return min(values)


def star_relation(A,B,tol=0):
    state=star_overlap(A,B)
    if state != -1 or not tol:
        return state
    aa=[tet[1:] for tet in _tetrahedra(A)];bb=[tet[1:] for tet in _tetrahedra(B)]
    tt=F(tol)**2
    for a in aa:
        for b in bb:
            if any(_point_tri_sq(p,b)<=tt for p in a) or any(_point_tri_sq(p,a)<=tt for p in b):
                return 0
            if any(_edge_edge_sq(p,q,u,v)<=tt
                   for p,q in zip(a,a[1:]+a[:1]) for u,v in zip(b,b[1:]+b[:1])):
                return 0
    return -1
