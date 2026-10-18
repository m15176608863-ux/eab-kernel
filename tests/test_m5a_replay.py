"""M5a fit/ledger gates and all 450 frozen interval certificates.

Independent oracle imports: fractions.Fraction, collections.Counter, json,
gzip, pathlib.Path. Closed-form fit expectations use explicit 3-4-5 rotation
coordinates, not SE2Motion.endpoint or production fit primitives. Historical
M4c records are identified comparison data, never a physical-motion oracle.
"""
from collections import Counter
from fractions import Fraction as F
import gzip
import json
from pathlib import Path
import sys

import pytest
from mutation_support import replace_module_callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from frozen_evidence import data_path
import m5a_se2_replay as replay


def _square():
    return tuple((F(x), F(y)) for x, y in ((0, 0), (1, 0), (1, 1), (0, 1)))


@pytest.mark.parametrize("scale", (F(1, 1000000), F(1), F(1000000)))
def test_exact_rational_rigid_fit_recovers_rotation_and_zero_residual(scale):
    A = tuple((scale*x+1000, scale*y-3000) for x, y in _square())
    B = tuple((F(3, 5)*x-F(4, 5)*y+17, F(4, 5)*x+F(3, 5)*y-9) for x, y in A)
    fit = replay.fit_rigid(A, B)
    assert fit.motion.u1 == F(1, 2), "exact rigid half-angle recovery"
    assert fit.delta == 0, "exact endpoint compatibility residual"
    assert fit.certificate == "CERTIFIED_RIGID_ENDPOINT_MODEL"
    assert tuple(fit.motion.endpoint(p) for p in A) == B


def test_guard_nonzero_residual_never_enters_certified_denominator():
    A = _square()
    B = tuple((x+1+F(1, 10**12)*y, y-2) for x, y in A)
    fit = replay.fit_rigid(A, B)
    assert fit.delta > 0, "non-rigid shear must leave a nonzero exact endpoint residual"
    assert fit.certificate == "UNCERTIFIED_NONRIGID_ENDPOINTS", "nonzero endpoint residual must stay uncertified"


def test_residual_certification_mutation_hits_semantic_assertion(monkeypatch):
    monkeypatch.setattr(replay.RigidFit, "certificate", property(lambda self: "CERTIFIED_RIGID_ENDPOINT_MODEL"))
    with pytest.raises(AssertionError, match="nonzero endpoint residual must stay uncertified"):
        test_guard_nonzero_residual_never_enters_certified_denominator()


def test_fit_translation_is_exact_and_large_rotation_is_rejected():
    A = _square()
    fit = replay.fit_rigid(A, tuple((x+F(2, 3), y-F(1, 7)) for x, y in A))
    assert fit.delta == fit.motion.u1 == 0
    assert fit.motion.translation == (F(2, 3), -F(1, 7))
    with pytest.raises(ValueError, match="quarter-turn"):
        replay.fit_rigid(A, tuple((-x, -y) for x, y in A))


@pytest.mark.parametrize("scale", (F(2)**-400, F(1), F(2)**397))
def test_fit_and_residual_displays_round_once_in_three_bands(scale):
    from eab.oracle_construction import scalar_exact
    A = tuple((scale*x, scale*y) for x, y in _square())
    B = tuple((2*x, 2*y) for x, y in A)
    fit = replay.fit_rigid(A, B)
    assert fit.motion.u1 == 0
    assert fit.motion.center == fit.motion.translation == (scale/2, scale/2)
    assert fit.delta == scale/2
    assert fit.record["delta_linf"] == str(scale/2)
    assert fit.record["delta_display"] == scalar_exact(scale/2), "fit residual uses one final checked rounding"
    distribution = replay.residual_distribution([scale/8, scale/4, scale/2, scale])
    for key, exact in (("min", scale/8), ("median", scale/4), ("p95", scale/2), ("max", scale)):
        assert distribution["quantiles_exact"][key] == str(exact)
        assert distribution["quantiles_display"][key] == scalar_exact(exact), "quantile display uses one final checked rounding"


def test_residual_three_band_products_are_distinct():
    products = [replay.residual_distribution([F(2)**e]) for e in (-400, 0, 397)]
    assert len({p["quantiles_exact"]["max"] for p in products}) == 3
    assert len({p["quantiles_display"]["max"] for p in products}) == 3


def test_projected_sweep_contains_independently_evaluated_rational_paths():
    A = _square()
    for u in (F(-1), F(-1, 3), F(0), F(1, 3), F(1)):
        model = replay.SE2Motion(u, (F(2, 3), F(-5, 7)), (F(5), F(-3)))
        for normal in ((1, 0), (0, 1), (3, -4), (F(1, 10**6), F(1, 10**7))):
            lo, hi = replay.projected_sweep(A, model, normal)
            for step in range(11):
                t, z = F(step, 10), F(step, 10)*u
                for x, y in A:
                    px = 5+t*F(2, 3)+((1-z*z)*(x-5)-2*z*(y+3))/(1+z*z)
                    py = -3-t*F(5, 7)+(2*z*(x-5)+(1-z*z)*(y+3))/(1+z*z)
                    assert lo <= normal[0]*px+normal[1]*py <= hi, "swept projection must contain every rigid path point"


