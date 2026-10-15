"""Emit M5b shared-domain rule-site counts, never refresh admission pins.

Counts are counterfactual emitted diagnostics: scan each reviewed file once
with its shared review enabled and once with that review disabled, retaining
all ordinary per-site admissions. Sites are distinct (path, function, rule,
line, AST column); identical expressions at two columns are two sites. One
shared review is NOT one site. Historical INT1 source is
read from the M5b rollback anchor, or read-only `git show df4f6f1:path`.
"""
from __future__ import annotations

import ast
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess

import check_exact_construction as gate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/codex/M5b_evidence"


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


@lru_cache(maxsize=None)
def historical_text(path):
    rollback = OUT / "tmp/int1_rollback" / Path(path).name
    if rollback.exists():
        return rollback.read_text(encoding="utf-8")
    return subprocess.check_output(["git", "show", "df4f6f1:" + path], cwd=ROOT).decode("utf-8")


def scoped_nodes(source):
    result = []

    def visit(node, scope=()):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            inner = (*scope, node.name)
            result.append((".".join(inner), node, ast.dump(node, include_attributes=False)))
            # The two passes label decorators/defaults differently: provenance
            # uses their execution scope, subset uses the definition scope.
            # Preserve both labels and resolve each pin by its recorded scope.
            for child in getattr(node, "decorator_list", ()):
                visit(child, scope)
                visit(child, inner)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in (*node.args.defaults, *node.args.kw_defaults):
                    if child is not None:
                        visit(child, scope)
                        visit(child, inner)
                for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs,
                            node.args.vararg, node.args.kwarg):
                    if arg is not None and arg.annotation is not None:
                        visit(arg.annotation, scope)
                if node.returns is not None:
                    visit(node.returns, scope)
            else:
                for child in (*node.bases, *(k.value for k in node.keywords)):
                    visit(child, scope)
            scope = inner
            for child in node.body:
                visit(child, scope)
            return
        if hasattr(node, "lineno"):
            result.append((".".join(scope) or "<module>", node, ast.dump(node, include_attributes=False)))
        for child in ast.iter_child_nodes(node):
            visit(child, scope)

    visit(ast.parse(source))
    return result


def diagnostic_occurrences(source, row):
    path, line, function, rule, code = row
    kinds = {"closed-callable-value": ast.Name, "closed-runtime-reflection": ast.Attribute,
             "closed-import": (ast.Import, ast.ImportFrom), "closed-syntax": ast.Lambda}
    kind = kinds.get(rule, ast.Call)
    matches = [node for scope, node, _ in scoped_nodes(source)
               if scope == function and isinstance(node, kind) and node.lineno == line
               and ast.get_source_segment(source, node) == code]
    if not matches:
        raise AssertionError("rule-site occurrence could not be uniquely classified: " + repr(row))
    return [dict(path=path, line=n.lineno, column=n.col_offset, function=function, rule=rule, source=code)
            for n in matches]


def active_site_counts(policy, historical=False):
    rows_by_path = {}
    for row in policy["waivers"]:
        rows_by_path.setdefault(row["path"], []).append(row)
    sites, active_rows, context_only = {}, [], []
    for path, rows in rows_by_path.items():
        source = historical_text(path) if historical else (ROOT / path).read_text(encoding="utf-8-sig")
        source = source.lstrip("\ufeff")
        contexts, nodes = gate._subset.site_contexts(source), scoped_nodes(source)
        for row in rows:
            if row["context"] != contexts.get(row["function"]):
                continue
            active_rows.append(row)
            located = False
            for scope, node, dump in nodes:
                if scope == row["function"] and dump == row["node"]:
                    located = True
                    key = (path, scope, row["rule"], node.lineno, node.col_offset)
                    sites[key] = row.get("category", "unspecified")
            if not located:
                # These four accepted legacy pins still match a function's
                # context but their AST node exists only in another function.
                # The old stale check searches nodes file-wide. They admit NO
                # current occurrence and must not inflate site counts. Keep
                # their immutable rows, disclose them, reject any new orphan.
                if row["id"] not in {"R12b-L0534", "R12b-L0536", "R12b-L0539", "R12b-L0691"}:
                    raise AssertionError("new admission has no scoped AST occurrence: " + row["id"])
                context_only.append(dict(id=row["id"], path=path, function=row["function"], rule=row["rule"]))
    return dict(active_rows=len(active_rows), distinct_rule_ast_occurrences=len(sites),
                rows_with_actual_scoped_occurrence=len(active_rows)-len(context_only),
                historical_context_only_rows_without_scoped_occurrence=context_only,
                by_path=dict(sorted(Counter(k[0] for k in sites).items())),
                by_rule=dict(sorted(Counter(k[2] for k in sites).items())),
                by_category=dict(sorted(Counter(sites.values()).items())))


