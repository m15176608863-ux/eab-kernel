"""Compile defects inside margin._resolve and call the migrated real gates.

No production source is written and no output rows are fabricated.
"""
from pathlib import Path
import inspect
import json
import sys
import traceback

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

import eab.margin as margin
import test_invariance_geom as invariance
import test_near_parallel_edges as parallel

original = margin._resolve
source = inspect.getsource(original)
mutations = [
    ("default_implicit_ctol", "ctol = _contact_window(contact_window)",
     "ctol = _contact_window(contact_resolution(A, B) if contact_window is None else contact_window)",
     lambda: parallel.test_near_parallel_ridge_edges_match_the_exact_rational_distance(1e-8, 1e-9, .3, 0),
     "default-exact distance construction"),
    ("explicit_window_ignored", "ctol = _contact_window(contact_window)", "ctol = Fraction(0)",
     lambda: parallel.test_near_parallel_ridge_edges_match_the_exact_rational_distance(1e-8, 1e-9, .3, 0),
     "assert d == 0.0"),
    ("default_source_ring_instead_of_actual_surface",
     "exact_surface=contact_window is None or not ctol", "exact_surface=False",
     lambda: invariance.test_margin_layer_is_invariant("box_box_face", 7, 0., .001),
     "default-exact surface nearest label"),
]
rows = []
for name, before, after, test, expected in mutations:
    changed = source.replace(before, after)
    assert changed != source
    namespace = dict(margin.__dict__)
    exec(compile(changed, "<E5b integration internal mutation>", "exec"), namespace)
    margin._resolve = namespace["_resolve"]
    try:
        test()
    except AssertionError as error:
        trace = traceback.extract_tb(error.__traceback__)
        target = trace[-1]
        message = str(error)
        killed = expected in message or expected in (target.line or "")
        rows.append(dict(id=name, status="KILLED" if killed else "WRONG_ASSERTION",
                         expected_assertion=expected, message=message,
                         actual_assertion=target.line, file=target.filename, line=target.lineno,
                         injection_before=before, injection_after=after,
                         injection_method="compile inside production _resolve; run existing test function"))
        assert killed, rows[-1]
    else:
        raise AssertionError(f"mutation escaped: {name}")
    finally:
        margin._resolve = original
out = Path(__file__).with_name("integration_mutations.json")
out.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(rows, ensure_ascii=False, indent=2))
