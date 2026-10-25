"""Small frozen path replays compare semantics, not current source hashes.

Data integrity and producer identity live in fixture metadata. These tests
actually rerun the exact path and the independent interpolation/Sturm/G0
oracle; no external evidence directory, Git checkout or sibling is needed.
"""
from fractions import Fraction as F
import json
from pathlib import Path

import pytest

from eab.kernel2d.se2 import SE2Motion
from eab.kernel2d.se2_paths import SE2EscapePath, verify_se2_escape
from t2a_oracle_audit import validate_escape_segments


def _ring(points):
    return tuple(tuple(F(x) for x in point) for point in points)


CASES = json.loads((Path(__file__).parent / "data/t2a_escape_replay.json").read_text("utf-8"))["cases"]


@pytest.mark.parametrize("case", CASES, ids=[case["case_id"] for case in CASES])
def test_fixed_escape_replay_compares_states_labels_times_and_counts(case):
    moving = _ring(case["moving"])
    obstacles = tuple(_ring(p) for p in case["obstacles"])
    poses, motions = [moving], []
    for piece in case["pieces"]:
        assert _ring(piece["start"]) == poses[-1]
        poses.append(_ring(piece["end"]))
        motions.append(SE2Motion(F(piece["u1"]), tuple(map(F, piece["translation"])),
                                 tuple(map(F, piece["center"]))))
    path = SE2EscapePath(tuple(poses), tuple(motions))
    ray = _ring(case["ray_path"])
    checked = verify_se2_escape(moving, obstacles, path, ray)
    expected = case["expected"]
    assert checked.valid, checked.reason
    assert checked.checked_segments == expected["se2_segments"]
    assert checked.checked_pairs == expected["production_pairs"]
    assert checked.ray_verification.ray_direction == tuple(map(F, expected["ray_direction"]))
    audit = validate_escape_segments(moving, obstacles,
        tuple((m.u1, m.translation, m.center) for m in motions), ray)
    assert audit["valid"] and audit["first_contact_calls"] == expected["oracle_calls"]
    rows = [p for p in audit["pairs"] if p["kind"] == "se2"]
    for actual, oracle in zip((p for row in checked.segment_results for p in row), rows):
        assert actual.status == oracle["status"] == "FREE"
        assert actual.exact_time is oracle["exact_time"] is None
        assert actual.incidences == tuple(oracle["incidences"]) == ()
        assert actual.features == tuple(oracle["features"]) == ()
        assert actual.initial_state == oracle["initial_state"]
        assert actual.end_state == oracle["end_state"]
        assert actual.touches_end == oracle["touches_end"]
