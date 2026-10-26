"""Frozen small-subset replay: complete results and exact instance identity.

Real replay invokes unchanged production and independent checkers. Identity
negative controls are explicitly metadata/integrity guards, not purported
mathematical-defect injections. No stored acceptance flag replaces replay.
"""
from dataclasses import asdict
from fractions import Fraction as F
import copy
import gzip
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from eab.adapters.tia2d import tolerance_knob
from eab.kernel2d.se2 import SE2Motion
from eab.kernel2d.se2_cage import verify_se2_cage
from eab.kernel2d.se2_paths import SE2EscapePath, verify_se2_escape
from eab.kernel2d.translation_space import translation_component
import t2a_oracle_audit as independent_escape
import t2b_independent_cage_verifier as independent_cage
import tests.t2d_knob_family_exact as exact
import tests.t2d_sections_exact as sections
import tests.t2d_critical_escape_exact as critical_escape


DATA = Path(__file__).parent / "data/t2d"
SELECTED = (
    "N4_square_cage_k6", "N8_octagon_cage_k8", "N16_K16_cage_k10",
    "N4_octagon_escape_k20", "N8_K16_escape_k20", "N32_K16_escape_k20",
    "N8_square_mixed_escape", "N16_square_mixed_escape", "N32_square_mixed_escape",
)
SLOW_REPLAY_NODES = (
    "tests/test_t2d_replay.py::test_t2d_N32_K16_escape_real_replay",
    "tests/test_t2d_replay.py::test_t2d_square_N8_mixed_path_real_replay",
    "tests/test_t2d_replay.py::test_t2d_square_N16_mixed_path_real_replay",
    "tests/test_t2d_replay.py::test_t2d_square_N32_mixed_path_real_replay",
)


def rational(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, F)):
        raise TypeError("replay requires exact rational JSON numbers")
    return F(value)


def ring(points):
    return tuple(tuple(rational(value) for value in point) for point in points)


def cyclic(points):
    start = min(range(len(points)), key=lambda index: points[index])
    return points[start:]+points[:start]


def algebraic(record):
    return exact.Surd(rational(record["a"]), rational(record["b"]), rational(record["q"]))


def read_index():
    return json.loads((DATA / "index.json").read_text(encoding="utf8"))


# File/codec/hash operations are test-driver scaffolding, not arithmetic.
# A missing formal fixture is never skipped: each actual test fails read_index.
PAYLOADS = {}
if (DATA / "index.json").is_file():
    for _row in read_index()["cases"]:
        _packed = (DATA / _row["file"]).read_bytes()
        assert len(_packed) == _row["bytes"] <= 1_000_000, "packed replay size changed"
        assert hashlib.sha256(_packed).hexdigest() == _row["sha256"], "packed replay integrity changed"
        _unpacked = gzip.decompress(_packed)
        assert len(_unpacked) == _row["decoded_bytes"], "decoded replay size changed"
        assert hashlib.sha256(_unpacked).hexdigest() == _row["decoded_sha256"], "decoded replay integrity changed"
        PAYLOADS[_row["id"]] = json.loads(_unpacked)


def read_payload(row):
    payload = PAYLOADS[row["id"]]
    assert payload["id"] == row["id"], "replay identity changed"
    assert (payload["N"], payload["element"], payload["kind"]) == (row["N"], row["element"], row["kind"])
    assert payload["metadata"].get("k") == row["k"], "dyadic offset identity changed"
    return payload

