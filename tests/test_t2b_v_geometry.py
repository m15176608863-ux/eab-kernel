"""Independent forged-geometry checks from cage lemma §§1--4 and §7.

Only the independent truth/builder and verifier are used.  Expected failures
are the first lemma condition, never a later condition hidden by an earlier
failure.  The original-point test explicitly records its redundant guard.
"""

import json
from fractions import Fraction as F

import pytest

import t2b_independent_cage_verifier as verifier
from t2b_hand_cage_builder import build_hand_cages, build_low_room_cage


HAND_CAGES = build_hand_cages()


def cage_copy(hand_cages, name="doorway"):
    return json.loads(json.dumps(hand_cages[name]))


def expect_rejection(instance, certificate, condition):
    result = verifier.verify_cage(instance, certificate)
    assert not result["valid"], result
    assert result["condition"] == condition, result
    return result


def rectangle(x0, y0, x1, y1):
    return [[str(F(x0)), str(F(y0))], [str(F(x1)), str(F(y0))],
            [str(F(x1)), str(F(y1))], [str(F(x0)), str(F(y1))]]


def set_moving(instance, certificate, ring):
    instance["moving"] = json.loads(json.dumps(ring))
    certificate["moving"] = json.loads(json.dumps(ring))
    certificate["moving_pieces"] = [json.loads(json.dumps(ring))]
    certificate["radius"] = "100"


def shifted_point(point, dx, dy):
    return [str(F(point[0]) + dx), str(F(point[1]) + dy)]


def shifted_line(line, dx, dy):
    result = []
    for point in line:
        result.append(shifted_point(point, dx, dy))
    return result


def translated_start(instance, certificate, dx, dy):
    """Translate the physical start and compensate every t-coordinate."""
    certificate["moving"] = shifted_line(certificate["moving"], dx, dy)
    instance["moving"] = json.loads(json.dumps(certificate["moving"]))
    pieces = []
    for piece in certificate["moving_pieces"]:
        pieces.append(shifted_line(piece, dx, dy))
    certificate["moving_pieces"] = pieces
    certificate["center"] = shifted_point(certificate["center"], dx, dy)
    for interval in certificate["intervals"]:
        interval["loop"] = shifted_line(interval["loop"], -dx, -dy)
    for category in ("links", "caps"):
        for item in certificate[category]:
            lines = []
            for line in item["chain"]:
                lines.append(shifted_line(line, -dx, -dy))
            item["chain"] = lines


def replace_loop(certificate, index, line):
    """Preserve required link/cap endpoints when changing one barrier."""
    certificate["intervals"][index]["loop"] = json.loads(json.dumps(line))
    count = len(certificate["intervals"])
    for item in certificate["links"]:
        at = item["at"]
        if at - 1 == index:
            item["chain"][0] = json.loads(json.dumps(line))
        if at == index:
            item["chain"][-1] = json.loads(json.dumps(line))
        if at == count and index == 0:
            item["chain"][-1] = json.loads(json.dumps(line))
    for item in certificate["caps"]:
        if item["at"] == 0 and index == 0:
            item["chain"][0] = json.loads(json.dumps(line))
        if item["at"] == count and index == count - 1:
            item["chain"][0] = json.loads(json.dumps(line))


def constant_closed_cage(certificate):
    point = json.loads(json.dumps(certificate["intervals"][0]["loop"][0]))
    obstacle = certificate["intervals"][0]["witnesses"][0][1]
    for interval in certificate["intervals"]:
        line = []
        witnesses = []
        for _ in interval["loop"]:
            line.append(json.loads(json.dumps(point)))
        for _ in interval["witnesses"]:
            witnesses.append([0, obstacle])
        interval["loop"] = line
        interval["witnesses"] = witnesses
    for item in certificate["links"]:
        line = certificate["intervals"][0]["loop"]
        item["chain"] = [json.loads(json.dumps(line)), json.loads(json.dumps(line))]
        witnesses = []
        for _ in range(len(line) - 1):
            witnesses.append([["disk"], obstacle])
        item["witnesses"] = [witnesses]


