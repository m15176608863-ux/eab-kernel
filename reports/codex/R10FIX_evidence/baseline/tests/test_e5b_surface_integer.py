"""Integer parity / certified star-union optimization equivalence gates.

Main independent oracle: exact L = union of two rectangular boxes and the
test-only tetrahedral SAT implementation e5a2_surface_oracle (no production
geometric primitives imported). Baseline Fraction parity is equivalence only.
"""
from fractions import Fraction as F
import inspect
import random

import pytest

from eab.kernel3d import geom3 as G, exact_geom as E
from e5a2_surface_oracle import star_overlap
from test_e5a2_surface import l_block, placed


def _fraction_parity(p,tris):
    # Previous algorithm, retained test-only to check the algebraic optimization.
    for _,tri in tris:
        if E.triangle_locate(p,*tri)>=0:
            return 0
    k=0
    while True:
        k+=1;d=(F(1),F(k),F(k*k));hits=0
        for _,tri in tris:
            a,b,c=tri;n=E.cross(E.sub(b,a),E.sub(c,a))
            offset=E.dot(n,E.sub(a,p));den=E.dot(n,d)
            if not den:
                if not offset:
                    break
                continue
            t=offset/den
            if t<=0:
                continue
            loc=E.triangle_locate(E.add(p,E.mul(d,t)),*tri)
            if loc==0:
                break
            hits+=loc==1
        else:
            return 1 if hits%2 else -1


@pytest.mark.parametrize('scale,translation',[(F(1),F(0)),(F(1,10**8),F(10**6)),(F(10**3),F(-10**5))])
def test_integer_parity_matches_fraction_and_independent_box_union(scale,translation):
    a=placed(l_block(),scale,translation);tris=E.triangles(a)
    rng=random.Random(52346)
    qs=[tuple(F(rng.randrange(-4,20),7) for _ in range(3)) for _ in range(96)]
    qs += [(F(x),F(y),F(z)) for x,y,z in ((0,0,0),(1,1,1),(2,2,0),(1,2,.5),(.5,.5,.5))]
    qs += [(F(1)+d,F(2),F(1,2)) for d in (F(-1,2**100),F(0),F(1,2**100))]
    states=set()
    for x,y,z in qs:
        closed=(0<=x<=3 and 0<=y<=1) or (0<=x<=1 and 0<=y<=3)
        inside=(0<x<3 and 0<y<1) or (0<x<1 and 0<y<3)
        want=1 if inside and 0<z<1 else (0 if closed and 0<=z<=1 else -1)
        p=placed(G.Polyhedron([(x,y,z)],[]),scale,translation).verts[0]
        assert E._point_in_triangles(p,tris)==_fraction_parity(p,tris)==want
        states.add(want)
    assert states=={-1,0,1}


@pytest.mark.parametrize('translation',[0.,1e3,1e6])
def test_certified_star_union_is_equal_to_general_path_and_independent_sat(translation,monkeypatch):
    real=E._star_union_overlap
    rng=random.Random(52347)
    states=set()
    for j in range(18):
        a=G.box(); b=G.box(center=(rng.choice([0,2,2+2**-30]),rng.uniform(-1,1),rng.uniform(-1,1)))
        def warp(p):
            return G.Polyhedron([(translation+x+.137*y,-2*translation+y+.271*z,3*translation+z+.119*x)
                                 for x,y,z in p.verts],list(p.faces))
        a,b=warp(a),warp(b)
        got=real(a,b)
        assert got is not None
        assert got==star_overlap(a,b)
        with monkeypatch.context() as m:
            m.setattr(E,'_star_union_overlap',lambda *args:None)
            assert G.polyhedra_overlap(a,b)==got
        states.add(got)
    assert -1 in states and 1 in states


def test_star_certificate_rejects_a_non_kernel_centroid_and_tracks_content():
    p=l_block()
    assert E._star_tetrahedra(tuple(p.verts),tuple(p.faces)) is None
    p=G.box()
    first=E._star_tetrahedra(tuple(p.verts),tuple(p.faces))
    p.verts[6]=(1.,1.,1.25)
    second=E._star_tetrahedra(tuple(p.verts),tuple(p.faces))
    assert first is not None and second is not None and first!=second


def test_integer_parity_internal_boundary_mutant_is_killed(monkeypatch):
    source=inspect.getsource(E._point_in_triangles)
    needle='offset == 0 and all(value >= 0 for value,_ in edge_values)'
    assert source.count(needle)==1
    ns=dict(E.__dict__)
    exec(source.replace(needle,'False'),ns)
    monkeypatch.setattr(E,'_point_in_triangles',ns['_point_in_triangles'])
    with pytest.raises(AssertionError,match='exact boundary classification'):
        assert G.point_in_polyhedron((0,0,1),G.box())==0, 'exact boundary classification'
