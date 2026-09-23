"""从 b-DDA 的 bdda_debug_verts.csv 重建各步块体多边形（CCW），并处理 dump 外露的回绕重复点。

实测（bb52，2026-09-18）：vidx 是全局顶点号；每块顶点按多边形序连续；尾部带两个回绕重复点
（df 存储 d[i2+1]=d[i1]、d[i2+2]=d[i1+1]）；legacy 接触表用重复索引引用首边，故返回 alias 表。

审查 C19（2026-09-21）：除尾部回绕外，**任何**循环意义下的连续重复点（零长边）也在这里剥除并登记
alias——内核不接受零长边（`kernel2d.geom.outward_normal` 清晰报错）。见 `strip_duplicate_vertices`。
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ..kernel2d.geom import Poly, ensure_ccw


@dataclass(slots=True)
class BlockGeom:
    block: int
    poly: Poly                    # CCW
    vidx: list[int]               # 局部索引 -> 全局顶点号（已随翻转重排）
    flipped: bool


@dataclass(slots=True)
class StepGeometry:
    step: int
    blocks: dict[int, BlockGeom]
    alias: dict[int, int] = field(default_factory=dict)   # 重复 vidx -> 真实 vidx

    def canon(self, v: int) -> int:
        return self.alias.get(v, v)

    def vertex_block(self) -> dict[int, int]:
        return {v: b for b, g in self.blocks.items() for v in g.vidx}

    def vertex_pos(self) -> dict[int, tuple[float, float]]:
        return {v: g.poly[i] for b, g in self.blocks.items() for i, v in enumerate(g.vidx)}


def strip_duplicate_vertices(vids: list[int], poly: Poly, dup_tol: float = 1e-12,
                             *, block: int | None = None) -> tuple[list[int], Poly, dict[int, int]]:
    """剥除一块多边形环上的重复点，返回 (保留的顶点号, 保留的点, alias: 被剥顶点号 -> 保留顶点号)。

    两步，都按坐标逐分量 |Δ| ≤ dup_tol 判"同一点"：
      1. df 的回绕尾巴：末点等于首点或第二点（d[i2+1]=d[i1]、d[i2+2]=d[i1+1]），从尾部逐个剥；
      2. 循环意义下的**任何**连续重复点（零长边）：顺序扫描保留首次出现者，最后再比末点与首点。
    alias 链压平到最终保留的顶点号。剩余不足 3 点抛 ValueError（带块号）。
    """
    vids, poly = list(vids), list(poly)
    alias: dict[int, int] = {}

    def same(p, q) -> bool:
        return abs(p[0] - q[0]) <= dup_tol and abs(p[1] - q[1]) <= dup_tol

    while len(poly) > 3:
        k = len(poly) - 1
        dup = next((h for h in range(2) if same(poly[h], poly[k])), None)
        if dup is None:
            break
        alias[vids[k]] = vids[dup]
        poly.pop()
        vids.pop()
    kv: list[int] = []
    kp: Poly = []
    for v, p in zip(vids, poly):
        if kp and same(kp[-1], p):
            alias[v] = kv[-1]
            continue
        kv.append(v)
        kp.append(p)
    while len(kp) > 1 and same(kp[-1], kp[0]):
        alias[kv[-1]] = kv[0]
        kv.pop()
        kp.pop()
    for k in list(alias):
        t = alias[k]
        while t in alias:
            t = alias[t]
        alias[k] = t
    if len(kp) < 3:
        raise ValueError(f"block {block}: fewer than 3 distinct vertices after stripping duplicates: {kp}")
    return kv, kp, alias


def load_step_geometries(verts_csv: Path, *, dup_tol: float = 1e-12) -> dict[int, StepGeometry]:
    by: dict[int, dict[int, list[tuple[int, tuple[float, float]]]]] = defaultdict(lambda: defaultdict(list))
    with Path(verts_csv).open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            by[int(r["step"])][int(r["block"])].append((int(r["vidx"]), (float(r["x"]), float(r["y"]))))
    out: dict[int, StepGeometry] = {}
    for step, blocks in by.items():
        sg = StepGeometry(step=step, blocks={})
        for b, lst in blocks.items():
            lst.sort()
            vids, poly, alias = strip_duplicate_vertices([v for v, _ in lst], [p for _, p in lst], dup_tol, block=b)
            sg.alias.update(alias)
            ccw, flipped = ensure_ccw(poly)
            sg.blocks[b] = BlockGeom(b, ccw, list(reversed(vids)) if flipped else vids, flipped)
        out[step] = sg
    return out
