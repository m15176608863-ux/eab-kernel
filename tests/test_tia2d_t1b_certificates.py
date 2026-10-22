"""Independent oracle gates: rational orientation/ear/SAT, not production E/O.

Analytic axis-aligned rectangles supply exact expectations. Concave examples
exercise independent ear removal. Mutations change verifier function source
before the same semantic assertion, never append fake post-check results.
"""
import ast
from fractions import Fraction as F
import inspect
import random

import pytest

from eab.kernel2d import translation_certificates as certificates


def _rectangle(x0, y0, x1, y1):
    return ((F(x0), F(y0)), (F(x1), F(y0)), (F(x1), F(y1)), (F(x0), F(y1)))


def _enclosure():
    moving = _rectangle(-F(1, 4), -F(1, 4), F(1, 4), F(1, 4))
    obstacles = (_rectangle(-3, -3, 3, -2), _rectangle(-3, 2, 3, 3),
                 _rectangle(-3, -3, -2, 3), _rectangle(2, -3, 3, 3))
    path = ((-2, -2), (2, -2), (2, 2), (-2, 2), (-2, -2))
    return moving, obstacles, path


def _assert_touching_enclosure_is_rejected():
    moving, obstacles, _ = _enclosure()
    r = F(7, 4)
    touching = ((-r, -r), (r, -r), (r, r), (-r, r), (-r, -r))
    checked = certificates.verify_trapping_certificate(moving, obstacles, touching)
    assert not checked.valid, "strict enclosure must reject boundary contact"
    assert "strict convex-pair" in checked.reason


def _assert_segment_obstruction_is_rejected():
    moving = _rectangle(-F(1, 4), -F(1, 4), F(1, 4), F(1, 4))
    obstacles = (_rectangle(1, -1, 2, 1),)
    assert certificates.translation_segment_is_free(moving, obstacles, (0, 0), (0, 0))
    assert certificates.translation_segment_is_free(moving, obstacles, (10, 0), (10, 0))
    checked = certificates.verify_escape_certificate(moving, obstacles, ((0, 0), (10, 0)))
    assert not checked.valid, "escape must check the interior of every segment"
    assert "segment enters" in checked.reason


def _assert_mixed_pair_enclosure_is_rejected():
    moving, obstacles, _ = _enclosure()
    r = F(5, 2)
    diamond = ((r, 0), (0, r), (-r, 0), (0, -r), (r, 0))
    # Each vertex lies strictly in a different wall's overlap region. The
    # midpoints (+/-5/4, +/-5/4), however, leave the complete moving square
    # inside the open central chamber (-2, 2)^2. Nonzero winding and blocked
    # vertices therefore do not certify a wholly blocked enclosure curve.
    for point, obstacle_index in zip(diamond, (3, 1, 2, 0)):
        assert not certificates.translation_segment_is_free(
            moving, (obstacles[obstacle_index],), point, point)
    for a, b in zip(diamond, diamond[1:]):
        midpoint = ((a[0]+b[0])/2, (a[1]+b[1])/2)
        assert all(abs(coordinate)+F(1, 4) < 2 for coordinate in midpoint)
        assert certificates.translation_segment_is_free(moving, obstacles, midpoint, midpoint)
    checked = certificates.verify_trapping_certificate(moving, obstacles, diamond)
    assert not checked.valid, "enclosure must reject endpoints in different convex pairs"
    assert "strict convex-pair" in checked.reason


def test_enclosure_has_strict_witnesses():
    moving, obstacles, path = _enclosure()
    checked = certificates.verify_trapping_certificate(moving, obstacles, path)
    assert checked.valid and checked.winding_number == 1
    assert checked.checked_segments == 4 and len(checked.witnesses) == 4
    assert certificates.verify_trapping_certificate(moving, obstacles, path[::-1]).winding_number == -1
    for a, b in zip(path, path[1:]):
        assert certificates.translation_segment_strictly_blocked(moving, obstacles, a, b)


def test_enclosure_rejects_boundary_contact():
    _assert_touching_enclosure_is_rejected()