def verify_metadata(payload):
    n, element, kind = payload["N"], payload["element"], payload["kind"]
    metadata = payload["metadata"]
    critical = exact.family_values(n, element)["delta"]
    verified = rational(metadata["verified_delta"])
    # Convex K containing zero gives delta1*K subset delta2*K. Erosion
    # reverses this inclusion; this is the exact directed-transfer premise.
    element_hull = exact.convex_hull(exact.element_vertices(element))
    assert all(a[0]*b[1]-a[1]*b[0] > 0 for a, b in zip(element_hull, element_hull[1:]+element_hull[:1])), \
        "nested erosion transfer requires the origin inside convex K"
    assert algebraic(metadata["critical"]) == critical, "critical metadata differs from exact family"
    if "target_delta" not in metadata:
        assert kind == "escape" and element == "square" and n in (8, 16, 32)
        assert critical < verified < critical+F(1, 4096), "mixed rational upper bracket changed"
        assert metadata["direct_rational_instance_verification"] is True
        assert metadata["deserialization_performed"] is False
        return verified
    target = algebraic(metadata["target_delta"])
    assert isinstance(metadata["k"], int) and not isinstance(metadata["k"], bool) and metadata["k"] > 0
    epsilon = F(1, 1 << metadata["k"])
    assert rational(metadata["epsilon"]) == epsilon
    assert metadata["direct_algebraic_instance_verification"] is False
    transfer = metadata["transfer"]
    assert transfer["kind"] == "erosion_nested_inclusion_with_fixed_obstacles"
    assert transfer["obstacles_unchanged"] is True
    if kind == "cage":
        assert target == critical-epsilon and target < verified < critical, "directed cage proxy order changed"
        assert (transfer["verified_vs_target"], transfer["moving_subset"], transfer["conclusion"]) == (
            ">", "verified_in_target", "cage_transfers_to_larger_target")
    else:
        assert kind == "escape"
        assert target == critical+epsilon and critical < verified < target, "directed escape proxy order changed"
        assert (transfer["verified_vs_target"], transfer["moving_subset"], transfer["conclusion"]) == (
            "<", "target_in_verified", "escape_transfers_to_smaller_target")
    assert abs(target-verified) < epsilon/1024, "proxy rounding consumed the declared margin"
    lower, upper = (rational(value) for value in metadata["sqrt_bounds"])
    q = rational(metadata["critical"]["q"])
    assert 0 <= lower < upper and lower*lower <= q < upper*upper
    assert (lower, upper) == exact.Surd(0, 1, q).bounds(64), "proxy root-enclosure prescription changed"
    a, b = rational(metadata["critical"]["a"]), rational(metadata["critical"]["b"])
    bounds = sorted((a+b*lower, a+b*upper))
    assert tuple(rational(value) for value in metadata["critical_bounds"]) == tuple(bounds)
    assert verified == (bounds[1]-epsilon if kind == "cage" else bounds[0]+epsilon), "proxy rational construction changed"
    return verified


def verify_instance_identity(payload):
    delta = verify_metadata(payload)
    n, element = payload["N"], payload["element"]
    raw = tolerance_knob(segments=n)
    assert raw["moving"] == exact.family_geometry(n)["A"], "raw family differs from production generator"
    expected_obstacles = critical_escape.truth_obstacles(n)
    assert tuple(cyclic(points) for points in raw["obstacles"]) == tuple(cyclic(points) for points in expected_obstacles)
    expected_moving = sections.eroded_polygon(n, element, delta)
    instance = json.loads(payload["instance_text"])
    assert cyclic(ring(instance["moving"])) == expected_moving, "verified delta is not bound to actual erosion vertices"
    assert tuple(cyclic(ring(points)) for points in instance["obstacles"]) == tuple(
        cyclic(points) for points in expected_obstacles), "wall geometry identity changed"
    if payload["kind"] == "escape":
        candidate = json.loads(payload["candidate_text"])
        assert cyclic(ring(candidate["moving"])) == expected_moving, "candidate body identity changed"
        assert tuple(cyclic(ring(points)) for points in candidate["obstacles"]) == tuple(
            cyclic(points) for points in expected_obstacles), "candidate wall identity changed"
    return instance


def compare_results(actual, expected):
    assert json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True), \
        "full verification result identity changed (including counts, labels and exact times)"


