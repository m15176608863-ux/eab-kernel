"""Exact escape gates with analytic rectangles and independent interval oracle.

The oracle independently interpolates event polynomials and applies its own
Sturm/G0 machinery. Source mutants alter verifier branches before executing
the same semantic assertion, never patch a returned answer.
"""
from fractions import Fraction as F
import inspect

import pytest

from eab.kernel2d import se2_paths as paths
from eab.kernel2d.se2 import SE2Motion, se2_first_entrance
from eab.kernel2d.erosion import erode_polygon_exact, octagon_element
from t2a_truth_geometry import doorway, doorway_motion_specs, rectangle
from t2a_independent_oracle import first_penetration, IDENTITY


def path_from_motions(moving, motions):
    poses = [moving]
    for motion in motions:
        poses.append(tuple(motion.endpoint(p) for p in poses[-1]))
    return paths.SE2EscapePath(tuple(poses), tuple(motions))


def test_waypoint_relative_cayley_parameters_close_exactly():
    moving = rectangle(-1, -F(1, 3), 2, F(2, 3))
    center = (F(1, 2), F(1, 6))
    waypoints = ((F(0), center), (F(1, 3), (F(3, 2), F(7, 6))),
                 (F(3, 4), (F(5, 2), F(7, 6))))
    path = paths.SE2EscapePath.from_waypoints(moving, waypoints, center)
    assert path.poses[0] == moving
    assert path.motions[1].u1 == F(1, 3)
    for a, b, motion in zip(path.poses, path.poses[1:], path.motions):
        assert tuple(motion.endpoint(p) for p in a) == b
    assert paths.verify_se2_escape(moving, (), path, ((0, 0), (100, 0))).valid
    with pytest.raises(ValueError, match="smaller chart"):
        paths.SE2EscapePath.from_waypoints(moving, ((1, center), (-1, center)), center)


@pytest.mark.parametrize("delta,valid", [(F(1, 8), True), (F(129, 1024), True), (F(127, 1024), False)])
def test_doorway_contact_allowed_escape_and_false_crossing(delta, valid):
    moving, obstacles = doorway(delta)
    # Independent support-line result agrees with the required body-frame erosion.
    raw = rectangle(F(-3, 2), 0, F(3, 2), 1)
    eroded = erode_polygon_exact(raw, delta, octagon_element())
    assert eroded.status == "ACCEPTED" and eroded.polygon == moving
    motions = tuple(SE2Motion(*spec) for spec in doorway_motion_specs())
    path = path_from_motions(moving, motions)
    result = paths.verify_se2_escape(moving, obstacles, path, ((0, 0), (0, 100)))
    assert result.valid is valid, "doorway boundary must allow contact but reject strict penetration"
    assert result.checked_segments == 3
    for pose, motion in zip(path.poses, motions):
        for obstacle in obstacles:
            oracle = first_penetration(pose, obstacle, (motion.u1, motion.translation, motion.center))
            actual = paths.se2_first_penetration(pose, obstacle, motion)
            assert actual.status == oracle["status"]
    if valid:
        assert result.ray_verification.valid
        assert result.ray_verification.ray_direction == (0, 1)


def _assert_exact_path_origin():
    moving = rectangle(0, 0, 1, 1)
    epsilon = F(1, 2**90)
    snapped = tuple((x+epsilon, y) for x, y in moving)
    motion = SE2Motion(0, (0, 3))
    bad = path_from_motions(snapped, (motion,))
    checked = paths.verify_se2_escape(moving, (), bad, ((0, 0), (100, 0)))
    assert not checked.valid, "exact input origin rejects unverified snapping"
    assert "exact input pose" in checked.reason
    fixed = path_from_motions(moving, (SE2Motion(0, (epsilon, 0)), motion))
    assert paths.verify_se2_escape(moving, (), fixed, ((0, 0), (100, 0))).valid


