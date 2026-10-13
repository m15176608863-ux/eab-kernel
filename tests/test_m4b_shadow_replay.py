"""M4b real snapshot path guards and frozen 15-family replay gates.

Oracle: M4a's independent Fraction edge/halfspace equations; no production
cover/cone/project/normal primitives. Mutations alter snapshot input or the
actual L5 enumeration/classifier, never append fabricated detector outputs.
"""
from collections import Counter
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import m4_shadow_replay as replay

FIXTURES = ROOT / "fixtures/m4b_shadow"
CASES = ("bb52", "bb12", "bb50", "bb51", "bb03", "bb05", "bb06", "bb09", "bb10",
         "bbv01", "bbv01_dbv01a", "bbv02", "bbv02_dbv02a", "bbF038", "bbS038")


def _small_snapshot():
    # Both squares use genuine CCW vertices, no legacy candidates restrict L5.
    # No production geometric primitive is used to construct this input.
    return [
        {"kind": "header", "schema": "bdda2.detect-shadow", "version": 1, "mode": "shadow",
         "detector": "legacy-df04-df05", "requested_steps": 2,
         "screen": {"max_x": 1920, "max_y": 1080},
         "geometry_columns": replay.GEOMETRY_COLUMNS[:], "tuple_columns": replay.TUPLE_COLUMNS[:]},
        *[{"kind": "step", "step": step,
           "parameters": dict(d0=.1, h1=3., h5=.3, f0=1e-7, f1=1e-4, f2=4e-4,
                              h2=0., w0=4., hh=.001, g0=.001),
           "geometry": [[1, 1, 5., -3.], [1, 2, 6., -3.], [1, 3, 6., -2.], [1, 4, 5., -2.],
                        [2, 5, 6.05, -3.], [2, 6, 7.05, -3.], [2, 7, 7.05, -2.], [2, 8, 6.05, -2.]],
           "raw_df05": [[0, 2, 8, 5, 0, 0, 0]], "post_df06": [[0, 2, 8, 5, 0, 0, 0]]}
          for step in (1, 2)],
        {"kind": "end", "completed_steps": 2, "status": "ok"}]



@pytest.mark.parametrize("case", CASES)
def test_fifteen_family_thirty_steps_have_frozen_classified_raw_and_post_tables(case):
    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
    expected = manifest["cases"][case]
    path = FIXTURES / expected["file"]
    assert replay.file_hash(path) == expected["sha256"], "frozen snapshot hash"
    result = replay.replay_file(path, expected_steps=30, m4a_fixture=expected["m4a_fixture"])
    assert result["audit"] == "GREEN" and result["steps"] == 30
    assert result["counts"] == expected["counts"], "frozen classification counts"
    assert replay.digest(result["frames"]) == expected["frames_sha256"], "frozen row-by-row replay"
    assert all(r["m4a_counts"] == r["m4b_counts"] for r in result["m4a_comparison"]), "M4a first-three-step frozen counts"
    assert sum(len(r["classification_changes"]) for r in result["m4a_comparison"]) == expected["m4a_changed_keys"], "M4a per-key input explanations"
    for frame in result["frames"]:
        for row in frame["phases"].values():
            assert row["legacy"] - row["legacy_unique"] == row["counts"].get("LEGACY_DUPLICATE_PRIMARY_REFERENCE", 0)
            assert len(row["differences"]) == sum(v for k, v in row["counts"].items() if k != "MATCH")


def test_capture_manifest_has_exact_family_and_distinct_detection_products():
    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["cases"]) == set(CASES)
    assert len({x["frames_sha256"] for x in manifest["cases"].values()}) >= 14
    assert all(x["steps"] == 30 for x in manifest["cases"].values())
    assert sum(x["steps"] for x in manifest["cases"].values()) == 450
    for expected in manifest["cases"].values():
        assert len(expected["source_sha256"]) == 64
        assert expected["m4a_comparison_audit"] == "EXPLAINED"


def test_snapshot_zero_legacy_candidates_does_not_filter_eab(tmp_path):
    rows = _small_snapshot()
    for row in rows[1:-1]:
        row["raw_df05"] = []
        row["post_df06"] = []
    path = tmp_path / "empty_contacts.jsonl"
    path.write_text("".join(json.dumps(row)+"\n" for row in rows), encoding="utf-8")
    result = replay.replay_file(path)
    for frame in result["frames"]:
        assert frame["phases"]["raw_df05"]["legacy"] == 0
        assert frame["phases"]["raw_df05"]["eab"] > 0


