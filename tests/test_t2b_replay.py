"""Two small frozen cage replays check semantics, never current source hashes.

The stored provenance names the generating commit and historical source bytes.
Only fixture payload integrity is hashed here. Actual verification reruns the
current exact cage checks, independently of external evidence paths and Git.
"""
import hashlib
import json
from pathlib import Path

import pytest

from eab.kernel2d.se2_cage import verify_se2_cage


DATA = json.loads((Path(__file__).parent / "data/t2b_cage_replay.json").read_text("utf-8"))
CASES = DATA["cases"]


def test_fixed_cage_replay_payload_integrity_and_historical_provenance():
    encoded = json.dumps(CASES, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    assert hashlib.sha256(encoded).hexdigest() == DATA["payload_sha256"]
    assert DATA["schema"] == "eab.t2b.fixed-cage-replay/1"
    assert DATA["producer"]["source_commit"] and DATA["producer"]["tool_version"]
    assert {case["case_id"] for case in CASES} == {"low_room", "d07"}


@pytest.mark.parametrize("case", CASES, ids=[case["case_id"] for case in CASES])
def test_fixed_cage_replay_reruns_conditions_and_exact_counts(case):
    # JSON strings exercise the canonical schema parser as well as geometry.
    actual = verify_se2_cage(json.dumps(case["instance"]), json.dumps(case["certificate"]))
    expected = case["expected"]
    assert actual.valid is expected["valid"] is True, actual.reason
    assert actual.condition == expected["condition"] == "ACCEPTED"
    assert actual.counts == expected["counts"]
    assert actual.counts["barrier_segments"] > 0
    assert actual.counts["connection_quadrilaterals"] > 0
    if case["case_id"] == "low_room":
        assert case["certificate"]["chain"]["kind"] == "capped"
        assert len(case["certificate"]["caps"]) == 2
        assert actual.counts["contraction_inequalities"] > 0
    else:
        assert case["certificate"]["chain"]["kind"] == "closed"
        assert case["certificate"]["caps"] == []
