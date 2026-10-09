"""互锁的力学量：逃逸高度剖面与剪胀比——由入口块边界直接读出，且对界面几何**可微**。

动机（04/06 号文档的 TIA 首选方向）：拓扑互锁结构的核心性能量不是"碰没碰上"，而是
**块体横向移动 δ 时必须抬升多少才能不互相贯入**。把它写成函数：

    h(δ; u) = min{ z ≥ 0 : A 平移 (δ·u + z·ẑ) 后与 B 不贯入 }        「逃逸高度剖面」

这正是入口块沿竖直线的上边界：a₀ + δ·u + z·ẑ 离开 E(A,B) 的最小 z。其斜率

    tanψ(δ) = dh/dδ                                                   「剪胀比」

在无摩擦极限下就是横向承载与法向压力之比（Rowe 剪胀关系，岩石力学标准结果）：
横向阻力 F_t / 法向力 F_n = tanψ。**所以入口块边界的斜率直接给出互锁的荷载传递比。**

两条路径都实现，互为门：
  · `escape_height_brute`  ——  对暴力相交谓词做二分，精确但不可微（oracle）；
  · `escape_height_covers` ——  由盖的 gap 沿竖直线求根，闭式、可微（生产路径）。

可微性走"**冻结活动盖**"的路子（与 DDA 冻结活动集后解析可微同构）：先用 float 定出
哪个盖当家（组合结构），再用对偶数重算该盖的几何量。这就是"片 + 划"里的那个"片"。

## 容差政策（纪律 F，2026-09-24 M0.2）

全部容差随尺度，与 `eab.margin` 同一套（`effective_geom_tol` / `rounding_floor`）：
  · 谓词容差 geom_tol_eff = max(1e-9·L, 64·eps·C)（L 特征长度、C 坐标量级）；显式给出按绝对长度、不低于地板；
  · 逃逸高度的分辨率是 geom_tol_eff / n_z：谓词按**法向**贯入深度判，某个盖在竖向差 Δz 处的法向间隙是 Δz·n_z；
  · 并列（`tied_labels`）按**同一把尺**判：候选盖在接受高度处的法向间隙 |Δz|·n_z ≤ geom_tol_eff（加舍入）即并列。
    旧实现按竖向高度 1e-9·max(1, |z|) 判并列（docstring 却称"相对"），与谓词不一致：陡坡上（n_z ≈ 0.117）
    谓词接受了比真值低 4e-9 的另一支候选、真活动的盖落在并列窗口外，折点旁报"可微"且给错支
    （tanψ −0.507 vs 真值 −8.528，lx = 0.2；G6 minor[11]）。现在谓词分辨带内的点一律报出两支；
  · 胜出盖在舍入意义上的并列组里按**枚举序**裁决（不按舍入噪声），刚体运动下标签逐字不变；
  · 暴力 oracle 的默认谓词容差 max(1e-12·L, 64·eps·C)、二分宽度 1e-10·L（旧：绝对 1e-12 / 1e-10——
    1e5 坐标、绕 z 转过的就位位形上二分出 5.9e-11 而不是 0）。
门：`tests/test_invariance_interlock.py`（平移 1e3/1e5 × 缩放 1e-3/1/1e3 × 绕 z 旋转）、
`tests/test_interlock_sensitivity.py::test_steep_profile_kink_is_flagged_consistently_with_the_predicate`。
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from ..dual import Dual, Number, val
from ..margin import characteristic_length, effective_geom_tol, rounding_floor
from .covers3 import ee_cover, enumerate_covers3, fv_cover, vf_cover
from .frozen import FACET_KINDS, frozen_ee_sign, frozen_gap, frozen_normal  # noqa: F401  (L5 转出的公共入口)
from .geom3 import Polyhedron, Vec3, dot, polyhedra_overlap, sub

_EPS = sys.float_info.epsilon
REL_BRUTE_GEOM_TOL = 1e-12         # oracle 的谓词容差：特征长度 L 的相对量
REL_BRUTE_TOL = 1e-10              # oracle 的二分终止宽度：L 的相对量


# ------------------------------------------------------------------ 暴力 oracle

def escape_height_brute(A: Polyhedron, B: Polyhedron, offset: Vec3, *,
                        hi: float, tol: float | None = None, geom_tol: float | None = None) -> float:
    """对分离谓词二分：返回使 A 平移 (offset + z·ẑ) 后**不贯入** B 的最小 z ∈ [0, hi]。

    前提：z 足够大时必分离（对竖向抬升的互锁块成立）。不可微，只作 oracle。
    默认容差随尺度：谓词 max(1e-12·L, 64·eps·C)、二分宽度 1e-10·L；显式给出按绝对长度、不低于舍入地板。
    """
    At = A.translated(offset)
    floor = rounding_floor(At, B)
    L = characteristic_length(At, B)
    gtol = max(REL_BRUTE_GEOM_TOL * L if geom_tol is None else float(geom_tol), floor)
    ztol = max(REL_BRUTE_TOL * L if tol is None else float(tol), 8.0 * _EPS * abs(hi))

    def intruding(z: float) -> bool:
        x = (offset[0], offset[1], offset[2] + z)
        return polyhedra_overlap(A.translated(x), B, gtol) == 1

    if not intruding(0.0):
        return 0.0
    if intruding(hi):
        raise ValueError(f"still intruding at z={hi}; raise hi")
    lo, up = 0.0, hi
    while up - lo > ztol:
        mid = 0.5 * (lo + up)
        if intruding(mid):
            lo = mid
        else:
            up = mid
    return up


# ------------------------------------------------------------------ 盖路径（可微）

@dataclass(slots=True)
class EscapeSolution:
    height: float
    cover_label: tuple | None      # 决定逃逸高度的那个盖（冻结的活动集；舍入意义上的并列按枚举序裁决）
    n_candidates: int
    # 在该高度上**并列活跃**的全部接触盖（含 cover_label，且它排第一，其余按枚举序）：候选盖在接受高度处的
    # 法向间隙 |Δz|·n_z ≤ geom_tol_eff（加舍入），即谓词分辨不开的那些。多于一种导数时该点不可微——
    # cover_label 只是并列里被裁决选中的那一支（审查 C13），且谓词分辨带内的点必然报出两支（G6 minor[11]）。
    tied_labels: tuple = ()


def _cover_escape_z(cover) -> tuple[float, float] | None:
    """单个盖在竖直线上的零间隙高度与它的 n_z：解 gap(z) = 0。

    盖的 gap 沿平移 x 是仿射的：gap(x) = n·(a + x − b)，故 gap(z) = gap(offset) + z·(n·ẑ)。
    只有 n·ẑ > 0 的盖（抬升能把它拉开）才给出有限的逃逸高度（n 是单位向量，1e-12 无量纲）。
    """
    n = cover.normal
    if n is None:
        return None
    nz = n[2]
    if nz <= 1e-12:
        return None
    return -cover.gap / nz, nz


def _cover_at(Az: Polyhedron, B: Polyhedron, label: tuple, tol: float, extent_tol: float):
    """同一对特征（面盖）在 A 抬升后的位形 Az 上重新求盖。有效性只看法向与法锥，与平移无关。"""
    kind, af, bf = label
    if kind == "VF":
        return vf_cover(Az, af[1], B, bf[1], tol, extent_tol)
    if kind == "FV":
        return fv_cover(Az, af[1], B, bf[1], tol, extent_tol)
    if kind == "EE":
        return ee_cover(Az, (af[1], af[2]), B, (bf[1], bf[2]), tol, extent_tol)
    return None


def _candidates(A: Polyhedron, B: Polyhedron, offset: Vec3, tol: float, extent_tol: float
                ) -> tuple[list[tuple], float]:
    """完备候选集 [(z, 标签, n_z, 枚举序号)]（z 升序）与法向间隙的舍入地板 r。见 `escape_candidates`。
    extent_tol 是谓词分辨率 geom_tol_eff（长度）：z* 处接触点落在面内 / 段内的边界带与谓词同一把尺——谓词分不开
    的折点两侧，另一支的接触点只越出它的面 ~|Δδ|，照样是候选（并列集因此报出两支，G6 minor[11]）。M0.2 靠把角度
    tol = 1e-9 当绝对长度用碰巧给出了这条带（单位缩放下不对），M0.3 把两种角色拆开。"""
    At = A.translated(offset)
    r = rounding_floor(At, B)
    raw: list[tuple] = []
    for idx, c in enumerate(enumerate_covers3(At, B, window=float("inf"), tol=tol, require_in_extent=False,
                                              include_low_dim=False)):
        zn = _cover_escape_z(c)
        if zn is None:
            continue
        z, nz = zn
        if z * nz >= -r:                  # 法向间隙在舍入以内的负高度 = 已接触，记 0
            raw.append((max(z, 0.0), c.label(), nz, idx))
    raw.sort(key=lambda t: t[0])
    out: list[tuple] = []
    z_prev, Az = None, None
    for z, lab, nz, idx in raw:
        if z <= 0.0:
            out.append((z, lab, nz, idx))     # 已接触/已分离：由调用方的谓词裁决，无需抬升
            continue
        if z_prev is None or z - z_prev > r:
            z_prev, Az = z, At.translated((0.0, 0.0, z))
        c = _cover_at(Az, B, lab, tol, extent_tol)
        if c is not None and c.in_extent:
            out.append((z, lab, nz, idx))
    return out, r


def escape_candidates(A: Polyhedron, B: Polyhedron, offset: Vec3, *, tol: float = 1e-9,
                      geom_tol: float | None = None) -> list[tuple[float, tuple]]:
    """盖给出的**完备候选高度集**：每个法向朝上的盖解一个 gap(z)=0，升序返回 (z, 标签)。

    in_extent 在**各自的 z* 处**判，不在 z=0 处判：
      · z=0 处过滤会漏真解——抬升会让投影移进/移出面，z=0 处的 in_extent 说明不了 z=z* 处的情况。
        2026-09-21 审查实测：曾用 `enumerate_covers3` 的默认过滤，非对称块
        interlocking_pair(5,2,0.3,1.0) 上 25 个随机偏移错 8–10 个（0.44749 vs 真值 0.40054，静默偏大）。
      · 完全不过滤不漏，但会混入"对方面的延长平面上的巧合零间隙"（投影落在面外、不是接触）。
        它的高度可以恰与真解并列（周期剖面上常见），被冻结后导数毫无意义
        （实测 δ=0.3 处并列胜出 FV(A 面 14, L 顶点 9)，∂h/∂amp 给 4.6，真值 0.6）。
      · 真解处两体相触，决定它的接触盖零间隙且接触点落在面内/段内，即在 z* 处 in_extent——
        所以按 z* 处的 in_extent 过滤**既不漏真解、又只留真接触**。
    低维盖（VE3/EV3/VV3）不参与：它们的 gap 是无符号距离（≥ 0），z = −gap/n_z ≤ 0，
    从不给出 z > 0 的候选（旧实现里它们只以 z≈0 出现，随即被裁决循环跳过）。
    法向间隙在舍入地板（64·eps·C）以内的负高度记为 0（旧：绝对 −1e-12，工程坐标上会把相触的盖丢掉）。
    门：tests/test_interlock_escape.py。
    """
    gtol = effective_geom_tol(A.translated(offset), B, geom_tol)
    return [(z, lab) for z, lab, _, _ in _candidates(A, B, offset, tol, gtol)[0]]


def escape_height_covers(A: Polyhedron, B: Polyhedron, offset: Vec3, *,
                         tol: float = 1e-9, geom_tol: float | None = None) -> EscapeSolution:
    """逃逸高度：**盖提供完备候选集、精确谓词裁决**，胜出的候选仍是闭式可微的。

    为什么不能只靠盖：对**凹**体，"全部有效盖间隙非负"既不充分也不必要
    （分离时也有 gap≈−2.7 的有效盖；而抬升会改变 in_extent 与法锥有效性）。
    2026-09-18 实测 δ=0.40 处纯盖规则给 0.300 而真值 0.200。

    正确分工与 G4 的结论一致：盖系统的价值在**完备、带语义的候选集**，不在当谓词。
    真解必是某个盖的零间隙高度（接触位形必有零间隙盖），故在候选集里升序找第一个
    不再贯入者即得——O(候选数) 次谓词调用，远优于盲二分，且结果带着决定它的那个盖标签。
    （曾有 `verify=False` 分支直接返回最大候选——正是上面判定无效的纯盖规则，已删除。）

    精度与并列（见模块"容差政策"）：谓词容差 geom_tol_eff 随尺度；高度精确到 geom_tol_eff / n_z
    （谓词分辨率——比真值低这么多的候选谓词也分不出贯入）；`tied_labels` 用同一把尺（法向间隙
    ≤ geom_tol_eff）判，分辨带内的点报出两支、不会"可微却给错支"。胜出盖 = 接受高度上舍入意义的并列组里
    枚举序第一个，`height` 取它的零间隙高度（冻结闭式在舍入内复现）。
    """
    At = A.translated(offset)
    gtol = effective_geom_tol(At, B, geom_tol)
    cands, r = _candidates(A, B, offset, tol, gtol)
    if polyhedra_overlap(At, B, gtol) != 1:
        return EscapeSolution(0.0, None, len(cands))
    z_prev, penetrating = None, True
    for z, _, nz, _ in cands:
        if z <= 0.0:
            continue
        if z_prev is None or z - z_prev > r:          # 并列候选（同一高度的多个接触盖）只问一次谓词
            x = (offset[0], offset[1], offset[2] + z)
            z_prev, penetrating = z, polyhedra_overlap(A.translated(x), B, gtol) == 1
        if not penetrating:
            return _escape_solution(z, nz, cands, gtol, r)
    raise ValueError("escape height not found among cover candidates (candidate set incomplete?)")


def _escape_solution(z: float, nz: float, cands: list[tuple], gtol: float, r: float) -> EscapeSolution:
    """接受高度 z（谓词首次答"不贯入"的候选）上的裁决：胜出盖与并列集。

    并列组（胜出者从中按枚举序取）：候选在 z 处的法向间隙在舍入以内——|Δz|·n_z' ≤ r·(1 + n_z'/n_z)；
    并列集（tied_labels）：法向间隙在谓词分辨率以内——|Δz|·n_z' ≤ geom_tol_eff + r·(1 + n_z'/n_z)。
    """
    pos = [t for t in cands if t[0] > 0.0]
    exact = [t for t in pos if abs(t[0] - z) * t[2] <= r * (1.0 + t[2] / nz)]
    zw, win, _, iw = min(exact, key=lambda t: t[3])
    band = sorted((t for t in pos if abs(t[0] - z) * t[2] <= gtol + r * (1.0 + t[2] / nz)), key=lambda t: t[3])
    tied = (win,) + tuple(t[1] for t in band if t[3] != iw)
    return EscapeSolution(zw, win, len(cands), tied)


def escape_height_from_frozen_cover(A: Polyhedron, B: Polyhedron, label: tuple,
                                    offset, *, ee_sign: float = 1.0) -> Number:
    """冻结盖下的逃逸高度闭式：z = −gap(offset) / (n·ẑ)，支持对偶数（∂z/∂θ）。

    这是"片 + 划"里的**片**：组合结构（哪个盖当家、EE 法向朝哪）已由 float 路径冻结，
    片内是纯解析表达式，对几何参数逐点可微——与 DDA 冻结活动集后解析可微同构。

    只接**面盖**（VF / FV / EE）：它们的 gap 沿平移仿射，z = −gap/(n·ẑ) 才是零间隙高度。
    低维盖（VE3 / EV3 / VV3）的 gap 是无符号距离，沿竖线非仿射，上式不是逃逸高度——拒收
    （`escape_height_covers` 也从不让它们胜出：gap ≥ 0 ⇒ z ≤ 0）。
    """
    if not label or label[0] not in FACET_KINDS:
        raise ValueError(f"escape height is defined by facet covers (VF/FV/EE) only, got {label[:1]}")
    n = frozen_normal(A, B, label, ee_sign)
    g = frozen_gap(A, B, label, offset, n)
    return -g / n[2]


def dilatancy_profile(A: Polyhedron, B: Polyhedron, *, direction: Vec3 = (1.0, 0.0, 0.0),
                      deltas: list[float] | None = None, tol: float = 1e-9) -> list[dict]:
    """逃逸高度剖面 h(δ) 与剪胀比 tanψ = dh/dδ（中心差分于 δ）。

    tanψ 在无摩擦极限下即横向承载与法向压力之比（Rowe 剪胀关系）。
    `deltas` 是模型单位下的横移量（默认 0.02·i 只适合 lx≈2 的示例块；换尺度请传缩放后的 δ），
    `direction` 应为单位向量。h ×s、tanψ 不变（门：tests/test_invariance_interlock.py）。
    """
    if deltas is None:
        deltas = [i * 0.02 for i in range(1, 16)]
    out = []
    for d in deltas:
        off = (d * direction[0], d * direction[1], d * direction[2])
        sol = escape_height_covers(A, B, off, tol=tol)
        out.append({"delta": d, "h": sol.height, "cover": sol.cover_label,
                    "n_covers": sol.n_candidates})
    for i, row in enumerate(out):
        if 0 < i < len(out) - 1:
            row["tan_psi"] = (out[i + 1]["h"] - out[i - 1]["h"]) / (out[i + 1]["delta"] - out[i - 1]["delta"])
        else:
            row["tan_psi"] = None
    return out