def _assert_exact_continuity():
    moving = rectangle(0, 0, 1, 1)
    path = path_from_motions(moving, (SE2Motion(F(1, 3), (0, 3)),))
    epsilon = F(1, 2**90)
    displaced = tuple((x+epsilon, y) for x, y in path.poses[-1])
    bad = paths.SE2EscapePath((moving, displaced), path.motions)
    checked = paths.verify_se2_escape(moving, (), bad, ((0, 0), (100, 0)))
    assert not checked.valid, "vertexwise exact continuity rejects tiny pose gaps"
    assert "exactly joined" in checked.reason


def test_escape_rejects_discontinuous_or_snapped_poses():
    _assert_exact_path_origin()
    _assert_exact_continuity()


def _assert_window_checked():
    moving = rectangle(-1, -1, 0, 0)
    obstacles = (rectangle(1, -2, 2, 2),)
    motion = SE2Motion(0, (4, 0))
    path = path_from_motions(moving, (motion,))
    checked = paths.verify_se2_escape(moving, obstacles, path, ((0, 0), (100, 0)))
    assert not checked.valid, "free endpoints cannot replace the continuous segment check"
    assert "strict overlap" in checked.reason


def test_escape_rejects_free_endpoints_with_blocked_interior():
    _assert_window_checked()


def test_escape_requires_certified_tail_and_strict_motion_support():
    moving = rectangle(0, 0, 1, 1)
    path = path_from_motions(moving, (SE2Motion(),))
    assert not paths.verify_se2_escape(moving, (), path, ((0, 0), (0, 0))).valid
    assert not paths.verify_se2_escape(moving, (), path, ((1, 0), (100, 0))).valid
    assert not paths.verify_se2_escape(moving, (), path, ((0, 0), (100.0, 0))).valid
    # Serialized objects must not bypass the existing SE2Motion support domain.
    forged = SE2Motion()
    object.__setattr__(forged, "u1", F(2))
    with pytest.raises(ValueError, match="supports"):
        paths.SE2EscapePath((moving, moving), (forged,))


def test_strictly_separated_no_contact_fast_check_agrees_with_penetration():
    moving, obstacles = doorway(F(129, 1024))
    path = path_from_motions(moving, tuple(SE2Motion(*s) for s in doorway_motion_specs()))
    for pose, motion in zip(path.poses, path.motions):
        for obstacle in obstacles:
            closed = se2_first_entrance(pose, obstacle, motion)
            opened = paths.se2_first_penetration(pose, obstacle, motion)
            assert closed.initial_state == -1
            assert closed.status == "no_contact" and opened.status == "FREE"
    # FREE alone does not imply no_contact: exact threshold slides on the door.
    moving, obstacles = doorway(F(1, 8))
    path = path_from_motions(moving, tuple(SE2Motion(*s) for s in doorway_motion_specs()))
    assert any(se2_first_entrance(path.poses[-2], b, path.motions[-1]).status == "contact"
               for b in obstacles)


def _mutate_function(monkeypatch, old, new):
    source = inspect.getsource(paths.verify_se2_escape)
    assert source.count(old) == 1, "mutant must identify one real verifier source branch"
    namespace = dict(vars(paths))
    exec(compile(source.replace(old, new), "<t2a_internal_escape_mutant>", "exec"), namespace)
    monkeypatch.setattr(paths, "verify_se2_escape", namespace["verify_se2_escape"])


@pytest.mark.parametrize("old,new,gate,message", [
    ("if path.poses[0] != moving:", "if False:", _assert_exact_path_origin,
     "exact input origin rejects unverified snapping"),
    ("if expected != end:",
     "if len(expected) != len(end) or any(abs(a-b) > F(1, 10**12) for p,q in zip(expected,end) for a,b in zip(p,q)):",
     _assert_exact_continuity, "vertexwise exact continuity rejects tiny pose gaps"),
    ('if any(result.status != "FREE" for result in row):',
     'if any(result.initial_state == 1 or result.end_state == 1 for result in row):',
     _assert_window_checked, "free endpoints cannot replace the continuous segment check"),
])
def test_internal_escape_mutations_are_killed(monkeypatch, old, new, gate, message):
    gate()
    _mutate_function(monkeypatch, old, new)
    with pytest.raises(AssertionError, match=message):
        gate()


