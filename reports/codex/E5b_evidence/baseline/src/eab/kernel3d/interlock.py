"""互锁逃逸高度与冻结活动盖的可微构造。

给定横向偏移后，暴力路径对“真实内部相交”做二分；盖路径提供浮点
候选高度，由一般闭表面的精确三态谓词验收。正 tol 在该谓词里只改变
分离侧的 -1/0 报告，不吞掉任何真实内部相交；这里只消费 state==1，
因此一律使用零 tol，省掉与贯入判定无关的表面距离计算。

候选根、法向和移动后的坐标仍是浮点构造，不是精确接触高度证书。
同一旧舍入簇中的不同 float 高度必须逐一验收；若该簇均未通过，可在
原有法向舍入报告带 r 内构造一个上探高度，再对实际返回高度对应的
A.translated((off_x,off_y,off_z+height)) 做精确非贯入核验。不得把低处
真实贯入重新标为相触，也不得返回只核验了更高探针的未核验高度。

候选的 extent、法向分辨率及并列组保留既有报告政策：geom_tol_eff 与
rounding_floor 影响报告和构造，不是内部相交判据。winner/tied_labels
仍解释 nominal 候选簇，不保证返回高度是任意折面体的精确最小根；
一般非平面源盖、精确候选完备性和冻结微叉积构造仍由 WO-E5b 处理。

桥接门：tests/test_e5a2_interlock_bridge.py；原逃逸、候选与灵敏度门保留。
"""

from __future__ import annotations

import sys
import math
from dataclasses import dataclass

from ..dual import Dual, Number, val
from ..margin import characteristic_length, effective_geom_tol, rounding_floor
from .covers3 import ee_cover, enumerate_covers3, fv_cover, vf_cover
from .frozen import FACET_KINDS, frozen_ee_sign, frozen_gap, frozen_normal  # noqa: F401  (L5 转出的公共入口)
from .geom3 import Polyhedron, Vec3, cross, dot, norm, polyhedra_overlap, sub
from .geom3 import exact_edge_vector
from .exact_geom import sqrt_rational

_EPS = sys.float_info.epsilon
REL_BRUTE_GEOM_TOL = 1e-12         # oracle 的谓词容差：特征长度 L 的相对量
REL_BRUTE_TOL = 1e-10              # oracle 的二分终止宽度：L 的相对量


# ------------------------------------------------------------------ 暴力 oracle

def escape_height_brute(A: Polyhedron, B: Polyhedron, offset: Vec3, *,
                        hi: float, tol: float | None = None, geom_tol: float | None = None) -> float:
    """Bisect strict interior overlap over a caller-supplied separating bracket.

    The returned upper bracket is nonpenetrating for the actual float-translated
    coordinates. The stopping width is scale-relative (or explicit tol), not a
    topology tolerance. geom_tol is retained/converted for API compatibility;
    it cannot alter the exact intruding Boolean and no distance band is queried.
    The caller must supply an appropriate vertically escaping/monotone bracket.
    """
    At = A.translated(offset)
    floor = rounding_floor(At, B)
    L = characteristic_length(At, B)
    _ = max(REL_BRUTE_GEOM_TOL * L if geom_tol is None else float(geom_tol), floor)  # compatibility conversion only
    ztol = max(REL_BRUTE_TOL * L if tol is None else float(tol), 8.0 * _EPS * abs(hi))

    def intruding(z: float) -> bool:
        x = (offset[0], offset[1], offset[2] + z)
        return polyhedra_overlap(A.translated(x), B, 0.0) == 1

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
    cover_label: tuple | None
    n_candidates: int
    # Legacy reporting ties are selected around nominal constructed roots.
    # They are not a claim that exact membership cannot distinguish the roots.
    tied_labels: tuple = ()


def _normal_noise(A: Polyhedron, B: Polyhedron, cover) -> float:
    """盖法向自身的方向噪声（弧度）：VF 取 B 那张面的、FV 取 A 那张面的面法向噪声；EE 取候选 unit(t_B × t_A) 的
    (n_A + n_B)/sinθ（与 covers3.ee_cover / facet_normal3 同一口径）。"""
    kind, af, bf = cover.label()
    if kind == "VF":
        return B.face_noise(bf[1])
    if kind == "FV":
        return A.face_noise(af[1])
    if kind == "EE":
        ea, eb = (af[1], af[2]), (bf[1], bf[2])
        sine = norm(cross(B.edge_dir(eb), A.edge_dir(ea)))
        if sine == 0.0:
            # E5a exact cones can retain a nonparallel pair whose rounded unit
            # vectors coincide. Preserve this legacy *resolution report* using
            # raw exact edges, rather than divide by the rounded zero. The
            # escape/noise-band semantics themselves remain an E5b task.
            a, b = exact_edge_vector(A, ea), exact_edge_vector(B, eb)
            n = cross(a, b)
            sine = sqrt_rational(dot(n, n) / (dot(a, a) * dot(b, b)))
            if sine == 0.0:
                return float("inf")  # below the representable angular range
        return (A.edge_noise(ea) + B.edge_noise(eb)) / sine
    return 0.0


