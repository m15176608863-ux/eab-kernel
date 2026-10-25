"""Multiple-defect diagnostics follow actual JSON data occurrence order.

These gates do not add a second validity oracle. Every ordering example is
already rejected by the unchanged condition logic; only the first offending
data location is compared. Missing keys anchor at their containing object.
"""
from fractions import Fraction as F
import json

import pytest

from eab.kernel2d.se2_cage import verify_se2_cage
from t2b_cage_fixtures import (
    capped_certificate, closed_disk_certificate, exact_copy, instance_of,
    json_text, rectangle,
)


@pytest.mark.parametrize("first", ["radius", "moving", "moving_pieces"])
def test_v0_cross_field_order_uses_json_occurrence(first):
    certificate = closed_disk_certificate()
    instance = instance_of(certificate)
    certificate["radius"] = F(-3)
    certificate["moving"] = certificate["moving"][1:] + certificate["moving"][:1]
    certificate["moving_pieces"][0].reverse()
    certificate = {first: certificate[first], **{k: v for k, v in certificate.items() if k != first}}
    result = verify_se2_cage(json_text(instance), json_text(certificate))
    assert not result.valid and result.condition == "V0"
    assert result.where.startswith("$." + first), result


@pytest.mark.parametrize("later", ["rational", "integer", "unknown", "nonfinite", "duplicate"])
def test_v0_later_json_hygiene_cannot_hide_earlier_ring_geometry(later):
    certificate = closed_disk_certificate()
    certificate["moving"].reverse()
    instance = instance_of(certificate)
    data = json.loads(json_text(certificate))
    if later == "rational":
        data["radius"] = "01"
    elif later == "integer":
        data["start_interval"] = True
    elif later == "unknown":
        data["unknown"] = None
    encoded = json.dumps(data)
    if later == "nonfinite":
        encoded = encoded.replace('"radius": "3"', '"radius": NaN')
    elif later == "duplicate":
        encoded = encoded.replace('"radius": "3"', '"radius": "3", "radius": "3"')
    result = verify_se2_cage(instance, encoded)
    assert not result.valid and result.condition == "V0"
    assert result.where == "$.moving", result


@pytest.mark.parametrize("first", ["unknown", "radius", "moving"])
def test_v0_present_unknown_key_and_bad_number_respect_their_positions(first):
    certificate = closed_disk_certificate()
    certificate["moving"].reverse()
    instance = instance_of(certificate)
    certificate["radius"] = "bad-rational"
    certificate["unknown"] = None
    certificate = {first: certificate[first], **{k: v for k, v in certificate.items() if k != first}}
    result = verify_se2_cage(instance, json_text(certificate))
    assert not result.valid and result.condition == "V0"
    assert result.where == "$." + first, result


@pytest.mark.parametrize("first", ["radius", "polygon", "host"])
def test_v0_nested_disk_field_order(first):
    certificate = closed_disk_certificate()
    certificate["disk"]["radius"] = F(-2)
    certificate["disk"]["host"] = 100
    certificate["disk"]["polygon"].reverse()
    disk = certificate["disk"]
    certificate["disk"] = {first: disk[first], **{k: v for k, v in disk.items() if k != first}}
    result = verify_se2_cage(instance_of(certificate), json_text(certificate))
    assert result.condition == "V0" and result.where == "$.disk." + first, result


@pytest.mark.parametrize("first", ["witnesses", "loop"])
def test_v0_nested_index_and_closed_polyline_order(first):
    certificate = closed_disk_certificate()
    interval = certificate["intervals"][0]
    interval["witnesses"][0][0] = 100
    interval["loop"][-1] = [F(-2), F(-3)]
    certificate["intervals"][0] = {first: interval[first], **{k: v for k, v in interval.items() if k != first}}
    result = verify_se2_cage(instance_of(certificate), json_text(certificate))
    assert result.condition == "V0"
    assert result.where.startswith("$.intervals[0]." + first), result


def test_v0_earlier_bad_index_survives_later_malformed_witness():
    certificate = closed_disk_certificate()
    certificate["intervals"][0]["witnesses"][0][0] = 100
    certificate["intervals"][0]["witnesses"][1][0] = "wrong-type"
    result = verify_se2_cage(instance_of(certificate), json_text(certificate))
    assert result.condition == "V0" and result.where == "$.intervals[0].witnesses[0][0]", result


