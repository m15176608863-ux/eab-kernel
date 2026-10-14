"""Exact PD_closed query without constructing the entire cell arrangement.

For each CCW convex-cell edge, subtract intervals on which another closed
cell occupies its outward side.  Positive-length gaps, with their closures,
are exactly the exposed edge pieces.  In particular a tight-fit internal
seam covered from its other side is not a union boundary.  The proof and
finite-endpoint qualification are in m4c_motion_entrance_design.md T3a.

All quantities remain Fraction.  The returned Distance2 owns the existing
construction.py display boundary; this module produces no binary64 value.
M3 comparisons are consistency gates, not an independent oracle.  Independent
rectangle and tight-seam formulas are in tests/test_m4c_exit.py.
"""
from __future__ import annotations

from fractions import Fraction as F

from .global_entrance import Distance2, GlobalEntrance2, _point


def _edges(ring):
    return zip(ring, ring[1:]+ring[:1])


def _difference(a, b):
    return a[0]-b[0], a[1]-b[1]


def _cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def _dot(a, b):
    return a[0]*b[0]+a[1]*b[1]


def _at(a, direction, parameter):
    return a[0]+parameter*direction[0], a[1]+parameter*direction[1]


def _nearest_segment(a, b, x):
    direction = _difference(b, a)
    parameter = min(F(1), max(F(0), _dot(_difference(x, a), direction)/_dot(direction, direction)))
    point = _at(a, direction, parameter)
    offset = _difference(point, x)
    return _dot(offset, offset), point


def _covers_outward_parallel(orient, outward_slope):
    """A coincident support is covered only on the cell's inward side."""
    return orient > 0 or (orient == 0 and outward_slope >= 0)


def _outward_interval(a, direction, outward, cell):
    """Closure of one positive-length outward-covered parameter interval.

At finitely many endpoints a nonparallel inequality may require a separate
epsilon sign.  Only positive-length complement pieces are used, followed by
closure, so those endpoint-only distinctions cannot add a boundary segment.
"""
    low, high = F(0), F(1)
    for p, q in _edges(cell):
        edge = _difference(q, p)
        origin = _cross(edge, _difference(a, p))
        slope = _cross(edge, direction)
        if not slope:
            if not _covers_outward_parallel(origin, _cross(edge, outward)):
                return None
        else:
            root = -origin/slope
            if slope > 0:
                low = max(low, root)
            else:
                high = min(high, root)
            if low >= high:
                return None
    return (low, high) if low < high else None


def _exposed_parameters(a, b, cells):
    direction = _difference(b, a)
    outward = direction[1], -direction[0]
    covered = []
    for cell in cells:
        interval = _outward_interval(a, direction, outward, cell)
        if interval is not None:
            covered.append(interval)
    cursor = F(0)
    exposed = []
    for low, high in sorted(covered):
        if cursor < low:
            exposed.append((cursor, low))
        cursor = max(cursor, high)
        if cursor >= 1:
            return tuple(exposed)
    if cursor < 1:
        exposed.append((cursor, F(1)))
    return tuple(exposed)


def _strictly_worse(bound, best):
    # Equal lower bounds may contain distinct tied minimizers and MUST run.
    return best is not None and bound > best


def shortest_exit_fast(A_or_model, B=None, x=(0, 0)):
    """PD_closed and all tied rational nearest points on boundary(E).

Accept a GlobalEntrance2, or two simple rings A/B.  Input in E is required;
the boundary endpoint remains in E, and is not a strict separation witness.
This is a query implementation, not a change to M3's geometry semantics.
Gates: test_fast_exit_equals_m3_complete_ties,
test_fast_exit_matches_independent_rectangle_and_tight_seam_formulas,
test_fast_exit_is_rigid_and_unit_covariant.
"""
    if isinstance(A_or_model, GlobalEntrance2):
        if B is not None:
            raise ValueError("B must be omitted when supplying GlobalEntrance2")
        model = A_or_model
    else:
        if B is None:
            raise ValueError("both A and B are required")
        model = GlobalEntrance2(A_or_model, B)
    x = _point(x)
    if model.membership(x) < 0:
        raise ValueError("shortest exit requires a point of E")
    candidates = sorted((_nearest_segment(a, b, x)[0], a, b)
                        for a, b in {edge for cell in model.cells for edge in _edges(cell)})
    best, tied = None, set()
    for bound, a, b in candidates:
        if _strictly_worse(bound, best):
            break
        direction = _difference(b, a)
        for low, high in _exposed_parameters(a, b, model.cells):
            p, q = _at(a, direction, low), _at(a, direction, high)
            squared, point = _nearest_segment(p, q, x)
            if best is None or squared < best:
                best, tied = squared, {point}
            elif squared == best:
                tied.add(point)
    if best is None:
        raise ArithmeticError("global boundary is empty")
    points = tuple(sorted(tied))
    return Distance2(best, points[0], points)
