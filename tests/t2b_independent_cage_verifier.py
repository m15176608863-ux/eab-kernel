"""Independent exact verifier for docs/t2b_cage_lemma.md, revision 5.

No production geometry or eab import is used.  Geometry primitives below are
derived from the lemma's SAT, segment separation, and signed crossing rules.
The dict API checks decoded values; load_json additionally checks raw JSON
integer tokens and duplicate keys, information that an ordinary dict loses.
"""
from fractions import Fraction
import json
import sys


FORMAT = "eab.t2b.cage/1"
INVALID = []  # Private identity sentinel; never mutated or returned as JSON.
TOP_KEYS = ("format", "moving", "obstacles", "center", "radius",
            "moving_pieces", "obstacle_pieces", "disk", "chain",
            "start_interval", "intervals", "links", "caps")


class CageReject(ValueError):
    """A semantic guard failure, also used by in-code mutation tests."""

    def __init__(self, check_id, condition, where, reason):
        self.check_id = check_id
        self.condition = condition
        self.where = where
        self.reason = reason


def _require(ok, check_id, condition, where, reason):
    """Single assertion boundary; test mutations act here, before output."""
    if not ok:
        raise CageReject(check_id, condition, where, reason)


def _guard(state, ok, check_id, condition, where, reason):
    state["counts"]["checks"] += 1
    try:
        _require(ok, check_id, condition, where, reason)
    except CageReject as error:
        state["errors"].append(error)
        return False
    return True


def _rank_json(value, path, ranks):
    pending = [(value, path)]
    while pending:
        item, current = pending.pop()
        ranks[current] = len(ranks)
        children = []
        if isinstance(item, dict):
            for key, child in item.items():
                children.append((child, current + (key,)))
        elif isinstance(item, list):
            for index, child in enumerate(item):
                children.append((child, current + (index,)))
        for child in reversed(children):
            pending.append(child)


def _path_rank(path, ranks):
    tail = 0
    while path not in ranks and path:
        path = path[:-1]
        tail += 1
    return (ranks.get(path, -1), tail)


def _result(state):
    if not state["errors"]:
        return {"valid": True, "condition": "OK", "reason": "all lemma checks passed",
                "where": None, "counts": state["counts"]}
    selected = state["errors"][0]
    for error in state["errors"][1:]:
        if _path_rank(error.where, state["ranks"]) < _path_rank(selected.where, state["ranks"]):
            selected = error
    return {"valid": False, "condition": selected.condition, "reason": selected.reason,
            "where": {"path": list(selected.where), "check": selected.check_id},
            "counts": state["counts"]}


