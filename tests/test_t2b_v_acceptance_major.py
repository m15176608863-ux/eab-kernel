"""Five supplied high-room forgeries that independently kill source mutants.

Each fixture is self-contained JSON from the 2026-10-26 acceptance inputs.
The unmodified verifier must reject at the named semantic check.  Acceptance
by the corresponding one-edit mutant is reproduced externally; this module
does not load mutant tools, depend on external evidence, or alter the verifier.
"""

import json
from pathlib import Path

import t2b_independent_cage_verifier as verifier


def acceptance_pair(prefix):
    directory = Path(__file__).parent / "data/t2b_acceptance"
    instance = json.loads((directory / (prefix + ".instance.json")).read_text(encoding="utf-8"))
    certificate = json.loads((directory / (prefix + ".cert.json")).read_text(encoding="utf-8"))
    return instance, certificate


def exact_rejection(prefix, condition, check):
    instance, certificate = acceptance_pair(prefix)
    result = verifier.verify_cage(instance, certificate)
    assert result["valid"] is False, result
    assert result["condition"] == condition, result
    assert result["where"]["check"] == check, result
    return certificate, result


def test_A17_growing_homotopy_vertex_count_cannot_hide_reversed_tail():
    certificate, result = exact_rejection("major_A17", "V0", "homotopy_vertex_count")
    chain = certificate["caps"][0]["chain"]
    assert len(chain[1]) > len(chain[0])
    assert result["where"]["path"] == ["certificate", "caps", 0, "chain", 1]


def test_V503_last_quadrilateral_cannot_hide_a_free_chord_sweep():
    certificate, result = exact_rejection("major_V503", "V5", "homotopy_strict")
    last = len(certificate["caps"][0]["witnesses"][0]) - 1
    assert result["where"]["path"] == ["certificate", "caps", 0, "witnesses", 0, last]


def test_V304_last_invariant_disk_vertex_is_not_an_unchecked_spike():
    certificate, result = exact_rejection("major_V304", "V3", "disk_polygon")
    last = len(certificate["disk"]["polygon"]) - 1
    assert result["where"]["path"] == ["certificate", "disk", "polygon", last]


def test_V203_last_rotated_kernel_vertex_is_not_an_unchecked_spike():
    certificate, result = exact_rejection("major_V203", "V2", "rotated_containment")
    last = len(certificate["intervals"][0]["pieces"][0]["polygon"]) - 1
    assert result["where"]["path"] == ["certificate", "intervals", 0, "pieces", 0, "polygon", last]


def test_V105_disk_first_mixed_kernel_still_requires_rotation_bound():
    certificate, result = exact_rejection("major_V105", "V1", "rotation_bound")
    pieces = certificate["intervals"][0]["pieces"]
    assert pieces[0]["kind"] == "disk"
    assert pieces[1]["kind"] == "rotated"
    assert result["where"]["path"] == ["certificate", "intervals", 0, "rho"]
