"""G0 exact independent votes and concave distance/first-exit completeness.

Convex votes use rational SAT, independent support sets and gift-wrap.
Concave membership, event partitioning and distance truth use g0_oracle's
independent integer/rational arithmetic. No hidden band excludes strict samples.
Relative/roundoff allowances audit float witness construction only, never truth.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from fractions import Fraction

from . import g0_oracle as independent
from .covers import ambiguous_facets, enumerate_covers, local_facets, membership_convex
from .exact import convex_overlap_exact, entrance_block_exact, strict_vertices
from .geom import Point, Poly, convex_hull, coord_scale, round_floor


@dataclass(slots=True)
class G0Report:
    samples: int = 0
    band_skipped: int = 0
    mismatches: list[tuple[Point, int, int]] = field(default_factory=list)   # (x, brute, cover)
    facet_local: int = 0
    facet_global: int = 0
    facet_symmetric_diff: list[tuple[str, int, int]] = field(default_factory=list)
    facet_ambiguous: int = 0           # 局部规则判"恰在法锥边界上"的 VE / EV 数（精确 = 0，对应精确平行；只报数，不豁免）
    hull_vertex_mismatch: int = 0      # 第三票：E 严格凸顶点集 vs conv{b−a} 精确凸包顶点集（不经法向/法锥/合并）
    hull_vertex_ambiguous: int = 0     # 恒为 0（精确之后没有"说不清"；字段保留只为兼容）
    boundary_probes: int = 0           # 真边界及其浮点舍入像的探针总数（各含 E 顶点与 facet 中点）

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


def _support_labels_independent(A: Poly, B: Poly) -> tuple[set[tuple], set[tuple]]:
    """独立票二 oracle：全顶点投影的最小支持集；只用内联 Fraction 算术，零法锥/极角/Minkowski 原语。

    唯一支持顶点给严格标签；多点并列给边界标签（包括平直顶点），不使用几何容差。
    """
    FA = [(Fraction(p[0]), Fraction(p[1])) for p in A]
    FB = [(Fraction(p[0]), Fraction(p[1])) for p in B]
    strict, boundary = set(), set()
    for target, edges, kind in ((FA, FB, "VE"), (FB, FA, "EV")):
        for k in range(len(edges)):
            p, q = edges[k], edges[(k + 1) % len(edges)]
            nx, ny = q[1] - p[1], p[0] - q[0]
            projections = [nx * v[0] + ny * v[1] for v in target]
            bottom = min(projections)
            support = [i for i, z in enumerate(projections) if z == bottom]
            labels = {(kind, i, k) if kind == "VE" else (kind, k, i) for i in support}
            (strict if len(support) == 1 else boundary).update(labels)
    return strict, boundary


def _difference_hull_independent(A: Poly, B: Poly) -> set[tuple[Fraction, Fraction]]:
    """独立票三 oracle：Jarvis gift-wrap，内联 Fraction 差/行列式/距离；不共用 exact 的单调链或任何几何原语。"""
    points = sorted({(Fraction(b[0]) - Fraction(a[0]), Fraction(b[1]) - Fraction(a[1]))
                     for a in A for b in B})
    if len(points) < 3:
        return set(points)
    start = current = points[0]
    hull = set()
    while True:
        hull.add(current)
        candidate = next(p for p in points if p != current)
        for p in points:
            ux, uy = candidate[0] - current[0], candidate[1] - current[1]
            vx, vy = p[0] - current[0], p[1] - current[1]
            determinant = ux * vy - uy * vx
            if determinant < 0 or (determinant == 0 and vx * vx + vy * vy > ux * ux + uy * uy):
                candidate = p
        current = candidate
        if current == start:
            return hull


def g0_convex(A: Poly, B: Poly, *, samples: int = 2000, seed: int = 0, tol: float | None = None,
              band: float | None = None) -> G0Report:
    """A、B 精确凸、CCW。三票精确（见模块文档）。`tol` / `band` 不再参与任何判定（保留只为兼容调用方）。"""
    rng = random.Random(seed)
    rep = G0Report()
    ex = entrance_block_exact(A, B)
    walk = {f.label for f in ex.facets if f.label[0] != "FF"}
    truth_strict, truth_boundary = _support_labels_independent(A, B)
    glob = walk - truth_boundary
    loc, amb = local_facets(A, B), ambiguous_facets(A, B)
    rep.facet_local, rep.facet_global, rep.facet_ambiguous = len(loc), len(glob), len(amb)
    # 全集等式而非 ambiguous 豁免：平直链余段也必须通过独立闭包支持检查。
    rep.facet_symmetric_diff = sorted((loc ^ truth_strict) | (amb ^ truth_boundary)
                                      | (glob ^ truth_strict) | (walk - truth_strict - truth_boundary))
    H = _difference_hull_independent(A, B)
    E = {ex.vertices[k] for k in strict_vertices(ex)}
    rep.hull_vertex_mismatch = len(E ^ H)
    # 真边界保留 Fraction，不能先把边界舍入到两侧；同时保留原来的浮点舍入探针。
    probes = sample_translations(A, B, samples, rng)
    exact_bnd = list(ex.vertices)
    exact_bnd += [(f.start[0] + f.direction[0] / 2, f.start[1] + f.direction[1] / 2) for f in ex.facets]
    bnd = exact_bnd + [(float(x), float(y)) for x, y in exact_bnd]
    rep.boundary_probes = len(bnd)
    for x in probes + bnd:
        cov = membership_convex(A, B, x)
        brute = convex_overlap_exact(A, B, x)
        rep.samples += 1
        if brute != cov:
            rep.mismatches.append((x, brute, cov))
    return rep


# ---------------------------------------------------------------- 凹块（也适用于凸块）：距离完备性

def _point_segment_distance(px, py, ax, ay, bx, by):
    """Independent rational closed-segment oracle; final sqrt is Decimal-only."""
    square, t = independent.segment_square((Fraction(px), Fraction(py)),
                                           (Fraction(ax), Fraction(ay)), (Fraction(bx), Fraction(by)))
    return independent.sqrt_display(square), float(t)


def brute_polygon_distance(A: Poly, B: Poly) -> tuple[float, tuple[str, int, int, float]]:
    """Independent rational vertex/closed-segment minimum for separated polygons.

    Oracle primitives are only g0_oracle's inline rational projections and Decimal
    square root. None is imported or called by production geometry/covers.
    """
    return independent.distance(A, B)


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
    """Exact classification plus independent rational distance-completeness vote.

    Oracle primitives: inline integer winding/intersections, rational closed-
    segment projection and Decimal sqrt; zero production geometry is shared.
    Translation stays rational. Only actual overlap/contact samples are outside
    the separation theorem. Every strict gap, however small, is checked.
    atol*max(L, truth)+roundoff audits float witnesses, never sample membership.
    """
    rep = DistanceReport()
    inf = float("inf")
    L = char_length(A, B)
    for x in translations:
        rep.draws += 1
        At = independent.translate(A, x)
        brute = independent.overlap(At, B)
        if brute == 1:
            rep.overlapping += 1
            continue
        if brute == 0:
            rep.touching += 1
            continue
        truth, arg = brute_polygon_distance(At, B)
        covs = enumerate_covers(At, B, window=inf)
        got = min((math.hypot(c.point_a[0] - c.point_b[0], c.point_a[1] - c.point_b[1])
                   for c in covs if c.point_a is not None and c.point_b is not None), default=inf)
        rep.samples += 1
        err = abs(got - truth)
        rep.worst_abs_error = max(rep.worst_abs_error, err)
        if err > atol * max(L, truth) + round_floor(coord_scale(At, B)):
            rep.failures.append((x, got, truth, arg))
    return rep


# ---------------------------------------------------------------- 相交样本：出口完备性（∂E 完备性的另一面）

def brute_ray_exit(A: Poly, B: Poly, u: Point) -> Fraction:
    """Independent exact first exit parameter from int E along nonzero u.

    Every rational vertex-edge event (including collinear endpoints) partitions
    the ray; independent integer winding checks each interval without a noise
    band. The Fraction result preserves the exact event for gate construction.
    No production geometric primitive is shared with the oracle.
    """
    return independent.ray_exit(A, B, u)


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
    """Exact first-exit completeness with an independent rational oracle.

    Membership, event times and interval classification use g0_oracle only;
    no production geometric primitive is shared. Only truly separated/touching
    samples are outside the strict-overlap theorem. Every interior sample is
    checked. The relative/roundoff allowance audits float witness construction.
    """
    if len(directions) != len(translations):
        raise ValueError(f"need one direction per translation: {len(directions)} != {len(translations)}")
    rep = ExitReport()
    inf = float("inf")
    L = char_length(A, B)
    for x, u in zip(translations, directions):
        rep.draws += 1
        At = independent.translate(A, x)
        brute = independent.overlap(At, B)
        if brute == -1:
            rep.separated += 1
            continue
        if brute == 0:
            rep.touching += 1
            continue
        t = brute_ray_exit(At, B, u)
        Az = independent.translate(At, (t * Fraction(u[0]), t * Fraction(u[1])))
        covs = enumerate_covers(Az, B, window=inf)
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
