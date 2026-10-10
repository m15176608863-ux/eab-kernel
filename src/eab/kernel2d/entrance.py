"""二维首入（命题 7，M2 的二维版）：沿给定的相对平动方向，A 的参考点首次触及 ∂E 的点定接触点与法向；已侵入时取最短出口。

此前二维只有 `covers.first_entrance_for_vertex`——不接收运动方向的静态简化版（对单个顶点、B 凸或已侵入时取最大间隙），
`docs/canon_map.md` 记"凹块分离时选错边"。本模块按**运动**定义，与三维 `kernel3d.entrance3` 同构，并且是 M4（b-DDA 接缝，二维）
真正要消费的那条规则。

定义。参考点沿射线 x(t) = x0 + t·d（t ≥ 0；A 平移 x(t)，B 固定）运动，首入时刻 t* = min{t ≥ 0 : x(t) ∈ E(A, B)}。
  · **凸对**（A、B 都凸 ⇒ E 凸）：E 有显式的 H 表示（`convex_entrance_block` 的 facet），每条 facet 的间隙沿平移仿射：
    g_i(t) = g_i(x0) + t·(n_i·d)。射线进入凸集的时刻是全部"进入型"facet（n_i·d < 0）时刻的**最大者** t_in，离开时刻是
    "离开型"facet 时刻的最小者 t_out，t_in ≤ t_out 才触及。闭式，不经谓词；取到最大值的 facet 就是首入 facet。
  · **凹对**：没有全局 E（M3 之前），用局部盖（VE/EV）给完备候选、在各自时刻重验"投影落在边内"、精确谓词 `polygons_overlap`
    裁决（t* 处相触或相交；t* 前一个分辨步处分离，否则抛 RuntimeError——候选集漏了更早的首入，不静默）；与三维同一结构。
  · 集值点（首入点落在 E 的顶点上，两条 facet 在分辨率内同时被触及）：按枚举序取第一个作裁决，并列集如实报出（tied_labels）。
  · x0 已在 E 内（已侵入）：取**最短出口**——在程的 facet 型盖里取间隙最大者（侵入最浅）作接触法向与出口方向。
容差（纪律 F）：谓词与并列按长度地板 c·eps·C 加调用方 tol；facet 法向沿用 `facet_gap` 的口径（噪声内共线链里最长边的法向）。
"""

from __future__ import annotations

from dataclasses import dataclass

from .covers import (Cover, _facet_normal_own, convex_entrance_block, enumerate_covers, ev_cover, facet_gap, ve_cover)
from .exact import convexity_violation
from .geom import (Point, Poly, add, coord_scale, dot, edge, is_convex, neg, norm, outward_normal, polygons_overlap,
                   round_floor, sub, translate)


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


def _facet_normal(A: Poly, B: Poly, label: tuple) -> Point:
    """facet 的外法向（B → A 的分离方向），与 `facet_gap` 同一口径（facet 自己那条边的法向；凸路径的 facet 由精确层给出）。"""
    return _facet_normal_own(A, B, label)[0]


def _facet_points(A: Poly, B: Poly, label: tuple, x: Point) -> tuple[Point, Point]:
    """首入位形下的接触点对（A 侧、B 侧）。VE：A 的顶点与它在 B 边上的投影；EV：B 的顶点与它在 A 边上的投影；FF：两条边的起点。"""
    kind, ai, bj = label
    if kind == "VE":
        a = add(A[ai], x)
        b0, b1 = edge(B, bj)
        e = sub(b1, b0)
        s = dot(sub(a, b0), e) / dot(e, e)
        s = min(max(s, 0.0), 1.0)
        return a, add(b0, (e[0] * s, e[1] * s))
    if kind == "EV":
        b = B[bj]
        a0, a1 = edge(A, ai)
        a0, a1 = add(a0, x), add(a1, x)
        e = sub(a1, a0)
        s = dot(sub(b, a0), e) / dot(e, e)
        s = min(max(s, 0.0), 1.0)
        return add(a0, (e[0] * s, e[1] * s)), b
    return add(edge(A, ai)[0], x), edge(B, bj)[0]


def _floor(A: Poly, B: Poly, x0: Point, d: Point) -> float:
    return round_floor(max(coord_scale(B), coord_scale(A) + max(abs(x0[0]), abs(x0[1])) + norm(d)))


