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
局部单盖（E3）：默认对给定浮点坐标精确，法锥、VV 锥交/活跃、边内和距离窗全部用 Fraction 符号或平方比较。
`tol` / `seg_tol` 是调用方明确指定的长度域窗口，`cone_tol` 是 sin 单位的角域窗口；None 角窗由 tol/最短边长给出。
窗口只放宽有效集、不抬到舍入地板，strict 始终是精确严格性；浮点只构造法向、间隙和见证点。
门：tests/test_kernel2d_covers_e3.py（精确邻点支持 oracle、零窗口、短棱端点、凸包真极点）。
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from math import atan2, isfinite, lcm

from ..predicates import cross2_sign, dot2_sign
from ..construction import scalar_rational, sqrt_rational, vector_rational
from .exact import (convexity_violation, entrance_block_exact, entrance_membership_exact, ev_side_exact, membership_exact,
                    ve_side_exact)
from .geom import (Point, Poly, add, cross, dot, edge, neg, norm, outward_normal, sub, unit)


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
    window_active: bool = False  # VV 显式域窗口放宽的活跃性；绝不冒充精确 strict

    def label(self) -> tuple[str, int, int]:
        return (self.kind, self.a_index, self.b_index)


# ---------------------------------------------------------------- 法锥

@lru_cache(maxsize=4096)
def _fr(p):
    return (Fraction(p[0]), Fraction(p[1]))


def _vsub(p, q):
    return (p[0] - q[0], p[1] - q[1])


def _raw_cone(poly, i):
    """顶点的两条未归一化精确外法向；零边清晰报错。"""
    ring = tuple(poly[k % len(poly)] for k in (i - 1, i, i + 1))
    return _raw_cone_ring(ring)


@lru_cache(maxsize=4096)
def _raw_cone_ring(ring):
    p, a, q = map(_fr, ring)
    e, f = _vsub(a, p), _vsub(q, a)
    if e == (0, 0) or f == (0, 0):
        raise ValueError("zero-length edge at vertex: strip duplicates at the reader boundary")
    return (e[1], -e[0]), (f[1], -f[0])


def _cross_ge_window(u, v, w2):
    c = cross(u, v)
    return c >= 0 or c * c <= w2 * dot(u, u) * dot(v, v)


def _bisector_positive(lo, hi, v):
    """v 点乘两单位边界之和的精确符号；平方比较消去两处平方根。"""
    a, b = dot(lo, v), dot(hi, v)
    if a >= 0 and b >= 0:
        return a > 0 or b > 0
    if a <= 0 and b <= 0:
        return False
    cmp = a * a * dot(hi, hi) - b * b * dot(lo, lo)
    return cmp > 0 if a > 0 else cmp < 0


def _cone_accepts(lo, hi, v, w2):
    return (_cross_ge_window(lo, v, w2) and _cross_ge_window(v, hi, w2)
            and _bisector_positive(lo, hi, v))


def _cone_nonreflex(lo, hi, w2):
    t = cross(lo, hi)
    return t >= 0 and (t > 0 or dot(lo, hi) > 0) or (
        t < 0 and dot(lo, hi) > 0 and t * t <= w2 * dot(lo, lo) * dot(hi, hi))


def normal_cone(poly: Poly, i: int, tol: float = 0.0) -> tuple[Point, Point] | None:
    """顶点法锥的浮点构造；反射判定精确。tol 是显式 sin 角域窗口，只放宽、不抬舍入地板。
    小反射仅在转角绝对值 < π/2 且 sin 不超过窗口时接纳；零长邻边抛 ValueError。"""
    lo, hi = _raw_cone(poly, i)
    if not _cone_nonreflex(lo, hi, Fraction(max(tol, 0.0)) ** 2):
        return None
    return outward_normal(poly, (i - 1) % len(poly)), outward_normal(poly, i)


def cone_width(cone: tuple[Point, Point]) -> float:
    """两条给定法向的有符号转角（弧度）；精确叉积/点积共同缩放后才构造 atan2。
    不用于精确分支；非零角不可表达时报错。门：test_r8fix_initial_state 的 cone_width 门。"""
    lo, hi = _fr(cone[0]), _fr(cone[1])
    determinant, scalar = cross(lo, hi), dot(lo, hi)
    scale = max(abs(determinant), abs(scalar))
    if not scale:
        return 0.0
    # Homogeneous atan2 arguments are not geometric output coordinates:
    # a tiny horizontal component may round to zero while pi/2 is valid.
    # Retain the final nonzero-angle guard; no correctly-rounded transcendental
    # guarantee beyond platform atan2 is asserted.
    angle = atan2(scalar_rational(determinant / scale, allow_underflow=True),
                  scalar_rational(scalar / scale, allow_underflow=True))
    if determinant and angle == 0:
        raise ArithmeticError("nonzero cone width below binary64 output range")
    return angle


