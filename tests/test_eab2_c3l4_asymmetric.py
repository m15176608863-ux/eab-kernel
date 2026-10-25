"""Raw seed and diagnostic-envelope oracles; no sensitivity slopes are inputs."""
import copy
from fractions import Fraction as Q
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from eab2_c3l4_asymmetric import (CHANNELS, asymmetric_cases, formal_cases, perturb,
    richardson_envelope, seed_channels, skeleton, skeleton_checks)
from eab2_c3l4_diff import exact_wire
from eab.kernel2d.contacts import assemble_contact_set2


def test_asymmetric_six_deterministic_channels_share_vertices_and_activate_load_arrays():
    source = next(formal_cases({"g1_unreversed_t2"}))
    channels = list(seed_channels(source))
    assert [name for name, _ in channels] == list(CHANNELS)
    assert channels == list(seed_channels(source))
    payloads = []
    for name, jet in channels:
        points = {}
        by_id = {body.body_id: body for body in source["model"].bodies}
        for (identity, vertex), velocity in zip(jet["vertex_ids"], jet["vertices"][0]):
            body = by_id[identity]
            point = (body.original_vertices or body.vertices)[vertex]
            assert point not in points or points[point] == velocity
            points[point] = velocity
        payloads.append(json.dumps({key: value for key, value in jet.items() if key != "parameters"}, sort_keys=True))
        if name in ("dead_live", "random_rational_2"):
            assert any(Q(v) for row in jet["dead"][0] for v in row)
            assert any(Q(v) for row in jet["live"][0] for v in row)
    assert len(set(payloads)) == 6


def test_asymmetric_face_and_single_vertex_really_break_symmetric_all_face_direction():
    source = next(formal_cases({"g1_unreversed_t2"}))
    channels = dict(seed_channels(source))
    for name in ("single_face", "single_vertex"):
        jet = channels[name]
        nonzero = [(identity, velocity) for identity, velocity in zip(jet["vertex_ids"], jet["vertices"][0]) if any(map(Q, velocity))]
        assert 0 < len(nonzero) < len(jet["vertex_ids"])/2
        assert len({body for (body, _), _ in nonzero}) == 2
    assert sum(any(map(Q, row)) for row in channels["single_vertex"]["vertices"][0]) == 2


def test_asymmetric_probe_checks_actual_l1_feature_skeleton_both_sides_three_steps():
    source = next(formal_cases({"g1_unreversed_t2"}))
    jet = dict(seed_channels(source))["single_face"]
    checks = skeleton_checks(source, jet)
    assert set(checks) == {"positive", "negative"}
    for row in checks.values():
        assert row["valid"] and len(row["probes"]) == 3
        assert all(item["same_skeleton"] for item in row["probes"])
    moved = perturb(source["model"], jet, Q(1, 2**18))
    actual = exact_wire(assemble_contact_set2(moved))
    assert skeleton(moved, actual) == skeleton(source["model"], source["contacts"])
    # A deleted actual contact cannot be concealed by coordinate-insensitive comparison.
    corrupt = copy.deepcopy(actual)
    corrupt["constraints"].pop()
    assert skeleton(moved, corrupt) != skeleton(moved, actual)


def test_asymmetric_case_preparation_does_not_claim_a_referee_or_certified_slope():
    source = next(formal_cases({"g1_unreversed_t2"}))
    case = next(asymmetric_cases([source]))
    assert case["family"] == "asymmetric/" + source["family"]
    threshold_queries = [q for _, q in case["queries"] if q.get("threshold_query_ref") == "critical"]
    limit_queries = [q for _, q in case["queries"] if q.get("limit_query_ref") == "limit"]
    assert len(threshold_queries) == 6 and len(case["queries"]) == 6 + len(limit_queries)
    limit_base = source["bases"].get("limit")
    finite = bool(limit_base and limit_base["result"].get("mathematical_status") == "OPTIMAL"
                  and limit_base["result"].get("exact_value") is not None)
    # The finite-capacity load-jet channel exists exactly when the source has
    # a finite limit; it carries both load arrays and no vertex velocity.
    assert len(limit_queries) == int(finite)
    for query in limit_queries:
        jet = query["geometry_seed"]
        assert query["asymmetric_probe"]["target"] == "limit" and query["result"]["parameter"] == "asym_limit_dead_live"
        assert all(v == ["0/1", "0/1"] for v in jet["vertices"][0])
        assert any(v != ["0/1"] * 3 for v in jet["live"][0]) and any(v != ["0/1"] * 3 for v in jet["dead"][0])
    for _, query in case["queries"]:
        assert query["generated_channel"] is True
        assert query["result"]["right_derivative"] is None
        assert query["result"]["reason"] == "pending_live_referee"
        assert len(query["asymmetric_probe"]["exponents"]) == 3


def test_richardson_red_flag_envelope_accepts_one_sided_approach_not_raw_quotient_minmax():
    epsilon = [Q(1, 2**k) for k in (6, 10, 14)]
    quotients = [(Q(1, 2)-step/3, Q(1, 2)-step/3) for step in epsilon]
    assert max(hi for _, hi in quotients) < Q(1, 2)
    low, high = richardson_envelope(quotients, epsilon)
    assert low <= Q(1, 2) <= high
    assert not low <= 0 <= high  # The false single-basis smooth zero is a red flag.


def test_richardson_red_flag_envelope_propagates_exact_threshold_bracket_uncertainty():
    epsilon = [Q(1, 2**k) for k in (6, 10, 14)]
    exact = [(Q(1, 2)-step/3, Q(1, 2)-step/3) for step in epsilon]
    intervals = [(lo-Q(1, 2**62)/step, hi+Q(1, 2**62)/step) for (lo, hi), step in zip(exact, epsilon)]
    first, expanded = richardson_envelope(exact, epsilon), richardson_envelope(intervals, epsilon)
    assert expanded[0] <= first[0] <= first[1] <= expanded[1]
    assert richardson_envelope([(Q(2), Q(2))]*3, epsilon) == (Q(2), Q(2))


@pytest.mark.parametrize("intervals,steps", (([(Q(0), Q(0))]*2, [Q(1, 4), Q(1, 8)]),
    ([(Q(1), Q(0))]*3, [Q(1, 4), Q(1, 8), Q(1, 16)]),
    ([(Q(0), Q(0))]*3, [Q(1, 8), Q(1, 4), Q(1, 16)])))
def test_richardson_diagnostics_refuse_missing_steps_or_reversed_intervals(intervals, steps):
    with pytest.raises(AssertionError):
        richardson_envelope(intervals, steps)
