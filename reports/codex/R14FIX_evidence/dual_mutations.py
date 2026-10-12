"""Rerunnable R14 production-source mutations; no production file writes."""
from pathlib import Path
import hashlib
import importlib.util
import inspect
import sys
import textwrap
import traceback

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]
import pytest
from eab import dual

spec = importlib.util.spec_from_file_location("r14_dual_gates", ROOT / "tests/test_r14_dual.py")
gates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gates)
source_path = ROOT / "src/eab/dual.py"
before = hashlib.sha256(source_path.read_bytes()).hexdigest()


def compile_mutant(function, needle, replacement):
    source = textwrap.dedent(inspect.getsource(function))
    assert source.count(needle) == 1
    namespace = dict(vars(dual))
    exec(compile(source.replace(needle, replacement), "<r14-production-mutant>", "exec"), namespace)
    return namespace[function.__name__]


def expect_red(label, patch, gate, exception, assertion):
    print("\nMUTATION", label)
    with pytest.MonkeyPatch.context() as mp:
        patch(mp)
        try:
            gate()
        except exception as error:
            assert assertion in str(error), (label, str(error))
            traceback.print_exc(file=sys.stdout)
            print("VERIFIED_RED", label, "target assertion:", assertion)
        else:
            raise AssertionError("mutation has no teeth: " + label)


expect_red("N01 early exponent float", lambda mp: mp.setattr(dual.Dual, "__pow__",
    compile_mutant(dual.Dual.__pow__, 'p = exact_input(p, "Dual power exponent")', 'p = Fraction(float(p))')),
    lambda: gates.test_r14_integer_power_keeps_exact_parity(2**54+1, int),
    AssertionError, "exact odd exponent must retain negative primal")

expect_red("N02 bypass exact angle check", lambda mp: mp.setattr(dual, "_lossless_libm_input",
    compile_mutant(dual._lossless_libm_input, 'return binary64_argument(value, quantity)', 'return float(value)')),
    lambda: gates.test_r14_trig_rejects_lossy_exact_parameters("sin", 2**54+1, False),
    pytest.fail.Exception, "DID NOT RAISE")

expect_red("SCAN noninteger exponent check", lambda mp: mp.setattr(dual, "_lossless_libm_input",
    compile_mutant(dual._lossless_libm_input, 'return binary64_argument(value, quantity)', 'return float(value)')),
    lambda: gates.test_r14_noninteger_power_rejects_lossy_exact_exponent(gates.F(1, 3)),
    pytest.fail.Exception, "DID NOT RAISE")

expect_red("SCAN atan2 exact nonzero output cell", lambda mp: mp.setattr(dual, "atan2",
    compile_mutant(dual.atan2,
        'if xv > 0 and yv != 0 and 2*abs(Fraction(yv)) <= Fraction(xv)*Fraction(math.ulp(0.0)):',
        'if False:')),
    lambda: gates.test_r14_atan2_nonzero_output_underflow_is_named(False),
    pytest.fail.Exception, "DID NOT RAISE")

assert hashlib.sha256(source_path.read_bytes()).hexdigest() == before
print("\nPRODUCTION_BYTES_UNCHANGED", before)
