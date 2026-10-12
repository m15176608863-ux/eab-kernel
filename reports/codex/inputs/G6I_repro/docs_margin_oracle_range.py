"""WO-G6I: independent interval truth exposes squared-distance pre-rounding.

Writes nothing; production and test helper are both exercised on the exact
same raw boxes. No production geometric primitive computes expected truth.
"""
from pathlib import Path
from fractions import Fraction as F
import json
import inspect
import ast
import subprocess
import math
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]
from eab.kernel3d.geom3 import Polyhedron
from eab.margin import body_distance
from e5b_margin_oracle import check_exact_margin
import eab.margin as production
import pytest

FACES = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
SIGNS = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
         (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]

def cube(center, scale):
    return Polyhedron([tuple(center[k] + sign[k]*scale for k in range(3))
                       for sign in SIGNS], FACES.copy())

rows = []
for exponent in (-500, -540, -600):
    scale = F(2)**exponent
    a, b = cube((4*scale, F(0), F(0)), scale), cube((F(0),)*3, scale)
    # Cartesian product truth: separation only in x, lower A.x - upper B.x = 2s.
    truth = 2*scale
    got, label = body_distance(a, b)
    assert got == float(truth) and got > 0
    prematurely_rounded = math.sqrt(float(truth**2))
    try:
        check_exact_margin(a, b, 3*scale, state=-1, minimum_squared=truth**2)
        status = "PASS"
    except AssertionError as error:
        status = f"AssertionError: {error}"
    rows.append({"exponent": exponent, "production": got,
                 "independent_interval_truth": float(truth),
                 "sqrt_float_squared_oracle": prematurely_rounded,
                 "test_oracle_status": status, "label": label})
assert rows[0]["test_oracle_status"] == "PASS"
assert all(row["test_oracle_status"] == "AssertionError: default-exact distance construction"
           for row in rows[1:])
print(json.dumps(rows, indent=2))
print("CONFIRMED: exact test oracle falsely rejects correct representable distance")

# Do not manufacture result records: compile premature rounding into the two
# real public construction functions, keeping their exact decisions/certificates
# and their ordinary self-check intact. The oracle then ACCEPTS wrong answers.
originals = {name: getattr(production, name) for name in ("body_distance", "margin_contacts")}
# Compare the ORIGINAL b6126cf distance-scale assertion on an original named
# pair at an additional admissible power-of-two scale (not falsely claiming the
# historical grid contained this scale). Bind its API to the default exact
# public entry point, because the migrated file now wraps old assertions in an
# explicit legacy contact window while check_exact_margin guards default mode.
import test_invariance_geom as invariance
old_text = subprocess.check_output(
    ["git", "show", "b6126cf:tests/test_invariance_geom.py"], cwd=ROOT).decode("utf-8")
old_node = next(node for node in ast.parse(old_text).body
                if isinstance(node, ast.FunctionDef)
                and node.name == "test_body_distance_scales_and_keeps_its_label")
old_source = ast.get_source_segment(old_text, old_node).replace(
    "def test_body_distance_scales_and_keeps_its_label", "def old_distance_gate")
old_scope = dict(vars(invariance))
exec(old_source, old_scope)
old_scope["body_distance"] = originals["body_distance"]
old_args = ("box_box_face", 0, 0.0, float(F(2)**-600))
base, motion, moved_a, moved_b = invariance._cell(*old_args)
old_scope["old_distance_gate"](*old_args)
try:
    check_exact_margin(moved_a, moved_b, old_args[-1]*invariance.PAIRS[old_args[0]][3], state=-1)
    new_baseline = "PASS"
except AssertionError as error:
    new_baseline = f"AssertionError: {error}"
assert new_baseline == "AssertionError: default-exact distance construction"
faults = (("body_distance", "_exact.sqrt_rational(d2)", "math.sqrt(float(d2))"),
          ("margin_contacts", "w = _exact.sqrt_rational(d2, allow_underflow=True)",
           "w = math.sqrt(float(d2))"))
with pytest.MonkeyPatch.context() as patch:
    for name, old, new in faults:
        source = inspect.getsource(originals[name])
        assert source.count(old) == 1
        namespace = dict(vars(production))
        exec(compile(source.replace(old, new), __file__, "exec"), namespace)
        patch.setattr(production, name, namespace[name])
    scale = F(2)**-600
    a, b = cube((4*scale, F(0), F(0)), scale), cube((F(0),)*3, scale)
    wrong, label = production.body_distance(a, b)
    contacts = production.margin_contacts(a, b, delta=3*scale)
    assert wrong == 0.0 and float(2*scale) > 0.0
    assert all(contact.distance == 0.0 for contact in contacts)
    check_exact_margin(a, b, 3*scale, state=-1, minimum_squared=4*scale**2)
    print(json.dumps({"real_internal_mutant": "pre-round squared distance before sqrt in body_distance and margin_contacts",
                      "wrong_public_body_distance": wrong,
                      "wrong_contact_distances": sorted({contact.distance for contact in contacts}),
                      "independent_truth": float(2*scale),
                      "oracle_result": "PASS"}, indent=2))
    old_scope["body_distance"] = production.body_distance
    try:
        old_scope["old_distance_gate"](*old_args)
        old_mutant = "PASS"
    except AssertionError as error:
        old_mutant = f"AssertionError: {error}"
    assert old_mutant.startswith("AssertionError:")
    check_exact_margin(moved_a, moved_b, old_args[-1]*invariance.PAIRS[old_args[0]][3], state=-1)
    print(json.dumps({"old_vs_new_same_input": old_args,
                      "grid_limit": "2^-600 is an added stress scale, not a deleted historical grid cell",
                      "old_gate_source": "git show b6126cf:tests/test_invariance_geom.py::test_body_distance_scales_and_keeps_its_label",
                      "old_baseline": "PASS", "new_oracle_baseline": new_baseline,
                      "old_internal_mutant": old_mutant, "new_oracle_internal_mutant": "PASS",
                      "retained_old_assertion": "abs(d - s * base[d]) <= M.dist_tol(L)",
                      "new_oracle_assertion": "abs(distance - sqrt(float(nearest))) <= 4*ulp(sqrt(float(nearest)))"}, indent=2))
assert all(getattr(production, name) is original for name, original in originals.items())
print("RESTORED: both production function bindings; all tracked files remain untouched")
