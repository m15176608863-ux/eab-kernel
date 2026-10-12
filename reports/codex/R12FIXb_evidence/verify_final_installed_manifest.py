"""Read-only verification of the installed local ledger; never installs policy."""
import ast
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("final_installed_review_subset", ROOT / "tools/exact_construction_subset.py")
subset = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subset)

policy_path = ROOT / "tools/exact_construction_policy.json"
ledger_path = HERE / "local_review_decisions.json"
policy = json.loads(policy_path.read_text(encoding="utf-8"))
ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
statistics = json.loads((HERE / "local_manifest_statistics.json").read_text(encoding="utf-8"))
installed = json.loads((HERE / "local_manifest_install.json").read_text(encoding="utf-8"))
rows = policy["waivers"]
fields = ("id", "path", "function", "rule", "node", "context", "category", "reason", "review_evidence")
assert policy["schema"] == 2
assert not any("dependenc" in key.lower() or "snapshot" in key.lower() for key in policy)
assert len(rows) == ledger["count"] == statistics["waivers"] == installed["waivers"] == 2365
assert rows == [{key: row[key] for key in fields} for row in ledger["decisions"]]
assert all(row["decision"] == "LOCAL_LEGACY_EXCLUSION_NOT_MACHINE_PROOF" and row["decision_owner"] == "root"
           and row["reviewer_waiver_approval_claimed"] is False for row in ledger["decisions"])
assert ledger["completion"] == "PARTIAL" and ledger["target_maximum"] == 200
assert statistics["within_200"] is False
keys, ids, files = set(), set(), {}
for row in rows:
    assert set(row) == set(fields)
    assert all(isinstance(row[field], str) and row[field].strip() for field in fields)
    assert re.fullmatch("[0-9a-f]{64}", row["context"])
    path = (ROOT / row["path"]).resolve()
    assert path.is_relative_to(ROOT) and row["path"].startswith(("src/", "tests/"))
    assert (ROOT / row["review_evidence"]).is_file()
    marker = tuple(row[field] for field in ("path", "function", "rule", "node"))
    assert marker not in keys and row["id"] not in ids
    keys.add(marker)
    ids.add(row["id"])
    if row["path"] not in files:
        text = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(text)
        scopes = {"<module>": [tree]}
        def visit(node, prefix=""):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    name = prefix + child.name
                    scopes.setdefault(name, []).append(child)
                    visit(child, name + ".")
                else:
                    visit(child, prefix)
        visit(tree)
        files[row["path"]] = subset.site_contexts(text), {
            name: {ast.dump(node, include_attributes=False) for scope in candidates for node in ast.walk(scope)}
            for name, candidates in scopes.items()}
    contexts, scope_nodes = files[row["path"]]
    assert contexts[row["function"]] == row["context"], ("expired scope", row["id"])
    assert row["node"] in scope_nodes[row["function"]], ("AST absent from named scope", row["id"])

categories = dict(Counter(row["category"] for row in rows))
assert categories == statistics["by_category"]
assert categories["UNFINISHED_NUMERICAL_DYNAMIC_REWRITE"] == 34
assert len({(row["path"], row["function"]) for row in rows}) == statistics["scope_count"]
assert len({(row["path"], row["function"], row["node"]) for row in rows}) == statistics["unique_ast_sites"]
policy_hash = hashlib.sha256(policy_path.read_bytes()).hexdigest()
ledger_hash = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
assert policy_hash == installed["policy_sha256"]
assert ledger_hash == installed["ledger_sha256"]
assert installed["no_stored_fingerprint_was_refreshed_or_replaced"] is True
assert installed["current_contexts_recomputed_for_comparison_only"] is True
result = {
    "status": "MECHANICAL_LOCAL_MANIFEST_CHECK_PASSED_NOT_NUMERICAL_APPROVAL",
    "waivers": len(rows), "files_with_waivers": len(files), "scope_count": statistics["scope_count"],
    "unique_ast_sites": statistics["unique_ast_sites"], "unfinished_dynamic_rows": 34,
    "policy_sha256": policy_hash, "ledger_sha256": ledger_hash, "by_category": categories,
    "dependency_snapshot_fields": [], "all_scopes_and_ast_nodes_match": True,
    "policy_is_exact_stored_ledger_projection": True, "all_evidence_files_exist": True,
    "completion": "PARTIAL", "independent_G6": False, "numerical_waivers_approved_by_this_review": 0,
}
(HERE / "final_installed_manifest_review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