def _ready(value):
    pending = [value]
    while pending:
        item = pending.pop()
        if item is INVALID:
            return False
        if isinstance(item, dict):
            for child in item.values():
                pending.append(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                pending.append(child)
    return True


def _keys(value, expected, state, path):
    if not _guard(state, isinstance(value, dict), "object_type", "V0", path, "expected an object"):
        return False
    for key in value:
        _guard(state, key in expected, "unknown_key", "V0", path + (key,), "unknown object key")
    for key in expected:
        _guard(state, key in value, "missing_key", "V0", path + (key,), "required key missing")
    return True


def _array(value, state, path):
    return _guard(state, isinstance(value, list), "array_type", "V0", path, "expected an array")


def _unsigned_ascii(token, allow_zero=True):
    if not token:
        return False
    if token[0] == "0":
        return allow_zero and len(token) == 1
    if token[0] not in "123456789":
        return False
    for char in token[1:]:
        if char not in "0123456789":
            return False
    return True


def _rational_grammar(token):
    if token[:1] == "-":
        token = token[1:]
    slash = -1
    for index, char in enumerate(token):
        if char == "/":
            if slash != -1:
                return False
            slash = index
    if slash == -1:
        return _unsigned_ascii(token)
    return _unsigned_ascii(token[:slash]) and _unsigned_ascii(token[slash + 1:], False)


def _q(value, state, path):
    if not _guard(state, isinstance(value, str), "rational_type", "V0", path, "rational must be a string"):
        return INVALID
    if not _guard(state, len(value) <= 4096 and _rational_grammar(value),
                  "rational_grammar", "V0", path, "non-ASCII or noncanonical rational grammar"):
        return INVALID
    number = Fraction(value)
    if not _guard(state, str(number) == value, "rational_canonical", "V0", path,
                  "rational must be reduced; no negative zero or denominator one"):
        return INVALID
    return number


def _integer(value, state, path):
    if not _guard(state, isinstance(value, int) and not isinstance(value, bool) and value >= 0, "integer_type", "V0", path,
                  "index must be a nonnegative integer, not a boolean"):
        return INVALID
    return value


def _point(value, state, path):
    if not _array(value, state, path):
        return INVALID
    if not _guard(state, len(value) == 2, "point_length", "V0", path, "point needs two coordinates"):
        return INVALID
    return (_q(value[0], state, path + (0,)), _q(value[1], state, path + (1,)))


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _orientation(a, b, p):
    return _cross(_sub(b, a), _sub(p, a))


def _on_segment(p, a, b):
    return _orientation(a, b, p) == 0 and _dot(_sub(p, a), _sub(p, b)) <= 0


def _segments_meet(a, b, c, d):
    x = _orientation(a, b, c)
    y = _orientation(a, b, d)
    z = _orientation(c, d, a)
    w = _orientation(c, d, b)
    if x * y < 0 and z * w < 0:
        return True
    return ((x == 0 and _on_segment(c, a, b)) or
            (y == 0 and _on_segment(d, a, b)) or
            (z == 0 and _on_segment(a, c, d)) or
            (w == 0 and _on_segment(b, c, d)))


def _area2(ring):
    area = Fraction(0)
    for index, a in enumerate(ring):
        area += _cross(a, ring[(index + 1) % len(ring)])
    return area


def _winding(loop, point):
    winding = 0
    for index in range(len(loop) - 1):
        a = _sub(loop[index], point)
        b = _sub(loop[index + 1], point)
        cross = _cross(a, b)
        if a[1] <= 0 < b[1] and cross > 0:
            winding += 1
        if b[1] <= 0 < a[1] and cross < 0:
            winding -= 1
    return winding


def _strict_inside(point, ring):
    for index, a in enumerate(ring):
        if _on_segment(point, a, ring[(index + 1) % len(ring)]):
            return False
    return _winding(tuple(ring) + (ring[0],), point) != 0


def _ring(value, mode, state, path):
    if not _array(value, state, path):
        return INVALID
    points = []
    for index, point in enumerate(value):
        points.append(_point(point, state, path + (index,)))
    if not _ready(points):
        return INVALID
    ring = tuple(points)
    if mode == "loop":
        if not _guard(state, len(ring) >= 2, "loop_length", "V0", path, "closed polyline needs a segment"):
            return INVALID
        _guard(state, ring[0] == ring[-1], "loop_closed", "V0", path, "polyline must explicitly close")
        return ring
    if not _guard(state, len(ring) >= 3, "ring_length", "V0", path, "ring needs at least three vertices"):
        return INVALID
    distinct = len(set(ring)) == len(ring)
    if not _guard(state, distinct, "ring_distinct", "V0", path, "ring vertices must be pairwise distinct"):
        return INVALID
    if mode == "convex":
        good = True
        for index, a in enumerate(ring):
            following = (index + 1) % len(ring)
            b = ring[following]
            for other, p in enumerate(ring):
                if other != index and other != following and _orientation(a, b, p) <= 0:
                    good = False
        _guard(state, good, "strict_convex_ring", "V0", path,
               "every other vertex must lie strictly left of every oriented edge")
    else:
        simple = True
        for index, a in enumerate(ring):
            following = (index + 1) % len(ring)
            b = ring[following]
            c = ring[(index + 2) % len(ring)]
            if _orientation(a, b, c) == 0 and _dot(_sub(a, b), _sub(c, b)) > 0:
                simple = False
            for other in range(index + 1, len(ring)):
                if other == following or (index == 0 and other == len(ring) - 1):
                    continue
                if _segments_meet(a, b, ring[other], ring[(other + 1) % len(ring)]):
                    simple = False
        _guard(state, simple, "simple_ring", "V0", path, "ring edges intersect other than at adjacent endpoints")
        _guard(state, _area2(ring) > 0, "ring_positive_area", "V0", path, "simple ring must have positive signed area")
    return ring


def _reference_decode(value, state, path):
    if not _array(value, state, path):
        return INVALID
    if not _guard(state, len(value) >= 1 and isinstance(value[0], str) and value[0] in
                  ("exact", "left", "right", "disk"), "ref_kind", "V0", path, "unknown witness reference"):
        return INVALID
    expected = 2
    if value[0] == "disk":
        expected = 1
    if not _guard(state, len(value) == expected, "ref_length", "V0", path, "wrong reference arity"):
        return INVALID
    if expected == 1:
        return ["disk"]
    return [value[0], _integer(value[1], state, path + (1,))]


def _witness_decode(value, tag, state, path):
    if tag == "ref":
        return _reference_decode(value, state, path)
    if not _array(value, state, path):
        return INVALID
    if not _guard(state, len(value) == 2, "witness_arity", "V0", path, "witness needs exactly two entries"):
        return INVALID
    if tag == "homotopy_witness":
        first = _reference_decode(value[0], state, path + (0,))
    else:
        first = _integer(value[0], state, path + (0,))
    return [first, _integer(value[1], state, path + (1,))]


def _decode(value, tag, state, path):
    # The schema is finite; an explicit work stack avoids implicit call recursion.
    schemas = {
        "instance": {"moving": "simple", "obstacles": "list:simple"},
        "certificate": {"format": "format", "moving": "simple", "obstacles": "list:simple",
                        "center": "point", "radius": "q", "moving_pieces": "list:convex",
                        "obstacle_pieces": "list:obstacle_piece", "disk": "disk",
                        "chain": "chain", "start_interval": "int", "intervals": "list:interval",
                        "links": "list:homotopy", "caps": "list:homotopy"},
        "obstacle_piece": {"obstacle": "int", "ring": "convex"},
        "disk": {"radius": "q", "host": "int", "polygon": "convex"},
        "chain": {"kind": "chain_kind", "breakpoints": "list:q"},
        "interval": {"rho": "q", "pieces": "list:kernel_piece", "loop": "loop", "witnesses": "list:barrier_witness"},
        "homotopy": {"at": "int", "chain": "list:loop", "witnesses": "list:list:homotopy_witness"},
    }
    root = [INVALID]
    pending = [(value, tag, path, root, 0)]
    while pending:
        item, kind, current, parent, key = pending.pop()
        result = INVALID
        if kind in ("simple", "convex", "loop"):
            result = _ring(item, kind, state, current)
        elif kind == "point":
            result = _point(item, state, current)
        elif kind == "q":
            result = _q(item, state, current)
        elif kind == "int":
            result = _integer(item, state, current)
        elif kind == "format":
            _guard(state, isinstance(item, str) and item == FORMAT, "format", "V0", current, "unsupported format")
            result = item
        elif kind == "chain_kind":
            _guard(state, isinstance(item, str) and item in ("closed", "capped"), "chain_kind", "V0", current, "unknown chain kind")
            result = item
        elif kind in ("barrier_witness", "homotopy_witness", "ref"):
            result = _witness_decode(item, kind, state, current)
        elif kind == "literal":
            result = item
        elif kind[:5] == "list:":
            if _array(item, state, current):
                result = []
                for unused in item:
                    result.append(INVALID)
                for index in range(len(item) - 1, -1, -1):
                    pending.append((item[index], kind[5:], current + (index,), result, index))
        elif kind == "disk" and item is None:
            result = None
        else:
            fields = {}
            accepted = True
            if kind == "kernel_piece":
                accepted = _guard(state, isinstance(item, dict), "object_type", "V0", current, "expected an object")
                if accepted:
                    label = item.get("kind")
                    accepted = _guard(state, isinstance(label, str) and label in ("rotated", "disk"),
                                      "kernel_kind", "V0", current + ("kind",), "unknown kernel kind")
                    fields = {"kind": "literal"}
                    if label == "rotated":
                        fields = {"kind": "literal", "piece": "int", "polygon": "convex"}
            else:
                fields = schemas[kind]
            if accepted and _keys(item, fields, state, current):
                result = {}
                for field in fields:
                    result[field] = INVALID
                children = []
                for field, child in item.items():
                    if field in fields:
                        children.append((child, fields[field], current + (field,), result, field))
                for child in reversed(children):
                    pending.append(child)
        parent[key] = result
    return root[0]


def _axes(ring, state, path):
    axes = []
    for index, a in enumerate(ring):
        edge = _sub(ring[(index + 1) % len(ring)], a)
        axis = (edge[1], -edge[0])
        _guard(state, axis != (0, 0), "nonzero_axis", "V0", path, "zero separation axis")
        axes.append(axis)
    return axes


def _projection(ring, axis):
    low = _dot(ring[0], axis)
    high = low
    for point in ring[1:]:
        value = _dot(point, axis)
        if value < low:
            low = value
        if value > high:
            high = value
    return (low, high)


def _weak_separated(a, b, state, path):
    for axis in _axes(a, state, path) + _axes(b, state, path):
        low_a, high_a = _projection(a, axis)
        low_b, high_b = _projection(b, axis)
        if high_a <= low_b or high_b <= low_a:
            return True
    return False


def _partition(parent, pieces, state, path):
    if not _guard(state, len(pieces) > 0, "partition_nonempty", "V0", path, "each parent needs at least one piece"):
        return
    total_area = Fraction(0)
    for index, piece in enumerate(pieces):
        sx = Fraction(0)
        sy = Fraction(0)
        for point in piece:
            sx += point[0]
            sy += point[1]
        mean = (sx / len(piece), sy / len(piece))
        _guard(state, _strict_inside(mean, parent), "partition_interior_point", "V0", path,
               "piece vertex mean is not strictly inside its parent")
        for edge, a in enumerate(parent):
            b = parent[(edge + 1) % len(parent)]
            _guard(state, _weak_separated(piece, (a, b), state, path), "partition_boundary", "V0", path,
                   "parent edge meets the interior of a piece (lemma 0)")
        for previous in pieces[:index]:
            _guard(state, _weak_separated(piece, previous, state, path), "partition_disjoint", "V0", path,
                   "two pieces have intersecting interiors")
        total_area += _area2(piece)
    _guard(state, total_area == _area2(parent), "partition_area", "V0", path, "piece areas do not sum to parent area")


def _index(value, size, state, path, check_id="index_range", condition="V0"):
    return _guard(state, 0 <= value < size, check_id, condition, path, "reference index out of range")


def _available_array(value):
    return value is not INVALID and isinstance(value, (list, tuple))


def _v0(instance, cert, state):
    # Validate independent dependencies separately: a malformed late field
    # must not mask an earlier geometric V0 failure in JSON occurrence order.
    path = ("certificate",)
    if isinstance(instance, dict):
        for key in ("moving", "obstacles"):
            if _ready(instance[key]) and _ready(cert[key]):
                _guard(state, instance[key] == cert[key], "instance_binding", "V0", path + (key,),
                       "certificate geometry differs from independently supplied instance")
    moving = cert["moving_pieces"]
    obstacles = cert["obstacle_pieces"]
    count = None
    chain = cert["chain"]
    if isinstance(chain, dict) and _available_array(chain["breakpoints"]):
        count = len(chain["breakpoints"]) - 1
    intervals = cert["intervals"]
    if count is not None:
        if _ready(cert["start_interval"]):
            _guard(state, 1 <= cert["start_interval"] <= count, "start_index", "V0", path + ("start_interval",), "start_interval outside 1..N")
        if _available_array(intervals):
            _guard(state, len(intervals) == count, "interval_count", "V0", path + ("intervals",), "interval count differs from N")
    radius = cert["radius"]
    if _ready(radius):
        _guard(state, radius > 0, "radius_positive", "V0", path + ("radius",), "radius must be positive")
        if _ready(cert["center"]) and _available_array(moving):
            for piece in moving:
                if not _ready(piece):
                    continue
                for point in piece:
                    delta = _sub(point, cert["center"])
                    _guard(state, radius * radius >= _dot(delta, delta), "radius_bound", "V0", path + ("radius",),
                           "radius squared is smaller than a moving vertex distance squared")
    if _ready(cert["moving"]) and _ready(moving):
        _partition(cert["moving"], moving, state, path + ("moving_pieces",))
    if _ready(cert["obstacles"]) and _available_array(obstacles):
        groups = []
        for unused in cert["obstacles"]:
            groups.append([])
        complete = _ready(obstacles)
        for index, piece in enumerate(obstacles):
            if not isinstance(piece, dict) or not _ready(piece["obstacle"]):
                continue
            if _index(piece["obstacle"], len(groups), state, path + ("obstacle_pieces", index, "obstacle")):
                if _ready(piece["ring"]):
                    groups[piece["obstacle"]].append(piece["ring"])
        if complete:
            for index, parent in enumerate(cert["obstacles"]):
                _partition(parent, groups[index], state, path + ("obstacles", index))
    disk = cert["disk"]
    if isinstance(disk, dict):
        if _ready(disk["radius"]):
            _guard(state, disk["radius"] > 0, "disk_radius_positive", "V0", path + ("disk", "radius"), "disk radius must be positive")
        if _ready(disk["host"]) and _available_array(moving):
            _index(disk["host"], len(moving), state, path + ("disk", "host"))
    if _available_array(intervals):
        for n, interval in enumerate(intervals):
            if not isinstance(interval, dict):
                continue
            ip = path + ("intervals", n)
            pieces = interval["pieces"]
            if _available_array(pieces):
                _guard(state, len(pieces) > 0, "kernel_nonempty", "V0", ip + ("pieces",), "interval needs a kernel piece")
                for k, piece in enumerate(pieces):
                    if not isinstance(piece, dict):
                        continue
                    pp = ip + ("pieces", k)
                    if piece["kind"] == "rotated":
                        if _ready(piece["piece"]) and _available_array(moving):
                            _index(piece["piece"], len(moving), state, pp + ("piece",))
                    else:
                        _guard(state, disk is not None, "disk_present", "V0", pp, "disk reference but disk is null")
            witnesses = interval["witnesses"]
            if _available_array(witnesses):
                if _available_array(interval["loop"]):
                    _guard(state, len(witnesses) == len(interval["loop"]) - 1,
                           "barrier_witness_count", "V0", ip + ("witnesses",), "one witness required per listed segment")
                for s, witness in enumerate(witnesses):
                    if not _available_array(witness):
                        continue
                    if _ready(witness[0]) and _available_array(pieces):
                        _index(witness[0], len(pieces), state, ip + ("witnesses", s, 0))
                    if _ready(witness[1]) and _available_array(obstacles):
                        _index(witness[1], len(obstacles), state, ip + ("witnesses", s, 1))
    for kind in ("links", "caps"):
        if not _available_array(cert[kind]):
            continue
        for index, item in enumerate(cert[kind]):
            if not isinstance(item, dict):
                continue
            hp = path + (kind, index)
            if _ready(item["at"]) and count is not None:
                _guard(state, item["at"] <= count, "at_index", "V0", hp + ("at",), "at outside 0..N")
            polylines = item["chain"]
            if _available_array(polylines):
                _guard(state, len(polylines) >= 2, "homotopy_length", "V0", hp + ("chain",), "homotopy needs at least two polylines")
                for j in range(len(polylines) - 1):
                    if _available_array(polylines[j]) and _available_array(polylines[j + 1]):
                        _guard(state, len(polylines[j]) == len(polylines[j + 1]),
                               "homotopy_vertex_count", "V0", hp + ("chain", j + 1), "adjacent polylines have different vertex counts")
            witnesses = item["witnesses"]
            if not _available_array(witnesses):
                continue
            if _available_array(polylines):
                _guard(state, len(witnesses) == len(polylines) - 1,
                       "homotopy_witness_rows", "V0", hp + ("witnesses",), "one witness row required per adjacent polyline pair")
            for j, row in enumerate(witnesses):
                if not _available_array(row):
                    continue
                if _available_array(polylines) and j < len(polylines) and _available_array(polylines[j]):
                    _guard(state, len(row) == len(polylines[j]) - 1, "homotopy_witness_count", "V0",
                           hp + ("witnesses", j), "one witness required per quadrilateral")
                for s, witness in enumerate(row):
                    if not _available_array(witness):
                        continue
                    ref, obstacle = witness
                    rp = hp + ("witnesses", j, s)
                    if _ready(obstacle) and _available_array(obstacles):
                        _index(obstacle, len(obstacles), state, rp + (1,))
                    if not _ready(ref):
                        continue
                    if ref[0] == "exact" and _available_array(moving):
                        _index(ref[1], len(moving), state, rp + (0, 1))
                    if ref[0] == "disk":
                        _guard(state, disk is not None, "disk_present", "V0", rp + (0,), "disk reference but disk is null")


def _chart(lower, upper):
    middle = (lower + upper) / 2
    k = -((3 - middle) // 4)
    offset = 4 * k
    sign = 1
    if middle - offset > 1:
        offset += 2
        sign = -1
    return (offset, sign, lower - offset, upper - offset, middle - offset)


def _contains_period(lower, upper, strict=False):
    first = -((-lower) // 4)
    if strict and 4 * first == lower:
        first += 1
    if strict:
        return 4 * first < upper
    return 4 * first <= upper


def _chain(cert, state):
    path = ("certificate",)
    points = cert["chain"]["breakpoints"]
    count = len(points) - 1
    _guard(state, count >= 1, "chain_nonempty", "CHAIN", path + ("chain", "breakpoints"), "N must be at least one")
    charts = []
    for index in range(count):
        lower, upper = points[index:index + 2]
        _guard(state, lower < upper, "breakpoints_increasing", "CHAIN", path + ("chain", "breakpoints", index + 1), "breakpoints must strictly increase")
        chart = _chart(lower, upper)
        charts.append(chart)
        _guard(state, -1 <= chart[2] < chart[3] <= 1, "interval_chart", "CHAIN", path + ("chain", "breakpoints", index), "endpoints not in one midpoint-selected chart")
    closed = cert["chain"]["kind"] == "closed"
    span = points[-1] - points[0]
    span_ok = span < 4
    if closed:
        span_ok = span == 4
    _guard(state, span_ok, "chain_span", "CHAIN", path + ("chain", "breakpoints"), "wrong chain span")
    n0 = cert["start_interval"]
    _guard(state, _contains_period(points[n0 - 1], points[n0]), "start_interval_contains_zero", "CHAIN", path + ("start_interval",), "selected interval does not contain a lift of rotation zero")
    if not closed:
        _guard(state, _contains_period(points[0], points[-1], strict=True), "capped_zero_interior", "CHAIN", path + ("chain",), "capped arc must contain rotation zero strictly inside")
    expected = list(range(1, count))
    if closed:
        expected.append(count)
    actual = []
    for item in cert["links"]:
        actual.append(item["at"])
    _guard(state, sorted(actual) == expected, "link_set", "CHAIN", path + ("links",), "link at values must equal the required set exactly")
    expected_caps = []
    if not closed:
        expected_caps = [0, count]
    actual_caps = []
    for item in cert["caps"]:
        actual_caps.append(item["at"])
    _guard(state, sorted(actual_caps) == expected_caps, "cap_set", "CHAIN", path + ("caps",), "cap at values must be exactly {0,N}, or empty for closed chain")
    intervals = cert["intervals"]
    for index, item in enumerate(cert["links"]):
        at = item["at"]
        if 1 <= at <= count:
            right = at % count
            _guard(state, item["chain"][0] == intervals[at - 1]["loop"] and item["chain"][-1] == intervals[right]["loop"],
                   "link_endpoints", "CHAIN", path + ("links", index, "chain"), "link endpoints differ from adjacent barriers")
    for index, item in enumerate(cert["caps"]):
        at = item["at"]
        hp = path + ("caps", index, "chain")
        if at in (0, count):
            interval = 0
            if at == count:
                interval = count - 1
            _guard(state, item["chain"][0] == intervals[interval]["loop"], "cap_start", "CHAIN", hp, "cap must start at its barrier")
        last = item["chain"][-1]
        _guard(state, len(set(last)) == 1, "cap_constant", "CHAIN", hp, "cap must end at a constant polyline")
    return charts


def _rotate(point, parameter, sign):
    square = parameter * parameter
    divisor = 1 + square
    co = (1 - square) / divisor
    si = 2 * parameter / divisor
    return (sign * (co * point[0] - si * point[1]), sign * (si * point[0] + co * point[1]))


def _body_ring(ring, center):
    result = []
    for point in ring:
        result.append(_sub(point, center))
    return tuple(result)


def _rotated_ring(ring, center, parameter, sign):
    result = []
    for point in ring:
        result.append(_rotate(_sub(point, center), parameter, sign))
    return tuple(result)


def _world_ring(ring, center):
    result = []
    for point in ring:
        result.append((point[0] + center[0], point[1] + center[1]))
    return tuple(result)


def _v1(cert, charts, state):
    radius = cert["radius"]
    for index, interval in enumerate(cert["intervals"]):
        path = ("certificate", "intervals", index, "rho")
        rho = interval["rho"]
        _guard(state, rho >= 0, "rho_nonnegative", "V1", path, "rho must be nonnegative")
        rotated = False
        for piece in interval["pieces"]:
            if piece["kind"] == "rotated":
                rotated = True
        if not rotated:
            continue
        chart = charts[index]
        center = chart[4]
        bound = Fraction(0)
        for parameter in (chart[2], chart[3]):
            difference = parameter - center
            value = difference * difference / ((1 + parameter * parameter) * (1 + center * center))
            if value > bound:
                bound = value
        _guard(state, rho * rho >= 4 * radius * radius * bound, "rotation_bound", "V1", path,
               "rho squared below exact same-chart rotation bound")


def _v2(cert, charts, state):
    for index, interval in enumerate(cert["intervals"]):
        chart = charts[index]
        rho = interval["rho"]
        for k, piece in enumerate(interval["pieces"]):
            if piece["kind"] != "rotated":
                continue
            path = ("certificate", "intervals", index, "pieces", k, "polygon")
            host = _rotated_ring(cert["moving_pieces"][piece["piece"]], cert["center"], chart[4], chart[1])
            for edge, normal in enumerate(_axes(host, state, path)):
                support = _dot(normal, host[edge])
                for vertex, point in enumerate(piece["polygon"]):
                    gap = support - _dot(normal, point)
                    _guard(state, gap >= 0 and gap * gap >= rho * rho * _dot(normal, normal),
                           "rotated_containment", "V2", path + (vertex,), "kernel vertex outside an inward-offset support line")


def _v3(cert, state):
    disk = cert["disk"]
    if disk is None:
        return
    path = ("certificate", "disk")
    host = _body_ring(cert["moving_pieces"][disk["host"]], cert["center"])
    radius = disk["radius"]
    for edge, normal in enumerate(_axes(host, state, path)):
        support = _dot(normal, host[edge])
        _guard(state, support >= 0 and support * support >= radius * radius * _dot(normal, normal),
               "disk_host", "V3", path + ("host",), "host does not contain the closed invariant disk")
    for index, point in enumerate(disk["polygon"]):
        _guard(state, _dot(point, point) <= radius * radius, "disk_polygon", "V3", path + ("polygon", index), "disk polygon vertex outside disk")


def _kernel(cert, interval, index):
    piece = cert["intervals"][interval]["pieces"][index]
    if piece["kind"] == "disk":
        return _world_ring(cert["disk"]["polygon"], cert["center"])
    return _world_ring(piece["polygon"], cert["center"])


def _strict_penetration(moving, obstacle, translation, state, path):
    state["counts"]["strict_sat"] += 1
    for axis in _axes(moving, state, path) + _axes(obstacle, state, path):
        low_a, high_a = _projection(moving, axis)
        low_b, high_b = _projection(obstacle, axis)
        shift = _dot(axis, translation)
        if high_a + shift <= low_b or high_b <= low_a + shift:
            return False
    return True


def _v4(cert, state):
    for index, interval in enumerate(cert["intervals"]):
        for segment, (kernel, obstacle) in enumerate(interval["witnesses"]):
            path = ("certificate", "intervals", index, "witnesses", segment)
            moving = _kernel(cert, index, kernel)
            fixed = cert["obstacle_pieces"][obstacle]["ring"]
            good = True
            for point in interval["loop"][segment:segment + 2]:
                if not _strict_penetration(moving, fixed, point, state, path):
                    good = False
            _guard(state, good, "barrier_strict", "V4", path, "both segment endpoints must strictly penetrate the given same piece pair")
            state["counts"]["barrier_segments"] += 1


def _reference(cert, charts, kind, at, ref, state, path):
    count = len(cert["intervals"])
    tag = ref[0]
    if tag == "disk":
        return _world_ring(cert["disk"]["polygon"], cert["center"])
    if tag == "exact":
        chart_index = at - 1
        if at == 0:
            chart_index = 0
        chart = charts[chart_index]
        parameter = cert["chain"]["breakpoints"][at] - chart[0]
        if not _guard(state, -1 <= parameter <= 1, "exact_chart", "V5", path, "exact rotation outside endpoint chart"):
            return INVALID
        rotated = _rotated_ring(cert["moving_pieces"][ref[1]], cert["center"], parameter, chart[1])
        return _world_ring(rotated, cert["center"])
    allowed = not (kind == "caps" and ((at == 0 and tag == "left") or (at == count and tag == "right")))
    if not _guard(state, allowed, "reference_side", "V5", path, "reference is on nonexistent side of cap"):
        return INVALID
    interval = at % count
    if tag == "left":
        interval = (at - 1) % count
    if not _index(ref[1], len(cert["intervals"][interval]["pieces"]), state, path + (1,), "side_index", "V5"):
        return INVALID
    return _kernel(cert, interval, ref[1])


def _v5(cert, charts, state):
    for kind in ("links", "caps"):
        for index, item in enumerate(cert[kind]):
            for step, row in enumerate(item["witnesses"]):
                first = item["chain"][step]
                second = item["chain"][step + 1]
                for segment, (ref, obstacle) in enumerate(row):
                    path = ("certificate", kind, index, "witnesses", step, segment)
                    moving = _reference(cert, charts, kind, item["at"], ref, state, path + (0,))
                    if moving is INVALID:
                        continue
                    fixed = cert["obstacle_pieces"][obstacle]["ring"]
                    good = True
                    for point in (first[segment], first[segment + 1], second[segment + 1], second[segment]):
                        if not _strict_penetration(moving, fixed, point, state, path):
                            good = False
                    _guard(state, good, "homotopy_strict", "V5", path, "all four vertices must strictly penetrate the given same piece pair")
                    state["counts"]["homotopy_quadrilaterals"] += 1


def _v6(cert, state):
    path = ("certificate",)
    for index, piece in enumerate(cert["moving_pieces"]):
        for obstacle in cert["obstacle_pieces"]:
            _guard(state, _weak_separated(piece, obstacle["ring"], state, path + ("moving_pieces", index)),
                   "start_free", "V6", path + ("moving_pieces", index), "initial moving and obstacle interiors intersect")
    n0 = cert["start_interval"] - 1
    loop = cert["intervals"][n0]["loop"]
    origin = (Fraction(0), Fraction(0))
    avoids = True
    for index in range(len(loop) - 1):
        if _on_segment(origin, loop[index], loop[index + 1]):
            avoids = False
    _guard(state, avoids, "loop_avoids_origin", "V6", path + ("intervals", n0, "loop"), "start barrier passes through origin")
    winding = _winding(loop, origin)
    _guard(state, winding != 0, "start_winding", "V6", path + ("intervals", n0, "loop"), "start barrier has zero winding")
    state["counts"]["start_winding"] = winding


def verify_cage(instance: dict, certificate: dict) -> dict:
    """Check only the supplied witnesses, in V0/CHAIN/V1..V6 order."""
    state = {"errors": [], "ranks": {}, "counts": {"checks": 0, "strict_sat": 0,
             "barrier_segments": 0, "homotopy_quadrilaterals": 0}}
    _rank_json(instance, ("instance",), state["ranks"])
    _rank_json(certificate, ("certificate",), state["ranks"])
    source = _decode(instance, "instance", state, ("instance",))
    cert = _decode(certificate, "certificate", state, ("certificate",))
    if isinstance(cert, dict):
        _v0(source, cert, state)
    if state["errors"]:
        return _result(state)
    charts = _chain(cert, state)
    if state["errors"]:
        return _result(state)
    _v1(cert, charts, state)
    if state["errors"]:
        return _result(state)
    _v2(cert, charts, state)
    if state["errors"]:
        return _result(state)
    _v3(cert, state)
    if state["errors"]:
        return _result(state)
    _v4(cert, state)
    if state["errors"]:
        return _result(state)
    _v5(cert, charts, state)
    if state["errors"]:
        return _result(state)
    _v6(cert, state)
    return _result(state)


def _json_integer(token):
    _require(_unsigned_ascii(token), "integer_token", "V0", (), "invalid JSON integer token")
    # Manual decimal accumulation has no interpreter digit-limit restriction.
    result = 0
    for char in token:
        result = result * 10 + int(char)
    return result


def _json_string(text, position):
    first = position
    position += 1
    while position < len(text):
        char = text[position]
        if char == '"':
            position += 1
            return (json.loads(text[first:position]), position)
        if char == "\\":
            position += 1
        position += 1
    raise CageReject("json_input", "V0", (), "unterminated JSON string")


def _json_attach(stack, root, value):
    if not stack:
        _require(not root["set"], "json_input", "V0", (), "multiple JSON roots")
        root["value"] = value
        root["set"] = True
        return
    frame = stack[-1]
    if frame["kind"] == "object":
        frame["value"][frame["key"]] = value
    else:
        frame["value"].append(value)
    frame["state"] = "after"


def _json_parse(text):
    """Strict JSON parser retaining duplicate-key and integer-token evidence.

    Only strings delegate to json.loads; no callback, float, or recursion is
    used. The explicit state stack enforces commas, colons and all closings.
    """
    root = {"set": False, "value": None}
    stack = []
    position = 0
    while True:
        while position < len(text) and text[position] in " \t\r\n":
            position += 1
        if not stack and root["set"]:
            _require(position == len(text), "json_input", "V0", (), "trailing JSON input")
            return root["value"]
        _require(position < len(text), "json_input", "V0", (), "incomplete JSON input")
        char = text[position]
        if stack:
            frame = stack[-1]
            closing = "]"
            if frame["kind"] == "object":
                closing = "}"
            if frame["state"] == "after":
                if char == closing:
                    stack.pop()
                else:
                    _require(char == ",", "json_input", "V0", (), "JSON comma or closing delimiter expected")
                    frame["state"] = "next"
                position += 1
                continue
            if frame["state"] == "first" and char == closing:
                stack.pop()
                position += 1
                continue
            if frame["kind"] == "object" and frame["state"] in ("first", "next"):
                _require(char == '"', "json_input", "V0", (), "JSON object key must be a string")
                key, position = _json_string(text, position)
                _require(key not in frame["value"], "duplicate_key", "V0", (), "duplicate JSON object key: " + key)
                frame["key"] = key
                frame["state"] = "colon"
                continue
            if frame["state"] == "colon":
                _require(char == ":", "json_input", "V0", (), "JSON colon expected")
                frame["state"] = "value"
                position += 1
                continue
        if char in "{[":
            container = []
            kind = "array"
            if char == "{":
                container = {}
                kind = "object"
            _json_attach(stack, root, container)
            stack.append({"kind": kind, "value": container, "state": "first", "key": None})
            position += 1
            continue
        if char == '"':
            value, position = _json_string(text, position)
        else:
            first = position
            while position < len(text) and text[position] not in " \t\r\n,]}:":
                position += 1
            token = text[first:position]
            if token == "true":
                value = True
            elif token == "false":
                value = False
            elif token == "null":
                value = None
            else:
                value = _json_integer(token)
        _json_attach(stack, root, value)


def load_json(path):
    """Load without losing duplicate-key or numeric-token evidence."""
    with open(path, "r", encoding="utf-8") as stream:
        text = stream.read()
    return _json_parse(text)


def _load_result(instance_path, certificate_path):
    try:
        instance = load_json(instance_path)
        certificate = load_json(certificate_path)
    except CageReject as error:
        return {"valid": False, "condition": "V0", "reason": error.reason,
                "where": {"path": list(error.where), "check": error.check_id}, "counts": {}}
    except (OSError, UnicodeError, ValueError) as error:
        return {"valid": False, "condition": "V0", "reason": str(error),
                "where": {"path": [], "check": "json_input"}, "counts": {}}
    return verify_cage(instance, certificate)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) == 0 or len(argv) % 2 != 0:
        with open(2, "w", encoding="utf-8", closefd=False) as output:
            output.write("usage: verifier.py instance.json cert.json [instance.json cert.json ...]\n")
        return 2
    status = 0
    for index in range(0, len(argv), 2):
        result = _load_result(argv[index], argv[index + 1])
        with open(1, "w", encoding="utf-8", closefd=False) as output:
            output.write(json.dumps(result, ensure_ascii=True, sort_keys=True) + "\n")
        if not result["valid"]:
            status = 1
    return status


CLI_STATUS = main() if __name__ == "__main__" else 0
if CLI_STATUS:
    raise ValueError("one or more cage inputs were rejected")
