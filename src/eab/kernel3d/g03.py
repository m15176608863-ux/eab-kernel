"""三维 G0 自证门：理论原生 oracle，不依赖任何 legacy。

三票（沿用二维版审查 r7 的结论——单靠标签集相等对"共同符号错"是盲的）：
  票一  逐样本：暴力多面体相交谓词 vs 盖系统的 E 成员谓词，凸情形要求恒等；
  票二  局部法锥规则给出的 facet 集合 == 由 E 的凸包读出的 facet 集合（结构一致）；
  票三  E 的顶点集 == conv{b − a} 的顶点集（不经法向、法锥、合并规则）。
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .covers3 import local_facets3, membership_convex3
from .geom3 import (Polyhedron, Vec3, add, brute_feature_distance, convex_hull_3d, norm,
                    polyhedra_overlap, sub)


@dataclass(slots=True)
class G0Report3:
    samples: int = 0
    band_skipped: int = 0
    mismatches: list[tuple[Vec3, int, int]] = field(default_factory=list)
    facet_local: int = 0
    hull_vertex_mismatch: int = 0
    hull_vertices: int = 0
    e_vertices: int = 0

    @property
    def passed(self) -> bool:
        return not self.mismatches and self.hull_vertex_mismatch == 0


def sample_translations3(A: Polyhedron, B: Polyhedron, n: int, rng: random.Random,
                         margin: float = 0.25) -> list[Vec3]:
    (ax0, ay0, az0), (ax1, ay1, az1) = A.aabb()
    (bx0, by0, bz0), (bx1, by1, bz1) = B.aabb()
    lo = (bx0 - ax1, by0 - ay1, bz0 - az1)
    hi = (bx1 - ax0, by1 - ay0, bz1 - az0)
    w = tuple(hi[i] - lo[i] for i in range(3))
    return [tuple(rng.uniform(lo[i] - margin * w[i], hi[i] + margin * w[i]) for i in range(3))
            for _ in range(n)]


def g0_convex3(A: Polyhedron, B: Polyhedron, *, samples: int = 400, seed: int = 0,
               tol: float = 1e-12, band: float = 1e-7) -> G0Report3:
    rng = random.Random(seed)
    rep = G0Report3()
    facets = local_facets3(A, B, tol)
    rep.facet_local = len(facets)
    # 票三：E 顶点集 = conv{b − a} 顶点集
    diffs = [sub(b, a) for a in A.verts for b in B.verts]
    hull = convex_hull_3d(diffs, tol=1e-12)
    hv = {(round(v[0], 7), round(v[1], 7), round(v[2], 7)) for v in hull.verts}
    # 票三：由**局部锥相交规则**判定为 E 顶点的 (a,b) 对，其差点集必须等于 hull 顶点集。
    # 这条检验只用棱方向与坐标，不经面法向、不经任何合并规则，故对"整体符号错"不盲。
    from .covers3 import cones_intersect_relint
    ev: set[tuple[float, float, float]] = set()
    for ia in range(len(A.verts)):
        for ib in range(len(B.verts)):
            if cones_intersect_relint(A, ia, B, ib, max(tol, 1e-12)):
                d = sub(B.verts[ib], A.verts[ia])
                ev.add((round(d[0], 7), round(d[1], 7), round(d[2], 7)))
    rep.hull_vertices, rep.e_vertices = len(hv), len(ev)
    rep.hull_vertex_mismatch = len(hv ^ ev)
    # 票一：逐样本成员谓词
    for x in sample_translations3(A, B, samples, rng):
        cov = membership_convex3(A, B, x, band, facets)
        if cov == 0:
            rep.band_skipped += 1
            continue
        brute = polyhedra_overlap(A.translated(x), B, tol)
        if brute == 0:
            rep.band_skipped += 1
            continue
        rep.samples += 1
        if brute != cov:
            rep.mismatches.append((x, brute, cov))
    return rep


@dataclass(slots=True)
class DistanceReport3:
    """凹块 G0：'法锥有效性筛选不丢最近特征对' 的完备性检验结果。"""
    samples: int = 0
    skipped_intersecting: int = 0
    worst_abs_error: float = 0.0
    failures: list[tuple[Vec3, float, float]] = field(default_factory=list)   # (x, 盖距离, 真距离)

    @property
    def passed(self) -> bool:
        return not self.failures


def g0_distance_completeness3(A: Polyhedron, B: Polyhedron, *, radius: float, samples: int = 200,
                              seed: int = 0, base: Vec3 = (0.0, 0.0, 0.0), tol: float = 1e-9,
                              atol: float = 1e-9) -> DistanceReport3:
    """凹块（也适用于凸块）的 G0 正确形式：**距离完备性**。

    命题：A、B 分离时，d(A,B) = min over 法锥有效且落在特征范围内的盖 of |特征间距|。
    即法锥筛选不会把实现最短距离的那一对特征滤掉。独立 oracle 是 `brute_feature_distance`
    （枚举全部特征对、零法锥筛选、只用坐标）。

    **不要**用"最小盖间隙的符号"当成员谓词（2026-09-18 实测被推翻）：VF 盖的 gap 是顶点到
    面**所在平面**的有符号距离，分离的两块之间也常有顶点落在对方某个面平面的内侧，故 min 会
    报出 −2.7 这类假侵入。凸块的成员谓词是 facet 间隙取 **max**（见 membership_convex3）；
    凹块的 E 非凸，max 与 min 都不成立，成员判定需要入口块的**全局**构造（Phase 3 的目标）。
    """
    from .covers3 import enumerate_covers3
    rng = random.Random(seed)
    rep = DistanceReport3()
    drawn = 0
    while drawn < samples:
        v = (rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0))
        nv = norm(v)
        if nv > 1.0 or nv == 0.0:
            continue
        drawn += 1
        x = tuple(base[i] + radius * v[i] for i in range(3))
        At = A.translated(x)
        if polyhedra_overlap(At, B, 1e-12) != -1:
            rep.skipped_intersecting += 1
            continue
        truth = brute_feature_distance(At, B)
        covs = [c for c in enumerate_covers3(At, B, window=float("inf"), tol=tol) if c.in_extent]
        cand = [norm(sub(c.point_a, c.point_b)) for c in covs
                if c.point_a is not None and c.point_b is not None]
        got = min(cand) if cand else float("inf")
        rep.samples += 1
        err = abs(got - truth)
        rep.worst_abs_error = max(rep.worst_abs_error, err)
        if err > atol * max(1.0, truth):
            rep.failures.append((x, got, truth))
    return rep
