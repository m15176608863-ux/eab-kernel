"""WO-M4c-fix replay semantics and dependency-scope guards.

PD oracle imports: none. Its exact expected exits and 24 features follow from
four axis translations of two coincident unit squares, not from production
geometry/PD/cone primitives. The tested path is frame_result -> _pd -> ledger.
"""
import ast
import inspect
from pathlib import Path

import pytest

from test_m4c_replay import replay, small_snapshot


def _square_exit_features():
    # (A edge, B edge, matched endpoints), in exits (-1,0), (0,-1),
    # (0,1), (1,0). Each opposed edge contributes four VE and two VV.
    opposed = (((2, 3), (5, 8), ((2, 5), (3, 8))),
               ((3, 4), (5, 6), ((3, 6), (4, 5))),
               ((1, 2), (7, 8), ((1, 8), (2, 7))),
               ((1, 4), (6, 7), ((1, 6), (4, 7))))
    expected = set()
    for edge_a, edge_b, vertices in opposed:
        expected.update(("VE", v, *edge_b) for v in edge_a)
        expected.update(("VE", v, *edge_a) for v in edge_b)
        expected.update(("VV", a, b) for a, b in vertices)
    assert len(expected) == 24
    return tuple(sorted(expected))


def test_pd_tied_nearest_points_have_complete_feature_union():
    frame = small_snapshot()[2]
    # One primary reference at each of the four equally short escape points.
    references = [[0, 2, 5, 8, 0, 0, 0], [0, 3, 5, 6, 0, 0, 0],
                  [0, 1, 7, 8, 0, 0, 0], [0, 1, 6, 7, 0, 0, 0]]
    frame["raw_df05"] = references
    frame["post_df06"] = references
    geometry = replay.snapshot.geometry_from_frame(frame)
    result = replay.frame_result(frame, geometry, geometry, pd_edge_limit=0)
    pair = result["pairs"][0]
    pd = pair["pd"]
    assert pair["initial_state"] == 1 and pd["status"] == "EVALUATED"
    assert pd["squared"] == "1"
    assert pd["points"] == [["-1", "0"], ["0", "-1"], ["0", "1"], ["1", "0"]]
    assert pd["features"] == _square_exit_features(), "PD all-tie feature union must include all four exits"


def test_pd_tied_nearest_points_are_all_classified_as_pd_match():
    frame = small_snapshot()[2]
    # One primary reference at each of the four equally short escape points.
    references = [[0, 2, 5, 8, 0, 0, 0], [0, 3, 5, 6, 0, 0, 0],
                  [0, 1, 7, 8, 0, 0, 0], [0, 1, 6, 7, 0, 0, 0]]
    frame["raw_df05"] = references
    frame["post_df06"] = references
    geometry = replay.snapshot.geometry_from_frame(frame)
    result = replay.frame_result(frame, geometry, geometry, pd_edge_limit=0)
    for phase in replay.PHASES:
        records = result["phases"][phase]["records"]
        assert tuple(row["category"] for row in records) == ("INITIAL_OVERLAP_PD_MATCH",)*4, "PD all-tie categories must not silently become OTHER_FEATURE"
        assert result["phases"][phase]["counts"] == {"INITIAL_OVERLAP_PD_MATCH": 4}


def test_pd_first_tie_only_internal_mutation_hits_both_semantic_guards(monkeypatch):
    guards = ((test_pd_tied_nearest_points_have_complete_feature_union, "PD all-tie feature union"),
              (test_pd_tied_nearest_points_are_all_classified_as_pd_match, "PD all-tie categories"))
    for guard, _ in guards:
        guard()  # Control green, before the mutation is installed.
    source = inspect.getsource(replay._pd)
    old = "for point in value.tied_exact_points:"
    assert source.count(old) == 1
    # Compile the defect INTO _pd's loop; do not fabricate or trim its output.
    mutated = source.replace(old, "for point in value.tied_exact_points[:1]:")
    namespace = dict(vars(replay))
    exec(compile(mutated, "<m4c-pd-first-tie-only-mutant>", "exec"), namespace)
    with monkeypatch.context() as patch:
        patch.setattr(replay, "_pd", namespace["_pd"])
        for guard, message in guards:
            with pytest.raises(AssertionError, match=message):
                guard()  # Red at the named union/category assertion, no hashes.
    for guard, _ in guards:
        guard()  # Restored green.


@pytest.mark.parametrize("zero_vertex,has_second", [(2, True), (3, True), (5, False)])
def test_vv_second_reference_presence_is_m4_positive_even_with_vertex_zero(zero_vertex, has_second):
    """b-DDA bdda2/core/contacts.hpp:80 has_second(k) is m4_[k] > 0.

    This copied contract is read-only evidence, not a runtime sibling import.
    The m5=0 and m6=0 grids must retain the second reference; m4=0 must not.
    """
    rows = small_snapshot()
    rename = lambda v: 0 if v == zero_vertex else v
    for frame in rows[1:3]:
        for row in frame["geometry"]:
            row[1] = rename(row[1])
        frame["raw_df05"] = [[1, *map(rename, (2, 8, 5, 5, 2, 3))]]
        frame["post_df06"] = []
    sg, eg = (replay.snapshot.geometry_from_frame(row) for row in rows[1:3])
    result = replay.frame_result(rows[1], sg, eg)
    phase = result["phases"]["raw_df05"]
    record = phase["records"][0]
    if has_second:
        expected = ("VE", rename(5), *sorted((rename(2), rename(3))))
        assert record["secondary_reference"] == expected, "m5/m6 vertex zero must not suppress VV second reference"
        assert record["secondary_category"] == "FIRST_COVER_MATCH"
        assert phase["secondary_counts"] == {"FIRST_COVER_MATCH": 1}
    else:
        assert record["secondary_reference"] is None, "m4=0 is the has_second absence sentinel"
        assert record["secondary_category"] is None and phase["secondary_counts"] == {}


def test_vv_all_nonzero_internal_mutation_loses_vertex_zero_reference(monkeypatch):
    guard = test_vv_second_reference_presence_is_m4_positive_even_with_vertex_zero
    guard(2, True)
    guard(3, True)
    source = inspect.getsource(replay.frame_result)
    old = "if raw[0] == 1 and raw[4] > 0:"
    assert source.count(old) == 1
    source = source.replace(old, "if raw[0] == 1 and all(raw[k] for k in (4, 5, 6)):")
    namespace = dict(vars(replay))
    exec(compile(source, "<m4c-vv-all-nonzero-mutant>", "exec"), namespace)
    with monkeypatch.context() as patch:
        patch.setattr(replay, "frame_result", namespace["frame_result"])
        for vertex in (2, 3):
            with pytest.raises(AssertionError, match="m5/m6 vertex zero must not suppress"):
                guard(vertex, True)
    guard(2, True)
    guard(3, True)