def test_enclosure_rejects_blocked_vertices_with_free_edge_interiors():
    """G0 rectangle oracle: blocked diamond vertices, four free edge midpoints."""
    _assert_mixed_pair_enclosure_is_rejected()


def test_escape_rejects_a_segment_with_only_free_endpoints():
    _assert_segment_obstruction_is_rejected()


def test_escape_checks_origin_length_and_explicit_infinite_ray():
    moving = _rectangle(0, 0, 1, 1)
    obstacles = (_rectangle(2, 0, 3, 1),)
    valid = certificates.verify_escape_certificate(moving, obstacles, ((0, 0), (-10, 0)))
    assert valid.valid and valid.ray_direction == (-1, 0)
    too_short = certificates.verify_escape_certificate(moving, obstacles, ((0, 0), (-1, 0)))
    assert not too_short.valid and "diameter" in too_short.reason
    wrong_start = certificates.verify_escape_certificate(moving, obstacles, ((1, 0), (-10, 0)))
    assert not wrong_start.valid and "start at zero" in wrong_start.reason
    penetrating = certificates.verify_escape_certificate(moving, (moving,), ((0, 0), (-10, 0)))
    assert not penetrating.valid and "origin" in penetrating.reason
    empty = certificates.verify_escape_certificate(moving, (), ((0, 0), (1, 0)))
    assert empty.valid and empty.ray_direction == (1, 0)
    assert not certificates.verify_escape_certificate(moving, (), ((0, 0), (0, 0))).valid


def test_escape_boundary_contact_is_allowed_but_arbitrarily_small_penetration_is_not():
    moving = _rectangle(0, 0, 1, 1)
    obstacle = _rectangle(2, 1, 3, 2)
    assert certificates.verify_escape_certificate(moving, (obstacle,), ((0, 0), (20, 0))).valid
    epsilon = F(1, 2**80)
    obstacle = tuple((x, y-epsilon) for x, y in obstacle)
    assert not certificates.verify_escape_certificate(moving, (obstacle,), ((0, 0), (20, 0))).valid


@pytest.mark.parametrize("body_index,horizontal", [(1, -F(3, 32)), (2, F(0)), (3, F(3, 32))])
def test_g1_inner_blocks_have_exact_straight_escape_certificates(body_index, horizontal):
    """At zero tolerance all three G1 interiors escape along one exact ray."""
    from eab.adapters.tia2d import g1
    assembly = g1(t=F(3, 32))
    moving = assembly.bodies[body_index].vertices
    obstacles = tuple(body.vertices for index, body in enumerate(assembly.bodies)
                      if index != body_index)
    path = ((0, 0), (64*horizontal, F(64)))
    checked = certificates.verify_escape_certificate(moving, obstacles, path)
    assert checked.valid and checked.checked_segments == 1


def test_enclosure_rejects_zero_winding_unclosed_path_and_occupied_origin():
    moving, obstacles, path = _enclosure()
    assert not certificates.verify_trapping_certificate(moving, obstacles, path[:-1]).valid
    doubled_back = ((-2, -2), (2, -2), (-2, -2), (-2, -2))
    checked = certificates.verify_trapping_certificate(moving, obstacles, doubled_back)
    assert not checked.valid and "zero winding" in checked.reason
    through_origin = ((0, 0), (2, -2), (2, 2), (0, 0))
    assert "passes through" in certificates.verify_trapping_certificate(moving, obstacles, through_origin).reason
    assert "origin" in certificates.verify_trapping_certificate(moving, obstacles+(moving,), path).reason


@pytest.mark.parametrize("ring", [
    ((0, 0), (1, 0)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (1, 1), (0, 1), (1, 0)),
    ((0, 0), (1, 0), (1, 1), (0, 0)),
    ((0.0, 0), (1, 0), (1, 1), (0, 1)),
])
def test_invalid_or_nonrational_polygon_is_rejected(ring):
    checked = certificates.verify_escape_certificate(ring, (), ((0, 0), (100, 0)))
    assert not checked.valid


