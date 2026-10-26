"""T2c2 frozen rational-surrogate replay with full semantic result comparison.

The cage oracle has private SAT/winding/JSON parsing. The T2a finite oracle
has private motion and polynomial root isolation. Neither is replaced by a
producer's acceptance flag. Target Q(sqrt(5)) values are NOT parser inputs:
the directed erosion inclusion transfer is checked separately and explicitly.
The independent infinite-tail supplement is coordinate order, not se2_paths.
"""
from dataclasses import asdict
from fractions import Fraction as F
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from eab.kernel2d.se2 import SE2Motion
from eab.kernel2d.se2_cage import verify_se2_cage
from eab.kernel2d.se2_paths import SE2EscapePath, verify_se2_escape
from eab.kernel2d.translation_space import translation_component
from t2a_oracle_audit import validate_escape_segments
import t2b_independent_cage_verifier as independent_cage
from t2c2_knob_exact import Q5, critical_delta, symbolic_vertices, truth_obstacles


DATA = Path(__file__).parent / "data/t2c2"
INDEX = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
ROWS = INDEX["cases"]
CAGES = [pytest.param(row, id=row["id"],
                     marks=pytest.mark.slow if row["slow"] else ())
         for row in ROWS if row["kind"] == "cage"]
ESCAPES = [pytest.param(row, id=row["id"],
                       marks=pytest.mark.slow if row["slow"] else ())
           for row in ROWS if row["kind"] == "escape"]


def _rational(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, F)):
        raise TypeError("replay numeric input must be an exact rational")
    return F(value)


def _ring(points):
    return tuple(tuple(_rational(x) for x in point) for point in points)


def _cyclic_ring(points):
    start = min(range(len(points)), key=lambda index: points[index])
    return points[start:] + points[:start]


def test_t2c2_replay_rejects_json_floating_coordinate_before_conversion():
    with pytest.raises(TypeError, match="exact rational"):
        _ring(json.loads('[[0.125, "1"]]'))
    with pytest.raises(TypeError, match="exact rational"):
        _ring([[True, "1"]])


def test_t2c2_replay_manifest_has_two_cages_and_two_escapes_per_element():
    assert INDEX["schema"] == "eab.t2c2.fixed-replay/1"
    assert len(ROWS) == 8
    assert len({row["id"] for row in ROWS}) == 8
    for element in ("square", "octagon"):
        assert {row["k"] for row in ROWS
                if row["element"] == element and row["kind"] == "cage"} == {6, 12}
        assert {row["k"] for row in ROWS
                if row["element"] == element and row["kind"] == "escape"} == {6, 24}
    assert INDEX["producer"]["source_commit"]
    assert INDEX["producer"]["tool_version"]
    assert INDEX["producer"]["source_manifest_sha256"]
    assert INDEX["direct_irrational_verification"] is False
    assert INDEX["timing_exclusions"] == ["wall-clock diagnostic timings only"]
    assert sum(row["bytes"] for row in ROWS) <= 3_000_000


@pytest.mark.parametrize("row", ROWS, ids=[row["id"] for row in ROWS])
def test_t2c2_frozen_payload_integrity_and_exact_directed_transfer(row):
    packed = (DATA / row["file"]).read_bytes()
    assert len(packed) == row["bytes"] <= 1_000_000
    assert hashlib.sha256(packed).hexdigest() == row["sha256"]
    decoded = gzip.decompress(packed)
    assert len(decoded) == row["decoded_bytes"]
    assert hashlib.sha256(decoded).hexdigest() == row["decoded_sha256"]
    payload = json.loads(decoded)
    assert (payload["id"], payload["element"], payload["k"], payload["kind"]) == (
        row["id"], row["element"], row["k"], row["kind"])
    metadata = payload["metadata"]
    target = metadata["target_delta"]
    assert target["radicand"] == 5
    target = Q5(F(target["a"]), F(target["b"]))
    verified = Q5(F(metadata["verified_delta"]))
    critical = critical_delta(row["element"])
    epsilon = Q5(F(1, 1 << row["k"]))
    if row["kind"] == "cage":
        assert target == critical - epsilon
        assert target < verified < critical
    else:
        assert target == critical + epsilon
        assert critical < verified < target
    # No rounding can consume the smallest requested margin.
    assert abs(verified - target) < epsilon / 1024


@pytest.mark.parametrize("row", ROWS, ids=[row["id"] for row in ROWS])
def test_t2c2_proxy_delta_labels_are_bound_to_exact_instance_geometry(row):
    payload = json.loads(gzip.decompress((DATA / row["file"]).read_bytes()))
    samples = [payload]
    if row["kind"] == "escape":
        samples.append(payload["replay_below"])
    expected_obstacles = tuple(_cyclic_ring(ring) for ring in truth_obstacles())
    for sample in samples:
        delta = _rational(sample["metadata"]["verified_delta"])
        expected_moving = symbolic_vertices(row["element"], Q5(delta))
        instance = json.loads(sample["instance_text"])
        assert _cyclic_ring(_ring(instance["moving"])) == expected_moving
        assert tuple(_cyclic_ring(_ring(ring)) for ring in instance["obstacles"]) == expected_obstacles
        if "candidate_text" in sample:
            candidate = json.loads(sample["candidate_text"])
            assert _cyclic_ring(_ring(candidate["moving"])) == expected_moving
            assert tuple(_cyclic_ring(_ring(ring)) for ring in candidate["obstacles"]) == expected_obstacles


