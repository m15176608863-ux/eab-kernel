"""二维首入（命题 7，M2 的二维版）：沿给定的相对平动方向，A 的参考点首次触及 ∂E 的点定接触点与法向；已侵入时取最短出口。

此前二维只有 `covers.first_entrance_for_vertex`——不接收运动方向的静态简化版（对单个顶点、B 凸或已侵入时取最大间隙），
`docs/canon_map.md` 记"凹块分离时选错边"。本模块按**运动**定义，与三维 `kernel3d.entrance3` 同构，并且是 M4（b-DDA 接缝，二维）
真正要消费的那条规则。

定义。参考点沿射线 x(t) = x0 + t·d（t ≥ 0；A 平移 x(t)，B 固定）运动，首入时刻 t* = min{t ≥ 0 : x(t) ∈ E(A, B)}。
  · **凸对**（A、B 都凸 ⇒ E 凸）：E 有显式的 H 表示（`convex_entrance_block` 的 facet），每条 facet 的间隙沿平移仿射：
    g_i(t) = g_i(x0) + t·(n_i·d)。射线进入凸集的时刻是全部"进入型"facet（n_i·d < 0）时刻的**最大者** t_in，离开时刻是
    "离开型"facet 时刻的最小者 t_out，t_in ≤ t_out 才触及。闭式，不经谓词；取到最大值的 facet 就是首入 facet。
  · **凹对**：没有全局 E（M3 之前），用局部盖（VE/EV）给完备候选、在各自时刻重验"投影落在边内"、精确谓词 `polygons_overlap_exact`
    裁决（t* 处相触或相交；t* 前全部原始接触事件及相邻事件中点分离，否则抛 RuntimeError——候选集漏了更早的首入，不静默）；与三维同一结构。
  · 集值点（首入点落在 E 的顶点上，两条 facet 精确同时被触及）：按枚举序取第一个作裁决，并列集如实报出（tied_labels）。
  · x0 已在 E 内（已侵入）：取**最短出口**——在程的 facet 型盖里取间隙最大者（侵入最浅）作接触法向与出口方向。
E2：凸选路、凸初态、半空间射线裁剪均用精确有理数；facet_gap/法向/接触点只作浮点输出，法向取 facet 自己的边。
E3：凹路径的平移、零间隙时刻、段内重验、相交与漏候选自检均用 Fraction；最短出口用精确平方距离排序。
精确并列集 tied_labels 与长度窗/舍入量级的 near_labels 分开；tol 不改 kind、时刻或获选标签。
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .covers import _facet_normal_own, enumerate_covers, facet_gap
from .exact import (convexity_violation, entrance_block_exact, membership_exact,
                    polygons_overlap_exact, ve_side_exact, ev_side_exact)
from .geom import Point, Poly, add, coord_scale, dot, edge, norm, round_floor, sub
from ..construction import sqrt_rational


@dataclass(slots=True)
class Entrance2:
    kind: str                       # "entrance" | "exit" | "none"
    t: float
    x: Point | None
    label: tuple | None             # ("VE", ia, jb) / ("EV", ka, ib) / ("FF", ka, jb)
    normal: Point | None            # B → A 的分离方向
    point_a: Point | None
    point_b: Point | None
    gap: float = 0.0
    tied_labels: tuple = ()
    n_candidates: int = 0
    near_labels: tuple = ()           # 可分辨性报告；不得并入精确 tied_labels
    t_exact: Fraction | None = None   # 射线时刻的精确证据；t/x 仍是浮点构造输出


def _facet_normal(A: Poly, B: Poly, label: tuple) -> Point:
    """facet 的外法向（B → A 的分离方向），与 `facet_gap` 同一口径（facet 自己那条边的法向；凸路径的 facet 由精确层给出）。"""
    return _facet_normal_own(A, B, label)[0]


def _facet_points(A: Poly, B: Poly, label: tuple, x: Point) -> tuple[Point, Point]:
    """首入位形下的接触点对（A 侧、B 侧）。VE：A 的顶点与它在 B 边上的投影；EV：B 的顶点与它在 A 边上的投影；FF：两条边的起点。"""
    kind, ai, bj = label
    A, B, x = [tuple(map(Fraction, p)) for p in A], [tuple(map(Fraction, p)) for p in B], tuple(map(Fraction, x))
    if kind == "VE":
        a = add(A[ai], x)
        b0, b1 = edge(B, bj)
        e = sub(b1, b0)
        parameter = min(max(dot(sub(a, b0), e) / dot(e, e), 0), 1)
        pa, pb = a, add(b0, (e[0]*parameter, e[1]*parameter))
    elif kind == "EV":
        b = B[bj]
        a0, a1 = edge(A, ai)
        a0, a1 = add(a0, x), add(a1, x)
        e = sub(a1, a0)
        parameter = min(max(dot(sub(b, a0), e) / dot(e, e), 0), 1)
        pa, pb = add(a0, (e[0]*parameter, e[1]*parameter)), b
    else:
        # Parallel face contact: report an actual common point of the closed
        # segments, not the unrelated starting vertices of opposite rings.
        a0, a1 = (add(p, x) for p in edge(A, ai))
        b0, b1 = edge(B, bj)
        e = sub(b1, b0)
        den = dot(e, e)
        low = max(0, min(dot(sub(a0, b0), e), dot(sub(a1, b0), e))/den)
        high = min(1, max(dot(sub(a0, b0), e), dot(sub(a1, b0), e))/den)
        if low > high:
            raise ArithmeticError("convex entrance face witness has no segment overlap")
        pa = pb = add(b0, (low*e[0], low*e[1]))
    return tuple(map(float, pa)), tuple(map(float, pb))


def _floor(A: Poly, B: Poly, x0: Point, d: Point) -> float:
    return round_floor(max(coord_scale(B), coord_scale(A) + max(abs(x0[0]), abs(x0[1])) + norm(d)))


def first_entrance(A: Poly, B: Poly, x0: Point, d: Point, *, tol: float = 0.0, t_max: float = float("inf")) -> Entrance2:
    """沿 x(t)=x0+t·d 的精确闭集首入；tol 只作 near_labels 的长度报告窗，不改答案。"""
    if d[0] == 0 and d[1] == 0:
        raise ValueError("direction must be nonzero")
    if tol < 0 or t_max < 0:
        raise ValueError("tol and t_max must be nonnegative")
    r = _floor(A, B, x0, d)
    if convexity_violation(A) is None and convexity_violation(B) is None:
        if membership_exact(A, B, x0) == 1:
            return shortest_exit(A, B, x0, tol=tol)
        return _first_entrance_convex(A, B, x0, d, tol, r, t_max)
    if polygons_overlap_exact(A, B, x0) == 1:
        return shortest_exit(A, B, x0, tol=tol)
    return _first_entrance_concave(A, B, x0, d, tol, r, t_max)


def _first_entrance_convex(A: Poly, B: Poly, x0: Point, d: Point, ctol: float, r: float, t_max: float) -> Entrance2:
    """精确有理数半空间射线裁剪；facet_gap 只在最后输出构造量，不参与去留/时刻分支。
    tol/r 仅为 near_labels 可分辨性报告窗，不能把错过 E 或超过 t_max 的射线变成命中。
    门：test_convex_ray_decisions_do_not_use_constructed_facet_gaps / test_convex_ray_resolves_tiny_slopes_and_misses。
    """
    eb = entrance_block_exact(A, B)
    X, D = tuple(map(Fraction, x0)), tuple(map(Fraction, d))
    enter = []
    active = []
    t_out = None

    def none():
        return Entrance2("none", 0.0, None, None, None, None, None, 0.0, (), len(enter))

    for f in eb.facets:
        ex, ey = f.direction
        # h >= 0 是 E 的内半空间；不用单位法向或浮点差分求斜率。
        h = ex * (X[1] - f.start[1]) - ey * (X[0] - f.start[0])
        slope = ex * D[1] - ey * D[0]
        if h == 0:
            active.append(f)
        if slope > 0:
            enter.append((-h / slope, slope, f))
        elif slope < 0:
            bound = -h / slope
            t_out = bound if t_out is None else min(t_out, bound)
        elif h < 0:
            return none()
    t_in = max([Fraction(0)] + [t for t, _, _ in enter])
    if (t_out is not None and t_in > t_out) or (t_max != float("inf") and t_in > Fraction(t_max)):
        return none()
    best = max(enter, key=lambda q: q[0]) if enter else None
    if t_in == 0 and active:
        # 已恰好接触：定义 min{t>=0:x(t)∈E}=0，包括沿边或背离运动。
        fbest = next((f for t, _, f in enter if t == 0), active[0])
    elif best is not None and best[0] == t_in:
        fbest = best[2]
    else:
        return none()
    band2 = Fraction(ctol + r) ** 2
    near = []
    tied = []
    for t, slope, f in enter:
        ex, ey = f.direction
        if ((t - t_in) * slope) ** 2 <= band2 * (ex * ex + ey * ey):
            near.append(f.label)
    # 恰在角点/沿边的闭集首触也有活动侧：不只报告进入型 facet。
    for f in eb.facets:
        ex, ey = f.direction
        h = ex * (X[1] + t_in * D[1] - f.start[1]) - ey * (X[0] + t_in * D[0] - f.start[0])
        if h == 0 and f.label not in tied:
            tied.append(f.label)
            if f.label not in near:
                near.append(f.label)
    if fbest.label not in tied:
        tied.insert(0, fbest.label)
    tied.sort(key=lambda lab: 0 if lab == fbest.label else 1)
    lab = fbest.label
    exact_x = (X[0] + D[0] * t_in, X[1] + D[1] * t_in)
    x = tuple(map(float, exact_x))
    pa, pb = _facet_points(A, B, lab, exact_x)
    return Entrance2("entrance", float(t_in), x, lab, _facet_normal(A, B, lab), pa, pb,
                     facet_gap(A, B, lab, exact_x), tuple(tied), len(enter), tuple(near), t_in)


def _frpoint(p):
    return (Fraction(p[0]), Fraction(p[1]))


def _at(X, D, t):
    return (X[0] + t * D[0], X[1] + t * D[1])


def _feature_data(A, B, label, X, D=(Fraction(0), Fraction(0))):
    """原坐标有理数：有符号 gap 分子、沿 d 斜率、投影分子、边长平方及投影斜率。
    不构造单位法向，不把 A+x 舍入成新的输入。"""
    kind, ai, bj = label
    if kind == "VE":
        p, q = _frpoint(B[bj]), _frpoint(B[(bj + 1) % len(B)])
        a = _frpoint(A[ai])
        v = (a[0] + X[0] - p[0], a[1] + X[1] - p[1])
        velocity = D
    else:
        p, q = _frpoint(A[ai]), _frpoint(A[(ai + 1) % len(A)])
        b = _frpoint(B[bj])
        v = (b[0] - p[0] - X[0], b[1] - p[1] - X[1])
        velocity = (-D[0], -D[1])
    ex, ey = q[0] - p[0], q[1] - p[1]
    length2 = ex * ex + ey * ey
    if length2 == 0:
        raise ValueError("zero-length edge in entrance candidate")
    return (ey * v[0] - ex * v[1], ey * velocity[0] - ex * velocity[1],
            ex * v[0] + ey * v[1], length2, ex * velocity[0] + ey * velocity[1])


def _feature_times(data):
    """零间隙为仿射式：横穿时精确求根；共线平移时保留进入/离开闭线段的端点事件。"""
    g, slope, projection, length2, projection_slope = data
    if slope != 0:
        return (-g / slope,)
    if g != 0:
        return ()
    times = [Fraction(0)] if 0 <= projection <= length2 else []
    if projection_slope != 0:
        times += [-projection / projection_slope, (length2 - projection) / projection_slope]
    return tuple(times)


def _all_event_times(A, B, X, D, bound):
    """未经法锥/候选筛选的全顶点-边事件；仅用于漏候选自校验。
    相交闭集的首次时刻必有顶点-边接触，含平行滑入的端点。它不是独立 oracle。"""
    out = {Fraction(0)}
    for kind in ("VE", "EV"):
        for ai in range(len(A)):
            for bj in range(len(B)):
                out.update(t for t in _feature_times(_feature_data(A, B, (kind, ai, bj), X, D))
                           if t >= 0 and (bound is None or t <= bound))
    return sorted(out)


def _contact_report(A, B, label, X):
    """接触点先在 Fraction 上构造再各舍入一次；浮点法向/gap 均不参与选择。"""
    kind, ai, bj = label
    g, _, projection, length2, _ = _feature_data(A, B, label, X)
    parameter = projection / length2
    if kind == "VE":
        pa = _at(_frpoint(A[ai]), X, Fraction(1))
        b0, b1 = _frpoint(B[bj]), _frpoint(B[(bj + 1) % len(B)])
        pb = (b0[0] + parameter * (b1[0] - b0[0]), b0[1] + parameter * (b1[1] - b0[1]))
    else:
        a0, a1 = _frpoint(A[ai]), _frpoint(A[(ai + 1) % len(A)])
        pa = (a0[0] + X[0] + parameter * (a1[0] - a0[0]), a0[1] + X[1] + parameter * (a1[1] - a0[1]))
        pb = _frpoint(B[bj])
    gap = sqrt_rational(g * g / length2) * ((g > 0) - (g < 0))
    return _facet_normal(A, B, label), tuple(map(float, pa)), tuple(map(float, pb)), gap


def _candidate_labels(A, B):
    # 枚举时不先浮点平移；局部有效性平移不变。tol=0 是数学入口，不是 legacy 域窗口。
    for c in enumerate_covers(A, B, window=float("inf"), require_in_segment=False):
        if c.kind in ("VE", "EV"):
            side = ve_side_exact(A, c.a_index, B, c.b_index) if c.kind == "VE" else ev_side_exact(A, c.a_index, B, c.b_index)
            if side >= 0:
                yield c.label()


def _first_entrance_concave(A: Poly, B: Poly, x0: Point, d: Point, ctol: float, r: float, t_max: float) -> Entrance2:
    """精确候选时刻/段内/相交裁决；t* 前全事件 + 相邻事件中点的精确自检。
    不能只退一个浮点分辨步：它可能跨过很窄的更早接触区间。"""
    X, D = _frpoint(x0), _frpoint(d)
    bound = None if t_max == float("inf") else Fraction(t_max)
    raw = []
    for idx, label in enumerate(_candidate_labels(A, B)):
        for t in _feature_times(_feature_data(A, B, label, X, D)):
            if t >= 0 and (bound is None or t <= bound):
                raw.append((t, idx, label))
    raw.sort(key=lambda q: (q[0], q[1]))

    def state(t):
        return polygons_overlap_exact(A, B, _at(X, D, t))

    for t, idx, label in raw:
        x = _at(X, D, t)
        g, _, projection, length2, _ = _feature_data(A, B, label, x)
        if g != 0 or not 0 <= projection <= length2:
            continue
        if state(t) < 0:
            continue
        prior = [tp for tp in _all_event_times(A, B, X, D, t) if tp < t]
        probes = prior + ([(prior[-1] + t) / 2] if prior else [])
        for tp in probes:
            if state(tp) >= 0:
                raise RuntimeError(f"first_entrance: bodies already touch at t = {tp!r} < candidate {t!r} ({label}); "
                                   "the cover candidate set missed an earlier entrance")
        tied, near = [], []
        band2 = Fraction(ctol + r) ** 2
        for t2, _, label2 in raw:
            g2, _, p2, l2, _ = _feature_data(A, B, label2, x)
            if 0 <= p2 <= l2:
                if t2 == t and g2 == 0 and label2 not in tied:
                    tied.append(label2)
                if g2 * g2 <= band2 * l2 and label2 not in near:
                    near.append(label2)
        tied.sort(key=lambda lab: 0 if lab == label else 1)
        normal, pa, pb, gap = _contact_report(A, B, label, x)
        return Entrance2("entrance", float(t), tuple(map(float, x)), label, normal, pa, pb,
                         gap, tuple(tied), len(raw), tuple(near), t)
    # 无候选也检查全部原始几何事件，不靠有限粗探漏掉短暂碰撞或无限射线上的触及。
    for tp in _all_event_times(A, B, X, D, bound):
        if state(tp) >= 0:
            raise RuntimeError(f"first_entrance: no in-segment cover candidate, yet the bodies touch at t = {tp!r}; "
                               "the candidate set missed an earlier entrance")
    return Entrance2("none", 0.0, None, None, None, None, None, 0.0, (), len(raw))


def shortest_exit(A: Poly, B: Poly, x0: Point, *, tol: float = 0.0) -> Entrance2:
    """已侵入时在程 VE/EV 的最大非正间隙；有理数平方距离选最浅盖，精确同距才并列。
    这是局部 facet 选择，不声称一般凹对该单次平移能令所有接触同时脱开。tol 只报告 near_labels。"""
    X = _frpoint(x0)
    candidates = []
    for label in _candidate_labels(A, B):
        g, _, projection, length2, _ = _feature_data(A, B, label, X)
        if g <= 0 and 0 <= projection <= length2:
            candidates.append((g * g / length2, label))
    if not candidates:
        raise RuntimeError("shortest_exit: penetrating configuration with no in-segment facet cover")
    best_distance, label = min(candidates, key=lambda q: q[0])
    tied = tuple(lab for distance, lab in candidates if distance == best_distance)
    # sqrt(distance)-sqrt(best) <= band：平方化后的精确有理数比较，不让报告反馈选择。
    band2 = Fraction(tol + _floor(A, B, x0, (0., 0.))) ** 2
    near = tuple(lab for distance, lab in candidates
                 if distance - best_distance - band2 <= 0 or
                 (distance - best_distance - band2) ** 2 <= 4 * band2 * best_distance)
    normal, pa, pb, gap = _contact_report(A, B, label, X)
    return Entrance2("exit", 0.0, x0, label, normal, pa, pb, gap, tied, len(candidates), near, Fraction(0))


def first_entrance_brute(A: Poly, B: Poly, x0: Point, d: Point, *, t_max: float, steps: int = 400,
                         tol: float = 0.0) -> float | None:
    """精确谓词扫描/二分佐证（不是独立 oracle：与生产共用 polygons_overlap_exact）。
    [0,t_max] 上所有平移在 Fraction 做；扫描步长仍须小于穿越区间，孤立切触可能漏采。
    二分到上下界舍入为同一/相邻 float，只控制输出分辨率，不以容差改变相交答案。tol 保留兼容、无判定作用。"""
    if steps <= 0 or t_max < 0 or t_max == float("inf"):
        raise ValueError("steps must be positive and t_max finite and nonnegative")
    X, D = _frpoint(x0), _frpoint(d)
    bound = Fraction(t_max)

    def state(t):
        return polygons_overlap_exact(A, B, _at(X, D, t))
    if state(Fraction(0)) >= 0:
        return 0.0
    prev, hit = Fraction(0), None
    for k in range(1, steps + 1):
        t = bound * k / steps
        if state(t) >= 0:
            hit = t
            break
        prev = t
    if hit is None:
        return None
    lo, up = prev, hit
    from math import nextafter, inf
    while float(lo) != float(up) and nextafter(float(lo), inf) < float(up):
        mid = (lo + up) / 2
        if state(mid) >= 0:
            up = mid
        else:
            lo = mid
    return float(up)