def verify_neck_disk_binding(payload, certificate):
    """Family-specific half-unit neck binding, not a generic verifier rule."""
    disk, circle = certificate["disk"], payload["circle"]
    radius = rational(disk["radius"])
    assert radius > F(1, 2), "family cage disk must be wider than the half-unit neck"
    assert tuple(rational(value) for value in certificate["center"]) == (0, 1)
    polygon = ring(disk["polygon"])
    assert len(polygon) == circle["vertices"] == 4*circle["quarter_samples"]
    assert rational(circle["radius"]) == radius
    assert all(x*x+y*y == radius*radius for x, y in polygon), "inner polygon vertices left the claimed disk circle"
    squared_distances = []
    for a, b in zip(polygon, polygon[1:]+polygon[:1]):
        cross = a[0]*b[1]-a[1]*b[0]
        assert cross > 0, "inner polygon must surround its disk center"
        dx, dy = b[0]-a[0], b[1]-a[1]
        squared_distances.append(cross*cross/(dx*dx+dy*dy))
    minimum = min(squared_distances)
    assert minimum == rational(circle["inradius_squared"]), "inner polygon inradius metadata changed"
    assert F(1, 4) < rational(circle["inradius_lower_bound_squared"]) <= minimum, \
        "family inner polygon must retain the strict half-neck margin"


def test_t2d_replay_manifest_scope_provenance_and_no_same_delta_contradictions():
    index = read_index()
    assert index["schema"] == "eab.t2d.fixed-replay/1"
    assert tuple(row["id"] for row in index["cases"]) == SELECTED
    assert index["producer"]["source_commit"] and index["producer"]["tool_version"]
    assert index["producer"]["source_manifest_sha256"] and index["producer"]["evidence_manifest_sha256"]
    assert index["timing_exclusions"] == ["wall-clock diagnostic timings only"]
    assert index["direct_algebraic_instance_verification"] is False
    assert sum(row["bytes"] for row in index["cases"]) < 5_000_000
    ledger = index["complete_case_ledger"]
    assert len(ledger) == 93
    identities = [(row["N"], row["element"], rational(row["verified_delta"])) for row in ledger]
    assert len(set(identities)) == len(identities), "same rational delta has conflicting certificates"
    for row in ledger:
        critical = exact.family_values(row["N"], row["element"])["delta"]
        delta = rational(row["verified_delta"])
        assert row["production_valid"] and row["independent_valid"]
        assert (delta < critical) if row["kind"] == "cage" else (delta > critical)
    assert sum(row["kind"] == "cage" for row in ledger) == 36
    assert sum(row["kind"] == "escape" for row in ledger) == 57


def test_t2d_frozen_identity_and_exact_directed_transfer():
    for row in read_index()["cases"]:
        verify_instance_identity(read_payload(row))


def test_t2d_N4_cage_real_replay_and_translation(tmp_path):
    rows = read_index()["cases"]
    assert sum(row["id"] == "N4_square_cage_k6" for row in rows) == 1, "required replay case missing or duplicated"
    for row in rows:
        if row["id"] == "N4_square_cage_k6":
            payload = read_payload(row)
            directory = tmp_path
            instance = verify_instance_identity(payload)
            instance_path, certificate_path = directory / "instance.json", directory / "certificate.json"
            instance_path.write_bytes(payload["instance_text"].encode("utf8"))
            certificate_path.write_bytes(payload["certificate_text"].encode("utf8"))
            production = verify_se2_cage(payload["instance_text"], payload["certificate_text"])
            seen = []
            original = independent_cage.load_json

            def observe_load(path):
                seen.append(path)
                return original(path)

            with patch.object(independent_cage, "load_json", observe_load):
                independent = independent_cage._load_result(instance_path, certificate_path)
            assert seen == [instance_path, certificate_path], "independent cage bypassed text load_json entry"
            compare_results(json.loads(json.dumps({"production": asdict(production), "independent": independent}, default=str)), payload["expected"])
            assert production.valid and independent["valid"]
            assert production.condition == "ACCEPTED" and independent["condition"] == "OK"
            certificate = json.loads(payload["certificate_text"])
            assert certificate["chain"]["kind"] == "closed" and certificate["caps"] == []
            assert certificate["disk"] is not None
            verify_neck_disk_binding(payload, certificate)
            assert all(piece == {"kind": "disk"} for interval in certificate["intervals"] for piece in interval["pieces"])
            translation = translation_component(ring(instance["moving"]), tuple(ring(points) for points in instance["obstacles"]))
            compare_results(json.loads(json.dumps(asdict(translation), default=str)), payload["translation_result"])
            assert translation.status == "TRAPPED_TRANSLATION"


