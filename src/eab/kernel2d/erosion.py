"""Exact erosion of a simple filled ring by a convex rational element.

Convex inputs use shifted supporting half-planes. Nonconvex inputs use the
complete vertex/edge contact arrangement and exact containment face tests;
they are never replaced by their half-plane intersection. Only a single
positive-area simple output ring is accepted. Lower-dimensional remnants,
multiple rings and empty outputs are rejected rather than silently discarded.
Gates: tests/test_tia2d_t1b_erosion.py, especially the independent orthogonal
cell oracle and transformed concave-ring tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F

from .global_entrance import (
    _area2, _at, _cross, _edges, _on, _point, _ring, _split_segments, _sub,
)


@dataclass(frozen=True)
class ErosionResult2:
    """Rational output and explicit refusal, with rings retained for diagnosis."""

    status: str
    polygon: tuple
    reason: str | None = None
    rings: tuple = ()


def square_element():
    """The axis-aligned square [-1,1]^2, in counterclockwise order."""
    return tuple(_point(p) for p in ((-1, -1), (1, -1), (1, 1), (-1, 1)))


def octagon_element():
    """The rational octagon with coordinates (+/-1,+/-5/12) and swaps."""
    a = F(5, 12)
    return tuple(_point(p) for p in (
        (-a, -1), (a, -1), (1, -a), (1, a),
        (a, 1), (-a, 1), (-1, a), (-1, -a),
    ))


def _convex(poly):
    return all(_cross(_sub(b, a), _sub(c, b)) >= 0
               for a, b, c in zip(poly, poly[1:]+poly[:1], poly[2:]+poly[:2]))


def _simplify(poly):
    out = list(poly)
    changed = True
    while changed and len(out) >= 3:
        changed = False
        for i, b in enumerate(out):
            a, c = out[i-1], out[(i+1) % len(out)]
            if b == a or _on(b, a, c):
                del out[i]
                changed = True
                break
    if len(out) < 3:
        return tuple(out)
    start = min(range(len(out)), key=lambda index: out[index])
    return tuple(out[start:]+out[:start])


def _inside(point, poly):
    """Closed simple-ring membership by rational ray parity."""
    inside = False
    for a, b in _edges(poly):
        if _on(point, a, b):
            return True
        if (a[1] > point[1]) != (b[1] > point[1]):
            x = a[0]+(point[1]-a[1])*(b[0]-a[0])/(b[1]-a[1])
            if x > point[0]:
                inside = not inside
    return inside


def _segment_in_open_convex(a, b, poly):
    """Whether any point of closed ab lies strictly inside convex poly."""
    lower, upper = F(0), F(1)
    direction = _sub(b, a)
    for c, d in _edges(poly):
        edge = _sub(d, c)
        height, slope = _cross(edge, _sub(a, c)), _cross(edge, direction)
        if slope == 0:
            if height <= 0:
                return False
        elif slope > 0:
            lower = max(lower, -height/slope)
        else:
            upper = min(upper, -height/slope)
    # A strict feasible interval cannot be a singleton for a nonzero segment.
    return lower < upper


def _contains_element(poly, element, point):
    """Boundary containment, including exclusion of a reflex indentation.

    The average of convex element vertices is a strict interior point. With
    no ring edge entering the element's open interior, that interior is in
    one component of the complement of the ring boundary. A contained average
    therefore certifies the entire closed element by closedness of the body.
    Vertex checks are only a cheap necessary rejection, never the certificate.
