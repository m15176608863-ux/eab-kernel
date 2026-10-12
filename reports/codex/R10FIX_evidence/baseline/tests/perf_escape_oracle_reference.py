"""Independent complete facet-candidate oracle for legacy escape windows.

Only data are read from bodies. No production geometry, cover or interlock
function is imported. Rational cyclic Newell/Gram predicates come from the
independent test oracle. The still-legacy escape resolution policy is evaluated
explicitly, rather than inferred from the production candidate/tied outputs.
"""
import math
from functools import lru_cache
from fractions import Fraction as F
from perf_cover_oracle_reference import model, vertex, arc, face_extent, dot, sub, add, scale, cross
from construction_oracle import norm_exact, scalar_exact, sqrt_exact, unit_exact

EPS = 2.220446049250313e-16


def unit(v):
    # Display only, backed by the exact model and exact cone tests; candidate nz
    # must exceed the explicit >=1e-12 window, never the subnormal range.
    return unit_exact(v, allow_underflow=True)


def norm(v):
    return norm_exact(v)


def _signed_gap(n, displacement):
    numerator = dot(n, displacement)
    magnitude = sqrt_exact(numerator*numerator/dot(n, n))
    return -magnitude if numerator < 0 else magnitude


def move(v, offset):
    # This is the caller's rounded translation, not an exact ideal motion.
    return tuple(tuple(p[k]+offset[k] for k in range(3)) for p in v)


def face_band(m, fi, p, extent):
    if face_extent(m, fi, p):
        return True
    if extent <= 0:
        return False
    ring = m[1][fi]
    for i,j in zip(ring, ring[1:]+ring[:1]):
        w,d = sub(p,m[0][i]),sub(m[0][j],m[0][i])
        t = max(F(0),min(F(1),dot(w,d)/dot(d,d)))
        r = sub(w,scale(d,t))
        if dot(r,r) <= F(extent)**2:
            return True
    return False


def parameter_band(t, direction, extent):
    return 0 <= t <= 1 or (min(abs(t),abs(t-1))**2*dot(direction,direction) <= F(extent)**2)


def facet(a,b,label,tol=1e-9,extent=0., *, extent_only=False, exact_coefficients=False):
    kind, af, bf = label
    if kind == 'VF':
        p, n = a[0][af[1]], b[2][bf[1]]
        if vertex(a,af[1],scale(n,-1),tol) < 0:
            return None
        w = sub(p,b[0][b[1][bf[1]][0]])
        projection = sub(p,scale(n,dot(n,w)/dot(n,n)))
        if extent_only:
            return None,None,face_band(b,bf[1],projection,extent)
        if exact_coefficients:
            return n,dot(n,w),face_band(b,bf[1],projection,extent)
        normal = unit(n)
        gap = _signed_gap(n, w)
        return normal,gap,face_band(b,bf[1],projection,extent)
    if kind == 'FV':
        record = facet(b,a,('VF',bf,af),tol,extent,extent_only=extent_only,
                       exact_coefficients=exact_coefficients)
        if extent_only:
            return record
        return None if record is None else (tuple(-x for x in record[0]),record[1],record[2])
    ea,eb = af[1:],bf[1:]
    u,v = sub(a[0][ea[1]],a[0][ea[0]]),sub(b[0][eb[1]],b[0][eb[0]])
    aa,ab,bb = dot(u,u),dot(u,v),dot(v,v)
    det = aa*bb-ab*ab
    if not det:
        return None
    w = sub(b[0][eb[0]],a[0][ea[0]])
    aw,bw = dot(u,w),dot(v,w)
    s,t = (bb*aw-ab*bw)/det,(ab*aw-aa*bw)/det
    n = cross(v,u)
    for d in (n,scale(n,-1)):
        if arc(b,eb,d,tol) < 0 or arc(a,ea,scale(d,-1),tol) < 0:
            continue
        pa,pb = add(a[0][ea[0]],scale(u,s)),add(b[0][eb[0]],scale(v,t))
        if extent_only:
            return None,None,parameter_band(s,u,extent) and parameter_band(t,v,extent)
        if exact_coefficients:
            return d,dot(d,sub(pa,pb)),parameter_band(s,u,extent) and parameter_band(t,v,extent)
        normal = unit(d)
        gap = _signed_gap(d, sub(pa, pb))
        return normal,gap,parameter_band(s,u,extent) and parameter_band(t,v,extent)
    return None


