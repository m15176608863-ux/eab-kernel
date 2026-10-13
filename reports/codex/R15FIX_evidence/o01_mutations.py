"""Replay targeted real-function mutants without changing production bytes."""
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
spec = importlib.util.spec_from_file_location("r15_force_test", ROOT / "tests/test_r15fix_force_reports.py")
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
rows = []
for api, module, name in [("single", t.single, "limit_load"), ("multi", t.multi, "limit_load_multi")]:
    original = getattr(module, name)
    source = inspect.getsource(original)
    for kind, old, new, assertion in [
        ("product", "raw[j] * Fraction(C.cols[j][i])", "raw[j] * C.cols[j][i]", "O01 complete exact resultant"),
        ("accumulator", "tuple(Fraction(0) for _ in range(dim))", "tuple(0.0 for _ in range(dim))", "O01 complete exact resultant"),
        ("unchecked_output", 'scalar_rational(v, allow_underflow=True, quantity="contact force")', "_fl(v)", "DID NOT RAISE"),
        ("intermediate_norm", "sum(x*x for x in f)", "Fraction(_norm(f))**2", "O01 selected intermediates must not be constructed"),
        ("silent_underflow", "contact_force_display_underflow=force_underflow", "contact_force_display_underflow=False", "O01 nonzero force display underflow must be flagged"),
        ("missing_certificate", "exact_contact_forces=exact_forces", "exact_contact_forces=()", "O01 exact underflow resultant certificate"),
    ]:
        assert source.count(old) == 1
        namespace = dict(vars(module))
        exec(compile(source.replace(old, new), "<R15 O01 internal mutation>", "exec"), namespace)
        setattr(module, name, namespace[name])
        try:
            if kind == "unchecked_output":
                t.test_contact_force_final_overflow_still_has_named_error(api)
            elif kind in ("silent_underflow", "missing_certificate"):
                t.test_contact_force_nonzero_final_underflow_has_explicit_exact_certificate(api, t.F(2)**-1100)
            elif kind == "intermediate_norm":
                t.test_force_selection_does_not_round_overflowing_intermediate_columns(api)
            else:
                t.test_contact_force_report_rounds_complete_exact_sum(api, 2, t.F(10), t.F(2)**-60)
        except BaseException as exc:
            trace = traceback.format_exc()
            print(api, kind, trace)
            rows.append(dict(api=api, kind=kind, killed=assertion in str(exc), assertion=assertion, traceback=trace))
        else:
            rows.append(dict(api=api, kind=kind, killed=False))
        finally:
            setattr(module, name, original)
out = Path(__file__).resolve().parent / "o01_mutations.json"
out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
assert all(r["killed"] for r in rows)
print("12 internal mutations killed at their designated assertions")
