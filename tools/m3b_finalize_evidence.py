"""Independent WO-M3b final evidence audit; missing evidence is INCOMPLETE.

This tool never runs pytest, changes source files, or copies large raw records.
It checks multiplicities (not just sets), every pytest phase, frozen/current
source bytes, complete scan aggregates, and uncaught semantic mutation logs.
Run with PYTHONDONTWRITEBYTECODE=1 python -X utf8. --self-test is stdlib-only.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M3b_evidence"
SELF = "tools/m3b_finalize_evidence.py"
POLICY = "tools/exact_construction_policy.json"
BOUND_SUMMARY = "reports/codex/M4c_evidence/frozen_summary.json"
PHASES = ("setup", "call", "teardown")
REPLAY_FIELDS = ("input_sha256", "exact_height", "exact_offset", "state")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def short_counter(counter):
    return [{"nodeid": key, "count": value} for key, value in sorted(counter.items())[:8]]


def data_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def strict_m4c_frames(original, current, expected_hashes, expected_count=30):
    """Independent full-JSON comparison, not trusting an 'equal frames' flag."""
    issues = []
    if not all(isinstance(rows, list) for rows in (original, current, expected_hashes)):
        return dict(ok=False, issues=["frame lists missing"])
    if any(len(rows) != expected_count for rows in (original, current, expected_hashes)):
        issues.append("frame counts do not match required complete case")
    sequence = list(range(1, expected_count+1))
    if any(not all(isinstance(row, dict) for row in rows) or [row.get("step") for row in rows] != sequence for rows in (original, current)):
        issues.append("frame steps are not complete, ordered, unique sequence")
    equal = 0
    for index in range(min(len(original), len(current), len(expected_hashes))):
        if original[index] != current[index]:
            issues.append("full normalized frame differs at step "+str(index+1))
        elif data_digest(current[index]) != expected_hashes[index]:
            issues.append("frozen frame hash differs at step "+str(index+1))
        else:
            equal += 1
    return dict(ok=not issues, equal_frames=equal, expected_frames=expected_count, issues=issues)


def strict_execution(dispatch, data):
    """Pure, independently testable multiplicity/outcome audit of one shard."""
    issues = []
    if not isinstance(dispatch, list) or not all(isinstance(n, str) and n for n in dispatch):
        return {"ok": False, "issues": ["invalid dispatch list"]}
    collected, reports = data.get("collected"), data.get("reports")
    if not isinstance(collected, list) or not all(isinstance(n, str) and n for n in collected):
        return {"ok": False, "issues": ["invalid collected list"]}
    if not isinstance(reports, list) or not all(isinstance(r, dict) and
            isinstance(r.get("nodeid"), str) and r.get("when") in PHASES and
            r.get("outcome") in ("passed", "failed", "skipped") for r in reports):
        return {"ok": False, "issues": ["invalid report schema or unknown phase/outcome"]}
    counters = {"dispatch": Counter(dispatch), "collected": Counter(collected)}
    counters.update({phase: Counter(r["nodeid"] for r in reports if r["when"] == phase) for phase in PHASES})
    for name, counter in counters.items():
        duplicates = Counter({key: n for key, n in counter.items() if n != 1})
        if duplicates:
            issues.append({"not_unique": name, "sample": short_counter(duplicates)})
        if counter != counters["dispatch"]:
            issues.append({"counter_mismatch": name,
                           "missing_sample": short_counter(counters["dispatch"]-counter),
                           "extra_sample": short_counter(counter-counters["dispatch"])})
    not_passed = [r for r in reports if r["outcome"] != "passed"]
    if not_passed:
        issues.append({"nonpassing_reports": len(not_passed), "sample": not_passed[:8]})
    if data.get("exitstatus") != 0:
        issues.append({"exitstatus": data.get("exitstatus")})
    if not dispatch or len(reports) != 3*len(dispatch):
        issues.append({"dispatch_count": len(dispatch), "report_count": len(reports), "required_reports": 3*len(dispatch)})
    return {"ok": not issues, "issues": issues, "counts": {k: sum(v.values()) for k, v in counters.items()},
            "report_count": len(reports), "skip_count": sum(r["outcome"] == "skipped" for r in reports),
            "all_phases_passed": not not_passed, "counters": counters}


def strict_replay(baseline, current, expected_count=392):
    """No positional zip or set-only collapse: compare unique case keys."""
    issues, maps = [], []
    for name, data in (("baseline", baseline), ("current", current)):
        rows = data.get("rows")
        if not isinstance(rows, list) or not all(isinstance(row, dict) and isinstance(row.get("case"), str) for row in rows):
            return dict(ok=False, issues=[name+" replay schema invalid"])
        keys = Counter(row["case"] for row in rows)
        if data.get("complete") is not True or data.get("count") != len(rows) or len(rows) != expected_count or any(v != 1 for v in keys.values()):
            issues.append(dict(run=name, count=data.get("count"), rows=len(rows), unique_keys=len(keys), complete=data.get("complete")))
        if data.get("brute_calls") != 0 or any(row.get("brute_calls") != 0 for row in rows):
            issues.append(dict(run=name, error="nonzero or missing per-row/global brute calls"))
        for row in rows:
            try:
                valid = (all(k in row for k in REPLAY_FIELDS) and
                         isinstance(row["input_sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", row["input_sha256"]) and
                         isinstance(row["exact_height"], str) and isinstance(row["exact_offset"], list) and
                         len(row["exact_offset"]) == 3 and all(isinstance(v, str) for v in row["exact_offset"]) and
                         type(row["state"]) is int and row["state"] in (-1, 0, 1))
                if valid:
                    Fraction(row["exact_height"])
                    tuple(Fraction(v) for v in row["exact_offset"])
                else:
                    raise ValueError("expected exact rational strings, SHA256, and a three-state integer")
            except (ValueError, ZeroDivisionError) as error:
                issues.append(dict(run=name, case=row["case"], error=str(error)))
        maps.append({row["case"]: row for row in rows})
    before, after = maps
    if set(before) != set(after):
        issues.append(dict(case_keys_differ=True, missing=sorted(set(before)-set(after))[:8], extra=sorted(set(after)-set(before))[:8]))
    equal_fields, mismatches = 0, []
    for case in sorted(set(before) & set(after)):
        for field in REPLAY_FIELDS:
            if field in before[case] and field in after[case] and before[case][field] == after[case][field]:
                equal_fields += 1
            else:
                mismatches.append(dict(case=case, field=field, baseline=before[case].get(field), current=after[case].get(field)))
    if mismatches or equal_fields != 4*expected_count:
        issues.append(dict(equal_fields=equal_fields, expected_fields=4*expected_count, mismatches=mismatches[:8]))
    return dict(ok=not issues, count=expected_count, equal_fields=equal_fields, mismatch_count=len(mismatches),
                per_row_brute_calls_zero=all(row.get("brute_calls") == 0 for data in (baseline, current) for row in data["rows"]), issues=issues)


def strict_parameter_outputs(data):
    """Check the actual output digests, not only the producer's distinct flag."""
    rows = data.get("parameter_output_fingerprints")
    expected_keys = {(exponent, translation) for exponent in (-400, 0, 400)
                     for translation in (0, 1000, 100000, 1000000)}
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        return dict(ok=False, issues=["invalid parameter output schema"])
    issues = []
    keys = Counter((row.get("exponent"), row.get("translation_magnitude")) for row in rows)
    if set(keys) != expected_keys or any(count != 1 for count in keys.values()):
        issues.append("required 3 scales x 4 translations not present exactly once")
    digests = [row.get("actual_output_sha256") for row in rows]
    valid_digests = all(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) for value in digests)
    if not valid_digests or len(set(digests)) != 12:
        issues.append("actual output SHA256 values must be 12 distinct valid digests")
    for row in rows:
        quaternion = row.get("quaternion")
        if not isinstance(quaternion, list) or len(quaternion) != 4 or not all(type(x) is int for x in quaternion) or not any(quaternion):
            issues.append("each rotation must have a nonzero integral four-coordinate quaternion")
    if data.get("parameter_outputs_distinct") is not True or data.get("parameter_output_count") != len(rows) or len(rows) != 12:
        issues.append("parameter output metadata disagrees with actual rows")
    if data.get("source_unchanged_during_run") is not True:
        issues.append("parameter source stability not attested")
    return dict(ok=not issues, count=len(rows), distinct_digests=len(set(digests)) if valid_digests else None, issues=issues)


