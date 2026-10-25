"""Owner truth and finite proposal gates; no failed search proves escape.

The truth geometry comes from the owner's explicit rings and T2a's independent
support-line formulas. Accepted candidates are always checked by the production
cage verifier, plus the separate existing translation or escape verifier.
"""
from fractions import Fraction as F
import time

import pytest

from eab.kernel2d.se2 import SE2Motion
from eab.kernel2d.se2_cage import verify_se2_cage
from eab.kernel2d.se2_paths import SE2EscapePath, verify_se2_escape
from eab.kernel2d.translation_space import translation_component
from t2a_truth_geometry import doorway_motion_specs
from t2b_cage_proposer import CageResources, propose_cage, scientific_instance
import t2b_cage_proposer as proposer
from t2b_truth_geometry_prod import truth_instance


def _escape(instance, motions):
    poses = [instance["moving"]]
    for motion in motions:
        poses.append(tuple(motion.endpoint(p) for p in poses[-1]))
    return verify_se2_escape(instance["moving"], instance["obstacles"],
                             SE2EscapePath(tuple(poses), tuple(motions)),
                             ((F(0), F(0)), (F(0), F(100))))


@pytest.mark.parametrize("name,delta", [
    ("doorway", F(127, 1024)), ("windmill", F(0)),
    ("midpoint_wedges", F(0)), ("diamond_plates", F(0)),
])
def test_truth_invariant_disk_proposals_are_checked_cages_and_translation_trapped(name, delta):
    instance, center = truth_instance(name, delta)
    result = propose_cage(instance, center=center, disk_only=True)
    assert result["status"] == "CERTIFIED_CAGE"
    certificate = result["certificate"]
    assert verify_se2_cage(instance, certificate).valid
    assert certificate["chain"]["kind"] == "closed" and not certificate["caps"]
    assert all(p["kind"] == "disk" for i in certificate["intervals"] for p in i["pieces"])
    assert translation_component(instance["moving"], instance["obstacles"]).status == "TRAPPED_TRANSLATION"


@pytest.mark.parametrize("delta", [F(1, 8), F(129, 1024)])
def test_doorway_equal_and_above_escape_and_no_proposed_cage(delta):
    instance, center = truth_instance("doorway", delta)
    escaped = _escape(instance, tuple(SE2Motion(*spec) for spec in doorway_motion_specs()))
    assert escaped.valid and escaped.ray_verification.valid
    caged = propose_cage(instance, center=center, resources=CageResources(max_seconds=5, max_intervals=4))
    assert caged["status"] == "UNPROVED" and caged["certificate"] is None


def test_low_room_requires_rotated_capped_chain_not_invariant_disk():
    instance, center = truth_instance("low_room")
    disk = propose_cage(instance, center=center, disk_only=True)
    assert disk["status"] == "UNPROVED" and disk["certificate"] is None
    result = propose_cage(instance, center=center)
    assert result["status"] == "CERTIFIED_CAGE"
    certificate = result["certificate"]
    assert verify_se2_cage(instance, certificate).valid
    assert certificate["chain"]["kind"] == "capped"
    assert {cap["at"] for cap in certificate["caps"]} == {0, len(certificate["intervals"])}
    assert any(p["kind"] == "rotated" for i in certificate["intervals"] for p in i["pieces"])
    assert translation_component(instance["moving"], instance["obstacles"]).status == "TRAPPED_TRANSLATION"
    assert not _escape(instance, (SE2Motion(F(1)), SE2Motion(F(0), (F(0), F(9))))).valid


def test_high_room_has_verified_quarter_turn_and_upward_escape_not_a_cage():
    instance, center = truth_instance("high_room")
    escaped = _escape(instance, (SE2Motion(F(1)), SE2Motion(F(0), (F(0), F(9)))))
    assert escaped.valid and escaped.checked_segments == 2
    assert escaped.ray_verification.valid
    result = propose_cage(instance, center=center, resources=CageResources(max_seconds=5, max_intervals=4))
    assert result["status"] == "UNPROVED" and result["certificate"] is None


def test_proposer_resource_limit_is_unproved_and_input_rings_are_not_rewritten():
    instance, center = truth_instance("low_room")
    moving, obstacles = instance["moving"], instance["obstacles"]
    result = propose_cage(instance, center=center, resources=CageResources(max_seconds=0))
    assert result["status"] == "UNPROVED" and result["certificate"] is None
    assert instance["moving"] is moving and instance["obstacles"] is obstacles
    assert result["attempts"][-1]["mode"] == "resource_limit"


