from fractions import Fraction as F
import math
import pytest
from eab.kernel2d import covers as c2, g0
from eab.kernel3d import covers3 as c3, g03
from eab.kernel3d.geom3 import Polyhedron

SQUARE = [(0., 0.), (1., 0.), (1., 1.), (0., 1.)]
FACES = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
VERTS = [(x,y,z) for z in (0.,1.) for x,y in SQUARE]

def shifted(dx, scale=1):
    return [(scale*x+dx,scale*y) for x,y in SQUARE]

@pytest.mark.parametrize('side', ['distance', 'exit'])
def test_g6f04_2d_strict_micro_sample_is_checked(side, monkeypatch):
    """Oracle: independent rational rectangle intervals; no tested primitives."""
    gap = 2.**-44
    A = shifted(1+gap if side == 'distance' else 1-gap)
    exact_gap = min(F(p[0]) for p in A)-1
    assert (exact_gap > 0) == (side == 'distance')
    monkeypatch.setattr(c2, '_ve_side', lambda *a, **k: -1)
    monkeypatch.setattr(c2, 'vv_cover', lambda *a, **k: None)
    rep = (g0.g0_distance_completeness(A,SQUARE,[(0.,0.)]) if side == 'distance'
           else g0.g0_exit_completeness(A,SQUARE,[(0.,0.)],[(1.,0.)]))
    assert rep.samples == 1, ('strict sample was skipped', rep)
    assert not rep.passed, ('internal cone defect escaped', rep)
    assert math.isinf(rep.failures[0][1 if side == 'distance' else 3])


def test_g6f04_3d_strict_micro_gap_is_checked(monkeypatch):
    """Oracle: independent rational interval gap, exact 2^-44."""
    B=Polyhedron(VERTS,FACES)
    A=Polyhedron([(x+1+2.**-44,y,z) for x,y,z in VERTS],FACES)
    assert min(F(v[0]) for v in A.verts)-1 == F(1,2**44)
    monkeypatch.setattr(c3,'_qvertex_contains',lambda *a,**k:-1)
    monkeypatch.setattr(c3,'_qedge_contains',lambda *a,**k:-1)
    rep=g03.g0_distance_completeness3(A,B,radius=0,samples=1)
    assert rep.samples == 1, ('strict sample was skipped',rep)
    assert not rep.passed, ('internal cone defect escaped',rep)
    assert math.isinf(rep.failures[0][1])


def test_g6f05_first_exit_preserves_micro_penetration():
    """Oracle: rational right-edge crossing, independent of production geometry."""
    A=shifted(1-2.**-39)
    expected=1-min(F(x) for x,y in A)
    got=g0.brute_ray_exit(A,SQUARE,(1.,0.))
    assert got == expected and got > 0, ('first strict exit',got,expected)


@pytest.mark.parametrize('exponent',[-600,0,600])
def test_g6f05_distance_does_not_underflow_or_overflow_its_square(exponent):
    """Oracle: independent closed rectangle distance s/2 (not squared floats)."""
    s=2.**exponent
    B=shifted(0.,s)
    A=[(x+1.5*s,y+.5*s) for x,y in B]
    got,_=g0.brute_polygon_distance(A,B)
    assert got == s/2, ('closed segment projection',got,s/2)
    if exponent <= 0:
        rep=g0.g0_distance_completeness(A,B,[(0.,0.)])
        assert rep.samples == 1 and rep.passed, ('correct kernel falsely rejected',rep)

@pytest.mark.parametrize('scale',[F(1,2**600),F(1),F(2**600)])
@pytest.mark.parametrize('translation',[F(0),F(10**8)])
def test_g0_surface_distance_matches_independent_product_intervals(scale,translation):
    from eab.kernel3d.g03_surface_oracle import separated_distance
    def cube(dx, size=1):
        return [tuple(translation+scale*(F(c)*size+(dx if i==0 else 0)) for i,c in enumerate(v)) for v in VERTS]
    a,b=cube(F(3,2)),cube(0)
    got=separated_distance(a,FACES,b,FACES)
    assert got == float(scale/2)
    assert separated_distance(cube(1),FACES,b,FACES) is None
    assert separated_distance(cube(F(1,2)),FACES,b,FACES) is None
    assert separated_distance(cube(F(1,4),F(1,2)),FACES,b,FACES) is None


