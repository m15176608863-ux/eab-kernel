"""M4c ledger/input guards and frozen audit checks.

Oracle imports: fractions.Fraction; m4c_motion_replay's independent Fraction
incidence/cone equations; kernel2d.g0_oracle (integer winding/intersection).
No production event/root/cone/triangulation primitive is an oracle here.
The 450-frame frozen artifact is checked in full. Only one real production
frame per family is rerun in pytest; tools/m4c_run_replays.py frozen is the
explicit full 450-frame computational gate, to keep routine-suite cost bounded.
"""
from collections import Counter
from copy import deepcopy
from fractions import Fraction as F
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import m4c_motion_replay as replay


def small_snapshot():
    header = {"kind": "header", "schema": "bdda2.detect-shadow", "version": 1, "mode": "shadow",
              "detector": "legacy-df04-df05", "requested_steps": 2,
              "screen": {"max_x": 1920, "max_y": 1080},
              "geometry_columns": replay.snapshot.GEOMETRY_COLUMNS[:], "tuple_columns": replay.snapshot.TUPLE_COLUMNS[:]}
    frames = []
    for step, left in ((1, 2), (2, 0)):
        frames.append({"kind": "step", "step": step,
                       "parameters": dict(d0=.1, h1=3., h5=.3, f0=1e-7, f1=1e-4, f2=4e-4, h2=0., w0=4., hh=.001, g0=.001),
                       "geometry": [[1, 1, 0, 0], [1, 2, 1, 0], [1, 3, 1, 1], [1, 4, 0, 1],
                                    [2, 5, left, 0], [2, 6, left+1, 0], [2, 7, left+1, 1], [2, 8, left, 1]],
                       "raw_df05": [[0, 1, 8, 5, 0, 0, 0]], "post_df06": [[0, 2, 8, 5, 0, 0, 0]]})
    return [header, *frames, {"kind": "end", "completed_steps": 2, "status": "ok"}]


def test_guard_category_not_folded_into_match():
    """External mutation runner calls this exact production-path guard."""
    rows = small_snapshot()
    sg, eg = (replay.snapshot.geometry_from_frame(row) for row in rows[1:3])
    result = replay.frame_result(rows[1], sg, eg)
    assert result["phases"]["raw_df05"]["records"][0]["category"] == "OTHER_FEATURE_FIRST", "motion category preserves earlier other feature"
    assert result["phases"]["post_df06"]["records"][0]["category"] == "FIRST_COVER_MATCH", "motion first cover identity"
    pair = result["pairs"][0]
    assert pair["actual"]["time"]["rational"] == "1/2", "motion first time"
    assert result["stats"]["new_contact_pairs"] == 1
    assert result["stats"]["translation_certified_identical_trajectory"] == 1


def test_guard_step_pairing():
    """External mutation runner shifts _pair_frames; exact pairing must fail."""
    rows = small_snapshot()
    terminal = deepcopy(rows[2]["geometry"])
    for r in terminal:
        if r[0] == 2:
            r[2] -= 2
    result = replay.paired_geometries(rows[1:-1], terminal)
    assert len(result) == 2


def test_synthetic_two_time_surfaces_have_exact_first_cover_categories():
    test_guard_category_not_folded_into_match()


def test_classifier_match_folding_mutation_hits_its_own_guard(monkeypatch):
    monkeypatch.setattr(replay, "classify_reference", lambda *args: "FIRST_COVER_MATCH")
    with pytest.raises(AssertionError, match="motion category preserves earlier other feature"):
        test_guard_category_not_folded_into_match()


def test_pairing_one_step_shift_mutation_hits_alignment_guard(monkeypatch):
    test_guard_step_pairing()
    original = replay._pair_frames
    def shifted(frames, terminal):
        for start, end in original(frames, terminal):
            yield start, {**end, "geometry": start["geometry"]}
    monkeypatch.setattr(replay, "_pair_frames", shifted)
    with pytest.raises(ValueError, match="motion geometry pairing mismatch"):
        test_guard_step_pairing()


def test_missing_terminal_cannot_silently_drop_the_last_interval():
    with pytest.raises(ValueError, match="terminal endpoint required"):
        replay.paired_geometries(small_snapshot()[1:-1], None)