def test_unverified_construction_never_claims_certified_cage():
    instance, center = truth_instance("windmill")
    result = propose_cage(instance, center=center, verify=False)
    assert result["status"] == "PROPOSAL_UNVERIFIED"
    assert result["certificate"] is not None


def test_scientific_instances_keep_fixed_center_across_erosion_and_use_input_generator():
    zero, center0 = scientific_instance("d07", F(0))
    eroded, center1 = scientific_instance("d07", F(1, 8))
    assert center0 == center1 == (F(0), F(1))
    assert zero["moving"] != eroded["moving"]
    assert zero["obstacles"] == eroded["obstacles"]
    result = propose_cage(eroded, center=center1, disk_only=True)
    assert result["status"] == "CERTIFIED_CAGE"
    assert result["certificate"]["moving"] == eroded["moving"]


def test_distinct_interval_loops_have_real_four_point_connection_chain():
    instance, center = truth_instance("low_room")
    parts = proposer._partition(instance["moving"])
    obstacles = tuple({"obstacle": j, "ring": piece}
                      for j, ring in enumerate(instance["obstacles"])
                      for piece in proposer._partition(ring))
    base = proposer._base_certificate(instance, center, parts, obstacles,
                                      proposer._disk(parts, center))
    certificate, reason = proposer._capped_candidate(
        base, F(1, 23), 2, CageResources(), time.perf_counter()+10,
        individual_only=True)
    assert reason == "individual_loops_four_point_links_and_caps_proposed"
    assert certificate is not None and verify_se2_cage(instance, certificate).valid
    left, right = (interval["loop"] for interval in certificate["intervals"])
    assert left != right, "the fallback must exercise genuinely different barriers"
    assert len(left) == len(right)
    link = certificate["links"][0]
    assert link["chain"][0] == left and link["chain"][-1] == right
    assert len(link["witnesses"]) == len(link["chain"])-1
    assert all(len(row) == len(left)-1 for row in link["witnesses"])


def test_common_loop_parameter_subdivision_preserves_all_source_vertices():
    first = ((F(-1), F(-1)), (F(1), F(-1)), (F(1), F(1)), (F(-1), F(1)), (F(-1), F(-1)))
    second = proposer._refine_loop(first, 3)
    aligned = proposer._aligned_loops((first, second))
    assert len(aligned[0]) == len(aligned[1])
    assert set(first).issubset(aligned[0]) and set(second).issubset(aligned[1])
    assert all(loop[0] == loop[-1] for loop in aligned)


def test_adaptive_bisection_splits_the_diagnosed_interval_only():
    knots = (F(-1, 2), F(0), F(1, 4), F(1, 2))
    following = proposer._bisect_failed_interval(knots, {"interval": 1})
    assert following == (F(-1, 2), F(0), F(1, 8), F(1, 4), F(1, 2))


def test_disk_closed_chain_cannot_exceed_the_interval_budget():
    instance, center = truth_instance("windmill")
    limited = propose_cage(instance, center=center, disk_only=True,
                           resources=CageResources(max_intervals=1))
    assert limited["status"] == "UNPROVED" and limited["certificate"] is None
    allowed = propose_cage(instance, center=center, disk_only=True,
                           resources=CageResources(max_intervals=2))
    assert allowed["status"] == "CERTIFIED_CAGE"
    assert len(allowed["certificate"]["intervals"]) == 2


@pytest.mark.parametrize("resources", [
    CageResources(max_loop_vertices=8), CageResources(max_cells=3),
    CageResources(max_cap_steps=0),
])
def test_disk_candidate_obeys_loop_cell_and_homotopy_limits(resources):
    instance, center = truth_instance("windmill")
    result = propose_cage(instance, center=center, disk_only=True, resources=resources)
    assert result["status"] == "UNPROVED" and result["certificate"] is None


def test_verified_disk_cannot_be_accepted_after_the_cooperative_deadline(monkeypatch):
    from eab.kernel2d import se2_cage as cage_verifier

    clock = {"now": 0.0}
    verified = []

    def delayed_verification(instance, certificate):
        checked = verify_se2_cage(instance, certificate)
        verified.append(checked.valid)
        clock["now"] = 2.0
        return checked

    monkeypatch.setattr(proposer.time, "perf_counter", lambda: clock["now"])
    monkeypatch.setattr(cage_verifier, "verify_se2_cage", delayed_verification)
    instance, center = truth_instance("windmill")
    result = propose_cage(instance, center=center, disk_only=True,
                          resources=CageResources(max_seconds=1.0))
    assert verified == [True], "the candidate is geometrically valid before the budget decision"
    assert result["status"] == "UNPROVED" and result["certificate"] is None
    assert result["attempts"][-1] == {"mode": "resource_limit", "reason": "elapsed_time_limit"}
