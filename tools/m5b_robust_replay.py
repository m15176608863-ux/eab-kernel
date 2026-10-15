"""Full-history P1/P2 model comparison and conservative P3 tube certificates.

Only strict certificates contribute to robust conclusions. An unproved pair is
not evidence of actual model sensitivity. P3 exact transcendental first roots and
positive-radius penetration-exit ordering are intentionally not implemented.
All long rows go to ignored tmp; completion binds inputs and source twice.
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
import m5b_endpoint_replay as endpoint
from m5c_source_binding import runtime_source_hashes, assert_current_sources
from eab.kernel2d.dda_motion import dda_motion_from_z, p2_p3_bound, dda_first_entrance
from eab.kernel2d.motion import motion_first_entrance
from eab.kernel2d.model_robustness import chord_paths, dda_paths, swept_axis_bounds, separation_certificate, single_cover_certificate
from eab.kernel2d.g0_oracle import overlap

EVIDENCE = ROOT / "reports/codex/M5b_evidence"
TMP = ROOT / "reports/codex/M5c_evidence/tmp"
LEGACY = EVIDENCE / "legacy_inputs"
PHASES = ("raw_df05", "post_df06")


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name+".writing")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str)+"\n", encoding="utf-8")
    tmp.replace(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_hashes():
    return runtime_source_hashes(ROOT, __file__)


def input_hashes():
    return {p.relative_to(ROOT).as_posix(): sha(p) for directory in (endpoint.INPUTS, LEGACY)
            for p in sorted(directory.iterdir()) if p.is_file()}


def freeze_legacy():
    """Copy only canonicalized legacy rows; bind original snapshot hashes."""
    if LEGACY.exists():
        raise ValueError("legacy bundle exists; immutable input")
    manifest = json.loads((endpoint.INPUTS / "manifest.json").read_text(encoding="utf-8"))
    LEGACY.mkdir(parents=True)
    output = {"complete": False, "cases": {}}
    for case, expected in manifest["cases"].items():
        path = TMP / "endpoint_originals" / case / "shadow.jsonl"
        before = sha(path)
        if before != expected["source_hashes"]["shadow.jsonl"]:
            raise AssertionError("legacy source hash mismatch")
        frames = [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines()][1:-1]
        packed = []
        for frame in frames:
            groups = defaultdict(list)
            for block, vertex, _, _ in frame["geometry"]:
                groups[block].append(vertex)
            aliases, owners = {}, {}
            for block, ids in groups.items():
                aliases.update({v: v for v in ids[:-2]})
                aliases.update(zip(ids[-2:], ids[:2]))
                owners.update({v: block for v in ids})
            phases = {}
            for phase in PHASES:
                phases[phase] = [dict(raw=row, pair=sorted((owners[row[1]], owners[row[2]])),
                                     primary=["VE", aliases[row[1]], *sorted((aliases[row[2]], aliases[row[3]]))])
                                 for row in frame[phase]]
            packed.append(dict(step=frame["step"], **phases))
        if sha(path) != before or len(packed) != expected["steps"]:
            raise AssertionError("legacy source changed or incomplete")
        target = LEGACY / (case+".jsonl.gz")
        target.write_bytes(gzip.compress("".join(json.dumps(r, separators=(",", ":"))+"\n" for r in packed).encode(), mtime=0))
        if target.stat().st_size > 1_000_000:
            raise AssertionError("legacy input exceeds 1 MB")
        output["cases"][case] = dict(source_sha256=before, sha256=sha(target), steps=len(packed))
        write_json(LEGACY / "manifest.json", output)
    output["complete"] = True
    write_json(LEGACY / "manifest.json", output)


def prepare(row):
    start, end = endpoint.exact_points(row["start"]), endpoint.exact_points(row["end"])
    ids = tuple(row["vertex_ids"])
    area = sum(p[0]*q[1]-p[1]*q[0] for p, q in zip(start, start[1:]+start[:1]))
    if area < 0:
        start, end, ids = tuple(reversed(start)), tuple(reversed(end)), tuple(reversed(ids))
    z = tuple(F(x) for x in row["z"])
    model = dda_motion_from_z(start, z)
    if not model.orientation_preserving_sufficient:
        raise ValueError("full input outside P2 non-inversion domain")
    paths1, paths2 = chord_paths(start, end), dda_paths(start, model)
    enclosure = p2_p3_bound(start, model, z[2])
    bound = enclosure["position"]
    endpoint_parameter = enclosure["radius_l1"]*enclosure["parameter_angle"]
    residual = max(abs(model.endpoint(p)[k]-q[k]) for p, q in zip(start, end) for k in (0, 1))
    # Explicit model family: linear per-vertex endpoint correction s*e_i.
    # P3's own closure residual may exceed P2's by endpoint_parameter. At s=1
    # the half-angle parameter error remains, but the time-law error is zero.
    # The same conservative sum is charged to BOTH P1 and P2 certificates.
    return dict(start=start, end=end, ids=ids, motion=model, paths1=paths1, paths2=paths2,
                bound=bound, residual=residual, endpoint_parameter=endpoint_parameter,
                radius=bound+residual+endpoint_parameter,
                box1=swept_axis_bounds(paths1), box2=swept_axis_bounds(paths2))


def box_gap(a, b):
    return max(max(b[k][0]-a[k][1], a[k][0]-b[k][1]) for k in (0, 1))


def global_labels(labels, a, b):
    result = []
    for tag, i, j in labels:
        if tag == "VV":
            result.append(("VV", *sorted((a["ids"][i], b["ids"][j]))))
        else:
            vertex, edge, index = (a["ids"][i], b["ids"], j) if tag == "VE" else (b["ids"][j], a["ids"], i)
            result.append(("VE", vertex, *sorted((edge[index], edge[(index+1) % len(edge)]))))
    return tuple(sorted(set(result)))


def record(result, a, b):
    return dict(status=result.status, features=global_labels(result.features, a, b),
                time=None if result.exact_time is None else result.exact_time.certificate)


def _bracket(time_value):
    lo, hi = F(0), F(1)
    for _ in range(20):
        mid = (lo+hi)/2
        if time_value < mid:
            hi = mid
        else:
            lo = mid
    return lo, hi


def compare_pair(a, b):
    radius = a["radius"]+b["radius"]
    gaps = box_gap(a["box1"], b["box1"]), box_gap(a["box2"], b["box2"])
    empty = dict(status="no_contact", features=(), time=None)
    if min(gaps) > radius:
        return dict(classification="ROBUST_NO_CONTACT", same=True, p1=empty, p2=empty,
                    certificate=dict(gap_lower=gaps, radius_sum=radius), oracle_checked=False,
                    comparison_basis="CERTIFICATE_DIRECT", production_initial_crosschecked=False)
    state = overlap(a["start"], b["start"])
    if state == 1:
        value = dict(status="initial_overlap", features=(), time=None)
        return dict(classification="MODEL_SENSITIVE_OR_UNPROVED", reason="INITIAL_EXIT_ORDER_UNCERTIFIED",
                    same=True, p1=value, p2=value, initial_state=state, oracle_checked=True,
                    comparison_basis="CONSTRUCTED_INITIAL_OVERLAP", production_initial_crosschecked=False)
    one = motion_first_entrance(a["start"], b["start"], a["end"], b["end"])
    two = dda_first_entrance(a["start"], b["start"], a["motion"], b["motion"])
    if one.initial_state != state or two.initial_state != state:
        raise AssertionError("independent initial solid-state oracle mismatch")
    p1, p2 = record(one, a, b), record(two, a, b)
    same = p1["status"] == p2["status"] and p1["features"] == p2["features"]
    result = dict(classification="MODEL_SENSITIVE_OR_UNPROVED", reason="NO_SUFFICIENT_CERTIFICATE",
                  same=same, p1=p1, p2=p2, initial_state=state, oracle_checked=True,
                  comparison_basis="EXPLICIT_TRAJECTORY" if state == -1 else "CONSTRUCTED_INITIAL_CONTACT",
                  production_initial_crosschecked=True)
    if not same:
        result["reason"] = "OBSERVED_P1_P2_DIFFERENCE"
        return result
    if one.status == "no_contact":
        certificates = [separation_certificate(a[key], b[key], a["radius"], b["radius"], panels=2)
                        for key in ("paths1", "paths2")]
        if all(certificates):
            result.update(classification="ROBUST_NO_CONTACT", certificate=certificates)
            result.pop("reason", None)
        return result
    if state != -1 or len(one.features) != 1 or one.features != two.features or one.features[0][0] == "VV":
        return result
    bounds = (_bracket(one.exact_time), _bracket(two.exact_time))
    for pad in (F(1, 256), F(1, 1024), F(1, 4096)):
        bracket = max(F(0), min(x[0] for x in bounds)-pad), min(F(1), max(x[1] for x in bounds)+pad)
        certificates = [single_cover_certificate(a[key], b[key], one.features[0], bracket,
                                                 a["radius"], b["radius"], panels=4)
                        for key in ("paths1", "paths2")]
        if all(certificates):
            result.update(classification="ROBUST_SINGLE_FIRST_COVER", certificate=certificates)
            result.pop("reason", None)
            break
    return result


def canonical_legacy_rows(rows, block_rows):
    """Normalize both tuple7 slots from frozen consecutive padded vertex IDs.

    Check the primary against its independently frozen canonical field. The two
    wrap aliases follow the retained ring, as checked at input freezing.
    """
    aliases, owners, edges = {}, {}, set()
    for block_index, block in enumerate(block_rows):
        ids = block["vertex_ids"]
        if ids != list(range(ids[0], ids[0]+len(ids))):
            raise ValueError("frozen ring IDs must preserve the consecutive padded order")
        aliases.update((v, v) for v in ids)
        aliases.update(zip((ids[-1]+1, ids[-1]+2), ids[:2]))
        owners.update((v, block_index) for v in ids)
        edges.update(tuple(sorted((v, w))) for v, w in zip(ids, ids[1:]+ids[:1]))
    normalized = []
    for row in rows:
        raw = row["raw"]
        primary = ("VE", aliases[raw[1]], *sorted((aliases[raw[2]], aliases[raw[3]])))
        if primary != tuple(row["primary"]):
            raise AssertionError("primary alias reconstruction differs from frozen canonical reference")
        secondary, shared_edge = None, None
        # df.c uses m6>0 for the mtype=0 common-edge slot. Other VE rows use
        # m4/m5 for lock-length hints, not a complete vertex-edge reference.
        # VV uses has_second=m4>0; its m5/m6 may be the actual vertex ID zero.
        present = (raw[0] == 1 and raw[4] > 0) or (raw[0] == 0 and raw[6] > 0)
        if present:
            slot = ("VE", aliases[raw[4]], *sorted((aliases[raw[5]], aliases[raw[6]])))
            v, e0, e1 = slot[1:]
            pair_owners = {owners[primary[1]], owners[primary[2]]}
            if (e0 == e1 or (e0, e1) not in edges or owners[e0] != owners[e1]
                    or owners[v] == owners[e0] or {owners[v], owners[e0]} != pair_owners):
                raise ValueError("complete legacy slot is not an opposite-block vertex and nondegenerate adjacent edge")
            if raw[0] == 1:
                secondary = slot
            else:
                shared_edge = slot
        normalized.append(dict(row, secondary=secondary, shared_edge=shared_edge))
    return normalized


def legacy_counts(result, rows):
    """Count primary, VV secondary and common-edge slots separately.

    ALL includes all valid slots; FORMAL_ALL excludes VE common-edge candidates.

    Historical FIRST_COVER_NOT_SELECTED retains PRIMARY-only meaning. It is
    never a missing-pair assertion; ALL_FIRST_COVER_NOT_SELECTED is separate.
    """
    counts = Counter()
    for phase in PHASES:
        selected = rows[phase]
        secondary = [tuple(row["secondary"]) for row in selected if row.get("secondary") is not None]
        shared_edge = [tuple(row["shared_edge"]) for row in selected if row.get("shared_edge") is not None]
        counts[phase+":PRIMARY_REFERENCE_TOTAL"] += len(selected)
        counts[phase+":SECONDARY_REFERENCE_TOTAL"] += len(secondary)
        counts[phase+":SHARED_EDGE_SLOT_TOTAL"] += len(shared_edge)
        if result["classification"] == "ROBUST_NO_CONTACT":
            counts[phase+":ROBUST_NO_CONTACT_REFERENCE"] += len(selected)
            counts[phase+":ROBUST_NO_CONTACT_SECONDARY_REFERENCE"] += len(secondary)
            counts[phase+":ROBUST_NO_CONTACT_SHARED_EDGE_SLOT"] += len(shared_edge)
        elif result["classification"] == "ROBUST_SINGLE_FIRST_COVER":
            features = set(result["p1"]["features"])
            for row in selected:
                counts[phase+(":FIRST_COVER_MATCH" if tuple(row["primary"]) in features else ":OTHER_REFERENCE")] += 1
            for feature in secondary:
                counts[phase+(":SECONDARY_FIRST_COVER_MATCH" if feature in features else ":SECONDARY_OTHER_REFERENCE")] += 1
            for feature in shared_edge:
                counts[phase+(":SHARED_EDGE_FIRST_COVER_MATCH" if feature in features else ":SHARED_EDGE_OTHER_REFERENCE")] += 1
            formal_features = [tuple(row["primary"]) for row in selected]+secondary
            if not any(feature in features for feature in formal_features):
                counts[phase+":FORMAL_ALL_FIRST_COVER_NOT_SELECTED"] += 1
            all_features = formal_features+shared_edge
            if not any(feature in features for feature in all_features):
                counts[phase+":ALL_FIRST_COVER_NOT_SELECTED"] += 1
            if not selected:
                counts[phase+":ROBUST_CONTACT_MISSING_PAIR"] += 1
            if not any(tuple(row["primary"]) in features for row in selected):
                counts[phase+":ROBUST_FIRST_COVER_NOT_SELECTED"] += 1
        else:
            counts[phase+":UNPROVED_REFERENCE"] += len(selected)
            counts[phase+":UNPROVED_SECONDARY_REFERENCE"] += len(secondary)
            counts[phase+":UNPROVED_SHARED_EDGE_SLOT"] += len(shared_edge)
    return counts


def replay_case(case, out, expected_source, expected_inputs):
    if source_hashes() != expected_source or input_hashes() != expected_inputs:
        raise AssertionError("replay inputs/source changed before worker")
    directory = Path(out) / case
    directory.mkdir(exist_ok=False)
    frames = defaultdict(list)
    for row in endpoint.iter_inputs(case=case):
        frames[row["step"]].append(row)
    legacy_path = LEGACY / (case+".jsonl.gz")
    legacy = {r["step"]: r for r in (json.loads(line) for line in gzip.decompress(legacy_path.read_bytes()).decode().splitlines())}
    if set(frames) != set(legacy):
        raise AssertionError("legacy/endpoint step mismatch")
    counts, references, examples = Counter(), Counter(), {}
    started = time.perf_counter()
    raw = directory / "pairs.jsonl.gz"
    with gzip.open(raw, "wt", encoding="utf-8", newline="\n") as stream:
        for step, block_rows in frames.items():
            blocks = {row["block"]: prepare(row) for row in block_rows}
            ids = sorted(blocks)
            for index, ida in enumerate(ids):
                for idb in ids[index+1:]:
                    a, b = blocks[ida], blocks[idb]
                    result = compare_pair(a, b)
                    selected = {phase: canonical_legacy_rows(
                        [r for r in legacy[step][phase] if r["pair"] == [ida, idb]], block_rows) for phase in PHASES}
                    reference = legacy_counts(result, selected)
                    references.update(reference)
                    counts["pairs"] += 1
                    counts[result["classification"]] += 1
                    basis = result["comparison_basis"]
                    counts["comparison_basis:"+basis] += 1
                    if basis == "EXPLICIT_TRAJECTORY":
                        counts["p1_p2_explicit_same" if result["same"] else "p1_p2_explicit_different"] += 1
                        counts["explicit_new_contact_pairs"] += result["p1"]["status"] != "no_contact"
                    counts["independent_initial_state_evaluations"] += result["oracle_checked"]
                    counts["production_initial_state_crosschecks"] += result["production_initial_crosschecked"]
                    if result.get("reason") and result["classification"] == "MODEL_SENSITIVE_OR_UNPROVED":
                        counts[result["reason"]] += 1
                    packed = dict(case=case, step=step, pair=[ida, idb], result=result, legacy_counts=dict(reference))
                    stream.write(json.dumps(packed, default=str, separators=(",", ":"))+"\n")
                    key = result["classification"] if result["classification"] != "MODEL_SENSITIVE_OR_UNPROVED" else result["reason"]
                    if key not in examples:
                        examples[key] = dict(**packed, blocks=[next(r for r in block_rows if r["block"] == bid) for bid in (ida, idb)], legacy=selected)
            counts["steps"] += 1
            counts["blocks"] += len(blocks)
            if step % 5 == 0 or step == len(frames):
                write_json(directory / "progress.json", dict(complete=False, step=step, counts=dict(counts), seconds=time.perf_counter()-started))
    final_sources = source_hashes()
    assert_current_sources(ROOT, expected_source, final_sources)
    if input_hashes() != expected_inputs:
        raise AssertionError("replay inputs changed during worker")
    result = dict(case=case, complete=True, counts=dict(counts), references=dict(references), examples=examples,
                  raw_sha256=sha(raw), seconds=time.perf_counter()-started,
                  source_hashes=expected_source, source_hashes_end=final_sources)
    write_json(directory / "summary.json", result)
    write_json(directory / "progress.json", dict(complete=True, counts=dict(counts)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-legacy", action="store_true")
    parser.add_argument("--name")
    parser.add_argument("--cases", nargs="*")
    parser.add_argument("--publish", action="store_true", help="archive previous bytes and publish a complete fresh batch")
    args = parser.parse_args()
    if args.freeze_legacy:
        freeze_legacy()
        return 0
    if not args.name or Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("fresh single directory --name required")
    os.environ["TEMP"] = os.environ["TMP"] = str(TMP)
    out = TMP / args.name
    out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((endpoint.INPUTS / "manifest.json").read_text(encoding="utf-8"))
    cases = args.cases or sorted(manifest["cases"])
    if len(set(cases)) != len(cases) or any(case not in manifest["cases"] for case in cases):
        raise ValueError("unique known cases required")
    target = EVIDENCE / "robust_summary.json"
    previous = target.read_bytes() if target.exists() else None
    backup = ROOT / "reports/codex/M5c_evidence" / (args.name+"_robust_summary_before.json")
    if args.publish:
        if set(cases) != set(manifest["cases"]):
            raise ValueError("publication requires every case")
        if backup.exists():
            raise ValueError("publication backup exists; use a fresh run name")
        if previous is not None:
            backup.write_bytes(previous)
    sources, inputs = source_hashes(), input_hashes()
    started = time.perf_counter()
    results, counts, references = {}, Counter(), Counter()
    write_json(out / "progress.json", dict(complete=False, completed=[], interruption_invalidates=True))
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(replay_case, case, out, sources, inputs): case for case in cases}
        for future in as_completed(futures):
            result = future.result()
            results[result["case"]] = result
            counts.update(result["counts"])
            references.update(result["references"])
            write_json(out / "progress.json", dict(complete=False, completed=sorted(results), counts=dict(counts)))
            print(result["case"], result["counts"], flush=True)
    final_sources = source_hashes()
    assert_current_sources(ROOT, sources, final_sources)
    if input_hashes() != inputs:
        raise AssertionError("full batch input change invalidates result")
    full = set(cases) == set(manifest["cases"])
    if full and (counts["steps"], counts["blocks"], counts["pairs"]) != (1810, 15220, 64010):
        raise AssertionError("full-history coverage mismatch")
    if counts["ROBUST_NO_CONTACT"]+counts["ROBUST_SINGLE_FIRST_COVER"]+counts["MODEL_SENSITIVE_OR_UNPROVED"] != counts["pairs"]:
        raise AssertionError("classification partition mismatch")
    result = dict(schema="eab.m5b-robust-model-replay.v1", complete=True, full_history=full,
                  counts=dict(counts), references=dict(references), cases=results,
                  source_hashes=sources, source_hashes_end=final_sources,
                  source_binding="runtime-loaded-repository-closure-start-and-end.v1",
                  input_hashes=inputs, seconds=time.perf_counter()-started,
                  limits=["P3 compared by certified tube only, no transcendental root solving",
                          "positive-radius initial shortest-exit ordering is unproved",
                          "MODEL_SENSITIVE_OR_UNPROVED includes unknown, not measured sensitivity"],
                  raw_directory=out.relative_to(ROOT).as_posix())
    write_json(out / "summary.json", result)
    write_json(out / "progress.json", dict(complete=True, counts=dict(counts)))
    if full and args.publish:
        if (target.read_bytes() if target.exists() else None) != previous:
            raise ValueError("publication target changed during real recomputation")
        write_json(target, result)
    print("M5B_MODEL_REPLAY_COMPLETE", dict(counts), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
