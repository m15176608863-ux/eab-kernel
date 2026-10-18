"""Check complete M4c delivery evidence; never promotes unfinished runs."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M4c_evidence"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", required=True)
    parser.add_argument("--frozen", required=True)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--mutations", required=True)
    args = parser.parse_args()
    full = read(EVIDENCE / args.full / "summary.json")
    frozen = read(EVIDENCE / args.frozen / "summary.json")
    for value, steps in ((full, 1810), (frozen, 450)):
        assert value["complete"] and value["steps"] == steps and len(value["cases"]) == 15
        assert value["stats"].get("pd_not_evaluated_resource_pairs", 0) == 0
        # H1: historical replay source identity is metadata; fixed first-frame
        # semantic tests execute current code without requiring byte identity.
    for name, directory in (("full_batch_revalidation.json", args.full),
                            ("frozen_batch_revalidation.json", args.frozen)):
        checked = read(EVIDENCE / name)
        assert checked["complete"] and checked["audit"] == "GREEN" and not checked["failures"]
        assert checked["summary_sha256"] == digest(EVIDENCE / directory / "summary.json")
        # H1: historical driver version is not a current-source pin.
    reproduced = read(EVIDENCE / "minimal_examples_reproduced.json")
    assert reproduced["complete"] and reproduced["audit"] == "GREEN"
    assert reproduced["source_sha256"] == digest(EVIDENCE / "minimal_examples.json")
    recount = read(EVIDENCE / "review_probes/summary_artifacts.json")
    assert recount["complete"] and recount["steps"] == 1810
    assert recount["four_questions_sha256"] == digest(EVIDENCE / "four_questions.json")
    assert recount["minimal_examples_sha256"] == digest(EVIDENCE / "minimal_examples.json")
    assert all(row["steps"] == 30 for row in frozen["cases"].values())
    suite = read(EVIDENCE / args.suite / "summary.json")
    assert suite["complete"] and suite["audit"] == "GREEN"
    assert all(s["exit_code"] == 0 and s["execution_complete"] and s["node_sets_equal"]
               and s["skip_count"] == 0 for s in suite["shards"])
    assert sum(s["executed"] for s in suite["shards"]) == suite["collected"]
    assert suite["static"]["exit_code"] == 0
    policy_path = "tools/exact_construction_policy.json"
    original_policy = subprocess.check_output(["git", "show", "HEAD:"+policy_path], cwd=ROOT)
    assert original_policy == (ROOT / policy_path).read_bytes(), "construction policy exemptions changed"
    waiver_count = len(read(ROOT / policy_path)["waivers"])
    export = read(EVIDENCE / args.suite / "export_manifest.json")
    verified_export_paths = []
    for row in export:
        if row["path"].startswith("fixtures/"):
            assert digest(ROOT / row["path"]) == row["sha256"], ("tested file changed", row["path"])
            verified_export_paths.append(row["path"])
    mutations = read(EVIDENCE / args.mutations / "summary.json")
    assert mutations["complete"] and mutations["audit"] == "GREEN" and len(mutations["rows"]) == 6
    assert all(row["killed_at_expected_check"] for row in mutations["rows"])
    # H1: historical mutation source inventory is not rebound to current code.
    durations = Counter()
    per_shard_new = []
    for i in range(1, 5):
        record = read(EVIDENCE / args.suite / f"shard_{i}_execution.json")
        total_new = 0
        for row in record["reports"]:
            if row["when"] == "call":
                durations["all_test_call_seconds"] += row["duration"]
                if row["nodeid"].startswith("tests/test_m4c_"):
                    durations["m4c_test_call_seconds"] += row["duration"]
                    durations["m4c_nodes"] += 1
                    total_new += row["duration"]
        per_shard_new.append(total_new)
    durations["m4c_call_fraction"] = durations["m4c_test_call_seconds"] / durations["all_test_call_seconds"]
    paths = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    paths += subprocess.check_output(["git", "diff", "--name-only", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    manifest = []
    no_bom_text = []
    for name in sorted(set(filter(None, paths))):
        path = ROOT / name
        if not path.is_file() or path.name in ("artifact_manifest.json", "delivery_audit.json"):
            continue
        raw = path.read_bytes()
        if path.suffix in (".md", ".py", ".json", ".txt", ".csv", ".log", ".xml", ".jsonl") or path.name == ".gitignore":
            assert not raw.startswith(b"\xef\xbb\xbf"), ("UTF8 BOM", name)
            raw.decode("utf-8")
            no_bom_text.append(name)
        assert len(raw) <= 1_000_000 or path.suffix == ".gz", ("large tracked evidence", name, len(raw))
        manifest.append(dict(path=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    write(EVIDENCE / "artifact_manifest.json", manifest)
    write(EVIDENCE / "delivery_audit.json", dict(
        schema="eab.m4c-delivery.v1", complete=True, audit="GREEN",
        full_steps=1810, frozen_steps=450, suite_nodes=suite["collected"], skip_count=0,
        full_run=args.full, frozen_run=args.frozen, suite_run=args.suite, mutation_run=args.mutations,
        final_lines=[s["last_line"] for s in suite["shards"]],
        static_last_line=suite["static"]["last_line"],
        construction_waivers=waiver_count, construction_waiver_increment=0,
        tested_file_hashes_verified=len(verified_export_paths),
        changed_utf8_no_bom_files=len(no_bom_text),
        performance=dict(durations, per_shard_m4c_call_seconds=per_shard_new),
        baseline="Historical M3 only; not identical-byte baseline; no strict before-after percentage claim",
        milestone_status="PARTIAL; see report for nonzero-delta certification and independent G6 limitations",
        environment_deviation="See environment_deviations.json; this is not a claim of zero out-of-tree temporary writes"))
    print("M4C_DELIVERY_AUDIT_GREEN", suite["collected"], "nodes; 1810+450 replay intervals; 0 skip")


if __name__ == "__main__":
    main()
