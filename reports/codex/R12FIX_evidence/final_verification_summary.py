"""Read-back gates for final delivery; does not refresh policy or alter tests."""
import ast
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


spec = importlib.util.spec_from_file_location("final_subset", ROOT / "tools/exact_construction_subset.py")
subset = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subset)
policy = read(ROOT / "tools/exact_construction_policy.json")
policy_keys = [(r["path"], r["function"], r["rule"], r["node"], r["context"]) for r in policy["waivers"]]
contexts = {p: subset.site_contexts((ROOT / p).read_text(encoding="utf-8-sig"))
            for p in {r["path"] for r in policy["waivers"]}}
context_mismatches = [r for r in policy["waivers"] if contexts[r["path"]].get(r["function"]) != r["context"]]

renames = {"test_k01_unrounded_or_definitely_overwritten_paths_remain_allowed":
           "test_k01_unrounded_paths_have_no_rounding_false_positive_but_fail_closed"}
grid_checks = []
for name in ("test_r9fix_construction_static.py", "test_r10_static_construction.py", "test_r11fix_static_flow.py"):
    path = "tests/" + name
    old = ast.parse(subprocess.check_output(["git", "show", "HEAD:" + path], cwd=ROOT, env=env).decode("utf-8-sig"))
    new = ast.parse((ROOT / path).read_text(encoding="utf-8-sig"))
    old_defs = {n.name: n for n in old.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
    new_defs = {n.name: n for n in new.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
    pairs = [(name, renames.get(name, name)) for name in old_defs]
    checks = {"same_function_set_with_documented_rename": {b for a, b in pairs} == set(new_defs),
              "parameter_decorators_unchanged": all(
                  [ast.dump(d, include_attributes=False) for d in old_defs[a].decorator_list] ==
                  [ast.dump(d, include_attributes=False) for d in new_defs[b].decorator_list]
                  for a, b in pairs)}
    assert all(checks.values()), (path, checks)
    grid_checks.append({"path": path, **checks, "test_functions": len(old_defs)})

tracked = read(HERE / "tracked_scope_snapshot.json")
drift = [r["path"] for r in tracked if hashlib.sha256((ROOT / r["path"]).read_bytes()).hexdigest() != r["sha256"]]
assert not drift, drift
protected = [r for r in tracked if r["path"].startswith(("src/", "fixtures/"))]
full = read(HERE / "full_suite/summary.json")
targets = read(HERE / "targeted_verification.json")
mutations = read(HERE / "mutation_teeth.json")
full_nodes = read(HERE / "full_suite/collection_nodes.json")
m4_nodes = [x for x in full_nodes if x.startswith(("tests/test_m4_bdda_adapter.py::",
                "tests/test_m4_bdda_shadow.py::", "tests/test_m4_bdda_vv_reader.py::"))]
checks = {
    "one_confirmed_finding": len(read(ROOT / "reports/codex/inputs/G6L_findings.json")["findings"]) == 1,
    "all_reviews_resolved": read(HERE / "policy_unreviewed_sites.json") == [],
    "policy_unique_exact_keys": len(policy_keys) == len(set(policy_keys)),
    "policy_all_contexts_match": not context_mismatches,
    "policy_dependency_bytes_match": subset.dependency_snapshot(ROOT) == policy["dependencies"],
    "policy_all_reasons_present_no_pending": all(r["reason"].strip() and "NEEDS_REVIEW" not in r["reason"] for r in policy["waivers"]),
    "tracked_scope_snapshot_unchanged": not drift,
    "production_and_fixtures_head_bytes_identical": all(r["identical_to_head"] for r in protected),
    "targeted_commands_all_exit_zero": all(r["exit_code"] == 0 for r in targets),
    "four_internal_mutations_trip_named_assertion": len(mutations) == 4 and all(
        r["status"] == "EXPECTED_ASSERTION_FAILURE" and "G6L-01 closed-subset rejection assertion" in r["failed_assertion"] for r in mutations),
    "m4_all_109_in_full_collection": len(m4_nodes) == 109,
    "full_suite_verified": full["status"] == "PASS" and all(full["checks"].values()),
    "all_112_new_cases_present": sum(x.startswith("tests/test_r12fix_static_closed.py::") for x in full_nodes) == 112,
    "head_unchanged": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, env=env).decode().strip() == "0ce65a44c9c26d99411cee68d7300e7b5521bb40",
}
result = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
          "python_version": sys.version, "policy_waivers": len(policy_keys), "raw_diagnostics": 18630,
          "policy_dependencies": len(policy["dependencies"]),
          "dependency_folders": collections.Counter(p.split('/')[0] for p in policy["dependencies"]),
          "waiver_folders": collections.Counter(r['path'].split('/')[0] for r in policy['waivers']),
          "source_and_fixture_files_head_identical": len(protected), "tracked_files_checked": len(tracked),
          "parameter_grid_checks": grid_checks, "targeted": targets, "full_suite": full}
(HERE / "verification_summary.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"status": result["status"], "checks": checks}, indent=2))
sys.exit(0 if result["status"] == "PASS" else 1)