@pytest.mark.parametrize("first", ["polygon", "host"])
def test_v3_disk_host_and_polygon_order(first):
    certificate = closed_disk_certificate()
    certificate["disk"]["radius"] = F(3)
    certificate["disk"]["polygon"] = rectangle(-4, -4, 4, 4)
    disk = certificate["disk"]
    certificate["disk"] = {first: disk[first], **{k: v for k, v in disk.items() if k != first}}
    result = verify_se2_cage(instance_of(certificate), json_text(certificate))
    assert result.condition == "V3" and result.where == "$.disk." + first, result


@pytest.mark.parametrize("first", ["links", "caps"])
def test_v5_links_and_caps_follow_top_level_json_order(first):
    certificate = capped_certificate()
    interval = certificate["intervals"][0]
    interval["rho"] = F(1, 6)
    certificate["chain"]["breakpoints"] = [F(-1, 10), F(0), F(1, 10)]
    certificate["intervals"] = [exact_copy(interval), exact_copy(interval)]
    certificate["caps"][1]["at"] = 2
    certificate["links"] = [{"at": 1,
        "chain": [exact_copy(interval["loop"]), exact_copy(interval["loop"])],
        "witnesses": [[[["exact", 0], index] for index in (0, 3, 1, 2)]]}]
    assert verify_se2_cage(instance_of(certificate), certificate).valid
    certificate["links"][0]["witnesses"][0][0][1] = 1
    certificate["caps"][0]["witnesses"][0][0][1] = 1
    certificate = {first: certificate[first], **{k: v for k, v in certificate.items() if k != first}}
    result = verify_se2_cage(instance_of(certificate), json_text(certificate))
    assert result.condition == "V5" and result.where.startswith("$." + first + "[0]"), result


def test_valid_certificate_field_permutations_preserve_all_counts():
    certificate = capped_certificate()
    instance = instance_of(certificate)
    baseline = verify_se2_cage(instance, certificate)
    reordered = {key: certificate[key] for key in reversed(certificate)}
    reordered["intervals"] = [{key: interval[key] for key in reversed(interval)}
                              for interval in certificate["intervals"]]
    result = verify_se2_cage(instance, json_text(reordered))
    assert baseline.valid and result.valid and result.counts == baseline.counts


@pytest.mark.parametrize("first", ["chain", "start_interval", "links", "caps"])
def test_chain_condition_uses_top_level_json_order(first):
    certificate = closed_disk_certificate()
    certificate["chain"]["breakpoints"][1] = F(3, 2)
    certificate["start_interval"] = 2
    certificate["links"].pop()
    certificate["caps"] = [exact_copy(capped_certificate()["caps"][0])]
    certificate = {first: certificate[first], **{k: v for k, v in certificate.items() if k != first}}
    result = verify_se2_cage(instance_of(certificate), json_text(certificate))
    assert result.condition == "CHAIN" and result.where.startswith("$." + first), result


@pytest.mark.parametrize("first", ["moving_pieces", "start_interval"])
def test_v6_initial_freedom_and_winding_use_data_order(first):
    certificate = closed_disk_certificate()
    obstacle = rectangle(-1, -1, 1, 1)
    certificate["obstacles"].append(obstacle)
    certificate["obstacle_pieces"].append({"obstacle": 4, "ring": exact_copy(obstacle)})
    # A loop followed by its reverse is strictly blocked but has winding zero.
    for interval in certificate["intervals"]:
        loop, witnesses = interval["loop"], interval["witnesses"]
        interval["loop"] = [*loop, *reversed(loop[:-1])]
        interval["witnesses"] = [*witnesses, *reversed(witnesses)]
    for link in certificate["links"]:
        loop = certificate["intervals"][0]["loop"]
        link["chain"] = [exact_copy(loop), exact_copy(loop)]
        row = link["witnesses"][0]
        link["witnesses"] = [[*row, *reversed(row)]]
    certificate = {first: certificate[first], **{k: v for k, v in certificate.items() if k != first}}
    result = verify_se2_cage(instance_of(certificate), json_text(certificate))
    assert result.condition == "V6" and result.where.startswith("$." + first), result