def test_internal_motion_domain_mutation_is_killed(monkeypatch):
    from eab.kernel2d import se2
    source = inspect.getsource(SE2Motion.__post_init__)
    import textwrap
    source = textwrap.dedent(source)
    assert source.count("if abs(u) > 1:") == 1
    namespace = dict(vars(se2))
    exec(compile(source.replace("if abs(u) > 1:", "if False:"), "<t2a_motion_mutant>", "exec"), namespace)
    def semantic_gate():
        refused = False
        try:
            SE2Motion(F(3, 2))
        except ValueError:
            refused = True
        assert refused, "motion domain must reject a step over ninety degrees"
    semantic_gate()
    monkeypatch.setattr(SE2Motion, "__post_init__", namespace["__post_init__"])
    with pytest.raises(AssertionError, match="motion domain must reject"):
        semantic_gate()


def test_subthreshold_doorway_rejects_crossing_with_every_endpoint_strictly_free():
    """Independent Sturm/G0 oracle checks a false escape with free endpoints.

    The eroded width after a quarter-turn is 385/512, wider than the 3/4
    doorway by 1/512. Raising the final pose above the roof must not hide
    the exact interior overlap on the last segment. Expected times follow
    from the upper support line, not a production event or root primitive.
    """
    from eab.kernel2d.exact import polygons_overlap_exact
    from m5a_independent_oracle import overlap as oracle_overlap, ring_at

    delta = F(127, 1024)
    moving, obstacles = doorway(delta)
    motions = tuple(SE2Motion(*spec) for spec in doorway_motion_specs()[:2]) + (
        SE2Motion(0, (0, 6), (0, 3)),)
    path = path_from_motions(moving, motions)
    assert path.poses[0] == moving
    assert len(path.poses) == 4 and len(obstacles) == 5
    assert min(y for _, y in path.poses[-1]) == F(7807, 1024) > 7
    # Check all shared endpoints, not just the initial and final configurations.
    for pose in path.poses:
        for obstacle in obstacles:
            assert polygons_overlap_exact(pose, obstacle) == -1
            assert oracle_overlap(pose, obstacle) == -1

    probe_time = F(1, 2)
    probe = tuple(motions[2].at(point, probe_time) for point in path.poses[2])
    spec = (motions[2].u1, motions[2].translation, motions[2].center)
    assert ring_at(path.poses[2], spec, probe_time) == probe
    expected_probe_states = (-1, -1, -1, 1, 1)
    assert tuple(polygons_overlap_exact(probe, obstacle) for obstacle in obstacles) == expected_probe_states
    assert tuple(oracle_overlap(probe, obstacle) for obstacle in obstacles) == expected_probe_states

    result = paths.verify_se2_escape(moving, obstacles, path, ((0, 0), (0, 100)))
    assert not result.valid, "free doorway endpoints must not certify the penetrating interior"
    assert result.reason == "a rigid path segment enters strict overlap"
    # checked_segments counts the failed segment too: index 2 is the third.
    assert result.checked_segments == 3 and result.checked_pairs == 15
    assert len(result.segment_results) == 3
    assert all(len(row) == 5 for row in result.segment_results)
    assert all(pair.status == "FREE" for row in result.segment_results[:2] for pair in row)
    assert tuple(pair.status for pair in result.segment_results[2]) == (
        "FREE", "FREE", "FREE", "PENETRATES", "PENETRATES")
    assert result.ray_verification is None

    expected_tau = (F(6) - (F(9, 2) - delta)) / 6
    assert expected_tau == F(1663, 6144) < probe_time
    for obstacle_index in (3, 4):
        pair = result.segment_results[2][obstacle_index]
        assert pair.initial_state == pair.end_state == -1
        assert pair.exact_time == expected_tau and not pair.immediate
        oracle = first_penetration(path.poses[2], obstacles[obstacle_index], spec)
        assert oracle["initial_state"] == oracle["end_state"] == -1
        assert oracle["status"] == "PENETRATES" and not oracle["immediate"]
        assert oracle["root"].sign((-expected_tau, 1)) == 0
        assert any(state == 1 for _, state in oracle["probes"])
