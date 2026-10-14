"""Reproducible M4c replay batch using only workspace-copied inputs."""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import gzip
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import m4c_motion_replay as replay

ROOT = replay.ROOT
INPUTS = ROOT / "reports/codex/M4c_evidence/tmp/kinematics_inputs"
FULL_STEPS = dict(zip(replay.CASES, (50, 100, 50, 50, 100, 100, 100, 100, 100, 100, 400, 100, 400, 30, 30)))


def _count_map(value, label, *, categories=False):
    replay.require(type(value) is dict, label+": expected count map")
    replay.require(all(type(k) is str and type(v) is int and v >= 0 for k, v in value.items()),
                   label+": counts must be non-bool nonnegative integers")
    if categories:
        replay.require(set(value) <= replay.CATEGORIES, label+": unknown category")


def _hash(value, label):
    replay.require(type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value),
                   label+": malformed SHA256")


def validate_audit_payload(result, case, code_hashes, expected_steps=None):
    """Typed ordinary-data schema, before aggregation can touch any value."""
    replay.require(type(result) is dict, "case audit is not an object")
    for field in ("counts", "secondary_counts"):
        table = result.get(field)
        replay.require(type(table) is dict and set(table) == set(replay.PHASES), field+": phase tables malformed")
        for phase in replay.PHASES:
            _count_map(table[phase], field+"."+phase, categories=True)
    _count_map(result.get("stats"), "stats")
    seconds = result.get("seconds")
    replay.require(type(seconds) in (int, float) and math.isfinite(seconds) and seconds >= 0, "seconds must be finite nonnegative number")
    replay.require(result.get("schema") == "eab.m4c-replay.v1" and result.get("complete") is True and result.get("audit") == "GREEN",
                   "case audit is not complete GREEN")
    replay.require(result.get("case") == case, "case identity mismatch")
    replay.require(result.get("code_hashes") == code_hashes, "case audit source hash mismatch")
    steps = result.get("steps")
    replay.require(type(steps) is int and steps > 0 and (expected_steps is None or steps == expected_steps), "case audit step count/type mismatch")
    replay.require(type(result.get("pd_edge_limit")) is int and result["pd_edge_limit"] >= 0, "PD cap type mismatch")
    inputs = result.get("input_hashes")
    replay.require(type(inputs) is dict and set(inputs) == {"snapshot", "terminal_source"}, "case audit input hashes malformed")
    for name, value in inputs.items():
        _hash(value, name)
    for name in ("frames_sha256", "normalized_sha256"):
        _hash(result.get(name), name)
    frames = result.get("frame_sha256")
    replay.require(type(frames) is list and len(frames) == steps, "case audit frame hashes missing")
    for value in frames:
        _hash(value, "frame_sha256")
    replay.require(replay.digest(frames) == result["frames_sha256"], "case frame-list digest mismatch")
    replay.require(type(result.get("examples")) is dict and type(result.get("partial")) is list
                   and all(type(v) is str for v in result["partial"]), "case audit explanatory fields malformed")


def validate_case_files(directory, case, mode, code_hashes, exit_code=0):
    """Read-only complete-case audit plus normalized/source byte binding."""
    result = json.loads((directory / case / "audit.json").read_text(encoding="utf-8"))
    validate_audit_payload(result, case, code_hashes, 30 if mode == "frozen" else FULL_STEPS.get(case))
    replay.require(exit_code == 0, "replay child exited nonzero")
    normalized = directory / case / "normalized.jsonl.gz"
    replay.require(replay.file_hash(normalized) == result["normalized_sha256"], "normalized artifact hash mismatch")
    source = INPUTS / case / "shadow.jsonl" if mode == "full" else ROOT / "fixtures/m4b_shadow" / (case+".jsonl.gz")
    terminal = INPUTS / case / "geom.csv" if mode == "full" else ROOT / "fixtures/m4c_motion/endpoints.json"
    replay.require(replay.file_hash(source) == result["input_hashes"]["snapshot"], "case source hash mismatch")
    replay.require(replay.file_hash(terminal) == result["input_hashes"]["terminal_source"], "case terminal source hash mismatch")
    counts = {p: Counter() for p in replay.PHASES}; secondary = {p: Counter() for p in replay.PHASES}; stats = Counter(); hashes = []
    with gzip.open(normalized, "rt", encoding="utf-8") as stream:
        for index, line in enumerate(stream, 1):
            frame = json.loads(line)
            replay.require(type(frame) is dict and type(frame.get("step")) is int and frame["step"] == index, "normalized step sequence mismatch")
            hashes.append(replay.digest(frame)); _count_map(frame.get("stats"), "normalized stats"); stats.update(frame["stats"])
            for phase in replay.PHASES:
                row = frame["phases"][phase]
                _count_map(row["counts"], "normalized primary counts", categories=True)
                _count_map(row["secondary_counts"], "normalized secondary counts", categories=True)
                replay.require(Counter(x["category"] for x in row["records"]) == row["counts"], "normalized primary row conservation mismatch")
                replay.require(Counter(x["secondary_category"] for x in row["records"] if x["secondary_category"] is not None) == row["secondary_counts"],
                               "normalized secondary row conservation mismatch")
                counts[phase].update(row["counts"]); secondary[phase].update(row["secondary_counts"])
    replay.require(hashes == result["frame_sha256"], "normalized frame hash sequence mismatch")
    replay.require({p: dict(v) for p, v in counts.items()} == result["counts"] and {p: dict(v) for p, v in secondary.items()} == result["secondary_counts"]
                   and dict(stats) == result["stats"], "normalized aggregate mismatch")
    return result