def seam_exact_forgery(hand_cages):
    """The wrong first-chart R(3) penetrates where correct -R(1) does not."""
    instance, certificate = cage_copy(hand_cages)
    midpoint = [certificate["intervals"][0]["loop"][0][0], "5/2"]
    for interval in certificate["intervals"]:
        line = json.loads(json.dumps(interval["loop"]))
        line.insert(1, json.loads(json.dumps(midpoint)))
        interval["loop"] = line
        witnesses = json.loads(json.dumps(interval["witnesses"]))
        witnesses.insert(1, json.loads(json.dumps(witnesses[0])))
        interval["witnesses"] = witnesses
    for link in certificate["links"]:
        lines = []
        for line in link["chain"]:
            expanded = json.loads(json.dumps(line))
            expanded.insert(1, json.loads(json.dumps(midpoint)))
            lines.append(expanded)
        link["chain"] = lines
        witnesses = []
        for group in link["witnesses"]:
            expanded = json.loads(json.dumps(group))
            expanded.insert(1, json.loads(json.dumps(expanded[0])))
            witnesses.append(expanded)
        link["witnesses"] = witnesses
    seam = certificate["links"][-1]
    middle = json.loads(json.dumps(seam["chain"][0]))
    middle[1] = ["9/2", "5/2"]
    seam["chain"].insert(1, middle)
    seam["witnesses"].append(json.loads(json.dumps(seam["witnesses"][0])))
    for group in seam["witnesses"]:
        group[0][0] = ["exact", 0]
        group[1][0] = ["exact", 0]
    return instance, certificate


@pytest.mark.parametrize("name", ["doorway", "windmill", "midpoint_wedges", "diamond_plates"])
def test_four_hand_cages_are_accepted(name):
    instance, certificate = cage_copy(HAND_CAGES, name)
    result = verifier.verify_cage(instance, certificate)
    assert result["valid"], result
    assert result["condition"] == "OK", result


def test_v0_radius_bound_not_v1():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["radius"] = "1/1000"
    expect_rejection(instance, certificate, "V0")


def test_v0_tiny_radius_on_escapable_high_room():
    instance, certificate = build_low_room_cage()
    high = [rectangle(F(-13, 5), -3, F(13, 5), -2),
            rectangle(F(-13, 5), -2, F(-8, 5), 2),
            rectangle(F(8, 5), -2, F(13, 5), 2),
            rectangle(F(-13, 5), 2, F(-11, 20), 6),
            rectangle(F(11, 20), 2, F(13, 5), 6)]
    instance["obstacles"] = json.loads(json.dumps(high))
    certificate["obstacles"] = json.loads(json.dumps(high))
    pieces = []
    for index, ring in enumerate(high):
        pieces.append({"obstacle": index, "ring": json.loads(json.dumps(ring))})
    certificate["obstacle_pieces"] = pieces
    certificate["radius"] = "1/1000"
    certificate["intervals"][0]["rho"] = "1/10000"
    expect_rejection(instance, certificate, "V0")


def test_v0_negative_radius_of_needle():
    instance, certificate = cage_copy(HAND_CAGES)
    set_moving(instance, certificate, rectangle(-3, F(-1, 10), 3, F(1, 10)))
    certificate["center"] = ["0", "0"]
    certificate["radius"] = "-4"
    walls = [rectangle(-5, -2, 5, -1), rectangle(-5, -1, -4, 6),
             rectangle(4, -1, 5, 6), rectangle(-5, 6, F(-1, 2), 7),
             rectangle(F(1, 2), 6, 5, 7)]
    instance["obstacles"] = json.loads(json.dumps(walls))
    certificate["obstacles"] = json.loads(json.dumps(walls))
    certificate["obstacle_pieces"] = []
    for index, ring in enumerate(walls):
        certificate["obstacle_pieces"].append({"obstacle": index, "ring": json.loads(json.dumps(ring))})
    expect_rejection(instance, certificate, "V0")


def test_v0_nonconvex_dart_kernel():
    instance, certificate = cage_copy(HAND_CAGES)
    polygon = [["-1", "-1"], ["1", "-1"], ["0", "0"],
               ["1", "1"], ["-1", "1"]]
    certificate["intervals"][0]["pieces"] = [
        {"kind": "rotated", "piece": 0, "polygon": polygon}]
    expect_rejection(instance, certificate, "V0")


