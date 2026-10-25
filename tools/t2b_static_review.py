"""Extract review candidates; never write a policy or grant an admission.

Candidate rows have empty reasons. A separate, explicitly reviewed copy is
required to emit a ledger. Scanners and baseline policy fields remain intact.
This finite source review is not a proof of numerical correctness.
"""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

import check_exact_construction as gate
import exact_construction_subset as subset
from m5b_audit_admissions import scoped_nodes


ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = Path("D:/eab-evidence/reports/codex/T2b_evidence")
REVIEW = "reports/codex/T2b_report.md#t2b-static-admission-review"
BASE_WAIVERS = 3659
BASE_POLICY_SHA = "621df0519431552c8cea255cf756f1bcb5c3acc90cb301ff0048649b1916cc5d"
BASE_WAIVERS_SHA = "abc03a3b28102e3790205a1c88ef3ccb8a5cb09f39216f1438738953644be5a9"
BASE_OTHER_SHA = "30e730ae82715ca70d3ab89b453276f1929915229fa2fa9022859edbb66963e5"
SCANNERS = {
    "tools/check_exact_construction.py": "cc6143a27369f1247718b2e48ae80f3afb7b5060b23de845437a53b5a0768517",
    "tools/exact_construction_subset.py": "35e6262a7c36ea5f20679f047dd6f030feeb6fcbe8be7813573212829b503274",
    "tools/exact_construction_flow.py": "814f00ab607726c7753fa86ddedc08fd728eb48c4e57b8a61dda55140c3cd1db",
}
PROOF_GAPS = frozenset({
    "closed-unproved-call", "closed-import-call", "closed-method-call",
    "closed-unknown-member", "closed-callable-value", "closed-dynamic-call",
    "closed-data-attribute", "closed-unknown-call", "closed-runtime-reflection",
})
POLICY_KEYS = ("path", "function", "rule", "node", "context", "category",
               "reason", "review_evidence", "id")
AUTHORED_SOURCES = (
    "src/eab/kernel2d/se2_cage.py",
    "tests/t2b_cage_fixtures.py", "tests/t2b_truth_geometry_prod.py",
    "tests/test_t2b_cage.py", "tests/test_t2b_metamorphic.py",
    "tests/test_t2b_mutations.py", "tests/test_t2b_ordering.py",
    "tests/test_t2b_proposer.py", "tests/test_t2b_replay.py",
    "tests/test_t2b_static_admissions.py",
)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def source_allowed(path):
    # Explicit inventory avoids inspecting another session's independently
    # authored verifier or truth geometry merely because its name contains T2b.
    return Path(path).as_posix() in AUTHORED_SOURCES


def verify_baseline(root=ROOT):
    root = Path(root)
    policy = json.loads((root / "tools/exact_construction_policy.json").read_text("utf-8"))
    assert digest(policy["waivers"][:BASE_WAIVERS]) == BASE_WAIVERS_SHA
    assert digest({k: v for k, v in policy.items() if k != "waivers"}) == BASE_OTHER_SHA
    assert len(policy["imports"]) == 648 and len(policy["members"]) == 432
    for path, expected in SCANNERS.items():
        assert hashlib.sha256((root / path).read_bytes()).hexdigest() == expected, path
    return policy


def counts(entries):
    return {
        "total": len(entries),
        "src": sum(row["path"].startswith("src/") for row in entries),
        "tests": sum(row["path"].startswith("tests/") for row in entries),
        "by_rule": dict(sorted(Counter(row["rule"] for row in entries).items())),
        "src_by_rule": dict(sorted(Counter(row["rule"] for row in entries
                                           if row["path"].startswith("src/")).items())),
        "tests_by_rule": dict(sorted(Counter(row["rule"] for row in entries
                                             if row["path"].startswith("tests/")).items())),
    }


