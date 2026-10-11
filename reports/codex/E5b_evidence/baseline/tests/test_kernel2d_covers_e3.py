"""E3 局部盖精确门；oracle 是内联 Fraction 邻点支持投影，不调用内核几何原语。"""
from fractions import Fraction as F
import math
import pytest
from eab.kernel2d.covers import ve_cover, ev_cover, vv_cover, enumerate_covers, first_entrance_for_vertex
from eab.kernel2d.geom import convex_hull

SQ = [(0., 0.), (1., 0.), (1., 1.), (0., 1.)]
TRI = [(0., 0.), (-1., 1.), (-1., -1.)]

def strict_vv_oracle(A, i, B, j):
    """分离向量在 A 最小、B 最大的两邻点支持投影；不调 covers/exact/geom。"""
    a, b = A[i], B[j]
    dx, dy = F(a[0])-F(b[0]), F(a[1])-F(b[1])
    if dx == dy == 0:
        return True
    return all(dx*(F(A[k][0])-F(a[0])) + dy*(F(A[k][1])-F(a[1])) > 0
               for k in ((i-1)%len(A), (i+1)%len(A))) and all(
        dx*(F(B[k][0])-F(b[0])) + dy*(F(B[k][1])-F(b[1])) < 0
               for k in ((j-1)%len(B), (j+1)%len(B)))

@pytest.mark.parametrize("C", [0., 1e3, 1e5])
@pytest.mark.parametrize("theta", [-5., 0., 5., 45., 50.])
def test_vv_active_exact_support_not_a_roundoff_band(C, theta):
    g=1e-6; a=math.radians(theta)
    A=[(C+u+g*math.cos(a),C+v+g*math.sin(a)) for u,v in SQ]
    B=[(C+u,C+v) for u,v in TRI]
    c=vv_cover(A,0,B,0)
    assert c is not None
    assert c.strict is strict_vv_oracle(A,0,B,0), "VV activity must match exact neighbor support"
    assert (('VV',0,0) in {x.label() for x in enumerate_covers(A,B,window=1e-3)}) is c.strict

@pytest.mark.parametrize("C", [0., 1e3, 1e5])
def test_local_no_window_rejects_a_real_reflex_vertex(C):
    h=math.ulp(max(C,1.))
    A=[(C,C),(C+1,C),(C+1,C+1),(C,C+1),(C+h,C+.5)]
    B=[(C-1,C),(C,C),(C,C+1),(C-1,C+1)]
    assert ve_cover(A,4,B,1) is None, "no-window local cone must reject exact reflex vertex"
    assert ev_cover(B,1,A,4) is None

def test_zero_distance_window_is_not_lifted_to_coordinate_noise():
    C=1e5; g=math.ulp(C)
    A=[(C+u,C+v+1+g) for u,v in SQ]
    B=[(C+u,C+v) for u,v in SQ]
    assert enumerate_covers(A,B,window=0.) == [], "explicit zero window cannot admit a positive gap"
    assert first_entrance_for_vertex(A,0,B,window=0.) is None

def test_segment_window_is_not_lifted_to_coordinate_noise():
    C=1e5; dx=math.ulp(C)
    A=[(C-dx,C+1.2),(C+.2,C+1.5),(C-.2,C+1.5)]
    B=[(C+u,C+v) for u,v in SQ]
    exact={c.label() for c in enumerate_covers(A,B,window=1.)}
    assert ('VE',0,2) not in exact, "exact projection outside segment cannot enter via roundoff floor"
    wide={c.label() for c in enumerate_covers(A,B,window=1.,seg_tol=2*dx)}
    assert ('VE',0,2) in wide
    assert exact <= wide

def test_convex_hull_keeps_true_extreme_point_not_transitive_tolerance_pop():
    pts=[(0.,0.),(1e-15,-1e-3),(1e-15,1.),(1e-3,-1e-3),(2.,-1e-3),(2.,1.)]
    H=convex_hull(pts)
    assert (1e-15,-1e-3) in H, "true extreme point lost by tolerance-pop chain"
    for a,b in zip(H,H[1:]+H[:1]):
        for p in pts:
            assert (F(b[0])-F(a[0]))*(F(p[1])-F(a[1]))-(F(b[1])-F(a[1]))*(F(p[0])-F(a[0])) >= 0


def test_vv_explicit_window_only_expands_activity_not_exact_strictness():
    theta=math.radians(-5); g=1e-6
    A=[(u+g*math.cos(theta),v+g*math.sin(theta)) for u,v in SQ]
    small=vv_cover(A,0,TRI,0,cone_tol=math.sin(math.radians(3)))
    wide=vv_cover(A,0,TRI,0,cone_tol=math.sin(math.radians(6)))
    assert small is not None and wide is not None
    assert not small.strict and not wide.strict
    assert not small.window_active and wide.window_active
    baseline={c.label() for c in enumerate_covers(A,TRI,window=1e-3)}
    expanded={c.label() for c in enumerate_covers(A,TRI,window=1e-3,cone_tol=math.sin(math.radians(6)))}
    assert baseline <= expanded
    assert ('VV',0,0) not in baseline and ('VV',0,0) in expanded


