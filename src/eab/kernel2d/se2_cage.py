"""Exact certificates for bounded planar rigid configuration components.

The contract is docs/t2b_cage_lemma.md, version 5.  This module selects no
witnesses and never infers an escape from a rejected certificate.  Gates are
tests/test_t2b_cage.py and tests/test_t2b_mutations.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
import json

from .translation_certificates import _axis_rows, _between, _intersects, _orientation


def _unsigned_token(value):
    value = str(value)
    return value == "0" or (bool(value) and value[0] in "123456789"
                            and all(char in "0123456789" for char in value))


def _rational_token(value):
    value = str(value)
    unsigned = value[1:] if value.startswith("-") else value
    parts = unsigned.split("/")
    return (len(parts) in (1, 2) and _unsigned_token(parts[0])
            and (len(parts) == 1 or (_unsigned_token(parts[1]) and parts[1] not in ("0", "1"))))


class _Invalid(ValueError):
    def __init__(self, condition, reason, where):
        self.condition, self.reason, self.where = condition, reason, where


class _IntegerToken(str):
    pass


class _Pairs(list):
    pass


def _fail(condition, reason, where):
    raise _Invalid(condition, reason, where)


def _reject_number(value):
    _fail("V0", "noninteger JSON number or nonfinite constant", "$")


def _unpack(value, where="$"):
    where = str(where)
    if isinstance(value, _Pairs):
        result = {}
        for key, child in value:
            if key in result:
                _fail("V0", "duplicate object key", where+"."+str(key))
            result[key] = _unpack(child, where+"."+str(key))
        return result
    if isinstance(value, list):
        return [_unpack(child, where+"["+str(i)+"]") for i, child in enumerate(value)]
    return value


def _load(value):
    if isinstance(value, str):
        return _unpack(json.loads(value, object_pairs_hook=_Pairs,
                                  parse_int=_IntegerToken, parse_float=_reject_number,
                                  parse_constant=_reject_number))
    return value


def _rational(value, where):
    where = str(where)
    if type(value) is int or isinstance(value, F):
        return F(value)
    if type(value) is not str or len(value) > 4096 or not _rational_token(value):
        _fail("V0", "expected a canonical rational string", where)
    result = F(value)
    if str(result) != value:
        _fail("V0", "rational string is not reduced and canonical", where)
    return result


def _index(value, where):
    where = str(where)
    if isinstance(value, _IntegerToken):
        if not _unsigned_token(value):
            _fail("V0", "noncanonical integer token", where)
        return int(value)
    if type(value) is not int or value < 0:
        _fail("V0", "expected a nonnegative integer, not a boolean", where)
    return value


def _array(value, where):
    where = str(where)
    if not isinstance(value, (list, tuple)) or isinstance(value, _Pairs):
        _fail("V0", "expected an array", where)
    return value


def _point(value, where):
    where = str(where)
    value = _array(value, where)
    if len(value) != 2:
        _fail("V0", "point needs two coordinates", where)
    return tuple(_rational(v, where+"["+str(i)+"]") for i, v in enumerate(value))


def _poly(value, where):
    where = str(where)
    return tuple(_point(p, where+"["+str(i)+"]") for i, p in enumerate(_array(value, where)))


def _object(value, fields, where):
    where = str(where)
    if not isinstance(value, dict):
        _fail("V0", "expected an object", where)
    if set(value) != set(fields):
        _fail("V0", "all specified keys, and no other keys, are required", where)
    return value


def _literal(value, choices, where):
    where = str(where)
    if type(value) is not str or value not in choices:
        _fail("V0", "unknown fixed string value", where)
    return value


def _reference(value, where):
    where = str(where)
    value = _array(value, where)
    if not value:
        _fail("V0", "empty reference", where)
    kind = _literal(value[0], ("exact", "left", "right", "disk"), where+"[0]")
    if len(value) != (1 if kind == "disk" else 2):
        _fail("V0", "reference has wrong length", where)
    return (kind,) if kind == "disk" else (kind, _index(value[1], where+"[1]"))


def _witness(value, where, connection=False):
    where = str(where)
    value = _array(value, where)
    if len(value) != 2:
        _fail("V0", "witness needs exactly two entries", where)
    first = _reference(value[0], where+"[0]") if connection else _index(value[0], where+"[0]")
    return first, _index(value[1], where+"[1]")


def _piece(value, where):
    where = str(where)
    if not isinstance(value, dict) or "kind" not in value:
        _fail("V0", "piece requires kind", where)
    kind = _literal(value["kind"], ("rotated", "disk"), where+".kind")
    fields = ("kind",) if kind == "disk" else ("kind", "piece", "polygon")
    value = _object(value, fields, where)
    result = {}
    for key, child in value.items():
        at = where+"."+str(key)
        result[key] = kind if key == "kind" else (_index(child, at) if key == "piece" else _poly(child, at))
    return result


def _interval(value, where):
    where = str(where)
    value = _object(value, ("rho", "pieces", "loop", "witnesses"), where)
    result = {}
    for key, child in value.items():
        at = where+"."+str(key)
        if key == "rho":
            result[key] = _rational(child, at)
        elif key == "loop":
            result[key] = _poly(child, at)
        elif key == "pieces":
            result[key] = tuple(_piece(p, at+"["+str(i)+"]") for i, p in enumerate(_array(child, at)))
        else:
            result[key] = tuple(_witness(p, at+"["+str(i)+"]") for i, p in enumerate(_array(child, at)))
    return result


def _connection(value, where):
    where = str(where)
    value = _object(value, ("at", "chain", "witnesses"), where)
    result = {}
    for key, child in value.items():
        at = where+"."+str(key)
        if key == "at":
            result[key] = _index(child, at)
        elif key == "chain":
            result[key] = tuple(_poly(p, at+"["+str(i)+"]") for i, p in enumerate(_array(child, at)))
        else:
            result[key] = tuple(tuple(_witness(w, at+"["+str(i)+"]["+str(j)+"]", True)
                                      for j, w in enumerate(_array(row, at+"["+str(i)+"]")))
                                for i, row in enumerate(_array(child, at)))
    return result


def _decode(value, instance=False):
    value = _load(value)
    fields = ("moving", "obstacles") if instance else (
        "format", "moving", "obstacles", "center", "radius", "moving_pieces",
        "obstacle_pieces", "disk", "chain", "start_interval", "intervals", "links", "caps")
    value = _object(value, fields, "$")
    result = {}
    for key, child in value.items():
        at = "$."+str(key)
        if key == "format":
            result[key] = _literal(child, ("eab.t2b.cage/1",), at)
        elif key == "moving":
            result[key] = _poly(child, at)
        elif key in ("obstacles", "moving_pieces"):
            result[key] = tuple(_poly(p, at+"["+str(i)+"]") for i, p in enumerate(_array(child, at)))
        elif key == "center":
            result[key] = _point(child, at)
        elif key == "radius":
            result[key] = _rational(child, at)
        elif key == "start_interval":
            result[key] = _index(child, at)
        elif key == "obstacle_pieces":
            items = []
            for i, item in enumerate(_array(child, at)):
                path = at+"["+str(i)+"]"
                item = _object(item, ("obstacle", "ring"), path)
                items.append({k: _index(v, path+"."+str(k)) if k == "obstacle" else _poly(v, path+"."+str(k))
                              for k, v in item.items()})
            result[key] = tuple(items)
        elif key == "disk":
            if child is None:
                result[key] = None
            else:
                child = _object(child, ("radius", "host", "polygon"), at)
                result[key] = {k: _rational(v, at+"."+str(k)) if k == "radius" else (
                    _index(v, at+"."+str(k)) if k == "host" else _poly(v, at+"."+str(k))) for k, v in child.items()}
        elif key == "chain":
            child = _object(child, ("kind", "breakpoints"), at)
            result[key] = {k: _literal(v, ("closed", "capped"), at+"."+str(k)) if k == "kind" else
                           tuple(_rational(x, at+".breakpoints["+str(i)+"]")
                                 for i, x in enumerate(_array(v, at+".breakpoints"))) for k, v in child.items()}
        elif key == "intervals":
            result[key] = tuple(_interval(v, at+"["+str(i)+"]") for i, v in enumerate(_array(child, at)))
        else:
            result[key] = tuple(_connection(v, at+"["+str(i)+"]") for i, v in enumerate(_array(child, at)))
    return result


def _encode(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {k: _encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_encode(v) for v in value]
    return value


@dataclass(frozen=True)
class SE2CageCertificate:
    """Typed exact payload; geometry and witnesses remain untrusted until verified."""
    data: dict

    @classmethod
    def from_json(cls, value):
        return SE2CageCertificate(_decode(value))

    @classmethod
    def from_data(cls, value):
        return SE2CageCertificate(_decode(value))

    def to_data(self):
        return _decode(self.data)

    def to_json(self):
        return json.dumps(_encode(_decode(self.data)), ensure_ascii=True, indent=2)+"\n"


@dataclass(frozen=True)
class SE2CageVerification:
    valid: bool
    condition: str
    reason: str
    where: str
    counts: dict


def _edges(poly):
    return zip(poly, poly[1:]+poly[:1])


def _area(poly):
    return sum((a[0]*b[1]-a[1]*b[0] for a, b in _edges(poly)), F(0))


def _convex(poly, where):
    where = str(where)
    if len(poly) < 3 or len(set(poly)) != len(poly):
        _fail("V0", "strict convex ring needs distinct vertices", where)
    for i, (a, b) in enumerate(_edges(poly)):
        for j, p in enumerate(poly):
            if j not in (i, (i+1) % len(poly)) and _orientation(a, b, p) <= 0:
                _fail("V0", "ring is not strictly convex and counterclockwise", where)


def _simple(poly, where):
    where = str(where)
    if len(poly) < 3 or len(set(poly)) != len(poly) or _area(poly) <= 0:
        _fail("V0", "simple ring needs distinct vertices and positive area", where)
    for i, b in enumerate(poly):
        a, c = poly[i-1], poly[(i+1) % len(poly)]
        if _orientation(a, b, c) == 0 and not _between(b, a, c):
            _fail("V0", "adjacent edges overlap", where)
    for i, (a, b) in enumerate(_edges(poly)):
        for j, (c, d) in enumerate(_edges(poly)):
            if j <= i+1 or (i == 0 and j == len(poly)-1):
                continue
            if _intersects(a, b, c, d):
                _fail("V0", "nonadjacent edges intersect", where)


def _closed(poly, where):
    where = str(where)
    if len(poly) < 2 or poly[0] != poly[-1]:
        _fail("V0", "polyline must be explicitly closed with at least one segment", where)


def _axes(poly):
    result = []
    for a, b in _edges(poly):
        axis = a[1]-b[1], b[0]-a[0]
        if axis == (0, 0):
            _fail("V0", "zero separating axis", "$.axis")
        result.append(axis)
    return tuple(result)


def _weak_separated(first, second):
    axes = _axes(first)+_axes(second)
    for nx, ny in axes:
        a = tuple(nx*p[0]+ny*p[1] for p in first)
        b = tuple(nx*p[0]+ny*p[1] for p in second)
        if max(a) <= min(b) or max(b) <= min(a):
            return True
    return False


def _winding_value(poly, point):
    winding = 0
    for a, b in zip(poly, poly[1:]):
        if _between(point, a, b):
            return None
        side = _orientation(a, b, point)
        if a[1] <= point[1] < b[1] and side > 0:
            winding += 1
        elif b[1] <= point[1] < a[1] and side < 0:
            winding -= 1
    return winding


def _contained(piece, parent):
    point = tuple(sum((p[k] for p in piece), F(0))/len(piece) for k in (0, 1))
    if _winding_value(parent+parent[:1], point) in (None, 0):
        return False
    return all(_weak_separated(piece, (a, b)) for a, b in _edges(parent))


def _partition(parent, pieces, where):
    where = str(where)
    if not pieces:
        _fail("V0", "every parent needs at least one piece", where)
    for i, piece in enumerate(pieces):
        if not _contained(piece, parent):
            _fail("V0", "piece is not contained in its parent", where+"["+str(i)+"]")
        for other in pieces[:i]:
            if not _weak_separated(piece, other):
                _fail("V0", "partition interiors overlap", where)
    if sum((_area(p) for p in pieces), F(0)) != _area(parent):
        _fail("V0", "partition area differs from parent area", where)


def _range(value, count, where):
    if not 0 <= value < count:
        _fail("V0", "index out of range", where)


def _check_v0(instance, cert, counts):
    if instance["moving"] != cert["moving"]:
        _fail("V0", "moving ring differs from the independent instance", "$.moving")
    if instance["obstacles"] != cert["obstacles"]:
        _fail("V0", "obstacle rings differ from the independent instance", "$.obstacles")
    _simple(cert["moving"], "$.moving")
    for i, p in enumerate(cert["obstacles"]):
        _simple(p, "$.obstacles["+str(i)+"]")
    radius, center = cert["radius"], cert["center"]
    if radius <= 0:
        _fail("V0", "radius must be positive", "$.radius")
    if any((v[0]-center[0])**2+(v[1]-center[1])**2 > radius**2
           for p in cert["moving_pieces"] for v in p):
        _fail("V0", "radius does not enclose every moving piece vertex", "$.radius")
    for i, p in enumerate(cert["moving_pieces"]):
        _convex(p, "$.moving_pieces["+str(i)+"]")
    _partition(cert["moving"], cert["moving_pieces"], "$.moving_pieces")
    for i, p in enumerate(cert["obstacle_pieces"]):
        at = "$.obstacle_pieces["+str(i)+"]"
        _range(p["obstacle"], len(cert["obstacles"]), at+".obstacle")
        _convex(p["ring"], at+".ring")
    for j, parent in enumerate(cert["obstacles"]):
        _partition(parent, tuple(p["ring"] for p in cert["obstacle_pieces"] if p["obstacle"] == j),
                   "$.obstacle_pieces")
    disk = cert["disk"]
    if disk is not None:
        if disk["radius"] <= 0:
            _fail("V0", "invariant radius must be positive", "$.disk.radius")
        _range(disk["host"], len(cert["moving_pieces"]), "$.disk.host")
        _convex(disk["polygon"], "$.disk.polygon")
    n = len(cert["chain"]["breakpoints"])-1
    if not 1 <= cert["start_interval"] <= n:
        _fail("V0", "start interval out of range", "$.start_interval")
    if len(cert["intervals"]) != n:
        _fail("V0", "interval count differs from breakpoint count", "$.intervals")
    for i, interval in enumerate(cert["intervals"]):
        at = "$.intervals["+str(i)+"]"
        if not interval["pieces"]:
            _fail("V0", "interval needs at least one inner piece", at+".pieces")
        for k, piece in enumerate(interval["pieces"]):
            path = at+".pieces["+str(k)+"]"
            if piece["kind"] == "disk":
                if disk is None:
                    _fail("V0", "missing invariant polygon", path)
            else:
                _range(piece["piece"], len(cert["moving_pieces"]), path+".piece")
                _convex(piece["polygon"], path+".polygon")
        _closed(interval["loop"], at+".loop")
        if len(interval["witnesses"]) != len(interval["loop"])-1:
            _fail("V0", "witness count differs from segment count", at+".witnesses")
        for k, l in interval["witnesses"]:
            _range(k, len(interval["pieces"]), at+".witnesses")
            _range(l, len(cert["obstacle_pieces"]), at+".witnesses")
    for family in ("links", "caps"):
        for i, link in enumerate(cert[family]):
            at = "$."+family+"["+str(i)+"]"
            _range(link["at"], n+1, at+".at")
            chain = link["chain"]
            if len(chain) < 2:
                _fail("V0", "connection needs at least two polylines", at+".chain")
            for j, poly in enumerate(chain):
                _closed(poly, at+".chain["+str(j)+"]")
                if j and len(poly) != len(chain[j-1]):
                    _fail("V0", "adjacent polylines have unequal vertex counts", at+".chain")
            if len(link["witnesses"]) != len(chain)-1:
                _fail("V0", "connection witness row count differs", at+".witnesses")
            for row, poly in zip(link["witnesses"], chain):
                if len(row) != len(poly)-1:
                    _fail("V0", "connection witness count differs from segment count", at+".witnesses")
                for ref, l in row:
                    _range(l, len(cert["obstacle_pieces"]), at+".witnesses")
                    if ref[0] == "exact":
                        _range(ref[1], len(cert["moving_pieces"]), at+".witnesses")
                    elif ref[0] == "disk" and disk is None:
                        _fail("V0", "missing invariant polygon", at+".witnesses")
    counts["moving_pieces"] = len(cert["moving_pieces"])
    counts["obstacle_pieces"] = len(cert["obstacle_pieces"])


def _chart(low, high):
    middle = (low+high)/2
    k = -((-(middle-3))//4)
    base = 4*k
    if middle-base > 1:
        base += 2
        sign = -1
    else:
        sign = 1
    return base, sign, low-base, high-base


def _rotate(point, value, chart, condition, where):
    base, sign, _, _ = chart
    u = value-base
    if not -1 <= u <= 1:
        _fail(condition, "rotation parameter outside its interval chart", where)
    x, y = point
    return (sign*((1-u*u)*x-2*u*y)/(1+u*u),
            sign*(2*u*x+(1-u*u)*y)/(1+u*u))


def _check_chain(cert, counts):
    breaks, kind = cert["chain"]["breakpoints"], cert["chain"]["kind"]
    n = len(breaks)-1
    charts = tuple(_chart(a, b) for a, b in zip(breaks, breaks[1:]))
    start = cert["start_interval"]-1
    k = -((-breaks[start])//4)
    for field in cert:
        if field == "chain":
            for part in cert["chain"]:
                if part == "breakpoints":
                    if n < 1 or any(a >= b for a, b in zip(breaks, breaks[1:])):
                        _fail("CHAIN", "breakpoints must strictly increase with at least one interval", "$.chain.breakpoints")
                    for i, (_, _, low, high) in enumerate(charts):
                        if not -1 <= low < high <= 1:
                            _fail("CHAIN", "interval crosses its midpoint-selected chart boundary", "$.chain.breakpoints["+str(i)+"]")
                elif (kind == "closed" and breaks[-1]-breaks[0] != 4) or (kind == "capped" and breaks[-1]-breaks[0] >= 4):
                    _fail("CHAIN", "chain span differs from its kind", "$.chain")
        elif field == "start_interval":
            if not breaks[start] <= 4*k <= breaks[start+1]:
                _fail("CHAIN", "start interval does not contain a lift of zero", "$.start_interval")
            if kind == "capped" and not breaks[0] < 4*k < breaks[-1]:
                _fail("CHAIN", "zero rotation must be strictly inside a capped chain", "$.start_interval")
        elif field == "links":
            expected = list(range(1, n+1 if kind == "closed" else n))
            if sorted(link["at"] for link in cert["links"]) != expected:
                _fail("CHAIN", "connection indices do not match required breakpoints", "$.links")
            for i, link in enumerate(cert["links"]):
                at = link["at"]
                if link["chain"][0] != cert["intervals"][at-1]["loop"] or link["chain"][-1] != cert["intervals"][at % n]["loop"]:
                    _fail("CHAIN", "connection endpoints differ from the interval polylines", "$.links["+str(i)+"].chain")
        elif field == "caps":
            expected_caps = [] if kind == "closed" else [0, n]
            if sorted(cap["at"] for cap in cert["caps"]) != expected_caps:
                _fail("CHAIN", "cap indices do not match both distinct endpoints", "$.caps")
            for i, cap in enumerate(cert["caps"]):
                index = 0 if cap["at"] == 0 else n-1
                if cap["chain"][0] != cert["intervals"][index]["loop"]:
                    _fail("CHAIN", "cap does not start at its interval polyline", "$.caps["+str(i)+"].chain")
                if any(p != cap["chain"][-1][0] for p in cap["chain"][-1]):
                    _fail("CHAIN", "cap does not end at a constant polyline", "$.caps["+str(i)+"].chain")
    counts["intervals"] = n
    return charts


def _body(piece, center):
    return tuple((p[0]-center[0], p[1]-center[1]) for p in piece)


def _world(piece, center):
    return tuple((p[0]+center[0], p[1]+center[1]) for p in piece)


def _halfplanes(poly):
    rows = []
    for a, b in _edges(poly):
        nx, ny = b[1]-a[1], a[0]-b[0]
        if nx == 0 and ny == 0:
            _fail("V0", "zero halfplane normal", "$.axis")
        rows.append((nx, ny, nx*a[0]+ny*a[1]))
    return tuple(rows)


def _check_v1(cert, charts, counts):
    for i, (interval, chart) in enumerate(zip(cert["intervals"], charts)):
        rho, low, high = interval["rho"], chart[2], chart[3]
        if rho < 0:
            _fail("V1", "negative contraction radius", "$.intervals["+str(i)+"].rho")
        if any(p["kind"] == "rotated" for p in interval["pieces"]):
            middle = (low+high)/2
            bound = 4*cert["radius"]**2*max((u-middle)**2/((1+u*u)*(1+middle*middle)) for u in (low, high))
            if rho**2 < bound:
                _fail("V1", "contraction radius below the exact rotation bound", "$.intervals["+str(i)+"].rho")


def _check_v2(cert, charts, counts):
    breaks = cert["chain"]["breakpoints"]
    for i, interval in enumerate(cert["intervals"]):
        for k, piece in enumerate(interval["pieces"]):
            if piece["kind"] == "disk":
                continue
            at = "$.intervals["+str(i)+"].pieces["+str(k)+"].polygon"
            source = _body(cert["moving_pieces"][piece["piece"]], cert["center"])
            rotated = tuple(_rotate(p, (breaks[i]+breaks[i+1])/2, charts[i], "V2", at) for p in source)
            for nx, ny, b in _halfplanes(rotated):
                for x, y in piece["polygon"]:
                    gap = b-nx*x-ny*y
                    if gap < 0 or gap**2 < interval["rho"]**2*(nx*nx+ny*ny):
                        _fail("V2", "inner polygon violates a contracted halfplane", at)
                    counts["contraction_inequalities"] += 1


def _check_v3(cert, counts):
    disk = cert["disk"]
    if disk is None:
        return
    for field in disk:
        if field == "host":
            host = _body(cert["moving_pieces"][disk["host"]], cert["center"])
            for nx, ny, b in _halfplanes(host):
                if b < 0 or b*b < disk["radius"]**2*(nx*nx+ny*ny):
                    _fail("V3", "invariant circle is not contained in its host", "$.disk.host")
        elif field == "polygon":
            for x, y in disk["polygon"]:
                if x*x+y*y > disk["radius"]**2:
                    _fail("V3", "invariant polygon leaves its circle", "$.disk.polygon")


def _inner(cert, interval, index):
    piece = cert["intervals"][interval]["pieces"][index]
    polygon = cert["disk"]["polygon"] if piece["kind"] == "disk" else piece["polygon"]
    return _world(polygon, cert["center"])


def _strict_points(first, second, points):
    _axes(first)
    _axes(second)
    for nx, ny, lower, upper in _axis_rows(first, second):
        for point in points:
            value = nx*point[0]+ny*point[1]
            if value <= lower or value >= upper:
                return False
    return True


def _check_v4(cert, counts):
    for i, interval in enumerate(cert["intervals"]):
        for s, ((a, b), (k, l)) in enumerate(zip(zip(interval["loop"], interval["loop"][1:]), interval["witnesses"])):
            if not _strict_points(_inner(cert, i, k), cert["obstacle_pieces"][l]["ring"], (a, b)):
                _fail("V4", "supplied segment witness is not strictly penetrating", "$.intervals["+str(i)+"].witnesses["+str(s)+"]")
            counts["barrier_segments"] += 1


def _resolve(cert, ref, at, cap, charts, where):
    n = len(cert["intervals"])
    kind = ref[0]
    if kind == "disk":
        return _world(cert["disk"]["polygon"], cert["center"])
    if kind == "exact":
        chart_index = 0 if at == 0 else at-1
        points = _body(cert["moving_pieces"][ref[1]], cert["center"])
        rotated = tuple(_rotate(p, cert["chain"]["breakpoints"][at], charts[chart_index], "V5", where) for p in points)
        return _world(rotated, cert["center"])
    if cap and ((at == 0 and kind == "left") or (at == n and kind == "right")):
        _fail("V5", "reference uses the absent side of a cap", where)
    interval = (at-1) % n if kind == "left" else at % n
    if not 0 <= ref[1] < len(cert["intervals"][interval]["pieces"]):
        _fail("V5", "side reference index out of range", where)
    return _inner(cert, interval, ref[1])


def _check_v5(cert, charts, counts):
    for family in (key for key in cert if key in ("links", "caps")):
        for i, link in enumerate(cert[family]):
            for j, (first, second, row) in enumerate(zip(link["chain"], link["chain"][1:], link["witnesses"])):
                for s, (ref, l) in enumerate(row):
                    at = "$."+family+"["+str(i)+"].witnesses["+str(j)+"]["+str(s)+"]"
                    piece = _resolve(cert, ref, link["at"], family == "caps", charts, at)
                    points = first[s], first[s+1], second[s+1], second[s]
                    if not _strict_points(piece, cert["obstacle_pieces"][l]["ring"], points):
                        _fail("V5", "supplied four-point witness is not strictly penetrating", at)
                    counts["connection_quadrilaterals"] += 1


def _check_v6(cert, counts):
    for field in cert:
        if field == "moving_pieces":
            for i, a in enumerate(cert["moving_pieces"]):
                for j, b in enumerate(cert["obstacle_pieces"]):
                    if not _weak_separated(a, b["ring"]):
                        _fail("V6", "initial pose is not free", "$.moving_pieces["+str(i)+"]")
                    counts["initial_pairs"] += 1
        elif field == "start_interval":
            loop = cert["intervals"][cert["start_interval"]-1]["loop"]
            winding = _winding_value(loop, (F(0), F(0)))
            if winding is None or winding == 0:
                _fail("V6", "initial loop crosses zero or has zero signed winding", "$.start_interval")
            counts["winding_number"] = winding


class _NumberToken(str):
    """Rejected numeric token retained only for failed-input diagnostic location."""


def _diagnostic_input(value, errors, positions, where="$"):
    """Keep input occurrence order even when a later number or key is invalid."""
    where = str(where)
    if where not in positions:
        positions[where] = len(positions)
    if isinstance(value, _Pairs):
        result = {}
        for key, child in value:
            at = where+"."+str(key)
            if key in result:
                errors.append(_Invalid("V0", "duplicate object key", at))
            decoded = _diagnostic_input(child, errors, positions, at)
            if key not in result:
                result[key] = decoded
        return result
    if isinstance(value, dict):
        return {key: _diagnostic_input(value[key], errors, positions, where+"."+str(key))
                for key in value}
    if isinstance(value, (list, tuple)):
        return [_diagnostic_input(child, errors, positions, where+"["+str(i)+"]")
                for i, child in enumerate(value)]
    return value


def _diagnostic_check(errors, operation, *arguments):
    """Reuse a fixed exact check; this dispatcher cannot select witnesses."""
    try:
        if operation == "array":
            result = _array(arguments[0], arguments[1])
        elif operation == "poly":
            result = _poly(arguments[0], arguments[1])
        elif operation == "simple":
            result = _simple(arguments[0], arguments[1])
        elif operation == "convex":
            result = _convex(arguments[0], arguments[1])
        elif operation == "closed":
            result = _closed(arguments[0], arguments[1])
        elif operation == "rational":
            result = _rational(arguments[0], arguments[1])
        elif operation == "index":
            result = _index(arguments[0], arguments[1])
        elif operation == "point":
            result = _point(arguments[0], arguments[1])
        elif operation == "witness":
            result = _witness(arguments[0], arguments[1], arguments[2])
        elif operation == "literal":
            result = _literal(arguments[0], arguments[1], arguments[2])
        elif operation == "partition":
            result = _partition(arguments[0], arguments[1], arguments[2])
        elif operation == "range":
            result = _range(arguments[0], arguments[1], arguments[2])
        else:
            _fail("V0", "unknown diagnostic operation", "$")
        return True, result
    except _Invalid as error:
        errors.append(error)
        return False, None


def _diagnostic_fields(kind, value):
    if kind == "certificate":
        return {"format": "format", "moving": "simple", "obstacles": "simple[]",
                "center": "point", "radius": "rational", "moving_pieces": "convex[]",
                "obstacle_pieces": "obstacle_piece[]", "disk": "disk", "chain": "turn_chain",
                "start_interval": "index", "intervals": "interval[]", "links": "connection[]",
                "caps": "connection[]"}
    if kind == "obstacle_piece":
        return {"obstacle": "index", "ring": "convex"}
    if kind == "disk":
        return {"radius": "rational", "host": "index", "polygon": "convex"}
    if kind == "turn_chain":
        return {"kind": "chain_kind", "breakpoints": "rational[]"}
    if kind == "interval":
        return {"rho": "rational", "pieces": "inner_piece[]", "loop": "closed",
                "witnesses": "segment_witness[]"}
    if kind == "connection":
        return {"at": "index", "chain": "closed[]", "witnesses": "connection_witness[][]"}
    if kind == "inner_piece":
        if value.get("kind") == "disk":
            return {"kind": "piece_kind"}
        return {"kind": "piece_kind", "piece": "index", "polygon": "convex"}
    return None


def _diagnostic_decode(value, kind, where, errors, parsed, geometry):
    """Partial typed view for diagnostics, never used as a certificate to accept."""
    where, kind = str(where), str(kind)
    if kind.endswith("[]"):
        ok, values = _diagnostic_check(errors, "array", value, where)
        if not ok:
            return False, None
        parsed[where+"#count"] = len(values)
        result, complete = [], True
        for i, child in enumerate(values):
            valid, item = _diagnostic_decode(child, kind[:-2], where+"["+str(i)+"]",
                                             errors, parsed, geometry)
            complete = complete and valid
            result.append(item)
        if complete:
            parsed[where] = tuple(result)
        return complete, tuple(result)
    if kind in ("simple", "convex", "closed"):
        ok, result = _diagnostic_check(errors, "poly", value, where)
        if ok:
            parsed[where] = result
            if kind == "simple":
                valid, _ = _diagnostic_check(errors, "simple", result, where)
            elif kind == "convex":
                valid, _ = _diagnostic_check(errors, "convex", result, where)
            else:
                valid, _ = _diagnostic_check(errors, "closed", result, where)
            geometry[where] = valid
        return ok, result
    if kind == "disk" and value is None:
        parsed[where] = None
        return True, None
    if kind in ("certificate", "obstacle_piece", "disk", "turn_chain", "interval", "connection", "inner_piece"):
        if not isinstance(value, dict):
            errors.append(_Invalid("V0", "expected an object", where))
            return False, None
        fields = _diagnostic_fields(kind, value)
        complete = True
        if any(key not in value for key in fields):
            errors.append(_Invalid("V0", "all specified keys, and no other keys, are required", where))
            complete = False
        result = {}
        for key in value:
            at = where+"."+str(key)
            if key not in fields:
                errors.append(_Invalid("V0", "unknown object key", at))
                complete = False
                continue
            valid, child = _diagnostic_decode(value[key], fields[key], at, errors, parsed, geometry)
            complete = complete and valid
            result[key] = child
        if complete:
            parsed[where] = result
        return complete, result
    if kind == "rational":
        ok, result = _diagnostic_check(errors, "rational", value, where)
    elif kind == "index":
        ok, result = _diagnostic_check(errors, "index", value, where)
    elif kind == "point":
        ok, result = _diagnostic_check(errors, "point", value, where)
    elif kind in ("segment_witness", "connection_witness"):
        ok, result = _diagnostic_check(errors, "witness", value, where, kind == "connection_witness")
    else:
        choices = {"format": ("eab.t2b.cage/1",), "chain_kind": ("closed", "capped"),
                   "piece_kind": ("rotated", "disk")}
        ok, result = _diagnostic_check(errors, "literal", value, choices[kind], where)
    if ok:
        parsed[where] = result
    return ok, result


def _diagnostic_relations(instance, values, geometry, errors):
    """Locate V0 relations at their existing subject fields, not at dependencies."""
    for field in ("moving", "obstacles"):
        at = "$."+field
        if at in values and values[at] != instance[field]:
            errors.append(_Invalid("V0", "geometry differs from the independent instance", at))
    radius = values.get("$.radius")
    if radius is not None:
        if radius <= 0:
            errors.append(_Invalid("V0", "radius must be positive", "$.radius"))
        if "$.center" in values and "$.moving_pieces" in values:
            center = values["$.center"]
            if any((v[0]-center[0])**2+(v[1]-center[1])**2 > radius**2
                   for piece in values["$.moving_pieces"] for v in piece):
                errors.append(_Invalid("V0", "radius does not enclose every moving piece vertex", "$.radius"))
    moving = values.get("$.moving_pieces")
    moving_count = values.get("$.moving_pieces#count")
    obstacles = values.get("$.obstacles")
    obstacle_count = values.get("$.obstacles#count")
    others = values.get("$.obstacle_pieces")
    other_count = values.get("$.obstacle_pieces#count")
    if moving is not None and geometry.get("$.moving") and all(
            geometry.get("$.moving_pieces["+str(i)+"]") for i in range(len(moving))):
        _diagnostic_check(errors, "partition", values["$.moving"], moving, "$.moving_pieces")
    if obstacle_count is not None:
        for at in values:
            at = str(at)
            if at.startswith("$.obstacle_pieces[") and at.endswith(".obstacle"):
                _diagnostic_check(errors, "range", values[at], obstacle_count, at)
    if obstacles is not None and others is not None:
        for j, parent in enumerate(obstacles):
            selected = tuple(piece["ring"] for piece in others if piece["obstacle"] == j)
            if geometry.get("$.obstacles["+str(j)+"]") and all(
                    geometry.get("$.obstacle_pieces["+str(i)+"].ring")
                    for i, piece in enumerate(others) if piece["obstacle"] == j):
                _diagnostic_check(errors, "partition", parent, selected, "$.obstacle_pieces")
    if "$.disk.radius" in values and values["$.disk.radius"] <= 0:
        errors.append(_Invalid("V0", "invariant radius must be positive", "$.disk.radius"))
    if moving_count is not None and "$.disk.host" in values:
        _diagnostic_check(errors, "range", values["$.disk.host"], moving_count, "$.disk.host")
    breaks = values.get("$.chain.breakpoints")
    n = None if breaks is None else len(breaks)-1
    if n is not None and "$.start_interval" in values and not 1 <= values["$.start_interval"] <= n:
        errors.append(_Invalid("V0", "start interval out of range", "$.start_interval"))
    intervals = values.get("$.intervals")
    if intervals is not None and n is not None and len(intervals) != n:
        errors.append(_Invalid("V0", "interval count differs from breakpoint count", "$.intervals"))
    for at in values:
        at = str(at)
        if at.startswith("$.intervals[") and at.endswith(".pieces") and not values[at]:
            errors.append(_Invalid("V0", "interval needs at least one inner piece", at))
        if at.startswith("$.intervals[") and at.endswith(".piece") and moving_count is not None:
            _diagnostic_check(errors, "range", values[at], moving_count, at)
        if at.startswith("$.intervals[") and at.endswith(".kind") and values[at] == "disk" and "$.disk" in values and values["$.disk"] is None:
            errors.append(_Invalid("V0", "missing invariant polygon", at[:-5]))
        if at.startswith("$.intervals[") and at.endswith(".witnesses"):
            base = at[:-10]
            if base+".loop" in values and len(values[at]) != len(values[base+".loop"])-1:
                errors.append(_Invalid("V0", "witness count differs from segment count", at))
            for s, (k, l) in enumerate(values[at]):
                if base+".pieces" in values:
                    _diagnostic_check(errors, "range", k, len(values[base+".pieces"]), at+"["+str(s)+"][0]")
                if others is not None:
                    _diagnostic_check(errors, "range", l, len(others), at+"["+str(s)+"][1]")
        if at.startswith("$.intervals[") and ".witnesses[" in at and at.endswith("]"):
            base, tail = at.split(".witnesses", 1)
            base, tail = str(base), str(tail)
            if tail.count("[") == 1:
                k, l = values[at]
                if base+".pieces#count" in values:
                    _diagnostic_check(errors, "range", k, values[base+".pieces#count"], at+"[0]")
                if other_count is not None:
                    _diagnostic_check(errors, "range", l, other_count, at+"[1]")
    for family in ("links", "caps"):
        prefix = "$."+family+"["
        for at in values:
            at = str(at)
            if not at.startswith(prefix):
                continue
            if at.endswith(".at") and n is not None:
                _diagnostic_check(errors, "range", values[at], int(n)+1, at)
            if at.endswith(".chain"):
                chain = values[at]
                if len(chain) < 2:
                    errors.append(_Invalid("V0", "connection needs at least two polylines", at))
                if any(len(a) != len(b) for a, b in zip(chain, chain[1:])):
                    errors.append(_Invalid("V0", "adjacent polylines have unequal vertex counts", at))
            if at.endswith(".witnesses"):
                chain = values.get(at[:-10]+".chain")
                if chain is not None:
                    if len(values[at]) != len(chain)-1:
                        errors.append(_Invalid("V0", "connection witness row count differs", at))
                    for row, poly in zip(values[at], chain):
                        if len(row) != len(poly)-1:
                            errors.append(_Invalid("V0", "connection witness count differs from segment count", at))
                for j, row in enumerate(values[at]):
                    for s, (ref, l) in enumerate(row):
                        position = at+"["+str(j)+"]["+str(s)+"]"
                        if others is not None:
                            _diagnostic_check(errors, "range", l, len(others), position+"[1]")
                        if ref[0] == "exact" and moving is not None:
                            _diagnostic_check(errors, "range", ref[1], len(moving), position+"[0][1]")
                        if ref[0] == "disk" and "$.disk" in values and values["$.disk"] is None:
                            errors.append(_Invalid("V0", "missing invariant polygon", position+"[0]"))
            if ".witnesses[" in at and at.endswith("]") and at.split(".witnesses", 1)[1].count("[") == 2:
                ref, l = values[at]
                if other_count is not None:
                    _diagnostic_check(errors, "range", l, other_count, at+"[1]")
                if ref[0] == "exact" and moving_count is not None:
                    _diagnostic_check(errors, "range", ref[1], moving_count, at+"[0][1]")
                if ref[0] == "disk" and "$.disk" in values and values["$.disk"] is None:
                    errors.append(_Invalid("V0", "missing invariant polygon", at+"[0]"))


def _ordered_v0_error(instance, raw, original):
    """Refine only an existing V0 rejection; never change a validity decision.

    Present data are ordered by JSON occurrence. Missing keys anchor at their
    containing object; radius and partition relations anchor at their subject
    fields. These diagnostic-location conventions do not alter the lemma.
    """
    try:
        value = (json.loads(raw, object_pairs_hook=_Pairs, parse_int=_IntegerToken,
                            parse_float=_NumberToken, parse_constant=_NumberToken)
                 if isinstance(raw, str) else raw)
        errors, positions, parsed, geometry = [], {}, {}, {}
        value = _diagnostic_input(value, errors, positions)
        _diagnostic_decode(value, "certificate", "$", errors, parsed, geometry)
        _diagnostic_relations(instance, parsed, geometry, errors)
        if errors:
            best = errors[0]
            for error in errors[1:]:
                if positions.get(error.where, len(positions)) < positions.get(best.where, len(positions)):
                    best = error
            return best
    except (TypeError, ValueError, ArithmeticError, RecursionError, KeyError, IndexError):
        pass
    return original


def verify_se2_cage(instance, certificate):
    """Check an independently supplied instance against an untrusted cage.

    In-memory exact integers/Fractions are accepted; JSON rational fields must
    be canonical strings.  Invalid certificates return their first condition
    in V0, CHAIN, V1, ..., V6 order.  No rejected proposal proves an escape.
    """
    counts = {"contraction_inequalities": 0, "barrier_segments": 0,
              "connection_quadrilaterals": 0, "initial_pairs": 0}
    decoded_instance = None
    raw = None
    try:
        instance = _decode(instance, True)
        decoded_instance = instance
        raw = certificate.data if isinstance(certificate, SE2CageCertificate) else certificate
        cert = _decode(raw)
        _check_v0(instance, cert, counts)
        charts = _check_chain(cert, counts)
        _check_v1(cert, charts, counts)
        _check_v2(cert, charts, counts)
        _check_v3(cert, counts)
        _check_v4(cert, counts)
        _check_v5(cert, charts, counts)
        _check_v6(cert, counts)
    except _Invalid as error:
        if error.condition == "V0" and decoded_instance is not None:
            error = _ordered_v0_error(decoded_instance, raw, error)
        return SE2CageVerification(False, error.condition, error.reason, error.where, counts)
    except (TypeError, ValueError, ArithmeticError, RecursionError) as error:
        return SE2CageVerification(False, "V0", str(error), "$", counts)
    return SE2CageVerification(True, "ACCEPTED", "exact cage conditions verified", "$", counts)