@lru_cache(maxsize=256)
def geometry_noise(vertices, faces):
    """Independent evaluation of the declared legacy face/edge noise report."""
    m = model(vertices,faces)
    coordinate = max(abs(c) for p in vertices for c in p)
    edge = {e:64*EPS*coordinate/norm(sub(vertices[e[1]],vertices[e[0]])) for e in m[3]}
    face = []
    for fi,ring in enumerate(faces):
        perimeter=sum(norm(sub(vertices[j],vertices[i])) for i,j in zip(ring,ring[1:]+ring[:1]))
        face.append(64*EPS*coordinate*perimeter/norm(m[2][fi]))
    return m,tuple(face),edge


def direction_noise(av, af, bv, bf, label):
    a,an,ae=geometry_noise(av,af)
    b,bn,be=geometry_noise(bv,bf)
    kind,x,y=label
    if kind=='VF':
        return bn[y[1]]
    if kind=='FV':
        return an[x[1]]
    ea,eb=x[1:],y[1:]
    da,db=sub(a[0][ea[1]],a[0][ea[0]]),sub(b[0][eb[1]],b[0][eb[0]])
    n=cross(da,db)
    nn = dot(n,n)
    if not nn:
        return math.inf
    total = F(ae[ea])+F(be[eb])
    try:
        return sqrt_exact(total*total*dot(da,da)*dot(db,db)/nn)
    except OverflowError:
        # Explicit saturation of a legacy uncertainty diagnostic, not geometry.
        return math.inf


def windows(av,bv):
    length=min(max(norm(sub(p,v[0])) for p in v) for v in (av,bv))
    coordinate=max(abs(x) for v in (av,bv) for p in v for x in p)
    rounding=64*EPS*max(coordinate,length)
    return max(1e-9*length,rounding),rounding


def candidates(A,B,offset):
    return _candidates(tuple(A.verts),tuple(A.faces),tuple(B.verts),tuple(B.faces),tuple(offset))


@lru_cache(maxsize=128)
def _candidates(av,af,bv,bf,offset):
    av=move(av,offset)
    a,b=model(av,af),model(bv,bf)
    extent,rounding=windows(av,bv)
    labels=[('VF',('vertex',i),('face',j)) for i in range(len(av)) for j in range(len(bf))]
    labels += [('FV',('face',i),('vertex',j)) for i in range(len(af)) for j in range(len(bv))]
    labels += [('EE',('edge',*ea),('edge',*eb)) for ea in sorted(a[3]) for eb in sorted(b[3])]
    raw=[]
    for index,label in enumerate(labels):
        c=facet(a,b,label,exact_coefficients=True)
        if c is None:
            continue
        normal,numerator,_=c
        nn = dot(normal,normal)
        threshold = max(1e-12,direction_noise(av,af,bv,bf,label))
        if normal[2] <= 0 or math.isinf(threshold) or normal[2]**2 <= F(threshold)**2*nn:
            continue
        if numerator <= 0 or numerator*numerator <= F(rounding)**2*nn:
            z=scalar_exact(-numerator/normal[2])
            nz=unit(normal)[2]
            raw.append((max(0.,z),label,nz,index))
    raw.sort(key=lambda row:row[0])
    out=[]
    zprev,az=None,None
    for z,label,nz,index in raw:
        if z<=0:
            out.append((z,label,nz,index))
            continue
        if zprev is None or z-zprev>rounding:
            zprev,az=z,model(move(av,(0.,0.,z)),af)
        # Extent-only validation never constructs an unused display residual.
        c=facet(az,b,label,extent=extent,extent_only=True)
        if c is not None and c[2]:
            out.append((z,label,nz,index))
    return tuple(out),extent,rounding


def tied_labels(A,B,offset,analytic_height):
    """Complete ties at the independently known accepted escape height.

    Selection policy is legacy and intentionally not claimed exact by E5a;
    every candidate's local geometric validity/extent is independently exact.
    """
    rows,extent,rounding=candidates(A,B,offset)
    close=[r for r in rows if r[0]>0 and abs(r[0]-analytic_height)<=4*rounding/max(r[2],1e-30)]
    assert close, 'analytic escape has no independent candidate'
    chosen=min(close,key=lambda r:r[0])
    z,_,nz,_=chosen
    ties={lab for zh,lab,nzh,_ in rows if zh>0 and abs(zh-z)*nzh<=extent+rounding*(1+nzh/nz)}
    return ties
