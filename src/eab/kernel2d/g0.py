"""G0 自证门：理论原生 oracle。

E(A,B) 的成员谓词可以暴力验证——随机采样参考点平移 x，直接做多边形相交测试，与盖系统给出的
判定比对。凸情形要求逐样本恒等（去掉 |gap| ≤ band 的边界带）；同时检验"局部法锥规则 = 全局
Minkowski facet 结构"（命题 4/5）。这条门不依赖任何 legacy。
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .covers import convex_entrance_block, local_facets, membership_convex
from .geom import Point, Poly, convex_hull, polygons_overlap, translate


@dataclass(slots=True)
class G0Report:
    samples: int = 0
    band_skipped: int = 0
    mismatches: list[tuple[Point, int, int]] = field(default_factory=list)   # (x, brute, cover)
    facet_local: int = 0
    facet_global: int = 0
    facet_symmetric_diff: list[tuple[str, int, int]] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.mismatches and not self.facet_symmetric_diff


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


def random_convex_polygon(rng: random.Random, n_points: int = 8, scale: float = 1.0) -> Poly:
    while True:
        pts = [(rng.uniform(-scale, scale), rng.uniform(-scale, scale)) for _ in range(n_points)]
        hull = convex_hull(pts)
        if len(hull) >= 3:
            return hull
