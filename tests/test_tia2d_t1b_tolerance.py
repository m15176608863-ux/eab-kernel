"""WO-T1b closed-form tolerance checks and independently verified examples."""
from fractions import Fraction as Q

import pytest

from eab.adapters.tia2d import tolerance_dovetail, tolerance_knob, g1
from eab.kernel2d.translation_certificates import (
    verify_escape_certificate, verify_trapping_certificate,
)
from tia2d_t1b_tolerance import (
    assembly_rows, dovetail_row, dovetail_threshold, evaluate, standard_rows, knob_row, run,
)


def _verify(sample):
    result = sample["result"]
    assert result.status in ("TRAPPED_TRANSLATION", "ESCAPABLE_TRANSLATION")
    if result.status == "TRAPPED_TRANSLATION":
        assert verify_trapping_certificate(sample["moving"], sample["obstacles"], result.path).valid
    else:
        assert verify_escape_certificate(sample["moving"], sample["obstacles"], result.path).valid


@pytest.mark.parametrize("element,expected", [("square", Q(1, 2)), ("octagon", Q(24, 41))])
@pytest.mark.parametrize("erode", [False, True])
def test_dovetail_closed_form_attainment_and_dyadic_certificates(element, expected, erode):
    """Hand support-function throat equation is separate from E/O construction."""
    row = dovetail_row(Q(3), Q(1), element, erode, iterations=3)
    assert row["closed_form_verified"]
    assert row["exact_threshold"] == expected/(1+erode)
    assert row["attained"] is False
    for sample in row["samples"]+row["bracket_inputs"]:
        _verify(sample)
    bracket = row["dyadic_bracket"]
    for key in ("low", "high"):
        denominator = bracket[key].denominator
        assert denominator & (denominator-1) == 0


@pytest.mark.slow
@pytest.mark.parametrize("element", ["square", "octagon"])
@pytest.mark.parametrize("erode", [False, True])
@pytest.mark.parametrize("wk", [Q(5, 2), Q(3), Q(7, 2)])
@pytest.mark.parametrize("wn", [Q(1), Q(3, 2), Q(2)])
def test_dovetail_three_by_three_exact_throat_event(wk, wn, element, erode):
    geometry = tolerance_dovetail(head_width=wk, neck_width=wn, height=Q(2))
    star = dovetail_threshold(wk, wn, Q(2), element, erode)
    before = evaluate(geometry["moving"], geometry["obstacles"], star-Q(1, 1024), element, erode)
    at = evaluate(geometry["moving"], geometry["obstacles"], star, element, erode)
    assert before["result"].status == "TRAPPED_TRANSLATION"
    assert at["result"].status == "ESCAPABLE_TRANSLATION"
    _verify(before)
    _verify(at)


def test_small_positive_tolerance_sensitive_and_large_tolerance_robust():
    rows = standard_rows()
    assert len(rows) == 8
    for row in rows:
        zero, positive = row["samples"]
        assert zero["result"].status == "TRAPPED_TRANSLATION"
        if row["name"] == "small_positive_tolerance_sensitive":
            assert row["throat_event"] > 0
            assert positive["result"].status == "ESCAPABLE_TRANSLATION"
            if row["element"] == "square" and row["erode_boundaries"]:
                assert row["throat_event"] == Q(1, 4098)
        else:
            assert positive["delta"] == Q(3, 8)
            assert positive["result"].status == "TRAPPED_TRANSLATION"
            assert positive["result"].area_bounds[0] > 0
        _verify(zero)
        _verify(positive)


@pytest.mark.parametrize("family,n", [("TIA-G1", 3), ("TIA-G5", 3), ("TIA-G5", 5), ("TIA-G5", 7)])
def test_every_inner_block_has_a_verified_escape_already_at_zero(family, n):
    rows = assembly_rows(family, "square", True, n)
    assert len(rows) == n
    for row in rows:
        assert row["critical_tolerance"] is None
        assert row["threshold_reason"] == "empty_trapped_set_already_escapable_at_zero"
        for sample in row["samples"]:
            assert sample["result"].status == "ESCAPABLE_TRANSLATION"
            _verify(sample)


def test_fixed_boundary_policy_does_not_stop_ordinary_neighbor_erosion():
    assembly = g1(t=Q(3, 32))
    body = assembly.bodies[2]
    others = assembly.bodies[:2]+assembly.bodies[3:]
    sample = evaluate(body.vertices, tuple(b.vertices for b in others), Q(1, 64),
                      "square", False, tuple(b.boundary_type is not None for b in others))
    for old, new in zip(others, sample["obstacles"]):
        if old.boundary_type is not None:
            assert set(old.vertices) == set(new)
        else:
            assert set(old.vertices) != set(new)
    _verify(sample)


@pytest.mark.parametrize("element", ["square", "octagon"])
def test_polygon_knob_reports_actual_segments_and_verified_opposite_states(element):
    geometry = tolerance_knob(segments=4)
    assert geometry["half_circle_sampling_segments"] == 4
    assert geometry["bulb_segment_count"] == 8
    before = evaluate(geometry["moving"], geometry["obstacles"], Q(1, 8), element, True)
    after = evaluate(geometry["moving"], geometry["obstacles"], Q(1, 4), element, True)
    assert before["result"].status == "TRAPPED_TRANSLATION"
    assert after["result"].status == "ESCAPABLE_TRANSLATION"
    _verify(before)
    _verify(after)


@pytest.mark.parametrize("element,erode,expected", [
    ("square", False, Q(1, 3)), ("square", True, Q(1, 7)),
    ("octagon", False, Q(12, 29)), ("octagon", True, Q(6, 35)),
])
def test_eight_chord_knob_piecewise_linear_event_and_attainment(element, erode, expected):
    row = knob_row(element, erode, iterations=0)
    assert row["exact_threshold"] == expected
    assert row["attained"] is False
    assert row["closed_form_verified"]
    for sample in row["samples"][-3:]:
        _verify(sample)


def test_tolerance_evidence_refuses_existing_artifacts(tmp_path):
    occupied = tmp_path/"existing.json"
    occupied.write_text("do not replace", encoding="utf-8")
    with pytest.raises(FileExistsError, match="refusing"):
        run(occupied, tmp_path/"summary.json", iterations=0)
    assert occupied.read_text(encoding="utf-8") == "do not replace"