def test_t2d_N8_octagon_cage_real_replay(tmp_path):
    rows = read_index()["cases"]
    assert sum(row["id"] == "N8_octagon_cage_k8" for row in rows) == 1, "required replay case missing or duplicated"
    for row in rows:
        if row["id"] == "N8_octagon_cage_k8":
            payload = read_payload(row)
            directory = tmp_path
            instance = verify_instance_identity(payload)
            instance_path, certificate_path = directory / "instance.json", directory / "certificate.json"
            instance_path.write_bytes(payload["instance_text"].encode("utf8"))
            certificate_path.write_bytes(payload["certificate_text"].encode("utf8"))
            production = verify_se2_cage(payload["instance_text"], payload["certificate_text"])
            seen = []
            original = independent_cage.load_json

            def observe_load(path):
                seen.append(path)
                return original(path)

            with patch.object(independent_cage, "load_json", observe_load):
                independent = independent_cage._load_result(instance_path, certificate_path)
            assert seen == [instance_path, certificate_path], "independent cage bypassed text load_json entry"
            compare_results(json.loads(json.dumps({"production": asdict(production), "independent": independent}, default=str)), payload["expected"])
            assert production.valid and independent["valid"]
            assert production.condition == "ACCEPTED" and independent["condition"] == "OK"
            certificate = json.loads(payload["certificate_text"])
            assert certificate["chain"]["kind"] == "closed" and certificate["caps"] == []
            assert certificate["disk"] is not None
            verify_neck_disk_binding(payload, certificate)
            assert all(piece == {"kind": "disk"} for interval in certificate["intervals"] for piece in interval["pieces"])
            translation = translation_component(ring(instance["moving"]), tuple(ring(points) for points in instance["obstacles"]))
            compare_results(json.loads(json.dumps(asdict(translation), default=str)), payload["translation_result"])
            assert translation.status == "TRAPPED_TRANSLATION"


def test_t2d_N16_K16_cage_real_replay(tmp_path):
    rows = read_index()["cases"]
    assert sum(row["id"] == "N16_K16_cage_k10" for row in rows) == 1, "required replay case missing or duplicated"
    for row in rows:
        if row["id"] == "N16_K16_cage_k10":
            payload = read_payload(row)
            directory = tmp_path
            instance = verify_instance_identity(payload)
            instance_path, certificate_path = directory / "instance.json", directory / "certificate.json"
            instance_path.write_bytes(payload["instance_text"].encode("utf8"))
            certificate_path.write_bytes(payload["certificate_text"].encode("utf8"))
            production = verify_se2_cage(payload["instance_text"], payload["certificate_text"])
            seen = []
            original = independent_cage.load_json

            def observe_load(path):
                seen.append(path)
                return original(path)

            with patch.object(independent_cage, "load_json", observe_load):
                independent = independent_cage._load_result(instance_path, certificate_path)
            assert seen == [instance_path, certificate_path], "independent cage bypassed text load_json entry"
            compare_results(json.loads(json.dumps({"production": asdict(production), "independent": independent}, default=str)), payload["expected"])
            assert production.valid and independent["valid"]
            assert production.condition == "ACCEPTED" and independent["condition"] == "OK"
            certificate = json.loads(payload["certificate_text"])
            assert certificate["chain"]["kind"] == "closed" and certificate["caps"] == []
            assert certificate["disk"] is not None
            verify_neck_disk_binding(payload, certificate)
            assert all(piece == {"kind": "disk"} for interval in certificate["intervals"] for piece in interval["pieces"])
            translation = translation_component(ring(instance["moving"]), tuple(ring(points) for points in instance["obstacles"]))
            compare_results(json.loads(json.dumps(asdict(translation), default=str)), payload["translation_result"])
            assert translation.status == "TRAPPED_TRANSLATION"


