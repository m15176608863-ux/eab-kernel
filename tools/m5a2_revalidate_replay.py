"""Reexecute all 450 frozen M5a frames after M5a2 kernel changes.

Four fresh child processes run production replay_case (never run_batch, whose
TEMP points to M5a). Recursive comparison admits only an exactly equal rigid
first-time certificate representation change; every other JSON leaf is exact.
The optional equality comparison uses tests/m5a_independent_oracle, not the
production polynomial/root primitives. Original fixtures are never rewritten.
An interrupted or changed-source run is invalid and must use a fresh name.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools"), str(ROOT / "tests")]
import m5a_se2_replay as replay
from m5a_independent_oracle import certificate_root, compare

EVIDENCE = ROOT / "reports/codex/M5a2_evidence"
MANIFEST = ROOT / "fixtures/m5a2/revalidation.json"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def compare_rows(actual, expected, path, representation_changes):
    """Compare every field; normalization is confined to equal first times."""
    if actual == expected:
        return
    if path.endswith(".rigid.time") and isinstance(actual, dict) and isinstance(expected, dict):
        require(compare(certificate_root(actual), certificate_root(expected)) == 0,
                "revalidation exact first-time mismatch: "+path)
        representation_changes.append(path)
        return
    if isinstance(actual, dict) and isinstance(expected, dict):
        require(set(actual) == set(expected), "revalidation dictionary keys changed: "+path)
        for key in actual:
            compare_rows(actual[key], expected[key], path+"."+key, representation_changes)
        return
    if isinstance(actual, list) and isinstance(expected, list):
        require(len(actual) == len(expected), "revalidation list length changed: "+path)
        for index, (a, b) in enumerate(zip(actual, expected)):
            compare_rows(a, b, path+"["+str(index)+"]", representation_changes)
        return
    raise AssertionError("revalidation semantic field mismatch: "+path+" "+repr(actual)+" != "+repr(expected))


def inputs():
    names = ["fixtures/m5a_se2/expected.json", "fixtures/m4c_motion/endpoints.json"]
    for case in replay.CASES:
        names.extend(("fixtures/m5a_se2/"+case+".jsonl.gz", "fixtures/m4b_shadow/"+case+".jsonl.gz",
                      "reports/codex/M4c_evidence/fix_frozen_replay/"+case+"/audit.json",
                      "reports/codex/M4c_evidence/fix_frozen_replay/"+case+"/normalized.jsonl.gz"))
    return {name: replay.file_hash(ROOT / name) for name in names}


def tool_hashes():
    return {name: replay.file_hash(ROOT / name) for name in (
        "tools/m5a2_revalidate_replay.py", "tests/m5a_independent_oracle.py")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="revalidation_r1")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--case-timeout", type=int, default=3600)
    args = parser.parse_args()
    require(1 <= args.jobs <= 4, "one through four workers required")
    require(Path(args.name).name == args.name and args.name not in (".", ".."), "fresh run name required")
    out = EVIDENCE / "tmp" / args.name
    require(not out.exists() and not MANIFEST.exists(), "fresh run and absent manifest required; no partial reuse")
    out.mkdir(parents=True)
    started = time.perf_counter()
    sources, prior_inputs, scripts = replay.code_hashes(), inputs(), tool_hashes()
    completed = {}
    def progress(**extra):
        replay.write_json(out / "progress.json", {"complete": False, "interruption_invalidates": True,
            "completed": completed, "code_hashes": sources, **extra})
    progress()
    temporary = EVIDENCE / "tmp"
    env = dict(os.environ, TEMP=str(temporary), TMP=str(temporary), PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    def run(case):
        command = [sys.executable, "-X", "utf8", str(ROOT / "tools/m5a_se2_replay.py"), "case",
                   "--mode", "frozen", "--case", case, "--out", str(out / case)]
        try:
            result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                    encoding="utf-8", errors="replace", timeout=args.case_timeout)
            output, code = result.stdout+result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            output, code = "CASE_TIMEOUT: nontermination makes this complete batch invalid", 124
        (out / (case+".log")).write_text(output, encoding="utf-8")
        return case, code
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for future in as_completed([pool.submit(run, case) for case in replay.CASES]):
            case, status = future.result()
            completed[case] = status
            progress()
            print("M5A2_REVALIDATE", case, status, flush=True)
    require(all(v == 0 for v in completed.values()) and len(completed) == 15, "case failure invalidates whole revalidation")
    require(sources == replay.code_hashes() and prior_inputs == inputs() and scripts == tool_hashes(),
            "source/input change invalidates whole revalidation")
    cases, total_changes = {}, []
    for case in replay.CASES:
        audit = json.loads((out / case / "audit.json").read_text(encoding="utf-8"))
        require(audit["complete"] and audit["steps"] == 30 and audit["code_hashes"] == sources, "case completion binding")
        path = out / case / "normalized.jsonl.gz"
        require(audit["normalized_sha256"] == replay.file_hash(path), "case output hash binding")
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            rows = list(map(json.loads, stream))
        with gzip.open(ROOT / "fixtures/m5a_se2" / (case+".jsonl.gz"), "rt", encoding="utf-8") as stream:
            old = list(map(json.loads, stream))
        require(len(rows) == len(old) == 30, "450-frame revalidation shape")
        require([replay.digest(row) for row in rows] == audit["frame_sha256"], "new frame digest binding")
        changes = []
        for a, b in zip(rows, old):
            compare_rows(a, b, case+".step"+str(a["step"]), changes)
        total_changes.extend(changes)
        cases[case] = {"complete": True, "steps": 30, "all_semantic_fields_equal": True,
                       "time_representation_changes": changes, "normalized_sha256": audit["normalized_sha256"],
                       "old_normalized_sha256": prior_inputs["fixtures/m5a_se2/"+case+".jsonl.gz"],
                       "counts": audit["counts"], "stats": audit["stats"], "seconds": audit["seconds"]}
    require(prior_inputs == inputs() and sources == replay.code_hashes() and scripts == tool_hashes(),
            "post-comparison source/input binding")
    summary = {"schema": "eab.m5a2-revalidation.v1", "complete": True, "audit": "GREEN", "steps": 450,
        "cases": cases, "code_hashes": sources, "input_hashes": prior_inputs, "tool_hashes": scripts,
        "prior_code_hashes": json.loads((ROOT / "fixtures/m5a_se2/expected.json").read_text(encoding="utf-8"))["code_hashes"],
        "all_historical_fixture_bytes_unchanged": True, "all_semantic_fields_equal": True,
        "allowed_difference": "rigid.time certificate representation only, independently exactly equal",
        "time_representation_changes": total_changes, "seconds": time.perf_counter()-started,
        "run_directory": out.relative_to(ROOT).as_posix(), "jobs": args.jobs,
        "scope": "15 x 30 frozen prefixes, not the full 1810-step historical run"}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    replay.write_json(MANIFEST, summary)
    replay.write_json(out / "summary.json", summary)
    replay.write_json(out / "progress.json", {"complete": True, "steps": 450, "manifest_sha256": replay.file_hash(MANIFEST)})
    print("M5A2_REVALIDATION_GREEN steps=450 seconds="+str(summary["seconds"]), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