@pytest.mark.parametrize("change,message", [
    ("missing_column", "geometry row width"), ("shifted_column", "columns missing or shifted"),
    ("step_jump", "step sequence discontinuity"), ("rollback", "step sequence discontinuity"),
    ("truncated", "missing/malformed end marker"), ("missing_tuple_column", "row width"),
    ("unknown_attempt", "step fields mismatch"),
])
def test_malformed_snapshot_is_audit_red(tmp_path, change, message):
    rows = small_snapshot()
    if change == "missing_column": rows[1]["geometry"][0].pop()
    elif change == "shifted_column": rows[0]["geometry_columns"][2:] = ["y", "x"]
    elif change == "step_jump": rows[2]["step"] = 3
    elif change == "rollback": rows[2]["step"] = 1
    elif change == "truncated": rows.pop()
    elif change == "missing_tuple_column": rows[1]["raw_df05"][0].pop()
    elif change == "unknown_attempt": rows[1]["attempt_id"] = 2
    source = tmp_path / "snapshot.jsonl"
    source.write_text("".join(json.dumps(r)+"\n" for r in rows), encoding="utf-8")
    with pytest.raises(ValueError, match=message): replay.snapshot.read_snapshot(source)
    assert replay.main([str(source), "--endpoint-file", str(tmp_path / "missing.json"), "--case", "synthetic", "--out", str(tmp_path / "out")]) == 2
    assert json.loads((tmp_path / "out/audit.json").read_text(encoding="utf-8"))["audit"] == "RED"


def test_unknown_category_is_red_not_an_alias_for_match(monkeypatch):
    monkeypatch.setattr(replay, "classify_reference", lambda *args: "UNCLASSIFIED")
    with pytest.raises(ValueError, match="unclassified motion ledger category"):
        test_guard_category_not_folded_into_match()


def test_translation_nonzero_residual_is_uncertified_not_mismatch():
    A = tuple((F(x), F(y)) for x, y in ((0, 0), (1, 0), (1, 1), (0, 1)))
    moved = tuple((x+1, y) for x, y in A)
    _, delta = replay.translation_surrogate(A, moved)
    assert delta == 0 and replay.translation_certificate(delta) == "CERTIFIED_IDENTICAL_TRAJECTORY"
    for amount in (F(1, 1000000), F(1, 2)):
        distorted = tuple((x+amount*y, y) for x, y in moved)
        _, delta = replay.translation_surrogate(A, distorted)
        assert delta > 0 and replay.translation_certificate(delta) == "UNCERTIFIED_NONTRANSLATION", "nontranslation cannot enter certified consistency denominator"


def test_swept_contact_pair_is_detected_with_both_legacy_tables_empty():
    rows = small_snapshot()
    rows[1]["raw_df05"] = []; rows[1]["post_df06"] = []
    sg, eg = (replay.snapshot.geometry_from_frame(row) for row in rows[1:3])
    result = replay.frame_result(rows[1], sg, eg)
    assert result["stats"]["new_contact_pairs_absent_both_tables"] == 1
    assert result["pairs"][0]["actual"]["time"]["rational"] == "1/2"


def test_vv_keeps_and_classifies_both_reference_halves():
    rows = small_snapshot()
    rows[1]["raw_df05"] = [[1, 2, 8, 5, 5, 2, 3]]
    sg, eg = (replay.snapshot.geometry_from_frame(row) for row in rows[1:3])
    result = replay.frame_result(rows[1], sg, eg)
    row = result["phases"]["raw_df05"]["records"][0]
    assert row["primary_reference"] == ("VE", 2, 5, 8)
    assert row["secondary_reference"] == ("VE", 5, 2, 3)
    assert row["category"] == row["secondary_category"] == "FIRST_COVER_MATCH"
    assert result["phases"]["raw_df05"]["secondary_counts"] == {"FIRST_COVER_MATCH": 1}


def test_explicit_pd_resource_limit_is_not_a_match():
    rows = small_snapshot()
    sg = replay.snapshot.geometry_from_frame(rows[2])
    result = replay.frame_result(rows[2], sg, sg, pd_edge_limit=1)
    assert result["stats"]["pd_not_evaluated_resource_pairs"] == 1
    assert result["phases"]["raw_df05"]["counts"] == {"INITIAL_OVERLAP_PD_NOT_EVALUATED_RESOURCE": 1}