def audit_scope(source, function):
    """Reject floating operations in the actual reviewed lexical scope.

    Ordinary aliases are followed. This deliberately finite check does not
    prove arbitrary Python dispatch safe and grants no exemption to a scanner.
    """
    tree = ast.parse(source)
    aliases = {}

    def dotted(node):
        if isinstance(node, ast.Name):
            return aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            return dotted(node.value) + "." + node.attr
        return ""

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                aliases[item.asname or item.name.split(".")[0]] = item.name
        elif isinstance(node, ast.ImportFrom):
            for item in node.names:
                aliases[item.asname or item.name] = (node.module or "") + "." + item.name
    for _ in range(sum(isinstance(node, ast.Assign) for node in ast.walk(tree)) + 1):
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, (ast.Name, ast.Attribute)):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        value = dotted(node.value)
                        if aliases.get(target.id) != value:
                            aliases[target.id] = value
                            changed = True
        if not changed:
            break
    definitions = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    selected = [node for node in tree.body if not isinstance(node, definitions)] if function == "<module>" else []
    pending = [(tree, ())]
    while pending:
        node, names = pending.pop()
        if isinstance(node, definitions):
            names = (*names, node.name)
            if ".".join(names) == function:
                selected.append(node)
        pending.extend((child, names) for child in ast.iter_child_nodes(node))
    assert selected, "reviewed lexical scope must exist"
    forbidden = []
    for scope in selected:
        annotations = set()
        for node in ast.walk(scope):
            annotation = (node.annotation if isinstance(node, (ast.arg, ast.AnnAssign))
                          else node.returns if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else None)
            if annotation is not None:
                annotations.update(id(item) for item in ast.walk(annotation))
        for node in ast.walk(scope):
            name = dotted(node)
            if name in {"float", "builtins.float"} or name.startswith((
                    "math.", "numpy.", "struct.", "ctypes.", "float.", "builtins.float.")):
                forbidden.append((node.lineno, name))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = [item.name for item in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                if any(value.split(".")[0] in {"math", "numpy", "struct", "ctypes"} for value in modules):
                    forbidden.append((node.lineno, "floating/binary64 import"))
            elif isinstance(node, ast.Constant) and type(node.value) is float:
                forbidden.append((node.lineno, "floating literal"))
            elif isinstance(node, ast.BinOp) and id(node) not in annotations and isinstance(
                    node.op, (ast.LShift, ast.RShift, ast.BitAnd, ast.BitOr, ast.BitXor)):
                forbidden.append((node.lineno, "binary bit operation"))
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Invert):
                forbidden.append((node.lineno, "binary bit operation"))
    assert not forbidden, "semantic exact-reuse scope excludes floating/binary64 operations: " + repr(forbidden)


def diagnostic_sites(source, diagnostic):
    """Resolve the scanner's actual AST kind, not same-text Expr wrappers."""
    _, line, function, rule, code = diagnostic
    kinds = {"closed-callable-value": (ast.Name, ast.Attribute),
             "closed-runtime-reflection": (ast.Name, ast.Attribute),
             "closed-data-attribute": ast.Attribute}
    kind = kinds.get(rule, ast.Call)
    matches = {(node.lineno, node.col_offset, dump): node
               for scope, node, dump in scoped_nodes(source) if scope == function
               and isinstance(node, kind) and node.lineno == line
               and ast.get_source_segment(source, node) == code}
    assert matches, ("unresolved exact AST site", diagnostic)
    return matches


def candidate_rows(paths, root=ROOT):
    """Current diagnostics become unapproved, source-pinned review candidates."""
    root = Path(root)
    verify_baseline(root)
    grouped = {}
    rejected = []
    diagnostics_count = 0
    for path in sorted(set(paths)):
        assert source_allowed(path), path
        source = (root / path).read_text("utf-8")
        contexts = subset.site_contexts(source)
        nodes = scoped_nodes(source)
        diagnostics = gate.scan_text(source, path, repository_root=root)
        diagnostics_count += len(diagnostics)
        for diagnostic in diagnostics:
            name, line, function, rule, code = diagnostic
            if rule not in PROOF_GAPS:
                rejected.append(dict(path=name, line=line, function=function, rule=rule, source=code))
                continue
            matches = diagnostic_sites(source, diagnostic)
            for (site_line, column, dump), node in sorted(matches.items()):
                key = (path, function, rule, dump, contexts[function])
                if key in grouped:
                    continue
                # The scanner's actual waiver key has no line/column. Record
                # every occurrence admitted by that exact scoped AST key, not
                # duplicate grants for the same key or only its first use.
                occurrences = sorted({(item.lineno, item.col_offset,
                                       ast.get_source_segment(source, item))
                                      for scope, item, item_dump in nodes
                                      if scope == function and item_dump == dump})
                first_line, first_column, first_source = occurrences[0]
                grouped[key] = dict(path=path, function=function, rule=rule, node=dump,
                    context=contexts[function], category="T2B_EXACT_REUSE_SITE_REVIEW",
                    reason="", review_evidence=REVIEW, line=first_line, column=first_column,
                    source_expression=first_source, source_contexts={function: contexts[function]},
                    occurrences=[dict(line=line, column=column, source_expression=expression)
                                 for line, column, expression in occurrences])
    result = list(grouped.values())
    for index, row in enumerate(result, 1):
        row["id"] = f"T2B-S{index:04d}"
    return dict(schema="t2b-static-review-candidates-1", approved=False,
                entries=result, counts=counts(result), forbidden_diagnostics=rejected,
                diagnostics_count=diagnostics_count,
                rule_site_occurrence_count=sum(len(row["occurrences"]) for row in result))


