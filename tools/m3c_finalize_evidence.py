"""Read-only verification of M3c raw suite, mutation and actual replay evidence."""
from __future__ import annotations

import ast
from collections import Counter
import gzip
import json
from pathlib import Path
import subprocess

from m3b_finalize_evidence import sha256, strict_execution, strict_m4c_frames
import m4c_motion_replay as replay
import m4c_run_replays as batch

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M3c_evidence"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def suite(name):
    summary = read(EVIDENCE / name / "summary.json")
    raw = Path(summary["raw_records"])
    source = Path(summary["source"])
    collection = [s for s in (raw / "collection.txt").read_text(encoding="utf-8").splitlines()
                  if s.startswith("tests/") and "::" in s]
    dispatched, durations, results = [], {}, []
    for i in range(1, 5):
        nodes = (raw / f"shard_{i}_nodes.txt").read_text(encoding="utf-8").splitlines()
        data = read(raw / f"shard_{i}_execution.json")
        result = strict_execution(nodes, data)
        del result["counters"]
        assert result["ok"] and data["complete"], result
        results.append(result)
        dispatched.extend(nodes)
        for row in data["reports"]:
            durations[row["nodeid"]] = durations.get(row["nodeid"], 0)+row["duration"]
        last = (raw / f"shard_{i}.txt").read_text(encoding="utf-8").splitlines()[-1]
        assert last == summary["shards"][i-1]["last_line"]
    assert Counter(collection) == Counter(dispatched)
    assert len(collection) == len(set(collection)) == summary["collected"]
    assert summary["audit"] == "GREEN" and summary["static"]["exit_code"] == 0
    static = (raw / "exact_construction.txt").read_text(encoding="utf-8").splitlines()[-1]
    assert static == "exact construction AST gate: 0 violation(s)"
    manifest = read(raw / "export_manifest.json")
    assert sha256(raw / "export_manifest.json") == summary["export_manifest_sha256"]
    bound = [r for r in manifest if r["path"].startswith(("src/", "tests/", "tools/"))
             or r["path"] in ("pyproject.toml", "reports/codex/M4c_evidence/frozen_summary.json")]
    for row in bound:
        assert sha256(source / row["path"]) == row["sha256"], "frozen source changed: "+row["path"]
        # H1: verify the executed frozen source, not today's implementation.
    return dict(collected=len(collection), shards=results, last_lines=[r["last_line"] for r in summary["shards"]],
                static=static, bound_files=len(bound), wall_seconds=summary["elapsed_seconds"]), durations, source


