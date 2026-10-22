"""C1 DLL exact-set differential runner, intentionally outside pytest.

Both exports are normalized by eab2_c1_exact; expectations never use the DLL.
Missing DLL paths/capabilities and any unexecuted selected case are failures.
Run: python tools/eab2_diff_c1.py --dll ABSOLUTE_DLL --output REPORT.json
"""
from __future__ import annotations

import argparse
from collections import Counter
import ctypes as C
import copy
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eab2_diff import AbiInfo, Context, Options, Text  # noqa: E402
from eab2_c1_cases import bits, corpus, make_case  # noqa: E402
from eab2_c1_exact import (GlobalEntrance2, canonical, compare_cover_rows, compare_exports,
                          layer_samples, point, ptext, python_export, qtext)  # noqa: E402
from eab2_c1_local import verify_local  # noqa: E402


class PointBits(C.Structure):
    _fields_ = [("x_bits", C.c_uint64), ("y_bits", C.c_uint64)]


class BodyInput(C.Structure):
    _fields_ = [("struct_size", C.c_uint32), ("abi_version", C.c_uint32),
                ("vertex_count", C.c_uint64), ("vertex_stride", C.c_uint64),
                ("vertices", C.POINTER(PointBits)), ("flags", C.c_uint32), ("reserved", C.c_uint32)]


class QueryInput(C.Structure):
    _fields_ = [("struct_size", C.c_uint32), ("abi_version", C.c_uint32),
                ("point_count", C.c_uint64), ("point_stride", C.c_uint64),
                ("points", C.POINTER(PointBits))]


class QueryItem(C.Structure):
    _fields_ = [("call_status", C.c_uint32), ("mathematical_status", C.c_uint32),
                ("body_state", C.c_uint32), ("topology_state", C.c_uint32)]


class QueryOutput(C.Structure):
    _fields_ = [("struct_size", C.c_uint32), ("abi_version", C.c_uint32),
                ("item_capacity", C.c_uint64), ("item_stride", C.c_uint64),
                ("item_count", C.c_uint64), ("items", C.POINTER(QueryItem))]


class ExactResult(C.Structure):
    _fields_ = [("struct_size", C.c_uint32), ("abi_version", C.c_uint32),
                ("call_status", C.c_uint32), ("mathematical_status", C.c_uint32),
                ("result", Context), ("data", C.c_void_p), ("byte_count", C.c_uint64)]


class C1AbiInfo(C.Structure):
    _fields_ = [(name, C.c_uint32) for name in (
        "struct_size", "abi_version", "body2_input_size", "entrance2_options_size",
        "query2_input_size", "query2_item_size", "query2_output_size", "exact_result_size",
        "point2_bits_size", "reserved")]


class PointExact(C.Structure):
    _fields_ = [("x", Text), ("y", Text)]


class QueryExactInput(C.Structure):
    _fields_ = [("struct_size", C.c_uint32), ("abi_version", C.c_uint32),
                ("point_count", C.c_uint64), ("point_stride", C.c_uint64),
                ("points", C.POINTER(PointExact))]


class CoversInput(C.Structure):
    _fields_ = [("struct_size", C.c_uint32), ("abi_version", C.c_uint32),
                ("require_in_segment", C.c_uint32), ("reserved", C.c_uint32),
                ("window", Text), ("tol", Text), ("cone_tol", Text), ("seg_tol", Text)]


def initialized(cls):
    value = cls()
    value.struct_size, value.abi_version = C.sizeof(cls), 1
    return value


