"""Summary integrity and denominator contracts, independent small arithmetic.

The expected ratios are hand-counted integers/Fraction strings, not values
calculated by replay classification. Terminal tampering changes a real CSV
that still passes geometric frame alignment, exercising the extra hash gate.
"""
from pathlib import Path
import inspect
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import m4c_summarize_evidence as summary


def test_summary_reference_denominators_separate_no_contact_incidence_and_secondary():
    counts = {"FIRST_COVER_MATCH": 2, "OTHER_FEATURE_FIRST": 3,
              "FIRST_INCIDENCE_NOT_COVER": 5, "NO_CONTACT_IN_STEP": 7,
              "INITIAL_TOUCH_COVER_MATCH": 11, "INITIAL_OVERLAP_PD_MATCH": 13,
              "INITIAL_OVERLAP_PD_OTHER_FEATURE": 17,
              "INITIAL_OVERLAP_PD_NOT_EVALUATED_RESOURCE": 19}
    result = summary.reference_metrics(counts)
    assert result["all_reference_rows"] == 77
    assert result["separated_rows"] == 17 and result["separated_contact_rows"] == 10
    assert result["first_cover_match_given_contact"]["exact"] == "1/5"
    assert result["other_feature_first_given_contact"]["exact"] == "3/10", "incidence is not an earlier other feature"
    assert result["first_incidence_not_cover_given_contact"]["exact"] == "1/2"
    assert result["nonfirst_cover_given_contact"]["exact"] == "4/5"
    assert result["no_contact_given_separated"]["exact"] == "7/17"
    assert result["first_cover_match_all_separated_rows"]["exact"] == "2/17"
    assert result["pd_cover_match"]["exact"] == "13/30", "resource exclusions stay outside evaluated PD denominator"
    secondary = summary.reference_metrics({"FIRST_COVER_MATCH": 1, "NO_CONTACT_IN_STEP": 2})
    assert secondary["all_reference_rows"] == 3 and secondary["first_cover_match_given_contact"]["exact"] == "1"
    assert result["all_reference_rows"] == 77, "secondary must never be added to primary"
    empty = summary.reference_metrics({})
    assert empty["first_cover_match_given_contact"] == {"numerator": 0, "denominator": 0, "exact": None, "percent_display": None}


@pytest.mark.parametrize("counts", ({"UNCLASSIFIED": 1}, {"FIRST_COVER_MATCH": -1}, {"FIRST_COVER_MATCH": True}))
def test_summary_unknown_or_invalid_reference_counts_are_red(counts):
    with pytest.raises(ValueError, match="unknown or invalid summary reference category"):
        summary.reference_metrics(counts)


def test_summary_vv_secondary_has_distinct_reproducible_example_identity():
    legacy = {"category": "FIRST_COVER_MATCH", "secondary_category": "OTHER_FEATURE_FIRST",
              "secondary_reference": ["VE", 5, 1, 2]}
    expected = (("raw_df05:FIRST_COVER_MATCH", "primary"),
                ("raw_df05:secondary:OTHER_FEATURE_FIRST", "secondary"))
    assert summary.legacy_example_categories("raw_df05", legacy) == expected, "VV references require separate example identities"
    for phase in ("raw_df05", "post_df06"):
        assert summary.legacy_example_categories(phase, {"category": "NO_CONTACT_IN_STEP", "secondary_category": None}) == ((phase+":NO_CONTACT_IN_STEP", "primary"),)
    legacy["secondary_reference"] = None
    with pytest.raises(ValueError, match="secondary example lacks reference"):
        summary.legacy_example_categories("raw_df05", legacy)


def _one_frame_csv_text(terminal_offset):
    points = [(1, 0, 0), (2, 1, 0), (3, 0, 1)]
    lines = ["kind,idx,x,y\n"]
    for kind in ("initial", "step0", "step1", "final"):
        offset = terminal_offset if kind in ("step1", "final") else 0
        lines.extend(f"{kind},{i},{x+offset},{y}\n" for i, x, y in points)
    return "".join(lines)


def test_summary_terminal_tampering_is_red_even_if_csv_alignment_still_passes(tmp_path):
    path = tmp_path / "geom.csv"
    path.write_text(_one_frame_csv_text(1), encoding="utf-8")
    frames = [{"step": 1, "geometry": [[1, 1, 0, 0], [1, 2, 1, 0], [1, 3, 0, 1]]}]
    expected_hash = summary.replay.file_hash(path)
    terminal = summary.bound_terminal_geometry(path, frames, expected_hash)
    assert terminal[0] == [1, 1, 1.0, 0.0]
    path.write_text(_one_frame_csv_text(2), encoding="utf-8")
    assert summary.replay.load_geometry_csv(path, frames)[0] == [1, 1, 2.0, 0.0], "old geometry-only path admits coherent terminal tamper"
    with pytest.raises(ValueError, match="example terminal source changed"):
        summary.bound_terminal_geometry(path, frames, expected_hash)


def test_summary_terminal_hash_defect_injected_inside_checker_fails_guard(tmp_path, monkeypatch):
    path = tmp_path / "geom.csv"
    path.write_text(_one_frame_csv_text(1), encoding="utf-8")
    frames = [{"step": 1, "geometry": [[1, 1, 0, 0], [1, 2, 1, 0], [1, 3, 0, 1]]}]
    expected_hash = summary.replay.file_hash(path)
    path.write_text(_one_frame_csv_text(2), encoding="utf-8")
    def guard():
        rejected = False
        try:
            summary.bound_terminal_geometry(path, frames, expected_hash)
        except ValueError:
            rejected = True
        assert rejected, "summary must reject changed terminal source"
    guard()
    monkeypatch.setattr(summary, "bound_terminal_geometry", lambda p, f, h: summary.replay.load_geometry_csv(p, f))
    with pytest.raises(AssertionError, match="summary must reject changed terminal source"):
        guard()


@pytest.mark.parametrize("defect", ("fold_incidence_into_other", "drop_secondary_example"))
def test_summary_internal_category_defects_fail_their_expected_assertion(monkeypatch, defect):
    if defect == "fold_incidence_into_other":
        target = "reference_metrics"
        original = 'other = counts.get("OTHER_FEATURE_FIRST", 0)'
        replacement = original+'+counts.get("FIRST_INCIDENCE_NOT_COVER", 0)'
        guard = test_summary_reference_denominators_separate_no_contact_incidence_and_secondary
        message = "incidence is not an earlier other feature"
        # Preserve the contact denominator to isolate the misleading rate,
        # rather than first failing a broader row conservation assertion.
        source = inspect.getsource(getattr(summary, target)).replace(original, replacement)
        source = source.replace('contact = matches+other+incidence', 'contact = matches+counts.get("OTHER_FEATURE_FIRST", 0)+incidence')
    else:
        target = "legacy_example_categories"
        original = 'if legacy.get("secondary_category") is not None:'
        source = inspect.getsource(getattr(summary, target)).replace(original, 'if False:')
        guard = test_summary_vv_secondary_has_distinct_reproducible_example_identity
        message = "VV references require separate example identities"
    guard()
    namespace = dict(vars(summary))
    exec(compile(source, "<M4c summary internal mutation>", "exec"), namespace)
    monkeypatch.setattr(summary, target, namespace[target])
    with pytest.raises(AssertionError, match=message):
        guard()
