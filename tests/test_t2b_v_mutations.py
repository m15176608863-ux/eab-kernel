"""Internal assertion mutations: semantic condition groups have teeth.

The mutation acts at the verifier's internal assertion boundary, not on its
returned dictionaries.  Each forged input first fails the expected condition
and then is accepted with that one condition group disabled.  This is a group
test, not a claim that logically redundant atomic assertions are independent.
"""

import json
from fractions import Fraction as F

import pytest

import t2b_independent_cage_verifier as verifier
from t2b_hand_cage_builder import build_hand_cages, build_low_room_cage
from test_t2b_v_geometry import constant_closed_cage, rectangle, seam_exact_forgery


def group_forgery(name, condition):
    if name == "low_room":
        instance, certificate = build_low_room_cage()
    else:
        instance, certificate = json.loads(json.dumps(build_hand_cages()[name]))
    if condition == "V0":
        ring = certificate["moving"]
        certificate["moving"] = ring[1:] + ring[:1]
    elif condition == "CHAIN":
        certificate["links"].pop()
    elif condition == "V1":
        if name == "low_room":
            certificate["intervals"][0]["rho"] = str(F(certificate["intervals"][0]["rho"]) / 2)
        else:
            certificate["intervals"][0]["rho"] = "-1"
    elif condition == "V2":
        if name == "low_room":
            certificate["intervals"][0]["pieces"][0]["polygon"] = rectangle(F(-7, 5), F(-9, 25), F(7, 5), F(9, 25))
        else:
            interval = certificate["intervals"][0]
            interval["rho"] = "3"
            interval["pieces"] = json.loads(json.dumps(interval["pieces"]))
            interval["pieces"].append({"kind": "rotated", "piece": 0,
                                       "polygon": rectangle(F(-1, 100), F(-1, 100), F(1, 100), F(1, 100))})
    elif condition == "V3":
        certificate["disk"]["radius"] = "2"
    elif condition == "V4":
        witness = certificate["intervals"][0]["witnesses"][0]
        witness[1] = (witness[1] + 2) % len(certificate["obstacle_pieces"])
    elif condition == "V5":
        link = certificate["links"][0]
        middle = json.loads(json.dumps(link["chain"][0]))
        middle[1] = ["0", "0"]
        link["chain"].insert(1, middle)
        link["witnesses"].append(json.loads(json.dumps(link["witnesses"][0])))
    elif condition == "V6":
        constant_closed_cage(certificate)
    else:
        raise AssertionError("unregistered semantic group")
    return instance, certificate


def mutation_parameters():
    cases = []
    for name in ("doorway", "windmill", "midpoint_wedges", "diamond_plates"):
        for condition in ("V0", "CHAIN", "V1", "V2", "V3", "V4", "V5", "V6"):
            cases.append((name, condition))
    cases.append(("low_room", "V1"))
    cases.append(("low_room", "V2"))
    return cases


@pytest.mark.parametrize("name,condition", mutation_parameters())
def test_each_applicable_semantic_group_has_an_internal_kill(monkeypatch, name, condition):
    instance, certificate = group_forgery(name, condition)
    original_result = verifier.verify_cage(instance, certificate)
    assert not original_result["valid"], original_result
    assert original_result["condition"] == condition, original_result
    original = verifier._require

    def disabled_condition(ok, check_id, actual_condition, where, reason):
        """Test-only internal assertion mutation, not a geometry helper."""
        if actual_condition != condition:
            return original(ok, check_id, actual_condition, where, reason)
        return None

    monkeypatch.setattr(verifier, "_require", disabled_condition)
    mutated_result = verifier.verify_cage(instance, certificate)
    assert mutated_result["valid"], mutated_result
    assert mutated_result["condition"] == "OK", mutated_result


def test_seam_chart_geometry_forgery_kills_wrong_chart_implementation(monkeypatch):
    instance, certificate = seam_exact_forgery(build_hand_cages())
    result = verifier.verify_cage(instance, certificate)
    assert result["condition"] == "V5", result
    original = verifier._reference

    def wrong_first_chart_at_seam(certificate, charts, kind, at, ref, state, path):
        """Inject I_1 at lambda_N and omit its mandatory range validation."""
        if kind == "links" and at == len(certificate["intervals"]) and ref[0] == "exact":
            chart = charts[0]
            parameter = certificate["chain"]["breakpoints"][at] - chart[0]
            polygon = verifier._rotated_ring(certificate["moving_pieces"][ref[1]],
                                             certificate["center"], parameter, chart[1])
            return verifier._world_ring(polygon, certificate["center"])
        return original(certificate, charts, kind, at, ref, state, path)

    monkeypatch.setattr(verifier, "_reference", wrong_first_chart_at_seam)
    mutated = verifier.verify_cage(instance, certificate)
    assert mutated["valid"], mutated
