"""WO-E5a exact primitive gates.

Oracles use rectangular unions, determinant formulas and rational affine maps;
they do not call production normals, membership, convex hull, or SAT routines.
"""
from fractions import Fraction as F
import inspect
import math
import random

import pytest

import eab.kernel3d.geom3 as G
from eab.kernel3d import exact_geom as EG


def _map(p, scale, translation):
    x,y,z=map(F,p)
    # An exactly orthogonal rational rotation: no rounded-input coplanarity fiction.
    u,v=F(3,5)*x-F(4,5)*y,F(4,5)*x+F(3,5)*y
    return (translation+scale*u, -2*translation+scale*(F(5,13)*v-F(12,13)*z),
            3*translation+scale*(F(12,13)*v+F(5,13)*z))


def _placed(P,scale,translation):
    return G.Polyhedron([_map(p,scale,translation) for p in P.verts],list(P.faces))


def _l_block():
    xy=[(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)]
    v=[(x,y,z) for z in (0,1) for x,y in xy]
    f=[(5,4,3,2,1,0),(6,7,8,9,10,11)]
    f += [(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]
    return G.Polyhedron(v,f)


@pytest.mark.parametrize('scale',[F(1,1000),F(1),F(1000)])
@pytest.mark.parametrize('translation',[F(0),F(1000),F(1000000)])
def test_exact_surface_membership_has_no_boundary_noise_band(scale,translation):
    P=_placed(_l_block(),scale,translation)
    delta=F(1,2**80)
    probes=[((F(1,2),F(1,2),F(1,2)),1),((2,2,F(1,2)),-1),((1,2,F(1,2)),0),
            ((1-delta,2,F(1,2)),1),((1+delta,2,F(1,2)),-1),((0,0,0),0)]
    for p,want in probes:
        assert G.exact_point_in_polyhedron(_map(p,scale,translation),P) == want


@pytest.mark.parametrize('scale',[F(1,1000),F(1),F(1000)])
@pytest.mark.parametrize('translation',[F(0),F(1000),F(1000000)])
@pytest.mark.parametrize('delta,want',[(F(-1,2**70),1),(F(0),0),(F(1,2**70),-1)])
def test_exact_convex_overlap_distinguishes_arbitrarily_thin_intersection(scale,translation,delta,want):
    a=G.box(half=(F(1,2),)*3)
    b=G.box(center=(F(1)+delta,F(0),F(0)),half=(F(1,2),)*3)
    a,b=_placed(a,scale,translation),_placed(b,scale,translation)
    assert G.exact_convex_overlap(a,b) == want
    assert G.exact_convex_overlap(b,a) == want


def test_exact_segment_crossing_requires_the_point_to_be_inside_the_face():
    P=G.box()
    assert G.exact_segment_crosses_face((0,0,0),(0,0,2),P,1)
    assert not G.exact_segment_crosses_face((3,0,0),(3,0,2),P,1)
    assert not G.exact_segment_crosses_face((1,0,0),(1,0,2),P,1)
    assert not G.exact_segment_crosses_face((0,0,1),(0,0,2),P,1)
    assert not G.exact_segment_crosses_face((-2,0,1),(2,0,1),P,1)
    # The still-legacy public crossing path must retain this same extent guard.
    assert not G.segment_crosses_face((3,0,0),(3,0,2),P,1)


def test_triangle_intersections_cover_coplanar_transverse_and_vertex_cases():
    a=((0,0,0),(2,0,0),(0,2,0))
    assert G.exact_triangle_intersection(a,((0,0,1),(2,0,1),(0,2,1))) == ()
    assert set(G.exact_triangle_intersection(a,((1,-1,0),(3,1,0),(-1,1,0)))) == {
        (F(0),F(0),F(0)),(F(2),F(0),F(0)),(F(0),F(1),F(0)),(F(1),F(1),F(0))}
    assert set(G.exact_triangle_intersection(a,((0,0,0),(-1,0,1),(0,-1,1)))) == {(0,0,0)}
    hit=G.exact_triangle_intersection(a,((F(1,2),F(1,2),-1),(F(1,2),F(1,2),1),(F(3,2),F(1,2),0)))
    assert set(hit) == {(F(1,2),F(1,2),F(0)),(F(3,2),F(1,2),F(0))}


def test_invalid_degenerate_surface_is_rejected_instead_of_retrying_rays_forever():
    bad=G.Polyhedron([(0,0,0),(1,0,0),(2,0,0)],[(0,1,2)])
    with pytest.raises(ValueError,match='zero-area triangle'):
        G.exact_point_in_polyhedron((0,1,0),bad)
    with pytest.raises(ValueError,match='nondegenerate'):
        G.exact_triangle_intersection(tuple(bad.verts),((0,0,1),(1,0,1),(0,1,1)))


def test_exact_thin_hull_facet_is_not_reported_as_zero_area_by_float_cancellation():
    points=[(-0.002326712452119078,0.0009422040475784042,0.00115808492688615),
            (0.0002099579211924021,-9.558716455349318e-06,0.0032122151706055267),
            (-0.000834553408994678,0.0003823435981467845,0.0023663968349563716)]
    P=G.Polyhedron(points,[(0,1,2)])
    a,b,c=[tuple(F(x) for x in p) for p in points]
    u,v=[tuple(p[i]-a[i] for i in range(3)) for p in (b,c)]
    n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
    assert any(n)
    want=math.sqrt(float(sum(x*x for x in n)/4))
    assert P.face_area(0) == pytest.approx(want,rel=1e-15,abs=0)
    length=math.sqrt(float(sum(x*x for x in n)))
    assert P.face_normal(0) == pytest.approx(tuple(float(x)/length for x in n),rel=1e-15,abs=0)


def test_coplanar_merge_never_merges_a_genuine_subulp_scale_ridge():
    P=G.box()
    P.verts[6]=(1.,1.,math.nextafter(1.,2.))
    H=G.convex_hull_3d(P.verts)
    merged=G.merge_coplanar(H,tol=1e-3)
    assert len(merged.faces) == 7
    assert all(G.orient3d(*(merged.verts[i] for i in f[:3]),merged.verts[j]) == 0
               for f in merged.faces for j in f)


def test_coplanar_merge_does_not_treat_a_nonplanar_newell_vector_as_a_plane():
    vertices=[(0.,0.,0.),(1.,0.,0.),(1.,1.,.1),(.5,1.5,-.1),(0.,1.,.1),(.5,-1.,0.)]
    P=G.Polyhedron(vertices,[(0,1,2,3,4),(1,0,5)])
    assert G.merge_coplanar(P).faces == P.faces
    S=G.exact_surface(P)
    assert len(S.faces)==4
    assert all(len(f)==3 for f in S.faces)


def test_convex_view_exposes_canonical_numbering_and_source_mapping():
    P=G.box()
    assert G.exact_convex_view(P) is P
    P=G.box();P.verts[6]=(1.,1.,math.nextafter(1.,2.))
    V=G.exact_convex_view(P)
    assert V is not P and len(V.faces)==7
    assert [P.verts[i] for i in V.source_vertices] == V.verts
    assert len(V.source_faces)==len(V.faces)
    assert all(all(set(V.source_vertices[v] for v in f).issubset(P.faces[src]) for src in sources)
               for f,sources in zip(V.faces,V.source_faces))


def test_exact_hull_has_no_coplanar_or_interior_redundant_vertices():
    from test_hull_robustness import _assert_exact_hull
    points=list(G.box().verts)+[(0.,0.,1.),(0.,1.,1.),(0.,0.,0.)]
    hull=G.convex_hull_3d(points)
    assert len(hull.verts) == 8
    _assert_exact_hull(hull,points)


def _g6e_distance_case():
    from test_near_parallel_edges import _quat,_move
    theta,half,x0,gap=1.5e-6,.3,.95,4.5793919600798964e-9
    c,s=math.cos(theta),math.sin(theta)
    b=G.tetra((-1.,0.,0.),(1.,0.,0.),(0.,-.8,-1.5),(0.,.9,-1.4))
    a=G.tetra((x0-half*c,-half*s,gap),(x0+half*c,half*s,gap),
              (x0-.1,-.7,1.3+gap),(x0+.2,.8,1.2+gap))
    return _move(a,_quat(5)),_move(b,_quat(5))


def test_g6e_near_parallel_oracle_uses_consistent_exact_distance():
    from test_near_parallel_edges import exact_seg_seg
    from eab.margin import body_distance
    A,B=_g6e_distance_case()
    args=(A.verts[0],A.verts[1],B.verts[0],B.verts[1])
    want=exact_seg_seg(*args)
    assert abs(G._seg_seg_distance(*args)-want) <= 2*math.ulp(want)
    assert abs(G._seg_seg_distance(*args[2:],*args[:2])-want) <= 2*math.ulp(want)
    assert body_distance(A,B)[0] == pytest.approx(want,abs=1e-15)


@pytest.mark.parametrize('length,gap',[(1.,1e-200),(1e-200,1e-200),(1e200,1e200),(1.,1e200)])
def test_exact_squared_distance_conversion_preserves_representable_small_and_large_distances(length,gap):
    assert G._seg_seg_distance((0.,0.,0.),(length,0.,0.),(0.,gap,0.),(length,gap,0.)) == gap


def test_g6e_near_parallel_legacy_parameter_mutation_is_killed():
    from test_near_parallel_edges import exact_seg_seg
    src=inspect.getsource(G._seg_seg_distance)
    old='if a > 0.0 and c > 0.0 and nn <= 1e-8 * a * c:'
    assert old in src
    ns=dict(vars(G));exec(src.replace(old,'if False:'),ns)
    A,B=_g6e_distance_case()
    args=(A.verts[0],A.verts[1],B.verts[0],B.verts[1])
    want=exact_seg_seg(*args)
    assert abs(ns['_seg_seg_distance'](*args)-want) > 2*math.ulp(want)


def test_segment_face_extent_mutation_is_killed_through_the_real_path(monkeypatch):
    src=inspect.getsource(EG.segment_triangle)
    old='if triangle_locate(x,a,b,c) < 0:'
    assert old in src
    ns=dict(vars(EG));exec(src.replace(old,'if False:'),ns)
    monkeypatch.setattr(EG,'segment_triangle',ns['segment_triangle'])
    assert G.exact_segment_crosses_face((3,0,0),(3,0,2),G.box(),1)


def test_polygon_interval_filters_match_pure_fraction_including_subnormals():
    rng=random.Random(55017)
    compared=0
    for scale,offset in ((1.,0.),(1e-6,1e6),(1e100,0.),(1e-100,0.),(1e-160,0.),(2.**-1070,0.)):
        vertices=((offset,0.,0.),(offset+3*scale,0.,0.),(offset+3*scale,scale,0.),
                  (offset+scale,scale,0.),(offset+scale,3*scale,0.),(offset,3*scale,0.))
        for _ in range(150):
            p=(offset+rng.uniform(-.2,3.2)*scale,rng.uniform(-.2,3.2)*scale,0.)
            tol=rng.choice((0.,1e-12,.001))*scale
            assert EG.polygon_locate(p,vertices,tol)==EG.polygon_locate_fraction(p,vertices,tol)
            compared+=1
        for p in vertices:
            for tol in (0.,scale/100):
                assert EG.polygon_locate(p,vertices,tol)==EG.polygon_locate_fraction(p,vertices,tol)
                compared+=1
    assert compared == 972
