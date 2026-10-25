"""Site-pinned T2b proof-gap reviews, never numerical exactness proofs.

The primary oracle here is literal baseline/AST/source inspection, not the
construction scanner. Floating defects are injected inside a real production
function and must fail a semantic source assertion, independently of hashes.
"""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

import pytest

import exact_construction_subset as subset
import t2b_static_review as review


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "reports/codex/T2b_evidence/static_admissions.json"


def test_t2b_static_baseline_and_three_scanners_are_unchanged():
    assert review.BASE_WAIVERS == 3659
    assert review.BASE_POLICY_SHA == "621df0519431552c8cea255cf756f1bcb5c3acc90cb301ff0048649b1916cc5d"
    assert review.BASE_WAIVERS_SHA == "abc03a3b28102e3790205a1c88ef3ccb8a5cb09f39216f1438738953644be5a9"
    assert review.BASE_OTHER_SHA == "30e730ae82715ca70d3ab89b453276f1929915229fa2fa9022859edbb66963e5"
    assert review.SCANNERS == {
        "tools/check_exact_construction.py": "cc6143a27369f1247718b2e48ae80f3afb7b5060b23de845437a53b5a0768517",
        "tools/exact_construction_subset.py": "35e6262a7c36ea5f20679f047dd6f030feeb6fcbe8be7813573212829b503274",
        "tools/exact_construction_flow.py": "814f00ab607726c7753fa86ddedc08fd728eb48c4e57b8a61dda55140c3cd1db",
    }
    review.verify_baseline(ROOT)


def test_t2b_reviewed_sites_match_policy_source_and_report_counts():
    def digest(value):
        return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                         separators=(",", ":")).encode("utf-8")).hexdigest()

    ledger = json.loads(LEDGER.read_text("utf-8"))
    policy = json.loads((ROOT / "tools/exact_construction_policy.json").read_text("utf-8"))
    assert ledger["schema"] == "t2b-static-admissions-1"
    assert ledger["baseline_policy"] == {
        "sha256": review.BASE_POLICY_SHA, "waiver_count": 3659,
        "imports_count": 648, "members_count": 432,
        "waivers_sha256": review.BASE_WAIVERS_SHA, "nonwaiver_sha256": review.BASE_OTHER_SHA,
    }
    assert digest(policy["waivers"][:3659]) == review.BASE_WAIVERS_SHA
    assert digest({key: value for key, value in policy.items() if key != "waivers"}) == review.BASE_OTHER_SHA
    assert {row["path"]: row["sha256"] for row in ledger["analyzers"]} == review.SCANNERS
    for path, expected in review.SCANNERS.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    entries = ledger["entries"]
    added = policy["waivers"][3659:]
    assert len(added) == len(entries)
    assert added == ledger["policy_rows"]
    assert len({row["id"] for row in added}) == len(added)
    assert len({tuple(row[key] for key in ("path", "function", "rule", "node", "context"))
                for row in added}) == len(added), "duplicate actual admission key"
    assert ledger["diagnostics_count"] >= len(added)
    for row, recorded in zip(added, entries):
        assert row == {key: recorded[key] for key in review.POLICY_KEYS}
        assert row["category"] == "T2B_EXACT_REUSE_SITE_REVIEW"
        assert row["id"].startswith("T2B-S") and row["reason"].strip()
        assert row["review_evidence"] == review.REVIEW
        assert row["rule"] in {
            "closed-unproved-call", "closed-import-call", "closed-method-call",
            "closed-unknown-member", "closed-callable-value", "closed-dynamic-call",
            "closed-data-attribute", "closed-unknown-call", "closed-runtime-reflection",
        }, "semantic: only exact-reuse proof gaps may be admitted"
        if row["path"].startswith("src/"):
            assert row["path"] == "src/eab/kernel2d/se2_cage.py"
        else:
            assert row["path"].startswith(("tests/test_t2b_", "tests/t2b_"))
            assert len(Path(row["path"]).parts) == 2
        source = (ROOT / row["path"]).read_text("utf-8")
        contexts = subset.site_contexts(source)
        assert contexts[row["function"]] == row["context"]
        assert recorded["source_contexts"] == {row["function"]: row["context"]}
        matches = []
        occurrences = []
        pending = [(ast.parse(source), ())]
        while pending:
            node, names = pending.pop()
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names = (*names, node.name)
            if ((".".join(names) or "<module>") == row["function"]
                    and ast.dump(node, include_attributes=False) == row["node"]):
                occurrences.append((node.lineno, node.col_offset, ast.get_source_segment(source, node)))
                if node.lineno == recorded["line"] and node.col_offset == recorded["column"]:
                    matches.append(node)
            pending.extend((child, names) for child in ast.iter_child_nodes(node))
        assert len(matches) == 1, "reviewed node absent from its exact lexical scope and source site"
        assert ast.get_source_segment(source, matches[0]) == recorded["source_expression"]
        assert recorded["occurrences"] == [dict(line=line, column=column, source_expression=expression)
                                            for line, column, expression in sorted(set(occurrences))]
        assert recorded["occurrences"][0] == {
            key: recorded[key] for key in ("line", "column", "source_expression")}
    assert ledger["rule_site_occurrence_count"] == sum(len(row["occurrences"]) for row in entries)

    counts = {
        "total": len(added), "src": sum(row["path"].startswith("src/") for row in added),
        "tests": sum(row["path"].startswith("tests/") for row in added),
        "by_rule": dict(Counter(row["rule"] for row in added)),
        "src_by_rule": dict(Counter(row["rule"] for row in added if row["path"].startswith("src/"))),
        "tests_by_rule": dict(Counter(row["rule"] for row in added if row["path"].startswith("tests/"))),
    }
    assert ledger["counts"] == counts and ledger["review_evidence"] == review.REVIEW
    report = (ROOT / "reports/codex/T2b_report.md").read_text("utf-8")
    assert '<a id="t2b-static-admission-review"></a>' in report
    start, end = "<!-- T2B_STATIC_ADMISSIONS_COUNTS_BEGIN -->", "<!-- T2B_STATIC_ADMISSIONS_COUNTS_END -->"
    assert report.count(start) == report.count(end) == 1
    table = {}
    for line in report.split(start)[1].split(end)[0].splitlines():
        cells = [value.strip().strip("`") for value in line.strip().strip("|").split("|")]
        if len(cells) == 4 and (cells[0].startswith("closed-") or cells[0] == "**总计**"):
            assert cells[0] not in table
            table[cells[0]] = tuple(int(value) for value in cells[1:])
    expected = {rule: (counts["src_by_rule"].get(rule, 0), counts["tests_by_rule"].get(rule, 0), total)
                for rule, total in counts["by_rule"].items()}
    expected["**总计**"] = (counts["src"], counts["tests"], counts["total"])
    assert table == expected, "semantic: report, ledger and policy admission counts must agree"


