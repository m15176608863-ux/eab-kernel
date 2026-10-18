"""Summarize M5a node identity, source identity, encoding and timing evidence.

Read-only Git queries only; writes small audit artifacts inside M5a_evidence.
This does not turn a fresh byte export into a fresh committed Git checkout.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M5a_evidence"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8")


def changed_files():
    changed = set(filter(None, git("diff", "--name-only", "-z").split("\0")))
    changed |= set(filter(None, git("ls-files", "--others", "--exclude-standard", "-z").split("\0")))
    return changed


def generated_output(relative):
    return relative.startswith("reports/codex/M5a_evidence/") or relative == "reports/codex/M5a_report.md"


def delivery_file_errors():
    text_errors, oversized = [], []
    for relative in sorted(changed_files()):
        p = ROOT/relative
        if not p.is_file():
            continue
        raw = p.read_bytes()
        if p.suffix in {".py", ".md", ".json", ".jsonl", ".txt", ".log", ".toml"}:
            try:
                raw.decode("utf-8")
                if raw.startswith(b"\xef\xbb\xbf"):
                    text_errors.append(relative+": UTF-8 BOM")
            except UnicodeDecodeError:
                text_errors.append(relative+": not UTF-8")
        if relative.startswith("reports/codex/M5a_evidence/") and len(raw) > 1_000_000:
            oversized.append(relative)
    return text_errors, oversized


def suite_audit(directory):
    summary = read(directory/"summary.json")
    assert summary["complete"] and summary["audit"] == "GREEN", "suite must be complete GREEN"
    collected = [s for s in (directory/"collection.txt").read_text(encoding="utf-8").splitlines()
                 if s.startswith("tests/") and "::" in s]
    dispatched, actual, calls, rows = [], [], [], []
    durations = Counter()
    new_durations = Counter()
    for i in range(1, 5):
        wanted = (directory/f"shard_{i}_nodes.txt").read_text(encoding="utf-8").splitlines()
        execution = read(directory/f"shard_{i}_execution.json")
        assert execution["complete"] and execution["exitstatus"] == 0
        call_reports = [r for r in execution["reports"] if r["when"] == "call"]
        executed = [r["nodeid"] for r in call_reports]
        assert Counter(wanted) == Counter(execution["collected"]) == Counter(executed), "shard node identities"
        assert all(r["outcome"] == "passed" for r in execution["reports"]), "zero failures, zero skips"
        for r in call_reports:
            durations[r["nodeid"].split("::")[0]] += r["duration"]
            if "test_m5a_" in r["nodeid"]:
                new_durations[i] += r["duration"]
        dispatched += wanted
        actual += execution["collected"]
        calls += executed
        rows.append(dict(shard=i, dispatched=len(wanted), collected=len(execution["collected"]),
                         executed=len(executed), last_line=summary["shards"][i-1]["last_line"],
                         execution_sha256=sha(directory/f"shard_{i}_execution.json")))
    assert Counter(collected) == Counter(dispatched) == Counter(actual) == Counter(calls), "global node identities"
    assert len(collected) == len(set(collected)), "duplicate collected node"
    return dict(complete=True, audit="GREEN", collected=len(collected), executed=len(calls), skip_count=0,
                shards=rows, call_seconds=sum(durations.values()), m5a_call_seconds=sum(new_durations.values()),
                m5a_call_seconds_by_shard=dict(new_durations), call_seconds_by_file=dict(durations),
                total_wall_seconds=summary["elapsed_seconds"], static=summary["static"],
                fresh_git_checkout=False, source=summary["source"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", default="final_suite_r1")
    parser.add_argument("--baseline", default="baseline_suite_r1")
    args = parser.parse_args()
    for name in (args.suite, args.baseline):
        if Path(name).name != name:
            parser.error("suite names must be local directory names")
    final = suite_audit(EVIDENCE/args.suite)
    baseline = suite_audit(EVIDENCE/args.baseline)
    write(EVIDENCE/"node_identity_audit.json", final)
    performance = dict(baseline=baseline, final=final,
                       wall_ratio=final["total_wall_seconds"]/baseline["total_wall_seconds"],
                       call_ratio=final["call_seconds"]/baseline["call_seconds"],
                       added_gate_fraction_of_baseline=final["m5a_call_seconds"]/baseline["call_seconds"],
                       controlled_environment=False,
                       limitation="Shared host has concurrent work; a single sequential baseline/final run is not a controlled 5 percent regression certificate.")
    write(EVIDENCE/"performance.json", performance)
    source = Path(final["source"])
    assert source.resolve().is_relative_to((EVIDENCE/"tmp").resolve())
    manifest = read(EVIDENCE/args.suite/"export_manifest.json")
    # Audit the actually executed copy after the run, not just current source.
    executed_mismatches = [r["path"] for r in manifest if not (source/r["path"]).is_file()
                           or sha(source/r["path"]) != r["sha256"]]
    important = [r for r in manifest if r["path"].startswith("fixtures/")]
    mismatches = [r["path"] for r in important if not (ROOT/r["path"]).is_file() or sha(ROOT/r["path"]) != r["sha256"]]
    files = set(filter(None, git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0")))
    current = {p for p in files if p.startswith("fixtures/") and (ROOT/p).is_file()}
    missing = sorted(current-{r["path"] for r in important})
    write(EVIDENCE/"runtime_environment.json", dict(python=sys.version, executable=sys.executable,
          platform=platform.platform(), cpu_count=os.cpu_count(), temp=os.environ.get("TEMP"), tmp=os.environ.get("TMP"),
          pytest=subprocess.check_output([sys.executable, "-X", "utf8", "-m", "pytest", "--version", "-p", "no:cacheprovider",
              "--basetemp", str(EVIDENCE/"tmp"/"version_probe")], cwd=ROOT).decode("utf-8").strip()))
    text_errors, oversized_runtime = delivery_file_errors()
    audit = dict(audit="GREEN" if not (mismatches or missing or executed_mismatches or text_errors or oversized_runtime) else "RED",
                 frozen_source_files=len(important), source_mismatches=mismatches, source_missing_from_export=missing,
                 executed_export_checked_files=len(manifest), executed_export_mismatches=executed_mismatches,
                 excluded_generated_outputs=["reports/codex/M5a_evidence/**", "reports/codex/M5a_report.md"],
                 changed_text_encoding_errors=text_errors, submit_candidate_oversized_runtime_files=oversized_runtime,
                 branch=git("symbolic-ref", "--short", "HEAD").strip(), head=git("rev-parse", "HEAD").strip(),
                 fresh_git_checkout=False, git_writes_performed=False,
                 source_export_manifest_sha256=sha(EVIDENCE/args.suite/"export_manifest.json"))
    write(EVIDENCE/"delivery_audit.json", audit)
    artifacts = []
    # Include files just generated by this invocation, not an earlier listing.
    for relative in sorted(changed_files()):
        p = ROOT/relative
        if p.is_file() and relative not in {"reports/codex/M5a_evidence/artifact_manifest.json"}:
            artifacts.append(dict(path=relative, bytes=p.stat().st_size, sha256=sha(p)))
    write(EVIDENCE/"artifact_manifest.json", dict(files=artifacts, note="Manifest excludes itself; regenerate after editing the report."))
    final_text_errors, final_oversized = delivery_file_errors()
    assert final_text_errors == text_errors and final_oversized == oversized_runtime, "generated output encoding/size audit"
    print(f"M5a delivery audit: {audit['audit']}; {final['collected']} collected/executed; 0 skip")
    return 0 if audit["audit"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
