"""Compare old/new test helper inputs and Lipschitz results, without policy."""
import json
from pathlib import Path
import random
import sys
import types

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests"), str(ROOT / "tools")]


def module(file, old):
    actual = ROOT / "tests" / file
    source_path = BASE / "test_factory_rewrite_backup/tests" / file if old else actual
    name = "r12fixb_equivalence_" + ("old_" if old else "new_") + file[:-3]
    mod = types.ModuleType(name)
    mod.__file__ = str(actual)
    sys.modules[name] = mod
    exec(compile(source_path.read_text(encoding="utf-8-sig"), str(actual), "exec"), mod.__dict__)
    return mod


def geometry(pair):
    return [(tuple(p.verts), tuple(p.faces)) for p in pair]


results = {"factory_cases": [], "lipschitz_cases": []}
for file, table_name, factory, index in (
    ("test_invariance_geom.py", "PAIRS", "_pair_for_name", 0),
    ("test_invariance_interlock.py", "MARGIN_CASES", "_margin_pair_for_name", 1),
):
    old, new = module(file, True), module(file, False)
    before, after = getattr(old, table_name), getattr(new, table_name)
    assert list(before) == list(after)
    for name, row in before.items():
        assert row[:index] + row[index+1:] == after[name][:index] + after[name][index+1:]
        a = geometry(row[index]())
        b = geometry(getattr(new, factory)(name))
        assert a == b, (file, name)
        results["factory_cases"].append({"file": file, "name": name, "identical_vertices_faces_and_metadata": True})

old, new = module("test_margin.py", True), module("test_margin.py", False)
delta = 0.25
E, local, loops, glob = old._lipschitz_setup(delta)
E2, local2, loops2, glob2 = new._lipschitz_setup(delta)
assert (E.verts, E.faces, local, loops, glob) == (E2.verts, E2.faces, local2, loops2, glob2)
p0 = min(glob, key=lambda xy: old.norm(old.sub(xy[0], xy[1])))[0]


def normal_for(mod, kind, trace):
    rng = random.Random(99)
    def normal(E, x):
        trace.append(x)
        if kind == "random":
            return mod.unit((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)))
        if kind == "constant":
            return (1.0, 0.0, 0.0)
        if kind == "radial":
            return mod.unit(x)
        n = mod._true_normal(E, x)
        if kind == "local_flip" and x[0] > 0.0:
            return tuple(-c for c in n)
        if kind == "bump" and mod.norm(mod.sub(x, p0)) < 1e-3:
            return (n[0] + 10.0, n[1], n[2])
        return n
    return normal


for kind in ("true", "random", "constant", "radial", "local_flip", "bump"):
    old_trace, new_trace = [], []
    old_normal = normal_for(old, kind, old_trace)
    new_normal = normal_for(new, kind, new_trace)
    before = old._lipschitz_verdict(old_normal, delta)
    samples = [[(x, y, new_normal(E, x), new_normal(E, y)) for x, y in pairs]
               for pairs in (local, loops, glob)]
    after = new._lipschitz_verdict(*samples, delta=delta)
    assert old_trace == new_trace, kind
    assert before == after, (kind, before, after)
    results["lipschitz_cases"].append({"kind": kind, "normal_call_count": len(old_trace),
                                     "normal_call_order_identical": True, "result_identical": True,
                                     "result": after})
results["identical_lipschitz_point_sets"] = True
(BASE / "test_factory_data_equivalence.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
print("FACTORY_DATA_EQUIVALENCE_OK", len(results["factory_cases"]), len(results["lipschitz_cases"]))