def in_cone(cone: tuple[Point, Point], v: Point, tol: float = 0.0) -> int:
    """对给定向量精确判：1 严格内部 / 0 边界或显式 sin 角窗 / -1 外部。"""
    lo, hi, v = _fr(cone[0]), _fr(cone[1]), _fr(v)
    if cross(lo, v) > 0 and cross(v, hi) > 0:
        return 1
    return 0 if _cone_accepts(lo, hi, v, Fraction(max(tol, 0.0)) ** 2) else -1


def _project(p: Point, a: Point, b: Point) -> tuple[float, Point]:
    """浮点见证构造；参数先精确相除，分支不消费舍入后的结果。"""
    P, A, B = _fr(p), _fr(a), _fr(b)
    e = _vsub(B, A)
    t = dot(_vsub(P, A), e) / dot(e, e)
    return scalar_rational(t), vector_rational((A[0] + t * e[0], A[1] + t * e[1]))


def _angle_window2(tol, cone_tol, vectors):
    """调用方的显式域窗口 sin²；无隐藏噪声项。tol/最短边长用精确平方比。"""
    if cone_tol is not None:
        return Fraction(max(cone_tol, 0.0)) ** 2
    return Fraction(max(tol, 0.0)) ** 2 / min(dot(v, v) for v in vectors)


def _ve_side(A, ia, B, jb, tol, cone_tol):
    lo, hi = _raw_cone(A, ia)
    b0, b1 = (_fr(p) for p in edge(B, jb))
    e = _vsub(b1, b0)
    if e == (0, 0):
        raise ValueError(f"zero-length edge {jb}")
    return _ve_side_directions(lo, hi, e, tol, cone_tol)


