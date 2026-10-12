"""Restore intermediate component rounding in the real VV3 constructor."""
from pathlib import Path
import inspect
import sys
import pytest
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
class Mutant:
    def pytest_sessionstart(self, session):
        import eab.kernel3d.covers3 as C
        source = inspect.getsource(C.vv3_cover)
        old = "sqrt_rational(vv, allow_underflow=True)"
        assert source.count(old) == 1
        ns = dict(vars(C))
        exec(source.replace(old, "norm(_float_vector(v))"), ns)
        C.vv3_cover = ns["vv3_cover"]
sys.exit(pytest.main(["-q", "-p", "no:cacheprovider",
    "tests/test_r6fix_construction.py::test_cover_construction_exposes_exact_nonzero_gap_and_area[-1075]",
    "--basetemp=reports/codex/R6FIX_evidence/tmp/mutant_cover"], plugins=[Mutant()]))
