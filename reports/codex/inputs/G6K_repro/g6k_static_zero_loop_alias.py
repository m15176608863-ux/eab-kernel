"""G6K static construction gate: zero-iteration callable aliases lose provenance.
Run: PYTHONDONTWRITEBYTECODE=1 python -X utf8 review/repro/g6k_static_zero_loop_alias.py
Only in-memory function mutation; every tracked source byte stays unchanged.
Oracle: Fraction convex-hull KKT certificate and exact binary64 midpoint interval.
No eab geometry / constructor participates in the expected value.
"""
from pathlib import Path
from fractions import Fraction as F
import hashlib
import importlib.util
import inspect
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
spec = importlib.util.spec_from_file_location("g6k_static_gate", ROOT / "tools/check_exact_construction.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
import eab.kernel3d.covers3 as covers
from eab.kernel3d.geom3 import tetra

source_path = ROOT / "src/eab/kernel3d/covers3.py"
before = hashlib.sha256(source_path.read_bytes()).hexdigest()
source = source_path.read_text(encoding="utf-8-sig")
original_return = "return norm_rational(p), noise"
assert source.count(original_return) == 1

u = math.ulp(0.0)
q = F(1, 2**1074)
assert F(u) == q
rows = ((-F(1), F(1), -q), (-q, -F(1), F(1)), (F(1), -q, -F(1)))
projection = (-q/3,) * 3
assert projection == tuple(sum(row[i] for row in rows)/3 for i in range(3))
squared = sum(x*x for x in projection)
assert all(sum(x*y for x,y in zip(projection, row)) == squared for row in rows)
# KKT: projection is a positive convex combination of the three rows and each
# row lies on its supporting plane; it is the unique minimum-norm hull point.
# The root is inside u's nearest-even cell (u/2, 3u/2).
assert (q/2)**2 < squared < (3*q/2)**2
shape = tetra((0.,0.,0.), (1.,-1.,u), (u,1.,-1.), (-1.,u,1.))
reflected = shape.reflected()
assert covers.cone_intersection_margin(shape, 0, reflected, 0)[0] == u

results = []
for name, loop in (("for_empty_tuple", "for _ in ():"),
                   ("for_range_zero", "for _ in range(0):"),
                   ("while_false", "while False:")):
    body = "root = norm_rational\n    " + loop + "\n        root = abs\n    return root(vector_rational(p, allow_underflow=True)), noise"
    mutant_source = source.replace(original_return, body)
    function_source = inspect.getsource(covers.cone_intersection_margin).replace(original_return, body)
    namespace = dict(vars(covers))
    exec(compile(function_source, "<g6k internal cone alias mutant>", "exec"), namespace)
    actual = namespace["cone_intersection_margin"](shape, 0, reflected, 0)[0]
    issues = gate.scan_text(mutant_source, "src/eab/kernel3d/covers3.py")
    assert actual == 0.0 and actual != u, "mutant must change the real computed cone margin"
    assert issues == [], "the current static gate silently accepts the bad local construction"
    results.append({"case": name, "expected": repr(u), "baseline": repr(u),
                    "mutant": repr(actual), "gate_issues": issues})

assert hashlib.sha256(source_path.read_bytes()).hexdigest() == before
print(json.dumps({"confirmed": True, "results": results, "tracked_source_unchanged": True},
                 ensure_ascii=False, indent=2))