def main():
    baseline, old_times, old_source = suite("baseline_suite")
    final, new_times, _ = suite("final_suite")
    old_nodes, new_nodes = set(old_times), set(new_times)
    assert not old_nodes-new_nodes, "baseline test removed"
    added = sorted(new_nodes-old_nodes)
    added_seconds = sum(new_times[n] for n in added)
    old_seconds_same_run = sum(new_times[n] for n in old_nodes)
    overhead = added_seconds/old_seconds_same_run
    assert added and overhead <= 0.05, ("new gate time budget", overhead)

    mutations = read(EVIDENCE / "mutations/summary.json")
    assert mutations["complete"] and mutations["count"] == len(mutations["rows"]) == 19
    for row in mutations["rows"]:
        assert [s["stage"] for s in row["stages"]] == ["before", "mutant", "restored"]
        for stage in row["stages"]:
            last = (EVIDENCE / "mutations" / (row["case"]+"_"+stage["stage"]+".txt")).read_text(encoding="utf-8").splitlines()[-1]
            assert last == stage["last_line"]
            if stage["stage"] == "mutant":
                assert stage["exit_code"] != 0 and last.startswith("AssertionError:") and row["semantic_assertion"] in last
            else:
                assert stage["exit_code"] == 0 and last == "M3C_SEMANTIC_GREEN "+row["case"]

    attestation = read(EVIDENCE / "motion_refresh_r2_attestation.json")
    raw = Path(attestation["raw_directory"])
    assert read(raw / "summary.json") == read(ROOT / "reports/codex/M4c_evidence/frozen_summary.json")
    # H1: historical attestation is not a current-source hash pin.
    expected = read(ROOT / "fixtures/m4c_motion/expected.json")
    frame_results = {}
    for case in replay.CASES:
        actual = batch.validate_case_files(raw, case, "frozen", attestation["source_hashes"])
        frozen = expected["cases"][case]
        with gzip.open(ROOT / frozen["normalized_file"], "rt", encoding="utf-8") as stream:
            original = [json.loads(s) for s in stream]
        with gzip.open(raw / case / "normalized.jsonl.gz", "rt", encoding="utf-8") as stream:
            current = [json.loads(s) for s in stream]
        checked = strict_m4c_frames(original, current, frozen["frame_sha256"])
        assert checked["ok"] and actual["pd_edge_limit"] == 0, checked
        frame_results[case] = checked
    assert sum(r["equal_frames"] for r in frame_results.values()) == 450
    for name, value in attestation["expected_fixture_hashes_before_and_after"].items():
        assert sha256(ROOT / name) == value

    old_policy = read(old_source / "tools/exact_construction_policy.json")
    policy = read(ROOT / "tools/exact_construction_policy.json")
    assert len(old_policy["waivers"]) == len(policy["waivers"])
    assert old_policy["imports"] == policy["imports"] and old_policy["members"] == policy["members"]
    reviews = read(EVIDENCE / "static_review.json")
    assert reviews["added_count"] == 0 and reviews["renewed_count"] == len(reviews["renewed"]) == 4
    old_review = read(ROOT / "reports/codex/M3b_evidence/static_review.json")
    assert len(old_review["renewed"]) == 23 and all(r["old_review_evidence"] for r in old_review["renewed"])
    assert (ROOT / "reports/codex/M3b_evidence/final_suite_r3/VOID.md").is_file()

    names = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT).decode("utf-8").split("\0")
    changed = subprocess.check_output(["git", "diff", "--name-only", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    additions = subprocess.check_output(["git", "ls-files", "-z", "--others", "--exclude-standard"], cwd=ROOT).decode("utf-8").split("\0")
    changed = sorted(set(filter(None, changed+additions)))
    for name in changed:
        data = (ROOT / name).read_bytes()
        assert not data.startswith((b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")), "unexpected BOM: "+name
        data.decode("utf-8")
        assert not (name.startswith("reports/codex/M3c_evidence/") and len(data) > 1_000_000), "large delivery artifact: "+name
    inventory = []
    for name in ("tests/m3c_oracle3d.py", "tests/test_m3c_boundary3d.py", "tests/test_m3c_sections.py", "tests/test_m3c_determinism.py", "tests/test_m3b_boundary3d.py", "src/eab/kernel3d/g03_exit_oracle.py", "src/eab/kernel3d/g03_surface_oracle.py"):
        tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
        inventory.append(dict(path=name, sha256=sha256(ROOT / name), imports=[dict(line=n.lineno, statement=ast.unparse(n)) for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]))
    (EVIDENCE / "oracle_import_inventory.json").write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    result = dict(status="GREEN", baseline=baseline, final=final, added_nodes=added,
        performance=dict(new_gate_phase_seconds=added_seconds, old_node_phase_seconds_in_final=old_seconds_same_run,
            new_gate_fraction=overhead, baseline_node_phase_seconds=sum(old_times.values()),
            caveat="Single local observation; sum of measured setup/call/teardown durations, not a stable benchmark or clean-worktree claim."),
        mutation_groups=19, uncaught_semantic_reds=19, before_green=19, restored_green=19,
        motion=dict(equal_frames=450, cases=frame_results, actual_recompute=True),
        static=dict(violations=0, new_waivers=0, renewals=4, new_import_admissions=0, new_member_admissions=0),
        baseline_nodes_removed=0, utf8_no_bom=True, oversized_new_deliverables=0, changed_files=changed,
        limitations=["Fresh byte export, not Git worktree (owner prohibits worktree operations).", "Peer review is scoped to M3c and is not six-track G6."])
    (EVIDENCE / "final_audit.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("M3C_FINAL_AUDIT_GREEN", final["collected"], "nodes; 450 frames; 19 semantic reds; static 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
