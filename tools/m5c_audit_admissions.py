"""M5c counterfactual emitted-diagnostic rule-site audit, without policy edits.

Count distinct (path, function, rule, line, AST column), not archive rows.
For each policy-touched file compare the actual scan to a scan with all site
admissions and shared instrumentation disabled. Separately disable shared
instrumentation alone to identify its actual marginal contribution.
"""
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from m5b_audit_admissions import scoped_nodes

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/codex/M5c_evidence"


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":"))+"\n", encoding="utf-8")


def audit(source, label):
    source = Path(source)
    spec = importlib.util.spec_from_file_location("counterfactual_gate_"+label, source / "tools/check_exact_construction.py")
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    subset = gate._subset
    policy = subset._policy()
    original_scope = subset.instrumentation_scope
    review = policy["mutation_instrumentation_reviews"][-1]
    shared_paths = {r["path"] for r in review["scopes"]}
    paths = sorted({r["path"] for r in policy["waivers"]} | shared_paths)
    disabled_policy = copy.deepcopy(policy)
    disabled_policy["waivers"] = []
    total, shared, violations = set(), set(), []
    for number, path in enumerate(paths, 1):
        text = (source / path).read_text(encoding="utf-8-sig")
        subset._policy = lambda: policy
        subset.instrumentation_scope = original_scope
        enabled = set(gate.scan_text(text, path, repository_root=source))
        violations.extend(enabled)
        subset._policy = lambda: disabled_policy
        subset.instrumentation_scope = lambda *args: False
        disabled = set(gate.scan_text(text, path, repository_root=source))
        shared_disabled = set()
        if path in shared_paths:
            subset._policy = lambda: policy
            shared_disabled = set(gate.scan_text(text, path, repository_root=source))
        nodes = scoped_nodes(text)
        for rows, destination in ((disabled-enabled, total), (shared_disabled-enabled, shared)):
            for _, line, function, rule, code in rows:
                locations = {n.col_offset for scope, n, _ in nodes
                             if scope == function and getattr(n, "lineno", None) == line
                             and __import__("ast").get_source_segment(text, n) == code}
                if not locations:
                    raise AssertionError("unlocated emitted diagnostic: "+repr((path, line, function, rule, code)))
                destination.update((path, function, rule, line, col) for col in locations)
        write(OUT / "tmp" / (label+"_admission_progress.json"), dict(complete=False, files=number, total=len(paths), sites=len(total)))
    if violations:
        raise AssertionError("enabled static diagnostics in policy-touched files: "+repr(violations[:10]))
    result = dict(complete=True, files=len(paths), effective_rule_site_count=len(total),
                  shared_marginal_rule_site_count=len(shared),
                  per_site_or_overlap_count=len(total-shared),
                  by_path=dict(sorted(Counter(x[0] for x in total).items())),
                  by_rule=dict(sorted(Counter(x[2] for x in total).items())),
                  sites=[list(x) for x in sorted(total)], shared_marginal_sites=[list(x) for x in sorted(shared)],
                  policy_sha256=hashlib.sha256((source / "tools/exact_construction_policy.json").read_bytes()).hexdigest())
    write(OUT / "tmp" / (label+"_admission_progress.json"), dict(complete=True, files=len(paths), sites=len(total)))
    return result


def main():
    baseline = OUT / "tmp/baseline_suite_export"
    if not baseline.is_dir():
        raise ValueError("fresh baseline byte export required")
    with ProcessPoolExecutor(max_workers=2) as pool:
        old_future = pool.submit(audit, baseline, "baseline")
        new_future = pool.submit(audit, ROOT, "current")
        old, new = old_future.result(), new_future.result()
    # Source line numbers can move without adding an admitted occurrence.
    delta = new["effective_rule_site_count"]-old["effective_rule_site_count"]
    result = dict(schema="eab.m5c-counterfactual-admissions.v1", complete=True,
                  baseline_revision="efb0dfe514a1f60c44e6341b69cce77ff5c9ec17",
                  counting_contract=__doc__, baseline=old, current=new,
                  admitted_rule_site_net_delta=delta,
                  policy_bytes_unchanged=old["policy_sha256"] == new["policy_sha256"])
    write(OUT / "admission_rule_sites.json", result)
    print("M5C_COUNTERFACTUAL_ADMISSIONS", old["effective_rule_site_count"], new["effective_rule_site_count"], "delta", delta, flush=True)


if __name__ == "__main__":
    main()
