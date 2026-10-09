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
  票三  局部侧只用棱方向与坐标（cones_intersect_relint）；凸包侧只用差点坐标——凸包的顶点集就是
        E 的顶点集（M0.3 起 Quickhull 保证容差内的共面/共线点不成为顶点：全局最远者优先、并列按离质心最远
        裁决、细条面兜底；旧版另有一道"极点筛"按 1e-7 rad 合并相邻面的法向，把棱脊高 1e-6 的真顶点筛掉）。

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
                    coord_scale, cross, dot, mul, neg, noise_floor, norm, polyhedra_overlap, sub, unit)


@dataclass(slots=True)
class G0Report3:
    samples: int = 0
    band_skipped: int = 0
    mismatches: list[tuple[Vec3, int, int]] = field(default_factory=list)
    facet_local: int = 0              # 局部法锥规则给出的严格 facet 标签数
    facet_global: int = 0             # conv{b − a} 上应当有严格标签的 facet 数
    facet_degenerate: int = 0         # conv{b − a} 上的 FF/FE 退化 facet 数（按设计无严格标签）
    facet_ambiguous: int = 0          # 凸包侧在噪声内说不清的 facet 数（两边都不计；见 _hull_facets）
    facet_local_dropped: int = 0      # 落在 ambiguous facet 支撑集里、因此不计的局部标签数
    # 票二的对称差：("hull_only", 法向, dimA, dimB) / ("local_only", 标签) / ("duplicate", 标签)
    #              / ("hull_anomaly", 法向, dimA, dimB)（凸包侧自身不自洽）
    facet_symmetric_diff: list[tuple] = field(default_factory=list)
    hull_vertex_mismatch: int = 0
    hull_vertices: int = 0            # 凸包顶点数（扣掉与"说不清"的局部顶点对重合的）
    e_vertices: int = 0               # 局部锥相交规则给出的 E 顶点数（裕度 > 噪声）
    e_vertices_ambiguous: int = 0     # 裕度落在噪声量级以内、两边都不计的顶点对数

    @property
    def passed(self) -> bool:
        return (not self.mismatches and not self.facet_symmetric_diff
                and self.hull_vertex_mismatch == 0)


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


def _plane_from_points(P: list[Vec3], fl: float) -> tuple[Vec3, float] | None:
    """良态的平面法向：相距最远的两点 + 离该线最远的点（三点张成的三角高最大）。返回 (单位法向, 法向的角噪声
    ≈ fl·(1/底 + 1/高))；点集在 4·fl 内共线或重合时返回 None。"""
    p0 = P[0]
    p1 = max(P, key=lambda p: norm(sub(p, p0)))
    e1 = sub(p1, p0)
    l1 = norm(e1)
    if l1 <= 4.0 * fl:
        return None
    t = unit(e1)
    best, h = None, 0.0
    for p in P:
        w = sub(p, p0)
        d = norm(sub(w, mul(t, dot(w, t))))
        if d > h:
            best, h = p, d
    if best is None or h <= 4.0 * fl:
        return None
    return unit(cross(e1, sub(best, p0))), fl * (1.0 / l1 + 1.0 / h)


def _farthest_pair(P: list[Vec3]) -> tuple[float, Vec3, Vec3]:
    best = (0.0, P[0], P[0])
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            d = norm(sub(P[j], P[i]))
            if d > best[0]:
                best = (d, P[i], P[j])
    return best