class Dll:
    def __init__(self, path):
        if not path.is_absolute() or not path.is_file():
            raise ValueError("--dll must be an existing absolute DLL path")
        self.path = path
        self.lib = C.CDLL(str(path))
        signatures = {
            "get_abi_info": [C.POINTER(AbiInfo)],
            "get_c1_abi_info": [C.POINTER(C1AbiInfo)],
            "context_create": [C.POINTER(Options), C.POINTER(Context)],
            "context_destroy": [Context],
            "body2_create": [Context, C.POINTER(BodyInput), C.POINTER(Context)],
            "body2_destroy": [Context, Context],
            "entrance2_create": [Context, Context, Context, C.POINTER(Options), C.POINTER(Context)],
            "entrance2_destroy": [Context, Context],
            "query2_batch": [Context, Context, C.POINTER(QueryInput), C.POINTER(QueryOutput)],
            "query2_exact_batch": [Context, Context, C.POINTER(QueryExactInput), C.POINTER(QueryOutput)],
            "result_export_exact": [Context, Context, C.POINTER(ExactResult)],
            "local_origin2_exact": [Context, Context, C.POINTER(ExactResult)],
            "covers2_exact": [Context, Context, C.POINTER(CoversInput), C.POINTER(ExactResult)],
            "result_destroy": [Context, Context],
        }
        for name, args in signatures.items():
            function = getattr(self.lib, "eab2_"+name)
            function.argtypes, function.restype = args, C.c_uint32
            setattr(self, name, function)
        info = initialized(AbiInfo)
        info.requested_capabilities = 1 | 4 | 8 | 16 | 32 | 128
        self.check(self.get_abi_info(C.byref(info)), "get_abi_info")
        if info.unsupported_capabilities or info.supported_capabilities & info.requested_capabilities != info.requested_capabilities:
            raise AssertionError("DLL does not advertise required C1 capabilities")
        self.identity = bytes(info.build_identity).decode("ascii")
        c1 = initialized(C1AbiInfo)
        self.check(self.get_c1_abi_info(C.byref(c1)), "get_c1_abi_info")
        for name, cls in (("body2_input", BodyInput), ("entrance2_options", Options),
                          ("query2_input", QueryInput), ("query2_item", QueryItem),
                          ("query2_output", QueryOutput), ("exact_result", ExactResult),
                          ("point2_bits", PointBits)):
            if getattr(c1, name+"_size") != C.sizeof(cls):
                raise AssertionError("C1 ABI size mismatch: "+name)
        self.context = Context()
        options = initialized(Options)
        self.check(self.context_create(C.byref(options), C.byref(self.context)), "context_create")

    @staticmethod
    def check(status, name):
        if status:
            raise AssertionError(f"{name}: call_status={status}")

    def close(self):
        self.check(self.context_destroy(self.context), "context_destroy")

    def body(self, ring):
        array = (PointBits*len(ring))(*(PointBits(*(int(bits(x), 16) for x in p)) for p in ring))
        request = initialized(BodyInput)
        request.vertex_count, request.vertex_stride, request.vertices = len(ring), C.sizeof(PointBits), array
        handle = Context()
        self.check(self.body2_create(self.context, C.byref(request), C.byref(handle)), "body2_create")
        return handle

    def entrance(self, a, b, flags=0):
        options = initialized(Options)
        options.flags = flags
        handle = Context()
        self.check(self.entrance2_create(self.context, a, b, C.byref(options), C.byref(handle)), "entrance2_create")
        return handle

    def export(self, handle, local=False):
        result = initialized(ExactResult)
        function = self.local_origin2_exact if local else self.result_export_exact
        self.check(function(self.context, handle, C.byref(result)), "local_origin2_exact" if local else "result_export_exact")
        try:
            self.check(result.call_status, "exact_result.call_status")
            if result.mathematical_status != 1 or not result.data:
                raise AssertionError("exact export missing mathematical VALUE")
            return json.loads(C.string_at(result.data, result.byte_count))
        finally:
            self.check(self.result_destroy(self.context, result.result), "result_destroy")

    def query(self, handle, samples, exact=True):
        if exact:
            keepalive = [tuple(qtext(x).encode("ascii") for x in p) for p in samples]
            array = (PointExact*len(samples))(*(PointExact(*(Text(x, len(x)) for x in p)) for p in keepalive))
            request, function, size = initialized(QueryExactInput), self.query2_exact_batch, C.sizeof(PointExact)
        else:
            array = (PointBits*len(samples))(*(PointBits(*(int(bits(float(x)), 16) for x in p)) for p in samples))
            request, function, size = initialized(QueryInput), self.query2_batch, C.sizeof(PointBits)
        request.point_count, request.point_stride, request.points = len(samples), size, array
        values = (QueryItem*len(samples))()
        output = initialized(QueryOutput)
        output.item_capacity, output.item_stride, output.items = len(samples), C.sizeof(QueryItem), values
        self.check(function(self.context, handle, C.byref(request), C.byref(output)), "query2_exact_batch" if exact else "query2_batch")
        if output.item_count != len(samples):
            raise AssertionError("query count differs")
        states = []
        for row in values:
            self.check(row.call_status, "query item")
            if row.mathematical_status != 1:
                raise AssertionError("query mathematical_status is not VALUE")
            states.append((row.body_state-1, row.topology_state-1))
        return states

    def covers(self, handle, *, window=F(0), tol=F(0), cone_tol=None, seg_tol=None, require_in_segment=True):
        request = initialized(CoversInput)
        request.require_in_segment = require_in_segment
        keepalive = []
        for name, value in (("window", window), ("tol", tol), ("cone_tol", cone_tol), ("seg_tol", seg_tol)):
            if value is None or value == math.inf:
                setattr(request, name, Text(None, 0))
            else:
                encoded = qtext(value).encode("ascii")
                keepalive.append(encoded)
                setattr(request, name, Text(encoded, len(encoded)))
        result = initialized(ExactResult)
        self.check(self.covers2_exact(self.context, handle, C.byref(request), C.byref(result)), "covers2_exact")
        try:
            self.check(result.call_status, "covers.call_status")
            if result.mathematical_status != 1:
                raise AssertionError("covers mathematical_status is not VALUE")
            return json.loads(C.string_at(result.data, result.byte_count))
        finally:
            self.check(self.result_destroy(self.context, result.result), "covers.result_destroy")


