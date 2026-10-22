"""Independent exact verification of translation escape and enclosure paths.

The oracle uses only rational orientation, independent ear removal and the
separating-axis inequalities of convex input pieces. It never constructs a
Minkowski polygon and imports no production geometry. Along a translation
segment every separating-axis inequality is affine in its parameter. Strict
overlap therefore is an intersection of open intervals, not an endpoint test.

Gates: tests/test_tia2d_t1b_certificates.py checks strict enclosure, collision
inside a segment, exact transformations, malformed rings and independence.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache


def _point(value):
    if len(value) != 2 or any(not isinstance(v, (int, Fraction)) or isinstance(v, bool) for v in value):
        raise ValueError("coordinates must be integer or Fraction pairs")
    return Fraction(value[0]), Fraction(value[1])


def _orientation(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def _between(p, a, b):
    return _orientation(a, b, p) == 0 and all(
        min(a[k], b[k]) <= p[k] <= max(a[k], b[k]) for k in (0, 1))


def _intersects(a, b, c, d):
    values = (_orientation(a, b, c), _orientation(a, b, d),
              _orientation(c, d, a), _orientation(c, d, b))
    if values[0]*values[1] < 0 and values[2]*values[3] < 0:
        return True
    return any((_between(c, a, b), _between(d, a, b),
                _between(a, c, d), _between(b, c, d)))


def _validated_ring(values):
    points = tuple(_point(p) for p in values)
    count = len(points)
    if count < 3 or len(set(points)) != count:
        raise ValueError("ring requires at least three distinct vertices")
    for i in range(count):
        a, b = points[i], points[(i+1) % count]
        for j in range(i+1, count):
            if j == i+1 or (i == 0 and j == count-1):
                continue
            if _intersects(a, b, points[j], points[(j+1) % count]):
                raise ValueError("ring must be simple")
    area = sum((_orientation(points[0], points[i], points[(i+1) % count])
                for i in range(count)), Fraction(0))
    if area == 0:
        raise ValueError("ring has zero area")
    if area < 0:
        points = tuple(reversed(points))
    for i, b in enumerate(points):
        a, c = points[i-1], points[(i+1) % count]
        if _orientation(a, b, c) == 0 and not _between(b, a, c):
            raise ValueError("ring has a backtracking edge")
    # Removing an in-between collinear vertex changes neither the set nor its
    # interior, and avoids artificial zero-area ears.
    return tuple(b for i, b in enumerate(points)
                 if _orientation(points[i-1], b, points[(i+1) % count]) != 0)


@lru_cache(maxsize=128)
def _pieces(points):
    """Independent exact decomposition; a convex input stays one piece."""
    points = _validated_ring(points)
    if all(_orientation(points[i-1], p, points[(i+1) % len(points)]) > 0
           for i, p in enumerate(points)):
        return (points,)
    remaining = list(points)
    result = []
    while len(remaining) > 3:
        candidates = []
        for i, b in enumerate(remaining):
            a, c = remaining[i-1], remaining[(i+1) % len(remaining)]
            if _orientation(a, b, c) <= 0:
                continue
            if any(_orientation(a, b, p) >= 0 and
                   _orientation(b, c, p) >= 0 and
                   _orientation(c, a, p) >= 0
                   for p in remaining if p not in (a, b, c)):
                continue
            candidates.append((b, i, (a, b, c)))
        if not candidates:
            raise ValueError("ring has no certified positive-area ear")
        _, index, triangle = min(candidates)
        result.append(triangle)
        del remaining[index]
    if _orientation(*remaining) <= 0:
        raise ValueError("ring decomposition ended in a degenerate piece")
    result.append(tuple(remaining))
    return tuple(result)


@lru_cache(maxsize=1024)
def _axis_rows(first, second):
    """Rows (nx, ny, lower, upper) with lower < n.x < upper for overlap."""
    rows = []
    for polygon in (first, second):
        for i, a in enumerate(polygon):
            b = polygon[(i+1) % len(polygon)]
            nx, ny = a[1]-b[1], b[0]-a[0]
            va = [nx*p[0]+ny*p[1] for p in first]
            vb = [nx*p[0]+ny*p[1] for p in second]
            rows.append((nx, ny, min(vb)-max(va), max(vb)-min(va)))
    return tuple(rows)


def _strict_pair_segment(first, second, start, end):
    for nx, ny, lower, upper in _axis_rows(first, second):
        for point in (start, end):
            value = nx*point[0]+ny*point[1]
            if value <= lower or value >= upper:
                return False
    return True


def _pair_segment_enters(first, second, start, end):
    low, high = Fraction(0), Fraction(1)
    for nx, ny, lower, upper in _axis_rows(first, second):
        value = nx*start[0]+ny*start[1]
        slope = nx*(end[0]-start[0])+ny*(end[1]-start[1])
        if slope == 0:
            if value <= lower or value >= upper:
                return False
            continue
        a, b = (lower-value)/slope, (upper-value)/slope
        low, high = max(low, min(a, b)), min(high, max(a, b))
        if low >= high:
            return False
    return low < high


def _prepare(moving, obstacles):
    first = tuple(_point(p) for p in moving)
    others = tuple(tuple(_point(p) for p in polygon) for polygon in obstacles)
    return first, others, _pieces(first), tuple(_pieces(p) for p in others)


def _free(first_parts, other_parts, start, end):
    return not any(_pair_segment_enters(a, b, start, end)
                   for parts in other_parts for a in first_parts for b in parts)


def _witness(first_parts, other_parts, start, end):
    for obstacle_index, parts in enumerate(other_parts):
        for first_index, a in enumerate(first_parts):
            for second_index, b in enumerate(parts):
                if _strict_pair_segment(a, b, start, end):
                    return obstacle_index, first_index, second_index
    return None


def translation_segment_is_free(moving, obstacles, start, end):
    """Check all points of a closed translation segment, with contact allowed.

    Invalid polygon or nonrational inputs raise ValueError. The finite strict
    triangle-pair overlap union equals strict overlap of the original rings.
    Gate: test_escape_rejects_a_segment_with_only_free_endpoints.
    """
    _, _, first_parts, other_parts = _prepare(moving, obstacles)
    return _free(first_parts, other_parts, _point(start), _point(end))


def translation_segment_strictly_blocked(moving, obstacles, start, end):
    """True only when one independently checked convex pair contains the segment.

    This sufficient test may require a caller to subdivide a valid curve when
    several convex pieces cover it. Gate: test_enclosure_has_strict_witnesses.
    """
    _, _, first_parts, other_parts = _prepare(moving, obstacles)
    return _witness(first_parts, other_parts, _point(start), _point(end)) is not None


def _winding(path):
    origin = Fraction(0), Fraction(0)
    winding = 0
    for a, b in zip(path, path[1:]):
        if _between(origin, a, b):
            raise ValueError("enclosure curve passes through the origin")
        if a[1] <= 0 < b[1] and _orientation(a, b, origin) > 0:
            winding += 1
        elif b[1] <= 0 < a[1] and _orientation(a, b, origin) < 0:
            winding -= 1
    return winding


@dataclass(frozen=True)
class CertificateVerification:
    """Exact verifier result; witnesses index independent convex decompositions."""
    valid: bool
    reason: str
    checked_segments: int = 0
    winding_number: int = 0
    witnesses: tuple = ()
    ray_direction: tuple | None = None


def verify_escape_certificate(moving, obstacles, path):
    """Certify a free rational path and a final obstacle-free infinite axis ray.

    The end must exceed the squared diagonal of the exact obstacle bounding
    rectangle and lie strictly outside that rectangle. The rectangle comes
    directly from coordinate extrema of b-a, not from a production obstacle.
    Gate: test_escape_checks_origin_length_and_explicit_infinite_ray.
    """
    try:
        first, others, first_parts, other_parts = _prepare(moving, obstacles)
        path = tuple(_point(p) for p in path)
    except (TypeError, ValueError, ArithmeticError) as error:
        return CertificateVerification(False, str(error))
    if len(path) < 2 or path[0] != (0, 0):
        return CertificateVerification(False, "escape path must start at zero and contain a segment")
    if _free(first_parts, other_parts, path[0], path[0]) is False:
        return CertificateVerification(False, "origin strictly overlaps an obstacle")
    for index, (a, b) in enumerate(zip(path, path[1:])):
        if _free(first_parts, other_parts, a, b) is False:
            return CertificateVerification(False, "escape segment enters strict overlap", index+1)
    endpoint = path[-1]
    if not others:
        if endpoint == (0, 0):
            return CertificateVerification(False, "escape endpoint does not exceed zero diameter")
        return CertificateVerification(True, "free path and empty obstacle family", len(path)-1,
                                       ray_direction=(Fraction(1), Fraction(0)))
    bounds = tuple((min(p[k] for polygon in others for p in polygon)-max(p[k] for p in first),
                    max(p[k] for polygon in others for p in polygon)-min(p[k] for p in first))
                   for k in (0, 1))
    diagonal_squared = sum(((hi-lo)**2 for lo, hi in bounds), Fraction(0))
    if endpoint[0]**2+endpoint[1]**2 <= diagonal_squared:
        return CertificateVerification(False, "escape endpoint does not exceed obstacle diameter", len(path)-1)
    for axis, (lo, hi) in enumerate(bounds):
        if endpoint[axis] < lo or endpoint[axis] > hi:
            direction = [Fraction(0), Fraction(0)]
            direction[axis] = Fraction(-1 if endpoint[axis] < lo else 1)
            return CertificateVerification(True, "free path and outward infinite axis ray", len(path)-1,
                                           ray_direction=tuple(direction))
    return CertificateVerification(False, "escape endpoint is not outside obstacle bounds", len(path)-1)


def verify_trapping_certificate(moving, obstacles, closed_path):
    """Certify nonzero winding of a rational closed curve wholly in strict overlap.

    Each closed segment needs one convex-pair witness valid at both endpoints;
    its affine strict inequalities then hold on the complete segment. A free
    origin and nonzero winding exclude every path from the origin to infinity.
    Gate: test_enclosure_has_strict_witnesses.
    """
    try:
        _, _, first_parts, other_parts = _prepare(moving, obstacles)
        path = tuple(_point(p) for p in closed_path)
    except (TypeError, ValueError, ArithmeticError) as error:
        return CertificateVerification(False, str(error))
    if len(path) < 4 or path[0] != path[-1]:
        return CertificateVerification(False, "enclosure must be an explicitly closed polygonal path")
    if _free(first_parts, other_parts, (Fraction(0), Fraction(0)), (Fraction(0), Fraction(0))) is False:
        return CertificateVerification(False, "origin strictly overlaps an obstacle")
    try:
        winding = _winding(path)
    except ValueError as error:
        return CertificateVerification(False, str(error))
    if winding == 0:
        return CertificateVerification(False, "enclosure has zero winding about origin")
    witnesses = []
    for index, (a, b) in enumerate(zip(path, path[1:])):
        if a == b:
            return CertificateVerification(False, "enclosure has a zero-length segment", index+1)
        witness = _witness(first_parts, other_parts, a, b)
        if witness is None:
            return CertificateVerification(False, "enclosure segment lacks a strict convex-pair witness", index+1)
        witnesses.append(witness)
    return CertificateVerification(True, "strict enclosure with nonzero winding", len(path)-1,
                                   winding, tuple(witnesses))


def _square_enters(first, second, radius):
    """SAT of (first + closed square) versus second, without forming a hull."""
    axes = [(Fraction(1), Fraction(0)), (Fraction(0), Fraction(1))]
    for polygon in (first, second):
        for i, a in enumerate(polygon):
            b = polygon[(i+1) % len(polygon)]
            axes.append((a[1]-b[1], b[0]-a[0]))
    for nx, ny in axes:
        expansion = radius*(abs(nx)+abs(ny))
        va = [nx*p[0]+ny*p[1] for p in first]
        vb = [nx*p[0]+ny*p[1] for p in second]
        if max(va)+expansion <= min(vb) or max(vb) <= min(va)-expansion:
            return False
    return True


@dataclass(frozen=True)
class WobbleBoundsVerification:
    valid: bool
    reason: str
    area_lower: Fraction | None = None
    area_upper: Fraction | None = None
    diameter_squared_lower: Fraction | None = None
    diameter_squared_upper: Fraction | None = None


def verify_wobble_bounds(moving, obstacles, closed_path, radius):
    """Certify an entire free centered square and enclosure-rectangle bounds.

    SAT tests the filled square of translations, not just its boundary. The
    square is connected to the origin. Nonzero winding confines its complete
    free component to the rectangle containing the enclosure. Squared diameter
    avoids an unjustified rational representation of a square root.
    Gate: test_wobble_checks_the_filled_square_not_only_its_boundary.
    """
    moving = tuple(moving)
    obstacles = tuple(tuple(p) for p in obstacles)
    closed_path = tuple(closed_path)
    enclosure = verify_trapping_certificate(moving, obstacles, closed_path)
    if not enclosure.valid:
        return WobbleBoundsVerification(False, enclosure.reason)
    if not isinstance(radius, (int, Fraction)) or isinstance(radius, bool) or radius < 0:
        return WobbleBoundsVerification(False, "square radius must be a nonnegative exact rational")
    radius = Fraction(radius)
    _, _, first_parts, other_parts = _prepare(moving, obstacles)
    if any(_square_enters(a, b, radius)
           for parts in other_parts for a in first_parts for b in parts):
        return WobbleBoundsVerification(False, "filled translation square enters strict overlap")
    path = tuple(_point(p) for p in closed_path)
    dx, dy = (max(p[k] for p in path)-min(p[k] for p in path) for k in (0, 1))
    return WobbleBoundsVerification(True, "free filled square and strict enclosure rectangle",
                                    4*radius*radius, dx*dy, 8*radius*radius, dx*dx+dy*dy)
