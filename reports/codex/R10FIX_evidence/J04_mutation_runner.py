"""Replay source-internal R10 Dual regressions without modifying working files."""
import importlib.util
import inspect
from pathlib import Path
import sys
import textwrap
import traceback
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]
import eab.dual as dual
import pytest

spec = importlib.util.spec_from_file_location("r10_dual_tests", ROOT / "tests/test_r10_dual_construction.py")
tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tests)

cases = [
    ("J04 sqrt rounded primal", dual, "sqrt",
     "return Dual(s, tuple(_sqrt_derivative(x.v, a) for a in x.e))",
     "return Dual(s, tuple((0.5 / s) * a for a in x.e))",
     lambda: tests.test_r10_sqrt_derivative_rounds_the_complete_expression(3, 1, 0),
     "complete sqrt derivative final rounding"),
    ("scan sin unchecked derivative", dual, "sin",
     "_derivative_float(Fraction(c) * Fraction(a))", "c * a",
     lambda: tests.test_r10_trigonometric_nonzero_derivative_cannot_underflow_silently("sin", 1.5, 1),
     "DID NOT RAISE"),
    ("scan cos unchecked derivative", dual, "cos",
     "_derivative_float(Fraction(c) * Fraction(a))", "c * a",
     lambda: tests.test_r10_trigonometric_nonzero_derivative_cannot_underflow_silently("cos", 0.25, 1),
     "DID NOT RAISE"),
    ("scan half-power Decimal fallback", dual.Dual, "__pow__",
     "if Fraction(p).denominator == 2:", "if False:",
     lambda: tests.test_r10_half_integer_power_derivative_keeps_exact_subnormal_ties(-716, 1.5, "0x1.8p-715", 1),
     "half-integer derivative exact tie must round to even"),
    ("scan atan2 premature float path", dual, "_ratio_derivative",
     "if not angular and _ordinary(u, v, a, b):", "if _ordinary(u, v, a, b):",
     lambda: tests.test_r10_atan2_derivative_uses_one_final_rational_rounding(0),
     "atan2 derivative exact rational final rounding"),
    ("scan pow missing primal range check", dual.Dual, "__pow__",
     "if value == 0.0 and self.v != 0.0:", "if False:",
     lambda: tests.test_r10_power_primal_underflow_without_an_exact_channel_fails_loudly(2.0),
     "DID NOT RAISE"),
]
for title, owner, name, needle, replacement, run, expected in cases:
    source = textwrap.dedent(inspect.getsource(getattr(owner, name)))
    assert source.count(needle) == 1, title
    namespace = dict(vars(dual))
    exec(compile(source.replace(needle, replacement), "<R10-source-mutation>", "exec"), namespace)
    with patch.object(owner, name, namespace[name]):
        try:
            run()
        except (AssertionError, pytest.fail.Exception) as exc:
            assert expected in str(exc), (title, str(exc))
            print(f"\nCONFIRMED_RED: {title}; guarded assertion: {expected}")
            print(traceback.format_exc())
        else:
            raise AssertionError(f"mutation survived: {title}")
print("6 source-internal mutations rejected by their intended assertions; production functions restored")
