"""P1.6 independent support-line oracle for exact dovetail erosion.

Oracle primitives are hand-derived source normals/intercepts, direct vertex
dot products, signed polygon area, and rational edge-direction comparisons.
They do not call the constructor's half-plane, line-intersection, erosion,
convex-hull, or canonicalization helpers.  The source coordinates are copied
only from the expressly allowed tolerance_dovetail function with h=w=2.
Both original facets and resulting edges are checked, including exact squared
Euclidean offset distances; feasible vertices alone are not a complete oracle.
"""

from fractions import Fraction as F
import json
from pathlib import Path

import pytest

import t2b_independent_instances as instances


SQUARE = ((F(-1), F(-1)), (F(1), F(-1)), (F(1), F(1)), (F(-1), F(1)))
OCTAGON = ((F(-5, 12), F(-1)), (F(5, 12), F(-1)),
           (F(1), F(-5, 12)), (F(1), F(5, 12)),
           (F(5, 12), F(1)), (F(-5, 12), F(1)),
           (F(-1), F(5, 12)), (F(-1), F(-5, 12)))
CASES = (
    ("d01", F(5, 2), F(3, 2), "square", 0, F(3, 10)),
    ("d02", F(7, 2), F(3, 2), "square", 0, F(2, 5)),
    ("d03", F(5, 2), F(1), "square", 0, F(21, 50)),
    ("d04", F(5, 2), F(1), "square", 1, F(1, 5)),
    ("d05", F(7, 2), F(3, 2), "octagon", 0, F(9, 20)),
    ("d06", F(3), F(1), "octagon", 0, F(11, 20)),
    ("d07", F(5, 2), F(3, 2), "octagon", 0, F(7, 20)),
    ("d08", F(3), F(3, 2), "octagon", 1, F(6, 25)),
)


def oracle_kernel(name):
    if name == "square":
        return SQUARE
    if name == "octagon":
        return OCTAGON
    raise ValueError("unknown oracle kernel")


def decode_ring(ring):
    result = []
    for point in ring:
        result.append((F(point[0]), F(point[1])))
    return result


def encode_ring(ring):
    result = []
    for point in ring:
        result.append([str(F(point[0])), str(F(point[1]))])
    return result


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def area_twice(ring):
    result = F(0)
    for index in range(len(ring)):
        result += cross(ring[index], ring[(index + 1) % len(ring)])
    return result


def support(ring, normal):
    result = dot(ring[0], normal)
    for point in ring[1:]:
        value = dot(point, normal)
        if value > result:
            result = value
    return result


def edge_normals(ring):
    result = []
    for index in range(len(ring)):
        a = ring[index]
        b = ring[(index + 1) % len(ring)]
        result.append((b[1] - a[1], a[0] - b[0]))
    return result


def same_direction(a, b):
    return cross(a, b) == 0 and dot(a, b) > 0


def oracle_source(wk, wn):
    """Literal allowed geometry, with each clean ring manually rotated to lex-min."""
    outside = wk / 2 + 2
    moving = ((-wk / 2, F(0)), (wk / 2, F(0)), (wn / 2, F(2)), (-wn / 2, F(2)))
    left = ((-outside, F(0)), (-wk / 2, F(0)), (-wn / 2, F(2)), (-outside, F(2)))
    right = ((wn / 2, F(2)), (wk / 2, F(0)), (outside, F(0)), (outside, F(2)))
    floor = ((-outside, F(-2)), (outside, F(-2)), (outside, F(0)), (-outside, F(0)))
    return moving, (left, right, floor)


def oracle_constraints(wk, wn):
    """Hand normals and intercepts, not recovered from constructor output.

    Sloping wall/body normals use the exact unnormalized pairs (±4,±(wk-wn));
    the factor four comes from height two and half-width endpoint differences.
    """
    outside = wk / 2 + 2
    taper = wk - wn
    down = (F(0), F(-1))
    up = (F(0), F(1))
    left = (F(-1), F(0))
    right = (F(1), F(0))
    moving = ((down, F(0)), ((F(4), taper), 2 * wk), (up, F(2)), ((F(-4), taper), 2 * wk))
    left_wall = ((down, F(0)), ((F(4), -taper), -2 * wk), (up, F(2)), (left, outside))
    right_wall = (((F(-4), -taper), -2 * wk), (down, F(0)), (right, outside), (up, F(2)))
    floor = ((down, F(2)), (right, outside), (up, F(0)), (left, outside))
    return moving, (left_wall, right_wall, floor)


