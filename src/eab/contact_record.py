"""ContactRecord：域无关的接触记录公共契约。

字段按生命周期分四组（设计文档 §四）：
  身份（跨步不变）  block_a/block_b, cover, feature_a/feature_b, joint_material
  步内冻结          ref_points, normal, length_or_area, params
  状态（迭代内演化）mode, mode_prev, entrance_index, gap, shear, normal_force
  转移（跨步携带）  mode_init, gap_ref, slip_ref, bond_flag, lock_position

设计要点：
- 统一词汇（CoverType / Mode）与不透明来源码同时保留（raw_mode / raw_cover）；
  来源码到公共词汇的映射由适配器解释，公共契约不赋予来源码语义。
- `extra` 装下一切不入正式字段的列，读取器**不许丢信息**。
- 典范序键 `canonical_key()` 与来源的枚举顺序无关（块序交换不变），用于跨引擎集合同构比较。
  分辨率取决于来源提供的特征身份；缺失身份与重复记录不能无声去重。
  具体来源的身份归约和表格式说明留在适配器及读取器中。
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any, Iterable

from .numeric_decode import scalar as scalar_rational
from .numeric_decode import decode_tree, integer, loads as loads_exact


class CoverType(str, Enum):
    """∂E(A,B) 的盖类型（方向无关；谁属于哪块记在 feature_a/feature_b）。"""

    VE = "VE"          # 2D 顶点-边
    VV = "VV"          # 2D 顶点-顶点（∂E 的顶点，法向集值点）
    VF = "VF"          # 3D 顶点-面（facet 盖）
    EE = "EE"          # 3D 交叉棱-棱（facet 盖）
    VE3 = "VE3"        # 3D 顶点-棱（∂E 的棱）
    VV3 = "VV3"        # 3D 顶点-顶点（∂E 的顶点）
    FF = "FF"          # 3D 退化：平行贴面
    FE = "FE"          # 3D 退化：棱平行于面
    EE_PAR = "EE_PAR"  # 3D 退化：平行棱-棱
    NN = "NN"          # 未展开的顶点-顶点候选
    NE = "NE"          # 未展开的顶点-棱候选
    UNKNOWN = "UNKNOWN"


class Mode(str, Enum):
    OPEN = "OPEN"
    SLIDING = "SLIDING"
    LOCKED = "LOCKED"
    BONDED = "BONDED"        # 键合态
    TENSION = "TENSION"      # 受拉态
    VV_CLOSED = "VV_CLOSED"  # 顶点-顶点闭合态
    UNVERIFIED = "UNVERIFIED"  # 引擎给了码、也有名字，但归入统一词汇的依据未核实（原始码见 raw_mode）
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class Feature:
    """块上的几何特征。index 为来源引擎的局部/全局编号，-1 表示未知。

    verts：来源没有特征编号、只用顶点号指代特征时的身份（**排序后**的顶点号元组，与列出顺序无关）。
    例如无面编号时可提供面上三角的排序顶点号；棱可提供排序后的两端点号。
    空元组表示未提供。来源特定的身份归约由适配器负责。
    """

    block: int
    kind: str  # "vertex" | "edge" | "face"
    index: int = -1
    verts: tuple[int, ...] = ()

    def as_tuple(self) -> tuple[int, str, int, tuple[int, ...]]:
        return (self.block, self.kind, self.index, self.verts)


Vec = tuple[float, ...]


@dataclass(slots=True)
class ContactRecord:
    # ---- 身份（跨步不变）----
    source: str                 # 由来源或适配器声明的不透明标签
    step: int
    contact_index: int          # 来源枚举序里的位置（只做映射，不做语义）
    block_a: int
    block_b: int
    cover: CoverType = CoverType.UNKNOWN
    raw_cover: int | str | None = None
    feature_a: Feature | None = None
    feature_b: Feature | None = None
    joint_material: int | None = None
    # ---- 步内冻结 ----
    ref_points: tuple[Vec, ...] = ()
    normal: Vec | None = None
    length_or_area: float | None = None   # 2D 长度 / 3D 面积
    params: Vec = ()                      # 特征上的参数坐标
    # ---- 状态（迭代内演化）----
    mode: Mode = Mode.UNKNOWN
    raw_mode: int | None = None
    mode_prev: Mode | None = None
    raw_mode_prev: int | None = None
    entrance_index: int | None = None
    gap: float | None = None              # 法向间隙/侵入（来源约定：正=张开）
    shear: Vec | None = None
    normal_force: float | None = None
    # ---- 转移（跨步携带）----
    mode_init: Mode | None = None
    raw_mode_init: int | None = None
    gap_ref: float | None = None          # 参考法向间隙
    slip_ref: Vec | None = None           # 参考滑移
    bond_flag: int | None = None          # 来源声明的键合标记
    lock_position: float | None = None    # 锁定状态的参数位置
    # ---- 溯源与余项 ----
    extra: dict[str, Any] = field(default_factory=dict)

    # 典范序键：与来源枚举顺序无关，用于跨引擎集合同构比较。
    def canonical_key(self) -> tuple:
        a, b = sorted((self.block_a, self.block_b))
        feats = tuple(sorted(f.as_tuple() for f in (self.feature_a, self.feature_b) if f is not None))
        return (a, b, self.cover.value, feats)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for f in fields(self):
            v = getattr(self, f.name)
            out[f.name] = _encode(v)
        return out

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ContactRecord":
        kw: dict[str, Any] = {}
        for f in fields(cls):
            if f.name not in d:
                continue
            kw[f.name] = _decode(f.name, d[f.name])
        return cls(**kw)


def _encode(v: Any) -> Any:
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, Feature):
        return {"block": v.block, "kind": v.kind, "index": v.index, "verts": list(v.verts)}
    if isinstance(v, tuple):
        return [_encode(x) for x in v]
    if isinstance(v, dict):
        return {k: _encode(x) for k, x in v.items()}
    return v


_TUPLE_FIELDS = {"ref_points", "normal", "params", "shear", "slip_ref"}
_SCALAR_FIELDS = {"length_or_area", "gap", "normal_force", "gap_ref", "lock_position"}
_INTEGER_FIELDS = {"step", "contact_index", "block_a", "block_b", "joint_material",
                   "raw_mode", "raw_mode_prev", "raw_mode_init", "entrance_index", "bond_flag"}


def _decode(name: str, v: Any) -> Any:
    if v is None:
        return None
    if name == "cover":
        return CoverType(v)
    if name in ("mode", "mode_prev", "mode_init"):
        return Mode(v)
    if name in ("feature_a", "feature_b"):
        return Feature(integer(v["block"], f"{name}.block"), str(v["kind"]),
                       integer(v["index"], f"{name}.index"),
                       tuple(integer(x, f"{name}.verts[{i}]") for i, x in enumerate(v.get("verts", ()))))
    if name == "ref_points":
        return tuple(tuple(scalar_rational(x, quantity=f"{name}[{i}][{j}]") for j, x in enumerate(p))
                     for i, p in enumerate(v))
    if name in _TUPLE_FIELDS:
        return tuple(scalar_rational(x, quantity=f"{name}[{i}]") for i, x in enumerate(v))
    if name in _SCALAR_FIELDS:
        return scalar_rational(v, quantity=name)
    if name in _INTEGER_FIELDS or (name == "raw_cover" and not isinstance(v, str)):
        return integer(v, name)
    if name == "extra":
        return decode_tree(v, name)
    return v


def validate(rec: ContactRecord) -> None:
    """契约校验：违反即 ValueError。只校验结构与有限性，不校验物理。"""

    if rec.block_a < 0 or rec.block_b < 0:
        raise ValueError(f"negative block id: {rec.block_a}, {rec.block_b}")
    if rec.step < 0:
        raise ValueError(f"negative step: {rec.step}")
    if not isinstance(rec.cover, CoverType) or not isinstance(rec.mode, Mode):
        raise ValueError("cover/mode must be enums")
    for f in (rec.feature_a, rec.feature_b):
        if f is not None and f.kind not in ("vertex", "edge", "face"):
            raise ValueError(f"bad feature kind: {f.kind}")
        if f is not None and (list(f.verts) != sorted(f.verts) or not all(isinstance(x, int) for x in f.verts)):
            raise ValueError(f"feature verts must be sorted ints: {f.verts}")
    for name in ("gap", "normal_force", "length_or_area", "gap_ref", "lock_position"):
        v = getattr(rec, name)
        if v is not None and not math.isfinite(v):
            raise ValueError(f"non-finite {name}: {v}")
    for name in ("normal", "shear", "slip_ref", "params"):
        v = getattr(rec, name)
        if v is not None and any(not math.isfinite(x) for x in v):
            raise ValueError(f"non-finite {name}: {v}")
    for p in rec.ref_points:
        if any(not math.isfinite(x) for x in p):
            raise ValueError(f"non-finite ref point: {p}")


def records_to_json(records: Iterable[ContactRecord]) -> str:
    return json.dumps([r.to_dict() for r in records], ensure_ascii=False, indent=1, sort_keys=True)


def records_from_json(text: str) -> list[ContactRecord]:
    return [ContactRecord.from_dict(d) for d in loads_exact(text)]
