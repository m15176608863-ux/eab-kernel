"""3DDA tf.cpp 探针 → ContactRecord / PairStageRow。

列头以 C:\\3DDA\\3d-DDA-work\\tf.cpp 原文为准（2026-09-18 核对，行 1332 / 1340）：
  tkb/tf/contact_pair_stage.tsv
    step time block_i block_j contact_start contact_end total_contacts nn_count ne_count np_count ee_count load_bucket
  tkb/tf/retry_contact_pair_probe.tsv
    step time event mr n1 trigger_block top_platen_block contact_index block_a block_b involves_top_pair
    contact_state previous_contact_state contact_entry contact_type gap area normal_force px py pz nx ny nz
    shear_dx shear_dy shear_dz shear_norm status_closed pair_role

编码（tf.cpp 注释 297-336）：contact_type 0 n-n / 1 n-e / 2 n-p / 3 e-e；
contact_state = m0[i][1]（0 open 1 friction 2 s-spring 3 tension 4/5/6 变体），previous = m0[i][3]，
contact_entry = m0[i][0]（当前选中入口的 m[][] 索引）。gap 约定：tf 的 o[i][2]，>0 张开 <0 侵入。
状态 4/5/6 → Mode.UNVERIFIED（归入统一词汇的依据未核实，见 contact_record.TF_MODE）；raw_mode 保留原始码。
执行门：tests/test_tf_reader.py（读取器重算普查 6716 条 / 100% n-p，并与零共用 oracle 逐行对账）。
两个探针都是 HeavyProbe，默认关闭；retry 探针只在重试事件时写、且只写涉及触发块/顶压板的接触
（record_limit 1024）——它不是完整接触列表，是抽样。完整计数在 contact_pair_stage。
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from ..contact_record import TF_COVER, TF_MODE, ContactRecord, CoverType, Mode


@dataclass(slots=True)
class PairStageRow:
    step: int
    time: float
    block_i: int
    block_j: int
    contact_start: int
    contact_end: int
    total_contacts: int
    nn_count: int
    ne_count: int
    np_count: int
    ee_count: int
    load_bucket: str


def _rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def read_pair_stage(path: Path) -> list[PairStageRow]:
    out = []
    for r in _rows(path):
        out.append(PairStageRow(
            step=int(r["step"]), time=float(r["time"]), block_i=int(r["block_i"]), block_j=int(r["block_j"]),
            contact_start=int(r["contact_start"]), contact_end=int(r["contact_end"]),
            total_contacts=int(r["total_contacts"]), nn_count=int(r["nn_count"]), ne_count=int(r["ne_count"]),
            np_count=int(r["np_count"]), ee_count=int(r["ee_count"]), load_bucket=r["load_bucket"],
        ))
    return out


_PROBE_CORE = {"step", "time", "block_a", "block_b", "contact_index", "contact_state", "previous_contact_state",
               "contact_entry", "contact_type", "gap", "area", "normal_force", "px", "py", "pz", "nx", "ny", "nz",
               "shear_dx", "shear_dy", "shear_dz"}


def load_records(probe_path: Path) -> list[ContactRecord]:
    out: list[ContactRecord] = []
    for r in _rows(probe_path):
        ctype = int(r["contact_type"])
        state = int(r["contact_state"])
        prev = int(r["previous_contact_state"])
        extra = {k: v for k, v in r.items() if k not in _PROBE_CORE}
        extra["time"] = float(r["time"])
        rec = ContactRecord(
            source="tf", step=int(r["step"]), contact_index=int(r["contact_index"]),
            block_a=int(r["block_a"]), block_b=int(r["block_b"]),
            cover=TF_COVER.get(ctype, CoverType.UNKNOWN), raw_cover=ctype,
            ref_points=((float(r["px"]), float(r["py"]), float(r["pz"])),),
            normal=(float(r["nx"]), float(r["ny"]), float(r["nz"])),
            length_or_area=float(r["area"]),
            mode=TF_MODE.get(state, Mode.UNKNOWN), raw_mode=state,
            mode_prev=TF_MODE.get(prev, Mode.UNKNOWN), raw_mode_prev=prev,
            entrance_index=int(r["contact_entry"]),
            gap=float(r["gap"]),
            shear=(float(r["shear_dx"]), float(r["shear_dy"]), float(r["shear_dz"])),
            normal_force=float(r["normal_force"]),
            extra=extra,
        )
        out.append(rec)
    return out
