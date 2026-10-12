"""One-time ROOT decision record for this rejected-policy migration only.

Not a refresh utility: pinned input, exact review-key coverage, and an EMPTY
destination policy are required. This records exclusions, NOT numerical proofs
or reviewer approvals. See manifest_transition_review.md before reading counts.
"""
import collections
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REVIEW_FILES = [
    "src_numerical_review.json", "src_structural_review.json",
    "tests_numerical_review.json", "tests_structural_review.json",
    "src_round5_supplement_review.json", "tests_round5_complete_review.json",
    "tests_round6_supplement_review.json", "src_final_supplement_review.json",
    "tests_final_supplement_review.json",
]
GROUPS = {
    "PROOF_GAP_MANUAL_EXCLUSION": """SOURCE_PROOF_GAP SOURCE_PROOF_GAP_EXACT_FLOW SOURCE_PROOF_GAP_CALLER_SENSITIVE
        SOURCE_PROOF_GAP_EXACT_JET_WRAPPER SOURCE_PROOF_GAP_EXACT_JET PROOF_CONTROL_FLOW_GAP exact_proof_gap""".split(),
    "INPUT_MODEL_OR_OUTPUT_BOUNDARY": """INPUT_PARSE_GIVEN_BINARY64_MODEL REPORTED_OUTPUT_AND_EXACT_LENGTH
        EXACT_FINAL_CONSTRUCTION_BOUNDARY CANDIDATE_CERTIFIED_BY_EXACT_INPUT PUBLIC_GIVEN_PRIMAL_MODEL
        PRIMAL_COMPARISON_NOT_CONSTRUCTION OUTWARD_FILTER_NOT_GEOMETRY TUPLE_DISPLAY_JET_PROTOCOL
        OUTPUT_WRAPPER_WITH_EXACT_JET GIVEN_PROBE_MODEL_EXACT_PREDICATE REVIEWED_FINAL_OUTPUT_OR_DATA
        IMMUTABLE_WITNESS_PROTOCOL OUTPUT_WRAPPER_WITH_EXACT_WITNESS OUTPUT_WITNESS_READBACK
        SUPPLIED_INPUT given_input_fixture_boundary given_input_fixture direct_fixture_dispatch_with_rounded_inputs""".split(),
    "APPROXIMATE_OR_NOMINAL_SCOPE_EXCLUSION": """SCOPED_MODEL_OR_DIAGNOSTIC_NOT_EXACT_APPROVAL
        APPROXIMATE_TRANSCENDENTAL_MODEL_NOT_EXACT APPROXIMATE_MODEL_OR_DIAGNOSTIC_NO_EXACT_APPROVAL
        ORDINARY_DUAL_ARITHMETIC_NOT_EXACT DIAGNOSTIC_NOT_EXACT_TRUTH LEGACY_APPROX_NOT_EXACT
        APPROXIMATE_DIAGNOSTIC_NOT_EXACT APPROXIMATE_CANDIDATE_GENERATION_NOT_EXACT
        NOMINAL_REPORT_NOT_EXACT_EVENT_SET NOMINAL_REPORT_BUDGET_NOT_EXACT_EVENT_SET
        EXPLICIT_ROUNDED_FRAME_MODEL LEGACY_APPROX bounded_legacy_diagnostic legacy_approximate_oracle
        legacy_approximate_diagnostic""".split(),
    "STRUCTURAL_DATA_OR_PROTOCOL_REVIEW": """DATA_COLLECTION_OR_LABELING DECLARATION_OR_TYPE_DATA
        DATA_SERIALIZATION_REFLECTION DATA_SERIALIZATION_PUBLIC_FACTORY SCALAR_PROTOCOL_DECLARATION
        VALIDATION_ERROR_PATH ORDINARY_DATA_OPERATION CACHE_IDENTITY_NOT_DISPATCH TYPE_GUARDED_FIELD_DATA
        NONFINITE_REPORT_BRANCH PUBLIC_OPTION_FORWARDING DATA_CONTAINER_FACTORY METADATA_OR_IO metadata""".split(),
    "TEST_EXECUTION_OR_INTENTIONAL_DEFECT": """TEST_ASSERTION_PROTOCOL test_harness MUTATION_HARNESS ACTUAL_BAD
        test_execution_legacy_contact_window test_execution_with_approx_diagnostic test_execution_direct_api test_execution""".split(),
    "UNFINISHED_NUMERICAL_DYNAMIC_REWRITE": ["DYNAMIC_NUMERIC_REWRITE"],
    "PUBLIC_DIAGNOSTIC_CALLBACK": ["REQUIRED_PUBLIC_DIAGNOSTIC_CALLBACK"],
}


