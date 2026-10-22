"""Independent Python checks of C1 local-origin exact evidence (no DLL helpers).

The expected raw sources use the frozen Python original-ring contract. Sector
directions are generated from original incident edges, not product cells; their
classification calls polygons_overlap_exact, not entrance_membership_exact.
This is a geometry handoff check, not a C3 mechanical constraint calculation.
"""
from __future__ import annotations

from fractions import Fraction as F
from functools import cmp_to_key

from eab.kernel2d.exact import polygons_overlap_exact
from eab.kernel2d.global_entrance import GlobalEntrance2, _ring


def point(p):
    return tuple(F(v) for v in p)


def sub(a, b):
    return a[0]-b[0], a[1]-b[1]


def cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def dot(a, b):
    return a[0]*b[0]+a[1]*b[1]


def edges(poly):
    return tuple(zip(poly, poly[1:]+poly[:1]))


def on(p, a, b):
    return cross(sub(p, a), sub(b, a)) == 0 and dot(sub(p, a), sub(p, b)) <= 0


def distance2(a, b):
    e = sub(b, a)
    t = max(F(0), min(F(1), -dot(a, e)/dot(e, e)))
    p = a[0]+t*e[0], a[1]+t*e[1]
    return dot(p, p)


def ray(p):
    norm = abs(p[0])+abs(p[1])
    return p[0]/norm, p[1]/norm


def angle_cmp(a, b):
    ha = 0 if a[1] > 0 or (a[1] == 0 and a[0] > 0) else 1
    hb = 0 if b[1] > 0 or (b[1] == 0 and b[0] > 0) else 1
    if ha != hb:
        return -1 if ha < hb else 1
    value = cross(a, b)
    return -1 if value > 0 else 1 if value < 0 else 0


def expected_sources(original_a, original_b):
    originals = [tuple(map(point, poly)) for poly in (original_a, original_b)]
    a, b = (_ring(poly) for poly in originals)
    ids_a, ids_b = ([original.index(p) for p in poly] for original, poly in zip(originals, (a, b)))
    found = {}
    for i, p in enumerate(a):
        for j, (q, r) in enumerate(edges(b)):
            if on(p, q, r):
                found[("VE", i, j)] = (p, ids_a[i], (ids_b[j], ids_b[(j+1) % len(b)]), (sub(q, p), sub(r, p)))
    for j, p in enumerate(b):
        for i, (q, r) in enumerate(edges(a)):
            if on(p, q, r):
                found[("EV", i, j)] = (p, ids_b[j], (ids_a[i], ids_a[(i+1) % len(a)]), (sub(p, q), sub(p, r)))
    return a, b, found


