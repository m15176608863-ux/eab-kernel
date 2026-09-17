"""b-DDA 插桩内核（df_rebuilt.exe, BDDA_KERNEL_MODE=1）dump → ContactRecord。

列头以 D:\\b-DDA\\df\\df.c 原文为准（2026-09-18 核对）：
  bdda_debug_contacts.csv  step,contact,mtype,p1,p2,p3,m4,m5,m6,m0_0,m0_2,o2,o3,o4,o5      (df07 末连通性+转移态)
  bdda_debug_df18.csv      step,contact,jj,block_i,block_j,mtype,q01,q02,b1,cs1,cs2,cs3,
                           x1,y1,x2,y2,x3,y3,s1..s30[,o3,o4,o5,m0_0,m0_1,m0_2,k5,fric_ang,cohesion]
  bdda_debug_df22.csv      step,oc_iter,contact,mtype,m0_0,m0_prev,m0_new,o3,o4,t3,w0        (开闭迭代逐次判定)
  bdda_debug_verts.csv     step,block,vidx,x,y

语义说明（来自 b-DDA sidecar.py 与 refkernel 注释）：
  mtype 0 = v-e, 1 = v-v；p1..p3 = 接触三点的顶点号（p1 顶点、p2-p3 边）；m4..m6 共边第二参考；
  m0_2 = 转移后的锁定态（0 开 1 滑 2 锁 3 v-v 第二参考闭合）；o2 = 投影比 s3；o3 法向；o4 剪向；o5 接触长度。
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from ..contact_record import BDDA_COVER, BDDA_MODE, ContactRecord, CoverType, Feature, Mode


@dataclass(slots=True)
class Df22Judgment:
    step: int
    oc_iter: int
    contact: int
    mtype: int
    m0_0: int
    m0_prev: int
    m0_new: int
    o3: float
    o4: float
    t3: float
    w0: float


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_contacts_csv(path: Path) -> dict[tuple[int, int], dict[str, float]]:
    """(step, contact) -> df07 连通性/转移态字段。"""

    out: dict[tuple[int, int], dict[str, float]] = {}
    for raw in _read_csv(path):
        key = (int(raw["step"]), int(raw["contact"]))
        out[key] = {k: float(v) for k, v in raw.items() if k not in ("step", "contact")}
    return out


def read_df18_csv(path: Path) -> dict[tuple[int, int], dict[str, str]]:
    """(step, contact) -> df18 几何/系数行。同一 (step, contact) 多次出现时保留最后一次，并记 count。"""

    out: dict[tuple[int, int], dict[str, str]] = {}
    counts: dict[tuple[int, int], int] = {}
    for raw in _read_csv(path):
        key = (int(raw["step"]), int(raw["contact"]))
        counts[key] = counts.get(key, 0) + 1
        out[key] = raw
    for key, row in out.items():
        row["_df18_rows"] = str(counts[key])
    return out


def read_df22_csv(path: Path) -> list[Df22Judgment]:
    rows: list[Df22Judgment] = []
    for raw in _read_csv(path):
        rows.append(Df22Judgment(
            step=int(raw["step"]), oc_iter=int(raw["oc_iter"]), contact=int(raw["contact"]),
            mtype=int(raw["mtype"]), m0_0=int(raw["m0_0"]), m0_prev=int(raw["m0_prev"]),
            m0_new=int(raw["m0_new"]), o3=float(raw["o3"]), o4=float(raw["o4"]),
            t3=float(raw["t3"]), w0=float(raw["w0"]),
        ))
    return rows


def read_verts_csv(path: Path) -> dict[int, dict[int, dict[int, tuple[float, float]]]]:
    out: dict[int, dict[int, dict[int, tuple[float, float]]]] = {}
    for raw in _read_csv(path):
        out.setdefault(int(raw["step"]), {}).setdefault(int(raw["block"]), {})[int(raw["vidx"])] = (
            float(raw["x"]), float(raw["y"]))
    return out


def load_records(dump_dir: Path) -> list[ContactRecord]:
    """合并 contacts + df18 (+ df22 末次判定) 为 ContactRecord 列表，按 (step, contact) 排序。

    contacts.csv 是主表（每步每接触一行）；df18 提供块号/几何/系数；df22 提供本步最后一次
    开闭判定作为 mode。三者缺任一则相应字段留空，不报错——读取器不许丢信息，也不许编信息。
    """

    dump_dir = Path(dump_dir)
    contacts = read_contacts_csv(dump_dir / "bdda_debug_contacts.csv") if (dump_dir / "bdda_debug_contacts.csv").exists() else {}
    df18 = read_df18_csv(dump_dir / "bdda_debug_df18.csv") if (dump_dir / "bdda_debug_df18.csv").exists() else {}
    df22 = read_df22_csv(dump_dir / "bdda_debug_df22.csv") if (dump_dir / "bdda_debug_df22.csv").exists() else []

    last_judgment: dict[tuple[int, int], Df22Judgment] = {}
    for j in df22:
        key = (j.step, j.contact)
        prev = last_judgment.get(key)
        if prev is None or j.oc_iter >= prev.oc_iter:
            last_judgment[key] = j

    # verts.csv 的 vidx 是全局顶点号（2026-09-18 实测：bb52 两步各 154 行 vidx 全唯一，
    # p1/p2 反查块号与 df18 的 block_i/block_j 54/54 吻合）。df18 只 dump 首步，
    # 第 2 步起的块号靠它补全；两者都在时交叉核对，不一致记 extra["_block_mismatch"]。
    verts_path = dump_dir / "bdda_debug_verts.csv"
    vert_block: dict[tuple[int, int], int] = {}
    if verts_path.exists():
        for step_v, blocks in read_verts_csv(verts_path).items():
            for b, vs in blocks.items():
                for vidx in vs:
                    vert_block[(step_v, vidx)] = b

    keys = sorted(set(contacts) | set(df18) | set(last_judgment))
    records: list[ContactRecord] = []
    for key in keys:
        step, contact = key
        c = contacts.get(key, {})
        g = df18.get(key)
        j = last_judgment.get(key)

        mtype = int(c["mtype"]) if "mtype" in c else (int(g["mtype"]) if g else (j.mtype if j else -1))
        cover = BDDA_COVER.get(mtype, CoverType.UNKNOWN)
        block_a = int(g["block_i"]) if g else -1
        block_b = int(g["block_j"]) if g else -1
        block_mismatch = False
        if "p1" in c and "p2" in c:
            va = vert_block.get((step, int(c["p1"])))
            vb = vert_block.get((step, int(c["p2"])))
            if va is not None and vb is not None:
                if block_a < 0:
                    block_a, block_b = va, vb
                elif (va, vb) != (block_a, block_b):
                    block_mismatch = True

        ref_points: tuple[tuple[float, ...], ...] = ()
        params: tuple[float, ...] = ()
        length = None
        if g:
            ref_points = ((float(g["x1"]), float(g["y1"])), (float(g["x2"]), float(g["y2"])),
                          (float(g["x3"]), float(g["y3"])))
            params = (float(g["cs3"]),)
            length = float(g["b1"])
        elif "o2" in c:
            params = (float(c["o2"]),)

        raw_mode = j.m0_new if j else (int(c["m0_2"]) if "m0_2" in c else None)
        raw_prev = j.m0_prev if j else None
        raw_init = int(c["m0_2"]) if "m0_2" in c else None

        fa = Feature(block_a, "vertex", int(c["p1"])) if ("p1" in c and block_a >= 0) else None
        fb = Feature(block_b, "edge", int(c["p2"])) if ("p2" in c and block_b >= 0) else None

        extra: dict = {}
        for k, v in c.items():
            if k not in ("mtype", "p1", "p2", "p3", "m0_0", "m0_2", "o2", "o3", "o4", "o5"):
                extra[f"c_{k}"] = v
        if "p3" in c:
            extra["p3"] = c["p3"]
        for k in ("m4", "m5", "m6"):
            if k in c:
                extra[k] = c[k]
        if g:
            for k in ("jj", "q01", "q02", "cs1", "cs2", "_df18_rows", "k5", "fric_ang", "cohesion", "m0_1"):
                if k in g:
                    extra[f"df18_{k}"] = g[k]
            extra["df18_s"] = [float(g[f"s{i}"]) for i in range(1, 31) if f"s{i}" in g]
        if j:
            extra["df22_oc_iter"] = j.oc_iter
            extra["df22_t3"] = j.t3
            extra["df22_w0"] = j.w0
            extra["df22_m0_0"] = j.m0_0

        rec = ContactRecord(
            source="bdda-df", step=step, contact_index=contact,
            block_a=max(block_a, 0) if block_a >= 0 else 0, block_b=max(block_b, 0) if block_b >= 0 else 0,
            cover=cover, raw_cover=mtype,
            feature_a=fa, feature_b=fb,
            ref_points=ref_points, length_or_area=length, params=params,
            mode=BDDA_MODE.get(raw_mode, Mode.UNKNOWN) if raw_mode is not None else Mode.UNKNOWN,
            raw_mode=raw_mode,
            mode_prev=BDDA_MODE.get(raw_prev, Mode.UNKNOWN) if raw_prev is not None else None,
            raw_mode_prev=raw_prev,
            gap=j.o3 if j else (float(c["o3"]) if "o3" in c else None),
            shear=(j.o4,) if j else ((float(c["o4"]),) if "o4" in c else None),
            mode_init=BDDA_MODE.get(raw_init, Mode.UNKNOWN) if raw_init is not None else None,
            raw_mode_init=raw_init,
            gap_ref=float(c["o3"]) if "o3" in c else None,
            slip_ref=(float(c["o4"]),) if "o4" in c else None,
            bond_flag=int(c["m0_0"]) if "m0_0" in c else None,
            lock_position=float(c["o2"]) if "o2" in c else None,
            extra=extra,
        )
        if "o5" in c:
            rec.extra["o5_length"] = c["o5"]
            if rec.length_or_area is None:
                rec.length_or_area = float(c["o5"])
        if block_a < 0:
            rec.extra["_blocks_unknown"] = True
        if block_mismatch:
            rec.extra["_block_mismatch"] = True
        records.append(rec)
    return records
