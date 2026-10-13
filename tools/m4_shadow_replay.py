"""M4b versioned read-only bdda2 snapshot replay, never a solver input.

The L5 detector sees only step-start geometry and explicit domain parameters.
Classification reuses M4a's independent Fraction halfspace/edge oracle, not
production geometric primitives. A malformed, truncated or unclassified audit
is RED; CLI errors never modify the snapshot or the legacy solver products.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
import io
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import m4_bdda_shadow as m4a
from eab.adapters import bdda2d
from eab.contact_record import ContactRecord, CoverType, Feature
from eab.construction import scalar_rational
from eab.kernel2d.geom import ensure_ccw
from eab.readers.bdda_geom import BlockGeom, StepGeometry, strip_duplicate_vertices
from eab.readers.bdda_df import _edge_start, _vv_opposite_vertex

GEOMETRY_COLUMNS = ["block", "vidx", "x", "y"]
TUPLE_COLUMNS = ["mtype", "p1", "p2", "p3", "m4", "m5", "m6"]
PARAMETERS = {"d0", "h1", "h5", "f0", "f1", "f2", "h2", "w0", "hh", "g0"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _integer(value, label, minimum=0):
    require(type(value) is int and value >= minimum, f"{label}: expected integer >= {minimum}")
    return value


def _finite(value, label):
    require(type(value) in (int, float) and math.isfinite(value), f"{label}: expected finite number")
    return scalar_rational(value, quantity=label)


def _unique_object(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, f"duplicate JSON field: {key}")
        out[key] = value
    return out


def read_snapshot(path, *, expected_steps=None):
    """Strict envelope, row width/order, continuity and topology validation."""
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        rows = [json.loads(line, object_pairs_hook=_unique_object,
                           parse_float=lambda value: scalar_rational(value, quantity="shadow JSON number")) for line in stream]
    require(len(rows) >= 3, "missing header/step/end snapshot envelope")
    header, end = rows[0], rows[-1]
    require(set(header) == {"kind", "schema", "version", "mode", "detector", "requested_steps",
                            "screen", "geometry_columns", "tuple_columns"}, "header fields mismatch")
    require(header["kind"] == "header" and header["schema"] == "bdda2.detect-shadow"
            and _integer(header["version"], "version", 1) == 1 and header["mode"] == "shadow"
            and header["detector"] == "legacy-df04-df05", "unsupported shadow schema/mode/detector")
    require(header["geometry_columns"] == GEOMETRY_COLUMNS, "geometry columns missing or shifted")
    require(header["tuple_columns"] == TUPLE_COLUMNS, "tuple columns missing or shifted")
    require(set(header["screen"]) == {"max_x", "max_y"}, "screen fields mismatch")
    for key, value in header["screen"].items():
        _integer(value, f"screen.{key}", 1)
    n = _integer(header["requested_steps"], "requested_steps", 1)
    require(expected_steps is None or n == expected_steps, "requested steps mismatch")
    require(set(end) == {"kind", "completed_steps", "status"} and end["kind"] == "end",
            "missing/malformed end marker")
    require(end["status"] == "ok", f"snapshot producer not ok: {end['status']}")
    require(_integer(end["completed_steps"], "completed_steps", 1) == n, "incomplete shadow capture")
    frames = rows[1:-1]
    require(len(frames) == n, "missing/extra snapshot step")
    topology = None
    for step, frame in enumerate(frames, 1):
        require(set(frame) == {"kind", "step", "parameters", "geometry", "raw_df05", "post_df06"},
                "step fields mismatch")
        require(frame["kind"] == "step" and _integer(frame["step"], "step", 1) == step,
                "snapshot step sequence discontinuity")
        require(set(frame["parameters"]) == PARAMETERS, "parameter columns missing/extra")
        for key, value in frame["parameters"].items():
            _finite(value, f"parameters.{key}")
        require(frame["geometry"], "empty geometry")
        ids = []
        for row in frame["geometry"]:
            require(isinstance(row, list) and len(row) == 4, "geometry row width: missing/shifted column")
            b, v, x, y = row
            ids.append((_integer(b, "block", 1), _integer(v, "vidx")))
            _finite(x, "geometry.x")
            _finite(y, "geometry.y")
        require(ids == sorted(ids) and len({v for _, v in ids}) == len(ids),
                "geometry row identity/order mismatch")
        require(topology is None or topology == ids, "geometry identity shifted across steps")
        topology = ids
        for phase in ("raw_df05", "post_df06"):
            require(isinstance(frame[phase], list), f"{phase}: expected table")
            for row in frame[phase]:
                require(isinstance(row, list) and len(row) == 7, f"{phase} row width: missing/shifted column")
                for value in row:
                    _integer(value, f"{phase} tuple")
                require(row[0] in (0, 1), f"{phase}: unknown mtype")
        sg = geometry_from_frame(frame)
        for phase in ("raw_df05", "post_df06"):
            records_from_frame(frame, sg, phase)
    return header, frames, end


def geometry_from_frame(frame):
    grouped = defaultdict(list)
    for block, vertex, x, y in frame["geometry"]:
        grouped[block].append((vertex, (x, y)))
    sg = StepGeometry(frame["step"], {})
    original = {v: p for rows in grouped.values() for v, p in rows}
    for block, rows in grouped.items():
        ids, poly, aliases = strip_duplicate_vertices([v for v, _ in rows], [p for _, p in rows], block=block)
        # M4a's reader tolerates nearly equal aliases; this capture is admitted
        # only if aliases are exactly equal supplied binary64 coordinates.
        require(all(original[v] == original[target] for v, target in aliases.items()),
                "nonexact geometry alias would change supplied snapshot")
        poly, flipped = ensure_ccw(poly)
        sg.blocks[block] = BlockGeom(block, poly, list(reversed(ids)) if flipped else ids, flipped)
        sg.alias.update(aliases)
    return sg


def records_from_frame(frame, sg, phase):
    """Map Tuple7 identities only; never invent post-solve state or metric data."""
    owners = sg.vertex_block()
    records = []
    for index, row in enumerate(frame[phase], 1):
        c = dict(zip(TUPLE_COLUMNS, row))
        mtype, p1, p2, p3, m4, m5, m6 = row
        for v in (p1, p2, p3):
            require(sg.canon(v) in owners, f"{phase}: primary vertex outside snapshot")
        a, b = owners[sg.canon(p1)], owners[sg.canon(p2)]
        require(a != b and owners[sg.canon(p3)] == b, f"{phase}: shifted tuple/block incidence")
        require(all(v == 0 or sg.canon(v) in owners for v in (m4, m5, m6)),
                f"{phase}: secondary vertex outside snapshot")
        extra = dict(raw_p1=p1, raw_p2=p2, p3=p3, m4=m4, m5=m5, m6=m6,
                     observable="step_start_tuple_identity", temporal_plane=phase)
        if mtype == 1:
            other = _vv_opposite_vertex(c, sg, a, b)
            fb = Feature(b, "vertex", other)
        else:
            start = _edge_start(sg, b, p2, p3, extra)
            require(not extra.get("_edge_not_adjacent"), f"{phase}: shifted/nonadjacent reference edge")
            fb = Feature(b, "edge", start)
        records.append(ContactRecord(source=f"bdda2-shadow:{phase}", step=sg.step, contact_index=index,
                                     block_a=a, block_b=b, cover=CoverType.VV if mtype else CoverType.VE,
                                     raw_cover=mtype, feature_a=Feature(a, "vertex", sg.canon(p1)),
                                     feature_b=fb, extra=extra))
    return records


def frame_result(frame):
    sg = geometry_from_frame(frame)
    p = frame["parameters"]
    window = bdda2d.Bdda2DWindow(frame["step"], p["d0"], p["h1"],
                                source="bdda2.detect-shadow:v1", raw_parameters=p)
    detected = bdda2d.detect_step(sg, window)
    phases, normalized = {}, {"step": sg.step, "eab": [r.to_dict() for r in detected]}
    for phase in ("raw_df05", "post_df06"):
        legacy = records_from_frame(frame, sg, phase)
        compared = m4a.compare_step(sg, window, legacy, eab=detected)
        m4a.assert_classified([compared])
        compared["difference_sha256"] = digest(compared["differences"])
        phases[phase] = compared
        # Materialize MATCH as well as differences on each original legacy row;
        # a duplicate keeps its own row index and never silently disappears.
        by_contact = {d["legacy_contact"]: d["category"] for d in compared["differences"]
                      if d.get("legacy_contact") is not None}
        by_key = {tuple(d["key"]): d["category"] for d in compared["differences"]
                  if d["category"] != "LEGACY_DUPLICATE_PRIMARY_REFERENCE"}
        normalized[phase] = []
        for record in legacy:
            output = record.to_dict()
            output["extra"]["classification"] = by_contact.get(record.contact_index, "MATCH")
            normalized[phase].append(output)
        for record, output in zip(detected, normalized["eab"]):
            output["extra"].setdefault("classification_by_legacy_plane", {})[phase] = by_key.get(
                m4a.record_key(record, sg), "MATCH")
    return {"step": sg.step, "phases": phases}, normalized


def compare_m4a(frames, results, fixture):
    """Explain every first-three-step count/key discrepancy by observed inputs.

    This does not excuse unexplained classification drift: equal detection
    inputs with a different classification fail. Both old and new snapshots
    independently pass the same exact local-eligibility classifier.
    """
    path = ROOT / "fixtures/bdda_df" / fixture
    old_geoms = m4a.load_step_geometries(path / "bdda_debug_verts.csv")
    old_records = m4a.bdda_df.load_records(path)
    frozen = json.loads((ROOT / "tests/m4_shadow_expected.json").read_text(encoding="utf-8"))[fixture]
    output = []
    for frame, result, expected in zip(frames[:3], results[:3], frozen):
        step = frame["step"]
        oldsg, newsg = old_geoms[step], geometry_from_frame(frame)
        oldwin = m4a.load_window(path, step)
        old = m4a.compare_step(oldsg, oldwin, [r for r in old_records if r.step == step])
        require(old["counts"] == expected["counts"] and digest(old["differences"]) == expected["difference_sha256"],
                "M4a frozen result no longer reproducible")
        new = result["phases"]["post_df06"]
        oldpos, newpos = oldsg.vertex_pos(), newsg.vertex_pos()
        require(set(oldpos) == set(newpos), "M4a vertex identity map differs")
        changed = [{"vertex": v, "m4a": oldpos[v], "m4b": newpos[v]} for v in sorted(oldpos)
                   if oldpos[v] != newpos[v]]
        oldtuples = [[r.raw_cover, r.extra["raw_p1"], r.extra["raw_p2"], r.extra["p3"],
                      r.extra["m4"], r.extra["m5"], r.extra["m6"]] for r in old_records if r.step == step]
        tuples_changed = oldtuples != frame["post_df06"]
        parameters_changed = {k: {"m4a": oldwin.raw_parameters.get(k), "m4b": value}
                              for k, value in frame["parameters"].items()
                              if k in oldwin.raw_parameters and oldwin.raw_parameters[k] != value}
        same = old["counts"] == new["counts"] and old["differences"] == new["differences"]
        require(same or changed or tuples_changed or parameters_changed,
                "M4a classification changed with identical snapshot inputs")
        # Attribute each key independently, including incident edges used by
        # the normal cone. An unrelated vertex/parameter change cannot excuse
        # a discrepancy elsewhere in the frame.
        def per_key(row, records, geom):
            out = defaultdict(Counter)
            nonmatches = {tuple(d["key"]) for d in row["differences"]
                          if d["category"] != "LEGACY_DUPLICATE_PRIMARY_REFERENCE"}
            for record in records:
                key = m4a.record_key(record, geom)
                if key not in nonmatches:
                    out[key]["MATCH"] = 1
            for difference in row["differences"]:
                out[tuple(difference["key"])][difference["category"]] += 1
            return out

        def local_vertices(key, sg):
            ids = set(key[1:])
            owners = sg.vertex_block()
            # VE's vertex normal cone; VV's two vertex normal cones.
            corners = key[1:] if key[0] == "VV" else key[1:2]
            for vertex in corners:
                block = sg.blocks[owners[vertex]]
                index = block.vidx.index(vertex)
                ids.update(block.vidx[k % len(block.vidx)] for k in (index-1, index+1))
            return ids

        oldrecs = [r for r in old_records if r.step == step]
        newrecords = records_from_frame(frame, newsg, "post_df06")
        olddiff, newdiff = per_key(old, oldrecs, oldsg), per_key(new, newrecords, newsg)
        oldkeys = Counter(m4a.record_key(r, oldsg) for r in oldrecs)
        newkeys = Counter(m4a.record_key(r, newsg) for r in newrecords)
        newwin = bdda2d.Bdda2DWindow(step, frame["parameters"]["d0"], frame["parameters"]["h1"])
        relevant_parameters = {k: v for k, v in parameters_changed.items() if k in ("d0", "h1")}
        changes = []
        for key in sorted(olddiff.keys() | newdiff.keys()):
            before, after = olddiff[key], newdiff[key]
            if before != after:
                local = local_vertices(key, oldsg) | local_vertices(key, newsg)
                local_changes = [r for r in changed if r["vertex"] in local]
                require(local_changes or relevant_parameters or oldkeys[key] != newkeys[key],
                        f"M4a unexplained per-key classification discrepancy: step {step} {key}")
                changes.append({"key": key, "m4a": dict(before), "m4b": dict(after),
                                "legacy_multiplicity": [oldkeys[key], newkeys[key]],
                                "m4a_eligibility": m4a.eligibility(key, oldsg, oldwin),
                                "m4b_eligibility": m4a.eligibility(key, newsg, newwin),
                                "m4a_strict_eligibility": m4a.eligibility(key, oldsg, oldwin, strict_window=True),
                                "m4b_strict_eligibility": m4a.eligibility(key, newsg, newwin, strict_window=True),
                                "local_coordinate_changes_including_incident_edges": local_changes,
                                "relevant_parameter_changes": relevant_parameters})
        # Classifications are a disjoint key partition, including duplicate rows.
        require(sum((c for c in olddiff.values()), Counter()) == Counter(old["counts"]),
                "M4a per-key attribution does not reconstruct frozen counts")
        require(sum((c for c in newdiff.values()), Counter()) == Counter(new["counts"]),
                "M4b per-key attribution does not reconstruct replay counts")
        output.append({"step": step, "identical_classification": same,
                       "m4a_counts": old["counts"], "m4b_counts": new["counts"],
                       "coordinate_changes": changed, "parameter_changes": parameters_changed,
                       "ordered_tuple_changes": ({"m4a": oldtuples, "m4b": frame["post_df06"]}
                                                 if tuples_changed else None),
                       "classification_changes": changes,
                       "cause": "IDENTICAL" if same else "OBSERVED_SNAPSHOT_INPUT_DIFFERENCE_NOT_M4A_CLASSIFIER_CHANGE"})
    return output


def replay_file(path, *, expected_steps=None, m4a_fixture=None, normalized_sink=None):
    header, frames, end = read_snapshot(path, expected_steps=expected_steps)
    results = []
    totals = {phase: Counter() for phase in ("raw_df05", "post_df06")}
    for frame in frames:
        result, normalized = frame_result(frame)
        results.append(result)
        if normalized_sink is not None:
            normalized_sink.write(json.dumps(normalized, ensure_ascii=False, separators=(",", ":"), allow_nan=False)+"\n")
        for phase in totals:
            totals[phase].update(result["phases"][phase]["counts"])
    return {"schema": "eab.m4b-replay.v1", "audit": "GREEN", "snapshot_sha256": file_hash(path),
            "snapshot_bytes": Path(path).stat().st_size, "header": header, "end": end,
            "observable": bdda2d.OBSERVABLE, "steps": len(results),
            "counts": {phase: dict(sorted(c.items())) for phase, c in totals.items()},
            "frames": results,
            "m4a_comparison": compare_m4a(frames, results, m4a_fixture) if m4a_fixture else None,
            "limits": ["Detection identity/local geometry only; no current-step motion/first-entrance claim.",
                       "No solver state, force, assembly or physical-equivalence claim.",
                       "Legacy tuples are never used to filter the L5 enumeration."]}


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")



def _same_file(first, second):
    """Resolve path aliases AND existing hardlinks before any output mutation."""
    first, second = Path(first), Path(second)
    return first.resolve() == second.resolve() or (first.exists() and second.exists() and first.samefile(second))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expected-steps", type=int)
    parser.add_argument("--m4a-fixture")
    args = parser.parse_args(argv)
    normalized = args.out / "normalized.jsonl.gz"
    audit = args.out / "audit.json"
    outputs_safe = False
    try:
        require(not _same_file(args.snapshot, normalized) and not _same_file(args.snapshot, audit),
                "snapshot path/hardlink overlaps audit output; source is read-only")
        require(not _same_file(normalized, audit), "audit outputs alias the same file/hardlink")
        outputs_safe = True
        args.out.mkdir(parents=True, exist_ok=True)
        # Empty gzip filename + fixed mtime make byte/hash evidence reproducible.
        with normalized.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8", newline="\n") as stream:
                result = replay_file(args.snapshot, expected_steps=args.expected_steps,
                                     m4a_fixture=args.m4a_fixture, normalized_sink=stream)
        result["normalized_sha256"] = file_hash(normalized)
        result["normalized_file"] = normalized.name
        write_json(args.out / "audit.json", result)
        print(json.dumps({"audit": "GREEN", "steps": result["steps"], "counts": result["counts"]}))
        return 0
    except Exception as exc:
        # Partial normalized rows are explicitly untrusted, never green output.
        failure = {"schema": "eab.m4b-replay.v1", "audit": "RED",
                   "snapshot": str(args.snapshot), "exception": type(exc).__name__, "error": str(exc),
                   "normalized_file_untrusted": normalized.name}
        try:
            require(outputs_safe and not _same_file(args.snapshot, audit), "unsafe audit output; preserved input and existing outputs")
            write_json(audit, failure)
        except (OSError, ValueError) as report_error:
            print(f"M4b RED audit file unavailable: {report_error}", file=sys.stderr)
        print(f"M4b audit RED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
