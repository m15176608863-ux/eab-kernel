"""Independent exact surface-distance oracle for concave G0.

Only coordinates and face rings enter. No production geometry or predicates are
imported: integer face-plane/winding and edge parameters determine separation;
rational squared distances use the independent midpoint-certified reference boundary.
"""
from fractions import Fraction as F
from functools import lru_cache
from math import gcd, lcm
from ..kernel2d.g0_oracle import sqrt_display


def minus(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def bounds(v):return tuple((min(p[i] for p in v),max(p[i] for p in v)) for i in range(3))
def boxes_disjoint(a,b):return any(x[1]<y[0] or y[1]<x[0] for x,y in zip(a,b))


def face_pieces(vertices, face):
    """Planar rings remain whole; folded rings use source-order projected ears.

    This independently implements the declared surface interpolation rather
    than replacing a folded ring by its first-three-point supporting plane.
    """
    ring=tuple(vertices[i] for i in face);o=ring[0]
    normal=(0,0,0)
    for a,b in zip(ring,ring[1:]+ring[:1]):
        w=cross(minus(a,o),minus(b,o))
        normal=tuple(normal[i]+w[i] for i in range(3))
    if not any(normal):raise ValueError('G0 oracle: degenerate face')
    h=dot(normal,o)
    if all(dot(normal,p)==h for p in ring):return (face,)
    axis=max(range(3),key=lambda i:abs(normal[i]));axes=((axis+1)%3,(axis+2)%3)
    projected={i:tuple(vertices[i][a] for a in axes) for i in face}
    def orient(a,b,c):
        a,b,c=projected[a],projected[b],projected[c]
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    sign=1 if normal[axis]>0 else -1
    rest=list(face);out=[]
    while len(rest)>3:
        for k,b in enumerate(rest):
            a,c=rest[k-1],rest[(k+1)%len(rest)]
            if sign*orient(a,b,c)<=0:continue
            if any(all(sign*orient(u,v,p)>=0 for u,v in ((a,b),(b,c),(c,a)))
                   for p in rest if p not in (a,b,c)):continue
            out.append((a,b,c));rest.pop(k);break
        else:
            k=next((k for k,b in enumerate(rest) if orient(rest[k-1],b,rest[(k+1)%len(rest)])==0),None)
            if k is None:raise ValueError('G0 oracle: nonsimple face projection')
            tri=(rest[k-1],rest[k],rest[(k+1)%len(rest)])
            a,b,c=(vertices[i] for i in tri)
            if any(cross(minus(b,a),minus(c,a))):out.append(tri)
            rest.pop(k)
    return tuple(out)+(tuple(rest),)


@lru_cache(maxsize=128)
def model(vertices,faces):
    """Content-keyed immutable integer payload: mutation cannot stale this cache."""
    faces=tuple(piece for f in faces for piece in face_pieces(vertices,f))
    edges=tuple(sorted({tuple(sorted((a,b))) for f in faces for a,b in zip(f,f[1:]+f[:1])}))
    rings=[]
    for f in faces:
        ring=tuple(vertices[i] for i in f);o=ring[0]
        n=next((cross(minus(a,o),minus(b,o)) for a,b in zip(ring[1:],ring[2:])
                if any(cross(minus(a,o),minus(b,o)))),None)
        if n is None:raise ValueError('G0 oracle: degenerate face')
        common=gcd(*n);n=tuple(v//common for v in n)
        h=dot(n,o);nn=dot(n,n)
        axes=tuple(i for i in range(3) if i!=max(range(3),key=lambda i:abs(n[i])))
        rings.append((ring,n,h,nn,axes,bounds(ring)))
    adjacency={i:set() for i in range(len(vertices))}
    for a,b in edges:adjacency[a].add(b);adjacency[b].add(a)
    unseen=set(adjacency);representatives=[]
    while unseen:
        root=min(unseen);representatives.append(vertices[root]);pending=[root];unseen.remove(root)
        while pending:
            for neighbor in adjacency[pending.pop()]:
                if neighbor in unseen:unseen.remove(neighbor);pending.append(neighbor)
    return vertices,tuple(rings),tuple((vertices[a],vertices[b]) for a,b in edges),bounds(vertices),tuple(representatives)


def in_face(numerator,denominator,face):
    """Exact homogeneous point membership in a planar (possibly concave) ring."""
    ring,_,_,_,axes,_=face;i,j=axes
    x,y=numerator[i],numerator[j];winding=0
    for a,b in zip(ring,ring[1:]+ring[:1]):
        ax,ay,bx,by=a[i]*denominator,a[j]*denominator,b[i]*denominator,b[j]*denominator
        t=(bx-ax)*(y-ay)-(by-ay)*(x-ax)
        if t==0 and min(ax,bx)<=x<=max(ax,bx) and min(ay,by)<=y<=max(ay,by):return 0
        if ay<=y<by and t>0:winding+=1
        elif by<=y<ay and t<0:winding-=1
    return 1 if winding else -1


def contains(p,M):
    """Integer generic-ray parity, retrying edge/vertex hits without tolerance."""
    _,faces,_,bbox,_=M
    if any(p[i]<bbox[i][0] or p[i]>bbox[i][1] for i in range(3)):return -1
    for face in faces:
        if dot(face[1],p)==face[2] and in_face(p,1,face)>=0:return 0
    # A moment-curve ray avoids each of finitely many bad planes/edge directions
    # for all but finitely many integer k, so exact retries terminate.
    k=1
    while True:
        u=(1,k,k*k);hits=0;retry=False
        for face in faces:
            n,h=face[1],face[2]
            den=dot(n,u);num=h-dot(n,p)
            if den==0:
                if num==0:retry=True;break
                continue
            if num*den<=0:continue
            if den<0:den,num=-den,-num
            q=tuple(p[i]*den+u[i]*num for i in range(3))
            state=in_face(q,den,face)
            if state==0:retry=True;break
            if state==1:hits+=1
        if not retry:return 1 if hits%2 else -1
        k+=1


def segment_face_hits(a,b,face):
    n,h=face[1],face[2]
    aa,bb=dot(n,a)-h,dot(n,b)-h
    if aa*bb>0:return False
    if aa==bb==0:
        # Coplanar boundary crossings are handled by edge-edge distance below;
        # endpoint membership catches coplanar containment.
        return in_face(a,1,face)>=0 or in_face(b,1,face)>=0
    den=aa-bb;num=aa
    if den<0:den,num=-den,-num
    p=tuple(a[i]*den+(b[i]-a[i])*num for i in range(3))
    return in_face(p,den,face)>=0


def separated_distance(av,af,bv,bf,*,squared=False):
    """Return distance for strictly disjoint solids, None for overlap/contact.

    Independent primitives: exact integer plane/ring winding and segment
    intersection, parity containment, rational vertex/face and edge/edge minima.
    Surface-contact distance zero is not mislabeled a separated sample.
    """
    av=tuple(tuple(F(c) for c in p) for p in av)
    bv=tuple(tuple(F(c) for c in p) for p in bv)
    den=lcm(*(c.denominator for p in av+bv for c in p))
    a=tuple(tuple(int(c*den) for c in p) for p in av)
    b=tuple(tuple(int(c*den) for c in p) for p in bv)
    A,B=model(a,tuple(map(tuple,af))),model(b,tuple(map(tuple,bf)))
    if not boxes_disjoint(A[3],B[3]):
        for P,Q in ((A,B),(B,A)):
            for p,q in P[2]:
                eb=bounds((p,q))
                for face in Q[1]:
                    if not boxes_disjoint(eb,face[5]) and segment_face_hits(p,q,face):return None
        if any(contains(p,B)>=0 for p in A[4]) or any(contains(p,A)>=0 for p in B[4]):return None
    best=F(dot(minus(a[0],b[0]),minus(a[0],b[0])))
    def keep(num,den=1):
        nonlocal best
        if num*best.denominator<best.numerator*den:best=F(num,den)
    def point_segment(p,q,r):
        u=minus(r,q);w=minus(p,q);uu=dot(u,u);uw=dot(u,w);ww=dot(w,w)
        if uw<=0:keep(ww)
        elif uw>=uu:keep(dot(minus(p,r),minus(p,r)))
        else:keep(ww*uu-uw*uw,uu)
    for P,Q in ((A,B),(B,A)):
        for p in P[0]:
            for face in Q[1]:
                _,n,h,nn,_,_=face
                height=dot(n,p)-h
                if height*height*best.denominator>=best.numerator*nn:continue
                projected=tuple(p[i]*nn-n[i]*height for i in range(3))
                if in_face(projected,nn,face)>=0:keep(height*height,nn)
    for p,q in A[2]:
        u=minus(q,p);aa=dot(u,u);abounds=bounds((p,q))
        for r,s in B[2]:
            bbounds=bounds((r,s))
            lower=sum(max(0,x[0]-y[1],y[0]-x[1])**2 for x,y in zip(abounds,bbounds))
            if lower*best.denominator>=best.numerator:continue
            point_segment(p,r,s);point_segment(q,r,s)
            point_segment(r,p,q);point_segment(s,p,q)
            v=minus(s,r);w=minus(p,r);bb=dot(u,v);cc=dot(v,v);dd=dot(u,w);ee=dot(v,w)
            det=aa*cc-bb*bb
            if det:
                sn,tn=bb*ee-cc*dd,aa*ee-bb*dd
                if 0<sn<det and 0<tn<det:
                    keep(dot(w,w)*det+dd*sn-ee*tn,det)
    if best==0:return None
    result=best/F(den*den)
    return result if squared else sqrt_display(result)
