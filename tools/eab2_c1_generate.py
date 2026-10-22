"""Seeded valid-ring near-degeneracy generator and full C1 exact-set differential.

Examples (explicit absolute test DLL is mandatory):
  python tools/eab2_c1_generate.py --dll D:/.../eab2_test.dll --count 100 --output REPORT.json
  python tools/eab2_c1_generate.py --dll D:/.../eab2_test.dll --count 10000 --output REPORT.json
The first is an estimate/smoke run, not the required 10,000-case result. Cases
are constructed with a known origin label, then perturbed and independently
validated. Rejected/duplicate candidates never count as legal differential cases.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction as F
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eab.kernel2d.exact import polygons_overlap_exact  # noqa: E402
from eab.kernel2d.global_entrance import _ring  # noqa: E402
from eab2_c1_cases import Case, bits  # noqa: E402
from eab2_diff_c1 import Dll, run_case, write_json  # noqa: E402


def rectangle(x, y, w, h):
    return ((x, y), (x+w, y), (x+w, y+h), (x, y+h))


def candidate(rng, attempt):
    # Eight categories, with small polygons dominant for an auditable full-set
    # replay. Concave seams/isolated contacts are not replaced by convex examples.
    bucket = attempt % 100
    family = ("collinear" if bucket < 20 else "one_ulp_gap" if bucket < 40
              else "one_ulp_overlap" if bucket < 60 else "near_parallel" if bucket < 78
              else "narrow_edge" if bucket < 96 else "extreme_exponent" if bucket < 98
              else "tight_seam" if bucket == 98 else "isolated_contact")
    u, h, w = (F(rng.randint(513, 8191), 1024) for _ in range(3))
    a = rectangle(F(0), F(0), u, h)
    b = rectangle(u, -h/4, w, 3*h/2)
    expected = 0
    if family == "collinear":
        a = ((F(0), F(0)), (u/2, F(0)), (u, F(0)), (u, h), (F(0), h))
    elif family == "one_ulp_gap":
        b = rectangle(F(math.nextafter(float(u), math.inf)), -h/4, w, 3*h/2)
        expected = -1
    elif family == "one_ulp_overlap":
        b = rectangle(F(math.nextafter(float(u), -math.inf)), -h/4, w, 3*h/2)
        expected = 1
    elif family == "near_parallel":
        a = ((F(0), F(0)), (u, F(0)), (F(math.nextafter(float(u), math.inf)), h), (F(0), h))
        expected = 1
    elif family == "narrow_edge":
        epsilon = F(math.ulp(float(u))) / 2**rng.randint(0, 20)
        a = rectangle(F(0), F(0), epsilon, h)
        b = rectangle(epsilon, -h/4, w, 3*h/2)
    elif family == "extreme_exponent":
        u, h, w = (F(rng.randint(1, 15)) for _ in range(3))
        scale_exp = rng.choice((-1070, -1000, -700, 700, 1000))
        scale = F(2)**scale_exp
        a = rectangle(F(0), F(0), u*scale, h*scale)
        b = rectangle(u*scale, F(0), w*scale, h*scale)
    elif family == "tight_seam":
        a = ((0, h/2), (u, h/2), (u, 3*h/2), (0, 3*h/2))
        b = ((-u, -h), (2*u, -h), (2*u, 2*h), (u, 2*h), (u, 0), (0, 0), (0, 2*h), (-u, 2*h))
    elif family == "isolated_contact":
        a = ((u, h), (5*u, h), (5*u, 5*h), (u, 5*h))
        b = ((0, 0), (6*u, 0), (6*u, 2*h), (5*u, 2*h), (5*u, h), (u, h),
             (u, 5*h), (5*u, 5*h), (5*u, 4*h), (6*u, 4*h), (6*u, 6*h), (0, 6*h))

    turns = rng.randrange(4)
    def transform(p):
        x, y = map(F, p)
        for _ in range(turns):
            x, y = -y, x
        return x, y
    a, b = tuple(map(transform, a)), tuple(map(transform, b))
    if attempt % 97 == 0:
        # A real loss-of-resolution perturbation, not a pre-labelled invalid
        # fixture: a large common binary translation can collapse a short edge.
        shift = F(2**50)
        a = tuple((x+shift, y-shift) for x, y in a)
        b = tuple((x+shift, y-shift) for x, y in b)
    rounded = tuple(tuple(tuple(float(v) for v in p) for p in poly) for poly in (a, b))
    changed = sum(F(v) != F(float(v)) for poly in (a, b) for p in poly for v in p)
    if rng.randrange(2):
        rounded = tuple(tuple(reversed(poly)) for poly in rounded)
    return family, rounded, expected, changed


def generated(count, seed, stats):
    rng = random.Random(seed)
    seen = set()
    accepted = 0
    while accepted < count:
        stats["attempts"] += 1
        if stats["attempts"] > 3*count+100:
            raise RuntimeError("finite candidate-attempt budget exceeded")
        family, (a, b), expected, changed = candidate(rng, stats["attempts"])
        try:
            if any(not math.isfinite(v) for poly in (a, b) for p in poly for v in p):
                raise ValueError("nonfinite coordinate after perturbation")
            pa, pb = _ring(a), _ring(b)
        except (ValueError, OverflowError) as error:
            stats["rejected"][str(error)] += 1
            continue
        state = polygons_overlap_exact(pa, pb)
        if state != expected:
            stats["rejected"]["known_label_not_preserved_after_binary64_perturbation"] += 1
            continue
        key = tuple(tuple(tuple(bits(v) for v in p) for p in poly) for poly in (a, b))
        if key in seen:
            stats["rejected"]["duplicate_ordered_input_bits"] += 1
            continue
        seen.add(key)
        accepted += 1
        stats["accepted"] = accepted
        stats["family_counts"][family] += 1
        stats["known_origin_states"][str(state)] += 1
        yield Case(f"generated/{family}/{accepted:05d}", a, b,
                   [f"seed={seed};attempt={stats['attempts']};known_origin_body_state={state}"], changed), key


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20261022)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("count must be positive")
    # Large journals and input chunks are replay evidence, intentionally not
    # deliverable source files. The summary retains hashes and exact paths.
    run_dir = ROOT / "reports/codex/C1E_evidence/tmp" / args.output.stem
    if run_dir.exists() or args.output.exists():
        parser.error("immutable runs require a new output name")
    run_dir.mkdir(parents=True)
    stats = {"attempts": 0, "accepted": 0, "rejected": Counter(), "family_counts": Counter(), "known_origin_states": Counter()}
    report = {"schema": "eab2.c1.generated.v1", "seed": args.seed, "requested_legal_cases": args.count,
              "complete": False, "status": "RUNNING", "completed_cases": 0, "mismatches": [],
              "statistics": stats, "input_chunks": [], "totals": Counter(),
              "comparison": "full exact canonical E/O sets, source strata, all layer states and local certificates; not just origin queries",
              "meets_10000_case_count": False, "journal": str(run_dir / "case_results.jsonl")}
    dll = Dll(args.dll)
    report.update(dll_sha256=hashlib.sha256(args.dll.read_bytes()).hexdigest(), build_identity=dll.identity)
    started = time.perf_counter()
    chunk = []
    def flush_chunk():
        if not chunk:
            return
        path = run_dir / f"inputs_{len(report['input_chunks'])+1:03d}.json.gz"
        data = gzip.compress((json.dumps(chunk, separators=(",", ":"))+"\n").encode(), mtime=0)
        path.write_bytes(data)
        report["input_chunks"].append({"path": str(path), "count": len(chunk), "sha256": hashlib.sha256(data).hexdigest()})
        chunk.clear()
    try:
        with (run_dir / "case_results.jsonl").open("w", encoding="utf-8", newline="") as journal:
            for case, encoded in generated(args.count, args.seed, stats):
                try:
                    row, _ = run_case(dll, case)
                except Exception as error:
                    failure = {"name": case.name, "reason": repr(error), "xy_bits": encoded, "sources": case.sources}
                    report["mismatches"].append(failure)
                    write_json(run_dir / "first_mismatch.json", failure)
                    break
                journal.write(json.dumps(row, separators=(",", ":"))+"\n")
                journal.flush()
                chunk.append({"case_id": case.name, "xy_bits": encoded, "source": case.sources})
                report["completed_cases"] += 1
                for name in ("cpp_layer_samples_rechecked", "python_layer_samples_reverse_checked", "raw_sources_checked", "independent_sector_samples"):
                    report["totals"][name] += row.get(name, row.get("local_statistics", {}).get(name, 0))
                if len(chunk) == 500:
                    flush_chunk()
                if report["completed_cases"] % 25 == 0:
                    report["seconds"] = time.perf_counter()-started
                    write_json(args.output, report)
                    print(f"C1_GENERATED_PROGRESS completed={report['completed_cases']}/{args.count} seconds={report['seconds']:.3f}", flush=True)
    finally:
        flush_chunk()
        dll.close()
        report["seconds"] = time.perf_counter()-started
        report["complete"] = report["completed_cases"] == args.count and not report["mismatches"]
        report["status"] = "PASS" if report["complete"] else "FAIL"
        report["meets_10000_case_count"] = report["complete"] and args.count >= 10000
        report["journal_sha256"] = hashlib.sha256((run_dir / "case_results.jsonl").read_bytes()).hexdigest()
        write_json(args.output, report)
    print(f"EAB2_C1_GENERATED attempts={stats['attempts']} legal={stats['accepted']} completed={report['completed_cases']} mismatches={len(report['mismatches'])} status={report['status']}")
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
