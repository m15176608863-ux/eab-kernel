"""C1 differential-only exact export and representation-independent comparison.

This module never calls a DLL. Fraction arithmetic below normalizes *both*
exports; Python's existing GlobalEntrance2 remains the mathematical judge.
No generated canonical form or artificial vertical-cell order is trusted.
"""
from __future__ import annotations

from collections import defaultdict
from fractions import Fraction as F
from math import gcd, lcm

from eab.kernel2d.global_entrance import GlobalEntrance2, _split_segments
from eab.kernel2d.covers import enumerate_covers


def qtext(value):
    value = F(value)
    return f"{value.numerator}/{value.denominator}"


def point(value):
    if len(value) != 2:
        raise ValueError("exact point must have two coordinates")
    return tuple(F(x) for x in value)


def ptext(value):
    return [qtext(x) for x in value]


def sub(a, b):
    return a[0]-b[0], a[1]-b[1]


def cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def on(p, a, b):
    return cross(sub(b, a), sub(p, a)) == 0 and all(
        min(a[k], b[k]) <= p[k] <= max(a[k], b[k]) for k in (0, 1))


def midpoint(a, b):
    return (a[0]+b[0])/2, (a[1]+b[1])/2


def adjacent_states(model, a, b):
    """Certified local probes for a raw segment, not a subdivision edge.

    Compact side_probes expects a split edge and can land on a later seam when
    passed an unsplit raw CONTACT segment. Every nonincident convex-cell line
    event bounds the step here, including artificial lines; this is harmless
    reference-only overpartitioning, not a C++ production boundary algorithm.
    """
    middle = midpoint(a, b)
    e = sub(b, a)
    direction = -e[1], e[0]
    step = F(1)
    for poly in model.cells:
        for p, q in edges(poly):
            v = sub(q, p)
            height, slope = cross(v, sub(middle, p)), cross(v, direction)
            if height and slope:
                step = min(step, abs(height/slope)/2)
    return tuple(model.membership((middle[0]+sign*step*direction[0],
                                   middle[1]+sign*step*direction[1])) for sign in (1, -1))


def edges(poly):
    return zip(poly, poly[1:]+poly[:1])