def independent_cover_oracle(A, B, window, tol=0., cone_tol=None, seg_tol=None):
    """独立 Fraction 邻点投影 oracle：不用内核几何/法锥/窗口原语。
    VV 锥交以四条线性不等式的 Fourier-Motzkin 消元判可行，不用被测的边界射线相加。
    返回标签/精确 strict；域窗口比较通过平方消根。仅用于非零边、CCW 的测试输入。
    """
    A,B=[[(F(x),F(y)) for x,y in P] for P in (A,B)]
    def displacement(p,q): return (p[0]-q[0],p[1]-q[1])
    def product(p,q): return p[0]*q[0]+p[1]*q[1]
    def turn(P,i):
        a,b,c=P[i-1],P[i],P[(i+1)%len(P)]
        return (b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0])
    def ring(P,i): return [displacement(P[k%len(P)],P[i]) for k in (i-1,i+1)]
    def angle2(vecs):
        return F(max(cone_tol,0.))**2 if cone_tol is not None else F(max(tol,0.))**2/min(product(v,v) for v in vecs)
    def ge(value,v2,w2): return value>=0 or value**2<=w2*v2
    def sum_units_positive(a,b,la,lb):
        if min(a,b)>=0: return max(a,b)>0
        if max(a,b)<=0: return False
        cmp=a*a*lb-b*b*la
        return cmp>0 if a>0 else cmp<0
    def strict_feasible(rows):
        for x in (-1,1):
            lowers=[];uppers=[];valid=True
            for a,b in rows:
                if b>0: lowers.append(-a*x/b)
                elif b<0: uppers.append(-a*x/b)
                elif a*x<=0: valid=False;break
            if valid and (not lowers or not uppers or max(lowers)<min(uppers)): return True
        return all(b>0 for a,b in rows) or all(b<0 for a,b in rows)
    out=set()
    def scan(P,Q,kind):
        for i,p in enumerate(P):
            rs=ring(P,i); lengths=[product(v,v) for v in rs]
            t=turn(P,i)
            for j,q in enumerate(Q):
                e=displacement(Q[(j+1)%len(Q)],q);l2=product(e,e);n=(e[1],-e[0]);w2=angle2(rs+[e])
                vals=[product(n,v) for v in rs]
                convex=t>=0 and (t>0 or product(rs[0],rs[1])<0)
                strict=convex and min(vals)>0
                exact=convex and min(vals)>=0 and (t>0 or vals!=[0,0] or product(n,(-rs[0][1],rs[0][0]))<0)
                # Straight vertices: n opposite to its own outward normal.
                if t==0 and convex:
                    incoming=(-rs[0][0],-rs[0][1]); normal=(incoming[1],-incoming[0])
                    exact=min(vals)>=0 and product(n,normal)<0
                allowed=exact
                if not allowed and w2>0:
                    refl_ok=t>=0 or (product(rs[0],rs[1])<0 and t*t<=w2*lengths[0]*lengths[1])
                    nl=(-rs[0][1],rs[0][0]);nh=(rs[1][1],-rs[1][0]);v=(-n[0],-n[1])
                    allowed=refl_ok and all(ge(z,l2*ll,w2) for z,ll in zip(vals,lengths)) and sum_units_positive(product(nl,v),product(nh,v),lengths[0],lengths[1])
                d=displacement(p,q);along=product(e,d);excess=max(-along,along-l2,0)
                st=F(max(tol if seg_tol is None else seg_tol,0.))
                gap=product(n,d)
                if allowed and excess*excess<=st*st*l2 and (math.isinf(window) or gap*gap<=F(window)**2*l2):
                    out.add((kind,i,j,strict) if kind=='VE' else (kind,j,i,strict))
    scan(A,B,'VE');scan(B,A,'EV')
    for i,a in enumerate(A):
        if turn(A,i)<=0: continue
        for j,b in enumerate(B):
            if turn(B,j)<=0: continue
            ar=ring(A,i);br=[(-u,-v) for u,v in ring(B,j)];rows=ar+br
            if not strict_feasible(rows): continue
            d=displacement(a,b);d2=product(d,d)
            if not math.isinf(window) and d2>F(window)**2: continue
            vals=[product(d,r) for r in rows]
            strict=d2==0 or min(vals)>0
            w2=angle2(rows)
            expanded=w2>0 and all(ge(z,d2*product(r,r),w2) for z,r in zip(vals,rows))
            # Small explicit windows in the test suite cannot wrap beyond a cone hemisphere.
            if strict or expanded: out.add(('VV',i,j,strict))
    return out


@pytest.mark.parametrize('scale',[1e-200,1.,1e200])
@pytest.mark.parametrize('reverse',[False,True])
def test_exact_overlap_triangulation_orientation_cannot_underflow(scale,reverse):
    """闭式 oracle：有非空内部的同一 L 形与自身内部相交；不用被测几何原语。"""
    from eab.kernel2d.exact import polygons_overlap_exact
    P=[(scale*x,scale*y) for x,y in [(0.,0.),(3.,0.),(3.,1.),(1.,1.),(1.,3.),(0.,3.)]]
    if reverse:P.reverse()
    assert polygons_overlap_exact(P,P)==1, 'exact triangulation orientation must not use float area'

@pytest.mark.parametrize('scale',[F(1,10**200),F(10**200)])
def test_fraction_orientation_does_not_route_through_float_filter(scale):
    from eab.kernel2d.geom import orient2d
    assert orient2d((F(0),F(0)),(scale,F(0)),(F(0),scale))==1
