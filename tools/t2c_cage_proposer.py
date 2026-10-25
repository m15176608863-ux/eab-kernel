"""Bounded, untrusted T2c cage proposals; the unchanged v5 verifier decides.

A failed cap, slice, connection, or resource check returns UNPROVED. Exact
arithmetic below constructs candidate data; it is not a replacement verifier.
Tests: test_t2c1_cage.py exercises non-origin/multistage caps, varying barriers,
rotation-only full-circle closure, mixed kernels and finite resource exits.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
import time

import t2b_cage_proposer as old
from eab.kernel2d.se2_cage import verify_se2_cage


@dataclass(frozen=True)
class CageResources(old.CageResources):
    max_intervals: int = 256
    max_targets: int = 12
    max_adaptive_steps: int = 256
    max_local_sweeps: int = 64
    max_state_seconds: float = 3.0


def _mean(points):
    return tuple(sum((p[k] for p in points), F(0))/len(points) for k in (0, 1))


def _winding(loop, point):
    number = 0
    for a, b in zip(loop, loop[1:]):
        ax, ay = a[0]-point[0], a[1]-point[1]
        bx, by = b[0]-point[0], b[1]-point[1]
        cross = ax*by-ay*bx
        if cross == 0 and ax*bx+ay*by <= 0:
            return None
        if ay <= 0 < by and cross > 0:
            number += 1
        if by <= 0 < ay and cross < 0:
            number -= 1
    return number


def _depth(cells, point):
    """Squared strict-cover clearance, used solely to rank candidate points."""
    depths = []
    px, py = F(point[0]), F(point[1])
    for cell in cells:
        if old._inside(cell, point):
            distances = []
            for nx, ny, bound in cell[2]:
                x, y, b = F(nx), F(ny), F(bound)
                gap = x*px+y*py+b
                distances.append(gap*gap/(x*x+y*y))
            depths.append(min(distances))
    return max(depths, default=F(0))

def _cap_targets(loop, cells, resources):
    """Rank covered points inside Gamma, not a distinguished coordinate origin."""
    candidates = {_mean(loop[:-1])}
    candidates.update(_mean(cell[0]) for cell in cells)
    first = loop[0]
    candidates.update(_mean((first, a, b)) for a, b in zip(loop[1:-1], loop[2:]))
    for a, b in zip(loop, loop[1:]):
        candidates.add(_mean((a, b, _mean(loop[:-1]))))
    accepted = [(point, _depth(cells, point)) for point in candidates
                if _winding(loop, point) not in (None, 0)]
    accepted = [item for item in accepted if item[1] > 0]
    accepted.sort(key=lambda item: (-item[1], item[0]))
    return tuple(item[0] for item in accepted[:resources.max_targets])


def _strip_witnesses(first, following, cells):
    row = []
    for index, (a, b, d, c) in enumerate(zip(first, first[1:], following, following[1:])):
        witness = old._witness(cells, (a, b, c, d))
        if witness is None:
            return None, {"segment": index, "points": (a, b, c, d),
                          "candidate_labels": [cell[3] for cell in cells
                                               if old._inside(cell, a)]}
        row.append(witness)
    return row, None


def _local_contract(loop, target, cells, resources, deadline):
    """Piecewise contraction via covered ears, followed by a covered point.

    Each changed vertex is checked with its two incident segments. A sweep is
    stored only after every simultaneous quadrilateral has an explicit strict
    cover witness. Unsuccessful local shortening has no topological status.
    """
    chain, rows = [loop], []
    count = len(loop)-1
    failed = None
    for sweep in range(min(resources.max_local_sweeps, resources.max_cap_steps)):
        old._check_time(deadline)
        current = chain[-1]
        constant = (target,)*len(current)
        row, failed = _strip_witnesses(current, constant, cells)
        if row is not None:
            return {"chain": chain+[constant], "witnesses": rows+[row]}, "local_cap_proposed"
        following = list(current[:-1])
        changed = False
        for index in range(count):
            previous = following[(index-1) % count]
            vertex = following[index]
            after = following[(index+1) % count]
            candidates = (target, after, _mean((previous, after)),
                          _mean((vertex, target)), _mean((vertex, previous, after)))
            for candidate in candidates:
                if candidate == vertex:
                    continue
                if old._witness(cells, (previous, vertex, candidate)) is None:
                    continue
                if old._witness(cells, (vertex, after, candidate)) is None:
                    continue
                trial = tuple(following[:index]+[candidate]+following[index+1:])
                trial += (trial[0],)
                row, failed = _strip_witnesses(current, trial, cells)
                if row is None:
                    continue
                following[index] = candidate
                changed = True
                break
        if not changed:
            return None, {"reason": "local_cap_stalled", "where": failed,
                          "sweeps": sweep, "target": target}
        following = tuple(following)+(following[0],)
        row, failed = _strip_witnesses(current, following, cells)
        if row is None:
            return None, {"reason": "local_cap_strip_missing", "where": failed}
        chain.append(following)
        rows.append(row)
    return None, {"reason": "local_cap_step_limit", "where": failed, "target": target}


def _cap(loop, cells, resources, deadline):
    middle = _mean(loop[:-1])
    probes = [middle, (F(0), F(0))]
    probes.extend(_mean((middle, a, b)) for a, b in zip(loop, loop[1:]))
    for probe in probes:
        if _winding(loop, probe) not in (None, 0) and old._witness(cells, (probe,)) is None:
            return None, {"reason": "cap_interior_free_probe", "probe": probe}
    targets = _cap_targets(loop, cells, resources)
    if not targets:
        return None, {"reason": "no_strictly_covered_interior_target"}
    failure = None
    for target in targets:
        old._check_time(deadline)
        # Attempt one direct strip first. There is no hard-coded origin test.
        constant = (target,)*len(loop)
        row, failure = _strip_witnesses(loop, constant, cells)
        if row is not None:
            return {"chain": [loop, constant], "witnesses": [row]}, "nonorigin_target_cap_proposed"
        cap, failure = _local_contract(loop, target, cells, resources, deadline)
        if cap is not None:
            return cap, "nonorigin_multistage_cap_proposed"
    return None, {"reason": "cap_contraction_unproved", "detail": failure,
                  "targets_tried": len(targets)}


def _aligned_loops(loops, resources):
    """Monotone edge-index correspondence, padded with repeated vertices.

    All original vertices/edges are retained. No vertex is dropped to reconcile
    different barrier lengths. Repetitions encode stationary vertices in V5.
    """
    prepared = []
    for loop in loops:
        points = list(loop[:-1])
        area = sum(a[0]*b[1]-a[1]*b[0] for a, b in old._edges(tuple(points)))
        if area < 0:
            points.reverse()
        anchor = prepared[0][0] if prepared else min(points)
        scores = tuple((old._norm2((point[0]-anchor[0], point[1]-anchor[1])), i)
                       for i, point in enumerate(points))
        first = min(scores)[1]
        ring = tuple(points[first:]+points[:first])
        prepared.append(ring+(ring[0],))
    parameters = sorted({F(i, len(loop)-1) for loop in prepared
                         for i in range(len(loop))})
    if len(parameters) > resources.max_loop_vertices:
        raise old.SearchLimit("aligned_loop_vertex_limit")
    result = []
    for loop in prepared:
        count = len(loop)-1
        row = []
        for value in parameters:
            index = (value*count).numerator//(value*count).denominator
            row.append(loop[min(index, count)])
        result.append(tuple(row))
    return tuple(result)


def _connection_cells(base, intervals, knots, at, resources, deadline):
    count = len(intervals)
    left, right = at-1, at % count
    value = knots[at]
    lo, hi = knots[at-1], knots[at]
    exact = tuple(old._world(old._rotate(old._local(part, base["center"]), value, lo, hi),
                             base["center"]) for part in base["moving_pieces"])
    polygons = list(exact)
    references = [["exact", i] for i in range(len(exact))]
    if base["disk"] is not None:
        polygons.append(old._world(base["disk"]["polygon"], base["center"]))
        references.append(["disk"])
    for label, index in (("left", left), ("right", right)):
        polys = old._kernel_polygons(intervals[index], base["disk"], base["center"])
        polygons.extend(polys)
        references.extend([label, i] for i in range(len(polys)))
    return old._cells(polygons, base["obstacle_pieces"], resources, deadline, references)


def _cap_cells(base, knots, at, resources, deadline):
    lo, hi = (knots[0], knots[1]) if at == 0 else (knots[-2], knots[-1])
    value = knots[at]
    polygons = tuple(old._world(old._rotate(old._local(part, base["center"]), value, lo, hi),
                                base["center"]) for part in base["moving_pieces"])
    return old._cells(polygons, base["obstacle_pieces"], resources, deadline,
                      [["exact", i] for i in range(len(polygons))])


def _interval_data(base, lo, hi, resources, deadline, mixed):
    disk = base["disk"] if mixed else None
    interval = old._interval(base["moving_pieces"], base["center"], base["radius"], lo, hi, disk)
    if interval is None:
        return None, {"reason": "contracted_piece_empty", "lambda_interval": (lo, hi)}
    cells = old._cells(old._kernel_polygons(interval, disk, base["center"]),
                       base["obstacle_pieces"], resources, deadline)
    loop = old._barrier(tuple(cell[0] for cell in cells))
    if not loop:
        return None, {"reason": "V4_no_winding_barrier", "lambda_interval": (lo, hi),
                      "rho": interval["rho"], "candidate_labels": [cell[3] for cell in cells]}
    for _ in range(resources.max_refinements+1):
        if len(loop) > resources.max_loop_vertices:
            break
        row = old._loop_witnesses(loop, cells)
        if row is not None:
            return (interval, cells, loop), None
        loop = old._refine_loop(loop)
    return None, {"reason": "V4_segment_witness_missing", "lambda_interval": (lo, hi),
                  "rho": interval["rho"]}


def _candidate(base, knots, kind, resources, deadline, cache, mixed):
    intervals, interval_cells, loops = [], [], []
    for index, (lo, hi) in enumerate(zip(knots, knots[1:])):
        old._check_time(deadline)
        if (lo, hi) not in cache:
            cache[lo, hi] = _interval_data(base, lo, hi, resources, deadline, mixed)
        data, failure = cache[lo, hi]
        if data is None:
            return None, {**failure, "interval": index, "stage": "V1_V4"}
        interval, cells, loop = data
        intervals.append(interval)
        interval_cells.append(cells)
        loops.append(loop)
    count = len(intervals)
    loops = _aligned_loops(loops, resources)
    last_failure = None
    for refinement in range(resources.max_refinements+1):
        if len(loops[0]) > resources.max_loop_vertices:
            raise old.SearchLimit("loop_vertex_limit")
        rows = [old._loop_witnesses(loop, cells)
                for loop, cells in zip(loops, interval_cells)]
        if any(row is None for row in rows):
            loops = tuple(old._refine_loop(loop) for loop in loops)
            continue
        links = []
        end = count+1 if kind == "closed" else count
        for at in range(1, end):
            old._check_time(deadline)
            cells = _connection_cells(base, intervals, knots, at, resources, deadline)
            first, following = loops[at-1], loops[at % count]
            link, failure = old._connect(first, following, cells, resources, deadline)
            if link is None:
                last_failure = {"reason": "V5_connection_unproved", "interval": at-1,
                                "at": at, "detail": failure}
                break
            links.append({"at": at, **link})
        if len(links) != end-1:
            loops = tuple(old._refine_loop(loop) for loop in loops)
            continue
        caps = []
        if kind == "capped":
            for at, loop in ((0, loops[0]), (count, loops[-1])):
                cells = _cap_cells(base, knots, at, resources, deadline)
                probe = (F(0), F(0))
                if _winding(loop, probe) not in (None, 0) and old._witness(cells, (probe,)) is None:
                    return None, {"reason": "cap_loop_contains_free_probe", "at": at,
                                  "interval": 0 if at == 0 else count-1, "probe": probe}
                cap, failure = _cap(loop, cells, resources, deadline)
                if cap is None and failure.get("reason") == "cap_interior_free_probe":
                    return None, {"reason": "cap_interior_free_probe", "interval": 0 if at == 0 else count-1,
                                  "at": at, "detail": failure}
                if cap is None:
                    last_failure = {"reason": "V5_cap_unproved", "interval": 0 if at == 0 else count-1,
                                    "at": at, "detail": failure}
                    break
                caps.append({"at": at, **cap})
            if len(caps) != 2:
                loops = tuple(old._refine_loop(loop) for loop in loops)
                continue
        result = dict(base)
        result.update(chain={"kind": kind, "breakpoints": knots},
                      start_interval=next(i for i in range(1, len(knots)) if knots[i-1] <= 0 <= knots[i]),
                      intervals=[{**interval, "loop": loop, "witnesses": row}
                                 for interval, loop, row in zip(intervals, loops, rows)],
                      links=links, caps=caps)
        return result, {"reason": "adaptive_"+kind+"_candidate", "mixed_kernels": mixed}
    return None, last_failure or {"reason": "loop_refinement_limit"}


def _rho_ratio(base, lo, hi):
    """V1 required contraction squared / host edge-clearance squared.

    Only a scheduling heuristic; empty/negative piece-centre margins are not
    rejected as geometry facts. The verifier checks actual rho and every E.
    """
    low, high, unused = old._chart(lo, hi)
    middle = (low+high)/2
    required = max(4*base["radius"]**2*(u-middle)**2/((1+u*u)*(1+middle*middle))
                   for u in (low, high))
    capacity = []
    for part in base["moving_pieces"]:
        center = _mean(part)
        capacity.append(min(((b[1]-a[1])*(center[0]-a[0])-(b[0]-a[0])*(center[1]-a[1]))**2 /
                            ((b[1]-a[1])**2+(b[0]-a[0])**2) for a, b in old._edges(part)))
    return required/max(capacity) if max(capacity) else required


def _split(knots, failure, base):
    index = failure.get("interval") if isinstance(failure, dict) else None
    if not isinstance(index, int) or not 0 <= index < len(knots)-1:
        scores = tuple((_rho_ratio(base, knots[i], knots[i+1]), -i) for i in range(len(knots)-1))
        index = -max(scores)[1]
    return knots[:index+1]+((knots[index]+knots[index+1])/2,)+knots[index+1:]


def propose_cage(instance, *, center=None, resources=None, verify=True,
                 modes=("disk", "capped", "closed"), halfwidths=None,
                 initial_intervals=4, mixed=True):
    """Finite candidate search; only accepted v5 data earns CERTIFIED_CAGE.

    Set mixed=False with modes=('closed',) to exercise rotation-only closure.
    verify=False is construction-only and returns PROPOSAL_UNVERIFIED.
    """
    resources = resources or CageResources()
    started = time.perf_counter()
    deadline = started+resources.max_seconds
    answer = {"status": "UNPROVED", "certificate": None, "attempts": [],
              "diagnostic": {"source": "untrusted_finite_search", "generation_seconds": None}}
    if center is None:
        center = _mean(instance["moving"])
    center = tuple(F(x) for x in center)
    try:
        old._check_time(deadline)
        if resources.max_loop_vertices < 4 or resources.max_cap_steps < 1:
            raise old.SearchLimit("loop_or_homotopy_resource_limit")
        parts = old._partition(tuple(instance["moving"]))
        obstacles = tuple({"obstacle": j, "ring": part}
                          for j, ring in enumerate(instance["obstacles"])
                          for part in old._partition(tuple(ring)))
        disk = old._disk(parts, center) if mixed or "disk" in modes else None
        base = old._base_certificate(instance, center, parts, obstacles, disk)
        states = []
        if "disk" in modes:
            states.append(("disk", (), {}))
        if "capped" in modes:
            widths = halfwidths or (F(1, 16), F(1, 8), F(1, 4), F(1, 2), F(3, 4), F(1))
            for width in widths:
                knots = tuple(-width+2*width*F(i, initial_intervals)
                              for i in range(initial_intervals+1))
                states.append(("capped", knots, {}))
        if "closed" in modes:
            count = max(4, initial_intervals)
            count += count % 2
            knots = tuple(F(-1)+4*F(i, count) for i in range(count+1))
            states.append(("closed", knots, {}))
        # Round-robin different angular extents; a hopeless cap cannot starve
        # the full-circle search. Cached intervals survive local bisection.
        for round_index in range(resources.max_adaptive_steps+1):
            following_states = []
            for kind, knots, cache in states:
                old._check_time(deadline)
                if kind != "disk" and len(knots)-1 > resources.max_intervals:
                    answer["attempts"].append({"mode": kind, "reason": "interval_limit"})
                    continue
                if kind == "disk":
                    candidate, reason = old._disk_candidate(base, resources, deadline)
                else:
                    state_deadline = min(deadline, time.perf_counter()+resources.max_state_seconds)
                    try:
                        candidate, reason = _candidate(base, knots, kind, resources, state_deadline, cache, mixed)
                    except old.SearchLimit as error:
                        if str(error) != "elapsed_time_limit":
                            raise
                        old._check_time(deadline)
                        candidate, reason = None, {"reason": "angular_state_time_limit"}
                record = {"mode": kind, "intervals": len(knots)-1 if knots else 2,
                          "round": round_index, "detail": reason}
                answer["attempts"].append(record)
                if candidate is not None:
                    old._check_candidate_resources(candidate, resources, deadline)
                    if verify:
                        checked = verify_se2_cage(instance, candidate)
                        record.update(verification_valid=checked.valid, condition=checked.condition,
                                      verification_reason=checked.reason, where=checked.where)
                        old._check_time(deadline)
                        if not checked.valid:
                            # A rejected candidate is diagnostic, never silently
                            # promoted; independent disagreement is handled upstream.
                            answer["diagnostic"]["rejected_candidate"] = record
                        else:
                            answer.update(status="CERTIFIED_CAGE", certificate=candidate,
                                          verification={"valid": checked.valid, "condition": checked.condition,
                                                        "reason": checked.reason, "where": checked.where,
                                                        "counts": checked.counts})
                    else:
                        answer.update(status="PROPOSAL_UNVERIFIED", certificate=candidate)
                    if answer["certificate"] is not None:
                        answer["diagnostic"].update(mode=kind, intervals=len(candidate["intervals"]),
                            uses_caps=bool(candidate["caps"]), full_circle=kind in ("disk", "closed"),
                            loop_vertices=sum(len(i["loop"]) for i in candidate["intervals"]))
                        elapsed = time.perf_counter()-started
                        answer["diagnostic"]["generation_seconds"] = elapsed
                        if elapsed > resources.max_seconds:
                            raise old.SearchLimit("elapsed_time_limit")
                        return answer
                if kind != "disk":
                    answer["diagnostic"]["last_geometric_failure"] = record
                    impossible_extent = isinstance(reason, dict) and reason.get("reason") == "cap_loop_contains_free_probe"
                    if len(knots)-1 < resources.max_intervals and not impossible_extent:
                        following_states.append((kind, _split(knots, reason, base), cache))
            states = following_states
            if not states:
                break
        if states:
            answer["attempts"].append({"mode": "resource_limit", "reason": "adaptive_step_limit"})
    except old.SearchLimit as error:
        answer.update(status="UNPROVED", certificate=None)
        answer.pop("verification", None)
        answer["attempts"].append({"mode": "resource_limit", "reason": str(error)})
    answer["diagnostic"]["generation_seconds"] = time.perf_counter()-started
    return answer
