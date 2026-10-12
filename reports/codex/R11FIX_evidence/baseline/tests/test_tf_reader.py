"""tf.cpp（3DDA）读取器的执行门（审查盲区 5，2026-09-21）。

此前 tf 读取路径只被 test_readers_roundtrip 执行过，唯一的语义断言是 cover ∈ {VF,EE,NN,NE}——
任何映射都能过。这里：
  (1) 用读取器（tf_probe.read_pair_stage / load_records）**重算**普查，钉 docs/sibling_observations.md
      里的数字：三份夹具共 6716 条接触、100% n-p（stage 5296 + fine 探针 864 + medium 探针 556）；
  (2) 用一条与读取器零共用的 oracle（按字节切行、按表头名定列，不用 csv 模块、不用 tf_probe）逐行、逐字段
      精确对账——含法向、接触点、法向力、剪切、contact_index 与全部余项列（G6 major 16 之前只比拓扑/计数/gap/area）；
      牙注入读取器源码本身（`_mutant_reader`），不在读取器产出之后改数据；
  (3) TF_MODE 对状态 4/5/6 的折叠：docs/sibling_observations.md 没有 tf.cpp 行号引文为它作证，
      所以映射标 UNVERIFIED，不断言 SLIDING/LOCKED；原始码照旧保留在 raw_mode。
"""
from construction_oracle import scalar_exact

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


_STAGE_INT = ("step", "block_i", "block_j", "contact_start", "contact_end", "total_contacts", "nn_count", "ne_count",
              "np_count", "ee_count")
_PROBE_CORE_COLS = {"step", "time", "block_a", "block_b", "contact_index", "contact_state", "previous_contact_state",
                    "contact_entry", "contact_type", "gap", "area", "normal_force", "px", "py", "pz", "nx", "ny", "nz",
                    "shear_dx", "shear_dy", "shear_dz"}


# 状态码 → Mode 的期望映射，测试自带一份（零共用：不从 eab 导入 TF_MODE）。依据见 contact_record.TF_MODE 的注释。
_TF_MODE_ORACLE = {0: "OPEN", 1: "SLIDING", 2: "LOCKED", 3: "TENSION", 4: "UNVERIFIED", 5: "UNVERIFIED", 6: "UNVERIFIED"}


