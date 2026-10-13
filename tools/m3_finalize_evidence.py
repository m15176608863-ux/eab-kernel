"""Independently reconcile the completed WO-M3 evidence (stdlib; no test runs).

Requires final_suite_r3/summary.json to exist and say GREEN. Rechecks raw
collection/call records, scans, mutation failure lines, old/new rational replay,
and frozen executable-input bytes. A pending suite exits 2 without manufacturing
PASS. Verification failures write RED and exit 1. No Git command is executed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M3_evidence"
TEMP = EVIDENCE / "tmp"
OUTPUT = EVIDENCE / "final_audit.json"
MAX_EVIDENCE_BYTES = 5_000_000
MUTANTS = {
    "remove_clipping": "cover clipping exposure mismatch",
    "label_inversion": "body label mismatch",
    "open_endpoint": "isolated closed contact",
    "missing_piece": "body label mismatch",
    "label_propagation": "topological label mismatch",
    "local_exit": "global exit cannot return the local zero-gap seam",
    "open_union_join": "open interval endpoint must remain physical contact",
    "missing_piece3d": "global3d physical-state zero mismatch",
    "local_escape": "global root not local cover event",
}


class AuditError(RuntimeError):
    """A required evidence invariant does not hold."""


def require(condition, message):
    if not condition:
        raise AuditError(message)


def workspace_path(path):
    result = Path(path)
    if not result.is_absolute():
        result = ROOT / result
    result = result.resolve()
    require(result.is_relative_to(ROOT), f"path escapes workspace: {path}")
    return result


def relative(path):
    return workspace_path(path).relative_to(ROOT).as_posix()


def digest(path):
    value = hashlib.sha256()
    with workspace_path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            value.update(chunk)
    return value.hexdigest()


class EvidenceReader:
    """Pin evidence read by this audit and reject changes during reconciliation."""
    def __init__(self):
        self.hashes = {}

    def text(self, path):
        path = workspace_path(path)
        require(path.is_file(), f"required evidence missing: {relative(path)}")
        data = path.read_bytes()
        key, value = relative(path), hashlib.sha256(data).hexdigest()
        require(key not in self.hashes or self.hashes[key] == value,
                f"evidence changed between reads: {key}")
        self.hashes[key] = value
        return data.decode("utf-8-sig")

    def json(self, path):
        return json.loads(self.text(path))

    def stable(self):
        changed = [name for name, value in self.hashes.items()
                   if not (ROOT/name).is_file() or digest(ROOT/name) != value]
        require(not changed, f"evidence changed during final audit: {changed}")


def suite_audit(reader, name, expected_count):
    folder = EVIDENCE/name
    summary = reader.json(folder/"summary.json")
    require(summary["audit"] == "GREEN", f"{name}: suite is not GREEN")
    collection = reader.text(folder/"collection.txt").splitlines()
    nodes = [line for line in collection if line.startswith("tests/") and "::" in line]
    require(len(nodes) == len(set(nodes)) == expected_count,
            f"{name}: collection count/uniqueness is not {expected_count}")
    require(summary["collected"] == expected_count, f"{name}: summary count differs")
    require(len(summary["shards"]) == 4, f"{name}: expected four shard summaries")
    all_collected, all_calls, shards = [], [], []
    for index in range(1, 5):
        dispatch = reader.text(folder/f"shard_{index}_nodes.txt").splitlines()
        raw = reader.json(folder/f"shard_{index}_execution.json")
        detail = reader.json(folder/f"shard_{index}.json")
        reports = raw["reports"]
        calls = [row["nodeid"] for row in reports if row["when"] == "call"]
        skipped = [row for row in reports if row["outcome"] == "skipped"]
        failed = [row for row in reports if row["outcome"] != "passed"]
        dispatch_set = set(dispatch)
        require(raw["exitstatus"] == detail["exit_code"] == summary["shards"][index-1]["exit_code"] == 0,
                f"{name}/shard_{index}: nonzero exit status")
        require(not skipped and not failed, f"{name}/shard_{index}: skip/nonpassed report")
        require(Counter(dispatch) == Counter(raw["collected"]) == Counter(calls),
                f"{name}/shard_{index}: dispatched/collected/actual-call multisets differ")
        require(all(row["nodeid"] in dispatch_set and row["when"] in ("setup", "call", "teardown")
                    for row in reports), f"{name}/shard_{index}: unexpected report node or phase")
        for phase in ("setup", "call", "teardown"):
            require(Counter(row["nodeid"] for row in reports if row["when"] == phase) == Counter(dispatch),
                    f"{name}/shard_{index}: missing/duplicate {phase} reports")
        last = reader.text(folder/f"shard_{index}.txt").strip().splitlines()[-1]
        match = re.search(r"\b(\d+) passed\b", last)
        require(match is not None and int(match.group(1)) == len(calls),
                f"{name}/shard_{index}: final log count differs from call records")
        require(last == detail["last_line"] == summary["shards"][index-1]["last_line"],
                f"{name}/shard_{index}: reported final line differs from raw log")
        all_collected.extend(raw["collected"])
        all_calls.extend(calls)
        shards.append(dict(shard=index, collected=len(raw["collected"]), actual_calls=len(calls),
                           skipped=0, exit_code=0, last_line=last))
    require(Counter(nodes) == Counter(all_collected) == Counter(all_calls),
            f"{name}: whole collection and actual execution multisets differ")
    static_last = reader.text(folder/"exact_construction.txt").strip().splitlines()[-1]
    require(summary["static"]["exit_code"] == 0 and static_last == "exact construction AST gate: 0 violation(s)",
            f"{name}: static gate not verified zero")
    result = dict(collected=len(nodes), actual_calls=len(all_calls), skip_count=0,
                  collected_equals_actual_call_multiset=True, shards=shards,
                  static_last_line=static_last, source=relative(summary["source"]),
                  elapsed_seconds=summary["elapsed_seconds"], fresh_git_checkout=False)
    return nodes, summary, result


def scan_audit(reader):
    summary = reader.json(EVIDENCE/"scans2d/summary_all.json")
    require(summary.get("source_unchanged_during_run") is True, "2D scan lacks stable-source certificate")
    for name, expected in summary["source_sha256"].items():
        require(digest(ROOT/name) == expected, f"2D scan source hash is stale: {name}")
    rows, samples, rays, stored, pieces, directions = summary["rows"], 0, 0, 0, 0, set()
    require(len(rows) == 16 and len({row["name"] for row in rows}) == 16, "2D scan needs 16 distinct rows")
    for row in rows:
        require(Path(row["name"]).name == row["name"], "invalid 2D scan row name")
        data = reader.json(EVIDENCE/"scans2d"/(row["name"]+".json"))
        require(row["sample_count"] == data["sample_count"], "2D scan summary/sample count differs")
        require(row["mismatch_count"] == data["mismatch_count"] == row["skipped"] == data["skipped"] == 0
                and not data["mismatches"], f"2D scan not zero-mismatch/no-skip: {row['name']}")
        require(sum(data["oracle_states"].values()) == data["sample_count"], "2D oracle state census differs")
        samples += data["sample_count"]
        if row["name"] == "bb52_historical_1260":
            require(len(data["samples"]) == data["sample_count"] == 1260, "bb52 historical count differs")
            require(len({(tuple(r["pair"]), r["index"]) for r in data["samples"]}) == 1260,
                    "bb52 historical records duplicate a pair/index")
            require(all(r["actual"] == r["expected"] for r in data["samples"]), "bb52 raw mismatch")
            continue
        require(sum(data["probes_by_kind"].values()) == data["sample_count"], "2D probe kinds differ")
        require(data["stored_cell_labels_checked"] == sum(data["dimensions"].values()), "stored-cell count differs")
        require(data["local_cover_midpoints_checked"] == data["exposed_pieces"]+data["hidden_pieces"],
                "local-cover census differs")
        require(data["random_ray_count"] == len(data["random_ray_exits"]) == 12, "configuration needs 12 rays")
        origin = tuple(Fraction(v) for v in data["random_ray_origin"])
        for ray in data["random_ray_exits"]:
            require(all(ray[k] is True for k in ("true_boundary", "local_covered", "global_covered")),
                    f"failed independent ray boundary/coverage: {row['name']}")
            t, direction = Fraction(ray["parameter"]), tuple(ray["direction"])
            hit = tuple(Fraction(v) for v in ray["point"])
            require(t >= 0 and direction != (0, 0) and hit == tuple(origin[k]+t*direction[k] for k in (0, 1)),
                    "ray exact root/point certificate differs")
            directions.add(direction)
            rays += 1
        stored += data["stored_cell_labels_checked"]
        pieces += data["local_cover_midpoints_checked"]
    require(samples == 27367 and rays == 180, "2D totals must be 27367 probes and 180 rays")
    three = reader.json(EVIDENCE/"three_d_scan.json")
    require(three["complete"] is True and three["total_probes"] == 6110
            and sum(r["probe_count"] for r in three["rows"]) == 6110, "3D scan count/completion differs")
    require(three["total_mismatches"] == 0 and all(r["mismatch_count"] == 0 and not r["mismatches"] for r in three["rows"]),
            "3D scan has mismatches")
    return dict(two_d_probes=samples, two_d_mismatches=0, three_d_probes=6110, three_d_mismatches=0,
                rays=rays, ray_boundary_and_cover_checks_passed=rays, distinct_direction_vectors=len(directions),
                stored_cell_labels=stored, local_cover_midpoints=pieces,
                scope="bb52: historical translations only; 3D: lazy convex-pair probes, not full overlays")


def mutation_audit(reader):
    rows = reader.json(EVIDENCE/"mutations/summary.json")
    require(len(rows) == len(MUTANTS) and {r["mutant"] for r in rows} == set(MUTANTS), "mutation census differs")
    verified = []
    for row in rows:
        name, expected = row["mutant"], MUTANTS[row["mutant"]]
        # A captured Windows CRCRLF leaves a final empty split line. Trim only
        # terminal whitespace; retain and inspect the actual pytest E lines.
        lines = reader.text(EVIDENCE/"mutations"/(name+".txt")).rstrip().splitlines()
        actual = [line for line in lines if re.match(r"^E\s+AssertionError:", line) and expected in line]
        require(row["exit_code"] == 1 and row["expected_assertion"] == expected and actual,
                f"mutation {name} did not fail on the intended actual assertion line")
        require(re.search(r"\b1 failed\b", lines[-1]) is not None and lines[-1] == row["last_line"],
                f"mutation {name}: actual red log count differs")
        verified.append(dict(mutant=name, exit_code=1, actual_assertion_lines=actual))
    return dict(count=len(verified), genuine_target_assertion_failures=len(verified), rows=verified)


def replay_audit(reader):
    old = reader.json(EVIDENCE/"three_d_old_replay.json")
    new = reader.json(EVIDENCE/"three_d_new_replay.json")
    comparison = reader.json(EVIDENCE/"three_d_replay_comparison.json")
    for name, data in (("old", old), ("new", new)):
        require(data["complete"] is True and data["count"] == len(data["rows"]) == 392, f"{name} replay incomplete")
        require(len({r["case"] for r in data["rows"]}) == 392, f"{name} replay duplicate cases")
        require(sum(r["brute_calls"] for r in data["rows"]) == data["brute_calls"], f"{name} brute-call census differs")
    prior, current = {r["case"]: r for r in old["rows"]}, {r["case"]: r for r in new["rows"]}
    require(set(prior) == set(current), "old/new replay cases differ")
    fields = ("input_sha256", "exact_height", "exact_offset", "state")
    detail = []
    for name in sorted(prior):
        a, b = prior[name], current[name]
        require(re.fullmatch(r"[0-9a-f]{64}", a["input_sha256"]) is not None, f"invalid input digest: {name}")
        require(len(a["exact_offset"]) == len(b["exact_offset"]) == 3
                and a["state"] in (-1, 0, 1) and b["state"] in (-1, 0, 1), f"invalid replay field shape: {name}")
        equal = {"input_sha256": a["input_sha256"] == b["input_sha256"],
                 "exact_height": Fraction(a["exact_height"]) == Fraction(b["exact_height"]),
                 "exact_offset": tuple(map(Fraction, a["exact_offset"])) == tuple(map(Fraction, b["exact_offset"])),
                 "state": a["state"] == b["state"]}
        require(all(equal.values()), f"old/new exact replay mismatch: {name}: {equal}")
        require(b["brute_calls"] == 0, f"new replay called brute: {name}")
        detail.append(dict(case=name, fields_equal=equal))
    require(new["brute_calls"] == 0, "new aggregate brute calls nonzero")
    require(comparison["count"] == 392 and comparison["mismatch_count"] == 0 and not comparison["mismatches"]
            and set(comparison["compared_fields"]) == set(fields) and comparison["field_comparison_count"] == 1568,
            "stored replay comparison summary differs")
    require(len(comparison["rows"]) == 392 and
            {r["case"]: r["fields_equal"] for r in comparison["rows"]} == {r["case"]: r["fields_equal"] for r in detail},
            "stored case-by-case comparisons differ from independent recomputation")
    return dict(cases=392, equal_field_comparisons=1568, compared_fields=list(fields), new_brute_calls=0,
                old_brute_calls=old["brute_calls"], rows=detail)


def snapshot_audit(reader, suite_summary):
    source = workspace_path(suite_summary["source"])
    require(source.is_relative_to(TEMP.resolve()), "final frozen export is outside evidence tmp")
    manifest = reader.json(EVIDENCE/"final_suite_r3/export_manifest.json")
    recorded = {r["path"]: r for r in manifest}
    require(len(recorded) == len(manifest), "duplicate frozen manifest paths")
    def critical_paths(base):
        paths = {p.relative_to(base).as_posix() for folder in ("src", "tests") for p in (base/folder).rglob("*.py")}
        return paths | {"pyproject.toml", "tools/exact_construction_policy.json"}
    current_names, frozen_names = critical_paths(ROOT), critical_paths(source)
    critical = []
    for name in sorted(current_names | frozen_names):
        current, frozen = workspace_path(ROOT/name), workspace_path(source/name)
        row = dict(path=name, current_exists=current.is_file(), frozen_exists=frozen.is_file())
        if current.is_file() and frozen.is_file():
            row.update(current_sha256=digest(current), frozen_sha256=digest(frozen),
                       byte_identical=current.read_bytes() == frozen.read_bytes())
            row["manifest_matches"] = (name in recorded and recorded[name]["sha256"] == row["frozen_sha256"]
                                       and recorded[name]["bytes"] == frozen.stat().st_size)
        else:
            row.update(byte_identical=False, manifest_matches=False)
        critical.append(row)
    changes = []
    for name, row in sorted(recorded.items()):
        path = workspace_path(ROOT/name)
        if not path.is_file():
            changes.append(dict(path=name, change="missing_current", frozen_sha256=row["sha256"]))
        else:
            current_hash = digest(path)
            if current_hash != row["sha256"]:
                changes.append(dict(path=name, change="changed_current", frozen_sha256=row["sha256"], current_sha256=current_hash))
    result = dict(source=relative(source), checked_critical_files=len(critical), critical_files=critical,
                  critical_byte_mismatch_count=sum(not r["byte_identical"] or not r["manifest_matches"] for r in critical),
                  current_changed_or_missing_manifest_entries=changes,
                  additional_audit_tool_not_in_snapshot="tools/m3_finalize_evidence.py" not in recorded,
                  difference_scope="All manifest paths compared; added/missing src/tests Python paths compared symmetrically. Noncritical additions other than this tool are not inventoried.")
    return result


def size_audit():
    oversized, count, largest = [], 0, 0
    for folder, directories, filenames in os.walk(EVIDENCE):
        if Path(folder).resolve() == EVIDENCE.resolve():
            directories[:] = [name for name in directories if name != "tmp"]
        for name in filenames:
            path = workspace_path(Path(folder)/name)
            require(not path.is_relative_to(TEMP.resolve()), "unexpected tmp link in persistent evidence")
            size = path.stat().st_size
            count += 1
            largest = max(largest, size)
            if size > MAX_EVIDENCE_BYTES:
                oversized.append(dict(path=relative(path), bytes=size, sha256=digest(path)))
    return dict(scope=relative(EVIDENCE), excluded="tmp/", limit_bytes=MAX_EVIDENCE_BYTES,
                files_checked=count, largest_bytes=largest, oversized=oversized)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    pending = EVIDENCE/"final_suite_r3/summary.json"
    if not pending.is_file():
        print("PENDING: final_suite_r3/summary.json does not exist; suite has not completed.", file=sys.stderr)
        return 2
    try:
        status = json.loads(pending.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        print(f"PENDING: cannot read final_suite_r3 summary: {error}", file=sys.stderr)
        return 2
    if status.get("audit") != "GREEN":
        print(f"NOT READY: final_suite_r3 audit is {status.get('audit')!r}, not GREEN.", file=sys.stderr)
        return 2
    TEMP.mkdir(parents=True, exist_ok=True)
    os.environ.update(PYTHONDONTWRITEBYTECODE="1", TEMP=str(TEMP), TMP=str(TEMP))
    sys.dont_write_bytecode = True
    reader = EvidenceReader()
    result = dict(audit="RED", timestamp_utc=datetime.now(timezone.utc).isoformat(),
                  verification="independent evidence reconciliation; no tests/solvers rerun", errors=[])
    try:
        before, _, result["baseline_suite"] = suite_audit(reader, "baseline_suite", 12662)
        after, final_summary, result["final_suite_r3"] = suite_audit(reader, "final_suite_r3", 12761)
        added, removed = sorted(set(after)-set(before)), sorted(set(before)-set(after))
        result["test_node_delta"] = dict(added_count=len(added), removed_count=len(removed), added=added, removed=removed)
        require(len(added) == 99 and not removed, "expected 99 added test nodes and no removals")
        result["scans"] = scan_audit(reader)
        result["mutations"] = mutation_audit(reader)
        result["exact_replay"] = replay_audit(reader)
        result["snapshot"] = snapshot_audit(reader, final_summary)
        require(result["snapshot"]["critical_byte_mismatch_count"] == 0, "current executable inputs differ from final r3 frozen export")
        result["evidence_sizes"] = size_audit()
        require(not result["evidence_sizes"]["oversized"], "persistent M3 evidence contains a file larger than 5 MB")
        reader.stable()
        result["audit"] = "GREEN"
    except (AuditError, OSError, ValueError, KeyError, TypeError, IndexError) as error:
        result["errors"].append(f"{type(error).__name__}: {error}")
    result["evidence_sha256"] = reader.hashes
    result["auditor_sha256"] = digest(Path(__file__))
    payload = json.dumps(result, ensure_ascii=False, indent=2)+"\n"
    if len(payload.encode("utf-8")) > MAX_EVIDENCE_BYTES:
        print("RED: audit output would exceed 5 MB; refusing persistent write.", file=sys.stderr)
        return 1
    temporary = TEMP/"m3_final_audit_pending.json"
    temporary.write_text(payload, encoding="utf-8", newline="")
    os.replace(temporary, OUTPUT)
    print(json.dumps(dict(audit=result["audit"], report=relative(OUTPUT), errors=result["errors"]), ensure_ascii=False))
    return 0 if result["audit"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