def key(row):
    return tuple(row[k] for k in ("path", "function", "rule", "node"))


def main():
    policy = json.loads((ROOT / "tools/exact_construction_policy.json").read_text("utf-8"))
    assert policy["waivers"] == [], "Not a renewal tool: only the first migration from the empty staging policy is allowed"
    raw_path = HERE / "raw_frozen.json"
    assert hashlib.sha256(raw_path.read_bytes()).hexdigest() == "3d6796612973030aeba448e1b71c3f992271319a54915d48ee364c20111f52ae"
    raw = {key(row): row for row in json.loads(raw_path.read_text("utf-8"))}
    assert len(raw) == 2365
    reviewed = {}
    for file in REVIEW_FILES:
        data = json.loads((HERE / file).read_text("utf-8"))
        rows = data if isinstance(data, list) else data.get("items", data.get("sites", []))
        for row in rows:
            reviewed[key(row)] = file, row
    assert set(raw) <= set(reviewed), sorted(set(raw) - set(reviewed))
    disposition_group = {detail: group for group, details in GROUPS.items() for detail in details}
    assert len(disposition_group) == sum(map(len, GROUPS.values()))
    spec = importlib.util.spec_from_file_location("initial_local_scope_reader", ROOT / "tools/exact_construction_subset.py")
    subset = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(subset)
    contexts, decisions = {}, []
    for number, (site_key, row) in enumerate(sorted(raw.items()), 1):
        file, review = reviewed[site_key]
        disposition = review["disposition"]
        category = disposition_group[disposition]
        path = row["path"]
        if path not in contexts:
            contexts[path] = subset.site_contexts((ROOT / path).read_text(encoding="utf-8-sig"))
        decisions.append({
            "id": f"R12b-L{number:04d}",
            **{k: row[k] for k in ("path", "function", "rule", "node", "source")},
            "context": contexts[path][row["function"]], "line_at_review": row["line"],
            "category": category, "review_disposition": disposition,
            "decision": "LOCAL_LEGACY_EXCLUSION_NOT_MACHINE_PROOF",
            "decision_owner": "root", "reviewer_waiver_approval_claimed": False,
            "reason": review["reason"],
            "review_evidence": "reports/codex/R12FIXb_evidence/" + file,
        })
    ledger = {
        "completion": "PARTIAL", "count": len(decisions), "target_maximum": 200,
        "decision_statement": "本轮未完成验收。root 将已逐站点审核的现有遗留范围记为局部过渡排除；不是审阅者批准或机器数值证明。证明缺口、真实近似与未改动态仍是未完成项，零诊断只说明此清单生效。",
        "no_refresh_contract": "只装本次固定源码上的初始清单；禁止整体更新指纹。之后每一变动作用域须重新审阅。独立G6未执行。",
        "scope_hash_note": "初始指纹采用最终局部源码算法（含尾部缩进注释、同名分支候选组）；不包含全库依赖hash。",
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "review_files": REVIEW_FILES, "decisions": decisions,
    }
    destination = HERE / "local_review_decisions.json"
    assert not destination.exists(), "Do not overwrite the root decision history"
    destination.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="")
    counts = dict(collections.Counter(row["category"] for row in decisions))
    stats = {"waivers": len(decisions), "original_waivers": 16936, "within_200": False,
             "unique_ast_sites": len({(r["path"], r["function"], r["node"]) for r in decisions}),
             "scope_count": len({(r["path"], r["function"]) for r in decisions}),
             "by_category": counts, "by_disposition": dict(collections.Counter(r["review_disposition"] for r in decisions)),
             "by_rule": dict(collections.Counter(r["rule"] for r in decisions)),
             "by_path": dict(collections.Counter(r["path"] for r in decisions)),
             "representatives": {group: [r for r in decisions if r["category"] == group][:2] for group in counts},
             "unreviewed_keys": 0, "reviewer_approvals_claimed": 0,
             "source_vs_tests": dict(collections.Counter(r["path"].split('/')[0] for r in decisions))}
    (HERE / "local_manifest_statistics.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"waivers": len(decisions), "by_category": counts, "scope_count": stats["scope_count"]}))


if __name__ == "__main__":
    main()
