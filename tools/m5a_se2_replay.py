"""M5a exact rigid-model replay; historical M4c outputs are hash-bound inputs.

Only the chosen rigid endpoint model is certified when its exact residual is
zero. No endpoint fit certifies b-DDA's unknown continuous physical trajectory.
Full records belong in ignored M5a_evidence/tmp; frozen prefixes are compact.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from fractions import Fraction as F
import gzip
import io
import json
from math import isqrt
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
import m4c_motion_replay as chord
from eab.construction import scalar_rational
from eab.kernel2d.se2 import SE2Motion, se2_first_entrance

CASES, PHASES = chord.CASES, chord.PHASES
CATEGORIES = chord.CATEGORIES
CERTIFICATES = frozenset({"CERTIFIED_RIGID_ENDPOINT_MODEL", "UNCERTIFIED_NONRIGID_ENDPOINTS"})
EVIDENCE = ROOT / "reports/codex/M5a_evidence"
INPUTS = EVIDENCE / "tmp/replay/inputs"
FULL_STEPS = dict(zip(CASES, (50, 100, 50, 50, 100, 100, 100, 100, 100, 100, 400, 100, 400, 30, 30)))
require, digest, file_hash, write_json = chord.require, chord.digest, chord.file_hash, chord.write_json


def code_hashes():
    """Bind the new numerical path and unchanged historical replay closure."""
    names = set(chord.REPLAY_SOURCE_FILES)
    names.update({"tools/m5a_se2_replay.py", "tools/ingest_fixtures.py", "src/eab/kernel2d/se2.py", "src/eab/kernel2d/algebraic.py"})
    return {name: file_hash(ROOT / name) for name in sorted(names)}


@dataclass(frozen=True)
class RigidFit:
    motion: SE2Motion
    delta: F

    @property
    def certificate(self):
        return "CERTIFIED_RIGID_ENDPOINT_MODEL" if self.delta == 0 else "UNCERTIFIED_NONRIGID_ENDPOINTS"

    @property
    def record(self):
        return {"u1": str(self.motion.u1), "center": list(map(str, self.motion.center)),
                "translation": list(map(str, self.motion.translation)), "delta_linf": str(self.delta),
                "delta_display": scalar_rational(self.delta, allow_underflow=True), "certificate": self.certificate}


def fit_rigid(start, end):
    """Deterministic rational fit proposal followed by an exact residual check.

    Equal-weight vertex centroids and dot/cross aggregates propose a rotation;
    this is not claimed to be the exact global minimizer of the L-infinity fit.
    An exactly rational rigid rotation is recovered without approximation.
    """
    start, end = chord._exact_poly(start), chord._exact_poly(end)
    require(len(start) == len(end) and len(start) >= 3, "rigid fit topology mismatch")
    centers = [tuple(sum(p[k] for p in poly)/len(poly) for k in (0, 1)) for poly in (start, end)]
    centered = [tuple(tuple(p[k]-c[k] for k in (0, 1)) for p in poly) for poly, c in zip((start, end), centers)]
    scale = sum(x*x+y*y for x, y in centered[0])
    require(scale > 0, "rigid fit degenerate initial geometry")
    c = sum(p[0]*q[0]+p[1]*q[1] for p, q in zip(*centered))/scale
    s = sum(p[0]*q[1]-p[1]*q[0] for p, q in zip(*centered))/scale
    require(c >= 0 and (c != 0 or s != 0), "rigid fit outside the quarter-turn model domain")
    square = c*c+s*s
    if square == 1:
        u = s/(1+c)
    else:
        n, d = isqrt(square.numerator), isqrt(square.denominator)
        scaled = square*(1 << 160)
        norm = F(n, d) if n*n == square.numerator and d*d == square.denominator else F(isqrt(scaled.numerator//scaled.denominator), 1 << 80)
        require(norm+c != 0, "rigid fit unresolved orientation")
        u = (s/(norm+c)).limit_denominator(1 << 40)
    model = SE2Motion(u1=u, center=centers[0], translation=tuple(centers[1][k]-centers[0][k] for k in (0, 1)))
    delta = max(abs(model.endpoint(p)[k]-q[k]) for p, q in zip(start, end) for k in (0, 1))
    return RigidFit(model, delta)


def projected_sweep(poly, model, normal):
    """Exact conservative projection bound; see design T8 broad-phase proof."""
    nx, ny = normal
    move = nx*model.translation[0]+ny*model.translation[1]
    lower, upper = [], []
    for x, y in poly:
        radius = 2*abs(model.u1)*(abs(x-model.center[0])+abs(y-model.center[1]))
        pad = (abs(nx)+abs(ny))*radius
        value = nx*x+ny*y
        lower.append(value+min(F(0), move)-pad)
        upper.append(value+max(F(0), move)+pad)
    return min(lower), max(upper)


def swept_separated(A, B, ma, mb):
    """A sufficient no-contact proof; failure to separate never means contact."""
    normals = [(F(1), F(0)), (F(0), F(1))]
    for poly in (A, B):
        normals.extend((q[1]-p[1], p[0]-q[0]) for p, q in zip(poly, poly[1:]+poly[:1]))
    for normal in normals:
        if normal == (0, 0):
            continue
        a, b = projected_sweep(A, ma, normal), projected_sweep(B, mb, normal)
        if a[1] < b[0] or b[1] < a[0]:
            return True
    return False


def same_time(time, certificate):
    if time is None or certificate is None:
        return time is None and certificate is None
    if certificate["rational"] is not None:
        return time == F(certificate["rational"])
    c, b, _ = map(F, certificate["polynomial"])
    if time.sign_polynomial(c, b, F(1)):
        return False
    return time < -b/2 if certificate["branch"] == -1 else time > -b/2


def _empty():
    return {"status": "no_contact", "time": None, "time_display": None, "features": [], "incidences": []}


def _same_cover(a, b):
    return a["status"] == b["status"] and set(map(tuple, a["features"])) == set(map(tuple, b["features"]))


def classify_reference(state, key, result, pd):
    canonical = {**result, "features": set(map(tuple, result["features"])), "incidences": set(map(tuple, result["incidences"]))}
    frozen_pd = None if pd is None else {**pd, "features": set(map(tuple, pd["features"]))}
    answer = chord.classify_reference(state, tuple(key), canonical, frozen_pd)
    require(answer in CATEGORIES, "unclassified SE2 legacy category")
    return answer


def frame_result(frame, sg, eg, baseline):
    require(frame["step"] == baseline["step"] and digest(frame["geometry"]) == baseline["start_geometry_sha256"], "baseline geometry/step mismatch")
    geometries = {b: (chord._exact_poly(sg.blocks[b].poly), chord._exact_poly(eg.blocks[b].poly)) for b in sg.blocks}
    fits = {b: fit_rigid(*pair) for b, pair in geometries.items()}
    old = {tuple(p["pair"]): p for p in baseline["pairs"]}
    stats, records = Counter(), {}
    blocks = sorted(geometries)
    for i, a in enumerate(blocks):
        for b in blocks[i+1:]:
            key = a, b
            fa, fb = fits[a], fits[b]
            certification = "CERTIFIED_RIGID_ENDPOINT_MODEL" if fa.delta+fb.delta == 0 else "UNCERTIFIED_NONRIGID_ENDPOINTS"
            stats[certification] += 1
            stats["all_pairs"] += 1
            prior = old.get(key)
            state = prior["initial_state"] if prior else -1
            A, B = geometries[a][0], geometries[b][0]
            separation = False if state >= 0 else swept_separated(A, B, fa.motion, fb.motion)
            if prior is None and separation:
                stats["omitted_proven_separated_pairs"] += 1
                continue
            actual_time = None
            if state >= 0:
                # Initial incidence/PD depends only on the SAME initial bodies,
                # not on interpolation; baseline byte binding is verified first.
                result = prior["actual"]
                path = "REUSED_IDENTICAL_INITIAL_GEOMETRY"
            elif separation:
                result, path = _empty(), "PROVED_SWEPT_PROJECTION_SEPARATION"
            else:
                actual = se2_first_entrance(A, B, fa.motion, fb.motion)
                require(actual.initial_state == state, "SE2/baseline initial-state mismatch")
                result, actual_time = chord._motion_record(actual, sg.blocks[a], sg.blocks[b]), actual.exact_time
                path = "SE2_EXACT_EVENT_ENUMERATION"
            stats[path] += 1
            stats["initial_"+str(state)+"_"+result["status"]] += 1
            baseline_result = prior["actual"] if prior else _empty()
            pd = prior["pd"] if prior else None
            if state == 1:
                require(pd["status"] == "EVALUATED", "initial PD baseline is incomplete")
            record = {"pair": list(key), "initial_state": state, "rigid": result, "chord": baseline_result,
                      "pd": pd, "certificate": certification, "delta_linf_sum": str(fa.delta+fb.delta), "path": path,
                      "same_chord_status_and_cover": _same_cover(result, baseline_result)}
            if state == -1:
                if prior is not None:
                    trans = prior["translation"]["result"]
                else:
                    At, _ = chord.translation_surrogate(*geometries[a]); Bt, _ = chord.translation_surrogate(*geometries[b])
                    tr = chord._checked_motion(A, B, At, Bt, state)
                    trans = chord._motion_record(tr, sg.blocks[a], sg.blocks[b])
                record["translation"] = trans
                record["same_translation_status_and_cover"] = _same_cover(result, trans)
                record["same_chord_time"] = same_time(actual_time, baseline_result["time"])
                stats["separated_chord_same" if record["same_chord_status_and_cover"] else "separated_chord_different"] += 1
                if baseline_result["status"] == "contact":
                    stats["chord_new_contacts"] += 1
                    if not _same_cover(baseline_result, trans):
                        record["m4c_translation_discrepancy_contact"] = True
                        stats["m4c_20_subset"] += 1
                        stats["m4c_20_se2_chord_same" if record["same_chord_status_and_cover"] else "m4c_20_se2_chord_different"] += 1
                if result["status"] == "contact":
                    stats["rigid_new_contacts"] += 1
            records[key] = record
    phases = {}
    for phase in PHASES:
        rows, counts, secondary, transitions = [], Counter(), Counter(), Counter()
        for row in baseline["phases"][phase]["records"]:
            pair = records[tuple(row["pair"])]
            category = classify_reference(pair["initial_state"], row["primary_reference"], pair["rigid"], pair["pd"])
            second = None if row["secondary_reference"] is None else classify_reference(pair["initial_state"], row["secondary_reference"], pair["rigid"], pair["pd"])
            counts[category] += 1
            if second is not None:
                secondary[second] += 1
            transitions[row["category"]+" -> "+category] += 1
            rows.append({**row, "chord_category": row["category"], "category": category,
                         "chord_secondary_category": row["secondary_category"], "secondary_category": second})
        require(len(rows) == len(frame[phase]) and sum(counts.values()) == len(rows), "legacy reference conservation failure")
        phases[phase] = {"counts": dict(sorted(counts.items())), "secondary_counts": dict(sorted(secondary.items())),
                         "transitions": dict(sorted(transitions.items())), "records": rows}
    return {"step": frame["step"], "endpoint_step": frame["step"]+1, "start_geometry_sha256": digest(frame["geometry"]),
            "baseline_frame_sha256": digest(baseline), "stats": dict(sorted(stats.items())),
            "blocks": {str(b): f.record for b, f in fits.items()}, "pairs": list(records.values()), "phases": phases}


def residual_distribution(values):
    values = sorted(values)
    return {"count": len(values), "zero": values.count(F(0)), "nonzero": sum(v > 0 for v in values),
            "quantiles_exact": {name: str(values[(len(values)-1)*n//d]) for name, n, d in
                                (("min", 0, 1), ("median", 1, 2), ("p95", 95, 100), ("max", 1, 1))},
            "quantiles_display": {name: scalar_rational(values[(len(values)-1)*n//d], allow_underflow=True) for name, n, d in
                                  (("min", 0, 1), ("median", 1, 2), ("p95", 95, 100), ("max", 1, 1))}}


def _paths(case, mode):
    if mode == "full":
        return INPUTS / case / "shadow.jsonl", INPUTS / case / "geom.csv", ROOT / "reports/codex/M4c_evidence/full_replay_r4" / case
    return ROOT / "fixtures/m4b_shadow" / (case+".jsonl.gz"), ROOT / "fixtures/m4c_motion/endpoints.json", ROOT / "reports/codex/M4c_evidence/fix_frozen_replay" / case


def replay_case(case, mode, out):
    start = time.perf_counter()
    out.mkdir(parents=True, exist_ok=False)
    initial_code = code_hashes()
    source, terminal_source, baseline_dir = _paths(case, mode)
    _, frames, _ = chord.snapshot.read_snapshot(source)
    terminal = chord.load_geometry_csv(terminal_source, frames) if mode == "full" else chord.load_endpoint(terminal_source, case, source, frames)
    pairs = chord.paired_geometries(frames, terminal)
    baseline_path, baseline_audit_path = baseline_dir / "normalized.jsonl.gz", baseline_dir / "audit.json"
    baseline_audit = json.loads(baseline_audit_path.read_text(encoding="utf-8"))
    require(baseline_audit["complete"] and baseline_audit["audit"] == "GREEN", "historical baseline incomplete")
    require(baseline_audit["normalized_sha256"] == file_hash(baseline_path), "historical baseline byte hash mismatch")
    require(baseline_audit["input_hashes"] == {"snapshot": file_hash(source), "terminal_source": file_hash(terminal_source)}, "historical baseline input mismatch")
    inputs = {"snapshot": file_hash(source), "terminal_source": file_hash(terminal_source),
              "baseline_normalized": file_hash(baseline_path), "baseline_audit": file_hash(baseline_audit_path)}
    stats, counts, secondary, transitions = Counter(), {p: Counter() for p in PHASES}, {p: Counter() for p in PHASES}, {p: Counter() for p in PHASES}
    hashes, deltas, subset, examples = [], [], [], {}
    normalized = out / "normalized.jsonl.gz"
    with gzip.open(baseline_path, "rt", encoding="utf-8") as old, normalized.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="\n") as sink:
                for index, (frame, sg, eg) in enumerate(pairs):
                    line = old.readline(); require(bool(line), "baseline missing frame")
                    baseline = json.loads(line)
                    require(digest(baseline) == baseline_audit["frame_sha256"][index], "baseline frame certificate mismatch")
                    result = frame_result(frame, sg, eg, baseline)
                    hashes.append(digest(result)); stats.update(result["stats"])
                    deltas.extend(F(r["delta_linf"]) for r in result["blocks"].values())
                    for phase in PHASES:
                        counts[phase].update(result["phases"][phase]["counts"])
                        secondary[phase].update(result["phases"][phase]["secondary_counts"])
                        transitions[phase].update(result["phases"][phase]["transitions"])
                    for row in result["pairs"]:
                        if row.get("m4c_translation_discrepancy_contact"):
                            subset.append({"case": case, "step": frame["step"], **row})
                        label = ("20_" if row.get("m4c_translation_discrepancy_contact") else "other_")+str(row["same_chord_status_and_cover"])
                        if row["initial_state"] == -1 and row["chord"]["status"] == "contact" and label not in examples:
                            a, b = row["pair"]
                            examples[label] = {"case": case, "step": frame["step"], "comparison": row,
                                               "A0": sg.blocks[a].poly, "A1": eg.blocks[a].poly,
                                               "B0": sg.blocks[b].poly, "B1": eg.blocks[b].poly,
                                               "A_ids": list(sg.blocks[a].vidx), "B_ids": list(sg.blocks[b].vidx),
                                               "legacy": {p: [r for r in result["phases"][p]["records"] if r["pair"] == row["pair"]] for p in PHASES}}
                    sink.write(json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False)+"\n"); sink.flush()
                    write_json(out / "progress.json", {"complete": False, "completed_steps": index+1, "requested_steps": len(pairs), "code_hashes": initial_code})
                require(not old.readline(), "baseline has surplus frames")
    require(code_hashes() == initial_code, "code changed during replay; whole run invalid")
    require(inputs == {"snapshot": file_hash(source), "terminal_source": file_hash(terminal_source), "baseline_normalized": file_hash(baseline_path), "baseline_audit": file_hash(baseline_audit_path)}, "input changed during replay")
    result = {"schema": "eab.m5a-replay.v1", "audit": "GREEN", "complete": True, "case": case, "mode": mode,
              "steps": len(pairs), "code_hashes": initial_code, "input_hashes": inputs,
              "baseline_reuse": {"audit_path": baseline_audit_path.relative_to(ROOT).as_posix(), "historical_code_hashes": baseline_audit["code_hashes"], "reexecuted": False},
              "counts": {p: dict(sorted(v.items())) for p, v in counts.items()}, "secondary_counts": {p: dict(sorted(v.items())) for p, v in secondary.items()},
              "transitions": {p: dict(sorted(v.items())) for p, v in transitions.items()}, "stats": dict(sorted(stats.items())),
              "frame_sha256": hashes, "frames_sha256": digest(hashes), "normalized_sha256": file_hash(normalized),
              "residuals": residual_distribution(deltas), "m4c_20_subset": subset, "examples": examples, "seconds": time.perf_counter()-start}
    write_json(out / "audit.json", result)
    write_json(out / "progress.json", {"complete": True, "completed_steps": len(pairs), "audit_sha256": file_hash(out / "audit.json")})
    return result


def run_batch(mode, out, jobs):
    out.mkdir(parents=True, exist_ok=False)
    initial = code_hashes(); started = time.perf_counter()
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "TEMP": str(EVIDENCE / "tmp/replay"), "TMP": str(EVIDENCE / "tmp/replay")}
    def run(case):
        command = [sys.executable, "-X", "utf8", str(Path(__file__)), "case", "--mode", mode, "--case", case, "--out", str(out / case)]
        process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, encoding="utf-8", errors="replace")
        (out / (case+".log")).write_text(process.stdout+process.stderr, encoding="utf-8")
        return case, process.returncode
    completed = {}
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for task in as_completed([pool.submit(run, case) for case in CASES]):
            case, status = task.result(); completed[case] = status
            write_json(out / "progress.json", {"complete": False, "completed": completed, "code_hashes": initial})
            print(case, status, flush=True)
    require(all(v == 0 for v in completed.values()) and initial == code_hashes(), "batch failed or code changed; no partial result reuse")
    stats, counts, secondary, transitions = Counter(), {p: Counter() for p in PHASES}, {p: Counter() for p in PHASES}, {p: Counter() for p in PHASES}
    cases, deltas, subset, examples = {}, [], [], {}
    for case in CASES:
        audit = json.loads((out / case / "audit.json").read_text(encoding="utf-8"))
        require(audit["complete"] and audit["code_hashes"] == initial and audit["steps"] == (FULL_STEPS[case] if mode == "full" else 30), "case completion binding mismatch")
        require(audit["normalized_sha256"] == file_hash(out / case / "normalized.jsonl.gz"), "case normalized byte hash mismatch")
        stats.update(audit["stats"]); subset.extend(audit["m4c_20_subset"])
        for p in PHASES:
            counts[p].update(audit["counts"][p]); secondary[p].update(audit["secondary_counts"][p]); transitions[p].update(audit["transitions"][p])
        for label, row in audit["examples"].items():
            examples.setdefault(label, row)
        with gzip.open(out / case / "normalized.jsonl.gz", "rt", encoding="utf-8") as stream:
            rows = list(map(json.loads, stream))
        require([digest(row) for row in rows] == audit["frame_sha256"], "case frame binding mismatch")
        deltas.extend(F(b["delta_linf"]) for row in rows for b in row["blocks"].values())
        cases[case] = {k: audit[k] for k in ("steps", "input_hashes", "stats", "counts", "secondary_counts", "frames_sha256", "normalized_sha256", "seconds")}
        cases[case]["audit_sha256"] = file_hash(out / case / "audit.json")
    summary = {"schema": "eab.m5a-batch.v1", "audit": "GREEN", "complete": True, "mode": mode, "cases": cases,
               "steps": sum(c["steps"] for c in cases.values()), "code_hashes": initial, "stats": dict(sorted(stats.items())),
               "counts": {p: dict(sorted(v.items())) for p, v in counts.items()}, "secondary_counts": {p: dict(sorted(v.items())) for p, v in secondary.items()},
               "transitions": {p: dict(sorted(v.items())) for p, v in transitions.items()}, "residuals": residual_distribution(deltas),
               "m4c_20_subset": subset, "examples": examples, "seconds": time.perf_counter()-started, "jobs": jobs,
               "limitations": ["Nonzero endpoint residuals are uncertified.", "Zero residual certifies the prescribed rigid endpoint model, not physical continuous b-DDA motion.", "M4c initial geometry/PD and chord outputs are verified historical data, not reexecuted by this batch."]}
    write_json(out / "summary.json", summary)
    write_json(out / "progress.json", {"complete": True, "steps": summary["steps"], "summary_sha256": file_hash(out / "summary.json")})
    return summary


def freeze(batch):
    """Freeze exactly 15 x 30 prefix frames from ONE complete audited run."""
    summary = json.loads((batch / "summary.json").read_text(encoding="utf-8"))
    require(summary["complete"] and summary["code_hashes"] == code_hashes(), "cannot freeze incomplete or stale run")
    destination = ROOT / "fixtures/m5a_se2"
    destination.mkdir(parents=True, exist_ok=False)
    expected = {"schema": "eab.m5a-frozen.v1", "source_summary_sha256": file_hash(batch / "summary.json"), "code_hashes": code_hashes(), "cases": {}}
    for case in CASES:
        audit = json.loads((batch / case / "audit.json").read_text(encoding="utf-8"))
        require(file_hash(batch / case / "audit.json") == summary["cases"][case]["audit_sha256"], "freeze audit binding mismatch")
        require(file_hash(batch / case / "normalized.jsonl.gz") == audit["normalized_sha256"], "freeze normalized binding mismatch")
        with gzip.open(batch / case / "normalized.jsonl.gz", "rt", encoding="utf-8") as stream:
            all_rows = list(map(json.loads, stream))
        require([digest(row) for row in all_rows] == audit["frame_sha256"], "freeze frame binding mismatch")
        rows = all_rows[:30]
        source = ROOT / "fixtures/m4b_shadow" / (case+".jsonl.gz")
        _, frames, _ = chord.snapshot.read_snapshot(source)
        require(len(rows) == len(frames) == 30 and [r["start_geometry_sha256"] for r in rows] == [digest(f["geometry"]) for f in frames], "freeze prefix mismatch")
        target = destination / (case+".jsonl.gz")
        with target.open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as compressed:
                compressed.write("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":"), allow_nan=False)+"\n" for row in rows).encode("utf-8"))
        require(target.stat().st_size < 1_000_000, "frozen record exceeds publication size cap")
        stats = Counter(); counts = {p: Counter() for p in PHASES}
        for row in rows:
            stats.update(row["stats"])
            for p in PHASES:
                counts[p].update(row["phases"][p]["counts"])
        expected["cases"][case] = {"steps": 30, "snapshot_sha256": file_hash(source), "normalized_sha256": file_hash(target),
                                   "frame_sha256": [digest(row) for row in rows], "frames_sha256": digest([digest(row) for row in rows]),
                                   "stats": dict(sorted(stats.items())), "counts": {p: dict(sorted(v.items())) for p, v in counts.items()}}
    write_json(destination / "expected.json", expected)
    from ingest_fixtures import provenance_entry, upsert_provenance
    entries = [provenance_entry(p.relative_to(ROOT / "fixtures").as_posix(), "M5a: tools/m5a_se2_replay.py freeze; exact 15x30 prefix of one complete source-bound SE2 run; historical M4c baseline is reused as identified data; no sibling executable run.", "2026-10-15") for p in sorted(destination.iterdir())]
    upsert_provenance(entries)
    return expected


def revalidate_m4c(out, jobs):
    """Fresh 450-frame predecessor rerun; never rewrites any old fixture."""
    out.mkdir(parents=True, exist_ok=False)
    initial = chord.code_hashes()
    old_summary_path = ROOT / "reports/codex/M4c_evidence/frozen_summary.json"
    old_summary_hash = file_hash(old_summary_path)
    old_summary = json.loads(old_summary_path.read_text(encoding="utf-8"))
    expected = json.loads((ROOT / "fixtures/m4c_motion/expected.json").read_text(encoding="utf-8"))
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "TEMP": str(EVIDENCE / "tmp/replay"), "TMP": str(EVIDENCE / "tmp/replay")}
    def run(case):
        source = ROOT / "fixtures/m4b_shadow" / (case+".jsonl.gz")
        command = [sys.executable, "-X", "utf8", str(ROOT / "tools/m4c_motion_replay.py"), str(source),
                   "--endpoint-file", str(ROOT / "fixtures/m4c_motion/endpoints.json"), "--case", case,
                   "--pd-edge-limit", "0", "--out", str(out / case)]
        p = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, encoding="utf-8", errors="replace")
        (out / (case+".log")).write_text(p.stdout+p.stderr, encoding="utf-8")
        return case, p.returncode
    completed = {}
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for task in as_completed([pool.submit(run, case) for case in CASES]):
            case, code = task.result(); completed[case] = code
            write_json(out / "progress.json", {"complete": False, "completed": completed})
            print("M4C_REVALIDATE", case, code, flush=True)
    require(all(v == 0 for v in completed.values()) and initial == chord.code_hashes(), "M4c rerun failed or sources changed")
    comparisons = {}
    for case in CASES:
        audit = json.loads((out / case / "audit.json").read_text(encoding="utf-8"))
        fields = ("steps", "counts", "secondary_counts", "stats", "input_hashes", "frame_sha256", "frames_sha256", "normalized_sha256")
        comparisons[case] = {key: audit[key] == expected["cases"][case][key] for key in fields}
        require(audit["complete"] and audit["code_hashes"] == initial and all(comparisons[case].values()), "M4c semantic rerun changed frozen result")
    require(file_hash(old_summary_path) == old_summary_hash, "M4c summary changed during rerun")
    evidence = {"schema": "eab.m5a-m4c-revalidation.v1", "complete": True, "steps": 450, "code_hashes": initial,
                "prior_summary_sha256": old_summary_hash, "prior_code_hashes": old_summary["code_hashes"],
                "comparisons": comparisons, "all_historical_fixture_bytes_unchanged": True,
                "new_run_directory": out.relative_to(ROOT).as_posix(), "reason": "construction.scalar_algebraic appended; all prior constructor implementations retained"}
    evidence_path = EVIDENCE / "m4c_frozen_revalidation.json"
    require(not evidence_path.exists(), "M4c revalidation evidence already exists")
    write_json(evidence_path, evidence)
    old_summary["code_hashes"] = initial
    old_summary["m5a_revalidation"] = evidence_path.relative_to(ROOT).as_posix()
    write_json(old_summary_path, old_summary)
    write_json(out / "progress.json", {"complete": True, "steps": 450, "evidence_sha256": file_hash(evidence_path)})
    return {"steps": 450, "seconds": 0}


def reproduce_examples(source, out):
    """Small standalone rerun from exact binary64 endpoint example payloads."""
    payload = json.loads(source.read_text(encoding="utf-8"))
    examples = payload["examples"]
    answers = {}
    for name, example in examples.items():
        fa, fb = fit_rigid(example["A0"], example["A1"]), fit_rigid(example["B0"], example["B1"])
        actual = se2_first_entrance(example["A0"], example["B0"], fa.motion, fb.motion)
        result = chord._motion_record(actual, SimpleNamespace(vidx=example["A_ids"]), SimpleNamespace(vidx=example["B_ids"]))
        expected = example["comparison"]
        require(_same_cover(result, expected["rigid"]), "minimal example first-cover mismatch")
        require(str(fa.delta+fb.delta) == expected["delta_linf_sum"], "minimal example exact residual mismatch")
        legacy = {p: [] for p in PHASES}
        for phase in PHASES:
            for reference in example["legacy"][phase]:
                category = classify_reference(actual.initial_state, reference["primary_reference"], result, expected["pd"])
                require(category == reference["category"], "minimal example legacy reference mismatch")
                legacy[phase].append({"index": reference["index"], "category": category, "chord_category": reference["chord_category"]})
        answers[name] = {"case": example["case"], "step": example["step"], "pair": expected["pair"], "rigid": result,
                         "fit_A": fa.record, "fit_B": fb.record, "legacy": legacy, "same_chord_status_and_cover": _same_cover(result, expected["chord"])}
    require(not out.exists(), "minimal example output already exists")
    write_json(out, {"complete": True, "source_sha256": file_hash(source), "code_hashes": code_hashes(), "answers": answers})
    return answers


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("case", "batch", "freeze", "revalidate-m4c", "reproduce"))
    parser.add_argument("--mode", choices=("full", "frozen"), default="full")
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--examples", type=Path)
    args = parser.parse_args(argv)
    require(args.out.resolve().is_relative_to(ROOT), "output must remain inside this worktree")
    require(1 <= args.jobs <= 4, "replay supports one through four workers")
    if args.action == "freeze":
        freeze(args.out); print("M5A_FROZEN_GREEN 450"); return 0
    if args.action == "revalidate-m4c":
        revalidate_m4c(args.out, args.jobs); print("M5A_M4C_REVALIDATED_GREEN 450"); return 0
    if args.action == "reproduce":
        require(args.examples is not None, "reproduce action needs --examples")
        answers = reproduce_examples(args.examples, args.out); print("M5A_EXAMPLES_GREEN", len(answers)); return 0
    require(args.action != "case" or args.case is not None, "case action needs --case")
    result = replay_case(args.case, args.mode, args.out) if args.action == "case" else run_batch(args.mode, args.out, args.jobs)
    print(f"M5A_REPLAY_GREEN steps={result['steps']} seconds={result['seconds']:.3f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
