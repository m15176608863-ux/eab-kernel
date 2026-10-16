"""Fixed-seed threshold-edge C1 stress run, separate from default pytest.

Both rings receive independent per-vertex nonrigid errors. The independent
oracle imports Fraction only. An interrupted or source-changing run is invalid;
start again in a fresh --name directory rather than concatenating its rows.
"""
from fractions import Fraction as F
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
from eab.kernel2d.m5d_exit_certificate import exit_order_certificate
from m5d_c1_oracle import exit_oracle
from m5c_source_binding import runtime_source_hashes, assert_current_sources

EVIDENCE = ROOT / "reports/codex/M5d_evidence"
TMP = EVIDENCE / "tmp"


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str)+"\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("fresh single directory name required")
    os.environ["TEMP"] = os.environ["TMP"] = str(TMP)
    out = TMP / args.name
    out.mkdir(parents=True, exist_ok=False)
    binding = runtime_source_hashes(ROOT, __file__)
    started = time.perf_counter()
    rng = random.Random(52761)
    rows, checks = [], 0
    write(out / "progress.json", dict(complete=False, interruption_invalidates=True))
    for case in range(48):
        a = tuple((F(x)+F(rng.randrange(-5, 6), 100), F(y)+F(rng.randrange(-5, 6), 100))
                  for x, y in ((0, 0), (4, 0), (0, 3)))
        b = tuple((F(x)+F(rng.randrange(-5, 6), 100), F(y)+F(rng.randrange(-5, 6), 100))
                  for x, y in ((1, 1), (5, 2), (2, 5)))
        low, high = F(0), F(1)
        if exit_order_certificate(a, b, low, low)["status"] != "CERTIFIED_UNIQUE_EXIT":
            raise AssertionError("seed outside positive-threshold design")
        if exit_order_certificate(a, b, high, high)["status"] != "UNPROVED":
            raise AssertionError("threshold upper bracket still certifies")
        for _ in range(40):
            mid = (low+high)/2
            if exit_order_certificate(a, b, mid, mid)["status"] == "CERTIFIED_UNIQUE_EXIT":
                low = mid
            else:
                high = mid
        for name, radius in (("threshold*(1-2^-24)", low*(1-F(1, 2**24))), ("threshold/2", low/2)):
            result = exit_order_certificate(a, b, radius, radius)
            if result["status"] != "CERTIFIED_UNIQUE_EXIT":
                raise AssertionError("interior threshold unexpectedly refuses")
            for trial in range(64):
                def moved(ring):
                    return tuple(tuple(value+radius*(rng.choice((-1, 1)) if trial < 32
                                      else F(rng.randrange(-1000, 1001), 1000)) for value in p) for p in ring)
                aa, bb = moved(a), moved(b)
                oracle = exit_oracle(aa, bb)
                if not oracle["inside"] or oracle["labels"] != (result["label"],):
                    write(out / "counterexample.json", dict(a=a, b=b, radius=radius, aa=aa, bb=bb,
                                                            certificate=result, oracle=oracle))
                    raise AssertionError("C1 threshold-edge oracle counterexample")
                checks += 1
            rows.append(dict(case=case, regime=name, threshold_lower=low, threshold_upper=high,
                             radius=radius, label=result["label"], perturbations=64))
        write(out / "progress.json", dict(complete=False, cases=case+1, checks=checks))
    observed = runtime_source_hashes(ROOT, __file__)
    assert_current_sources(ROOT, binding, observed)
    result = dict(schema="eab.m5d-c1-threshold-adversarial.v1", complete=True, seed=52761,
                  nominal_configurations=48, threshold_bisections=40, certified_radii=len(rows),
                  nonrigid_both_ring_perturbations=checks, counterexamples=0,
                  oracle_imports=["fractions.Fraction"], source_hashes=binding, source_hashes_end=observed,
                  rows=rows, seconds=time.perf_counter()-started,
                  limits=["Finite adversarial search supports but does not replace the sufficient-condition proof",
                          "Threshold_lower is a certified 40-bisection lower endpoint, not an exact algebraic threshold"])
    write(out / "summary.json", result)
    write(out / "progress.json", dict(complete=True, checks=checks))
    if args.publish:
        target = EVIDENCE / "c1_adversarial.json"
        if target.exists():
            raise ValueError("publication exists; use a separately archived fresh run")
        write(target, result)
    print("M5D_C1_ADVERSARIAL_COMPLETE", checks, "zero counterexamples", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
