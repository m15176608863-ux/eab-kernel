"""G0 自证门：理论原生 oracle。

E(A,B) 的成员谓词可以暴力验证——随机采样参考点平移 x，直接做多边形相交测试，与盖系统给出的
判定比对。凸情形要求逐样本恒等（去掉 |gap| ≤ band 的边界带）；同时检验"局部法锥规则 = 全局
Minkowski facet 结构"（命题 4/5）。这条门不依赖任何 legacy。

凹情形没有局部成员谓词（E 非凸，facet 间隙取 max 或 min 都不成立），G0 改检验同一条定理
"∂E ⊆ ∪ 有效盖的平移线段"的两面：分离样本上的**距离完备性**（`g0_distance_completeness`，与三维
`g0_distance_completeness3` 同构），相交样本上的**出口完备性**（`g0_exit_completeness`：沿射线首次离开
E 的那个 ∂E 点必有有效盖作见证）。两者都不是凹块的成员谓词——成员判定要等入口块全局构造（M3）。

容差（纪律 F，M0.2）：本模块内部不再有绝对阈值。暴力谓词的接触带取 1e-12·L，判据阈值取 atol·L（或 atol·真值）
加舍入下限 c·eps·C——L 为两块的特征长度（包围盒对角线的较大者），C 为坐标量级。所以同一位形经刚体运动、
搬到工程坐标、换单位后，样本分类（分离/接触/相交）与判定不变。门：tests/test_invariance_2d.py。
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from .covers import ambiguous_facets, convex_entrance_block, enumerate_covers, local_facets, membership_convex
from .geom import (EPS, ROUND_C, Point, Poly, convex_hull, coord_scale, cross, norm, polygons_overlap, round_floor, sub,
                   translate)


@dataclass(slots=True)
class G0Report:
    samples: int = 0
    band_skipped: int = 0
    mismatches: list[tuple[Point, int, int]] = field(default_factory=list)   # (x, brute, cover)
    facet_local: int = 0
    facet_global: int = 0
    facet_symmetric_diff: list[tuple[str, int, int]] = field(default_factory=list)
    facet_ambiguous: int = 0           # 局部规则判"容差内说不清"的盖，两边都不计（covers.ambiguous_facets）
    hull_vertex_mismatch: int = 0      # 第三票：E 顶点集 vs conv{b−a} 顶点集（不经法向/法锥/合并）
    hull_vertex_ambiguous: int = 0     # 第三票里折点离弦 ≤ 凸包弦距容差、两边口径下都说不清的顶点数（两边都不计）

    @property
    def passed(self) -> bool:
        return not self.mismatches and not self.facet_symmetric_diff and self.hull_vertex_mismatch == 0


def _bbox(P: Poly) -> tuple[float, float, float, float]:
    xs = [p[0] for p in P]
    ys = [p[1] for p in P]
    return min(xs), max(xs), min(ys), max(ys)


def char_length(*polys: Poly) -> float:
    """特征长度 L：各多边形包围盒对角线的最大者。随单位缩放、对平移不变（纪律 F 的相对容差以它为尺）。"""
    out = 0.0
    for P in polys:
        x0, x1, y0, y1 = _bbox(P)
        out = max(out, math.hypot(x1 - x0, y1 - y0))
    return out


def sample_translations(A: Poly, B: Poly, n: int, rng: random.Random, margin: float = 0.25) -> list[Point]:
    """在 (B 的包围盒 − A 的包围盒) 外扩 margin 的范围里均匀采样平移。"""
    ax0, ax1, ay0, ay1 = _bbox(A)
    bx0, bx1, by0, by1 = _bbox(B)
    lo_x, hi_x = bx0 - ax1, bx1 - ax0
    lo_y, hi_y = by0 - ay1, by1 - ay0
    wx, wy = hi_x - lo_x, hi_y - lo_y
    return [(rng.uniform(lo_x - margin * wx, hi_x + margin * wx),
             rng.uniform(lo_y - margin * wy, hi_y + margin * wy)) for _ in range(n)]


def g0_convex(A: Poly, B: Poly, *, samples: int = 2000, seed: int = 0, tol: float | None = None,
              band: float | None = None) -> G0Report:
    """A、B 凸 CCW。逐样本：暴力相交谓词 vs E 成员谓词；再比对局部/全局 facet 集合。

    tol（长度，缺省 1e-12·L）：暴力谓词的接触带与法锥判据，也是 E 的平行边合并容差（长度）。band（长度，缺省
    1e-9·L）：成员谓词的边界带，带内样本跳过。旧版缺省是绝对 1e-12 / 1e-9，第三票的顶点比对是 round(·, 9)——
    旋转后坐标 1e3 处的方块对就因舍入落在不同的 1e-9 格子里报 4 个"顶点失配"（G6 纪律 F 复现）。
    """
    rng = random.Random(seed)
    rep = G0Report()
    L = char_length(A, B)
    tol = 1e-12 * L if tol is None else tol
    band = 1e-9 * L if band is None else band
    eb = convex_entrance_block(A, B, (0.0, 0.0), tol)
    amb = ambiguous_facets(A, B, tol)
    glob = {lab for lab in eb.facets if lab[0] != "FF"} - amb
    loc = local_facets(A, B, tol)
    rep.facet_local, rep.facet_global, rep.facet_ambiguous = len(loc), len(glob), len(amb)
    rep.facet_symmetric_diff = sorted(loc ^ glob)
    # 第三票（审查 r7）：标签集相等对"outward_normal 整体反号"是盲的；E 的顶点集必须等于
    # 差点集 {b − a} 的凸包顶点集——这条检验不经过法向、法锥或合并规则。
    # 顶点按距离配对（容差 1e-9·L + 舍入下限 × 累加步数），不按 round(·, 9) 的格子。
    # 差点 b − a 的量级小，但带着 A、B 原坐标的舍入 ~eps·C：共线判据的下限必须按原坐标量级取。
    hull = convex_hull([(b[0] - a[0], b[1] - a[1]) for a in A for b in B], round_floor(coord_scale(A, B)))
    mtol = 1e-9 * L + round_floor(coord_scale(A, B)) * (len(A) + len(B))

    def near(v, W):
        return any(math.hypot(v[0] - w[0], v[1] - w[1]) <= mtol for w in W)
    # 第四轮 regress 镜头（2026-10-10）：合法的 E 只保证**点集**相等，不保证顶点集相等——B 的短边对 A 的长边带一个真实微倾 d
    # （d ≫ 两边方向噪声，合法地不并成 FF），折点离弦 |e_s|·d 却低于凸包的弦距容差（舍入地板）时，convex_hull 按弦距丢掉折点、
    # E 保留它：两边口径下这个顶点都"说不清"。按弦距 ≤ 地板（加配对容差）判为 ambiguous，两边都不计（与三维 e_vertices_ambiguous
    # 同一做法）；旧版一刀切成失配，24 格里 13 格假红，而票一、票二都干净。
    hfl = round_floor(coord_scale(A, B))

    def chord_height(W, k):
        p, q = W[k - 1], W[(k + 1) % len(W)]
        pq = sub(q, p)
        return abs(cross(pq, sub(W[k], p))) / norm(pq) if norm(pq) > 0.0 else 0.0
    e_only = [k for k, v in enumerate(eb.vertices) if not near(v, hull)]
    h_only = [k for k, h in enumerate(hull) if not near(h, eb.vertices)]
    amb_e = [k for k in e_only if chord_height(eb.vertices, k) <= 4.0 * hfl + mtol]
    amb_h = [k for k in h_only if chord_height(hull, k) <= 4.0 * hfl + mtol]
    rep.hull_vertex_ambiguous = len(amb_e) + len(amb_h)
    rep.hull_vertex_mismatch = (len(e_only) - len(amb_e)) + (len(h_only) - len(amb_h))
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
    tol 是长度（随单位缩放）；atol 是**相对**阈值：|见证 − 真值| > atol·max(L, 真值) + c·eps·C 判失败
    （旧版 atol·max(1, 真值) 混了绝对量纲）。暴力谓词的接触带 1e-12·L（旧版绝对 1e-12：搬到 1e5 处，贴合样本
    因舍入被判成分离，G6 纪律 F 复现）。

    **不要**用 sign(min gap) 当凹块的成员谓词：VE 盖的 gap 是顶点到对方边**所在直线**的有符号距离，
    分离的两块之间也常有顶点落在对方某条边直线的内侧（细臂 L 块 + 凹槽内悬浮方块：gap −0.16，
    实际分离），三维上同一条规则 2026-09-18 已被证伪，二维 2026-09-21 审查复现。
    凹块的成员判定需要入口块的全局构造（M3）；在那之前，相交样本只计数、不检验。

    oracle 与被测对象的共用（纪律 A）：`polygons_overlap` 与盖枚举共用 geom 的向量算术
    （sub/dot/cross/norm）与舍入下限 `round_floor`；它另用的 `point_in_polygon`/`segments_properly_cross`/
    `triangulate`/`orient2d` 盖枚举都不用；不共用法锥、转角、外法向、投影、窗口或边内判据。
    `brute_polygon_distance` 只用内联算术。
    """
    rep = DistanceReport()
    inf = float("inf")
    L = char_length(A, B)
    for x in translations:
        rep.draws += 1
        At = translate(A, x)
        brute = polygons_overlap(At, B, 1e-12 * L)
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
        if err > atol * max(L, truth) + round_floor(coord_scale(At, B)):
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

    t 以 |u| 为单位：t_sep 是投影长度差，要除以 |u|²（G6 minor 13：旧版漏除，|u|<1 时哨兵落在真出口之前，
    返回的 t 处两块仍相交——u=(0.5,0) 的方块对报 0.35 而非 1.4）。候选线段参数 s 放宽舍入下限（端点命中不许
    因舍入漏掉：漏一个命中，区间中点就可能跨过 ∂E，返回更晚的出口）；多出的命中只会细分区间，无害。
    区间状态的接触带取 1e-12·L（纪律 F，旧版绝对 1e-12）。
    """
    ux, uy = u
    uu = ux * ux + uy * uy
    if uu == 0.0:
        raise ValueError("brute_ray_exit: direction u must be non-zero")
    hits: list[float] = []
    L = char_length(A, B)
    fl = ROUND_C * EPS * coord_scale(A, B)

    def hit(px: float, py: float, dx: float, dy: float, q0: Point, q1: Point) -> None:
        # 点 p 沿 (dx, dy) 走 t 落在闭线段 [q0, q1] 上：p + t·d = q0 + s·e，t > 0，s ∈ [0, 1]（放宽 fl/|e|）
        ex, ey = q1[0] - q0[0], q1[1] - q0[1]
        den = dx * ey - dy * ex
        if den == 0.0:                       # 射线与该边平行：共线段只在测度零的方向上出现
            return
        wx, wy = q0[0] - px, q0[1] - py
        t = (wx * ey - wy * ex) / den
        s = (wx * dy - wy * dx) / den
        sl = fl / math.hypot(ex, ey)
        if t > 0.0 and -sl <= s <= 1.0 + sl:
            hits.append(t)

    nA, nB = len(A), len(B)
    for px, py in A:                          # A 的顶点随 A 走 +u，撞 B 的边
        for j in range(nB):
            hit(px, py, ux, uy, B[j], B[(j + 1) % nB])
    for qx, qy in B:                          # 相对地，B 的顶点走 −u，撞 A 的边
        for k in range(nA):
            hit(qx, qy, -ux, -uy, A[k], A[(k + 1) % nA])
    t_sep = (max(bx * ux + by * uy for bx, by in B) - min(ax * ux + ay * uy for ax, ay in A)) / uu
    lo = 0.0
    for t in sorted({h for h in hits if h < t_sep}) + [t_sep]:
        mid = 0.5 * (lo + t)
        if polygons_overlap(translate(A, (mid * ux, mid * uy)), B, 1e-12 * L) != 1:
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
        min{ |point_a − point_b| : c ∈ enumerate_covers(A+z, B, window=∞, tol) } ≤ atol·L + c·eps·C，
    即法锥有效性筛选与边内筛选没有把出口处那段 ∂E 滤掉。atol 是相对阈值（L 为特征长度），c·eps·C 是出口位形
    坐标的舍入下限（旧版 atol·max(1, 坐标量级) 把绝对量纲与坐标量级混在一起：原点附近 ×1e-3 的块松到 1e-6·L，
    1e5 处松到 1e-4）。

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
    L = char_length(A, B)
    for x, u in zip(translations, directions):
        rep.draws += 1
        At = translate(A, x)
        brute = polygons_overlap(At, B, 1e-12 * L)
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
        rep.samples += 1
        rep.worst_witness = max(rep.worst_witness, got)
        if got > atol * L + round_floor(coord_scale(Az, B)):
            rep.failures.append((x, u, t, got, brute_polygon_distance(Az, B)[1]))
    return rep


def random_convex_polygon(rng: random.Random, n_points: int = 8, scale: float = 1.0) -> Poly:
    while True:
        pts = [(rng.uniform(-scale, scale), rng.uniform(-scale, scale)) for _ in range(n_points)]
        hull = convex_hull(pts)
        if len(hull) >= 3:
            return hull