def line_key(a, b):
    if a == b:
        raise ValueError("zero-length canonical segment")
    row = (a[1]-b[1], b[0]-a[0], a[0]*b[1]-a[1]*b[0])
    den = lcm(*(x.denominator for x in row))
    nums = tuple(int(x*den) for x in row)
    common = gcd(gcd(abs(nums[0]), abs(nums[1])), abs(nums[2]))
    nums = tuple(x//common for x in nums)
    return tuple(-x for x in nums) if next(x for x in nums if x) < 0 else nums


def canonical_segments(segments, labelled=False):
    """Union closed segment closures, retaining relative-open label strata.

    Each return row is (start, end[, labels]). Labels change only at input
    interval endpoints. Coincident sources are unioned, not arbitrarily chosen.
    Endpoint inclusion/isolated points are separately checked by canonical().
    """
    groups = defaultdict(list)
    for item in segments:
        if isinstance(item, dict):
            a, b = point(item["start"]), point(item["end"])
            labels = frozenset(tuple(x) for x in item.get("labels", ()))
        else:
            a, b = map(point, item)
            labels = frozenset()
        a, b = sorted((a, b))
        groups[line_key(a, b)].append((a, b, labels))
    result = []
    for rows in groups.values():
        stops = sorted({p for a, b, _ in rows for p in (a, b)})
        runs = []
        for lo, hi in zip(stops, stops[1:]):
            active = [labels for a, b, labels in rows if a <= lo and hi <= b]
            if not active:
                continue
            labels = tuple(sorted(set().union(*active))) if labelled else ()
            if runs and runs[-1][1] == lo and runs[-1][2] == labels:
                runs[-1] = (runs[-1][0], hi, labels)
            else:
                runs.append((lo, hi, labels))
        result.extend(runs if labelled else [(a, b) for a, b, _ in runs])
    return tuple(sorted(result))


def face_regions(faces):
    """Exact oriented boundaries of state-labelled 2D regions.

    Split every collinear incidence at all endpoints before cancellation.
    Internal vertical cuts cancel; nonzero boundary multiplicities are kept,
    so duplicate full faces are not silently accepted. Outside faces are not
    compared because finite enclosures may differ. E closure and E\\O strata
    together determine both physical sets, including interior contact seams.
    """
    groups = defaultdict(list)
    for face in faces:
        state = (face["body_state"], face["topology_state"])
        poly = tuple(map(point, face["vertices"]))
        area = sum(cross(a, b) for a, b in edges(poly))
        if not area:
            raise AssertionError("zero-area exported face")
        if area < 0:
            poly = tuple(reversed(poly))
        sample = point(face["sample"])
        if not all(cross(sub(b, a), sub(sample, a)) > 0 for a, b in edges(poly)):
            raise AssertionError("face sample is not in its relative interior")
        if state == (-1, -1):
            continue
        if state != (1, 1):
            raise AssertionError(f"invalid full-dimensional body/topology state: {state}")
        for a, b in edges(poly):
            sign = 1 if a < b else -1
            a, b = sorted((a, b))
            groups[(state, line_key(a, b))].append((a, b, sign))
    out = []
    for (state, _), rows in groups.items():
        stops = sorted({p for a, b, _ in rows for p in (a, b)})
        runs = []
        for lo, hi in zip(stops, stops[1:]):
            multiplicity = sum(sign for a, b, sign in rows if a <= lo and hi <= b)
            if not multiplicity:
                continue
            if runs and runs[-1][1] == lo and runs[-1][2] == multiplicity:
                runs[-1] = (runs[-1][0], hi, multiplicity)
            else:
                runs.append((lo, hi, multiplicity))
        out.extend((state, a, b, m) for a, b, m in runs)
    return tuple(sorted(out))


def canonical(export):
    if export.get("schema") != "eab2.c1.exact.v1":
        raise AssertionError("unexpected C1 export schema")
    raw = [(point(r["start"]), point(r["end"]), tuple(r["label"]))
           for r in export["raw_segments"]]
    contact = export["contact_segments"]
    for row in contact:
        a, b = point(row["start"]), point(row["end"])
        mid = midpoint(a, b)
        expected = {label for p, q, label in raw if on(mid, p, q)}
        if {tuple(x) for x in row["labels"]} != expected:
            raise AssertionError("CONTACT segment labels omit/add a raw source")
    unlabelled = canonical_segments(contact)
    labelled = canonical_segments(contact, labelled=True)
    points = {point(r["point"]): tuple(sorted(tuple(x) for x in r["labels"]))
              for r in export["contact_points"]}
    for p, labels in points.items():
        if set(labels) != {label for a, b, label in raw if on(p, a, b)}:
            raise AssertionError("CONTACT point labels omit/add a raw source")
    endpoints = {p for row in contact for p in (point(row["start"]), point(row["end"]))}
    if not endpoints <= points.keys():
        raise AssertionError("CONTACT segment endpoint missing from point stratum")
    isolated = tuple(sorted((p, labels) for p, labels in points.items()
                            if not any(on(p, a, b) for a, b in unlabelled)))
    # Retain geometric ends, source transitions, and crossing/branch points;
    # redundant decomposition vertices in a straight identical-label run vanish.
    essential = {p for a, b, _ in labelled for p in (a, b)}
    for p in points:
        lines = {line_key(a, b) for a, b in unlabelled if on(p, a, b)}
        if len(lines) > 1:
            essential.add(p)
    return {
        "segments": unlabelled,
        "source_strata": labelled,
        "endpoint_layers": tuple(sorted((p, points[p]) for p in essential)),
        "isolated_points": isolated,
        "face_regions": face_regions(export["subdivision"]["faces"]),
        "boundary": canonical_segments(export["boundary"]),
    }


def python_export(model, *, include_boundary=True):
    """Serialize the existing Python judge without C++ helpers or predicates."""
    raw = []
    for i, a in enumerate(model.A):
        for j, b in enumerate(model.B):
            raw.append({"label": ["VE", i, j], "start": ptext(sub(b, a)),
                        "end": ptext(sub(model.B[(j+1) % len(model.B)], a))})
            raw.append({"label": ["EV", i, j], "start": ptext(sub(b, a)),
                        "end": ptext(sub(b, model.A[(i+1) % len(model.A)]))})
    exact_raw = [(point(r["start"]), point(r["end"]), tuple(r["label"])) for r in raw]
    split = _split_segments(tuple({tuple(sorted((a, b))) for a, b, _ in exact_raw}))
    def labels(p):
        return sorted({label for a, b, label in exact_raw if on(p, a, b)})
    contacts = [{"start": ptext(a), "end": ptext(b), "labels": labels(midpoint(a, b))}
                for a, b in split if model.membership(midpoint(a, b)) == 0]
    points = [{"point": ptext(p), "labels": labels(p)}
              for p in sorted({p for ab in split for p in ab}) if model.membership(p) == 0]
    subdivision = model.subdivision
    def layer(rows):
        return [{"vertices": [ptext(p) for p in r.vertices], "sample": ptext(r.sample),
                 "body_state": r.state, "topology_state": model.topology(r.sample)} for r in rows]
    # Python boundary is intentionally used for the small-corpus cross-check.
    # It is a reference path, not the C++ production construction strategy.
    boundary = model.boundary if include_boundary else tuple(
        (point(r["start"]), point(r["end"])) for r in contacts
        if model.topology(midpoint(point(r["start"]), point(r["end"]))) == 0)
    return {"schema": "eab2.c1.exact.v1", "raw_segments": raw,
            "contact_segments": contacts, "contact_points": points,
            "subdivision": {"vertices": layer(subdivision.vertices),
                            "edges": layer(subdivision.edges), "faces": layer(subdivision.faces),
                            "exterior_state": subdivision.exterior_state},
            "boundary": [[ptext(a), ptext(b)] for a, b in boundary]}


def layer_samples(export):
    for kind in ("vertices", "edges", "faces"):
        for row in export["subdivision"][kind]:
            yield kind, point(row["sample"]), (row["body_state"], row["topology_state"])


def compare_exports(expected, actual, model):
    def raw_signature(export):
        return tuple(sorted((tuple(r["label"]), point(r["start"]), point(r["end"]))
                            for r in export["raw_segments"]))
    if raw_signature(expected) != raw_signature(actual):
        raise AssertionError("complete unfiltered raw VE/EV source segments differ")
    a, b = canonical(expected), canonical(actual)
    for field in a:
        if a[field] != b[field]:
            missing = sorted(set(a[field])-set(b[field]))[:3]
            extra = sorted(set(b[field])-set(a[field]))[:3]
            raise AssertionError(f"canonical {field} mismatch; missing={missing}; extra={extra}")
    count = 0
    for kind, sample, states in layer_samples(actual):
        truth = model.membership(sample), model.topology(sample)
        if states != truth:
            raise AssertionError(f"C++ {kind} sample state mismatch at {sample}: {states} != {truth}")
        count += 1
    for row in actual["contact_segments"]:
        start, end = point(row["start"]), point(row["end"])
        sample = midpoint(start, end)
        if model.membership(sample) != 0:
            raise AssertionError("exported contact segment is not CONTACT")
        sides = adjacent_states(model, start, end)
        if tuple(row["side_states"]) != sides:
            raise AssertionError("contact segment exact side occupancy differs")
        if row["boundary"] != (model.topology(sample) == 0):
            raise AssertionError("contact segment boundary flag differs")
    for row in actual["contact_points"]:
        if model.membership(point(row["point"])) != 0:
            raise AssertionError("exported contact point is not CONTACT")
    cover_statistics = compare_covers(actual, model)
    return {"cpp_layer_samples_rechecked": count,
            "canonical_segments": len(a["segments"]), "source_strata": len(a["source_strata"]),
            "isolated_points": len(a["isolated_points"]),
            "face_boundary_segments": len(a["face_regions"]), **cover_statistics}


def compare_covers(actual, model):
    """Compare labels to Python, exact recipes to original Fraction inputs."""
    cover_count = compare_cover_rows(actual["covers_zero_window"], model.A, model.B)
    def pieces(rows):
        out = []
        for r in rows:
            a, b = point(r["start"]), point(r["end"])
            # Clipped-cover Python probes and C++ infinitesimal sectors need
            # not share sample coordinates; a Python probe may itself lie on
            # an interior contact seam. The boundary semantic is closed-E
            # occupancy, not equality of those unrelated probe body states.
            sides = tuple(v >= 0 for v in r["side_states"])
            if a > b:
                sides = tuple(reversed(sides))
            key = (*r["label"], r["body_state"], r["exposed"], *sides)
            out.append({"start": a, "end": b, "labels": [key]})
        return canonical_segments(out, labelled=True)
    python_pieces = [{"start": p.start, "end": p.end, "label": p.label,
                      "body_state": p.body_state, "exposed": p.exposed, "side_states": p.side_states}
                     for p in model.clipped_covers]
    if pieces(python_pieces) != pieces(actual["clipped_covers"]):
        raise AssertionError("clipped cover relative-open labelled sets differ")
    for row in actual["clipped_covers"]:
        if tuple(row["side_states"]) != adjacent_states(model, point(row["start"]), point(row["end"])):
            raise AssertionError("clipped cover infinitesimal side body states differ")
    return {"zero_window_covers_checked": cover_count,
            "clipped_cover_strata": len(pieces(python_pieces))}


def compare_cover_rows(rows, a_ring, b_ring, *, window=F(0), tol=F(0), cone_tol=None, seg_tol=None,
                       require_in_segment=True):
    """Standalone cover comparison also used for explicit nonzero windows."""
    expected = {c.label(): c for c in enumerate_covers(a_ring, b_ring, window=window, tol=tol,
                                                      cone_tol=cone_tol, seg_tol=seg_tol,
                                                      require_in_segment=require_in_segment)}
    received = {tuple(c["label"]): c for c in rows}
    if len(received) != len(rows) or received.keys() != expected.keys():
        raise AssertionError(f"cover label set differs; missing={sorted(expected.keys()-received.keys())}; extra={sorted(received.keys()-expected.keys())}")
    def dot(a, b):
        return a[0]*b[0]+a[1]*b[1]
    for label, cover in expected.items():
        row = received[label]
        kind, i, j = label
        a, b = a_ring[i], b_ring[j]
        if kind == "VE":
            e = sub(b_ring[(j+1) % len(b_ring)], b)
            t = dot(sub(a, b), e)/dot(e, e)
            pa, pb = a, (b[0]+t*e[0], b[1]+t*e[1])
            normal = e[1], -e[0]
        elif kind == "EV":
            e = sub(a_ring[(i+1) % len(a_ring)], a)
            t = dot(sub(b, a), e)/dot(e, e)
            pa, pb = (a[0]+t*e[0], a[1]+t*e[1]), b
            normal = -e[1], e[0]
        else:
            t, pa, pb = None, a, b
            normal = sub(a, b) if a != b else None
        delta = sub(pa, pb)
        signed = dot(delta, normal) if normal is not None else 0
        gap_sign = (signed > 0)-(signed < 0)
        if (row["strict"] != cover.strict or row["window_active"] != cover.window_active
                or (None if row["param"] is None else F(row["param"])) != t
                or point(row["point_a"]) != pa or point(row["point_b"]) != pb
                or F(row["gap_squared"]) != dot(delta, delta) or row["gap_sign"] != gap_sign):
            raise AssertionError(f"exact cover recipe differs: {label}")
        got_normal = None if row["normal_direction"] is None else point(row["normal_direction"])
        if normal is None:
            if got_normal is not None:
                raise AssertionError("coincident VV must not invent a normal")
        elif got_normal is None or cross(normal, got_normal) or dot(normal, got_normal) <= 0:
            raise AssertionError("cover normal direction differs")
    return len(expected)
