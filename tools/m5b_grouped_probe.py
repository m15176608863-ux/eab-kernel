"""Secondary binary64-value replay with the C++ lo..hi summation start.

The endpoint input ring starts at pad_lo=lo-1. Cyclically rotating by one has
no effect on exact centroid/affine results, but changes binary64 summation.
Keep this correction separate from the already-running bound full-history
replay; do not silently rewrite its earlier diagnostic count.
Frozen Fraction inputs merge signed zeros; equality does not prove zero-sign
bit equality. This audit compares exact numerical binary64 values only.
"""
from collections import Counter
import argparse
import csv
import json
from pathlib import Path
import time

import m5b_endpoint_replay as endpoint

EVIDENCE = endpoint.EVIDENCE
RANGES = EVIDENCE / "endpoint_physical_ranges.json"


def freeze_ranges():
    if RANGES.exists():
        raise ValueError("physical ranges already frozen")
    inputs = json.loads((endpoint.INPUTS / "manifest.json").read_text(encoding="utf-8"))
    result = {"schema": "eab.m5b-physical-ranges.v1", "cases": {}}
    for case, info in inputs["cases"].items():
        path = endpoint.TMP / "endpoint_originals" / case / "geom.csv"
        before = endpoint.sha(path)
        if before != info["source_hashes"]["geom.csv"]:
            raise ValueError("geometry source mismatch")
        with path.open(encoding="utf-8", newline="") as stream:
            ranges = {row["idx"]: [int(row["x"]), int(row["y"])]
                      for row in csv.DictReader(stream) if row["kind"] == "range"}
        if endpoint.sha(path) != before:
            raise ValueError("geometry source changed")
        result["cases"][case] = {"source_sha256": before, "ranges": ranges}
    endpoint.write_json(RANGES, result)


def physical_order(row, lo, hi):
    if row["vertex_ids"] != list(range(lo-1, hi)):
        raise ValueError("input ring does not match captured physical lo..hi")
    return {**row, "start": row["start"][1:]+row["start"][:1],
            "end": row["end"][1:]+row["end"][:1]}


def run(name):
    if not name or Path(name).name != name or name in (".", ".."):
        raise ValueError("fresh single run directory required")
    output = endpoint.TMP / name
    output.mkdir(exist_ok=False)
    ranges = json.loads(RANGES.read_text(encoding="utf-8"))
    hashes = {"tool": endpoint.sha(__file__), "endpoint_tool": endpoint.sha(endpoint.__file__),
              "physical_ranges": endpoint.sha(RANGES), "manifest": endpoint.sha(endpoint.INPUTS / "manifest.json")}
    counts, per_case, mismatch_example = Counter(), {}, None
    started = time.perf_counter()
    endpoint.write_json(output / "progress.json", {"complete": False, "processed": 0})
    for row in endpoint.iter_inputs():
        lo, hi = ranges["cases"][row["case"]]["ranges"][str(row["block"])]
        changed = physical_order(row, lo, hi)
        # Exact cyclic invariance is independently checked for every block frame.
        if endpoint.area_centroid(row["start"]) != endpoint.area_centroid(changed["start"]):
            raise AssertionError("cyclic exact centroid invariance")
        matches, coordinates = endpoint.grouped_binary64_replay(changed)
        unshifted, _ = endpoint.grouped_binary64_replay(row)
        if unshifted != coordinates and mismatch_example is None:
            mismatch_example = {"input": row, "physical_range": [lo, hi],
                                "unshifted_matches": unshifted, "shifted_matches": matches, "coordinates": coordinates}
        cell = per_case.setdefault(row["case"], Counter())
        for target in (counts, cell):
            target.update(block_frames=1, coordinates=coordinates, physical_order_matches=matches,
                          old_pad_order_matches=unshifted)
        if counts["block_frames"] % 500 == 0:
            endpoint.write_json(output / "progress.json", {"complete": False, "processed": counts["block_frames"]})
    final = {"tool": endpoint.sha(__file__), "endpoint_tool": endpoint.sha(endpoint.__file__),
             "physical_ranges": endpoint.sha(RANGES), "manifest": endpoint.sha(endpoint.INPUTS / "manifest.json")}
    if final != hashes:
        raise AssertionError("grouped replay source changed")
    if counts["coordinates"] != counts["physical_order_matches"]:
        raise AssertionError("physical-order binary64 replay disagrees with observed coordinates")
    result = {"schema": "eab.m5b-grouped-replay.v1", "complete": True, "run": name,
              "counts": dict(counts), "cases": {k: dict(v) for k, v in per_case.items()},
              "source_hashes": hashes, "seconds": time.perf_counter()-started,
              "example": mismatch_example,
              "interpretation": "all observed binary64 coordinate values consistent with Python trig candidates and C++ statement grouping; signed zeros merged by Fraction, not bitwise equality or unique recovery of historical internal bits"}
    endpoint.write_json(output / "summary.json", result)
    endpoint.write_json(output / "progress.json", {"complete": True, "processed": counts["block_frames"]})
    endpoint.write_json(EVIDENCE / "endpoint_grouped_summary.json", result)
    print(json.dumps({"complete": True, **dict(counts), "seconds": result["seconds"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-ranges", action="store_true")
    parser.add_argument("--name")
    args = parser.parse_args()
    if args.freeze_ranges:
        freeze_ranges()
    if args.name:
        run(args.name)