def test_swept_projection_is_only_a_sufficient_separation_certificate():
    A = _square(); B = tuple((x+10, y) for x, y in A)
    assert replay.swept_separated(A, B, replay.SE2Motion(), replay.SE2Motion())
    assert not replay.swept_separated(A, B, replay.SE2Motion(0, (10, 0)), replay.SE2Motion())


def test_swept_projection_padding_mutation_hits_its_semantic_containment_guard(monkeypatch):
    replace_module_callable(monkeypatch, replay, "projected_sweep",
                            [("pad = (abs(nx)+abs(ny))*radius", "pad = F(0)")])
    with pytest.raises(AssertionError, match="swept projection must contain every rigid path point"):
        test_projected_sweep_contains_independently_evaluated_rational_paths()


def test_legacy_classifier_handles_serialized_and_live_feature_keys():
    key = ["VE", 2, 5, 6]
    for features in ([key], (tuple(key),)):
        result = {"status": "contact", "features": features, "incidences": features}
        assert replay.classify_reference(-1, key, result, None) == "FIRST_COVER_MATCH", "serialized legacy key must match live exact cover"
    with pytest.raises(ValueError, match="unclassified SE2"):
        original = replay.chord.classify_reference
        try:
            replay.chord.classify_reference = lambda *args: "UNCLASSIFIED"
            replay.classify_reference(-1, key, result, None)
        finally:
            replay.chord.classify_reference = original


def test_replay_frame_recomputes_translation_degenerate_legacy_categories():
    from test_m4c_replay import small_snapshot
    frames = small_snapshot()[1:-1]
    sg, eg = (replay.chord.snapshot.geometry_from_frame(row) for row in frames)
    baseline = replay.chord.frame_result(frames[0], sg, eg, pd_edge_limit=0)
    # Exercise the actual historical-data serialization seam.
    result = replay.frame_result(frames[0], sg, eg, json.loads(json.dumps(baseline)))
    pair = result["pairs"][0]
    assert pair["rigid"]["time"]["rational"] == "1/2"
    assert pair["same_chord_status_and_cover"] and pair["same_chord_time"]
    assert pair["certificate"] == "CERTIFIED_RIGID_ENDPOINT_MODEL"
    assert result["phases"]["raw_df05"]["counts"] == {"OTHER_FEATURE_FIRST": 1}
    assert result["phases"]["post_df06"]["counts"] == {"FIRST_COVER_MATCH": 1}


