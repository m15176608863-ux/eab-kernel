"""b-DDA 二维 L5 影子适配器：静态、显式域窗口内的局部有效盖。

本模块只消费检测时的 StepGeometry 和 detparams，不读取 legacy 接触表、不改
内核默认判据。CSV 没有本步完整仿射运动，不能从相邻快照差冒充沿运动方向的首入。
所以 observable 明记 static_window_valid_covers，而不是 first_entrance。

距离窗口 d0、角窗口 sin(h1)、边端外长度窗口 seg_tol 都由调用方显式给出。
默认 seg_tol=1e-9 延续 tools/bb52_g0.py 的已验证枚举口径；fit_tol=1e-6
只供逐条对账使用，不参与几何枚举。缺参数时明记 bb52 fallback；已有 CSV 缺步、
重复步或非法参数则报错，不静默借用第一步。契约由 tests/test_m4_bdda_adapter.py 看护。
Numeric boundary: docs/exact_predicates_plan.md (R13FIXb). Readers retain
all finite representable binary64 values; exact decimal conversion rejects
nonzero underflow and finite overflow with ConstructionDomainError.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

from ..construction import norm_rational, scalar_rational
from ..numeric_domain import check_input, exact_input
from ..contact_record import ContactRecord, CoverType, Feature
from ..kernel2d import covers
from ..readers.bdda_geom import BlockGeom, StepGeometry
from ..readers.numeric_decode import integer


OBSERVABLE = "static_window_valid_covers"
FALLBACK_D0 = 0.19687500000000002
FALLBACK_H1_DEGREES = 3.0


@dataclass(frozen=True, slots=True)
class Bdda2DWindow:
    """有单位的 L5 域窗；seg_tol 和 fit_tol 不能互相代替。"""

    step: int
    d0: float
    h1_degrees: float
    seg_tol: float = 1e-9
    fit_tol: float = 1e-6
    source: str = "explicit"
    fallback_fields: tuple[str, ...] = ()
    raw_parameters: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        integer(self.step, "bdda2d.window.step")
        if self.step < 0:
            raise ValueError("negative window step")
        for name in ("d0", "seg_tol", "fit_tol", "h1_degrees"):
            value = getattr(self, name)
            # Retain the existing ValueError contract for invalid float inputs.
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
            q = exact_input(value, f"bdda2d.window.{name}")
            if q < 0:
                raise ValueError(f"{name} must be nonnegative")
            if name == "h1_degrees":
                if q >= 90:
                    raise ValueError("h1 must be finite and in [0, 90) degrees")
                check_input(q, "bdda2d.window.h1_degrees")
            # Geometry windows retain their exact input (not an early-rounded
            # replacement); the boundary only checks eventual representability.
            scalar_rational(q, quantity=f"bdda2d.window.{name}")

    @property
    def cone_tol(self) -> float:
        # Explicit legacy libm coefficient model, not an exact transcendental
        # predicate. The input envelope avoids radians underflow; its measured
        # platform error gate is test_cone_coefficient_has_a_rational_series_gate.
        check_input(self.h1_degrees, "bdda2d.cone_tol.h1_degrees")
        return math.sin(math.radians(scalar_rational(self.h1_degrees, quantity="bdda2d.cone_tol.h1_degrees")))

    def metadata(self) -> dict:
        return {"d0": self.d0, "h1_degrees": self.h1_degrees, "cone_sin": self.cone_tol,
                "seg_tol": self.seg_tol, "fit_tol": self.fit_tol, "source": self.source,
                "fallback_fields": list(self.fallback_fields)}


def load_window(dump_dir: Path, step: int) -> Bdda2DWindow:
    """Read this step's d0/h1; record every fallback, reject malformed existing data."""
    path = Path(dump_dir) / "bdda_debug_detparams.csv"
    if not path.exists():
        return Bdda2DWindow(step, FALLBACK_D0, FALLBACK_H1_DEGREES,
                            source="bb52_fallback:no_detparams", fallback_fields=("d0", "h1"))
    with path.open(newline="", encoding="utf-8") as fh:
        rows = [row for row in csv.DictReader(fh) if int(row["step"]) == step]
    if len(rows) != 1:
        raise ValueError(f"detparams step {step}: expected one row, got {len(rows)}")
    raw = {name: scalar_rational(value, quantity=f"bdda2d.window.{name}")
           for name, value in rows[0].items() if name != "step" and value != ""}
    fallback = tuple(name for name in ("d0", "h1") if name not in raw)
    return Bdda2DWindow(step, raw.get("d0", FALLBACK_D0), raw.get("h1", FALLBACK_H1_DEGREES),
                        source="detparams" + ("+bb52_fallback" if fallback else ""),
                        fallback_fields=fallback, raw_parameters=raw)


