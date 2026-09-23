"""tf.cpp（3DDA）读取器的执行门（审查盲区 5，2026-09-21）。

此前 tf 读取路径只被 test_readers_roundtrip 执行过，唯一的语义断言是 cover ∈ {VF,EE,NN,NE}——
任何映射都能过。这里：
  (1) 用读取器（tf_probe.read_pair_stage / load_records）**重算**普查，钉 docs/sibling_observations.md
      里的数字：三份夹具共 6716 条接触、100% n-p（stage 5296 + fine 探针 864 + medium 探针 556）；
  (2) 用一条与读取器零共用的 oracle（按字节切行、按表头名定列，不用 csv 模块、不用 tf_probe）逐行对账；
  (3) TF_MODE 对状态 4/5/6 的折叠：docs/sibling_observations.md 没有 tf.cpp 行号引文为它作证，
      所以映射标 UNVERIFIED，不断言 SLIDING/LOCKED；原始码照旧保留在 raw_mode。
"""

import sys
from collections import Counter
from pathlib import Path

import pytest

from eab import TF_MODE, Mode
from eab.readers import tf_probe

ROOT = Path(__file__).resolve().parents[1]
TF = ROOT / "fixtures" / "tf"
STAGE = TF / "smoke_cpu_20260722" / "contact_pair_stage.tsv"
PROBES = {"sandstone_fine_20260712": 864, "sandstone_medium_20260712": 556}
pytestmark = pytest.mark.skipif(not STAGE.exists(), reason="tf fixtures missing")


