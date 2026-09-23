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
"""

from __future__ import annotations

from dataclasses import dataclass

from ..dual import Dual, Number, val
from .covers3 import ee_cover, enumerate_covers3, fv_cover, vf_cover
from .frozen import FACET_KINDS, frozen_ee_sign, frozen_gap, frozen_normal  # noqa: F401  (L5 转出的公共入口)
from .geom3 import Polyhedron, Vec3, dot, polyhedra_overlap, sub


# ------------------------------------------------------------------ 暴力 oracle

def escape_height_brute(A: Polyhedron, B: Polyhedron, offset: Vec3, *,
                        hi: float, tol: float = 1e-10, geom_tol: float = 1e-12) -> float:
    """对分离谓词二分：返回使 A 平移 (offset + z·ẑ) 后**不贯入** B 的最小 z ∈ [0, hi]。

    前提：z 足够大时必分离（对竖向抬升的互锁块成立）。不可微，只作 oracle。
    """
    def intruding(z: float) -> bool:
        x = (offset[0], offset[1], offset[2] + z)
        return polyhedra_overlap(A.translated(x), B, geom_tol) == 1

    if not intruding(0.0):
        return 0.0
    if intruding(hi):
        raise ValueError(f"still intruding at z={hi}; raise hi")
    lo, up = 0.0, hi
    while up - lo > tol:
        mid = 0.5 * (lo + up)
        if intruding(mid):
            lo = mid
        else:
            up = mid
    return up


# ------------------------------------------------------------------ 盖路径（可微）

TIE_TOL = 1e-9                     # 候选高度并列的相对容差（与谓词的 geom_tol 同量级）


@dataclass(slots=True)
class EscapeSolution:
    height: float
    cover_label: tuple | None      # 决定逃逸高度的那个盖（冻结的活动集；并列时按枚举序裁决）
    n_candidates: int
    # 在该高度上**并列活跃**的全部接触盖（含 cover_label，且它排第一）。多于一种导数时该点
    # 不可微——cover_label 只是并列里被裁决选中的那一支（审查 C13）。
    tied_labels: tuple = ()


def _cover_escape_z(A: Polyhedron, B: Polyhedron, cover, offset: Vec3) -> float | None:
    """单个盖在竖直线上的零间隙高度：解 gap(z) = 0。

    盖的 gap 沿平移 x 是仿射的：gap(x) = n·(a + x − b)，故 gap(z) = gap(offset) + z·(n·ẑ)。
    只有 n·ẑ > 0 的盖（抬升能把它拉开）才给出有限的逃逸高度。
    """
    n = cover.normal
    if n is None:
        return None
    nz = n[2]
    if nz <= 1e-12:
        return None
    return -cover.gap / nz


def _same_z(z: float, z0: float | None) -> bool:
    return z0 is not None and abs(z - z0) <= 1e-12 * max(1.0, abs(z))


def _cover_at(Az: Polyhedron, B: Polyhedron, label: tuple, tol: float):
    """同一对特征（面盖）在 A 抬升后的位形 Az 上重新求盖。有效性只看法向与法锥，与平移无关。"""
    kind, af, bf = label
    if kind == "VF":
        return vf_cover(Az, af[1], B, bf[1], tol)
    if kind == "FV":
        return fv_cover(Az, af[1], B, bf[1], tol)
    if kind == "EE":
        return ee_cover(Az, (af[1], af[2]), B, (bf[1], bf[2]), tol)
    return None


def escape_candidates(A: Polyhedron, B: Polyhedron, offset: Vec3, *, tol: float = 1e-9
                      ) -> list[tuple[float, tuple]]:
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
    门：tests/test_interlock_escape.py。
    """
    At = A.translated(offset)
    raw: list[tuple[float, tuple]] = []
    for c in enumerate_covers3(At, B, window=float("inf"), tol=tol, require_in_extent=False,
                               include_low_dim=False):
        z = _cover_escape_z(At, B, c, offset)
        if z is not None and z >= -1e-12:
            raw.append((max(z, 0.0), c.label()))
    raw.sort(key=lambda t: t[0])
    out: list[tuple[float, tuple]] = []
    z_prev, Az = None, None
    for z, lab in raw:
        if z <= 0.0:
            out.append((z, lab))          # 已接触/已分离：由调用方的谓词裁决，无需抬升
            continue
        if not _same_z(z, z_prev):
            z_prev, Az = z, At.translated((0.0, 0.0, z))
        c = _cover_at(Az, B, lab, tol)
        if c is not None and c.in_extent:
            out.append((z, lab))
    return out


def escape_height_covers(A: Polyhedron, B: Polyhedron, offset: Vec3, *,
                         tol: float = 1e-9, geom_tol: float = 1e-9) -> EscapeSolution:
    """逃逸高度：**盖提供完备候选集、精确谓词裁决**，胜出的候选仍是闭式可微的。

    为什么不能只靠盖：对**凹**体，"全部有效盖间隙非负"既不充分也不必要
    （分离时也有 gap≈−2.7 的有效盖；而抬升会改变 in_extent 与法锥有效性）。
    2026-09-18 实测 δ=0.40 处纯盖规则给 0.300 而真值 0.200。

    正确分工与 G4 的结论一致：盖系统的价值在**完备、带语义的候选集**，不在当谓词。
    真解必是某个盖的零间隙高度（接触位形必有零间隙盖），故在候选集里升序找第一个
    不再贯入者即得——O(候选数) 次谓词调用，远优于盲二分，且结果带着决定它的那个盖标签。
    （曾有 `verify=False` 分支直接返回最大候选——正是上面判定无效的纯盖规则，已删除。）
    """
    cands = escape_candidates(A, B, offset, tol=tol)
    if polyhedra_overlap(A.translated(offset), B, geom_tol) != 1:
        return EscapeSolution(0.0, None, len(cands))
    z_prev, penetrating = None, True
    for z, lab in cands:
        if z <= 0.0:
            continue
        if not _same_z(z, z_prev):        # 并列候选（同一高度的多个接触盖）只问一次谓词
            x = (offset[0], offset[1], offset[2] + z)
            z_prev, penetrating = z, polyhedra_overlap(A.translated(x), B, geom_tol) == 1
        if not penetrating:
            tied = tuple(l for zz, l in cands if zz > 0.0 and abs(zz - z) <= TIE_TOL * max(1.0, abs(z)))
            return EscapeSolution(z, lab, len(cands), (lab,) + tuple(l for l in tied if l != lab))
    raise ValueError("escape height not found among cover candidates (candidate set incomplete?)")


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
