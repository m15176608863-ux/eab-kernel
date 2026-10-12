"""Same-input baseline/current microbenchmark; no persistent production edits."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "profile"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
from eab.kernel3d import covers3
import test_perf_covers as gates

path = OUT.parent / "baseline/src/eab/kernel3d/covers3.py"
name = "eab.kernel3d._perf_baseline_covers"
spec = importlib.util.spec_from_file_location(name, path)
baseline = importlib.util.module_from_spec(spec)
sys.modules[name] = baseline
spec.loader.exec_module(baseline)

simplexes = [pts for scale, offset in ((1., 0.), (1e-6, 1e6), (1e3, -1e5))
             for kind in ("random", "duplicate", "coplanar", "collinear", "mixed_denominators")
             for pts in gates._samples(kind, scale, offset)]
hulls = [pts for scale, offset in ((1., 0.), (1e-6, 1e6), (1e3, -1e5))
         for kind in ("random", "duplicate", "coplanar", "collinear", "mixed_denominators")
         for pts in gates._samples(kind, scale, offset, 12)]


def measure(name, old, new, inputs):
    expected = [old(points) for points in inputs]
    actual = [new(points) for points in inputs]
    assert actual == expected
    results = {"baseline": [], "optimized": []}
    for repeat in range(7):
        order = (("baseline", old), ("optimized", new))
        if repeat % 2:
            order = order[::-1]
        for label, func in order:
            start = time.perf_counter()
            answers = [func(points) for points in inputs]
            results[label].append(time.perf_counter() - start)
            assert answers == expected
    before = statistics.median(results["baseline"])
    after = statistics.median(results["optimized"])
    return {"operation": name, "cases": len(inputs), "rounds": 7,
            "exact_point_and_support_equality": True, "baseline_seconds": before,
            "optimized_seconds": after, "speedup": before / after, "runs": results}


result = {
    "baseline_source": str(path.relative_to(ROOT)),
    "baseline_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "optimized_sha256": hashlib.sha256(Path(covers3.__file__).read_bytes()).hexdigest(),
    "measurement": "alternating order, median of seven same-input rounds; no caches or filters added",
    "results": [measure("_qclosest_simplex", baseline._qclosest_simplex, covers3._qclosest_simplex, simplexes),
                measure("_qclosest_hull_uncached", baseline._qclosest_hull.__wrapped__, covers3._qclosest_hull.__wrapped__, hulls)],
}
(OUT / "covers_benchmark.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
