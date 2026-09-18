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
"""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, pi

from .geom import (Point, Poly, add, cross, dot, edge, neg, norm, outward_normal, reflect, sub, unit,
                   vertex_turn)


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

    def label(self) -> tuple[str, int, int]:
        return (self.kind, self.a_index, self.b_index)


# ---------------------------------------------------------------- 法锥

def normal_cone(poly: Poly, i: int, tol: float = 0.0) -> tuple[Point, Point] | None:
    """顶点 i 的法锥（CCW 极角序）：(n_prev, n_next)；反射（凹）顶点返回 None。

    tol 以 sin(转角) 计：turn < -tol 判为反射；平直顶点（turn≈0）保留——其法锥退化为单射线，
    对应 legacy 里"直边中间的顶点贴在对方边上"这类接触（tol=0 时仍保留 turn==0）。
    """
    n = len(poly)
    e_prev = unit(sub(poly[i % n], poly[(i - 1) % n]))
    e_next = unit(sub(poly[(i + 1) % n], poly[i % n]))
    if cross(e_prev, e_next) < -tol:
        return None
    return outward_normal(poly, (i - 1) % n), outward_normal(poly, i)


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

def ve_cover(A: Poly, ia: int, B: Poly, jb: int, tol: float = 0.0, cone_tol: float | None = None) -> Cover | None:
    """A 的顶点 ia 对 B 的边 jb。无效（法锥外/反射顶点）返回 None。

    cone_tol：法锥判据的角容差（sin 单位；None = 用 tol）。legacy 兼容模式给 sin(h1°)。
    """
    ct = tol if cone_tol is None else cone_tol
    cone = normal_cone(A, ia, ct)
    if cone is None:
        return None
    nB = outward_normal(B, jb)
    side = in_cone(cone, neg(nB), ct)
    if side < 0:
        return None
    a = A[ia]
    b0, b1 = edge(B, jb)
    s, pt = _project(a, b0, b1)
    return Cover("VE", ia, jb, nB, dot(nB, sub(a, b0)), s, pt, side == 1)


def ev_cover(A: Poly, ka: int, B: Poly, ib: int, tol: float = 0.0, cone_tol: float | None = None) -> Cover | None:
    """B 的顶点 ib 对 A 的边 ka。"""
    ct = tol if cone_tol is None else cone_tol
    cone = normal_cone(B, ib, ct)
    if cone is None:
        return None
    nA = outward_normal(A, ka)
    side = in_cone(cone, neg(nA), ct)
    if side < 0:
        return None
    b = B[ib]
    a0, a1 = edge(A, ka)
    s, pt = _project(b, a0, a1)
    return Cover("EV", ka, ib, neg(nA), dot(nA, sub(b, a0)), s, pt, side == 1)


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
    """
    ct = tol if cone_tol is None else cone_tol
    ca = normal_cone(A, ia, ct)
    cb = normal_cone(B, jb, ct)
    if ca is None or cb is None:
        return None
    s1 = _span(neg(ca[0]), neg(ca[1]))
    s2 = _span(cb[0], cb[1])
    best: tuple[float, float] | None = None
    for k in (-1, 0, 1):
        lo = max(s1[0], s2[0] + 2 * pi * k)
        hi = min(s1[1], s2[1] + 2 * pi * k)
        if best is None or hi - lo > best[1] - best[0]:
            best = (lo, hi)
    assert best is not None
    if best[1] - best[0] <= tol:
        return None
    a, b = A[ia], B[jb]
    d = sub(a, b)
    dist = norm(d)
    if dist == 0.0:
        return Cover("VV", ia, jb, None, 0.0, None, a, True)
    u = unit(d)
    au = _ang(u)
    active = any(best[0] - tol <= au + 2 * pi * k <= best[1] + tol for k in (-1, 0, 1))
    return Cover("VV", ia, jb, u, dist, None, a, active)


# ---------------------------------------------------------------- 枚举

def enumerate_covers(A: Poly, B: Poly, *, window: float, tol: float = 0.0,
                     require_in_segment: bool = True, cone_tol: float | None = None,
                     seg_tol: float | None = None) -> list[Cover]:
    """当前位形下所有有效且落在距离窗口内的盖。A、B 均为 CCW。

    window：|gap| ≤ window 才收（对应 legacy 的 d0 搜索距离，两侧对称，调用方再筛）。
    require_in_segment：VE/EV 的投影参数须在 [0,1]（容差 seg_tol/边长，缺省 tol）。VV 只收活跃的。
    cone_tol：法锥角容差（sin 单位）；严格数学用 0，legacy 兼容用 sin(h1°)。
    """
    st = tol if seg_tol is None else seg_tol
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
    """
    best: Cover | None = None
    for jb in range(len(B)):
        c = ve_cover(A, ia, B, jb, tol, cone_tol)
        if c is None or abs(c.gap) > window:
            continue
        le = _edge_len(B, jb)
        if not (-tol / le <= c.param <= 1.0 + tol / le):
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


def convex_entrance_block(A: Poly, B: Poly, a0: Point = (0.0, 0.0), tol: float = 0.0) -> EntranceBlock:
    """A、B 凸且 CCW。E = a0 + (B ⊕ (−A))，边按极角合并，每条边带盖标签。

    平行边（极角相等，容差 tol）合并成一条 FF 边。
    """
    P = B
    Q = reflect(A)                # Q[k] = −A[k]；Q 的边 k = −(A 的边 k)
    n, m = len(P), len(Q)
    iP, iQ = _start_index(P), _start_index(Q)
    angP = [_edge_angle(P, (iP + k) % n) for k in range(n)]
    angQ = [_edge_angle(Q, (iQ + k) % m) for k in range(m)]
    # 从最低点出发的凸 CCW 多边形，边角在 [0, 2π) 内非降；数值容错保证单调
    for arr in (angP, angQ):
        for k in range(1, len(arr)):
            if arr[k] < arr[k - 1] - 1e-12:
                arr[k] += 2 * pi
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
            if abs(d) <= tol:
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
    """参考点相对 E 的位置：1 内部（A+x 与 B 内部相交）/ 0 边界（恰好接触）/ -1 外部（分离）。"""
    if eb is None:
        eb = convex_entrance_block(A, B, (0.0, 0.0), tol)
    g = max(facet_gap(A, B, lab, x) for lab in eb.facets)
    if g > tol:
        return -1
    if g < -tol:
        return 1
    return 0


def local_facets(A: Poly, B: Poly, tol: float = 0.0) -> set[tuple[str, int, int]]:
    """凸情形下用局部法锥规则得到的全部严格有效盖（不设窗口、不限边内）。

    定理检验（命题 4/5）：应与 convex_entrance_block 的 facet 标签集合（去 FF）完全相同。
    """
    out: set[tuple[str, int, int]] = set()
    for ia in range(len(A)):
        for jb in range(len(B)):
            c = ve_cover(A, ia, B, jb, tol)
            if c is not None and c.strict:
                out.add(c.label())
    for ka in range(len(A)):
        for ib in range(len(B)):
            c = ev_cover(A, ka, B, ib, tol)
            if c is not None and c.strict:
                out.add(c.label())
    return out
