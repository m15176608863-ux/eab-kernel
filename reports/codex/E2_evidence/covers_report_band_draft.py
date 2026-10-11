"""二维接触盖：∂E(A,B) 的语义化分解。

记号（与 01 精细版一致）：B 固定，A 平移，参考点取自 A。E(A,B) = a0 + (B ⊕ (−A))。
盖类型（方向无关，谁属于哪块记在索引里）：
  VE  A 的顶点 a_i 对 B 的边 e_j          —— E 的 facet，来自 B 的边 j 与 A 的支撑顶点
  EV  B 的顶点 b_j 对 A 的边 e_k          —— E 的 facet，来自 A 的边 k 与 B 的支撑顶点
  VV  A 的顶点对 B 的顶点                  —— E 的顶点（法向集值点）
  FF  平行贴边（退化）                     —— 两条平行边同时贡献 facet

有效性 = 法锥条件（命题 5）：VE(a_i, e_j) 是 ∂E 的极大 facet ⟺ −n_B(j) ∈ relint N_A(a_i)，
即 A 在方向 −n_B(j) 上的**局部**支撑顶点恰是 a_i（凹顶点无法锥，永不有效）。
接触法向统一取"B 指向 A 的分离方向"：VE 用 n_B(j)，EV 用 −n_A(k)，VV 用 unit(a − b)。
间隙 gap 沿该法向度量，>0 分离、<0 侵入、=0 接触。

**凸路径是精确的**（2026-10-10，G6 第五轮之后，`docs/exact_predicates_plan.md` 的 E2）：`convex_entrance_block` /
`membership_convex` / `local_facets` / `ambiguous_facets` 的全部分支判定（凸性、极角序、平行、法锥有效性、成员）都在
`kernel2d/exact.py` 里对给定浮点坐标精确求值，只有精确平行同向的边才并成 FF；`facet_gap` 只是构造量（facet 自己那条边的
法向）。此前的"方向可行窗 + 噪声内共线链"一套浮点带宽在五轮复核里每轮都漏（第五轮 critical：宽窗把 1e-14 的倒角边与 60°
的边并成 FF、链法向取了别的 facet 的边，真实压入 0.15 判"分离"），已删除。
局部单盖（`ve_cover` / `ev_cover` / `vv_cover` / `enumerate_covers`，凹块路径的候选生成器与 legacy 对账的窗口化入口）
仍是浮点 + 容差，下面这段说的是它们：
容差（纪律 F，M0.2）：`tol` / `seg_tol` / `window` 是长度（调用方单位，换单位随之缩放），库内抬到舍入下限
c·eps·C；法锥判据的角容差 `cone_tol` 是无量纲的（sin 单位）——缺省（None）时取长度容差在所涉最短边上张的角
tol/ℓ（旧版直接把长度 tol 当角度用，单位缩放 ×1e3 时角容差也跟着 ×1e3，bb52 真几何上盖集随单位而变），
再抬到角度舍入下限 c·eps·C/ℓ。门：tests/test_invariance_2d.py::test_cover_enumeration_is_invariant。
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import asin, atan2, pi

from .exact import (convexity_violation, entrance_block_exact, ev_side_exact, membership_exact,
                    polygons_overlap_exact, ve_side_exact)
from .geom import (Point, Poly, add, angle_floor, coord_scale, cross, dot, edge, neg, norm, outward_normal,
                   round_floor, sub, turn_angle, turn_floor, unit)


@dataclass(slots=True)
class Cover:
    kind: str                 # "VE" | "EV" | "VV" | "FF"
    a_index: int              # VE/VV: A 的顶点；EV/FF: A 的边
    b_index: int              # VE/FF: B 的边；EV/VV: B 的顶点
    normal: Point | None      # B → A 的分离方向（VV 重合时 None）
    gap: float                # 沿 normal 的有符号间隙
    param: float | None       # 投影参数（VE/EV），VV 为 None
    point: Point | None       # 边上投影点 / 顶点
    strict: bool              # 法锥相对内部条件严格成立（VV：分离方向落在交锥内）
    # 见证点对（距离完备性门用）：point_a 在 A 上、point_b 在 B 上，|point_a − point_b| 即该盖给出的
    # 特征间距。VE：(A 的顶点, 它在 B 边所在直线上的垂足)；EV：(B 顶点在 A 边直线上的垂足, B 的顶点)；
    # VV：(A 的顶点, B 的顶点)。投影参数落在 [0,1] 内时两点都在各自多边形上，见证距离 ≥ 真距离。
    point_a: Point | None = None
    point_b: Point | None = None

    def label(self) -> tuple[str, int, int]:
        return (self.kind, self.a_index, self.b_index)


# ---------------------------------------------------------------- 法锥

def normal_cone(poly: Poly, i: int, tol: float = 0.0) -> tuple[Point, Point] | None:
    """顶点 i 的法锥（CCW 极角序）：(n_prev, n_next)；反射（凹）顶点返回 None。

    tol 以 sin(转角) 计：turn < -tol 判为反射；平直顶点（turn≈0）保留——其法锥退化为单射线，
    对应 legacy 里"直边中间的顶点贴在对方边上"这类接触（tol=0 时仍保留 turn==0）。
    tol 再抬到该顶点转角的舍入下限 `geom.turn_floor`（平直顶点经刚体运动后转角 ±eps·C/ℓ，不许翻成反射）。
    邻边为零长边时抛 ValueError('zero-length edge ...')（不是 ZeroDivisionError）。
    """
    n = len(poly)
    # 零长邻边先于转角判：atan2(0,0)=0 会把它伪装成"平直顶点"（审查 C19）。清晰报错，不静默跳过——
    # 跳过会让重复点处那个真实角点失去法锥，距离完备性静默破缺。
    for k in ((i - 1) % n, i % n):
        if poly[k] == poly[(k + 1) % n]:
            raise ValueError(f"zero-length edge {k} at vertex {i % n}: consecutive duplicate vertex {poly[k]}; "
                             f"strip duplicates at the reader boundary")
    # 用转角（atan2）判反射：sin 分不清 θ 与 π−θ，会把 178° 的窄缝当作 2° 的近共线放行（审查 r1）。
    ta = turn_angle(poly, i)
    if ta < 0.0 and ta < -max(asin(min(max(tol, 0.0), 1.0)), turn_floor(poly, i)):
        return None
    return outward_normal(poly, (i - 1) % n), outward_normal(poly, i)


def cone_width(cone: tuple[Point, Point]) -> float:
    """法锥角宽（弧度，(-π, π]）：n_prev 到 n_next 的有向转角。平直顶点 0，容差内微反射为负。"""
    return atan2(cross(cone[0], cone[1]), dot(cone[0], cone[1]))


def in_cone(cone: tuple[Point, Point], v: Point, tol: float = 0.0) -> int:
    """v 相对法锥 (n_prev → n_next, CCW)：1 严格内部 / 0 落在边界（容差 tol）/ -1 外部。凸顶点锥角 < π。"""
    n_prev, n_next = cone
    c1 = cross(n_prev, v)
    c2 = cross(v, n_next)
    if c1 > tol and c2 > tol:
        return 1
    if c1 >= -tol and c2 >= -tol and dot(v, add(n_prev, n_next)) > 0:
        return 0
    return -1


def _project(p: Point, a: Point, b: Point) -> tuple[float, Point]:
    e = sub(b, a)
    s = dot(sub(p, a), e) / dot(e, e)
    return s, add(a, (e[0] * s, e[1] * s))


def _edge_len(P: Poly, k: int) -> float:
    p, q = edge(P, k)
    return norm(sub(q, p))


# ---------------------------------------------------------------- 单个盖

def _vertex_ring(P: Poly, i: int) -> tuple[Point, Point, Point]:
    n = len(P)
    return P[(i - 1) % n], P[i % n], P[(i + 1) % n]


def _angle_tols(tol: float, cone_tol: float | None, pts, lengths) -> tuple[float, float, float]:
    """(法锥角容差, 长度容差张的角, 角度舍入下限)，都无量纲。ℓ = 所涉最短边，C = 所涉点的坐标量级。
    cone_tol 缺省取 tol/ℓ；两者都抬到 c·eps·C/ℓ。零长边时返回 0（不放宽任何判据；随后的 outward_normal /
    normal_cone 对零长边清晰报 ValueError，审查 C19）。"""
    ell = min(lengths)
    if ell <= 0.0:
        return 0.0, 0.0, 0.0
    fl = angle_floor(coord_scale(pts), ell)
    t_ang = max(tol / ell, fl)
    return (max(cone_tol, fl) if cone_tol is not None else t_ang), t_ang, fl


def ve_cover(A: Poly, ia: int, B: Poly, jb: int, tol: float = 0.0, cone_tol: float | None = None) -> Cover | None:
    """A 的顶点 ia 对 B 的边 jb。无效（法锥外/反射顶点）返回 None。

    tol：长度容差。cone_tol：法锥判据的角容差（sin 单位，无量纲；None = tol/ℓ，ℓ 为所涉三条边的最短者）。
    legacy 兼容模式给 sin(h1°)。两者都抬到角度舍入下限 c·eps·C/ℓ（纪律 F）。
    """
    nB = outward_normal(B, jb)                       # 零长边在这里清晰报错
    ap, a, an = _vertex_ring(A, ia)
    b0, b1 = edge(B, jb)
    ct, _, _ = _angle_tols(tol, cone_tol, (ap, a, an, b0, b1), (norm(sub(a, ap)), norm(sub(an, a)), norm(sub(b1, b0))))
    cone = normal_cone(A, ia, ct)
    if cone is None:
        return None
    side = in_cone(cone, neg(nB), ct)
    if side < 0:
        return None
    s, pt = _project(a, b0, b1)
    return Cover("VE", ia, jb, nB, dot(nB, sub(a, b0)), s, pt, side == 1, a, pt)


def ev_cover(A: Poly, ka: int, B: Poly, ib: int, tol: float = 0.0, cone_tol: float | None = None) -> Cover | None:
    """B 的顶点 ib 对 A 的边 ka。容差口径同 `ve_cover`。"""
    nA = outward_normal(A, ka)
    bp, b, bn = _vertex_ring(B, ib)
    a0, a1 = edge(A, ka)
    ct, _, _ = _angle_tols(tol, cone_tol, (bp, b, bn, a0, a1), (norm(sub(b, bp)), norm(sub(bn, b)), norm(sub(a1, a0))))
    cone = normal_cone(B, ib, ct)
    if cone is None:
        return None
    side = in_cone(cone, neg(nA), ct)
    if side < 0:
        return None
    s, pt = _project(b, a0, a1)
    return Cover("EV", ka, ib, neg(nA), dot(nA, sub(b, a0)), s, pt, side == 1, pt, b)


def _ang(v: Point) -> float:
    return atan2(v[1], v[0])


def _span(lo: Point, hi: Point) -> tuple[float, float]:
    a0, a1 = _ang(lo), _ang(hi)
    if a1 < a0:
        a1 += 2 * pi
    return a0, a1


def vv_cover(A: Poly, ia: int, B: Poly, jb: int, tol: float = 0.0, cone_tol: float | None = None) -> Cover | None:
    """A 的顶点 ia 对 B 的顶点 jb：E 的顶点。有效 ⟺ N_B(b) 与 −N_A(a) 的相对内部相交。

    活跃（strict=True）还要求分离方向 a − b 落在该交锥内，否则参考点离这个 E 顶点不是最近。
    容差（纪律 F）：法锥用 `_angle_tols` 的角容差；交锥宽度与活跃判据用长度容差张的角 tol/ℓ（旧版直接拿长度 tol
    当弧度）；锥宽判"退化"用角度舍入下限；两顶点重合判据用长度舍入下限。ℓ 取两顶点的四条邻边的最短者。
    """
    ap, a, an = _vertex_ring(A, ia)
    bp, b, bn = _vertex_ring(B, jb)
    ct, vt, fl = _angle_tols(tol, cone_tol, (ap, a, an, bp, b, bn),
                             (norm(sub(a, ap)), norm(sub(an, a)), norm(sub(b, bp)), norm(sub(bn, b))))
    ca = normal_cone(A, ia, ct)
    cb = normal_cone(B, jb, ct)
    if ca is None or cb is None:
        return None
    # 锥宽 ≤ 舍入下限（平直顶点或容差内微反射）→ 法锥退化为单射线，相对内部交为空，不是 E 的顶点。
    # 不能对原始法向做 _span：数值共线顶点的 n_next 略偏 CW 会回绕成 ≈360° 假锥（审查 r3，31% 触发）。
    wa, wb = cone_width(ca), cone_width(cb)
    if wa <= fl or wb <= fl:
        return None
    a_lo = _ang(neg(ca[0]))
    b_lo = _ang(cb[0])
    s1 = (a_lo, a_lo + wa)
    s2 = (b_lo, b_lo + wb)
    best: tuple[float, float] | None = None
    for k in (-1, 0, 1):
        lo = max(s1[0], s2[0] + 2 * pi * k)
        hi = min(s1[1], s2[1] + 2 * pi * k)
        if best is None or hi - lo > best[1] - best[0]:
            best = (lo, hi)
    assert best is not None
    if best[1] - best[0] <= vt:
        return None
    d = sub(a, b)
    dist = norm(d)
    if dist <= round_floor(max(abs(a[0]), abs(a[1]), abs(b[0]), abs(b[1]))):
        return Cover("VV", ia, jb, None, 0.0, None, a, True, a, b)
    u = unit(d)
    au = _ang(u)
    # 分离方向 u = unit(a − b) 自身的噪声 rfl/|a − b|（三维 ve3/ev3/vv3 第三轮已补 fl/|v|，二维同类第四轮补上）：
    # 方向恰在交锥边界、两顶点间距远小于坐标量级时，strict 曾随刚体运动对半翻转，盖标签集不再不变（G6 第四轮 major）
    du = round_floor(max(abs(a[0]), abs(a[1]), abs(b[0]), abs(b[1]))) / dist
    active = any(best[0] - vt - du <= au + 2 * pi * k <= best[1] + vt + du for k in (-1, 0, 1))
    return Cover("VV", ia, jb, u, dist, None, a, active, a, b)


# ---------------------------------------------------------------- 枚举

def enumerate_covers(A: Poly, B: Poly, *, window: float, tol: float = 0.0,
                     require_in_segment: bool = True, cone_tol: float | None = None,
                     seg_tol: float | None = None) -> list[Cover]:
    """当前位形下所有有效且落在距离窗口内的盖。A、B 均为 CCW。

    window：|gap| ≤ window 才收（对应 legacy 的 d0 搜索距离，两侧对称，调用方再筛）。
    require_in_segment：VE/EV 的投影参数须在 [0,1]（容差 seg_tol/边长，缺省 tol）。VV 只收活跃的。
    cone_tol：法锥角容差（sin 单位，无量纲）；严格数学用 0，legacy 兼容用 sin(h1°)；None = tol/ℓ。
    长度量（window、seg_tol、tol）都抬到舍入下限 c·eps·C（C = 两块的坐标量级；纪律 F）。
    """
    lf = round_floor(coord_scale(A, B))
    st = max(tol if seg_tol is None else seg_tol, lf)
    window = max(window, lf)
    out: list[Cover] = []
    nA, nB = len(A), len(B)
    for ia in range(nA):
        for jb in range(nB):
            c = ve_cover(A, ia, B, jb, tol, cone_tol)
            if c is not None and abs(c.gap) <= window:
                if require_in_segment:
                    # 带 = (长度带 + 杠杆项 |a − b0|·rfl/|e|) / |e|：投影参数还带边方向噪声 × 到顶点的距离（三维第三轮补的同一项；
                    # 顶点恰投影在短边端点、间隙 ≫ 边长时旧带宽 st/|e| 远小于它，盖随刚体运动随机出入边内带，G6 第四轮 minor）
                    le = _edge_len(B, jb)
                    band = (st + lf * norm(sub(A[ia], edge(B, jb)[0])) / le) / le
                    if not (-band <= c.param <= 1.0 + band):
                        continue
                out.append(c)
    for ka in range(nA):
        for ib in range(nB):
            c = ev_cover(A, ka, B, ib, tol, cone_tol)
            if c is not None and abs(c.gap) <= window:
                if require_in_segment:
                    le = _edge_len(A, ka)
                    band = (st + lf * norm(sub(B[ib], edge(A, ka)[0])) / le) / le
                    if not (-band <= c.param <= 1.0 + band):
                        continue
                out.append(c)
    for ia in range(nA):
        for jb in range(nB):
            c = vv_cover(A, ia, B, jb, tol, cone_tol)
            if c is not None and c.strict and c.gap <= window:
                out.append(c)
    return out


def first_entrance_for_vertex(A: Poly, ia: int, B: Poly, *, window: float, tol: float = 0.0,
                              cone_tol: float | None = None) -> Cover | None:
    """顶点 ia 对块 B 的首入盖：投影在边内的有效 VE 盖里取最大间隙（最浅侵入 / 最先被触及）。

    与 tf.cpp 每接触取最大 v1 者作当前入口是同一裁决；无边内 VE 时退到活跃 VV。
    适用范围：B 凸，或已侵入情形（最短出口）。B 凹且分离时（如 L 形内角）"最大间隙"会选到远边——
    审查 r8 指出这与命题 7 的"首入"不同，凹块分离情形应取最小正间隙，待 Phase 3 处理。
    """
    lf = round_floor(coord_scale(A, B))
    st, window = max(tol, lf), max(window, lf)
    best: Cover | None = None
    for jb in range(len(B)):
        c = ve_cover(A, ia, B, jb, tol, cone_tol)
        if c is None or abs(c.gap) > window:
            continue
        le = _edge_len(B, jb)
        band = (st + lf * norm(sub(A[ia], edge(B, jb)[0])) / le) / le          # 含杠杆项，同 enumerate_covers
        if not (-band <= c.param <= 1.0 + band):
            continue
        if best is None or c.gap > best.gap:
            best = c
    if best is not None:
        return best
    for jb in range(len(B)):
        c = vv_cover(A, ia, B, jb, tol, cone_tol)
        if c is not None and c.strict and c.gap <= window:
            if best is None or c.gap < best.gap:
                best = c
    return best


# ---------------------------------------------------------------- 凸情形的全局构造（Minkowski 合并）

@dataclass(slots=True)
class EntranceBlock:
    vertices: list[Point]                     # E 的顶点（CCW）
    facets: list[tuple[str, int, int]]        # 每条边的盖标签 (kind, a_index, b_index)，对应 vertices[i]->[i+1]
    vv: list[tuple[int, int]]                 # 每个顶点对应的 (A 顶点, B 顶点)


def convex_entrance_block(A: Poly, B: Poly, a0: Point = (0.0, 0.0), tol: float = 0.0) -> EntranceBlock:
    """A、B 凸且 CCW。E = a0 + (B ⊕ (−A))，边按极角归并，每条边带盖标签 (kind, A 的下标, B 的下标)。

    **精确**（`kernel2d.exact.entrance_block_exact`）：凸性、极角序、平行全部在 Fraction 上判，只有**精确**平行同向的
    两条边才并成 FF；顶点 b_j − a_i 先精确算、再加 a0 后舍入成浮点输出。输入须**精确**凸（平直顶点允许；零长边、反射顶点、
    折回、绕圈不止一次都清晰报 ValueError）——刚体运动把平直顶点舍入成微凹时，这里如实拒收，调用方改走凹块路径
    （`enumerate_covers` + 精确谓词），不再像旧版那样在容差内"吞下"微凹（那正是五轮复核里静默错判的来源之一）。
    `tol` 不再参与任何判定（保留参数只为兼容调用方）；需要"容差内平行"的口径（如 legacy 的平行贴边）由 L5 适配器显式给窗。
    """
    for name, poly in (("A", A), ("B", B)):
        why = convexity_violation(poly)
        if why is not None:
            raise ValueError(f"input polygon {name} not convex: {why}")
    ex = entrance_block_exact(A, B)
    fa0 = (Fraction(a0[0]), Fraction(a0[1]))
    verts = [(float(v[0] + fa0[0]), float(v[1] + fa0[1])) for v in ex.vertices]
    return EntranceBlock(verts, [f.label for f in ex.facets], list(ex.pairs))


def _facet_normal_own(A: Poly, B: Poly, label: tuple[str, int, int]) -> tuple[Point, Point]:
    """facet 的外法向（B → A 的分离方向）与它过的一点（未加平移）：取 facet **自己那条边**的法向。
    FF 的两条边精确平行，取较长边的法向（浮点构造更准，方向相同）。"""
    kind, ai, bj = label
    if kind == "VE":
        return outward_normal(B, bj), sub(edge(B, bj)[0], A[ai])
    if kind == "EV":
        return neg(outward_normal(A, ai)), sub(B[bj], edge(A, ai)[0])
    b0, b1 = edge(B, bj)
    a0, a1 = edge(A, ai)
    n = outward_normal(B, bj) if norm(sub(b1, b0)) >= norm(sub(a1, a0)) else neg(outward_normal(A, ai))
    return n, sub(b0, a0)


def facet_gap(A: Poly, B: Poly, label: tuple[str, int, int], x: Point) -> float:
    """E 的一条 facet 在平移 x 下的有符号间隙（>0 参考点在该 facet 外侧）。**构造量**：facet 自己那条边的单位外法向点乘
    (x − facet 上一点)；成员与首入的**分支**判定不看它的符号（见 `membership_convex`、`entrance.first_entrance`）。"""
    n, p = _facet_normal_own(A, B, label)
    return dot(n, sub(x, p))


def _in_exact_boundary_band(ex, x: Point, tol: float) -> bool:
    """到精确 E 边界闭线段的距离不大于 tol；全部比较距离平方，不用浮点构造量或舍入地板。"""
    X = (Fraction(x[0]), Fraction(x[1]))
    t2 = Fraction(tol) ** 2
    for f in ex.facets:
        dx, dy = f.direction
        ux, uy = X[0] - f.start[0], X[1] - f.start[1]
        l2 = dx * dx + dy * dy
        along = ux * dx + uy * dy
        if along <= 0:
            distance2 = ux * ux + uy * uy
        elif along >= l2:
            distance2 = (ux - dx) ** 2 + (uy - dy) ** 2
        else:
            distance2 = (dx * uy - dy * ux) ** 2 / l2
        if distance2 <= t2:
            return True
    return False


def membership_convex(A: Poly, B: Poly, x: Point, tol: float = 0.0,
                      eb: EntranceBlock | None = None) -> int:
    """参考点相对 E 的位置：1 内部（A+x 与 B 内部相交）/ 0 边界或显式报告带 / -1 外部（分离）。

    tol=0 时**对给定浮点坐标精确**：A、B 精确凸时用精确 E 的 facet 符号，否则（包括刚体运动把平直顶点舍入成微凹）
    用一般简单多边形的精确相交；x 的加法也在 Fraction 上做。tol（长度）只把有边界距离见证的非零答案报告为 0，
    不吞带外答案、不抬到舍入下限。凸对完整检验到 E 边界的欧氏距离 ≤ tol（精确线段距离平方；外角不等同于最大 facet gap）。
    非凸对没有全局 E：只沿四条坐标轴探到距离 tol，精确状态改变即由连续性证明其间有边界；这是**保守、不完备**的报告带，
    无见证时保留精确答案，不承诺检出全部带内样本。完整非凸 E 距离留待全局构造。eb 保留只为兼容旧调用。
    门：tests/test_kernel2d_report_band.py（闭式欧氏带、巨大坐标微小 tol、非凸见证与不完备性、Fraction 平移）。"""
    if convexity_violation(A) is None and convexity_violation(B) is None:
        ex = entrance_block_exact(A, B)
        s = membership_exact(A, B, x, ex)
        if s == 0 or not tol > 0.0:
            return s
        if tol == float("inf"):
            return 0
        return 0 if _in_exact_boundary_band(ex, x, tol) else s
    s = polygons_overlap_exact(A, B, x)
    if s == 0 or not tol > 0.0:
        return s
    if tol == float("inf"):
        return 0
    X, t = (Fraction(x[0]), Fraction(x[1])), Fraction(tol)
    for dx, dy in ((t, 0), (-t, 0), (0, t), (0, -t)):
        if polygons_overlap_exact(A, B, (X[0] + dx, X[1] + dy)) != s:
            return 0
    return s

def local_facets(A: Poly, B: Poly, tol: float = 0.0) -> set[tuple[str, int, int]]:
    """凸情形下局部法锥规则（命题 5）给出的全部**严格**有效 VE / EV 标签，精确判（`exact.ve_side_exact` /
    `ev_side_exact`）。定理检验：与 `convex_entrance_block` 排除 FF 及精确边界支持分段后的严格 facet 集**精确相等**。
    平直边链的剩余非 FF 分段也可能只有非严格支持，不能仅按标签不是 FF 就算严格。`tol` 不参与。
    门：tests/test_kernel2d_e2_contract.py 的独立全顶点投影支撑 oracle 与平直链门。"""
    return _local_facets(A, B, 1)


def ambiguous_facets(A: Poly, B: Poly, tol: float = 0.0) -> set[tuple[str, int, int]]:
    """局部法锥规则判为"恰在法锥边界上"的 VE / EV（精确判据 = 0）：对方边与本顶点的一条邻边**精确**平行，
    全局构造里它们并进 FF（或在平直顶点处成为相邻共线 facet）。`tol` 不参与。"""
    return _local_facets(A, B, 0)


def _local_facets(A: Poly, B: Poly, want: int) -> set[tuple[str, int, int]]:
    out: set[tuple[str, int, int]] = set()
    for ia in range(len(A)):
        for jb in range(len(B)):
            if ve_side_exact(A, ia, B, jb) == want:
                out.add(("VE", ia, jb))
    for ka in range(len(A)):
        for ib in range(len(B)):
            if ev_side_exact(A, ka, B, ib) == want:
                out.add(("EV", ka, ib))
    return out
