"""Wiring oracle: literal geometry/legacy expectations, not reused predicates.

Oracle imports Fraction and stdlib protocol/hash readers only. This file does
not pretend replay integration assertions are an independent geometry oracle.
Full 1810-step work is explicit evidence, never hidden in the default test run.
"""
from fractions import Fraction as F
import json
from pathlib import Path
import sys

import pytest
from mutation_support import replace_module_callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import m5b_robust_replay as replay


def _row(start, end, z, ids):
    return dict(start=[[str(v) for v in p] for p in start], end=[[str(v) for v in p] for p in end],
                z=[str(v) for v in z], vertex_ids=list(ids))


def test_replay_distinguishes_robust_first_cover_from_unproved_initial_exit():
    a = ((-2, 0), (-1, F(-1, 2)), (0, 0), (-1, F(1, 2)))
    end = tuple((x+2, y) for x, y in a)
    b = ((1, -2), (3, -2), (3, 2), (1, 2))
    aa = replay.prepare(_row(a, end, (2, 0, 0, 0, 0, 0), (1, 2, 3, 4)))
    bb = replay.prepare(_row(b, b, (0, 0, 0, 0, 0, 0), (11, 12, 13, 14)))
    result = replay.compare_pair(aa, bb)
    assert result["classification"] == "ROBUST_SINGLE_FIRST_COVER"
    assert result["p1"]["features"] == result["p2"]["features"] == (("VE", 3, 11, 14),)
    rows = {"raw_df05": [dict(primary=["VE", 3, 11, 14])], "post_df06": []}
    counts = replay.legacy_counts(result, rows)
    assert counts["raw_df05:FIRST_COVER_MATCH"] == 1
    assert counts["post_df06:ROBUST_CONTACT_MISSING_PAIR"] == 1
    assert counts["post_df06:ROBUST_FIRST_COVER_NOT_SELECTED"] == 1
    unproved = replay.compare_pair(aa, aa)
    assert unproved["classification"] == "MODEL_SENSITIVE_OR_UNPROVED"
    assert unproved["reason"] == "INITIAL_EXIT_ORDER_UNCERTIFIED"


def test_legacy_ledger_is_primary_only_even_if_secondary_matches_first_cover():
    """Explicit scope guard: a secondary match is not a missing contact pair.

    Literal tuple7 decoding is the oracle; no production geometry primitive
    supplies the expected primary/secondary references. Reports must retain
    this primary-only qualifier and leave secondary accounting PARTIAL.
    """
    feature = ("VE", 20, 10, 11)
    raw = [1, 11, 20, 21, 20, 10, 11]
    secondary = ("VE", raw[4], *sorted((raw[5], raw[6])))
    assert raw[0] == 1 and raw[4] > 0 and secondary == feature
    result = dict(classification="ROBUST_SINGLE_FIRST_COVER", p1=dict(features=(feature,)))
    rows = {phase: [dict(raw=raw, primary=["VE", 11, 20, 21])] for phase in replay.PHASES}
    counts = replay.legacy_counts(result, rows)
    for phase in replay.PHASES:
        assert counts[phase+":OTHER_REFERENCE"] == 1
        assert counts[phase+":FIRST_COVER_MATCH"] == 0
        assert counts[phase+":ROBUST_FIRST_COVER_NOT_SELECTED"] == 1, "unselected means unselected as PRIMARY only"
        assert counts[phase+":ROBUST_CONTACT_MISSING_PAIR"] == 0, "secondary presence cannot make an existing pair missing"


def test_replay_rounding_tube_is_charged_even_when_models_have_same_status():
    a = ((0, 0), (1, 0), (0, 1))
    b = tuple((x+3, y) for x, y in a)
    aa = replay.prepare(_row(a, a, (0, 0, 0, 0, 0, 0), (1, 2, 3)))
    bb = replay.prepare(_row(b, b, (0, 0, 0, 0, 0, 0), (4, 5, 6)))
    result = replay.compare_pair(aa, bb)
    assert result["classification"] == "ROBUST_NO_CONTACT"
    # A 2-unit tube can reach the other triangle; agreement alone cannot certify.
    aa["radius"] = F(2)
    result = replay.compare_pair(aa, bb)
    assert result["same"] is True
    assert result["classification"] == "MODEL_SENSITIVE_OR_UNPROVED", "same status is not a tube certificate"


def test_replay_tube_wiring_mutation_is_killed_by_semantic_assertion(monkeypatch):
    replace_module_callable(monkeypatch, replay, "compare_pair", [
        ('radius = a["radius"]+b["radius"]', 'radius = F(0)')])
    with pytest.raises(AssertionError, match="same status is not a tube certificate"):
        test_replay_rounding_tube_is_charged_even_when_models_have_same_status()


def test_p3_own_endpoint_closure_has_separate_parameter_error_budget(monkeypatch):
    # Wiring-only fixture: the geometric bound provider is independently tested
    # in test_m5b_motion; here distinct exact inputs expose a missing summand.
    monkeypatch.setattr(replay, "p2_p3_bound", lambda *args: dict(position=F(3), radius_l1=F(2), parameter_angle=F(1, 7)))
    a = ((0, 0), (1, 0), (0, 1))
    aa = replay.prepare(_row(a, a, (0, 0, 0, 0, 0, 0), (1, 2, 3)))
    assert aa["radius"] == F(23, 7), "P3 own endpoint closure must include parameter error twice"


def test_p3_endpoint_closure_budget_mutation_dies_on_wiring_assertion(monkeypatch):
    replace_module_callable(monkeypatch, replay, "prepare", [
        ("radius=bound+residual+endpoint_parameter", "radius=bound+residual")])
    with pytest.raises(AssertionError, match="own endpoint closure"):
        test_p3_own_endpoint_closure_has_separate_parameter_error_budget(monkeypatch)


def test_frozen_input_counts_cover_fifteen_cases_and_15220_blocks():
    manifest = json.loads((ROOT / "reports/codex/M5b_evidence/endpoint_inputs/manifest.json").read_text(encoding="utf-8"))
    assert manifest["complete"] and len(manifest["cases"]) == 15
    assert sum(row["steps"] for row in manifest["cases"].values()) == 1810
    assert sum(row["block_frames"] for row in manifest["cases"].values()) == 15220
    legacy = json.loads((replay.LEGACY / "manifest.json").read_text(encoding="utf-8"))
    assert legacy["complete"] and set(legacy["cases"]) == set(manifest["cases"])
    for case, row in legacy["cases"].items():
        assert replay.sha(replay.LEGACY / (case+".jsonl.gz")) == row["sha256"]
        assert row["source_sha256"] == manifest["cases"][case]["source_hashes"]["shadow.jsonl"]


def test_five_real_model_certificates_recompute_from_self_contained_minimal_inputs():
    import m5b_minimal_examples
    assert m5b_minimal_examples.verify() == 5
