"""Owner-approved T2a site reviews, not a numerical exactness proof.

The oracle here is direct policy/source inspection: unchanged historical rows
and scanners, a finite proof-gap rule set, and absence of floating/binary64
operations in each reviewed lexical scope. Internal source injections must
trip the latter semantic assertion, independently of all source hashes.
"""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

import pytest

import exact_construction_subset as subset


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "reports/codex/T2a_evidence/static_admissions.json"
BASE_WAIVERS = 3522
BASE_POLICY_SHA = "cb813970c4194d61761dc10ccd576e765ea339c2f36d87a352fd31111585b97d"
BASE_WAIVERS_SHA = "1754c7dc89d32111d388a7099be68e4413a8187848650e2cc887b1fdb8e92137"
BASE_OTHER_SHA = "30e730ae82715ca70d3ab89b453276f1929915229fa2fa9022859edbb66963e5"
SCANNERS = {
    "tools/check_exact_construction.py": "cc6143a27369f1247718b2e48ae80f3afb7b5060b23de845437a53b5a0768517",
    "tools/exact_construction_subset.py": "35e6262a7c36ea5f20679f047dd6f030feeb6fcbe8be7813573212829b503274",
    "tools/exact_construction_flow.py": "814f00ab607726c7753fa86ddedc08fd728eb48c4e57b8a61dda55140c3cd1db",
}
PROOF_GAPS = {
    "closed-unproved-call", "closed-import-call", "closed-method-call",
    "closed-unknown-member", "closed-callable-value", "closed-dynamic-call",
    "closed-data-attribute", "closed-unknown-call", "closed-runtime-reflection",
}
REVIEW = "reports/codex/T2a_report.md#t2a-static-admission-review"


def test_t2a_site_reviews_preserve_baseline_and_match_report():
    def digest(value):
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    policy = json.loads((ROOT / "tools/exact_construction_policy.json").read_text(encoding="utf-8"))
    baseline = ledger["baseline_policy"]
    assert baseline["sha256"] == BASE_POLICY_SHA
    assert baseline["waiver_count"] == BASE_WAIVERS
    assert baseline["waivers_sha256"] == BASE_WAIVERS_SHA
    assert baseline["nonwaiver_sha256"] == BASE_OTHER_SHA
    assert digest(policy["waivers"][:BASE_WAIVERS]) == BASE_WAIVERS_SHA
    assert digest({key: value for key, value in policy.items() if key != "waivers"}) == BASE_OTHER_SHA
    assert baseline["imports_count"] == len(policy["imports"]) == 648
    assert baseline["members_count"] == len(policy["members"]) == 432
    assert {row["path"]: row["sha256"] for row in ledger["analyzers"]} == SCANNERS
    for path, expected in SCANNERS.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected

    added = policy["waivers"][BASE_WAIVERS:]
    assert added and len(added) == len(ledger["entries"])
    identities = set()
    for row, recorded in zip(added, ledger["entries"]):
        assert {key: recorded[key] for key in row} == row
        assert row["category"] == "T2A_EXACT_REUSE_SITE_REVIEW"
        assert row["id"].startswith("T2A-S") and row["id"] not in identities
        identities.add(row["id"])
        assert row["reason"].strip() and row["review_evidence"] == REVIEW
        assert row["rule"] in PROOF_GAPS, "semantic: only exact-reuse proof gaps may be admitted"
        if row["path"].startswith("src/"):
            assert row["path"] == "src/eab/kernel2d/se2_paths.py"
        else:
            assert row["path"].startswith(("tests/test_t2a_", "tests/t2a_"))
        source = (ROOT / row["path"]).read_text(encoding="utf-8")
        contexts = subset.site_contexts(source)
        assert contexts[row["function"]] == row["context"]

        # Unlike the legacy stale-review check, require the AST to occur in
        # this exact lexical scope, not in an unrelated same-spelled function.
        matches = {}
        pending = [(ast.parse(source), ())]
        while pending:
            node, names = pending.pop()
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names = (*names, node.name)
            scope = ".".join(names) or "<module>"
            if scope == row["function"] and ast.dump(node, include_attributes=False) == row["node"]:
                matches[scope] = contexts[scope]
            pending.extend((child, names) for child in ast.iter_child_nodes(node))
        assert matches, (row["id"], "reviewed node absent from its lexical scope")
        assert recorded["source_contexts"] == matches
        if row["rule"] == "closed-runtime-reflection":
            assert row["path"] == "src/eab/kernel2d/se2_paths.py"
            assert row["function"] == "SE2EscapePath.__post_init__"
            allowed = {
                ast.dump(ast.parse("object.__setattr__(self, 'poses', tuple(_exact_ring(p) for p in self.poses))", mode="eval").body,
                         include_attributes=False),
                ast.dump(ast.parse("object.__setattr__(self, 'motions', tuple(_checked_motion(m) for m in self.motions))", mode="eval").body,
                         include_attributes=False),
            }
            reflected = ast.dump(ast.parse("object.__setattr__", mode="eval").body,
                                 include_attributes=False)
            assert row["node"] == reflected, "semantic: reflection admission is only the frozen path fields"
            path_class = next(node for node in ast.parse(source).body
                              if isinstance(node, ast.ClassDef) and node.name == "SE2EscapePath")
            initialization = next(node for node in path_class.body
                                  if isinstance(node, ast.FunctionDef) and node.name == "__post_init__")
            uses = []
            for parent in ast.walk(initialization):
                for child in ast.iter_child_nodes(parent):
                    if ast.dump(child, include_attributes=False) == reflected:
                        assert isinstance(parent, ast.Call) and parent.func is child
                        uses.append(ast.dump(parent, include_attributes=False))
            assert set(uses) == allowed and len(uses) == 2, \
                "semantic: reflection admission is only the frozen path fields"
            assert any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                       and node.func.id == "dataclass"
                       and any(keyword.arg == "frozen" and isinstance(keyword.value, ast.Constant)
                               and keyword.value.value is True for keyword in node.keywords)
                       for node in path_class.decorator_list)

    counts = {
        "total": len(added),
        "src": sum(row["path"].startswith("src/") for row in added),
        "tests": sum(row["path"].startswith("tests/") for row in added),
        "by_rule": dict(Counter(row["rule"] for row in added)),
        "src_by_rule": dict(Counter(row["rule"] for row in added if row["path"].startswith("src/"))),
        "tests_by_rule": dict(Counter(row["rule"] for row in added if row["path"].startswith("tests/"))),
    }
    assert ledger["counts"] == counts
    assert ledger["review_evidence"] == REVIEW
    report = (ROOT / "reports/codex/T2a_report.md").read_text(encoding="utf-8")
    assert '<a id="t2a-static-admission-review"></a>' in report
    start = "<!-- T2A_STATIC_ADMISSIONS_COUNTS_BEGIN -->"
    end = "<!-- T2A_STATIC_ADMISSIONS_COUNTS_END -->"
    assert report.count(start) == report.count(end) == 1
    block = report.split(start)[1].split(end)[0]
    table = {}
    for line in block.splitlines():
        cells = [value.strip().strip("`") for value in line.strip().strip("|").split("|")]
        if len(cells) == 4 and (cells[0].startswith("closed-") or cells[0] == "**总计**"):
            assert cells[0] not in table
            table[cells[0]] = tuple(int(value) for value in cells[1:])
    expected = {rule: (counts["src_by_rule"].get(rule, 0),
                       counts["tests_by_rule"].get(rule, 0), total)
                for rule, total in counts["by_rule"].items()}
    expected["**总计**"] = (counts["src"], counts["tests"], counts["total"])
    assert table == expected, "semantic: report/ledger/policy admission counts must agree"


