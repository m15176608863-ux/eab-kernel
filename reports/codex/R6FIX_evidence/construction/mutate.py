"""Process-local real implementation/doc mutations; no live files are edited."""
from pathlib import Path
import inspect
import math
import sys
import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
which = sys.argv[1]


class Mutant:
    def pytest_sessionstart(self, session):
        if which == "06":
            import eab.kernel2d.entrance as E
            E.sqrt_rational = lambda value: math.sqrt(float(value))
        elif which == "08":
            import eab.margin as M
            source = inspect.getsource(M.nearest_point_on_convex_entrance)
            step = "return point if exact else tuple(map(float, point))"
            assert source.count(step) == 1
            scope = dict(vars(M))
            exec(source.replace(step, "return tuple(map(float, point))"), scope)
            M.nearest_point_on_convex_entrance = scope["nearest_point_on_convex_entrance"]
        elif which == "10":
            original = Path.read_text
            def mutated(path, *args, **kwargs):
                value = original(path, *args, **kwargs)
                if path.resolve() == ROOT / "docs/canon_map.md":
                    assert "先有理化输入再作 b−a" in value
                    return value.replace("先有理化输入再作 b−a", "仍先浮点构造 b−a")
                return value
            Path.read_text = mutated
        else:
            raise ValueError(which)


node = {
    "06": "test_g6f06_exit_gap_preserves_representable_nonzero_magnitude[-600]",
    "08": "test_g6f08_distance_and_normal_use_exact_relative_projection[s0-translation2]",
    "10": "test_g6f10_canon_definition_matches_exact_difference_contract",
}[which]
sys.exit(pytest.main(["-q", "-p", "no:cacheprovider",
                      "tests/test_r6fix_construction.py::"+node,
                      "--basetemp=reports/codex/R6FIX_evidence/tmp/mutant_"+which], plugins=[Mutant()]))
