"""Finite T2c proposal gates; only the unchanged two verifiers decide cages.

Independent full-cage oracle: the v5 text loader/verifier implements rational
SAT, ring checks and winding without production geometry imports. The local
U-shaped cap gate separately checks strict axis-aligned box inequalities.
"""
from fractions import Fraction as F
import time

import pytest

from eab.kernel2d.se2_cage import verify_se2_cage
from eab.kernel2d.translation_space import translation_component
from t2a_truth_geometry import rectangle
import t2b_independent_cage_verifier as independent
from t2b_truth_geometry_prod import truth_instance
import t2c_cage_proposer as proposer


def test_rotation_only_full_circle_is_dual_verified_with_no_caps_or_disk(tmp_path):
    instance, center = truth_instance("diamond_plates")
    result = proposer.propose_cage(instance, center=center, modes=("closed",), mixed=False,
                                   initial_intervals=16,
                                   resources=proposer.CageResources(max_seconds=20))
    assert result["status"] == "CERTIFIED_CAGE", result
    certificate = result["certificate"]
    assert certificate["chain"]["kind"] == "closed" and not certificate["caps"]
    assert certificate["chain"]["breakpoints"][-1]-certificate["chain"]["breakpoints"][0] == 4
    assert certificate["disk"] is None
    assert all(piece["kind"] == "rotated" for interval in certificate["intervals"]
               for piece in interval["pieces"])
    assert len(certificate["links"]) == len(certificate["intervals"])
    a, b = tmp_path/"i.json", tmp_path/"c.json"
    proposer.old.write_json(a, instance)
    proposer.old.write_json(b, certificate)
    production = verify_se2_cage(a.read_text("utf-8"), b.read_text("utf-8"))
    alternate = independent._load_result(a, b)
    assert production.valid and alternate["valid"], (production, alternate)
    assert translation_component(instance["moving"], instance["obstacles"]).status == "TRAPPED_TRANSLATION"


def test_low_room_has_mixed_kernels_distinct_loops_and_nonorigin_caps(tmp_path):
    instance, center = truth_instance("low_room")
    result = proposer.propose_cage(instance, center=center, modes=("capped",),
                                   halfwidths=(F(1, 23),), initial_intervals=2,
                                   resources=proposer.CageResources(max_seconds=20))
    assert result["status"] == "CERTIFIED_CAGE", result
    certificate = result["certificate"]
    assert len(certificate["caps"]) == 2
    assert len({interval["loop"] for interval in certificate["intervals"]}) > 1
    assert all({piece["kind"] for piece in interval["pieces"]} == {"disk", "rotated"}
               for interval in certificate["intervals"])
    assert any(cap["chain"][-1][0] != (0, 0) for cap in certificate["caps"])
    assert any(len(cap["chain"]) > 2 for cap in certificate["caps"])
    a, b = tmp_path/"i.json", tmp_path/"c.json"
    proposer.old.write_json(a, instance)
    proposer.old.write_json(b, certificate)
    alternate = independent._load_result(a, b)
    assert alternate["valid"], alternate
    assert verify_se2_cage(a.read_text("utf-8"), b.read_text("utf-8")).valid


def test_nonstar_shaped_cap_contracts_in_multiple_stages_without_origin():
    # The three exact boxes form a U, not a star-shaped region. No point can
    # directly see both upper arms. Translation removes the coordinate origin.
    boxes = ((F(-1), F(-1), F(5), F(3, 2)),
             (F(-1), F(-1), F(3, 2), F(5)),
             (F(5, 2), F(-1), F(5), F(5)))
    shift = (F(11), F(-7))
    cells = []
    translated_boxes = []
    for j, (x0, y0, x1, y1) in enumerate(boxes):
        bounds = (x0+shift[0], y0+shift[1], x1+shift[0], y1+shift[1])
        translated_boxes.append(bounds)
        polygon = rectangle(*bounds)
        box, rows = proposer.old._indexed_cell(polygon)
        cells.append((polygon, box, rows, [["exact", 0], j]))
    loop = tuple((F(x, 2)+shift[0], F(y, 2)+shift[1]) for x, y in
                 ((0, 0), (8, 0), (8, 8), (6, 8), (6, 2), (2, 2), (2, 8), (0, 8), (0, 0)))
    loop = proposer.old._refine_loop(loop, 2)
    result, reason = proposer._cap(loop, cells, proposer.CageResources(), time.perf_counter()+10)
    assert result is not None, reason
    assert len(result["chain"]) > 2
    assert len(set(result["chain"][-1])) == 1
    assert result["chain"][-1][0] != (0, 0)
    assert result["chain"][0] == loop
    assert len(result["witnesses"]) == len(result["chain"])-1
    for first, following, row in zip(result["chain"], result["chain"][1:], result["witnesses"]):
        assert first[0] == first[-1] and following[0] == following[-1]
        assert len(row) == len(first)-1
        for k, reference in enumerate(row):
            x0, y0, x1, y1 = translated_boxes[reference[1]]
            for x, y in (first[k], first[k+1], following[k], following[k+1]):
                assert x0 < x < x1 and y0 < y < y1


