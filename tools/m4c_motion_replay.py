"""Read-only M4c endpoint-chord audit, not a replacement detector.

The independent ledger predicates use Fraction arithmetic and g0_oracle's
integer overlap, never production contact/cone/event primitives. An incomplete
run is not reusable evidence: progress and the final input/code hashes bind it.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from fractions import Fraction as F
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
import m4_shadow_replay as snapshot
from eab.construction import scalar_rational
from eab.kernel2d import g0_oracle as oracle
from eab.kernel2d import motion
from eab.kernel2d.global_entrance import GlobalEntrance2
from eab.kernel2d.motion_exit import shortest_exit_fast

PHASES = ("raw_df05", "post_df06")
CATEGORIES = frozenset({
    "FIRST_COVER_MATCH", "FIRST_INCIDENCE_NOT_COVER", "OTHER_FEATURE_FIRST",
    "NO_CONTACT_IN_STEP", "INITIAL_TOUCH_COVER_MATCH", "INITIAL_TOUCH_INCIDENCE_NOT_COVER",
    "INITIAL_TOUCH_OTHER_FEATURE", "INITIAL_OVERLAP_PD_MATCH", "INITIAL_OVERLAP_PD_OTHER_FEATURE",
    "INITIAL_OVERLAP_PD_NOT_EVALUATED_RESOURCE",
})
CASES = ("bb52", "bb12", "bb50", "bb51", "bb03", "bb05", "bb06", "bb09", "bb10",
         "bbv01", "bbv01_dbv01a", "bbv02", "bbv02_dbv02a", "bbF038", "bbS038")
require = snapshot.require
digest = snapshot.digest
file_hash = snapshot.file_hash
write_json = snapshot.write_json


def code_hashes():
    paths = [Path(__file__), ROOT / "tools/m4_shadow_replay.py", ROOT / "tools/m4_bdda_shadow.py",
             *sorted((ROOT / "src/eab").rglob("*.py"))]
    return {str(p.relative_to(ROOT)): file_hash(p) for p in paths}


def _exact_poly(poly):
    return tuple(tuple(F(c) for c in p) for p in poly)


def load_geometry_csv(path, frames):
    """Cross-check EVERY start frame before admitting the final endpoint."""
    groups = defaultdict(dict)
    with Path(path).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == ["kind", "idx", "x", "y"], "geometry CSV columns missing or shifted")
        for row in reader:
            require(None not in row and all(v is not None for v in row.values()), "geometry CSV row width")
            kind = row["kind"]
            if kind.startswith("step"):
                suffix = kind[4:]
                require(suffix.isascii() and suffix.isdigit() and kind == f"step{int(suffix)}",
                        "geometry CSV noncanonical step kind")
            else:
                require(kind in ("initial", "final", "range", "fixed"), "geometry CSV unknown kind")
            if kind in ("range", "fixed"):
                continue
            index = int(row["idx"])
            require(index not in groups[kind], "duplicate geometry CSV vertex")
            groups[kind][index] = tuple(scalar_rational(row[k], quantity="motion CSV coordinate") for k in ("x", "y"))
    n = len(frames)
    require({int(k[4:]) for k in groups if k.startswith("step")} == set(range(n+1)),
            "geometry CSV step sequence discontinuity or terminal missing")
    for frame in frames:
        points = groups[f"step{frame['step']-1}"]
        for _, v, x, y in frame["geometry"]:
            require(v in points and (x, y) == points[v], "snapshot/CSV step alignment mismatch")
    require(groups["step0"] == groups["initial"] and groups[f"step{n}"] == groups["final"],
            "geometry CSV initial/final mismatch")
    require(all(set(p) == set(groups["step0"]) for p in groups.values()), "geometry CSV topology mismatch")
    return [[b, v, *groups[f"step{n}"][v]] for b, v, _, _ in frames[-1]["geometry"]]


def load_endpoint(path, case, source, frames):
    payload = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=snapshot._unique_object)
    require(type(payload) is dict and set(payload) == {"schema", "cases"}
            and payload["schema"] == "eab.m4c-endpoints.v1" and type(payload["cases"]) is dict,
            "endpoint schema mismatch")
    row = payload["cases"][case]
    require(type(row) is dict and set(row) == {"endpoint_step", "geometry", "geometry_sha256", "snapshot_sha256",
            "start_geometry_sha256", "full_snapshot_sha256", "geometry_csv_sha256", "origin"}, "endpoint fields mismatch")
    for key in ("geometry_sha256", "snapshot_sha256", "start_geometry_sha256", "full_snapshot_sha256", "geometry_csv_sha256"):
        value = row[key]
        require(type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value), "endpoint hash type mismatch")
    require(type(row["endpoint_step"]) is int and row["endpoint_step"] >= 2, "endpoint step requires integer")
    require(row["snapshot_sha256"] == file_hash(source), "endpoint snapshot binding mismatch")
    require(row["endpoint_step"] == len(frames)+1, "endpoint step pairing mismatch")
    require(row["start_geometry_sha256"] == digest(frames[-1]["geometry"]), "endpoint start binding mismatch")
    geometry = row["geometry"]
    require(type(geometry) is list and geometry, "endpoint geometry must be a nonempty table")
    for values in geometry:
        require(type(values) is list and len(values) == 4, "endpoint geometry row width")
        b, v, x, y = values
        snapshot._integer(b, "endpoint block", 1)
        snapshot._integer(v, "endpoint vertex")
        snapshot._finite(x, "endpoint geometry.x")
        snapshot._finite(y, "endpoint geometry.y")
    require(digest(geometry) == row["geometry_sha256"], "endpoint geometry hash mismatch")
    return geometry


def _pair_frames(frames, terminal):
    """Single audited pairing seam; a one-frame-shift mutation must fail."""
    ending = {**frames[-1], "step": frames[-1]["step"]+1, "geometry": terminal,
              "raw_df05": [], "post_df06": []}
    for start, end in zip(frames, frames[1:]+[ending]):
        yield start, end


def paired_geometries(frames, terminal):
    require(terminal is not None, "terminal endpoint required; N starts are not N intervals")
    original_ids = [(b, v) for b, v, _, _ in frames[0]["geometry"]]
    require([(b, v) for b, v, _, _ in terminal] == original_ids, "terminal topology/order mismatch")
    output = []
    for index, (start, end) in enumerate(_pair_frames(frames, terminal)):
        require(start["step"] == index+1 and end["step"] == start["step"]+1,
                "motion step pairing mismatch")
        expected = frames[index+1]["geometry"] if index+1 < len(frames) else terminal
        require(end["geometry"] == expected, "motion geometry pairing mismatch")
        sg, eg = snapshot.geometry_from_frame(start), snapshot.geometry_from_frame(end)
        require(set(sg.blocks) == set(eg.blocks), "motion block topology mismatch")
        for block in sg.blocks:
            require(sg.blocks[block].vidx == eg.blocks[block].vidx, "motion canonical vertex topology mismatch")
        output.append((start, sg, eg))
    require(len(output) == len(frames), "motion pairing lost a step")
    return output


def _sign(value):
    return (value > 0)-(value < 0)


def algebraic_sign(t, c0, c1=0, c2=0):
    """Independent Fraction sign; imports no production algebraic predicate."""
    if t.rational is not None:
        return _sign(c0+c1*t.rational+c2*t.rational*t.rational)
    u, v = c0-c2*t.c, c1-c2*t.b
    r, z, d = u-v*t.b/2, v*t.branch/2, t.b*t.b-4*t.c
    if not z:
        return _sign(r)
    if not r or _sign(r) == _sign(z):
        return _sign(z)
    return _sign(r)*_sign(r*r-z*z*d)


def _difference(p, q):
    return tuple(p[k]-q[k] for k in (0, 1))


def _bilinear(a, b, cross=False):
    def f(p, q):
        return p[0]*q[1]-p[1]*q[0] if cross else p[0]*q[0]+p[1]*q[1]
    return f(a[0], b[0]), f(a[0], b[1])+f(a[1], b[0]), f(a[1], b[1])


def _path_difference(a, b):
    return _difference(a[0], b[0]), _difference(a[1], b[1])


def independent_features(A0, B0, A1, B1, t):
    """All closed incidences and locally valid covers, independently evaluated."""
    A = tuple((p, _difference(q, p)) for p, q in zip(A0, A1))
    B = tuple((p, _difference(q, p)) for p, q in zip(B0, B1))
    incidences, covers = set(), set()
    for P, Q, tag in ((A, B, "VE"), (B, A, "EV")):
        for i, p in enumerate(P):
            for j, a in enumerate(Q):
                b = Q[(j+1) % len(Q)]
                e = _path_difference(b, a)
                u, v = _path_difference(p, a), _path_difference(p, b)
                if algebraic_sign(t, *_bilinear(e, u, True)) or algebraic_sign(t, *_bilinear(u, v)) > 0:
                    continue
                key = (tag, i, j) if tag == "VE" else (tag, j, i)
                incidences.add(key)
                before = _path_difference(p, P[i-1])
                after = _path_difference(P[(i+1) % len(P)], p)
                turn = algebraic_sign(t, *_bilinear(before, after, True))
                cone = turn >= 0 and algebraic_sign(t, *_bilinear(e, before, True)) >= 0 and algebraic_sign(t, *_bilinear(after, e, True)) >= 0
                if turn == 0:
                    cone = cone and algebraic_sign(t, *_bilinear(before, after)) > 0 and algebraic_sign(t, *_bilinear(e, before)) < 0
                if cone:
                    covers.add(key)
    for i, p in enumerate(A):
        for j, q in enumerate(B):
            u, v = _path_difference(p, q)
            if all(algebraic_sign(t, u[k], v[k]) == 0 for k in (0, 1)):
                incidences.add(("VV", i, j)); covers.add(("VV", i, j))
    return tuple(sorted(incidences)), tuple(sorted(covers))


def _feature_keys(labels, a, b):
    keys = set()
    for tag, i, j in labels:
        if tag == "VV":
            keys.add(("VV", *sorted((a.vidx[i], b.vidx[j]))))
        else:
            v, edge, ei = (a.vidx[i], b, j) if tag == "VE" else (b.vidx[j], a, i)
            keys.add(("VE", v, *sorted((edge.vidx[ei], edge.vidx[(ei+1) % len(edge.vidx)]))))
    return tuple(sorted(keys))


def _legacy_key(row, sg):
    return ("VE", sg.canon(row[1]), *sorted((sg.canon(row[2]), sg.canon(row[3]))))


def _legacy_pair(row, sg):
    owners = sg.vertex_block()
    return tuple(sorted((owners[sg.canon(row[1])], owners[sg.canon(row[2])])) )


def _swept_overlap(A0, B0, A1, B1):
    return all(max(p[k] for p in A0+A1) >= min(p[k] for p in B0+B1)
               and max(p[k] for p in B0+B1) >= min(p[k] for p in A0+A1) for k in (0, 1))


def translation_surrogate(A0, A1):
    delta = tuple(_difference(q, p) for p, q in zip(A0, A1))
    mean = tuple(sum(p[k] for p in delta)/len(delta) for k in (0, 1))
    radius = max(abs(p[k]-mean[k]) for p in delta for k in (0, 1))
    return tuple(tuple(p[k]+mean[k] for k in (0, 1)) for p in A0), radius


def translation_certificate(delta):
    return "CERTIFIED_IDENTICAL_TRAJECTORY" if delta == 0 else "UNCERTIFIED_NONTRANSLATION"


def _checked_motion(A0, B0, A1, B1, initial_state):
    result = motion.motion_first_entrance(A0, B0, A1, B1)
    require(result.initial_state == initial_state, "independent initial state mismatch")
    if result.exact_time is not None:
        incidences, covers = independent_features(A0, B0, A1, B1, result.exact_time)
        require(result.incidences == incidences, "independent complete incidence mismatch")
        require(result.features == covers, "independent complete cover mismatch")
    return result


def _motion_record(result, a, b):
    return {"status": result.status, "time": None if result.exact_time is None else result.exact_time.certificate,
            "time_display": result.time, "features": _feature_keys(result.features, a, b),
            "incidences": _feature_keys(result.incidences, a, b)}


def _pd(A, B, a, b, limit):
    # A deterministic input-work cap, never a data-dependent time-out that
    # silently changes a classification. --pd-edge-limit 0 means unlimited.
    if limit and (len(A)-2)*(len(B)-2)*6 > limit:
        return {"status": "NOT_EVALUATED_RESOURCE", "features": ()}
    model = GlobalEntrance2(A, B)
    if limit and len(model.cell_edges) > limit:
        return {"status": "NOT_EVALUATED_RESOURCE", "features": ()}
    value = shortest_exit_fast(model, x=(0, 0))
    keys = set()
    for point in value.tied_exact_points:
        moved = tuple((p[0]+point[0], p[1]+point[1]) for p in A)
        require(oracle.overlap(moved, B) == 0 and oracle.boundary_has_exterior(moved, B),
                "independent PD boundary certificate failed")
        _, covers = independent_features(moved, B, moved, B, motion.QuadraticTime(F(0)))
        keys.update(_feature_keys(covers, a, b))
    return {"status": "EVALUATED", "squared": str(value.squared),
            "points": [[str(x), str(y)] for x, y in value.tied_exact_points], "features": tuple(sorted(keys))}


def classify_reference(initial_state, key, result, pd):
    """Closed partition. State and feature membership are exact predicates."""
    if initial_state == 1:
        if pd["status"] != "EVALUATED":
            return "INITIAL_OVERLAP_PD_NOT_EVALUATED_RESOURCE"
        return "INITIAL_OVERLAP_PD_MATCH" if key in pd["features"] else "INITIAL_OVERLAP_PD_OTHER_FEATURE"
    if result["status"] == "no_contact":
        return "NO_CONTACT_IN_STEP"
    prefix = "FIRST" if initial_state == -1 else "INITIAL_TOUCH"
    if key in result["features"]:
        return prefix+"_COVER_MATCH"
    if key in result["incidences"]:
        return prefix+"_INCIDENCE_NOT_COVER"
    return "OTHER_FEATURE_FIRST" if initial_state == -1 else "INITIAL_TOUCH_OTHER_FEATURE"


def _penetration_witness(A, B):
    """Certified point-inside depth, NOT global PD or maximum transient depth."""
    squares = []
    for P, Q in ((A, B), (B, A)):
        for p in P:
            if oracle.inside(p, Q) == 1:
                squares.append(min(oracle.segment_square(p, q, Q[(j+1) % len(Q)])[0] for j, q in enumerate(Q)))
    return {"observable": "largest_vertex_interior_clearance_at_step_end_not_global_PD",
            "squared": str(max(squares)) if squares else None, "has_strict_vertex_witness": bool(squares)}


def frame_result(frame, sg, eg, previous=None, *, pd_edge_limit=24):
    geometries = {b: (_exact_poly(sg.blocks[b].poly), _exact_poly(eg.blocks[b].poly)) for b in sg.blocks}
    # Validate every block, including blocks excluded by the swept-pair boxes.
    for A0, A1 in geometries.values():
        motion._validated_motion(A0, A1)
    legacy_pairs = {phase: {_legacy_pair(r, sg) for r in frame[phase]} for phase in PHASES}
    union = set().union(*legacy_pairs.values())
    pair_records = {}
    stats = Counter()
    blocks = sorted(sg.blocks)
    for ix, ba in enumerate(blocks):
        for bb in blocks[ix+1:]:
            A0, A1 = geometries[ba]; B0, B1 = geometries[bb]
            pair = (ba, bb)
            if pair not in union and not _swept_overlap(A0, B0, A1, B1):
                stats["swept_box_proven_no_contact_pairs"] += 1
                continue
            a, b = sg.blocks[ba], sg.blocks[bb]
            state = oracle.overlap(A0, B0)
            stats[{1: "initial_overlap_pairs", 0: "initial_touch_pairs", -1: "initial_separated_pairs"}[state]] += 1
            pd = None
            if state == 1:
                pd = _pd(A0, B0, a, b, pd_edge_limit)
                record = {"status": "initial_overlap", "time": None, "time_display": None, "features": (), "incidences": ()}
                stats["pd_"+pd["status"].lower()+"_pairs"] += 1
            else:
                actual = _checked_motion(A0, B0, A1, B1, state)
                record = _motion_record(actual, a, b)
                if state == -1 and actual.status == "contact":
                    stats["new_contact_pairs"] += 1
            row = {"pair": pair, "initial_state": state, "actual": record, "pd": pd}
            if state >= 0 and pair not in union:
                row["initial_contact_absent_both_legacy_tables"] = True
                stats["initial_contact_pairs_absent_both_tables"] += 1
            if state == -1:
                At, da = translation_surrogate(A0, A1); Bt, db = translation_surrogate(B0, B1)
                surrogate = _checked_motion(A0, B0, At, Bt, state)
                trans = _motion_record(surrogate, a, b)
                # This is a descriptive comparison of TWO exact paths. It is
                # not the certificate that one path safely substitutes another.
                same = record["status"] == trans["status"] and record["features"] == trans["features"]
                same_time = record["time"] == trans["time"]
                certificate = translation_certificate(da+db)
                row["translation"] = {"delta_linf": str(da+db), "certificate": certificate,
                                      "same_first_cover_set": same, "same_time": same_time, "result": trans}
                stats["translation_"+certificate.lower()] += 1
                stats["translation_descriptive_same_cover" if same else "translation_descriptive_different_cover"] += 1
                if certificate == "CERTIFIED_IDENTICAL_TRAJECTORY":
                    require(same and same_time, "certified translation contract mismatch")
                if previous is None:
                    row["prediction"] = {"status": "UNAVAILABLE_NO_PREVIOUS_STEP"}
                    stats["prediction_unavailable"] += 1
                else:
                    Ap = _exact_poly(previous.blocks[ba].poly); Bp = _exact_poly(previous.blocks[bb].poly)
                    Ae = tuple(tuple(2*p[k]-q[k] for k in (0, 1)) for p, q in zip(A0, Ap))
                    Be = tuple(tuple(2*p[k]-q[k] for k in (0, 1)) for p, q in zip(B0, Bp))
                    try:
                        predicted = _checked_motion(A0, B0, Ae, Be, state)
                    except ValueError as exc:
                        row["prediction"] = {"status": "UNAVAILABLE_PREDICTED_DOMAIN", "reason": str(exc)}
                        stats["prediction_invalid_domain"] += 1
                    else:
                        forecast = _motion_record(predicted, a, b)
                        same_prediction = record["status"] == forecast["status"] and record["features"] == forecast["features"]
                        row["prediction"] = {"status": "EVALUATED_PREVIOUS_DISPLACEMENT", "same_first_cover_set": same_prediction, "result": forecast}
                        stats["prediction_same_cover" if same_prediction else "prediction_different_cover"] += 1
                if record["status"] == "contact" and pair not in union:
                    row["missing_both_legacy_tables"] = True
                    row["depth_witness"] = _penetration_witness(A1, B1)
                    stats["new_contact_pairs_absent_both_tables"] += 1
            pair_records[pair] = row
    phases = {}
    for phase in PHASES:
        records, counts, secondary_counts = [], Counter(), Counter()
        for index, raw in enumerate(frame[phase], 1):
            pair = _legacy_pair(raw, sg); key = _legacy_key(raw, sg); row = pair_records[pair]
            category = classify_reference(row["initial_state"], key, row["actual"], row["pd"])
            require(category in CATEGORIES, "unclassified motion ledger category: "+category)
            counts[category] += 1
            # VV secondary reference is preserved explicitly, never replaced
            # with only a point-point identity match.
            secondary = None
            secondary_category = None
            if raw[0] == 1 and all(raw[k] for k in (4, 5, 6)):
                secondary = ("VE", sg.canon(raw[4]), *sorted((sg.canon(raw[5]), sg.canon(raw[6]))))
                secondary_category = classify_reference(row["initial_state"], secondary, row["actual"], row["pd"])
                require(secondary_category in CATEGORIES, "unclassified secondary motion ledger category")
                secondary_counts[secondary_category] += 1
            records.append({"index": index, "tuple7": raw, "pair": pair, "primary_reference": key,
                            "secondary_reference": secondary, "category": category, "secondary_category": secondary_category})
        require(sum(counts.values()) == len(frame[phase]), "legacy row conservation mismatch")
        phases[phase] = {"counts": dict(sorted(counts.items())), "secondary_counts": dict(sorted(secondary_counts.items())), "records": records}
    return {"step": frame["step"], "endpoint_step": frame["step"]+1,
            "start_geometry_sha256": digest(frame["geometry"]),
            "stats": dict(sorted(stats.items())), "pairs": list(pair_records.values()), "phases": phases}


def replay_file(path, *, geometry_csv=None, endpoint_file=None, case=None, pd_edge_limit=24,
                normalized_sink=None, progress_path=None):
    started = time.perf_counter()
    header, frames, end = snapshot.read_snapshot(path)
    require((geometry_csv is None) != (endpoint_file is None), "exactly one terminal source is required")
    terminal = load_geometry_csv(geometry_csv, frames) if geometry_csv else load_endpoint(endpoint_file, case, path, frames)
    paired = paired_geometries(frames, terminal)
    source_hashes = {"snapshot": file_hash(path), "terminal_source": file_hash(geometry_csv or endpoint_file)}
    initial_code = code_hashes()
    stats = Counter(); counts = {p: Counter() for p in PHASES}; secondary_counts = {p: Counter() for p in PHASES}; frame_hashes = []; examples = {}
    previous = None
    for frame, sg, eg in paired:
        result = frame_result(frame, sg, eg, previous, pd_edge_limit=pd_edge_limit)
        previous = sg
        stats.update(result["stats"])
        frame_hashes.append(digest(result))
        for phase in PHASES:
            counts[phase].update(result["phases"][phase]["counts"])
            secondary_counts[phase].update(result["phases"][phase]["secondary_counts"])
            for row in result["phases"][phase]["records"]:
                key = phase+":"+row["category"]
                if key not in examples:
                    pair = next(p for p in result["pairs"] if p["pair"] == row["pair"])
                    ba, bb = row["pair"]
                    examples[key] = {"step": frame["step"], "legacy": row, "comparison": pair,
                                     "A0": sg.blocks[ba].poly, "A1": eg.blocks[ba].poly,
                                     "B0": sg.blocks[bb].poly, "B1": eg.blocks[bb].poly}
        if normalized_sink is not None:
            normalized_sink.write(json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False)+"\n")
            normalized_sink.flush()
        if progress_path is not None:
            write_json(progress_path, {"complete": False, "completed_steps": frame["step"], "requested_steps": len(frames),
                                      "input_hashes": source_hashes, "code_hashes": initial_code})
    require(code_hashes() == initial_code, "code changed during replay; run invalid")
    require(file_hash(path) == source_hashes["snapshot"] and file_hash(geometry_csv or endpoint_file) == source_hashes["terminal_source"],
            "input changed during replay; run invalid")
    partial = ["Nonzero nontranslation first-cover stability is uncertified."]
    if stats.get("pd_not_evaluated_resource_pairs", 0):
        partial.append("Initial-overlap PD above the deterministic work cap is not evaluated.")
    return {"schema": "eab.m4c-replay.v1", "audit": "GREEN", "complete": True, "case": case,
            "steps": len(frames), "counts": {p: dict(sorted(c.items())) for p, c in counts.items()},
            "secondary_counts": {p: dict(sorted(c.items())) for p, c in secondary_counts.items()},
            "stats": dict(sorted(stats.items())), "input_hashes": source_hashes, "code_hashes": initial_code,
            "frame_sha256": frame_hashes, "frames_sha256": digest(frame_hashes), "examples": examples,
            "pd_edge_limit": pd_edge_limit, "seconds": time.perf_counter()-started,
            "partial": partial}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--geometry-csv", type=Path)
    parser.add_argument("--endpoint-file", type=Path)
    parser.add_argument("--case")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pd-edge-limit", type=int, default=24, help="deterministic work cap; 0 is unlimited")
    args = parser.parse_args(argv)
    paths = [args.out / "audit.json", args.out / "normalized.jsonl.gz", args.out / "progress.json"]
    sources = [p for p in (args.snapshot, args.geometry_csv, args.endpoint_file) if p is not None]
    try:
        require(args.pd_edge_limit >= 0, "negative PD work cap")
        require(not any(snapshot._same_file(p, s) for p in paths for s in sources), "output aliases read-only input")
        require(not any(snapshot._same_file(p, q) for i, p in enumerate(paths) for q in paths[i+1:]), "outputs alias each other")
        args.out.mkdir(parents=True, exist_ok=True)
        require(not paths[0].exists() and not paths[1].exists(), "output evidence directory already has a run; choose a new directory")
        with paths[1].open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding="utf-8", newline="\n") as sink:
                    result = replay_file(args.snapshot, geometry_csv=args.geometry_csv, endpoint_file=args.endpoint_file,
                                         case=args.case, pd_edge_limit=args.pd_edge_limit, normalized_sink=sink, progress_path=paths[2])
        result["normalized_sha256"] = file_hash(paths[1])
        write_json(paths[0], result)
        write_json(paths[2], {"complete": True, "completed_steps": result["steps"], "audit_sha256": file_hash(paths[0])})
        print(f"M4C_AUDIT_GREEN {args.case} steps={result['steps']} seconds={result['seconds']:.3f}")
        return 0
    except Exception as exc:
        # This is the outer CLI AUDIT boundary, not a geometric fallback.
        # Every ordinary failure stays a nonzero/RED result with its original
        # type. BaseException (KeyboardInterrupt/SystemExit) must propagate.
        error_type = type(exc).__name__
        print("M4C_AUDIT_RED "+error_type+": "+str(exc), file=sys.stderr)
        # Never overwrite a pre-existing evidence file or an alias just to
        # produce a RED report. The stderr failure is the remaining safe sink.
        if args.out.exists() and not paths[0].exists() and not any(snapshot._same_file(paths[0], s) for s in sources+paths[1:]):
            try:
                write_json(paths[0], {"audit": "RED", "complete": False, "error_type": error_type, "error": str(exc)})
            except Exception as write_error:
                # One attempt only. A broken/full/unwritable audit sink is
                # reported on stderr, never recursively retried or made GREEN.
                print("M4C_AUDIT_RED_WRITE_ERROR "+type(write_error).__name__+": "+str(write_error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
