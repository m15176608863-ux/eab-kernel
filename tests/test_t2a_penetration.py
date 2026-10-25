"""Exact closed-form and event-partition gates for contact-allowed paths.

The primary expectations use translated interval interiors and the explicit
square support equation, not a production collision query. Partition gates
also inspect the mathematical candidate set: an extra supporting-line root
would not necessarily change the final overlap infimum, but is not a legal
closed-segment event. Broad randomized independent checks are in the oracle
test module; this file deliberately stays small enough for the fast tier.
"""
from fractions import Fraction as F

import pytest

from eab.kernel2d.algebraic import RealAlgebraic, roots_interval
from eab.kernel2d.motion import QuadraticTime
from eab.kernel2d.se2 import SE2Motion, _line_polynomials, _validated_ring
from eab.kernel2d.se2_paths import (
    _event_partition, _rational_between, se2_first_penetration,
    se2_first_penetration_many,
)


SQUARE = ((0, 0), (1, 0), (1, 1), (0, 1))


def test_new_path_results_never_request_binary64_display(monkeypatch):
    def forbidden_display(self):
        raise AssertionError("path certificates must not request rounded time displays")

    monkeypatch.setattr(QuadraticTime, "time", property(forbidden_display))
    monkeypatch.setattr(RealAlgebraic, "time", property(forbidden_display))
    rational = se2_first_penetration(SQUARE, shifted(SQUARE, 2), SE2Motion(0, (4, 0)))
    square = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    wall = ((F(6, 5), -3), (3, -3), (3, 3), (F(6, 5), 3))
    algebraic = se2_first_penetration(square, wall, SE2Motion(1))
    assert rational.exact_time == F(1, 4)
    assert isinstance(algebraic.exact_time, RealAlgebraic)
    assert not hasattr(type(rational), "time") and not hasattr(type(algebraic), "time")


def shifted(polygon, x, y=0):
    return tuple((F(a)+x, F(b)+y) for a, b in polygon)


@pytest.mark.parametrize("obstacle_x,displacement,end_state,touches", [
    (1, -1, -1, False),
    (1, 0, 0, True),
    (2, 1, 0, True),
    (2, 0, -1, False),
])
def test_contact_departure_and_endpoint(obstacle_x, displacement, end_state, touches):
    got = se2_first_penetration(SQUARE, shifted(SQUARE, obstacle_x),
                                SE2Motion(0, (displacement, 0)))
    assert got.status == "FREE", "contact is allowed, including at the final endpoint"
    assert got.exact_time is None and not got.immediate
    assert got.incidences == got.features == ()
    assert got.end_state == end_state and got.touches_end is touches


def test_initial_contact_can_penetrate_immediately():
    got = se2_first_penetration(SQUARE, shifted(SQUARE, 1), SE2Motion(0, (1, 0)))
    assert got.initial_state == 0 and got.status == "PENETRATES"
    assert got.exact_time == 0 and isinstance(got.exact_time, QuadraticTime)
    assert got.immediate and got.end_state == 1 and not got.touches_end
    assert ("VE", 1, 3) in got.incidences and ("VV", 1, 0) in got.features


def test_initial_overlap_has_zero_infimum_and_still_checks_endpoint():
    got = se2_first_penetration(SQUARE, SQUARE, SE2Motion(0, (1, 0)))
    assert got.initial_state == 1 and got.status == "INITIAL_OVERLAP"
    assert got.exact_time == 0 and got.immediate
    assert got.touches_end and got.end_state == 0
    assert len([label for label in got.incidences if label[0] == "VV"]) == 4


def test_internal_overlap_with_free_endpoints():
    got = se2_first_penetration(SQUARE, shifted(SQUARE, 2), SE2Motion(0, (4, 0)))
    assert got.initial_state == got.end_state == -1
    assert got.status == "PENETRATES" and got.exact_time == F(1, 4), \
        "return interval left boundary, never the interior overlap probe"
    assert not got.immediate and not got.touches_end
    assert ("VE", 1, 3) in got.incidences