def assert_canonical_full_ring(encoded):
    assert len(encoded) >= 3
    ring = decode_ring(encoded)
    assert area_twice(ring) > 0
    assert len(set(ring)) == len(ring)
    lowest = ring[0]
    for point in ring[1:]:
        if point < lowest:
            lowest = point
    assert ring[0] == lowest
    for index, point in enumerate(encoded):
        assert len(point) == 2
        for value in point:
            assert isinstance(value, str)
            assert str(F(value)) == value
        previous = ring[index - 1]
        current = ring[index]
        following = ring[(index + 1) % len(ring)]
        before = (current[0] - previous[0], current[1] - previous[1])
        after = (following[0] - current[0], following[1] - current[1])
        assert cross(before, after) != 0


def assert_support_contract(source, encoded, constraints, kernel, delta):
    """Check both facet directions and exact inward Euclidean distances."""
    assert_canonical_full_ring(encoded)
    result = decode_ring(encoded)
    assert len(result) == len(constraints)
    new_normals = edge_normals(result)
    for normal, intercept in constraints:
        assert support(source, normal) == intercept
        kernel_support = support(kernel, normal)
        new_intercept = support(result, normal)
        shift = intercept - new_intercept
        assert shift >= 0
        assert shift == delta * kernel_support
        norm_squared = dot(normal, normal)
        assert norm_squared > 0
        distance_squared = shift * shift / norm_squared
        expected_distance_squared = delta * delta * kernel_support * kernel_support / norm_squared
        assert distance_squared == expected_distance_squared
        matches = 0
        for new_normal in new_normals:
            if same_direction(new_normal, normal):
                matches += 1
        assert matches == 1
        for point in result:
            assert dot(normal, point) <= intercept - delta * kernel_support
    for new_normal in new_normals:
        matches = 0
        for normal, unused_intercept in constraints:
            if same_direction(new_normal, normal):
                matches += 1
        assert matches == 1
        offset = support(source, new_normal) - support(result, new_normal)
        assert offset >= 0
        assert offset == delta * support(kernel, new_normal)


def assert_instance_contract(case, delta):
    unused_name, wk, wn, kernel_name, walls_eroded, unused_delta = case
    kernel = oracle_kernel(kernel_name)
    actual = instances.dovetail_instance(wk, wn, kernel, walls_eroded, delta)
    moving, walls = oracle_source(wk, wn)
    moving_constraints, wall_constraints = oracle_constraints(wk, wn)
    assert list(actual) == ["moving", "obstacles"]
    assert len(actual["obstacles"]) == 3
    assert_support_contract(moving, actual["moving"], moving_constraints, kernel, delta)
    wall_delta = F(0)
    if walls_eroded == 1:
        wall_delta = delta
    for index in range(3):
        output = actual["obstacles"][index]
        assert_support_contract(walls[index], output, wall_constraints[index], kernel, wall_delta)
        if walls_eroded == 0:
            assert output == encode_ring(walls[index])
        else:
            assert area_twice(decode_ring(output)) < area_twice(walls[index])
    return actual


@pytest.mark.parametrize("case", CASES, ids=[case[0] for case in CASES])
def test_zero_erosion_equals_allowed_source_geometry(case):
    unused_name, wk, wn, kernel_name, walls_eroded, unused_delta = case
    moving, walls = oracle_source(wk, wn)
    expected = {"moving": encode_ring(moving), "obstacles": []}
    for wall in walls:
        expected["obstacles"].append(encode_ring(wall))
    actual = instances.dovetail_instance(wk, wn, oracle_kernel(kernel_name), walls_eroded, F(0))
    assert actual == expected


@pytest.mark.parametrize("case", CASES, ids=[case[0] for case in CASES])
def test_declared_delta_matches_every_old_and_new_support_line(case):
    assert_instance_contract(case, case[5])


@pytest.mark.parametrize("case", CASES, ids=[case[0] for case in CASES])
def test_general_rational_delta_not_in_case_table(case):
    delta = F(7, 53)
    for table_case in CASES:
        assert delta != table_case[5]
    assert_instance_contract(case, delta)


