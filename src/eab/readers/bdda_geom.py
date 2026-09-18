"""从 b-DDA 的 bdda_debug_verts.csv 重建各步块体多边形（CCW），并处理 dump 外露的回绕重复点。

实测（bb52，2026-09-18）：vidx 是全局顶点号；每块顶点按多边形序连续；尾部带两个回绕重复点
（df 存储 d[i2+1]=d[i1]、d[i2+2]=d[i1+1]）；legacy 接触表用重复索引引用首边，故返回 alias 表。
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
            vids = [v for v, _ in lst]
            poly = [p for _, p in lst]
            while len(poly) > 3:
                k = len(poly) - 1
                dup = None
                for h, p in enumerate(poly[:2]):
                    if abs(p[0] - poly[k][0]) <= dup_tol and abs(p[1] - poly[k][1]) <= dup_tol:
                        dup = h
                        break
                if dup is None:
                    break
                sg.alias[vids[k]] = vids[dup]
                poly.pop()
                vids.pop()
            ccw, flipped = ensure_ccw(poly)
            sg.blocks[b] = BlockGeom(b, ccw, list(reversed(vids)) if flipped else vids, flipped)
        out[step] = sg
    return out
