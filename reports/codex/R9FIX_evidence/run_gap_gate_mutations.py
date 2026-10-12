"""Exercise each real internal margin arithmetic mutant, preserving target errors."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

from pytest import MonkeyPatch
import test_r8fix_margin_gap_gate as gate_module


count = 0
for fault in ("old_subtraction", "omit_delta", "reverse_delta", "double_distance"):
    for gate in (gate_module._ordinary_gap_gate, gate_module._large_gap_gate):
        with MonkeyPatch.context() as patch:
            gate_module._arithmetic_fault_inside_margin_contacts(patch, fault)
            try:
                gate()
            except AssertionError as error:
                assert "exact margin-gap midpoint" in str(error), str(error)
                print(f"TARGET RED {fault} {gate.__name__}: {error}")
                count += 1
            else:
                raise AssertionError(f"NO TEETH: {fault} {gate.__name__}")
assert count == 8
print("PASS: all 8 original mutation cells hit exact margin-gap midpoint assertions")
