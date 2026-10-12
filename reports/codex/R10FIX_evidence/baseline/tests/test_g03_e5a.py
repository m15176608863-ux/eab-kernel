"""E5a zero-exemption gates. Oracle uses only its own rational determinants/SAT.

g03_exact does not import tested geom3/covers3 primitives; the boxes additionally
have closed-form 8 vertices, 12 edges and 6 facets. Mutations enter the predicate
or local enumeration before G0 compares, never append false G0 output.
"""
from fractions import Fraction as F
import inspect

import pytest

from eab.kernel3d import covers3, g03, g03_exact
from eab.kernel3d.geom3 import Polyhedron, box, exact_convex_view, convex_hull_3d, tetra
from test_g03_two_rulers import _yaw, _move, _quat, _ridge_pair
from test_covers3_g0_vote2 import _random_pair


def test_g0_vote_one_checks_all_exact_vertices_edge_midpoints_and_face_centers():
    a,b=box(),box(center=(3,2,1))
    r=g03.g0_convex3(a,b,samples=3)
    assert r.boundary_kinds==(8,12,6)
    assert r.boundary_probes==r.boundary_checked==26
    assert r.samples==29 and r.band_skipped==0 and r.passed
    probes,_=g03_exact.boundary_probes(tuple(a.verts),tuple(b.verts))
    assert all(g03_exact.overlap(tuple(a.verts),tuple(b.verts),p)==0 for p in probes)
    assert all(covers3.membership_convex3(a,b,p)==0 for p in probes)


def test_g0_vote_one_boundary_misclassification_is_not_skipped(monkeypatch):
    real=g03.membership_convex3
    def lose_boundary(*args,**kw):
        answer=real(*args,**kw)
        return 1 if answer==0 else answer
    monkeypatch.setattr(g03,'membership_convex3',lose_boundary)
    r=g03.g0_convex3(box(),box(),samples=0)
    assert not r.passed
    assert len(r.mismatches)==r.boundary_probes==26
    assert all((brute,got)==(0,1) for _,brute,got in r.mismatches)
    assert r.band_skipped==0


def test_g0_vote_three_rejects_false_local_vertices_instead_of_low_e_exemption(monkeypatch):
    a,b=_random_pair(0)
    assert g03.g0_convex3(a,b,samples=0).passed
    monkeypatch.setattr(covers3,'cones_intersect_relint',lambda *args:True)
    r=g03.g0_convex3(a,b,samples=0)
    assert r.hull_vertex_mismatch>0 and not r.passed
    assert r.e_vertices_ambiguous==0


def test_default_facet_vote_has_no_undefined_resolution_scale():
    a,b=_random_pair(0)
    a,b=exact_convex_view(a),exact_convex_view(b)
    p,f,_=g03_exact.difference_hull(tuple(a.verts),tuple(b.verts))
    h=Polyhedron(list(p),list(f))
    result=g03.facet_vote3(a,b,covers3.local_facets3(a,b),h,list(p))
    assert result[-1]==[] and result[2:4]==(0,0)


@pytest.mark.parametrize('ratio,yaw,rot',[(1000,1e-6,7),(100,1e-7,7),(10,1e-8,3),(100,1e-7,11)])
def test_fifth_round_ratio_yaw_inputs_have_zero_exemptions(ratio,yaw,rot):
    h=ratio/2
    a=_yaw(box(center=(0,0,h+.6),half=(.5,.5,.5)),yaw)
    b=box(half=(h,h,h))
    r=g03.g0_convex3(_move(a,_quat(rot)),_move(b,_quat(rot)),samples=0)
    assert r.passed, r
    assert r.facet_ambiguous==r.facet_local_dropped==r.e_vertices_ambiguous==r.band_skipped==0
    assert r.samples==r.boundary_probes==r.boundary_checked>0


