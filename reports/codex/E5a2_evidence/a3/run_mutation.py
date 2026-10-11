"""Process-local source mutation: edit production function source before pytest.

Run from repository root with PYTHONDONTWRITEBYTECODE=1 python -X utf8.
No production file is written and no output is decorated after enumeration.
"""
import hashlib
import inspect
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from eab.kernel3d import covers3 as C
import pytest

mode = sys.argv[1]
if mode == "support_plane_band":
    function = C.membership_convex3
    before = "return 0 if dot(nearest, nearest) <= tol2 else -1"
    after = "return 0  # MUTANT: all support-plane distances passed"
    target = "tests/test_e5a2_covers.py::test_membership_report_band_is_euclidean"
elif mode == "constructed_gap_window":
    function = C._cover_in_window
    before = "return numerator <= _squared_tol(window) * denominator"
    after = "return abs(c.gap) <= window  # MUTANT: constructed float distance"
    target = "tests/test_e5a2_covers.py::test_enumeration_window_does_not_read_a_gap_rounded_to_zero"
else:
    raise ValueError(mode)
source = inspect.getsource(function)
assert source.count(before) == 1
mutated = source.replace(before, after)
exec(compile(mutated, function.__code__.co_filename, "exec"), C.__dict__)
started = time.perf_counter()
code = pytest.main(["-q", target, "-p", "no:cacheprovider", "--tb=short",
                    "--basetemp=reports/codex/E5a2_evidence/tmp/a3_mutation_" + mode])
result = dict(mode=mode, before=before, after=after, target=target,
              pytest_exit=int(code), seconds=time.perf_counter()-started,
              original_function_sha256=hashlib.sha256(source.encode()).hexdigest(),
              mutated_function_sha256=hashlib.sha256(mutated.encode()).hexdigest(),
              test_sha256=hashlib.sha256((ROOT/"tests/test_e5a2_covers.py").read_bytes()).hexdigest(),
              restored="process-local only; production files never modified")
Path(__file__).with_name(mode + ".json").write_text(json.dumps(result, indent=2), encoding="utf8")
raise SystemExit(0 if code == pytest.ExitCode.TESTS_FAILED else 2)