"""
    moved = tuple((point[0]+v[0], point[1]+v[1]) for v in element)
    if not all(_inside(v, poly) for v in moved):
        return False
    middle = tuple(sum((p[k] for p in moved), F(0))/len(moved) for k in (0, 1))
    if not _inside(middle, poly):
        return False
    return not any(_segment_in_open_convex(a, b, moved) for a, b in _edges(poly))


def _clip(poly, a, direction, minimum):
    out = []
    if not poly:
        return ()
    for p, q in _edges(poly):
        u = _cross(direction, _sub(p, a))+minimum
        v = _cross(direction, _sub(q, a))+minimum
        if u >= 0:
            out.append(p)
        if (u < 0 < v) or (v < 0 < u):
            out.append(_at(p, _sub(q, p), u/(u-v)))
    return _simplify(tuple(out))


def _convex_erosion(poly, element):
    clipped = poly
    for a, b in _edges(poly):
        direction = _sub(b, a)
        minimum = min(_cross(direction, v) for v in element)
        clipped = _clip(clipped, a, direction, minimum)
    if len(clipped) < 3 or _area2(clipped) <= 0:
        return ErosionResult2("REJECTED", (), "EMPTY_OR_DEGENERATE")
    return ErosionResult2("ACCEPTED", clipped, rings=(clipped,))


def _contact_segments(poly, element):
    segments = set()
    for a, b in _edges(poly):
        direction = _sub(b, a)
        minimum = min(_cross(direction, v) for v in element)
        for v in element:
            if _cross(direction, v) == minimum:
                segments.add(tuple(sorted((_sub(a, v), _sub(b, v)))))
    for p in poly:
        for a, b in _edges(element):
            segments.add(tuple(sorted((_sub(p, a), _sub(p, b)))))
    return tuple(sorted(segments))


def _side_probes(a, b, segments):
    middle = ((a[0]+b[0])/2, (a[1]+b[1])/2)
    direction = (a[1]-b[1], b[0]-a[0])
    step = F(1)
    for c, d in segments:
        edge = _sub(d, c)
        height, slope = _cross(edge, _sub(middle, c)), _cross(edge, direction)
        if height and slope:
            step = min(step, abs(height/slope)/2)
    return middle, _at(middle, direction, step), _at(middle, direction, -step)


def _arrangement_erosion(poly, element):
    segments = _contact_segments(poly, element)
    atoms = _split_segments(segments)
    boundary, adjacent_area, vertices = [], set(), set()
    thin = False
    for a, b in atoms:
        vertices.update((a, b))
        middle, left, right = _side_probes(a, b, segments)
        li, ri = _contains_element(poly, element, left), _contains_element(poly, element, right)
        if li or ri:
            adjacent_area.update((a, b))
        if li != ri:
            boundary.append((a, b) if li else (b, a))
        elif not li and _contains_element(poly, element, middle):
            thin = True
    if any(_contains_element(poly, element, v) for v in vertices-adjacent_area):
        thin = True
    if thin:
        return ErosionResult2("REJECTED", (), "LOWER_DIMENSIONAL_REMNANT")
    if not boundary:
        return ErosionResult2("REJECTED", (), "EMPTY_OR_DEGENERATE")
    outgoing, incoming = {}, {}
    for a, b in boundary:
        outgoing.setdefault(a, []).append(b)
        incoming.setdefault(b, []).append(a)
    if any(len(outgoing.get(v, ())) != 1 or len(incoming.get(v, ())) != 1
           for v in set(outgoing) | set(incoming)):
        return ErosionResult2("REJECTED", (), "DEGENERATE_BOUNDARY")
    remaining = set(outgoing)
    rings = []
    while remaining:
        first = min(remaining)
        ring, current = [], first
        while current in remaining:
            remaining.remove(current)
            ring.append(current)
            current = outgoing[current][0]
        if current != first:
            return ErosionResult2("REJECTED", (), "DEGENERATE_BOUNDARY")
        rings.append(_simplify(tuple(ring)))
    rings = tuple(sorted(rings))
    if any(len(r) < 3 or _area2(r) <= 0 for r in rings):
        return ErosionResult2("REJECTED", (), "DEGENERATE_OR_INNER_RING", rings)
    if len(rings) != 1:
        return ErosionResult2("REJECTED", (), "MULTIPLE_RINGS", rings)
    return ErosionResult2("ACCEPTED", rings[0], rings=rings)


def erode_polygon_exact(poly, delta, element="square"):
    """Compute the exact closed erosion poly minus delta*element.

Input coordinates/delta are converted with Fraction, without float display
rounding. ``element`` is ``square``, ``octagon``, or a convex rational ring
containing the origin strictly. Invalid inputs raise ValueError. A valid
input whose erosion is not one positive-area simple ring returns REJECTED;
the reason and any recovered rings must not be treated as an accepted body.
"""
    poly = _ring(poly)
    delta = F(delta)
    if delta < 0:
        raise ValueError("erosion distance must be nonnegative")
    if isinstance(element, str):
        if element == "square":
            element = square_element()
        elif element == "octagon":
            element = octagon_element()
        else:
            raise ValueError("unknown erosion element")
    element = _ring(element)
    if not _convex(element) or not all(
            _cross(_sub(b, a), (-a[0], -a[1])) > 0 for a, b in _edges(element)):
        raise ValueError("erosion element must be convex and contain the origin strictly")
    if delta == 0:
        output = _simplify(poly)
        return ErosionResult2("ACCEPTED", output, rings=(output,))
    scaled = tuple((delta*p[0], delta*p[1]) for p in element)
    if _convex(poly):
        return _convex_erosion(poly, scaled)
    return _arrangement_erosion(poly, scaled)
