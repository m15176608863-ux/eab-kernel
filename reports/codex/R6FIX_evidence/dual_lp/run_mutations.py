"""Run real internal R6FIX mutations in isolated interpreters (no source edits)."""
import ast
import inspect
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import zipfile

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))


def child(name):
    import eab.dual as dual
    import eab.lp as lp
    import pytest

    with zipfile.ZipFile(EVIDENCE.parent / "baseline_tracked.zip") as z:
        old = z.read("src/eab/dual.py").decode("utf-8")
    tree = ast.parse(old)

    def baseline_function(function_name, method=False):
        container = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Dual") if method else tree
        node = next(n for n in container.body if isinstance(n, ast.FunctionDef) and n.name == function_name)
        code = textwrap.dedent(ast.get_source_segment(old, node))
        scope = dict(vars(dual))
        exec(compile(code, str(ROOT / "src/eab/dual.py"), "exec"), scope)
        return scope[function_name]

    test_file = "tests/test_r6fix_dual_lp.py"
    if name == "07_div":
        dual.Dual.__truediv__ = baseline_function("__truediv__", True)
        selector = f"{test_file}::test_r6fix07_division_and_reverse_preserve_representable_derivatives[{math.ldexp(1.0, 665)}]"
    elif name == "07_atan2":
        dual.atan2 = baseline_function("atan2")
        selector = f"{test_file}::test_r6fix07_atan2_matches_independent_fraction_derivative[1e+200-1e+200-0.0-1.0]"
    elif name == "07_mul":
        dual.Dual.__mul__ = baseline_function("__mul__", True)
        selector = f"{test_file}::test_r6fix07_related_product_derivative_avoids_intermediate_range_loss"
    elif name == "07_pow":
        dual.Dual.__pow__ = baseline_function("__pow__", True)
        selector = f"{test_file}::test_r6fix07_related_inverse_power_derivative_is_representable"
    elif name in ("frozen_gap", "frozen_unit"):
        import eab.kernel3d.frozen as frozen
        with zipfile.ZipFile(EVIDENCE.parent / "baseline_tracked.zip") as z:
            old_frozen = z.read("src/eab/kernel3d/frozen.py").decode("utf-8")
        if name == "frozen_gap":
            exec(compile(old_frozen, str(ROOT / "src/eab/kernel3d/frozen.py"), "exec"), vars(frozen))
            selector = "tests/test_r6fix_frozen_construction.py::test_frozen_gap_does_not_overflow_cancelling_dot_products"
        else:
            node = next(n for n in ast.parse(old_frozen).body if isinstance(n, ast.FunctionDef) and n.name == "_unit_jet")
            exec(compile(ast.get_source_segment(old_frozen, node), str(ROOT / "src/eab/kernel3d/frozen.py"), "exec"), vars(frozen))
            selector = "tests/test_r6fix_frozen_construction.py::test_frozen_unit_jet_divides_before_rounding_an_overflowing_tangent_component"
    elif name == "11":
        source = textwrap.dedent(inspect.getsource(dual.Dual.__pow__))
        needle = "    if p == 0.0:\n        return Dual(1.0, (0.0,) * self.width)\n"
        assert source.count(needle) == 1
        scope = dict(vars(dual))
        exec(compile(source.replace(needle, ""), str(ROOT / "src/eab/dual.py"), "exec"), scope)
        dual.Dual.__pow__ = scope["__pow__"]
        selector = f"{test_file}::test_r6fix11_zero_power_is_constant_one_with_same_width"
    elif name == "12":
        source = inspect.getsource(lp.solve)
        needle = "exact_x=(Fraction(0),) * n, exact_y=()"
        assert source.count(needle) == 1
        scope = dict(vars(lp))
        exec(compile(source.replace(needle, "exact_x=None, exact_y=None"), str(ROOT / "src/eab/lp.py"), "exec"), scope)
        lp.solve = scope["solve"]
        selector = f"{test_file}::test_r6fix12_every_optimal_path_has_complete_exact_witnesses"
    else:
        raise ValueError(name)
    print(f"INTERNAL MUTATION {name}: reinstated pre-fix arithmetic / removed guard or certificate fields", flush=True)
    sys.exit(pytest.main(["-q", "-p", "no:cacheprovider", "--maxfail=1", selector,
                          "--basetemp", str(EVIDENCE.parent / "tmp" / f"dual_lp_mutant_{name}")]))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--child":
        child(sys.argv[2])
    summaries = []
    for name in ("07_div", "07_atan2", "07_mul", "07_pow", "11", "12", "frozen_gap", "frozen_unit"):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        p = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "--child", name],
                           cwd=ROOT, env=env, text=True, encoding="utf-8", errors="replace", capture_output=True)
        log = p.stdout + p.stderr
        (EVIDENCE / f"mutation_{name}.log").write_text(log, encoding="utf-8")
        summaries.append({"mutation": name, "exit_code": p.returncode,
                          "last_line": log.strip().splitlines()[-1] if log.strip() else ""})
    (EVIDENCE / "mutations.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    print(json.dumps(summaries, indent=2))
    assert all(row["exit_code"] == 1 and "1 failed" in row["last_line"] for row in summaries)