def verify_entry(row, root=ROOT):
    assert source_allowed(row["path"]), row["path"]
    assert row["rule"] in PROOF_GAPS, "semantic: only enumerated exact-reuse proof gaps may be admitted"
    assert row["category"] == "T2B_EXACT_REUSE_SITE_REVIEW"
    assert row["id"].startswith("T2B-S") and row["review_evidence"] == REVIEW
    assert len(row["reason"].strip()) >= 24 and "TODO" not in row["reason"], "an explicit site review is required"
    source = (Path(root) / row["path"]).read_text("utf-8")
    contexts = subset.site_contexts(source)
    assert contexts[row["function"]] == row["context"], "reviewed source changed"
    matches = [(node, dump) for scope, node, dump in scoped_nodes(source)
               if scope == row["function"] and dump == row["node"]
               and getattr(node, "lineno", None) == row["line"]
               and node.col_offset == row["column"]]
    assert len(matches) == 1, "reviewed node absent from its exact lexical source site"
    assert ast.get_source_segment(source, matches[0][0]) == row["source_expression"]
    occurrences = sorted({(node.lineno, node.col_offset, ast.get_source_segment(source, node))
                          for scope, node, dump in scoped_nodes(source)
                          if scope == row["function"] and dump == row["node"]})
    assert row["occurrences"] == [dict(line=line, column=column, source_expression=expression)
                                  for line, column, expression in occurrences]
    assert row["occurrences"][0] == {key: row[key] for key in ("line", "column", "source_expression")}
    assert row["source_contexts"] == {row["function"]: row["context"]}
    audit_scope(source, row["function"])


def reviewed_ledger(reviewed, root=ROOT):
    """Validate manually supplied reasons and pins; do not apply policy rows."""
    verify_baseline(root)
    assert reviewed["approved"] is True, "candidate extraction is not human review"
    assert not reviewed["forbidden_diagnostics"], "forbidden diagnostics cannot be reviewed away"
    entries = reviewed["entries"]
    assert len({row["id"] for row in entries}) == len(entries)
    assert len({tuple(row[key] for key in ("path", "function", "rule", "node", "context"))
                for row in entries}) == len(entries), "duplicate admission key"
    for row in entries:
        verify_entry(row, root)
    return dict(schema="t2b-static-admissions-1", review_evidence=REVIEW,
        baseline_policy=dict(sha256=BASE_POLICY_SHA, waiver_count=BASE_WAIVERS,
            imports_count=648, members_count=432, waivers_sha256=BASE_WAIVERS_SHA,
            nonwaiver_sha256=BASE_OTHER_SHA),
        analyzers=[dict(path=path, sha256=sha) for path, sha in SCANNERS.items()],
        counts=counts(entries), entries=entries,
        diagnostics_count=reviewed["diagnostics_count"],
        rule_site_occurrence_count=sum(len(row["occurrences"]) for row in entries),
        policy_rows=[{key: row[key] for key in POLICY_KEYS} for row in entries])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--candidates", action="store_true")
    mode.add_argument("--reviewed", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    destination = args.output.resolve()
    assert (destination.is_relative_to(EXTERNAL.resolve())
            or destination.is_relative_to((ROOT / "reports/codex/T2b_evidence").resolve())), "output escaped this work order"
    assert not destination.exists(), "review artifacts are append-only; choose a new output"
    before = (ROOT / "tools/exact_construction_policy.json").read_bytes()
    if args.candidates:
        result = candidate_rows(AUTHORED_SOURCES)
    else:
        result = reviewed_ledger(json.loads(args.reviewed.read_text("utf-8")))
    assert before == (ROOT / "tools/exact_construction_policy.json").read_bytes(), "read-only review changed policy"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes((json.dumps(result, ensure_ascii=False, indent=2)+"\n").encode("utf-8"))
    print(json.dumps(dict(output=str(destination), counts=result["counts"],
                          policy_written=False, forbidden=len(result.get("forbidden_diagnostics", ())))))
    return 1 if result.get("forbidden_diagnostics") else 0


if __name__ == "__main__":
    raise SystemExit(main())
