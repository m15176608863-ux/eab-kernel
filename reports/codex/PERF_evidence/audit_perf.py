"""Read-only source/fixture/collection audit; writes evidence only under audit/.

Conservative AST checks flag, rather than excuse, every non-marker old-test edit.
Run after final edits, optionally with --junit reports/codex/PERF_evidence/final.xml.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent
BASE = EVIDENCE / "baseline"
OUT = EVIDENCE / "audit"
HELPER_CHANGES = {
    "tests/e5a_cover_oracle.py": {"dot", "cross", "vertex", "arc"},
    "tests/e5a_escape_oracle.py": {"facet"},
}


def audit_oracle_helpers():
    """Account for explicitly equivalent helper edits, never exempt test gates."""
    rows = []
    for relative, allowed in HELPER_CHANGES.items():
        reference = relative.replace("e5a_", "perf_").replace("_oracle.py", "_oracle_reference.py")
        before = ast.parse((BASE / relative).read_text(encoding="utf-8-sig"))
        current = ast.parse((ROOT / relative).read_text(encoding="utf-8-sig"))
        frozen = ast.parse((ROOT / reference).read_text(encoding="utf-8-sig"))
        for node in ast.walk(frozen):
            if isinstance(node, ast.ImportFrom) and node.module == "perf_cover_oracle_reference":
                node.module = "e5a_cover_oracle"
        old_defs, new_defs = definitions(before), definitions(current)
        changed = {name for name in old_defs if name in new_defs and canonical(old_defs[name]) != canonical(new_defs[name])}
        old_imports = [canonical(n) for n in before.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        new_imports = [canonical(n) for n in current.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        row = dict(file=relative, reference=reference, allowed_changed_helpers=sorted(allowed),
                   actual_changed_helpers=sorted(changed),
                   frozen_reference_matches_baseline_ast=canonical(frozen) == canonical(before),
                   imports_unchanged=new_imports == old_imports,
                   no_production_geometry_imports=not any("eab" in text for text in new_imports),
                   reference_sha256=hashlib.sha256((ROOT/reference).read_bytes()).hexdigest(),
                   optimized_sha256=hashlib.sha256((ROOT/relative).read_bytes()).hexdigest())
        row["status"] = "PASS" if (changed == allowed and row["frozen_reference_matches_baseline_ast"]
            and row["imports_unchanged"] and row["no_production_geometry_imports"]) else "REVIEW_REQUIRED"
        rows.append(row)
    result = dict(status="PASS" if all(r["status"] == "PASS" for r in rows) else "REVIEW_REQUIRED", rows=rows,
                  equivalence_gate="tests/test_perf_oracle_algebra.py",
                  boundary="Only test-only oracle algebra/construction was accelerated. Original test_*.py gates and parameter grids have no exemptions. Frozen references retain independent Newell/Gram logic, not production geometry.")
    (OUT/"oracle_helper_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    return result


def canonical(node):
    return ast.dump(node, include_attributes=False)


def definitions(tree):
    result = {}
    def descend(body, prefix=""):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + node.name
                result[name] = node
                if isinstance(node, ast.ClassDef):
                    descend(node.body, name + ".")
    descend(tree.body)
    return result


def marker_free(node):
    result = copy.deepcopy(node)
    for part in ast.walk(result):
        if hasattr(part, "decorator_list"):
            part.decorator_list = [d for d in part.decorator_list if ast.unparse(d) != "pytest.mark.exhaustive"]
    return canonical(result)


def banned_calls(tree):
    bad = Counter()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = ast.unparse(node.func)
            if name in {"pytest.skip", "pytest.xfail", "pytest.mark.skip", "pytest.mark.skipif", "pytest.mark.xfail", "unittest.skip", "unittest.skipIf", "unittest.skipUnless"}:
                bad[canonical(node)] += 1
        if isinstance(node, ast.Attribute) and ast.unparse(node) in {"pytest.mark.skip", "pytest.mark.skipif", "pytest.mark.xfail"}:
            bad[canonical(node)] += 1
    return bad


def nodes(text):
    return [line.strip() for line in text.splitlines() if line.startswith("tests/") and "::" in line]


def read_collection(path):
    data = path.read_bytes()
    return data.decode("utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")


def run(junit=None):
    OUT.mkdir(exist_ok=True)
    helper_audit = audit_oracle_helpers()
    manifest = json.loads((EVIDENCE / "baseline_manifest.json").read_text(encoding="utf-8"))
    missing_functions, lost_assertions, changed_old_definitions, changed_module_statements, new_skips = [], [], [], [], []
    new_tests, marked, helper_changes = [], [], []
    old_paths = {p.relative_to(BASE) for p in (BASE / "tests").rglob("*.py")}
    current_paths = {p.relative_to(ROOT) for p in (ROOT / "tests").rglob("*.py")}
    for relative in sorted(old_paths | current_paths):
        before = ast.parse((BASE / relative).read_text(encoding="utf-8-sig")) if relative in old_paths else ast.Module(body=[], type_ignores=[])
        after = ast.parse((ROOT / relative).read_text(encoding="utf-8-sig")) if relative in current_paths else ast.Module(body=[], type_ignores=[])
        old_defs, new_defs = definitions(before), definitions(after)
        for name, old in old_defs.items():
            key = relative.as_posix() + "::" + name
            if name not in new_defs:
                missing_functions.append(key)
                continue
            new = new_defs[name]
            old_assert = Counter(canonical(x) for x in ast.walk(old) if isinstance(x, ast.Assert))
            new_assert = Counter(canonical(x) for x in ast.walk(new) if isinstance(x, ast.Assert))
            if old_assert - new_assert:
                lost_assertions.append({"definition": key, "removed_ast": list((old_assert - new_assert).elements())})
            if marker_free(old) != marker_free(new):
                if helper_audit["status"] == "PASS" and name in HELPER_CHANGES.get(relative.as_posix(), set()):
                    helper_changes.append(key)
                else:
                    changed_old_definitions.append(key)
            if any(ast.unparse(d) == "pytest.mark.exhaustive" for d in getattr(new, "decorator_list", [])):
                marked.append(key)
        new_tests.extend(relative.as_posix() + "::" + name for name in new_defs.keys() - old_defs.keys() if name.split(".")[-1].startswith("test_"))
        old_module = Counter(canonical(x) for x in before.body if not isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)))
        new_module = Counter(canonical(x) for x in after.body if not isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)))
        if old_module - new_module:
            changed_module_statements.append({"file": relative.as_posix(), "removed_or_changed_ast": list((old_module - new_module).elements())})
        added = banned_calls(after) - banned_calls(before)
        if added:
            new_skips.append({"file": relative.as_posix(), "new_skip_or_xfail_ast": list(added.elements())})

    fixtures = {p: h for p, h in manifest.items() if p.startswith("fixtures/")}
    changed_fixtures = [p for p, h in fixtures.items() if not (ROOT / p).is_file() or hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h]
    cmd = [sys.executable, "-X", "utf8", "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"]
    collect = subprocess.run(cmd, cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    (OUT / "current_collect.txt").write_text(collect.stdout, encoding="utf-8")
    original = nodes(read_collection(EVIDENCE / "baseline_collect.txt"))
    current = nodes(collect.stdout)
    missing_nodes = sorted((Counter(original) - Counter(current)).elements())
    extra_nodes = sorted((Counter(current) - Counter(original)).elements())
    result = {
        "baseline_head": "c194dbb", "scope": str(ROOT),
        "collection_command": cmd, "collection_exit_code": collect.returncode,
        "baseline_collected_nodes": len(original), "current_collected_nodes": len(current),
        "missing_baseline_nodes": missing_nodes, "added_node_count": len(extra_nodes), "added_nodes": extra_nodes,
        "old_test_definitions_removed": missing_functions, "old_assertions_removed_or_changed": lost_assertions,
        "old_definition_non_marker_ast_changes": changed_old_definitions,
        "separately_audited_equivalent_oracle_helper_changes": helper_changes,
        "oracle_helper_audit_status": helper_audit["status"],
        "old_module_statement_changes_including_parameter_grids": changed_module_statements,
        "new_skip_or_xfail": new_skips, "new_test_definitions": sorted(new_tests),
        "exhaustive_marked_definitions": marked,
        "fixture_count": len(fixtures), "changed_or_missing_fixtures": changed_fixtures,
        "limitations": "AST retention is deliberately stricter than semantic assertion strength; any flagged edit requires independent review. This audit does not execute assertions or prove production equivalence.",
    }
    if junit:
        source = ROOT / junit
        cases = list(ET.parse(source).iter("testcase"))
        result["final_junit"] = str(source.relative_to(ROOT))
        result["final_junit_nodes"] = len(cases)
        result["final_junit_bad_nodes"] = [c.get("classname", "") + "::" + c.get("name", "") for c in cases if any(c.find(tag) is not None for tag in ("failure", "error", "skipped"))]
        actual = [c.get("classname", "").replace(".", "/") + ".py::" + c.get("name", "") for c in cases]
        result["final_junit_missing_collected_nodes"] = sorted((Counter(current) - Counter(actual)).elements())
    blockers = [key for key in ("missing_baseline_nodes", "old_test_definitions_removed", "old_assertions_removed_or_changed", "old_definition_non_marker_ast_changes", "old_module_statement_changes_including_parameter_grids", "new_skip_or_xfail", "changed_or_missing_fixtures", "final_junit_bad_nodes", "final_junit_missing_collected_nodes") if result.get(key)]
    if collect.returncode:
        blockers.append("collection_exit_code")
    if helper_audit["status"] != "PASS":
        blockers.append("oracle_helper_audit_status")
    result["status"] = "PASS" if not blockers else "REVIEW_REQUIRED"
    result["blockers"] = blockers
    (OUT / "retention_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# WO-PERF 保留审计", "", f"状态：{result['status']}", "", f"- 基线节点 {len(original)}；当前节点 {len(current)}；旧节点丢失 {len(missing_nodes)}。", f"- 旧断言修改/丢失 {len(lost_assertions)}；旧函数非标记 AST 修改 {len(changed_old_definitions)}；模块语句/参数网格修改 {len(changed_module_statements)}。", f"- fixtures {len(fixtures)} 份，改变/缺失 {len(changed_fixtures)}；新增 skip/xfail {len(new_skips)}。", f"- exhaustive 标记函数 {len(marked)} 个。", "", "详细节点、原断言 AST、阻塞项与命令见 `retention_audit.json`；当前收集原文见 `current_collect.txt`。", "", result["limitations"]]
    (OUT / "retention_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in {"added_nodes", "new_test_definitions"}}, ensure_ascii=False, indent=2))
    return int(bool(blockers))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--junit")
    args = parser.parse_args()
    raise SystemExit(run(args.junit))