def _hull_facets(A: Polyhedron, B: Polyhedron, diffs: list[Vec3], hull: Polyhedron,
                 fl: float, area_tol: float) -> list[tuple]:
    """凸包侧：conv{b − a} 的每个 facet → (支撑定向外法向, dim F_A, dim F_B, 是否支撑自洽, F_A 下标集, F_B 下标集,
    说不清时的宽带种子集 (ia0, ib0)，否则 None)。

    F_A = A 上使 n·a 最小的顶点集（−A 在 n 方向的支撑面），F_B = B 上使 n·b 最大的顶点集。
    E 的 facet = F_B ⊕ (−F_A) 是二维的；严格 ⟺ (0,2) VF、(2,0) FV、(1,1) EE；其余为退化。
    不读 Polyhedron.face_normal，不信面环朝向。

    M0.3（G6 第二轮 major 的后半）："组合来自凸包、几何来自特征"。凸包三角（常是细条）的法向噪声 ≈ fl·周长/(2·面积)，
    直接拿它判支撑集会把法向只差 5e-4 rad 的相邻 facet 混在一起。做法：
      1. 三角法向 n0 + 宽带（4·fl + 力臂 × n0 的噪声）给出**种子**支撑集 F_A⁰、F_B⁰ 与自洽性（全部差点落在非正侧）；
      2. 从种子支撑特征**重算**法向：A 面的平面、B 面的平面、A 棱 × B 棱——这些由物体自己的顶点算，良态；
         取与 n0 最近的候选；若第二个候选在噪声内同样说得通，记 ambiguous；
      3. 用重算的法向、逐顶点的紧带（fl + 法向噪声 × 到锚点的距离，锚点是该体的极值顶点）定最终支撑集；
         有顶点落在紧带的 1/16（真实舍入量级：地板 c·eps·C 里 c = 64 是政策，4·eps·C 才是坐标自身的舍入）与 4 倍之间的
         （阈值两侧都算），也记 ambiguous。
    同一 facet 的多个三角按支撑顶点集组合去重。ambiguous 的 facet 两边都不计（见 facet_vote3）。
    旧版：法向就用三角的、支撑带是人为的 1e-9·L、facet 按法向夹角 1e-7 去重。"""
    out: list[tuple] = []
    seen: set[tuple[frozenset, frozenset]] = set()
    for f in hull.faces:
        o = hull.verts[f[0]]
        c = (0.0, 0.0, 0.0)
        per = sum(norm(sub(hull.verts[f[(i + 1) % len(f)]], hull.verts[f[i]])) for i in range(len(f)))
        for i in range(1, len(f) - 1):
            c = add(c, cross(sub(hull.verts[f[i]], o), sub(hull.verts[f[i + 1]], o)))
        area2 = norm(c)
        if area2 <= area_tol:
            continue                                            # 零面积碎片（舍入级共面点间的细条三角）不给法向
        n0 = unit(c)
        noise0 = fl * per / area2
        lever = max(norm(sub(p, o)) for p in diffs)
        band0 = 4.0 * fl + lever * noise0
        h0 = dot(n0, o)
        vals = [dot(n0, p) for p in diffs]
        ok = True
        if max(vals) <= h0 + band0:
            pass
        elif min(vals) >= h0 - band0:
            n0 = neg(n0)
        else:
            ok = False                                          # 不是支撑平面：凸包不自洽
        amin = min(dot(n0, a) for a in A.verts)
        bmax = max(dot(n0, b) for b in B.verts)
        ia0 = frozenset(i for i, a in enumerate(A.verts) if dot(n0, a) <= amin + band0)
        ib0 = frozenset(i for i, b in enumerate(B.verts) if dot(n0, b) >= bmax - band0)
        FA0 = [A.verts[i] for i in ia0]
        FB0 = [B.verts[i] for i in ib0]
        cands: list[tuple[Vec3, float]] = []
        for P in (FA0, FB0):
            if len(P) >= 3:
                pl = _plane_from_points(P, fl)
                if pl is not None:
                    cands.append(pl)
        if len(FA0) >= 2 and len(FB0) >= 2:
            la, a0, a1 = _farthest_pair(FA0)
            lb, b0, b1 = _farthest_pair(FB0)
            cr = cross(sub(b1, b0), sub(a1, a0))
            if la > 4.0 * fl and lb > 4.0 * fl and norm(cr) > 0.0:
                # 叉积只正交到 eps/sinθ：近平行的最远点对给出的候选噪声要除以 sinθ = |cr|/(la·lb)，否则它以 4e-14 的自报噪声
                # 压过 3e-16 的精确平面候选、紧带随之排掉其余面顶点（G6 第三轮 major：偏航 1e-3 的叠放方块随机旋转后门红）
                cands.append((unit(cr), fl * (1.0 / la + 1.0 / lb) * (la * lb / norm(cr))))
        ambiguous = False
        n1, noise = n0, noise0
        if cands:
            ranked = sorted((min(angle_between(n, n0), angle_between(neg(n), n0)), k) for k, (n, _) in enumerate(cands))
            ang1, k1 = ranked[0]
            n1, noise = cands[k1]
            if dot(n1, n0) < 0.0:
                n1 = neg(n1)
            for ang2, k2 in ranked[1:]:
                n2, noise2 = cands[k2]
                apart = min(angle_between(n2, n1), angle_between(neg(n2), n1))
                # 另一个候选也在三角法向的噪声内说得通，而且它与选中者**不是同一个平面**（平行面的 FF 退化
                # facet 两个候选本就重合，不算说不清）
                if ang2 <= ang1 + noise0 + noise + noise2 and apart > noise + noise2:
                    ambiguous = True
        ka = min(range(len(A.verts)), key=lambda i: dot(n1, A.verts[i]))
        kb = max(range(len(B.verts)), key=lambda i: dot(n1, B.verts[i]))
        ia: set[int] = set()
        ib: set[int] = set()
        # 紧带 = 长度地板 + 法向噪声 × 到锚点的距离（与 covers3 的逐特征口径一致：局部侧判"严格"的门槛正是
        # 噪声 × 棱长 = fl）；落在阈值两侧 4 倍以内的顶点都算说不清——不许一边按 1 倍噪声判严格、另一边按 4 倍并掉
        for i, a in enumerate(A.verts):
            gap = dot(n1, sub(a, A.verts[ka]))
            tight = fl + noise * norm(sub(a, A.verts[ka]))
            if gap <= tight:
                ia.add(i)
            if tight / 16.0 < gap <= 4.0 * tight and i != ka:
                ambiguous = True
        for i, b in enumerate(B.verts):
            gap = dot(n1, sub(B.verts[kb], b))
            tight = fl + noise * norm(sub(b, B.verts[kb]))
            if gap <= tight:
                ib.add(i)
            if tight / 16.0 < gap <= 4.0 * tight and i != kb:
                ambiguous = True
        key = (frozenset(ia), frozenset(ib))
        if key in seen:
            continue
        seen.add(key)
        out.append((n1, _affine_dim([A.verts[i] for i in ia], 4.0 * fl), _affine_dim([B.verts[i] for i in ib], 4.0 * fl),
                    ok, key[0], key[1], (ia0, ib0) if ambiguous else None))
    return out


