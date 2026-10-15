"""Independent A5 tuple7 accounting review, without geometry oracle sharing.

Expected labels follow literal padded-ring identities and df.c's slot contract:
VE lock-length hints have m6=0; complete common-edge slots have m6>0; VV's
second three-point reference is separately tagged. No geometry helper provides
an expected answer. Runtime binding is tested separately in policy_binding.
"""
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import m5b_robust_replay as replay


@pytest.mark.parametrize("raw,secondary,shared", (
    ([0, 2, 7, 8, 3, 0, 0], None, None),
    ([0, 2, 7, 8, 0, 3, 0], None, None),
    ([0, 2, 7, 8, 7, 3, 2], None, ("VE", 7, 2, 3)),
    ([1, 2, 7, 8, 7, 3, 2], ("VE", 7, 2, 3), None),
    ([1, 2, 7, 8, 7, 0, 1], ("VE", 7, 0, 1), None),
    ([0, 2, 7, 8, 7, 3, 4], None, ("VE", 7, 0, 3)),
))
def test_lock_length_hints_vv_second_and_complete_common_slots_are_not_conflated(raw, secondary, shared):
    blocks = [dict(vertex_ids=[0, 1, 2, 3]), dict(vertex_ids=[6, 7, 8, 9])]
    row = dict(raw=raw, pair=[1, 2], primary=["VE", 2, 7, 8])
    result = replay.canonical_legacy_rows([row], blocks)[0]
    assert result["secondary"] == secondary, "M5c VV second reference must not include VE lock hints or common slots"
    assert result["shared_edge"] == shared, "M5c common-edge slot requires m6 and valid complete geometry identities"


@pytest.mark.parametrize("slot", ((7, 0, 2), (7, 1, 1), (1, 2, 3), (7, 2, 8), (13, 2, 3)))
def test_malformed_complete_slots_fail_loud_instead_of_entering_all_reference_counts(slot):
    blocks = [dict(vertex_ids=[0, 1, 2, 3]), dict(vertex_ids=[6, 7, 8, 9]),
              dict(vertex_ids=[12, 13, 14, 15])]
    row = dict(raw=[0, 2, 7, 8, *slot], primary=["VE", 2, 7, 8])
    with pytest.raises(ValueError, match="opposite-block vertex and nondegenerate adjacent edge"):
        replay.canonical_legacy_rows([row], blocks)


def test_all_slots_and_formal_reference_answers_remain_distinct_even_when_common_slot_hits():
    feature = ("VE", 7, 2, 3)
    result = dict(classification="ROBUST_SINGLE_FIRST_COVER", p1=dict(features=(feature,)))
    common = dict(primary=("VE", 2, 7, 8), secondary=None, shared_edge=feature)
    formal = dict(primary=("VE", 2, 7, 8), secondary=feature, shared_edge=None)
    for row, formal_missing in ((common, 1), (formal, 0)):
        counts = replay.legacy_counts(result, {phase: [row] for phase in replay.PHASES})
        for phase in replay.PHASES:
            assert counts[phase+":ROBUST_FIRST_COVER_NOT_SELECTED"] == 1
            assert counts[phase+":FORMAL_ALL_FIRST_COVER_NOT_SELECTED"] == formal_missing
            assert counts[phase+":ALL_FIRST_COVER_NOT_SELECTED"] == 0
            assert counts[phase+":ROBUST_CONTACT_MISSING_PAIR"] == 0
    absent = replay.legacy_counts(result, {phase: [] for phase in replay.PHASES})
    for phase in replay.PHASES:
        assert absent[phase+":ROBUST_CONTACT_MISSING_PAIR"] == 1
        assert absent[phase+":FORMAL_ALL_FIRST_COVER_NOT_SELECTED"] == 1
        assert absent[phase+":ALL_FIRST_COVER_NOT_SELECTED"] == 1


def test_reference_row_totals_do_not_collapse_duplicates_into_pair_counts():
    feature = ("VE", 7, 2, 3)
    row = dict(primary=feature, secondary=feature, shared_edge=None)
    result = dict(classification="ROBUST_SINGLE_FIRST_COVER", p1=dict(features=(feature,)))
    counts = replay.legacy_counts(result, {phase: [row, row] for phase in replay.PHASES})
    for phase in replay.PHASES:
        assert counts[phase+":PRIMARY_REFERENCE_TOTAL"] == counts[phase+":FIRST_COVER_MATCH"] == 2
        assert counts[phase+":SECONDARY_REFERENCE_TOTAL"] == counts[phase+":SECONDARY_FIRST_COVER_MATCH"] == 2
        assert counts[phase+":ROBUST_CONTACT_MISSING_PAIR"] == counts[phase+":ALL_FIRST_COVER_NOT_SELECTED"] == 0


def test_padded_alias_labels_are_equivariant_under_vertex_renumbering_and_block_order():
    blocks = [dict(vertex_ids=[1, 2, 3, 4]), dict(vertex_ids=[7, 8, 9, 10])]
    raw = [0, 2, 11, 8, 7, 4, 5]
    row = dict(raw=raw, primary=["VE", 2, 7, 8])
    original = replay.canonical_legacy_rows([row], blocks)[0]
    shifted = [dict(vertex_ids=[x+1000 for x in b["vertex_ids"]]) for b in reversed(blocks)]
    changed = dict(raw=[raw[0], *(v+1000 for v in raw[1:])], primary=["VE", 1002, 1007, 1008])
    result = replay.canonical_legacy_rows([changed], shifted)[0]
    assert result["shared_edge"] == (original["shared_edge"][0], *(v+1000 for v in original["shared_edge"][1:]))
    assert result["secondary"] is original["secondary"] is None
