"""WO-INT1 machine audit of baseline/final suites and immutable history.

Read-only Git commands identify the rollback anchor and changed-file manifest.
No tests are rerun or results spliced here; every suite uses its own complete
four-process execution journal from a fresh byte export.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/INT1_evidence"


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (EVIDENCE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8", newline="")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def suite(name):
    summary = read(EVIDENCE / name / "summary.json")
    temp = Path(summary["temp"])
    collected = [line for line in (temp / "collection.txt").read_text(encoding="utf-8").splitlines()
                 if line.startswith("tests/") and "::" in line]
    calls, failures, phase_counts, seconds = [], [], Counter(), Counter()
    shards = []
    for i, result in enumerate(summary["shards"], 1):
        record_path = temp / f"shard_{i}_execution.json"
        record = read(record_path)
        dispatched = (temp / f"shard_{i}_nodes.txt").read_text(encoding="utf-8").splitlines()
        actual = [r["nodeid"] for r in record["reports"] if r["when"] == "call"]
        assert record["complete"]
        assert Counter(dispatched) == Counter(record["collected"]) == Counter(actual)
        calls.extend(actual)
        for row in record["reports"]:
            phase_counts[row["when"] + ":" + row["outcome"]] += 1
            if row["outcome"] != "passed":
                failures.append(row)
            if row["when"] == "call":
                seconds[row["nodeid"]] += row["duration"]
        shards.append(dict(shard=i, collected=len(actual), executed=len(actual),
                           exit_code=result["exit_code"], last_line=result["last_line"],
                           execution_sha256=digest(record_path)))
    assert len(collected) == len(set(collected))
    assert Counter(collected) == Counter(calls)
    return dict(audit=summary["audit"], complete=True, collected=len(collected), executed=len(calls),
                phase_counts=dict(phase_counts), failures=failures, shards=shards,
                static=summary["static"], call_seconds=sum(seconds.values()),
                wall_seconds=summary["elapsed_seconds"], source=summary["source"],
                manifest=summary["manifest"], temp=str(temp), fresh_git_checkout=False), seconds


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "final_suite_r1"
    baseline, old_times = suite("baseline_suite_r2_postreboot")
    final, new_times = suite(name)
    write("baseline_diagnosis.json", baseline)
    write("node_identity_audit.json", final)
    added = sorted(new_times.keys() - old_times.keys())
    deleted = sorted(old_times.keys() - new_times.keys())
    write("suite_delta.json", dict(added=added, deleted=deleted,
                                  baseline_count=len(old_times), final_count=len(new_times)))
    write("performance.json", dict(baseline_call_seconds=baseline["call_seconds"],
          final_call_seconds=final["call_seconds"], added_gate_call_seconds=sum(new_times[n] for n in added),
          added_gate_fraction=sum(new_times[n] for n in added) / baseline["call_seconds"],
          total_call_ratio=final["call_seconds"] / baseline["call_seconds"],
          total_wall_ratio=final["wall_seconds"] / baseline["wall_seconds"], controlled_host=False,
          limitation="Shared host and simultaneous evidence tasks; added-node cost is measured, not a controlled total-runtime guarantee."))

    original_policy = json.loads(git("show", "3bf5e95:tools/exact_construction_policy.json"))
    seam_policy = json.loads(git("show", "f012d6a:tools/exact_construction_policy.json"))
    policy = read(ROOT / "tools/exact_construction_policy.json")
    current_rows = {r["id"]: r for r in policy["waivers"]}
    assert len(current_rows) == len(policy["waivers"])
    assert len(original_policy["waivers"]) == 3103
    old_changes = [r["id"] for r in original_policy["waivers"] if current_rows.get(r["id"]) != r]
    m5_changes = [r["id"] for r in seam_policy["waivers"]
                  if r["id"].startswith(("M5A-", "M5A2-")) and current_rows.get(r["id"]) != r]
    provenance_before = json.loads(git("show", "f012d6a:fixtures/PROVENANCE.json"))
    provenance = read(ROOT / "fixtures/PROVENANCE.json")
    changed_provenance = [a["dest"] for a, b in zip(provenance_before["entries"], provenance["entries"]) if a != b]
    assert len(provenance["entries"]) == len(provenance_before["entries"])
    assert changed_provenance == ["m5a2/revalidation.json"]
    assert all(value == provenance[key] for key, value in provenance_before.items() if key != "entries")
    row = next(r for r in provenance["entries"] if r["dest"] == changed_provenance[0])
    assert row["sha256"] == digest(ROOT / "fixtures" / row["dest"])
    assert row["bytes"] == (ROOT / "fixtures" / row["dest"]).stat().st_size
    write("immutability_audit.json", dict(old_3103_changes=old_changes, m5a_m5a2_changes=m5_changes,
          provenance_changed_entries=changed_provenance,
          baseline_rows=len(seam_policy["waivers"]), final_rows=len(policy["waivers"]),
          baseline_rules=dict(Counter(r["rule"] for r in seam_policy["waivers"])),
          final_rules=dict(Counter(r["rule"] for r in policy["waivers"]))))

    # Compare the executed frozen source to both its manifest and current files.
    from m5a2_run_gates import export_mismatches
    source = Path(final["source"])
    manifest = read(Path(final["manifest"]))
    executed_mismatches = export_mismatches(source, manifest)
    generated = lambda p: p.startswith("reports/codex/INT1_evidence/") or p == "reports/codex/INT1_report.md"
    current_mismatches = [r["path"] for r in manifest if not generated(r["path"])
                          and (not (ROOT / r["path"]).is_file() or digest(ROOT / r["path"]) != r["sha256"])]
    names = set(filter(None, git("ls-files", "-z", "--cached", "--others", "--exclude-standard").decode("utf-8").split("\0")))
    missing = sorted(n for n in names if not generated(n) and n not in {r["path"] for r in manifest})
    changed = set(filter(None, (git("diff", "--name-only", "-z") + git("ls-files", "--others", "--exclude-standard", "-z")).decode("utf-8").split("\0")))
    errors, artifacts = [], []
    for name in sorted(changed):
        path = ROOT / name
        if not path.is_file() or name.endswith("INT1_evidence/artifact_manifest.json"):
            continue
        raw = path.read_bytes()
        if path.suffix in {".py", ".md", ".json", ".jsonl", ".txt", ".log"}:
            try:
                raw.decode("utf-8")
                if raw.startswith(b"\xef\xbb\xbf"):
                    errors.append(name + ": BOM")
            except UnicodeDecodeError:
                errors.append(name + ": not UTF-8")
        if name.startswith("reports/codex/INT1_evidence/") and len(raw) > 1_000_000:
            errors.append(name + ": oversized submit-candidate evidence")
        artifacts.append(dict(path=name, bytes=len(raw), sha256=digest(path)))
    green = (final["audit"] == "GREEN" and not final["failures"] and not old_changes and not m5_changes
             and not executed_mismatches and not current_mismatches and not missing and not errors and not deleted)
    audit = dict(audit="GREEN" if green else "RED", head=git("rev-parse", "HEAD").decode().strip(),
                 git_writes_performed=False, fresh_git_checkout=False, encoding_size_errors=errors,
                 executed_source_mismatches=executed_mismatches, current_source_mismatches=current_mismatches,
                 current_source_missing_from_export=missing, deleted_tests=deleted)
    write("delivery_audit.json", audit)
    write("artifact_manifest.json", dict(files=artifacts, excludes_self=True))
    print("INT1_DELIVERY_" + audit["audit"])
    return 0 if green else 1


if __name__ == "__main__":
    raise SystemExit(main())