def test_t2b_every_reviewed_scope_excludes_floating_operations():
    ledger = json.loads(LEDGER.read_text("utf-8"))
    scopes = {(row["path"], row["function"]) for row in ledger["entries"]}
    for path, function in sorted(scopes):
        review.audit_scope((ROOT / path).read_text("utf-8"), function)


@pytest.mark.parametrize("injection", [
    "float(0)", "import builtins as b; b.float(0)", "convert = float; convert(0)",
    "import math; math.sqrt(4)", "from math import sin as sine; sine(0)",
    "import numpy as np; np.asarray([0])", "from numpy import float64 as binary; binary(0)",
    "import struct; struct.pack('d', 0)", "from struct import unpack as decode; decode('d', b'12345678')",
    "import ctypes; ctypes.c_double(0)", "bits = 1 << 52", "bits = 1 & 0x7ff0000000000000",
    "value = 0.5", "other = convert; convert = float; other(0)",
])
def test_t2b_floating_injections_inside_real_production_scope_are_rejected(injection):
    source = (ROOT / "src/eab/kernel2d/se2_cage.py").read_text("utf-8")
    review.audit_scope(source, "_rational")
    tree = ast.parse(source)
    target = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_rational")
    target.body[0:0] = ast.parse(injection).body
    with pytest.raises(AssertionError, match="semantic exact-reuse scope excludes floating/binary64 operations"):
        review.audit_scope(ast.unparse(tree), "_rational")


@pytest.mark.parametrize("rule", [
    "direct-float", "closed-rounded-call", "closed-rounded-construction",
    "closed-unproved-arithmetic", "closed-indirect-call", "closed-syntax", "closed-import",
])
def test_t2b_review_rejects_numeric_or_unapproved_rules(rule):
    with pytest.raises(AssertionError, match="semantic: only enumerated exact-reuse proof gaps"):
        review.verify_entry({"path": "src/eab/kernel2d/se2_cage.py", "rule": rule})


def test_t2b_candidate_extraction_is_not_approval_and_cannot_write_policy():
    path = ROOT / "tools/exact_construction_policy.json"
    before = path.read_bytes()
    with pytest.raises(AssertionError, match="candidate extraction is not human review"):
        review.reviewed_ledger({"approved": False})
    assert path.read_bytes() == before


def test_t2b_candidate_site_resolution_excludes_same_text_expression_wrappers():
    source = "def exercise(callback):\n    callback()\n    callback()\n"
    diagnostics = review.gate.scan_text(source, "src/eab/kernel2d/review_probe.py", repository_root=ROOT)
    assert diagnostics
    sites = [key for diagnostic in diagnostics
             for key in review.diagnostic_sites(source, diagnostic)]
    assert all(dump.startswith("Call(") for line, column, dump in sites)
    assert {line for line, column, dump in sites} == {2, 3}