def run_case(dll, case, flags=0, query_first=True):
    started = time.perf_counter()
    model = GlobalEntrance2(case.a, case.b, merge_convex=True, compact_subdivision=True)
    expected = python_export(model, include_boundary=not case.name.startswith("formal/"))
    python_seconds = time.perf_counter()-started
    a = b = entrance = actual = None
    try:
        started = time.perf_counter()
        a, b = dll.body(case.a), dll.body(case.b)
        entrance = dll.entrance(a, b, flags)
        build_seconds = time.perf_counter()-started
        zero = [(F(0), F(0))]
        zero_truth = [(model.membership(zero[0]), model.topology(zero[0]))]
        if query_first and dll.query(entrance, zero, exact=False) != zero_truth:
            raise AssertionError("binary64 origin query disagrees before export")
        local = dll.export(entrance, local=True)
        if local["global_subdivision_materialized"]:
            raise AssertionError("local origin query forced global subdivision")
        local_statistics = verify_local(local, case.a, case.b)
        started = time.perf_counter()
        actual = dll.export(entrance)
        export_seconds = time.perf_counter()-started
        for key, original, normalized in (("a", case.a, model.A), ("b", case.b, model.B)):
            body = actual[key]
            if tuple(map(point, body["vertices"])) != normalized:
                raise AssertionError("normalized ring mismatch: "+key)
            wanted_vertices = [next(i for i, p in enumerate(original) if point(p) == q) for q in normalized]
            wanted_edges = []
            for i, p in enumerate(normalized):
                q = normalized[(i+1) % len(normalized)]
                wanted_edges.append(next(j for j in range(len(original))
                                         if {point(original[j]), point(original[(j+1) % len(original)])} == {p, q}))
            if body["original_vertex_ids"] != wanted_vertices or body["original_edge_ids"] != wanted_edges:
                raise AssertionError("original vertex/edge mapping mismatch: "+key)
            if body["input_bits"] != [[bits(x) for x in p] for p in original]:
                raise AssertionError("input binary64 bits provenance mismatch: "+key)
        result = compare_exports(expected, actual, model)
        if case.name.startswith("covers_e3/"):
            windows = [{"window": F(1)}, {"window": math.inf},
                       {"window": F(1), "cone_tol": F(1, 8), "seg_tol": F(1, 512)},
                       {"window": F(1, 4), "tol": F(1, 16), "require_in_segment": False}]
            result["explicit_cover_window_checks"] = [
                {"options": {k: str(v) for k, v in options.items()},
                 "covers": compare_cover_rows(dll.covers(entrance, **options), model.A, model.B, **options)}
                for options in windows]
        samples = list(layer_samples(expected))
        got = dll.query(entrance, [p for _, p, _ in samples])
        for (kind, p, state), answer in zip(samples, got):
            if answer != state:
                raise AssertionError(f"reverse Python {kind} probe mismatch {p}: {answer} != {state}")
        if dll.query(entrance, zero, exact=False) != zero_truth:
            raise AssertionError("binary64 origin query disagrees after export")
        if actual != dll.export(entrance):
            raise AssertionError("repeated cached export changed fields")
        result.update({"name": case.name, "source_occurrences": len(case.sources),
                       "rounded_input_coordinates": case.rounded_coordinates,
                       "python_layer_samples_reverse_checked": len(samples),
                       "origin_body_state": zero_truth[0][0], "origin_topology_state": zero_truth[0][1],
                       "python_seconds": python_seconds, "cpp_build_seconds": build_seconds,
                       "cpp_export_seconds": export_seconds, "raw_segments": len(actual["raw_segments"]),
                       "convex_cells": len(actual.get("cells", [])),
                       "subdivision_sizes": {key: len(actual["subdivision"][key]) for key in ("vertices", "edges", "faces")},
                       "statistics": actual.get("statistics", {}), "local_statistics": local_statistics})
        return result, actual
    except Exception as exc:
        exc.c1_expected_export = expected
        exc.c1_actual_export = actual
        raise
    finally:
        if entrance is not None:
            dll.check(dll.entrance2_destroy(dll.context, entrance), "entrance2_destroy")
        for body in (b, a):
            if body is not None:
                dll.check(dll.body2_destroy(dll.context, body), "body2_destroy")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Reports include every source alias and case counter; compact JSON keeps
    # the complete audit below the repository's 1 MB tracked-file ceiling.
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)+"\n",
                    encoding="utf-8", newline="")


