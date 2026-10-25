"""Named exact truth gates; hand formulas and independent oracle agree.

Oracle primitives: test-only rational complex rotation, interpolation,
Sturm isolation and G0 overlap, none of production SE(2)'s symbolic roots.
The doorway geometry is independently hand-eroded support-line data.
"""
from fractions import Fraction as F
from random import Random

import pytest

from eab.kernel2d.erosion import erode_polygon_exact
from eab.kernel2d.se2 import SE2Motion
from eab.kernel2d.se2_paths import se2_first_penetration, se2_first_penetration_many
from eab.kernel2d.translation_certificates import translation_segment_is_free
from t2a_independent_oracle import first_penetration, ring_at, time_matches
from t2a_truth_geometry import (
    IDENTITY, diamond_plates, doorway, doorway_motion_specs, midpoint_wedges,
    rectangle, windmill,
)


@pytest.mark.parametrize("geometry,u,status,time,touches", (
    (windmill, F(1, 2), "FREE", None, True),
    (windmill, F(1), "PENETRATES", F(1, 2), True),
    (windmill, F(-1, 2), "PENETRATES", F(0), False),
    (midpoint_wedges, F(1, 2), "PENETRATES", F(0), False),
    (midpoint_wedges, F(-1, 2), "PENETRATES", F(0), False),
    (diamond_plates, F(1), "FREE", None, True),
    (diamond_plates, F(-1), "FREE", None, True),
))
def test_hand_truth_and_independent_oracle(geometry, u, status, time, touches):
    moving, obstacles = geometry()
    spec = (u, IDENTITY[1], IDENTITY[2])
    got = se2_first_penetration_many(moving, obstacles, SE2Motion(*spec))
    assert got.status == status, "hand-derived contact-allowed truth status"
    assert got.exact_time == time, "hand-derived tau is interval left endpoint, not probe"
    assert got.touches_end == touches, "closed final contact is not discarded"
    assert got.immediate == (time == 0)
    if status == "PENETRATES":
        assert got.obstacle_indices == (0, 1, 2, 3), "all four exact obstacle ties"
    for index, obstacle in enumerate(obstacles):
        actual = se2_first_penetration(moving, obstacle, SE2Motion(*spec))
        independent = first_penetration(moving, obstacle, spec)
        assert actual.status == independent["status"] == status
        assert actual.exact_time == time
        assert actual.touches_end == independent["touches_end"] == touches
        assert set(actual.incidences) == independent["incidences"]
        assert set(actual.features) == independent["features"]
        if time is not None:
            assert time_matches(actual.exact_time.certificate, independent["root"])
            first_probe = next(s for s, state in independent["probes"] if state == 1)
            assert time < first_probe, "positive interval probe must never replace its left boundary"


@pytest.mark.parametrize("delta,accepted", (
    (F(1, 8), True), (F(1, 8)+F(1, 1024), True),
    (F(1, 8)-F(1, 1024), False),
))
def test_doorway_octagon_closed_form_and_segment_oracle(delta, accepted):
    moving, obstacles = doorway(delta)
    uncut = rectangle(F(-3, 2), 0, F(3, 2), 1)
    eroded = erode_polygon_exact(uncut, delta, "octagon")
    assert eroded.status == "ACCEPTED" and eroded.polygon == moving
    strict_failures = []
    contacts = []
    for segment, spec in enumerate(doorway_motion_specs()):
        for obstacle_index, obstacle in enumerate(obstacles):
            actual = se2_first_penetration(moving, obstacle, SE2Motion(*spec))
            expected = first_penetration(moving, obstacle, spec)
            assert actual.status == expected["status"]
            assert actual.touches_end == expected["touches_end"]
            if expected["root"] is not None:
                assert time_matches(actual.exact_time.certificate, expected["root"])
            if actual.status != "FREE":
                strict_failures.append((segment, obstacle_index))
            if expected["contact_status"] == "contact":
                contacts.append((segment, obstacle_index))
        moving = ring_at(moving, spec, F(1))
    assert (not strict_failures) == accepted, "door width threshold is exactly delta=1/8"
    if delta == F(1, 8):
        assert contacts == [(2, 3), (2, 4)], "threshold passes with persistent two-sided contact"
    if not accepted:
        assert strict_failures == [(2, 3), (2, 4)], "under-width forged pass intersects both jambs"


def test_random_rational_pure_translation_matches_existing_segment_verifier():
    """Independent verifier uses triangulation plus affine SAT intervals."""
    rng = Random(2026102501)
    seen = set()
    for index in range(64):
        width, height = F(rng.randrange(1, 7), 3), F(rng.randrange(1, 7), 4)
        moving = rectangle(0, 0, width, height)
        obstacle = rectangle(F(rng.randrange(-9, 10), 3), F(rng.randrange(-9, 10), 4),
                             F(15, 3), F(15, 4))
        start = (F(rng.randrange(-9, 10), 5), F(rng.randrange(-9, 10), 7))
        end = (F(rng.randrange(-9, 10), 3), F(rng.randrange(-9, 10), 4))
        if index % 8 == 0:
            # Deliberate initial edge contact, with both separating and
            # penetrating directions represented by the seeded end point.
            obstacle = rectangle(width, 0, width+1, height)
            start = (F(0), F(0))
        placed = tuple((x+start[0], y+start[1]) for x, y in moving)
        displacement = tuple(end[k]-start[k] for k in (0, 1))
        actual = se2_first_penetration(placed, obstacle, SE2Motion(0, displacement))
        expected = translation_segment_is_free(moving, (obstacle,), start, end)
        assert (actual.status == "FREE") == expected, "translation degeneration agrees on whole interval"
        seen.add(actual.status)
    assert seen == {"FREE", "PENETRATES", "INITIAL_OVERLAP"}