def first_entrance(A: Poly, B: Poly, x0: Point, d: Point, *, tol: float = 0.0, t_max: float = float("inf")) -> Entrance2:
    """沿 x(t) = x0 + t·d 的首入（见模块文档）。A、B 均 CCW；tol 为长度容差（并列与谓词的带，抬到舍入地板）。"""
    dn = norm(d)
    if dn == 0.0:
        raise ValueError("direction must be nonzero")
    r = _floor(A, B, x0, d)
    ctol = max(tol, r)
    if polygons_overlap(translate(A, x0), B, ctol) == 1:
        return shortest_exit(A, B, x0, tol=tol)
    if convexity_violation(A) is None and convexity_violation(B) is None:      # 精确凸才走凸路径（E2）
        return _first_entrance_convex(A, B, x0, d, ctol, r, t_max)
    return _first_entrance_concave(A, B, x0, d, ctol, r, t_max)


def _first_entrance_convex(A: Poly, B: Poly, x0: Point, d: Point, ctol: float, r: float, t_max: float) -> Entrance2:
    eb = convex_entrance_block(A, B, (0.0, 0.0), ctol)
    enter: list[tuple[float, float, tuple]] = []        # (t_i, −n·d, label)
    t_out = float("inf")
    for lab in eb.facets:
        g0 = facet_gap(A, B, lab, x0)
        g1 = facet_gap(A, B, lab, add(x0, d))
        slope = g1 - g0                                   # = n·d
        if slope < -1e-12 * norm(d):
            enter.append((g0 / (-slope), -slope, lab))
        elif slope > 1e-12 * norm(d):
            t_out = min(t_out, -g0 / slope)
        elif g0 > ctol:                                   # 与射线平行、且参考点在它外侧的 facet：射线永远进不了 E
            return Entrance2("none", 0.0, None, None, None, None, None, 0.0, (), 0)
    if not enter:
        return Entrance2("none", 0.0, None, None, None, None, None, 0.0, (), len(enter))
    t_in = max(t for t, _, _ in enter)
    if t_in < 0.0:                                        # 全部进入型 facet 都在身后而谓词说没相交：参考点已在 E 内？不该到这里
        t_in = 0.0
    if t_in > t_out + ctol / max(norm(d), 1e-300) or t_in > t_max + r / norm(d):
        return Entrance2("none", 0.0, None, None, None, None, None, 0.0, (), len(enter))
    # 并列：法向间隙在 ctol 以内的进入型 facet（枚举序，取到最大值的排第一）
    tied = [lab for t, nd, lab in enter if abs(t - t_in) * nd <= ctol + r]
    best = max(enter, key=lambda q: (q[0], 0))
    lab = best[2]
    tied.sort(key=lambda q: 0 if q == lab else 1)
    x = add(x0, (d[0] * t_in, d[1] * t_in))
    pa, pb = _facet_points(A, B, lab, x)
    return Entrance2("entrance", t_in, x, lab, _facet_normal(A, B, lab), pa, pb, facet_gap(A, B, lab, x), tuple(tied), len(enter))


def _cover_at(A: Poly, B: Poly, label: tuple, x: Point, tol: float) -> Cover | None:
    kind, ai, bj = label
    At = translate(A, x)
    if kind == "VE":
        return ve_cover(At, ai, B, bj, tol)
    if kind == "EV":
        return ev_cover(At, ai, B, bj, tol)
    return None


def _in_segment(c: Cover, A: Poly, B: Poly, x: Point, r: float) -> bool:
    """投影参数落在边内（带 = 舍入地板 / 边长 + 杠杆项，与 enumerate_covers 同口径）。"""
    if c.param is None:
        return True
    if c.kind == "VE":
        b0, b1 = edge(B, c.b_index)
        le = norm(sub(b1, b0))
        lever = norm(sub(add(A[c.a_index], x), b0))
    else:
        a0, a1 = edge(A, c.a_index)
        le = norm(sub(a1, a0))
        lever = norm(sub(B[c.b_index], add(a0, x)))
    band = (r + r * lever / le) / le
    return -band <= c.param <= 1.0 + band


