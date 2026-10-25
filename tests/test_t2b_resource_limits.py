"""A cap budget below the minimum construction step count is UNPROVED.

These public proposer checks distinguish an exhausted finite search from an
exception or a geometric verdict. The positive boundary goes through both cage
verifiers, with the independent implementation loading raw JSON files.
"""
import json

import pytest

from eab.kernel2d.se2_cage import verify_se2_cage
from t2b_cage_proposer import CageResources, encode, propose_cage
from t2b_independent_cage_verifier import _load_result
from t2b_truth_geometry_prod import truth_instance


@pytest.mark.parametrize("limit", [0, 1, 7])
def test_low_room_cap_budget_below_eight_is_unproved_not_an_exception(limit):
    instance, center = truth_instance("low_room")
    result = propose_cage(instance, center=center,
                          resources=CageResources(max_cap_steps=limit))
    assert result["status"] == "UNPROVED"
    assert result["certificate"] is None
    assert result["attempts"][-1] == {
        "mode": "resource_limit", "reason": "homotopy_step_limit",
    }


def test_low_room_eight_step_cap_boundary_remains_dually_accepted(tmp_path):
    instance, center = truth_instance("low_room")
    result = propose_cage(instance, center=center,
                          resources=CageResources(max_cap_steps=8))
    assert result["status"] == "CERTIFIED_CAGE"
    certificate = result["certificate"]
    assert certificate is not None
    assert verify_se2_cage(instance, certificate).valid
    assert certificate["chain"]["kind"] == "capped"
    assert len(certificate["caps"]) == 2
    assert all(len(cap["chain"]) == 9 for cap in certificate["caps"])
    instance_path = tmp_path / "instance.json"
    certificate_path = tmp_path / "certificate.json"
    instance_path.write_text(json.dumps(encode(instance)), encoding="utf-8")
    certificate_path.write_text(json.dumps(encode(certificate)), encoding="utf-8")
    independent = _load_result(instance_path, certificate_path)
    assert independent["valid"] and independent["condition"] == "OK", independent
