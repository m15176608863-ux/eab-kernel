"""Exact first contact of two simple rings with affine vertex trajectories.

The support domain is a single simple nondegenerate ring at *every* s in
[0, 1], not just the two snapshots. All event and domain predicates are
rational polynomials evaluated at exact degree-two algebraic numbers.
The proof and the distinction between incidence and a normal-cone-valid cover
are in docs/m4c_motion_entrance_design.md. The independent closed-form and G0
gates are in tests/test_m4c_motion.py; no oracle primitive is imported here.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache
from math import isqrt

from ..construction import normalized_difference_rational, scalar_rational
from .exact import polygons_overlap_exact
from .global_entrance import _ring


def _sgn(x):
    return (x > 0) - (x < 0)


def _radical_sign(u, v, d):
    if not v:
        return _sgn(u)
    if not u or _sgn(u) == _sgn(v):
        return _sgn(v)
    return _sgn(u) * _sgn(u*u-v*v*d)


@dataclass(frozen=True, eq=False)
class QuadraticTime:
    """A rational, or one specified root of irreducible t*t+b*t+c.

    Exact equality uses its unique monic minimal polynomial and root branch.
    Constructor fields must be exact integers/Fractions (not bool). Comparison
    follows Python numeric equality for int/Fraction/finite float, including
    bool as an integer; float operands are compared at their exact binary value.
    Strings and other parseable objects are not numbers in this protocol.
    Ordering isolates distinct roots by rational bisection; no tolerance or
    floating root enters a decision. Gate: test_quadratic_numbers_are_exact.
    """
    rational: F | None = None
    b: F = F(0)
    c: F = F(0)
    branch: int = 0

    def __post_init__(self):
        if type(self.branch) is not int:
            raise ValueError("quadratic branch must be an integer, not bool or float")
        if (not isinstance(self.b, (int, F)) or isinstance(self.b, bool)
                or not isinstance(self.c, (int, F)) or isinstance(self.c, bool)):
            raise ValueError("quadratic coefficients must be integers or Fractions")
        if self.rational is not None:
            if not isinstance(self.rational, (int, F)) or isinstance(self.rational, bool):
                raise ValueError("rational time must be an integer or Fraction")
            if self.b or self.c or self.branch:
                raise ValueError("rational time cannot carry a quadratic branch")
        else:
            d = self.b*self.b-4*self.c
            if self.branch not in (-1, 1) or d <= 0 or _rational_sqrt(d) is not None:
                raise ValueError("quadratic time requires an irreducible real root and branch")

    def sign_polynomial(self, c0, c1=0, c2=0):
        """Exact sign of c0+c1*t+c2*t*t; output is a discrete predicate."""
        c0, c1, c2 = F(c0), F(c1), F(c2)
        if self.rational is not None:
            return _sgn(c0+self.rational*(c1+self.rational*c2))
        u, v = c0-c2*self.c, c1-c2*self.b
        return _radical_sign(u-v*self.b/2, v*self.branch/2, self.b*self.b-4*self.c)

    def __eq__(self, other):
        if not isinstance(other, QuadraticTime):
            if not isinstance(other, (int, F, float)):
                return False
            try:
                other = QuadraticTime(F(other))
            except (TypeError, ValueError, OverflowError):
                return False
        return (self.rational, self.b, self.c, self.branch) == (
            other.rational, other.b, other.c, other.branch)

    def __hash__(self):
        if self.rational is not None:
            return hash(self.rational)
        return hash((self.b, self.c, self.branch))

    def __lt__(self, other):
        if not isinstance(other, QuadraticTime):
            if not isinstance(other, (int, F, float)):
                raise TypeError("quadratic time ordering requires a supported finite number")
            try:
                other = QuadraticTime(F(other))
            except (ValueError, OverflowError):
                raise TypeError("quadratic time ordering requires a supported finite number") from None
        if self == other:
            return False
        if other.rational is not None:
            return self.sign_polynomial(-other.rational, 1) < 0
        if self.rational is not None:
            return other.sign_polynomial(-self.rational, 1) > 0
        if (self.b, self.c) == (other.b, other.c):
            return self.branch < other.branch
        bound = F(2)+abs(self.b)+abs(self.c)+abs(other.b)+abs(other.c)
        lo, hi = -bound, bound
        while True:
            middle = (lo+hi)/2
            a = self.sign_polynomial(-middle, 1)
            b = other.sign_polynomial(-middle, 1)
            if a != b:
                return a < b
            if a < 0:
                hi = middle
            else:
                lo = middle

    def __le__(self, other):
        return self == other or self < other

    def __gt__(self, other):
        return not self <= other

    def __ge__(self, other):
        return not self < other

    @property
    def time(self):
        """Single correctly rounded binary64 display, only via construction."""
        if self.rational is not None:
            return scalar_rational(self.rational, allow_underflow=True)
        d = F(self.b)*self.b-4*self.c
        return normalized_difference_rational(self.branch*d/2, d, F(self.b)/2,
                                              allow_underflow=True)

    @property
    def certificate(self):
        """Lossless strings, not a new quantitative binary64 construction."""
        return {"rational": None if self.rational is None else str(self.rational),
                "polynomial": [str(self.c), str(self.b), "1"] if self.rational is None else None,
                "branch": self.branch}


def _rational_sqrt(x):
    n, d = isqrt(x.numerator), isqrt(x.denominator)
    return F(n, d) if n*n == x.numerator and d*d == x.denominator else None


def _roots(poly):
    c, b, a = F(poly[0]), F(poly[1]), F(poly[2])
    if not a:
        return (QuadraticTime(-c/b),) if b else ()
    b, c = b/a, c/a
    discriminant = b*b-4*c
    if discriminant < 0:
        return ()
    square = _rational_sqrt(discriminant)
    if square is not None:
        return tuple(sorted({QuadraticTime((-b-square)/2), QuadraticTime((-b+square)/2)}))
    return (QuadraticTime(None, b, c, -1), QuadraticTime(None, b, c, 1))


def _sub(a, b):
    return (a[0]-b[0], a[1]-b[1])


def _cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def _dot(a, b):
    return a[0]*b[0]+a[1]*b[1]


def _vector(p, q):
    return _sub(p[0], q[0]), _sub(p[1], q[1])


def _cross_poly(u, v):
    return _cross(u[0], v[0]), _cross(u[0], v[1])+_cross(u[1], v[0]), _cross(u[1], v[1])


def _dot_poly(u, v):
    return _dot(u[0], v[0]), _dot(u[0], v[1])+_dot(u[1], v[0]), _dot(u[1], v[1])


def _line_polynomials(p, a, b):
    e, v, w = _vector(b, a), _vector(p, a), _vector(p, b)
    return _cross_poly(e, v), _dot_poly(v, w)


def _contains(time, orient, between):
    return time.sign_polynomial(*orient) == 0 and time.sign_polynomial(*between) <= 0


def _event_times(p, a, b):
    orient, between = _line_polynomials(p, a, b)
    # Persistent collinearity changes closed-segment membership only at a
    # zero of the between-polynomial. Include both window endpoints.
    candidates = _roots(orient if any(orient) else between)
    if not any(orient):
        candidates += (QuadraticTime(F(0)), QuadraticTime(F(1)))
    return tuple(t for t in candidates if 0 <= t <= 1 and _contains(t, orient, between))


def _point(p):
    try:
        if len(p) != 2:
            raise ValueError("motion points must have two coordinates")
        return F(p[0]), F(p[1])
    except (TypeError, ValueError, OverflowError, ZeroDivisionError):
        raise ValueError("motion coordinate is nonfinite, nonrational or not a 2D point") from None


@dataclass(frozen=True)
class _MotionRing:
    start: tuple
    end: tuple
    paths: tuple
    vertex_ids: tuple
    edge_ids: tuple


@lru_cache(maxsize=512)
def _validated_motion(start, end):
    if len(start) != len(end):
        raise ValueError("motion topology mismatch: vertex counts differ")
    normalized = _ring(start)
    _ring(end)
    n = len(start)
    paths = tuple((a, _sub(b, a)) for a, b in zip(start, end))
    for j in range(n):
        edge = _vector(paths[(j+1) % n], paths[j])
        squared = _dot_poly(edge, edge)
        if any(0 <= t <= 1 for t in _roots(squared)):
            raise ValueError("motion has a zero-length edge within the step")
    # Starting rings are valid. The first loss of simplicity, including
    # adjacent backtracking, contains a nonincident vertex-edge incidence.
    for i, p in enumerate(paths):
        for j in range(n):
            if i not in (j, (j+1) % n) and _event_times(p, paths[j], paths[(j+1) % n]):
                raise ValueError("motion is self-intersecting or backtracking within the step")
    if normalized == start:
        indices = tuple(range(n))
        edges = indices
    else:
        indices = tuple(reversed(range(n)))
        edges = tuple((i-1) % n for i in indices)
    return _MotionRing(tuple(start[i] for i in indices), tuple(end[i] for i in indices),
                       tuple(paths[i] for i in indices), indices, edges)


def _cone(time, paths, vertex, other_edge):
    previous = _vector(paths[vertex], paths[vertex-1])
    following = _vector(paths[(vertex+1) % len(paths)], paths[vertex])
    turn = time.sign_polynomial(*_cross_poly(previous, following))
    if turn < 0 or (turn == 0 and time.sign_polynomial(*_dot_poly(previous, following)) <= 0):
        return False
    c1 = time.sign_polynomial(*_cross_poly(other_edge, previous))
    c2 = time.sign_polynomial(*_cross_poly(following, other_edge))
    if c1 < 0 or c2 < 0:
        return False
    return turn != 0 or time.sign_polynomial(*_dot_poly(other_edge, previous)) < 0


def _feature_sets(time, a, b):
    incidences = set()
    covers = set()
    for p, q, tag in ((a, b, "VE"), (b, a, "EV")):
        for i, vertex in enumerate(p.paths):
            for j, edge_start in enumerate(q.paths):
                edge_end = q.paths[(j+1) % len(q.paths)]
                if not _contains(time, *_line_polynomials(vertex, edge_start, edge_end)):
                    continue
                label = ((tag, p.vertex_ids[i], q.edge_ids[j]) if tag == "VE" else
                         (tag, q.edge_ids[j], p.vertex_ids[i]))
                incidences.add(label)
                if _cone(time, p.paths, i, _vector(edge_end, edge_start)):
                    covers |= {label}
    for i, p in enumerate(a.paths):
        for j, q in enumerate(b.paths):
            base, slope = _vector(p, q)
            if all(time.sign_polynomial(base[k], slope[k]) == 0 for k in (0, 1)):
                label = ("VV", a.vertex_ids[i], b.vertex_ids[j])
                incidences.add(label)
                covers.add(label)
    return tuple(sorted(incidences)), tuple(sorted(covers))


@dataclass(frozen=True)
class MotionEntrance2:
    initial_state: int
    status: str
    exact_time: QuadraticTime | None
    incidences: tuple
    features: tuple

    @property
    def time(self):
        return None if self.exact_time is None else self.exact_time.time


def motion_first_entrance(A0, B0, A1, B1):
    """Return all first-contact covers/incidences in the closed unit window.

    Input vertex correspondence is positional, and output labels use input
    indices, including clockwise rings. Initially overlapping bodies return
    initial_overlap with no invented first-contact time. Initial touching
    returns contact at exactly zero. Stationary separation is no_contact.
    There is no special translation branch. Named gates are
    test_translation_is_exactly_m3_with_complete_features,
    test_motion_matches_independent_closed_form_and_integer_oracle, and
    test_invalid_motion_is_rejected_between_valid_snapshots.
    """
    a = _validated_motion(tuple(_point(p) for p in A0), tuple(_point(p) for p in A1))
    b = _validated_motion(tuple(_point(p) for p in B0), tuple(_point(p) for p in B1))
    # Exact swept boxes are a proof of no contact, not a tolerance rejection.
    if any(max(p[k] for p in a.start+a.end) < min(p[k] for p in b.start+b.end)
           or max(p[k] for p in b.start+b.end) < min(p[k] for p in a.start+a.end)
           for k in (0, 1)):
        return MotionEntrance2(-1, "no_contact", None, (), ())
    state = polygons_overlap_exact(a.start, b.start)
    if state == 1:
        return MotionEntrance2(1, "initial_overlap", None, (), ())
    if state == 0:
        time = QuadraticTime(F(0))
    else:
        times = []
        for p, q in ((a, b), (b, a)):
            for vertex in p.paths:
                for j, edge_start in enumerate(q.paths):
                    times.extend(_event_times(vertex, edge_start, q.paths[(j+1) % len(q.paths)]))
        if not times:
            return MotionEntrance2(-1, "no_contact", None, (), ())
        time = min(times)
    incidences, features = _feature_sets(time, a, b)
    return MotionEntrance2(state, "contact", time, incidences, features)