def verify_local(export, original_a, original_b, *, require_lazy=True):
    assert export["schema"] == "eab2.local2.exact.v1"
    if require_lazy:
        assert not export["global_subdivision_materialized"], "local query forced the global subdivision"
    a, b, sources = expected_sources(original_a, original_b)
    zero = (F(0), F(0))
    state = polygons_overlap_exact(a, b)
    assert export["body_state"] == state
    assert export["topology_state"] == GlobalEntrance2(a, b).topology(zero)
    radius = F(export["radius"])
    assert radius > 0
    local = export["local_cells"]
    excluded = export["cell_exclusions"]
    all_cells = {r["cell_index"]: tuple(map(point, r["vertices"])) for r in local+excluded}
    assert len(all_cells) == len(local)+len(excluded) == export["cell_count"]
    assert set(all_cells) == set(range(export["cell_count"])), "incomplete cell evidence"
    required_bounds = {}
    for index, poly in all_cells.items():
        assert len(poly) >= 3
        assert all(cross(sub(q, p), sub(r, q)) > 0 for p, q, r in zip(poly, poly[1:]+poly[:1], poly[2:]+poly[:2]))
        for edge_index, (start, end) in enumerate(edges(poly)):
            if not on(zero, start, end):
                required_bounds[index, edge_index] = (start, end, distance2(start, end))
    actual_bounds = {}
    for row in export["radius_bounds"]:
        value = F(row["squared_distance"])
        assert radius*radius < value
        key = row["cell_index"], row["edge_index"]
        assert key not in actual_bounds
        actual_bounds[key] = point(row["start"]), point(row["end"]), value
    assert actual_bounds == required_bounds, "nonincident edge exclusion is not complete/exact"
    for row in local:
        poly = all_cells[row["cell_index"]]
        assert all(cross(sub(end, start), sub(zero, start)) >= 0 for start, end in edges(poly))
        expected_active = tuple((p, q) for p, q in edges(poly) if on(zero, p, q))
        active = tuple(tuple(map(point, e)) for e in row["active_edges"])
        assert active == expected_active, "active tangent halfplanes differ"
    for row in excluded:
        poly = all_cells[row["cell_index"]]
        bounds = tuple(map(F, row["aabb"]))
        assert bounds == (min(p[0] for p in poly), min(p[1] for p in poly), max(p[0] for p in poly), max(p[1] for p in poly))
        assert row["aabb_contains_zero"] == (bounds[0] <= 0 <= bounds[2] and bounds[1] <= 0 <= bounds[3])
        p, q = map(point, row["edge"])
        assert (p, q) == edges(poly)[row["edge_index"]]
        assert F(row["signed_cross"]) == cross(sub(q, p), sub(zero, p)) < 0
    got = {}
    for row in export["raw_sources"]:
        label = tuple(row["label"])
        assert label not in got
        segment = tuple(map(point, row["translation_segment"]))
        assert row["at_start"] == (segment[0] == zero)
        assert row["at_end"] == (segment[1] == zero)
        got[label] = point(row["point"]), row["vertex_id"], tuple(row["edge_vertex_ids"]), segment
    assert got == sources, "all original VE/EV incidences including endpoints must agree"

    # Original-boundary directions, including both directions of every incident
    # edge. The finite exact sampling radius is separately certified above.
    directions = {(F(1), F(0)), (F(0), F(1)), (F(-1), F(0)), (F(0), F(-1))}
    for p, *_ in sources.values():
        for poly in (a, b):
            for start, end in edges(poly):
                if on(p, start, end):
                    u = ray(sub(end, start))
                    directions.update((u, (-u[0], -u[1])))
    ordered = sorted(directions, key=cmp_to_key(angle_cmp))
    samples = list(ordered)
    for u, v in edges(tuple(ordered)):
        w = (u[0]+v[0], u[1]+v[1]) if cross(u, v) > 0 else (-u[1], u[0])
        samples.append(ray(w))
    for direction in samples:
        closed = False
        actual = -1
        for row in local:
            signs = [cross(sub(point(q), point(p)), direction) for p, q in row["active_edges"]]
            if all(s > 0 for s in signs):
                actual = 1
                break
            closed |= all(s >= 0 for s in signs)
        else:
            actual = 0 if closed else -1
        translation = tuple(v*radius/2 for v in direction)
        shifted = tuple((p[0]+translation[0], p[1]+translation[1]) for p in a)
        expected = polygons_overlap_exact(shifted, b)
        assert actual == expected, ("original-edge sector oracle", direction, actual, expected)
    return {"raw_sources_checked": len(got), "local_cells_checked": len(local),
            "excluded_cells_checked": len(excluded), "radius_bounds_checked": len(actual_bounds),
            "independent_sector_samples": len(samples)}


def contact_set_source(row, body_a, body_b):
    """Translate a local record to T1a's original-ID raw source tuple."""
    kind = row["label"][0]
    vertex = row["vertex_id"]
    edge = tuple(row["edge_vertex_ids"])
    return (kind, body_a, vertex, body_b, edge) if kind == "VE" else (kind, body_a, edge, body_b, vertex)