def test_t2d_N4_octagon_escape_real_replay():
    rows = read_index()["cases"]
    assert sum(row["id"] == "N4_octagon_escape_k20" for row in rows) == 1, "required replay case missing or duplicated"
    for row in rows:
        if row["id"] == "N4_octagon_escape_k20":
            payload = read_payload(row)
            verify_instance_identity(payload)
            candidate = json.loads(payload["candidate_text"])
            moving, obstacles = ring(candidate["moving"]), tuple(ring(points) for points in candidate["obstacles"])
            poses, motions, specs = [moving], [], []
            for piece in candidate["pieces"]:
                assert ring(piece["start"]) == poses[-1], "piece continuity changed"
                spec = (rational(piece["u1"]), tuple(rational(x) for x in piece["translation"]),
                        tuple(rational(x) for x in piece["center"]))
                specs.append(spec)
                motions.append(SE2Motion(*spec))
                poses.append(ring(piece["end"]))
            ray = ring(candidate["ray_path"])
            production = verify_se2_escape(moving, obstacles, SE2EscapePath(tuple(poses), tuple(motions)), ray)
            independent = independent_escape.validate_escape_segments(moving, obstacles, tuple(specs), ray)
            compare_results(json.loads(json.dumps({"production": asdict(production), "independent": independent}, default=str)), payload["expected"])
            assert production.valid and production.ray_verification.valid and independent["valid"]
            assert independent["infinite_ray_verified"] is False, "finite independent oracle must not claim infinite-tail verification"
            endpoint = ring(independent["se2_endpoint"])
            bottom, top = min(y for _, y in endpoint), max(y for points in obstacles for _, y in points)
            assert len(ray) == 2 and ray[0] == (0, 0) and ray[1][0] == 0 and ray[1][1] > 0
            assert bottom > top, "independent endpoint does not certify an unobstructed upward infinite tail"
            tail = {"valid": True, "lowest_endpoint_y": bottom, "highest_obstacle_y": top,
                    "strict_vertical_clearance": bottom-top,
                    "method": "independent_se2_endpoint_plus_exact_upward_halfplane", "old_oracle_infinite_ray_verified": False}
            compare_results(json.loads(json.dumps(tail, default=str)), payload["independent_tail"])


def test_t2d_N8_K16_escape_real_replay():
    rows = read_index()["cases"]
    assert sum(row["id"] == "N8_K16_escape_k20" for row in rows) == 1, "required replay case missing or duplicated"
    for row in rows:
        if row["id"] == "N8_K16_escape_k20":
            payload = read_payload(row)
            verify_instance_identity(payload)
            candidate = json.loads(payload["candidate_text"])
            moving, obstacles = ring(candidate["moving"]), tuple(ring(points) for points in candidate["obstacles"])
            poses, motions, specs = [moving], [], []
            for piece in candidate["pieces"]:
                assert ring(piece["start"]) == poses[-1], "piece continuity changed"
                spec = (rational(piece["u1"]), tuple(rational(x) for x in piece["translation"]),
                        tuple(rational(x) for x in piece["center"]))
                specs.append(spec)
                motions.append(SE2Motion(*spec))
                poses.append(ring(piece["end"]))
            ray = ring(candidate["ray_path"])
            production = verify_se2_escape(moving, obstacles, SE2EscapePath(tuple(poses), tuple(motions)), ray)
            independent = independent_escape.validate_escape_segments(moving, obstacles, tuple(specs), ray)
            compare_results(json.loads(json.dumps({"production": asdict(production), "independent": independent}, default=str)), payload["expected"])
            assert production.valid and production.ray_verification.valid and independent["valid"]
            assert independent["infinite_ray_verified"] is False, "finite independent oracle must not claim infinite-tail verification"
            endpoint = ring(independent["se2_endpoint"])
            bottom, top = min(y for _, y in endpoint), max(y for points in obstacles for _, y in points)
            assert len(ray) == 2 and ray[0] == (0, 0) and ray[1][0] == 0 and ray[1][1] > 0
            assert bottom > top, "independent endpoint does not certify an unobstructed upward infinite tail"
            tail = {"valid": True, "lowest_endpoint_y": bottom, "highest_obstacle_y": top,
                    "strict_vertical_clearance": bottom-top,
                    "method": "independent_se2_endpoint_plus_exact_upward_halfplane", "old_oracle_infinite_ray_verified": False}
            compare_results(json.loads(json.dumps(tail, default=str)), payload["independent_tail"])


