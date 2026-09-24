"""三维 G0 自证门：理论原生 oracle，不依赖任何 legacy。

三票（沿用二维版审查 r7 的结论——单靠标签集相等对"共同符号错"是盲的）：
  票一  逐样本：暴力多面体相交谓词 vs 盖系统的 E 成员谓词，凸情形要求恒等；
  票二  局部法锥规则给出的严格 facet 集合 == 由 conv{b − a} 读出的严格 facet 集合（结构一致）；
  票三  E 的顶点集 == conv{b − a} 的**极点**集（不经 A、B 的面法向、法锥、合并规则）。

各票的 oracle 与被测对象共用了什么（纪律 A）：
  票一  暴力谓词 polyhedra_overlap（射线奇偶 + geom3.point_in_face_polygon）与成员谓词
        membership_convex3（面法向 + 支撑顶点 + EE 标签）不共用判定原语；二者共用
        Polyhedron.face_normal，但暴力谓词的**判定**只用它的方向不用符号（内点、微推与接触锥证人的
        搜索方向用到符号，而每个证人都经符号无关的 point_in_polyhedron 复验——符号错最多让
        证人搜不到，不会造成假阳性），故对"法向整体翻号"不盲（test_kernel3d_covers 的翻转法向牙）。
        接触锥证人的 Gordan 方向是 geom3 里的独立实现（`_gordan_direction`），不经 covers3 的
        cone_relint_direction / closest_point_of_convex_hull_to_origin。
  票二  局部侧经 covers3.facet_normal3（face_normal、edge_arc_contains）；凸包侧只用差点坐标：
        三角面叉积给候选法向、**支撑定向**（全部差点落在非正侧）、再按 A、B 各自支撑集的
        仿射维数判它是严格 facet 还是 FF/FE 退化。凸包（2026-09-24 起为 Quickhull）用自己的三角叉积
        判可见性，**不再**调用 Polyhedron.face_normal——票二两侧的共用只剩 Polyhedron 的坐标本身。
  票三  局部侧只用棱方向与坐标（cones_intersect_relint）；凸包侧只用差点坐标（极点判定见
        _hull_extreme_vertices）。

票二在 2026-09-21 之前只存了一个计数、从不比较（审查 C23/C27：删掉任一严格 facet，190 次里
181 次仍 passed）。现在 `passed` 看 facet_symmetric_diff。

尺度（2026-09-24 G6 minor 9，纪律 F）：g0_convex3 的 tol / band 是**相对** E 的尺度 L（差点集 AABB
对角线）的；凸包、支撑容差、平面去重角、票三顶点匹配全部按 L 与坐标量级 C 的舍入地板取。此前凸包
tol = 1e-12 与 ∝ 长度³ 的三重积比，尺度 ≤ 1e-5 时凸包报"共面"；票三用 round(·, 7) 的绝对顶点键。
票三现在按距离容差逐点匹配（不用舍入键：键在舍入边界两侧会把同一点拆成两个）。
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .covers3 import facet_normal3, local_facets3, membership_convex3
from .geom3 import (Polyhedron, Vec3, add, angle_between, brute_feature_distance, convex_hull_3d,
                    coord_scale, cross, dot, neg, noise_floor, norm, polyhedra_overlap, sub, unit)


@dataclass(slots=True)
class G0Report3:
    samples: int = 0
    band_skipped: int = 0
    mismatches: list[tuple[Vec3, int, int]] = field(default_factory=list)
    facet_local: int = 0              # 局部法锥规则给出的严格 facet 标签数
    facet_global: int = 0             # conv{b − a} 上应当有严格标签的 facet 数
    facet_degenerate: int = 0         # conv{b − a} 上的 FF/FE 退化 facet 数（按设计无严格标签）
    # 票二的对称差：("hull_only", 法向, dimA, dimB) / ("local_only", 标签) / ("duplicate", 标签)
    #              / ("hull_anomaly", 法向, dimA, dimB)（凸包侧自身不自洽）
    facet_symmetric_diff: list[tuple] = field(default_factory=list)
    hull_vertex_mismatch: int = 0
    hull_vertices: int = 0
    e_vertices: int = 0

    @property
    def passed(self) -> bool:
        return (not self.mismatches and not self.facet_symmetric_diff
                and self.hull_vertex_mismatch == 0)


def _hull_extreme_vertices(hull: Polyhedron, ang: float = 1e-7, area_tol: float | None = None) -> list[Vec3]:
    """凸包三角网格里真正的**极点**：关联的非退化三角至少张出 3 个不同平面。

    convex_hull_3d 会把落在 facet 内部或棱上的共面/共线点留作三角网格顶点（加点顺序决定），
    它们不是 E 的顶点。一般位置下不存在这种点，退化输入（平行面：tetra vs box、box vs box）
    则大量出现——此前票三因此在退化输入上误红（19 vs 13、26 vs 8；2026-09-23 修 C2 时发现）。
    只用凸包自身的坐标：叉积给平面方向（不读 face_normal、不看朝向），按无向角去重。
    零面积碎片的判据相对凸包尺度（area_tol 缺省 1e-14·L²，此前是 1e-14·max(1, L)²）。
    """
    lo, hi = hull.aabb()
    scale = norm(sub(hi, lo)) or 1.0
    if area_tol is None:
        area_tol = 1e-14 * scale * scale
    planes: dict[int, list[Vec3]] = {}
    for f in hull.faces:
        o = hull.verts[f[0]]
        c = (0.0, 0.0, 0.0)
        for i in range(1, len(f) - 1):
            c = add(c, cross(sub(hull.verts[f[i]], o), sub(hull.verts[f[i + 1]], o)))
        if norm(c) <= area_tol:
            continue
        n = unit(c)
        for vi in f:
            lst = planes.setdefault(vi, [])
            if not any(min(angle_between(n, m), angle_between(neg(n), m)) <= ang for m in lst):
                lst.append(n)
    return [hull.verts[vi] for vi, lst in planes.items() if len(lst) >= 3]


def _affine_dim(points: list[Vec3], tol: float) -> int:
    """点集的仿射维数（0 / 1 / 2 / 3），容差 tol（长度）。只用坐标。"""
    p0 = points[0]
    far = max(points, key=lambda p: norm(sub(p, p0)))
    if norm(sub(far, p0)) <= tol:
        return 0
    t = unit(sub(far, p0))
    off = [sub(sub(p, p0), tuple(dot(sub(p, p0), t) * c for c in t)) for p in points]
    j = max(range(len(points)), key=lambda i: norm(off[i]))
    if norm(off[j]) <= tol:
        return 1
    n = unit(cross(t, off[j]))
    return 3 if any(abs(dot(n, sub(p, p0))) > tol for p in points) else 2


def _hull_facets(A: Polyhedron, B: Polyhedron, diffs: list[Vec3], hull: Polyhedron,
                 scale: float, ptol: float, ang: float,
                 area_tol: float | None = None) -> list[tuple[Vec3, int, int, bool]]:
    """凸包侧：conv{b − a} 的每个 facet → (支撑定向外法向, dim F_A, dim F_B, 是否支撑自洽)。

    F_A = A 上使 n·a 最小的顶点集（−A 在 n 方向的支撑面），F_B = B 上使 n·b 最大的顶点集。
    E 的 facet = F_B ⊕ (−F_A) 是二维的；严格 ⟺ (0,2) VF、(2,0) FV、(1,1) EE；其余为退化。
    法向由面三角的叉积给出、朝向由支撑条件定——不读 Polyhedron.face_normal，不信面环朝向。
    """
    out: list[tuple[Vec3, int, int, bool]] = []
    for f in hull.faces:
        c = (0.0, 0.0, 0.0)
        o = hull.verts[f[0]]
        for i in range(1, len(f) - 1):
            c = add(c, cross(sub(hull.verts[f[i]], o), sub(hull.verts[f[i + 1]], o)))
        if norm(c) <= (1e-14 * scale * scale if area_tol is None else area_tol):
            continue                                            # 零面积碎片不给法向
        n = unit(c)
        h0 = dot(n, o)
        vals = [dot(n, p) for p in diffs]
        ok = True
        if max(vals) <= h0 + ptol:
            pass
        elif min(vals) >= h0 - ptol:
            n = neg(n)
        else:
            ok = False                                          # 不是支撑平面：凸包不自洽
        if any(angle_between(n, m) <= ang for m, *_ in out):
            continue
        amin = min(dot(n, a) for a in A.verts)
        bmax = max(dot(n, b) for b in B.verts)
        FA = [a for a in A.verts if dot(n, a) <= amin + ptol]
        FB = [b for b in B.verts if dot(n, b) >= bmax - ptol]
        out.append((n, _affine_dim(FA, ptol), _affine_dim(FB, ptol), ok))
    return out


def _gate_scales(A: Polyhedron, B: Polyhedron, diffs: list[Vec3]) -> tuple[float, float, float, float]:
    """(L, ptol, ang, area_tol)：E 的尺度 L（差点集 AABB 对角线）、支撑/仿射维数的长度容差、
    平面去重角、零面积碎片阈值。长度取 max(1e-9·L, 舍入地板)，角度取 max(1e-7, 方向噪声)——
    差点由量级 C 的坐标相减得到，退化关系（共面、平行）被舍入破坏到 ~eps·C（纪律 F）。"""
    xs = [p[0] for p in diffs]
    ys = [p[1] for p in diffs]
    zs = [p[2] for p in diffs]
    L = norm((max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))) or 1.0
    CA, _, la = A.metrics()
    CB, _, lb = B.metrics()
    fl = 16.0 * noise_floor(max(CA, CB, coord_scale(*diffs)))
    ptol = max(1e-9 * L, fl)
    ang = max(1e-7, fl / min(la, lb))
    return L, ptol, ang, max(1e-14 * L * L, 2.0 * fl * L)


def facet_vote3(A: Polyhedron, B: Polyhedron, facets: set[tuple], hull: Polyhedron,
                diffs: list[Vec3]) -> tuple[int, int, list[tuple]]:
    """票二：返回 (facet_global, facet_degenerate, 对称差)。见模块文档。"""
    scale, ptol, ang, area_tol = _gate_scales(A, B, diffs)

    def key(n: Vec3) -> tuple:
        return tuple(round(c, 7) + 0.0 for c in n)

    strict: list[tuple[Vec3, int, int]] = []
    diff: list[tuple] = []
    n_deg = 0
    for n, da, db, ok in _hull_facets(A, B, diffs, hull, scale, ptol, ang, area_tol):
        if not ok or (da, db) not in ((0, 2), (2, 0), (1, 1), (1, 2), (2, 1), (2, 2)):
            diff.append(("hull_anomaly", key(n), da, db))
        elif (da, db) in ((0, 2), (2, 0), (1, 1)):
            strict.append((n, da, db))
        else:
            n_deg += 1
    matched = [False] * len(strict)
    for lab in sorted(facets):
        n = facet_normal3(A, B, lab)
        j = next((j for j, (m, _, _) in enumerate(strict) if angle_between(n, m) <= ang), None)
        if j is None:
            diff.append(("local_only", lab))
        elif matched[j]:
            diff.append(("duplicate", lab))
        else:
            matched[j] = True
    for j, (m, da, db) in enumerate(strict):
        if not matched[j]:
            diff.append(("hull_only", key(m), da, db))
    return len(strict), n_deg, sorted(diff)


def sample_translations3(A: Polyhedron, B: Polyhedron, n: int, rng: random.Random,
                         margin: float = 0.25) -> list[Vec3]:
    (ax0, ay0, az0), (ax1, ay1, az1) = A.aabb()
    (bx0, by0, bz0), (bx1, by1, bz1) = B.aabb()
    lo = (bx0 - ax1, by0 - ay1, bz0 - az1)
    hi = (bx1 - ax0, by1 - ay0, bz1 - az0)
    w = tuple(hi[i] - lo[i] for i in range(3))
    return [tuple(rng.uniform(lo[i] - margin * w[i], hi[i] + margin * w[i]) for i in range(3))
            for _ in range(n)]


def _dedup_points(pts: list[Vec3], tol: float) -> list[Vec3]:
    out: list[Vec3] = []
    for p in pts:
        if not any(norm(sub(p, q)) <= tol for q in out):
            out.append(p)
    return out


def _unmatched(P: list[Vec3], Q: list[Vec3], tol: float) -> int:
    """两点集按距离 ≤ tol 贪心一一配对后，两侧剩余的点数之和（= 点集对称差的大小）。"""
    free = list(Q)
    miss = 0
    for p in P:
        j = next((j for j, q in enumerate(free) if norm(sub(p, q)) <= tol), None)
        if j is None:
            miss += 1
        else:
            free.pop(j)
    return miss + len(free)


def g0_convex3(A: Polyhedron, B: Polyhedron, *, samples: int = 400, seed: int = 0,
               tol: float = 1e-12, band: float = 1e-7) -> G0Report3:
    """凸块 G0 三票。tol（票一暴力谓词的边界带、凸包的相对容差）与 band（票一成员谓词的跳过带）
    都是**相对** E 的尺度 L 的（见模块文档"尺度"）；局部法锥规则的 tol 是角度，原样传给 covers3。"""
    rng = random.Random(seed)
    rep = G0Report3()
    facets = local_facets3(A, B, tol)
    rep.facet_local = len(facets)
    # 票三：E 顶点集 = conv{b − a} 极点集（凸包三角网格里的共面/共线非极点不算）
    diffs = [sub(b, a) for a in A.verts for b in B.verts]
    L, ptol, ang, area_tol = _gate_scales(A, B, diffs)
    hull = convex_hull_3d(diffs, tol=max(tol, ptol / L))
    hv = _dedup_points(_hull_extreme_vertices(hull, ang, area_tol), ptol)
    # 票三：由**局部锥相交规则**判定为 E 顶点的 (a,b) 对，其差点集必须等于 hull 顶点集。
    # 这条检验只用棱方向与坐标，不经面法向、不经任何合并规则，故对"整体符号错"不盲。
    from .covers3 import cones_intersect_relint
    ev_raw: list[Vec3] = []
    for ia in range(len(A.verts)):
        for ib in range(len(B.verts)):
            if cones_intersect_relint(A, ia, B, ib, max(tol, 1e-12)):
                ev_raw.append(sub(B.verts[ib], A.verts[ia]))
    ev = _dedup_points(ev_raw, ptol)
    rep.hull_vertices, rep.e_vertices = len(hv), len(ev)
    rep.hull_vertex_mismatch = _unmatched(hv, ev, max(1e-7 * L, ptol))
    # 票二：严格 facet 集合（定向法向）== conv{b − a} 上的严格 facet 集合
    rep.facet_global, rep.facet_degenerate, rep.facet_symmetric_diff = facet_vote3(
        A, B, facets, hull, diffs)
    # 票一：逐样本成员谓词（band、tol 相对 L；另加坐标舍入地板）
    band_abs = max(band * L, ptol)
    tol_abs = tol * L
    for x in sample_translations3(A, B, samples, rng):
        cov = membership_convex3(A, B, x, band_abs, facets)
        if cov == 0:
            rep.band_skipped += 1
            continue
        brute = polyhedra_overlap(A.translated(x), B, tol_abs)
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
    即法锥筛选不会把实现最短距离的那一对特征滤掉。oracle 是 `brute_feature_distance`
    （枚举全部特征对、零法锥筛选、只用坐标）。

    纪律 A（共用与风险）：oracle 的点-面距离与盖的 in_extent 共用 geom3.point_in_face_polygon——
    它若错，两边一起错，本门看不见（2026-09-21 审查 C7 正是这样：两边都用半平面核，凹面上
    同错）。所以 point_in_face_polygon 另有不经 geom3 的独立门（tests/test_geom3_face_polygon.py：
    矩形并集、星形极坐标、闭式距离），本门只对"法锥筛选丢特征对"有牙。
    另：本门的采样区只在给定 base 附近，凹面臂上的最近对需要**定点探针**才会被采到
    （tests/test_geom3_face_polygon.py 的骨形块侧面探针）。

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