def _first_entrance_concave(A: Poly, B: Poly, x0: Point, d: Point, ctol: float, r: float, t_max: float) -> Entrance2:
    At = translate(A, x0)
    raw: list[tuple[float, Cover, float, int]] = []
    for idx, c in enumerate(enumerate_covers(At, B, window=float("inf"), tol=ctol, require_in_segment=False)):
        if c.kind == "VV" or c.normal is None:
            continue
        nd = dot(c.normal, d)
        if nd >= -1e-12 * norm(d) or c.gap < -r:
            continue
        t = max(0.0, c.gap / (-nd))
        if t <= t_max + r / (-nd):
            raw.append((t, c, nd, idx))
    raw.sort(key=lambda q: (q[0], q[3]))
    for t, c, nd, idx in raw:
        x = add(x0, (d[0] * t, d[1] * t))
        cc = _cover_at(A, B, c.label(), x, ctol)
        if cc is None or not _in_segment(cc, A, B, x, r):
            continue
        if polygons_overlap(translate(A, x), B, ctol) < 0:
            continue
        step = 2.0 * (ctol + r) / (-nd)
        if t - step > 0.0 and polygons_overlap(translate(A, add(x0, (d[0] * (t - step), d[1] * (t - step)))), B, ctol) >= 0:
            raise RuntimeError(f"first_entrance: bodies already touch at t = {t - step!r} < candidate {t!r} ({c.label()}); "
                               f"the cover candidate set missed an earlier entrance")
        tied: list[tuple] = []
        for t2, c2, nd2, _ in raw:
            if abs(t2 - t) * (-nd2) <= ctol + r:
                c2x = _cover_at(A, B, c2.label(), x, ctol)
                if c2x is not None and _in_segment(c2x, A, B, x, r):
                    tied.append(c2.label())
        tied.sort(key=lambda q: 0 if q == cc.label() else 1)
        return Entrance2("entrance", t, x, cc.label(), cc.normal, cc.point_a, cc.point_b, cc.gap, tuple(tied), len(raw))
    ts = sorted({q[0] for q in raw})
    probes = ts + [0.5 * (a + b) for a, b in zip(ts, ts[1:])]
    if t_max < float("inf"):                            # 候选为空（或全部出程）时至少沿射线粗探几处，不许静默答"不触及"
        probes += [t_max * f for f in (1.0, 0.5, 0.25, 0.125)]
    for tp in probes:
        if polygons_overlap(translate(A, add(x0, (d[0] * tp, d[1] * tp))), B, ctol) >= 0:
            raise RuntimeError(f"first_entrance: no in-segment cover candidate, yet the bodies touch at t = {tp!r}; "
                               f"the candidate set missed an earlier entrance")
    return Entrance2("none", 0.0, None, None, None, None, None, 0.0, (), len(raw))


def shortest_exit(A: Poly, B: Poly, x0: Point, *, tol: float = 0.0) -> Entrance2:
    """已侵入位形的最短出口：在程（投影落在边内）的 VE/EV 盖里取间隙最大者（侵入最浅）。并列按枚举序裁决、如实报出。"""
    r = _floor(A, B, x0, (0.0, 0.0))
    ctol = max(tol, r)
    At = translate(A, x0)
    cands = [c for c in enumerate_covers(At, B, window=float("inf"), tol=ctol, require_in_segment=True)
             if c.kind != "VV" and c.normal is not None and c.gap <= ctol + r]
    if not cands:
        raise RuntimeError("shortest_exit: penetrating configuration with no in-segment facet cover")
    best = max(cands, key=lambda c: c.gap)
    tied = [c.label() for c in cands if best.gap - c.gap <= ctol + r]
    tied.sort(key=lambda q: 0 if q == best.label() else 1)
    return Entrance2("exit", 0.0, x0, best.label(), best.normal, best.point_a, best.point_b, best.gap, tuple(tied), len(cands))


def first_entrance_brute(A: Poly, B: Poly, x0: Point, d: Point, *, t_max: float, steps: int = 400,
                         tol: float = 0.0) -> float | None:
    """纪律 A 的 oracle：只用谓词。把 [0, t_max] 均分扫描找到第一个 polygons_overlap ≥ 0 的步，再二分到舍入级。
    扫描步长必须小于 A 沿 d 穿过 B 的最短时间（由测试负责）。x0 已相触/相交时返回 0；扫描内不触及返回 None。"""
    r = _floor(A, B, x0, d)
    ctol = max(tol, r)

    def state(t: float) -> int:
        return polygons_overlap(translate(A, add(x0, (d[0] * t, d[1] * t))), B, ctol)
    if state(0.0) >= 0:
        return 0.0
    prev, hit = 0.0, None
    for k in range(1, steps + 1):
        t = t_max * k / steps
        if state(t) >= 0:
            hit = t
            break
        prev = t
    if hit is None:
        return None
    lo, up = prev, hit
    ztol = max(1e-13 * (abs(t_max) + 1.0), 8.0 * 2.220446049250313e-16 * t_max)
    while up - lo > ztol:
        mid = 0.5 * (lo + up)
        if state(mid) >= 0:
            up = mid
        else:
            lo = mid
    return up
