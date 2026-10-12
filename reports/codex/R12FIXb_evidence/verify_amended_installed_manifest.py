"""Read-only check of an explicitly named amended ledger and its receipt."""
import argparse
import ast
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--ledger", required=True)
parser.add_argument("--receipt", required=True)
parser.add_argument("--statistics", default="local_manifest_statistics_release.json")
args = parser.parse_args()

def read(name):
    path = (HERE / name).resolve()
    assert path.is_relative_to(HERE)
    return json.loads(path.read_text(encoding="utf-8"))

spec = importlib.util.spec_from_file_location("amended_review_subset", ROOT / "tools/exact_construction_subset.py")
subset = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subset)
policy_path = ROOT / "tools/exact_construction_policy.json"
policy = json.loads(policy_path.read_text(encoding="utf-8"))
ledger = read(args.ledger)
receipt = read(args.receipt)
stats = read(args.statistics)
originals = {r["id"]: r for r in read("local_review_decisions.json")["decisions"]}
bindings = {r["id"]: r for r in read("fingerprint_extraction_corrections.json")}
metadata = {r["id"]: r for r in read("suggested_metadata_corrections.json")["corrections"]}
metadata.update({r["id"]: r for r in read("src_final_reason_metadata_corrections.json")["corrections"]})
utf8 = {r["id"]: r for r in read("src_reason_utf8_corrections.json")["corrections"]}
rows = policy["waivers"]
fields = ("id", "path", "function", "rule", "node", "context", "category", "reason", "review_evidence")
assert policy["schema"] == 2
assert not any("dependenc" in k.lower() or "snapshot" in k.lower() for k in policy)
assert len(rows) == ledger["count"] == stats["waivers"] == 2365
assert rows == [{k: r[k] for k in fields} for r in ledger["decisions"]]
assert set(originals) == {r["id"] for r in rows}
assert ledger["completion"] == "PARTIAL" and ledger["target_maximum"] == 200
assert stats["within_200"] is False
keys, files = set(), {}
for row in rows:
    old = originals[row["id"]]
    assert set(row) == set(fields)
    assert all(isinstance(row[k], str) and row[k].strip() for k in fields)
    assert re.fullmatch("[0-9a-f]{64}", row["context"])
    assert all(row[k] == old[k] for k in ("path", "function", "rule", "context"))
    expected_node = bindings[row["id"]]["after_node"] if row["id"] in bindings else old["node"]
    assert row["node"] == expected_node
    expected_reason = utf8[row["id"]]["reason"] if row["id"] in utf8 else metadata[row["id"]]["new_reason"] if row["id"] in metadata else old["reason"]
    assert row["reason"] == expected_reason
    if row["id"] in utf8:
        assert "?" not in row["reason"] and "\ufffd" not in row["reason"]
        assert any("\u4e00" <= c <= "\u9fff" for c in row["reason"])
    assert row["category"] == (metadata[row["id"]]["new_category"] if row["id"] in metadata else old["category"])
    marker = tuple(row[k] for k in ("path", "function", "rule", "node"))
    assert marker not in keys
    keys.add(marker)
    path = (ROOT / row["path"]).resolve()
    assert path.is_relative_to(ROOT) and row["path"].startswith(("src/", "tests/"))
    assert (ROOT / row["review_evidence"]).is_file()
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
            name: {ast.dump(n, include_attributes=False) for s in candidates for n in ast.walk(s)}
            for name, candidates in scopes.items()}
    contexts, nodes = files[row["path"]]
    assert contexts[row["function"]] == row["context"], row["id"]
    assert row["node"] in nodes[row["function"]], row["id"]

assert all(r["decision"] == "LOCAL_LEGACY_EXCLUSION_NOT_MACHINE_PROOF" and r["decision_owner"] == "root"
           and r["reviewer_waiver_approval_claimed"] is False for r in ledger["decisions"])
for row in ledger["decisions"]:
    expected_disposition = utf8[row["id"]]["disposition"] if row["id"] in utf8 else metadata[row["id"]]["new_review_disposition"] if row["id"] in metadata else originals[row["id"]]["review_disposition"]
    assert row["review_disposition"] == expected_disposition
categories = dict(Counter(r["category"] for r in rows))
assert categories == stats["by_category"]
assert categories["UNFINISHED_NUMERICAL_DYNAMIC_REWRITE"] == 16
assert len({(r["path"], r["function"]) for r in rows}) == stats["scope_count"]
assert len({(r["path"], r["function"], r["node"]) for r in rows}) == stats["unique_ast_sites"]
policy_hash = hashlib.sha256(policy_path.read_bytes()).hexdigest()
ledger_hash = hashlib.sha256((HERE / args.ledger).read_bytes()).hexdigest()
assert policy_hash == receipt["policy_sha256"]
assert ledger_hash == receipt["ledger_sha256"]
result = {
    "status": "AMENDED_MECHANICAL_LOCAL_MANIFEST_CHECK_PASSED_NOT_NUMERICAL_APPROVAL",
    "ledger": args.ledger, "receipt": args.receipt, "statistics": args.statistics,
    "waivers": len(rows), "files_with_waivers": len(files), "scope_count": stats["scope_count"],
    "unique_ast_sites": stats["unique_ast_sites"], "by_category": categories,
    "policy_sha256": policy_hash, "ledger_sha256": ledger_hash,
    "all_local_scopes_and_nodes_match": True, "new_waivers": 0, "scope_hashes_refreshed": 0,
    "explicit_expr_binding_corrections": len(bindings), "explicit_metadata_corrections": len(metadata),
    "explicit_utf8_reason_repairs": len(utf8), "corrupt_repaired_reasons": 0,
    "policy_is_exact_stored_ledger_projection": True, "dependency_snapshot_fields": [],
    "completion": "PARTIAL", "independent_G6": False, "numerical_waivers_approved_by_this_review": 0,
}
(HERE / "final_installed_manifest_review_verified.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="")
print(json.dumps(result, ensure_ascii=False, indent=2))