@pytest.mark.parametrize("alias", ["audit.json", "normalized.jsonl.gz"])
def test_output_hardlink_alias_never_modifies_read_only_source(tmp_path, alias):
    import os
    source = tmp_path / "source.jsonl"
    source.write_text("".join(json.dumps(r)+"\n" for r in small_snapshot()), encoding="utf-8")
    output = tmp_path / "out"; output.mkdir()
    os.link(source, output / alias)
    before = source.read_bytes()
    assert replay.main([str(source), "--endpoint-file", str(tmp_path / "missing.json"), "--case", "synthetic", "--out", str(output)]) == 2
    assert source.read_bytes() == before and (output / alias).read_bytes() == before


def test_penetration_without_vertex_witness_is_unknown_not_zero():
    A = tuple((F(x), F(y)) for x, y in ((-2, -1), (2, -1), (2, 1), (-2, 1)))
    B = tuple((F(x), F(y)) for x, y in ((-1, -2), (1, -2), (1, 2), (-1, 2)))
    value = replay._penetration_witness(A, B)
    assert value["squared"] is None and not value["has_strict_vertex_witness"]
    assert replay.oracle.overlap(A, B) == 1


@pytest.mark.parametrize("kind", ["step00", "step01", "unexpected"])
def test_geometry_csv_unknown_or_noncanonical_kind_is_red(tmp_path, kind):
    frames = small_snapshot()[1:-1]
    csv_path = tmp_path / "geom.csv"
    csv_path.write_text("kind,idx,x,y\n"+kind+",0,0,0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="geometry CSV (noncanonical step kind|unknown kind)"):
        replay.load_geometry_csv(csv_path, frames)


def test_truncated_gzip_cli_persists_red_and_preserves_source(tmp_path):
    source = tmp_path / "truncated.jsonl.gz"
    contents = "".join(json.dumps(row)+"\n" for row in small_snapshot()).encode("utf-8")
    source.write_bytes(gzip.compress(contents, mtime=0)[:-8])
    before = source.read_bytes()
    out = tmp_path / "audit"
    assert replay.main([str(source), "--endpoint-file", str(tmp_path / "unneeded.json"), "--case", "synthetic", "--out", str(out)]) == 2
    result = json.loads((out / "audit.json").read_text(encoding="utf-8"))
    assert result["audit"] == "RED" and result["complete"] is False
    assert "end-of-stream" in result["error"]
    assert source.read_bytes() == before


@pytest.mark.parametrize("plane", ["header", "frame", "end"])
@pytest.mark.parametrize("shape", [None, 7, [], {}], ids=["null", "scalar", "list", "missing_fields"])
def test_cli_bad_snapshot_top_level_shapes_always_persist_typed_red(tmp_path, plane, shape):
    rows = small_snapshot(); rows[{"header": 0, "frame": 1, "end": -1}[plane]] = shape
    source = tmp_path / "snapshot.jsonl"
    source.write_text("".join(json.dumps(row)+"\n" for row in rows), encoding="utf-8")
    before = source.read_bytes(); output = tmp_path / "audit"
    assert replay.main([str(source), "--endpoint-file", str(tmp_path / "unneeded.json"), "--case", "synthetic", "--out", str(output)]) == 2
    result = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert result["audit"] == "RED" and result["complete"] is False
    assert result["error_type"] in ("TypeError", "ValueError", "KeyError", "AttributeError")
    assert source.read_bytes() == before


@pytest.mark.parametrize("field", ["geometry", "raw_df05", "post_df06", "parameters"])
@pytest.mark.parametrize("shape", [None, 3, [], [None]], ids=["null", "scalar", "empty_list", "null_row"])
def test_cli_bad_nested_snapshot_shapes_are_red(tmp_path, field, shape):
    # Empty legacy tables are legitimate, so use an object for those two
    # empty-list grid cells rather than marking a supported input as invalid.
    if shape == [] and field in ("raw_df05", "post_df06"):
        shape = {}
    rows = small_snapshot(); rows[1][field] = shape
    source = tmp_path / "snapshot.jsonl"
    source.write_text("".join(json.dumps(row)+"\n" for row in rows), encoding="utf-8")
    output = tmp_path / "audit"
    assert replay.main([str(source), "--endpoint-file", str(tmp_path / "unneeded.json"), "--case", "synthetic", "--out", str(output)]) == 2
    result = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert result["audit"] == "RED" and result["complete"] is False and result["error_type"]


@pytest.mark.parametrize("suffix,contents,error_type", [
    (".jsonl", b"\xff\n{}\n{}\n", "UnicodeDecodeError"),
    (".jsonl", b"{broken JSON}\n", "JSONDecodeError"),
    (".jsonl.gz", b"not a gzip stream", "BadGzipFile"),
])
def test_cli_bad_encoding_json_and_gzip_have_typed_red_audits(tmp_path, suffix, contents, error_type):
    source = tmp_path / ("bad"+suffix); source.write_bytes(contents)
    output = tmp_path / "audit"
    assert replay.main([str(source), "--endpoint-file", str(tmp_path / "unneeded.json"), "--case", "synthetic", "--out", str(output)]) == 2
    result = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert result["audit"] == "RED" and result["error_type"] == error_type
    assert source.read_bytes() == contents


@pytest.mark.parametrize("shape", [None, 3, [], {}, {"schema": "eab.m4c-endpoints.v1", "cases": None}])
def test_cli_endpoint_bad_top_level_shapes_are_red(tmp_path, shape):
    source = tmp_path / "snapshot.jsonl"
    source.write_text("".join(json.dumps(row)+"\n" for row in small_snapshot()), encoding="utf-8")
    endpoint = tmp_path / "endpoint.json"; endpoint.write_text(json.dumps(shape), encoding="utf-8")
    output = tmp_path / "audit"
    assert replay.main([str(source), "--endpoint-file", str(endpoint), "--case", "synthetic", "--out", str(output)]) == 2
    result = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert result["audit"] == "RED" and result["complete"] is False and result["error_type"]


@pytest.mark.parametrize("shape", [None, 3, [], {}])
def test_cli_endpoint_bad_case_record_shapes_are_red(tmp_path, shape):
    source = tmp_path / "snapshot.jsonl"
    source.write_text("".join(json.dumps(row)+"\n" for row in small_snapshot()), encoding="utf-8")
    endpoint = tmp_path / "endpoint.json"
    endpoint.write_text(json.dumps({"schema": "eab.m4c-endpoints.v1", "cases": {"synthetic": shape}}), encoding="utf-8")
    output = tmp_path / "audit"
    assert replay.main([str(source), "--endpoint-file", str(endpoint), "--case", "synthetic", "--out", str(output)]) == 2
    result = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert result["audit"] == "RED" and result["complete"] is False and result["error_type"]


def test_cli_unexpected_runtime_failure_is_not_made_green(tmp_path, monkeypatch, capsys):
    def broken(*args, **kwargs):
        raise RuntimeError("injected unexpected runtime failure")
    monkeypatch.setattr(replay, "replay_file", broken)
    output = tmp_path / "audit"
    assert replay.main([str(tmp_path / "unused.jsonl"), "--endpoint-file", str(tmp_path / "unused-end.json"), "--out", str(output)]) == 2
    result = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert result["error_type"] == "RuntimeError" and result["complete"] is False
    assert "M4C_AUDIT_RED RuntimeError" in capsys.readouterr().err


@pytest.mark.parametrize("interrupt", [KeyboardInterrupt, SystemExit])
def test_cli_audit_boundary_does_not_swallow_control_interrupts(tmp_path, monkeypatch, interrupt):
    def interrupted(*args, **kwargs):
        raise interrupt()
    monkeypatch.setattr(replay, "replay_file", interrupted)
    with pytest.raises(interrupt):
        replay.main([str(tmp_path / "unused.jsonl"), "--endpoint-file", str(tmp_path / "unused-end.json"), "--out", str(tmp_path / "audit")])


def test_cli_red_sink_failure_is_attempted_once_and_reported(tmp_path, monkeypatch, capsys):
    calls = []
    def broken(*args, **kwargs):
        raise RuntimeError("original failure")
    def unwritable(*args, **kwargs):
        calls.append(1)
        raise OSError("audit sink failure")
    monkeypatch.setattr(replay, "replay_file", broken)
    monkeypatch.setattr(replay, "write_json", unwritable)
    assert replay.main([str(tmp_path / "unused.jsonl"), "--endpoint-file", str(tmp_path / "unused-end.json"), "--out", str(tmp_path / "audit")]) == 2
    assert calls == [1]
    error = capsys.readouterr().err
    assert "M4C_AUDIT_RED RuntimeError" in error and "M4C_AUDIT_RED_WRITE_ERROR OSError" in error


@pytest.mark.parametrize("failure", ["missing_audit", "broken_json", "nonobject_json", "child_nonzero", "launch_oserror"])
def test_batch_child_failure_always_writes_red_incomplete_summary(tmp_path, monkeypatch, failure):
    import m4c_run_replays as batch
    from types import SimpleNamespace
    monkeypatch.setattr(replay, "CASES", ("bbF038",))
    out = tmp_path / "batch"
    def fake_process(command, **kwargs):
        if failure == "launch_oserror":
            raise OSError("injected executable launch failure")
        case_dir = out / "bbF038"; case_dir.mkdir()
        if failure == "broken_json": (case_dir / "audit.json").write_text("{", encoding="utf-8")
        elif failure == "nonobject_json": (case_dir / "audit.json").write_text("[]", encoding="utf-8")
        elif failure == "child_nonzero": (case_dir / "audit.json").write_text('{"complete":true,"audit":"GREEN"}', encoding="utf-8")
        return SimpleNamespace(returncode=7 if failure == "child_nonzero" else 0, stdout="", stderr="")
    monkeypatch.setattr(batch.subprocess, "run", fake_process)
    assert batch.run_batch("full", out, 1) == 2
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["audit"] == "RED" and summary["complete"] is False
    assert summary["cases"]["bbF038"]["complete"] is False
    assert summary["steps"] == 0


@pytest.mark.parametrize("field,bad,message", [
    ("count", "1", "counts must be non-bool nonnegative integers"),
    ("count", True, "counts must be non-bool nonnegative integers"),
    ("count", -1, "counts must be non-bool nonnegative integers"),
    ("secondary", 1.0, "counts must be non-bool nonnegative integers"),
    ("stats", None, "expected count map"),
    ("stats", {"pairs": "1"}, "counts must be non-bool nonnegative integers"),
    ("stats", {"pairs": True}, "counts must be non-bool nonnegative integers"),
    ("seconds", True, "seconds must be finite"),
    ("seconds", -1, "seconds must be finite"),
    ("seconds", float("inf"), "seconds must be finite"),
    ("seconds", float("nan"), "seconds must be finite"),
])
def test_batch_malformed_numeric_payload_never_reaches_aggregation(field, bad, message):
    import m4c_run_replays as batch
    result = {"counts": {p: {} for p in replay.PHASES}, "secondary_counts": {p: {} for p in replay.PHASES},
              "stats": {}, "seconds": 0}
    if field == "count": result["counts"]["raw_df05"]["FIRST_COVER_MATCH"] = bad
    elif field == "secondary": result["secondary_counts"]["raw_df05"]["FIRST_COVER_MATCH"] = bad
    else: result[field] = bad
    with pytest.raises(ValueError, match=message):
        batch.validate_audit_payload(result, "probe", {})


@pytest.mark.parametrize("mutation,message", [
    ("duplicate_key", "duplicate JSON field"), ("bool_step", "endpoint step requires integer"),
    ("float_step", "endpoint step requires integer"), ("missing_column", "endpoint geometry row width"),
    ("bool_vertex", "endpoint vertex: expected integer"), ("nonfinite", "expected finite number"),
    ("shifted_geometry", "terminal topology/order mismatch"),
])
def test_endpoint_schema_mutations_fail_closed(tmp_path, mutation, message):
    source = ROOT / "fixtures/m4b_shadow/bb52.jsonl.gz"
    _, frames, _ = replay.snapshot.read_snapshot(source)
    original = json.loads((ROOT / "fixtures/m4c_motion/endpoints.json").read_text(encoding="utf-8"))
    row = original["cases"]["bb52"]
    if mutation == "bool_step": row["endpoint_step"] = True
    elif mutation == "float_step": row["endpoint_step"] = 31.0
    elif mutation == "missing_column": row["geometry"][0].pop()
    elif mutation == "bool_vertex": row["geometry"][0][1] = True
    elif mutation == "nonfinite": row["geometry"][0][2] = float("nan")
    elif mutation == "shifted_geometry":
        row["geometry"][0][1] += 10000
        row["geometry_sha256"] = replay.digest(row["geometry"])
    text = json.dumps(original)
    if mutation == "duplicate_key":
        text = text.replace('"schema":', '"schema":"duplicate", "schema":', 1)
    endpoint = tmp_path / "endpoints.json"; endpoint.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        geometry = replay.load_endpoint(endpoint, "bb52", source, frames)
        replay.paired_geometries(frames, geometry)
    output = tmp_path / "audit"
    assert replay.main([str(source), "--endpoint-file", str(endpoint), "--case", "bb52", "--out", str(output)]) == 2
    result = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert result["audit"] == "RED" and result["complete"] is False and result["error_type"]


def _expected():
    return json.loads((ROOT / "fixtures/m4c_motion/expected.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", replay.CASES)
def test_frozen_all_thirty_frames_are_hashed_classified_and_conservative(case):
    expected = _expected()["cases"][case]
    source = ROOT / "fixtures/m4b_shadow" / (case+".jsonl.gz")
    endpoints = ROOT / "fixtures/m4c_motion/endpoints.json"
    assert replay.file_hash(source) == expected["input_hashes"]["snapshot"]
    assert replay.file_hash(endpoints) == expected["input_hashes"]["terminal_source"]
    artifact = ROOT / expected["normalized_file"]
    assert replay.file_hash(artifact) == expected["normalized_sha256"], "frozen normalized artifact hash"
    with gzip.open(artifact, "rt", encoding="utf-8") as stream:
        frames = [json.loads(line) for line in stream]
    assert len(frames) == 30 and [r["step"] for r in frames] == list(range(1, 31))
    assert [replay.digest(r) for r in frames] == expected["frame_sha256"], "frozen all-thirty frame identities"
    counts = {p: Counter() for p in replay.PHASES}; secondary = {p: Counter() for p in replay.PHASES}; stats = Counter()
    for frame in frames:
        stats.update(frame["stats"])
        by_pair = {tuple(r["pair"]): r for r in frame["pairs"]}
        for phase in replay.PHASES:
            row = frame["phases"][phase]
            counts[phase].update(row["counts"])
            secondary[phase].update(row["secondary_counts"])
            assert Counter(x["category"] for x in row["records"]) == row["counts"]
            assert Counter(x["secondary_category"] for x in row["records"] if x["secondary_category"] is not None) == row["secondary_counts"]
            assert set(row["counts"]) <= replay.CATEGORIES
            for record in row["records"]:
                pair = by_pair[tuple(record["pair"])]
                # Frozen categories are independently rebuilt from the exact
                # feature/state witnesses, not trusted because a hash matches.
                assert replay.classify_reference(pair["initial_state"], record["primary_reference"], pair["actual"], pair["pd"]) == record["category"]
                if record["secondary_reference"] is not None:
                    assert replay.classify_reference(pair["initial_state"], record["secondary_reference"], pair["actual"], pair["pd"]) == record["secondary_category"]
    assert {p: dict(v) for p, v in counts.items()} == expected["counts"]
    assert {p: dict(v) for p, v in secondary.items()} == expected["secondary_counts"]
    assert dict(stats) == expected["stats"]


@pytest.mark.parametrize("case", replay.CASES)
def test_real_first_frame_per_family_recomputes_the_frozen_classification(case):
    expected = _expected()["cases"][case]
    _, frames, _ = replay.snapshot.read_snapshot(ROOT / "fixtures/m4b_shadow" / (case+".jsonl.gz"))
    sg, eg = (replay.snapshot.geometry_from_frame(row) for row in frames[:2])
    result = replay.frame_result(frames[0], sg, eg, pd_edge_limit=0)
    assert replay.digest(result) == expected["frame_sha256"][0], "frozen production frame classification"


def test_frozen_family_has_fifteen_cases_and_distinct_outputs():
    cases = _expected()["cases"]
    assert set(cases) == set(replay.CASES)
    assert sum(r["steps"] for r in cases.values()) == 450
    assert len({r["frames_sha256"] for r in cases.values()}) >= 14, "parameterized replay products must differ"


def test_frozen_full_computation_is_bound_to_current_production_sources():
    summary = json.loads((ROOT / "reports/codex/M4c_evidence/frozen_summary.json").read_text(encoding="utf-8"))
    assert summary["complete"] and summary["steps"] == 450
    assert summary["code_hashes"] == replay.code_hashes(), "production source changed: rerun the explicit 450-frame motion audit before refreezing"