def strict_gp_probe(data):
    """Read every rational witness; do not accept a producer pass-count alone."""
    expected = dict(full_dimension=2, cross_face_face_nonparallel=16,
                    a_edge_b_face_transverse=24, b_edge_a_face_transverse=24,
                    cross_edge_edge_nonparallel=36)
    groups = data.get("gp_conditions")
    if not isinstance(groups, dict) or set(groups) != set(expected):
        return dict(ok=False, issues=["wrong sufficient-GP condition groups"])
    issues, witnesses = [], 0
    for name, count in expected.items():
        group = groups[name]
        if not isinstance(group, dict) or not isinstance(group.get("exact_witnesses"), list):
            issues.append(name+" invalid witness schema")
            continue
        rows = group["exact_witnesses"]
        if group.get("count") != count or group.get("passed") != count or len(rows) != count:
            issues.append(name+" condition count/pass mismatch")
        for row in rows:
            witnesses += 1
            try:
                value = row["value"]
                values = value if isinstance(value, list) else [value]
                vector = name.endswith("nonparallel")
                if (row.get("passed") is not True or len(values) != (3 if vector else 1) or
                        not all(isinstance(v, str) for v in values) or not any(Fraction(v) != 0 for v in values)):
                    issues.append(name+" failed/zero/invalid exact witness")
            except (KeyError, TypeError, ValueError, ZeroDivisionError):
                issues.append(name+" invalid exact rational witness")
    counts = data.get("counts", {})
    if (data.get("status") != "COMPLETE" or data.get("gp_total_conditions") != witnesses or witnesses != 102 or
            data.get("mismatches") != 0 or data.get("skipped") != 0):
        issues.append("GP run not complete, or wrong condition total, mismatch, or skip")
    if (not isinstance(counts, dict) or any(type(counts.get(k)) is not int or counts[k] <= 0 for k in ("vertex", "edge", "face", "side")) or
            sum(counts.get(k, 0) for k in ("vertex", "edge", "face", "side")) != 72 or
            data.get("total_probe_checks") != 72 or counts.get("local_atomic") != 13):
        issues.append("GP 72-probe strata or 13 local-atomic count mismatch")
    return dict(ok=not issues, exact_conditions=witnesses, probe_count=data.get("total_probe_checks"),
                local_atomic=counts.get("local_atomic") if isinstance(counts, dict) else None, issues=issues)


