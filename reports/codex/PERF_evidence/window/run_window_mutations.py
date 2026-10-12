"""Re-run two in-process production mutations; no source file is overwritten."""
from pathlib import Path
import inspect
import json
import runpy
import sys
import traceback

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
import eab.margin as M
from eab.kernel3d import exact_sweep as S
import pytest


def main():
    helpers = runpy.run_path(str(ROOT / "tests/test_perf_contact_window.py"))
    original_shell = inspect.getsource(S.star_core)
    original_models = inspect.getsource(S.contact_models)
    anchor = "choices.append((f'shift_{axis}_{sign}',translate_exact(A,offset),B))"
    cases = [
        ("shell_w_to_2w", S.star_core,
         original_shell.replace("alpha=min(w/radius,F(1,2))", "alpha=min(2*w/radius,F(1,2))"),
         helpers['_assert_thick_bilateral_overlap_rejected'], "reject-thicker-than-w-shell"),
        ("six_axes_to_five", S.contact_models,
         original_models.replace(anchor, "\n            if (axis,sign)!=(2,1):\n                " + anchor),
         lambda: helpers['_assert_axis_certificate'](2, 1), "axis-public-report"),
    ]
    output = []
    for name, function, source, gate, expected in cases:
        assert source != inspect.getsource(function)
        namespace = dict(S.__dict__)
        exec(compile(source, f"<PERF mutation {name}>", "exec"), namespace)
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(S, function.__name__, namespace[function.__name__])
            patch.setattr(M, '_resolved', M._resolve)
            try:
                gate()
            except AssertionError as error:
                assert expected in str(error), (name, str(error))
                trace = traceback.format_exc()
                (Path(__file__).parent / f"mutation_{name}.log").write_text(trace, encoding="utf-8")
                output.append({"mutation": name, "production_function": function.__name__,
                               "target_assertion": expected, "caught": True,
                               "failure": str(error), "injection": "in-memory function body"})
            else:
                raise AssertionError(f"mutation survived: {name}")
    (Path(__file__).parent / "mutation_results.json").write_text(
        json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
