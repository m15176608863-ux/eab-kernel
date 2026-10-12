"""Independent margin-oracle gate: analytic slab and manual ridge midpoint.

No production geometric primitive computes the expected answer. The raw boxes
and folded roof are assigned explicitly; the oracle's test-only triangulation
must not replace the closed-form lower/upper bound used here.
"""
from fractions import Fraction as F
from types import SimpleNamespace
import pytest
import e5a_cover_oracle as O

FACES=((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))


@pytest.mark.parametrize('scale,translation',[(F(1),F(0)),(F(1,2**20),F(10**6)),(F(2**20),F(-10**6))])
def test_margin_oracle_uses_actual_folded_surface_not_newell_descriptor(scale,translation):
    av=((0,0,3),(1,0,3),(1,1,3),(0,1,3),(0,0,4),(1,0,4),(1,1,4),(0,1,4))
    bv=((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,0),(1,-1,1),(1,1,0),(-1,1,1))
    pose=lambda v:tuple(translation+scale*F(c) for c in v)
    a=SimpleNamespace(verts=tuple(map(pose,av)),faces=FACES)
    b=SimpleNamespace(verts=tuple(map(pose,bv)),faces=FACES)
    label=('VF',('vertex',0),('face',1))
    # B has z<=1 and ridge midpoint (v5+v7)/2=(0,0,1); A.v0=(0,0,3).
    assert tuple((F(bv[5][k])+bv[7][k])/2 for k in range(3))==(0,0,1)
    expected=O.margin_selection(a,b,F(5,2)*scale)
    assert label in expected, 'folded-margin-oracle-inclusion'
    assert expected[label]==float(2*scale), 'folded-margin-oracle-distance'


def test_restoring_newell_margin_distance_is_rejected(monkeypatch):
    monkeypatch.setattr(O, '_margin_witness_distance', O.witness_distance)
    with pytest.raises(AssertionError, match='folded-margin-oracle-inclusion'):
        test_margin_oracle_uses_actual_folded_surface_not_newell_descriptor(F(1),F(0))