def _assert_rows_agree(stage, probes):
    """逐行、逐字段、精确相等地对账（G6 major 16）：原先只比拓扑/计数/标量 gap·area，法向、接触点、法向力、
    剪切、contact_index 五个变异全套照绿。现在 ContactRecord 的每个物理字段都对原始 TSV 独立解析的值做
    **精确浮点相等**比较（同一个十进制串经 float() 只有一个结果，不需要容差），余项列逐一比对 extra。
    oracle 与读取器零共用：`_raw_table` 按字节切行、按表头名取列，不用 csv 模块、不用 tf_probe。
    每条断言的消息首项是字段名——牙测试据此确认"红在看护该字段的那条断言上"。"""
    raw = _raw_table(STAGE)
    assert len(raw) == len(stage), ("stage rows", len(stage), len(raw))
    for r, o in zip(stage, raw):
        for k in _STAGE_INT:
            assert getattr(r, k) == int(o[k]), ("stage " + k, getattr(r, k), o[k])
        assert r.time == scalar_exact(o["time"]) and r.load_bucket == o["load_bucket"], ("stage time/bucket", r, o)
    for name, recs in probes.items():
        raw = _raw_table(TF / name / "retry_contact_pair_probe.tsv")
        assert len(raw) == len(recs), ("probe rows", name, len(recs), len(raw))
        for rec, o in zip(recs, raw):
            f = {c: scalar_exact(o[c]) for c in ("gap", "area", "normal_force", "px", "py", "pz", "nx", "ny", "nz",
                                          "shear_dx", "shear_dy", "shear_dz", "time")}
            assert rec.source == "tf", ("source", rec.source)
            assert rec.step == int(o["step"]), ("step", rec.step, o["step"])
            assert rec.contact_index == int(o["contact_index"]), ("contact_index", rec.contact_index, o["contact_index"])
            assert (rec.block_a, rec.block_b) == (int(o["block_a"]), int(o["block_b"])), ("blocks", rec, o)
            assert rec.raw_cover == int(o["contact_type"]), ("raw_cover", rec.raw_cover, o["contact_type"])
            assert rec.cover.value == {"0": "NN", "1": "NE", "2": "VF", "3": "EE"}[o["contact_type"]], ("cover", rec.cover)
            assert (rec.raw_mode, rec.raw_mode_prev) == (int(o["contact_state"]), int(o["previous_contact_state"])), \
                ("state", rec.raw_mode, rec.raw_mode_prev, o["contact_state"], o["previous_contact_state"])
            assert (rec.mode.value, rec.mode_prev.value) == (_TF_MODE_ORACLE[int(o["contact_state"])],
                                                             _TF_MODE_ORACLE[int(o["previous_contact_state"])]), \
                ("mode", rec.mode, rec.mode_prev, o["contact_state"], o["previous_contact_state"])
            assert rec.entrance_index == int(o["contact_entry"]), ("entrance_index", rec.entrance_index, o["contact_entry"])
            assert rec.gap == f["gap"], ("gap", rec.gap, o["gap"])
            assert rec.length_or_area == f["area"], ("area", rec.length_or_area, o["area"])
            assert rec.normal_force == f["normal_force"], ("normal_force", rec.normal_force, o["normal_force"])
            assert rec.ref_points == ((f["px"], f["py"], f["pz"]),), ("ref_points", rec.ref_points, (o["px"], o["py"], o["pz"]))
            assert rec.normal == (f["nx"], f["ny"], f["nz"]), ("normal", rec.normal, (o["nx"], o["ny"], o["nz"]))
            assert rec.shear == (f["shear_dx"], f["shear_dy"], f["shear_dz"]), \
                ("shear", rec.shear, (o["shear_dx"], o["shear_dy"], o["shear_dz"]))
            want_extra = {k: v for k, v in o.items() if k not in _PROBE_CORE_COLS}
            want_extra["time"] = f["time"]
            assert rec.extra == want_extra, ("extra", rec.extra, want_extra)


def test_tf_readers_agree_row_by_row_with_a_zero_shared_oracle():
    stage, probes = _load()
    _assert_rows_agree(stage, probes)


def test_tf_census_tool_agrees_with_the_readers():
    sys.path.insert(0, str(ROOT / "tools"))
    import tf_census
    c = tf_census.census()
    assert c["smoke_cpu_20260722/stage"]["contacts"] == 5296
    assert c["smoke_cpu_20260722/stage"]["by_kind"]["np_count"] == 5296
    for k, n in PROBES.items():
        assert c[f"{k}/probe"]["rows"] == n and c[f"{k}/probe"]["by_kind"] == {"n-p": n}


def _mutant_reader(monkeypatch, old: str, new: str):
    """把缺陷注入**读取器源码本身**（AGENTS.md §2：牙要穿过被测路径，不许在它的产出之后追加假数据）：
    对 src/eab/readers/tf_probe.py 做一处文本替换（断言恰好命中一次），编译成一个变异模块，
    再把 tf_probe 的公开入口换成变异版——之后 `_load()` 走的就是有缺陷的解析代码。"""
    import types
    src = Path(tf_probe.__file__).read_text(encoding="utf-8")
    assert src.count(old) == 1, ("mutation site must match exactly once", old)
    name = "eab.readers._tf_probe_mutant"
    mod = types.ModuleType(name)
    mod.__package__ = "eab.readers"
    mod.__file__ = tf_probe.__file__
    monkeypatch.setitem(sys.modules, name, mod)
    exec(compile(src.replace(old, new), tf_probe.__file__, "exec"), mod.__dict__)
    monkeypatch.setattr(tf_probe, "load_records", mod.load_records)
    monkeypatch.setattr(tf_probe, "read_pair_stage", mod.read_pair_stage)


