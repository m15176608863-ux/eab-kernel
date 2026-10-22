"""Report-only C1 20x40 geometry measurement. No performance pass threshold.

The aligned 4x5 assembly has shared wavy interfaces, forty vertices per simple
nonconvex ring, and binary64-exact dyadic coordinates. All 190 closed AABB pairs
are considered. Default measures the actual CONTACT pairs (edge and diagonal
VV); --all-pairs is a separate forced 190-pair stress denominator. No C3 lock,
mechanics, multi-body mobility, or speedup over unlike archived workloads is claimed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction as F
import hashlib
from itertools import combinations
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eab.kernel2d.exact import polygons_overlap_exact  # noqa: E402
from eab.kernel2d.global_entrance import GlobalEntrance2, _ring  # noqa: E402
from eab2_c1_cases import bits  # noqa: E402
from eab2_diff_c1 import Dll, write_json  # noqa: E402


def synthetic_assembly():
    stops = [F(0), *(F(k, 16) for k in range(1, 9)), F(3, 4), F(1)]
    def wiggle(k, parity):
        return F(0) if k in (0, 10) else F(1 if (k+parity) % 2 else -1, 64)
    horizontal = {(i, j): tuple((F(i)+t, F(j)+wiggle(k, i+j)) for k, t in enumerate(stops))
                  for i in range(5) for j in range(5)}
    vertical = {(i, j): tuple((F(i)+wiggle(k, i-j), F(j)+t) for k, t in enumerate(stops))
                for i in range(6) for j in range(4)}
    bodies = []
    for j in range(4):
        for i in range(5):
            ring = (horizontal[i, j][:-1] + vertical[i+1, j][:-1]
                    + tuple(reversed(horizontal[i, j+1]))[:-1]
                    + tuple(reversed(vertical[i, j]))[:-1])
            assert len(ring) == 40 and _ring(ring) == ring
            result = tuple(tuple(float(v) for v in p) for p in ring)
            assert all(F(v) == q for p, e in zip(result, ring) for v, q in zip(p, e))
            bodies.append(result)
    return bodies


def aabb(poly):
    return min(p[0] for p in poly), min(p[1] for p in poly), max(p[0] for p in poly), max(p[1] for p in poly)


def boxes_meet(a, b):
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--all-pairs", action="store_true")
    parser.add_argument("--limit", type=int, help="timing estimate only; does not claim full measurement")
    parser.add_argument("--formal-diff", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("use a new output name")
    bodies = synthetic_assembly()
    boxes = list(map(aabb, bodies))
    broad = []
    for a, b in combinations(range(len(bodies)), 2):
        possible = boxes_meet(boxes[a], boxes[b])
        state = polygons_overlap_exact(bodies[a], bodies[b]) if possible else -1
        broad.append({"a": a, "b": b, "aabb_candidate": possible, "body_state": state})
    selected = broad if args.all_pairs else [r for r in broad if r["body_state"] == 0]
    intended_count = len(selected)
    if args.limit is not None:
        selected = selected[:args.limit]
    report = {"schema": "eab2.c1.measure.v1", "report_only": True,
              "performance_threshold": None, "complete": False, "status": "RUNNING",
              "mode": "forced_190_pairs" if args.all_pairs else "all_actual_contacts_including_VV",
              "body_count": 20, "vertices_per_body": 40, "grid": "4 rows x 5 columns; shared dyadic zigzag interfaces",
              "broad_phase": broad, "body_states": Counter(r["body_state"] for r in broad),
              "edge_adjacent_pairs": sum(abs(r["a"] % 5-r["b"] % 5)+abs(r["a"] // 5-r["b"] // 5) == 1 and r["body_state"] == 0 for r in broad),
              "diagonal_VV_pairs": sum(abs(r["a"] % 5-r["b"] % 5) == abs(r["a"] // 5-r["b"] // 5) == 1 and r["body_state"] == 0 for r in broad),
              "intended_pairs": intended_count, "selected_pairs": len(selected), "measurements": [],
              "notes": ["Single cold execution per pair, not affinity-isolated; no throughput/performance gate.",
                        "C++ timings include ctypes/ABI; exact export also includes serialization and Python JSON parsing.",
                        "Python timings include GlobalEntrance2 construction and compact subdivision, not slow boundary.",
                        "max_integer_bits is stored exact coordinate numerator/denominator size, not temporary arithmetic peak.",
                        "intersection_points includes segment endpoints and collinear overlaps; see implementation scope.",
                        "Filter/exact fallback statistics are N/A: this build uses only exact arithmetic.",
                        "No C3 Shi lock/mobility/limit classification is performed by this C1 measurement."]}
    if args.formal_diff:
        formal = json.loads(args.formal_diff.read_text(encoding="utf-8"))
        report["formal_measurement_source"] = {"path": str(args.formal_diff), "sha256": hashlib.sha256(args.formal_diff.read_bytes()).hexdigest(),
            "coverage": formal["coverage"], "rows": [r for r in formal["cases"] if r["name"].startswith("formal/")],
            "timing_scope": "Same-run Python exact export versus C++ cold construction+export; archived T1a assembly LP times are a different workload."}
    dll = Dll(args.dll)
    report["dll_sha256"] = hashlib.sha256(args.dll.read_bytes()).hexdigest()
    report["build_identity"] = dll.identity
    total_start = time.perf_counter()
    try:
        for index, entry in enumerate(selected):
            print(f"C1_MEASURE_BEGIN {index+1}/{len(selected)} pair={entry['a']},{entry['b']}", flush=True)
            row = dict(entry)
            first = second = entrance = None
            try:
                started = time.perf_counter()
                first, second = dll.body(bodies[entry["a"]]), dll.body(bodies[entry["b"]])
                entrance = dll.entrance(first, second)
                row["cpp_cold_body_E_seconds"] = time.perf_counter()-started
                started = time.perf_counter()
                local = dll.export(entrance, local=True)
                row["cpp_local_seconds"] = time.perf_counter()-started
                assert not local["global_subdivision_materialized"]
                started = time.perf_counter()
                export = dll.export(entrance)
                row["cpp_global_export_seconds"] = time.perf_counter()-started
                row.update(raw_segments=len(export["raw_segments"]), cells=len(export["cells"]),
                           contact_segments=len(export["contact_segments"]), contact_points=len(export["contact_points"]),
                           skeleton={k: len(export["subdivision"][k]) for k in ("vertices", "edges", "faces")},
                           statistics=export["statistics"], cpp_status="OK")
            except Exception as error:
                row.update(cpp_status="ERROR", cpp_error=repr(error))
            finally:
                if entrance is not None:
                    dll.check(dll.entrance2_destroy(dll.context, entrance), "entrance2_destroy")
                for handle in (second, first):
                    if handle is not None:
                        dll.check(dll.body2_destroy(dll.context, handle), "body2_destroy")
            started = time.perf_counter()
            model = GlobalEntrance2(bodies[entry["a"]], bodies[entry["b"]], merge_convex=True, compact_subdivision=True)
            row["python_cold_E_seconds"] = time.perf_counter()-started
            started = time.perf_counter()
            subd = model.subdivision
            row["python_compact_subdivision_seconds"] = time.perf_counter()-started
            row["python_skeleton"] = {"vertices": len(subd.vertices), "edges": len(subd.edges), "faces": len(subd.faces)}
            row["python_cells"] = len(model.cells)
            report["measurements"].append(row)
            write_json(args.output, report)
            print(f"C1_MEASURE_END {index+1}/{len(selected)} cpp={row.get('cpp_global_export_seconds')} python={row['python_compact_subdivision_seconds']:.3f} status={row['cpp_status']}", flush=True)
    finally:
        dll.close()
        report["seconds"] = time.perf_counter()-total_start
        report["complete"] = len(report["measurements"]) == intended_count
        report["status"] = "MEASURED" if report["complete"] else "PARTIAL_MEASUREMENT"
        write_json(args.output, report)
    print(f"EAB2_C1_MEASURE selected={len(selected)} measured={len(report['measurements'])} intended={intended_count} status={report['status']} report_only=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
