"""Frozen v5 cages and refusal codes are replayed through two implementations.

The second oracle implements the lemma without production geometry imports.
Every independent verification reads both raw files through its load_json
entry, preserving duplicate-key and integer-token evidence. Instance comparison
uses independent shifted half-planes, not the production erosion algorithm.
Only historical fixture bytes are hashed; current source hashes and Git are
neither read nor asserted. No external evidence path is needed at runtime.
"""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

import pytest
import t2b_independent_cage_verifier as independent_module

from eab.kernel2d.se2_cage import verify_se2_cage
from t2b_cage_proposer import scientific_instance
from t2b_independent_cage_verifier import _load_result
from t2b_independent_instances import (
    OCTAGON, SQUARE, canonical_instance, dovetail_instance,
)


DATA = Path(__file__).parent / "data" / "t2b_dual_cases"
MANIFEST = json.loads((DATA / "manifest.json").read_text("utf-8"))
CASES = MANIFEST["cases"]


def test_dual_replay_payload_integrity_and_historical_provenance():
    assert MANIFEST["schema"] == "eab.t2b.dual-replay/1"
    assert len(CASES) == 15
    assert sum(case["kind"] == "truth" for case in CASES) == 5
    assert sum(case["kind"] == "lower" for case in CASES) == 10
    assert {case["case_id"] for case in CASES} == {
        "truth_diamond_plates", "truth_door_below", "truth_low_room",
        "truth_midpoint_wedges", "truth_windmill", "lower_d01", "lower_d02",
        "lower_d03", "lower_d04", "lower_d05", "lower_d06", "lower_d07",
        "lower_d08", "lower_k01", "lower_k02",
    }
    for case in CASES:
        assert case["producer"]["source_commit"]
        assert case["producer"]["tool_version"]
        for row in case["files"].values():
            assert hashlib.sha256((DATA / row["path"]).read_bytes()).hexdigest() == row["sha256"]


@pytest.mark.parametrize("case", CASES, ids=[case["case_id"] for case in CASES])
def test_all_five_truth_and_ten_table_lower_cages_have_dual_acceptance(case):
    instance_path = DATA / case["files"]["instance"]["path"]
    certificate_path = DATA / case["files"]["certificate"]["path"]
    production = verify_se2_cage(instance_path.read_text("utf-8"),
                                certificate_path.read_text("utf-8"))
    independent = _load_result(instance_path, certificate_path)
    assert production.valid and production.condition == "ACCEPTED", production
    assert independent["valid"] and independent["condition"] == "OK", independent
    assert production.counts["barrier_segments"] > 0
    if case["case_id"] == "truth_low_room":
        certificate = json.loads(certificate_path.read_text("utf-8"))
        assert certificate["chain"]["kind"] == "capped"
        assert len(certificate["caps"]) == 2


@pytest.mark.parametrize("kind,expected_count", [("truth", 5), ("lower", 10)])
def test_truth_and_science_rechecks_use_json_text_entry(monkeypatch, kind, expected_count):
    """Spy on real replays, not source spelling or an already decoded dict."""
    production_original = verify_se2_cage
    loader_original = independent_module.load_json
    production_calls = []
    independent_loads = []

    def production_text_only(instance, certificate):
        assert type(instance) is str and type(certificate) is str
        production_calls.append((instance, certificate))
        return production_original(instance, certificate)

    def independent_raw_loader(path):
        independent_loads.append(path)
        return loader_original(path)

    monkeypatch.setitem(globals(), "verify_se2_cage", production_text_only)
    monkeypatch.setattr(independent_module, "load_json", independent_raw_loader)
    expected_paths = []
    for case in CASES:
        if case["kind"] != kind:
            continue
        instance_path = DATA / case["files"]["instance"]["path"]
        certificate_path = DATA / case["files"]["certificate"]["path"]
        expected_paths.extend((instance_path, certificate_path))
        test_all_five_truth_and_ten_table_lower_cages_have_dual_acceptance(case)
    assert len(production_calls) == expected_count
    assert independent_loads == expected_paths