def test_concave_ring_and_clockwise_collinear_ring_use_independent_pieces():
    moving = _rectangle(-F(1, 8), -F(1, 8), F(1, 8), F(1, 8))
    concave = ((1, 1), (4, 1), (4, 4), (3, 4), (3, 2), (1, 2))
    assert certificates.verify_escape_certificate(moving, (concave,), ((0, 0), (-30, 0))).valid
    assert not certificates.translation_segment_is_free(moving, (concave,), (0, 3), (10, 3))
    assert certificates.translation_segment_is_free(moving, (concave,), (0, 3), (2, 3))
    collinear = ((1, 1), (2, 1), (3, 1), (3, 2), (1, 2))[::-1]
    assert certificates.verify_escape_certificate(moving, (collinear,), ((0, 0), (-30, 0))).valid


@pytest.mark.parametrize("scale", [F(1, 128), F(1), F(128)])
@pytest.mark.parametrize("offset", [0, 1000, 100000])
def test_certificates_are_covariant_under_exact_rigid_motion_and_units(scale, offset):
    moving, obstacles, path = _enclosure()
    cosine, sine = F(3, 5), F(4, 5)
    def transform(p, translated=True):
        x = scale*(cosine*p[0]-sine*p[1])
        y = scale*(sine*p[0]+cosine*p[1])
        return (x+offset, y-2*offset) if translated else (x, y)
    transformed_moving = tuple(transform(p) for p in moving)
    transformed_obstacles = tuple(tuple(transform(p) for p in polygon) for polygon in obstacles)
    transformed_path = tuple(transform(p, False) for p in path)
    checked = certificates.verify_trapping_certificate(transformed_moving, transformed_obstacles, transformed_path)
    assert checked.valid and checked.winding_number == 1
    escape_obstacles = (obstacles[3],)
    escape_path = ((0, 0), (-100, 0))
    checked = certificates.verify_escape_certificate(
        transformed_moving, tuple(tuple(transform(p) for p in polygon) for polygon in escape_obstacles),
        tuple(transform(p, False) for p in escape_path))
    assert checked.valid and checked.ray_direction is not None


def test_seeded_random_exact_rotations_preserve_enclosure():
    moving, obstacles, path = _enclosure()
    generator = random.Random(20261022)
    for _ in range(5):
        parameter = F(generator.randint(-17, 17), generator.randint(2, 19))
        cosine = (1-parameter*parameter)/(1+parameter*parameter)
        sine = 2*parameter/(1+parameter*parameter)
        def transform(p, translated=True):
            x, y = cosine*p[0]-sine*p[1], sine*p[0]+cosine*p[1]
            return (x+100000, y-200000) if translated else (x, y)
        checked = certificates.verify_trapping_certificate(
            tuple(transform(p) for p in moving),
            tuple(tuple(transform(p) for p in polygon) for polygon in obstacles),
            tuple(transform(p, False) for p in path))
        assert checked.valid and checked.winding_number == 1


def test_mutation_accepting_nonstrict_enclosure_is_killed(monkeypatch):
    source = inspect.getsource(certificates._strict_pair_segment)
    assert source.count("value <= lower or value >= upper") == 1
    mutated = source.replace("value <= lower or value >= upper", "value < lower or value > upper")
    namespace = dict(certificates.__dict__)
    exec(compile(mutated, "<strict-enclosure-mutant>", "exec"), namespace)
    monkeypatch.setattr(certificates, "_strict_pair_segment", namespace["_strict_pair_segment"])
    with pytest.raises(AssertionError, match="strict enclosure must reject boundary contact"):
        _assert_touching_enclosure_is_rejected()


def test_mutation_checking_only_escape_endpoints_is_killed(monkeypatch):
    source = inspect.getsource(certificates._pair_segment_enters)
    signature = source.splitlines()[0]
    mutated = signature+"\n    return (_strict_pair_segment(first, second, start, start) or\n" \
                         "            _strict_pair_segment(first, second, end, end))\n"
    namespace = dict(certificates.__dict__)
    exec(compile(mutated, "<endpoint-only-mutant>", "exec"), namespace)
    monkeypatch.setattr(certificates, "_pair_segment_enters", namespace["_pair_segment_enters"])
    with pytest.raises(AssertionError, match="escape must check the interior of every segment"):
        _assert_segment_obstruction_is_rejected()