def verify_batch(directory, output):
    """Audit the entire SAME completed batch; never join partial executions."""
    before = replay.file_hash(directory / "summary.json")
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    current = replay.code_hashes(); failures = {}; cases = {}; counts = {p: Counter() for p in replay.PHASES}; secondary = {p: Counter() for p in replay.PHASES}; stats = Counter()
    replay.require(summary.get("complete") is True and summary.get("code_hashes") == current and set(summary.get("cases", {})) == set(replay.CASES),
                   "only complete current-source fifteen-case batches may be revalidated")
    replay.require(summary.get("mode") in ("full", "frozen"), "batch mode malformed")
    for case in replay.CASES:
        try:
            result = validate_case_files(directory, case, summary["mode"], current)
            replay.require(replay.file_hash(directory / case / "audit.json") == summary["cases"][case]["audit_sha256"], "summary case audit binding mismatch")
            cases[case] = {"steps": result["steps"], "audit_sha256": summary["cases"][case]["audit_sha256"], "normalized_sha256": result["normalized_sha256"]}
            for phase in replay.PHASES:
                counts[phase].update(result["counts"][phase]); secondary[phase].update(result["secondary_counts"][phase])
            stats.update(result["stats"])
        except Exception as exc:
            failures[case] = {"error_type": type(exc).__name__, "error": str(exc)}
    totals = {p: dict(v) for p, v in counts.items()}; secondary_totals = {p: dict(v) for p, v in secondary.items()}
    complete = not failures and totals == summary["counts"] and secondary_totals == summary["secondary_counts"] and dict(stats) == summary["stats"]
    complete = complete and sum(r["steps"] for r in cases.values()) == summary["steps"] == (1810 if summary["mode"] == "full" else 450)
    replay.require(replay.file_hash(directory / "summary.json") == before, "source summary changed during verification")
    output.parent.mkdir(parents=True, exist_ok=True)
    replay.require(not output.exists(), "revalidation output already exists")
    replay.write_json(output, {"schema": "eab.m4c-batch-revalidation.v1", "audit": "GREEN" if complete else "RED", "complete": complete,
                              "summary_sha256": before, "driver_sha256": replay.file_hash(Path(__file__)), "mode": summary["mode"],
                              "cases": cases, "failures": failures, "code_hashes": current, "counts": totals,
                              "secondary_counts": secondary_totals, "stats": dict(stats)})
    return 0 if complete else 2


def freeze_endpoints():
    """Bind each prefix's last endpoint to fully verified existing exports."""
    manifest = json.loads((ROOT / "fixtures/m4b_shadow/manifest.json").read_text(encoding="utf-8"))
    cases = {}
    for case in replay.CASES:
        source = INPUTS / case / "shadow.jsonl"
        csv_path = INPUTS / case / "geom.csv"
        _, full, _ = replay.snapshot.read_snapshot(source)
        replay.load_geometry_csv(csv_path, full)
        source_hash = replay.file_hash(source)
        require = replay.require
        require(source_hash == manifest["cases"][case]["source_sha256"], "copied full snapshot provenance mismatch")
        fixture = ROOT / "fixtures/m4b_shadow" / manifest["cases"][case]["file"]
        _, prefix, _ = replay.snapshot.read_snapshot(fixture)
        require(prefix == full[:30], "frozen prefix differs from verified full snapshot")
        points = {}
        with csv_path.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                if row["kind"] == "step30":
                    points[int(row["idx"])] = tuple(replay.scalar_rational(row[k]) for k in ("x", "y"))
        geometry = [[b, v, *points[v]] for b, v, _, _ in prefix[-1]["geometry"]]
        cases[case] = {"endpoint_step": 31, "geometry": geometry, "geometry_sha256": replay.digest(geometry),
                       "snapshot_sha256": replay.file_hash(fixture), "start_geometry_sha256": replay.digest(prefix[-1]["geometry"]),
                       "full_snapshot_sha256": source_hash, "geometry_csv_sha256": replay.file_hash(csv_path),
                       "origin": "existing geom.csv step30; all complete-run starts cross-checked against shadow"}
    output = ROOT / "fixtures/m4c_motion/endpoints.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    replay.write_json(output, {"schema": "eab.m4c-endpoints.v1", "cases": cases})
    print(output)