def _gate_scales(A: Polyhedron, B: Polyhedron, diffs: list[Vec3]) -> tuple[float, float, float]:
    """(L, fl, area_tol)：E 的尺度 L（差点集 AABB 对角线）、长度舍入地板 fl（c·eps·C，与 covers3 同一口径；M0.2 曾乘 16
    以掩盖凸包细条三角的法向噪声，现在法向从支撑特征重算，不再需要）、零面积碎片阈值。
    差点由量级 C 的坐标相减得到，退化关系（共面、平行）被舍入破坏到 ~eps·C（纪律 F）。
    M0.3：票二逐 facet 取支撑带、按组合匹配（见 `_hull_facets`）；票三的顶点匹配用 max(1e-7·L, fl)。"""
    xs = [p[0] for p in diffs]
    ys = [p[1] for p in diffs]
    zs = [p[2] for p in diffs]
    L = norm((max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))) or 1.0
    fl = noise_floor(max(A.metrics()[0], B.metrics()[0], coord_scale(*diffs)))
    return L, fl, max(1e-14 * L * L, 2.0 * fl * L)


def _label_sets(A: Polyhedron, B: Polyhedron, lab: tuple) -> tuple[frozenset, frozenset]:
    """facet 标签涉及的 A、B 顶点下标集。"""
    kind, af, bf = lab
    sa = frozenset(A.faces[af[1]]) if af[0] == "face" else frozenset(af[1:])
    sb = frozenset(B.faces[bf[1]]) if bf[0] == "face" else frozenset(bf[1:])
    return sa, sb


