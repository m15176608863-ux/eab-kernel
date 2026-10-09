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

容差（纪律 F，M0.2）：`tol` / `seg_tol` / `window` 是长度（调用方单位，换单位随之缩放），库内抬到舍入下限
c·eps·C；法锥判据的角容差 `cone_tol` 是无量纲的（sin 单位）——缺省（None）时取长度容差在所涉最短边上张的角
tol/ℓ（旧版直接把长度 tol 当角度用，单位缩放 ×1e3 时角容差也跟着 ×1e3，bb52 真几何上盖集随单位而变），
再抬到角度舍入下限 c·eps·C/ℓ。门：tests/test_invariance_2d.py::test_cover_enumeration_is_invariant。
"""

from __future__ import annotations

from dataclasses import dataclass
from math import asin, atan2, pi

from .geom import (Point, Poly, add, angle_floor, convex_hull, coord_scale, cross, dot, edge, neg, norm, outward_normal, reflect,
                   round_floor, signed_area, sub, turn_angle, turn_floor, unit, zero_length_edges)


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
    active = any(best[0] - vt <= au + 2 * pi * k <= best[1] + vt for k in (-1, 0, 1))
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
                    le = _edge_len(B, jb)
                    if not (-st / le <= c.param <= 1.0 + st / le):
                        continue
                out.append(c)
    for ka in range(nA):
        for ib in range(nB):
            c = ev_cover(A, ka, B, ib, tol, cone_tol)
            if c is not None and abs(c.gap) <= window:
                if require_in_segment:
                    le = _edge_len(A, ka)
                    if not (-st / le <= c.param <= 1.0 + st / le):
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
        if not (-st / le <= c.param <= 1.0 + st / le):
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


def _start_index(P: Poly) -> int:
    return min(range(len(P)), key=lambda i: (P[i][1], P[i][0]))


def _edge_angle(P: Poly, i: int) -> float:
    p, q = edge(P, i)
    a = atan2(q[1] - p[1], q[0] - p[0])
    return a if a >= 0.0 else a + 2 * pi


def _unwrapped_angles(a0: float, edges: list[Point], name: str) -> list[float]:
    """从最低点出发的凸 CCW 多边形各边的方向角，按**相邻边转角累加**得到（不跨 0/2π 缝）。

    首边理想方向角 ∈ [0, π)，舍入可使它成 −δ（_edge_angle 映到 2π − δ），减回去。之后每条边 = 前一条 + 转角
    atan2(e₀ × e₁, e₀ · e₁)；转角为负的只有凸包深度 ≤ t 的微凹顶点（上面已核过），夹平成 0。
    总转角（含末边回到首边）必须是 2π：绕圈不止一次的非简单多边形（五角星，顶点都在凸包上、深度检验看不见）总转角是 4π。
    M0.3 第一版按 [0, 2π) 里的极角判"下降 > π/2 即绕圈"：平直顶点落在最底边上、刚体运动后微凹时，两条相邻边的极角成 δ 与
    2π − δ，后面的下降 ≈ 3π/2 被当成绕圈误拒（G6 第三轮 major）。"""
    if a0 > pi:
        a0 -= 2 * pi
    angs = [a0]
    total = 0.0
    for k in range(1, len(edges)):
        turn = atan2(cross(edges[k - 1], edges[k]), dot(edges[k - 1], edges[k]))
        total += turn
        angs.append(angs[-1] + max(turn, 0.0))
    total += atan2(cross(edges[-1], edges[0]), dot(edges[-1], edges[0]))
    if abs(total - 2 * pi) > 1e-6:
        raise ValueError(f"input polygon {name} not convex: total turning angle {total:.6f} rad is not 2π "
                         f"(the boundary winds more than once)")
    return angs


def _hull_defect(P: Poly) -> float:
    """P 的顶点落在其凸包边界以内的最大深度（长度）：凸多边形为 0，平直顶点经刚体运动后的微凹为舍入级。"""
    H = convex_hull(P)
    if len(H) < 3:
        return 0.0
    return max(min(dot(outward_normal(H, k), sub(H[k], v)) for k in range(len(H))) for v in P)


def convex_entrance_block(A: Poly, B: Poly, a0: Point = (0.0, 0.0), tol: float = 0.0) -> EntranceBlock:
    """A、B 凸且 CCW。E = a0 + (B ⊕ (−A))，边按极角合并，每条边带盖标签。

    tol 为**长度**容差（调用方单位），抬到舍入下限 c·eps·C（C = A、B 的坐标量级）。两处用它，都逐特征、按长度判：
      · 平行边合并：B 的边 e_P 与 −A 的边 e_Q 同向且 |e_P × e_Q| ≤ t·min(|e_P|, |e_Q|) 才并成一条 FF 边。
        并后的 FF 面以 B 的边法向过合并起点，偏离真实的两段边界至多 |e_Q|·|sin Δθ| ≤ t——合并不引入超过 t 的误差；
      · 凸性前提：顶点落在自身凸包边界以内的深度 ≤ t（平直顶点经刚体运动后的舍入级微凹）才吞下它的极角下降，
        否则清晰报错（审查 r4c：微凹被 +2π 级联静默吃掉，产出非凸 E）。
    旧版（M0.2 到 cad2ffc）两处都用**角度**：tol 是弧度，再抬到极角舍入下限 c·eps·C/ℓ_min，ℓ_min 取**整个多边形**
    的最短边——多边形上一条 1e-8 的短边放在 1e5 处，下限就是 0.14 rad，夹角 0.1 rad 的两条长边被并成 FF，
    成员判定静默答反（与三维 covers3 的 G6 critical 同类）；membership_convex 还把长度 tol 直接当弧度传进来（G6 major）。
    零长边（连续重复顶点）清晰报错（审查 C19）。
    """
    for name, poly in (("A", A), ("B", B)):
        bad = zero_length_edges(poly)
        if bad:
            raise ValueError(f"zero-length edge {bad[0]} in {name} (consecutive duplicate vertex {poly[bad[0]]}); "
                             f"strip duplicates at the reader boundary")
    t = max(tol, round_floor(coord_scale(A, B)))
    for name, poly in (("A", A), ("B", B)):
        if signed_area(poly) <= 0.0:
            raise ValueError(f"input polygon {name} is not counter-clockwise (signed area {signed_area(poly):.3e})")
        dfc = _hull_defect(poly)
        if dfc > t:
            raise ValueError(f"input polygon {name} not convex: a vertex lies {dfc:.3e} inside its convex hull "
                             f"(tolerance {t:.3e})")
    P = B
    Q = reflect(A)                # Q[k] = −A[k]；Q 的边 k = −(A 的边 k)
    n, m = len(P), len(Q)
    iP, iQ = _start_index(P), _start_index(Q)
    eP = [sub(*reversed(edge(P, (iP + k) % n))) for k in range(n)]
    eQ = [sub(*reversed(edge(Q, (iQ + k) % m))) for k in range(m)]
    angP = _unwrapped_angles(_edge_angle(P, iP), eP, "B")
    angQ = _unwrapped_angles(_edge_angle(Q, iQ), eQ, "A")
    i = j = 0
    cur = add(P[iP], Q[iQ])
    verts = [add(cur, a0)]
    facets: list[tuple[str, int, int]] = []
    vv = [(iQ % m, iP % n)]
    while i < n or j < m:
        take_p = take_q = False
        if j >= m:
            take_p = True
        elif i >= n:
            take_q = True
        else:
            d = angP[i] - angQ[j]
            ep, eq = eP[i], eQ[j]
            if dot(ep, eq) > 0.0 and abs(cross(ep, eq)) <= t * min(norm(ep), norm(eq)):
                take_p = take_q = True
            elif d < 0:
                take_p = True
            else:
                take_q = True
        bi = (iP + i) % n
        aj = (iQ + j) % m
        if take_p and take_q:
            p0, p1 = edge(P, bi)
            q0, q1 = edge(Q, aj)
            step = add(sub(p1, p0), sub(q1, q0))
            facets.append(("FF", aj, bi))
            i += 1
            j += 1
        elif take_p:
            p0, p1 = edge(P, bi)
            step = sub(p1, p0)
            facets.append(("VE", aj, bi))          # B 的边 bi 与 A 的顶点 aj
            i += 1
        else:
            q0, q1 = edge(Q, aj)
            step = sub(q1, q0)
            facets.append(("EV", aj, bi))          # A 的边 aj 与 B 的顶点 bi
            j += 1
        cur = add(cur, step)
        verts.append(add(cur, a0))
        vv.append(((iQ + j) % m, (iP + i) % n))
    verts.pop()   # 闭合点 = 起点
    vv.pop()
    return EntranceBlock(verts, facets, vv)


def facet_gap(A: Poly, B: Poly, label: tuple[str, int, int], x: Point) -> float:
    """E 的一条 facet 在平移 x 下的有符号间隙（>0 参考点在该 facet 外侧）。"""
    kind, ai, bj = label
    if kind in ("VE", "FF"):
        nB = outward_normal(B, bj)
        return dot(nB, sub(add(A[ai], x), edge(B, bj)[0]))   # FF：ai 为 A 该平行边的起点顶点
    nA = outward_normal(A, ai)
    return dot(nA, sub(B[bj], add(edge(A, ai)[0], x)))


def membership_convex(A: Poly, B: Poly, x: Point, tol: float = 0.0,
                      eb: EntranceBlock | None = None) -> int:
    """参考点相对 E 的位置：1 内部（A+x 与 B 内部相交）/ 0 边界（恰好接触）/ -1 外部（分离）。

    tol 为长度容差，抬到舍入下限 c·eps·C（C = B 与 A+x 的坐标量级；纪律 F）。不给 eb 时用同一个长度 tol 构造 E
    （convex_entrance_block 的 tol 也是长度）。旧版 convex_entrance_block 收的是弧度，这里却把长度 tol 原样传进去：
    毫米单位、tol = 1 mm 时 57° 以内的边都被并成 FF，三角压方块判"分离"（G6 第二轮 major）。"""
    if eb is None:
        eb = convex_entrance_block(A, B, (0.0, 0.0), tol)
    tol = max(tol, round_floor(max(coord_scale(B), coord_scale(A) + max(abs(x[0]), abs(x[1])))))
    g = max(facet_gap(A, B, lab, x) for lab in eb.facets)
    if g > tol:
        return -1
    if g < -tol:
        return 1
    return 0


def local_facets(A: Poly, B: Poly, tol: float = 0.0) -> set[tuple[str, int, int]]:
    """凸情形下用局部法锥规则得到的全部严格有效盖（不设窗口、不限边内）。

    定理检验（命题 4/5）：应与 convex_entrance_block 的 facet 标签集合（去 FF、去 `ambiguous_facets`）完全相同。
    """
    return _local_facets(A, B, tol, True)


def ambiguous_facets(A: Poly, B: Poly, tol: float = 0.0) -> set[tuple[str, int, int]]:
    """局部法锥规则判为"有效但不严格"的盖：对方边法向落在顶点法锥的边界带内（角容差 = 长度 tol 或舍入下限在
    所涉最短边上张的角）。这类盖在容差内说不清是不是 E 的 facet——全局构造可能把它并进 FF、也可能留作一条极短的
    精确 facet（一条几个 ulp 长的短边就是这样），标签比对时两边都不计。"""
    return _local_facets(A, B, tol, False)


def _local_facets(A: Poly, B: Poly, tol: float, strict: bool) -> set[tuple[str, int, int]]:
    out: set[tuple[str, int, int]] = set()
    for ia in range(len(A)):
        for jb in range(len(B)):
            c = ve_cover(A, ia, B, jb, tol)
            if c is not None and c.strict == strict:
                out.add(c.label())
    for ka in range(len(A)):
        for ib in range(len(B)):
            c = ev_cover(A, ka, B, ib, tol)
            if c is not None and c.strict == strict:
                out.add(c.label())
    return out
