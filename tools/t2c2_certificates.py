"""WO-T2c2 finite certificate proposals with explicit rational transfer.

The unchanged verifiers accept rational input, not Q(sqrt(5)) coordinates.
Every bundle therefore distinguishes its algebraic target from the rational
instance actually checked. A cage for a smaller body transfers to the target;
an escape for a larger body transfers to the target. No rounded input is
labelled as direct verification of the algebraic target. Test replay keeps
all semantic results, not timings or hashes of the current implementation.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction as F
import hashlib
import json
from math import isqrt
from pathlib import Path
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / name) for name in ("src", "tools", "tests")]

from eab.kernel2d.se2 import SE2Motion
from eab.kernel2d.se2_cage import verify_se2_cage
from eab.kernel2d.se2_paths import SE2EscapePath, verify_se2_escape
from eab.kernel2d.translation_space import translation_component
from t2a_oracle_audit import validate_escape_segments
import t2b_cage_proposer as old
import t2b_independent_cage_verifier as independent_cage


TOOL_VERSION = "t2c2-certificates-2"
ELEMENTS = {"square": ("k01", F(3, 2)), "octagon": ("k02", F(29, 24))}
SOURCE_FILES = (
    "tools/t2c2_certificates.py", "tools/t2b_cage_proposer.py",
    "tools/t2_se2_grid.py", "src/eab/kernel2d/se2_cage.py",
    "src/eab/kernel2d/se2_paths.py", "src/eab/kernel2d/erosion.py",
    "tests/t2b_independent_cage_verifier.py", "tests/t2a_oracle_audit.py",
    "tests/t2a_independent_oracle.py", "tests/m5a_independent_oracle.py",
    "docs/t2c2_knob_theorem.md", "docs/t2b_cage_lemma.md",
)


def canonical(value):
    """Only exact structured data: Fraction strings and dataclass fields."""
    return json.loads(json.dumps(value, default=str))


def json_text(value):
    return json.dumps(canonical(value), ensure_ascii=False, indent=2) + "\n"


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json_text(value))


def provenance():
    return {"tool_version": TOOL_VERSION,
            "source_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
            "source_archive_scope": "listed files only; not the complete transitive dependency closure",
            "files": [{"path": name,
                       "sha256": hashlib.sha256((ROOT / name).read_bytes()).hexdigest(),
                       "bytes": (ROOT / name).stat().st_size} for name in SOURCE_FILES]}


def archive_sources(output, source):
    destination = output / "listed_source.zip"
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for row in source["files"]:
            data = (ROOT / row["path"]).read_bytes()
            if hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise RuntimeError("source changed before archive: " + row["path"])
            archive.writestr(row["path"], data)
    with zipfile.ZipFile(destination) as archive:
        for row in source["files"]:
            if hashlib.sha256(archive.read(row["path"])).hexdigest() != row["sha256"]:
                raise AssertionError("archived source bytes failed readback")
    source["archive"] = {"path": destination.name, "bytes": destination.stat().st_size,
                         "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()}


def numeric_input_audit(value):
    """Audit actual verifier inputs, never wall-clock diagnostic metadata."""
    pending = [value]
    counts = {"integer": 0, "fraction": 0, "string": 0, "null": 0,
              "float": 0, "nonfinite_string": 0}
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, (list, tuple)):
            pending.extend(item)
        elif isinstance(item, F):
            counts["fraction"] += 1
        elif type(item) is int:
            counts["integer"] += 1
        elif isinstance(item, str):
            counts["string"] += 1
            if item.lower() in ("nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"):
                raise ValueError("nonfinite string in actual verifier input")
        elif item is None:
            counts["null"] += 1
        else:
            raise TypeError("nonexact leaf in actual verifier input: " + type(item).__name__)
    return {"valid": True, "counts": counts,
            "scope": "actual geometry and certificate/path inputs; diagnostic metadata excluded"}


def check_sources(source):
    changed = [row["path"] for row in source["files"]
               if hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() != row["sha256"]]
    if changed:
        raise RuntimeError("source changed during run; entire run invalid: " + repr(changed))


def sqrt5_bounds(bits=48):
    denominator = 2 ** bits
    numerator = isqrt(5 * denominator * denominator)
    if not numerator * numerator < 5 * denominator * denominator < (numerator + 1) ** 2:
        raise AssertionError("strict integer sqrt5 enclosure failed")
    return F(numerator, denominator), F(numerator + 1, denominator)


def proxy_metadata(element, k, kind):
    """Directed rational witnesses; sqrt5 inequalities are integer exact."""
    if kind not in ("cage", "escape") or k < 1:
        raise ValueError("expected cage/escape and positive k")
    _, h = ELEMENTS[element]
    s0, s1 = sqrt5_bounds()
    low, high = (4 - s1) / (4 * h), (4 - s0) / (4 * h)
    epsilon = F(1, 2 ** k)
    if not 0 < high - low < epsilon:
        raise AssertionError("algebraic enclosure is not narrower than offset")
    sign = -1 if kind == "cage" else 1
    verified = high - epsilon if kind == "cage" else low + epsilon
    if not 0 < verified < F(1, 2) / h:
        raise AssertionError("proxy leaves the intended translation-trapped range")
    return {"target_delta": {"a": 1 / h + sign * epsilon,
                              "b": -F(1, 4) / h, "radicand": 5},
            "target_expression": "(4-sqrt(5))/(4*h)" + ("-" if sign < 0 else "+") + "2^-" + str(k),
            "h": h, "epsilon": epsilon, "verified_delta": verified,
            "sqrt5_bounds": [s0, s1], "critical_delta_bounds": [low, high],
            "direct_algebraic_instance_verification": False,
            "transfer": {
                "kind": "erosion_nested_inclusion_with_fixed_obstacles",
                "verified_vs_target": ">" if kind == "cage" else "<",
                "moving_subset": "verified_in_target" if kind == "cage" else "target_in_verified",
                "conclusion": "cage_transfers_to_larger_target" if kind == "cage" else "escape_transfers_to_smaller_target",
                "obstacles_unchanged": True,
                "strict_order_evidence": "integer sqrt5 bounds and affine delta formula",
            }}


def circle_polygon(radius):
    """Rational circle samples with exactly checked inradius above 1/2."""
    if radius <= F(1, 2):
        raise ValueError("disk radius must exceed half neck width")
    count = 1
    while 4 * radius * radius * count * count <= count * count + 1:
        count *= 2
    quarter = []
    for j in range(count):
        u = F(j, count)
        quarter.append((radius * (1 - u * u) / (1 + u * u),
                        radius * 2 * u / (1 + u * u)))
    points = []
    for _ in range(4):
        points.extend(quarter)
        quarter = [(-y, x) for x, y in quarter]
    if not all(x * x + y * y == radius * radius for x, y in points):
        raise AssertionError("circle sample does not lie on its exact circle")
    inradius_squared = min((a[0] * b[1] - a[1] * b[0]) ** 2 /
                           ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)
                           for a, b in zip(points, points[1:] + points[:1]))
    if inradius_squared <= F(1, 4):
        raise AssertionError("inscribed polygon cannot block the neck")
    return tuple(points), {"vertices": len(points), "quarter_samples": count,
                           "radius": radius, "inradius_squared": inradius_squared,
                           "inradius_lower_bound_squared": radius * radius * count * count / (count * count + 1)}


def instance_for(element, delta):
    return old.scientific_instance(ELEMENTS[element][0], delta)[0]


def cage_bundle(element, k, output, *, max_seconds=300):
    metadata = proxy_metadata(element, k, "cage")
    instance = instance_for(element, metadata["verified_delta"])
    center = (F(0), F(1))
    parts = old._partition(instance["moving"])
    obstacles = tuple({"obstacle": j, "ring": part}
                      for j, ring in enumerate(instance["obstacles"])
                      for part in old._partition(ring))
    disk = old._disk(parts, center)
    if disk is None:
        raise AssertionError("no invariant host disk")
    disk["polygon"], circle = circle_polygon(disk["radius"])
    base = old._base_certificate(instance, center, parts, obstacles, disk)
    resources = old.CageResources(max_seconds=max_seconds, max_loop_vertices=4097,
                                  max_refinements=8)
    deadline = time.perf_counter() + max_seconds
    certificate, reason = old._disk_candidate(base, resources, deadline)
    if certificate is None:
        raise RuntimeError("disk-only proposal UNPROVED: " + str(reason))
    old._check_candidate_resources(certificate, resources, deadline)
    if certificate["caps"] or any(piece != {"kind": "disk"}
                                   for item in certificate["intervals"] for piece in item["pieces"]):
        raise AssertionError("not an invariant-disk-only closed chain")
    output.mkdir(parents=True, exist_ok=False)
    input_audit = numeric_input_audit({"instance": instance, "certificate": certificate})
    write_json(output / "numeric_input_audit.json", input_audit)
    write_json(output / "instance.json", instance)
    write_json(output / "certificate.json", certificate)
    instance_text = (output / "instance.json").read_text("utf-8")
    certificate_text = (output / "certificate.json").read_text("utf-8")
    production = verify_se2_cage(instance_text, certificate_text)
    independent = independent_cage._load_result(output / "instance.json", output / "certificate.json")
    expected = {"production": canonical(asdict(production)), "independent": independent}
    write_json(output / "verification.json", expected)
    if production.valid != independent["valid"]:
        raise RuntimeError("finite cage verifier disagreement; preserve this run")
    if not production.valid or not independent["valid"]:
        raise RuntimeError("disk candidate rejected by both checkers")
    translation = translation_component(instance["moving"], instance["obstacles"])
    if translation.status != "TRAPPED_TRANSLATION":
        raise RuntimeError("cage contradicts translation classification")
    bundle = {"id": element + "_cage_k" + str(k), "element": element, "k": k,
              "kind": "cage", "metadata": metadata, "circle": circle,
              "instance_text": instance_text, "certificate_text": certificate_text,
              "expected": expected, "translation_result": canonical(asdict(translation)),
              "numeric_input_audit": input_audit,
              "independent_entry": "load_json(instance.json), load_json(certificate.json)"}
    write_json(output / "bundle.json", bundle)
    return bundle


def path_candidate(instance):
    """Theorem-informed proposal, subsequently checked over complete segments."""
    s0, _ = sqrt5_bounds()
    specs = ((2 - s0, (F(0), F(0)), (F(0), F(1))),
             (F(0), (F(0), F(4)), (F(0), F(1))))
    current = instance["moving"]
    pieces = []
    for spec in specs:
        motion = SE2Motion(*spec)
        following = tuple(motion.endpoint(point) for point in current)
        pieces.append({"start": current, "end": following, "u1": spec[0],
                       "translation": spec[1], "center": spec[2]})
        current = following
    return {"moving": instance["moving"], "obstacles": instance["obstacles"],
            "pieces": pieces, "ray_path": ((F(0), F(0)), (F(0), F(100)))}


def decode_candidate(candidate):
    moving = tuple(tuple(F(x) for x in point) for point in candidate["moving"])
    obstacles = tuple(tuple(tuple(F(x) for x in point) for point in ring)
                      for ring in candidate["obstacles"])
    poses, motions, specs = [moving], [], []
    for piece in candidate["pieces"]:
        if tuple(tuple(F(x) for x in point) for point in piece["start"]) != poses[-1]:
            raise ValueError("candidate is discontinuous")
        spec = (F(piece["u1"]), tuple(F(x) for x in piece["translation"]),
                tuple(F(x) for x in piece["center"]))
        specs.append(spec)
        motions.append(SE2Motion(*spec))
        poses.append(tuple(tuple(F(x) for x in point) for point in piece["end"]))
    ray = tuple(tuple(F(x) for x in point) for point in candidate["ray_path"])
    return moving, obstacles, SE2EscapePath(tuple(poses), tuple(motions)), tuple(specs), ray


def audit_path(candidate):
    moving, obstacles, path, specs, ray = decode_candidate(candidate)
    production = verify_se2_escape(moving, obstacles, path, ray)
    independent = validate_escape_segments(moving, obstacles, specs, ray)
    expected = {"production": canonical(asdict(production)), "independent": independent}
    # Production stops at first occupied segment. Compare every pair it did
    # inspect to the independently checked full finite trajectory.
    for i, row in enumerate(production.segment_results):
        for j, result in enumerate(row):
            other = next(item for item in independent["pairs"]
                         if item["kind"] == "se2" and item["segment"] == i and item["obstacle"] == j)
            for field in ("status", "initial_state", "end_state", "immediate", "touches_end"):
                if getattr(result, field) != other[field]:
                    raise RuntimeError("finite escape verifier disagreement: " + json_text(expected))
            for field in ("incidences", "features"):
                if sorted(canonical(getattr(result, field))) != sorted(canonical(other[field])):
                    raise RuntimeError("finite feature verifier disagreement: " + json_text(expected))
            first_time, other_time = result.exact_time, other["exact_time"]
            if (first_time is None) != (other_time is None):
                raise RuntimeError("finite entrance-time verifier disagreement: " + json_text(expected))
            if first_time is not None:
                # The proposed turn is free; all occupied pieces are pure
                # translations and must have rational event times. An
                # unexpected nonrational time is a stop, never rounded.
                if getattr(first_time, "rational", None) is None or other_time["rational"] is None:
                    raise RuntimeError("unexpected nonrational translation event; preserve evidence")
                if first_time.rational != F(other_time["rational"]):
                    raise RuntimeError("finite entrance-time verifier disagreement: " + json_text(expected))
    if production.valid and not independent["valid"]:
        raise RuntimeError("finite escape verifier disagreement: " + json_text(expected))
    if independent["infinite_ray_verified"]:
        raise AssertionError("unchanged finite oracle scope unexpectedly changed")
    return expected


def independent_tail_check(independent, obstacles, ray):
    """Separate exact coordinate proof; not a claim made by the old oracle."""
    endpoint = tuple(tuple(F(x) for x in point) for point in independent["final_endpoint"])
    lowest = min(point[1] for point in endpoint)
    highest = max(point[1] for ring in obstacles for point in ring)
    upward = ray[-1][0] == ray[-2][0] and ray[-1][1] > ray[-2][1]
    valid = upward and lowest > highest
    return {"valid": valid, "method": "independent_oracle_endpoint_plus_exact_upward_halfplane",
            "endpoint_source": "WO-T2a independent rational ring_at, not production poses",
            "lowest_endpoint_y": lowest, "highest_obstacle_y": highest,
            "strict_vertical_clearance": lowest - highest, "ray_direction": [0, 1],
            "old_oracle_infinite_ray_verified": independent["infinite_ray_verified"]}


def escape_bundle(element, k, output):
    metadata = proxy_metadata(element, k, "escape")
    instance = instance_for(element, metadata["verified_delta"])
    candidate = path_candidate(instance)
    output.mkdir(parents=True, exist_ok=False)
    input_audit = numeric_input_audit({"instance": instance, "candidate": candidate})
    write_json(output / "numeric_input_audit.json", input_audit)
    write_json(output / "instance.json", instance)
    write_json(output / "candidate.json", candidate)
    expected = audit_path(candidate)
    write_json(output / "verification.json", expected)
    if not expected["production"]["valid"] or not expected["independent"]["valid"]:
        raise RuntimeError("theorem-informed finite escape proposal rejected")
    tail = independent_tail_check(expected["independent"], instance["obstacles"], candidate["ray_path"])
    if not tail["valid"]:
        raise RuntimeError("independent infinite-tail halfplane supplement failed")
    lower_metadata = proxy_metadata(element, k, "cage")
    lower_instance = instance_for(element, lower_metadata["verified_delta"])
    lower_candidate = path_candidate(lower_instance)
    lower_input_audit = numeric_input_audit({"instance": lower_instance, "candidate": lower_candidate})
    write_json(output / "lower_numeric_input_audit.json", lower_input_audit)
    if any((a["u1"], a["translation"], a["center"]) !=
           (b["u1"], b["translation"], b["center"])
           for a, b in zip(candidate["pieces"], lower_candidate["pieces"])):
        raise AssertionError("lower replay changed the motion parameters")
    write_json(output / "lower_instance.json", lower_instance)
    write_json(output / "lower_candidate.json", lower_candidate)
    lower_expected = audit_path(lower_candidate)
    write_json(output / "lower_verification.json", lower_expected)
    if lower_expected["production"]["valid"] or lower_expected["independent"]["valid"]:
        raise RuntimeError("same escape path did not collide on the smaller lower proxy")
    if not any(row["status"] != "FREE" for row in lower_expected["independent"]["pairs"]
               if row["kind"] == "se2"):
        raise AssertionError("lower replay failed without a finite rigid collision")
    lower_metadata["transfer"]["conclusion"] = "strict_collision_on_subset_transfers_to_larger_lower_target"
    bundle = {"id": element + "_escape_k" + str(k), "element": element, "k": k,
              "kind": "escape", "metadata": metadata,
              "instance_text": (output / "instance.json").read_text("utf-8"),
              "candidate_text": (output / "candidate.json").read_text("utf-8"),
              "expected": expected, "independent_tail": tail, "numeric_input_audit": input_audit,
              "replay_below": {"metadata": lower_metadata,
                  "numeric_input_audit": lower_input_audit,
                  "instance_text": (output / "lower_instance.json").read_text("utf-8"),
                  "candidate_text": (output / "lower_candidate.json").read_text("utf-8"),
                  "expected": lower_expected}}
    write_json(output / "bundle.json", bundle)
    return bundle


def journal(output, **record):
    record["epoch_diagnostic_only"] = time.time()
    with (output / "progress.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(canonical(record), ensure_ascii=False) + "\n")
        stream.flush()
    print(json.dumps(canonical(record), ensure_ascii=False), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--elements", nargs="+", choices=tuple(ELEMENTS), default=list(ELEMENTS))
    parser.add_argument("--cage-k", nargs="*", type=int, default=list(range(6, 13)))
    parser.add_argument("--escape-k", nargs="*", type=int, default=list(range(6, 25)))
    args = parser.parse_args(argv)
    output = args.output.resolve()
    allowed = Path("D:/eab-evidence/reports/codex/T2c2_evidence").resolve()
    if not output.is_relative_to(allowed) or output == allowed:
        raise ValueError("output must be a new child of the designated external evidence directory")
    output.mkdir(parents=True, exist_ok=False)
    source = provenance()
    archive_sources(output, source)
    write_json(output / "source_manifest.json", source)
    rows = []
    started = time.perf_counter()
    try:
        for element in args.elements:
            for kind, indices in (("cage", args.cage_k), ("escape", args.escape_k)):
                for k in indices:
                    if not 6 <= k <= (12 if kind == "cage" else 24):
                        raise ValueError("k outside the work-order range")
                    check_sources(source)
                    directory = output / element / (kind + "_k" + str(k).zfill(2))
                    journal(output, phase="begin", element=element, kind=kind, k=k)
                    began = time.perf_counter()
                    bundle = (cage_bundle if kind == "cage" else escape_bundle)(element, k, directory)
                    check_sources(source)
                    row = {"id": bundle["id"], "element": element, "kind": kind, "k": k,
                           "bundle": directory.relative_to(output).as_posix() + "/bundle.json",
                           "verified_delta": bundle["metadata"]["verified_delta"],
                           "target_delta": bundle["metadata"]["target_delta"],
                           "production_valid": bundle["expected"]["production"]["valid"],
                           "independent_valid": bundle["expected"]["independent"]["valid"],
                           "seconds_diagnostic_only": time.perf_counter() - began}
                    rows.append(row)
                    journal(output, phase="accepted", **row)
        if any(a["element"] == b["element"] and a["verified_delta"] == b["verified_delta"]
               and a["kind"] != b["kind"] for a in rows for b in rows):
            raise AssertionError("same rational delta has contradictory certificates")
        files = [{"path": p.relative_to(output).as_posix(), "bytes": p.stat().st_size,
                  "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in sorted(output.rglob("*")) if p.is_file() and p.suffix in (".json", ".zip")]
        result = {"schema": "eab.t2c2.finite-evidence/1", "status": "ACCEPTED_DIRECTED_RATIONAL_TRANSFERS",
                  "source": source, "cases": rows, "files": files,
                  "counts": {"cages": sum(row["kind"] == "cage" for row in rows),
                             "escapes": sum(row["kind"] == "escape" for row in rows)},
                  "direct_algebraic_instance_verification": False,
                  "seconds_diagnostic_only": time.perf_counter() - started}
        write_json(output / "manifest.json", result)
        journal(output, phase="complete", counts=result["counts"])
        return 0
    except BaseException as error:
        write_json(output / "invalid_run.json", {"status": "INVALID_ENTIRE_RUN",
                   "reason": type(error).__name__ + ": " + str(error), "completed_not_reused": rows})
        journal(output, phase="invalid_entire_run", reason=repr(error))
        raise


if __name__ == "__main__":
    raise SystemExit(main())
