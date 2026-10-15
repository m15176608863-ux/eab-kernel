"""Exact first contact along explicitly chosen rational SE(2) paths.

Definitions and degree-five completeness proof: docs/m5a_se2_design.md.
Gates: test_m5a_se2.py (closed forms, translation degeneration, covariance),
test_m5a_oracle.py (independent rational event and solid-state oracle).
No claim is made about the unknown physical path between snapshot endpoints.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction as F
from functools import cached_property, lru_cache

from .algebraic import RealAlgebraic, p_add, p_sub, p_mul, p_scale, roots_interval
from .exact import polygons_overlap_exact
from .global_entrance import GlobalEntrance2, _ring
from .motion import QuadraticTime
from .motion_exit import shortest_exit_fast


def _point(p):
    try:
        if len(p) != 2:
            raise ValueError("SE(2) requires two-dimensional points")
        return F(p[0]), F(p[1])
    except (TypeError, ValueError, OverflowError, ZeroDivisionError):
        raise ValueError("SE(2) requires finite rational two-dimensional coordinates") from None


def _parameter(value):
    if not isinstance(value, (int, F)) or isinstance(value, bool):
        raise ValueError("SE(2) parameters must be exact integers or Fractions")
    return F(value)


def _sub(a, b):
    return a[0]-b[0], a[1]-b[1]


def _cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def _dot(a, b):
    return a[0]*b[0]+a[1]*b[1]


def rotate_rational(point, u):
    """Rational half-angle rotation; test_rotation_is_rigid_and_endpoints_close."""
    x, y = _point(point)
    u = _parameter(u)
    d = 1+u*u
    return ((1-u*u)*x-2*u*y)/d, (2*u*x+(1-u*u)*y)/d


@dataclass(frozen=True)
class SE2Motion:
    """X(s,x)=center+s*translation+R(s*u1)*(x-center), |u1|<=1.

    Parameters specify a model, not a fit or an inferred physical velocity.
    Gate: test_rotation_is_rigid_and_endpoints_close.
    """
    u1: F = F(0)
    translation: tuple = (F(0), F(0))
    center: tuple = (F(0), F(0))

    def __post_init__(self):
        u = _parameter(self.u1)
        if abs(u) > 1:
            raise ValueError("SE(2) path supports |u1|<=1 (at most 90 degrees per body)")
        object.__setattr__(self, "u1", u)
        object.__setattr__(self, "translation", _point(self.translation))
        object.__setattr__(self, "center", _point(self.center))

    def at(self, point, s):
        s = _parameter(s)
        if not 0 <= s <= 1:
            raise ValueError("SE(2) time is outside the closed unit window")
        rotated = rotate_rational(_sub(_point(point), self.center), s*self.u1)
        return tuple(self.center[k]+s*self.translation[k]+rotated[k] for k in (0, 1))

    def endpoint(self, point):
        return self.at(point, F(1))


def se2_slice(A, B, u):
    """Fixed-angle E_theta, not a full C-space arrangement; test_fixed_slice_is_m3."""
    return GlobalEntrance2(tuple(rotate_rational(p, u) for p in A), B)


def _rotation_numerators(u, p):
    x, y = p
    return (x, -2*u*y, -u*u*x), (y, 2*u*x, -u*u*y)


def _pcross(a, b):
    return p_sub(p_mul(a[0], b[1]), p_mul(a[1], b[0]))


def _pdot(a, b):
    return p_add(p_mul(a[0], b[0]), p_mul(a[1], b[1]))


@dataclass(frozen=True)
class _RigidRing:
    start: tuple
    motion: SE2Motion
    local: tuple
    vectors: tuple
    edges: tuple
    denominator: tuple
    vertex_ids: tuple
    edge_ids: tuple


@lru_cache(maxsize=512)
def _validated_ring(start, motion):
    normalized = _ring(start)
    n = len(start)
    if normalized == start:
        indices, edge_ids = tuple(range(n)), tuple(range(n))
    else:
        indices = tuple(reversed(range(n)))
        edge_ids = tuple((i-1) % n for i in indices)
    local = tuple(_sub(p, motion.center) for p in normalized)
    vectors = tuple(_rotation_numerators(motion.u1, p) for p in local)
    edges = tuple(_rotation_numerators(motion.u1, _sub(local[(j+1) % n], p))
                  for j, p in enumerate(local))
    return _RigidRing(normalized, motion, local, vectors, edges,
                      (F(1), F(0), motion.u1**2), indices, edge_ids)


def _line_polynomials(a, i, b, j):
    """Numerators F,G,H over the same positive denominator D_A*D_B."""
    m, n = a.motion, b.motion
    relative_center = tuple((m.center[k]-n.center[k], m.translation[k]-n.translation[k])
                            for k in (0, 1))
    w = tuple(p_add(p_mul(relative_center[k], a.denominator), a.vectors[i][k]) for k in (0, 1))
    denominator = p_mul(a.denominator, b.denominator)
    edge = _sub(b.local[(j+1) % len(b.local)], b.local[j])
    f = p_sub(_pcross(b.edges[j], w), p_scale(denominator, _cross(edge, b.local[j])))
    g = p_sub(_pdot(b.edges[j], w), p_scale(denominator, _dot(edge, b.local[j])))
    h = p_sub(p_scale(denominator, _dot(edge, edge)), g)
    return f, g, h


def _contains(time, f, g, h):
    return (time.sign_polynomial(*f) == 0 and time.sign_polynomial(*g) >= 0
            and time.sign_polynomial(*h) >= 0)


def _event_times(f, g, h):
    if any(f):
        candidates = roots_interval(f)
    else:
        # Persistent collinearity is not an empty event family. Membership
        # changes only at projection endpoints, including a whole-window tie.
        candidates = (RealAlgebraic.from_rational(0), RealAlgebraic.from_rational(1))
        for polynomial in (g, h):
            if any(polynomial):
                candidates += roots_interval(polynomial)
    return tuple(t for t in candidates if _contains(t, f, g, h))


def _cone(time, ring, vertex, other_edge):
    previous = ring.edges[vertex-1]
    following = ring.edges[vertex]
    u = _sub(ring.local[vertex], ring.local[vertex-1])
    v = _sub(ring.local[(vertex+1) % len(ring.local)], ring.local[vertex])
    turn = _cross(u, v)
    if turn < 0 or (turn == 0 and _dot(u, v) <= 0):
        return False
    if time.sign_polynomial(*_pcross(other_edge, previous)) < 0:
        return False
    if time.sign_polynomial(*_pcross(following, other_edge)) < 0:
        return False
    return turn != 0 or time.sign_polynomial(*_pdot(other_edge, previous)) < 0


def _features(time, a, b, events):
    incidences, covers = set(), set()
    for p, q, tag, i, j, polynomials in events:
        if not _contains(time, *polynomials):
            continue
        label = ((tag, p.vertex_ids[i], q.edge_ids[j]) if tag == "VE" else
                 (tag, q.edge_ids[j], p.vertex_ids[i]))
        incidences.add(label)
        if _cone(time, p, i, q.edges[j]):
            covers.add(label)
        for k, projection in ((j, polynomials[1]), ((j+1) % len(q.start), polynomials[2])):
            if time.sign_polynomial(*projection) == 0:
                vv = (("VV", p.vertex_ids[i], q.vertex_ids[k]) if tag == "VE" else
                      ("VV", q.vertex_ids[k], p.vertex_ids[i]))
                incidences.add(vv)
                covers.add(vv)
    return tuple(sorted(incidences)), tuple(sorted(covers))


def _swept_bounds(ring):
    m = ring.motion
    radii = tuple(2*abs(m.u1)*(abs(x)+abs(y)) for x, y in ring.local)
    return tuple((min(p[k]+min(F(0), m.translation[k])-r for p, r in zip(ring.start, radii)),
                  max(p[k]+max(F(0), m.translation[k])+r for p, r in zip(ring.start, radii)))
                 for k in (0, 1))


@dataclass(frozen=True)
class SE2Entrance2:
    initial_state: int
    status: str
    exact_time: RealAlgebraic | QuadraticTime | None
    incidences: tuple
    features: tuple
    _initial_geometry: tuple = field(default=(), repr=False, compare=False)

    @property
    def time(self):
        return None if self.exact_time is None else self.exact_time.time

    @property
    def tied_features(self):
        return self.features

    @cached_property
    def pd_closed(self):
        """Lazy frozen initial PD_closed, not motion exit; test_initial_pd_is_frozen."""
        return shortest_exit_fast(*self._initial_geometry) if self.initial_state == 1 else None


def se2_first_entrance(A0, B0, motion_a=SE2Motion(), motion_b=SE2Motion()):
    """Closed-window first contact with all incidences and valid cover ties.

    No translation dispatch: u=0 traverses the same polynomial event path.
    Gate: test_zero_rotation_is_exactly_m3_and_m4c_all_fields.
    Inputs are single simple rings; material holes and rotations >90 degrees
    per step fail loudly. Frozen slices may have holes as in M3.
    """
    if not isinstance(motion_a, SE2Motion) or not isinstance(motion_b, SE2Motion):
        raise ValueError("SE(2) requires explicit SE2Motion parameters")
    original = tuple(_point(p) for p in A0), tuple(_point(p) for p in B0)
    a, b = _validated_ring(original[0], motion_a), _validated_ring(original[1], motion_b)
    bounds_a, bounds_b = _swept_bounds(a), _swept_bounds(b)
    if any(bounds_a[k][1] < bounds_b[k][0] or bounds_b[k][1] < bounds_a[k][0] for k in (0, 1)):
        return SE2Entrance2(-1, "no_contact", None, (), ())
    state = polygons_overlap_exact(a.start, b.start)
    if state == 1:
        return SE2Entrance2(1, "initial_overlap", None, (), (), original)
    events = tuple((p, q, tag, i, j, _line_polynomials(p, i, q, j))
                   for p, q, tag in ((a, b, "VE"), (b, a, "EV"))
                   for i in range(len(p.start)) for j in range(len(q.start)))
    if state == 0:
        time = RealAlgebraic.from_rational(0)
    else:
        time = None
        for *_, polynomials in events:
            for candidate in _event_times(*polynomials):
                if time is None or candidate < time:
                    time = candidate
        if time is None:
            return SE2Entrance2(-1, "no_contact", None, (), ())
    incidences, features = _features(time, a, b, events)
    # Preserve the existing exact rational time protocol without bypassing
    # the general event enumeration or its complete feature reconstruction.
    public_time = QuadraticTime(time.rational) if time.rational is not None else time
    return SE2Entrance2(state, "contact", public_time, incidences, features)