def _cover_escape_z(cover, noise: float = 0.0) -> tuple[float, float] | None:
    """单个盖在竖直线上的零间隙高度与它的 n_z：解 gap(z) = 0。

    盖的 gap 沿平移 x 是仿射的：gap(x) = n·(a + x − b)，故 gap(z) = gap(offset) + z·(n·ẑ)。
    只有 n·ẑ **可分辨地** > 0 的盖（抬升能把它拉开）才给出有限的逃逸高度：n_z 是被测量，它的噪声是盖法向自身的方向噪声
    `noise`（`_normal_noise`）——竖直墙面的 n_z 在工程坐标下是 ~1e-11 的纯舍入，旧的绝对阈值 1e-12 把它当成"朝上"，
    z = −gap/n_z 是垃圾高度（G6 第五轮 critical：U 形槽里的键在 |t| = 1e5 处报 0.99 / 0.58 / 0.35，真值 0.2）。
    """
    n = cover.normal
    if n is None:
        return None
    nz = n[2]
    if nz <= max(1e-12, noise):
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
        zn = _cover_escape_z(c, _normal_noise(At, B, c))
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
    门："不漏真解"在 tests/test_interlock_escape.py；"只留真接触"与 z* 处的棱内带 = geom_tol_eff 在
    tests/test_interlock_candidates_contract.py（G6 第五轮：此前这两半句只被 test_interlock_sensitivity 间接看护）。
    """
    gtol = effective_geom_tol(A.translated(offset), B, geom_tol)
    return [(z, lab) for z, lab, _, _ in _candidates(A, B, offset, tol, gtol)[0]]


def escape_height_covers(A: Polyhedron, B: Polyhedron, offset: Vec3, *,
                         tol: float = 1e-9, geom_tol: float | None = None) -> EscapeSolution:
    """Return a verified nonpenetrating constructed lift and nominal cover labels.

    Every distinct nominal float height is checked against the exact supplied
    surface. If a rounding cluster has no safe nominal candidate, one upward
    construction at nextafter(z+r/nz,+inf) is tried; the returned lifted height
    itself, not a different probe, must be nonpenetrating. This is construction
    recovery within the existing reporting policy, not a tolerance in topology.

    Cover winners/ties use the nominal cluster and the existing gtol/r report
    bands. The return is not a proof of a globally exact minimum for arbitrary
    folded source rings; that candidate/normal-cone migration remains E5b.
    """
    At = A.translated(offset)
    gtol = effective_geom_tol(At, B, geom_tol)
    cands, r = _candidates(A, B, offset, tol, gtol)
    if polyhedra_overlap(At, B, 0.0) != 1:
        return EscapeSolution(0.0, None, len(cands))
    # Only identical constructed heights can share an exact predicate answer.
    # A lower member of a rounding cluster can penetrate while the very next
    # representable candidate already separates the actual supplied surface.
    groups=[]
    for item in cands:
        if not groups or item[0]-groups[-1][0][0] > r:
            groups.append([item])
        else:
            groups[-1].append(item)
    for group in groups:
        z_prev=None
        for z, _, nz, _ in group:
            if z <= 0.0 or z == z_prev:
                continue
            z_prev=z
            x=(offset[0],offset[1],offset[2]+z)
            if polyhedra_overlap(A.translated(x),B,0.0) != 1:
                return _escape_solution(z,nz,cands,gtol,r)
        # Candidates are floating constructions, not exact contact roots.
        # Try one upward construction within the existing normal-rounding
        # report band. The returned height itself must pass exact no-overlap;
        # we never relabel an interior state as boundary or return unsafe z.
        z, _, nz, _=max(group,key=lambda item:item[0])
        lifted=math.nextafter(z+r/nz,math.inf)
        x=(offset[0],offset[1],offset[2]+lifted)
        if polyhedra_overlap(A.translated(x),B,0.0) != 1:
            if z > 0:
                solution=_escape_solution(z,nz,cands,gtol,r)
                return EscapeSolution(lifted,solution.cover_label,solution.n_candidates,solution.tied_labels)
            tied=tuple(item[1] for item in sorted(group,key=lambda item:item[3]))
            return EscapeSolution(lifted,tied[0],len(cands),tied)
    raise ValueError("escape height not found among cover candidates (candidate set incomplete?)")


def _escape_solution(z: float, nz: float, cands: list[tuple], gtol: float, r: float) -> EscapeSolution:
    """Select nominal-cluster winner and legacy geometric reporting ties.

    These gtol/r bands only label the candidate construction. The caller must
    separately verify and return its actual nonpenetrating constructed height.
    """
    pos = [t for t in cands if t[0] > 0.0]
    exact = [t for t in pos if abs(t[0] - z) * t[2] <= r * (1.0 + t[2] / nz)]
    _, win, _, iw = min(exact, key=lambda t: t[3])
    band = sorted((t for t in pos if abs(t[0] - z) * t[2] <= gtol + r * (1.0 + t[2] / nz)), key=lambda t: t[3])
    tied = (win,) + tuple(t[1] for t in band if t[3] != iw)
    return EscapeSolution(z, win, len(cands), tied)


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
