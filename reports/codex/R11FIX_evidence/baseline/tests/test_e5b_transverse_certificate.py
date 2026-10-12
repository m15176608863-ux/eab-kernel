"""Transverse fast path: independent rectangular-union / beam inequalities.

The oracle inverse-transform and open-box inequalities share no production
geometry primitives. Full arrangement comparison is equivalence evidence.
"""
from fractions import Fraction as F

import pytest

from eab.kernel3d import exact_geom as E, geom3 as G
from test_e5a2_surface import l_block, placed


@pytest.mark.parametrize('scale,translation',[(F(1),F(0)),(F(1,1000),F(10**6)),(F(1000),F(10**5))])
def test_transverse_fast_certificate_has_independent_strict_interior_witness(scale,translation,monkeypatch):
    a=l_block()
    b=G.box(center=(F(3,2),F(3,2),F(1,2)),half=(F(3,10),F(2),F(1,5)))
    a,b=placed(a,scale,translation),placed(b,scale,translation)
    at,bt=E.triangles(a),E.triangles(b); ap,bp=E._planes(at),E._planes(bt)
    w=E._transverse_interior_witness(at,bt,ap,bp)
    assert w is not None
    x,y,z=w; u=(x-translation)/scale; v=(y+2*translation)/scale
    x,y,z=(3*u+4*v)/5,(-4*u+3*v)/5,(z-3*translation)/scale
    assert 0<z<1 and ((0<x<3 and 0<y<1) or (0<x<1 and 0<y<3))
    assert F(6,5)<x<F(9,5) and F(-1,2)<y<F(7,2) and F(3,10)<z<F(7,10)
    assert E._surface_interior_witness(at,bt,ap,bp) is not None
    assert G.polyhedra_overlap(a,b)==1
    real=E._transverse_interior_witness
    calls=[]
    def witness(*args):
        result=real(*args)
        calls.append(result)
        return result
    monkeypatch.setattr(E,'_transverse_interior_witness',witness)
    assert G.polyhedra_overlap(a,b)==1
    assert calls and calls[-1] is not None, 'production fast-path wiring'


def test_failed_transverse_certificate_keeps_coplanar_arrangement(monkeypatch):
    a=l_block()
    monkeypatch.setattr(E,'_transverse_interior_witness',lambda *args:None)
    assert G.polyhedra_overlap(a,a)==1
    for x,want in ((F(1),0),(F(1)-F(1,2**80),1),(F(1)+F(1,2**80),-1)):
        b=G.box(center=((x+3)/2,(x+3)/2,F(1,2)),half=((3-x)/2,(3-x)/2,F(1,2)))
        assert G.polyhedra_overlap(a,b)==want
