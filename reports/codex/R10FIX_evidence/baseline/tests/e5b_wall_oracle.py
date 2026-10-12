"""Independent wall escape oracle: integer triangle SAT intervals + parity rays.

Only raw vertices/rings are consumed. No production predicate, event enumerator,
translation, vector primitive, distance or triangulation is imported. The ring
triangulator is the existing independent E5a2 test implementation. This oracle
certifies the wall family by a connected union of *strict transverse* triangle
collision intervals and excludes containment at the earliest uncovered root.
"""
from fractions import Fraction as F
from math import lcm
from functools import lru_cache
from e5a2_surface_oracle import _ring_triangles


def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])


def triangles(P):
    v=tuple(tuple(map(F,p)) for p in P.verts)
    return tuple(t for ring in P.faces for t in _ring_triangles(v,ring))


def inside(p,tris):
    """Independent Moller-style rational parity, explicit boundary exclusion."""
    for k in range(1,1000):
        d=(F(1),F(k),F(k*k+1));hits=0;bad=False
        for a,b,c in tris:
            e1,e2,w=sub(b,a),sub(c,a),sub(p,a);h=cross(d,e2);det=dot(e1,h)
            if not det: continue
            q=cross(w,e1);u,v,t=dot(w,h)/det,dot(d,q)/det,dot(e2,q)/det
            if t<0 or min(u,v)<0 or u+v>1:continue
            if t==0:return False
            if min(u,v)==0 or u+v==1:bad=True;break
            hits+=1
        if not bad:return hits%2==1
    raise AssertionError('independent ray family exhausted')


def _interval(a,b,denominator,strict):
    ae=[sub(a[(i+1)%3],a[i]) for i in range(3)]
    be=[sub(b[(i+1)%3],b[i]) for i in range(3)]
    an,bn=cross(ae[0],ae[1]),cross(be[0],be[1])
    axes=[an,bn]+[cross(u,v) for u in ae for v in be]
    if not any(cross(an,bn)):
        if strict:return None
        axes += [cross(an,u) for u in ae]+[cross(bn,v) for v in be]
    lo,hi=None,None
    for n in axes:
        if not any(n):continue
        av=[dot(n,p) for p in a];bv=[dot(n,p) for p in b]
        lower,upper=min(bv)-max(av),max(bv)-min(av)
        velocity=n[2]*denominator
        if not velocity:
            if (lower>=0 or upper<=0) if strict else (lower>0 or upper<0):return None
            continue
        x,y=F(lower,velocity),F(upper,velocity)
        x,y=min(x,y),max(x,y)
        lo=x if lo is None else max(lo,x);hi=y if hi is None else min(hi,y)
        if lo>hi or (strict and lo==hi):return None
    if hi is None or hi<0:return None
    return lo,hi


def earliest_wall_escape(A,B):
    aa,bb=triangles(A),triangles(B)
    return _earliest(aa,bb)