# 变异点：(原文, 变异, 应当报红的断言的字段名)。前五个是 G6 在 8200ba6 上逐一证明"全套照绿"的读取器缺陷。
READER_MUTANTS = {
    "normal_transposed_nz_negated": ('normal=(float(r["nx"]), float(r["ny"]), float(r["nz"]))',
                                     'normal=(float(r["ny"]), float(r["nx"]), -float(r["nz"]))', "normal"),
    "point_xy_transposed": ('ref_points=((float(r["px"]), float(r["py"]), float(r["pz"])),)',
                            'ref_points=((float(r["py"]), float(r["px"]), float(r["pz"])),)', "ref_points"),
    "normal_force_negated": ('normal_force=float(r["normal_force"])', 'normal_force=-float(r["normal_force"])',
                             "normal_force"),
    "contact_index_offset_7": ('contact_index=int(r["contact_index"])', 'contact_index=int(r["contact_index"]) + 7',
                               "contact_index"),
    "shear_xy_transposed": ('shear=(float(r["shear_dx"]), float(r["shear_dy"]), float(r["shear_dz"]))',
                            'shear=(float(r["shear_dy"]), float(r["shear_dx"]), float(r["shear_dz"]))', "shear"),
    "drop_last_probe_row": ("    for r in _rows(probe_path):", "    for r in _rows(probe_path)[:-1]:", "probe rows"),
    "drop_first_stage_row": ("    for r in _rows(path):", "    for r in _rows(path)[1:]:", "stage rows"),
    "cover_2_as_ee": ('ctype = int(r["contact_type"])', 'ctype = 3', "raw_cover"),
    # G6 第二轮 minor：映射后的 mode / mode_prev 没人比，这一个变异让 864 条 fine 探针记录全成 OPEN，全套照绿
    "mode_prev_const_open": ("mode_prev=TF_MODE.get(prev, Mode.UNKNOWN)", "mode_prev=Mode.OPEN", "mode"),
}
# 列对调的变异：夹具里每行 state == prev（见 test_tf_fixtures_never_exercise_states_4_5_6），逐行门在夹具上看不见，
# 由下面 state ≠ prev 的合成行看护
MODE_COLUMN_MUTANTS = {
    "mode_from_prev_column": ("mode=TF_MODE.get(state, Mode.UNKNOWN)", "mode=TF_MODE.get(prev, Mode.UNKNOWN)"),
    "mode_prev_from_state_column": ("mode_prev=TF_MODE.get(prev, Mode.UNKNOWN)",
                                    "mode_prev=TF_MODE.get(state, Mode.UNKNOWN)"),
}


@pytest.mark.parametrize("mut", sorted(READER_MUTANTS))
def test_tf_row_gate_has_teeth_through_the_reader(mut, monkeypatch):
    """门要有牙，且牙穿过读取器：每个读取器源码变异都必须让逐行对账门红，**红在看护该字段的那条断言上**。"""
    old, new, field = READER_MUTANTS[mut]
    _mutant_reader(monkeypatch, old, new)
    stage, probes = _load()
    with pytest.raises(AssertionError) as ei:
        _assert_rows_agree(stage, probes)
    assert str(ei.value).startswith(repr((field,))[:-2] + ","), (mut, str(ei.value)[:120])   # 红在该字段的断言上


@pytest.mark.parametrize("mut", ["drop_last_probe_row", "drop_first_stage_row", "cover_2_as_ee"])
def test_tf_census_gate_has_teeth(mut, monkeypatch):
    """普查门的牙同样穿过读取器（旧版在 `_load()` 返回之后切片 / dataclasses.replace——AGENTS.md 禁止的做法）。"""
    old, new, _ = READER_MUTANTS[mut]
    _mutant_reader(monkeypatch, old, new)
    stage, probes = _load()
    with pytest.raises(AssertionError):
        _assert_census(_census(stage, probes))


