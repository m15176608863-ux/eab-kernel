"""Bounded, untrusted fine-grid escape proposals for WO-T2c1.

A sparse tube around a previous path replaces the full cubic grid. The grid
and its SAT margins only select rational candidate data. Search exhaustion is
UNPROVED, never trapping. The unchanged independent oracle checks finite SE2
and tail-prefix segments only; no result here claims an independent infinite
ray proof. New table upper endpoints therefore require an owner scope ruling.
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from fractions import Fraction as F
import json
import math
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools"), str(ROOT / "tests")]

from eab.kernel2d.se2 import SE2Motion
from eab.kernel2d.se2_paths import SE2EscapePath, verify_se2_escape
from eab.kernel2d.translation_certificates import _pieces
from t2_se2_grid import CASES, geometry, normals, rationalize, strings
from t2a_oracle_audit import validate_escape_segments


@dataclass(frozen=True)
class EscapeResources:
    """Cooperative proposal limits; exact audits are separately timed.

    A single vector operation may overrun the deadline, but an overdue
    candidate is discarded. Tube width and half-turn domain are proposal
    restrictions, never evidence that an escape path cannot exist.
    """
    max_seconds: float = 180.0
    max_cells: int = 750000
    max_path_nodes: int = 200000
    tube_radius: int = 3
    tube_radii: tuple = ()
    steps: tuple = (F(1, 100), F(1, 200), F(1, 400))
    extra_height: F = F(1)


class SearchLimit(Exception):
    pass


def _check(deadline):
    if time.perf_counter() > deadline:
        raise SearchLimit("elapsed_time_limit")


def _ring(value):
    return tuple(tuple(F(x) for x in point) for point in value)


def _load_seed(seed):
    if isinstance(seed, (str, Path)):
        return json.loads(Path(seed).read_text(encoding="utf-8"))
    return seed


def _write(path, value):
    with Path(path).open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(strings(value), ensure_ascii=False, indent=2) + "\n")


def _progress(output, **record):
    if output is None:
        return
    with (Path(output) / "progress.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(strings(record), ensure_ascii=False) + "\n")
        stream.flush()


def _seed_waypoints(seed):
    """Read exact absolute Cayley turns and reference displacements."""
    moving = _ring(seed["moving"])
    origin = tuple(sum(p[k] for p in moving) / len(moving) for k in (0, 1))
    point, u = origin, F(0)
    result = [(F(0), F(0), F(0))]
    current = moving
    for piece in seed["pieces"]:
        if _ring(piece["start"]) != current:
            raise ValueError("seed path is not joined to its exact source pose")
        motion = SE2Motion(F(piece["u1"]), tuple(F(x) for x in piece["translation"]),
                           tuple(F(x) for x in piece["center"]))
        end = tuple(motion.endpoint(p) for p in current)
        if end != _ring(piece["end"]):
            raise ValueError("seed endpoint differs from its motion")
        denominator = 1-u*motion.u1
        if denominator == 0:
            raise ValueError("seed leaves the half-turn proposal chart")
        u = (u+motion.u1)/denominator
        if abs(u) > 1:
            raise ValueError("seed leaves the half-turn proposal chart")
        point = motion.endpoint(point)
        result.append((u, point[0]-origin[0], point[1]-origin[1]))
        current = end
    return result


def _guide(waypoints, n, step, extra_height, max_nodes, deadline):
    nodes = [(round(u*n), round(x/step), round(y/step)) for u, x, y in waypoints]
    nodes.append((nodes[-1][0], nodes[-1][1], nodes[-1][2]+math.ceil(extra_height/step)))
    guide = [nodes[0]]
    for start, end in zip(nodes, nodes[1:]):
        count = max(abs(end[k]-start[k]) for k in range(3))
        if len(guide)+count > max_nodes:
            raise SearchLimit("guide_node_limit")
        _check(deadline)
        for index in range(1, count+1):
            guide.append(tuple(start[k]+round(F(index, count)*(end[k]-start[k])) for k in range(3)))
    return guide


def _tube(guide, n, radius, max_cells, deadline):
    layers = {}
    count = 0
    for index, (k, x, y) in enumerate(guide):
        if index % 128 == 0:
            _check(deadline)
        for dk in range(-radius, radius+1):
            if not -n <= k+dk <= n:
                continue
            points = layers.setdefault(k+dk, set())
            before = len(points)
            for dx in range(-radius, radius+1):
                for dy in range(-radius, radius+1):
                    points.add((x+dx, y+dy))
            count += len(points)-before
            if count > max_cells:
                raise SearchLimit("tube_cell_limit")
    return layers, count


def _free_tube(moving, obstacles, centre, layers, n, step, deadline, output):
    """Floating SAT only; points passing it are still unverified proposals."""
    moving_parts = tuple(np.array([(p[0]-centre[0], p[1]-centre[1]) for p in part], dtype=float)
                         for part in _pieces(moving))
    obstacle_parts = tuple(np.array(part, dtype=float) for polygon in obstacles for part in _pieces(polygon))
    free = set()
    h = float(step)
    for ordinal, k in enumerate(sorted(layers)):
        _check(deadline)
        nodes = sorted(layers[k])
        points = np.array(nodes, dtype=float)*h+np.array(centre, dtype=float)
        u = k/n
        rotation = np.array([[1-u*u, -2*u], [2*u, 1-u*u]])/(1+u*u)
        allowed = np.ones(len(nodes), dtype=bool)
        for original in moving_parts:
            part = original @ rotation.T
            for obstacle in obstacle_parts:
                separation = np.full(len(nodes), -np.inf)
                for axis in np.concatenate((normals(part), normals(obstacle))):
                    a, b = part @ axis, obstacle @ axis
                    shift = points @ axis
                    gap = np.maximum(b.min()-a.max()-shift, a.min()+shift-b.max())
                    np.maximum(separation, gap, out=separation)
                allowed &= separation > 0.55*h
        free.update((k, nodes[index][0], nodes[index][1]) for index in np.flatnonzero(allowed))
        if ordinal % 128 == 0:
            _progress(output, phase="sparse_occupancy", step=step, layer=ordinal,
                      layers=len(layers), free_cells=len(free))
    _check(deadline)
    return free


def _flood(free, local, centre, wall_top, n, step, resources, deadline):
    start = (0, 0, 0)
    if start not in free:
        return None, {"reason": "origin_not_in_diagnostic_margin", "visited": 0}
    parents = {start: start}
    queue = deque((start,))
    bottom = {}
    goal = None
    iterations = 0
    while queue:
        iterations += 1
        if iterations % 128 == 0:
            _check(deadline)
        node = queue.popleft()
        k, i, j = node
        if k not in bottom:
            u = F(k, n)
            bottom[k] = min((2*u*x+(1-u*u)*y)/(1+u*u) for x, y in local)
        if centre[1]+j*step+bottom[k] > wall_top+2*step:
            goal = node
            break
        for change in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            following = tuple(node[index]+change[index] for index in range(3))
            if following in free and following not in parents:
                parents[following] = node
                queue.append(following)
    stats = {"visited": len(parents), "reason": "no_tube_path_found_not_a_trapping_conclusion"}
    if goal is None:
        return None, stats
    path = [goal]
    while path[-1] != start:
        path.append(parents[path[-1]])
        if len(path) > resources.max_path_nodes:
            raise SearchLimit("path_node_limit")
    path.reverse()
    stats["reason"] = "unverified_grid_path"
    return path, stats


def propose_escape(case_id, delta, seed, *, resources=EscapeResources(), output=None):
    """Propose at one delta; returns no mathematical escape decision."""
    if resources.tube_radius < 0 or any(r < 0 for r in resources.tube_radii) or any(step <= 0 for step in resources.steps):
        raise ValueError("tube radius must be nonnegative and steps positive")
    if output is not None:
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    deadline = started+resources.max_seconds
    case = list(next(row for row in CASES if row[0] == case_id))
    case[6] = str(F(delta))
    moving, obstacles = geometry(tuple(case))
    centre = tuple(sum(p[k] for p in moving)/len(moving) for k in (0, 1))
    local = tuple((p[0]-centre[0], p[1]-centre[1]) for p in moving)
    seed = _load_seed(seed)
    waypoints = _seed_waypoints(seed)
    wall_top = max(p[1] for polygon in obstacles for p in polygon)
    answer = dict(schema="t2c1-untrusted-escape-1", case_id=case_id, delta=F(delta),
                  moving=moving, obstacles=obstacles, status="UNPROVED", attempts=[],
                  source="t2a_origin_centred_sparse_cayley_tube",
                  search_failure_is_not_a_trapping_proof=True)
    for step, radius_cells in ((step, radius) for step in resources.steps
                               for radius in (resources.tube_radii or (resources.tube_radius,))):
        attempt = dict(step=step, tube_radius_cells=radius_cells,
                       artificial_boundary="half_turn_and_seed_tube_not_a_proof")
        answer["attempts"].append(attempt)
        try:
            _check(deadline)
            radius = max(math.hypot(float(x), float(y)) for x, y in local)
            n = max(1, math.ceil(2*radius/float(step)))
            guide = _guide(waypoints, n, step, resources.extra_height, resources.max_cells, deadline)
            layers, cells = _tube(guide, n, radius_cells, resources.max_cells, deadline)
            attempt.update(cells=cells, angle_denominator=n, guide_nodes=len(guide))
            free = _free_tube(moving, obstacles, centre, layers, n, step, deadline, output)
            attempt["free_cells"] = len(free)
            path, stats = _flood(free, local, centre, wall_top, n, step, resources, deadline)
            attempt.update(stats)
            if path is not None:
                pieces = rationalize(path, dict(n=n, step=step, centre=centre, local=local))
                if not pieces or pieces[0]["start"] != moving:
                    raise ArithmeticError("grid proposal lost exact source pose")
                endpoint = pieces[-1]["end"]
                ray_length = 1+sum(max(abs(p[k]) for ring in (*obstacles, endpoint) for p in ring)
                                   for k in (0, 1))*8
                _check(deadline)
                answer.update(status="PROPOSAL_UNVERIFIED", pieces=pieces,
                              ray_path=((F(0), F(0)), (F(0), ray_length)),
                              diagnostic=dict(grid_nodes=len(path), segment_count=len(pieces),
                                              actual_grid_step=step))
                break
        except SearchLimit as error:
            attempt["reason"] = str(error)
            if str(error) == "elapsed_time_limit":
                break
        _progress(output, phase="proposal_attempt", case_id=case_id, delta=delta, **attempt)
    answer["seconds"] = time.perf_counter()-started
    if output is not None:
        _write(output / "proposal.json", answer)
    return answer


def audit_proposal(instance, candidate):
    """Call unchanged production and finite independent entries, without overclaim.

    The explicit false independent-infinite flag is an acceptance boundary,
    not a missing display value. Gate: test_finite_oracle_scope_is_not_escape.
    """
    moving, obstacles = _ring(candidate["moving"]), tuple(_ring(p) for p in candidate["obstacles"])
    if moving != instance["moving"] or obstacles != instance["obstacles"]:
        raise ValueError("proposal geometry differs from supplied instance")
    pieces = candidate["pieces"]
    poses = [moving]
    motions, specs = [], []
    for piece in pieces:
        if _ring(piece["start"]) != poses[-1]:
            raise ValueError("proposal path has a discontinuous start")
        spec = (F(piece["u1"]), tuple(F(x) for x in piece["translation"]),
                tuple(F(x) for x in piece["center"]))
        specs.append(spec)
        motions.append(SE2Motion(*spec))
        poses.append(_ring(piece["end"]))
    path = SE2EscapePath(tuple(poses), tuple(motions))
    ray = tuple(tuple(F(x) for x in point) for point in candidate["ray_path"])
    started = time.perf_counter()
    production = verify_se2_escape(moving, obstacles, path, ray)
    production_record = dict(valid=production.valid, reason=production.reason,
                             checked_segments=production.checked_segments, checked_pairs=production.checked_pairs,
                             ray_valid=bool(production.ray_verification and production.ray_verification.valid),
                             seconds=time.perf_counter()-started)
    production_record["pairs"] = [dict(segment=i, obstacle=j, status=result.status,
        initial_state=result.initial_state, end_state=result.end_state,
        immediate=result.immediate, touches_end=result.touches_end,
        incidences=result.incidences, features=result.features,
        exact_time=None if result.exact_time is None else str(result.exact_time))
        for i, row in enumerate(production.segment_results) for j, result in enumerate(row)]
    started = time.perf_counter()
    independent = validate_escape_segments(moving, obstacles, tuple(specs), ray)
    independent_seconds = time.perf_counter()-started
    if independent["infinite_ray_verified"]:
        raise AssertionError("unchanged finite oracle unexpectedly claims an infinite ray")
    finite_disagreement = (production.valid and not independent["valid"]) or (
        independent["valid"] and any(result.status != "FREE"
                                     for row in production.segment_results for result in row))
    if finite_disagreement:
        raise RuntimeError("finite_verifier_disagreement: " + json.dumps(
            {"production": asdict(production), "independent": independent,
             "input_evidence": "preserve the proposal.json written before this audit"},
            default=str, sort_keys=True))
    valid = production.valid and independent["valid"]
    return dict(status="FINITE_ORACLE_VERIFIED" if valid else "UNPROVED",
                finite_and_production_valid=valid, eligible_new_upper=False,
                production=production_record, independent=independent,
                independent_seconds=independent_seconds,
                acceptance_scope="production_infinite_ray_plus_independent_finite_only",
                pending_owner_scope_ruling=True)


def refine_escape(case_id, lower, upper, seed, *, exponent=12, max_probes=12,
                  resources=EscapeResources(), output=None):
    """Downward binary-grid exploration; never promote a failed-search lower.

    Pending the independent-infinite scope ruling, even successful smaller
    candidates are exploratory only; certified_upper remains the input upper.
    """
    if not 1 <= exponent <= 16 or not F(lower) < F(upper):
        raise ValueError("require exponent in 1..16 and lower < upper")
    if output is not None:
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)
    denominator = 2**exponent
    low = math.floor(F(lower)*denominator)
    high = math.ceil(F(upper)*denominator)
    best_delta, best = F(upper), _load_seed(seed)
    probes = []
    for index in range(max_probes):
        if high-low <= 1:
            break
        middle = (low+high)//2
        delta = F(middle, denominator)
        destination = None if output is None else output / ("probe_"+str(index))
        candidate = propose_escape(case_id, delta, best, resources=resources, output=destination)
        record = dict(delta=delta, proposal_status=candidate["status"], attempts=candidate["attempts"])
        accepted = False
        if candidate["status"] == "PROPOSAL_UNVERIFIED":
            audit = audit_proposal(dict(moving=candidate["moving"], obstacles=candidate["obstacles"]), candidate)
            record["audit"] = audit
            accepted = audit["finite_and_production_valid"]
            if destination is not None:
                _write(destination / "audit.json", audit)
        if accepted:
            high, best_delta, best = middle, delta, candidate
        else:
            low = middle
        record["failed_search_does_not_raise_certified_lower"] = True
        probes.append(record)
        _progress(output, phase="downward_exploration", case_id=case_id, delta=delta,
                  proposal_status=candidate["status"], finite_and_production_valid=accepted)
    answer = dict(case_id=case_id, certified_lower=F(lower), certified_upper=F(upper),
                  exploratory_upper=best_delta, eligible_new_upper=False,
                  status="FINITE_ORACLE_VERIFIED" if best_delta < F(upper) else "UNPROVED",
                  grid_exponent=exponent, probes=probes, candidate=best,
                  unproved_search_boundary=F(low, denominator))
    if output is not None:
        _write(output / "refinement.json", answer)
    return answer