@pytest.mark.parametrize("case", (CASES[3], CASES[7]), ids=("d04", "d08"))
@pytest.mark.parametrize("wall_index", (0, 1, 2), ids=("left", "right", "floor"))
def test_e1_each_of_three_walls_has_strictly_smaller_exact_area(case, wall_index):
    unused_name, wk, wn, kernel_name, e, delta = case
    assert e == 1
    actual = instances.dovetail_instance(wk, wn, oracle_kernel(kernel_name), e, delta)
    unused_moving, original_walls = oracle_source(wk, wn)
    original_area_twice = area_twice(original_walls[wall_index])
    eroded_area_twice = area_twice(decode_ring(actual["obstacles"][wall_index]))
    assert F(0) < eroded_area_twice < original_area_twice


@pytest.mark.parametrize("case", (CASES[0], CASES[1], CASES[2], CASES[4], CASES[5], CASES[6]),
                         ids=("d01", "d02", "d03", "d05", "d06", "d07"))
def test_e0_all_obstacle_vertices_and_order_remain_exactly_unchanged(case):
    unused_name, wk, wn, kernel_name, e, delta = case
    assert e == 0
    actual = instances.dovetail_instance(wk, wn, oracle_kernel(kernel_name), e, delta)
    unused_moving, walls = oracle_source(wk, wn)
    expected = []
    for wall in walls:
        expected.append(encode_ring(wall))
    assert actual["obstacles"] == expected


@pytest.mark.parametrize("case", CASES, ids=[case[0] for case in CASES])
def test_eight_exported_json_instances_are_canonical_and_match_api(case):
    name, wk, wn, kernel_name, walls_eroded, delta = case
    directory = Path(__file__).parent / "data/t2b_independent_instances"
    path = directory / (name + ".json")
    data = path.read_bytes()
    assert not data.startswith(bytes((239, 187, 191)))
    assert b"\r" not in data
    assert data.endswith(b"\n")
    decoded = json.loads(data.decode("utf-8"))
    expected = instances.dovetail_instance(wk, wn, oracle_kernel(kernel_name), walls_eroded, delta)
    assert decoded == expected
    assert decoded == instances.build_independent_instances()[name]
    assert list(decoded) == ["moving", "obstacles"]
    assert_canonical_full_ring(decoded["moving"])
    for wall in decoded["obstacles"]:
        assert_canonical_full_ring(wall)


def test_case_manifest_has_exactly_the_eight_owner_cases():
    names = []
    for case in CASES:
        names.append(case[0])
    assert list(instances.build_independent_instances()) == names
    directory = Path(__file__).parent / "data/t2b_independent_instances"
    assert sorted(path.name for path in directory.glob("*.json")) == [name + ".json" for name in names]
    assert instances.SQUARE == SQUARE
    assert instances.OCTAGON == OCTAGON


@pytest.mark.parametrize("variant", ("original", "clockwise", "cyclic", "collinear", "duplicate", "closed"))
def test_canonical_ring_normalizes_only_representation(variant):
    base = [(F(-2), F(-1)), (F(3), F(-1)), (F(3), F(4)), (F(-2), F(4))]
    ring = list(base)
    if variant == "clockwise":
        ring.reverse()
    elif variant == "cyclic":
        ring = ring[2:] + ring[:2]
    elif variant == "collinear":
        ring.insert(1, (F(0), F(-1)))
    elif variant == "duplicate":
        ring.insert(1, ring[0])
    elif variant == "closed":
        ring.extend([ring[0], ring[0]])
    assert instances.canonical_ring(ring) == encode_ring(base)


def test_canonical_ring_preserves_arbitrarily_small_noncollinear_feature():
    epsilon = F(1, 1000000000000000000000000000000)
    expected = [(F(-1), F(-1)), (F(1), F(-1)), (F(1), F(1) - epsilon),
                (F(1) - epsilon, F(1)), (F(-1), F(1))]
    variant = list(reversed(expected))
    variant.append(variant[0])
    actual = instances.canonical_ring(variant)
    assert actual == encode_ring(expected)
    assert len(actual) == 5


def test_canonical_ring_preserves_concave_notch_without_convexifying():
    epsilon = F(1, 1000000000000000000000000000000)
    expected = [(F(-2), F(-2)), (F(2), F(-2)), (F(2), F(2)),
                (epsilon, F(2)), (epsilon, F(1)), (F(0), F(1)),
                (F(0), F(2)), (F(-2), F(2))]
    variant = list(reversed(expected))
    variant.append(variant[0])
    actual = instances.canonical_ring(variant)
    assert actual == encode_ring(expected)
    assert area_twice(decode_ring(actual)) == F(32) - 2 * epsilon


