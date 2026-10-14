"""Independent repeatable M4c input/prediction review; no production edits.

Run from the workspace with PYTHONDONTWRITEBYTECODE=1 and python -X utf8.
All generated negative inputs and subprocess basetemp are forced below the
workspace evidence tmp.  Sibling files are only hashed, never executed.
"""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from fractions import Fraction
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = ROOT / "reports/codex/M4c_evidence"
TMP = EVIDENCE / "tmp"
os.environ["TEMP"] = os.environ["TMP"] = str(TMP)
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
import m4c_motion_replay as replay
import m4c_run_replays as batches


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise AssertionError(message)


def local_output(path):
    require(path.resolve().is_relative_to(TMP.resolve()), "negative output outside workspace tmp")
    return path


def reject(call, label, kind, records):
    try:
        call()
    except ValueError as error:
        records.append({"kind": kind, "case": label, "rejected": True, "message": str(error)})
    else:
        raise AssertionError("malformed input was accepted: " + label)


def main():
    tmp = local_output(TMP / ("review_inputs_prediction_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")))
    tmp.mkdir(parents=True)
    code_start = replay.code_hashes()
    extra_paths = (ROOT / "tools/m4c_run_replays.py", ROOT / "tests/test_m4c_replay.py",
                   ROOT / "tests/test_m4c_batch_publish.py", Path(__file__))
    extra_start = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in extra_paths}
    prior = json.loads((EVIDENCE / "kinematics_audit.json").read_text(encoding="utf-8"))
    endpoint_path = ROOT / "fixtures/m4c_motion/endpoints.json"
    endpoint_rows = json.loads(endpoint_path.read_text(encoding="utf-8"))["cases"]
    cases = []
    full_count = frozen_count = geometry_count = 0
    for case in prior["cases"]:
        name, hashes = case["case"], {}
        for kind, item in case["files"].items():
            require(sha(item["source"]) == item["sha256"] == sha(item["copy"]), "input/copy drift " + name + kind)
            hashes[kind] = item["sha256"]
        local = TMP / "kinematics_inputs" / name
        _, full, _ = replay.snapshot.read_snapshot(local / "shadow.jsonl")
        terminal = replay.load_geometry_csv(local / "geom.csv", full)
        full_pairs = replay.paired_geometries(full, terminal)
        fixture = ROOT / "fixtures/m4b_shadow" / (name + ".jsonl.gz")
        _, prefix, _ = replay.snapshot.read_snapshot(fixture)
        require(len(prefix) == 30 and prefix == full[:30], "prefix mismatch")
        endpoint = replay.load_endpoint(endpoint_path, name, fixture, prefix)
        expected = full[30]["geometry"] if len(full) > 30 else terminal
        require(endpoint == expected, "frozen terminal time-plane mismatch")
        require(endpoint_rows[name]["full_snapshot_sha256"] == sha(local / "shadow.jsonl"), "full-source binding drift")
        require(endpoint_rows[name]["geometry_csv_sha256"] == sha(local / "geom.csv"), "geometry binding drift")
        prefix_pairs = replay.paired_geometries(prefix, endpoint)
        require(len(full_pairs) == len(full) and len(prefix_pairs) == 30, "interval missing")
        full_count += len(full_pairs)
        frozen_count += len(prefix_pairs)
        geometry_count += sum(len(frame["geometry"]) for frame in full)
        cases.append({"case": name, "full_frames": len(full), "full_intervals": len(full_pairs),
                      "frozen_frames": 30, "frozen_intervals": len(prefix_pairs),
                      "prefix_endpoint_source": "full step31 start" if len(full) > 30 else "geom step30 final",
                      "source_and_copy_hashes_verified": hashes})
    require((full_count, frozen_count, geometry_count) == (1810, 450, 188320), "dataset inventory drift")
    for item in prior["source_files"]:
        require(sha(item["path"]) == item["sha256"] == sha(item["shadow_tree_source_path"]), "sibling source drift")
    static = json.loads((EVIDENCE / "motion_exit_static.json").read_text(encoding="utf-8"))
    static_current = not static["violations"] and all(sha(ROOT / p) == h for p, h in static["code_sha256"].items())

    negatives = []
    local = TMP / "kinematics_inputs/bb52"
    _, frames, _ = replay.snapshot.read_snapshot(local / "shadow.jsonl")
    original = (local / "geom.csv").read_text(encoding="utf-8")
    for label, kind in (("leading_zero", "step00"), ("explicit_plus", "step+0"),
                        ("unicode_digit", "step\uff10"), ("unknown_kind", "unexpected_geometry")):
        changed = original.replace("step0,", kind + ",", 1) if label != "unknown_kind" else original + kind + ",0,0,0\n"
        path = local_output(tmp / (label + ".csv"))
        path.write_text(changed, encoding="utf-8")
        reject(lambda: replay.load_geometry_csv(path, frames), label, "geom_csv", negatives)
    fixture = ROOT / "fixtures/m4b_shadow/bb52.jsonl.gz"
    _, prefix, _ = replay.snapshot.read_snapshot(fixture)
    for label in ("boolean_step", "boolean_id", "string_coordinate", "unknown_attempt", "changed_start_binding"):
        payload = json.loads(endpoint_path.read_text(encoding="utf-8"))
        row = payload["cases"]["bb52"]
        if label == "boolean_step":
            row["endpoint_step"] = True
        elif label == "boolean_id":
            row["geometry"][0][0] = True
        elif label == "string_coordinate":
            row["geometry"][0][2] = "0"
        elif label == "unknown_attempt":
            row["attempt_id"] = 1
        else:
            row["start_geometry_sha256"] = "0" * 64
        path = local_output(tmp / (label + ".json"))
        path.write_text(json.dumps(payload), encoding="utf-8")
        reject(lambda: replay.load_endpoint(path, "bb52", fixture, prefix), label, "endpoint", negatives)

    bad_gzip = local_output(tmp / "truncated.jsonl.gz")
    bad_gzip.write_bytes(fixture.read_bytes()[:-12])
    source_hash = sha(bad_gzip)
    gzip_out = local_output(tmp / "truncated_result")
    diagnostics = io.StringIO()
    with redirect_stderr(diagnostics), redirect_stdout(diagnostics):
        returncode = replay.main([str(bad_gzip), "--endpoint-file", str(endpoint_path), "--case", "bb52", "--out", str(gzip_out)])
    gzip_audit = json.loads((gzip_out / "audit.json").read_text(encoding="utf-8"))
    require(returncode == 2 and gzip_audit["audit"] == "RED" and gzip_audit["complete"] is False,
            "truncated gzip did not persist RED")
    require(source_hash == sha(bad_gzip), "negative gzip source changed")
    negatives.append({"kind": "gzip_cli", "case": "truncated_footer", "rejected": True,
                      "exit_code": returncode, "message": gzip_audit["error"], "source_unchanged": True})

    # Exercise the real executable boundary, not only main() in this process.
    # Mutations are made to supplied envelopes before the production reader.
    with gzip.open(fixture, "rt", encoding="utf-8") as stream:
        envelope = [json.loads(line) for line in stream]
    cli_cases = []
    for plane, index in (("header", 0), ("frame", 1), ("end", -1)):
        for label, shape in (("null", None), ("integer", 9), ("list", [1]), ("empty_object", {})):
            rows = list(envelope)
            rows[index] = shape
            contents = "".join(json.dumps(row) + "\n" for row in rows).encode("utf-8")
            cli_cases.append((plane + "_" + label, ".jsonl", contents, {"TypeError", "ValueError"}))
    for label, suffix, contents, error_type in (
            ("invalid_utf8", ".jsonl", b"\xff\xfe\n", "UnicodeDecodeError"),
            ("invalid_json", ".jsonl", b"{\n", "JSONDecodeError"),
            ("invalid_gzip", ".jsonl.gz", b"not gzip", "BadGzipFile"),
            ("truncated_gzip", ".jsonl.gz", fixture.read_bytes()[:-12], "EOFError")):
        cli_cases.append((label, suffix, contents, {error_type}))
    for label, suffix, contents, expected_errors in cli_cases:
        source = local_output(tmp / ("real_cli_" + label + suffix))
        source.write_bytes(contents)
        output = local_output(tmp / ("real_cli_" + label + "_out"))
        command = [sys.executable, "-X", "utf8", str(ROOT / "tools/m4c_motion_replay.py"),
                   str(source), "--endpoint-file", str(endpoint_path), "--case", "bb52", "--out", str(output)]
        completed = subprocess.run(command, cwd=ROOT, env=dict(os.environ), capture_output=True,
                                   text=True, encoding="utf-8")
        audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
        require(completed.returncode == 2 and audit["audit"] == "RED" and audit["complete"] is False,
                "real CLI did not persist RED: " + label)
        require(audit["error_type"] in expected_errors, "real CLI rejected at wrong input boundary: " + label)
        require("M4C_AUDIT_RED " + audit["error_type"] in completed.stderr, "missing typed CLI diagnostic")
        require("binding" not in audit["error"].lower() and "sha256" not in audit["error"].lower(),
                "malformed envelope slipped through to unrelated hash guard")
        require(source.read_bytes() == contents, "CLI changed malformed source")
        negatives.append({"kind": "real_cli", "case": label, "rejected": True,
                          "exit_code": completed.returncode, "error_type": audit["error_type"],
                          "message": audit["error"], "source_unchanged": True})

    for failure in ("missing_audit", "broken_json", "nonobject_json", "child_nonzero", "launch_oserror",
                    "string_count", "boolean_count", "negative_count", "malformed_stats", "string_stat"):
        batch_out = local_output(tmp / ("batch_" + failure))
        def fake_child(command, **kwargs):
            if failure == "launch_oserror":
                raise OSError("independent-review launch failure")
            child = local_output(Path(command[command.index("--out") + 1]))
            if failure in ("broken_json", "nonobject_json"):
                child.mkdir(parents=True)
                (child / "audit.json").write_text("{" if failure == "broken_json" else "[]", encoding="utf-8")
            if failure in ("string_count", "boolean_count", "negative_count", "malformed_stats", "string_stat"):
                child.mkdir(parents=True)
                malformed = {"audit": "GREEN", "complete": True, "code_hashes": replay.code_hashes(), "steps": 1,
                             "counts": {phase: {} for phase in replay.PHASES},
                             "secondary_counts": {phase: {} for phase in replay.PHASES},
                             "stats": {}, "seconds": 0, "input_hashes": {"snapshot": "0" * 64, "terminal_source": "0" * 64},
                             "frames_sha256": "0" * 64, "normalized_sha256": "0" * 64}
                if failure in ("string_count", "boolean_count", "negative_count"):
                    malformed["counts"][replay.PHASES[0]][sorted(replay.CATEGORIES)[0]] = {
                        "string_count": "not-an-integer", "boolean_count": True, "negative_count": -1}[failure]
                elif failure == "malformed_stats":
                    malformed["stats"] = None
                else:
                    malformed["stats"] = {"initial_separated_pairs": "not-an-integer"}
                (child / "audit.json").write_text(json.dumps(malformed), encoding="utf-8")
            return SimpleNamespace(returncode=7 if failure == "child_nonzero" else 0, stdout="", stderr="")
        capture = io.StringIO()
        with patch.object(replay, "CASES", ("independent_review_case",)), patch.object(batches.subprocess, "run", fake_child):
            with redirect_stdout(capture), redirect_stderr(capture):
                result = batches.run_batch("full", batch_out, 1)
        summary = json.loads((batch_out / "summary.json").read_text(encoding="utf-8"))
        require(result == 2 and summary["audit"] == "RED" and summary["complete"] is False,
                "bad child did not persist incomplete RED summary")
        require(summary["cases"]["independent_review_case"]["audit"] == "RED", "bad child lost its RED case")
        message = summary["cases"]["independent_review_case"]["error"]
        expected_numeric_error = {
            "string_count": "counts.raw_df05: counts must be non-bool nonnegative integers",
            "boolean_count": "counts.raw_df05: counts must be non-bool nonnegative integers",
            "negative_count": "counts.raw_df05: counts must be non-bool nonnegative integers",
            "malformed_stats": "stats: expected count map",
            "string_stat": "stats: counts must be non-bool nonnegative integers"}
        if failure in expected_numeric_error:
            require(message == expected_numeric_error[failure], "numeric audit defect hit unrelated guard")
        negatives.append({"kind": "batch_child", "case": failure, "rejected": True, "exit_code": result,
                          "message": message})

    square = ((0, 0), (1, 0), (1, 1), (0, 1))
    def frame(step, left):
        return {"step": step, "geometry": [[1, i + 1, x, y] for i, (x, y) in enumerate(square)]
                + [[2, i + 5, x + left, y] for i, (x, y) in enumerate(square)], "raw_df05": [], "post_df06": []}
    previous, start, end = frame(1, 6), frame(2, 3), frame(3, 3)
    pg, sg, eg = [replay.snapshot.geometry_from_frame(value) for value in (previous, start, end)]
    result = replay.frame_result(start, sg, eg, pg, pd_edge_limit=0)
    prediction = replay.motion.motion_first_entrance(square, tuple((x + 3, y) for x, y in square), square, square)
    require(result["pairs"] == [] and prediction.exact_time == Fraction(2, 3), "prediction-scope counterexample changed")

    # Final artifacts are reread, never rewritten or assembled from partial runs.
    # This checks data/record integrity, not a second geometric implementation.
    completed_batches = {}
    for mode, folder, target in (("full", "full_replay_r4", 1810), ("frozen", "frozen_replay_r2", 450)):
        directory = EVIDENCE / folder
        summary_path = directory / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        validation_path = EVIDENCE / (mode + "_batch_revalidation.json")
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        require(summary["audit"] == "GREEN" and summary["complete"] is True and summary["steps"] == target,
                "final batch is not complete GREEN")
        require(validation["audit"] == "GREEN" and validation["complete"] is True and not validation["failures"],
                "final batch lacks GREEN revalidation")
        require(summary["code_hashes"] == code_start == validation["code_hashes"], "batch source hash drift")
        require(validation["driver_sha256"] == sha(ROOT / "tools/m4c_run_replays.py"), "batch revalidation driver drift")
        require(validation["summary_sha256"] == sha(summary_path), "batch revalidation summary binding drift")
        require(set(summary["cases"]) == set(replay.CASES) == set(validation["cases"]), "batch case inventory drift")
        case_records = {}
        for case in replay.CASES:
            row = batches.validate_case_files(directory, case, mode, code_start)
            audit_sha = sha(directory / case / "audit.json")
            require(row["pd_edge_limit"] == 0, "final batch retains a PD cap")
            require(summary["cases"][case]["audit_sha256"] == audit_sha == validation["cases"][case]["audit_sha256"],
                    "final case audit binding drift")
            require(row["normalized_sha256"] == validation["cases"][case]["normalized_sha256"], "final normalized binding drift")
            case_records[case] = {"steps": row["steps"], "audit_sha256": audit_sha,
                                  "normalized_sha256": row["normalized_sha256"]}
        require(sum(row["steps"] for row in case_records.values()) == target, "final batch step inventory drift")
        completed_batches[mode] = {"folder": folder, "steps": target, "cases": case_records,
                                   "summary_sha256": sha(summary_path), "revalidation_sha256": sha(validation_path),
                                   "driver_sha256": validation["driver_sha256"], "pd_cap": 0,
                                   "method": "read-only full case payload, source, terminal, normalized hash and row conservation revalidation"}

    command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider",
               "tests/test_m4c_replay.py", "tests/test_m4c_batch_publish.py", "-k",
               "(not frozen and not real_first_frame) or relative_output_path",
               "--basetemp", str(local_output(tmp / "pytest"))]
    completed = subprocess.run(command, cwd=ROOT, env=dict(os.environ), capture_output=True, text=True, encoding="utf-8")
    require(completed.returncode == 0, completed.stdout + completed.stderr)
    require(replay.code_hashes() == code_start, "production code changed during independent review")
    require(all(sha(ROOT / p) == h for p, h in extra_start.items()), "review dependency changed during review")
    evidence = {"schema": "eab.m4c-input-prediction-review.v2", "snapshot_utc": datetime.now(timezone.utc).isoformat(),
                "scope": "independent kinematics/input/prediction review; reviewer authored fast PD, not an independent PD review or G6",
                "status": "PASS_WITH_EXPLICIT_SCOPE_LIMIT", "full_intervals": full_count, "frozen_intervals": frozen_count,
                "geometry_rows": geometry_count, "cases": cases, "endpoint_sha256": sha(endpoint_path),
                "kinematics_audit_sha256": sha(EVIDENCE / "kinematics_audit.json"), "code_hashes": code_start,
                "additional_reviewed_hashes": extra_start, "negative_input_checks": negatives,
                "negative_input_check_count": len(negatives), "targeted_pytest": completed.stdout.strip(),
                "targeted_pytest_command": command, "targeted_pytest_exit_code": completed.returncode,
                "fast_pd_static_record_current": static_current,
                "fast_pd_static_violations": len(static["violations"]),
                "prediction_counterexample": {"previous_B_left": 6, "current_B_left": 3, "actual_next_B_left": 3,
                                              "legacy_tables_empty": True, "actual_candidate_pair_omitted": True,
                                              "predicted_contact_exact_time": "2/3"},
                "prediction_interpretation_required": "initial-separated actual-swept/legacy candidate conditional rate, not all-pair online forecast accuracy",
                "batch_numeric_schema_finding": {
                    "severity_at_discovery": "MAJOR",
                    "before_fix": "String-valued FIRST_COVER_MATCH was aggregated and persisted in a complete GREEN batch.",
                    "before_fix_evidence": "reports/codex/M4c_evidence/tmp/batch_malformed_counts_110618064755/summary.json",
                    "closure": "Fresh checks reject string/bool/negative counts and malformed/string-valued stats before aggregation.",
                    "complete_real_batch_artifacts_revalidated": True},
                "complete_batch_artifact_validation": completed_batches,
                "residual_domain_limits": ["No general nonzero-delta stability certificate.",
                                           "Endpoint chord is not a unique continuous DDA path.",
                                           "No generic accepted/rejected-attempt schema.",
                                           "Predicted false positives outside actual/legacy candidates are not evaluated."],
                "temporary_negative_inputs": str(tmp), "all_generated_probe_paths_inside_workspace_tmp": True,
                "full_replay_or_frozen_geometry_recomputed_by_this_review": False}
    (EVIDENCE / "review_inputs_prediction.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"INPUTS full={full_count} frozen={frozen_count} geometry={geometry_count}; negatives={len(negatives)}")
    print(completed.stdout.strip())


if __name__ == "__main__":
    main()
