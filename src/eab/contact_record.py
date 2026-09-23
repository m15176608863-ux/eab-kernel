"""ContactRecord：六种现有接触表示的公共契约。

字段按生命周期分四组（设计文档 §四）：
  身份（跨步不变）  block_a/block_b, cover, feature_a/feature_b, joint_material
  步内冻结          ref_points, normal, length_or_area, params
  状态（迭代内演化）mode, mode_prev, entrance_index, gap, shear, normal_force
  转移（跨步携带）  mode_init, gap_ref, slip_ref, bond_flag, lock_position

设计要点：
- 统一词汇（CoverType / Mode）+ 各引擎原始码**同时保留**（raw_mode / raw_cover），
  因为三家的 "3" 含义不同：b-DDA 3 = v-v 第二参考闭合，bdda3d 3 = 键合，tf.cpp 3 = 受拉。
- `extra` 装下一切不入正式字段的列，读取器**不许丢信息**。
- 典范序键 `canonical_key()` 与来源的枚举顺序无关（块序交换不变），用于跨引擎集合同构比较。
  它的分辨率取决于来源给了多少特征身份（审查 C20）：bdda_df（有 verts.csv）与 bdda3d 逐步唯一；
  tf 探针不带特征，键只到 (块对, 盖类) 级；bdda_df 缺 verts.csv 时块号未知的记录同样只到块对级。
  这几条由 tests/test_readers_roundtrip.py 在真实夹具上断言。
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any, Iterable


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
    NN = "NN"          # tf.cpp 候选类 0（入口展开前）
    NE = "NE"          # tf.cpp 候选类 1（入口展开前）
    UNKNOWN = "UNKNOWN"


class Mode(str, Enum):
    OPEN = "OPEN"
    SLIDING = "SLIDING"
    LOCKED = "LOCKED"
    BONDED = "BONDED"        # bdda3d 键合态
    TENSION = "TENSION"      # tf.cpp 受拉态
    VV_CLOSED = "VV_CLOSED"  # b-DDA v-v 第二参考闭合（m0=3）
    UNKNOWN = "UNKNOWN"


# 各引擎状态码 → 统一词汇。原始码另存 raw_mode，映射不可逆时靠 raw 还原。
BDDA_MODE: dict[int, Mode] = {0: Mode.OPEN, 1: Mode.SLIDING, 2: Mode.LOCKED, 3: Mode.VV_CLOSED}
BDDA3D_MODE: dict[int, Mode] = {0: Mode.OPEN, 1: Mode.SLIDING, 2: Mode.LOCKED, 3: Mode.BONDED}
# tf.cpp 注释（tf.cpp:306-313）：0 open 1 friction 2 s-spring 3 t-tension 4 2f-friction 5 2f-lock 6 top-lock
TF_MODE: dict[int, Mode] = {0: Mode.OPEN, 1: Mode.SLIDING, 2: Mode.LOCKED, 3: Mode.TENSION,
                            4: Mode.SLIDING, 5: Mode.LOCKED, 6: Mode.LOCKED}
# tf.cpp c[i][2] / m[j][2]：0 n-n 1 n-e 2 n-p 3 e-e（tf.cpp:297-300, 329-336）
TF_COVER: dict[int, CoverType] = {0: CoverType.NN, 1: CoverType.NE, 2: CoverType.VF, 3: CoverType.EE}
# b-DDA mtype：0 v-e 1 v-v（df05）
BDDA_COVER: dict[int, CoverType] = {0: CoverType.VE, 1: CoverType.VV}
# bdda3d etype
BDDA3D_COVER: dict[str, CoverType] = {"np": CoverType.VF, "ee": CoverType.EE}


@dataclass(frozen=True, slots=True)
class Feature:
    """块上的几何特征。index 为来源引擎的局部/全局编号，-1 表示未知。

    verts：来源没有特征编号、只用顶点号指代特征时的身份（**排序后**的顶点号元组，与列出顺序无关）。
    例：bdda3d 的 n-p 入口用宿主块面扇形里的一个三角 (P2,P3,P4) 指代面，没有面号 → index=-1、
    verts=sorted(P2,P3,P4)；e-e 入口的棱 → verts=sorted(两端点)。空元组表示未提供。
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
    source: str                 # "bdda-df" | "bdda2" | "bdda3d" | "tf" | "dda4" | "eab"
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
    length_or_area: float | None = None   # 2D 边长 b1 / 3D 面积
    params: Vec = ()                      # 2D (s3,) / 3D (t1, t2)
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
    gap_ref: float | None = None          # o3t
    slip_ref: Vec | None = None           # o4t / 三维滑移参考
    bond_flag: int | None = None          # m0_0
    lock_position: float | None = None    # c206 写回的 s3（钉定的"泄漏"语义）
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


def _decode(name: str, v: Any) -> Any:
    if v is None:
        return None
    if name == "cover":
        return CoverType(v)
    if name in ("mode", "mode_prev", "mode_init"):
        return Mode(v)
    if name in ("feature_a", "feature_b"):
        return Feature(int(v["block"]), str(v["kind"]), int(v["index"]), tuple(int(x) for x in v.get("verts", ())))
    if name == "ref_points":
        return tuple(tuple(float(x) for x in p) for p in v)
    if name in _TUPLE_FIELDS:
        return tuple(float(x) for x in v)
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
    return [ContactRecord.from_dict(d) for d in json.loads(text)]