def _expected():
    return json.loads((ROOT / "fixtures/m5a_se2/expected.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", replay.CASES)
def test_frozen_fifteen_by_thirty_records_are_complete_and_semantically_closed(case):
    expected = _expected()["cases"][case]
    path = ROOT / "fixtures/m5a_se2" / (case+".jsonl.gz")
    source = ROOT / "fixtures/m4b_shadow" / (case+".jsonl.gz")
    assert replay.file_hash(path) == expected["normalized_sha256"]
    assert replay.file_hash(source) == expected["snapshot_sha256"]
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        rows = list(map(json.loads, stream))
    _, frames, _ = replay.chord.snapshot.read_snapshot(source)
    assert len(rows) == len(frames) == expected["steps"] == 30
    assert [replay.digest(row) for row in rows] == expected["frame_sha256"]
    stats, counts = Counter(), {p: Counter() for p in replay.PHASES}
    for index, (row, frame) in enumerate(zip(rows, frames), 1):
        assert row["step"] == index and row["endpoint_step"] == index+1
        assert row["start_geometry_sha256"] == replay.digest(frame["geometry"])
        assert row["stats"]["all_pairs"] == row["stats"].get("omitted_proven_separated_pairs", 0)+len(row["pairs"])
        assert row["stats"]["all_pairs"] == sum(row["stats"].get(c, 0) for c in replay.CERTIFICATES)
        stats.update(row["stats"])
        pairs = {tuple(p["pair"]): p for p in row["pairs"]}
        for pair in pairs.values():
            residual = sum(F(row["blocks"][str(b)]["delta_linf"]) for b in pair["pair"])
            assert F(pair["delta_linf_sum"]) == residual
            assert (pair["certificate"] == "CERTIFIED_RIGID_ENDPOINT_MODEL") == (residual == 0)
        for phase in replay.PHASES:
            data = row["phases"][phase]
            assert len(data["records"]) == len(frame[phase])
            assert Counter(r["category"] for r in data["records"]) == data["counts"]
            counts[phase].update(data["counts"])
            for record in data["records"]:
                pair = pairs[tuple(record["pair"])]
                assert record["category"] in replay.CATEGORIES
                assert replay.classify_reference(pair["initial_state"], record["primary_reference"], pair["rigid"], pair["pd"]) == record["category"]
                if record["secondary_reference"] is not None:
                    assert replay.classify_reference(pair["initial_state"], record["secondary_reference"], pair["rigid"], pair["pd"]) == record["secondary_category"]
    assert dict(stats) == expected["stats"]
    assert {p: dict(v) for p, v in counts.items()} == expected["counts"]


@pytest.mark.parametrize("case", replay.CASES)
def test_real_first_block_fit_per_family_is_reexecuted_not_just_hash_checked(case):
    _, frames, _ = replay.chord.snapshot.read_snapshot(ROOT / "fixtures/m4b_shadow" / (case+".jsonl.gz"))
    sg, eg = (replay.chord.snapshot.geometry_from_frame(f) for f in frames[:2])
    with gzip.open(ROOT / "fixtures/m5a_se2" / (case+".jsonl.gz"), "rt", encoding="utf-8") as stream:
        first = json.loads(stream.readline())
    b = min(sg.blocks)
    assert replay.fit_rigid(sg.blocks[b].poly, eg.blocks[b].poly).record == first["blocks"][str(b)], "real fitted transform/residual semantic replay"


@pytest.mark.parametrize("case,step,pair", (("bb52", 1, (2, 6)), ("bb12", 2, (2, 9)), ("bb10", 7, (5, 6))))
def test_real_rotating_candidate_pairs_reexecute_exact_events_not_just_frozen_hashes(case, step, pair):
    """No-contact, degree-five contact, and changed-cover production paths."""
    from eab.kernel2d.algebraic import RealAlgebraic
    _, frames, _ = replay.chord.snapshot.read_snapshot(ROOT / "fixtures/m4b_shadow" / (case+".jsonl.gz"))
    sg, eg = (replay.chord.snapshot.geometry_from_frame(f) for f in frames[step-1:step+1])
    with gzip.open(ROOT / "fixtures/m5a_se2" / (case+".jsonl.gz"), "rt", encoding="utf-8") as stream:
        frozen = next(row for row in map(json.loads, stream) if row["step"] == step)
    expected = next(row for row in frozen["pairs"] if tuple(row["pair"]) == pair)
    a, b = pair
    fa, fb = (replay.fit_rigid(sg.blocks[k].poly, eg.blocks[k].poly) for k in pair)
    assert fa.motion.u1 != 0 or fb.motion.u1 != 0, "frozen event rerun must exercise genuine rotation"
    actual = replay.se2_first_entrance(sg.blocks[a].poly, sg.blocks[b].poly, fa.motion, fb.motion)
    result = replay.chord._motion_record(actual, sg.blocks[a], sg.blocks[b])
    assert actual.initial_state == expected["initial_state"] and result["status"] == expected["rigid"]["status"], "real rotated status semantic replay"
    for field in ("features", "incidences"):
        assert set(map(tuple, result[field])) == set(map(tuple, expected["rigid"][field])), "real rotated complete feature semantic replay"
    certificate = expected["rigid"]["time"]
    if certificate is None:
        assert actual.exact_time is None
    elif certificate["rational"] is not None:
        assert actual.exact_time == F(certificate["rational"])
    else:
        target = RealAlgebraic(tuple(map(F, certificate["polynomial"])), *map(F, certificate["interval"]))
        assert actual.exact_time == target, "real rotated exact algebraic time semantic replay"


def test_frozen_family_products_are_distinct_and_retain_historical_revalidation():
    expected = _expected()
    assert set(expected["cases"]) == set(replay.CASES)
    assert sum(c["steps"] for c in expected["cases"].values()) == 450
    assert len({c["frames_sha256"] for c in expected["cases"].values()}) >= 14, "frozen parameter products must differ"
    revalidated = json.loads((ROOT / "fixtures/m5a2/revalidation.json").read_text(encoding="utf-8"))
    assert revalidated["complete"] and revalidated["audit"] == "GREEN"
    assert revalidated["steps"] == 450 and set(revalidated["cases"]) == set(replay.CASES)
    assert revalidated["prior_code_hashes"] == expected["code_hashes"], "M5a2 revalidation binds the unchanged historical model"
    # H1: real first-block and rotating-pair tests above replace code-byte pins.
    assert revalidated["all_historical_fixture_bytes_unchanged"] and revalidated["all_semantic_fields_equal"]
    for path, digest in revalidated["input_hashes"].items():
        assert replay.file_hash(data_path(ROOT, path)) == digest, "M5a2 revalidation input hash changed: "+path
    for case in replay.CASES:
        result = revalidated["cases"][case]
        assert result["complete"] and result["steps"] == 30 and result["all_semantic_fields_equal"]
        assert result["old_normalized_sha256"] == expected["cases"][case]["normalized_sha256"]
        assert result["counts"] == expected["cases"][case]["counts"]
        assert result["stats"] == expected["cases"][case]["stats"]
