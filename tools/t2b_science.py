"""Bounded WO-T2b scientific searches, with production-only evidence status.

The lower scan records successful cage certificates, not an inferred caging
threshold. Failed proposals never prove escape. Upper endpoints require the
existing exact escape verifier. Independent cage acceptance remains pending.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools"), str(ROOT / "tests")]

from eab.kernel2d.se2 import SE2Motion
from eab.kernel2d.se2_paths import SE2EscapePath, verify_se2_escape
from eab.kernel2d.translation_space import translation_component
from t2_se2_grid import CASES, propose as propose_escape
from t2b_cage_proposer import CageResources, encode, propose_cage, scientific_instance, write_json


def _log(output, **item):
    item["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with (output / "progress.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(encode(item), ensure_ascii=False) + "\n")
        stream.flush()
    print(json.dumps(encode(item), ensure_ascii=False), flush=True)


def _point(value):
    return tuple(F(v) for v in value)


def _ring(value):
    return tuple(_point(p) for p in value)


def _escape_path(candidate):
    pieces = candidate["pieces"]
    poses = [_ring(pieces[0]["start"])]
    motions = []
    for piece in pieces:
        if _ring(piece["start"]) != poses[-1]:
            raise ValueError("escape proposal is not exactly joined")
        poses.append(_ring(piece["end"]))
        motions.append(SE2Motion(F(piece["u1"]), _point(piece["translation"]), _point(piece["center"])))
    return SE2EscapePath(tuple(poses), tuple(motions)), tuple(_point(p) for p in candidate["ray_path"])


def _verify_escape(instance, candidate):
    if _ring(candidate["moving"]) != instance["moving"] or tuple(_ring(p) for p in candidate["obstacles"]) != instance["obstacles"]:
        raise AssertionError("escape source geometry differs from independent generation")
    path, ray = _escape_path(candidate)
    start = time.perf_counter()
    result = verify_se2_escape(instance["moving"], instance["obstacles"], path, ray)
    record = {"valid": result.valid, "reason": result.reason,
              "checked_segments": result.checked_segments, "checked_pairs": result.checked_pairs,
              "ray_valid": bool(result.ray_verification and result.ray_verification.valid),
              "seconds": time.perf_counter()-start}
    return record


def _search_lower(case, output, *, exponent, seconds, disk_only):
    identifier = case[0]
    denominator = 2**exponent
    top = int(F(case[6])*denominator)
    coarse = max(1, denominator//32)
    mode = "disk" if disk_only else "cage"
    probes = []
    cache = {}

    def query(tick):
        if tick in cache:
            return cache[tick]
        delta = F(tick, denominator)
        instance, center = scientific_instance(identifier, delta)
        result = propose_cage(instance, center=center, disk_only=disk_only,
                             resources=CageResources(max_seconds=seconds, max_intervals=8,
                                                     max_loop_vertices=513, max_cap_steps=64))
        accepted = result["status"] == "CERTIFIED_CAGE"
        translation = None
        if accepted:
            check = translation_component(instance["moving"], instance["obstacles"])
            translation = check.status
            if check.status != "TRAPPED_TRANSLATION":
                raise AssertionError("accepted SE2 cage lacks consistent translation trapping")
        row = {"tick": tick, "delta": delta, "status": result["status"],
               "translation_status": translation, "diagnostic": result["diagnostic"],
               "last_attempt": result["attempts"][-1] if result["attempts"] else None}
        probes.append(row)
        cache[tick] = (accepted, instance, result)
        _log(output, case=identifier, phase="lower_probe", mode=mode, **row)
        return cache[tick]

    if not query(0)[0]:
        return {"status": "NO_CERTIFIED_LOWER", "probes": probes}, None, None
    low, high = 0, None
    ticks = list(range(coarse, top+1, coarse))
    if top not in ticks:
        ticks.append(top)
    for tick in ticks:
        if query(tick)[0]:
            low = tick
        else:
            high = tick
            break
    if high is not None:
        while high-low > 1:
            middle = (low+high)//2
            if query(middle)[0]:
                low = middle
            else:
                high = middle
    accepted, instance, result = cache[low]
    assert accepted
    record = {"status": "CERTIFIED_LOWER_PRODUCTION_ONLY", "delta": F(low, denominator),
              "grid_exponent": exponent, "first_unproved_delta": F(high, denominator) if high is not None else None,
              "failure_is_not_upper_bound": True, "probes": probes,
              "diagnostic": result["diagnostic"]}
    return record, instance, result["certificate"]


def _search_upper(case, lower, output, *, attempts, max_grid_cells):
    identifier = case[0]
    initial = F(case[6])
    source = Path("D:/eab-evidence/reports/codex/T2a_evidence/certificates") / (identifier+".json")
    candidate = json.loads(source.read_text(encoding="utf-8"))
    instance, _ = scientific_instance(identifier, initial)
    verification = _verify_escape(instance, candidate)
    if not verification["valid"]:
        raise AssertionError("accepted T2a starting escape fails present exact verification")
    best = candidate
    best_delta = initial
    probes = [{"delta": initial, "kind": "T2a_start_reverified", "verification": verification,
               "source_file": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}]
    _log(output, case=identifier, phase="upper_start", **probes[-1])
    bottom = lower
    for index in range(attempts):
        delta = (bottom+best_delta)/2
        row = list(case)
        row[6] = str(delta)
        destination = output / identifier / ("escape_proposal_"+str(index+1))
        destination.mkdir(parents=True, exist_ok=False)
        started = time.perf_counter()
        proposed = propose_escape(tuple(row), (F(1, 50),), destination, max_grid_cells)
        record = {"delta": delta, "kind": "fresh_downward_bisection",
                  "proposal_status": proposed["status"], "proposal_seconds": time.perf_counter()-started,
                  "proposal_file": str(destination / (identifier+".json"))}
        if proposed["status"] == "PROPOSAL_UNVERIFIED":
            instance, _ = scientific_instance(identifier, delta)
            check = _verify_escape(instance, proposed)
            record["verification"] = check
            if check["valid"]:
                best_delta, best, verification = delta, proposed, check
            else:
                bottom = delta
        else:
            bottom = delta
        # This search lower endpoint is only a proposal-failure boundary;
        # it is NEVER substituted for the separately certified cage lower.
        record["failed_search_is_not_non_escape"] = True
        probes.append(record)
        _log(output, case=identifier, phase="upper_probe", **record)
    return {"delta": best_delta, "initial_delta": initial, "improved": best_delta < initial,
            "verification": verification, "probes": probes}, best


def _snapshot_source(output, source_commit):
    paths = sorted((ROOT / "src").rglob("*.py"))
    paths.extend(ROOT / name for name in (
        "tools/t2b_science.py", "tools/t2b_cage_proposer.py", "tools/t2_se2_grid.py",
        "tests/t2b_truth_geometry_prod.py", "tests/t2a_truth_geometry.py"))
    source = {}
    with zipfile.ZipFile(output / "tested_source.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            source[relative] = hashlib.sha256(data).hexdigest()
            archive.writestr(relative, data)
    write_json(output / "source_manifest.json", {"source_commit": source_commit,
                                                "tool_version": "t2b-science-1",
                                                "sha256": source})
    return source


def run(output, *, cases, exponent=8, seconds=2.0, upper_attempts=1,
        max_grid_cells=30000000, source_commit="NOT_RECORDED"):
    if not 1 <= exponent <= 20:
        raise ValueError("grid exponent must be in 1..20")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "state.json", {"complete": False, "phase": "STARTING",
                                       "acceptance": "production_only_pending_independent"})
    source = _snapshot_source(output, source_commit)
    started = time.perf_counter()
    rows = []
    for identifier in cases:
        case = next(row for row in CASES if row[0] == identifier)
        disk, disk_instance, disk_certificate = _search_lower(case, output, exponent=exponent,
                                                             seconds=seconds, disk_only=True)
        cage, instance, certificate = _search_lower(case, output, exponent=exponent,
                                                   seconds=seconds, disk_only=False)
        if certificate is None or disk_certificate is None:
            raise AssertionError("scientific input has no certified lower endpoint")
        upper, escape_candidate = _search_upper(case, cage["delta"], output,
                                               attempts=upper_attempts, max_grid_cells=max_grid_cells)
        if cage["delta"] >= upper["delta"]:
            raise AssertionError("strict cage and escape bracket endpoints overlap")
        out = output / identifier
        write_json(out / "instance.json", instance)
        write_json(out / "certificate.json", certificate)
        write_json(out / "disk_instance.json", disk_instance)
        write_json(out / "disk_certificate.json", disk_certificate)
        escape_instance, center = scientific_instance(identifier, upper["delta"])
        write_json(out / "escape_instance.json", escape_instance)
        write_json(out / "escape_candidate.json", escape_candidate)
        opposite = propose_cage(escape_instance, center=center,
                                resources=CageResources(max_seconds=seconds, max_intervals=8))
        if opposite["status"] == "CERTIFIED_CAGE":
            raise AssertionError("cage and escape certificates coexist at one input")
        width = upper["delta"]-cage["delta"]
        row = {"case_id": identifier, "element": case[4], "wall_erosion": case[5],
               "delta_disk": disk["delta"], "delta_cage": cage["delta"],
               "delta_escape": upper["delta"], "delta_translation_star": F(case[7]),
               "width": width, "relative_width_to_translation_star": width/F(case[7]),
               "relative_width_definition": "(delta_escape-delta_cage)/delta_translation_star",
               "intervals": len(certificate["intervals"]), "uses_caps": bool(certificate["caps"]),
               "acceptance": "production_only_pending_independent", "outside_bracket": "UNPROVED",
               "disk_scan": disk, "cage_scan": cage, "escape_scan": upper,
               "same_input_consistency": {"escape_endpoint_cage_search_status": opposite["status"],
                                          "every_accepted_cage_translation_trapped": True}}
        write_json(out / "summary.json", row)
        rows.append(row)
        write_json(output / "summary.json", {"complete": False, "rows": rows,
                                              "acceptance": "production_only_pending_independent"})
        _log(output, case=identifier, phase="case_complete", delta_disk=row["delta_disk"],
             delta_cage=row["delta_cage"], delta_escape=row["delta_escape"], width=width)
    changed = [name for name, sha in source.items() if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != sha]
    if changed:
        write_json(output / "state.json", {"complete": False, "phase": "INVALID_SOURCE_CHANGED",
                                           "changed_files": changed})
        raise RuntimeError("scientific run invalid: recorded source changed during execution")
    summary = {"complete": True, "rows": rows, "seconds": time.perf_counter()-started,
               "acceptance": "production_only_pending_independent",
               "source_commit": source_commit, "source_bytes_unchanged": True,
               "configuration": {"grid_exponent": exponent, "proposal_seconds": seconds,
                                 "upper_attempts": upper_attempts, "max_grid_cells": max_grid_cells}}
    write_json(output / "summary.json", summary)
    write_json(output / "state.json", {"complete": True, "phase": "FINISHED",
                                       "acceptance": "production_only_pending_independent"})
    manifest = []
    for path in sorted(output.rglob("*")):
        if path.is_file():
            manifest.append({"path": path.relative_to(output).as_posix(),
                             "size": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    write_json(output / "artifact_manifest.json", manifest)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cases", nargs="+", default=[case[0] for case in CASES])
    parser.add_argument("--grid-exponent", type=int, default=8)
    parser.add_argument("--proposal-seconds", type=float, default=2.0)
    parser.add_argument("--upper-attempts", type=int, default=1)
    parser.add_argument("--max-grid-cells", type=int, default=30000000)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    result = run(args.output, cases=args.cases, exponent=args.grid_exponent,
                 seconds=args.proposal_seconds, upper_attempts=args.upper_attempts,
                 max_grid_cells=args.max_grid_cells, source_commit=args.source_commit)
    print(json.dumps({"complete": result["complete"], "cases": len(result["rows"]),
                      "seconds": result["seconds"], "acceptance": result["acceptance"]}))


if __name__ == "__main__":
    main()