def test_v0_repeated_moving_piece_vertex_with_protrusion():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["radius"] = "100"
    piece = rectangle(-2, F(1, 4), 2, F(3, 4))
    piece.insert(2, json.loads(json.dumps(piece[1])))
    certificate["moving_pieces"] = [piece]
    expect_rejection(instance, certificate, "V0")


def test_v0_ccw_piece_has_collinear_triple():
    instance, certificate = cage_copy(HAND_CAGES)
    piece = certificate["moving_pieces"][0]
    midpoint = [str((F(piece[0][0]) + F(piece[1][0])) / 2), piece[0][1]]
    piece.insert(1, midpoint)
    expect_rejection(instance, certificate, "V0")


def test_v0_clockwise_piece():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["moving_pieces"][0].reverse()
    expect_rejection(instance, certificate, "V0")


def test_v0_pentagram_mother():
    instance, certificate = cage_copy(HAND_CAGES)
    ring = [["0", "3"], ["-2", "-3"], ["3", "1"],
            ["-3", "1"], ["2", "-3"]]
    set_moving(instance, certificate, ring)
    expect_rejection(instance, certificate, "V0")


def test_v0_square_traversed_twice():
    instance, certificate = cage_copy(HAND_CAGES)
    square = rectangle(-1, -1, 1, 1)
    set_moving(instance, certificate, square + json.loads(json.dumps(square)))
    expect_rejection(instance, certificate, "V0")


def test_v0_partition_missing_piece_area():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["moving_pieces"][0] = certificate["moving_pieces"][0][:3]
    expect_rejection(instance, certificate, "V0")


def test_v0_partition_overlapping_pieces():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["moving_pieces"].append(json.loads(json.dumps(certificate["moving_pieces"][0])))
    expect_rejection(instance, certificate, "V0")


def test_v0_partition_piece_outside_parent():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["radius"] = "100"
    certificate["moving_pieces"] = [rectangle(-2, F(1, 4), 2, F(3, 4))]
    expect_rejection(instance, certificate, "V0")


def test_v0_parent_edge_crosses_piece_through_two_vertices():
    """All child vertices lie in S, but a notch edge cuts int(C).

    The child's average (1/4,0) is strictly inside S.  The mother's edge
    (0,3)->(0,-1) passes through child vertices (0,1),(0,-1), so merely
    checking child endpoints or proper edge crossings would miss the notch.
    """
    instance, certificate = cage_copy(HAND_CAGES)
    parent = [["-3", "-3"], ["3", "-3"], ["3", "3"], ["0", "3"],
              ["0", "-1"], ["-1/10", "-1"], ["-1/10", "3"], ["-3", "3"]]
    child = [["-1", "0"], ["0", "-1"], ["2", "0"], ["0", "1"]]
    set_moving(instance, certificate, parent)
    certificate["center"] = ["0", "0"]
    certificate["moving_pieces"] = [child]
    expect_rejection(instance, certificate, "V0")


def test_v0_point_must_have_exactly_two_coordinates():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["center"] = ["0"]
    result = expect_rejection(instance, certificate, "V0")
    assert result["where"]["check"] == "point_length"


def test_v0_certificate_root_must_be_an_object():
    instance, unused_certificate = cage_copy(HAND_CAGES)
    result = expect_rejection(instance, None, "V0")
    assert result["where"]["check"] == "object_type"


def test_v0_convex_ring_needs_three_vertices():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["moving_pieces"][0] = certificate["moving_pieces"][0][:2]
    result = expect_rejection(instance, certificate, "V0")
    assert result["where"]["check"] == "ring_length"


def test_v0_loop_needs_at_least_one_explicit_segment():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["intervals"][0]["loop"] = [["0", "0"]]
    certificate["intervals"][0]["witnesses"] = []
    result = expect_rejection(instance, certificate, "V0")
    assert result["where"]["check"] == "loop_length"


def test_v0_simple_mother_needs_positive_signed_area():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["moving"].reverse()
    instance["moving"] = json.loads(json.dumps(certificate["moving"]))
    result = expect_rejection(instance, certificate, "V0")
    assert result["where"]["check"] == "ring_positive_area"


