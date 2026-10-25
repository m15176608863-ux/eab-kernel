"""Noncertified floating bottleneck diagnostics for exact SE(2) candidates.

Distances below are sampled/local-minimization estimates, not continuous
lower bounds. Labels use the original input vertex/edge indices and the
``_features`` convention VE=(moving vertex, fixed edge), EV=(moving edge,
fixed vertex). They identify nearby feature candidates, not exact incidences
or cone-certified contact covers. This tool never accepts an escape path.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as F
import json
import math
from pathlib import Path
import time

import numpy as np


def array(ring):
    return np.array([[float(F(x)), float(F(y))] for x, y in ring])


def transformed(piece, s):
    u = float(F(piece["u1"])) * s
    c = np.array([float(F(x)) for x in piece["center"]])
    d = np.array([float(F(x)) for x in piece["translation"]])
    rotation = np.array([[1 - u * u, -2 * u], [2 * u, 1 - u * u]]) / (1 + u * u)
    return (array(piece["start"]) - c) @ rotation.T + c + s * d


def vertex_edge_distances(vertices, polygon):
    edges = np.roll(polygon, -1, axis=0) - polygon
    offsets = vertices[:, None, :] - polygon[None, :, :]
    parameters = (offsets * edges[None, :, :]).sum(axis=2) / (edges * edges).sum(axis=1)[None, :]
    projections = polygon[None, :, :] + np.clip(parameters, 0, 1)[:, :, None] * edges[None, :, :]
    return np.linalg.norm(vertices[:, None, :] - projections, axis=2), parameters


def distances(piece, obstacles, s, labels=False):
    moving = transformed(piece, s)
    minimum = math.inf
    entries = []
    for obstacle_id, obstacle in enumerate(obstacles):
        ve, vp = vertex_edge_distances(moving, obstacle)
        ev, ep = vertex_edge_distances(obstacle, moving)
        minimum = min(minimum, float(ve.min()), float(ev.min()))
        if labels:
            for i in range(len(moving)):
                for j in range(len(obstacle)):
                    entries.append(dict(obstacle=obstacle_id, label=["VE", i, j],
                                        separation=float(ve[i, j]), projection=float(vp[i, j])))
                    entries.append(dict(obstacle=obstacle_id, label=["EV", i, j],
                                        separation=float(ev[j, i]), projection=float(ep[j, i])))
    if not labels:
        return minimum
    # This purely diagnostic grouping threshold must never reach a verifier.
    window = max(1e-8, minimum * 1e-5)
    active = [entry for entry in entries if entry["separation"] <= minimum + window]
    return minimum, active, window


def refine(piece, obstacles, left, right):
    ratio = (math.sqrt(5) - 1) / 2
    x = right - ratio * (right - left)
    y = left + ratio * (right - left)
    fx, fy = distances(piece, obstacles, x), distances(piece, obstacles, y)
    for _ in range(36):
        if fx <= fy:
            right, y, fy = y, x, fx
            x = right - ratio * (right - left)
            fx = distances(piece, obstacles, x)
        else:
            left, x, fx = x, y, fy
            y = left + ratio * (right - left)
            fy = distances(piece, obstacles, y)
    return (fx, x) if fx <= fy else (fy, y)


def segment_diagnostic(piece, obstacles, samples):
    times = np.linspace(0, 1, samples)
    sampled = [distances(piece, obstacles, float(s)) for s in times]
    # Always retain both endpoints. Bracket every sampled local minimum.
    candidates = [(distance, float(s)) for distance, s in zip(sampled, times)]
    refined_count = 0
    for i in range(1, samples - 1):
        if sampled[i] <= sampled[i - 1] and sampled[i] <= sampled[i + 1]:
            # Flat segments need no redundant local minimization.
            if sampled[i] == sampled[i - 1] == sampled[i + 1]:
                continue
            candidates.append(refine(piece, obstacles, float(times[i - 1]), float(times[i + 1])))
            refined_count += 1
    _, time_at_minimum = min(candidates)
    minimum, near, window = distances(piece, obstacles, time_at_minimum, labels=True)
    return dict(sampled_local_minimum_separation=minimum, time_estimate=time_at_minimum,
                near_feature_candidates=near, grouping_window_diagnostic_only=window,
                uniform_samples=samples, refined_sample_brackets=refined_count,
                certified_continuous_minimum=False)


def diagnose(path, samples):
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("status") != "PROPOSAL_UNVERIFIED" or not data.get("pieces"):
        return dict(case_id=data.get("case_id", path.stem), accepted=False,
                    status="NO_CANDIDATE_TO_DIAGNOSE", source=str(path))
    obstacles = tuple(array(ring) for ring in data["obstacles"])
    started = time.perf_counter()
    segments = []
    for index, piece in enumerate(data["pieces"]):
        segments.append(dict(segment_index=index, **segment_diagnostic(piece, obstacles, samples)))
    minimum = min(row["sampled_local_minimum_separation"] for row in segments)
    active_segments = [row["segment_index"] for row in segments
                       if row["sampled_local_minimum_separation"] <= minimum + max(1e-8, minimum * 1e-5)]
    active_combinations = [dict(segment_index=i, features=segments[i]["near_feature_candidates"])
                           for i in active_segments]
    return dict(case_id=data["case_id"], accepted=False,
                status="PENDING_EXACT_AND_INDEPENDENT_VERIFICATION", source=str(path),
                diagnostic_only=True, method="uniform samples plus golden-section refinement of sampled local minima",
                label_scope="near VE/EV candidates; not exact incidences or cone-certified covers",
                minimum_estimate=minimum, active_combinations=active_combinations,
                pose_diagnostic=data.get("diagnostic", {}), segments=segments,
                elapsed_s=time.perf_counter() - started)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("D:/eab-evidence/reports/codex/T2a_evidence/proposals"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--samples", type=int, default=65)
    args = parser.parse_args()
    if args.samples < 3:
        parser.error("samples must be at least three")
    files = sorted(args.input.glob("d[0-9][0-9].json")) + sorted(args.input.glob("k[0-9][0-9].json"))
    destination = args.output or args.input / "diagnostics.json"
    results = []
    for path in files:
        result = diagnose(path, args.samples)
        results.append(result)
        destination.write_text(json.dumps(dict(accepted=False, diagnostic_only=True, results=results),
                                          ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(dict(case_id=result["case_id"], status=result["status"],
                              minimum_estimate=result.get("minimum_estimate"),
                              elapsed_s=result.get("elapsed_s"))), flush=True)


if __name__ == "__main__":
    main()