@pytest.mark.parametrize('height',[1e-6,1e-12,1e-14])
def test_true_ridges_are_checked_not_hidden_below_a_resolution_threshold(height):
    a,b=_ridge_pair(height)
    r=g03.g0_convex3(a,b,samples=0)
    assert r.passed and r.hull_vertices==r.e_vertices
    assert r.e_vertices_ambiguous==r.facet_ambiguous==r.facet_local_dropped==0


def test_g0_oracle_has_no_tested_geometric_primitive_import():
    source=inspect.getsource(g03_exact)
    assert 'from .geom3 import' not in source and 'from .covers3 import' not in source
    assert 'float(' not in source


def test_exact_rational_translation_is_not_rounded_before_the_membership_vote():
    a=box(center=(1e6,0,0),half=(.5,.5,.5))
    b=box(center=(1e6+2,0,0),half=(.5,.5,.5))
    for dx,want in [(F(1)-F(1,10**30),-1),(F(1),0),(F(1)+F(1,10**30),1)]:
        p=(dx,F(0),F(0))
        assert covers3.membership_convex3(a,b,p)==want
        assert g03_exact.overlap(tuple(a.verts),tuple(b.verts),p)==want


def test_g0_oracle_keeps_original_points_before_a_defective_convex_view(monkeypatch):
    a,b=box(),box()
    real=g03.exact_convex_view
    def drop_extreme(p):
        if p is a:
            # Defect enters canonicalization, before local facets/membership.
            return real(Polyhedron(list(p.verts[:-1]),[]))
        return real(p)
    monkeypatch.setattr(g03,'exact_convex_view',drop_extreme)
    r=g03.g0_convex3(a,b,samples=0)
    assert not r.passed
    assert r.hull_vertex_mismatch>0 or r.mismatches or r.facet_symmetric_diff


def test_fifth_round_original_roof_input_is_not_flattened_by_support_bands():
    import math
    def roof(h, yaw=0.):
        section=[(-1.,-1.),(1.,-1.),(1.,0.),(0.,h),(-1.,0.)]
        v=[(-2.,y,z) for y,z in section]+[(2.,y,z) for y,z in section]
        f=[(4,3,2,1,0),(5,6,7,8,9)]+[(i,(i+1)%5,5+(i+1)%5,5+i) for i in range(5)]
        c,s=math.cos(yaw),math.sin(yaw)
        return Polyhedron([(c*x-s*y,s*x+c*y,z) for x,y,z in v],f)
    a,b=roof(.1,10**-8.75),roof(.1)
    a=Polyhedron([(x,y,-z+.61) for x,y,z in a.verts],[tuple(reversed(f)) for f in a.faces])
    r=g03.g0_convex3(a,b,samples=40,seed=1)
    assert r.passed and r.facet_symmetric_diff==[]
    assert r.e_vertices_ambiguous==r.facet_ambiguous==r.facet_local_dropped==0
    assert r.boundary_checked==r.boundary_probes>0


@pytest.mark.parametrize('tmag',[0.,100.,1e3,1e4,1e6])
def test_fifth_round_original_chamfer_has_no_fitted_nonplanar_support(tmag):
    e=1e-6
    points=[(x,y,z) for x in (-1.,1.) for y in (-1.,1.) for z in (-1.,1.)]
    points.remove((1.,1.,1.))
    points += [(1.-e,1.,1.),(1.,1.-e,1.),(1.,1.,1.-e)]
    b=convex_hull_3d(points)
    ap=(1.08,1.05,1.033)
    a=tetra(ap,(ap[0]+1.,ap[1]+.3,ap[2]+.2),(ap[0]+.2,ap[1]+1.,ap[2]+.4),
            (ap[0]+.3,ap[1]+.1,ap[2]+1.))
    def move(p):
        return Polyhedron([(x+.6*tmag,y-.48*tmag,z+.64*tmag) for x,y,z in p.verts],list(p.faces))
    r=g03.g0_convex3(move(a),move(b),samples=40,seed=1)
    assert r.passed and r.facet_symmetric_diff==[]
    assert r.e_vertices_ambiguous==r.facet_ambiguous==r.facet_local_dropped==0
    assert r.boundary_checked==r.boundary_probes>0