def test_v0_nonnull_disk_radius_must_be_positive():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["disk"]["radius"] = "0"
    result = expect_rejection(instance, certificate, "V0")
    assert result["where"]["check"] == "disk_radius_positive"


def test_v0_disk_reference_has_no_index_argument():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["links"][0]["witnesses"][0][0][0] = ["disk", 0]
    result = expect_rejection(instance, certificate, "V0")
    assert result["where"]["check"] == "ref_length"


def test_v0_witness_has_exactly_two_entries():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["intervals"][0]["witnesses"][0] = [0]
    result = expect_rejection(instance, certificate, "V0")
    assert result["where"]["check"] == "witness_arity"


def test_v0_partition_mean_must_be_strictly_inside_parent():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["radius"] = "1000"
    certificate["moving_pieces"] = [rectangle(99, F(1, 4), 101, F(3, 4))]
    result = expect_rejection(instance, certificate, "V0")
    assert result["where"]["check"] == "partition_interior_point"


def test_v1_halved_rho():
    instance, certificate = build_low_room_cage()
    certificate["intervals"][0]["rho"] = str(F(certificate["intervals"][0]["rho"]) / 2)
    expect_rejection(instance, certificate, "V1")


def test_v1_negative_rho_even_disk_only():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["intervals"][0]["rho"] = "-1"
    expect_rejection(instance, certificate, "V1")


def test_v1_midpoint_chart_not_independent_endpoint_charts():
    """[1,3],[3,5] each has coordinate width 2, never width zero."""
    instance, certificate = cage_copy(HAND_CAGES)
    needle = rectangle(-3, F(-1, 10), 3, F(1, 10))
    set_moving(instance, certificate, needle)
    certificate["center"] = ["0", "0"]
    certificate["radius"] = "4"
    certificate["disk"] = None
    certificate["chain"]["breakpoints"] = ["1", "3", "5"]
    certificate["start_interval"] = 2
    for interval in certificate["intervals"]:
        interval["rho"] = "0"
        interval["pieces"] = [{"kind": "rotated", "piece": 0,
                               "polygon": rectangle(F(-1, 100), F(-1, 100), F(1, 100), F(1, 100))}]
    for link in certificate["links"]:
        for group in link["witnesses"]:
            for witness in group:
                witness[0] = ["exact", 0]
    expect_rejection(instance, certificate, "V1")


def test_v2_kernel_vertex_beyond_eroded_halfplane():
    instance, certificate = build_low_room_cage()
    certificate["intervals"][0]["pieces"][0]["polygon"] = rectangle(F(-7, 5), F(-9, 25), F(7, 5), F(9, 25))
    expect_rejection(instance, certificate, "V2")


def test_v2_wrong_moving_piece_reference():
    instance, certificate = build_low_room_cage()
    left = rectangle(F(-3, 2), F(-1, 2), 0, F(1, 2))
    right = rectangle(0, F(-1, 2), F(3, 2), F(1, 2))
    certificate["moving_pieces"] = [left, right]
    certificate["intervals"][0]["pieces"][0]["polygon"] = rectangle(-1, F(-1, 4), F(-1, 2), F(1, 4))
    certificate["intervals"][0]["pieces"][0]["piece"] = 1
    expect_rejection(instance, certificate, "V2")


def test_v3_host_edge_distance_too_small():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["disk"]["radius"] = str(F(certificate["disk"]["radius"]) + F(1, 1024))
    expect_rejection(instance, certificate, "V3")


def test_v3_polygon_vertex_outside_disk():
    instance, certificate = cage_copy(HAND_CAGES)
    polygon = []
    for point in certificate["disk"]["polygon"]:
        polygon.append([str(2 * F(point[0])), str(2 * F(point[1]))])
    certificate["disk"]["polygon"] = polygon
    expect_rejection(instance, certificate, "V3")


def test_v3_host_does_not_contain_center():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["center"] = ["10", "0"]
    certificate["radius"] = "100"
    expect_rejection(instance, certificate, "V3")


def test_v3_unused_nonnull_disk_is_still_checked():
    instance, certificate = build_low_room_cage()
    certificate["disk"] = {"radius": "1", "host": 0,
                           "polygon": rectangle(F(-1, 4), F(-1, 4), F(1, 4), F(1, 4))}
    expect_rejection(instance, certificate, "V3")