def shared_counts(review, historical=False):
    subset = gate._subset
    original = subset.instrumentation_scope
    sites = []
    files = sorted({r["path"] for r in review["scopes"]})
    try:
        for path in files:
            source = historical_text(path) if historical else (ROOT / path).read_text(encoding="utf-8")
            contexts = subset.site_contexts(source)

            def admitted(text, name, function, rule):
                return name == path and rule in review["rules"] and any(
                    row["path"] == path and row["function"] == function
                    and row["context"] == contexts.get(function)
                    and (historical or row.get("module_context") == contexts.get("<module>"))
                    for row in review["scopes"])

            # Current counts must exercise the actual binding checker, including
            # helper-byte and full caller-source pins. Only the old contract is
            # reconstructed for the explicitly historical counterfactual.
            subset.instrumentation_scope = admitted if historical else original
            enabled = set(gate.scan_text(source, path, repository_root=ROOT))
            subset.instrumentation_scope = lambda *args: False
            disabled = set(gate.scan_text(source, path, repository_root=ROOT))
            for row in sorted(disabled-enabled):
                sites.extend(diagnostic_occurrences(source, row))
    finally:
        subset.instrumentation_scope = original
    return dict(review_id=review["id"], review_records=1, scope_count=len(review["scopes"]),
                allowed_rule_count=len(review["rules"]), effective_rule_site_count=len(sites),
                by_rule=dict(sorted(Counter(s["rule"] for s in sites).items())),
                by_scope=dict(sorted(Counter(s["path"]+"::"+s["function"] for s in sites).items())),
                sites=sites)


def main():
    policy = json.loads((ROOT / "tools/exact_construction_policy.json").read_text(encoding="utf-8"))
    old = json.loads(historical_text("tools/exact_construction_policy.json"))
    baseline = shared_counts(old["mutation_instrumentation_review"], historical=True)
    current = shared_counts(policy["mutation_instrumentation_reviews"][-1])
    baseline_sites, current_sites = active_site_counts(old, True), active_site_counts(policy)
    result = dict(schema=1, baseline_revision="df4f6f1", counting_contract=__doc__,
                  old_history_prefix_preserved=policy["waivers"][:len(old["waivers"])] == old["waivers"],
                  old_renewal_prefix_preserved=policy["renewals"][:len(old["renewals"])] == old["renewals"],
                  old_shared_record_preserved=policy["mutation_instrumentation_review"] == old["mutation_instrumentation_review"],
                  baseline_shared=baseline, current_shared=current,
                  shared_rule_site_net_delta=current["effective_rule_site_count"]-baseline["effective_rule_site_count"],
                  current_archived_rows=len(policy["waivers"]), current_context_active_rows=current_sites["active_rows"],
                  baseline_per_site=baseline_sites, current_per_site=current_sites,
                  admitted_rule_site_net_delta=(current_sites["distinct_rule_ast_occurrences"]+current["effective_rule_site_count"]
                                               -baseline_sites["distinct_rule_ast_occurrences"]-baseline["effective_rule_site_count"]),
                  new_rows=policy["waivers"][len(old["waivers"]):],
                  new_renewals=policy["renewals"][len(old["renewals"]):],
                  active_by_category=current_sites["by_category"],
                  proof_boundary=policy["mutation_instrumentation_reviews"][-1]["proof_domain"])
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "admission_rule_sites.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("current_archived_rows", "current_context_active_rows", "shared_rule_site_net_delta")}, ensure_ascii=False))
    print("shared baseline/current rule-sites:", baseline["effective_rule_site_count"], current["effective_rule_site_count"])
    print("evidence:", target.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
