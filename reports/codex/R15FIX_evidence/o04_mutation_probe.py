"""Replay internal R15 O04 mutations; selected ordinary gate MUST fail."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests"), str(ROOT)]
import pytest
import test_r15fix_numeric_decode as gates


case = sys.argv[1]
if case == "parser":
    decoder = gates.numeric_decode
    decoder._decimal = gates._internal_mutant(
        decoder, decoder._decimal, "q = Fraction(token)",
        'q = Fraction(token)\n    scalar_rational(q, quantity="JSON numeric literal")')
    node = "test_o04_contact_decimal_integer_identity_is_unbounded[1e400-step]"
elif case in ("nsign", "owner"):
    old = ('c["nsign"] = integer(c["nsign"], "bdda3d.nsign")' if case == "nsign" else
           'c["owner"] = [integer(v, "bdda3d.owner") for v in c["owner"]]')
    gates.bdda3d.record_from_entrance = gates._internal_mutant(
        gates.bdda3d, gates.bdda3d.record_from_entrance, old, "pass")
    node = f"test_o04_scan_discrete_bdda3d_evidence_uses_integer_schema[{case}]"
else:
    assert case in ("d1", "fa", "coh", "tens", "t1", "t2")
    old = 'for name in ("t1", "t2", "d1", "fa", "coh", "tens"):'
    names = tuple(name for name in ("t1", "t2", "d1", "fa", "coh", "tens") if name != case)
    gates.bdda3d.record_from_entrance = gates._internal_mutant(
        gates.bdda3d, gates.bdda3d.record_from_entrance, old, f"for name in {names!r}:")
    node = f"test_o04_scan_known_bdda3d_continuous_integer_literals_cannot_bypass_domain[{case}]"

raise SystemExit(pytest.main(["-q", "-p", "no:cacheprovider",
                             f"tests/test_r15fix_numeric_decode.py::{node}",
                             "--basetemp=reports/codex/R15FIX_evidence/tmp/o04_mutant_" + case]))
