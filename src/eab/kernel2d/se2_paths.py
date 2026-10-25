"""Contact-allowed, exact paths of two planar rigid polygonal bodies.

Unlike ``se2_first_entrance``, an initial contact is not a failure: the first
open interval with intersecting interiors determines the penetration infimum.
The event-completeness argument is recorded in reports/codex/T2a_report.md.
Gates: tests/test_t2a_penetration.py and tests/test_t2a_truth.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F

from .algebraic import RealAlgebraic
from .exact import polygons_overlap_exact
from .motion import QuadraticTime
from .se2 import SE2Motion, _event_times, _features, _line_polynomials, _parameter, _validated_ring
from .translation_certificates import verify_escape_certificate


# The motion record is frozen; fixed neighbors share the same exact identity.
_STATIONARY_MOTION = SE2Motion()


def _exact_point(point):
    try:
        coordinates = tuple(point)
    except TypeError:
        raise ValueError("path coordinates must be exact two-dimensional points") from None
    if len(coordinates) != 2 or any(
            not isinstance(x, (int, F)) or isinstance(x, bool) for x in coordinates):
        raise ValueError("path coordinates must be exact integers or Fractions")
    return tuple(F(x) for x in coordinates)


def _exact_ring(polygon):
    try:
        return tuple(_exact_point(point) for point in polygon)
    except TypeError:
        raise ValueError("a path body must be a simple rational polygon") from None


def _checked_motion(motion):
    if not isinstance(motion, SE2Motion):
        raise ValueError("a path requires explicit SE2Motion parameters")
    # Recheck the public support domain even for an object restored externally.
    # Normalize the scalar here as well as inside the frozen motion record: the
    # caller explicitly supplies exact input to every downstream polynomial.
    return SE2Motion(_parameter(motion.u1), _exact_point(motion.translation), _exact_point(motion.center))


def _event_partition(events):
    """Distinct legal closed-segment events, including the window endpoints.

    Persistent collinearity is handled by ``_event_times`` through projection
    endpoint roots. Supporting-line roots outside the closed segment are not
    cuts. Gate: test_partition_excludes_supporting_line_only_events.
    """
    candidates = [RealAlgebraic.from_rational(0), RealAlgebraic.from_rational(1)]
    for *_, polynomials in events:
        candidates.extend(_event_times(*polynomials))
    distinct = []
    for time in sorted(candidates):
        if not distinct or time != distinct[-1]:
            distinct.append(time)
    return tuple(distinct)


def _rational_between(left, right):
    """A certified interior rational probe, never an approximate root value."""
    if not left < right:
        raise ValueError("interval endpoints must be strictly increasing")
    while left.upper >= right.lower:
        left, right = left.refine(), right.refine()
    return (left.upper+right.lower)/2


def _public_time(time):
    rational = time.as_rational()
    return QuadraticTime(rational) if rational is not None else time


def _algebraic_time(time):
    return RealAlgebraic.from_rational(time.rational) if isinstance(time, QuadraticTime) else time


@dataclass(frozen=True)
class SE2Penetration2:
    """Exact infimum of strict overlap on a closed parameter window.

    ``FREE`` has no time. ``INITIAL_OVERLAP`` has time zero, distinguished
    from ``PENETRATES`` immediately after an allowed initial contact.
    ``touches_end`` means end_state == 0, not merely boundary incidences inside
    an already overlapping pair. Gate: test_contact_departure_and_endpoint.
    """
    initial_state: int
    status: str
    exact_time: RealAlgebraic | QuadraticTime | None
    immediate: bool
    incidences: tuple
    features: tuple
    touches_end: bool
    end_state: int

    @property
    def tied_features(self):
        return self.features


def se2_first_penetration(A0, B0, motion_a=_STATIONARY_MOTION, motion_b=_STATIONARY_MOTION):
    """First strict-overlap infimum; isolated or sustained contact is allowed.

    Enumerate all legal VE/EV events, including persistent collinearity, and
    classify a rational probe in every intervening open interval. Interior
    intersection is open under continuous rigid motion; its state can change
    only when a vertex meets a closed opposite edge. Hence the first occupied
    interval's *left boundary*, not its probe, is the requested infimum.
    The final endpoint is also classified explicitly. Inputs must be exact
    rational simple rings. Gates: test_internal_overlap_with_free_endpoints,
    test_initial_contact_can_penetrate_immediately, test_irrational_infimum.
    """
    motion_a, motion_b = _checked_motion(motion_a), _checked_motion(motion_b)
    original = _exact_ring(A0), _exact_ring(B0)
    a, b = _validated_ring(original[0], motion_a), _validated_ring(original[1], motion_b)
    initial_state = polygons_overlap_exact(a.start, b.start)
    final_a = tuple(motion_a.endpoint(p) for p in a.start)
    final_b = tuple(motion_b.endpoint(p) for p in b.start)
    end_state = polygons_overlap_exact(final_a, final_b)
    events = tuple((p, q, tag, i, j, _line_polynomials(p, i, q, j))
                   for p, q, tag in ((a, b, "VE"), (b, a, "EV"))
                   for i in range(len(p.start)) for j in range(len(q.start)))
    if initial_state == 1:
        time = RealAlgebraic.from_rational(0)
        incidences, features = _features(time, a, b, events)
        return SE2Penetration2(initial_state, "INITIAL_OVERLAP", _public_time(time),
                               True, incidences, features, end_state == 0, end_state)
    cuts = _event_partition(events)
    for left, right in zip(cuts, cuts[1:]):
        probe = _rational_between(left, right)
        at_a = tuple(motion_a.at(p, probe) for p in a.start)
        at_b = tuple(motion_b.at(p, probe) for p in b.start)
        if polygons_overlap_exact(at_a, at_b) == 1:
            incidences, features = _features(left, a, b, events)
            return SE2Penetration2(initial_state, "PENETRATES", _public_time(left),
                                   left == 0, incidences, features, end_state == 0, end_state)
    # Strict overlap at the endpoint would persist on a left neighborhood.
    if end_state == 1:
        raise ArithmeticError("event partition missed strict overlap at the final endpoint")
    return SE2Penetration2(initial_state, "FREE", None, False, (), (), end_state == 0, end_state)


@dataclass(frozen=True)
class SE2PenetrationMany:
    """Earliest penetration with all obstacle ties and complete pair results."""
    status: str
    exact_time: RealAlgebraic | QuadraticTime | None
    immediate: bool
    obstacle_indices: tuple
    incidences: tuple
    features: tuple
    touches_end: bool
    results: tuple


def se2_first_penetration_many(A0, obstacles, motion_a=_STATIONARY_MOTION, motions_b=None):
    """Minimum exact pair infimum, preserving every simultaneous obstacle.

    Neighbors are fixed unless an equal-length ``motions_b`` sequence is
    supplied. Per-pair states remain in ``results``; initial overlap takes
    precedence in the aggregate status, but ties with immediate penetration
    are still retained. Gate: test_many_preserves_all_earliest_obstacles.
    """
    motion_a = _checked_motion(motion_a)
    original = _exact_ring(A0)
    _validated_ring(original, motion_a)
    obstacles = tuple(obstacles)
    motions = tuple(_STATIONARY_MOTION for _ in obstacles) if motions_b is None else tuple(motions_b)
    if len(motions) != len(obstacles):
        raise ValueError("obstacle motion count must match the obstacle count")
    results = tuple(se2_first_penetration(original, obstacle, motion_a, motion)
                    for obstacle, motion in zip(obstacles, motions))
    occupied = tuple((index, result) for index, result in enumerate(results)
                     if result.status != "FREE")
    touches_end = any(result.touches_end for result in results)
    if not occupied:
        return SE2PenetrationMany("FREE", None, False, (), (), (), touches_end, results)
    first = min(_algebraic_time(result.exact_time) for _, result in occupied)
    tied = tuple((index, result) for index, result in occupied
                 if _algebraic_time(result.exact_time) == first)
    status = "INITIAL_OVERLAP" if any(result.status == "INITIAL_OVERLAP" for _, result in tied) else "PENETRATES"
    return SE2PenetrationMany(
        status, _public_time(first), first == 0, tuple(index for index, _ in tied),
        tuple((index, label) for index, result in tied for label in result.incidences),
        tuple((index, label) for index, result in tied for label in result.features),
        touches_end, results)


@dataclass(frozen=True)
class SE2EscapePath:
    """Explicit ordered vertex poses and the motions joining them.

    The verifier checks every coordinate, not fitted transformations or a
    tolerance. Poses retain the input vertex numbering. Gate:
    test_escape_rejects_discontinuous_or_snapped_poses.
    """
    poses: tuple
    motions: tuple

    def __post_init__(self):
        object.__setattr__(self, "poses", tuple(_exact_ring(p) for p in self.poses))
        object.__setattr__(self, "motions", tuple(_checked_motion(m) for m in self.motions))
        if not self.poses or len(self.poses) != len(self.motions)+1:
            raise ValueError("a path needs one more pose than motions")

    @classmethod
    def from_waypoints(cls, moving, waypoints, center=(0, 0)):
        """Build poses from absolute Cayley parameters and reference positions.

        A waypoint is ``(u_absolute, reference_position)`` with pose
        ``reference_position + R(u_absolute)*(moving-center)``. Each relative
        parameter is exactly (u_b-u_a)/(1+u_a*u_b); antipodal or >90 degree
        steps are rejected, never wrapped. The verifier still checks the
        original pose: a displaced first waypoint does not certify an escape.
        Gate: test_waypoint_relative_cayley_parameters_close_exactly.
        """
        from .se2 import rotate_rational
        moving, center = _exact_ring(moving), _exact_point(center)
        waypoints = tuple((_parameter(u), _exact_point(p)) for u, p in waypoints)
        poses = tuple(tuple(tuple(p[k]+rotated[k] for k in (0, 1))
                            for rotated in (rotate_rational(
                                (v[0]-center[0], v[1]-center[1]), u) for v in moving))
                      for u, p in waypoints)
        motions = []
        for (ua, a), (ub, b) in zip(waypoints, waypoints[1:]):
            denominator = 1+ua*ub
            if denominator == 0:
                raise ValueError("waypoint rotation requires a smaller chart step")
            motions.append(SE2Motion((ub-ua)/denominator,
                                     (b[0]-a[0], b[1]-a[1]), a))
        return cls(poses, tuple(motions))


@dataclass(frozen=True)
class SE2EscapeVerification:
    """Exact path decision, pair results and the existing infinite-ray proof."""
    valid: bool
    reason: str
    checked_segments: int = 0
    checked_pairs: int = 0
    segment_results: tuple = ()
    ray_verification: object = None


def verify_se2_escape(moving, obstacles, path, ray):
    """Verify original pose, exact continuity, every segment and an infinite ray.

    ``ray`` is a rational translation polyline relative to the final rigid
    pose, beginning at (0,0). The existing ``verify_escape_certificate``
    certifies all its finite segments and returns an outward infinite axis
    direction. It is not enough for the rigid path to end above a bounding
    box or at a visually separated pose. Gate: tests/test_t2a_escape.py.
    """
    try:
        moving = _exact_ring(moving)
        obstacles = tuple(_exact_ring(p) for p in obstacles)
        _validated_ring(moving, _STATIONARY_MOTION)
        for obstacle in obstacles:
            _validated_ring(obstacle, _STATIONARY_MOTION)
        if not isinstance(path, SE2EscapePath):
            raise ValueError("escape requires an explicit SE2EscapePath")
        # Revalidate serialized or externally restored instances.
        path = SE2EscapePath(path.poses, path.motions)
        ray = tuple(_exact_point(p) for p in ray)
    except (TypeError, ValueError, ArithmeticError) as error:
        return SE2EscapeVerification(False, str(error))
    if path.poses[0] != moving:
        return SE2EscapeVerification(False, "escape path does not start at the exact input pose")
    for start, end, motion in zip(path.poses, path.poses[1:], path.motions):
        expected = tuple(motion.endpoint(p) for p in start)
        if expected != end:
            return SE2EscapeVerification(False, "consecutive poses are not exactly joined by the motion")
    results, pairs = [], 0
    for index, (start, motion) in enumerate(zip(path.poses, path.motions)):
        row = tuple(se2_first_penetration(start, obstacle, motion) for obstacle in obstacles)
        results.append(row)
        pairs += len(row)
        if any(result.status != "FREE" for result in row):
            return SE2EscapeVerification(False, "a rigid path segment enters strict overlap",
                                          index+1, pairs, tuple(results))
    tail = verify_escape_certificate(path.poses[-1], obstacles, ray)
    if not tail.valid:
        return SE2EscapeVerification(False, "infinite ray certificate rejected: "+tail.reason,
                                      len(path.motions), pairs, tuple(results), tail)
    return SE2EscapeVerification(True, "exact original path and certified infinite ray",
                                  len(path.motions), pairs, tuple(results), tail)