def run_batch(mode, out, jobs):
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    initial_code = replay.code_hashes()
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8",
           "TEMP": str(ROOT / "reports/codex/M4c_evidence/tmp"), "TMP": str(ROOT / "reports/codex/M4c_evidence/tmp")}
    def run(case):
        if mode == "full":
            source = INPUTS / case / "shadow.jsonl"
            extra = ["--geometry-csv", str(INPUTS / case / "geom.csv")]
        else:
            source = ROOT / "fixtures/m4b_shadow" / (case+".jsonl.gz")
            extra = ["--endpoint-file", str(ROOT / "fixtures/m4c_motion/endpoints.json")]
        command = [sys.executable, "-X", "utf8", str(ROOT / "tools/m4c_motion_replay.py"), str(source),
                   *extra, "--case", case, "--pd-edge-limit", "0", "--out", str(out / case)]
        try:
            result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, encoding="utf-8", errors="replace")
        except OSError as exc:
            (out / (case+".log")).write_text("REPLAY_LAUNCH_RED "+str(exc)+"\n", encoding="utf-8")
            return case, 127, command
        (out / (case+".log")).write_text(result.stdout+result.stderr, encoding="utf-8")
        return case, result.returncode, command
    completed = {}
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = [pool.submit(run, case) for case in replay.CASES]
        for future in as_completed(futures):
            case, status, command = future.result()
            completed[case] = {"exit_code": status, "command": command}
            replay.write_json(out / "batch_progress.json", {"complete": False, "mode": mode, "completed": completed,
                                                            "code_hashes": initial_code})
            print(case, status, flush=True)
    counts = {p: Counter() for p in replay.PHASES}; secondary = {p: Counter() for p in replay.PHASES}; stats = Counter(); summaries = {}
    complete = all(r["exit_code"] == 0 for r in completed.values()) and replay.code_hashes() == initial_code
    for case in replay.CASES:
        path = out / case / "audit.json"
        try:
            result = validate_case_files(out, case, mode, initial_code, completed[case]["exit_code"])
        except Exception as exc:
            complete = False
            summaries[case] = {"audit": "RED", "complete": False, "exit_code": completed[case]["exit_code"],
                               "error_type": type(exc).__name__, "error": str(exc), "audit_path": str(path)}
            continue
        for phase in counts:
            counts[phase].update(result["counts"][phase])
            secondary[phase].update(result["secondary_counts"][phase])
        stats.update(result["stats"])
        summaries[case] = {k: result[k] for k in ("steps", "counts", "secondary_counts", "stats", "seconds", "input_hashes", "frames_sha256", "normalized_sha256")}
        summaries[case]["audit_sha256"] = replay.file_hash(path)
    summary = {"schema": "eab.m4c-batch.v1", "audit": "GREEN" if complete else "RED", "complete": complete, "mode": mode, "cases": summaries,
               "steps": sum(r.get("steps", 0) for r in summaries.values()), "code_hashes": initial_code,
               "counts": {p: dict(sorted(v.items())) for p, v in counts.items()}, "stats": dict(sorted(stats.items())),
               "secondary_counts": {p: dict(sorted(v.items())) for p, v in secondary.items()},
               "wall_seconds": time.perf_counter()-started, "jobs": jobs}
    replay.write_json(out / "summary.json", summary)
    replay.write_json(out / "batch_progress.json", {"complete": complete, "summary_sha256": replay.file_hash(out / "summary.json")})
    if mode == "frozen" and complete:
        expected = {"schema": "eab.m4c-frozen.v1", "cases": {}}
        for case in replay.CASES:
            result = json.loads((out / case / "audit.json").read_text(encoding="utf-8"))
            expected["cases"][case] = {k: result[k] for k in ("steps", "counts", "secondary_counts", "stats", "input_hashes", "frame_sha256", "frames_sha256")}
            expected["cases"][case]["normalized_file"] = str((out / case / "normalized.jsonl.gz").relative_to(ROOT)).replace("\\", "/")
            expected["cases"][case]["normalized_sha256"] = result["normalized_sha256"]
        replay.write_json(ROOT / "fixtures/m4c_motion/expected.json", expected)
    print("BATCH_COMPLETE" if complete else "BATCH_INCOMPLETE", summary["steps"], flush=True)
    return 0 if complete else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("full", "frozen", "freeze-endpoints", "verify-batch"))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--batch", type=Path)
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    if args.mode == "freeze-endpoints":
        freeze_endpoints(); return 0
    if args.mode == "verify-batch":
        replay.require(args.batch is not None and args.out is not None, "verify-batch requires --batch and --out")
        return verify_batch(args.batch, args.out)
    replay.require(args.out is not None, "--out is required for replay")
    return run_batch(args.mode, args.out, args.jobs)


if __name__ == "__main__":
    raise SystemExit(main())
