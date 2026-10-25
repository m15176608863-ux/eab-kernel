"""Owner-supplied counterexamples exercise semantic rejection of v5 cages.

The independent oracle implements the contract without production geometry
imports. Both verifiers receive raw JSON text: the independent entry reads
with load_json, preserving duplicate keys and original integer-token checks.
These tests make no assertion about current source hashes or mutation sites.
The manifest records historical source hashes; only CRLF was normalized to LF.
"""
from pathlib import Path

from eab.kernel2d.se2_cage import verify_se2_cage
from t2b_independent_cage_verifier import _load_result


DATA = Path(__file__).parent / "data" / "t2b_forgeries" / "acceptance_20261026"




def test_acceptance_a01_radius_bound_first_piece_only_is_v0():
    instance = DATA / 'F_A01_radius_bound_first_piece_only' / "instance.json"
    certificate = DATA / 'F_A01_radius_bound_first_piece_only' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_b0x_plugged_obstacles_is_v0():
    instance = DATA / 'F_B0x_plugged_obstacles' / "instance.json"
    certificate = DATA / 'F_B0x_plugged_obstacles' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_h12_unknown_piece_kind_skips_v1_is_v0():
    instance = DATA / 'F_H12_unknown_piece_kind_skips_V1' / "instance.json"
    certificate = DATA / 'F_H12_unknown_piece_kind_skips_V1' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_h13_unknown_ref_tag_is_v0():
    instance = DATA / 'F_H13_unknown_ref_tag' / "instance.json"
    certificate = DATA / 'F_H13_unknown_ref_tag' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_k03_closed_chain_short_span_is_chain():
    instance = DATA / 'F_K03_closed_chain_short_span' / "instance.json"
    certificate = DATA / 'F_K03_closed_chain_short_span' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'CHAIN', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'CHAIN', independent


def test_acceptance_k06_missing_transition_links_is_chain():
    instance = DATA / 'F_K06_missing_transition_links' / "instance.json"
    certificate = DATA / 'F_K06_missing_transition_links' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'CHAIN', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'CHAIN', independent


def test_acceptance_k07_seam_link_omitted_is_chain():
    instance = DATA / 'F_K07_seam_link_omitted' / "instance.json"
    certificate = DATA / 'F_K07_seam_link_omitted' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'CHAIN', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'CHAIN', independent


def test_acceptance_k08_link_first_polyline_unbound_is_chain():
    instance = DATA / 'F_K08_link_first_polyline_unbound' / "instance.json"
    certificate = DATA / 'F_K08_link_first_polyline_unbound' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'CHAIN', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'CHAIN', independent


def test_acceptance_k10_seam_bound_to_last_interval_is_chain():
    instance = DATA / 'F_K10_seam_bound_to_last_interval' / "instance.json"
    certificate = DATA / 'F_K10_seam_bound_to_last_interval' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'CHAIN', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'CHAIN', independent


def test_acceptance_k11_cap_n_bound_to_first_loop_is_chain():
    instance = DATA / 'F_K11_cap_N_bound_to_first_loop' / "instance.json"
    certificate = DATA / 'F_K11_cap_N_bound_to_first_loop' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'CHAIN', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'CHAIN', independent


def test_acceptance_p02_wider_equal_area_piece_is_v0():
    instance = DATA / 'F_P02_wider_equal_area_piece' / "instance.json"
    certificate = DATA / 'F_P02_wider_equal_area_piece' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_p03_overlapping_pieces_hide_pin_is_v0():
    instance = DATA / 'F_P03_overlapping_pieces_hide_pin' / "instance.json"
    certificate = DATA / 'F_P03_overlapping_pieces_hide_pin' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_p04_partition_misses_pinned_corner_is_v0():
    instance = DATA / 'F_P04_partition_misses_pinned_corner' / "instance.json"
    certificate = DATA / 'F_P04_partition_misses_pinned_corner' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_p06_out_of_range_obstacle_piece_is_v0():
    instance = DATA / 'F_P06_out_of_range_obstacle_piece' / "instance.json"
    certificate = DATA / 'F_P06_out_of_range_obstacle_piece' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_r03_bowtie_obstacle_lobe_uncovered_is_v0():
    instance = DATA / 'F_R03_bowtie_obstacle_lobe_uncovered' / "instance.json"
    certificate = DATA / 'F_R03_bowtie_obstacle_lobe_uncovered' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_r06_nonconvex_kernel_false_sat_is_v0():
    instance = DATA / 'F_R06_nonconvex_kernel_false_sat' / "instance.json"
    certificate = DATA / 'F_R06_nonconvex_kernel_false_sat' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_r07_doubly_traversed_half_pin_is_v0():
    instance = DATA / 'F_R07_doubly_traversed_half_pin' / "instance.json"
    certificate = DATA / 'F_R07_doubly_traversed_half_pin' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_v201_kernel_outside_body_is_v2():
    instance = DATA / 'F_V201_kernel_outside_body' / "instance.json"
    certificate = DATA / 'F_V201_kernel_outside_body' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V2', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V2', independent


def test_acceptance_v204_kernel_first_vertex_only_is_v2():
    instance = DATA / 'F_V204_kernel_first_vertex_only' / "instance.json"
    certificate = DATA / 'F_V204_kernel_first_vertex_only' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V2', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V2', independent


def test_acceptance_v302_polygon_outside_circle_is_v3():
    instance = DATA / 'F_V302_polygon_outside_circle' / "instance.json"
    certificate = DATA / 'F_V302_polygon_outside_circle' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V3', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V3', independent


def test_acceptance_v401_segment_end_unchecked_is_v4():
    instance = DATA / 'F_V401_segment_end_unchecked' / "instance.json"
    certificate = DATA / 'F_V401_segment_end_unchecked' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V4', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V4', independent


def test_acceptance_v403_touching_chimney_triangles_is_v4():
    instance = DATA / 'F_V403_touching_chimney_triangles' / "instance.json"
    certificate = DATA / 'F_V403_touching_chimney_triangles' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V4', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V4', independent


def test_acceptance_v501_cap_checks_first_polyline_only_is_v5():
    instance = DATA / 'F_V501_cap_checks_first_polyline_only' / "instance.json"
    certificate = DATA / 'F_V501_cap_checks_first_polyline_only' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V5', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V5', independent


def test_acceptance_v502_cap_quad_drops_corner_is_v5():
    instance = DATA / 'F_V502_cap_quad_drops_corner' / "instance.json"
    certificate = DATA / 'F_V502_cap_quad_drops_corner' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V5', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V5', independent


def test_acceptance_v503_cap_n_left_swapped_is_v5():
    instance = DATA / 'F_V503_cap_N_left_swapped' / "instance.json"
    certificate = DATA / 'F_V503_cap_N_left_swapped' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V5', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V5', independent


def test_acceptance_v505_cap_n_uses_i1_right_is_v5():
    instance = DATA / 'F_V505_cap_N_uses_I1_right' / "instance.json"
    certificate = DATA / 'F_V505_cap_N_uses_I1_right' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V5', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V5', independent


def test_acceptance_v603_start_loop_zero_winding_is_v6():
    instance = DATA / 'F_V603_start_loop_zero_winding' / "instance.json"
    certificate = DATA / 'F_V603_start_loop_zero_winding' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V6', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V6', independent