def pullback_export(export, model, baseline, inv_point, inv_a, inv_b, swapped=False):
    """Reindex raw labels by physical input features, never by enum order."""
    result = copy.deepcopy(export)
    def feature(poly, mapped, index, edge):
        targets = (mapped[index], mapped[(index+1) % len(mapped)]) if edge else (mapped[index],)
        for j in range(len(poly)):
            candidate = (poly[j], poly[(j+1) % len(poly)]) if edge else (poly[j],)
            if frozenset(targets) == frozenset(candidate):
                return j
        raise AssertionError("metamorphic source feature has no exact original")
    ma, mb = tuple(map(inv_a, model.A)), tuple(map(inv_b, model.B))
    def label(value):
        kind, i, j = value
        if not swapped:
            return [kind, feature(baseline.A, ma, i, kind == "EV"),
                    feature(baseline.B, mb, j, kind == "VE")]
        return ["EV" if kind == "VE" else "VE",
                feature(baseline.A, mb, j, kind == "VE"),
                feature(baseline.B, ma, i, kind == "EV")]
    def p(value):
        return ptext(inv_point(point(value)))
    for row in result["raw_segments"]:
        row["start"], row["end"], row["label"] = p(row["start"]), p(row["end"]), label(row["label"])
    for row in result["contact_segments"]:
        row["start"], row["end"] = p(row["start"]), p(row["end"])
        row["labels"] = [label(v) for v in row["labels"]]
    for row in result["contact_points"]:
        row["point"], row["labels"] = p(row["point"]), [label(v) for v in row["labels"]]
    for kind in ("vertices", "edges", "faces"):
        for row in result["subdivision"][kind]:
            row["vertices"], row["sample"] = [p(v) for v in row["vertices"]], p(row["sample"])
    result["boundary"] = [[p(a), p(b)] for a, b in result["boundary"]]
    return result


