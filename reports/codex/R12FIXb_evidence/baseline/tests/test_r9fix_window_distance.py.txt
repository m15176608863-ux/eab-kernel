"""Window policy cannot justify rounding witness points before the distance.

The input poses reuse the fixed invariance grid; expected squared distances
come only from the independent test-owned Gram and triangle oracle. The final
float is certified against Fraction midpoints, not a production constructor.
"""
import inspect
import textwrap

import pytest

import eab.margin as M
from construction_oracle import assert_sqrt_rounding
import e5a_cover_oracle as oracle
import test_invariance_interlock as grid


@pytest.mark.parametrize('translation,scale', [(1000.,.001),(100000.,.001),(100000.,1.)])
def test_window_contact_distance_rounds_exact_scalar_not_global_witness_points(translation,scale):
    _,A0,B0,d0,_,_=grid._margin_ref('sep_ve3')
    A,B=grid._rigid(A0,grid.ROT_3['q4'],translation,scale),grid._rigid(B0,grid.ROT_3['q4'],translation,scale)
    window=M.contact_resolution(A,B)
    contacts=M.margin_contacts(A,B,delta=1.5*scale*d0,contact_window=window)
    assert contacts
    for contact in contacts:
        squared=oracle.margin_witness_squared(A,B,contact.label)
        assert_sqrt_rounding(contact.distance,squared,'window-distance-exact-midpoint')
    distance,label=M.body_distance(A,B,contact_window=window)
    assert_sqrt_rounding(distance,oracle.margin_witness_squared(A,B,label),'window-body-distance-exact-midpoint')


def test_window_distance_gate_rejects_restored_display_construction(monkeypatch):
    source=textwrap.dedent(inspect.getsource(M.margin_contacts))
    needle='else:\n            w = _exact.sqrt_rational(d2, allow_underflow=True)'
    assert source.count(needle)==1
    namespace=dict(vars(M))
    exec(compile(source.replace(needle,'elif contact_window is None or not ctol:\n            w = _exact.sqrt_rational(d2, allow_underflow=True)'),
                 '<r9-window-distance-mutant>','exec'),namespace)
    monkeypatch.setattr(M,'margin_contacts',namespace['margin_contacts'])
    with pytest.raises(AssertionError,match='window-distance-exact-midpoint'):
        test_window_contact_distance_rounds_exact_scalar_not_global_witness_points(1000.,.001)
