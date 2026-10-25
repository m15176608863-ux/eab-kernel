"""Exact T2a candidate replay and independent test-oracle evidence.

Candidate coordinates are parsed as Fractions. No floating proposal clearance
or grid occupancy enters a decision. Oracle computation remains in tests/.
"""
import argparse
from dataclasses import asdict
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]
from eab.kernel2d.se2 import SE2Motion, se2_first_entrance
from eab.kernel2d.se2_paths import SE2EscapePath, verify_se2_escape
from t2a_oracle_audit import validate_escape_segments
from t2a_truth_geometry import doorway, doorway_motion_specs

EVIDENCE = Path("D:/eab-evidence/reports/codex/T2a_evidence")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def point(p):
    return tuple(F(v) for v in p)


def ring(p):
    return tuple(point(v) for v in p)


def encode(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, tuple) or isinstance(value, list):
        return [encode(v) for v in value]
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    return value


def make_path(pieces):
    if not pieces:
        raise ValueError("proposal must contain finite rigid path pieces")
    poses = [ring(pieces[0]["start"])]
    motions = []
    for piece in pieces:
        if ring(piece["start"]) != poses[-1]:
            raise ValueError("proposal has discontinuous starting poses")
        poses.append(ring(piece["end"]))
        motions.append(SE2Motion(F(piece["u1"]), point(piece["translation"]), point(piece["center"])))
    return SE2EscapePath(tuple(poses), tuple(motions))


def verify_case(candidate, source, out):
    name = candidate["case_id"]
    write(out / (name+".progress.json"), dict(complete=False, stage="PRODUCTION"))
    moving = ring(candidate["moving"])
    obstacles = tuple(ring(p) for p in candidate["obstacles"])
    path = make_path(candidate["pieces"])
    ray = tuple(point(p) for p in candidate["ray_path"])
    started = time.perf_counter()
    production = verify_se2_escape(moving, obstacles, path, ray)
    seconds_production = time.perf_counter()-started
    pair_rows = []
    for segment, row in enumerate(production.segment_results):
        for obstacle, result in enumerate(row):
            pair_rows.append(dict(segment=segment, obstacle=obstacle,
                status=result.status, initial_state=result.initial_state,
                exact_time=result.exact_time.certificate if result.exact_time is not None else None,
                immediate=result.immediate, incidences=result.incidences, features=result.features,
                touches_end=result.touches_end, end_state=result.end_state))
    write(out / (name+".progress.json"), dict(complete=False, stage="INDEPENDENT_ORACLE",
                                           production_valid=production.valid))
    started = time.perf_counter()
    audit = validate_escape_segments(moving, obstacles,
        tuple((m.u1, m.translation, m.center) for m in path.motions), ray)
    seconds_oracle = time.perf_counter()-started
    finite_oracle = [r for r in audit["pairs"] if r["kind"] == "se2"]
    agreement = len(pair_rows) == len(finite_oracle) and all(
        (p["status"], p["initial_state"], p["end_state"], p["immediate"], p["touches_end"]) ==
        (q["status"], q["initial_state"], q["end_state"], q["immediate"], q["touches_end"])
        for p, q in zip(pair_rows, finite_oracle))
    if production.valid:
        assert audit["se2_endpoint"] == encode(path.poses[-1]), "independent endpoint identity"
        assert agreement and audit["valid"], "accepted path must agree with all independent interval probes"
    # This implication is a supplementary fast-path check, not a requirement
    # that every contact-allowed path be strictly separated.
    closed_rows = []
    if production.valid and candidate["geometry"].get("delta") != "0":
        for index, (pose, motion) in enumerate(zip(path.poses, path.motions)):
            for j, obstacle in enumerate(obstacles):
                result = se2_first_entrance(pose, obstacle, motion)
                closed_rows.append(dict(segment=index, obstacle=j, status=result.status,
                                        initial_state=result.initial_state))
    valid = production.valid and audit["valid"] and agreement
    result = dict(schema="t2a-exact-se2-escape-1", case_id=name,
        status="VERIFIED_ESCAPE" if valid else "REJECTED_CANDIDATE",
        source="exact_original_pose_event_partition_and_independent_oracle",
        geometry=candidate["geometry"], translation_threshold=candidate.get("translation_threshold"),
        candidate_sha256=digest(source) if source else None,
        moving=candidate["moving"], obstacles=candidate["obstacles"],
        pieces=candidate["pieces"], ray_path=candidate["ray_path"],
        production=dict(valid=production.valid, reason=production.reason,
            checked_segments=production.checked_segments, checked_pairs=production.checked_pairs,
            pair_results=pair_rows, ray=encode(asdict(production.ray_verification))
            if production.ray_verification is not None else None),
        independent_oracle=audit, production_oracle_agree=agreement,
        closed_contact_crosscheck=closed_rows,
        diagnostic_timing_seconds=dict(production=seconds_production, oracle=seconds_oracle),
        tool_version="t2a-replay-2", base_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
        source_sha256={p: digest(ROOT / p) for p in (
            "src/eab/kernel2d/se2_paths.py", "src/eab/kernel2d/se2.py",
            "tests/t2a_independent_oracle.py", "tests/t2a_oracle_audit.py", "tests/m5a_independent_oracle.py",
            "tools/t2_verify_evidence.py")})
    write(out / (name+".json"), encode(result))
    write(out / (name+".progress.json"), dict(complete=True, status=result["status"]))
    summary = dict(case_id=name, status=result["status"], segments=len(path.motions),
        production_pairs=production.checked_pairs, oracle_pairs=audit["first_contact_calls"],
        ray_verified=production.ray_verification.valid if production.ray_verification else False,
        production_oracle_agree=agreement, diagnostic_seconds=seconds_production+seconds_oracle)
    print(json.dumps(summary), flush=True)
    return summary


def doorway_candidate(delta):
    moving, obstacles = doorway(delta)
    current, pieces = moving, []
    for u, d, c in doorway_motion_specs():
        motion = SE2Motion(u, d, c)
        end = tuple(motion.endpoint(p) for p in current)
        pieces.append(dict(start=current, u1=u, translation=d, center=c, end=end))
        current = end
    name = {F(127, 1024): "door_below", F(1, 8): "door_equal", F(129, 1024): "door_above"}[delta]
    return encode(dict(case_id=name, geometry=dict(kind="doorway", element="octagon", wall_erosion=0,
        delta=delta), moving=moving, obstacles=obstacles, pieces=pieces,
        ray_path=((F(0), F(0)), (F(0), F(100)))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--cases", nargs="*", default=[])
    parser.add_argument("--doorway", action="store_true")
    args = parser.parse_args()
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("name must be a new directory component")
    out = EVIDENCE / args.name
    out.mkdir(parents=True, exist_ok=False)
    summaries = []
    for name in args.cases:
        path = EVIDENCE / "proposals" / (name+".json")
        summaries.append(verify_case(json.loads(path.read_text("utf-8")), path, out))
    if args.doorway:
        for delta in (F(1, 8), F(129, 1024), F(127, 1024)):
            summaries.append(verify_case(doorway_candidate(delta), None, out))
    write(out / "summary.json", summaries)


if __name__ == "__main__":
    main()
