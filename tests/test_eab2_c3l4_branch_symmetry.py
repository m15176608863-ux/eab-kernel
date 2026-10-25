"""L4 enrichment is proof-symmetric, not an unchecked semantic-field waiver.

The actual-side witness is a live repaired certificate, replayed by the
independent raw-geometry K checker. The conservative side retains the same
independently valid L3 bracket but has no exact threshold or derivative proof.
"""
import copy
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from eab2_c3l4_diff import (compare_sensitivity, directional_values, exact_wire,
    expected_channel, formal_cases, referee_seed, refresh_case)
from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.sensitivity import evaluate_sensitivity2
from eab.kernel2d.statics import CriticalParameter2, critical_parameter
import eab.kernel2d.branch_certificate as branch_engine


@pytest.mark.parametrize("defect", (None, "upper_ray", "invalid_direction", "unproved_exact_jet", "unproved_s", "unproved_upper"))
def test_cpp_only_l4_branch_enrichment_replays_real_k_proof_before_normalizing_fields(defect):
    source = next(formal_cases({"g1_unreversed_t2"}))
    source["queries"] = [(i, q) for i, q in source["queries"] if q["result"]["parameter"] == "t"]
    case = refresh_case(source)
    query = copy.deepcopy(next(q for _, q in case["queries"] if q["result"]["parameter"] == "t"))
    actual_base = copy.deepcopy(case["bases"]["critical"]["result"])
    actual = expected_channel(query)
    assert actual["result"]["branch_certificate"] is not None
    assert actual["result"]["quality"] == "exact_jet"

    conservative = copy.deepcopy(actual_base)
    for field in ("exact_threshold", "attained", "threshold_certificate", "threshold_proof", "threshold_proof_reason"):
        conservative[field] = None
    case["bases"]["critical"]["result"] = conservative
    # Exercise the real public Python missing-threshold behavior; no invented
    # no-value result is used to make an enrichment exception pass.
    unavailable = CriticalParameter2("OK", conservative["mathematical_status"],
                                    validity_conditions=tuple(conservative["validity_conditions"]))
    query["result"] = exact_wire(evaluate_sensitivity2(unavailable, None, parameter="t",
                                 validity_conditions=query["declared_validity_conditions"]))
    query["seed"] = query["threshold_mu_seed"] = None
    query["directional_values"] = directional_values(query["result"])
    assert query["result"]["reason"] == "exact_threshold_basis_and_seed_required"
    assert query["result"]["quality"] == "approximate"

    if defect == "upper_ray":
        ray = actual["result"]["branch_certificate"]["forward"]["upper"]["ray"]
        ray["numerators"] = [[] for _ in ray["numerators"]]
        message = "normalization"
    elif defect == "invalid_direction":
        query["direction_domain"]["positive"] = False
        message = "outside valid direction"
    elif defect in ("unproved_exact_jet", "unproved_s", "unproved_upper"):
        certificate = copy.deepcopy(actual["result"]["branch_certificate"])
        for direction in ("forward", "reverse"):
            certificate[direction].update(status="unresolved", reason="threshold_branch_certificate_unavailable",
                                           s=None, lower=None, upper=None, candidate_branches=[])
        actual["result"] = copy.deepcopy(query["result"])
        actual["result"]["branch_certificate"] = certificate
        # Keep the aggregate reason consistent so this negative gate reaches
        # its intended unproved-value/quality assertion, not an envelope check.
        actual["result"]["reason"] = "threshold_branch_certificate_unavailable"
        if defect == "unproved_exact_jet":
            actual["result"]["quality"] = "exact_jet"
            message = "uncertified branch cannot claim exact_jet"
        else:
            certificate["forward"]["s" if defect == "unproved_s" else "upper"] = "0/1"
            message = "unproved branch must not carry"

    dispositions = []
    if defect is not None:
        with pytest.raises((ValueError, AssertionError), match=message):
            compare_sensitivity(case, actual_base, query, actual, dispositions)
        assert dispositions == []  # Reject before any proof-availability waiver.
    else:
        delta, floor = compare_sensitivity(case, actual_base, query, actual, dispositions)
        assert delta == [] and floor["checked"] == 0 and floor["exceptions"] == []
        assert len(dispositions) == 1
        row = dispositions[0]
        assert row["classification"] == "verified_cpp_only_threshold_branch_enrichment"
        assert row["exact_threshold"] == actual_base["exact_threshold"] and row["attained"] is False
        assert row["python"]["right_derivative"] is None and row["cpp"]["right_derivative"] == "1/1"
        assert "original_geometry_complete_polynomials_K" in row["verification"]


def test_zero_candidate_budget_normal_threshold_is_unresolved_not_a_single_basis_fallback(monkeypatch):
    case = next(formal_cases({"g1_unreversed_t2"}))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == "t")
    contacts = assemble_contact_set2(case["model"])
    critical = critical_parameter(case["model"], contact_set=contacts, mu_max=1, max_steps=24)
    seed = referee_seed(critical.threshold_certificate.problem, query["geometry_seed"])
    monkeypatch.setattr(branch_engine, "CANDIDATE_LIMIT", 0)
    result = evaluate_sensitivity2(critical, seed, parameter="t")
    assert result.differentiability == "unresolved" and result.quality == "approximate"
    assert result.reason == "threshold_branch_certificate_unavailable"
    assert result.directional_derivative is result.right_derivative is result.left_derivative is None
    for direction in ("forward", "reverse"):
        branch = result.branch_certificate[direction]
        assert branch["status"] == "unresolved" and branch["s"] is None
        assert branch["candidate_count"] == branch["attempts"] == 0
        assert branch["lower"] is branch["upper"] is None and branch["candidate_branches"] == []
