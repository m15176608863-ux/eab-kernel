"""A1 gates use independent rational rectangular unions / integer tetra SAT.

The oracles consume only raw coordinates. No production geometric primitive
is reused; Fraction arithmetic is the sole common computational substrate.
"""
from fractions import Fraction as F
import inspect
import random
import pytest
from eab.kernel3d import geom3 as G, exact_geom as E
from e5a2_surface_oracle import star_overlap


def l_block():
    xy=[(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)]
    v=[(F(x),F(y),F(z)) for z in (0,1) for x,y in xy]
    f=[(5,4,3,2,1,0),(6,7,8,9,10,11)]
    f += [(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]
    return G.Polyhedron(v,f)


def placed(P,s,t):
    def transform(p):
        x,y,z=(F(_r12_item) for _r12_item in p)
        return (t+s*(3*x-4*y)/5,-2*t+s*(4*x+3*y)/5,3*t+s*z)
    return G.Polyhedron([transform(p) for p in P.verts],list(P.faces))


def independent_l_box_relation(lo,hi):
    # L is the exact union [0,3]x[0,1]x[0,1] and [0,1]x[0,3]x[0,1].
    states=[]
    for top in ((3,1,1),(1,3,1)):
        widths=[min(F(top[i]),hi[i])-max(F(0),lo[i]) for i in range(3)]
        states.append(-1 if min(widths)<0 else (0 if min(widths)==0 else 1))
    return max(states)


@pytest.mark.parametrize('scale',[F(1,1000),F(1),F(1000)])
@pytest.mark.parametrize('translation',[F(0),F(1000),F(1000000)])
def test_general_surface_exact_overlap_coplanar_and_common_edge_certificates(scale,translation):
    delta=F(1,2**70)
    L=l_block()
    cases=[((1,1,0),(3,3,1)),((1-delta,1-delta,0),(3,3,1)),
           ((1+delta,1+delta,0),(3,3,1)),((F(1,2),F(1,2),0),(2,2,1)),
           ((-1,0,0),(0,1,1)),((0,0,1),(1,1,2))]
    for low,high in cases:
        lo,hi=tuple(map(F,low)),tuple(map(F,high))
        B=G.box(tuple((a+b)/2 for a,b in zip(lo,hi)),tuple((b-a)/2 for a,b in zip(lo,hi)))
        a,b=placed(L,scale,translation),placed(B,scale,translation)
        want=independent_l_box_relation(lo,hi)
        assert G.polyhedra_overlap(a,b)==want
        assert G.polyhedra_overlap(b,a)==want
    # All vertices lie on the other boundary: only the coplanar cell branch can certify this concave solid.
    a=placed(L,scale,translation)
    assert G.polyhedra_overlap(a,a)==1


def test_coplanar_internal_mutation_is_killed_by_the_overlap_assertion(monkeypatch):
    source=inspect.getsource(E._surface_interior_witness)
    assert 'elif loc == 0:' in source
    namespace=dict(E.__dict__)
    exec(source.replace('elif loc == 0:','elif False and loc == 0:'),namespace)
    monkeypatch.setattr(E,'_surface_interior_witness',namespace['_surface_interior_witness'])
    A=l_block()
    with pytest.raises(AssertionError,match='coplanar interior certificate'):
        assert G.polyhedra_overlap(A,A)==1, 'coplanar interior certificate removed'


@pytest.mark.parametrize('translation',[0.,1e3,1e6])
def test_general_surface_fast_path_matches_independent_tetrahedral_oracle(translation):
    rng=random.Random(513)
    for case in range(24):
        A=G.box(); B=G.box(center=(rng.choice([0,2,2+2**-40]),rng.uniform(-1,1),rng.uniform(-1,1)))
        # Affine shear and independently rounded engineering coordinates retain
        # star shape but deliberately make quadrilateral rings nonplanar.
        def warp(P):
            return G.Polyhedron([(translation+x+.137*y,-2*translation+y+.271*z,3*translation+z+.119*x)
                                 for x,y,z in P.verts],list(P.faces))
        A,B=warp(A),warp(B)
        assert G.polyhedra_overlap(A,B)==star_overlap(A,B),case


@pytest.mark.parametrize('scale',[F(1,1000),F(1),F(1000)])
@pytest.mark.parametrize('translation',[F(0),F(1000),F(1000000)])
def test_legacy_surface_membership_and_crossing_are_exact(scale,translation):
    L=placed(l_block(),scale,translation)
    def p(v):
        return placed(G.Polyhedron([v],[]),scale,translation).verts[0]
    d=F(1,2**80)
    for q,want in [((1-d,2,F(1,2)),1),((1+d,2,F(1,2)),-1),((1,2,F(1,2)),0),((2,2,0),-1)]:
        assert G.point_in_polyhedron(p(q),L)==want
    assert G.segment_crosses_face(p((F(1,2),2,-1)),p((F(1,2),2,2)),L,0)
    assert not G.segment_crosses_face(p((2,2,-1)),p((2,2,2)),L,0)
    assert not G.segment_crosses_face(p((0,0,0)),p((3,0,0)),L,0)


def test_positive_tolerance_is_only_an_explicit_euclidean_reporting_band():
    A=G.box()
    assert G.point_in_polyhedron((F(11,10),F(11,10),0),A,F(1,10))==-1
    assert G.point_in_polyhedron((F(11,10),F(11,10),0),A,F(3,20))==0
    d=F(1,2**80)
    assert G.polyhedra_overlap(A,G.box((2-d,0,0),(F(1),)*3),F(1,10))==1
    assert G.polyhedra_overlap(A,G.box((F(21,10),F(21,10),0),(F(1),)*3),F(1,10))==-1
    assert G.polyhedra_overlap(A,G.box((F(21,10),F(21,10),0),(F(1),)*3),F(3,20))==0


@pytest.mark.parametrize('translation',[F(0),F(1000),F(1000000)])
def test_convex_surface_sat_matches_general_fraction_path(monkeypatch,translation):
    """New exact SAT shortcut agrees with full rational surface certificates.

    Random offsets, exact face/edge/corner degeneracies and engineering-scale
    translations are checked individually; neither path changes the input.
    """
    rng=random.Random(823)
    cases=[(F(2),F(0),F(0)),(F(2),F(2),F(0)),(F(2),F(2),F(2)),
           (F(2)-F(1,2**70),F(0),F(0)),(F(2)+F(1,2**70),F(0),F(0))]
    cases += [tuple(F(rng.randrange(-20,21),8) for _ in range(3)) for _ in range(7)]
    fast=E._convex_surface_sat
    for c in cases:
        A=placed(G.box((F(0),)*3,(F(1),)*3),F(1),translation)
        B=placed(G.box(c,(F(1),)*3),F(1),translation)
        want=G.polyhedra_overlap(A,B)
        monkeypatch.setattr(E,'_convex_surface_sat',lambda *args:None)
        assert G.polyhedra_overlap(A,B)==want==star_overlap(A,B)
        monkeypatch.setattr(E,'_convex_surface_sat',fast)


def test_coplanar_witness_is_independently_inside_the_concave_solid():
    """The witness itself, not merely the returned state, passes a union oracle."""
    A=l_block(); tris=E.triangles(A); planes=E._planes(tris)
    x,y,z=E._surface_interior_witness(tris,tris,planes,planes)
    assert all(isinstance(v,F) for v in (x,y,z))
    assert 0 < z < 1 and ((0 < x < 3 and 0 < y < 1) or (0 < x < 1 and 0 < y < 3))


def roof():
    P=G.box()
    P.verts[4]=(-1.,-1.,0.)
    P.verts[6]=(1.,1.,0.)
    return P


def test_internal_fold_touch_is_not_a_transverse_source_face_crossing():
    """Analytic roof z=1-|x+y|/2: the horizontal ridge touch stays outside.

    This closed nonplanar-ring body uses no production primitive for its truth.
    The vertical probe has one endpoint above and one below the ridge.
    """
    P=roof()
    assert not G.segment_crosses_face((-.5,-.5,1.),(.5,.5,1.),P,1)
    assert not G.exact_segment_crosses_face((-.5,-.5,1.),(.5,.5,1.),P,1)
    assert G.segment_crosses_face((0.,0.,2.),(0.,0.,0.),P,1)
    assert G.exact_segment_crosses_face((0.,0.,2.),(0.,0.,0.),P,1)


def test_internal_fold_side_test_mutation_hits_the_tangent_assertion(monkeypatch):
    source=inspect.getsource(E.segment_crosses)
    needle='triangle_locate(x,*tri) == 0 and not _transverse_fold_crossing(p,q,hit[1],tris)'
    assert needle in source
    namespace=dict(E.__dict__)
    exec(source.replace(needle,'False'),namespace)
    monkeypatch.setattr(E,'segment_crosses',namespace['segment_crosses'])
    with pytest.raises(AssertionError,match='tangent roof is not crossing'):
        assert not G.segment_crosses_face((-.5,-.5,1.),(.5,.5,1.),roof(),1), 'tangent roof is not crossing'


def test_reused_exact_planes_and_bounds_match_fresh_fraction_membership():
    """Ephemeral precomputation matches fresh queries and an independent L union."""
    P=l_block(); tris=E.triangles(P);planes=E._planes(tris);bounds=E._triangle_bounds(tris)
    for x in (F(-1,7),F(0),F(1,2),F(1),F(2),F(3)):
        for y in (F(0),F(1,2),F(1),F(2),F(3)):
            for z in (F(0),F(1,2),F(1),F(8,7)):
                inside=(0<x<3 and 0<y<1) or (0<x<1 and 0<y<3)
                closed=(0<=x<=3 and 0<=y<=1) or (0<=x<=1 and 0<=y<=3)
                want=1 if inside and 0<z<1 else (0 if closed and 0<=z<=1 else -1)
                p=(x,y,z)
                assert E._point_in_triangles(p,tris,planes,bounds)==E._point_in_triangles(p,tris)==want
