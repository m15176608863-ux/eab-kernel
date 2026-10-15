"""Independent R3 closed forms; oracle imports Fraction and itertools only.

Production imports are subjects, not oracle primitives.  No production root,
intersection, orientation, projection or interval routine computes an expected
answer.  Mutation infrastructure only replaces real internal callables.
"""
from fractions import Fraction as F
from itertools import product

import pytest
from mutation_support import replace_module_callable
from eab.kernel2d import model_robustness as old
from eab.kernel2d import m5c_certificates as cert


def _concave():
    return ((-2, -1), (-1, -1), (-1, F(-1, 2)), (0, 0),
            (-1, F(1, 2)), (-1, 1), (-2, 1), (F(-3, 2), 0))


def _wall():
    return ((1, -2), (3, -2), (3, 2), (1, 2))


def _paths(start, end):
    # Input construction is independent of the production chord adapter.
    return tuple(((F(x), F(u-x)), (F(y), F(v-y)), (F(1),))
                 for (x, y), (u, v) in zip(start, end))


def test_concave_single_cover_matches_closed_form_oracle():
    a, b = _concave(), _wall()
    aa = _paths(a, tuple((x+2, y) for x, y in a))
    bb = _paths(b, b)
    bracket = F(49, 100), F(51, 100)
    radius = F(1, 10000)
    result = cert.single_cover_certificate(aa, bb, ("VE", 3, 3), bracket, radius, radius)
    assert result is not None, "simple concave ring is certifiable"
    assert old.single_cover_certificate(aa, bb, ("VE", 3, 3), bracket, radius, radius) is None
    for da, db in product((-radius, F(0), radius), repeat=2):
        # For this entire translation family the unique rightmost point stays
        # one unit beyond every other vertex.  Its wall time is exact below.
        expected_time = (1+db-da)/2
        expected_label = ("VE", 3, 3)
        assert result["label"] == expected_label
        assert result["bracket"][0] < expected_time < result["bracket"][1]
        shifted = tuple((x+da, y) for x, y in a)
        wall = tuple((x+db, y) for x, y in b)
        subject = cert.single_cover_certificate(_paths(shifted, tuple((x+2, y) for x, y in shifted)),
                                                _paths(wall, wall), expected_label, bracket)
        assert subject is not None and subject["label"] == expected_label
        assert all(x+2*expected_time+da < 1+db for k, (x, _) in enumerate(a) if k != 3)


def test_common_translation_cancels_exactly():
    a = ((0, 0), (1, 0), (0, 1))
    b = tuple((x+3, y) for x, y in a)
    aa, bb = (_paths(r, tuple((x+100, y+100) for x, y in r)) for r in (a, b))
    result = cert.relative_separation_certificate(aa, bb, F(1, 10), F(1, 10), panels=1)
    assert result is not None and result["gap_lower"] >= 2
    assert old.separation_certificate(aa, bb, F(1, 10), F(1, 10), panels=1) is None
    assert cert.relative_separation_certificate(aa, bb, 1, 1, panels=1) is None, "equality is not separation"


@pytest.mark.parametrize("radius", (F(1, 1000000), F(1, 1000)))
def test_near_ties_and_endpoint_ties_are_never_signed(radius):
    # Independent times are 1/2 and 1/2+gap/2.  With gap < 2r,
    # allowed independent x-errors can reverse the nominal vertex order.
    gap = radius
    a = ((-1, -1), (0, F(-1, 2)), (-gap, F(1, 2)), (-1, 1))
    aa, bb = _paths(a, tuple((x+2, y) for x, y in a)), _paths(_wall(), _wall())
    assert cert.single_cover_certificate(aa, bb, ("VE", 1, 3), (F(49, 100), F(51, 100)),
                                         radius, radius) is None
    # A rightmost point reaching a wall corner has a second incidence.
    corner = tuple((x, y+2) for x, y in _concave())
    assert cert.single_cover_certificate(_paths(corner, tuple((x+2, y) for x, y in corner)),
                                         bb, ("VE", 3, 3), (F(49, 100), F(51, 100))) is None