@pytest.mark.parametrize("row", CAGES)
def test_t2c2_cage_replay_full_results_text_entry_and_translation(row, tmp_path, monkeypatch):
    payload = json.loads(gzip.decompress((DATA / row["file"]).read_bytes()))
    instance_path, certificate_path = tmp_path / "i.json", tmp_path / "c.json"
    instance_path.write_bytes(payload["instance_text"].encode("utf-8"))
    certificate_path.write_bytes(payload["certificate_text"].encode("utf-8"))
    production = verify_se2_cage(payload["instance_text"], payload["certificate_text"])
    seen = []
    original = independent_cage.load_json

    def record_entry(path):
        seen.append(path)
        return original(path)

    monkeypatch.setattr(independent_cage, "load_json", record_entry)
    independent = independent_cage._load_result(instance_path, certificate_path)
    assert seen == [instance_path, certificate_path]
    assert json.loads(json.dumps(asdict(production), default=str)) == payload["expected"]["production"]
    assert json.loads(json.dumps(independent)) == payload["expected"]["independent"]
    assert production.valid and independent["valid"]
    assert production.condition == "ACCEPTED" and independent["condition"] == "OK"
    certificate = json.loads(payload["certificate_text"])
    assert certificate["chain"]["kind"] == "closed" and not certificate["caps"]
    assert certificate["disk"] is not None
    instance = json.loads(payload["instance_text"])
    translation = translation_component(
        _ring(instance["moving"]), tuple(_ring(ring) for ring in instance["obstacles"]))
    assert json.loads(json.dumps(asdict(translation), default=str)) == payload["translation_result"]
    assert translation.status == "TRAPPED_TRANSLATION"


@pytest.mark.parametrize("row", ESCAPES)
def test_t2c2_escape_replay_full_results_and_independent_unbounded_tail(row):
    payload = json.loads(gzip.decompress((DATA / row["file"]).read_bytes()))
    candidate = json.loads(payload["candidate_text"])
    moving = _ring(candidate["moving"])
    obstacles = tuple(_ring(ring) for ring in candidate["obstacles"])
    poses, motions, specs = [moving], [], []
    for piece in candidate["pieces"]:
        assert _ring(piece["start"]) == poses[-1]
        spec = (_rational(piece["u1"]), tuple(_rational(x) for x in piece["translation"]),
                tuple(_rational(x) for x in piece["center"]))
        specs.append(spec)
        motions.append(SE2Motion(*spec))
        poses.append(_ring(piece["end"]))
    ray = _ring(candidate["ray_path"])
    production = verify_se2_escape(
        moving, obstacles, SE2EscapePath(tuple(poses), tuple(motions)), ray)
    independent = validate_escape_segments(moving, obstacles, tuple(specs), ray)
    assert json.loads(json.dumps(asdict(production), default=str)) == payload["expected"]["production"]
    assert json.loads(json.dumps(independent)) == payload["expected"]["independent"]
    assert production.valid and production.ray_verification.valid
    assert independent["valid"] and independent["infinite_ray_verified"] is False
    # Recompute the tail separation from the independently reconstructed pose,
    # not the producer's endpoint or its stored tail acceptance flag.
    endpoint = _ring(independent["se2_endpoint"])
    obstacles = tuple(_ring(ring) for ring in candidate["obstacles"])
    ray = _ring(candidate["ray_path"])
    assert ray[0] == (0, 0) and ray[1][0] == 0 and ray[1][1] > 0
    assert min(point[1] for point in endpoint) > max(
        point[1] for ring in obstacles for point in ring)


@pytest.mark.parametrize("row", ESCAPES)
def test_t2c2_same_escape_motions_collide_on_paired_lower_instance(row):
    payload = json.loads(gzip.decompress((DATA / row["file"]).read_bytes()))
    lower = payload["replay_below"]
    upper_candidate = json.loads(payload["candidate_text"])
    lower_candidate = json.loads(lower["candidate_text"])
    for first, second in zip(upper_candidate["pieces"], lower_candidate["pieces"]):
        assert [first[key] for key in ("u1", "translation", "center")] == [
            second[key] for key in ("u1", "translation", "center")]
    assert len(upper_candidate["pieces"]) == len(lower_candidate["pieces"])
    assert upper_candidate["ray_path"] == lower_candidate["ray_path"]
    moving = _ring(lower_candidate["moving"])
    obstacles = tuple(_ring(ring) for ring in lower_candidate["obstacles"])
    poses, motions, specs = [moving], [], []
    for piece in lower_candidate["pieces"]:
        assert _ring(piece["start"]) == poses[-1]
        spec = (_rational(piece["u1"]), tuple(_rational(x) for x in piece["translation"]),
                tuple(_rational(x) for x in piece["center"]))
        specs.append(spec)
        motions.append(SE2Motion(*spec))
        poses.append(_ring(piece["end"]))
    ray = _ring(lower_candidate["ray_path"])
    production = verify_se2_escape(
        moving, obstacles, SE2EscapePath(tuple(poses), tuple(motions)), ray)
    independent = validate_escape_segments(moving, obstacles, tuple(specs), ray)
    assert json.loads(json.dumps(asdict(production), default=str)) == lower["expected"]["production"]
    assert json.loads(json.dumps(independent)) == lower["expected"]["independent"]
    assert not production.valid and not independent["valid"]
    assert any(result.status in ("PENETRATES", "INITIAL_OVERLAP")
               for group in production.segment_results for result in group)
    assert any(pair["status"] in ("PENETRATES", "INITIAL_OVERLAP")
               for pair in independent["pairs"] if pair["kind"] == "se2")
    metadata = lower["metadata"]
    target = metadata["target_delta"]
    assert Q5(F(target["a"]), F(target["b"])) == critical_delta(row["element"]) - F(1, 1 << row["k"])
    assert Q5(F(metadata["verified_delta"])) > Q5(F(target["a"]), F(target["b"]))