@lru_cache(maxsize=256)
def _earliest(aa,bb):
    denominator=lcm(*(x.denominator for tri in aa+bb for p in tri for x in p))
    origin=aa[0][0]
    ints=lambda seq:[tuple(tuple(int((p[i]-origin[i])*denominator) for i in range(3)) for p in tri) for tri in seq]
    ia,ib=ints(aa),ints(bb)
    spans=[]
    for a in ia:
        for b in ib:
            result=_interval(a,b,denominator,True)
            if result is not None:spans.append(result)
    spans.sort()
    root=F(0);started=False
    for lo,hi in spans:
        if lo<root and hi>root:
            root=hi;started=True
        elif not started and lo<0<hi:
            root=hi;started=True
        elif lo>=root:
            break
    assert started,'wall oracle requires a strict transverse initial overlap certificate'
    # Every height below root is covered by the interval union. At root no
    # strict triangle-interior crossing remains; verify there is no containment.
    moved=tuple(tuple((p[0],p[1],p[2]+root) for p in tri) for tri in aa)
    assert not any(inside(p,bb) for tri in moved for p in tri),'key vertex contained at oracle escape'
    assert not any(inside(p,moved) for tri in bb for p in tri),'wall vertex contained at oracle escape'
    # Same-side coincident 2D boundaries would require a separate volume test.
    # The wall family at its exit has only opposite-facing contact patches.
    for a in ia:
        for b in ib:
            an=cross(sub(a[1],a[0]),sub(a[2],a[0]));bn=cross(sub(b[1],b[0]),sub(b[2],b[0]))
            if any(cross(an,bn)) or dot(an,bn)<=0:continue
            span=_interval(a,b,denominator,False)
            if span is not None and span[0]<=root<=span[1]:
                # A common plane on the same side is permissible only when
                # its closed footprints have no relative-interior overlap.
                shifted=tuple((F(p[0]),F(p[1]),F(p[2])+root*denominator) for p in a)
                if dot(an,sub(b[0],shifted[0]))==0:
                    axes=[cross(an,sub(a[(i+1)%3],a[i])) for i in range(3)]+[cross(bn,sub(b[(i+1)%3],b[i])) for i in range(3)]
                    assert any(max(dot(n,p) for p in shifted)<=min(dot(n,p) for p in b) or max(dot(n,p) for p in b)<=min(dot(n,p) for p in shifted) for n in axes if any(n)), 'same-side area overlap unsupported by wall oracle'
    # Strictly separated right neighbourhood independently certifies safety
    # at the endpoint: strict volume overlap is open in the translation height.
    # Closed triangle SAT intervals bound that neighbourhood; all pairs must be
    # strictly separated there, with parity rays excluding containment.
    closed=[span for a in ia for b in ib if (span:=_interval(a,b,denominator,False)) is not None]
    endpoints=[z for lo,hi in closed for z in (lo,hi) if z is not None and z>root]
    probe=(root+min(endpoints))/2 if endpoints else root+F(1)
    assert all(not(lo<=probe<=hi) for lo,hi in closed), 'wall oracle requires strict right-side surface separation'
    moved_probe=tuple(tuple((p[0],p[1],p[2]+probe) for p in tri) for tri in aa)
    assert not inside(moved_probe[0][0],bb) and not inside(bb[0][0],moved_probe), 'right-side containment excluded'
    return root

def earliest_star_escape(A,B,offset=(0,0,0)):
    """Independent exact tetrahedral-union swept SAT oracle for star bodies.

    The test-only decomposition first certifies its star centre. Each tetrahedron
    pair contributes an open interval of strict volume intersection. Their union
    gives every and only penetrating height, hence its first missing point is
    the exact earliest escape; no event enumeration or production predicate.
    """
    from e5a2_surface_oracle import _tetrahedra
    aa,bb=_tetrahedra(A),_tetrahedra(B)
    d=tuple(map(F,offset))
    aa=tuple(tuple(tuple(p[i]+d[i] for i in range(3)) for p in tet) for tet in aa)
    return _star_root(aa,tuple(bb))


@lru_cache(maxsize=256)
def _star_root(aa,bb):
    from itertools import combinations
    denominator=lcm(*(x.denominator for tet in aa+bb for p in tet for x in p))
    origin=aa[0][0]
    ints=lambda seq:[tuple(tuple(int((p[i]-origin[i])*denominator) for i in range(3)) for p in tet) for tet in seq]
    ia,ib=ints(aa),ints(bb)
    spans=[]
    for a in ia:
        for b in ib:
            if any(max(p[i] for p in a)<=min(p[i] for p in b) or max(p[i] for p in b)<=min(p[i] for p in a) for i in (0,1)):
                continue
            axes=[cross(sub(t[j],t[i]),sub(t[k],t[i])) for t in (a,b) for i,j,k in combinations(range(4),3)]
            ae=[sub(q,p) for p,q in combinations(a,2)];be=[sub(q,p) for p,q in combinations(b,2)]
            axes += [cross(u,v) for u in ae for v in be]
            lo=hi=None;valid=True
            for n in axes:
                if not any(n):continue
                av=[dot(n,p) for p in a];bv=[dot(n,p) for p in b]
                lower,upper=min(bv)-max(av),max(bv)-min(av);velocity=n[2]*denominator
                if not velocity:
                    if lower>=0 or upper<=0:valid=False;break
                    continue
                x,y=F(lower,velocity),F(upper,velocity);x,y=min(x,y),max(x,y)
                lo=x if lo is None else max(lo,x);hi=y if hi is None else min(hi,y)
                if lo>=hi:valid=False;break
            if valid and hi is not None and hi>0:spans.append((lo,hi))
    root=F(0)
    for lo,hi in sorted(spans):
        if lo<root<hi:root=hi
        elif lo>=root:break
    return root
