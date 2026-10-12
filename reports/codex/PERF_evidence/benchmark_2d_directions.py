"""Cold-evaluation microbenchmark and BB52 integration old/current comparison."""
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "profile"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests"), str(ROOT)]
from eab.kernel2d import covers as current
from tools import bb52_g0
import test_perf_2d_directions as cases

path = OUT.parent / "baseline/src/eab/kernel2d/covers.py"
name = "eab.kernel2d._perf_directions_baseline"
spec = importlib.util.spec_from_file_location(name, path)
baseline = importlib.util.module_from_spec(spec)
sys.modules[name] = baseline
spec.loader.exec_module(baseline)

inputs = [args for kind in ("random", "collinear", "boundary", "almost_reflex", "unequal_lengths")
          for scale, offset in ((cases.F(1), cases.F(0)), (cases.F(1, 10**8), cases.F(10**6)))
          for args in cases.direction_cases(kind, scale, offset)]
old = baseline._ve_side_directions.__wrapped__
new = current._ve_side_directions.__wrapped__
expected = [old(*args) for args in inputs]
assert expected == [new(*args) for args in inputs]
runs = {"baseline": [], "optimized": []}
for repeat in range(7):
    order = (("baseline", old), ("optimized", new))
    if repeat % 2:
        order = order[::-1]
    for label, function in order:
        start = time.perf_counter()
        answers = [function(*args) for args in inputs]
        runs[label].append(time.perf_counter()-start)
        assert answers == expected
before, after = (statistics.median(runs[key]) for key in ("baseline", "optimized"))

saved = current._ve_side_directions
integration_runs = {"baseline": [], "optimized": []}
expected_result = None
try:
    for repeat in range(3):
        order = (("baseline", baseline._ve_side_directions), ("optimized", saved))
        if repeat % 2:
            order = order[::-1]
        for label, function in order:
            function.cache_clear()
            current._ve_side_directions = function
            start = time.perf_counter()
            result = bb52_g0.analyze(samples_per_pair=3, seed=0)
            integration_runs[label].append(time.perf_counter()-start)
            if expected_result is None:
                expected_result = result
            assert result == expected_result, "complete BB52 report equality"
finally:
    current._ve_side_directions = saved
    saved.cache_clear()
old_integration, new_integration = (statistics.median(integration_runs[key]) for key in ("baseline", "optimized"))
result = dict(
    baseline_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    optimized_sha256=hashlib.sha256(Path(current.__file__).read_bytes()).hexdigest(),
    micro=dict(cases=len(inputs), rounds=7, mode="cache bypassed; alternating order; median",
               states=sorted(set(expected)), baseline_seconds=before, optimized_seconds=after,
               speedup=before/after, runs=runs),
    bb52=dict(samples_per_pair=3, seed=0, rounds=3, mode="direction cache cleared each call; alternating order",
              complete_result_equality=True, baseline_seconds=old_integration,
              optimized_seconds=new_integration, speedup=old_integration/new_integration, runs=integration_runs))
(OUT / "directions_benchmark.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
