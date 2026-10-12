"""Quantitative document claims tested at the stated (not relaxed) bound.

Oracle: Fraction arithmetic and squaring positive rational endpoints around
2+sqrt(2). No production norm/noise/root routine supplies the reference.
"""
from fractions import Fraction as F
import inspect
import textwrap
import pytest
from eab.kernel3d import geom3 as G


@pytest.mark.parametrize("exponent",[-400,0,390])
def test_face_noise_obeys_the_documented_two_rounding_relative_bound(exponent):
    s=F(2)**exponent
    polygon=G.Polyhedron([(0,0,0),(s,0,0),(0,s,0)],[(0,1,2)])
    ratio=F(polygon.face_noise(0))/F(2)**-46
    u=F(1,2**53)
    delta=2*u+u*u
    # |ratio-target|<=delta*target iff ratio/(1+delta)<=target
    # and target<=ratio/(1-delta). target=2+sqrt(2), endpoints rational.
    lower=ratio/(1+delta)
    upper=ratio/(1-delta)
    assert lower<=2 or (lower-2)**2<=2,"documented 2u+u^2 relative bound: lower side"
    assert upper>=2 and (upper-2)**2>=2,"documented 2u+u^2 relative bound: upper side"


def test_face_noise_strict_constant_gate_rejects_internal_eight_u_bias(monkeypatch):
    source=textwrap.dedent(inspect.getsource(G.Polyhedron.face_noise))
    needle="v = _eg.sqrt_rational(numerator*numerator/_eg.dot(n,n))"
    assert source.count(needle)==1
    replacement="v = scalar_rational(Fraction(_eg.sqrt_rational(numerator*numerator/_eg.dot(n,n)))*(1+Fraction(8,2**53)))"
    scope=dict(vars(G));exec(source.replace(needle,replacement),scope)
    monkeypatch.setattr(G.Polyhedron,"face_noise",scope["face_noise"])
    with pytest.raises(AssertionError,match=r"documented 2u\+u\^2 relative bound"):
        test_face_noise_obeys_the_documented_two_rounding_relative_bound(0)
