"""Audit four-shard identity, immutable policy/provenance, and delivery bytes."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M5a2_evidence"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8")


def suite(name):
    summary = read(EVIDENCE / name / "summary.json")
    assert summary["audit"] == "GREEN" and summary["complete"]
    temp = Path(summary["temp"])
    collected = [line for line in (temp / "collection.txt").read_text(encoding="utf-8").splitlines()
                 if line.startswith("tests/") and "::" in line]
    executed, dispatched, actual, rows = [], [], [], []
    total_time = new_time = 0
    for i, result in enumerate(summary["shards"], 1):
        wanted = (temp / f"shard_{i}_nodes.txt").read_text(encoding="utf-8").splitlines()
        record = read(temp / f"shard_{i}_execution.json")
        calls = [r for r in record["reports"] if r["when"] == "call"]
        ids = [r["nodeid"] for r in calls]
        assert record["complete"] and record["exitstatus"] == 0
        assert Counter(wanted) == Counter(record["collected"]) == Counter(ids)
        assert all(r["outcome"] == "passed" for r in record["reports"])
        dispatched += wanted; actual += record["collected"]; executed += ids
        total_time += sum(r["duration"] for r in calls)
        new_time += sum(r["duration"] for r in calls if r["nodeid"].startswith("tests/test_m5a2_"))
        rows.append(dict(shard=i, collected=len(ids), executed=len(ids), last_line=result["last_line"],
                         execution_sha256=digest(temp / f"shard_{i}_execution.json")))
    assert len(collected) == len(set(collected))
    assert Counter(collected) == Counter(dispatched) == Counter(actual) == Counter(executed)
    return dict(audit="GREEN", complete=True, collected=len(collected), executed=len(executed),
                skip_count=0, call_seconds=total_time, new_gate_call_seconds=new_time,
                wall_seconds=summary["elapsed_seconds"], shards=rows, static=summary["static"],
                source=summary["source"], manifest=summary["manifest"], temp=str(temp), fresh_git_checkout=False)


def main():
    final = suite(sys.argv[1] if len(sys.argv) > 1 else "final_suite_r3")
    baseline = suite("baseline_suite_r2")
    write(EVIDENCE / "node_identity_audit.json", final)
    write(EVIDENCE / "performance.json", dict(baseline=baseline, final=final,
          new_gate_fraction_of_baseline=final["new_gate_call_seconds"]/baseline["call_seconds"],
          call_ratio=final["call_seconds"]/baseline["call_seconds"],
          wall_ratio=final["wall_seconds"]/baseline["wall_seconds"], controlled_host=False,
          limitation="Concurrent work on the shared host; new-gate cost is measured, not a controlled total regression benchmark."))
    original = json.loads(subprocess.check_output(["git", "show", "HEAD:tools/exact_construction_policy.json"], cwd=ROOT))
    policy = read(ROOT / "tools/exact_construction_policy.json")
    assert len(original["waivers"]) == 3220 and policy["waivers"][:3220] == original["waivers"]
    assert all(policy[key] == value for key, value in original.items() if key != "waivers")
    old_provenance = json.loads(subprocess.check_output(["git", "show", "HEAD:fixtures/PROVENANCE.json"], cwd=ROOT))
    provenance = read(ROOT / "fixtures/PROVENANCE.json")
    new_entries = [row for row in provenance["entries"] if row["dest"].startswith("m5a2/")]
    assert len(new_entries) == 1
    assert [row for row in provenance["entries"] if not row["dest"].startswith("m5a2/")] == old_provenance["entries"]
    assert all(digest(ROOT / "fixtures" / row["dest"]) == row["sha256"] for row in new_entries)
    changed = set(filter(None, (git("diff", "--name-only", "-z") + git("ls-files", "--others", "--exclude-standard", "-z")).split("\0")))
    errors, artifacts = [], []
    for name in sorted(changed):
        path = ROOT / name
        if not path.is_file() or name == "reports/codex/M5a2_evidence/artifact_manifest.json":
            continue
        raw = path.read_bytes()
        if path.suffix in {".py", ".md", ".json", ".jsonl", ".txt", ".log"}:
            try:
                raw.decode("utf-8")
                if raw.startswith(b"\xef\xbb\xbf"):
                    errors.append(name+": BOM")
            except UnicodeDecodeError:
                errors.append(name+": not UTF-8")
        if name.startswith("reports/codex/M5a2_evidence/") and len(raw) > 1_000_000:
            errors.append(name+": oversized submit-candidate evidence")
        artifacts.append(dict(path=name, bytes=len(raw), sha256=digest(path)))
    frozen = read(Path(final["manifest"]))
    source = Path(final["source"])
    from m5a2_run_gates import export_mismatches
    executed_mismatches = export_mismatches(source, frozen)
    generated = lambda name: name.startswith("reports/codex/M5a2_evidence/") or name == "reports/codex/M5a2_report.md"
    source_mismatches = [row["path"] for row in frozen if not generated(row["path"])
                         and digest(ROOT / row["path"]) != row["sha256"]]
    names = set(filter(None, git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0")))
    missing = sorted(name for name in names if not generated(name) and name not in {row["path"] for row in frozen})
    audit = dict(audit="GREEN" if not (errors or executed_mismatches or source_mismatches or missing) else "RED",
                 old_3220_admissions_unchanged=True, new_admissions=len(policy["waivers"])-3220,
                 explicit_renewals=len(policy.get("renewals", [])), provenance_old_entries_unchanged=True,
                 new_fixture_entries=[row["dest"] for row in new_entries], encoding_size_errors=errors,
                 executed_source_mismatches=executed_mismatches, current_source_mismatches=source_mismatches,
                 current_source_missing_from_export=missing, head=git("rev-parse", "HEAD").strip(),
                 git_writes_performed=False, fresh_git_checkout=False, temp=os.environ.get("TEMP"), tmp=os.environ.get("TMP"))
    write(EVIDENCE / "delivery_audit.json", audit)
    # Rehash generated audit files rather than keeping a pre-write snapshot.
    artifacts = [dict(row, bytes=(ROOT / row["path"]).stat().st_size, sha256=digest(ROOT / row["path"])) for row in artifacts]
    if not any(row["path"] == "reports/codex/M5a2_evidence/delivery_audit.json" for row in artifacts):
        path = EVIDENCE / "delivery_audit.json"
        artifacts.append(dict(path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size, sha256=digest(path)))
    write(EVIDENCE / "artifact_manifest.json", dict(files=artifacts, excludes_self=True))
    print(f"M5a2 delivery audit: {audit['audit']}; {final['collected']} collected/executed; 0 skip")
    return 0 if audit["audit"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
