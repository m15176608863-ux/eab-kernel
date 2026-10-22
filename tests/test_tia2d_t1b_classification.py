"""Acceptance regression: exact critical roots and the two-point force rule.

The rational expected values and force-angle identity are hand/reference
oracles. Irreducibility checks verify exact polynomial witnesses, not another
LP optimum. All inputs are constructed here; no reports or external files
are required. Complete eight-root and 28-equality coverage is slow-tier.
"""
from fractions import Fraction as Q

import pytest

from eab.adapters.tia2d import g1_morphology
from eab.kernel2d.statics import critical_parameter
from tia2d_t1b_classification import (branch_switch, classify_saved_critical,
                                     thrust_line_prediction)
from tia2d_t1b_morphology import certificate_arithmetic, scan_parameters, wire


@pytest.mark.parametrize("index,expected", [
    (13, Q(131009, 2097408)), (16, Q(98283, 2097664)), (30, Q(326839, 6291456))])
def test_t1b_three_rational_brackets_upgrade_by_exact_critical_basis(index, expected):
    model = g1_morphology(**scan_parameters()[index])
    answer = critical_parameter(model.assembly, max_steps=48)
    assert answer.exact_threshold == expected and answer.attained is True
    assert answer.threshold_proof_reason == "exact_basis_continuation"
    assert answer.threshold_proof.lower_signs is not None
    assert answer.threshold_certificate.status == "UNBOUNDED"
    assert certificate_arithmetic(answer.threshold_certificate)
    assert thrust_line_prediction(model)["mu"] == expected


def test_t1b_two_point_rule_flat_control_and_branch_switch_window():
    for tilt in (Q(3, 32), Q(11, 128)):
        model = g1_morphology(amplitude=Q(0), tilt=tilt)
        expected = tilt - Q(1, 32) * (1 + tilt * tilt)
        assert thrust_line_prediction(model)["mu"] == expected
    switch = branch_switch()
    lo, hi = switch["amplitude_interval"]
    assert hi - lo <= Q(1, 2**90)
    assert Q(10128, 10000) < 4096 * lo < 4096 * hi < Q(10129, 10000)
    assert Q(3, 10**6) < lo - Q(1, 4096) < Q(32, 10**7)


def test_t1b_coupled_phase_cubic_has_modular_irreducibility_witness():
    model = g1_morphology(**scan_parameters()[22])
    critical = critical_parameter(model.assembly, max_steps=40)
    classified = classify_saved_critical(wire(critical))
    assert critical.exact_threshold is None
    assert classified["classification"] == "irrational" and classified["degree"] == 3
    assert classified["coefficients_ascending"] == (-654634592, 102848077337, -663286744, 102848613376)
    assert classified["irreducibility"]["prime"] == 17
    assert all(classified["irreducibility"]["nonzero_evaluation_residues"])
    prediction = thrust_line_prediction(model)["mu"]
    assert prediction == Q(3037, 523584)
    assert Q(critical.mu_lo) - prediction > Q(5, 10000)
    assert classified["attained"] is None


@pytest.mark.slow
@pytest.mark.parametrize("index,degree", [(1, 2), (2, 2), (5, 2), (10, 2),
                                         (11, 2), (14, 2), (19, 3), (22, 3)])
def test_t1b_eight_irrational_roots_keep_certified_brackets(index, degree):
    model = g1_morphology(**scan_parameters()[index])
    critical = critical_parameter(model.assembly, max_steps=40)
    classified = classify_saved_critical(wire(critical))
    assert classified["classification"] == "irrational" and classified["degree"] == degree
    assert critical.exact_threshold is None and critical.attained is None
    assert Q(critical.mu_hi) - Q(critical.mu_lo) <= Q(1, 2**40)
    assert certificate_arithmetic(critical.lower_certificate)
    assert certificate_arithmetic(critical.upper_certificate)
    assert {b["kind"] for b in classified["branch_continuation"]} == {"mechanism", "improving_ray"}
    assert all(b["residual_root_counts"] == 0 for b in classified["branch_continuation"])
    assert thrust_line_prediction(model)["mu"] < Q(critical.mu_lo)


@pytest.mark.slow
@pytest.mark.parametrize("index", [i for i in range(36) if i not in (1, 2, 5, 10, 11, 14, 19, 22)])
def test_t1b_twenty_eight_exact_thresholds_match_two_point_rule(index):
    model = g1_morphology(**scan_parameters()[index])
    critical = critical_parameter(model.assembly, max_steps=48)
    prediction = thrust_line_prediction(model)
    assert critical.exact_threshold == prediction["mu"]
    assert certificate_arithmetic(critical.threshold_certificate)
    if critical.attained is False:
        assert any(prediction[side]["mu"] == critical.exact_threshold and prediction[side]["rise"] == 0
                   for side in ("left", "right"))
