"""M5a2 replay semantics, small-angle boxes and irrational equality gates.

Oracle imports: fractions.Fraction, math.isqrt, random.Random, gzip,
json, pathlib.Path, functools.lru_cache, types.SimpleNamespace. For A1 the
objects under test are replay wiring/serialization/classification, NOT the
SE2/chord geometry kernels: those kernels are called directly, bypassing ALL
replay result/classification helpers. A separately written exact fit and a
state/membership decision table supply inputs and ledger expectations. The
small-angle oracle expands rational rotation coordinates itself and shares
no geometry, polynomial or bound primitive with the kernel. Its import of
SE2Motion supplies input data only; _swept_bounds is the object under test.
"""
from fractions import Fraction as F
from collections import Counter
import hashlib
from functools import lru_cache
import gzip
import json
from math import isqrt
from pathlib import Path
from random import Random
import sys
from types import SimpleNamespace

import pytest

from eab.kernel2d.algebraic import RealAlgebraic
from eab.oracle_construction import scalar_exact
from eab.kernel2d.motion import motion_first_entrance
from eab.kernel2d import se2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import m5a_se2_replay as replay

CASES = (("bb05", 4, (1, 4)), ("bb05", 4, (2, 4)),
         ("bb10", 7, (5, 6)), ("bb12", 2, (2, 9)))


def _json(value):
    return json.loads(json.dumps(value))


@lru_cache(maxsize=None)
def real_inputs(case, step, pair):
    """Keep the real frame/ids, limiting only the number of enumerated pairs."""
    _, frames, _ = replay.chord.snapshot.read_snapshot(
        ROOT / "fixtures/m4b_shadow" / (case+".jsonl.gz"))
    frame = _json(frames[step-1])
    sg, eg = (replay.chord.snapshot.geometry_from_frame(f) for f in frames[step-1:step+1])
    with gzip.open(ROOT / "fixtures/m5a_se2" / (case+".jsonl.gz"), "rt", encoding="utf-8") as stream:
        frozen = next(r for r in map(json.loads, stream) if r["step"] == step)
    with gzip.open(ROOT / "reports/codex/M4c_evidence/fix_frozen_replay" / case / "normalized.jsonl.gz",
                   "rt", encoding="utf-8") as stream:
        baseline = next(r for r in map(json.loads, stream) if r["step"] == step)
    baseline["pairs"] = [r for r in baseline["pairs"] if tuple(r["pair"]) == pair]
    owners = {v: b for b, block in sg.blocks.items() for v in block.vidx}
    indices = {}
    for phase in replay.PHASES:
        rows = [r for r in baseline["phases"][phase]["records"] if tuple(r["pair"]) == pair]
        baseline["phases"][phase]["records"] = rows
        selected = [(index, raw) for index, raw in enumerate(frame[phase], 1)
                    if tuple(sorted((owners[sg.canon(raw[1])], owners[sg.canon(raw[2])]))) == pair]
        indices[phase] = [index for index, _ in selected]
        frame[phase] = [raw for _, raw in selected]
    return (frame, SimpleNamespace(blocks={b: sg.blocks[b] for b in pair}, canon=sg.canon, phase_indices=indices),
            SimpleNamespace(blocks={b: eg.blocks[b] for b in pair}), baseline, frozen)