@pytest.mark.parametrize("name,condition", [
    ("undersized_radius", "V0"), ("cross_chart_interval", "CHAIN"),
    ("small_rho", "V1"), ("missed_contracted_edge", "V2"),
    ("negative_host_halfplane", "V3"), ("merely_touching_barrier", "V4"),
    ("wrong_cap_side", "V5"), ("initial_overlap", "V6"),
])
def test_fixed_forgery_subset_has_identical_validity_and_refusal_codes(tmp_path, name, condition):
    wrapper = Path(__file__).parent / "data" / "t2b_forgeries" / (name + ".json")
    data = json.loads(wrapper.read_text("utf-8"))
    instance_path = tmp_path / "instance.json"
    certificate_path = tmp_path / "certificate.json"
    instance_path.write_text(json.dumps(data["instance"]), encoding="utf-8")
    certificate_path.write_text(json.dumps(data["certificate"]), encoding="utf-8")
    production = verify_se2_cage(instance_path.read_text("utf-8"),
                                certificate_path.read_text("utf-8"))
    independent = _load_result(instance_path, certificate_path)
    assert not production.valid and not independent["valid"]
    assert production.condition == independent["condition"] == condition == data["expected"]


@pytest.mark.parametrize("change", ["duplicate", "negative_zero", "decimal", "exponent"])
def test_dual_raw_json_parser_path_does_not_erase_invalid_tokens(tmp_path, change):
    original = DATA / "lower_d01"
    encoded = (original / "certificate.json").read_text("utf-8")
    data = json.loads(encoded)
    token = '"start_interval": ' + str(data["start_interval"])
    assert token in encoded
    replacement = token
    if change == "duplicate":
        replacement = token + ", " + token
    elif change == "negative_zero":
        replacement = '"start_interval": -0'
    elif change == "decimal":
        replacement = '"start_interval": 1.0'
    elif change == "exponent":
        replacement = '"start_interval": 1e0'
    encoded = encoded.replace(token, replacement, 1)
    certificate_path = tmp_path / "raw_certificate.json"
    certificate_path.write_text(encoded, encoding="utf-8")
    instance_path = original / "instance.json"
    production = verify_se2_cage(instance_path.read_text("utf-8"), encoded)
    independent = _load_result(instance_path, certificate_path)
    assert not production.valid and not independent["valid"]
    assert production.condition == independent["condition"] == "V0"


@pytest.mark.parametrize("name,wk,wn,kernel,wall_erosion", [
    ("d01", F(5, 2), F(3, 2), SQUARE, 0),
    ("d02", F(7, 2), F(3, 2), SQUARE, 0),
    ("d03", F(5, 2), F(1), SQUARE, 0),
    ("d04", F(5, 2), F(1), SQUARE, 1),
    ("d05", F(7, 2), F(3, 2), OCTAGON, 0),
    ("d06", F(3), F(1), OCTAGON, 0),
    ("d07", F(5, 2), F(3, 2), OCTAGON, 0),
    ("d08", F(3), F(3, 2), OCTAGON, 1),
])
@pytest.mark.parametrize("endpoint", ["delta_cage", "delta_escape"])
def test_eight_dovetail_instances_match_independent_erosion_at_both_bounds(
        name, wk, wn, kernel, wall_erosion, endpoint):
    delta = F(MANIFEST["science_endpoints"][name][endpoint])
    production, center = scientific_instance(name, delta)
    independent = dovetail_instance(wk, wn, kernel, wall_erosion, delta)
    assert center == (F(0), F(1))
    assert canonical_instance(production) == canonical_instance(independent)
    if endpoint == "delta_cage":
        frozen = json.loads((DATA / ("lower_" + name) / "instance.json").read_text("utf-8"))
        assert canonical_instance(frozen) == canonical_instance(independent)