def facet_vote3(A: Polyhedron, B: Polyhedron, facets: set[tuple], hull: Polyhedron,
                diffs: list[Vec3]) -> tuple[int, int, int, int, list[tuple]]:
    """票二：返回 (facet_global, facet_degenerate, facet_ambiguous, facet_local_dropped, 对称差)。见模块文档。

    标签与凸包 facet 的配对是**组合的**（M0.3）：标签涉及的 A、B 顶点集分别包含于该 facet 的两个支撑集，且标签
    种类与支撑集维数一致（VF ↔ (0,2)、FV ↔ (2,0)、EE ↔ (1,1)）。旧版按法向夹角 ≤ 1e-7 配对。
    凸包侧在噪声内说不清的 facet（`_hull_facets` 的 ambiguous）不进对称差，落在它支撑集里的局部标签也不计
    （facet_local_dropped）——与二维 g0 的 ambiguous_facets 同一做法：分辨率以下的格子只声明"分辨不了"，不装作一致或不一致。"""
    _, fl, area_tol = _gate_scales(A, B, diffs)
    dims = {"VF": (0, 2), "FV": (2, 0), "EE": (1, 1)}

    def key(n: Vec3) -> tuple:
        return tuple(round(c, 7) + 0.0 for c in n)

    strict: list[tuple[Vec3, int, int, frozenset, frozenset]] = []
    amb: list[tuple[frozenset, frozenset]] = []
    deg: list[tuple[Vec3, frozenset, frozenset]] = []
    diff: list[tuple] = []
    n_deg = 0
    for n, da, db, ok, ia, ib, seed in _hull_facets(A, B, diffs, hull, fl, area_tol):
        if seed is not None:
            amb.append(seed)                                    # 说不清：按宽带种子集丢标签（整个不确定区都不计）
        elif not ok or (da, db) not in ((0, 2), (2, 0), (1, 1), (1, 2), (2, 1), (2, 2)):
            # 说不清优先于异常（G6 第三轮 major：已标 ambiguous、但紧带支撑集退化成 (0,0)/(1,0) 的 facet 曾被报成 hull_anomaly）
            diff.append(("hull_anomaly", key(n), da, db))
        elif (da, db) in ((0, 2), (2, 0), (1, 1)):
            strict.append((n, da, db, ia, ib))
        else:
            n_deg += 1
            deg.append((n, ia, ib))

    def label_noise(lab: tuple) -> float:
        """局部标签自己的法向噪声：VF 用 B 面、FV 用 A 面、EE 用两条棱的方向噪声之和。"""
        kind, af, bf = lab
        if kind == "VF":
            return B.face_noise(bf[1])
        if kind == "FV":
            return A.face_noise(af[1])
        return A.edge_noise((af[1], af[2])) + B.edge_noise((bf[1], bf[2]))

    matched = [False] * len(strict)
    n_dropped = 0
    for lab in sorted(facets):
        sa, sb = _label_sets(A, B, lab)
        if any(sa <= ia and sb <= ib for ia, ib in amb):
            n_dropped += 1
            continue
        j = next((j for j, (_, da, db, ia, ib) in enumerate(strict)
                  if (da, db) == dims[lab[0]] and sa <= ia and sb <= ib), None)
        if j is None:
            # 严格标签落进某个**退化** facet 的支撑集、且标签法向与它的夹角在标签自己的噪声之内：局部侧按它自己的
            # 噪声分不清这个 facet 与那个退化 facet（两条 EE facet 法向只差 2e-9 rad、棱方向噪声 2e-8），不是不一致
            nl = facet_normal3(A, B, lab)
            if any(sa <= ia and sb <= ib and angle_between(nl, n) <= label_noise(lab) for n, ia, ib in deg):
                n_dropped += 1
                continue
            diff.append(("local_only", lab))
        elif matched[j]:
            diff.append(("duplicate", lab))
        else:
            matched[j] = True
    for j, (m, da, db, _, _) in enumerate(strict):
        if not matched[j]:
            diff.append(("hull_only", key(m), da, db))
    return len(strict), n_deg, len(amb), n_dropped, sorted(diff)


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


def _match(P: list[Vec3], Q: list[Vec3], tol: float) -> tuple[list[Vec3], list[Vec3]]:
    """两点集按距离 ≤ tol 贪心一一配对，返回两侧各自剩余的点（点集对称差）。"""
    free = list(Q)
    miss: list[Vec3] = []
    for p in P:
        j = next((j for j, q in enumerate(free) if norm(sub(p, q)) <= tol), None)
        if j is None:
            miss.append(p)
        else:
            free.pop(j)
    return miss, free


def _unmatched(P: list[Vec3], Q: list[Vec3], tol: float) -> int:
    a, b = _match(P, Q, tol)
    return len(a) + len(b)


def _vertex_height(hull: Polyhedron, v: Vec3, tol: float) -> float:
    """凸包顶点 v 相对**其余顶点**的凸包的高度（去掉它重建、量它到新凸包各面的最大有符号距离）。
    低于分辨率的顶点是真极点但特征低于容差，凸包保不保留它只取决于加点顺序——票三对这种顶点记"说不清"。"""
    others = [p for p in hull.verts if p != v]
    if len(others) < 4:
        return float("inf")
    try:
        H = convex_hull_3d(others, tol=tol)
    except ValueError:
        return float("inf")
    return max(dot(H.face_normal(fi), sub(v, H.verts[H.faces[fi][0]])) for fi in range(len(H.faces)))