@pytest.mark.parametrize("mutation,expected", [
    ("header_missing_column", "columns missing or shifted"),
    ("header_shift", "columns missing or shifted"),
    ("geometry_missing_column", "geometry row width"),
    ("tuple_missing_column", "row width"),
    ("tuple_value_shift", "shifted tuple/block incidence"),
    ("step_jump", "step sequence discontinuity"),
    ("missing_step", "missing/extra snapshot step"),
    ("truncated_end", "missing/malformed end marker"),
    ("nan", "expected finite number"),
    ("missing_parameter", "parameter columns"),
    ("duplicate_vertex", "identity/order mismatch"),
    ("failed_producer", "producer not ok"),
    ("version_bool", "version: expected integer"),
    ("screen_fraction", "screen.max_x: expected integer"),
])
def test_real_snapshot_input_mutations_fail_closed(tmp_path, mutation, expected):
    rows = _small_snapshot()
    path = tmp_path / "snapshot.jsonl"
    path.write_text("".join(json.dumps(row)+"\n" for row in rows), encoding="utf-8")
    replay.replay_file(path)  # The unmodified input passes through detection.
    if mutation == "header_missing_column":
        rows[0]["tuple_columns"].pop()
    elif mutation == "header_shift":
        rows[0]["geometry_columns"][2:] = ["y", "x"]
    elif mutation == "geometry_missing_column":
        rows[1]["geometry"][0].pop()
    elif mutation == "tuple_missing_column":
        rows[1]["raw_df05"][0].pop()
    elif mutation == "tuple_value_shift":
        rows[1]["raw_df05"][0][1] = rows[1]["raw_df05"][0][2]
    elif mutation == "step_jump":
        rows[2]["step"] = 3
    elif mutation == "missing_step":
        rows.pop(2)
    elif mutation == "truncated_end":
        rows.pop()
    elif mutation == "nan":
        rows[1]["geometry"][0][2] = float("nan")
    elif mutation == "missing_parameter":
        del rows[1]["parameters"]["d0"]
    elif mutation == "duplicate_vertex":
        rows[1]["geometry"][1][1] = rows[1]["geometry"][0][1]
    elif mutation == "failed_producer":
        rows[-1]["status"] = "failed"
    elif mutation == "version_bool":
        rows[0]["version"] = True
    elif mutation == "screen_fraction":
        rows[0]["screen"]["max_x"] = 1920.5
    path.write_text("".join(json.dumps(row)+"\n" for row in rows), encoding="utf-8")
    with pytest.raises(ValueError, match=expected):
        replay.replay_file(path)
    # Exercise the CLI audit sink too: errors are persisted RED, return nonzero.
    assert replay.main([str(path), "--out", str(tmp_path / "audit")]) == 2
    audit = json.loads((tmp_path / "audit/audit.json").read_text(encoding="utf-8"))
    assert audit["audit"] == "RED" and expected.split("|")[0] in audit["error"]


def test_actual_l5_angle_window_defect_is_caught_by_replay_gate(monkeypatch):
    original = replay.bdda2d.covers.enumerate_covers
    def omit_angle(A, B, **kwargs):
        kwargs["cone_tol"] = 0.0
        return original(A, B, **kwargs)
    monkeypatch.setattr(replay.bdda2d.covers, "enumerate_covers", omit_angle)
    with pytest.raises(AssertionError, match="unclassified differences|frozen classification counts"):
        test_fifteen_family_thirty_steps_have_frozen_classified_raw_and_post_tables("bb52")


def test_actual_unknown_classifier_result_makes_audit_red(tmp_path, monkeypatch):
    original = replay.m4a.classify_extra
    def unknown(key, sg, window):
        original(key, sg, window)
        return "UNREGISTERED"
    monkeypatch.setattr(replay.m4a, "classify_extra", unknown)
    path = tmp_path / "snapshot.jsonl"
    path.write_text("".join(json.dumps(row)+"\n" for row in _small_snapshot()), encoding="utf-8")
    assert replay.main([str(path), "--out", str(tmp_path / "audit")]) == 2
    result = json.loads((tmp_path / "audit/audit.json").read_text(encoding="utf-8"))
    assert result["audit"] == "RED" and "unclassified differences" in result["error"]


@pytest.mark.parametrize("alias", ["source_normalized", "source_audit", "outputs_each_other"])
def test_hardlinked_outputs_fail_without_mutating_source_or_existing_files(tmp_path, alias):
    """The real filesystem write path must preserve all pre-existing bytes."""
    import os
    source = tmp_path / "snapshot.jsonl"
    source.write_text("".join(json.dumps(row)+"\n" for row in _small_snapshot()), encoding="utf-8")
    out = tmp_path / "audit"
    out.mkdir()
    normalized, audit = out / "normalized.jsonl.gz", out / "audit.json"
    if alias == "source_normalized":
        os.link(source, normalized)
    elif alias == "source_audit":
        os.link(source, audit)
    else:
        normalized.write_bytes(b"existing independent output bytes")
        os.link(normalized, audit)
    before = {p: p.read_bytes() for p in (source, normalized, audit) if p.exists()}
    assert replay.main([str(source), "--out", str(out)]) == 2
    assert {p: p.read_bytes() for p in before} == before, "read-only source/output alias failure mutated bytes"