# ---------------------------------------------------------------- TF_MODE 的依据

def test_tf_mode_states_4_5_6_are_unverified_not_asserted():
    """状态 4/5/6（tf.cpp 源码注释名 2f-friction / 2f-lock / top-lock）折进 SLIDING/LOCKED 没有台账依据：
    docs/sibling_observations.md 没有这几个状态码的 tf.cpp 行号引文。映射如实标 UNVERIFIED。"""
    assert {s: TF_MODE[s].value for s in (4, 5, 6)} == {4: "UNVERIFIED", 5: "UNVERIFIED", 6: "UNVERIFIED"}
    assert (TF_MODE[0], TF_MODE[1], TF_MODE[2], TF_MODE[3]) == (Mode.OPEN, Mode.SLIDING, Mode.LOCKED, Mode.TENSION)


def _synthetic_probe(tmp_path, states):
    """合成探针表：每行 (contact_state, previous_contact_state)，其余列取占位值。"""
    head = ("step time event mr n1 trigger_block top_platen_block contact_index block_a block_b involves_top_pair "
            "contact_state previous_contact_state contact_entry contact_type gap area normal_force px py pz nx ny nz "
            "shear_dx shear_dy shear_dz shear_norm status_closed pair_role").split()
    rows = []
    for st, pv in states:
        v = {k: "0" for k in head}
        v.update(contact_state=str(st), previous_contact_state=str(pv), contact_type="2", event="retry",
                 pair_role="x", time="0.0")
        rows.append("\t".join(v[k] for k in head))
    p = tmp_path / "probe.tsv"
    p.write_text("\t".join(head) + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return p


_STATE_CHANGES = [(1, 2), (2, 1), (0, 3), (3, 0), (4, 2), (2, 6)]


def _assert_modes_follow_their_own_columns(recs):
    got = [(r.mode.value, r.mode_prev.value, r.raw_mode, r.raw_mode_prev) for r in recs]
    assert got == [(_TF_MODE_ORACLE[s], _TF_MODE_ORACLE[p], s, p) for s, p in _STATE_CHANGES], got


def test_tf_mode_and_mode_prev_are_mapped_from_their_own_columns(tmp_path):
    """state ≠ prev 的合成行（G6 第二轮 minor）：mode 只来自 contact_state、mode_prev 只来自 previous_contact_state。"""
    _assert_modes_follow_their_own_columns(tf_probe.load_records(_synthetic_probe(tmp_path, _STATE_CHANGES)))


@pytest.mark.parametrize("mut", sorted(MODE_COLUMN_MUTANTS))
def test_tf_mode_column_gate_has_teeth(mut, monkeypatch, tmp_path):
    _mutant_reader(monkeypatch, *MODE_COLUMN_MUTANTS[mut])
    with pytest.raises(AssertionError):
        _assert_modes_follow_their_own_columns(tf_probe.load_records(_synthetic_probe(tmp_path, _STATE_CHANGES)))


def test_tf_unverified_state_keeps_its_raw_code(tmp_path):
    recs = tf_probe.load_records(_synthetic_probe(tmp_path, [(4, 4), (5, 5), (6, 6), (1, 1)]))
    assert [(r.mode.value, r.raw_mode) for r in recs] == [("UNVERIFIED", 4), ("UNVERIFIED", 5), ("UNVERIFIED", 6),
                                                          ("SLIDING", 1)]


def test_tf_fixtures_never_exercise_states_4_5_6():
    """如实记录：入库的三份夹具里只出现状态 1、2（fine 探针 860×2 + 4×1，medium 556×2），
    所以 4/5/6 的 UNVERIFIED 改动不改变任何现有记录的 mode。"""
    _, probes = _load()
    states = Counter(r.raw_mode for recs in probes.values() for r in recs)
    prev = Counter(r.raw_mode_prev for recs in probes.values() for r in recs)
    assert states == Counter({2: 1416, 1: 4}) and prev == states