@pytest.mark.parametrize("scale,offset,u", (
    (F(1), (0, 0), F(0)),
    (F(1, 2**80), (10**6, -10**6), F(2, 7)),
    (F(2**60), (-10**5, 10**3), F(-3, 8)),
))
def test_relative_simple_certificate_rigid_unit_covariance(scale, offset, u):
    c, s = (1-u*u)/(1+u*u), 2*u/(1+u*u)
    def transform(ring):
        return tuple((offset[0]+scale*(c*x-s*y), offset[1]+scale*(s*x+c*y)) for x, y in ring)
    a, b = _concave(), _wall()
    aa = _paths(transform(a), transform(tuple((x+2, y) for x, y in a)))
    bb = _paths(transform(b), transform(b))
    radius = scale*(abs(c)+abs(s))/100000
    result = cert.single_cover_certificate(aa, bb, ("VE", 3, 3), (F(49, 100), F(51, 100)), radius, radius)
    assert result is not None and result["label"] == ("VE", 3, 3)


def test_nonlocal_edge_crossing_is_rejected_by_simple_ring_guard():
    # Positive signed area and a unique rightmost point do not prove simplicity.
    # All cross-block guards pass here; the actual internal simplicity path is
    # what prevents the public entrypoint from signing a self-intersecting ring.
    crossed = ((0, 0), (-3, 2), (-1, 2), (-3, 0))
    wall = ((1, -3), (3, -3), (3, 3), (1, 3))
    assert cert.single_cover_certificate(_paths(crossed, tuple((x+2, y) for x, y in crossed)),
                                         _paths(wall, wall), ("VE", 0, 3),
                                         (F(2, 5), F(3, 5))) is None, \
        "self-intersecting ring cannot receive first-cover certificate"
    # Zero-area bow tie is also caught by the lower-level edge-pair guard.
    ring = ((0, 0), (2, 2), (0, 2), (2, 0))
    assert cert._simple(_paths(ring, ring), F(0), F(0), F(1)) <= 0, "crossing ring must fail simplicity"


def test_relative_separation_equality_mutation_fails_semantics(monkeypatch):
    replace_module_callable(monkeypatch, cert, "_separation", [("gap > ra+rb", "gap >= ra+rb")])
    with pytest.raises(AssertionError, match="equality is not separation"):
        test_common_translation_cancels_exactly()


def test_removed_simplicity_internal_guard_fails_semantics(monkeypatch):
    replace_module_callable(monkeypatch, cert, "_simple", [("return min(margins)", "return F(1)")])
    with pytest.raises(AssertionError, match="self-intersecting ring cannot receive"):
        test_nonlocal_edge_crossing_is_rejected_by_simple_ring_guard()


@pytest.mark.parametrize("value", (0.5, True, "1/2"))
def test_r3_rejects_nonexact_coordinates_radii_and_windows(value):
    a, b = _concave(), _wall()
    aa, bb = _paths(a, a), _paths(b, b)
    with pytest.raises(ValueError, match="exact rationals"):
        cert.relative_separation_certificate(aa, bb, value)
    with pytest.raises(ValueError, match="exact rationals"):
        cert.relative_separation_certificate(aa, bb, lo=value)
    malformed = (((value,), (F(0),), (F(1),)), *aa[1:])
    with pytest.raises(ValueError, match="exact rationals"):
        cert.relative_separation_certificate(malformed, bb)
    with pytest.raises(ValueError, match="exact rationals"):
        cert.single_cover_certificate(aa, bb, ("VE", 3, 3), (F(2, 5), F(3, 5)), value)


def test_tangent_touch_and_invalid_indices_are_not_certified():
    a, b = _concave(), _wall()
    # x_tip(s)=4s-4s^2 touches x=1 only at 1/2. A permitted small
    # left shift eliminates the contact, so no positive-tube certificate.
    aa = tuple(((F(x), F(4), F(-4)), (F(y),), (F(1),)) for x, y in a)
    bb = _paths(b, b)
    assert cert.single_cover_certificate(aa, bb, ("VE", 3, 3), (F(2, 5), F(3, 5)), F(1, 1000)) is None
    for label in (("VE", True, 3), ("VE", 3, False), ("VE", -1, 3), ("VE", 8, 3)):
        with pytest.raises(ValueError, match="feature indices"):
            cert.single_cover_certificate(aa, bb, label, (F(2, 5), F(3, 5)))
