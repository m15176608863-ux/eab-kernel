"""Self-contained DDA endpoint reconstruction, with rational transcendental bounds.

Input boundary: %.17g decimals are decoded to binary64 once, then frozen as
exact rational strings. No sibling code or executable is imported or run.
The reconstructed rational map uses Python's binary64 cos/sin, whose error
against mathematical cos/sin is certified by alternating-series intervals.
It is NOT assumed that an unidentified historical C++ CRT returns those bits.
Actual snapshot endpoint residuals are checked independently and exactly.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from fractions import Fraction as F
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
from frozen_evidence import data_path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M5b_evidence"
INPUTS = data_path(ROOT, EVIDENCE / "endpoint_inputs")
TMP = ROOT / "reports/codex/M5c_evidence/tmp"


def source_hashes():
    # midpoint_discrepancy has lazy imports: load the exact same dependencies
    # before the start snapshot, not after the closure has already been sealed.
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
    from eab.adapters.bdda2d_affine import DDAAffineMotion
    from eab.kernel2d.affine_motion import fit_affine
    from m5a_se2_replay import fit_rigid
    from m5c_source_binding import runtime_source_hashes
    return runtime_source_hashes(ROOT, __file__)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def binary64_decimal(text):
    """The explicit external numeric boundary, never used as a predicate."""
    value = float(text)
    if not math.isfinite(value) or (value == 0 and F(text) != 0):
        raise ValueError("non-finite or underflowed binary64 input")
    return F(value)


def exact_points(points):
    return tuple(tuple(F(v) for v in p) for p in points)


def area_centroid(points):
    """Signed polygon area centroid; rational, no tolerance or geometry helper.

    Gate: test_area_centroid_matches_independent_triangle_integrals.
    """
    points = exact_points(points)
    pairs = tuple(zip(points, points[1:]+points[:1]))
    crosses = tuple(x*v-u*y for (x, y), (u, v) in pairs)
    area2 = sum(crosses)
    if area2 == 0:
        raise ValueError("zero signed polygon area")
    return tuple(sum((p[k]+q[k])*v for (p, q), v in zip(pairs, crosses))/(3*area2)
                 for k in (0, 1))


def sin_cos_intervals(theta, terms=10):
    """Exact alternating Taylor enclosures for |theta|<=1, terms>=1.

    Terms decrease in absolute value on this domain. The exact value lies
    between the partial sum and that sum plus the first omitted term.
    Gate: test_trig_enclosures_match_independent_lagrange_oracle.
    """
    theta = F(theta)
    if abs(theta) > 1 or type(terms) is not int or terms < 1:
        raise ValueError("Taylor enclosure requires |theta|<=1 and terms>=1")
    answer = []
    for parity in (1, 0):
        term = theta if parity else F(1)
        total = F(0)
        for n in range(terms):
            total += term
            degree = 2*n+parity
            term *= -theta*theta/F((degree+1)*(degree+2))
        answer.append((min(total, total+term), max(total, total+term)))
    return tuple(answer)


def linear_interval(offset, terms):
    lower = upper = F(offset)
    for coefficient, (lo, hi) in terms:
        low, high = coefficient*lo, coefficient*hi
        lower += min(low, high)
        upper += max(low, high)
    return lower, upper


def dda_position_intervals(points, z, s=F(1)):
    """P3 value enclosures at one rational s, not a sampled path certificate."""
    points, z, s = exact_points(points), tuple(map(F, z)), F(s)
    if len(z) != 6 or not 0 <= s <= 1:
        raise ValueError("DDA needs six components and 0<=s<=1")
    cx, cy = area_centroid(points)
    dx, dy, theta, ex, ey, gamma = z
    sine, cosine = sin_cos_intervals(s*theta)
    result = []
    for px, py in points:
        x, y = px-cx, py-cy
        result.append((linear_interval(cx+s*dx+s*(ex*x+gamma*y/2), ((x, cosine), (-y, sine))),
                       linear_interval(cy+s*dy+s*(ey*y+gamma*x/2), ((y, cosine), (x, sine)))))
    return tuple(result)


def endpoint_map(points, z, cosine, sine):
    """Exact rational affine map M_DDA for explicitly supplied trig values.

    Gate: test_endpoint_map_matches_independent_displacement_oracle.
    """
    points, z = exact_points(points), tuple(map(F, z))
    if len(z) != 6:
        raise ValueError("DDA needs six components")
    c = area_centroid(points)
    dx, dy, _, ex, ey, gamma = z
    cosine, sine = F(cosine), F(sine)
    matrix = ((cosine+ex, -sine+gamma/2), (sine+gamma/2, cosine+ey))
    mapped = tuple(tuple(c[k]+(dx, dy)[k]+sum(matrix[k][j]*(p[j]-c[j]) for j in (0, 1))
                         for k in (0, 1)) for p in points)
    return c, matrix, mapped


def rounding_unit(points):
    """One block-frame ULP, not unit roundoff or coordinate*2^-52.

    U=ulp(max(abs(coordinate))) over both endpoints. All frozen inputs are
    finite binary64, so this is the spacing above that positive magnitude;
    at zero U=2^-1074. The same U normalizes both coordinate errors.
    """
    maximum = max(abs(v) for p in exact_points(points) for v in p)
    return F(math.ulp(float(maximum)))


def reconstruct(row):
    """Return the rational M_DDA and exact/bounded endpoint diagnostics."""
    start, end, z = exact_points(row["start"]), exact_points(row["end"]), tuple(map(F, row["z"]))
    if len(start) != len(end) or len(start) < 3:
        raise ValueError("endpoint topology mismatch")
    cosine, sine = F(math.cos(z[2])), F(math.sin(z[2]))
    center, matrix, predicted = endpoint_map(start, z, cosine, sine)
    delta = max(abs(p[k]-q[k]) for p, q in zip(predicted, end) for k in (0, 1))
    intervals = dda_position_intervals(start, z)
    ideal_delta = max(abs(bound-q[k]) for bounds, q in zip(intervals, end)
                      for k in (0, 1) for bound in bounds[k])
    sb, cb = sin_cos_intervals(z[2])
    trig_error = max(abs(v-t) for t, bounds in ((sine, sb), (cosine, cb)) for v in bounds)
    trig_radius = trig_error*max(abs(p[0]-center[0])+abs(p[1]-center[1]) for p in start)
    unit = rounding_unit(start+end)
    return {"center": center, "matrix": matrix, "translation": z[:2],
            "cosine": cosine, "sine": sine, "delta": delta,
            "ideal_delta_upper": ideal_delta, "trig_error_upper": trig_error,
            "trig_position_error_upper": trig_radius, "rounding_unit": unit,
            "binary_ratio": delta/unit, "ideal_ratio_upper": ideal_delta/unit}


def grouped_binary64_replay(row):
    """Secondary audit of source statement grouping, never a primary oracle.

    Uses the supplied original DDA ring order, not the CCW-normalized order.
    Exact equality to an observed endpoint is consistency evidence only:
    it does not uniquely identify historical internal centroid/trig bits.
    """
    start = tuple(tuple(float(F(v)) for v in p) for p in row["start"])
    end = exact_points(row["end"])
    z = tuple(float(F(v)) for v in row["z"])
    area = mx = my = 0.0
    for (x2, y2), (x3, y3) in zip(start, start[1:]+start[:1]):
        cross = x2*y3-x3*y2
        area += cross/2.0
        mx += cross*(x2+x3)/6.0
        my += cross*(y2+y3)/6.0
    cx, cy = mx/area, my/area
    u0, v0, r0, ex, ey, gamma = z
    cosine, sine = math.cos(r0), math.sin(r0)
    exact_matches = 0
    for (x, y), observed in zip(start, end):
        dx, dy = x-cx, y-cy
        predicted = (x+(u0+ex*dx+gamma*dy/2.0)+(dx*(cosine-1.0)-dy*sine),
                     y+(v0+ey*dy+gamma*dx/2.0)+(dy*(cosine-1.0)+dx*sine))
        exact_matches += sum(F(predicted[k]) == observed[k] for k in (0, 1))
    return exact_matches, 2*len(start)


def _pack_points(poly):
    return [[str(v) for v in p] for p in poly]


def freeze_inputs(destination=None):
    """Create once; cross-check raw z/geometry pairing against all snapshots."""
    destination = Path(destination) if destination is not None else EVIDENCE / "endpoint_inputs"
    if destination.exists():
        raise ValueError("input bundle exists: never overwrite frozen inputs")
    destination.mkdir(parents=True)
    audit_path = ROOT / "reports/codex/M4c_evidence/kinematics_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    manifest = {"schema": "eab.m5b-endpoint-inputs.v1", "complete": False,
                "pairing": "z(step=k,block=b): geom.step(k-1)->geom.step(k); snapshot k is start; final supplies last end",
                "numeric_boundary": "%.17g -> binary64 -> exact rational; original decimal strings are not exact coordinates",
                "audit_sha256": sha(audit_path), "cases": {}, "shards": []}
    write_json(destination / "manifest.json", manifest)
    for case_info in audit["cases"]:
        case = case_info["case"]
        paths, source_hashes = {}, {}
        for name in ("shadow.jsonl", "geom.csv", "out.csv"):
            original = case_info["files"][name]
            source = Path(original["copy"])
            if not source.exists():
                source = Path(original["source"])
            if sha(source) != original["sha256"]:
                raise ValueError("historical source hash mismatch")
            target = TMP / "endpoint_originals" / case / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.resolve() != target.resolve():
                shutil.copyfile(source, target)
            if sha(target) != original["sha256"]:
                raise ValueError("source copy changed")
            paths[name] = target
            source_hashes[name] = original["sha256"]
        raw = [json.loads(line, parse_float=str) for line in paths["shadow.jsonl"].read_text(encoding="utf-8").splitlines()]
        header, frames, ending = raw[0], raw[1:-1], raw[-1]
        n = len(frames)
        if ending != {"kind": "end", "completed_steps": n, "status": "ok"} or header["requested_steps"] != n:
            raise ValueError("incomplete snapshot")
        geometries = defaultdict(dict)
        with paths["geom.csv"].open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                kind = row["kind"]
                if kind.startswith("step") or kind in ("initial", "final"):
                    vertex = int(row["idx"])
                    if vertex in geometries[kind]:
                        raise ValueError("duplicate geometry vertex")
                    geometries[kind][vertex] = tuple(binary64_decimal(row[k]) for k in ("x", "y"))
        if set(geometries) != {"initial", "final"} | {f"step{k}" for k in range(n+1)}:
            raise ValueError("missing geometry interval")
        if geometries["initial"] != geometries["step0"] or geometries["final"] != geometries[f"step{n}"]:
            raise ValueError("terminal or initial pairing mismatch")
        displacements = {}
        with paths["out.csv"].open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                key = int(row["step"]), int(row["block"])
                if key in displacements:
                    raise ValueError("duplicate displacement key")
                displacements[key] = tuple(binary64_decimal(row[f"z{k}"]) for k in range(1, 7))
        packed, count, signature = [], 0, None
        for expected_step, frame in enumerate(frames, 1):
            if frame["step"] != expected_step:
                raise ValueError("nonconsecutive snapshots")
            identity = tuple((b, v) for b, v, _, _ in frame["geometry"])
            if signature is None:
                signature = identity
            if identity != signature:
                raise ValueError("topology changed")
            grouped = defaultdict(list)
            for b, vertex, x, y in frame["geometry"]:
                point = binary64_decimal(x), binary64_decimal(y)
                if point != geometries[f"step{expected_step-1}"][vertex]:
                    raise ValueError("snapshot/geometry off-by-one mismatch")
                grouped[b].append((vertex, point))
            for b, vertices in sorted(grouped.items()):
                # DDA's two wraparound aliases are exact supplied coordinates.
                if [p for _, p in vertices[-2:]] != [p for _, p in vertices[:2]]:
                    raise ValueError("DDA wraparound alias mismatch")
                vertices = vertices[:-2]
                ids = [v for v, _ in vertices]
                start = tuple(p for _, p in vertices)
                end = tuple(geometries[f"step{expected_step}"][v] for v in ids)
                z = displacements.pop((expected_step, b))
                packed.append({"case": case, "step": expected_step, "block": b, "vertex_ids": ids,
                               "start": _pack_points(start), "end": _pack_points(end), "z": list(map(str, z))})
                count += 1
            if expected_step % 25 == 0 or expected_step == n:
                name = f"{case}_{expected_step:04d}.jsonl.gz"
                data = "".join(json.dumps(row, separators=(",", ":"))+"\n" for row in packed).encode("utf-8")
                compressed = gzip.compress(data, mtime=0)
                if len(compressed) > 1_000_000:
                    raise ValueError("input shard exceeds 1 MB")
                (destination / name).write_bytes(compressed)
                manifest["shards"].append({"file": name, "sha256": sha(destination / name), "bytes": len(compressed), "rows": len(packed)})
                packed = []
                write_json(destination / "manifest.json", manifest)
        if displacements:
            raise ValueError("unpaired displacement rows")
        if {name: sha(path) for name, path in paths.items()} != source_hashes:
            raise ValueError("source changed during freeze; discard bundle")
        manifest["cases"][case] = {"steps": n, "block_frames": count, "source_hashes": source_hashes}
        print("frozen", case, count, flush=True)
    manifest["complete"] = True
    manifest["block_frames"] = sum(value["block_frames"] for value in manifest["cases"].values())
    write_json(destination / "manifest.json", manifest)
    return manifest


def iter_inputs(directory=INPUTS, case=None):
    """Yield independently hash-checked dictionaries with rational-string data."""
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if not manifest["complete"]:
        raise ValueError("incomplete input bundle")
    count = 0
    for part in manifest["shards"]:
        if case is not None and not part["file"].startswith(case+"_"):
            continue
        path = directory / part["file"]
        if sha(path) != part["sha256"]:
            raise ValueError("frozen input hash mismatch")
        rows = [json.loads(line) for line in gzip.decompress(path.read_bytes()).decode("utf-8").splitlines()]
        if len(rows) != part["rows"]:
            raise ValueError("frozen input count mismatch")
        for row in rows:
            if case is None or row["case"] == case:
                count += 1
                yield row
    expected = manifest["block_frames"] if case is None else manifest["cases"][case]["block_frames"]
    if count != expected:
        raise ValueError("frozen input total mismatch")


def midpoint_discrepancy(row):
    """Old M5a2 fit family vs mathematical DDA P3; no path supremum claim."""
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
    from eab.adapters.bdda2d_affine import DDAAffineMotion
    from eab.kernel2d.affine_motion import fit_affine
    from m5a_se2_replay import fit_rigid
    start, end = exact_points(row["start"]), exact_points(row["end"])
    fit, rigid = fit_affine(start, end), fit_rigid(start, end)
    model = DDAAffineMotion(matrix=fit.matrix, u1=rigid.motion.u1, translation=fit.translation, center=fit.center)
    truth = dda_position_intervals(start, row["z"], F(1, 2))
    bounds = []
    for point, intervals in zip(start, truth):
        old = model.at(point, F(1, 2))
        bounds.append(tuple(max(abs(v-old[k]) for v in intervals[k]) for k in (0, 1)))
    return max(max(p) for p in bounds), max(x*x+y*y for x, y in bounds)


def run(run_name, directory=INPUTS):
    if (not isinstance(run_name, str) or not run_name or run_name in (".", "..")
            or any(c in run_name for c in '/\\:\x00<>"|?*') or run_name != run_name.strip()
            or run_name.endswith(".")):
        raise ValueError("run-name must be a single portable directory name")
    destination = (TMP / run_name).resolve()
    if destination.parent != TMP.resolve():
        raise ValueError("run directory must remain in M5b tmp")
    if destination.exists():
        raise ValueError("run directory exists; interrupted evidence is not resumable")
    destination.mkdir(parents=True)
    started = time.perf_counter()
    manifest_path = Path(directory) / "manifest.json"
    from m5c_source_binding import assert_run_sources_unchanged
    initial = source_hashes()
    manifest_hash = sha(manifest_path)
    summary = {"schema": "eab.m5b-endpoint-reconstruction.v1", "complete": False,
               "source_hashes": initial, "input_hashes": {"manifest": manifest_hash},
               "source_binding": "runtime-loaded-repository-closure-start-and-end.v1",
               "cases": {}, "block_frames": 0,
               "grouped_binary64_coordinates": 0, "grouped_binary64_exact_matches": 0,
               "unit_definition": "U=ulp(max|coordinate|) over block-frame start and end; one spacing, not half spacing",
               "trig_contract": "Python binary64 candidates bounded against mathematical trig by exact rational alternating Taylor; historical CRT bit identity NOT asserted"}
    write_json(destination / "progress.json", summary)
    global_max = {}
    examples = {}
    with gzip.open(destination / "endpoint_rows.jsonl.gz", "wt", encoding="utf-8", newline="\n") as stream:
        for row in iter_inputs(directory):
            result = reconstruct(row)
            matched, coordinates = grouped_binary64_replay(row)
            summary["grouped_binary64_coordinates"] += coordinates
            summary["grouped_binary64_exact_matches"] += matched
            midpoint, midpoint_square = midpoint_discrepancy(row)
            result.update(midpoint_linf_upper=midpoint, midpoint_l2_square_upper=midpoint_square)
            case = row["case"]
            statistics = summary["cases"].setdefault(case, {"block_frames": 0, "maxima_exact": {}})
            statistics["block_frames"] += 1
            summary["block_frames"] += 1
            fields = ("delta", "ideal_delta_upper", "binary_ratio", "ideal_ratio_upper", "trig_error_upper",
                      "trig_position_error_upper", "midpoint_linf_upper", "midpoint_l2_square_upper")
            for name in fields:
                value = result[name]
                if value > F(statistics["maxima_exact"].get(name, "-1")):
                    statistics["maxima_exact"][name] = str(value)
                if value > global_max.get(name, F(-1)):
                    global_max[name] = value
                    examples[name] = {"input": row, "value_exact": str(value)}
            record = {"case": case, "step": row["step"], "block": row["block"],
                      **{name: str(result[name]) for name in fields},
                      "center": list(map(str, result["center"])), "matrix": _pack_points(result["matrix"]),
                      "translation": list(map(str, result["translation"])),
                      "cosine": str(result["cosine"]), "sine": str(result["sine"])}
            stream.write(json.dumps(record, separators=(",", ":"))+"\n")
            if summary["block_frames"] % 100 == 0:
                summary["elapsed_seconds"] = time.perf_counter()-started
                write_json(destination / "progress.json", summary)
                print("endpoint", summary["block_frames"], case, row["step"], flush=True)
    final = source_hashes()
    assert_run_sources_unchanged(ROOT, initial, final)
    if sha(manifest_path) != manifest_hash:
        raise ValueError("bound input manifest changed; discard run and restart")
    # Re-read every frozen shard after the computation before publication.
    if sum(1 for _ in iter_inputs(directory)) != summary["block_frames"]:
        raise ValueError("input changed during endpoint replay")
    summary.update(complete=True, source_hashes_end=final, seconds=time.perf_counter()-started,
                   maxima_exact={key: str(value) for key, value in global_max.items()},
                   maxima_display={key: float(value) for key, value in global_max.items()},
                   examples=examples, rows_sha256=sha(destination / "endpoint_rows.jsonl.gz"),
                   run_name=run_name)
    for statistics in summary["cases"].values():
        statistics["maxima_display"] = {key: float(F(value)) for key, value in statistics["maxima_exact"].items()}
    write_json(destination / "summary.json", summary)
    write_json(destination / "progress.json", {"complete": True, "block_frames": summary["block_frames"]})
    write_json(EVIDENCE / "endpoint_summary.json", summary)
    write_json(EVIDENCE / "endpoint_minimal_examples.json", {
        "schema": "eab.m5b-endpoint-minimal.v1", "summary_sha256": sha(EVIDENCE / "endpoint_summary.json"),
        "binary_rounding_maximum": examples["binary_ratio"],
        "midpoint_full_corpus_maximum": examples["midpoint_linf_upper"],
        "historical_midpoint_value_status": "2.8e-6 retained as external acceptance history; norm/model/data-scope equivalence unresolved"})
    print(json.dumps({"complete": True, "block_frames": summary["block_frames"], "seconds": summary["seconds"],
                      "maxima_display": summary["maxima_display"]}), flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-inputs", action="store_true")
    parser.add_argument("--run-name")
    args = parser.parse_args()
    TMP.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(TMP)
    if args.freeze_inputs:
        freeze_inputs()
    if args.run_name:
        run(args.run_name)
    if not args.freeze_inputs and not args.run_name:
        parser.error("request --freeze-inputs and/or --run-name")


if __name__ == "__main__":
    main()
