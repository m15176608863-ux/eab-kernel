"""Fixed T2c1 replay: full semantic results, not present-source hashes.

The cage oracle owns independent integer/rational SAT, winding and JSON
parsing; its load_json text entry is observed here. The finite escape oracle
uses private rational motion, polynomial root isolation and open-interval
classification, not production motion/event primitives. It does NOT certify
an infinite ray; the production ray verifier does. No wall-clock diagnostic
field is expected; exact_time fields, all statuses and all counts are kept.
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
from t2b_independent_instances import OCTAGON, SQUARE, canonical_instance, dovetail_instance


DATA = Path(__file__).parent / "data/t2c1"
INDEX = json.loads((DATA / "index.json").read_text("utf-8"))
ROWS = INDEX["cases"]
CAGE_CASES = [pytest.param(row, id=row["case_id"],
                          marks=pytest.mark.slow if row["cage_slow"] else ()) for row in ROWS]
ESCAPE_CASES = [pytest.param(row, index, id=row["case_id"] + "_" + str(index))
                for row in ROWS for index in range(row["escape_samples"])]


def test_replay_manifest_has_ten_cases_and_historical_provenance():
    assert INDEX["schema"] == "eab.t2c1.fixed-replay/1"
    assert len(ROWS) == 10
    assert {row["case_id"] for row in ROWS} == {
        "d01", "d02", "d03", "d04", "d05", "d06", "d07", "d08", "k01", "k02"}
    assert INDEX["producer"]["source_commit"]
    assert INDEX["producer"]["tool_version"]
    assert INDEX["producer"]["source_manifest_sha256"]
    assert "independent finite" in INDEX["escape_scope"]
    assert INDEX["timing_exclusions"] == [
        "wall-clock diagnostic timings only; exact_time is retained"]
    assert sum(row["bytes"] for row in ROWS) <= 5_000_000


@pytest.mark.parametrize("row", ROWS, ids=[row["case_id"] for row in ROWS])
def test_replay_payload_bytes_and_certified_bracket(row):
    packed = (DATA / row["file"]).read_bytes()
    assert len(packed) == row["bytes"] <= 1_000_000
    assert hashlib.sha256(packed).hexdigest() == row["sha256"]
    decoded = gzip.decompress(packed)
    assert len(decoded) == row["decoded_bytes"]
    assert hashlib.sha256(decoded).hexdigest() == row["decoded_sha256"]
    payload = json.loads(decoded)
    assert payload["case_id"] == row["case_id"]
    for key, field in (("instance", "cage_instance_text"), ("certificate", "cage_certificate_text")):
        data = payload[field].encode("utf-8")
        assert hashlib.sha256(data).hexdigest() == payload["origins"][key]["sha256"]
        assert len(data) == payload["origins"][key]["bytes"]
    assert F(row["old_delta_cage"]) <= F(row["delta_cage"])
    assert F(row["delta_cage"]) < F(row["delta_escape"]) <= F(row["delta_translation_star"])
    assert F(row["delta_escape"]) <= F(row["old_delta_escape"])
    certificate = json.loads(payload["cage_certificate_text"])
    assert len(certificate["intervals"]) == row["intervals"]
    assert bool(certificate["caps"]) is row["uses_caps"]
    assert (certificate["chain"]["kind"] == "closed") is row["full_circle"]
    assert len(payload["escapes"]) == row["escape_samples"]
    for sample in payload["escapes"]:
        text = sample["candidate_text"].encode("utf-8")
        assert hashlib.sha256(text).hexdigest() == sample["origin"]["sha256"]
        assert len(text) == sample["origin"]["bytes"]
        assert F(row["delta_cage"]) < F(sample["delta"]) < F(row["old_delta_escape"])
        assert sample["is_final_upper"] is (F(sample["delta"]) == F(row["delta_escape"]))


@pytest.mark.parametrize("row", CAGE_CASES)
def test_replay_cage_full_results_text_entry_instance_and_translation(row, tmp_path, monkeypatch):
    payload = json.loads(gzip.decompress((DATA / row["file"]).read_bytes()))
    instance_path, certificate_path = tmp_path / "i.json", tmp_path / "c.json"
    instance_path.write_bytes(payload["cage_instance_text"].encode("utf-8"))
    certificate_path.write_bytes(payload["cage_certificate_text"].encode("utf-8"))
    production = verify_se2_cage(instance_path.read_text("utf-8"), certificate_path.read_text("utf-8"))
    seen = []
    original = independent_cage.load_json

    def record_entry(path):
        seen.append(path)
        return original(path)

    monkeypatch.setattr(independent_cage, "load_json", record_entry)
    independent = independent_cage._load_result(instance_path, certificate_path)
    assert seen == [instance_path, certificate_path]
    assert asdict(production) == payload["expected_cage"]["production"]
    assert independent == payload["expected_cage"]["independent"]
    assert production.valid and independent["valid"]
    assert production.condition == "ACCEPTED" and independent["condition"] == "OK"
    instance = json.loads(payload["cage_instance_text"])
    moving = tuple(tuple(F(x) for x in p) for p in instance["moving"])
    obstacles = tuple(tuple(tuple(F(x) for x in p) for p in polygon) for polygon in instance["obstacles"])
    translation = translation_component(moving, obstacles)
    assert translation.status == payload["translation_status"] == "TRAPPED_TRANSLATION"
    if row["kind"] == "dovetail":
        other = dovetail_instance(F(row["head_width"]), F(row["neck_width"]),
            OCTAGON if row["element"] == "octagon" else SQUARE, row["wall_erosion"], F(row["delta_cage"]))
        assert canonical_instance(instance) == canonical_instance(other)
        assert payload["independent_instance"] == {"applicable": True, "equal": True}
    else:
        assert payload["independent_instance"]["applicable"] is False


if ESCAPE_CASES:
    @pytest.mark.slow
    @pytest.mark.parametrize("row,sample_index", ESCAPE_CASES)
    def test_replay_improved_escape_full_production_and_independent(row, sample_index):
        payload = json.loads(gzip.decompress((DATA / row["file"]).read_bytes()))
        sample = payload["escapes"][sample_index]
        candidate = json.loads(sample["candidate_text"])
        moving = tuple(tuple(F(x) for x in p) for p in candidate["moving"])
        obstacles = tuple(tuple(tuple(F(x) for x in p) for p in polygon) for polygon in candidate["obstacles"])
        poses, motions, specs = [moving], [], []
        for piece in candidate["pieces"]:
            assert tuple(tuple(F(x) for x in p) for p in piece["start"]) == poses[-1]
            spec = (F(piece["u1"]), tuple(F(x) for x in piece["translation"]),
                    tuple(F(x) for x in piece["center"]))
            specs.append(spec)
            motions.append(SE2Motion(*spec))
            poses.append(tuple(tuple(F(x) for x in p) for p in piece["end"]))
        ray = tuple(tuple(F(x) for x in p) for p in candidate["ray_path"])
        production = verify_se2_escape(moving, obstacles, SE2EscapePath(tuple(poses), tuple(motions)), ray)
        independent = validate_escape_segments(moving, obstacles, tuple(specs), ray)
        assert json.loads(json.dumps(asdict(production), default=str)) == sample["expected"]["production"]
        assert json.loads(json.dumps(independent)) == sample["expected"]["independent"]
        assert production.valid and production.ray_verification.valid
        assert independent["valid"] and independent["infinite_ray_verified"] is False
        assert sample["scope"] == INDEX["escape_scope"]
        assert F(row["delta_cage"]) < F(sample["delta"]) <= F(row["delta_translation_star"])
        if row["kind"] == "dovetail":
            other = dovetail_instance(F(row["head_width"]), F(row["neck_width"]),
                OCTAGON if row["element"] == "octagon" else SQUARE, row["wall_erosion"], F(sample["delta"]))
            assert canonical_instance({"moving": candidate["moving"], "obstacles": candidate["obstacles"]}) == canonical_instance(other)