class Audit:
    def __init__(self, root=ROOT, evidence=EVIDENCE, final_name="final_suite_r4"):
        self.root = root.resolve()
        self.evidence = evidence.resolve()
        self.final_name = final_name
        self.checks, self.missing, self.inputs = [], [], {}

    def check(self, scope, name, passed, detail=None):
        row = dict(scope=scope, check=name, passed=bool(passed))
        if detail is not None:
            row["detail"] = detail
        self.checks.append(row)
        return bool(passed)

    def path(self, value, relative_to=None):
        path = Path(value)
        path = path if path.is_absolute() else (relative_to or self.root) / path
        path = path.resolve()
        if not path.is_relative_to(self.root):
            self.check("paths", "path_stays_in_workspace", False, str(path))
            return None
        return path

    def read(self, path, *, as_json=False):
        path = self.path(path)
        if path is None:
            return None
        if not path.is_file():
            name = str(path)
            if name not in self.missing:
                self.missing.append(name)
            return None
        try:
            content = path.read_text(encoding="utf-8-sig")
            self.inputs[path.relative_to(self.root).as_posix()] = sha256(path)
            return json.loads(content) if as_json else content
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            self.check("read", "valid_readable_evidence", False, {"path": str(path), "error": str(error)})
            return None

    def verify_hashes(self, scope, hashes):
        if not self.check(scope, "source_hash_inventory_nonempty", isinstance(hashes, dict) and bool(hashes)):
            return {}
        checked, mismatches = 0, []
        for name, expected in hashes.items():
            path = self.path(name)
            if path is None:
                continue
            if not path.is_file():
                self.missing.append(str(path))
                continue
            actual = sha256(path)
            checked += 1
            if actual != expected:
                mismatches.append(dict(path=name, recorded=expected, current=actual))
        self.check(scope, "recorded_source_hashes_match_current_bytes", not mismatches, mismatches)
        return dict(checked=checked, mismatches=mismatches)

    def suite(self, name):
        scope, folder = name, self.evidence / name
        summary = self.read(folder / "summary.json", as_json=True)
        if summary is None:
            return dict(status="INCOMPLETE", name=name), None
        if not self.check(scope, "summary_is_object", isinstance(summary, dict)):
            return dict(status="FAILED", name=name), None
        records = self.path(summary.get("raw_records", self.evidence / "tmp" / (name+"_records")))
        source = self.path(summary.get("source", self.evidence / "tmp" / (name+"_export")))
        if records is None or source is None:
            return dict(status="FAILED", name=name), None
        collection = self.read(records / "collection.txt")
        if collection is None:
            return dict(status="INCOMPLETE", name=name), None
        nodes = [line for line in collection.splitlines() if line.startswith("tests/") and "::" in line]
        counts = Counter(nodes)
        match = re.findall(r"(?m)^(\d+) tests? collected(?: in .*)?$", collection)
        self.check(scope, "collection_summary_count_matches_nodes", len(match) == 1 and int(match[0]) == len(nodes),
                   dict(nodes=len(nodes), collection_summary=match))
        self.check(scope, "global_collection_unique_nonempty", bool(nodes) and all(v == 1 for v in counts.values()),
                   short_counter(Counter({k: v for k, v in counts.items() if v != 1})))
        self.check(scope, "declared_collection_count_matches_raw", summary.get("collected") == len(nodes))
        shards = summary.get("shards", [])
        self.check(scope, "exactly_four_shards", isinstance(shards, list) and len(shards) == 4)
        if not isinstance(shards, list):
            shards = []
        totals = {key: Counter() for key in ("dispatch", "collected", *PHASES)}
        rows = []
        for index in range(1, 5):
            shard_scope = f"{scope}/shard_{index}"
            dispatch_text = self.read(records / f"shard_{index}_nodes.txt")
            execution = self.read(records / f"shard_{index}_execution.json", as_json=True)
            shard = self.read(folder / f"shard_{index}.json", as_json=True)
            log = self.read(folder / f"shard_{index}.txt")
            if any(value is None for value in (dispatch_text, execution, shard, log)):
                rows.append(dict(shard=index, status="INCOMPLETE"))
                continue
            if not isinstance(execution, dict) or not isinstance(shard, dict):
                self.check(shard_scope, "record_schema", False)
                continue
            dispatch = [line for line in dispatch_text.splitlines() if line]
            result = strict_execution(dispatch, execution)
            self.check(shard_scope, "strict_phase_counters_and_outcomes", result["ok"], result["issues"])
            for key, counter in result.pop("counters", {}).items():
                totals[key].update(counter)
            last = next((line for line in reversed(log.splitlines()) if line.strip()), "")
            passed = re.search(r"\b(\d+) passed\b", last)
            self.check(shard_scope, "zero_exit_and_raw_log_pass_count", shard.get("exit_code") == 0 and
                       execution.get("exitstatus") == 0 and passed is not None and int(passed[1]) == len(dispatch))
            self.check(shard_scope, "last_line_exactly_matches_saved_summary", shard.get("last_line") == last)
            actual_counts = result.get("counts", {})
            self.check(shard_scope, "declared_counts_match_raw", all(shard.get(field) == actual_counts.get(key)
                       for field, key in (("dispatched", "dispatch"), ("collected", "collected"), ("executed", "call"))) and
                       shard.get("skip_count") == result.get("skip_count") == 0)
            declared = shards[index-1] if index <= len(shards) else None
            self.check(shard_scope, "per_shard_summary_equals_suite_summary", declared == shard)
            command = shard.get("command", [])
            response = [v[1:] for v in command if isinstance(v, str) and v.startswith("@")]
            temp_index = command.index("--basetemp") if "--basetemp" in command else -1
            temp_path = self.path(command[temp_index+1]) if 0 <= temp_index < len(command)-1 else None
            self.check(shard_scope, "command_uses_audited_dispatch_no_cache_and_explicit_temp",
                       response == [str(records / f"shard_{index}_nodes.txt")] and
                       "no:cacheprovider" in command and temp_path is not None and
                       temp_path.is_relative_to(self.evidence / "tmp"))
            rows.append(dict(shard=index, last_line=last, **result))
        for key, counter in totals.items():
            self.check(scope, "four_shard_"+key+"_counter_equals_global_collection", counter == counts,
                       dict(total=sum(counter.values()), missing=short_counter(counts-counter), extra=short_counter(counter-counts)))
        self.check(scope, "runner_declared_green", summary.get("audit") == "GREEN")
        static = summary.get("static", {})
        static_log = self.read(folder / "exact_construction.txt")
        static_last = next((line for line in reversed((static_log or "").splitlines()) if line.strip()), "")
        self.check(scope, "static_zero_and_raw_log_agrees", static.get("exit_code") == 0 and
                   static.get("last_line") == static_last == "exact construction AST gate: 0 violation(s)")
        return dict(name=name, collected=len(nodes), shards=rows, static_last_line=static_last,
                    elapsed_seconds=summary.get("elapsed_seconds"), frozen_source=str(source), raw_records=str(records)), counts

    def manifest(self, final_suite):
        scope = "final_export_manifest"
        records = self.path(final_suite.get("raw_records", self.evidence / "tmp" / (self.final_name+"_records")))
        source = self.path(final_suite.get("frozen_source", self.evidence / "tmp" / (self.final_name+"_export")))
        if records is None or source is None:
            return {}
        manifest = self.read(records / "export_manifest.json", as_json=True)
        if manifest is None:
            return dict(status="INCOMPLETE")
        if not self.check(scope, "manifest_is_record_list", isinstance(manifest, list) and all(isinstance(r, dict) and isinstance(r.get("path"), str) for r in manifest)):
            return {}
        def included(name):
            path = Path(name)
            return name != SELF and (name in (POLICY, BOUND_SUMMARY) or (path.parts and path.parts[0] in ("src", "tests", "tools") and path.suffix == ".py"))
        entries = [r for r in manifest if included(r["path"])]
        frozen_names = Counter(r["path"] for r in entries)
        current_names = Counter(p.relative_to(self.root).as_posix() for folder in ("src", "tests", "tools")
                                for p in (self.root / folder).rglob("*.py") if p.relative_to(self.root).as_posix() != SELF)
        current_names[POLICY] += 1
        current_names[BOUND_SUMMARY] += 1
        self.check(scope, "frozen_and_current_file_inventory_equal", frozen_names == current_names,
                   dict(missing_from_export=short_counter(current_names-frozen_names), missing_now=short_counter(frozen_names-current_names)))
        self.check(scope, "frozen_paths_unique", all(n == 1 for n in frozen_names.values()))
        changed = []
        for row in entries:
            for stage, path in (("current", self.root / row["path"]), ("frozen_export", source / row["path"])):
                path = self.path(path)
                if path is None:
                    continue
                if not path.is_file():
                    self.missing.append(str(path))
                    continue
                if path.stat().st_size != row.get("bytes") or sha256(path) != row.get("sha256"):
                    changed.append(dict(path=row["path"], stage=stage, expected_bytes=row.get("bytes"),
                                        actual_bytes=path.stat().st_size, expected_sha256=row.get("sha256"), actual_sha256=sha256(path)))
        self.check(scope, "every_frozen_and_current_byte_hash_matches_manifest", not changed, changed)
        return dict(checked_files=len(entries), changed=changed, excluded_auditor=SELF,
                    exclusion_reason="The independent final auditor may be created after source freeze; no other Python file is excluded.")

    def scans(self):
        result = {}
        for name, relative, list_key, sample_key, mismatch_key in (
            ("bb52", "two_d_bb52/summary.json", "rows", "sample_count", "mismatch_count"),
            ("boundary3d", "boundary3d_scan.json", "families", "total_probe_checks", "mismatches")):
            data = self.read(self.evidence / relative, as_json=True)
            if data is None:
                result[name] = dict(status="INCOMPLETE")
                continue
            if not self.check(name, "scan_schema", isinstance(data, dict) and isinstance(data.get(list_key), list)):
                continue
            rows = data[list_key]
            self.check(name, "scan_complete_zero_mismatch_zero_skip", data.get("status") == "COMPLETE" and
                       data.get(mismatch_key) == 0 and data.get("skipped") == 0 and bool(rows))
            if name == "bb52":
                keys = [tuple(r.get("pair", [])) for r in rows]
                self.check(name, "all_21_distinct_pairs", data.get("pair_count") == len(rows) == len(set(keys)) == 21)
                self.check(name, "unchanged_source_run", data.get("source_unchanged_during_run") is True)
                total = 0
                for row in rows:
                    dimensions = row.get("dimensions", {})
                    kinds = row.get("probes_by_kind", {})
                    expected = dict(vertex=dimensions.get("0"), edge_midpoint=dimensions.get("1"),
                                    face_interior=dimensions.get("2"), exact_edge_side=2*dimensions.get("1", 0))
                    self.check(name, "complete_strata_count_"+str(row.get("pair")), kinds == expected and
                               row.get("sample_count") == sum(kinds.values()) and row.get("mismatch_count") == row.get("skipped") == 0)
                    self.check(name, "every_side_is_checked_in_its_adjacent_open_face_"+str(row.get("pair")),
                               row.get("adjacent_open_face_checks") == expected["exact_edge_side"])
                    total += row.get("sample_count", 0)
            else:
                self.check(name, "distinct_nonempty_families", len({r.get("name") for r in rows}) == len(rows) and bool(rows))
                total = 0
                for row in rows:
                    counts = row.get("counts", {})
                    self.check(name, "complete_strata_count_"+str(row.get("name")), all(isinstance(counts.get(k), int) and counts[k] > 0 for k in ("vertex", "edge", "face", "side")) and
                               row.get("mismatches") == row.get("skipped") == 0)
                    total += sum(counts.get(k, 0) for k in ("vertex", "edge", "face", "side"))
            self.check(name, "aggregate_probe_count_matches_rows", total == data.get(sample_key))
            required_sources = ({"src/eab/kernel2d/global_entrance.py", "src/eab/kernel2d/g0_oracle.py", "tools/m3b_scan2d.py"}
                                if name == "bb52" else
                                {"src/eab/kernel3d/boundary.py", "src/eab/kernel3d/global_entrance.py", "src/eab/kernel3d/g03.py",
                                 "src/eab/kernel3d/g03_exit_oracle.py", "tests/test_m3b_boundary3d.py", "tools/m3b_boundary3d_evidence.py"})
            self.check(name, "critical_source_inventory_present", required_sources <= set(data.get("source_sha256", {})))
            result[name] = dict(samples=total, mismatches=data.get(mismatch_key), skipped=data.get("skipped"),
                                source_hashes=self.verify_hashes(name, data.get("source_sha256")))
        return result

    def mutations(self):
        result = {}
        for filename, list_key, expected_names in (
            ("two_d_mutations.json", "rows", {"nonconvex_merge", "index_candidate_loss", "strict_only_local_cover", "drop_isolated_contact", "compact_probe_event_loss"}),
            ("construction3d_mutations.json", "rows", {"self_intersection", "spatial_omission", "nonconvex_merge"}),
            ("boundary3d_mutations.json", "mutations", {"remove_clipping", "physical_zero_one_seam", "restore_intersecting_skip"}),
            ("boundary3d_numeric_mutations.json", "mutations", {"side_step_third", "ee_normal_double"})):
            data = self.read(self.evidence / filename, as_json=True)
            if data is None:
                result[filename] = dict(status="INCOMPLETE")
                continue
            if not self.check(filename, "mutation_schema", isinstance(data, dict) and isinstance(data.get(list_key), list)):
                continue
            rows, checked = data[list_key], []
            complete = (data.get("all_semantic_red") is True if filename == "two_d_mutations.json" else
                        data.get("complete") is True if filename == "construction3d_mutations.json" else
                        data.get("status") == "COMPLETE" or data.get("complete") is True)
            self.check(filename, "producer_marks_mutation_run_complete", complete)
            names = [r.get("name", r.get("kind")) for r in rows]
            self.check(filename, "all_required_mutants_present_once", set(names) == expected_names and len(names) == len(expected_names))
            for row in rows:
                name = row.get("name", row.get("kind"))
                log_name = row.get("log", row.get("traceback"))
                if not isinstance(log_name, str):
                    self.check(filename, "mutation_log_declared", False, name)
                    continue
                log_path = self.path(log_name, self.evidence if Path(log_name).name == log_name else self.root)
                log = self.read(log_path) if log_path is not None else None
                if log is None:
                    continue
                expected = row.get("expected_assertion")
                last = next((line for line in reversed(log.splitlines()) if line.strip()), "")
                hash_flags = [row[k] for k in ("source_hash_gate", "hash_gate_executed", "source_hash_tripwire_executed") if k in row]
                disabled = bool(hash_flags) and all(value is False or value == "not_executed" for value in hash_flags)
                red = (row.get("returncode") == 1 and isinstance(expected, str) and bool(expected) and
                       last == "AssertionError: "+expected and "Traceback (most recent call last):" in log)
                self.check(filename, "uncaught_expected_semantic_red_"+str(name), red and disabled,
                           dict(returncode=row.get("returncode"), final_exception=last, hash_gate_disabled=disabled))
                if "baseline_passed" in row:
                    self.check(filename, "producer_baseline_passed_"+str(name), row["baseline_passed"] is True)
                checked.append(dict(name=name, returncode=row.get("returncode"), final_exception=last, semantic_red=red, hash_gate_disabled=disabled))
            if "source_sha256" in data:
                self.verify_hashes(filename, data["source_sha256"])
            result[filename] = dict(checked=len(checked), rows=checked)
            if filename == "boundary3d_numeric_mutations.json":
                outputs = strict_parameter_outputs(data)
                self.check(filename, "twelve_actual_parameter_outputs_distinct", outputs["ok"], outputs)
                result[filename]["parameter_outputs"] = outputs
        return result

    def replay(self):
        scope = "frozen_escape_replay"
        baseline_path = self.evidence / "construction3d_baseline_replay.json"
        current_path = self.evidence / "construction3d_frozen_r4_replay.json"
        attestation_path = self.evidence / "construction3d_frozen_r4_replay_attestation.json"
        baseline = self.read(baseline_path, as_json=True)
        current = self.read(current_path, as_json=True)
        attestation = self.read(attestation_path, as_json=True)
        if any(value is None for value in (baseline, current, attestation)):
            return dict(status="INCOMPLETE")
        if not self.check(scope, "replay_record_schemas", all(isinstance(value, dict) for value in (baseline, current, attestation))):
            return dict(status="FAILED")
        compared = strict_replay(baseline, current)
        self.check(scope, "392_unique_keys_1568_exact_fields_zero_brute", compared["ok"], compared["issues"])
        before, after = attestation.get("before_sha256"), attestation.get("after_sha256")
        complete = (attestation.get("complete") is True and attestation.get("exit_code") == 0 and
                    attestation.get("invocations") == 1 and attestation.get("resume_or_splice") is False and
                    attestation.get("source_unchanged") is True)
        self.check(scope, "single_complete_nonspliced_invocation", complete)
        inventories_valid = isinstance(before, dict) and bool(before) and isinstance(after, dict)
        self.check(scope, "pre_post_inventories_equal", inventories_valid and before == after and
                   attestation.get("source_file_count") == len(before or {}))
        self.check(scope, "attested_output_hash_matches_replay", attestation.get("output_sha256") == sha256(current_path))
        if not inventories_valid:
            return dict(comparison=compared, status="FAILED")
        frozen_root = self.path(attestation.get("cwd", ""))
        record_root = self.path(current.get("source_root", ""))
        self.check(scope, "replay_root_matches_attested_cwd", frozen_root == record_root and frozen_root is not None and frozen_root.is_relative_to(self.evidence / "tmp"))
        for key in ("TEMP", "TMP"):
            path = self.path(attestation.get(key, ""))
            self.check(scope, key+"_stays_in_evidence_tmp", path is not None and path.is_relative_to(self.evidence / "tmp"))
        frozen_changes = []
        if frozen_root is not None:
            for name, expected in before.items():
                path = self.path(name, frozen_root)
                if path is None:
                    continue
                if not path.is_file():
                    self.missing.append(str(path))
                elif sha256(path) != expected:
                    frozen_changes.append(dict(path=name, recorded=expected, current_frozen=sha256(path)))
        self.check(scope, "attested_frozen_source_still_matches", not frozen_changes, frozen_changes)
        src_hashes = {name: value for name, value in before.items() if name.startswith("src/") and name.endswith(".py")}
        current_src_names = {p.relative_to(self.root).as_posix() for p in (self.root / "src").rglob("*.py")}
        self.check(scope, "all_current_src_files_attested", set(src_hashes) == current_src_names)
        source_check = self.verify_hashes(scope, src_hashes)
        import_path = self.evidence / "construction3d_frozen_r4_actual_imports.json"
        actual_imports = self.read(import_path, as_json=True)
        import_check = dict(status="INCOMPLETE")
        actual_bound_hashes = {}
        if actual_imports is not None:
            modules = actual_imports.get("modules", {}) if isinstance(actual_imports, dict) else {}
            driver = actual_imports.get("driver", {}) if isinstance(actual_imports, dict) else {}
            valid = (isinstance(actual_imports, dict) and actual_imports.get("complete") is True and
                     isinstance(modules, dict) and bool(modules) and actual_imports.get("module_count") == len(modules) and
                     all(isinstance(row, dict) and isinstance(row.get("path"), str) and isinstance(row.get("sha256"), str) for row in modules.values()) and
                     isinstance(driver, dict) and driver.get("path") == "reports/codex/M3_evidence/three_d_scan.py" and isinstance(driver.get("sha256"), str))
            self.check(scope, "same_child_actual_import_inventory_complete", valid)
            if valid:
                hashes = {row["path"]: row["sha256"] for row in modules.values()}
                hashes[driver["path"]] = driver["sha256"]
                actual_bound_hashes = hashes
                self.check(scope, "actual_imports_bound_to_attestation_and_frozen_bytes", sha256(import_path) == attestation.get("actual_imports_sha256") and
                           self.path(actual_imports.get("source_root", "")) == frozen_root and all(before.get(name) == value for name, value in hashes.items()))
                import_check = dict(module_count=len(modules), distinct_files_with_driver=len(hashes),
                                    hashes=self.verify_hashes(scope+"/actual_imports_and_driver", hashes))
        equivalence = self.read(self.evidence / "construction3d_frozen_r4_equivalence.json", as_json=True)
        equivalence_check = dict(status="INCOMPLETE")
        if isinstance(equivalence, dict):
            final_root = self.evidence / "tmp" / (self.final_name+"_export")
            rows = equivalence.get("checked_files", [])
            expected_names = set(src_hashes) | set(actual_bound_hashes)
            flags = ("production_src_equal_workspace", "production_src_equal_final_suite_r4",
                     "actual_imports_and_driver_equal_workspace", "actual_imports_and_driver_equal_final_suite_r4")
            valid = (equivalence.get("complete") is True and all(equivalence.get(k) is True for k in flags) and
                     self.path(equivalence.get("replay_root", "")) == frozen_root and
                     self.path(equivalence.get("final_suite_r4_root", "")) == final_root and
                     self.path(equivalence.get("workspace_root", "")) == self.root and
                     isinstance(rows, list) and all(isinstance(row, dict) and isinstance(row.get("path"), str) for row in rows) and
                     Counter(row["path"] for row in rows) == Counter({name: 1 for name in expected_names}) and
                     equivalence.get("production_src_file_count") == len(src_hashes) and
                     equivalence.get("actual_import_module_count") == import_check.get("module_count") and
                     equivalence.get("actual_import_and_driver_count") == len(actual_bound_hashes))
            self.check(scope, "final_suite_equivalence_inventory_complete", valid)
            mismatches = []
            if valid:
                for row in rows:
                    name = row["path"]
                    expected = src_hashes.get(name, actual_bound_hashes.get(name))
                    for stage, root in (("replay", frozen_root), ("current", self.root), ("final_suite_r4", final_root)):
                        path = self.path(name, root)
                        if path is None:
                            continue
                        if not path.is_file():
                            self.missing.append(str(path))
                        elif sha256(path) != expected or row.get(stage+"_sha256") != expected:
                            mismatches.append(dict(path=name, stage=stage))
                    if row.get("production_source") != (name in src_hashes) or row.get("actual_import_or_driver") != (name in actual_bound_hashes):
                        mismatches.append(dict(path=name, stage="declared_scope"))
                self.check(scope, "recomputed_three_way_actual_bytes_equal", not mismatches, mismatches)
            artifacts = equivalence.get("bound_artifacts", {})
            required = {"construction3d_frozen_r4_"+suffix+".json" for suffix in
                        ("replay_attestation", "actual_imports", "replay", "comparison", "prem3_comparison")}
            self.check(scope, "all_five_equivalence_artifacts_bound", isinstance(artifacts, dict) and set(artifacts) == required)
            artifact_hashes = self.verify_hashes(scope+"/equivalence_artifacts", {
                (self.evidence / name).relative_to(self.root).as_posix(): value for name, value in artifacts.items()}) if isinstance(artifacts, dict) else {}
            equivalence_check = dict(checked_files=len(rows), mismatches=mismatches, artifacts=artifact_hashes)
        non_src_changes = []
        for name, expected in before.items():
            if name in src_hashes:
                continue
            path = self.path(name)
            if path is None:
                continue
            actual = sha256(path) if path.is_file() else None
            if actual != expected:
                non_src_changes.append(dict(path=name, attested=expected, current=actual))
        new_non_src = sorted(p.relative_to(self.root).as_posix() for folder in ("tests", "tools")
                             for p in (self.root / folder).rglob("*.py")
                             if p.relative_to(self.root).as_posix() not in before and p.relative_to(self.root).as_posix() != SELF)
        return dict(comparison=compared, source_hashes=source_check, source_root=str(frozen_root),
                    actual_imports=import_check,
                    final_suite_equivalence=equivalence_check,
                    single_invocation=complete, before_after_equal=before == after,
                    post_replay_non_src_changes=non_src_changes, post_replay_added_tests_or_tools=new_non_src,
                    scope_note="This section compares every attested frozen src byte to current src. Subsequent tests/evidence-harness changes are listed, not silently treated as replayed; the selected final suite separately freezes and verifies all current src/tests/tools.")

    def gp_probe(self):
        scope = "gp_boundary_probe"
        data = self.read(self.evidence / "gp_boundary_probe.json", as_json=True)
        if data is None:
            return dict(status="INCOMPLETE")
        if not self.check(scope, "object_schema", isinstance(data, dict)):
            return dict(status="FAILED")
        checked = strict_gp_probe(data)
        self.check(scope, "102_nonzero_rational_witnesses_72_probes_13_local_atomic", checked["ok"], checked)
        before, after = data.get("source_sha256_before"), data.get("source_sha256_after")
        self.check(scope, "pre_post_source_hashes_identical", isinstance(before, dict) and bool(before) and before == after and data.get("source_unchanged") is True)
        hashes = self.verify_hashes(scope, before)
        return dict(**checked, source_hashes=hashes, scope_note="Separate 72-probe GP supplement; not added to the original 6733-probe family scan.")

    def m4c_replay(self):
        scope = "m4c_compatibility_replay"
        attestation = self.read(self.evidence / "m4c_refresh_attestation.json", as_json=True)
        summary_path = self.root / "reports/codex/M4c_evidence/frozen_summary.json"
        summary = self.read(summary_path, as_json=True)
        old_path = self.evidence / "m4c_frozen_summary_before_r2.json"
        old = self.read(old_path, as_json=True)
        expected = self.read(self.root / "fixtures/m4c_motion/expected.json", as_json=True)
        if any(value is None for value in (attestation, summary, old, expected)):
            return dict(status="INCOMPLETE")
        if not self.check(scope, "summary_schemas", all(isinstance(value, dict) for value in (attestation, summary, old, expected))):
            return dict(status="FAILED")
        raw = self.path(attestation.get("raw_directory", ""))
        if raw is None or not self.check(scope, "raw_artifacts_in_M3b_tmp", raw.is_relative_to(self.evidence / "tmp")):
            return dict(status="FAILED")
        start = self.read(raw / "start.json", as_json=True)
        raw_summary = self.read(raw / "summary.json", as_json=True)
        if start is None or raw_summary is None:
            return dict(status="INCOMPLETE")
        self.check(scope, "single_complete_450_invocation", attestation.get("status") == "COMPLETE" and attestation.get("complete") is True and
                   attestation.get("invocations") == 1 and attestation.get("resume_or_splice") is False and
                   attestation.get("frames") == attestation.get("equal_frames") == 450 and
                   attestation.get("mismatches") == attestation.get("skipped") == 0 and attestation.get("all_gzip_bytes_equal") is True)
        self.check(scope, "new_summary_is_real_raw_batch_summary", summary == raw_summary and summary.get("complete") is True and
                   summary.get("audit") == "GREEN" and summary.get("steps") == 450 and
                   sha256(summary_path) == attestation.get("new_summary_sha256") and
                   sha256(old_path) == attestation.get("old_summary_sha256"))
        before, after = attestation.get("source_before"), attestation.get("source_after")
        self.check(scope, "stable_exact_source_binding", isinstance(before, dict) and len(before) == 23 and before == after ==
                   start.get("source_before") == summary.get("code_hashes") and set(before) == set(old.get("code_hashes", {})))
        source_hashes = self.verify_hashes(scope, after)
        fixtures = {p.relative_to(self.root).as_posix(): sha256(p) for p in (self.root / "fixtures").rglob("*") if p.is_file()}
        self.check(scope, "all_fixture_and_PROVENANCE_bytes_unchanged", fixtures == start.get("fixture_before") and
                   len(fixtures) == attestation.get("fixture_count") and data_digest(fixtures) == attestation.get("fixture_manifest_digest") and
                   attestation.get("fixtures_unchanged") is True and "fixtures/PROVENANCE.json" in fixtures)
        self.check(scope, "wrapper_and_batch_driver_bound", sha256(self.evidence / "m4c_refresh.py") == attestation.get("driver_sha256") and
                   sha256(self.root / "tools/m4c_run_replays.py") == attestation.get("batch_driver_sha256"))
        cases, original_cases, frozen_cases = summary.get("cases", {}), old.get("cases", {}), expected.get("cases", {})
        self.check(scope, "all_fifteen_cases_preserved", isinstance(cases, dict) and len(cases) == 15 and set(cases) == set(original_cases) == set(frozen_cases))
        equal_frames, gzip_equal, results = 0, 0, []
        for case in sorted(cases):
            if case not in frozen_cases or case not in original_cases:
                continue
            current = self.read(raw / case / "audit.json", as_json=True)
            if current is None:
                continue
            reference = frozen_cases[case]
            paths = [self.path(reference.get("normalized_file", "")), self.path(raw / case / "normalized.jsonl.gz")]
            frame_lists = []
            for path in paths:
                if path is None:
                    frame_lists.append(None)
                elif not path.is_file():
                    self.missing.append(str(path)); frame_lists.append(None)
                else:
                    try:
                        self.inputs[path.relative_to(self.root).as_posix()] = sha256(path)
                        with gzip.open(path, "rt", encoding="utf-8") as stream:
                            frame_lists.append([json.loads(line) for line in stream])
                    except (OSError, UnicodeError, json.JSONDecodeError) as error:
                        self.check(scope, "read_frame_data_"+case, False, str(error)); frame_lists.append(None)
            if any(value is None for value in frame_lists):
                continue
            checked = strict_m4c_frames(*frame_lists, reference.get("frame_sha256"))
            self.check(scope, "all_thirty_actual_frames_equal_"+case, checked["ok"], checked)
            equal_frames += checked["equal_frames"]
            compressed_equal = sha256(paths[0]) == sha256(paths[1]) == reference.get("normalized_sha256") == current.get("normalized_sha256")
            self.check(scope, "normalized_gzip_bytes_equal_"+case, compressed_equal)
            gzip_equal += compressed_equal
            self.check(scope, "real_new_case_audit_bound_"+case, current.get("complete") is True and current.get("audit") == "GREEN" and
                       current.get("steps") == 30 and current.get("code_hashes") == after and
                       sha256(raw / case / "audit.json") == cases[case].get("audit_sha256") and
                       current.get("frame_sha256") == reference.get("frame_sha256"))
            fields = ("steps", "counts", "secondary_counts", "stats", "input_hashes", "frames_sha256", "normalized_sha256")
            self.check(scope, "historic_semantics_equal_"+case, all(current.get(k) == reference.get(k) == original_cases[case].get(k) == cases[case].get(k) for k in fields))
            results.append(dict(case=case, equal_frames=checked["equal_frames"], gzip_bytes_equal=compressed_equal))
        self.check(scope, "actual_complete_450_frames_15_byte_equal_gzips", equal_frames == 450 and gzip_equal == len(results) == 15)
        return dict(equal_frames=equal_frames, gzip_byte_equal_cases=gzip_equal, source_hashes=source_hashes,
                    fixture_count=len(fixtures), cases=results, source_root=str(raw),
                    scope_note="450 fresh production frames compared by stdlib full-JSON equality to unchanged frozen results, not a substitute for an independent geometry oracle.")

    def run(self):
        baseline, baseline_nodes = self.suite("baseline_suite")
        final, final_nodes = self.suite(self.final_name)
        comparison = {}
        if baseline_nodes is not None and final_nodes is not None:
            comparison = dict(baseline=sum(baseline_nodes.values()), final=sum(final_nodes.values()),
                              added=sum((final_nodes-baseline_nodes).values()), removed=sum((baseline_nodes-final_nodes).values()),
                              removed_sample=short_counter(baseline_nodes-final_nodes))
            self.check("suites", "final_has_more_collected_nodes_than_baseline", comparison["final"] > comparison["baseline"], comparison)
            self.check("suites", "no_baseline_node_removed", not baseline_nodes-final_nodes, comparison["removed_sample"])
        manifest, scans, mutations, replay, gp, m4c = self.manifest(final), self.scans(), self.mutations(), self.replay(), self.gp_probe(), self.m4c_replay()
        failures = [row for row in self.checks if not row["passed"]]
        status = "INCOMPLETE" if self.missing else ("FAILED" if failures else "GREEN")
        return dict(status=status, generated_utc=datetime.now(timezone.utc).isoformat(),
                    final_name=self.final_name,
                    contract="Strict Counters: dispatch=collected=setup=call=teardown exactly once, all outcomes passed; no source-hash or missing-evidence shortcuts.",
                    baseline_suite=baseline, final_suite=final, suite_comparison=comparison,
                    final_manifest=manifest, scans=scans, mutations=mutations, frozen_escape_replay=replay, gp_boundary_probe=gp, m4c_compatibility_replay=m4c,
                    missing=sorted(set(self.missing)), failure_count=len(failures), failures=failures,
                    checks=self.checks, input_sha256=self.inputs,
                    limitations=["This audit verifies recorded local evidence, not an independent six-track G6 review.",
                                 "Raw execution records stay in ignored tmp; only compact counts and bounded failure samples are emitted."])


