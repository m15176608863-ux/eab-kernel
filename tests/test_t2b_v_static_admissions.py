"""WO-T2b-V source-local static audit without reading production geometry.

This is an auxiliary finite static gate, not a proof of numerical correctness.
Only the new independent work-order files are submitted to scan_text.  The
repository-wide gate remains with the owner on a fresh tree. The continuation
ruling permits the repository tool's internal parsing; no production geometry
source is inspected or cited by this independent implementation.
"""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TOOL_HASHES = {
    "tools/check_exact_construction.py": "cc6143a27369f1247718b2e48ae80f3afb7b5060b23de845437a53b5a0768517",
    "tools/exact_construction_subset.py": "35e6262a7c36ea5f20679f047dd6f030feeb6fcbe8be7813573212829b503274",
    "tools/exact_construction_flow.py": "814f00ab607726c7753fa86ddedc08fd728eb48c4e57b8a61dda55140c3cd1db",
    "tools/exact_construction_policy.json": "621df0519431552c8cea255cf756f1bcb5c3acc90cb301ff0048649b1916cc5d",
}
IMPLEMENTATION_FILES = (
    "tests/t2b_independent_cage_verifier.py",
    "tests/t2b_truth_geometry.py",
    "tests/t2b_hand_cage_builder.py",
    "tests/t2b_independent_instances.py",
)


def test_t2b_v_static_analyzers_and_policy_are_byte_unchanged():
    for relative, expected in EXPECTED_TOOL_HASHES.items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected, relative


def test_t2b_v_static_admission_counts_match_report():
    policy = json.loads((ROOT / "tools/exact_construction_policy.json").read_text(encoding="utf-8"))
    paths = set(IMPLEMENTATION_FILES)
    for path in (ROOT / "tests").glob("test_t2b_v_*.py"):
        paths.add(path.relative_to(ROOT).as_posix())
    admitted = []
    counts = {}
    for row in policy["waivers"]:
        if row["path"] in paths:
            admitted.append(row)
            counts[row["rule"]] = counts.get(row["rule"], 0) + 1
    assert len(admitted) == 0
    assert counts == {}
    report = (ROOT / "reports/codex/T2b_V_report.md").read_text(encoding="utf-8")
    assert "T2BV_STATIC_ADMISSIONS_TOTAL=0" in report.splitlines()
    assert "T2BV_STATIC_ADMISSIONS_BY_RULE={}" in report.splitlines()
    # Any future admission must remain a reviewed proof gap, never a floating
    # sink waiver; with zero admissions this obligation is satisfied vacuously.
    for row in admitted:
        assert row["reason"].strip() and row["review_evidence"].strip()
        tree = ast.parse((ROOT / row["path"]).read_text(encoding="utf-8"))
        owners = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == row["function"].split(".")[-1]:
                    owners.append(node)
        assert len(owners) == 1
        for node in ast.walk(owners[0]):
            if isinstance(node, ast.Call):
                assert not (isinstance(node.func, ast.Name) and node.func.id == "float")
                assert not (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                            and node.func.value.id in ("math", "numpy", "struct"))


def test_t2b_v_implementation_has_no_floating_sink_or_production_import():
    for relative in IMPLEMENTATION_FILES:
        source = (ROOT / relative).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                assert not isinstance(node.value, float), (relative, node.lineno)
            if isinstance(node, ast.Call):
                assert not (isinstance(node.func, ast.Name) and node.func.id == "float"), (relative, node.lineno)
            if isinstance(node, ast.BinOp):
                assert not isinstance(node.op, ast.Pow), (relative, node.lineno)
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = []
                if isinstance(node, ast.ImportFrom):
                    modules.append(node.module or "")
                else:
                    for alias in node.names:
                        modules.append(alias.name)
                for module in modules:
                    assert module.split(".")[0] not in ("eab", "math", "numpy", "struct"), (relative, node.lineno)
        encoded = (ROOT / relative).read_bytes()
        assert not encoded.startswith(b"\xef\xbb\xbf")
        assert b"\r" not in encoded


def test_t2b_v_new_sources_pass_unmodified_source_local_static_gate():
    specification = importlib.util.spec_from_file_location(
        "t2bv_independent_static_gate", ROOT / "tools/check_exact_construction.py")
    checker = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(checker)
    paths = []
    for relative in IMPLEMENTATION_FILES:
        paths.append(ROOT / relative)
    for path in (ROOT / "tests").glob("test_t2b_v_*.py"):
        paths.append(path)
    violations = []
    for path in sorted(paths):
        relative = path.relative_to(ROOT).as_posix()
        violations.extend(checker.scan_text(path.read_text(encoding="utf-8"), relative, repository_root=ROOT))
    assert violations == []