def test_mutation_checking_trapping_endpoints_in_different_pairs_is_killed(monkeypatch):
    source = inspect.getsource(certificates._witness)
    original = "if _strict_pair_segment(a, b, start, end):"
    assert source.count(original) == 1
    # Corrupt the production witness search itself: allow the end to use any
    # other convex pair instead of the start's pair. Keep a real start witness
    # rather than fabricating a verifier result after the check.
    replacement = ("if _strict_pair_segment(a, b, start, start) and any(\n"
                   "                        _strict_pair_segment(c, d, end, end)\n"
                   "                        for other in other_parts for c in first_parts for d in other):")
    mutated = source.replace(original, replacement)
    namespace = dict(certificates.__dict__)
    exec(compile(mutated, "<mixed-pair-trapping-mutant>", "exec"), namespace)
    monkeypatch.setattr(certificates, "_witness", namespace["_witness"])
    with pytest.raises(AssertionError, match="enclosure must reject endpoints in different convex pairs"):
        _assert_mixed_pair_enclosure_is_rejected()


def test_verifier_imports_no_production_geometry():
    tree = ast.parse(inspect.getsource(certificates))
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert all(isinstance(node, ast.ImportFrom) and node.level == 0 and
               node.module in {"__future__", "dataclasses", "fractions", "functools"}
               for node in imports)


def test_wobble_bounds_include_whole_free_component_conservatively():
    moving, obstacles, path = _enclosure()
    checked = certificates.verify_wobble_bounds(moving, obstacles, path, F(7, 4))
    assert checked.valid
    assert (checked.area_lower, checked.area_upper) == (F(49, 4), F(16))
    assert (checked.diameter_squared_lower, checked.diameter_squared_upper) == (F(49, 2), F(32))
    assert not certificates.verify_wobble_bounds(moving, obstacles, path, F(7, 4)+F(1, 2**80)).valid
    assert certificates.verify_wobble_bounds(moving, obstacles, path, 0).area_lower == 0


def test_wobble_checks_the_filled_square_not_only_its_boundary():
    moving, obstacles, path = _enclosure()
    # This extra obstacle lies entirely inside the lower square of translation
    # candidates, misses its four edges, and does not occupy the origin.
    obstacles += (_rectangle(F(3, 4), F(3, 4), 1, 1),)
    radius = F(3, 2)
    square = ((-radius, -radius), (radius, -radius), (radius, radius),
              (-radius, radius), (-radius, -radius))
    assert all(certificates.translation_segment_is_free(moving, obstacles, a, b)
               for a, b in zip(square, square[1:]))
    checked = certificates.verify_wobble_bounds(moving, obstacles, path, radius)
    assert not checked.valid and "filled translation square" in checked.reason


def test_critical_tolerance_freezes_iterators_before_repeated_queries():
    """A reused iterator must not change the body family between bracket ends."""
    from eab.adapters.tia2d import tolerance_dovetail
    from eab.kernel2d.erosion import square_element
    from eab.kernel2d.translation_space import critical_tolerance, tolerance_component
    data = tolerance_dovetail()
    direct = critical_tolerance(data["moving"], data["obstacles"], 0, F(1, 32), iterations=0)
    streamed = critical_tolerance(iter(data["moving"]), iter(data["obstacles"]),
                                  0, F(1, 32), iterations=0, element=iter(square_element()))
    assert direct["status"] == streamed["status"] == "UNPROVED"
    for endpoint in ("low_result", "high_result"):
        assert direct[endpoint].status == streamed[endpoint].status == "TRAPPED_TRANSLATION"
        assert streamed[endpoint].verification.valid
    result = tolerance_component(data["moving"], iter(data["obstacles"]), F(1, 32),
                                 element=iter(square_element()))
    assert result.status == "TRAPPED_TRANSLATION" and result.verification.valid