def _raw_table(path: Path) -> list[dict[str, str]]:
    """零共用 oracle：按字节切行（兼容 CRLF）、按制表符切列、按表头名取列。"""
    lines = [ln for ln in path.read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n") if ln]
    head = lines[0].split("\t")
    return [dict(zip(head, ln.split("\t"))) for ln in lines[1:]]


def _census(stage_rows, probe_recs: dict[str, list]) -> dict:
    kinds = Counter()
    for r in stage_rows:
        kinds["n-n"] += r.nn_count
        kinds["n-e"] += r.ne_count
        kinds["n-p"] += r.np_count
        kinds["e-e"] += r.ee_count
    stage_total = sum(r.total_contacts for r in stage_rows)
    names = {0: "n-n", 1: "n-e", 2: "n-p", 3: "e-e"}
    for recs in probe_recs.values():
        for rec in recs:
            kinds[names[rec.raw_cover]] += 1
    return {"stage": stage_total, "probes": {k: len(v) for k, v in probe_recs.items()},
            "total": stage_total + sum(len(v) for v in probe_recs.values()), "kinds": kinds}


def _assert_census(c):
    assert c["stage"] == 5296
    assert c["probes"] == PROBES
    assert c["total"] == 6716
    assert c["kinds"]["n-p"] == 6716 and c["kinds"]["n-p"] == c["total"]          # 100% n-p
    assert c["kinds"]["n-n"] == c["kinds"]["n-e"] == c["kinds"]["e-e"] == 0


def _load():
    return (tf_probe.read_pair_stage(STAGE),
            {k: tf_probe.load_records(TF / k / "retry_contact_pair_probe.tsv") for k in PROBES})


def test_tf_census_recomputed_through_the_readers():
    stage, probes = _load()
    _assert_census(_census(stage, probes))
    assert all(rec.cover.value == "VF" for recs in probes.values() for rec in recs)


def test_tf_readers_agree_row_by_row_with_a_zero_shared_oracle():
    stage, probes = _load()
    raw = _raw_table(STAGE)
    assert len(raw) == len(stage)
    for r, o in zip(stage, raw):
        assert (r.step, r.block_i, r.block_j, r.total_contacts, r.nn_count, r.ne_count, r.np_count, r.ee_count) == \
            tuple(int(o[k]) for k in ("step", "block_i", "block_j", "total_contacts", "nn_count", "ne_count",
                                      "np_count", "ee_count"))
    for k, recs in probes.items():
        raw = _raw_table(TF / k / "retry_contact_pair_probe.tsv")
        assert len(raw) == len(recs)
        for rec, o in zip(recs, raw):
            assert (rec.step, rec.block_a, rec.block_b, rec.raw_cover, rec.raw_mode, rec.raw_mode_prev,
                    rec.entrance_index) == tuple(int(o[c]) for c in (
                        "step", "block_a", "block_b", "contact_type", "contact_state", "previous_contact_state",
                        "contact_entry"))
            assert rec.gap == float(o["gap"]) and rec.length_or_area == float(o["area"])


def test_tf_census_tool_agrees_with_the_readers():
    sys.path.insert(0, str(ROOT / "tools"))
    import tf_census
    c = tf_census.census()
    assert c["smoke_cpu_20260722/stage"]["contacts"] == 5296
    assert c["smoke_cpu_20260722/stage"]["by_kind"]["np_count"] == 5296
    for k, n in PROBES.items():
        assert c[f"{k}/probe"]["rows"] == n and c[f"{k}/probe"]["by_kind"] == {"n-p": n}


@pytest.mark.parametrize("cut", ["drop_last_probe_row", "drop_first_stage_row", "cover_2_as_ee"])
def test_tf_census_gate_has_teeth(cut, monkeypatch):
    """门要有牙：读取器丢一行、或把候选类映射错，普查门必须红。"""
    stage, probes = _load()
    if cut == "drop_last_probe_row":
        probes["sandstone_fine_20260712"] = probes["sandstone_fine_20260712"][:-1]
    elif cut == "drop_first_stage_row":
        stage = stage[1:]
    else:
        import dataclasses
        probes = {k: [dataclasses.replace(r, raw_cover=3) for r in v] for k, v in probes.items()}
    with pytest.raises(AssertionError):
        _assert_census(_census(stage, probes))


# ---------------------------------------------------------------- TF_MODE 的依据

def test_tf_mode_states_4_5_6_are_unverified_not_asserted():
    """状态 4/5/6（tf.cpp 源码注释名 2f-friction / 2f-lock / top-lock）折进 SLIDING/LOCKED 没有台账依据：
    docs/sibling_observations.md 没有这几个状态码的 tf.cpp 行号引文。映射如实标 UNVERIFIED。"""
    assert {s: TF_MODE[s].value for s in (4, 5, 6)} == {4: "UNVERIFIED", 5: "UNVERIFIED", 6: "UNVERIFIED"}
    assert (TF_MODE[0], TF_MODE[1], TF_MODE[2], TF_MODE[3]) == (Mode.OPEN, Mode.SLIDING, Mode.LOCKED, Mode.TENSION)


def test_tf_unverified_state_keeps_its_raw_code(tmp_path):
    head = ("step time event mr n1 trigger_block top_platen_block contact_index block_a block_b involves_top_pair "
            "contact_state previous_contact_state contact_entry contact_type gap area normal_force px py pz nx ny nz "
            "shear_dx shear_dy shear_dz shear_norm status_closed pair_role").split()
    rows = []
    for st in (4, 5, 6, 1):
        v = {k: "0" for k in head}
        v.update(contact_state=str(st), previous_contact_state=str(st), contact_type="2", event="retry",
                 pair_role="x", time="0.0")
        rows.append("\t".join(v[k] for k in head))
    p = tmp_path / "probe.tsv"
    p.write_text("\t".join(head) + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    recs = tf_probe.load_records(p)
    assert [(r.mode.value, r.raw_mode) for r in recs] == [("UNVERIFIED", 4), ("UNVERIFIED", 5), ("UNVERIFIED", 6),
                                                          ("SLIDING", 1)]


def test_tf_fixtures_never_exercise_states_4_5_6():
    """如实记录：入库的三份夹具里只出现状态 1、2（fine 探针 860×2 + 4×1，medium 556×2），
    所以 4/5/6 的 UNVERIFIED 改动不改变任何现有记录的 mode。"""
    _, probes = _load()
    states = Counter(r.raw_mode for recs in probes.values() for r in recs)
    prev = Counter(r.raw_mode_prev for recs in probes.values() for r in recs)
    assert states == Counter({2: 1416, 1: 4}) and prev == states
