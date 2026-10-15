"""Read-only M5a2 full-endpoint affine residual and discrepancy diagnostic.

No general affine first-entrance solver or positive-residual certificate is
implied. All >1 MB per-block/diagnostic records stay in the ignored tmp tree.
An interrupted run has complete=false and is never resumed as evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from fractions import Fraction as F
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
import m5a_se2_replay as rigid
from eab.construction import scalar_rational, sqrt_rational
from eab.kernel2d.affine_motion import DDAAffineMotion, fit_affine
from eab.kernel2d import g0_oracle as oracle

EVIDENCE = ROOT / "reports/codex/M5a2_evidence"
TMP = EVIDENCE / "tmp"
FROZEN = ROOT / "reports/codex/M5a_evidence/tmp/replay/full_r1"


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")


def code_hashes():
    names = set(rigid.code_hashes())
    names.update(("src/eab/kernel2d/affine_motion.py", "tools/m5a2_affine_replay.py"))
    return {name: file_hash(ROOT / name) for name in sorted(names)}


def input_paths(case):
    return {"snapshot": rigid.INPUTS / case / "shadow.jsonl",
            "terminal": rigid.INPUTS / case / "geom.csv",
            "m5a_normalized": FROZEN / case / "normalized.jsonl.gz",
            "m5a_audit": FROZEN / case / "audit.json"}


def input_hashes(paths):
    return {name: file_hash(path) for name, path in sorted(paths.items())}


def require_stable_inputs(paths, initial):
    if input_hashes(paths) != initial:
        raise AssertionError("affine replay input changed during run: discard and rerun")


def distribution(values, square_root=False):
    values = sorted(values)
    if not values:
        return {"count": 0, "zero": 0, "quantiles_exact": {}, "quantiles_display": {}}
    picked = {name: values[(len(values)-1)*n//d] for name, n, d in
              (("min", 0, 1), ("median", 1, 2), ("p95", 95, 100), ("max", 1, 1))}
    display = sqrt_rational if square_root else scalar_rational
    return {"count": len(values), "zero": values.count(F(0)),
            "exact_values_are_squares": square_root,
            "quantiles_exact": {name: str(value) for name, value in picked.items()},
            "quantiles_display": {name: display(value, allow_underflow=True) for name, value in picked.items()}}


def gap_square(A, B):
    """Exact solid-set Euclidean gap squared; zero for touching/overlap.

    Uses independent G0 integer winding and rational projection, not production
    SE2/affine events. This is a normalizing observable, never a certificate.
    """
    if oracle.overlap(A, B) >= 0:
        return F(0)
    return min(oracle.segment_square(p, q, Q[(j+1) % len(Q)])[0]
               for P, Q in ((A, B), (B, A)) for p in P for j, q in enumerate(Q))


def nearest_gap_squares(polygons):
    """AABB lower bound only skips pairs already proved non-minimal."""
    boxes = {b: tuple((min(p[k] for p in poly), max(p[k] for p in poly)) for k in (0, 1))
             for b, poly in polygons.items()}
    cache, result = {}, {}
    for a in sorted(polygons):
        candidates = []
        for b in polygons:
            if b != a:
                lower = sum(max(F(0), boxes[a][k][0]-boxes[b][k][1], boxes[b][k][0]-boxes[a][k][1])**2 for k in (0, 1))
                candidates.append((lower, b))
        best = None
        for lower, b in sorted(candidates):
            if best is not None and lower >= best:
                break
            key = tuple(sorted((a, b)))
            if key not in cache:
                cache[key] = gap_square(polygons[a], polygons[b])
            value = cache[key]
            best = value if best is None else min(best, value)
        result[a] = best
    return result


def pack(values):
    return {key: distribution(value, key.endswith("_gap_square")) for key, value in sorted(values.items())}


def json_points(poly):
    return [[str(v) for v in p] for p in poly]


def replay_case(case, output, expected_inputs=None):
    start_time = time.perf_counter()
    directory = Path(output) / case
    directory.mkdir(parents=True, exist_ok=False)
    progress = directory / "progress.json"
    write_json(progress, {"case": case, "complete": False, "processed_steps": 0})
    paths = input_paths(case)
    initial_inputs = input_hashes(paths)
    if expected_inputs is not None and initial_inputs != expected_inputs:
        raise AssertionError("affine replay input changed before worker: discard and rerun")
    source, terminal_source = paths["snapshot"], paths["terminal"]
    _, frames, _ = rigid.chord.snapshot.read_snapshot(source)
    terminal = rigid.chord.load_geometry_csv(terminal_source, frames)
    paired = rigid.chord.paired_geometries(frames, terminal)
    baseline_path = paths["m5a_normalized"]
    baseline_audit = json.loads(paths["m5a_audit"].read_text(encoding="utf-8"))
    assert baseline_audit["complete"] and baseline_audit["audit"] == "GREEN"
    assert baseline_audit["normalized_sha256"] == initial_inputs["m5a_normalized"]
    assert baseline_audit["input_hashes"]["snapshot"] == initial_inputs["snapshot"]
    assert baseline_audit["input_hashes"]["terminal_source"] == initial_inputs["terminal"]
    require_stable_inputs(paths, initial_inputs)
    values, counts, discrepancies, examples = defaultdict(list), Counter(), Counter(), {}
    rows_path = directory / "block_residuals.jsonl.gz"
    with gzip.open(baseline_path, "rt", encoding="utf-8") as old, gzip.open(rows_path, "wt", encoding="utf-8", newline="\n") as rows:
        for frame, sg, eg in paired:
            frozen = json.loads(next(old))
            assert frozen["step"] == frame["step"] and frozen["start_geometry_sha256"] == rigid.chord.digest(frame["geometry"])
            geometries = {b: (rigid.chord._exact_poly(sg.blocks[b].poly), rigid.chord._exact_poly(eg.blocks[b].poly)) for b in sg.blocks}
            affine = {b: fit_affine(*pair) for b, pair in geometries.items()}
            se2 = {b: rigid.fit_rigid(*pair) for b, pair in geometries.items()}
            gaps = nearest_gap_squares({b: pair[0] for b, pair in geometries.items()})
            for b, (A, end) in geometries.items():
                a, r = affine[b], se2[b]
                assert r.delta == F(frozen["blocks"][str(b)]["delta_linf"]), "rigid fit semantic reproduction"
                span = max(max(p[k] for p in A)-min(p[k] for p in A) for k in (0, 1))
                coord_scale = max(abs(v) for poly in (A, end) for p in poly for v in p)
                epsilon_scale = coord_scale*F(1, 2**52)
                gap = gaps[b]
                for name, delta in (("rigid", r.delta), ("affine", a.delta)):
                    values[name+"_absolute"].append(delta)
                    values[name+"_over_block_span"].append(delta/span)
                    values[name+"_over_coordinate_epsilon"].append(delta/epsilon_scale)
                    if gap is not None and gap > 0:
                        values[name+"_over_gap_square"].append(delta*delta/gap)
                counts["blocks"] += 1
                counts[a.endpoint_certificate] += 1
                counts["nearest_gap_zero" if gap == 0 else "nearest_gap_positive" if gap is not None else "nearest_gap_unavailable"] += 1
                model = DDAAffineMotion(a.matrix, r.motion.u1, a.translation, a.center)
                counts["orientation_sufficient" if model.orientation_preserving_sufficient else "orientation_unknown"] += 1
                assert tuple(model.corrected_at(p, e, 1) for p, e in zip(A, a.residuals)) == end
                row = {"case": case, "step": frame["step"], "block": b, "vertices": len(A),
                       "delta_rigid": str(r.delta), "delta_affine": str(a.delta), "block_span": str(span),
                       "coordinate_epsilon_scale": str(epsilon_scale), "nearest_gap_square": None if gap is None else str(gap),
                       "endpoint_certificate": a.endpoint_certificate}
                rows.write(json.dumps(row, separators=(",", ":"))+"\n")
                if "nonzero_affine_residual" not in examples and a.delta > 0:
                    examples["nonzero_affine_residual"] = {**row, "start": json_points(A), "end": json_points(end),
                                                          "matrix": json_points(a.matrix), "residuals": json_points(a.residuals)}
            ids = sorted(geometries)
            zero = sum(affine[b].delta == 0 for b in ids)
            counts["all_pairs"] += len(ids)*(len(ids)-1)//2
            counts["zero_affine_endpoint_residual_pairs"] += zero*(zero-1)//2
            counts["positive_affine_residual_uncertified_pairs"] += len(ids)*(len(ids)-1)//2-zero*(zero-1)//2
            counts["physical_path_uncertified_pairs"] += len(ids)*(len(ids)-1)//2
            counts["steps"] += 1
            for pair in frozen["pairs"]:
                if pair["initial_state"] != -1 or pair["same_chord_status_and_cover"]:
                    continue
                a, b = pair["pair"]
                A, Aend = geometries[a]
                B, Bend = geometries[b]
                endpoint_chord = oracle.overlap(Aend, Bend)
                endpoint_rigid = oracle.overlap(tuple(se2[a].motion.endpoint(p) for p in A), tuple(se2[b].motion.endpoint(p) for p in B))
                endpoint_affine = oracle.overlap(tuple(affine[a].endpoint(p) for p in A), tuple(affine[b].endpoint(p) for p in B))
                flipped = endpoint_rigid != endpoint_chord
                affine_matches = endpoint_affine == endpoint_chord
                label = ("endpoint_state_flip" if flipped else "same_endpoint_state")+"__"+("affine_matches_snapshot" if affine_matches else "affine_endpoint_state_flip")
                discrepancies["all_m5a_chord_discrepancies"] += 1
                discrepancies[label] += 1
                if label not in examples:
                    examples[label] = {"case": case, "step": frame["step"], "pair": [a, b],
                        "endpoint_states": {"snapshot_chord": endpoint_chord, "rigid": endpoint_rigid, "affine_fit": endpoint_affine},
                        "frozen_first_results": {"rigid": pair["rigid"], "chord": pair["chord"]},
                        "delta_affine": [str(affine[x].delta) for x in (a, b)], "delta_rigid": [str(se2[x].delta) for x in (a, b)],
                        "A0": json_points(A), "A1": json_points(Aend), "B0": json_points(B), "B1": json_points(Bend)}
            if frame["step"] % 10 == 0 or frame["step"] == len(paired):
                write_json(progress, {"case": case, "complete": False, "processed_steps": frame["step"],
                                      "elapsed_seconds": time.perf_counter()-start_time})
        assert next(old, None) is None, "frozen replay frame count mismatch"
    assert counts["steps"] == rigid.FULL_STEPS[case]
    require_stable_inputs(paths, initial_inputs)
    result = {"case": case, "complete": True, "counts": dict(counts), "discrepancies": dict(discrepancies),
              "distributions": pack(values), "examples": examples,
              "input_hashes": initial_inputs,
              "full_rows_sha256": file_hash(rows_path), "seconds": time.perf_counter()-start_time}
    write_json(directory / "summary.json", result)
    write_json(progress, {"case": case, "complete": True, "processed_steps": len(paired)})
    return result, dict(values)


def run_directory(name):
    """Require one portable directory name and resolve containment before writes."""
    if (not isinstance(name, str) or not name or name in (".", "..")
            or name != name.strip() or name.endswith(".")
            or any(c in name for c in '/\\:\x00<>"|?*') or Path(name).name != name):
        raise argparse.ArgumentTypeError("run-name must be a single directory name")
    root = TMP.resolve()
    output = (root / name).resolve()
    if output.parent != root:
        raise argparse.ArgumentTypeError("resolved run directory must remain directly inside TMP")
    return output


def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", nargs="*", default=list(rigid.CASES), choices=rigid.CASES)
    parser.add_argument("--workers", type=int, default=4, choices=range(1, 5))
    parser.add_argument("--run-name", type=run_directory, default="affine_full_r1")
    return parser.parse_args(argv)


def main():
    args = parse_arguments()
    TMP.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(TMP)
    output = args.run_name
    output.mkdir(exist_ok=False)
    initial_code = code_hashes()
    initial_inputs = {case: input_hashes(input_paths(case)) for case in args.cases}
    start_time = time.perf_counter()
    write_json(output / "progress.json", {"complete": False, "cases": [], "source_hashes": initial_code})
    results, totals, counts, differences = {}, defaultdict(list), Counter(), Counter()
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(replay_case, case, output, initial_inputs[case]): case for case in args.cases}
        for future in as_completed(futures):
            result, values = future.result()
            results[result["case"]] = result
            counts.update(result["counts"])
            differences.update(result["discrepancies"])
            for key, data in values.items():
                totals[key].extend(data)
            write_json(output / "progress.json", {"complete": False, "cases": sorted(results), "counts": dict(counts)})
            print(result["case"], result["counts"]["steps"], "steps", result["seconds"], "s", flush=True)
    assert code_hashes() == initial_code, "code changed during run: discard and rerun"
    for case in args.cases:
        require_stable_inputs(input_paths(case), initial_inputs[case])
    full = args.cases == list(rigid.CASES)
    if full:
        assert counts["steps"] == 1810
        assert differences["all_m5a_chord_discrepancies"] == 937
    summary = {"schema": "eab.m5a2-affine-endpoint-diagnostic.v1", "complete": True, "full_1810_steps": full,
               "not_claimed": ["general affine first entrance", "positive residual first-cover certificate", "physical-path reconstruction", "causal path-only attribution"],
               "counts": dict(counts), "discrepancies": dict(differences), "distributions": pack(totals),
               "cases": results, "source_hashes": initial_code,
               "read_only_bdda_moments_sha256": file_hash(Path("D:/b-DDA/bdda2/geom/moments.hpp")),
               "seconds": time.perf_counter()-start_time}
    write_json(output / "summary.json", summary)
    write_json(output / "progress.json", {"complete": True, "cases": sorted(results), "counts": dict(counts)})
    if full:
        destination = EVIDENCE / "affine_full_summary.json"
        write_json(destination, summary)
        assert destination.stat().st_size < 1000000, "compact delivery exceeds one MB"
    print(json.dumps({"complete": True, "counts": dict(counts), "differences": dict(differences), "seconds": summary["seconds"]}), flush=True)


if __name__ == "__main__":
    main()
