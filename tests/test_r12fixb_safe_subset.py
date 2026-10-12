"""Positive type/flow admission contracts, paired with forbidden-flow teeth.

These are scanner source probes; the oracle is the Python int/Fraction type
contract, not an eab geometric calculation or a regenerated policy snapshot.
No probe path has a waiver in the checked-in policy.
"""
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("r12fixb_safe_subset_gate", ROOT / "tools/check_exact_construction.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


SAFE_PROGRAMS = [
    ("fraction_arithmetic_comparison", (
        "from fractions import Fraction\n"
        "def safe(a: Fraction, b: Fraction):\n"
        "    result = (a + b) * (a - b) / Fraction(3)\n"
        "    return result, result < a, result == b\n"
    )),
    ("integer_arithmetic_comparison", (
        "def safe(a: int, b: int):\n"
        "    result = (a + b) * (a - b)\n"
        "    return result, result < a, result // 3, result / 3\n"
    )),
    ("fraction_variable_sum", (
        "from fractions import Fraction\n"
        "from eab.construction import sqrt_rational\n"
        "def safe(a: Fraction, b: Fraction):\n"
        "    squared = sum((a*a, b*b), Fraction(0))\n"
        "    return sqrt_rational(squared)\n"
    )),
    ("known_pure_functions", (
        "import math\n"
        "from fractions import Fraction\n"
        "def safe(a: Fraction, b: Fraction):\n"
        "    return math.isfinite(a), abs(a), min(a, b), max(a, b)\n"
    )),
    ("float_display_arithmetic", (
        "def safe(a: float, b: float):\n"
        "    score = (a + b) * 0.5 - a / 3.0\n"
        "    return score\n"
    )),
    ("float_pure_checks", (
        "import math\n"
        "def safe(a: float, b: float):\n"
        "    return math.isfinite(a), abs(a), min(a, b), max(a, b)\n"
    )),
    ("canonical_construction_calls", (
        "from fractions import Fraction\n"
        "from eab.construction import scalar_rational, sqrt_rational, norm_rational, unit_rational\n"
        "def safe(a: Fraction, b: Fraction):\n"
        "    return scalar_rational(a), sqrt_rational(a*a), norm_rational((a,b)), unit_rational((a,b))\n"
    )),
    ("first_order_exact_helper", (
        "from fractions import Fraction\n"
        "from eab.construction import sqrt_rational\n"
        "def exact_square(a: Fraction):\n"
        "    return a*a\n"
        "def safe(a: Fraction):\n"
        "    return sqrt_rational(exact_square(a))\n"
    )),
]


@pytest.mark.parametrize("path", ["src/eab/r12fixb_safe_probe.py", "tests/r12fixb_safe_helper.py"])
@pytest.mark.parametrize("label,source", SAFE_PROGRAMS, ids=[row[0] for row in SAFE_PROGRAMS])
def test_normal_safe_numeric_programs_are_proved_without_waivers(path, label, source):
    assert gate._subset.approved_sites(source, path) == set()
    issues = gate.scan_text(source, path)
    assert issues == [], ("R12FIXb safe numeric admission", label, path, issues)


FORBIDDEN_PROGRAMS = [
    ("unknown_implicit_context_protocol", "def bad(context):\n    with context:\n        return 1\n"),
    ("float_derived_through_local_helper", (
        "from eab.construction import sqrt_rational\n"
        "def rounded_square(a: float):\n"
        "    return a*a\n"
        "def bad(a: float):\n"
        "    return sqrt_rational(rounded_square(a))\n"
    )),
    ("fraction_does_not_unround_float_product", (
        "from fractions import Fraction\n"
        "from eab.construction import sqrt_rational\n"
        "def bad(a: Fraction):\n"
        "    return sqrt_rational(Fraction(a*1.0))\n"
    )),
    ("dynamic_callable_parameter", "def bad(value, callback):\n    return callback(value)\n"),
    ("unknown_math_callable", "import math\ndef bad(value):\n    return math.unreviewed_numeric_function_913(value)\n"),
]


@pytest.mark.parametrize("path", ["src/eab/r12fixb_forbidden_probe.py", "tests/r12fixb_forbidden_helper.py"])
@pytest.mark.parametrize("label,source", FORBIDDEN_PROGRAMS, ids=[row[0] for row in FORBIDDEN_PROGRAMS])
def test_expanded_subset_does_not_admit_forbidden_or_unknown_flows(path, label, source):
    issues = gate.scan_text(source, path)
    assert issues, ("R12FIXb expanded subset must preserve default rejection", label, path)
    assert any(row[2] == "bad" for row in issues), ("R12FIXb bad sink itself must be reported", label, path, issues)


def test_new_local_source_import_needs_no_repository_registry_refresh(tmp_path):
    """New source is analysed, not trusted merely because an import resolves."""
    helper = tmp_path / "src/eab/new_local_numeric_module.py"
    helper.parent.mkdir(parents=True)
    helper.write_text(
        "from fractions import Fraction\n"
        "def square(a: Fraction):\n    return a*a\n", encoding="utf-8")
    source = (
        "from fractions import Fraction\n"
        "from eab.new_local_numeric_module import square\n"
        "from eab.construction import sqrt_rational\n"
        "def checked(a: Fraction):\n    return sqrt_rational(square(a))\n"
    )
    path = "src/eab/new_local_caller.py"
    assert gate.scan_text(source, path, repository_root=tmp_path) == []
    # Editing only the callee makes the original caller unsafe: source facts
    # must be recomputed even though no waiver, global digest or registry moved.
    helper.write_text(
        "from fractions import Fraction\n"
        "def square(a: Fraction):\n    return a*1.0\n", encoding="utf-8")
    issues = gate.scan_text(source, path, repository_root=tmp_path)
    assert any(row[2] == "checked" for row in issues), issues