def test_t2d_N32_K16_escape_real_replay():
    rows = read_index()["cases"]
    assert sum(row["id"] == "N32_K16_escape_k20" for row in rows) == 1, "required replay case missing or duplicated"
    for row in rows:
        if row["id"] == "N32_K16_escape_k20":
            payload = read_payload(row)
            verify_instance_identity(payload)
            candidate = json.loads(payload["candidate_text"])
            moving, obstacles = ring(candidate["moving"]), tuple(ring(points) for points in candidate["obstacles"])
            poses, motions, specs = [moving], [], []
            for piece in candidate["pieces"]:
                assert ring(piece["start"]) == poses[-1], "piece continuity changed"
                spec = (rational(piece["u1"]), tuple(rational(x) for x in piece["translation"]),
                        tuple(rational(x) for x in piece["center"]))
                specs.append(spec)
                motions.append(SE2Motion(*spec))
                poses.append(ring(piece["end"]))
            ray = ring(candidate["ray_path"])
            production = verify_se2_escape(moving, obstacles, SE2EscapePath(tuple(poses), tuple(motions)), ray)
            independent = independent_escape.validate_escape_segments(moving, obstacles, tuple(specs), ray)
            compare_results(json.loads(json.dumps({"production": asdict(production), "independent": independent}, default=str)), payload["expected"])
            assert production.valid and production.ray_verification.valid and independent["valid"]
            assert independent["infinite_ray_verified"] is False, "finite independent oracle must not claim infinite-tail verification"
            endpoint = ring(independent["se2_endpoint"])
            bottom, top = min(y for _, y in endpoint), max(y for points in obstacles for _, y in points)
            assert len(ray) == 2 and ray[0] == (0, 0) and ray[1][0] == 0 and ray[1][1] > 0
            assert bottom > top, "independent endpoint does not certify an unobstructed upward infinite tail"
            tail = {"valid": True, "lowest_endpoint_y": bottom, "highest_obstacle_y": top,
                    "strict_vertical_clearance": bottom-top,
                    "method": "independent_se2_endpoint_plus_exact_upward_halfplane", "old_oracle_infinite_ray_verified": False}
            compare_results(json.loads(json.dumps(tail, default=str)), payload["independent_tail"])