@lru_cache(maxsize=32768)
def _ve_side_directions(lo, hi, e, tol, cone_tol):
    """Exact directions with one common positive integer scale; same cache key.

    A shared denominator preserves the shortest of all three vector lengths.
    Length tol is lifted exactly by the same factor; cone_tol is dimensionless.
    Gate: test_perf_2d_directions::test_integer_ve_state_matches_fraction_reference.
    """
    den = lcm(*(c.denominator for vector in (lo, hi, e) for c in vector))
    lo, hi, e = (tuple(c.numerator * (den // c.denominator) for c in vector)
                 for vector in (lo, hi, e))
    v = (-e[1], e[0])
    turn, c1, c2 = cross(lo, hi), cross(lo, v), cross(v, hi)
    if turn >= 0 and (turn > 0 or dot(lo, hi) > 0) and c1 >= 0 and c2 >= 0 and (turn > 0 or dot(lo, v) > 0):
        return 1 if c1 > 0 and c2 > 0 else 0
    if tol <= 0 and (cone_tol is None or cone_tol <= 0):
        return -1
    if cone_tol is None:
        tol = Fraction(tol) * den
    w2 = _angle_window2(tol, cone_tol, (lo, hi, e))
    return 0 if w2 > 0 and _cone_nonreflex(lo, hi, w2) and _cone_accepts(lo, hi, v, w2) else -1


# ---------------------------------------------------------------- 单个盖

def ve_cover(A: Poly, ia: int, B: Poly, jb: int, tol: float = 0.0, cone_tol: float | None = None) -> Cover | None:
    """VE 的有效性/严格性默认精确。tol 是显式长度域窗，cone_tol 是显式 sin 角窗；仅扩大有效集。
    返回 normal/gap/param/point 是浮点构造，不作为枚举的判据。"""
    side = _ve_side(A, ia, B, jb, tol, cone_tol)
    if side < 0:
        return None
    a, (b0, b1) = A[ia], edge(B, jb)
    nB = outward_normal(B, jb)
    s, pt = _project(a, b0, b1)
    g, l2, _ = _line_data(a, b0, b1)
    gap = sqrt_rational(g*g/l2) * ((g > 0)-(g < 0))
    return Cover("VE", ia, jb, nB, gap, s, pt, side == 1, a, pt)


def ev_cover(A: Poly, ka: int, B: Poly, ib: int, tol: float = 0.0, cone_tol: float | None = None) -> Cover | None:
    """EV，交换两块后的 VE 判据；显式窗口语义同 ve_cover。"""
    side = _ve_side(B, ib, A, ka, tol, cone_tol)
    if side < 0:
        return None
    b, (a0, a1) = B[ib], edge(A, ka)
    nA = outward_normal(A, ka)
    s, pt = _project(b, a0, a1)
    g, l2, _ = _line_data(b, a0, a1)
    gap = sqrt_rational(g*g/l2) * ((g > 0)-(g < 0))
    return Cover("EV", ka, ib, neg(nA), gap, s, pt, side == 1, pt, b)



def _open_cone(lo, hi, v):
    return cross2_sign(lo, v) > 0 and cross2_sign(v, hi) > 0


def vv_cover(A: Poly, ia: int, B: Poly, jb: int, tol: float = 0.0, cone_tol: float | None = None) -> Cover | None:
    """VV 锥交有效性精确：两个非退化凸锥的相对内部相交。活跃性用严格精确符号；
    方向恰在锥边界时不标 strict（该处由 VE/EV 表示）；仅 a == b 才是重合。
    显式 tol/cone_tol 只放宽 window_active，strict 仍报告精确严格性。"""
    alo, ahi = _raw_cone(A, ia)
    blo, bhi = _raw_cone(B, jb)
    if cross2_sign(alo, ahi) <= 0 or cross2_sign(blo, bhi) <= 0:
        return None
    alo, ahi = neg(alo), neg(ahi)
    rays = (alo, ahi, blo, bhi)
    # 交锥若非空，其两条边界必取自这四条射线；真边界的正和严格落在交锥内。
    if not any(_open_cone(alo, ahi, add(u, v)) and _open_cone(blo, bhi, add(u, v))
               for k, u in enumerate(rays) for v in rays[k + 1:]):
        return None
    a, b = A[ia], B[jb]
    d = _vsub(_fr(a), _fr(b))
    if d == (0, 0):
        return Cover("VV", ia, jb, None, 0.0, None, a, True, a, b)
    active = _open_cone(alo, ahi, d) and _open_cone(blo, bhi, d)
    w2 = _angle_window2(tol, cone_tol, rays)
    expanded = w2 > 0 and _cone_accepts(alo, ahi, d, w2) and _cone_accepts(blo, bhi, d, w2)
    return Cover("VV", ia, jb, unit(d), norm(d), None, a, active, a, b, expanded)


# ---------------------------------------------------------------- 枚举

def _line_data(p, a, b):
    P, A, B = _fr(p), _fr(a), _fr(b)
    e, d = _vsub(B, A), _vsub(P, A)
    return -cross(e, d), dot(e, e), dot(e, d)


def _in_segment_exact(p, a, b, window):
    _, l2, along = _line_data(p, a, b)
    excess = max(-along, along - l2, 0)
    if excess == 0 or window == float("inf"):
        return True
    return isfinite(window) and excess * excess <= Fraction(max(window, 0.0)) ** 2 * l2


def _in_gap_window(c, A, B, window):
    return _feature_in_gap_window(c.kind, c.a_index, c.b_index, A, B, window)


def _feature_in_gap_window(kind, ai, bj, A, B, window):
    """Exact window check before potentially unrepresentable construction."""
    if window < 0:
        return False
    if window == float("inf"):
        return True
    if kind == "VV":
        d = _vsub(_fr(A[ai]), _fr(B[bj]))
        return dot(d, d) <= Fraction(window) ** 2
    P, E, i, j = (A, B, ai, bj) if kind == "VE" else (B, A, bj, ai)
    g, l2, _ = _line_data(P[i], *edge(E, j))
    return g * g <= Fraction(window) ** 2 * l2


def enumerate_covers(A: Poly, B: Poly, *, window: float, tol: float = 0.0,
                     require_in_segment: bool = True, cone_tol: float | None = None,
                     seg_tol: float | None = None) -> list[Cover]:
    """枚举有效盖；window 是 |gap| 的显式距离域窗，seg_tol 是边端外的显式长度域窗（默认 tol）。
    距离窗/边内/法锥全部精确平方比较，窗口不抬到舍入地板；VV 仅收活跃盖。"""
    st = tol if seg_tol is None else seg_tol
    out = []
    for ia in range(len(A)):
        for jb in range(len(B)):
            if not _feature_in_gap_window("VE", ia, jb, A, B, window):
                continue
            c = ve_cover(A, ia, B, jb, tol, cone_tol)
            if c is not None and (
                not require_in_segment or _in_segment_exact(A[ia], *edge(B, jb), st)):
                out.append(c)
    for ka in range(len(A)):
        for ib in range(len(B)):
            if not _feature_in_gap_window("EV", ka, ib, A, B, window):
                continue
            c = ev_cover(A, ka, B, ib, tol, cone_tol)
            if c is not None and (
                not require_in_segment or _in_segment_exact(B[ib], *edge(A, ka), st)):
                out.append(c)
    for ia in range(len(A)):
        for jb in range(len(B)):
            if not _feature_in_gap_window("VV", ia, jb, A, B, window):
                continue
            c = vv_cover(A, ia, B, jb, tol, cone_tol)
            if c is not None and (c.strict or c.window_active):
                out.append(c)
    return out


def _signed_gap_key(A, ia, B, jb):
    g, l2, _ = _line_data(A[ia], *edge(B, jb))
    return ((g > 0) - (g < 0), g * abs(g) / l2)


def first_entrance_for_vertex(A: Poly, ia: int, B: Poly, *, window: float, tol: float = 0.0,
                              cone_tol: float | None = None) -> Cover | None:
    """边内有效 VE 里取最大有符号间隙，所有比较精确；没有时退到最短活跃 VV。
    这是凸 B / 已侵入情形的局部选择器，不是一般凹块的沿路径首入（后者见 entrance.first_entrance）。
    window/tol/cone_tol 均是调用方显式域窗口，不抬噪声地板。"""
    ves, vvs = [], []
    for jb in range(len(B)):
        c = ve_cover(A, ia, B, jb, tol, cone_tol)
        if c is not None and _in_gap_window(c, A, B, window) and _in_segment_exact(A[ia], *edge(B, jb), tol):
            ves.append(c)
    if ves:
        return max(ves, key=lambda c: _signed_gap_key(A, ia, B, c.b_index))
    for jb in range(len(B)):
        c = vv_cover(A, ia, B, jb, tol, cone_tol)
        if c is not None and (c.strict or c.window_active) and _in_gap_window(c, A, B, window):
            vvs.append(c)
    return min(vvs, key=lambda c: sum(v*v for v in _vsub(_fr(A[ia]), _fr(B[c.b_index])))) if vvs else None


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
    verts = [vector_rational((v[0] + fa0[0], v[1] + fa0[1])) for v in ex.vertices]
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
    da, db = _vsub(_fr(a1), _fr(a0)), _vsub(_fr(b1), _fr(b0))
    n = outward_normal(B, bj) if dot(db, db) >= dot(da, da) else neg(outward_normal(A, ai))
    return n, sub(b0, a0)


def facet_gap(A: Poly, B: Poly, label: tuple[str, int, int], x: Point) -> float:
    """E 的一条 facet 在平移 x 下的有符号间隙（>0 参考点在该 facet 外侧）。**构造量**：facet 自己那条边的单位外法向点乘
    (x − facet 上一点)；成员与首入的**分支**判定不看它的符号（见 `membership_convex`、`entrance.first_entrance`）。"""
    kind, ai, bj = label
    X = _fr(x)
    if kind == "VE":
        b0, b1 = map(_fr, edge(B, bj))
        direction = sub(b1, b0)
        v = sub(add(_fr(A[ai]), X), b0)
    elif kind == "EV":
        a0, a1 = map(_fr, edge(A, ai))
        direction = sub(a1, a0)
        v = sub(_fr(B[bj]), add(a0, X))
    else:
        a0, a1 = map(_fr, edge(A, ai))
        b0, b1 = map(_fr, edge(B, bj))
        da, db = sub(a1, a0), sub(b1, b0)
        direction = db if dot(db, db) >= dot(da, da) else neg(da)
        v = sub(add(a0, X), b0)
    numerator = direction[1]*v[0]-direction[0]*v[1]
    return sqrt_rational(numerator*numerator/dot(direction, direction)) * ((numerator > 0)-(numerator < 0))


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
    """参考点相对 E 的位置：1 拓扑内部（含紧配接触内缝）/ 0 边界或显式报告带 / -1 外部（分离）。

    tol=0 时**对给定浮点坐标精确**：A、B 精确凸时用精确 E 的 facet 符号，否则（包括刚体运动把平直顶点舍入成微凹）
    用一般简单多边形的精确 E 成员判定（相触时核局部切锥并，不能把实体内缝当 ∂E）；x 的加法也在 Fraction 上做。tol（长度）只把有边界距离见证的非零答案报告为 0，
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
    s = entrance_membership_exact(A, B, x)
    if s == 0 or not tol > 0.0:
        return s
    if tol == float("inf"):
        return 0
    X, t = (Fraction(x[0]), Fraction(x[1])), Fraction(tol)
    for dx, dy in ((t, 0), (-t, 0), (0, t), (0, -t)):
        if entrance_membership_exact(A, B, (X[0] + dx, X[1] + dy)) != s:
            return 0
    return s

def local_facets(A: Poly, B: Poly, tol: float = 0.0) -> set[tuple[str, int, int]]:
    """凸情形下局部法锥规则（命题 5）给出的全部**严格**有效 VE / EV 标签，精确判（`exact.ve_side_exact` /
    `ev_side_exact`）。定理检验：与 `convex_entrance_block` 排除 FF 及精确边界支持分段后的严格 facet 集**精确相等**。
    平直边链的剩余非 FF 分段也可能只有非严格支持，不能仅按标签不是 FF 就算严格。`tol` 不参与。
    门：tests/test_kernel2d_exact.py 的独立全顶点投影支撑 oracle 与平直链门。"""
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
