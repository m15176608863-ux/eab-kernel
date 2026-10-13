"""WO-G6N: current production Dual integer exponent loses parity before exact branch.
Run: python -X utf8 review/repro/support_dual_power.py
No production constructor/power routine computes the reference.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from eab.dual import Dual
from fractions import Fraction

p = 2**54 + 1
expected_primal = -1.0 if p % 2 else 1.0
# d(x**p)/dx at x=-1 = p*(-1)**(p-1), independently from parity.
expected_derivative = float(Fraction(p) * (1 if (p-1) % 2 == 0 else -1))
for exponent in (p, Fraction(p)):
    result = Dual(-1.0, (1.0,)) ** exponent
    print(f"input exponent type={type(exponent).__name__}, exact p={p}, float(p)={float(exponent)!r}")
    print(f"actual={result!r}; expected primal={expected_primal!r}, derivative={expected_derivative!r}")
    assert result.v != expected_primal and result.e[0] != expected_derivative
print("CONFIRMED: finite integer input below 2**400 returns wrong primal and derivative signs without an exception")
