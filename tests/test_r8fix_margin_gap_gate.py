"""R8 margin-output gate migration: independent raw geometry and RN-even proof.

Mutations replace arithmetic INSIDE the real margin_contacts function; neither
records nor the asserted output are postprocessed to manufacture a failure.
"""
from fractions import Fraction as F
import inspect
import math
import struct

import pytest
import eab.margin as margin
from eab.kernel3d.geom3 import box
from e5a_cover_oracle import assert_margin_gap_rounding
import test_invariance_geom as invariance


def _arithmetic_fault_inside_margin_contacts(monkeypatch, fault):
    source = inspect.getsource(margin.margin_contacts)
    anchor = "gap = _normalized_difference(d2, d2 or Fraction(1), Fraction(delta), allow_underflow=True)"
    assert source.count(anchor) == 1
    replacement = {"old_subtraction": "w - delta", "omit_delta": "w",
                   "reverse_delta": "w + delta", "double_distance": "2*w - delta"}[fault]
    scope = dict(vars(margin))
    exec(compile(source.replace(anchor, "gap = " + replacement), __file__, "exec"), scope)
    monkeypatch.setattr(margin, "margin_contacts", scope["margin_contacts"])


def _ordinary_gap_gate():
    # Preserve the original pose and every assertion. R9 correctly constructs
    # RN(sqrt(d2)) in window mode too; old subtraction happens to round correctly
    # for this pose, so add an ordinary binary64 cell that provably distinguishes it.
    invariance.test_margin_layer_is_invariant("box_box_face", 7, 0., .001)
    _ordinary_binary64_midpoint_gap_gate()


def _ordinary_binary64_midpoint_gap_gate():
    # Independent Cartesian intervals: A.x=[1,2], B.x=[-1,-2**-53],
    # overlapping y/z intervals. Every supplied vertex coordinate is binary64.
    # d=1+2**-53 is exactly halfway between 1 and its successor; RN-even(d)=1.
    # But d-1/4=3/4+2**-53 is representable, one ulp above RN(d)-1/4.
    quantum = F(1, 2**53)
    exact_distance, delta = F(1)+quantum, F(1, 4)
    assert exact_distance == (F(1.)+F(math.nextafter(1., math.inf)))/2
    assert struct.unpack('>Q', struct.pack('>d', 1.))[0] % 2 == 0
    expected = math.nextafter(.75, math.inf)
    assert F(expected) == exact_distance-delta
    assert F(.75) < exact_distance-delta
    A = box((1.5, 0., 0.), (.5, .5, .5))
    B = box((-.5, 0., 0.), (.5, 1., 1.))
    B.verts = [(-2.**-53 if x == 0. else x, y, z) for x, y, z in B.verts]
    rows = margin.margin_contacts(A, B, delta=.25, band=1., tol=0, contact_window=0.)
    assert rows
    squared = exact_distance**2
    nearest = min(row.exact_distance_squared for row in rows)
    assert nearest == squared, "independent interval-product distance"
    for row in rows:
        if row.exact_distance_squared == nearest:
            assert row.distance == 1., "distance root midpoint rounds to even"
            assert_margin_gap_rounding(row.margin_gap, squared, delta)
            assert row.margin_gap == expected, "ordinary representable cancellation"
            assert not row.closed


def _large_gap_gate():
    M, excess = F(10**20), F(1)
    A = box((M+excess+1, F(0), F(0)), (F(1), F(1), F(1)))
    B = box((F(-1), F(0), F(0)), (F(1), F(2), F(2)))
    rows = margin.margin_contacts(A, B, delta=M, band=excess+1, tol=0)
    assert rows
    first = rows[0]
    # Independent interval-product gap: min(A.x)-max(B.x)=M+1.
    squared = (M+excess)**2
    assert first.exact_distance_squared == squared
    assert_margin_gap_rounding(first.margin_gap, squared, M)
    assert first.margin_gap == 1., "representable final cancellation"
    assert not first.closed


@pytest.mark.parametrize("gate", [_ordinary_gap_gate, _large_gap_gate], ids=["ordinary_1ulp", "large_cancellation"])
@pytest.mark.parametrize("fault", ["old_subtraction", "omit_delta", "reverse_delta", "double_distance"])
def test_migrated_margin_gate_catches_real_pre_subtraction_rounding(monkeypatch, gate, fault):
    gate()
    _arithmetic_fault_inside_margin_contacts(monkeypatch, fault)
    with pytest.raises(AssertionError, match="exact margin-gap midpoint"):
        gate()


@pytest.mark.parametrize("sign", [-1, 1])
@pytest.mark.parametrize("lower", [0., math.ulp(0.), 1., math.nextafter(1., math.inf)])
def test_margin_midpoint_oracle_enforces_ties_to_even_for_both_signs(lower, sign):
    upper = math.nextafter(lower, math.inf)
    even_lower = struct.unpack('>Q', struct.pack('>d', lower))[0] % 2 == 0
    right, wrong = (lower, upper) if even_lower else (upper, lower)
    target = sign*(F(lower)+F(upper))/2
    delta = F(2)
    squared = (delta+target)**2
    assert_margin_gap_rounding(sign*right, squared, delta)
    with pytest.raises(AssertionError, match="exact margin-gap midpoint"):
        assert_margin_gap_rounding(sign*wrong, squared, delta)


@pytest.mark.parametrize("sign", [-1, 1])
def test_margin_midpoint_oracle_checks_signed_subnormal_underflow(sign):
    target = sign*F(math.ulp(0.))/4
    delta = F(2)
    squared = (delta+target)**2
    assert_margin_gap_rounding(math.copysign(0., sign), squared, delta)
    with pytest.raises(AssertionError, match="signed underflow"):
        assert_margin_gap_rounding(math.copysign(0., -sign), squared, delta)