@pytest.mark.parametrize("injection", [
    None,
    "float(0)",
    "import builtins as b; b.float(0)",
    "convert = float; convert(0)",
    "import math; math.sqrt(4)",
    "from math import sin as sine; sine(0)",
    "import numpy as np; np.asarray([0])",
    "from numpy import float64 as binary; binary(0)",
    "import struct; struct.pack('d', 0)",
    "from struct import unpack as decode; decode('d', b'12345678')",
    "import ctypes; ctypes.c_double(0)",
    "bits = 1 << 52",
    "bits = 1 & 0x7ff0000000000000",
    "value = 0.5",
])
def test_t2a_reviewed_scopes_exclude_floating_operations_and_kill_injections(injection):
    def audit(source, function):
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
        # References to a banned operation remain banned under ordinary local
        # aliases. This finite lexical check is not dynamic Python analysis.
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, (ast.Name, ast.Attribute)):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        aliases[target.id] = dotted(node.value)

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

    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    scopes = {(row["path"], scope) for row in ledger["entries"] for scope in row["source_contexts"]}
    assert scopes
    for path, scope in sorted(scopes):
        audit((ROOT / path).read_text(encoding="utf-8"), scope)
    if injection is not None:
        path = "src/eab/kernel2d/se2_paths.py"
        function = "_checked_motion"
        assert (path, function) in scopes
        source = (ROOT / path).read_text(encoding="utf-8")
        tree = ast.parse(source)
        target = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == function)
        target.body[0:0] = ast.parse(injection).body
        # The mutant is inside a real reviewed production function. Do not
        # invoke the hash gate here: the intended semantic assertion must fail.
        with pytest.raises(AssertionError, match="semantic exact-reuse scope excludes floating/binary64 operations"):
            audit(ast.unparse(tree), function)
