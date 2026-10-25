"""Untrusted SE(2) grid proposals for WO-T2a; never an escape verifier.

The floating SAT grid only chooses candidate poses. Every saved rational
segment still requires ``verify_se2_escape`` and the independent test oracle.
In particular, a failed search is UNPROVED, not a rigidity/trapping result.
The grid is centred at the exact input reference point: no start snapping.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as F
import json
import math
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.adapters.tia2d import tolerance_dovetail, tolerance_knob
from eab.kernel2d.erosion import erode_polygon_exact
from eab.kernel2d.se2 import SE2Motion, rotate_rational
from eab.kernel2d.translation_certificates import _pieces


CASES = (
    ("d01", "dovetail", "5/2", "3/2", "square", 0, "3/10", "1/3"),
    ("d02", "dovetail", "7/2", "3/2", "square", 0, "2/5", "1/2"),
    ("d03", "dovetail", "5/2", "1", "square", 0, "21/50", "3/7"),
    ("d04", "dovetail", "5/2", "1", "square", 1, "1/5", "3/14"),
    ("d05", "dovetail", "7/2", "3/2", "octagon", 0, "9/20", "24/41"),
    ("d06", "dovetail", "3", "1", "octagon", 0, "11/20", "24/41"),
    ("d07", "dovetail", "5/2", "3/2", "octagon", 0, "7/20", "24/65"),
    ("d08", "dovetail", "3", "3/2", "octagon", 1, "6/25", "12/49"),
    ("k01", "knob", "2", "1", "square", 0, "8/25", "1/3"),
    ("k02", "knob", "2", "1", "octagon", 0, "2/5", "12/29"),
)


def geometry(case):
    name, kind, wk, wn, element, walls, delta, threshold = case
    options = dict(head_width=F(wk), neck_width=F(wn), height=F(2), wall=F(2))
    raw = tolerance_dovetail(**options) if kind == "dovetail" else tolerance_knob(segments=4, **options)
    result = erode_polygon_exact(raw["moving"], F(delta), element)
    if result.status != "ACCEPTED":
        raise ValueError("moving erosion rejected: " + str(result.reason))
    obstacles = []
    for polygon in raw["obstacles"]:
        result_o = erode_polygon_exact(polygon, F(delta) if walls else F(0), element)
        if result_o.status != "ACCEPTED":
            raise ValueError("obstacle erosion rejected: " + str(result_o.reason))
        obstacles.append(result_o.polygon)
    return result.polygon, tuple(obstacles)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def log(output, **item):
    item["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with (output / "progress.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(item, ensure_ascii=False) + "\n")
        stream.flush()
    print(json.dumps(item, ensure_ascii=False), flush=True)


def normals(polygon):
    edges = np.roll(polygon, -1, axis=0) - polygon
    axes = np.stack((-edges[:, 1], edges[:, 0]), axis=1)
    return axes / np.linalg.norm(axes, axis=1)[:, None]


def separation_grid(first, second, xs, ys):
    """Diagnostic SAT separation for a pair of convex float polygons."""
    separation = np.full((len(xs), len(ys)), -np.inf)
    for axis in np.concatenate((normals(first), normals(second))):
        a, b = first @ axis, second @ axis
        shift = xs[:, None] * axis[0] + ys[None, :] * axis[1]
        gap = np.maximum(b.min() - a.max() - shift, a.min() + shift - b.max())
        np.maximum(separation, gap, out=separation)
    return separation


def build_grid(moving, obstacles, step, output, case, max_cells):
    centre = tuple(sum(p[k] for p in moving) / len(moving) for k in (0, 1))
    local = tuple((p[0] - centre[0], p[1] - centre[1]) for p in moving)
    vertices = np.array(local, dtype=float)
    radius = float(np.linalg.norm(vertices, axis=1).max())
    h = float(step)
    n = max(1, math.ceil(2 * radius / h))
    # A full half-turn interval [-90,90] suffices as a proposal domain only.
    # Its artificial boundary is never used as evidence of non-escape.
    half_width = max(abs(float(p[0] - centre[0])) for p in moving) + 0.7
    ilo, ihi = -math.ceil(half_width / h), math.ceil(half_width / h)
    jlo = math.floor((-0.25 - float(centre[1])) / h)
    wall_top = max(p[1] for polygon in obstacles for p in polygon)
    jhi = math.ceil((float(wall_top) + radius + 0.2 - float(centre[1])) / h)
    shape = (2 * n + 1, ihi - ilo + 1, jhi - jlo + 1)
    cells = math.prod(shape)
    if cells > max_cells:
        return None, dict(reason="grid_resource_limit", grid_shape=shape, cells=cells)
    xs = float(centre[0]) + np.arange(ilo, ihi + 1) * h
    ys = float(centre[1]) + np.arange(jlo, jhi + 1) * h
    moving_parts = tuple(np.array([(p[0] - centre[0], p[1] - centre[1]) for p in part], dtype=float)
                         for part in _pieces(moving))
    obstacle_parts = tuple(np.array(part, dtype=float) for polygon in obstacles for part in _pieces(polygon))
    free = np.ones(shape, dtype=bool)
    escape_j = []
    start_time = time.perf_counter()
    for index, k in enumerate(range(-n, n + 1)):
        u = k / n
        rotation = np.array([[1 - u * u, -2 * u], [2 * u, 1 - u * u]]) / (1 + u * u)
        for part in moving_parts:
            rotated = part @ rotation.T
            for obstacle in obstacle_parts:
                free[index] &= separation_grid(rotated, obstacle, xs, ys) > 0.55 * h
        bottom = float((vertices @ rotation.T)[:, 1].min())
        escape_j.append(int(np.searchsorted(ys, float(wall_top) - bottom + 2 * h, side="right")))
        if index % 50 == 0 or index == shape[0] - 1:
            log(output, case=case, phase="occupancy", step=str(step), layer=index + 1,
                layers=shape[0], elapsed_s=time.perf_counter() - start_time)
    spec = dict(n=n, ilo=ilo, jlo=jlo, centre=centre, local=local,
                shape=shape, step=step, wall_top=wall_top, escape_j=np.array(escape_j))
    return (free, spec), dict(grid_shape=shape, cells=cells, occupancy_s=time.perf_counter() - start_time)


def flood(free, spec, output, case):
    """Six-neighbour flood with a parent for every visited configuration."""
    nt, nx, ny = free.shape
    plane = nx * ny
    n, ilo, jlo = spec["n"], spec["ilo"], spec["jlo"]
    start = n * plane + (-ilo) * ny + (-jlo)
    available = free.reshape(-1)
    if not available[start]:
        return None, dict(reason="origin_not_in_diagnostic_margin")
    parents = np.full(available.size, -1, dtype=np.int32)
    parents[start] = start
    frontier = np.array([start], dtype=np.int32)
    goal = None
    iterations = 0
    visited = 1
    begin = time.perf_counter()
    while frontier.size:
        k = frontier // plane
        i = (frontier // ny) % nx
        j = frontier % ny
        hit = frontier[j >= spec["escape_j"][k]]
        if hit.size:
            goal = int(hit[0])
            break
        directions = ((ny, i + 1 < nx), (-ny, i > 0),
                      (1, j + 1 < ny), (-1, j > 0),
                      (plane, k + 1 < nt), (-plane, k > 0))
        following = []
        for offset, mask in directions:
            origins = frontier[mask]
            destinations = origins + offset
            keep = available[destinations] & (parents[destinations] == -1)
            origins, destinations = origins[keep], destinations[keep]
            parents[destinations] = origins
            following.append(destinations)
        frontier = np.concatenate(following)
        visited += len(frontier)
        iterations += 1
        if iterations % 100 == 0:
            log(output, case=case, phase="flood", step=str(spec["step"]),
                layers=iterations, frontier=len(frontier), visited=visited,
                elapsed_s=time.perf_counter() - begin)
    stats = dict(flood_layers=iterations, visited=visited, flood_s=time.perf_counter() - begin)
    if goal is None:
        stats["reason"] = "no_grid_path_found_not_a_trapping_conclusion"
        return None, stats
    path = [goal]
    while path[-1] != start:
        path.append(int(parents[path[-1]]))
    path.reverse()
    return [(p // plane - n, (p // ny) % nx + ilo, p % ny + jlo) for p in path], stats


def direction(a, b):
    return tuple(b[k] - a[k] for k in range(3))


def rationalize(path, spec):
    """Exact grid poses, Cayley angle subtraction, and same-direction merging."""
    n, step, centre, local = spec["n"], spec["step"], spec["centre"], spec["local"]

    def pose(node):
        k, i, j = node
        u = F(k, n)
        c = (centre[0] + i * step, centre[1] + j * step)
        return tuple((c[0] + p[0], c[1] + p[1]) for p in (rotate_rational(v, u) for v in local))

    runs = []
    for a, b in zip(path, path[1:]):
        step_direction = direction(a, b)
        merge = bool(runs and runs[-1][2] == step_direction)
        if merge and step_direction[0]:
            ua, ub = F(runs[-1][0][0], n), F(b[0], n)
            denominator = 1 + ua * ub
            merge = denominator != 0 and abs((ub - ua) / denominator) <= 1
        if merge:
            runs[-1][1] = b
        else:
            runs.append([a, b, step_direction])
    pieces = []
    for a, b, change in runs:
        if change[0]:
            ua, ub = F(a[0], n), F(b[0], n)
            motion = SE2Motion((ub - ua) / (1 + ua * ub), (F(0), F(0)),
                               (centre[0] + a[1] * step, centre[1] + a[2] * step))
        else:
            motion = SE2Motion(F(0), ((b[1] - a[1]) * step, (b[2] - a[2]) * step))
        start, end = pose(a), pose(b)
        # This is an arithmetic serialization sanity check, not collision QA.
        if tuple(motion.endpoint(p) for p in start) != end:
            raise ArithmeticError("rational pose continuity failure")
        pieces.append(dict(start=start, u1=motion.u1, translation=motion.translation,
                           center=motion.center, end=end))
    return pieces


def strings(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {k: strings(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [strings(v) for v in value]
    return value


def propose(case, steps, output, max_cells):
    name, kind, wk, wn, element, wall_policy, delta, threshold = case
    moving, obstacles = geometry(case)
    answer = dict(schema="t2a-untrusted-se2-proposal-1", case_id=name,
                  status="UNPROVED", source="fresh_origin_centred_cayley_grid",
                  geometry=dict(kind=kind, head_width=wk, neck_width=wn, height="2", wall="2",
                                element=element, wall_erosion=wall_policy, delta=delta),
                  translation_threshold=threshold, moving=moving, obstacles=obstacles, attempts=[])
    destination = output / (name + ".json")
    for step in steps:
        log(output, case=name, phase="start_grid", step=str(step))
        grid, stats = build_grid(moving, obstacles, step, output, name, max_cells)
        attempt = dict(step=str(step), **stats)
        answer["attempts"].append(attempt)
        if grid is None:
            write_json(destination, strings(answer))
            continue
        free, spec = grid
        path, flood_stats = flood(free, spec, output, name)
        attempt.update(flood_stats)
        if path is None:
            write_json(destination, strings(answer))
            continue
        pieces = rationalize(path, spec)
        if not pieces or pieces[0]["start"] != moving:
            raise ArithmeticError("proposal must start at exact input pose")
        endpoint = pieces[-1]["end"]
        ray_length = 1 + sum(max(abs(p[k]) for ring in (*obstacles, endpoint) for p in ring)
                             for k in (0, 1)) * 8
        answer.update(status="PROPOSAL_UNVERIFIED", pieces=pieces,
                      ray_path=((F(0), F(0)), (F(0), ray_length)),
                      exact_start_equal=True, continuity_equal=True,
                      diagnostic=dict(grid_nodes=len(path), segment_count=len(pieces),
                                      maximum_absolute_angle_degrees=max(abs(math.degrees(2 * math.atan(p[0] / spec["n"]))) for p in path),
                                      endpoint_minimum_y_above_walls=str(min(p[1] for p in endpoint) - spec["wall_top"]),
                                      clearance_margin_grid_only=0.55 * float(step)))
        write_json(destination, strings(answer))
        log(output, case=name, phase="proposal_saved", step=str(step), segments=len(pieces),
            path=str(destination), status=answer["status"])
        return answer
    log(output, case=name, phase="search_finished", status="UNPROVED", path=str(destination))
    return answer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", nargs="+", default=["d01", "d07", "d02", "d03", "d04", "d05", "d06", "d08", "k01", "k02"])
    parser.add_argument("--steps", nargs="+", default=["1/50", "1/100", "1/200"])
    parser.add_argument("--output", type=Path, default=Path("D:/eab-evidence/reports/codex/T2a_evidence/proposals"))
    parser.add_argument("--max-cells", type=int, default=180_000_000)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cases = {case[0]: case for case in CASES}
    for name in args.cases:
        if name not in cases:
            parser.error("unknown case: " + name)
        propose(cases[name], tuple(F(step) for step in args.steps), args.output, args.max_cells)
        results = []
        for identifier in cases:
            path = args.output / (identifier + ".json")
            if path.exists():
                result = json.loads(path.read_text(encoding="utf-8"))
                results.append(dict(case_id=identifier, status=result["status"], file=path.name))
        write_json(args.output / "index.json", dict(status="UNTRUSTED_PROPOSALS_ONLY", results=results))


if __name__ == "__main__":
    main()