def _bounds(block: BlockGeom):
    """Original supplied coordinates to Fraction; no rounded midpoint/radius."""
    return tuple((min(Fraction(p[k]) for p in block.poly), max(Fraction(p[k]) for p in block.poly))
                 for k in (0, 1))


def _boxes_may_meet(a, b, window: Bdda2DWindow) -> bool:
    # A valid VE witness is at most d0 along its normal and seg_tol beyond its
    # edge endpoint. Their sum safely bounds every coordinate; VV needs only d0.
    # The sum stays exact, so even a large common translation cannot shrink it.
    reach = Fraction(window.d0) + Fraction(window.seg_tol)
    return all(max(alo - bhi, blo - ahi, 0) <= reach
               for (alo, ahi), (blo, bhi) in zip(a, b))


def _record(c: covers.Cover, A: BlockGeom, B: BlockGeom, step: int, window: Bdda2DWindow) -> ContactRecord:
    extra = {"observable": OBSERVABLE, "window": window.metadata(),
             "kernel_label": c.label(), "strict": c.strict, "window_active": c.window_active}
    if c.kind == "VV":
        return ContactRecord(source="eab-bdda2d-shadow", step=step, contact_index=0,
                             block_a=A.block, block_b=B.block, cover=CoverType.VV,
                             feature_a=Feature(A.block, "vertex", A.vidx[c.a_index]),
                             feature_b=Feature(B.block, "vertex", B.vidx[c.b_index]),
                             normal=c.normal, gap=c.gap, ref_points=(A.poly[c.a_index], B.poly[c.b_index]),
                             extra=extra)
    if c.kind == "VE":
        vertex_block, edge_block, vi, ei, normal = A, B, c.a_index, c.b_index, c.normal
    elif c.kind == "EV":
        vertex_block, edge_block, vi, ei = B, A, c.b_index, c.a_index
        normal = tuple(-x for x in c.normal) if c.normal is not None else None
    else:
        raise ValueError(f"unexpected local cover kind {c.kind}")
    p, q = edge_block.poly[ei], edge_block.poly[(ei + 1) % len(edge_block.poly)]
    extra["edge_vertices"] = (edge_block.vidx[ei], edge_block.vidx[(ei + 1) % len(edge_block.poly)])
    return ContactRecord(source="eab-bdda2d-shadow", step=step, contact_index=0,
                         block_a=vertex_block.block, block_b=edge_block.block, cover=CoverType.VE,
                         feature_a=Feature(vertex_block.block, "vertex", vertex_block.vidx[vi]),
                         feature_b=Feature(edge_block.block, "edge", edge_block.vidx[ei]),
                         normal=normal, gap=c.gap, params=(c.param,),
                         ref_points=(vertex_block.poly[vi], p, q),
                         length_or_area=norm_rational(Fraction(q[k])-Fraction(p[k]) for k in (0, 1)),
                         extra=extra)


def detect_step(geometry: StepGeometry, window: Bdda2DWindow) -> list[ContactRecord]:
    """Deterministic static covers, with no dependency on legacy contact records."""
    if geometry.step != window.step:
        raise ValueError(f"geometry step {geometry.step} != window step {window.step}")
    ids = sorted(geometry.blocks)
    bounds = {bid: _bounds(geometry.blocks[bid]) for bid in ids}
    out = []
    for k, ai in enumerate(ids):
        for bi in ids[k + 1:]:
            if not _boxes_may_meet(bounds[ai], bounds[bi], window):
                continue
            A, B = geometry.blocks[ai], geometry.blocks[bi]
            for c in covers.enumerate_covers(A.poly, B.poly, window=window.d0, tol=0.0,
                                             cone_tol=window.cone_tol, seg_tol=window.seg_tol):
                out.append(_record(c, A, B, geometry.step, window))
    out.sort(key=ContactRecord.canonical_key)
    for index, record in enumerate(out, 1):
        record.contact_index = index
    return out
