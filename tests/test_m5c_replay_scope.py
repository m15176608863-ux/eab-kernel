"""M5c accounting oracle: literal slots and closed-form initial states.

Oracle uses Fraction and literal tuples only, no production geometry primitive
to determine expected contact, primary/secondary labels, or count denominators.
"""
from fractions import Fraction as F
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from frozen_evidence import data_path
import m5b_robust_replay as replay


def test_model_comparison_denominators_distinguish_computation_from_identity():
    a = ((0, 0), (1, 0), (0, 1))
    aa = replay.prepare(dict(start=a, end=a, z=(0,)*6, vertex_ids=[0, 1, 2]))
    b = tuple((x+3, y) for x, y in a)
    bb = replay.prepare(dict(start=b, end=b, z=(0,)*6, vertex_ids=[5, 6, 7]))
    certified = replay.compare_pair(aa, bb)
    assert certified["comparison_basis"] == "CERTIFICATE_DIRECT"
    assert not certified["oracle_checked"] and not certified["production_initial_crosschecked"]
    assert "reason" not in certified
    overlapped = replay.compare_pair(aa, aa)
    assert overlapped["comparison_basis"] == "CONSTRUCTED_INITIAL_OVERLAP"
    assert overlapped["oracle_checked"] and not overlapped["production_initial_crosschecked"]
    # Both triangles are static and disjoint; the deliberately large allowed
    # tube blocks certification without changing the nominal geometric answer.
    aa["radius"] = F(2)
    compared = replay.compare_pair(aa, bb)
    assert compared["comparison_basis"] == "EXPLICIT_TRAJECTORY"
    assert compared["oracle_checked"] and compared["production_initial_crosschecked"]
    assert compared["p1"]["status"] == compared["p2"]["status"] == "no_contact"
    c = tuple((x+1, y) for x, y in a)
    cc = replay.prepare(dict(start=c, end=c, z=(0,)*6, vertex_ids=[10, 11, 12]))
    touching = replay.compare_pair(aa, cc)
    assert touching["comparison_basis"] == "CONSTRUCTED_INITIAL_CONTACT"
    assert touching["production_initial_crosschecked"]


def test_primary_secondary_and_missing_pair_are_three_distinct_questions():
    # Padded IDs 4,5 wrap to 0,1; IDs 10,11 wrap to 6,7.
    blocks = [dict(vertex_ids=[0, 1, 2, 3]), dict(vertex_ids=[6, 7, 8, 9])]
    raw = [1, 5, 6, 7, 6, 3, 4]
    row = dict(raw=raw, primary=["VE", 1, 6, 7])
    normalized = replay.canonical_legacy_rows([row], blocks)
    assert normalized[0]["secondary"] == ("VE", 6, 0, 3)
    result = dict(classification="ROBUST_SINGLE_FIRST_COVER", p1=dict(features=(("VE", 6, 0, 3),)))
    rows = {phase: normalized for phase in replay.PHASES}
    counts = replay.legacy_counts(result, rows)
    for phase in replay.PHASES:
        assert counts[phase+":FIRST_COVER_MATCH"] == 0
        assert counts[phase+":SECONDARY_FIRST_COVER_MATCH"] == 1
        assert counts[phase+":ROBUST_FIRST_COVER_NOT_SELECTED"] == 1
        assert counts[phase+":ALL_FIRST_COVER_NOT_SELECTED"] == 0
        assert counts[phase+":ROBUST_CONTACT_MISSING_PAIR"] == 0


def test_bb03_raw_first_cover_is_in_the_same_rows_secondary_slot():
    """Real minimal example, literal tuple7 oracle; not a geometric oracle."""
    data = json.loads((data_path(ROOT, replay.EVIDENCE / "robust_minimal_examples.json")).read_text(encoding="utf-8"))
    example = next(r for r in data["examples"] if (r["case"], r["step"], r["pair"]) == ("bb03", 15, [8, 11]))
    a, b = (replay.prepare(r) for r in example["blocks"])
    result = replay.compare_pair(a, b)
    assert result["classification"] == "ROBUST_SINGLE_FIRST_COVER"
    assert "reason" not in result, "certified rows cannot retain an unproved reason"
    first = set(result["p1"]["features"])
    rows = replay.canonical_legacy_rows(example["legacy"]["raw_df05"], example["blocks"])
    assert all(tuple(r["primary"]) not in first for r in rows)
    assert any(r["raw"][4] > 0 and tuple(r["shared_edge"]) in first for r in rows), "same raw tuple7 has first cover in m4-m6"


def test_frozen_summary_has_disjoint_comparison_and_crosscheck_denominators():
    data = json.loads((data_path(ROOT, replay.EVIDENCE / "robust_summary.json")).read_text(encoding="utf-8"))
    c = data["counts"]
    assert data["complete"] and data["full_history"]
    assert data["schema"] == "eab.m5b-robust-model-replay.v1"
    assert data["source_binding"] == "runtime-loaded-repository-closure-start-and-end.v1"
    assert data["source_hashes"] == data["source_hashes_end"]
    assert c["comparison_basis:EXPLICIT_TRAJECTORY"] == 14079
    assert c["explicit_new_contact_pairs"] == 68
    assert c["p1_p2_explicit_same"] == 14079
    assert c.get("p1_p2_explicit_different", 0) == 0
    assert c["comparison_basis:CONSTRUCTED_INITIAL_OVERLAP"] == 16676
    assert c["comparison_basis:CONSTRUCTED_INITIAL_CONTACT"] == 213
    assert c["comparison_basis:CERTIFICATE_DIRECT"] == 33042
    assert sum(v for k, v in c.items() if k.startswith("comparison_basis:")) == c["pairs"] == 64010
    assert c["independent_initial_state_evaluations"] == 30968
    assert c["production_initial_state_crosschecks"] == 14292
    for phase in replay.PHASES:
        assert data["references"][phase+":SECONDARY_REFERENCE_TOTAL"] == 7768
        assert data["references"][phase+":SHARED_EDGE_SLOT_TOTAL"] == 32075
    for case in data["cases"].values():
        assert case["source_hashes"] == case["source_hashes_end"]
        for example in case["examples"].values():
            if example["result"]["classification"].startswith("ROBUST_"):
                assert "reason" not in example["result"]