@pytest.mark.parametrize('x',[F(-1,2),F(0),F(1,2),F(1),F(3,2),F(2),F(5,2)])
@pytest.mark.parametrize('y',[F(-1,2),F(0),F(1,2),F(1),F(3,2),F(2),F(5,2)])
def test_g0_polygon_membership_matches_independent_cell_union(x,y):
    """L shape is three unit cells: independent Cartesian product intersections."""
    from eab.kernel2d.g0_oracle import overlap
    L=[(0,0),(2,0),(2,1),(1,1),(1,2),(0,2)]
    A=[(F(a)/2+x,F(b)/2+y) for a,b in SQUARE]
    dims=[(min(x+F(1,2),cx+1)-max(x,cx), min(y+F(1,2),cy+1)-max(y,cy))
          for cx,cy in ((0,0),(1,0),(0,1))]
    want=1 if any(min(d)>0 for d in dims) else (0 if any(min(d)>=0 for d in dims) else -1)
    assert overlap(A,L)==want

@pytest.mark.parametrize('tol',[0.,2.**-54])
def test_r6scan_2d_legacy_predicates_do_not_hide_strict_micro_geometry(tol):
    from eab.kernel2d import geom
    eps=2.**-50
    dent=[(0.,0.),(2.,0.),(2.,1.),(1.,1.-eps),(0.,1.)]
    assert geom.reflex_vertices(dent,tol)==[3]
    assert not geom.is_convex(dent,tol)
    assert geom.point_in_polygon((1.+eps,.5),SQUARE,tol)==-1
    assert geom.point_in_polygon((1.-eps,.5),SQUARE,tol)==1
    assert geom.polygons_overlap(shifted(1.+eps),SQUARE,tol)==-1
    assert geom.polygons_overlap(shifted(1.-eps),SQUARE,tol)==1
    assert geom.segments_properly_cross((0.,0.),(1.,0.),(.5,-eps),(.5,eps),tol)

@pytest.mark.parametrize('exponent',[-600,600])
def test_r6scan_2d_centroid_and_orientation_survive_unrepresentable_area(exponent):
    from eab.kernel2d.geom import centroid, is_ccw
    s=2.**exponent
    P=[(0.,0.),(2*s,0.),(s,s),(0.,s)]
    assert is_ccw(P), 'exact positive area sign must not depend on float area display'
    want=(float(F(7,9)*F(s)),float(F(4,9)*F(s)))
    assert centroid(P)==want


def test_g0_surface_oracle_checks_every_disconnected_component():
    from eab.kernel3d.g03_surface_oracle import separated_distance
    outside=[(x+10,y,z) for x,y,z in VERTS]
    contained=[(F(x)/2+F(1,4),F(y)/2+F(1,4),F(z)/2+F(1,4)) for x,y,z in VERTS]
    faces=FACES+[tuple(i+8 for i in f) for f in FACES]
    # The first component is disjoint; only the second lies inside B.
    assert separated_distance(outside+contained,faces,VERTS,FACES) is None
    assert separated_distance(VERTS,FACES,outside+contained,faces) is None

@pytest.mark.parametrize('case',['tiny_notch','rational_far_triangle'])
def test_r6scan_interior_point_retains_exact_affine_geometry(case):
    from eab.kernel2d.geom import interior_point
    from test_kernel2d_review import _exact_parity
    if case=='tiny_notch':
        s=2.**-600
        P=[(s*x,s*y) for x,y in [(0.,0.),(8.,-4.),(9.,0.),(6.,.6),(2.,0.),(8.,4.)]]
    else:
        t=F(10**8);s=F(1,10**9)
        P=[(t,t),(t+s,t),(t,t+s)]
    got=interior_point(P)
    assert _exact_parity(got,P)==1, ('constructed witness must remain strictly inside',got)


def test_r6scan_outward_normal_preserves_mixed_scalar_short_edge():
    from eab.kernel2d.geom import outward_normal
    t=10**8;s=F(1,10**9)
    P=[(float(t),float(t)),(F(t),F(t)+s),(F(t)-s,F(t)+s),(F(t)-s,F(t))]
    assert outward_normal(P,0)==(1.,0.)
