"""B semantic gates: literal tuple identities and rational dot/determinants.

Independent oracle imports only stdlib; no production geometry/normalization
primitive computes expected features or invariance. Frozen first labels and
certificate flags are observation inputs, not an independent R3 oracle.
"""
from copy import deepcopy
from fractions import Fraction as F
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import m5d_wording_audit as audit
import m5b_robust_replay as production


def test_certified_nineteen_are_two_row_near_parallel_ve_not_vv_or_crowded():
    observed = audit.audit()
    certified = [r for r in observed["rows"] if r["certified_union"]]
    assert len(certified) == 19
    for row in certified:
        for phase in audit.PHASES:
            assert len(row["phases"][phase]["rows"]) == 2
            assert all(r["raw"][0] == 0 for r in row["phases"][phase]["rows"])
            assert F(row["phases"][phase]["sin_squared"]) < F(1, 300)
    for row in observed["rows"]:
        raw = row["phases"]["raw_df05"]["rows"]
        if any(r["raw"][0] == 1 for r in raw) or len(raw) > 2:
            assert not row["certified_union"], "VV or crowded references must stay unproved"
    assert sum(any(r["raw"][0] == 1 for r in x["phases"]["raw_df05"]["rows"])
               for x in observed["rows"]) == 12
    assert sum(len(x["phases"]["raw_df05"]["rows"]) > 2 for x in observed["rows"]) == 6


def test_case_pair_first_feature_dedup_has_seventeen_not_nineteen_identities():
    observed = audit.audit()
    assert observed["unique_configurations"] == 17
    repeated = [r for r in observed["configurations"] if len(r["steps"]) > 1]
    assert repeated == [dict(case="bb05", pair=(2, 3), features=(("VE", 18, 11, 12),), steps=[3, 11, 20])]
    assert sum(len(r["steps"]) for r in observed["configurations"]) == 19


def test_post_df06_primary_hit_means_promotion_of_retained_angular_candidate():
    observed = audit.audit()
    for row in observed["rows"]:
        if not row["certified_union"]:
            continue
        first = set(map(tuple, row["features"]))
        raw, post = (row["phases"][phase]["rows"] for phase in audit.PHASES)
        assert audit.reference_hits(first, raw)["all_slots"]
        assert audit.reference_hits(first, post)["primary"]
        for before, after in zip(raw, post):
            if before["primary"] != after["primary"]:
                assert before["shared_edge"] == after["primary"]
                assert before["primary"] == after["shared_edge"]
    assert observed["counts"]["certified:raw_df05"]["primary"] == 7
    assert observed["counts"]["certified:post_df06"]["primary"] == 19


def test_unproved_49_remain_nominal_including_bb51_step2_pair3_9_all_slot_miss():
    observed = audit.audit()
    rows = [r for r in observed["rows"] if not r["certified_union"]]
    assert len(rows) == 49
    assert all(r["interpretation"] == "NOMINAL_ONLY_UNCERTIFIED_NO_CONCLUSION" for r in rows)
    for phase, expected in zip(audit.PHASES, ((31, 9, 8, 40, 48), (38, 9, 1, 47, 48))):
        count = observed["counts"]["nominal_unproved:"+phase]
        assert tuple(count[k] for k in ("primary", "vv_second", "common_slot", "formal_all", "all_slots")) == expected
        missing = [r for r in rows if not r["phases"][phase]["hits"]["all_slots"]]
        assert [(r["case"], r["step"], r["pair"]) for r in missing] == [("bb51", 2, [3, 9])]
        assert missing[0]["features"] == [["VE", 93, 149, 153]]
        assert not missing[0]["phases"][phase]["hits"]["missing_pair"]


def test_positive_raw_vv_edge_ids_normalize_to_legal_canonical_zero():
    blocks = [dict(vertex_ids=[0, 1, 2, 3]), dict(vertex_ids=[6, 7, 8, 9])]
    raw = [1, 2, 7, 8, 7, 4, 5]
    assert all(v > 0 for v in raw[1:])
    row = dict(raw=raw, primary=["VE", 2, 7, 8])
    expected = ("VE", 7, 0, 1)  # positive raw 4,5 wrap to retained pad 0,1
    assert audit.decode([row], blocks)[0]["secondary"] == expected
    assert production.canonical_legacy_rows([row], blocks)[0]["secondary"] == expected


def test_all_68_reference_slots_match_independent_literal_oracle():
    observed = audit.audit()
    for row in observed["rows"]:
        blocks = [dict(vertex_ids=ids) for ids in row["canonical_ring_ids"]]
        for phase in audit.PHASES:
            expected = row["phases"][phase]["rows"]
            actual = production.canonical_legacy_rows(expected, blocks)
            assert actual == expected, "M5d all candidate literal slot oracle mismatch"


@pytest.mark.parametrize("scale,translation", ((F(1, 1000), (10**6, -10**6)), (F(10**5), (-1000, 1000))))
def test_near_parallel_description_is_invariant_under_rigid_motion_and_units(scale, translation):
    blocks = [dict(vertex_ids=[1, 2, 3], start=[(0, 0), (4, 1), (0, 2)]),
              dict(vertex_ids=[7, 8, 9], start=[(10, 0), (14, F(6, 5)), (10, 2)])]
    rows = [dict(raw=[0], primary=("VE", 1, 7, 8)), dict(raw=[0], primary=("VE", 7, 1, 2))]
    changed = deepcopy(blocks)
    for block in changed:
        block["start"] = [(scale*(F(3, 5)*x-F(4, 5)*y)+translation[0],
                           scale*(F(4, 5)*x+F(3, 5)*y)+translation[1]) for x, y in block["start"]]
    assert 0 < audit.parallel_measure(rows, blocks) == audit.parallel_measure(rows, changed)