def test_canonical_instance_keeps_obstacle_order():
    moving, walls = oracle_source(F(5, 2), F(3, 2))
    raw = {"moving": list(reversed(moving)), "obstacles": [list(reversed(walls[2])), list(reversed(walls[0])), list(reversed(walls[1]))]}
    expected = {"moving": encode_ring(moving), "obstacles": [encode_ring(walls[2]), encode_ring(walls[0]), encode_ring(walls[1])]}
    assert instances.canonical_instance(raw) == expected


def test_canonical_ring_uses_numeric_not_string_lexicographic_minimum():
    raw = ((10, -1), (10, 1), (2, 1), (2, -1))
    expected = [["2", "-1"], ["10", "-1"], ["10", "1"], ["2", "1"]]
    assert "10" < "2"
    assert instances.canonical_ring(raw) == expected


@pytest.mark.parametrize("case", CASES, ids=[case[0] for case in CASES])
def test_canonical_instance_is_idempotent_after_noncanonical_representation(case):
    unused_name, wk, wn, kernel_name, e, delta = case
    expected = instances.dovetail_instance(wk, wn, oracle_kernel(kernel_name), e, delta)
    moving = list(reversed(expected["moving"]))
    moving.append(moving[0])
    raw = {"moving": moving, "obstacles": []}
    for wall in expected["obstacles"]:
        changed = wall[1:] + wall[:1]
        changed.append(changed[0])
        raw["obstacles"].append(changed)
    once = instances.canonical_instance(raw)
    twice = instances.canonical_instance(once)
    assert once == expected
    assert twice == once


@pytest.mark.parametrize("name,ring,delta,expected", (
    ("point", ((-1, -1), (1, -1), (1, 1), (-1, 1)), F(1), [["0", "0"]]),
    ("segment", ((-2, -1), (2, -1), (2, 1), (-2, 1)), F(1), [["-1", "0"], ["1", "0"]]),
    ("empty", ((-1, -1), (1, -1), (1, 1), (-1, 1)), F(3, 2), []),
))
def test_erosion_retains_exact_empty_point_and_segment_boundaries(name, ring, delta, expected):
    assert instances.erode_convex(ring, SQUARE, delta) == expected


def test_dovetail_exact_collapse_at_five_sixths_and_empty_at_one():
    point = instances.dovetail_instance(F(5, 2), F(3, 2), SQUARE, 0, F(5, 6))
    empty = instances.dovetail_instance(F(5, 2), F(3, 2), SQUARE, 0, F(1))
    assert point["moving"] == [["0", "5/6"]]
    assert empty["moving"] == []


@pytest.mark.parametrize("kernel", (SQUARE, OCTAGON))
def test_negative_delta_for_centrally_symmetric_kernel_is_not_dilation(kernel):
    positive = instances.dovetail_instance(F(5, 2), F(3, 2), kernel, 1, F(1, 5))
    negative = instances.dovetail_instance(F(5, 2), F(3, 2), kernel, 1, F(-1, 5))
    assert negative == positive


def test_negative_delta_reflects_an_asymmetric_kernel_without_abs_shortcut():
    ring = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    kernel = ((F(0), F(0)), (F(1), F(0)), (F(0), F(1)))
    positive = instances.erode_convex(ring, kernel, F(1, 4))
    negative = instances.erode_convex(ring, kernel, F(-1, 4))
    assert positive == [["-1", "-1"], ["3/4", "-1"], ["3/4", "3/4"], ["-1", "3/4"]]
    assert negative == [["-3/4", "-3/4"], ["1", "-3/4"], ["1", "1"], ["-3/4", "1"]]
    assert positive != negative


@pytest.mark.parametrize("ring,expected", (
    ([], []),
    ([(0, 0), (0, 0)], [["0", "0"]]),
    ([(2, 2), (0, 0), (1, 1), (-1, -1), (2, 2)], [["-1", "-1"], ["2", "2"]]),
))
def test_canonical_ring_keeps_degenerate_set_dimension(ring, expected):
    assert instances.canonical_ring(ring) == expected