def test_monotone_alignment_retains_edges_and_pads_repeated_vertices():
    first = ((F(-2), F(-1)), (F(2), F(-1)), (F(1), F(2)), (F(-2), F(-1)))
    second = proposer.old._refine_loop(first, 2)
    aligned = proposer._aligned_loops((first, second), proposer.CageResources())
    assert len(aligned[0]) == len(aligned[1])
    assert set(first) <= set(aligned[0]) and set(second) <= set(aligned[1])
    assert any(a == b for a, b in zip(aligned[0], aligned[0][1:]))
    for source, changed in zip((first, second), aligned):
        nonzero = [(a, b) for a, b in zip(changed, changed[1:]) if a != b]
        assert set(nonzero) == set(zip(source, source[1:]))


def test_alignment_uses_stable_geometric_anchor_not_lexicographic_jump():
    first = tuple((F(x), F(y)) for x, y in ((-4, 0), (-3, -3), (3, -3), (3, 2), (-4, 0)))
    second = tuple((F(x), F(y)) for x, y in ((-3, 0), (-4, -3), (3, -3), (3, 2), (-3, 0)))
    aligned = proposer._aligned_loops((first, second), proposer.CageResources())
    assert aligned[0][0] == (F(-4), F(0))
    assert aligned[1][0] == (F(-3), F(0))


def test_adaptive_split_uses_failure_interval_without_changing_other_knots():
    knots = (F(-1), F(0), F(1), F(3))
    assert proposer._split(knots, {"interval": 1}, {}) == (F(-1), F(0), F(1, 2), F(1), F(3))


@pytest.mark.parametrize("resources", [
    proposer.CageResources(max_seconds=0), proposer.CageResources(max_intervals=1),
    proposer.CageResources(max_cells=1), proposer.CageResources(max_loop_vertices=2),
    proposer.CageResources(max_cap_steps=0),
])
def test_limits_never_return_escape_or_a_certificate(resources):
    instance, center = truth_instance("diamond_plates")
    result = proposer.propose_cage(instance, center=center, resources=resources)
    assert result["status"] == "UNPROVED" and result["certificate"] is None
    assert "ESCAP" not in result["status"]


def test_construction_only_status_is_not_a_certificate_claim():
    instance, center = truth_instance("diamond_plates")
    result = proposer.propose_cage(instance, center=center, verify=False)
    assert result["status"] == "PROPOSAL_UNVERIFIED"
    assert verify_se2_cage(instance, result["certificate"]).valid


def test_far_translated_asymmetric_low_room_keeps_a_valid_cage():
    source, center = truth_instance("low_room")
    shift = (F(1000), F(-37))
    instance = {"moving": tuple((x+shift[0], y+shift[1]) for x, y in source["moving"]),
                "obstacles": tuple(tuple((x+shift[0], y+shift[1]) for x, y in ring)
                                   for ring in source["obstacles"])}
    result = proposer.propose_cage(instance, center=(center[0]+shift[0], center[1]+shift[1]),
                                   modes=("capped",), halfwidths=(F(1, 23),), initial_intervals=2,
                                   resources=proposer.CageResources(max_seconds=20))
    assert result["status"] == "CERTIFIED_CAGE", result
    assert verify_se2_cage(instance, result["certificate"]).valid
    assert source["moving"] != instance["moving"]


def test_final_observed_overrun_discards_an_already_verified_candidate(monkeypatch):
    instance, center = truth_instance("diamond_plates")
    clock = {"armed": False, "reads": 0}
    verified = []

    def fake_clock():
        if clock["armed"]:
            clock["reads"] += 1
            return 2 if clock["reads"] >= 2 else 0
        return 0

    def verification_then_delay(source, certificate):
        result = verify_se2_cage(source, certificate)
        verified.append(result.valid)
        clock["armed"] = True
        return result

    monkeypatch.setattr(proposer.time, "perf_counter", fake_clock)
    monkeypatch.setattr(proposer, "verify_se2_cage", verification_then_delay)
    result = proposer.propose_cage(instance, center=center, modes=("disk",),
                                   resources=proposer.CageResources(max_seconds=1))
    assert verified == [True]
    assert result["diagnostic"]["generation_seconds"] == 2
    assert result["status"] == "UNPROVED" and result["certificate"] is None
    assert "verification" not in result
    assert result["attempts"][-1] == {"mode": "resource_limit", "reason": "elapsed_time_limit"}
