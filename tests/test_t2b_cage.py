"""Exact clause and parser gates for the production cage verifier.

The oracle consists of hand-specified rectangular half-planes and witnesses;
it does not use the proposer, Minkowski construction or production partitions.
"""
from copy import deepcopy
from fractions import Fraction as F
import json
from pathlib import Path

import pytest

from eab.kernel2d.se2_cage import SE2CageCertificate, verify_se2_cage
from t2b_cage_fixtures import (
    FORGERY_NAMES, capped_certificate, closed_disk_certificate, forged_case,
    instance_of, json_text, refined_rotated_certificate, repeat_winding,
)


@pytest.mark.parametrize("factory", [closed_disk_certificate, refined_rotated_certificate,
                                     capped_certificate])
def test_hand_built_certificate_is_accepted(factory):
    certificate = factory()
    result = verify_se2_cage(instance_of(certificate), certificate)
    assert result.valid and result.condition == "ACCEPTED", result


def test_certificate_json_exact_round_trip():
    original = capped_certificate()
    certificate = SE2CageCertificate.from_data(original)
    encoded = certificate.to_json()
    decoded = SE2CageCertificate.from_json(encoded)
    assert decoded.to_data() == certificate.to_data()
    assert json.loads(json_text(decoded.to_data())) == json.loads(json_text(original))
    assert decoded.to_json() == encoded
    assert verify_se2_cage(json_text(instance_of(original)), encoded).valid


@pytest.mark.parametrize("sign", [1, -1])
def test_even_nonzero_signed_winding_is_accepted(sign):
    certificate = repeat_winding(closed_disk_certificate())
    if sign == -1:
        for interval in certificate["intervals"]:
            interval["loop"].reverse()
            interval["witnesses"].reverse()
        for item in certificate["links"]:
            for loop in item["chain"]:
                loop.reverse()
            for row in item["witnesses"]:
                row.reverse()
    result = verify_se2_cage(instance_of(certificate), certificate)
    assert result.valid, "semantic: winding two is nonzero, not even parity outside"
    assert result.counts["winding_number"] == 2*sign


def test_initial_overlap_reaches_v6_after_all_previous_conditions():
    instance, certificate, expected = forged_case("initial_overlap")
    result = verify_se2_cage(instance, certificate)
    assert expected == result.condition == "V6" and not result.valid
    assert result.reason == "initial pose is not free"
    assert result.counts["barrier_segments"] == 8
    assert result.counts["connection_quadrilaterals"] == 8
    assert result.counts["initial_pairs"] == 4


@pytest.mark.parametrize("name", FORGERY_NAMES)
def test_named_forgery_has_contract_rejection_code(name):
    instance, certificate, expected = forged_case(name)
    result = verify_se2_cage(instance, certificate)
    assert not result.valid and result.condition == expected, (name, result)


@pytest.mark.parametrize("name", FORGERY_NAMES)
def test_archived_forgery_matches_exact_generated_input_and_rejection(name):
    path = Path(__file__).parent / "data" / "t2b_forgeries" / (name + ".json")
    saved = json.loads(path.read_text(encoding="utf-8"))
    instance, certificate, expected = forged_case(name)
    assert saved == json.loads(json_text({"name": name, "expected": expected,
                                         "instance": instance, "certificate": certificate}))
    result = verify_se2_cage(json.dumps(saved["instance"]), json.dumps(saved["certificate"]))
    assert not result.valid and result.condition == expected, (name, result)


@pytest.mark.parametrize("bad", ["0/1", "2/4", "-0", "00", "+1", "1/01", "1/0",
                                "1/1", " 1", "1 ", "1.0", "1e0", "１", "1/２"])
def test_noncanonical_rational_is_v0(bad):
    certificate = closed_disk_certificate()
    encoded = json.loads(json_text(certificate))
    encoded["radius"] = bad
    result = verify_se2_cage(json_text(instance_of(certificate)), json.dumps(encoded))
    assert not result.valid and result.condition == "V0", result


@pytest.mark.parametrize("token", ["1.0", "1e0", "-0", "true", "false", "-1"])
def test_noncanonical_integer_token_is_v0(token):
    certificate = closed_disk_certificate()
    encoded = json_text(certificate).replace('"start_interval": 1', '"start_interval": ' + token)
    result = verify_se2_cage(instance_of(certificate), encoded)
    assert not result.valid and result.condition == "V0", result


@pytest.mark.parametrize("change", ["duplicate", "unknown", "missing", "number", "nan",
                                   "infinity", "oversized", "boolean_index"])
def test_json_hygiene_is_v0(change):
    certificate = closed_disk_certificate()
    encoded = json_text(certificate)
    if change == "duplicate":
        encoded = encoded.replace('"radius": "3"', '"radius": "3", "radius": "3"', 1)
    elif change == "unknown":
        encoded = encoded.replace('"radius": "3"', '"radius": "3", "unknown": null', 1)
    elif change == "missing":
        encoded = encoded.replace('  "radius": "3",\n', "", 1)
    elif change == "number":
        encoded = encoded.replace('"radius": "3"', '"radius": 3', 1)
    elif change == "nan":
        encoded = encoded.replace('"radius": "3"', '"radius": NaN', 1)
    elif change == "infinity":
        encoded = encoded.replace('"radius": "3"', '"radius": Infinity', 1)
    elif change == "oversized":
        encoded = encoded.replace('"radius": "3"', '"radius": "' + "1" * 4097 + '"', 1)
    else:
        encoded = encoded.replace('"start_interval": 1', '"start_interval": true', 1)
    result = verify_se2_cage(instance_of(certificate), encoded)
    assert not result.valid and result.condition == "V0", result


def test_first_failed_condition_order_is_fixed():
    instance, certificate, _ = forged_case("false_barrier_witness")
    certificate["intervals"][0]["rho"] = F(-1)
    certificate["start_interval"] = 2
    assert verify_se2_cage(instance, certificate).condition == "CHAIN"
    certificate["start_interval"] = 1
    assert verify_se2_cage(instance, certificate).condition == "V1"
    certificate["intervals"][0]["rho"] = F(0)
    assert verify_se2_cage(instance, certificate).condition == "V4"
    certificate["radius"] = F(-3)
    assert verify_se2_cage(instance, certificate).condition == "V0"


def test_disk_only_intervals_require_no_artificial_rotation_shrink():
    certificate = closed_disk_certificate()
    assert all(interval["rho"] == 0 for interval in certificate["intervals"])
    assert verify_se2_cage(instance_of(certificate), certificate).valid


def test_explicit_zero_length_polyline_segments_are_allowed():
    certificate = closed_disk_certificate()
    for interval in certificate["intervals"]:
        interval["loop"].insert(1, deepcopy(interval["loop"][0]))
        interval["witnesses"].insert(0, deepcopy(interval["witnesses"][0]))
    for item in certificate["links"]:
        for loop in item["chain"]:
            loop.insert(1, deepcopy(loop[0]))
        item["witnesses"][0].insert(0, deepcopy(item["witnesses"][0][0]))
    assert verify_se2_cage(instance_of(certificate), certificate).valid
