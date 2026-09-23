"""G0 自证门：理论原生 oracle。

E(A,B) 的成员谓词可以暴力验证——随机采样参考点平移 x，直接做多边形相交测试，与盖系统给出的
判定比对。凸情形要求逐样本恒等（去掉 |gap| ≤ band 的边界带）；同时检验"局部法锥规则 = 全局
Minkowski facet 结构"（命题 4/5）。这条门不依赖任何 legacy。

凹情形没有局部成员谓词（E 非凸，facet 间隙取 max 或 min 都不成立），G0 改检验同一条定理
"∂E ⊆ ∪ 有效盖的平移线段"的两面：分离样本上的**距离完备性**（`g0_distance_completeness`，与三维
`g0_distance_completeness3` 同构），相交样本上的**出口完备性**（`g0_exit_completeness`：沿射线首次离开
E 的那个 ∂E 点必有有效盖作见证）。两者都不是凹块的成员谓词——成员判定要等入口块全局构造（M3）。
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


# ---------------------------------------------------------------- 相交样本：出口完备性（∂E 完备性的另一面）

def brute_ray_exit(A: Poly, B: Poly, u: Point) -> float:
    """A 与 B 内部相交时，A 沿方向 u 平移、**首次**离开 int E 的平移参数 t*（暴力 oracle；t 以 u 的长度计）。

    依据：z ∈ ∂E ⟹ A+z 与 B 仅边界接触。两条边在各自内部横截相交必致内部相交，所以接触处必有"一方的
    顶点落在另一方的边上"（共线重叠时，重叠段的端点也是顶点）。于是 ∂E ⊆ ∪{顶点 × 边 的候选线段}——
    取**全部**顶点-边对、两个方向、**不做任何法锥筛选**。射线 x + t·u 在相邻两次候选命中之间不碰 ∂E，
    成员状态恒定，取区间中点用 `polygons_overlap` 判一次即可。t ≥ t_sep = max_B(b·u) − min_A(a·u)
    时 A 在 u 方向整体越过 B、必不内部相交，t_sep 作最后一个命中。t* = 第一个"中点不相交"区间的左端。

    oracle 与被测对象的共用（纪律 A）：射线-线段求交只用内联算术；状态判定用 `polygons_overlap`（与盖枚举
    共用 geom 的 sub/dot/cross/norm，见 `g0_distance_completeness`）；不用法锥、转角、外法向、投影或窗口。
    输入须满足 polygons_overlap(A, B) == 1（调用方判），u 非零。
    """
    ux, uy = u
    hits: list[float] = []

    def hit(px: float, py: float, dx: float, dy: float, q0: Point, q1: Point) -> None:
        # 点 p 沿 (dx, dy) 走 t 落在闭线段 [q0, q1] 上：p + t·d = q0 + s·e，t > 0，s ∈ [0, 1]
        ex, ey = q1[0] - q0[0], q1[1] - q0[1]
        den = dx * ey - dy * ex
        if den == 0.0:                       # 射线与该边平行：共线段只在测度零的方向上出现
            return
        wx, wy = q0[0] - px, q0[1] - py
        t = (wx * ey - wy * ex) / den
        s = (wx * dy - wy * dx) / den
        if t > 0.0 and 0.0 <= s <= 1.0:
            hits.append(t)

    nA, nB = len(A), len(B)
    for px, py in A:                          # A 的顶点随 A 走 +u，撞 B 的边
        for j in range(nB):
            hit(px, py, ux, uy, B[j], B[(j + 1) % nB])
    for qx, qy in B:                          # 相对地，B 的顶点走 −u，撞 A 的边
        for k in range(nA):
            hit(qx, qy, -ux, -uy, A[k], A[(k + 1) % nA])
    t_sep = max(bx * ux + by * uy for bx, by in B) - min(ax * ux + ay * uy for ax, ay in A)
    lo = 0.0
    for t in sorted({h for h in hits if h < t_sep}) + [t_sep]:
        mid = 0.5 * (lo + t)
        if polygons_overlap(translate(A, (mid * ux, mid * uy)), B, 1e-12) != 1:
            return lo
        lo = t
    return t_sep


@dataclass(slots=True)
class ExitReport:
    """二维相交样本的出口完备性检验结果（`g0_exit_completeness`）。"""
    draws: int = 0
    separated: int = 0              # 暴力谓词判分离：归距离完备性检验，这里只计数
    touching: int = 0               # 暴力谓词判仅接触：只计数
    samples: int = 0                # 暴力谓词判相交、实际做了出口检验的样本数
    worst_witness: float = 0.0      # 出口位形上"有效盖最小见证距离"的最大值（理想为 0）
    # (x, u, t*, 出口处有效盖最小见证距离, 暴力给出的出口接触特征对 (类别, i, j, t))
    failures: list[tuple[Point, Point, float, float, tuple]] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.failures


def g0_exit_completeness(A: Poly, B: Poly, translations: list[Point], directions: list[Point], *,
                         tol: float = 1e-9, atol: float = 1e-9) -> ExitReport:
    """相交样本上的二维 G0：**出口完备性**——∂E 完备性在 E 内侧的检验。

    定理（与距离完备性同一条）：∂E ⊆ ∪{有效盖的平移线段}。z ∈ ∂E 处接触若是"顶点 a 对边 e 的内部"，
    a 为反射顶点则 A 在 a 附近必越过 e 所在直线、内部相交；a 凸但 −n_B(e) ∉ N_A(a) 同理——所以
    边界位形上的顶点-边接触都是法锥有效的盖；纯顶点-顶点接触的 z 是相邻有效线段的端点（投影参数 0/1）。
    检验：对每个暴力判相交的平移 x 与对应方向 u，z = x + t*·u（`brute_ray_exit`）处
        min{ |point_a − point_b| : c ∈ enumerate_covers(A+z, B, window=∞, tol) } ≤ atol·max(1, 坐标量级)，
    即法锥有效性筛选与边内筛选没有把出口处那段 ∂E 滤掉。

    **不是**成员谓词：它不判定 x 在不在 E 内（真值由 `polygons_overlap` 给），也不给出凹块的穿透深度；
    凹块的成员判定仍待入口块全局构造（M3）。与分离侧的距离完备性互补：后者检验 E 外一点的最近 ∂E 点，
    这里检验 E 内一点沿随机方向的首个 ∂E 点。
    零维 VV 盖在一般方向的出口上不起作用（出口几乎必在某段的相对内部），所以丢 VV 盖这里不会红——
    那颗牙在距离完备性那边（角对角实现的最短距离）。
    """
    if len(directions) != len(translations):
        raise ValueError(f"need one direction per translation: {len(directions)} != {len(translations)}")
    rep = ExitReport()
    inf = float("inf")
    for x, u in zip(translations, directions):
        rep.draws += 1
        At = translate(A, x)
        brute = polygons_overlap(At, B, 1e-12)
        if brute == -1:
            rep.separated += 1
            continue
        if brute == 0:
            rep.touching += 1
            continue
        t = brute_ray_exit(At, B, u)
        Az = translate(At, (t * u[0], t * u[1]))
        covs = enumerate_covers(Az, B, window=inf, tol=tol)
        got = min((math.hypot(c.point_a[0] - c.point_b[0], c.point_a[1] - c.point_b[1])
                   for c in covs if c.point_a is not None and c.point_b is not None), default=inf)
        scale = max(1.0, max(abs(v) for p in (*Az, *B) for v in p))
        rep.samples += 1
        rep.worst_witness = max(rep.worst_witness, got)
        if got > atol * scale:
            rep.failures.append((x, u, t, got, brute_polygon_distance(Az, B)[1]))
    return rep


def random_convex_polygon(rng: random.Random, n_points: int = 8, scale: float = 1.0) -> Poly:
    while True:
        pts = [(rng.uniform(-scale, scale), rng.uniform(-scale, scale)) for _ in range(n_points)]
        hull = convex_hull(pts)
        if len(hull) >= 3:
            return hull
