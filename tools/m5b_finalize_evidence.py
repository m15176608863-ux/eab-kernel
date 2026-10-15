"""Audit complete four-shard execution and newly added test cost, without reruns."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M5b_evidence"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def audit(name):
    summary = read(EVIDENCE / name / "summary.json")
    assert summary["complete"] and summary["audit"] == "GREEN", "incomplete/RED suite is not publishable"
    collected, calls, durations = [], [], {}
    details = []
    for number in range(1, 5):
        data = read(Path(summary["temp"]) / f"shard_{number}_execution.json")
        assert data["complete"] and data["exitstatus"] == 0
        assert all(r["outcome"] == "passed" for r in data["reports"]), "all setup/call/teardown must pass"
        executed = [r["nodeid"] for r in data["reports"] if r["when"] == "call"]
        assert Counter(data["collected"]) == Counter(executed)
        for row in data["reports"]:
            if row["when"] == "call":
                durations[row["nodeid"]] = row["duration"]
        collected.extend(data["collected"])
        calls.extend(executed)
        details.append(dict(shard=number, collected=len(data["collected"]), executed=len(executed),
                            last_line=summary["shards"][number-1]["last_line"]))
    assert len(collected) == len(set(collected)) == len(calls) == summary["collected"]
    integrity = read(EVIDENCE / name / "export_integrity.json")
    assert not integrity["before_mismatches"] and not integrity["after_mismatches"]
    return summary, collected, durations, details


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "final_r1"
    baseline, old, old_cost, _ = audit("baseline_r1")
    final, nodes, cost, shards = audit(name)
    added, removed = sorted(set(nodes)-set(old)), sorted(set(old)-set(nodes))
    final_source = Path(final["source"])
    manifest = read(final["manifest"])
    drift = []
    for row in manifest:
        path = row["path"]
        if not path.startswith(("src/", "tests/", "tools/", "fixtures/")):
            continue
        current = ROOT / path
        if not current.exists() or hashlib.sha256(current.read_bytes()).hexdigest() != row["sha256"]:
            drift.append(path)
    assert not drift, "code/tests/policy/fixtures differ from actually executed fresh export"
    performance = dict(controlled_host=False, baseline_call_seconds=sum(old_cost.values()),
                       final_call_seconds=sum(cost.values()), added_call_seconds=sum(cost[n] for n in added),
                       added_over_baseline=sum(cost[n] for n in added)/sum(old_cost.values()),
                       baseline_wall_seconds=baseline["elapsed_seconds"], final_wall_seconds=final["elapsed_seconds"],
                       note="Concurrent reviews and evidence runs; only added-node cost is the scoped gate overhead, not a controlled speed benchmark.")
    write(EVIDENCE / "suite_delta.json", dict(added_count=len(added), removed_count=len(removed), added=added, removed=removed))
    write(EVIDENCE / "performance.json", performance)
    write(EVIDENCE / "execution_audit.json", dict(complete=True, audit="GREEN", run=name, collected=len(nodes),
          executed=len(nodes), skip_count=0, all_stages_passed=True, collected_equals_executed=True,
          shards=shards, static_last_line=final["static"]["last_line"], fresh_git_checkout=False,
          fresh_byte_export=str(final_source), executable_source_drift=drift,
          source_unchanged_during_execution=True, performance=performance))
    print("M5B_EXECUTION_AUDIT_GREEN", len(nodes), "collected = executed; 0 skip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