def self_test():
    frames = [dict(step=i, phases={"raw": i}) for i in range(1, 3)]
    frame_hashes = [data_digest(row) for row in frames]
    assert strict_m4c_frames(frames, frames, frame_hashes, expected_count=2)["ok"]
    assert not strict_m4c_frames(frames, frames[:1], frame_hashes, expected_count=2)["ok"], "missing production frame must be rejected"
    assert not strict_m4c_frames(frames, [dict(frames[0], phases={"raw": 999}), frames[1]], frame_hashes, expected_count=2)["ok"], "a claimed equal frame must be compared, not trusted"
    names = ["tests/a.py::a", "tests/a.py::b"]
    clean = dict(collected=names, reports=[dict(nodeid=n, when=p, outcome="passed") for n in names for p in PHASES], exitstatus=0)
    assert strict_execution(names, clean)["ok"]
    for phase in PHASES:
        duplicate = dict(clean, reports=clean["reports"]+[dict(nodeid=names[0], when=phase, outcome="passed")])
        assert not strict_execution(names, duplicate)["ok"], "duplicate phase hidden by set equality must fail"
    assert not strict_execution(names+[names[0]], clean)["ok"], "duplicate dispatch must fail"
    assert not strict_execution(names, dict(clean, collected=names+[names[0]]))["ok"], "duplicate collection must fail"
    missing = dict(clean, reports=clean["reports"][:-1])
    assert not strict_execution(names, missing)["ok"], "missing teardown must fail"
    for outcome in ("failed", "skipped"):
        bad = dict(clean, reports=[dict(r, outcome=outcome) if r["when"] == "setup" else r for r in clean["reports"]])
        assert not strict_execution(names, bad)["ok"], "nonpassing setup must fail"
    replay_row = dict(case="one", input_sha256="a"*64, exact_height="1/3", exact_offset=["0", "0", "1/3"], state=0, brute_calls=0)
    replay = dict(complete=True, count=1, brute_calls=0, rows=[replay_row])
    assert strict_replay(replay, replay, expected_count=1)["ok"]
    assert not strict_replay(replay, dict(replay, rows=[dict(replay_row, exact_height="2/3")]), expected_count=1)["ok"]
    assert not strict_replay(replay, dict(replay, count=2, rows=[replay_row, replay_row]), expected_count=1)["ok"]
    assert not strict_replay(replay, dict(replay, rows=[dict(replay_row, brute_calls=1)]), expected_count=1)["ok"]
    parameter_rows = [dict(exponent=e, translation_magnitude=t, quaternion=[1, 2, 3, 4],
                           actual_output_sha256=hashlib.sha256(str((e, t)).encode()).hexdigest())
                      for e in (-400, 0, 400) for t in (0, 1000, 100000, 1000000)]
    parameters = dict(parameter_output_fingerprints=parameter_rows, parameter_outputs_distinct=True,
                      parameter_output_count=12, source_unchanged_during_run=True)
    assert strict_parameter_outputs(parameters)["ok"]
    assert not strict_parameter_outputs(dict(parameters, parameter_output_fingerprints=parameter_rows[:-1]+[parameter_rows[0]]))["ok"]
    duplicate_digest = [dict(row, actual_output_sha256=parameter_rows[0]["actual_output_sha256"]) for row in parameter_rows]
    assert not strict_parameter_outputs(dict(parameters, parameter_output_fingerprints=duplicate_digest))["ok"], "producer flag cannot hide duplicate actual output hashes"
    gp_groups = {name: dict(count=n, passed=n, exact_witnesses=[dict(value=["1", "0", "0"] if name.endswith("nonparallel") else "1", passed=True) for _ in range(n)])
                 for name, n in dict(full_dimension=2, cross_face_face_nonparallel=16, a_edge_b_face_transverse=24,
                                     b_edge_a_face_transverse=24, cross_edge_edge_nonparallel=36).items()}
    gp = dict(status="COMPLETE", gp_conditions=gp_groups, gp_total_conditions=102, mismatches=0, skipped=0,
              counts=dict(vertex=11, edge=22, face=13, side=26, local_atomic=13), total_probe_checks=72)
    assert strict_gp_probe(gp)["ok"]
    gp_groups["full_dimension"]["exact_witnesses"][0]["value"] = "0"
    assert not strict_gp_probe(gp)["ok"], "producer pass counts cannot hide a zero GP witness"
    parent = EVIDENCE / "tmp/final_audit_selftest"
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent) as temporary:
        root = Path(temporary)
        audit = Audit(root, root / "evidence")
        result = audit.run()
        assert result["status"] == "INCOMPLETE" and result["missing"], "missing evidence must never be green"
        assert any("final_suite_r4/summary.json" in name.replace("\\", "/") for name in result["missing"]), "default must audit r4, never reuse an abandoned earlier run"
        chosen = Audit(root, root / "evidence", final_name="selected_suite").run()
        assert any("selected_suite/summary.json" in name.replace("\\", "/") for name in chosen["missing"]), "explicit final name must select its own source chain"
    print("self-test: clean pass; duplicate, missing phase, failed/skip phase rejected; absent evidence INCOMPLETE")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--final-name", default="final_suite_r4", help="Final suite evidence directory; abandoned runs are never combined (default: final_suite_r4)")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.final_name):
        parser.error("--final-name must be one directory name without path separators")
    if args.self_test:
        self_test()
        return 0
    result = Audit(final_name=args.final_name).run()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "final_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    lines = ["# WO-M3b 最终证据独立审计", "", "状态："+result["status"], "最终运行："+result["final_name"],
             "缺失："+str(len(result["missing"])), "失败检查："+str(result["failure_count"]), ""]
    for name in ("baseline_suite", "final_suite"):
        suite = result[name]
        lines.append(name+" collected="+str(suite.get("collected", "missing")))
        lines.extend("- "+row["last_line"] for row in suite.get("shards", []) if "last_line" in row)
    lines.extend(["", "详情见 [final_audit.json](final_audit.json)。原始大记录只读保留在 tmp；未复制。", ""])
    lines.extend("- 缺失："+name for name in result["missing"])
    lines.extend("- 失败："+row["scope"]+" / "+row["check"] for row in result["failures"])
    (EVIDENCE / "final_audit.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(result["status"], "missing", len(result["missing"]), "failed checks", result["failure_count"])
    return 0 if result["status"] == "GREEN" else (2 if result["status"] == "INCOMPLETE" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
