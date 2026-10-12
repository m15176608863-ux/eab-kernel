"""Replay the frozen R12FIXb decision ledger, never refresh a review.

This evidence-only installer accepts no scan output and calculates no replacement
fingerprints. Every stored AST/context must still match. A later source edit
therefore fails here just as it fails the gate: it cannot renew a waiver.
"""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("reviewed_local_subset", ROOT / "tools/exact_construction_subset.py")
subset = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subset)


def main():
    ledger = json.loads((HERE / "local_review_decisions.json").read_text(encoding="utf-8"))
    rows = ledger["decisions"]
    assert rows and ledger["completion"] == "PARTIAL"
    contexts = {}
    keys = set()
    for row in rows:
        assert row["decision"] == "LOCAL_LEGACY_EXCLUSION_NOT_MACHINE_PROOF"
        assert row["reason"].strip() and row["review_evidence"]
        path = row["path"]
        if path not in contexts:
            text = (ROOT / path).read_text(encoding="utf-8-sig")
            contexts[path] = subset.site_contexts(text), {
                ast.dump(node, include_attributes=False) for node in ast.walk(ast.parse(text))}
        scope, nodes = contexts[path]
        assert scope[row["function"]] == row["context"], ("Expired review: do not refresh", row["id"])
        assert row["node"] in nodes, ("Removed AST site", row["id"])
        key = tuple(row[k] for k in ("path", "function", "rule", "node"))
        assert key not in keys
        keys.add(key)
    policy_path = ROOT / "tools/exact_construction_policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    assert not any("dependenc" in key for key in policy)
    policy["schema"] = 2
    policy["review_contract"] = (
        "Local AST site and minimal enclosing source SHA256 only. No dependency snapshot; "
        "no automatic refresh. PARTIAL legacy inventory: see R12FIXb_report.md for count, "
        "proof gaps, approximate scope exclusions and unfinished numerical rewrites.")
    policy["waivers"] = [{k: row[k] for k in (
        "id", "path", "function", "rule", "node", "context", "category", "reason", "review_evidence")} for row in rows]
    payload = json.dumps(policy, ensure_ascii=False, indent=2) + "\n"
    policy_path.write_text(payload, encoding="utf-8", newline="")
    result = {"waivers": len(rows), "policy_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
              "ledger_sha256": hashlib.sha256((HERE / "local_review_decisions.json").read_bytes()).hexdigest(),
              "no_stored_fingerprint_was_refreshed_or_replaced": True,
              "current_contexts_recomputed_for_comparison_only": True}
    (HERE / "local_manifest_install.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
