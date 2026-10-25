"""Cage lemma §§2.0--2.1, §7: topology and exact bookkeeping forgeries."""

import json

from t2b_hand_cage_builder import build_low_room_cage
from test_t2b_v_geometry import HAND_CAGES, cage_copy, expect_rejection


def alter_closed_line(line):
    result = json.loads(json.dumps(line))
    result[1] = ["100", "100"]
    return result


def test_v0_barrier_requires_explicit_closing_vertex():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["intervals"][0]["loop"].pop()
    certificate["intervals"][0]["witnesses"].pop()
    expect_rejection(instance, certificate, "V0")


def test_v0_unclosed_link_fake_endpoint_copy_contraction():
    instance, certificate = cage_copy(HAND_CAGES)
    item = certificate["links"][0]
    line = json.loads(json.dumps(item["chain"][0]))
    line[-1] = json.loads(json.dumps(line[-2]))
    item["chain"].insert(1, line)
    item["witnesses"].append(json.loads(json.dumps(item["witnesses"][0])))
    expect_rejection(instance, certificate, "V0")


def test_v0_unclosed_cap_fake_endpoint_copy_contraction():
    instance, certificate = build_low_room_cage()
    item = certificate["caps"][0]
    item["chain"][1][-1] = json.loads(json.dumps(item["chain"][1][-2]))
    expect_rejection(instance, certificate, "V0")


def test_v0_link_adjacent_polyline_vertex_counts_disagree():
    instance, certificate = cage_copy(HAND_CAGES)
    item = certificate["links"][0]
    line = json.loads(json.dumps(item["chain"][0]))
    line.insert(1, json.loads(json.dumps(line[0])))
    item["chain"].insert(1, line)
    item["witnesses"].append(json.loads(json.dumps(item["witnesses"][0])))
    expect_rejection(instance, certificate, "V0")


def test_v0_cap_adjacent_polyline_vertex_counts_disagree():
    instance, certificate = build_low_room_cage()
    item = certificate["caps"][0]
    item["chain"][1].insert(1, json.loads(json.dumps(item["chain"][1][0])))
    expect_rejection(instance, certificate, "V0")


def test_v0_link_must_have_at_least_two_lines():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["links"][0]["chain"] = certificate["links"][0]["chain"][:1]
    certificate["links"][0]["witnesses"] = []
    expect_rejection(instance, certificate, "V0")


def test_v0_cap_must_have_at_least_two_lines():
    instance, certificate = build_low_room_cage()
    certificate["caps"][0]["chain"] = certificate["caps"][0]["chain"][:1]
    certificate["caps"][0]["witnesses"] = []
    expect_rejection(instance, certificate, "V0")


def test_v0_geometry_binding_rejects_cyclic_shift():
    instance, certificate = cage_copy(HAND_CAGES)
    ring = certificate["moving"]
    certificate["moving"] = ring[1:] + ring[:1]
    expect_rejection(instance, certificate, "V0")


def test_v0_obstacle_without_any_partition_piece():
    instance, certificate = cage_copy(HAND_CAGES)
    last = len(certificate["obstacles"]) - 1
    pieces = []
    for piece in certificate["obstacle_pieces"]:
        if piece["obstacle"] != last:
            pieces.append(piece)
    certificate["obstacle_pieces"] = pieces
    # Repair all references: absence of this parent's piece, not an index
    # overflow, is the intended partition defect.
    for interval in certificate["intervals"]:
        for witness in interval["witnesses"]:
            if witness[1] >= len(pieces):
                witness[1] = 0
    for link in certificate["links"]:
        for group in link["witnesses"]:
            for witness in group:
                if witness[1] >= len(pieces):
                    witness[1] = 0
    expect_rejection(instance, certificate, "V0")


def test_chain_breakpoints_not_strictly_increasing():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["chain"]["breakpoints"] = ["-1", "-1", "3"]
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_interval_crosses_chart_boundary_one():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["chain"]["breakpoints"] = ["-1", "2", "3"]
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_one_interval_cannot_cover_zero_to_four():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["chain"]["breakpoints"] = ["0", "4"]
    certificate["intervals"] = certificate["intervals"][:1]
    certificate["links"] = certificate["links"][:1]
    certificate["links"][0]["at"] = 1
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_closed_total_span_not_four():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["chain"]["breakpoints"] = ["-1", "1", "5/2"]
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_capped_arc_does_not_contain_zero():
    instance, certificate = build_low_room_cage()
    certificate["chain"]["breakpoints"] = ["1/100", "1/10"]
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_zero_at_cap_endpoint_not_strictly_inside_arc():
    instance, certificate = build_low_room_cage()
    certificate["chain"]["breakpoints"] = ["0", "1/23"]
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_start_interval_does_not_contain_zero():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["start_interval"] = 2
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_wrong_start_interval_cannot_select_a_winding_loop():
    """Claimed interval winds, actual zero-angle interval is constant."""
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["start_interval"] = 2
    point = json.loads(json.dumps(certificate["intervals"][0]["loop"][0]))
    line = []
    for _ in certificate["intervals"][0]["loop"]:
        line.append(json.loads(json.dumps(point)))
    certificate["intervals"][0]["loop"] = line
    certificate["links"][0]["chain"][0] = json.loads(json.dumps(line))
    certificate["links"][1]["chain"][-1] = json.loads(json.dumps(line))
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_start_cap_first_line_differs_from_first_barrier():
    instance, certificate = build_low_room_cage()
    cap = certificate["caps"][0]
    cap["chain"][0] = alter_closed_line(cap["chain"][0])
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_end_cap_first_line_differs_from_last_barrier():
    instance, certificate = build_low_room_cage()
    cap = certificate["caps"][1]
    cap["chain"][0] = alter_closed_line(cap["chain"][0])
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_cap_final_line_is_not_constant():
    instance, certificate = build_low_room_cage()
    cap = certificate["caps"][0]
    cap["chain"][-1] = alter_closed_line(cap["chain"][-1])
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_two_caps_at_start_are_not_two_ends():
    instance, certificate = build_low_room_cage()
    certificate["caps"][1]["at"] = 0
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_missing_end_cap():
    instance, certificate = build_low_room_cage()
    certificate["caps"].pop()
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_link_first_line_differs_from_left_barrier():
    instance, certificate = cage_copy(HAND_CAGES)
    item = certificate["links"][0]
    item["chain"][0] = alter_closed_line(item["chain"][0])
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_link_final_line_differs_from_right_barrier():
    instance, certificate = cage_copy(HAND_CAGES)
    item = certificate["links"][0]
    item["chain"][-1] = alter_closed_line(item["chain"][-1])
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_missing_closed_seam_link():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["links"].pop()
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_duplicate_link_item():
    instance, certificate = cage_copy(HAND_CAGES)
    certificate["links"].append(json.loads(json.dumps(certificate["links"][0])))
    expect_rejection(instance, certificate, "CHAIN")


def test_chain_closed_chain_must_not_have_caps():
    instance, certificate = cage_copy(HAND_CAGES)
    cap = json.loads(json.dumps(certificate["links"][0]))
    cap["at"] = 0
    certificate["caps"].append(cap)
    expect_rejection(instance, certificate, "CHAIN")
