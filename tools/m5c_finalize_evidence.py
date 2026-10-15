"""Audit complete four-shard execution against raw records and exported bytes."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M5c_evidence"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")


def log_last_line(record, inputs):
    assert record["exit_code"] == 0 and not record["process_timed_out"], "failed/timed-out process"
    path = Path(record["log"])
    inputs[str(path)] = digest(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines, "missing process log"
    assert lines[-1] == record["last_line"], "summary last line differs from original log"
    return lines[-1]


def executable_path(path):
    # Include root configuration (pyproject, pytest.ini, conftest, etc.).
    return "/" not in path or path.startswith(("src/", "tests/", "tools/", "fixtures/"))


def current_export_drift(manifest):
    paths = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT
    ).decode("utf-8").split("\0")
    current = {p for p in paths if p and executable_path(p) and (ROOT / p).is_file()}
    expected = {row["path"]: row["sha256"] for row in manifest if executable_path(row["path"])}
    drift = set(current) ^ set(expected)
    drift.update(p for p in current & set(expected) if digest(ROOT / p) != expected[p])
    return sorted(drift)


def audit(name):
    assert name and Path(name).name == name and name not in (".", ".."), "run name must be a single directory"
    summary_path = EVIDENCE / name / "summary.json"
    inputs = {str(summary_path): digest(summary_path)}
    summary = read(summary_path)
    assert summary["complete"] is True and summary["audit"] == "GREEN", "incomplete/RED suite is not publishable"
    assert len(summary["shards"]) == 4, "exactly four shards required"
    collected, calls, durations, details = [], [], {}, []
    for number, record in enumerate(summary["shards"], 1):
        execution_path = Path(summary["temp"]) / f"shard_{number}_execution.json"
        inputs[str(execution_path)] = digest(execution_path)
        data = read(execution_path)
        assert data["complete"] is True and data["exitstatus"] == 0
        assert all(r["outcome"] == "passed" for r in data["reports"]), "all setup/call/teardown must pass"
        phases = Counter((r["nodeid"], r["when"]) for r in data["reports"])
        expected = Counter((node, phase) for node in data["collected"] for phase in ("setup", "call", "teardown"))
        assert phases == expected, "each collected node needs exactly one setup, call and teardown"
        executed = [r["nodeid"] for r in data["reports"] if r["when"] == "call"]
        assert Counter(data["collected"]) == Counter(executed)
        for row in data["reports"]:
            assert row["duration"] >= 0, "negative execution duration"
            if row["when"] == "call":
                durations[row["nodeid"]] = row["duration"]
        assert record["execution_complete"] is True and record["node_sets_equal"] is True
        assert record["skip_count"] == 0
        assert record["dispatched"] == record["collected"] == record["executed"] == len(executed)
        nodes_path = Path(summary["temp"]) / f"shard_{number}_nodes.txt"
        inputs[str(nodes_path)] = digest(nodes_path)
        assert nodes_path.read_text(encoding="utf-8").splitlines() == data["collected"], "dispatch/collection order drift"
        collected.extend(data["collected"])
        calls.extend(executed)
        details.append(dict(shard=number, collected=len(data["collected"]), executed=len(executed),
                            last_line=log_last_line(record, inputs)))
    assert len(collected) == len(set(collected)) == len(calls) == summary["collected"]
    assert log_last_line(summary["static"], inputs) == "exact construction AST gate: 0 violation(s)"
    integrity_path = EVIDENCE / name / "export_integrity.json"
    inputs[str(integrity_path)] = digest(integrity_path)
    integrity = read(integrity_path)
    assert integrity["complete"] is True and not integrity["before_mismatches"] and not integrity["after_mismatches"]
    source = Path(summary["source"])
    assert Path(integrity["source"]).resolve() == source.resolve()
    manifest_path = Path(summary["manifest"])
    inputs[str(manifest_path)] = digest(manifest_path)
    manifest = read(manifest_path)
    assert len(manifest) == len({r["path"] for r in manifest}) == integrity["checked_files"]
    actual = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    assert actual == {r["path"] for r in manifest}, "export file set changed after execution"
    assert all(digest(source / r["path"]) == r["sha256"] for r in manifest), "export bytes changed after execution"
    assert all(digest(p) == value for p, value in inputs.items()), "audit input changed during read"
    return summary, collected, durations, details, inputs


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "final_suite"
    baseline, old, old_cost, _, old_inputs = audit("baseline_suite")
    final, nodes, cost, shards, inputs = audit(name)
    added, removed = sorted(set(nodes)-set(old)), sorted(set(old)-set(nodes))
    final_source = Path(final["source"])
    manifest = read(final["manifest"])
    drift = current_export_drift(manifest)
    assert not drift, "current code/tests/policy/fixtures/root config differ from executed export: " + repr(drift)
    assert sum(old_cost.values()) > 0
    performance = dict(controlled_host=False, baseline_call_seconds=sum(old_cost.values()),
                       final_call_seconds=sum(cost.values()), added_call_seconds=sum(cost[n] for n in added),
                       added_over_baseline=sum(cost[n] for n in added)/sum(old_cost.values()),
                       baseline_wall_seconds=baseline["elapsed_seconds"], final_wall_seconds=final["elapsed_seconds"],
                       note="Concurrent reviews and evidence runs; only added-node cost is the scoped gate overhead, not a controlled speed benchmark.")
    inputs.update(old_inputs)
    assert all(digest(p) == value for p, value in inputs.items()), "audit input changed before publication"
    write(EVIDENCE / "suite_delta.json", dict(added_count=len(added), removed_count=len(removed), added=added, removed=removed))
    write(EVIDENCE / "performance.json", performance)
    write(EVIDENCE / "execution_audit.json", dict(complete=True, audit="GREEN", run=name, collected=len(nodes),
          executed=len(nodes), skip_count=0, all_stages_passed=True, collected_equals_executed=True,
          shards=shards, static_last_line=final["static"]["last_line"], fresh_git_checkout=False,
          fresh_byte_export=str(final_source), executable_source_drift=drift,
          source_unchanged_during_execution=True, performance=performance, audit_input_hashes=inputs))
    print("M5C_EXECUTION_AUDIT_GREEN", len(nodes), "collected = executed; 0 skip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
