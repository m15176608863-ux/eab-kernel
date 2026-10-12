"""M4a VV identity gates: oracle uses explicit topology, no eab geometric primitives.

The synthetic oracle names two corner ids before constructing df05's two reference
triples. It does not call the reader's intersection helper to construct expectations.
"""

from __future__ import annotations

import csv
from fractions import Fraction
from pathlib import Path

import pytest

from eab.contact_record import CoverType
from eab.readers import bdda_df


FIX = Path(__file__).resolve().parents[1] / "fixtures" / "bdda_df"
HEADER = "step,contact,mtype,p1,p2,p3,m4,m5,m6,m0_0,m0_2,o2,o3,o4,o5"


def _bb52_gate():
    rows = [r for r in bdda_df.load_records(FIX / "bb52_N3") if r.cover == CoverType.VV]
    assert len(rows) == 3
    for r in rows:
        assert {r.feature_a.index, r.feature_b.index} == {125, 171}, "VV_CORNER_IDENTITY"
        assert r.extra["raw_p2"] == 126


def test_bb52_vv_reader_uses_shared_corner_not_reference_edge_endpoint():
    _bb52_gate()


def _write_case(path, six):
    path.mkdir(exist_ok=True)
    (path / "bdda_debug_contacts.csv").write_text(
        HEADER + "\n" + ",".join(map(str, (1, 1, 1, *six, 0, 1, 0, 0, 0, 0))) + "\n",
        encoding="utf-8",
    )
    # 13 aliases 10; use the same alias on neither, either or both references.
    (path / "bdda_debug_verts.csv").write_text(
        "step,block,vidx,x,y\n"
        "1,1,10,0,0\n1,1,11,2,0\n1,1,12,0,2\n1,1,13,0,0\n"
        "1,2,20,0,0\n1,2,21,1,3\n1,2,22,-2,1\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize("main,second", [
    ((10, 21, 20), (20, 10, 12)),
    ((10, 21, 20), (10, 20, 22)),
    ((20, 11, 10), (20, 10, 12)),
    ((20, 11, 10), (10, 20, 22)),
])
@pytest.mark.parametrize("swap", [False, True])
@pytest.mark.parametrize("alias", [False, True])
def test_vv_identity_survives_both_reference_branches_half_swap_and_alias(tmp_path, main, second, swap, alias):
    if swap:
        main, second = second, main
    if alias:
        main = tuple(13 if v == 10 else v for v in main)
    _write_case(tmp_path, main + second)
    r, = bdda_df.load_records(tmp_path)
    assert {r.feature_a.index, r.feature_b.index} == {10, 20}, "VV_CORNER_IDENTITY"
    assert {r.feature_a.block, r.feature_b.block} == {1, 2}


@pytest.mark.parametrize("six", [
    (10, 21, 20, 22, 11, 12),   # no shared corners
    (10, 21, 20, 22, 20, 12),   # just one shared corner
    (10, 21, 20, 10, 21, 20),   # all three shared, no unique opposite corner
    (10, 11, 12, 10, 11, 20),   # two shared corners, but on the same block
    (10, 21, 20, 21, 20, 12),   # primary vertex is not a shared corner
])
def test_malformed_vv_references_fail_instead_of_guessing_p2(tmp_path, six):
    _write_case(tmp_path, six)
    with pytest.raises(ValueError, match="VV reference"):
        bdda_df.load_records(tmp_path)


def test_real_fixture_vv_opposite_corner_can_be_either_reference_edge_endpoint():
    total = old_p2_wrong = unresolved = 0
    for d in sorted(FIX.iterdir()):
        p = d / "bdda_debug_contacts.csv"
        if not p.exists():
            continue
        with p.open(newline="", encoding="utf-8") as fh:
            raw = {(int(r["step"]), int(r["contact"])): r for r in csv.DictReader(fh)}
        aliases, coordinate_id = {}, {}
        vertices = []
        if (d / "bdda_debug_verts.csv").exists():
            with (d / "bdda_debug_verts.csv").open(newline="", encoding="utf-8") as fh:
                vertices = list(csv.DictReader(fh))
        for v in sorted(vertices, key=lambda v: int(v["vidx"])):
            key = (int(v["step"]), int(v["block"]), Fraction(v["x"]), Fraction(v["y"]))
            vid = int(v["vidx"])
            aliases[(int(v["step"]), vid)] = coordinate_id.setdefault(key, vid)
        for r in bdda_df.load_records(d):
            if r.cover != CoverType.VV:
                continue
            c = raw[(r.step, r.contact_index)]
            # Independent exact decimal-coordinate aliasing, no production geometry helper.
            def corner(k):
                return aliases.get((r.step, int(c[k])), int(c[k]))
            primary = {corner(k) for k in ("p1", "p2", "p3")}
            secondary = {corner(k) for k in ("m4", "m5", "m6")}
            shared = primary & secondary
            assert len(shared) == 2 and corner("p1") in shared
            if r.feature_a is None:
                # The historical sensor step 2 has neither verts nor df18 block ids.
                assert r.feature_b is None and r.extra["_blocks_unknown"]
                unresolved += 1
            else:
                assert {r.feature_a.index, r.feature_b.index} == shared
            total += 1
            old_p2_wrong += corner("p2") not in shared
    assert (total, old_p2_wrong) == (180, 124)
    assert unresolved == 1


def test_vv_corner_gate_kills_the_original_reader_mapping(monkeypatch):
    # Mutate inside the load_records path, not by altering its output afterward.
    monkeypatch.setattr(bdda_df, "_vv_opposite_vertex",
                        lambda c, sg, block_a, block_b: sg.canon(int(c["p2"])))
    with pytest.raises(AssertionError, match="VV_CORNER_IDENTITY"):
        _bb52_gate()
