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


DATA = Path(__file__).parent / "data" / "t2b_forgeries" / "acc"




def test_acceptance_a01_radius_bound_first_piece_only_is_v0():
    instance = DATA / 'A01' / "instance.json"
    certificate = DATA / 'A01' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_b0x_plugged_obstacles_is_v0():
    instance = DATA / 'B0x' / "instance.json"
    certificate = DATA / 'B0x' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_h12_unknown_piece_kind_skips_v1_is_v0():
    instance = DATA / 'H12' / "instance.json"
    certificate = DATA / 'H12' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_h13_unknown_ref_tag_is_v0():
    instance = DATA / 'H13' / "instance.json"
    certificate = DATA / 'H13' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_k03_closed_chain_short_span_is_chain():
    instance = DATA / 'K03' / "instance.json"
    certificate = DATA / 'K03' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'CHAIN', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'CHAIN', independent


def test_acceptance_k06_missing_transition_links_is_chain():
    instance = DATA / 'K06' / "instance.json"
    certificate = DATA / 'K06' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'CHAIN', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'CHAIN', independent


def test_acceptance_k07_seam_link_omitted_is_chain():
    instance = DATA / 'K07' / "instance.json"
    certificate = DATA / 'K07' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'CHAIN', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'CHAIN', independent


def test_acceptance_k08_link_first_polyline_unbound_is_chain():
    instance = DATA / 'K08' / "instance.json"
    certificate = DATA / 'K08' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'CHAIN', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'CHAIN', independent


def test_acceptance_k10_seam_bound_to_last_interval_is_chain():
    instance = DATA / 'K10' / "instance.json"
    certificate = DATA / 'K10' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'CHAIN', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'CHAIN', independent


def test_acceptance_k11_cap_n_bound_to_first_loop_is_chain():
    instance = DATA / 'K11' / "instance.json"
    certificate = DATA / 'K11' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'CHAIN', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'CHAIN', independent


def test_acceptance_p02_wider_equal_area_piece_is_v0():
    instance = DATA / 'P02' / "instance.json"
    certificate = DATA / 'P02' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_p03_overlapping_pieces_hide_pin_is_v0():
    instance = DATA / 'P03' / "instance.json"
    certificate = DATA / 'P03' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_p04_partition_misses_pinned_corner_is_v0():
    instance = DATA / 'P04' / "instance.json"
    certificate = DATA / 'P04' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_p06_out_of_range_obstacle_piece_is_v0():
    instance = DATA / 'P06' / "instance.json"
    certificate = DATA / 'P06' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_r03_bowtie_obstacle_lobe_uncovered_is_v0():
    instance = DATA / 'R03' / "instance.json"
    certificate = DATA / 'R03' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_r06_nonconvex_kernel_false_sat_is_v0():
    instance = DATA / 'R06' / "instance.json"
    certificate = DATA / 'R06' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_r07_doubly_traversed_half_pin_is_v0():
    instance = DATA / 'R07' / "instance.json"
    certificate = DATA / 'R07' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V0', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V0', independent


def test_acceptance_v201_kernel_outside_body_is_v2():
    instance = DATA / 'V201' / "instance.json"
    certificate = DATA / 'V201' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V2', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V2', independent


def test_acceptance_v204_kernel_first_vertex_only_is_v2():
    instance = DATA / 'V204' / "instance.json"
    certificate = DATA / 'V204' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V2', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V2', independent


def test_acceptance_v302_polygon_outside_circle_is_v3():
    instance = DATA / 'V302' / "instance.json"
    certificate = DATA / 'V302' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V3', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V3', independent


def test_acceptance_v401_segment_end_unchecked_is_v4():
    instance = DATA / 'V401' / "instance.json"
    certificate = DATA / 'V401' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V4', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V4', independent


def test_acceptance_v403_touching_chimney_triangles_is_v4():
    instance = DATA / 'V403' / "instance.json"
    certificate = DATA / 'V403' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V4', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V4', independent


def test_acceptance_v501_cap_checks_first_polyline_only_is_v5():
    instance = DATA / 'V501' / "instance.json"
    certificate = DATA / 'V501' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V5', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V5', independent


def test_acceptance_v502_cap_quad_drops_corner_is_v5():
    instance = DATA / 'V502' / "instance.json"
    certificate = DATA / 'V502' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V5', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V5', independent


def test_acceptance_v503_cap_n_left_swapped_is_v5():
    instance = DATA / 'V503' / "instance.json"
    certificate = DATA / 'V503' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V5', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V5', independent


def test_acceptance_v505_cap_n_uses_i1_right_is_v5():
    instance = DATA / 'V505' / "instance.json"
    certificate = DATA / 'V505' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V5', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V5', independent


def test_acceptance_v603_start_loop_zero_winding_is_v6():
    instance = DATA / 'V603' / "instance.json"
    certificate = DATA / 'V603' / "cert.json"
    production = verify_se2_cage(instance.read_text("utf-8"),
                                certificate.read_text("utf-8"))
    assert not production.valid and production.condition == 'V6', production
    independent = _load_result(instance, certificate)
    assert not independent["valid"] and independent["condition"] == 'V6', independent

