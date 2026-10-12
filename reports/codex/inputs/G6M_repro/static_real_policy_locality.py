"""Rerunnable locality checks using the installed, unmodified real manifest.

Run from the repository root:
  $env:PYTHONDONTWRITEBYTECODE='1'
  python -X utf8 reports/codex/R12FIXb_evidence/real_policy_locality_probe.py

Only this evidence directory is written. Source mutations exist in memory;
the actual src/tests/tools/docs and the manifest are never modified.
This verifies review pin locality, NOT that the legacy waivers are safe.
"""
from __future__ import annotations

import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "review/static_logs"
sys.path.insert(0, str(ROOT / "tools"))

import check_exact_construction as gate
import exact_construction_subset as subset


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


def pin(row):
    return row["function"], row["rule"], row["node"]


def issue_record(row):
    return dict(zip(("path", "line", "function", "rule", "message", "node", "context"), row))


def scan(text, path):
    return gate.scan_text(text, path, repository_root=ROOT)


def insert_body_comment(text, function):
    definition = next(n for n in ast.parse(text).body
                      if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == function)
    # Before the first body statement, preserving any original docstring as
    # the first statement. No expression/branch/order or AST fingerprint changes.
    first = definition.body[0]
    lines = text.splitlines(keepends=True)
    lines.insert(first.lineno - 1, " " * first.col_offset + "# R12FIXb in-memory real-policy locality probe\n")
    changed = "".join(lines)
    assert ast.dump(ast.parse(changed), include_attributes=False) == ast.dump(ast.parse(text), include_attributes=False)
    return changed


