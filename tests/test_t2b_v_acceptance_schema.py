"""Isolated schema/bookkeeping rejection gates for surviving source mutants.

Fixtures J07/J15/J16/J14/C09/V505 are accepted by their corresponding single
source mutant, not merely rejected elsewhere.  A22 instead exposes the mutant's
IndexError and A24 its wrong CHAIN first rejection; neither is called accepted.
Only repository-local JSON and the unchanged independent verifier are used.
"""

from test_t2b_v_acceptance_major import exact_rejection


def test_J07_valid_radius_as_json_integer_is_rejected_as_rational_type():
    certificate, unused_result = exact_rejection("schema_J07", "V0", "rational_type")
    assert type(certificate["radius"]) is int
    assert certificate["radius"] == 2


def test_J15_extra_witness_entry_is_not_silently_ignored():
    certificate, unused_result = exact_rejection("schema_J15", "V0", "witness_arity")
    assert len(certificate["intervals"][0]["witnesses"][0]) == 3


def test_J16_extra_point_coordinate_is_not_silently_ignored():
    certificate, unused_result = exact_rejection("schema_J16", "V0", "point_length")
    assert len(certificate["center"]) == 3


def test_J14_unknown_two_item_reference_cannot_fall_through_to_right():
    certificate, unused_result = exact_rejection("schema_J14", "V0", "ref_kind")
    reference = certificate["links"][0]["witnesses"][0][0][0]
    assert reference == ["unrecognized", 0]


def test_C09_duplicate_valid_cap_is_not_accepted_as_an_at_set():
    certificate, unused_result = exact_rejection("schema_C09", "CHAIN", "cap_set")
    assert len(certificate["caps"]) == 3
    assert certificate["caps"][0] == certificate["caps"][2]


def test_A22_extra_otherwise_valid_interval_is_rejected_before_chart_indexing():
    certificate, unused_result = exact_rejection("schema_A22", "V0", "interval_count")
    assert len(certificate["intervals"]) == len(certificate["chain"]["breakpoints"])


def test_A24_zero_start_interval_is_v0_not_later_chain_rejection():
    certificate, unused_result = exact_rejection("schema_A24", "V0", "start_index")
    assert certificate["start_interval"] == 0


def test_V505_start_cap_forbidden_left_has_an_otherwise_valid_quad():
    certificate, result = exact_rejection("schema_V505_start", "V5", "reference_side")
    assert certificate["caps"][0]["at"] == 0
    assert certificate["caps"][0]["witnesses"][0][1][0] == ["left", 0]
    assert result["where"]["path"] == ["certificate", "caps", 0, "witnesses", 0, 1, 0]


def test_V505_end_cap_forbidden_right_has_an_otherwise_valid_quad():
    certificate, result = exact_rejection("schema_V505_end", "V5", "reference_side")
    assert certificate["caps"][1]["at"] == len(certificate["intervals"])
    assert certificate["caps"][1]["witnesses"][0][2][0] == ["right", 0]
    assert result["where"]["path"] == ["certificate", "caps", 1, "witnesses", 0, 2, 0]
