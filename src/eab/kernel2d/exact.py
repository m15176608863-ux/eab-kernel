"""二维凸入口块的**精确**构造与成员判定（对给定浮点坐标精确；"精确谓词、浮点只做构造"）。

为什么要有这一层（G6 第五轮，2026-10-10）：二维核的判定此前全部是"浮点 + 噪声带"——每个判据都要论证"被测量 + 它的噪声"，
五轮独立重审每轮都从"两把尺"或"漏了某个方向的噪声"里挖出新的静默错判（第五轮 critical：Minkowski 扫描按宽窗合并了一条
1e-14 的倒角边与一条 60° 的边，facet_gap 却拿链里长边的法向，x = (1.1, 0.5) 处真实压入 0.15 被判"分离"）。
浮点输入本身就是精确有理数，所以对**这组浮点数据**，几何判定都有唯一正确的答案；本模块用 `Fraction` 精确算：

  · 凸性：每个顶点的 orient2d ≥ 0（CCW；平直顶点允许）——精确；
  · E = B ⊕ (−A) 的 facet：两组边向量按**精确**极角归并（同半平面 + 叉积符号），只有**精确平行同向**的边才合并成 FF；
    E 的顶点 b_j − a_i 精确（Fraction 差，不舍入）；
  · 成员：参考平移 x 对每条 facet 的精确叉积符号——1 内部相交 / 0 恰好相触 / −1 分离。

刚体运动后坐标舍入会改变"恰好相触 / 恰好平行"这类边界态的答案——那是数据本身变了，不是判定错了；可分辨性
（离边界多远才算稳定）是调用方另外的问题，不在这里用容差改答案。本模块当前的角色：二维凸成员判定的**精确 oracle**
与 `covers.membership_convex` 的精确核验（见 `tests/test_kernel2d_exact.py`）。
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .geom import Point, Poly

FPoint = tuple[Fraction, Fraction]


def _fr(p: Point) -> FPoint:
    return (Fraction(p[0]), Fraction(p[1]))


def _sub(a: FPoint, b: FPoint) -> FPoint:
    return (a[0] - b[0], a[1] - b[1])


def _cross(a: FPoint, b: FPoint) -> Fraction:
    return a[0] * b[1] - a[1] * b[0]


def _dot(a: FPoint, b: FPoint) -> Fraction:
    return a[0] * b[0] + a[1] * b[1]


def _sgn(v: Fraction) -> int:
    return (v > 0) - (v < 0)


def signed_area2(P: list[FPoint]) -> Fraction:
    o = P[0]
    return sum((_cross(_sub(P[i], o), _sub(P[(i + 1) % len(P)], o)) for i in range(len(P))), Fraction(0))


def convexity_violation(P: Poly) -> str | None:
    """P 作为 CCW 凸多边形的精确违例（None = 精确凸；平直顶点允许）：零长边 / 非 CCW / 反射顶点 / 折回（转角恰 π）/
    绕圈不止一次（五角星：每个顶点都左转、总转角 4π——边方向的极角序下降不止一次）。"""
    F = [_fr(p) for p in P]
    n = len(F)
    if n < 3:
        return "fewer than 3 vertices"
    E = [_sub(F[(i + 1) % n], F[i]) for i in range(n)]
    for i, e in enumerate(E):
        if e == (0, 0):
            return f"zero-length edge {i}"
    if signed_area2(F) <= 0:
        return "not counter-clockwise"
    for i in range(n):
        c = _cross(E[i - 1], E[i])
        if c < 0:
            return f"reflex vertex {i}"
        if c == 0 and _dot(E[i - 1], E[i]) < 0:
            return f"folds back on itself at vertex {i}"
    descents = sum(1 for i in range(n) if _angle_less(E[(i + 1) % n], E[i]))
    if descents != 1:
        return f"winds {descents} times (total turning is not 2π)"
    return None


def is_convex_exact(P: Poly) -> bool:
    """CCW 多边形精确凸（平直顶点允许，零长边、折回、绕圈不允许）。"""
    return convexity_violation(P) is None


def _half(v: FPoint) -> int:
    """极角所在的半平面：[0, π) 记 0，[π, 2π) 记 1。"""
    return 0 if (v[1] > 0 or (v[1] == 0 and v[0] > 0)) else 1


def _angle_less(u: FPoint, v: FPoint) -> bool:
    hu, hv = _half(u), _half(v)
    if hu != hv:
        return hu < hv
    return _cross(u, v) > 0


@dataclass(frozen=True)
class ExactFacet:
    label: tuple            # ("VE", ia, jb) / ("EV", ka, ib) / ("FF", ka, jb)
    start: FPoint           # facet 起点（E 的顶点，未加 a0）
    direction: FPoint       # facet 方向（CCW 走向；FF 是两条边向量之和）


@dataclass(frozen=True)
class ExactEntranceBlock:
    vertices: list[FPoint]  # E = B ⊕ (−A) 的顶点（CCW，未加 a0），精确；含平直顶点（相邻 facet 共线）
    facets: list[ExactFacet]
    pairs: list[tuple[int, int]]   # 每个顶点 = b_j − a_i 的 (i, j)


def _lowest(F: list[FPoint]) -> int:
    return min(range(len(F)), key=lambda i: (F[i][1], F[i][0]))


def entrance_block_exact(A: Poly, B: Poly) -> ExactEntranceBlock:
    """凸 A、B（CCW）的 E = B ⊕ (−A)，精确。A、B 须**精确**凸（`is_convex_exact`），否则 ValueError——
    凹块（含刚体运动后舍入成微凹的平直顶点）不能走凸路径。"""
    for name, P in (("A", A), ("B", B)):
        why = convexity_violation(P)
        if why is not None:
            raise ValueError(f"input polygon {name} is not exactly convex: {why} "
                             f"(a flat vertex rounded by a rigid motion may be reflex; use the concave path)")
    FA = [_fr(p) for p in A]
    FB = [_fr(p) for p in B]
    na, nb = len(FA), len(FB)
    # −A 的顶点 −a_i 仍是 CCW；它的第 k 条边（−a_k → −a_{k+1}）的向量是 −(a_{k+1} − a_k)，对应 A 的边 k。
    # 两组边各自从最低点出发、按极角递增（凸多边形的边序本身就是极角序，只需对齐起点）。
    ib0 = _lowest(FB)
    negA = [(-p[0], -p[1]) for p in FA]
    ia0 = _lowest(negA)
    eb = [(j % nb, _sub(FB[(j + 1) % nb], FB[j % nb])) for j in range(ib0, ib0 + nb)]
    ea = [(k % na, _sub(negA[(k + 1) % na], negA[k % na])) for k in range(ia0, ia0 + na)]
    # 平直顶点（零转角）让相邻两条边同向：按精确极角归并时它们各自成段，下面的合并只合并 B 边与 −A 边的精确平行对；
    # 同一多边形内的同向相邻边保留为两条 facet（共线），成员判定不受影响。
    v = _sub(FB[ib0], FA[(ia0) % na])                  # b_{ib0} + (−a_{ia0})
    cur_b = ib0                                         # 当前 B 的顶点（EV facet 的支撑顶点）
    cur_a = ia0                                         # 当前 A 的顶点（VE facet 的支撑顶点）
    verts: list[FPoint] = []
    facets: list[ExactFacet] = []
    pairs: list[tuple[int, int]] = []
    i = j = 0
    while i < nb or j < na:
        verts.append(v)
        pairs.append((cur_a, cur_b))
        if j >= na or (i < nb and _angle_less(eb[i][1], ea[j][1])):
            jb, d = eb[i]
            facets.append(ExactFacet(("VE", cur_a, jb), v, d))
            cur_b = (jb + 1) % nb
            i += 1
        elif i >= nb or _angle_less(ea[j][1], eb[i][1]):
            ka, d = ea[j]
            facets.append(ExactFacet(("EV", ka, cur_b), v, d))
            cur_a = (ka + 1) % na
            j += 1
        else:                                           # 精确平行同向：FF
            jb, db = eb[i]
            ka, da = ea[j]
            d = (db[0] + da[0], db[1] + da[1])
            facets.append(ExactFacet(("FF", ka, jb), v, d))
            cur_b, cur_a = (jb + 1) % nb, (ka + 1) % na
            i += 1
            j += 1
        v = (v[0] + facets[-1].direction[0], v[1] + facets[-1].direction[1])
    assert v == verts[0], "Minkowski walk did not close (inputs not convex?)"
    return ExactEntranceBlock(verts, facets, pairs)


def strict_vertices(eb: ExactEntranceBlock) -> list[int]:
    """E 的严格凸顶点（相邻两条 facet 不共线）的下标。"""
    n = len(eb.facets)
    return [k for k in range(n) if _cross(eb.facets[k - 1].direction, eb.facets[k].direction) != 0]


def hull_exact(points: list[Point]) -> list[FPoint]:
    """点集的精确凸包顶点（CCW，单调链，**共线点一律不作顶点**）。输入是浮点，比较与转向全部在 Fraction 上做。"""
    return hull_exact_fr([_fr(p) for p in points])


def hull_exact_fr(points: list[FPoint]) -> list[FPoint]:
    """同 `hull_exact`，输入已是 Fraction 点（如精确差点 b − a）。"""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def half(seq):
        out: list[FPoint] = []
        for p in seq:
            while len(out) >= 2 and _cross(_sub(out[-1], out[-2]), _sub(p, out[-2])) <= 0:
                out.pop()
            out.append(p)
        return out
    lo, hi = half(pts), half(reversed(pts))
    return lo[:-1] + hi[:-1]


def membership_exact(A: Poly, B: Poly, x: Point, eb: ExactEntranceBlock | None = None) -> int:
    """参考平移 x（A 平移 x、B 固定）：1 内部相交 / 0 恰好相触 / −1 分离——对给定浮点坐标精确。"""
    eb = eb or entrance_block_exact(A, B)
    X = _fr(x)
    worst = 1
    for f in eb.facets:
        s = _sgn(_cross(f.direction, _sub(X, f.start)))
        if s < 0:
            return -1
        worst = min(worst, s)
    return worst


def convex_overlap_exact(A: Poly, B: Poly, x: Point = (0.0, 0.0)) -> int:
    """A 平移 x 后与 B（都凸、CCW）的精确相交状态（分离轴定理，全部用 Fraction，平移也精确做）：1 内部相交 / 0 恰好相触 /
    −1 分离。与 `membership_exact` 零共用（不经 Minkowski 和），当它的独立 oracle。"""
    X = _fr(x)
    FA, FB = [(a[0] + X[0], a[1] + X[1]) for a in (_fr(p) for p in A)], [_fr(p) for p in B]
    touch = False
    for P, Q in ((FA, FB), (FB, FA)):
        n = len(P)
        for k in range(n):
            e = _sub(P[(k + 1) % n], P[k])
            if e == (0, 0):
                continue
            # 外法向（CCW 的右法向）方向上：P 的最大投影 = 这条边的投影；Q 的最小投影
            nrm = (e[1], -e[0])
            pmax = _dot(nrm, P[k])
            qmin = min(_dot(nrm, q) for q in Q)
            if qmin > pmax:
                return -1
            if qmin == pmax:
                touch = True
    return 0 if touch else 1


# ---------------------------------------------------------------- 法锥判据（命题 5），精确

def _edge_vec(P: list[FPoint], k: int) -> FPoint:
    n = len(P)
    return _sub(P[(k + 1) % n], P[k % n])


def vertex_side_exact(P: Poly, i: int, d_edge: FPoint) -> int:
    """方向 d = −n(e)（e 为对方的一条边、CCW 外法向 n = 右法向）相对 P 顶点 i 的法锥：1 相对内部 / 0 边界 / −1 外（含反射顶点）。

    右法向保持叉积：cross(perp u, perp v) = cross(u, v)，所以全部判据化成边向量的叉积 / 点积符号（坐标的二次多项式），
    在 Fraction 上精确：
      顶点凸        ⟺ cross(e_{i−1}, e_i) ≥ 0（= 0 为平直顶点，法锥退化为单射线）；
      d 在锥内      ⟺ c1 = cross(e, e_{i−1}) ≥ 0 且 c2 = cross(e_i, e) ≥ 0（锥角 < π 时两个半平面之交恰是锥）；
                      平直顶点（锥退化为单射线 n）另须 d 与 n 同向：dot(e, e_{i−1}) < 0；
      相对内部      ⟺ c1 > 0 且 c2 > 0。
    （不能拿 e_{i−1} + e_i 当角平分线判同侧：两边长不等时和向量偏向长边，锥内方向会被判到锥外。）"""
    F = [_fr(p) for p in P]
    e_prev, e_next = _edge_vec(F, i - 1), _edge_vec(F, i)
    turn = _cross(e_prev, e_next)
    if turn < 0 or (turn == 0 and _dot(e_prev, e_next) <= 0):
        return -1
    c1 = _cross(d_edge, e_prev)
    c2 = _cross(e_next, d_edge)
    if c1 < 0 or c2 < 0:
        return -1
    if turn == 0 and _dot(d_edge, e_prev) >= 0:
        return -1
    return 1 if (c1 > 0 and c2 > 0) else 0


def ve_side_exact(A: Poly, ia: int, B: Poly, jb: int) -> int:
    """VE(a_ia, e_jb) 的法锥有效性：−n_B(jb) 相对 N_A(a_ia)。"""
    return vertex_side_exact(A, ia, _edge_vec([_fr(p) for p in B], jb))


def ev_side_exact(A: Poly, ka: int, B: Poly, ib: int) -> int:
    """EV(e_ka, b_ib) 的法锥有效性：−n_A(ka) 相对 N_B(b_ib)。"""
    return vertex_side_exact(B, ib, _edge_vec([_fr(p) for p in A], ka))


# ---------------------------------------------------------------- 一般简单多边形的精确相交（凹块的精确谓词）

def polygons_overlap_exact(A: Poly, B: Poly, x: Point = (0.0, 0.0)) -> int:
    """A 平移 x 后与 B（任意简单多边形、任意朝向）的精确相交状态：1 内部相交 / 0 只有边界接触 / −1 分离。

    两份精确耳切（`geom.triangulate` 用精确 `orient2d`）逐对三角形做精确分离轴检验（平移在 Fraction 上做）：
    内部相交 ⟺ 某对三角形内部相交（多边形内部 = 三角形内部 ∪ 对角线的相对内部，两内部之交是开集，非空即有正面积）；
    否则，若某对三角形相触，相触点必在两个多边形的**边界**上（落在 A 内部的点若在 B 里，附近就有 B 的内部点，前一条已判 1）。"""
    from .geom import triangulate
    X = _fr(x)
    ta = [[A[i], A[j], A[k]] for i, j, k in triangulate(A)]
    tb = [[B[i], B[j], B[k]] for i, j, k in triangulate(B)]
    touch = False
    for T in ta:
        for U in tb:
            s = _tri_overlap_exact(T, U, X)
            if s == 1:
                return 1
            if s == 0:
                touch = True
    return 0 if touch else -1


def _tri_overlap_exact(T, U, X: FPoint) -> int:
    FT = [(_fr(p)[0] + X[0], _fr(p)[1] + X[1]) for p in T]
    FU = [_fr(p) for p in U]
    if signed_area2(FT) < 0:
        FT.reverse()
    if signed_area2(FU) < 0:
        FU.reverse()
    touch = False
    for P, Q in ((FT, FU), (FU, FT)):
        for k in range(3):
            e = _sub(P[(k + 1) % 3], P[k])
            nrm = (e[1], -e[0])
            pmax = _dot(nrm, P[k])
            qmin = min(_dot(nrm, q) for q in Q)
            if qmin > pmax:
                return -1
            if qmin == pmax:
                touch = True
    return 0 if touch else 1