def main():
    started = time.perf_counter()
    policy_path = ROOT / "tools/exact_construction_policy.json"
    policy_bytes = policy_path.read_bytes()
    policy = json.loads(policy_bytes)
    rows = policy["waivers"]
    assert "dependency_snapshot" not in policy
    assert all("dependencies" not in row for row in rows)

    # Real rows from two independent top-level functions in the same file.
    path = "tests/test_invariance_geom.py"
    functions = ("_pair_generic", "_pair_ve3_wedge")
    text = source(path)
    originals = {p: (ROOT / p).read_bytes() for p in {r["path"] for r in rows}}
    source_contexts = {p: subset.site_contexts(data.decode("utf-8-sig")) for p, data in originals.items()}
    stale_baseline_rows = [r for r in rows if source_contexts[r["path"]].get(r["function"]) != r["context"]]
    assert not stale_baseline_rows, "Installed real manifest must match its current local scopes"
    before_approved = subset.approved_sites(text, path, ROOT)
    before_gate = scan(text, path)
    assert before_gate == [], before_gate
    examples = []
    for function in functions:
        selected = [r for r in rows if r["path"] == path and r["function"] == function]
        assert selected, "Each selected function must have real installed waivers"
        selected_pins = {pin(r) for r in selected}
        assert selected_pins <= before_approved
        changed = insert_body_comment(text, function)
        after_approved = subset.approved_sites(changed, path, ROOT)
        after_contexts = subset.site_contexts(changed)
        assert before_approved - after_approved == selected_pins
        assert after_approved - before_approved == set()
        assert {p for p in before_approved if p[0] != function} <= after_approved
        changed_scope_names = sorted(name for name in set(source_contexts[path]) | set(after_contexts)
                                     if source_contexts[path].get(name) != after_contexts.get(name))
        assert changed_scope_names == [function], changed_scope_names

        # Compare ALL real policy rows, not just this file or a synthetic fixture.
        changed_policy_rows = [r for r in rows if (
            after_contexts.get(r["function"]) if r["path"] == path
            else source_contexts[r["path"]].get(r["function"])) != r["context"]]
        assert {(r["path"], *pin(r)) for r in changed_policy_rows} == {(path, *p) for p in selected_pins}
        issues = scan(changed, path)
        assert issues, "Changing a reviewed real function body must be red"
        assert {r[2] for r in issues} == {function}, issues
        stale = [r for r in issues if r[3] == "closed-stale-waiver"]
        # scan_text intentionally returns public five-column diagnostics and
        # deduplicates equivalent messages; inspect the pin checker separately
        # when correlating individual real AST fingerprints.
        stale_details = subset.stale_waiver_issues(changed, path)
        assert {(r[4], r[5]) for r in stale_details} == {
            ("Local review expired: " + r["rule"], r["node"]) for r in selected}
        examples.append({
            "function": function, "selected_real_waivers": len(selected),
            "before_context": source_contexts[path][function],
            "after_context": after_contexts[function],
            "changed_scope_names": changed_scope_names,
            "approved_sites_before": len(before_approved), "approved_sites_after": len(after_approved),
            "removed_approved_sites": sorted([list(p) for p in before_approved - after_approved]),
            "unexpected_approved_additions": 0,
            "other_policy_rows_context_unchanged": len(rows) - len(changed_policy_rows),
            "changed_policy_rows": len(changed_policy_rows),
            "red_issue_count": len(issues), "stale_issue_count": len(stale),
            "expired_site_detail_count": len(stale_details),
            "all_red_functions": sorted({r[2] for r in issues}),
            "issues": [issue_record(r) for r in issues],
            "expired_site_details": [issue_record(r) for r in stale_details],
        })

    # New prohibited construction does not inherit or enlarge the real manifest.
    new_name = "_r12fixb_new_unreviewed_forbidden"
    new_body = ("\n\ndef " + new_name + "(value: float):\n"
                "    return math.sqrt(value * value)\n")
    new_source = text + new_body
    assert subset.approved_sites(new_source, path, ROOT) == before_approved
    new_contexts = subset.site_contexts(new_source)
    assert all(new_contexts.get(r["function"]) == r["context"] for r in rows if r["path"] == path)
    new_issues = scan(new_source, path)
    assert new_issues and {r[2] for r in new_issues} == {new_name}, new_issues
    assert not any(r[3] == "closed-stale-waiver" for r in new_issues)

    # This is a source-text smoke check; the actual repository-copy comment
    # gate remains part of the full pytest run, not a claim made by this script.
    unrelated_path = "src/eab/__init__.py"
    unrelated_bytes = (ROOT / unrelated_path).read_bytes()
    unrelated_before = source(unrelated_path)
    unrelated_after = unrelated_before + "\n# R12FIXb unrelated-source comment only\n"
    assert scan(unrelated_before, unrelated_path) == []
    assert scan(unrelated_after, unrelated_path) == []
    assert subset.approved_sites(unrelated_before, unrelated_path, ROOT) == subset.approved_sites(unrelated_after, unrelated_path, ROOT)

    # Prove the evidence generator did not rewrite any reviewed file or policy.
    assert policy_path.read_bytes() == policy_bytes
    assert all((ROOT / p).read_bytes() == data for p, data in originals.items())
    assert (ROOT / unrelated_path).read_bytes() == unrelated_bytes
    result = {
        "status": "REAL_POLICY_LOCALITY_PASS",
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": time.perf_counter() - started,
        "manifest": "tools/exact_construction_policy.json",
        "manifest_sha256": sha(policy_bytes),
        "manifest_waiver_count": len(rows),
        "reviewed_source_file_count": len(originals),
        "manifest_or_reviewed_source_modified": False,
        "baseline_local_pin_mismatches": len(stale_baseline_rows),
        "selected_file": path,
        "selected_file_sha256": sha(originals[path]),
        "baseline_selected_file_issues": before_gate,
        "locality_mutations": examples,
        "new_forbidden_function": {
            "name": new_name, "source": new_body,
            "all_existing_approved_sites_unchanged": True,
            "all_existing_contexts_unchanged": True,
            "issues": [issue_record(r) for r in new_issues],
        },
        "unrelated_comment": {"path": unrelated_path, "before_issues": 0, "after_issues": 0,
                              "scope": "in-memory scan_text, not a repository-copy run"},
        "boundaries": [
            "Uses the installed real manifest; no monkeypatch, synthetic waiver or policy enlargement.",
            "All mutations are source strings only; no src/tests/tools/docs file is written.",
            "Tests pin locality and fail-closed detection, not the numerical safety of legacy waivers.",
            "The full-suite real-repository comment test is separate evidence.",
        ],
    }
    output = OUT / "real_policy_locality_probe.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log = [result["status"], f"MANIFEST_SHA256={result['manifest_sha256']}",
           f"REAL_WAIVERS={len(rows)}", f"REVIEWED_SOURCE_FILES={len(originals)}"]
    for case in examples:
        log.append(f"{case['function']}: expired={case['selected_real_waivers']} "
                   f"other_contexts_unchanged={case['other_policy_rows_context_unchanged']} "
                   f"red={case['red_issue_count']} only_function={case['all_red_functions']}")
    log.extend([f"NEW_FORBIDDEN_RED={len(new_issues)}", "UNRELATED_COMMENT_ISSUES=0",
                "MANIFEST_AND_REVIEWED_SOURCE_UNCHANGED=True", f"ELAPSED_SECONDS={result['elapsed_seconds']:.6f}"])
    rendered = "\n".join(log) + "\n"
    (OUT / "real_policy_locality_probe.log").write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
