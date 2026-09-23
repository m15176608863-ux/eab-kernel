"""3-b-dda（bdda3d）入口 dict → ContactRecord。

输入是 tools/ingest_bdda3d.py 在 3-b-dda 自己的环境里导出的 JSON（列表，每项一个入口 dict）。
键约定以 D:\\3-b-dda\\src\\bdda3d\\detect.py 模块 docstring 为准（2026-09-18 核对）：
  etype "np"|"ee"; bi, bj; refs 4×(块号, 顶点局部索引); owner 长 4 的 0/1; nsign ±1;
  t1, t2; d1; area; fa, coh, tens; m0init (0 开/1 滑/2 锁/3 键合); m0_0 (2=键合起源);
  o3t 转移法向参考; slip_ref 转移滑移 3 向量。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..contact_record import BDDA3D_COVER, BDDA3D_MODE, ContactRecord, CoverType, Feature, Mode

_KNOWN = {"etype", "bi", "bj", "refs", "owner", "nsign", "t1", "t2", "d1", "area",
          "fa", "coh", "tens", "m0init", "m0_0", "o3t", "slip_ref"}


def record_from_entrance(c: dict[str, Any], *, step: int = 0, index: int = 0,
                         verts: dict[str, Any] | None = None) -> ContactRecord:
    etype = str(c.get("etype", ""))
    cover = BDDA3D_COVER.get(etype, CoverType.UNKNOWN)
    bi, bj = int(c["bi"]), int(c["bj"])
    refs = [(int(r[0]), int(r[1])) for r in c.get("refs", [])]
    # n-p：P1 顶点属 bi，P2-P4 是 bj 的面扇形三角；e-e：P1,P2 属 bi 的棱，P3,P4 属 bj 的棱。
    # 入口 dict 不带面号/棱号：特征身份 = 排序后的顶点号元组（审查 C20：面下标写死 −1 时，同一顶点对
    # 同一宿主块两片不同三角的两条入口撞成同一个键）。同一几何面的不同三角仍是不同身份——那是 legacy
    # 自己的区分；把三角归约到几何面要几何，见 tools/g2_bdda3d.py。
    fa: Feature | None = None
    fb: Feature | None = None
    if refs:
        if cover is CoverType.VF:
            fa = Feature(refs[0][0], "vertex", refs[0][1])
            fb = Feature(refs[1][0], "face", -1, tuple(sorted(r[1] for r in refs[1:])))
        elif cover is CoverType.EE:
            fa = Feature(refs[0][0], "edge", -1, tuple(sorted(r[1] for r in refs[0:2])))
            fb = Feature(refs[2][0], "edge", -1, tuple(sorted(r[1] for r in refs[2:4])))
    ref_points: tuple[tuple[float, ...], ...] = ()
    if verts is not None and refs:
        pts = []
        for b, k in refs:
            pts.append(tuple(float(x) for x in verts[str(b)][k]))
        ref_points = tuple(pts)

    raw_init = int(c["m0init"]) if "m0init" in c else None
    extra = {k: v for k, v in c.items() if k not in _KNOWN}
    for k in ("owner", "nsign", "d1", "refs"):
        if k in c:
            extra[k] = c[k]
    for k in ("fa", "coh", "tens"):
        if k in c:
            extra[f"joint_{k}"] = c[k]

    slip = c.get("slip_ref")
    return ContactRecord(
        source="bdda3d", step=step, contact_index=index,
        block_a=bi, block_b=bj, cover=cover, raw_cover=etype,
        feature_a=fa, feature_b=fb,
        ref_points=ref_points,
        length_or_area=float(c["area"]) if "area" in c else None,
        params=(float(c["t1"]), float(c["t2"])) if ("t1" in c and "t2" in c) else (),
        mode=BDDA3D_MODE.get(raw_init, Mode.UNKNOWN) if raw_init is not None else Mode.UNKNOWN,
        raw_mode=raw_init,
        mode_init=BDDA3D_MODE.get(raw_init, Mode.UNKNOWN) if raw_init is not None else None,
        raw_mode_init=raw_init,
        gap_ref=float(c["o3t"]) if c.get("o3t") is not None else None,
        slip_ref=tuple(float(x) for x in slip) if slip is not None else None,
        bond_flag=int(c["m0_0"]) if c.get("m0_0") is not None else None,
        extra=extra,
    )


def load_records(json_path: Path) -> list[ContactRecord]:
    """读取 tools/ingest_bdda3d.py 的导出：{"case": ..., "verts": {block: [[x,y,z],...]}, "entrances": [...]}。"""

    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    verts = data.get("verts")
    out = []
    for i, c in enumerate(data["entrances"]):
        rec = record_from_entrance(c, step=int(data.get("step", 0)), index=i, verts=verts)
        rec.extra["case"] = data.get("case")
        out.append(rec)
    return out
