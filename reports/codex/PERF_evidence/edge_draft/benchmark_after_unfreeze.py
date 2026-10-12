"""Run only after unfreeze/application: whole edge state, same inputs, old vs new."""
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
from eab.kernel3d import covers3 as current
import test_perf_edge_frame as cases

path = OUT.parent / "baseline/src/eab/kernel3d/covers3.py"
name = "eab.kernel3d._perf_edge_baseline"
spec = importlib.util.spec_from_file_location(name, path)
baseline = importlib.util.module_from_spec(spec)
sys.modules[name] = baseline
spec.loader.exec_module(baseline)

inputs = []
for kind in ("axis", "skew", "folded", "flat_seam"):
    for scale, offset in ((cases.F(1), cases.F(0)), (cases.F(1, 10**8), cases.F(10**6))):
        P = cases._body(kind, scale, offset, False)
        inputs += [(P, edge, direction, tol) for edge, direction, tol in cases._queries(P)]
expected = [baseline._qedge_contains(*args) for args in inputs]
assert expected == [cases._reference_edge_state(*args) for args in inputs]
assert expected == [current._qedge_contains(*args) for args in inputs]

runs = {"baseline": [], "optimized": []}
for repeat in range(7):
    order = (("baseline", baseline._qedge_contains), ("optimized", current._qedge_contains))
    if repeat % 2:
        order = order[::-1]
    for label, function in order:
        start = time.perf_counter()
        actual = [function(*args) for args in inputs]
        runs[label].append(time.perf_counter()-start)
        assert actual == expected
before, after = (statistics.median(runs[key]) for key in ("baseline", "optimized"))
result = dict(cases=len(inputs), rounds=7, states=sorted(set(expected)),
              baseline_seconds=before, optimized_seconds=after, speedup=before/after,
              baseline_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
              optimized_sha256=hashlib.sha256(Path(current.__file__).read_bytes()).hexdigest(),
              cache="existing frame/norm caches warm, identical full state inputs, alternating order", runs=runs)
(OUT / "edge_benchmark.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