def g0_convex3(A: Polyhedron, B: Polyhedron, *, samples: int = 400, seed: int = 0,
               tol: float = 1e-12, band: float = 1e-7) -> G0Report3:
    """凸块 G0 三票。tol（票一暴力谓词的边界带、凸包的相对容差）与 band（票一成员谓词的跳过带）
    都是**相对** E 的尺度 L 的（见模块文档"尺度"）；局部法锥规则的 tol 是角度，原样传给 covers3。"""
    rng = random.Random(seed)
    rep = G0Report3()
    facets = local_facets3(A, B, tol)
    rep.facet_local = len(facets)
    # 票三：E 顶点集 = conv{b − a} 的顶点集（Quickhull 不把容差内的共面/共线点收作顶点）
    diffs = [sub(b, a) for a in A.verts for b in B.verts]
    L, fl, area_tol = _gate_scales(A, B, diffs)
    ptol = max(1e-9 * L, fl)
    # 凸包用细容差、且**不许**自适应放大越过门的分辨率（放大会静默抹平真特征，G6 第二轮 major）
    hull = convex_hull_3d(diffs, tol=max(tol, fl / L), max_tol=max(tol, ptol / L))
    hv = _dedup_points(list(hull.verts), ptol)
    # 票三：由**局部锥相交规则**判定为 E 顶点的 (a,b) 对，其差点集必须等于 hull 顶点集。
    # 这条检验只用棱方向与坐标，不经面法向、不经任何合并规则，故对"整体符号错"不盲。
    # 三态（M0.3，G6 第三轮 major）：锥相交裕度 |p| > 噪声 ⇒ E 顶点；噪声/16 < |p| ≤ 噪声 ⇒ 说不清——这组坐标的精度下
    # 既不能说它是、也不能说它不是（针底 1.7 mm 的棱在 1e3 处噪声 5e-9 rad，而真 E 顶点的裕度 1e-9），对应的凸包顶点
    # 两边都不计并如实报出；旧版一刀切成"不是"，凸包侧却按长度容差保留它，报成失配。
    from .covers3 import cone_intersection_margin
    ev_raw: list[Vec3] = []
    amb_raw: list[Vec3] = []
    for ia in range(len(A.verts)):
        for ib in range(len(B.verts)):
            dist, noise = cone_intersection_margin(A, ia, B, ib)
            thr = max(tol, 1e-12, noise)
            if dist > thr:
                ev_raw.append(sub(B.verts[ib], A.verts[ia]))
            elif dist > thr / 16.0:
                amb_raw.append(sub(B.verts[ib], A.verts[ia]))
    mtol = max(1e-7 * L, ptol)
    ev = _dedup_points(ev_raw, ptol)
    amb = [a for a in _dedup_points(amb_raw, ptol) if not any(norm(sub(a, e)) <= mtol for e in ev)]
    hv_clear = [h for h in hv if not any(norm(sub(h, a)) <= mtol for a in amb)]
    miss_h, miss_e = _match(hv_clear, ev, mtol)
    # 凸包侧的"说不清"：没配上的凸包顶点若相对其余顶点凸包的高度 ≤ 4·ptol（特征低于分辨率；是真极点，但凸包保不保留它
    # 只取决于加点顺序），两边都不计
    low = [h for h in miss_h if _vertex_height(hull, h, max(tol, fl / L)) <= 4.0 * ptol]
    hv_clear = [h for h in hv_clear if h not in low]
    rep.hull_vertices, rep.e_vertices = len(hv_clear), len(ev)
    rep.e_vertices_ambiguous = len(amb) + len(low)
    rep.hull_vertex_mismatch = len(miss_h) - len(low) + len(miss_e)
    # 票二：严格 facet 集合（定向法向）== conv{b − a} 上的严格 facet 集合
    (rep.facet_global, rep.facet_degenerate, rep.facet_ambiguous, rep.facet_local_dropped,
     rep.facet_symmetric_diff) = facet_vote3(A, B, facets, hull, diffs)
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

    容差（纪律 F，M0.3）：tol 是盖枚举的**角度**容差（无量纲）；atol 是**相对** L 的距离判据：
    |盖距离 − 真值| > atol·max(L, 真值) + c·eps·C 即失败（L = 两体 AABB 对角线之大者，C = 坐标量级）；贯入预筛带
    1e-12·L。旧版是绝对的 atol·max(1, 真值) 与 1e-12：同一个无量纲误差在 s = 1 报红、s = 1e-3 放行（G6 第二轮 minor）。
    """
    from .covers3 import enumerate_covers3
    rng = random.Random(seed)
    rep = DistanceReport3()
    L = max(A.metrics()[1], B.metrics()[1])
    drawn = 0
    while drawn < samples:
        v = (rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0))
        nv = norm(v)
        if nv > 1.0 or nv == 0.0:
            continue
        drawn += 1
        x = tuple(base[i] + radius * v[i] for i in range(3))
        At = A.translated(x)
        if polyhedra_overlap(At, B, 1e-12 * L) != -1:
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
        if err > atol * max(L, truth) + noise_floor(max(At.metrics()[0], B.metrics()[0])):
            rep.failures.append((x, got, truth))
    return rep