def test_t2d_square_N8_mixed_path_real_replay():
    rows = read_index()["cases"]
    assert sum(row["id"] == "N8_square_mixed_escape" for row in rows) == 1, "required replay case missing or duplicated"
    for row in rows:
        if row["id"] == "N8_square_mixed_escape":
            payload = read_payload(row)
            verify_instance_identity(payload)
            candidate = json.loads(payload["candidate_text"])
            moving, obstacles = ring(candidate["moving"]), tuple(ring(points) for points in candidate["obstacles"])
            poses, motions, specs = [moving], [], []
            for piece in candidate["pieces"]:
                assert ring(piece["start"]) == poses[-1], "piece continuity changed"
                spec = (rational(piece["u1"]), tuple(rational(x) for x in piece["translation"]),
                        tuple(rational(x) for x in piece["center"]))
                specs.append(spec)
                motions.append(SE2Motion(*spec))
                poses.append(ring(piece["end"]))
            ray = ring(candidate["ray_path"])
            production = verify_se2_escape(moving, obstacles, SE2EscapePath(tuple(poses), tuple(motions)), ray)
            independent = independent_escape.validate_escape_segments(moving, obstacles, tuple(specs), ray)
            compare_results(json.loads(json.dumps({"production": asdict(production), "independent": independent}, default=str)), payload["expected"])
            assert production.valid and production.ray_verification.valid and independent["valid"]
            assert independent["infinite_ray_verified"] is False, "finite independent oracle must not claim infinite-tail verification"
            endpoint = ring(independent["se2_endpoint"])
            bottom, top = min(y for _, y in endpoint), max(y for points in obstacles for _, y in points)
            assert len(ray) == 2 and ray[0] == (0, 0) and ray[1][0] == 0 and ray[1][1] > 0
            assert bottom > top, "independent endpoint does not certify an unobstructed upward infinite tail"
            tail = {"valid": True, "lowest_endpoint_y": bottom, "highest_obstacle_y": top,
                    "strict_vertical_clearance": bottom-top,
                    "method": "independent_se2_endpoint_plus_exact_upward_halfplane", "old_oracle_infinite_ray_verified": False}
            compare_results(json.loads(json.dumps(tail, default=str)), payload["independent_tail"])


def test_t2d_square_N16_mixed_path_real_replay():
    rows = read_index()["cases"]
    assert sum(row["id"] == "N16_square_mixed_escape" for row in rows) == 1, "required replay case missing or duplicated"
    for row in rows:
        if row["id"] == "N16_square_mixed_escape":
            payload = read_payload(row)
            verify_instance_identity(payload)
            candidate = json.loads(payload["candidate_text"])
            moving, obstacles = ring(candidate["moving"]), tuple(ring(points) for points in candidate["obstacles"])
            poses, motions, specs = [moving], [], []
            for piece in candidate["pieces"]:
                assert ring(piece["start"]) == poses[-1], "piece continuity changed"
                spec = (rational(piece["u1"]), tuple(rational(x) for x in piece["translation"]),
                        tuple(rational(x) for x in piece["center"]))
                specs.append(spec)
                motions.append(SE2Motion(*spec))
                poses.append(ring(piece["end"]))
            ray = ring(candidate["ray_path"])
            production = verify_se2_escape(moving, obstacles, SE2EscapePath(tuple(poses), tuple(motions)), ray)
            independent = independent_escape.validate_escape_segments(moving, obstacles, tuple(specs), ray)
            compare_results(json.loads(json.dumps({"production": asdict(production), "independent": independent}, default=str)), payload["expected"])
            assert production.valid and production.ray_verification.valid and independent["valid"]
            assert independent["infinite_ray_verified"] is False, "finite independent oracle must not claim infinite-tail verification"
            endpoint = ring(independent["se2_endpoint"])
            bottom, top = min(y for _, y in endpoint), max(y for points in obstacles for _, y in points)
            assert len(ray) == 2 and ray[0] == (0, 0) and ray[1][0] == 0 and ray[1][1] > 0
            assert bottom > top, "independent endpoint does not certify an unobstructed upward infinite tail"
            tail = {"valid": True, "lowest_endpoint_y": bottom, "highest_obstacle_y": top,
                    "strict_vertical_clearance": bottom-top,
                    "method": "independent_se2_endpoint_plus_exact_upward_halfplane", "old_oracle_infinite_ray_verified": False}
            compare_results(json.loads(json.dumps(tail, default=str)), payload["independent_tail"])


