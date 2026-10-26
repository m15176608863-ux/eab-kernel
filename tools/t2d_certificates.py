"""WO-T2d untrusted finite proposals and unchanged dual-verifier orchestration.

The rational verifier inputs are explicitly distinguished from algebraic
targets. No pickle deserializer is used: the optional isolated inspection
reports opcodes only. Wall-clock values are diagnostics, never predicates.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction as F
import hashlib
import json
from math import isqrt
import math
from pathlib import Path
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT)] + [str(ROOT / name) for name in ("src", "tools", "tests")]

from eab.adapters.tia2d import tolerance_knob
from eab.kernel2d.erosion import erode_polygon_exact, octagon_element, square_element
from eab.kernel2d.se2 import SE2Motion
from eab.kernel2d.se2_paths import SE2EscapePath, verify_se2_escape
from eab.kernel2d.se2_cage import verify_se2_cage
from eab.kernel2d.translation_space import translation_component
from t2a_oracle_audit import validate_escape_segments
import t2b_cage_proposer as old
import t2b_independent_cage_verifier as independent_cage
from t2c2_certificates import circle_polygon, numeric_input_audit
from tests.t2d_knob_family_exact import family_geometry, family_values
from tests.t2d_sections_exact import eroded_polygon


TOOL_VERSION = "t2d-certificates-1"
EVIDENCE = Path("D:/eab-evidence/reports/codex/T2d_evidence")
CENTER = (F(0), F(1))


def canonical(value):
    return json.loads(json.dumps(value, default=str))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(canonical(value), ensure_ascii=False, indent=2) + "\n")


def journal(output, **row):
    row["epoch_diagnostic_only"] = time.time()
    with (output / "progress.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(canonical(row), ensure_ascii=False) + "\n")
        stream.flush()
    print(json.dumps(canonical(row), ensure_ascii=False), flush=True)


def new_output(path):
    path = Path(path).resolve()
    if not path.is_relative_to(EVIDENCE.resolve()) or path == EVIDENCE.resolve():
        raise ValueError("new output must be a child of the T2d evidence directory")
    path.mkdir(parents=True, exist_ok=False)
    return path


def sqrt_bounds(q, bits=64):
    q = F(q)
    if q < 0 or bits < 1:
        raise ValueError("nonnegative radicand and positive precision required")
    denominator = 1 << bits
    n = isqrt(q.numerator * denominator * denominator // q.denominator)
    lo, hi = F(n, denominator), F(n + 1, denominator)
    assert lo * lo <= q < hi * hi
    return lo, hi


def proxy_metadata(critical, k, kind):
    a, b, q = (F(critical[key]) for key in ("a", "b", "q"))
    if kind not in ("cage", "escape") or k < 1:
        raise ValueError("positive offset and cage/escape kind required")
    root_lo, root_hi = sqrt_bounds(q)
    pair = (a + b * root_lo, a + b * root_hi)
    lo, hi = min(pair), max(pair)
    epsilon = F(1, 1 << k)
    assert hi - lo < epsilon / 1024
    sign = -1 if kind == "cage" else 1
    verified = hi - epsilon if kind == "cage" else lo + epsilon
    assert verified > 0
    return {
        "critical": critical, "target_delta": {"a": a + sign * epsilon, "b": b, "q": q},
        "epsilon": epsilon, "verified_delta": verified, "k": k,
        "sqrt_bounds": (root_lo, root_hi), "critical_bounds": (lo, hi),
        "direct_algebraic_instance_verification": False,
        "transfer": {
            "kind": "erosion_nested_inclusion_with_fixed_obstacles",
            "verified_vs_target": ">" if kind == "cage" else "<",
            "moving_subset": "verified_in_target" if kind == "cage" else "target_in_verified",
            "conclusion": "cage_transfers_to_larger_target" if kind == "cage" else "escape_transfers_to_smaller_target",
            "obstacles_unchanged": True,
        },
    }


def element_vertices(element):
    if element == "square":
        return square_element()
    if element == "octagon":
        return octagon_element()
    if element != "K16":
        raise ValueError("unknown tolerance element")
    points = [(sx * x, sy * y) for x, y in
              ((F(99, 101), F(20, 101)), (F(20, 101), F(99, 101)),
               (F(91, 109), F(60, 109)), (F(60, 109), F(91, 109)))
              for sx in (-1, 1) for sy in (-1, 1)]
    return old._hull(points)


def instance_for(n, element, delta):
    raw = tolerance_knob(segments=n, head_width=F(2), neck_width=F(1), height=F(2), wall=F(2))
    assert raw["moving"] == family_geometry(n)["A"], "independent section model differs from production raw body"
    moving = eroded_polygon(n, element, delta)
    return {"moving": moving, "obstacles": raw["obstacles"]}


def partition_with_core(n, element, delta, moving):
    """Propose eroded Q as central host; both checkers verify full partition.

    Each original convex partition cell is successively cut by Q's shifted
    halfplanes. Outside pieces are retained, the final inside cell omitted.
    Adding the one complete core replaces those disjoint inside fragments.
    No inclusion, area, or nonoverlap claim bypasses either V0 checker.
    """
    q = family_geometry(n)["Q"]
    result = erode_polygon_exact(q, delta, element_vertices(element))
    if result.status != "ACCEPTED":
        raise ValueError("convex Q erosion rejected")
    core = result.polygon
    pieces = [core]
    for triangle in old._partition(moving):
        remaining = triangle
        for a, b in zip(core, core[1:] + core[:1]):
            if not remaining:
                break
            nx, ny = b[1] - a[1], a[0] - b[0]
            bound = nx * a[0] + ny * a[1]
            outside = old._clip(remaining, -nx, -ny, -bound)
            if outside:
                pieces.append(outside)
            remaining = old._clip(remaining, nx, ny, bound)
    return tuple(pieces)


def _cell_parameter_interval(cell, first, last):
    """Open interval where one proposed segment lies in a convex open cell."""
    lo, hi = F(-1), F(2)
    dx, dy = last[0] - first[0], last[1] - first[1]
    for nx, ny, bound in cell[2]:
        height = nx * first[0] + ny * first[1] + bound
        slope = nx * dx + ny * dy
        if not slope:
            if height <= 0:
                return None
        elif slope > 0:
            lo = max(lo, -height / slope)
        else:
            hi = min(hi, -height / slope)
    return (lo, hi) if lo < hi and hi > 0 and lo < 1 else None


def _covered_edge(first, last, cells):
    intervals = [(bounds[0], bounds[1], cell) for cell in cells
                 if (bounds := _cell_parameter_interval(cell, first, last)) is not None]
    eligible = [row for row in intervals if row[0] < 0 < row[1]]
    if not eligible:
        raise RuntimeError("proposed rectangle vertex is not strictly covered")
    chosen = max(eligible, key=lambda row: row[1])
    parameter, points, witnesses = F(0), [first], []
    while chosen[1] <= 1:
        next_cells = [row for row in intervals if row[0] < chosen[1] < row[1]]
        if not next_cells:
            raise RuntimeError("proposed rectangle edge has an uncovered gap")
        following = max(next_cells, key=lambda row: row[1])
        value = (max(parameter, following[0]) + chosen[1]) / 2
        point = tuple(a + value * (b - a) for a, b in zip(first, last))
        assert old._inside(chosen[2], points[-1]) and old._inside(chosen[2], point)
        points.append(point)
        witnesses.append(chosen[2][3])
        parameter, chosen = value, following
    assert old._inside(chosen[2], points[-1]) and old._inside(chosen[2], last)
    return points + [last], witnesses + [chosen[2][3]]


def rectangular_disk_candidate(n, base, resources, deadline):
    """Family-informed proposal only; unchanged V4/V5 check every segment."""
    disk = base["disk"]
    cells = old._cells((old._world(disk["polygon"], base["center"]),),
                       base["obstacle_pieces"], resources, deadline)
    top = (family_geometry(n)["neck_height"] + 2) / 2 - 1
    corners = ((F(-2), F(-1)), (F(2), F(-1)), (F(2), top), (F(-2), top), (F(-2), F(-1)))
    loop, witnesses = [corners[0]], []
    for first, last in zip(corners, corners[1:]):
        points, row = _covered_edge(first, last, cells)
        loop.extend(points[1:])
        witnesses.extend(row)
    loop = tuple(loop)
    interval = {"rho": F(0), "pieces": [{"kind": "disk"}], "loop": loop, "witnesses": witnesses}
    joined = [[[["disk"], witness[1]] for witness in witnesses]]
    return {**base, "intervals": [interval, dict(interval)],
            "links": [{"at": n, "chain": [loop, loop], "witnesses": joined} for n in (1, 2)]}


def cage_bundle(n, element, metadata, output, *, max_seconds=600):
    """Initially use the actual rational body, with disk-only barriers."""
    output = new_output(output)
    began = time.perf_counter()
    instance = instance_for(n, element, metadata["verified_delta"])
    geometry_seconds = time.perf_counter() - began
    write_json(output / "instance.json", instance)
    parts = partition_with_core(n, element, metadata["verified_delta"], instance["moving"])
    obstacles = tuple({"obstacle": j, "ring": part}
                      for j, ring in enumerate(instance["obstacles"]) for part in old._partition(ring))
    disk = old._disk(parts, CENTER)
    if disk is None or disk["radius"] <= F(1, 2):
        failure = {"status": "UNPROVED_HOST_DISK", "disk": disk, "moving_pieces": parts,
                   "geometry_seconds_diagnostic_only": geometry_seconds}
        write_json(output / "proposal_failure.json", failure)
        return failure
    disk["polygon"], circle = circle_polygon(disk["radius"])
    base = old._base_certificate(instance, CENTER, parts, obstacles, disk)
    resources = old.CageResources(max_seconds=max_seconds, max_loop_vertices=4097, max_refinements=8)
    deadline = time.perf_counter() + max_seconds
    certificate = rectangular_disk_candidate(n, base, resources, deadline)
    old._check_candidate_resources(certificate, resources, deadline)
    assert not certificate["caps"] and all(piece == {"kind": "disk"}
        for interval in certificate["intervals"] for piece in interval["pieces"])
    write_json(output / "certificate.json", certificate)
    input_audit = numeric_input_audit({"instance": instance, "certificate": certificate})
    production = verify_se2_cage((output / "instance.json").read_text("utf-8"),
                                 (output / "certificate.json").read_text("utf-8"))
    independent = independent_cage._load_result(output / "instance.json", output / "certificate.json")
    expected = {"production": asdict(production), "independent": independent}
    write_json(output / "verification.json", expected)
    if not production.valid or not independent["valid"]:
        raise RuntimeError("cage dual verification failed; full inputs retained")
    translation = translation_component(instance["moving"], instance["obstacles"])
    assert translation.status == "TRAPPED_TRANSLATION"
    bundle = {"schema": "eab.t2d.finite-bundle/1", "N": n, "element": element, "kind": "cage",
              "metadata": metadata, "circle": circle, "expected": expected,
              "instance_text": (output / "instance.json").read_text("utf-8"),
              "certificate_text": (output / "certificate.json").read_text("utf-8"),
              "translation_result": asdict(translation), "numeric_input_audit": input_audit,
              "geometry_construction": "independent exact section envelope of actual A; raw A bound to production generator",
              "independent_entry": "load_json(instance.json), load_json(certificate.json)",
              "geometry_seconds_diagnostic_only": geometry_seconds,
              "seconds_diagnostic_only": time.perf_counter() - began}
    write_json(output / "bundle.json", bundle)
    return bundle


def path_candidate(instance, specs):
    current, pieces = instance["moving"], []
    for spec in specs:
        motion = SE2Motion(*spec)
        following = tuple(motion.endpoint(point) for point in current)
        pieces.append({"start": current, "end": following, "u1": spec[0],
                       "translation": spec[1], "center": spec[2]})
        current = following
    return {**instance, "pieces": pieces, "ray_path": ((F(0), F(0)), (F(0), F(100)))}


def strip_specs(normal):
    mx, my = (F(x) for x in normal)
    lo, hi = sqrt_bounds(mx * mx + my * my)
    root = (lo + hi) / 2
    u = -my / (root + mx)
    return ((u, (F(0), F(0)), CENTER), (F(0), (F(0), F(4)), CENTER))


def verify_candidate(candidate):
    specs = tuple((piece["u1"], piece["translation"], piece["center"]) for piece in candidate["pieces"])
    poses = (candidate["moving"],) + tuple(piece["end"] for piece in candidate["pieces"])
    path = SE2EscapePath(poses, tuple(SE2Motion(*spec) for spec in specs))
    production = verify_se2_escape(candidate["moving"], candidate["obstacles"], path, candidate["ray_path"])
    independent = validate_escape_segments(candidate["moving"], candidate["obstacles"], specs, candidate["ray_path"])
    return {"production": asdict(production), "independent": independent}


def assert_accepted_pair_agreement(expected):
    """Compare semantic finite-pair fields without conflating oracle scope."""
    production, independent = expected["production"], expected["independent"]
    assert production["valid"] and independent["valid"]
    for segment, group in enumerate(production["segment_results"]):
        for obstacle, result in enumerate(group):
            other = next(row for row in independent["pairs"] if row["kind"] == "se2"
                         and row["segment"] == segment and row["obstacle"] == obstacle)
            for key in ("status", "initial_state", "end_state", "immediate", "touches_end"):
                assert result[key] == other[key], (segment, obstacle, key)
            for key in ("features", "incidences"):
                assert sorted(canonical(result[key])) == sorted(canonical(other[key]))
            assert result["exact_time"] is None and other["exact_time"] is None


def independent_tail_check(independent, obstacles, ray):
    endpoint = tuple(tuple(F(x) for x in point) for point in independent["se2_endpoint"])
    bottom = min(p[1] for p in endpoint)
    top = max(p[1] for ring in obstacles for p in ring)
    upward = ray[0] == (0, 0) and ray[-1][0] == 0 and ray[-1][1] > 0
    return {"valid": upward and bottom > top, "lowest_endpoint_y": bottom,
            "highest_obstacle_y": top, "strict_vertical_clearance": bottom - top,
            "method": "independent_se2_endpoint_plus_exact_upward_halfplane",
            "old_oracle_infinite_ray_verified": independent["infinite_ray_verified"]}


def escape_bundle(n, element, metadata, normal, output, *, specs=None):
    output = new_output(output)
    began = time.perf_counter()
    instance = instance_for(n, element, metadata["verified_delta"])
    geometry_seconds = time.perf_counter() - began
    candidate = path_candidate(instance, strip_specs(normal) if specs is None else specs)
    write_json(output / "instance.json", instance)
    write_json(output / "candidate.json", candidate)
    audit = numeric_input_audit({"instance": instance, "candidate": candidate})
    expected = verify_candidate(candidate)
    write_json(output / "verification.json", expected)
    tail = independent_tail_check(expected["independent"], instance["obstacles"], candidate["ray_path"])
    write_json(output / "independent_tail.json", tail)
    if not (expected["production"]["valid"] and expected["independent"]["valid"] and tail["valid"]):
        raise RuntimeError("escape dual verification or independent infinite tail failed")
    assert_accepted_pair_agreement(expected)
    assert expected["independent"]["infinite_ray_verified"] is False
    bundle = {"schema": "eab.t2d.finite-bundle/1", "N": n, "element": element, "kind": "escape",
              "metadata": metadata, "expected": expected, "independent_tail": tail,
              "instance_text": (output / "instance.json").read_text("utf-8"),
              "candidate_text": (output / "candidate.json").read_text("utf-8"),
              "geometry_construction": "independent exact section envelope of actual A; raw A bound to production generator",
              "numeric_input_audit": audit, "geometry_seconds_diagnostic_only": geometry_seconds,
              "seconds_diagnostic_only": time.perf_counter() - began}
    write_json(output / "bundle.json", bundle)
    return bundle


def inspect_pickle_opcodes(path):
    """Isolated static disassembly only; never calls pickle.load/loads."""
    script = '''import hashlib,json,pickletools,sys
from pathlib import Path
p=Path(sys.argv[1]); data=p.read_bytes()
if len(data)>1000000: raise ValueError("inspection size budget exceeded")
rows=[]
for op,arg,pos in pickletools.genops(data):
    if isinstance(arg,float): arg={"binary64_hex":arg.hex()}
    if isinstance(arg,bytes): arg={"bytes_hex":arg.hex()}
    rows.append({"offset":pos,"opcode":op.name,"argument":arg})
forbidden={"GLOBAL","STACK_GLOBAL","REDUCE","BUILD","OBJ","INST","NEWOBJ","NEWOBJ_EX","PERSID","BINPERSID","EXT1","EXT2","EXT4","NEXT_BUFFER","READONLY_BUFFER"}
print(json.dumps({"path":str(p),"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data),"deserialization_performed":False,"forbidden_opcodes":[r for r in rows if r["opcode"] in forbidden],"opcodes":rows}))
'''
    result = subprocess.run([sys.executable, "-I", "-c", script, str(Path(path).resolve())],
                            check=True, capture_output=True, text=True, encoding="utf-8", timeout=30)
    return json.loads(result.stdout)


def numeric_waypoints_from_opcodes(audit):
    """Extract one literal float-triple sequence from static opcode records.

    This is not a pickle loader and does not reconstruct its dict/list graph.
    Only the already-disassembled BINFLOAT.hex values within the literal
    waypoint region are consumed. All metadata acceptance flags are ignored.
    The original container is still not claimed safe to deserialize.
    """
    if audit["deserialization_performed"] or audit["forbidden_opcodes"]:
        raise ValueError("expected static disassembly with no executable opcodes")
    rows = audit["opcodes"]
    starts = [i for i, row in enumerate(rows) if row["opcode"] == "SHORT_BINUNICODE"
              and row["argument"] == "waypoints"]
    if len(starts) != 1:
        raise ValueError("expected exactly one literal waypoint region")
    pending, points, ended = [], [], False
    for row in rows[starts[0] + 1:]:
        op = row["opcode"]
        if op in ("EMPTY_LIST", "MEMOIZE", "MARK"):
            continue
        if op == "BINFLOAT":
            value = row["argument"]
            if set(value) != {"binary64_hex"}:
                raise ValueError("numeric opcode was not hex encoded")
            number = float.fromhex(value["binary64_hex"])
            if not math.isfinite(number):
                raise ValueError("nonfinite waypoint proposal")
            pending.append(F(number))
        elif op == "TUPLE3":
            if len(pending) != 3:
                raise ValueError("waypoint is not a literal numeric triple")
            points.append(tuple(pending))
            pending = []
        elif op == "APPENDS":
            ended = True
            break
        else:
            raise ValueError("unexpected opcode in literal waypoint region: " + op)
    if not ended or pending or len(points) < 2 or points[0] != (0, 0, 0):
        raise ValueError("incomplete literal waypoint proposal")
    return tuple(points)


def waypoint_specs(points, bits=40):
    """Untrusted numerical angle conversion, followed by exact motions."""
    denominator = 1 << bits
    refined = [points[0]]
    for first, last in zip(points, points[1:]):
        count = max(1, math.ceil(abs(float(last[2] - first[2])) / (math.pi / 4)))
        refined.extend(tuple(a + F(j, count) * (b - a) for a, b in zip(first, last))
                       for j in range(1, count + 1))
    poses = tuple((x, y, F(round(math.tan(float(angle) / 2) * denominator), denominator))
                  for x, y, angle in refined)
    result = []
    for (x, y, v), (xx, yy, vv) in zip(poses, poses[1:]):
        u = (vv - v) / (1 + v * vv)
        if abs(u) > 1:
            raise ValueError("proposed segment exceeds the quarter-turn contract")
        result.append((u, (xx - x, yy - y), (x, 1 + y)))
    return tuple(result)


def freeze_sources(output):
    names = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT).decode("utf-8").split("\0")
    selected = sorted({name for name in names if name and (ROOT / name).is_file()
                       and (name.endswith(".py") or name in
                            ("docs/t2d_knob_family_theorem.md", "docs/t2c2_knob_theorem.md", "docs/t2b_cage_lemma.md"))})
    active = {path.relative_to(ROOT).as_posix() for path in (ROOT / "src").rglob("*.py")}
    for module in tuple(sys.modules.values()):
        name = getattr(module, "__file__", None)
        if name:
            path = Path(name).resolve()
            if path.is_relative_to(ROOT) and path.suffix == ".py":
                active.add(path.relative_to(ROOT).as_posix())
    active.add("tools/t2d_certificates.py")
    rows = []
    with zipfile.ZipFile(output / "source_snapshot.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in selected:
            data = (ROOT / name).read_bytes()
            archive.writestr(name, data)
            rows.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                         "active_dependency_checked_during_run": name in active})
    if active - set(selected):
        raise AssertionError("active source absent from snapshot: " + repr(active - set(selected)))
    result = {"tool_version": TOOL_VERSION, "python_version": sys.version,
              "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
              "git_status_porcelain": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).decode("utf-8"),
              "snapshot_scope": "all listed tracked and untracked Python sources plus readonly mathematical contracts",
              "runtime_immutability_scope": "all src and all locally imported active modules; unrelated tests may be authored concurrently",
              "files": rows}
    write_json(output / "source_manifest.json", result)
    return result


def check_sources(source):
    changed = [row["path"] for row in source["files"] if row["active_dependency_checked_during_run"]
               and hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() != row["sha256"]]
    if changed:
        raise RuntimeError("active dependency changed; entire scientific run invalid: " + repr(changed))


def square_proposal(n):
    source = EVIDENCE / "acceptance_inputs_20261026" / ("se2cert_square_N" + str(n) + ".pkl")
    audit = inspect_pickle_opcodes(source)
    points = numeric_waypoints_from_opcodes(audit)
    proposed_delta = {8: F(185792159389, 549755813888), 16: F(384996244747, 1099511627776),
                      32: F(193962731649, 549755813888)}[n]
    values = family_values(n, "square")
    critical = {key: getattr(values["delta"], key) for key in ("a", "b", "q")}
    directed_upper = proxy_metadata(critical, 12, "escape")["verified_delta"]
    delta = min(proposed_delta, directed_upper)
    assert values["delta"] < delta < values["delta"] + F(1, 4096)
    metadata = {"verified_delta": delta, "critical": critical,
                "source_proposed_delta": proposed_delta, "delta_reduction": proposed_delta - delta,
                "upper_gap_strictly_below": F(1, 4096), "direct_rational_instance_verification": True,
                "source_sha256": audit["sha256"], "deserialization_performed": False,
                "proposal_source": "static BINFLOAT.hex extraction; metadata acceptance ignored",
                "source_binary_container_not_approved_for_loading": True}
    return metadata, waypoint_specs(points), audit


def run_certificates(output, cage_k=(6, 8, 10), escape_k=(6, 9, 12, 15, 18, 20)):
    output = new_output(output)
    source = freeze_sources(output)
    started, rows = time.perf_counter(), []
    write_json(output / "state.json", {"complete": False, "phase": "STARTING"})
    try:
        for n in (4, 8, 16, 32):
            for element in ("square", "octagon", "K16"):
                values = family_values(n, element)
                d = values["delta"]
                critical = {"a": d.a, "b": d.b, "q": d.q}
                normal = values["e_star"][0]["normal"]
                for kind, indices in (("cage", cage_k), ("escape", escape_k if all(values["S"]) else ())):
                    for k in indices:
                        check_sources(source)
                        name = "N" + str(n) + "_" + element + "_" + kind + "_k" + str(k)
                        destination = output / name
                        metadata = proxy_metadata(critical, k, kind)
                        journal(output, phase="begin", case=name)
                        bundle = cage_bundle(n, element, metadata, destination) if kind == "cage" else escape_bundle(n, element, metadata, normal, destination)
                        if "expected" not in bundle:
                            raise RuntimeError("proposal did not produce an accepted certificate")
                        check_sources(source)
                        row = {"id": name, "N": n, "element": element, "kind": kind, "k": k,
                               "bundle": name + "/bundle.json", "verified_delta": metadata["verified_delta"],
                               "target_delta": metadata["target_delta"],
                               "production_valid": bundle["expected"]["production"]["valid"],
                               "independent_valid": bundle["expected"]["independent"]["valid"],
                               "seconds_diagnostic_only": bundle["seconds_diagnostic_only"]}
                        rows.append(row)
                        journal(output, phase="accepted", **row)
        for n in (8, 16, 32):
            check_sources(source)
            metadata, specs, opcode_audit = square_proposal(n)
            name = "N" + str(n) + "_square_mixed_escape"
            journal(output, phase="begin", case=name)
            bundle = escape_bundle(n, "square", metadata, (F(1), F(0)), output / name, specs=specs)
            write_json(output / name / "proposal_opcode_audit.json", opcode_audit)
            check_sources(source)
            row = {"id": name, "N": n, "element": "square", "kind": "escape", "k": None,
                   "bundle": name + "/bundle.json", "verified_delta": metadata["verified_delta"],
                   "production_valid": bundle["expected"]["production"]["valid"],
                   "independent_valid": bundle["expected"]["independent"]["valid"],
                   "seconds_diagnostic_only": bundle["seconds_diagnostic_only"]}
            rows.append(row)
            journal(output, phase="accepted", **row)
        identities = [(row["N"], row["element"], row["verified_delta"]) for row in rows]
        assert len(set(identities)) == len(rows), "same rational delta has two certificates"
        assert sum(row["kind"] == "cage" for row in rows) == 36
        assert sum(row["kind"] == "escape" for row in rows) == 57
        counts = {"cages": 36, "strip_escapes": 54, "mixed_square_escapes": 3}
        journal(output, phase="complete", counts=counts)
        files = [{"path": p.relative_to(output).as_posix(), "bytes": p.stat().st_size,
                  "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in sorted(output.rglob("*")) if p.is_file() and p.name != "state.json"]
        result = {"schema": "eab.t2d.finite-evidence/1", "status": "ACCEPTED_DIRECTED_RATIONAL_TRANSFERS",
                  "source": source, "cases": rows, "files": files,
                  "counts": counts,
                  "same_delta_contradictions": 0, "direct_algebraic_instance_verification": False,
                  "seconds_diagnostic_only": time.perf_counter() - started}
        write_json(output / "manifest.json", result)
        write_json(output / "state.json", {"complete": True, "phase": "FINISHED", "counts": result["counts"]})
        return result
    except BaseException as error:
        write_json(output / "invalid_run.json", {"status": "INVALID_ENTIRE_RUN", "reason": repr(error),
                   "completed_not_reused": rows})
        write_json(output / "state.json", {"complete": False, "phase": "INVALID_ENTIRE_RUN"})
        journal(output, phase="invalid_entire_run", reason=repr(error))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inspect-pickle", type=Path, nargs="*")
    parser.add_argument("--run-certificates", action="store_true")
    args = parser.parse_args(argv)
    if args.run_certificates:
        run_certificates(args.output)
        return 0
    output = new_output(args.output)
    if args.inspect_pickle:
        for path in args.inspect_pickle:
            write_json(output / (path.stem + "_opcode_audit.json"), inspect_pickle_opcodes(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