def test_v4_loop_vertex_in_free_region():
    instance, certificate = cage_copy(HAND_CAGES)
    line = json.loads(json.dumps(certificate["intervals"][0]["loop"]))
    line[1] = ["0", "0"]
    replace_loop(certificate, 0, line)
    expect_rejection(instance, certificate, "V4")


def test_v4_segment_endpoints_require_the_same_pair():
    instance, certificate = cage_copy(HAND_CAGES)
    interval = certificate["intervals"][0]
    first_obstacle = interval["witnesses"][0][1]
    other_point = None
    for index, witness in enumerate(interval["witnesses"]):
        if witness[1] != first_obstacle:
            other_point = json.loads(json.dumps(interval["loop"][index + 1]))
            break
    assert other_point is not None
    line = json.loads(json.dumps(interval["loop"]))
    line[1] = other_point
    replace_loop(certificate, 0, line)
    expect_rejection(instance, certificate, "V4")


def test_v4_contact_at_nonzero_translation_is_not_strict():
    instance, certificate = cage_copy(HAND_CAGES)
    radius = F(certificate["disk"]["radius"])
    point = ["0", str(radius - F(1, 2))]
    assert point != ["0", "0"]
    line = json.loads(json.dumps(certificate["intervals"][0]["loop"]))
    line[0] = json.loads(json.dumps(point))
    line[-1] = json.loads(json.dumps(point))
    replace_loop(certificate, 0, line)
    certificate["intervals"][0]["witnesses"][0] = [0, 0]
    certificate["intervals"][0]["witnesses"][-1] = [0, 0]
    expect_rejection(instance, certificate, "V4")


def test_v5_connection_quadrilateral_vertex_outside_piece():
    instance, certificate = cage_copy(HAND_CAGES)
    link = certificate["links"][0]
    middle = json.loads(json.dumps(link["chain"][0]))
    middle[1] = ["0", "0"]
    link["chain"].insert(1, middle)
    link["witnesses"].append(json.loads(json.dumps(link["witnesses"][0])))
    expect_rejection(instance, certificate, "V5")


def test_v5_left_index_out_of_range_not_v0():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["links"][0]["witnesses"][0][0][0] = ["left", 1]
    expect_rejection(instance, certificate, "V5")


def test_v5_right_index_out_of_range_not_v0():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["links"][0]["witnesses"][0][0][0] = ["right", 1]
    expect_rejection(instance, certificate, "V5")


def test_v5_nonadjacent_interval_kernel_cannot_supply_local_index():
    instance, certificate = cage_copy(HAND_CAGES)
    base_interval = certificate["intervals"][0]
    base_link = certificate["links"][0]
    certificate["chain"]["breakpoints"] = ["-1", "0", "1", "2", "3"]
    certificate["intervals"] = []
    certificate["links"] = []
    for index in range(4):
        certificate["intervals"].append(json.loads(json.dumps(base_interval)))
        link = json.loads(json.dumps(base_link))
        link["at"] = index + 1
        certificate["links"].append(link)
    certificate["intervals"][0]["pieces"].append({"kind": "disk"})
    # I_1 has piece 1, but the at=2 connection touches only I_2 and I_3.
    certificate["links"][1]["witnesses"][0][0][0] = ["left", 1]
    expect_rejection(instance, certificate, "V5")


def test_v5_closed_seam_exact_uses_last_interval_chart():
    instance, certificate = seam_exact_forgery(HAND_CAGES)
    expect_rejection(instance, certificate, "V5")


def test_v5_left_reference_forbidden_at_start_cap():
    instance, certificate = build_low_room_cage()
    certificate["caps"][0]["witnesses"][0][0][0] = ["left", 0]
    expect_rejection(instance, certificate, "V5")


def test_v5_right_reference_forbidden_at_end_cap():
    instance, certificate = build_low_room_cage()
    certificate["caps"][1]["witnesses"][0][0][0] = ["right", 0]
    expect_rejection(instance, certificate, "V5")


