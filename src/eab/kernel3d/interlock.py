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
from .covers3 import enumerate_covers3
from .frozen import frozen_ee_sign, frozen_gap, frozen_normal  # noqa: F401  (L5 转出的公共入口)
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

@dataclass(slots=True)
class EscapeSolution:
    height: float
    cover_label: tuple | None      # 决定逃逸高度的那个盖（冻结的活动集）
    n_candidates: int


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


def escape_candidates(A: Polyhedron, B: Polyhedron, offset: Vec3, *, tol: float = 1e-9
                      ) -> list[tuple[float, tuple]]:
    """盖给出的**完备候选高度集**：每个法向朝上的盖解一个 gap(z)=0，升序返回 (z, 标签)。

    不施加 in_extent 过滤——抬升会让投影移出面，z=0 处的 in_extent 说明不了 z=z* 处的情况；
    候选集宁可多不可漏（漏了就丢掉真解）。
    """
    At = A.translated(offset)
    out: list[tuple[float, tuple]] = []
    for c in enumerate_covers3(At, B, window=float("inf"), tol=tol):
        z = _cover_escape_z(At, B, c, offset)
        if z is not None and z >= -1e-12:
            out.append((max(z, 0.0), c.label()))
    out.sort(key=lambda t: t[0])
    return out


def escape_height_covers(A: Polyhedron, B: Polyhedron, offset: Vec3, *,
                         tol: float = 1e-9, geom_tol: float = 1e-9,
                         verify: bool = True) -> EscapeSolution:
    """逃逸高度：**盖提供完备候选集、精确谓词裁决**，胜出的候选仍是闭式可微的。

    为什么不能只靠盖：对**凹**体，"全部有效盖间隙非负"既不充分也不必要
    （分离时也有 gap≈−2.7 的有效盖；而抬升会改变 in_extent 与法锥有效性）。
    2026-09-18 实测 δ=0.40 处纯盖规则给 0.300 而真值 0.200。

    正确分工与 G4 的结论一致：盖系统的价值在**完备、带语义的候选集**，不在当谓词。
    真解必是某个盖的零间隙高度（接触位形必有零间隙盖），故在候选集里升序找第一个
    不再贯入者即得——O(候选数) 次谓词调用，远优于盲二分，且结果带着决定它的那个盖标签。
    """
    cands = escape_candidates(A, B, offset, tol=tol)
    if not verify:
        best = max((z for z, _ in cands), default=0.0)
        lab = next((l for z, l in cands if z == best), None)
        return EscapeSolution(best, lab, len(cands))
    if polyhedra_overlap(A.translated(offset), B, geom_tol) != 1:
        return EscapeSolution(0.0, None, len(cands))
    for z, lab in cands:
        if z <= 0.0:
            continue
        x = (offset[0], offset[1], offset[2] + z)
        if polyhedra_overlap(A.translated(x), B, geom_tol) != 1:
            return EscapeSolution(z, lab, len(cands))
    raise ValueError("escape height not found among cover candidates (candidate set incomplete?)")


def escape_height_from_frozen_cover(A: Polyhedron, B: Polyhedron, label: tuple,
                                    offset, *, ee_sign: float = 1.0) -> Number:
    """冻结盖下的逃逸高度闭式：z = −gap(offset) / (n·ẑ)，支持对偶数（∂z/∂θ）。

    这是"片 + 划"里的**片**：组合结构（哪个盖当家、EE 法向朝哪）已由 float 路径冻结，
    片内是纯解析表达式，对几何参数逐点可微——与 DDA 冻结活动集后解析可微同构。
    """
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