def metamorphic_checks(dll):
    # Dyadic, asymmetric L versus a flat-vertex rectangle: every input transform
    # is checked to be representable before it is sent to either implementation.
    a = ((0, 0), (F(1, 2), 0), (1, 0), (1, F(3, 4)), (0, F(3, 4)))
    b = ((-1, -1), (3, -1), (3, 0), (0, 0), (0, 2), (-1, 2))
    case = make_case("meta/base", a, b, "exact dyadic asymmetry matrix")
    base_model = GlobalEntrance2(case.a, case.b, merge_convex=True, compact_subdivision=True)
    _, base = run_case(dll, case)
    expected, results = canonical(base), []
    identity = lambda p: tuple(F(v) for v in p)
    for flags in range(8):
        _, actual = run_case(dll, case, flags=flags, query_first=False)
        if expected != canonical(actual):
            raise AssertionError(f"merge/compact/query-order invariant failed: flags={flags}")
        results.append({"name": "flags/query-order", "flags": flags})
    variants = [("cyclic", case.a[2:]+case.a[:2], case.b[3:]+case.b[:3], identity, identity, identity, False),
                ("cw", tuple(reversed(case.a)), tuple(reversed(case.b)), identity, identity, identity, False),
                ("body_swap", case.b, case.a, lambda p: (-p[0], -p[1]), identity, identity, True)]
    transforms = [
        ("rotate90", lambda p: (-p[1], p[0]), lambda p: (p[1], -p[0]), F(1), (0, 0), (0, 0)),
        ("reflect", lambda p: (-p[0], p[1]), lambda p: (-p[0], p[1]), F(1), (0, 0), (0, 0)),
        ("scale_small", identity, identity, F(1, 16), (0, 0), (0, 0)),
        ("scale_large", identity, identity, F(32), (0, 0), (0, 0)),
        ("translate_2p10", identity, identity, F(1), (2**10, -2**10), (-2**10, 2**10)),
        ("translate_2p17", identity, identity, F(1), (2**17, -2**17), (2**17, -2**17)),
    ]
    for name, rot, invrot, scale, ta, tb in transforms:
        def body(poly, t):
            return tuple(tuple(scale*rot(p)[k]+t[k] for k in (0, 1)) for p in poly)
        def inverse(p, t=(0, 0), s=scale, r=invrot):
            return r(tuple((p[k]-t[k])/s for k in (0, 1)))
        pa, pb = body(a, ta), body(b, tb)
        if any(F(float(v)) != v for poly in (pa, pb) for p in poly for v in p):
            raise AssertionError("metamorphic transform is not exactly binary64 representable")
        delta = tuple(tb[k]-ta[k] for k in (0, 1))
        variants.append((name, pa, pb, lambda p, t=delta, f=inverse: f(p, t),
                         lambda p, t=ta, f=inverse: f(p, t), lambda p, t=tb, f=inverse: f(p, t), False))
    for name, pa, pb, inv, ia, ib, swap in variants:
        transformed = make_case("meta/"+name, pa, pb, "exact dyadic asymmetry matrix")
        _, actual = run_case(dll, transformed)
        model = GlobalEntrance2(pa, pb, merge_convex=True, compact_subdivision=True)
        got = canonical(pullback_export(actual, model, base_model, inv, ia, ib, swap))
        if expected != got:
            fields = [key for key in expected if expected[key] != got[key]]
            raise AssertionError(f"exact metamorphic {name} mismatch: {fields}")
        results.append({"name": name, "exact_binary64_transform": True})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case-prefix", default="")
    parser.add_argument("--no-formal", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--metamorphic", action="store_true", help="exact ring/body/order/options/rigid/scale metamorphic matrix")
    parser.add_argument("--source-commit", default="not_supplied", help="owner-provided provenance; the runner never invokes git")
    args = parser.parse_args()
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")
    started = time.perf_counter()
    dll = Dll(args.dll)
    cases, coverage = corpus(not args.no_formal)
    selected = [c for c in cases if c.name.startswith(args.case_prefix)]
    if args.limit is not None:
        selected = selected[:args.limit]
    if not selected:
        raise ValueError("selection is empty")
    report = {"schema": "eab2.c1.diff.v1", "dll": str(args.dll),
              "dll_sha256": hashlib.sha256(args.dll.read_bytes()).hexdigest(),
              "source_commit": args.source_commit,
              "source_sha256": {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
                  "tools/eab2_diff_c1.py", "tools/eab2_c1_exact.py", "tools/eab2_c1_cases.py", "tools/eab2_c1_local.py",
                  "src/eab/kernel2d/global_entrance.py", "src/eab/kernel2d/exact.py", "src/eab/kernel2d/covers.py")},
              "build_identity": dll.identity, "coverage": coverage,
              "selected_cases": len(selected), "completed_cases": 0, "mismatches": [], "cases": [],
              "source_aliases": {c.name: c.sources for c in selected},
              "scope_note": "RN binary64 input; no claim original non-dyadic rational relations survive RN; identical ordered bit pairs deduplicated with all source aliases retained.",
              "comparison": "Python-computed maximal E\\O segments/source strata/endpoints/isolated points + exact oriented face-region boundaries + boundary; bidirectional rational layer queries"}
    try:
        for index, case in enumerate(selected):
            print(f"C1_CASE_BEGIN {index+1}/{len(selected)} {case.name}", flush=True)
            try:
                row, _ = run_case(dll, case)
                report["cases"].append(row)
                report["completed_cases"] += 1
            except Exception as exc:
                failure_path = ROOT / "reports/codex/C1E_evidence/tmp/failures" / f"case_{index:04d}.json"
                write_json(failure_path, {"case": case.name, "error": str(exc),
                                          "expected": getattr(exc, "c1_expected_export", None),
                                          "actual": getattr(exc, "c1_actual_export", None)})
                report["mismatches"].append({"name": case.name, "error": str(exc),
                                             "failure_artifact": str(failure_path),
                                             "a_bits": [[bits(x) for x in p] for p in case.a],
                                             "b_bits": [[bits(x) for x in p] for p in case.b]})
                write_json(args.output, report)
                raise
            report["elapsed_seconds"] = time.perf_counter()-started
            write_json(args.output, report)
            print(f"C1_CASE_PASS {index+1}/{len(selected)} {case.name}", flush=True)
        if args.metamorphic:
            report["metamorphic"] = metamorphic_checks(dll)
        report["origin_state_counts"] = dict(Counter(str(row["origin_body_state"]) for row in report["cases"]))
        report["elapsed_seconds"] = time.perf_counter()-started
        report["last_line"] = (f"C1_DIFF selected={len(selected)} completed={report['completed_cases']} "
                               f"mismatches=0 layer_queries={sum(r['cpp_layer_samples_rechecked']+r['python_layer_samples_reverse_checked'] for r in report['cases'])}")
        write_json(args.output, report)
        print(report["last_line"], flush=True)
    finally:
        dll.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"C1_DIFF_FAIL {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1)