def test_irrational_infimum():
    square = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    wall = ((F(6, 5), -3), (3, -3), (3, 3), (F(6, 5), 3))
    got = se2_first_penetration(square, wall, SE2Motion(1))
    # max x = (1+2s-s*s)/(1+s*s); first equality to 6/5.
    assert got.status == "PENETRATES" and isinstance(got.exact_time, RealAlgebraic)
    assert got.exact_time.sign_polynomial(1, -10, 11) == 0
    assert F(1, 10) < got.exact_time < F(1, 8)
    assert got.incidences == got.features == (("VE", 1, 3),)
    assert got.end_state == -1 and not got.touches_end


def test_partition_excludes_supporting_line_only_events():
    a = _validated_ring(shifted(SQUARE, -1, 3), SE2Motion(0, (3, 0)))
    b = _validated_ring(shifted(SQUARE, 0), SE2Motion())
    events = tuple((p, q, tag, i, j, _line_polynomials(p, i, q, j))
                   for p, q, tag in ((a, b, "VE"), (b, a, "EV"))
                   for i in range(len(p.start)) for j in range(len(q.start)))
    assert roots_interval(events[1][-1][0]), "there really is a supporting-line root"
    assert _event_partition(events) == (0, 1), "only closed-segment events may partition the path"


def test_persistent_collinearity_uses_projection_endpoints():
    a = _validated_ring(shifted(SQUARE, 0), SE2Motion(0, (4, 0)))
    b = _validated_ring(shifted(SQUARE, 2, 1), SE2Motion())
    polynomials = _line_polynomials(a, 2, b, 0)
    assert not any(polynomials[0])
    events = ((a, b, "VE", 2, 0, polynomials),)
    assert _event_partition(events) == (0, F(1, 4), F(1, 2), 1)
    got = se2_first_penetration(a.start, b.start, a.motion)
    assert got.status == "FREE", "sustained collinear sliding contact is allowed"


def test_rational_probe_is_strictly_between_nearby_algebraic_roots():
    left = roots_interval((-F(1, 2), 0, 1))[0]
    right = roots_interval((-F(1, 2)-F(1, 10**20), 0, 1))[0]
    probe = _rational_between(left, right)
    assert isinstance(probe, F) and left < probe < right
    with pytest.raises(ValueError, match="strictly increasing"):
        _rational_between(left, left)


def test_many_preserves_all_earliest_obstacles():
    obstacles = (shifted(SQUARE, 2), shifted(SQUARE, 2), shifted(SQUARE, 3))
    got = se2_first_penetration_many(SQUARE, obstacles, SE2Motion(0, (4, 0)))
    assert got.status == "PENETRATES" and got.exact_time == F(1, 4)
    assert got.obstacle_indices == (0, 1)
    assert {index for index, _ in got.incidences} == {0, 1}
    assert got.results[2].exact_time == F(1, 2)
    assert got.touches_end
    empty = se2_first_penetration_many(SQUARE, ())
    assert empty.status == "FREE" and empty.results == ()
    assert empty.obstacle_indices == () and empty.exact_time is None


def test_many_mixed_rational_and_irrational_times():
    square = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    walls = tuple(((x, -3), (3, -3), (3, 3), (x, 3)) for x in (F(6, 5), F(7, 5)))
    got = se2_first_penetration_many(square, walls, SE2Motion(1))
    assert got.obstacle_indices == (0,)
    assert isinstance(got.exact_time, RealAlgebraic)
    assert got.results[1].exact_time == F(1, 3)


@pytest.mark.parametrize("bad", [0.0, True, "0"])
def test_nonrational_input_is_rejected(bad):
    polygon = ((bad, 0),) + SQUARE[1:]
    with pytest.raises(ValueError, match="exact"):
        se2_first_penetration(polygon, shifted(SQUARE, 2))


def test_motion_domain_and_obstacle_count_are_checked():
    with pytest.raises(ValueError, match="explicit"):
        se2_first_penetration(SQUARE, shifted(SQUARE, 2), (0, (1, 0), (0, 0)))
    restored = SE2Motion()
    object.__setattr__(restored, "u1", F(2))
    with pytest.raises(ValueError, match="90 degrees"):
        se2_first_penetration(SQUARE, shifted(SQUARE, 2), restored)
    with pytest.raises(ValueError, match="count"):
        se2_first_penetration_many(SQUARE, (SQUARE,), motions_b=())
