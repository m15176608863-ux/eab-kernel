"""WO-T2c2 source-local checks, not a proof of numerical correctness.

The oracle is literal policy/source inspection. New exact helpers must pass
the existing three scanners without new admission. Mutation controls enter
the policy parser or an actual helper's AST, not a post-hoc result list.
"""
import ast
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import check_exact_construction as checker


ROOT = Path(__file__).resolve().parents[1]
PREFIXES = ("tests/t2c2_", "tests/test_t2c2_", "tools/t2c2_")
SCANNERS = {
    "tools/check_exact_construction.py": "cc6143a27369f1247718b2e48ae80f3afb7b5060b23de845437a53b5a0768517",
    "tools/exact_construction_subset.py": "35e6262a7c36ea5f20679f047dd6f030feeb6fcbe8be7813573212829b503274",
    "tools/exact_construction_flow.py": "814f00ab607726c7753fa86ddedc08fd728eb48c4e57b8a61dda55140c3cd1db",
}


def test_t2c2_static_admission_and_floating_sink_counts_are_zero():
    policy = json.loads((ROOT / "tools/exact_construction_policy.json").read_text("utf-8"))
    admissions = [row for row in policy["waivers"] if row["path"].startswith(PREFIXES)]
    assert admissions == [], ("T2c2 requires zero static admissions and zero floating sink admissions", admissions)


def test_t2c2_internal_policy_admission_mutation_is_rejected():
    for path in ("tests/t2c2_knob_exact.py", "tests/test_t2c2_knob_theorem.py", "tools/t2c2_probe.py"):
        # The count assertion must reject even a nominal proof-gap entry.
        policy = {"waivers": [{"path": path, "rule": "closed-unproved-call"}]}
        with patch.object(json, "loads", return_value=policy):
            with unittest.TestCase().assertRaisesRegex(AssertionError, "T2c2 requires zero static admissions"):
                test_t2c2_static_admission_and_floating_sink_counts_are_zero()


def test_t2c2_three_static_scanners_remain_byte_unchanged():
    for path, expected in SCANNERS.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path


def test_t2c2_exact_sources_reject_internal_floating_injections():
    def audit(source):
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
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, (ast.Name, ast.Attribute)):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        aliases[target.id] = dotted(node.value)

        forbidden = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and type(node.value) is float:
                forbidden.append((node.lineno, "floating literal"))
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
                exponent = node.right
                if isinstance(exponent, ast.UnaryOp) and isinstance(exponent.op, (ast.UAdd, ast.USub)):
                    exponent = exponent.operand
                if not (isinstance(exponent, ast.Constant) and type(exponent.value) is int):
                    forbidden.append((node.lineno, "power exponent is not an integer constant"))
            elif isinstance(node, ast.Call):
                name = dotted(node.func)
                if name in ("float", "builtins.float") or name.startswith((
                        "math.", "numpy.", "struct.", "ctypes.", "float.", "builtins.float.")):
                    forbidden.append((node.lineno, name))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [item.name for item in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                if any(name.split(".")[0] in ("math", "numpy", "struct", "ctypes") for name in names):
                    forbidden.append((node.lineno, "floating or binary64 import"))
        assert not forbidden, ("T2c2 exact source excludes floating sinks", forbidden)

    paths = sorted(set((ROOT / "tests").glob("t2c2_*.py")) | set((ROOT / "tests").glob("test_t2c2_*.py")))
    helper = ROOT / "tests/t2c2_knob_exact.py"
    assert helper in paths, "the exact helper must be inspected, not silently absent"
    for path in paths:
        encoded = path.read_bytes()
        assert not encoded.startswith(b"\xef\xbb\xbf") and b"\r" not in encoded, path
        audit(encoded.decode("utf-8"))

    source = helper.read_text("utf-8")
    tree = ast.parse(source)
    target = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
    for exact_power in ("Q5(5) ** 2", "Q5(5) ** -2", "Q5(5) ** +2"):
        audit(exact_power)
    for injection in (
            "float(0)", "import builtins as b; b.float(0)",
            "convert = float; convert(0)", "import math; math.sqrt(4)",
            "from math import sin as sine; sine(0)",
            "import numpy as np; np.asarray([0])",
            "from struct import unpack as decode; decode('d', b'12345678')",
            "import ctypes; ctypes.c_double(0)", "value = 0.5",
            "value = 5 ** F(1, 2)", "value = 5 ** exponent", "value = 5 ** True"):
        # Reparse for each mutation: injections never accumulate or touch disk.
        mutant = ast.parse(source)
        selected = next(node for node in ast.walk(mutant)
                        if isinstance(node, ast.FunctionDef) and node.lineno == target.lineno)
        selected.body[0:0] = ast.parse(injection).body
        with unittest.TestCase().assertRaisesRegex(AssertionError, "T2c2 exact source excludes floating sinks"):
            audit(ast.unparse(mutant))


def test_t2c2_new_test_sources_pass_unmodified_static_gate():
    paths = sorted(set((ROOT / "tests").glob("t2c2_*.py")) | set((ROOT / "tests").glob("test_t2c2_*.py")))
    assert ROOT / "tests/t2c2_knob_exact.py" in paths
    issues = []
    for path in paths:
        issues.extend(checker.scan_text(path.read_text("utf-8"), path.relative_to(ROOT).as_posix(), repository_root=ROOT))
    assert issues == [], issues
