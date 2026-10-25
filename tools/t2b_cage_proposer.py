"""Untrusted rational SE(2) cage proposals; only the verifier decides.

Input rings are never changed. Convex partitions, inscribed disks, contracted
pieces, overlap-graph loops and homotopies are candidate data. Failure means
UNPROVED, never an escape claim. The finite search is intentionally incomplete.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction as F
import json
from math import isqrt
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests"), str(ROOT / "tools")]

from eab.kernel2d.global_entrance import (
    _area2, _hull, _indexed_cell, _merge_convex_parts, _triangulate,
)
from eab.kernel2d.translation_space import _barrier
from t2_se2_grid import CASES, geometry
from t2b_truth_geometry_prod import truth_instance


@dataclass(frozen=True)
class CageResources:
    """Cooperative limits, not an interruptible wall-clock execution deadline.

    Vertex limits apply to every individual closed polyline; the homotopy
    step limit applies to links as well as caps. A completed expensive call
    can exceed the time limit, but that over-budget candidate is not accepted.
    """
    max_seconds: float = 90.0
    max_intervals: int = 32
    max_loop_vertices: int = 1025
    max_cells: int = 256
    max_cap_steps: int = 128
    max_refinements: int = 4


class SearchLimit(Exception):
    pass


def encode(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [encode(item) for item in value]
    if isinstance(value, dict):
        return {key: encode(item) for key, item in value.items()}
    return value


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(encode(value), ensure_ascii=False, indent=2) + "\n")


def scientific_instance(case_id, delta):
    """Construct from T2a's unchanged generator and erosion pipeline.

    The centre (0,1) is fixed across delta, including the chordal inputs.
    It does not inherit the grid proposer's delta-dependent vertex average.
    """
    row = list(next(case for case in CASES if case[0] == case_id))
    row[6] = str(F(delta))
    moving, obstacles = geometry(tuple(row))
    return {"moving": moving, "obstacles": obstacles}, (F(0), F(1))


def _check_time(deadline):
    if time.perf_counter() > deadline:
        raise SearchLimit("elapsed_time_limit")


def _check_candidate_resources(candidate, resources, deadline):
    """Check the actual proposed data, including the special disk-only path."""
    _check_time(deadline)
    intervals = candidate["intervals"]
    if len(intervals) > resources.max_intervals:
        raise SearchLimit("interval_limit")
    if any(len(interval["pieces"])*len(candidate["obstacle_pieces"]) > resources.max_cells
           for interval in intervals):
        raise SearchLimit("convex_cell_limit")
    loops = [interval["loop"] for interval in intervals]
    for item in (*candidate["links"], *candidate["caps"]):
        if len(item["chain"])-1 > resources.max_cap_steps:
            raise SearchLimit("homotopy_step_limit")
        loops.extend(item["chain"])
    if any(len(loop) > resources.max_loop_vertices for loop in loops):
        raise SearchLimit("loop_vertex_limit")


def _edges(ring):
    return zip(ring, ring[1:] + ring[:1])


def _norm2(point):
    return point[0] * point[0] + point[1] * point[1]


def _sqrt_rational(value, *, upper, denominator=1000000):
    """Exact rational lower/upper enclosure, preserving rational square roots."""
    value = F(value)
    if value < 0:
        raise ValueError("square-root bound requires a nonnegative value")
    a, b = isqrt(value.numerator), isqrt(value.denominator)
    if a*a == value.numerator and b*b == value.denominator:
        return F(a, b)
    scaled = value * denominator * denominator
    n = isqrt(scaled.numerator // scaled.denominator)
    result = F(n, denominator)
    if upper and result*result < value:
        result += F(1, denominator)
    return result


def _partition(ring):
    # Merging exact equal-area hulls removes artificial collinear/T junction
    # vertices from each convex ring. The production verifier checks the cover.
    return _merge_convex_parts(_triangulate(tuple(ring)))


def _local(ring, center):
    return tuple((p[0]-center[0], p[1]-center[1]) for p in ring)


def _world(ring, center):
    return tuple((p[0]+center[0], p[1]+center[1]) for p in ring)


def _circle_polygon(radius):
    quadrant = ((F(1), F(0)), (F(12, 13), F(5, 13)),
                (F(4, 5), F(3, 5)), (F(3, 5), F(4, 5)),
                (F(5, 13), F(12, 13)))
    points = []
    for _ in range(4):
        points.extend((radius*x, radius*y) for x, y in quadrant)
        quadrant = tuple((-y, x) for x, y in quadrant)
    return tuple(points)


def _disk(moving_parts, center):
    best = None
    for index, part in enumerate(moving_parts):
        bounds = []
        for a, b in _edges(_local(part, center)):
            nx, ny = b[1]-a[1], a[0]-b[0]
            support = nx*a[0]+ny*a[1]
            if support <= 0:
                break
            bounds.append(support*support/(nx*nx+ny*ny))
        else:
            radius = _sqrt_rational(min(bounds), upper=False)
            if radius > 0 and (best is None or radius > best["radius"]):
                best = {"radius": radius, "host": index,
                        "polygon": _circle_polygon(radius)}
    return best


def _chart(lo, hi):
    middle = (lo+hi)/2
    k = -((F(3)-middle)//4)
    shift = 4*k + (0 if middle-4*k <= 1 else 2)
    return lo-shift, hi-shift, 1 if shift == 4*k else -1


def _rotate(ring, value, lo, hi):
    low, high, sign = _chart(lo, hi)
    u = value-(lo-low)
    if not -1 <= low < high <= 1 or not -1 <= u <= 1:
        raise ValueError("candidate interval crosses a chart boundary")
    co, si = sign*(1-u*u)/(1+u*u), sign*2*u/(1+u*u)
    return tuple((co*x-si*y, si*x+co*y) for x, y in ring)


def _clip(poly, nx, ny, bound):
    out = []
    for a, b in _edges(poly):
        ha, hb = bound-nx*a[0]-ny*a[1], bound-nx*b[0]-ny*b[1]
        if ha >= 0:
            out.append(a)
        if ha*hb < 0:
            ratio = ha/(ha-hb)
            out.append((a[0]+ratio*(b[0]-a[0]), a[1]+ratio*(b[1]-a[1])))
    return _hull(out) if len(set(out)) >= 3 else ()


def _contract(part, center, lo, hi, rho):
    rotated = _rotate(_local(part, center), (lo+hi)/2, lo, hi)
    poly = rotated
    for a, b in _edges(rotated):
        nx, ny = b[1]-a[1], a[0]-b[0]
        margin = rho*_sqrt_rational(nx*nx+ny*ny, upper=True)
        poly = _clip(poly, nx, ny, nx*a[0]+ny*a[1]-margin)
        if len(poly) < 3:
            return ()
    return poly


def _interval(parts, center, radius, lo, hi, disk):
    low, high, _ = _chart(lo, hi)
    if not -1 <= low < high <= 1:
        return None
    middle = (low+high)/2
    bound = max((u-middle)**2/((1+u*u)*(1+middle*middle)) for u in (low, high))
    rho = _sqrt_rational(4*radius*radius*bound, upper=True)
    kernels = []
    for index, part in enumerate(parts):
        poly = _contract(part, center, lo, hi, rho)
        if len(poly) >= 3 and _area2(poly) > 0:
            kernels.append({"kind": "rotated", "piece": index, "polygon": poly})
    if disk is not None:
        kernels.append({"kind": "disk"})
    if not kernels:
        return None
    return {"rho": rho, "pieces": kernels, "loop": (), "witnesses": ()}


def _kernel_polygons(interval, disk, center):
    return tuple(_world(disk["polygon"] if piece["kind"] == "disk"
                        else piece["polygon"], center) for piece in interval["pieces"])


def _cells(polygons, obstacle_parts, resources, deadline, refs=None):
    if len(polygons)*len(obstacle_parts) > resources.max_cells:
        raise SearchLimit("convex_cell_limit")
    cells = []
    for i, moving in enumerate(polygons):
        for j, obstacle in enumerate(obstacle_parts):
            _check_time(deadline)
            poly = _hull((b[0]-a[0], b[1]-a[1]) for a in moving for b in obstacle["ring"])
            box, rows = _indexed_cell(poly)
            label = [i, j] if refs is None else [refs[i], j]
            cells.append((poly, box, rows, label))
    return tuple(cells)


def _inside(cell, point):
    _, box, rows, _ = cell
    if any(not box[k][0] < point[k] < box[k][1] for k in (0, 1)):
        return False
    return all(nx*point[0]+ny*point[1]+b > 0 for nx, ny, b in rows)


def _witness(cells, points):
    for cell in cells:
        if all(_inside(cell, point) for point in points):
            return cell[3]
    return None


def _loop_witnesses(loop, cells):
    result = []
    for a, b in zip(loop, loop[1:]):
        witness = _witness(cells, (a, b))
        if witness is None:
            return None
        result.append(witness)
    return result


def _refine_loop(loop, factor=2):
    return tuple((a[0]+F(i, factor)*(b[0]-a[0]), a[1]+F(i, factor)*(b[1]-a[1]))
                 for a, b in zip(loop, loop[1:]) for i in range(factor)) + (loop[-1],)


def _box_loop(x, y, per_side=8):
    corners = ((-x, -y), (x, -y), (x, y), (-x, y), (-x, -y))
    return _refine_loop(corners, per_side)


def _base_certificate(instance, center, parts, obstacle_parts, disk):
    radius = _sqrt_rational(max(_norm2(p) for part in parts for p in _local(part, center)), upper=True)
    return {"format": "eab.t2b.cage/1", "moving": instance["moving"],
            "obstacles": instance["obstacles"], "center": center, "radius": radius,
            "moving_pieces": parts, "obstacle_pieces": obstacle_parts, "disk": disk,
            "chain": {"kind": "closed", "breakpoints": (F(-1), F(1), F(3))},
            "start_interval": 1, "intervals": [], "links": [], "caps": []}


def _disk_candidate(base, resources, deadline):
    if resources.max_intervals < 2:
        return None, "disk_interval_limit"
    disk = base["disk"]
    if disk is None:
        return None, "center_has_no_positive_host_disk"
    cells = _cells((_world(disk["polygon"], base["center"]),),
                   base["obstacle_pieces"], resources, deadline)
    loop = _barrier(tuple(cell[0] for cell in cells))
    if not loop:
        return None, "no_disk_winding_loop"
    for _ in range(resources.max_refinements+1):
        _check_time(deadline)
        if len(loop) > resources.max_loop_vertices:
            return None, "disk_loop_vertex_limit"
        witnesses = _loop_witnesses(loop, cells)
        if witnesses is not None:
            interval = {"rho": F(0), "pieces": [{"kind": "disk"}],
                        "loop": loop, "witnesses": witnesses}
            candidate = dict(base)
            candidate["intervals"] = [interval, dict(interval)]
            joined = [[[["disk"], witness[1]] for witness in witnesses]]
            candidate["links"] = [{"at": n, "chain": [loop, loop], "witnesses": joined}
                                  for n in (1, 2)]
            return candidate, "disk_closed_chain_proposed"
        loop = _refine_loop(loop)
    return None, "disk_loop_witness_refinement_limit"


def _cap(loop, cells, resources, deadline):
    target = (F(0), F(0))
    if _witness(cells, (target,)) is None:
        return None, "cap_target_is_not_strictly_covered"
    steps = 8
    while steps <= resources.max_cap_steps:
        chain = [loop]
        witnesses = []
        failed = None
        for step in range(1, steps+1):
            _check_time(deadline)
            factor = F(steps-step, steps)
            following = tuple((factor*p[0], factor*p[1]) for p in loop)
            row = []
            for index, (a, b, d, c) in enumerate(zip(chain[-1], chain[-1][1:], following, following[1:])):
                witness = _witness(cells, (a, b, c, d))
                if witness is None:
                    failed = {"step": step, "segment": index, "steps": steps}
                    break
                row.append(witness)
            if failed is not None:
                break
            chain.append(following)
            witnesses.append(row)
        if failed is None:
            return {"chain": chain, "witnesses": witnesses}, "radial_cap_proposed"
        steps *= 2
    return None, {"reason": "cap_four_point_witness_missing", "where": failed}


def _aligned_loops(loops):
    """Align cyclic starts/orientation, retaining every original vertex.

    The union of rational edge-index parameters is a common subdivision;
    unequal segment counts are never reconciled by dropping source vertices.
    """
    prepared = []
    for loop in loops:
        points = list(loop[:-1])
        area = sum(a[0]*b[1]-a[1]*b[0] for a, b in _edges(tuple(points)))
        if area < 0:
            points.reverse()
        first = min(range(len(points)), key=lambda i: points[i])
        ring = tuple(points[first:]+points[:first])
        prepared.append(ring+(ring[0],))
    parameters = sorted({F(i, len(loop)-1) for loop in prepared for i in range(len(loop))})
    result = []
    for loop in prepared:
        count = len(loop)-1
        sampled = []
        for value in parameters:
            if value == 1:
                sampled.append(loop[-1])
                continue
            position = value*count
            index = position.numerator//position.denominator
            weight = position-index
            a, b = loop[index], loop[index+1]
            sampled.append((a[0]+weight*(b[0]-a[0]), a[1]+weight*(b[1]-a[1])))
        result.append(tuple(sampled))
    return tuple(result)


def _connect(first, last, cells, resources, deadline):
    """Propose four-point-covered linear homotopy strips, not endpoint-only links."""
    if len(first) != len(last):
        raise ValueError("connection requires the common loop subdivision")
    steps = 1
    failed = None
    while steps <= resources.max_cap_steps:
        chain, witnesses = [first], []
        failed = None
        for step in range(1, steps+1):
            _check_time(deadline)
            weight = F(step, steps)
            following = tuple((a[0]+weight*(b[0]-a[0]), a[1]+weight*(b[1]-a[1]))
                              for a, b in zip(first, last))
            row = []
            for index, (a, b, d, c) in enumerate(zip(chain[-1], chain[-1][1:], following, following[1:])):
                witness = _witness(cells, (a, b, c, d))
                if witness is None:
                    failed = {"step": step, "segment": index, "steps": steps}
                    break
                row.append(witness)
            if failed is not None:
                break
            chain.append(following)
            witnesses.append(row)
        if failed is None:
            return {"chain": chain, "witnesses": witnesses}, "four_point_connection_proposed"
        steps *= 2
    return None, {"reason": "connection_four_point_witness_missing", "where": failed}


def _connection_cells(base, intervals, knots, at, resources, deadline):
    value, lo, hi = knots[at], knots[at-1], knots[at]
    polygons = [_world(_rotate(_local(part, base["center"]), value, lo, hi), base["center"])
                for part in base["moving_pieces"]]
    refs = [["exact", i] for i in range(len(polygons))]
    if base["disk"] is not None:
        polygons.append(_world(base["disk"]["polygon"], base["center"]))
        refs.append(["disk"])
    for tag, interval in (("left", intervals[at-1]), ("right", intervals[at])):
        local = _kernel_polygons(interval, base["disk"], base["center"])
        polygons.extend(local)
        refs.extend([tag, i] for i in range(len(local)))
    return _cells(tuple(polygons), base["obstacle_pieces"], resources, deadline, refs=refs)


def _individual_loops_candidate(base, intervals, interval_cells, endpoint_cells,
                                knots, resources, deadline):
    """Fallback when one barrier cannot serve every angle interval."""
    raw = []
    for index, cells in enumerate(interval_cells):
        _check_time(deadline)
        loop = _barrier(tuple(cell[0] for cell in cells))
        if not loop:
            return None, {"reason": "individual_interval_has_no_winding_loop", "interval": index}
        raw.append(loop)
    loops = _aligned_loops(raw)
    connections = [_connection_cells(base, intervals, knots, at, resources, deadline)
                   for at in range(1, len(intervals))]
    failure = "individual_homotopy_refinement_limit"
    for _ in range(resources.max_refinements+1):
        if len(loops[0]) > resources.max_loop_vertices:
            return None, "individual_loop_vertex_limit"
        rows = [_loop_witnesses(loop, cells) for loop, cells in zip(loops, interval_cells)]
        if any(row is None for row in rows):
            loops = tuple(_refine_loop(loop) for loop in loops)
            continue
        links = []
        for at, cells in enumerate(connections, 1):
            link, failure = _connect(loops[at-1], loops[at], cells, resources, deadline)
            if link is None:
                if isinstance(failure, dict):
                    failure["interval"] = at-1
                break
            links.append({"at": at, **link})
        if len(links) != len(intervals)-1:
            loops = tuple(_refine_loop(loop) for loop in loops)
            continue
        caps = []
        for at, loop, cells in ((0, loops[0], endpoint_cells[0]),
                                (len(intervals), loops[-1], endpoint_cells[1])):
            cap, failure = _cap(loop, cells, resources, deadline)
            if cap is None:
                if isinstance(failure, dict):
                    failure["interval"] = 0 if at == 0 else len(intervals)-1
                break
            caps.append({"at": at, **cap})
        if len(caps) == 2:
            result = dict(base)
            result.update(chain={"kind": "capped", "breakpoints": knots},
                          start_interval=next(i for i in range(1, len(knots)) if knots[i-1] <= 0 <= knots[i]),
                          intervals=[{**interval, "loop": loop, "witnesses": row}
                                     for interval, loop, row in zip(intervals, loops, rows)],
                          links=links, caps=caps)
            return result, "individual_loops_four_point_links_and_caps_proposed"
        loops = tuple(_refine_loop(loop) for loop in loops)
    return None, failure


def _bisect_failed_interval(knots, diagnostic):
    index = diagnostic.get("interval") if isinstance(diagnostic, dict) else None
    if not isinstance(index, int) or not 0 <= index < len(knots)-1:
        index = max(range(len(knots)-1), key=lambda i: knots[i+1]-knots[i])
    return knots[:index+1] + ((knots[index]+knots[index+1])/2,) + knots[index+1:]


def _capped_candidate(base, halfwidth, count, resources, deadline, *, knots=None,
                      individual_only=False):
    if count > resources.max_intervals:
        return None, "interval_limit"
    knots = knots or tuple(-halfwidth+2*halfwidth*F(i, count) for i in range(count+1))
    count = len(knots)-1
    intervals = [_interval(base["moving_pieces"], base["center"], base["radius"], a, b, base["disk"])
                 for a, b in zip(knots, knots[1:])]
    if any(interval is None for interval in intervals):
        return None, {"reason": "contracted_piece_empty_or_chart_invalid",
                      "interval": next(i for i, interval in enumerate(intervals) if interval is None)}
    interval_cells = [_cells(_kernel_polygons(interval, base["disk"], base["center"]),
                             base["obstacle_pieces"], resources, deadline)
                      for interval in intervals]
    endpoint_cells = []
    for value, a, b in ((knots[0], knots[0], knots[1]), (knots[-1], knots[-2], knots[-1])):
        exact = tuple(_world(_rotate(_local(part, base["center"]), value, a, b), base["center"])
                      for part in base["moving_pieces"])
        endpoint_cells.append(_cells(exact, base["obstacle_pieces"], resources, deadline,
                                     refs=[["exact", i] for i in range(len(exact))]))
    if any(_witness(cells, ((F(0), F(0)),)) is None for cells in endpoint_cells):
        return None, "cap_origin_not_covered"
    # Prefer one common barrier so all interval links are degenerate strips.
    if individual_only:
        return _individual_loops_candidate(base, intervals, interval_cells, endpoint_cells,
                                            knots, resources, deadline)
    first_loop = _barrier(tuple(cell[0] for cell in interval_cells[count//2]))
    candidates = []
    if first_loop:
        candidates.append(first_loop)
    candidates.extend(_box_loop(x, y) for x, y in (
        (F(1, 4), F(1, 4)), (F(1, 2), F(1, 2)), (F(1), F(1)),
        (F(1, 2), F(1)), (F(1), F(1, 2)), (F(2), F(2))))
    diagnostic = "no_common_barrier"
    for initial_loop in candidates:
        loop = initial_loop
        for _ in range(resources.max_refinements+1):
            _check_time(deadline)
            if len(loop) > resources.max_loop_vertices:
                break
            rows = [_loop_witnesses(loop, cells) for cells in interval_cells]
            if any(row is None for row in rows):
                # Subdivision cannot repair a vertex outside the open union.
                if any(any(_witness(cells, (point,)) is None for point in loop)
                       for cells in interval_cells):
                    break
                loop = _refine_loop(loop)
                continue
            caps = []
            for at, cells in zip((0, count), endpoint_cells):
                cap, diagnostic = _cap(loop, cells, resources, deadline)
                if cap is None:
                    break
                caps.append({"at": at, **cap})
            if len(caps) == 2:
                prepared = [{**interval, "loop": loop, "witnesses": row}
                            for interval, row in zip(intervals, rows)]
                links = [{"at": at, "chain": [loop, loop],
                          "witnesses": [[[["left", pair[0]], pair[1]] for pair in rows[at-1]]]}
                         for at in range(1, count)]
                candidate = dict(base)
                candidate.update(chain={"kind": "capped", "breakpoints": knots},
                                 start_interval=next(i for i in range(1, count+1)
                                                     if knots[i-1] <= 0 <= knots[i]),
                                 intervals=prepared, links=links, caps=caps)
                return candidate, "common_loop_radial_caps_proposed"
            loop = _refine_loop(loop)
    return _individual_loops_candidate(base, intervals, interval_cells, endpoint_cells,
                                        knots, resources, deadline)


def propose_cage(instance, *, center=None, disk_only=False, resources=None,
                 verify=True, halfwidths=None, interval_counts=None):
    """Return a separately verified certificate, or explicit UNPROVED.

    ``verify=False`` is only for construction smoke tests; its success status
    is PROPOSAL_UNVERIFIED and never CERTIFIED_CAGE. Timing/failed locations are
    diagnostic and do not establish either trapping or escape.
    """
    resources = resources or CageResources()
    started = time.perf_counter()
    deadline = started+resources.max_seconds
    if center is None:
        center = tuple(sum((p[k] for p in instance["moving"]), F(0))/len(instance["moving"])
                       for k in (0, 1))
    center = tuple(F(x) for x in center)
    attempts = []
    answer = {"status": "UNPROVED", "certificate": None, "attempts": attempts,
              "diagnostic": {"source": "untrusted_finite_search", "generation_seconds": None}}
    parts = _partition(tuple(instance["moving"]))
    obstacle_parts = tuple({"obstacle": j, "ring": part}
                           for j, ring in enumerate(instance["obstacles"])
                           for part in _partition(tuple(ring)))
    disk = _disk(parts, center)
    base = _base_certificate(instance, center, parts, obstacle_parts, disk)

    def accept(candidate, reason, kind):
        if candidate is None:
            attempts.append({"mode": kind, "reason": reason})
            if kind != "disk":
                answer["diagnostic"]["last_geometric_failure"] = {"mode": kind, "detail": reason}
            return False
        _check_candidate_resources(candidate, resources, deadline)
        if verify:
            from eab.kernel2d.se2_cage import verify_se2_cage
            check_start = time.perf_counter()
            result = verify_se2_cage(instance, candidate)
            seconds = time.perf_counter()-check_start
            _check_time(deadline)
            attempts.append({"mode": kind, "reason": reason, "verification_valid": result.valid,
                             "condition": result.condition, "verification_reason": result.reason})
            if not result.valid:
                answer["diagnostic"]["rejected_candidate"] = {"condition": result.condition,
                                                               "reason": result.reason}
                return False
            answer["diagnostic"]["verification_seconds"] = seconds
            answer["verification"] = {"valid": result.valid, "condition": result.condition,
                                      "reason": result.reason, "where": result.where,
                                      "counts": result.counts}
            answer["status"] = "CERTIFIED_CAGE"
        else:
            attempts.append({"mode": kind, "reason": reason})
            answer["status"] = "PROPOSAL_UNVERIFIED"
        answer["certificate"] = candidate
        answer["diagnostic"].update(mode=kind, intervals=len(candidate["intervals"]),
                                    uses_caps=bool(candidate["caps"]),
                                    loop_vertices=sum(len(i["loop"]) for i in candidate["intervals"]))
        return True

    try:
        candidate, reason = _disk_candidate(base, resources, deadline)
        done = accept(candidate, reason, "disk")
        if not done and not disk_only:
            widths = halfwidths or (F(1, 23), F(1, 16), F(1, 8), F(1, 4), F(1, 2), F(1))
            counts = interval_counts or (1, 2, 4, 8, 16, 32)
            states = {F(width): ((-F(width), F(width)), None) for width in widths}
            for count in counts:
                if done:
                    break
                for width in widths:
                    _check_time(deadline)
                    knots, diagnostic = states[F(width)]
                    while len(knots)-1 < count and len(knots)-1 < resources.max_intervals:
                        knots = _bisect_failed_interval(knots, diagnostic)
                        diagnostic = None
                    candidate, reason = _capped_candidate(base, F(width), count, resources, deadline, knots=knots)
                    states[F(width)] = knots, reason
                    done = accept(candidate, reason, "capped:"+str(width)+":"+str(count))
                    if done:
                        break
    except SearchLimit as error:
        attempts.append({"mode": "resource_limit", "reason": str(error)})
    elapsed = time.perf_counter()-started
    if elapsed > resources.max_seconds and answer["status"] != "UNPROVED":
        answer.update(status="UNPROVED", certificate=None)
        answer.pop("verification", None)
        attempts.append({"mode": "resource_limit", "reason": "elapsed_time_limit"})
    answer["diagnostic"]["generation_seconds"] = elapsed
    return answer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--delta", default="0")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--disk-only", action="store_true")
    parser.add_argument("--max-seconds", type=float, default=90)
    parser.add_argument("--max-intervals", type=int, default=32)
    parser.add_argument("--max-loop-vertices", type=int, default=1025)
    args = parser.parse_args()
    if args.case in {row[0] for row in CASES}:
        instance, center = scientific_instance(args.case, F(args.delta))
    else:
        instance, center = truth_instance(args.case, F(args.delta))
    result = propose_cage(instance, center=center, disk_only=args.disk_only,
                          resources=CageResources(max_seconds=args.max_seconds,
                              max_intervals=args.max_intervals, max_loop_vertices=args.max_loop_vertices))
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / "instance.json", instance)
    if result["certificate"] is not None:
        write_json(args.output / "certificate.json", result["certificate"])
    summary = {key: value for key, value in result.items() if key != "certificate"}
    summary.update(case_id=args.case, delta=args.delta)
    write_json(args.output / "summary.json", summary)
    print(json.dumps(encode(summary), ensure_ascii=False))


if __name__ == "__main__":
    main()