def test_t2d_square_N32_mixed_path_real_replay():
    rows = read_index()["cases"]
    assert sum(row["id"] == "N32_square_mixed_escape" for row in rows) == 1, "required replay case missing or duplicated"
    for row in rows:
        if row["id"] == "N32_square_mixed_escape":
            payload = read_payload(row)
            verify_instance_identity(payload)
            candidate = json.loads(payload["candidate_text"])
            moving, obstacles = ring(candidate["moving"]), tuple(ring(points) for points in candidate["obstacles"])
            poses, motions, specs = [moving], [], []
            for piece in candidate["pieces"]:
                assert ring(piece["start"]) == poses[-1], "piece continuity changed"
                spec = (rational(piece["u1"]), tuple(rational(x) for x in piece["translation"]),
                        tuple(rational(x) for x in piece["center"]))
                specs.append(spec)
                motions.append(SE2Motion(*spec))
                poses.append(ring(piece["end"]))
            ray = ring(candidate["ray_path"])
            production = verify_se2_escape(moving, obstacles, SE2EscapePath(tuple(poses), tuple(motions)), ray)
            independent = independent_escape.validate_escape_segments(moving, obstacles, tuple(specs), ray)
            compare_results(json.loads(json.dumps({"production": asdict(production), "independent": independent}, default=str)), payload["expected"])
            assert production.valid and production.ray_verification.valid and independent["valid"]
            assert independent["infinite_ray_verified"] is False, "finite independent oracle must not claim infinite-tail verification"
            endpoint = ring(independent["se2_endpoint"])
            bottom, top = min(y for _, y in endpoint), max(y for points in obstacles for _, y in points)
            assert len(ray) == 2 and ray[0] == (0, 0) and ray[1][0] == 0 and ray[1][1] > 0
            assert bottom > top, "independent endpoint does not certify an unobstructed upward infinite tail"
            tail = {"valid": True, "lowest_endpoint_y": bottom, "highest_obstacle_y": top,
                    "strict_vertical_clearance": bottom-top,
                    "method": "independent_se2_endpoint_plus_exact_upward_halfplane", "old_oracle_infinite_ray_verified": False}
            compare_results(json.loads(json.dumps(tail, default=str)), payload["independent_tail"])


def test_t2d_replay_delta_metadata_mutation_is_an_identity_guard():
    payload = copy.deepcopy(read_payload(read_index()["cases"][0]))
    payload["metadata"]["verified_delta"] = str(rational(payload["metadata"]["verified_delta"])+F(1, 2))
    with unittest.TestCase().assertRaisesRegex(AssertionError, "proxy order"):
        verify_instance_identity(payload)


def test_t2d_replay_instance_vertex_mutation_is_an_identity_guard():
    payload = copy.deepcopy(read_payload(read_index()["cases"][0]))
    instance = json.loads(payload["instance_text"])
    instance["moving"][0][0] = str(rational(instance["moving"][0][0])+F(1, 101))
    payload["instance_text"] = json.dumps(instance)
    with unittest.TestCase().assertRaisesRegex(AssertionError, "actual erosion vertices"):
        verify_instance_identity(payload)


def test_t2d_replay_result_count_mutation_is_an_integrity_guard():
    payload = read_payload(read_index()["cases"][3])
    changed = copy.deepcopy(payload["expected"])
    changed["production"]["checked_pairs"] += 1
    with unittest.TestCase().assertRaisesRegex(AssertionError, "full verification result"):
        compare_results(payload["expected"], changed)


def test_t2d_replay_json_boolean_coordinate_is_rejected_before_conversion():
    with unittest.TestCase().assertRaisesRegex(TypeError, "exact rational"):
        ring([[True, "1"]])


def test_t2d_replay_slow_tier_mapping_preserves_fast_actual_replays():
    policy = json.loads((DATA.parent.parent / "slow_tests.json").read_text(encoding="utf8"))
    observed = tuple(node for node in policy["slow_functions"] if node.startswith("tests/test_t2d_replay.py::"))
    assert observed == SLOW_REPLAY_NODES and len(observed) == 4
    assert "tests/test_t2d_replay.py::test_t2d_N4_cage_real_replay_and_translation" not in policy["slow_functions"]
    assert "tests/test_t2d_replay.py::test_t2d_N4_octagon_escape_real_replay" not in policy["slow_functions"]
