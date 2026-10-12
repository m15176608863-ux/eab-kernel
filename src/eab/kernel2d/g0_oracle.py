"""Independent exact G0 oracle, sharing no production geometric primitive.

The implementation uses integer winding/intersections and rational segment
projections/events. Final display uses the independent Fraction-midpoint reference boundary.
Support-domain policy: docs/exact_predicates_plan.md (R13FIXb). Exact rational
outputs remain unrestricted; final float displays reject unrepresentable values.
"""
from eab.oracle_construction import sqrt_exact, scalar_exact
from fractions import Fraction as F
from math import lcm


def sqrt_display(q):
    """Independent midpoint-certified square root; never round the square to float."""
    return sqrt_exact(q)


def points(P):
    return tuple((F(x), F(y)) for x, y in P)


def translate(P, x):
    x, y = (F(_mapped_value) for _mapped_value in x)
    return tuple((F(a)+x, F(b)+y) for a, b in P)


def turn(a,b,c):
    if any(isinstance(x,float) for p in (a,b,c) for x in p):
        a,b,c=points((a,b,c))
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def on_segment(p,a,b):
    return turn(a,b,p)==0 and all(min(a[i],b[i])<=p[i]<=max(a[i],b[i]) for i in (0,1))


def inside(p,P):
    winding=0
    for a,b in zip(P,P[1:]+P[:1]):
        t=turn(a,b,p)
        if t==0 and on_segment(p,a,b):return 0
        if a[1]<=p[1]<b[1] and t>0:winding+=1
        elif b[1]<=p[1]<a[1] and t<0:winding-=1
    return 1 if winding else -1


def overlap(A,B):
    """Strict overlap/contact/separation for simple CCW rings, exactly -1/0/1.

    Proper edge crossings and strict interior boundary portions imply area
    overlap. Remaining coincident edges overlap in area iff their CCW interiors
    are on the same side. Integer arithmetic is an exact common-denominator lift.
    """
    A,B=points(A),points(B)
    den=lcm(*(v.denominator for p in A+B for v in p))
    A=tuple(tuple(int(v*den) for v in p) for p in A)
    B=tuple(tuple(int(v*den) for v in p) for p in B)
    # Exact broad-phase: disjoint coordinate intervals prove separation.
    if any(max(p[i] for p in A)<min(p[i] for p in B) or
           max(p[i] for p in B)<min(p[i] for p in A) for i in (0,1)):
        return -1
    boundary=False
    for P,Q in ((A,B),(B,A)):
        for p in P:
            state=inside(p,Q)
            if state==1:return 1
            boundary |= state==0
    for a,b in zip(A,A[1:]+A[:1]):
        cuts={a,b}
        for c,d in zip(B,B[1:]+B[:1]):
            ac,ad,ca,cb=turn(a,b,c),turn(a,b,d),turn(c,d,a),turn(c,d,b)
            if ac*ad<0 and ca*cb<0:return 1
            if ac==ad==0:
                axis=0 if a[0]!=b[0] else 1
                lo=max(min(a[axis],b[axis]),min(c[axis],d[axis]))
                hi=min(max(a[axis],b[axis]),max(c[axis],d[axis]))
                if lo<hi and (b[axis]-a[axis])*(d[axis]-c[axis])>0:return 1
            if on_segment(c,a,b):cuts.add(c)
            if on_segment(d,a,b):cuts.add(d)
        # If crossings only hit vertices, split there before checking interiors.
        ordered=sorted(cuts)
        doubled=tuple((2*x,2*y) for x,y in B)
        for p,q in zip(ordered,ordered[1:]):
            if inside((p[0]+q[0],p[1]+q[1]),doubled)==1:return 1
    # Symmetric vertex-on-edge portions are covered by proper crossings above;
    # testing B edge midpoints also handles a containing ring with shared corners.
    doubled=tuple((2*x,2*y) for x,y in A)
    for a,b in zip(B,B[1:]+B[:1]):
        if inside((a[0]+b[0],a[1]+b[1]),doubled)==1:return 1
    return 0 if boundary else -1


def segment_square(p,a,b):
    p,a,b=points((p,a,b))
    ex,ey=b[0]-a[0],b[1]-a[1]
    wx,wy=p[0]-a[0],p[1]-a[1]
    length=ex*ex+ey*ey
    t=min(F(1),max(F(0),(wx*ex+wy*ey)/length)) if length else F(0)
    dx,dy=wx-t*ex,wy-t*ey
    return dx*dx+dy*dy,t


