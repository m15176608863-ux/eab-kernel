"""G0 自证门：理论原生 oracle。

E(A,B) 的成员谓词可以暴力验证——随机采样参考点平移 x，直接做多边形相交测试，与盖系统给出的
判定比对。凸情形要求逐样本恒等（去掉 |gap| ≤ band 的边界带）；同时检验"局部法锥规则 = 全局
Minkowski facet 结构"（命题 4/5）。这条门不依赖任何 legacy。

凹情形没有局部成员谓词（E 非凸，facet 间隙取 max 或 min 都不成立），G0 改检验**距离完备性**
（`g0_distance_completeness`，与三维 `g0_distance_completeness3` 同构）。
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from .covers import convex_entrance_block, enumerate_covers, local_facets, membership_convex
from .geom import Point, Poly, convex_hull, polygons_overlap, translate


@dataclass(slots=True)
class G0Report:
    samples: int = 0
    band_skipped: int = 0
    mismatches: list[tuple[Point, int, int]] = field(default_factory=list)   # (x, brute, cover)
    facet_local: int = 0
    facet_global: int = 0
    facet_symmetric_diff: list[tuple[str, int, int]] = field(default_factory=list)
    hull_vertex_mismatch: int = 0      # 第三票：E 顶点集 vs conv{b−a} 顶点集（不经法向/法锥/合并）

    @property
    def passed(self) -> bool:
        return not self.mismatches and not self.facet_symmetric_diff and self.hull_vertex_mismatch == 0


def _bbox(P: Poly) -> tuple[float, float, float, float]:
    xs = [p[0] for p in P]
    ys = [p[1] for p in P]
    return min(xs), max(xs), min(ys), max(ys)


def sample_translations(A: Poly, B: Poly, n: int, rng: random.Random, margin: float = 0.25) -> list[Point]:
    """在 (B 的包围盒 − A 的包围盒) 外扩 margin 的范围里均匀采样平移。"""
    ax0, ax1, ay0, ay1 = _bbox(A)
    bx0, bx1, by0, by1 = _bbox(B)
    lo_x, hi_x = bx0 - ax1, bx1 - ax0
    lo_y, hi_y = by0 - ay1, by1 - ay0
    wx, wy = hi_x - lo_x, hi_y - lo_y
    return [(rng.uniform(lo_x - margin * wx, hi_x + margin * wx),
             rng.uniform(lo_y - margin * wy, hi_y + margin * wy)) for _ in range(n)]


def g0_convex(A: Poly, B: Poly, *, samples: int = 2000, seed: int = 0, tol: float = 1e-12,
              band: float = 1e-9) -> G0Report:
    """A、B 凸 CCW。逐样本：暴力相交谓词 vs E 成员谓词；再比对局部/全局 facet 集合。"""
    rng = random.Random(seed)
    rep = G0Report()
    eb = convex_entrance_block(A, B, (0.0, 0.0), tol)
    glob = {lab for lab in eb.facets if lab[0] != "FF"}
    loc = local_facets(A, B, tol)
    rep.facet_local, rep.facet_global = len(loc), len(glob)
    rep.facet_symmetric_diff = sorted(loc ^ glob)
    # 第三票（审查 r7）：标签集相等对"outward_normal 整体反号"是盲的；E 的顶点集必须等于
    # 差点集 {b − a} 的凸包顶点集——这条检验不经过法向、法锥或合并规则。
    hull = convex_hull([(b[0] - a[0], b[1] - a[1]) for a in A for b in B])
    ev = {(round(v[0], 9), round(v[1], 9)) for v in eb.vertices}
    hv = {(round(v[0], 9), round(v[1], 9)) for v in hull}
    rep.hull_vertex_mismatch = len(ev ^ hv)
    for x in sample_translations(A, B, samples, rng):
        cov = membership_convex(A, B, x, band, eb)
        if cov == 0:
            rep.band_skipped += 1
            continue
        brute = polygons_overlap(translate(A, x), B, tol)
        if brute == 0:
            rep.band_skipped += 1
            continue
        rep.samples += 1
        if brute != cov:
            rep.mismatches.append((x, brute, cov))
    return rep


# ---------------------------------------------------------------- 凹块（也适用于凸块）：距离完备性

def _point_segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float
                            ) -> tuple[float, float]:
    """点到**闭线段**的欧氏距离与夹紧后的参数 t∈[0,1]。只用内联浮点算术（不调 geom/covers 的任何原语）。"""
    ex, ey = bx - ax, by - ay
    l2 = ex * ex + ey * ey
    t = 0.0 if l2 == 0.0 else ((px - ax) * ex + (py - ay) * ey) / l2
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return math.hypot(px - (ax + t * ex), py - (ay + t * ey)), t


def brute_polygon_distance(A: Poly, B: Poly) -> tuple[float, tuple[str, int, int, float]]:
    """两个**不相交**简单多边形之间的距离（暴力 oracle），附实现它的特征对。

    依据：不相交紧集的距离在边界上实现；边界是有限条闭线段之并；两条不相交闭线段的距离必在
    其中一条的端点处实现。故 d(A,B) = min{ 点-线段距离 : A 顶点 × B 边，B 顶点 × A 边 }。
    **零法锥筛选、零投影参数容差、零方向约定**——只用顶点坐标与内联算术，与盖枚举
    （法锥、转角、外法向、投影）不共用任何几何原语（纪律 A）。

    返回 (距离, (类别, i, j, t))：类别 "A-vertex/B-edge" 时 i 为 A 顶点、j 为 B 边；反之亦然；
    t 为夹紧后的线段参数（0 或 1 表示实现于端点，即顶点-顶点）。相交输入的返回值无意义，调用方先用
    `polygons_overlap` 判分离。
    """
    best = math.inf
    arg: tuple[str, int, int, float] = ("", -1, -1, 0.0)
    for P, Q, tag in ((A, B, "A-vertex/B-edge"), (B, A, "B-vertex/A-edge")):
        m = len(Q)
        for i, (px, py) in enumerate(P):
            for j in range(m):
                (ax, ay), (bx, by) = Q[j], Q[(j + 1) % m]
                d, t = _point_segment_distance(px, py, ax, ay, bx, by)
                if d < best:
                    best, arg = d, (tag, i, j, t)
    return best, arg


@dataclass(slots=True)
class DistanceReport:
    """二维凹块 G0：'法锥有效性筛选不丢最近特征对' 的完备性检验结果（与三维 DistanceReport3 同构）。"""
    draws: int = 0
    overlapping: int = 0            # 暴力谓词判相交：距离命题不适用，只计数
    touching: int = 0               # 暴力谓词判仅边界接触：同上
    samples: int = 0                # 暴力谓词判分离、实际检验了完备性的样本数
    worst_abs_error: float = 0.0
    # (x, 盖见证距离, 暴力距离, 暴力实现特征对)
    failures: list[tuple[Point, float, float, tuple]] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.failures


def g0_distance_completeness(A: Poly, B: Poly, translations: list[Point], *, tol: float = 1e-9,
                             atol: float = 1e-9) -> DistanceReport:
    """凹块（也适用于凸块）二维 G0 的正确形式：**距离完备性**。

    真值：`polygons_overlap`（暴力谓词）判分离；分离时的真距离由 `brute_polygon_distance` 给出。
    被检验的命题：A+x 与 B 分离时，
        d(A+x, B) = min{ |point_a − point_b| : c ∈ enumerate_covers(A+x, B, window=∞, tol) }，
    即法锥有效性筛选与边内筛选不会把实现最短距离的那一对特征滤掉。见证点都在各自多边形上
    （边内容差 tol 除外），所以见证距离恒 ≥ 真距离；相等 ⟺ 完备。

    **不要**用 sign(min gap) 当凹块的成员谓词：VE 盖的 gap 是顶点到对方边**所在直线**的有符号距离，
    分离的两块之间也常有顶点落在对方某条边直线的内侧（细臂 L 块 + 凹槽内悬浮方块：gap −0.16，
    实际分离），三维上同一条规则 2026-09-18 已被证伪，二维 2026-09-21 审查复现。
    凹块的成员判定需要入口块的全局构造（M3）；在那之前，相交样本只计数、不检验。

    oracle 与被测对象的共用（纪律 A）：`polygons_overlap` 与盖枚举共用 geom 的向量算术
    （sub/dot/cross/norm）与 `point_in_polygon`/`segments_properly_cross`（后两者盖枚举不用）；
    不共用法锥、转角、外法向、投影、窗口或边内判据。`brute_polygon_distance` 只用内联算术。
    """
    rep = DistanceReport()
    inf = float("inf")
    for x in translations:
        rep.draws += 1
        At = translate(A, x)
        brute = polygons_overlap(At, B, 1e-12)
        if brute == 1:
            rep.overlapping += 1
            continue
        if brute == 0:
            rep.touching += 1
            continue
        truth, arg = brute_polygon_distance(At, B)
        covs = enumerate_covers(At, B, window=inf, tol=tol)
        got = min((math.hypot(c.point_a[0] - c.point_b[0], c.point_a[1] - c.point_b[1])
                   for c in covs if c.point_a is not None and c.point_b is not None), default=inf)
        rep.samples += 1
        err = abs(got - truth)
        rep.worst_abs_error = max(rep.worst_abs_error, err)
        if err > atol * max(1.0, truth):
            rep.failures.append((x, got, truth, arg))
    return rep


def random_convex_polygon(rng: random.Random, n_points: int = 8, scale: float = 1.0) -> Poly:
    while True:
        pts = [(rng.uniform(-scale, scale), rng.uniform(-scale, scale)) for _ in range(n_points)]
        hull = convex_hull(pts)
        if len(hull) >= 3:
            return hull