def _fit_without_replay(start, end):
    """Independent transcription of the declared rational fit proposal."""
    n = len(start)
    c0 = tuple(sum(p[k] for p in start)/n for k in (0, 1))
    c1 = tuple(sum(p[k] for p in end)/n for k in (0, 1))
    vectors = [((p[0]-c0[0], p[1]-c0[1]), (q[0]-c1[0], q[1]-c1[1]))
               for p, q in zip(start, end)]
    length = sum(x*x+y*y for (x, y), _ in vectors)
    cosine = sum(x*X+y*Y for (x, y), (X, Y) in vectors)/length
    sine = sum(x*Y-y*X for (x, y), (X, Y) in vectors)/length
    length2 = cosine*cosine+sine*sine
    numerator_root = isqrt(length2.numerator)
    denominator_root = isqrt(length2.denominator)
    perfect = numerator_root**2 == length2.numerator and denominator_root**2 == length2.denominator
    norm = (F(numerator_root, denominator_root) if perfect else
            F(isqrt((length2.numerator << 160)//length2.denominator), 1 << 80))
    half_angle = sine/(norm+cosine)
    if length2 != 1:
        half_angle = half_angle.limit_denominator(1 << 40)
    translation = tuple(c1[k]-c0[k] for k in (0, 1))
    model = se2.SE2Motion(half_angle, translation, c0)
    ends = independent_at(start, model, F(1))
    residual = max(abs(x-y) for p, q in zip(ends, end) for x, y in zip(p, q))
    return model, residual


def independent_at(poly, model, time):
    z = time*model.u1
    c, d = model.center, model.translation
    return tuple((c[0]+time*d[0]+((1-z*z)*(x-c[0])-2*z*(y-c[1]))/(1+z*z),
                  c[1]+time*d[1]+(2*z*(x-c[0])+(1-z*z)*(y-c[1]))/(1+z*z)) for x, y in poly)


def _ids(labels, a, b):
    """Map local kernel labels without the replay's feature mapper."""
    result = set()
    for kind, i, j in labels:
        if kind == "VV":
            result.add(("VV", *sorted((a.vidx[i], b.vidx[j]))))
        elif kind == "VE":
            result.add(("VE", a.vidx[i], *sorted((b.vidx[j], b.vidx[(j+1) % len(b.vidx)])) ))
        else:
            assert kind == "EV"
            result.add(("VE", b.vidx[j], *sorted((a.vidx[i], a.vidx[(i+1) % len(a.vidx)])) ))
    return sorted(result)


def _exact_time(certificate):
    if certificate is None:
        return None
    if certificate["rational"] is not None:
        return RealAlgebraic.from_rational(F(certificate["rational"]))
    polynomial = tuple(map(F, certificate["polynomial"]))
    if "interval" in certificate:
        lower, upper = map(F, certificate["interval"])
    else:
        c, b, _ = polynomial
        bound, middle = 2+abs(c)+abs(b), -b/2
        lower, upper = (-bound, middle) if certificate["branch"] < 0 else (middle, bound)
    return RealAlgebraic(polynomial, lower, upper)


def _record(result, a, b):
    return {"status": result.status,
            "time": None if result.exact_time is None else result.exact_time.certificate,
            "time_display": result.time, "features": _json(_ids(result.features, a, b)),
            "incidences": _json(_ids(result.incidences, a, b))}


def _category(state, key, result):
    """Decision table, no import/call of either replay classifier."""
    assert state == -1, "selected ledger examples begin strictly separated"
    in_cover = tuple(key) in map(tuple, result["features"])
    in_incidence = tuple(key) in map(tuple, result["incidences"])
    table = {("no_contact", False, False): "NO_CONTACT_IN_STEP",
             ("contact", True, True): "FIRST_COVER_MATCH",
             ("contact", False, True): "FIRST_INCIDENCE_NOT_COVER",
             ("contact", False, False): "OTHER_FEATURE_FIRST"}
    return table[(result["status"], in_cover, in_incidence)]


def _cover_equal(a, b):
    return (a["status"], a["features"]) == (b["status"], b["features"])


def _assert_record(actual, expected, model):
    assert set(actual) == set(expected), "M5a2 ledger model field set"
    for field in ("status", "time_display", "features", "incidences"):
        assert actual[field] == expected[field], "M5a2 ledger "+model+" "+field
    assert _exact_time(actual["time"]) == _exact_time(expected["time"]), "M5a2 ledger "+model+" exact time"


@lru_cache(maxsize=None)
def independent_expected(case, step, pair):
    frame, sg, eg, _, _ = real_inputs(case, step, pair)
    a, b = (sg.blocks[k] for k in pair)
    A, B = (tuple(tuple(map(F, p)) for p in block.poly) for block in (a, b))
    A1, B1 = (tuple(tuple(map(F, p)) for p in eg.blocks[k].poly) for k in pair)
    ma, da = _fit_without_replay(A, A1)
    mb, db = _fit_without_replay(B, B1)
    assert ma.u1 or mb.u1, "M5a2 ledger must use genuine rotation"
    rigid = se2.se2_first_entrance(A, B, ma, mb)
    chord = motion_first_entrance(A, B, A1, B1)
    At = tuple(tuple(p[k]+ma.translation[k] for k in (0, 1)) for p in A)
    Bt = tuple(tuple(p[k]+mb.translation[k] for k in (0, 1)) for p in B)
    translation = motion_first_entrance(A, B, At, Bt)
    assert rigid.initial_state == chord.initial_state == translation.initial_state == -1
    records = [_record(r, a, b) for r in (rigid, chord, translation)]
    r, c, t = records
    result = {"pair": list(pair), "initial_state": -1, "rigid": r, "chord": c, "translation": t,
              "pd": None, "certificate": "CERTIFIED_RIGID_ENDPOINT_MODEL" if da+db == 0 else "UNCERTIFIED_NONRIGID_ENDPOINTS",
              "delta_linf_sum": str(da+db), "same_chord_status_and_cover": _cover_equal(r, c),
              "same_translation_status_and_cover": _cover_equal(r, t),
              "same_chord_time": _exact_time(r["time"]) == _exact_time(c["time"]),
              "path": "PROVED_SWEPT_PROJECTION_SEPARATION" if (case, step, pair) == CASES[1] else "SE2_EXACT_EVENT_ENUMERATION"}
    if c["status"] == "contact" and not _cover_equal(c, t):
        result["m4c_translation_discrepancy_contact"] = True
    phases = {}
    for phase in replay.PHASES:
        references = []
        for index, raw in zip(sg.phase_indices[phase], frame[phase]):
            key = ["VE", sg.canon(raw[1]), *sorted((sg.canon(raw[2]), sg.canon(raw[3])))]
            second = (["VE", sg.canon(raw[4]), *sorted((sg.canon(raw[5]), sg.canon(raw[6])))]
                      if raw[0] == 1 and raw[4] > 0 else None)
            references.append({"index": index, "tuple7": raw, "pair": list(pair), "primary_reference": key, "secondary_reference": second,
                               "category": _category(-1, key, r), "chord_category": _category(-1, key, c),
                               "secondary_category": None if second is None else _category(-1, second, r),
                               "chord_secondary_category": None if second is None else _category(-1, second, c)})
        phases[phase] = references
    return result, phases


def assert_ledger_semantics(case, step, pair, ledger):
    """Accept either original frozen data or freshly serialized mutant data."""
    expected, phases = independent_expected(case, step, pair)
    actual = next(r for r in ledger["pairs"] if tuple(r["pair"]) == pair)
    assert set(actual) == set(expected), "M5a2 ledger pair field set"
    for field in expected:
        if field in ("rigid", "chord", "translation"):
            _assert_record(actual[field], expected[field], field)
        else:
            assert actual[field] == expected[field], "M5a2 ledger pair "+field
    for phase, references in phases.items():
        rows = [r for r in ledger["phases"][phase]["records"] if tuple(r["pair"]) == pair]
        assert len(rows) == len(references), "M5a2 ledger reference conservation"
        for row, target in zip(rows, references):
            assert set(row) == set(target), "M5a2 ledger reference field set"
            for field, value in target.items():
                assert row[field] == value, "M5a2 ledger independently classified "+field


@pytest.mark.parametrize("case,step,pair", CASES)
def test_real_rotating_ledger_matches_direct_kernels_and_independent_classification(case, step, pair):
    frame, sg, eg, baseline, frozen = real_inputs(case, step, pair)
    # No code_hashes call: freezing data again cannot turn a semantic defect green.
    assert_ledger_semantics(case, step, pair, frozen)
    live = _json(replay.frame_result(frame, sg, eg, baseline))
    assert_ledger_semantics(case, step, pair, live)


def test_rotating_ledger_examples_include_equal_and_different_conclusions():
    results = [independent_expected(*case)[0] for case in CASES]
    assert {r["same_chord_status_and_cover"] for r in results} == {False, True}
    assert {(r["rigid"]["status"], r["chord"]["status"]) for r in results} >= {
        ("contact", "contact"), ("contact", "no_contact"), ("no_contact", "no_contact")}
    assert len({json.dumps(r, sort_keys=True) for r in results}) == len(CASES), "M5a2 parameter products distinct"


@pytest.mark.parametrize("u", tuple(sign*F(1, 10**power) for sign in (-1, 1) for power in range(1, 7)))
def test_small_angle_swept_bounds_contain_independent_asymmetric_paths(u):
    products = []
    z = F(Random(20261015).randrange(1, 23), 29)
    rotations = ((F(1), F(0)), (F(3, 5), F(4, 5)), ((1-z*z)/(1+z*z), 2*z/(1+z*z)))
    for scale, shift in ((F(1, 10**6), 0), (F(1), 1000), (F(10**5), 10**6)):
        for cosine, sine in rotations:
            local = ((F(0), F(0)), (F(1, 10000), F(0)), (F(1, 100000), F(1)), (F(0), F(3, 5)))
            poly = tuple((shift+scale*(cosine*x-sine*y), -3*shift+scale*(sine*x+cosine*y)) for x, y in local)
            model = se2.SE2Motion(u, (-scale*sine/F(7), scale*cosine/F(7)), (shift, -3*shift))
            ring = se2._validated_ring(poly, model)
            bounds = se2._swept_bounds(ring)
            products.append(bounds)
            for tick in range(11):
                for point in independent_at(poly, model, F(tick, 10)):
                    for k in (0, 1):
                        assert bounds[k][0] <= point[k] <= bounds[k][1], "M5a2 small-angle swept bounds contain path"
    assert len(set(products)) == 9, "M5a2 swept frame/scale/translation products distinct"


def test_same_time_irrational_uses_polynomial_and_correct_root_branch():
    polynomial = (F(1, 8), -1, 1)
    roots = (RealAlgebraic(polynomial, 0, F(1, 2)), RealAlgebraic(polynomial, F(1, 2), 1))
    for index, root in enumerate(roots):
        certificate = {"rational": None, "polynomial": ["1/8", "-1", "1"], "branch": (-1, 1)[index]}
        assert replay.same_time(root, certificate), "M5a2 same_time irrational matching branch"
        assert not replay.same_time(roots[1-index], certificate), "M5a2 same_time rejects opposite irrational branch"
        unrelated = RealAlgebraic((F(1, 16), -1, 1), 0, F(1, 2))
        assert not replay.same_time(unrelated, certificate), "M5a2 same_time rejects different irrational polynomial"
    assert replay.same_time(None, None)
    assert not replay.same_time(roots[0], None)


@pytest.mark.parametrize("kind", ("swapped_models", "chord_no_contact_shortcut", "classifier_uses_chord",
                                  "sweep_nine_fifths", "same_time_wrong_branch", "same_time_ignores_polynomial"))
def test_internal_mutants_hit_new_semantic_guards_after_hash_masking_and_refreeze(kind, monkeypatch, tmp_path):
    from m5a2_replay_mutations import MUTATIONS, inject, run_guard
    inject(kind, monkeypatch)
    with pytest.raises(AssertionError, match=MUTATIONS[kind][3]):
        run_guard(kind, tmp_path, full_freeze=False)


def _independent_digest(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@lru_cache(maxsize=None)
def independent_frame_expected(case, step, pair):
    """Single real pair, full frame schema: no replay metadata/classifier helper.

    Fraction endpoint fit is re-expanded above; residual display comes from
    oracle_construction.scalar_exact, not the replay's scalar_rational.
    Counts are derived from independent model results and reference tables.
    """
    frame, sg, eg, baseline, _ = real_inputs(case, step, pair)
    expected_pair, expected_references = independent_expected(case, step, pair)
    blocks = {}
    for b in pair:
        start, end = (tuple(tuple(F(v) for v in p) for p in g.blocks[b].poly) for g in (sg, eg))
        motion, delta = _fit_without_replay(start, end)
        blocks[str(b)] = {"u1": str(motion.u1), "center": [str(v) for v in motion.center],
                          "translation": [str(v) for v in motion.translation], "delta_linf": str(delta),
                          "delta_display": scalar_exact(delta, allow_underflow=True),
                          "certificate": "CERTIFIED_RIGID_ENDPOINT_MODEL" if delta == 0 else "UNCERTIFIED_NONRIGID_ENDPOINTS"}
    stats = Counter({"all_pairs": 1, expected_pair["certificate"]: 1, expected_pair["path"]: 1,
                     "initial_-1_"+expected_pair["rigid"]["status"]: 1})
    same = expected_pair["same_chord_status_and_cover"]
    stats["separated_chord_same" if same else "separated_chord_different"] = 1
    if expected_pair["rigid"]["status"] == "contact":
        stats["rigid_new_contacts"] = 1
    if expected_pair["chord"]["status"] == "contact":
        stats["chord_new_contacts"] = 1
    if expected_pair.get("m4c_translation_discrepancy_contact"):
        stats["m4c_20_subset"] = 1
        stats["m4c_20_se2_chord_same" if same else "m4c_20_se2_chord_different"] = 1
    phases = {}
    for phase, references in expected_references.items():
        phases[phase] = {"records": references,
                         "counts": dict(Counter(r["category"] for r in references)),
                         "secondary_counts": dict(Counter(r["secondary_category"] for r in references if r["secondary_category"] is not None)),
                         "transitions": dict(Counter(r["chord_category"]+" -> "+r["category"] for r in references))}
    return {"step": step, "endpoint_step": step+1, "start_geometry_sha256": _independent_digest(frame["geometry"]),
            "baseline_frame_sha256": _independent_digest(baseline), "blocks": blocks,
            "stats": dict(stats), "pairs": [expected_pair], "phases": phases}


def assert_frame_semantics(case, step, pair, ledger):
    """Guard every field of a focused production frame, including aggregation."""
    expected = independent_frame_expected(case, step, pair)
    assert set(ledger) == set(expected), "M5a2 frame top-level schema"
    for field in ("step", "endpoint_step", "start_geometry_sha256", "baseline_frame_sha256", "blocks", "stats"):
        assert ledger[field] == expected[field], "M5a2 frame independent "+field
    assert len(ledger["pairs"]) == 1, "M5a2 frame focused pair conservation"
    assert_ledger_semantics(case, step, pair, ledger)
    assert set(ledger["phases"]) == set(expected["phases"]), "M5a2 frame phase schema"
    for phase, target in expected["phases"].items():
        actual = ledger["phases"][phase]
        assert set(actual) == set(target), "M5a2 frame phase field schema"
        for field in ("counts", "secondary_counts", "transitions"):
            assert actual[field] == target[field], "M5a2 frame independent phase "+field


@pytest.mark.parametrize("case,step,pair", CASES)
def test_live_focused_frame_aggregates_and_blocks_match_independent_semantics(case, step, pair):
    frame, sg, eg, baseline, _ = real_inputs(case, step, pair)
    live = _json(replay.frame_result(frame, sg, eg, baseline))
    assert_frame_semantics(case, step, pair, live)


@pytest.mark.parametrize("kind", ("swapped_stat_buckets", "wrong_block_center", "phase_counts_use_chord"))
def test_frame_aggregate_internal_mutants_hit_named_semantic_guards(kind, monkeypatch, tmp_path):
    from m5a2_replay_mutations import MUTATIONS, inject, run_guard
    inject(kind, monkeypatch)
    with pytest.raises(AssertionError, match=MUTATIONS[kind][3]):
        run_guard(kind, tmp_path, full_freeze=False)