def distance(A,B):
    A,B=points(A),points(B)
    best=None;arg=None
    for P,Q,tag in ((A,B,'A-vertex/B-edge'),(B,A,'B-vertex/A-edge')):
        for i,p in enumerate(P):
            for j,a in enumerate(Q):
                square,t=segment_square(p,a,Q[(j+1)%len(Q)])
                if best is None or square<best:
                    best,arg=square,(tag,i,j,scalar_exact(t))
    return sqrt_display(best),arg



def boundary_has_exterior(A, B):
    """Exact local complement certificate, independent of production primitives.

    Vertex/supporting-edge lines partition translation space into cells where
    intersection is constant. At a contact event, inspect one rational point in
    every open angular sector of its incident lines. The step is smaller than
    every nonincident line crossing. An exterior sector means true boundary E;
    a tight-fit seam with no exterior sector is interior E, not an exit.
    """
    lines = set()
    rays = set()
    for P, Q, sign in ((A, B, 1), (B, A, -1)):
        for p in P:
            for a, b in zip(Q, Q[1:]+Q[:1]):
                ex, ey = b[0]-a[0], b[1]-a[1]
                if ex == ey == 0:
                    continue
                h = turn(a, b, p)
                lines.add((sign*-ey, sign*ex, h))
                if h == 0:
                    length = abs(ex)+abs(ey)
                    ray = (ex/length, ey/length)
                    rays.update((ray, (-ray[0], -ray[1])))
    def half(v):
        return 0 if v[1] > 0 or (v[1] == 0 and v[0] > 0) else 1
    def compare(u, v):
        if half(u) != half(v):
            return half(u)-half(v)
        determinant = u[0]*v[1]-u[1]*v[0]
        return -1 if determinant > 0 else (1 if determinant < 0 else 0)
    ordered = []
    for ray in rays:
        at = len(ordered)
        while at and compare(ordered[at-1], ray) > 0:
            at -= 1
        ordered.insert(at, ray)
    for a, b in zip(ordered, ordered[1:]+ordered[:1]):
        dx, dy = a[0]+b[0], a[1]+b[1]
        if dx == dy == 0:
            dx, dy = -a[1], a[0]
        step = F(1)
        for nx, ny, h in lines:
            slope = nx*dx+ny*dy
            if h and slope:
                step = min(step, abs(h/slope)/2)
        if overlap(translate(A, (step*dx, step*dy)), B) == -1:
            return True
    return False


def ray_exit(A,B,u):
    """First exit from topological int E, including isolated boundary events.

    Strict body overlap implies int E, but the converse fails at tight-fit
    seams. Non-overlap events/intervals therefore require a local exterior
    sector certificate; merely inspecting adjacent ray intervals is unsound.
    """
    A,B=points(A),points(B);ux,uy=(F(_mapped_value) for _mapped_value in u)
    uu=ux*ux+uy*uy
    if not uu:raise ValueError('brute_ray_exit: direction u must be non-zero')
    hits=set()
    for P,Q,dx,dy in ((A,B,ux,uy),(B,A,-ux,-uy)):
        for p in P:
            for a,b in zip(Q,Q[1:]+Q[:1]):
                ex,ey=b[0]-a[0],b[1]-a[1]
                wx,wy=a[0]-p[0],a[1]-p[1]
                den=dx*ey-dy*ex
                if den:
                    t=(wx*ey-wy*ex)/den
                    s=(wx*dy-wy*dx)/den
                    if t>0 and 0<=s<=1:hits.add(t)
                elif wx*dy-wy*dx==0:
                    # Collinear travel has endpoint events, not an exemption.
                    for q in (a,b):
                        t=((q[0]-p[0])*dx+(q[1]-p[1])*dy)/uu
                        if t>0:hits.add(t)
    end=(max(x*ux+y*uy for x,y in B)-min(x*ux+y*uy for x,y in A))/uu
    lo=F(0)
    for hi in sorted({t for t in hits if t<end})+[end]:
        mid=(lo+hi)/2
        Am = translate(A, (mid*ux, mid*uy))
        state = overlap(Am, B)
        if state == -1 or (state == 0 and boundary_has_exterior(Am, B)):
            return lo
        Ah = translate(A, (hi*ux, hi*uy))
        if overlap(Ah, B) == 0 and boundary_has_exterior(Ah, B):
            return hi
        lo=hi
    return end
