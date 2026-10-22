"""Thickness-band oracle: hand contact-wrench convexity, no production geometry.

The primary zero-friction oracle is the vertical width of a two-slope
endpoint-wrench convex hull. It shares neither contact assembly nor LP
primitives with the tested production results. Positive sampled thresholds
add exact primal/dual continuation, not a claim from numerical closeness.
"""
from fractions import Fraction as Q

import pytest

from eab.adapters.tia2d import g1_morphology
from eab.kernel2d.statics import limit_load_ideal_exact_2d
from tia2d_t1b_morphology import certificate_arithmetic
from tia2d_t1b_thickness import (PRIMARY_FAMILIES, CONTROL_FAMILIES,
    TILT, certified_thick_control, certified_thickness_sample, zero_friction_band)


@pytest.mark.parametrize("family,upper", tuple(zip(PRIMARY_FAMILIES,
    (Q(32, 257), Q(16, 145), Q(1280, 12373), Q(64, 677)))))
def test_t1b_thickness_band_exact_wrench_boundaries(family, upper):
    a, n, eta = family
    band = zero_friction_band(a, n, eta)
    assert band["morphology_creates_threshold_interval"] == (Q(96, 1033), upper)
    assert band["interval_closed"] == (True, False)
    # Independent endpoint arithmetic; no polygon or LP constructor involved.
    for slope_index, slope in enumerate(band["slopes"]):
        intercepts = []
        for cycle in range(n):
            if slope_index == 0:
                endpoints = ((Q(cycle, n), Q(0)), ((Q(cycle) + eta) / n, Q(1)))
            else:
                endpoints = (((Q(cycle) + eta) / n, Q(1)), (Q(cycle + 1, n), Q(0)))
            for z, value in endpoints:
                intercepts.append(z + slope * (TILT * (z - Q(1, 2)) + a * value))
        assert max(intercepts) - min(intercepts) == band["wrench_widths"][slope_index]


@pytest.mark.parametrize("family", PRIMARY_FAMILIES)
@pytest.mark.parametrize("weight", (Q(0), Q(1, 2), Q(3, 4)))
def test_t1b_thickness_band_flat_zero_teeth_positive_exact_certificates(family, weight):
    a, n, eta = family
    band = zero_friction_band(a, n, eta)
    lo, hi = band["morphology_creates_threshold_interval"]
    ratio = (1 - weight) * lo + weight * hi
    record = certified_thickness_sample(ratio, a, n, eta, max_steps=28)
    assert record["flat_threshold"] == 0
    assert record["exact_threshold"] > 0 and record["attained"] is True
    assert record["certificate_arithmetic"]
    assert record["threshold_certificate"].status == "UNBOUNDED"
    assert record["threshold_proof"].lower_signs is not None


@pytest.mark.parametrize("family", PRIMARY_FAMILIES)
def test_t1b_thickness_band_open_upper_and_closed_lower(family):
    a, n, eta = family
    band = zero_friction_band(a, n, eta)
    lo, hi = band["morphology_creates_threshold_interval"]
    step = Q(1, 65536)
    for ratio, expected in ((hi - step, "OPTIMAL"), (hi, "UNBOUNDED"),
                            (hi + step, "UNBOUNDED")):
        model = g1_morphology(height=2 * ratio, amplitude=2 * a * ratio,
                              periods=n, asymmetry=eta).assembly
        answer = limit_load_ideal_exact_2d(model, mu=Q(0))
        assert answer.status == expected
        assert certificate_arithmetic(answer)
    for ratio, expected in ((lo - step, "OPTIMAL"), (lo, "UNBOUNDED")):
        flat = g1_morphology(height=2 * ratio, amplitude=Q(0)).assembly
        answer = limit_load_ideal_exact_2d(flat, mu=Q(0))
        assert answer.status == expected
        assert certificate_arithmetic(answer)


@pytest.mark.parametrize("family", CONTROL_FAMILIES)
def test_t1b_thickness_two_period_large_tooth_has_no_creation_band(family):
    band = zero_friction_band(*family)
    assert not band["nonempty"] and band["morphology_creates_threshold_interval"] is None
    a, n, eta = family
    answer = certified_thickness_sample(Q(96, 1033), a, n, eta, max_steps=24)
    assert answer["flat_threshold"] == answer["exact_threshold"] == 0


@pytest.mark.parametrize("family", PRIMARY_FAMILIES + CONTROL_FAMILIES)
@pytest.mark.parametrize("ratio", (Q(3, 16), Q(1, 4), Q(1, 2)))
def test_t1b_thickness_discrete_thick_controls_remain_closed_zero(family, ratio):
    answer = certified_thick_control(ratio, *family)
    assert answer["exact_threshold"] == 0 and answer["attained"]
    assert answer["certificate_arithmetic"]


def test_t1b_thickness_peak_value_and_scan_input_guards():
    record = certified_thickness_sample(Q(3, 32), Q(1, 64), 1, Q(1, 2), max_steps=24)
    assert record["exact_threshold"] == Q(253, 16384)
    assert record["flat_threshold"] == 0
    for a, n, eta in ((Q(0), 1, Q(1, 2)), (Q(1, 32), 1, Q(1, 2)),
                       (Q(1, 64), 4, Q(1, 2)), (Q(1, 64), 1, Q(1, 3))):
        with pytest.raises(ValueError):
            zero_friction_band(a, n, eta)
