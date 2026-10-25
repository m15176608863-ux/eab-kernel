"""Search bookkeeping is not a geometric oracle.

The numerical oracle is exact Fraction arithmetic on literal endpoints. The
failure tests inject a lying status at the orchestration call boundary and
require the unchanged, independently parsed cage checker to catch it.
"""
from fractions import Fraction as F
import json
from pathlib import Path

import pytest

import t2c_science as science


@pytest.mark.parametrize("lower,upper,exponent,expected", [
    (F(1, 4), F(1, 2), 12, F(3, 8)),
    (F(1, 3), F(3, 8), 12, F(1450, 4096)),
    (F(1024, 4096), F(1025, 4096), 12, None),
    (F(1, 4), F(1025, 4096), 16, F(2049, 8192)),
    (F(1024, 4096), F(1026, 4096), 12, F(1025, 4096)),
])
def test_binary_probe_is_strictly_interior_or_grid_exhausted(lower, upper, exponent, expected):
    assert science.grid_middle(lower, upper, exponent) == expected
    if expected is not None:
        assert lower < expected < upper
        assert (expected * 2 ** exponent).denominator == 1


def test_cage_orchestration_uses_independent_raw_json_entry(monkeypatch):
    import t2b_independent_cage_verifier as independent
    folder = Path(__file__).parent / "data/t2b_dual_cases/lower_d01"
    original = independent.load_json
    paths = []

    def spy(path):
        paths.append(path)
        return original(path)

    monkeypatch.setattr(independent, "load_json", spy)
    record = science.check_cage_files(folder / "instance.json", folder / "certificate.json")
    assert paths == [folder / "instance.json", folder / "certificate.json"]
    assert record["production"]["valid"] is True
    assert record["independent"]["valid"] is True
    assert record["production"]["counts"]["barrier_segments"] > 0


def test_cage_orchestration_stops_on_verifier_disagreement(monkeypatch):
    folder = Path(__file__).parent / "data/t2b_forgeries/acc/A01"
    from eab.kernel2d.se2_cage import SE2CageVerification

    def lie(*args):
        return SE2CageVerification(True, "ACCEPTED", "injected at call boundary", None, {})

    monkeypatch.setattr(science, "verify_se2_cage", lie)
    with pytest.raises(AssertionError, match="verifier disagreement"):
        science.check_cage_files(folder / "instance.json", folder / "cert.json")


@pytest.mark.parametrize("case_id,delta", [
    ("d01", F(1, 3)), ("d03", F(1001, 4096)), ("d08", F(415, 4096)),
])
def test_science_probe_dovetail_matches_independent_instance(case_id, delta):
    instance, _ = science.scientific_instance(case_id, delta)
    assert science.instance_comparison(case_id, delta, instance) == {"applicable": True, "equal": True}


@pytest.mark.parametrize("scope", [False, True])
def test_alternating_unknown_probes_do_not_change_certified_bounds(monkeypatch, tmp_path, scope):
    """Exercise scheduler control flow, not a synthetic geometry certificate."""
    import t2c_escape_proposer as escape
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    (baseline / "escape_candidate.json").write_text("{}", encoding="utf-8")
    (baseline / "certificate.json").write_text(json.dumps({
        "chain": {"kind": "closed"}, "intervals": [{}, {}], "caps": []}), encoding="utf-8")
    monkeypatch.setattr(science, "freeze_sources", lambda _: [])
    monkeypatch.setattr(science, "baseline_case", lambda row, output: (baseline, {}))
    monkeypatch.setattr(escape, "audit_proposal", lambda *args: {"finite_and_production_valid": True})
    seen = []

    def cage(case_id, delta, *args):
        seen.append(("cage", delta))
        return {"status": "UNPROVED"}

    def unknown_escape(case_id, delta, *args):
        seen.append(("escape", delta))
        return {"status": "UNPROVED", "t2b_scope_accepted": False}, {}

    monkeypatch.setattr(science, "cage_probe", cage)
    monkeypatch.setattr(science, "escape_probe", unknown_escape)
    result = science.run(tmp_path / "run", ["d07"], max_probes=4, accept_t2b_escape_scope=scope)
    row = result["rows"][0]
    assert [kind for kind, _ in seen] == ["cage", "escape", "cage", "escape"]
    assert seen[0][1] == seen[1][1]
    assert seen[2][1] < seen[0][1] < seen[3][1]
    assert row["new_delta_cage"] == F(13, 64)
    assert row["new_delta_escape"] == F(849, 2560)
    assert row["search_failure_frontier_not_a_bound"] > row["new_delta_cage"]
    assert row["escape_failure_frontier_not_a_bound"] < row["new_delta_escape"]
    assert row["outside_bracket"] == "UNPROVED"