def test_v5_constant_cap_point_in_free_space():
    instance, certificate = build_low_room_cage()
    cap = certificate["caps"][0]
    line = []
    for _ in cap["chain"][-1]:
        line.append(["100", "100"])
    cap["chain"][-1] = line
    expect_rejection(instance, certificate, "V5")


def test_v6_start_pose_has_interior_intersection():
    instance, certificate = cage_copy(HAND_CAGES)
    point = certificate["intervals"][0]["loop"][0]
    translated_start(instance, certificate, F(point[0]), F(point[1]))
    expect_rejection(instance, certificate, "V6")


def test_v6_start_loop_has_zero_winding():
    instance, certificate = cage_copy(HAND_CAGES)
    constant_closed_cage(certificate)
    expect_rejection(instance, certificate, "V6")


def test_origin_crossing_free_start_first_fails_v4():
    """§7 order: an origin-crossing barrier cannot pass V4 at free q0."""
    instance, certificate = cage_copy(HAND_CAGES)
    line = json.loads(json.dumps(certificate["intervals"][0]["loop"]))
    line[0] = ["0", "0"]
    line[-1] = ["0", "0"]
    replace_loop(certificate, 0, line)
    expect_rejection(instance, certificate, "V4")


def test_origin_crossing_v4_valid_first_fails_v6_start_pose():
    """V4-valid origin crossing necessarily makes q0 penetrating.

    This is not an independent kill of the no-origin/winding boundary guard.
    """
    instance, certificate = cage_copy(HAND_CAGES)
    point = certificate["intervals"][0]["loop"][0]
    translated_start(instance, certificate, F(point[0]), F(point[1]))
    assert certificate["intervals"][0]["loop"][0] == ["0", "0"]
    expect_rejection(instance, certificate, "V6")


def test_cross_input_replay_of_doorway_threshold_is_v0():
    instance, certificate = cage_copy(HAND_CAGES)
    instance["moving"] = rectangle(F(-11, 8), F(1, 8), F(11, 8), F(7, 8))
    expect_rejection(instance, certificate, "V0")


def test_doorway_equal_width_invariant_disk_is_rejected():
    instance, certificate = cage_copy(HAND_CAGES)
    ring = rectangle(F(-11, 8), F(1, 8), F(11, 8), F(7, 8))
    set_moving(instance, certificate, ring)
    certificate["radius"] = "2"
    certificate["disk"]["radius"] = "3/8"
    certificate["disk"]["polygon"] = [["3/8", "0"], ["0", "3/8"],
                                         ["-3/8", "0"], ["0", "-3/8"]]
    # Recompute the same adjacent-M closed-intersection averages at equality.
    # The roof intersection collapses to a segment; its average (0,6) is
    # contact, not strict penetration, and must not create a false cage.
    line = [["55/16", "-1/2"], ["55/16", "11/2"], ["0", "6"],
            ["-55/16", "11/2"], ["-55/16", "-1/2"], ["55/16", "-1/2"]]
    for interval in certificate["intervals"]:
        interval["loop"] = json.loads(json.dumps(line))
    for item in certificate["links"]:
        item["chain"] = [json.loads(json.dumps(line)), json.loads(json.dumps(line))]
    expect_rejection(instance, certificate, "V4")


def test_low_room_capped_certificate_is_accepted():
    instance, certificate = build_low_room_cage()
    result = verifier.verify_cage(instance, certificate)
    assert result["valid"], result


def test_same_low_room_construction_rebound_to_high_room_is_rejected():
    instance, certificate = build_low_room_cage()
    high = [rectangle(F(-13, 5), -3, F(13, 5), -2),
            rectangle(F(-13, 5), -2, F(-8, 5), 2),
            rectangle(F(8, 5), -2, F(13, 5), 2),
            rectangle(F(-13, 5), 2, F(-11, 20), 6),
            rectangle(F(11, 20), 2, F(13, 5), 6)]
    instance["obstacles"] = json.loads(json.dumps(high))
    certificate["obstacles"] = json.loads(json.dumps(high))
    certificate["obstacle_pieces"] = []
    for index, ring in enumerate(high):
        certificate["obstacle_pieces"].append({"obstacle": index, "ring": json.loads(json.dumps(ring))})
    expect_rejection(instance, certificate, "V4")
