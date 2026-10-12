"""One-off R12 audit assembly; NOT an automatic acceptance/refresh command.

Only exact sites with a separately recorded review can be assembled. Unknown
sites stop this script. Normal scanner execution never runs it.
"""
import ast
import collections
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("r12_gate", ROOT / "tools/check_exact_construction.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def key(row):
    return row["path"], row["function"], row["rule"], row["code"]


def main():
    review_files = [
        "src_waiver_review_candidates.json", "test_waiver_review.json",
        "src_final_waiver_review.json", "test_final_waiver_review.json",
        "test_legacy_call_review.json", "parent_site_review.json",
        "src_positive_subset_review.json", "test_oracle_positive_subset_review.json",
        "test_driver_helpers_positive_subset_review.json",
    ]
    reviews = {}
    for name in review_files:
        p = HERE / name
        if not p.exists():
            continue
        for row in json.loads(p.read_text(encoding="utf-8")):
            reason = row.get("reason", "")
            if (row.get("needs_review") or row.get("status") in ("needs_review", "pending")
                    or not reason.strip() or "NEEDS_REVIEW" in reason):
                continue
            reviews[key(row)] = {**row, "review_origin": name}
    raw = json.loads((HERE / "final_raw_scan_v2.json").read_text(encoding="utf-8"))
    missing, waivers = [], {}
    by_path = collections.defaultdict(list)
    for row in raw:
        by_path[row[0]].append(row)
    for path, rows in by_path.items():
        text = (ROOT / path).read_text(encoding="utf-8-sig")
        tree = ast.parse(text)
        contexts = gate._subset.site_contexts(text)
        closed = {tuple(r[:5]): r for r in gate._subset.closed_subset_issues(text, path, apply_waivers=False)}
        for row in rows:
            path, line, fn, rule, code = row
            review = reviews.get((path, fn, rule, code))
            if not review:
                missing.append({"path": path, "line": line, "function": fn, "rule": rule, "code": code})
                continue
            if tuple(row) in closed:
                node_dump, context = closed[tuple(row)][5:]
            else:
                kind = ast.Call if rule.endswith("-call") or rule in ("rounded-vector", "rounded-root") else (ast.BinOp, ast.AugAssign)
                nodes = [n for n in ast.walk(tree) if isinstance(n, kind)
                         and getattr(n, "lineno", None) == line and ast.get_source_segment(text, n) == code]
                assert nodes and len({ast.dump(n, include_attributes=False) for n in nodes}) == 1, (path, line, fn, rule, code, len(nodes))
                node_dump = ast.dump(nodes[0], include_attributes=False)
                context = contexts[fn]
            unique = (path, fn, rule, node_dump, context)
            waivers[unique] = {"path": path, "function": fn, "rule": rule,
                              "node": node_dump, "context": context, "line": line,
                              "code": code, "reason": review["reason"],
                              "review_origin": review["review_origin"],
                              "category": review.get("category", "manually-reviewed-fixed-site")}
    (HERE / "policy_unreviewed_sites.json").write_text(json.dumps(missing, indent=2), encoding="utf-8")
    print(json.dumps({"raw_issues": len(raw), "distinct_reviewed_waivers": len(waivers),
                      "missing_review": len(missing), "missing_by_rule": collections.Counter(r["rule"] for r in missing)}, indent=2))
    if missing:
        return 1
    target = ROOT / "tools/exact_construction_policy.json"
    policy = json.loads(target.read_text(encoding="utf-8"))
    policy["dependencies"] = gate._subset.dependency_snapshot(ROOT)
    policy["waivers"] = sorted(waivers.values(), key=lambda r: (r["path"], r["line"], r["rule"], r["node"]))
    policy["review_contract"] = (
        "Manual fixed-baseline admissions only, pinned to exact node + module AST and all src/tests/tools Python bytes. "
        "No runtime policy enlargement. Not an arbitrary Python numerical proof. "
        "Legacy approximate diagnostics and test-driver/scaffolding exclusions are not exact geometric oracles."
    )
    target.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
