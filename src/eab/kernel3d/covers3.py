"""三维接触盖：∂E(A,B) 的语义化分解。

记号与二维版一致：**B 固定，A 平移，参考点取自 A**，E(A,B) = a0 + (B ⊕ (−A))。

盖类型（命题 4 的三维分类，一般位置下）：
  facet（二维面）  VF  A 的顶点 × B 的面
                   FV  A 的面   × B 的顶点
                   EE  交叉棱-棱（两棱方向不平行）
  edge（一维）     VE3 A 的顶点 × B 的棱 ／ EV3 A 的棱 × B 的顶点
  vertex（零维）   VV3 A 的顶点 × B 的顶点
  退化            FF（平行贴面）、FE（棱平行于面）、EEP（平行棱-棱）

有效性 = **局部**法锥条件（命题 5）：闭条件成立即给出盖，相对内部是否严格成立记在 `strict`
字段——枚举**不按 strict 过滤**（边界态盖是 FF/FE/EEP 退化族的唯一表达）。局部化的两个理由：
(1) 与石根华的"角"概念一致；(2) Phase 3 的凹块可以沿用同一实现——反射顶点/凹棱的局部锥为空，
自动被排除。凸成员谓词 `membership_convex3` 另用 E 的全部支撑半空间，不依赖一般位置。

法锥的表示与判据（这是三维版与二维版唯一实质不同的地方）：
  顶点 v：N(v) = {d : d·e_i ≤ 0, e_i 为 v 的所有入射棱方向}；relint ⟺ 全部严格 <0。
  棱 e：  N(e) = {d ⊥ t_e} ∩ {两相邻面法向张成的楔}；relint ⟺ 严格在两法向之间（要求凸二面角）。
  面 f：  N(f) = 外法向单条射线。
"""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2

from .geom3 import (Polyhedron, Vec3, add, angle_between, cross, dot, mul, neg, norm,
                    point_in_face_polygon, sub, unit)


@dataclass(slots=True)
class Cover3:
    kind: str                     # VF | FV | EE | VE3 | EV3 | VV3 | FF | FE | EEP
    a_feature: tuple[str, ...]    # ("vertex", i) | ("face", i) | ("edge", i, j)
    b_feature: tuple[str, ...]
    normal: Vec3 | None           # B → A 的分离方向（单位）
    gap: float                    # 沿 normal 的有符号间隙（>0 分离）
    point_a: Vec3 | None          # A 侧代表点
    point_b: Vec3 | None          # B 侧代表点
    params: tuple[float, ...]     # VF/FV: 面内重心参数留空；EE: (s, t) 两棱参数
    area: float | None            # 代表面积（VF/FV 取面面积；EE 为 None）
    strict: bool                  # 法锥相对内部条件严格成立
    in_extent: bool               # 投影/最近点落在面内或段内

    def label(self) -> tuple:
        return (self.kind, self.a_feature, self.b_feature)


# ------------------------------------------------------------------ 法锥判据

def vertex_cone_contains(P: Polyhedron, vi: int, d: Vec3, tol: float = 0.0) -> int:
    """d 相对顶点 vi 的局部法锥：1 严格内部 / 0 边界 / -1 外部。

    判据 d·e_i ≤ 0（e_i 为入射棱单位方向）：全严格则在相对内部。反射顶点的锥自动为空或退化。
    """
    dirs = P.vertex_edge_dirs(vi)
    if not dirs:
        return -1
    worst = max(dot(d, e) for e in dirs)
    if worst < -tol:
        return 1
    if worst <= tol:
        return 0
    return -1


def edge_arc_contains(P: Polyhedron, e: tuple[int, int], d: Vec3, tol: float = 0.0) -> int:
    """d 相对棱 e 的局部法锥（两相邻面法向之间的球面弧）：1 严格内 / 0 边界 / -1 外。

    要求 d ⊥ t_e（容差内），且 d 严格落在两法向张成的凸楔中；凹二面角（反射棱）返回 -1。
    """
    fs = P.edge_faces(e)
    if len(fs) != 2:
        return -1
    if P.dihedral_turn(e) <= tol:          # 平棱或凹棱：弧退化/为空
        return -1
    t = P.edge_dir(e)
    if abs(dot(d, t)) > tol + 1e-12:
        return -1
    n1, n2 = P.face_normal(fs[0]), P.face_normal(fs[1])
    # 在垂直于 t 的平面内比较极角：d 必须严格在 n1 与 n2 之间（走凸的那一侧）
    w = angle_between(n1, n2)
    a1 = angle_between(n1, d)
    a2 = angle_between(n2, d)
    if a1 + a2 <= w + tol + 1e-12:
        if a1 > tol and a2 > tol:
            return 1
        return 0
    return -1


def cone_constraints(A: Polyhedron, ia: int, B: Polyhedron, ib: int) -> list[Vec3]:
    """N_B(b) ∩ N_{−A}(−a) 的约束法向集 g：该锥 = {d : d·g ≤ 0, ∀g}。

    N_B(b) = {d : d·e_i ≤ 0}（e_i 为 B 在 ib 的入射棱方向）；
    N_{−A}(−a) = {d : d·(−f_j) ≤ 0}（f_j 为 A 在 ia 的入射棱方向，因 −A 的棱方向取反）。
    """
    return [*B.vertex_edge_dirs(ib), *(neg(f) for f in A.vertex_edge_dirs(ia))]


def _closest_point_on_segment(a: Vec3, b: Vec3) -> Vec3:
    d = sub(b, a)
    dd = dot(d, d)
    if dd <= 0.0:
        return a
    t = -dot(a, d) / dd
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return add(a, mul(d, t))


def _closest_point_on_triangle(a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    """原点到三角 abc 的最近点（含退化情形回退到边）。"""
    n = cross(sub(b, a), sub(c, a))
    nn = dot(n, n)
    if nn <= 1e-300:
        best = _closest_point_on_segment(a, b)
        for cand in (_closest_point_on_segment(b, c), _closest_point_on_segment(a, c)):
            if dot(cand, cand) < dot(best, best):
                best = cand
        return best
    # 原点在三角平面上的投影
    p = mul(n, dot(a, n) / nn)
    u = dot(cross(sub(b, p), sub(c, p)), n)
    v = dot(cross(sub(c, p), sub(a, p)), n)
    w = dot(cross(sub(a, p), sub(b, p)), n)
    if u >= 0.0 and v >= 0.0 and w >= 0.0:
        return p
    best = _closest_point_on_segment(a, b)
    for cand in (_closest_point_on_segment(b, c), _closest_point_on_segment(a, c)):
        if dot(cand, cand) < dot(best, best):
            best = cand
    return best


def closest_point_of_convex_hull_to_origin(pts: list[Vec3]) -> Vec3:
    """原点到 conv(pts) 的最近点（3D，点数少时枚举单形；原点在内则返回零向量）。

    依据：多胞形上离原点最近的点落在某个 ≤2 维面的相对内部，即 ≤3 个点的凸包上；
    若原点落在某个四点单形内部，则距离为 0。
    """
    n = len(pts)
    if n == 0:
        raise ValueError("empty point set")
    # 四点含原点？（有符号体积同号）
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                for l in range(k + 1, n):
                    a, b, c, d = pts[i], pts[j], pts[k], pts[l]
                    def vol(p, q, r, s):
                        return dot(sub(q, p), cross(sub(r, p), sub(s, p)))
                    v0 = vol(a, b, c, d)
                    if abs(v0) <= 1e-300:
                        continue
                    o = (0.0, 0.0, 0.0)
                    s1 = vol(o, b, c, d) / v0
                    s2 = vol(a, o, c, d) / v0
                    s3 = vol(a, b, o, d) / v0
                    s4 = vol(a, b, c, o) / v0
                    if s1 >= 0.0 and s2 >= 0.0 and s3 >= 0.0 and s4 >= 0.0:
                        return (0.0, 0.0, 0.0)
    best = pts[0]
    bd = dot(best, best)
    for i in range(n):
        for j in range(i + 1, n):
            cand = _closest_point_on_segment(pts[i], pts[j])
            d2 = dot(cand, cand)
            if d2 < bd:
                best, bd = cand, d2
            for k in range(j + 1, n):
                cand = _closest_point_on_triangle(pts[i], pts[j], pts[k])
                d2 = dot(cand, cand)
                if d2 < bd:
                    best, bd = cand, d2
    for p in pts:
        d2 = dot(p, p)
        if d2 < bd:
            best, bd = p, d2
    return best


def cone_relint_direction(g: list[Vec3], tol: float = 1e-12) -> Vec3 | None:
    """在 {d : d·g_k ≤ 0} 的**相对内部**里找一个方向；空（或降维）则返回 None。

    严格判据（Gordan 定理）：∃d 使全部 d·g_k < 0 ⟺ 原点 ∉ conv{g_k}。且最优方向为
    −unit(p)，p = 原点到 conv{g_k} 的最近点；此时 max_k d·g_k = −|p|。
    启发式候选集（负平均、极射线平均等）会漏判——2026-09-18 实测 43 个 E 顶点只找到 31 个。
    """
    if not g:
        return None
    gs = [unit(x) for x in g if norm(x) > 1e-300]
    if not gs:
        return None
    p = closest_point_of_convex_hull_to_origin(gs)
    dist = norm(p)
    if dist <= tol:
        return None
    return unit(neg(p))


def cones_intersect_relint(A: Polyhedron, ia: int, B: Polyhedron, ib: int, tol: float = 1e-12) -> bool:
    """(ia, ib) 是否给出 ∂E 的一个顶点（命题 4 的零维盖条件）。"""
    return cone_relint_direction(cone_constraints(A, ia, B, ib), tol) is not None


def _project_on_face(p: Vec3, P: Polyhedron, fi: int) -> tuple[Vec3, float]:
    n = P.face_normal(fi)
    o = P.verts[P.faces[fi][0]]
    g = dot(n, sub(p, o))
    return add(p, mul(n, -g)), g


# ------------------------------------------------------------------ 三类 facet 盖
#
# in_extent（投影落在面多边形内）一律用 geom3.point_in_face_polygon：面可以非凸
# （merge_coplanar 归并出的十边形侧面、L 块顶底面）。此前这里自带一份半平面核判据，
# 只对凸面正确（2026-09-21 审查 C7：L 块臂上的 VF 盖 in_extent=False 被丢）。

def vf_cover(A: Polyhedron, ia: int, B: Polyhedron, fb: int, tol: float = 0.0) -> Cover3 | None:
    """A 的顶点 ia 对 B 的面 fb。有效 ⟺ −n_f ∈ relint N_A(ia)。"""
    nB = B.face_normal(fb)
    side = vertex_cone_contains(A, ia, neg(nB), tol)
    if side < 0:
        return None
    a = A.verts[ia]
    proj, g = _project_on_face(a, B, fb)
    return Cover3("VF", ("vertex", ia), ("face", fb), nB, g, a, proj, (),
                  B.face_area(fb), side == 1, point_in_face_polygon(proj, B, fb, tol))


def fv_cover(A: Polyhedron, fa: int, B: Polyhedron, ib: int, tol: float = 0.0) -> Cover3 | None:
    """A 的面 fa 对 B 的顶点 ib。有效 ⟺ −n_A(fa) ∈ relint N_B(ib)。分离法向 = −n_A。"""
    nA = A.face_normal(fa)
    side = vertex_cone_contains(B, ib, neg(nA), tol)
    if side < 0:
        return None
    b = B.verts[ib]
    proj, g = _project_on_face(b, A, fa)     # g = n_A·(b − a0)：>0 表示 B 顶点在 A 面外侧
    return Cover3("FV", ("face", fa), ("vertex", ib), neg(nA), g, proj, b, (),
                  A.face_area(fa), side == 1, point_in_face_polygon(proj, A, fa, tol))


def _closest_params(p1: Vec3, d1: Vec3, p2: Vec3, d2: Vec3) -> tuple[float, float] | None:
    """两直线最近点参数（d1、d2 为方向向量，非单位亦可）；平行返回 None。"""
    a, b, c = dot(d1, d1), dot(d1, d2), dot(d2, d2)
    den = a * c - b * b
    if abs(den) < 1e-300:
        return None
    w = sub(p1, p2)
    d = dot(d1, w)
    e = dot(d2, w)
    s = (b * e - c * d) / den
    t = (a * e - b * d) / den
    return s, t


def ee_cover(A: Polyhedron, ea: tuple[int, int], B: Polyhedron, eb: tuple[int, int],
             tol: float = 0.0) -> Cover3 | None:
    """A 的棱 ea 对 B 的棱 eb（交叉）。候选法向 ±unit(t_B × t_A)，取落在两条弧相对内部者。"""
    tA, tB = A.edge_dir(ea), B.edge_dir(eb)
    c = cross(tB, tA)
    if norm(c) <= tol + 1e-12:               # 平行棱：退化盖，另行处理
        return None
    n = unit(c)
    best: Cover3 | None = None
    for cand in (n, neg(n)):
        sb = edge_arc_contains(B, eb, cand, tol)
        sa = edge_arc_contains(A, ea, neg(cand), tol)
        if sb < 0 or sa < 0:
            continue
        pa0, pb0 = A.verts[ea[0]], B.verts[eb[0]]
        dA = sub(A.verts[ea[1]], pa0)
        dB = sub(B.verts[eb[1]], pb0)
        pr = _closest_params(pa0, dA, pb0, dB)
        if pr is None:
            continue
        s, t = pr
        qa = add(pa0, mul(dA, s))
        qb = add(pb0, mul(dB, t))
        g = dot(cand, sub(qa, qb))
        in_ext = (-tol <= s <= 1.0 + tol) and (-tol <= t <= 1.0 + tol)
        cov = Cover3("EE", ("edge", ea[0], ea[1]), ("edge", eb[0], eb[1]), cand, g, qa, qb,
                     (s, t), None, sb == 1 and sa == 1, in_ext)
        if best is None or abs(cov.gap) < abs(best.gap):
            best = cov
    return best


# ------------------------------------------------------------------ 低维与退化盖

def ve3_cover(A: Polyhedron, ia: int, B: Polyhedron, eb: tuple[int, int], tol: float = 0.0) -> Cover3 | None:
    """A 的顶点 × B 的棱 → ∂E 的棱（一维盖）。有效 ⟺ N_B(eb) 的弧与 −N_A(ia) 的锥相交（闭）。

    实现上取分离方向 = 顶点到棱的最短向量（若最近点在段内），再验它同时落在两个锥里。
    strict = 两个判据**都**严格（相对内部）；任一为边界（0）即 False——与 ee_cover 同一口径
    （2026-09-21 审查 C10：此前写死 True）。边界态盖**照样返回**：平行棱-棱最近对（EEP 退化）
    只能由它表达，见 enumerate_covers3。
    """
    a = A.verts[ia]
    p0 = B.verts[eb[0]]
    d = sub(B.verts[eb[1]], p0)
    s = dot(sub(a, p0), d) / dot(d, d)
    q = add(p0, mul(d, s))
    v = sub(a, q)
    if norm(v) <= tol:
        return None
    n = unit(v)
    sb = edge_arc_contains(B, eb, n, tol)
    sa = vertex_cone_contains(A, ia, neg(n), tol)
    if sb < 0 or sa < 0:
        return None
    return Cover3("VE3", ("vertex", ia), ("edge", eb[0], eb[1]), n, norm(v), a, q, (s,), None,
                  sb == 1 and sa == 1, -tol <= s <= 1.0 + tol)


def ev3_cover(A: Polyhedron, ea: tuple[int, int], B: Polyhedron, ib: int, tol: float = 0.0) -> Cover3 | None:
    """A 的棱 × B 的顶点 → ∂E 的棱。strict 口径同 ve3_cover。"""
    b = B.verts[ib]
    p0 = A.verts[ea[0]]
    d = sub(A.verts[ea[1]], p0)
    s = dot(sub(b, p0), d) / dot(d, d)
    q = add(p0, mul(d, s))
    v = sub(q, b)
    if norm(v) <= tol:
        return None
    n = unit(v)
    sb = vertex_cone_contains(B, ib, n, tol)
    sa = edge_arc_contains(A, ea, neg(n), tol)
    if sb < 0 or sa < 0:
        return None
    return Cover3("EV3", ("edge", ea[0], ea[1]), ("vertex", ib), n, norm(v), q, b, (s,), None,
                  sb == 1 and sa == 1, -tol <= s <= 1.0 + tol)


def vv3_cover(A: Polyhedron, ia: int, B: Polyhedron, ib: int, tol: float = 0.0) -> Cover3 | None:
    """A 的顶点 × B 的顶点 → ∂E 的顶点（零维盖，法向集值）。

    两个判据必须分开（2026-09-18 实测混为一谈会让 E 顶点数恒为 0）：
      strict    = 两锥**相对内部相交** ⟺ 这对顶点确实给出 ∂E 的一个顶点（命题 4）；
      in_extent = 分离方向 a − b 落在交锥内 ⟺ 参考点到 E 的最近特征正是这个顶点（活跃）。
    """
    a, b = A.verts[ia], B.verts[ib]
    is_vertex = cones_intersect_relint(A, ia, B, ib, max(tol, 1e-12))
    if not is_vertex:
        return None
    v = sub(a, b)
    if norm(v) <= tol:
        return Cover3("VV3", ("vertex", ia), ("vertex", ib), None, 0.0, a, b, (), None, True, True)
    n = unit(v)
    active = (vertex_cone_contains(B, ib, n, tol) >= 0 and vertex_cone_contains(A, ia, neg(n), tol) >= 0)
    return Cover3("VV3", ("vertex", ia), ("vertex", ib), n, norm(v), a, b, (), None, True, active)


# ------------------------------------------------------------------ 枚举

def enumerate_covers3(A: Polyhedron, B: Polyhedron, *, window: float, tol: float = 0.0,
                      require_in_extent: bool = True, include_low_dim: bool = True) -> list[Cover3]:
    """当前位形下所有有效且在距离窗口内的三维盖。

    有效 = 法锥**闭**条件成立（判据 ≥ 0）；strict 只是盖上的一个字段，**任何一类盖都不按
    strict 过滤**。低维盖尤其不能过滤（2026-09-21 审查 C10 实测）：平行棱-棱最近对
    （EEP 退化，ee_cover 对平行棱返回 None）只由边界态 VE3/EV3 表达，一旦按 strict 过滤，
    margin.body_distance 的距离完备性就丢（tests/test_margin.py 三例红）。
    """
    out: list[Cover3] = []
    for ia in range(len(A.verts)):
        for fb in range(len(B.faces)):
            c = vf_cover(A, ia, B, fb, tol)
            if c is not None and abs(c.gap) <= window and (c.in_extent or not require_in_extent):
                out.append(c)
    for fa in range(len(A.faces)):
        for ib in range(len(B.verts)):
            c = fv_cover(A, fa, B, ib, tol)
            if c is not None and abs(c.gap) <= window and (c.in_extent or not require_in_extent):
                out.append(c)
    for ea in A.edges():
        for eb in B.edges():
            c = ee_cover(A, ea, B, eb, tol)
            if c is not None and abs(c.gap) <= window and (c.in_extent or not require_in_extent):
                out.append(c)
    if include_low_dim:
        for ia in range(len(A.verts)):
            for eb in B.edges():
                c = ve3_cover(A, ia, B, eb, tol)
                if c is not None and abs(c.gap) <= window and (c.in_extent or not require_in_extent):
                    out.append(c)
        for ea in A.edges():
            for ib in range(len(B.verts)):
                c = ev3_cover(A, ea, B, ib, tol)
                if c is not None and abs(c.gap) <= window and (c.in_extent or not require_in_extent):
                    out.append(c)
        for ia in range(len(A.verts)):
            for ib in range(len(B.verts)):
                c = vv3_cover(A, ia, B, ib, tol)
                if c is not None and c.in_extent and c.gap <= window:
                    out.append(c)
    return out


def local_facets3(A: Polyhedron, B: Polyhedron, tol: float = 0.0) -> set[tuple]:
    """严格有效的 facet 型盖（VF/FV/EE），不设窗口、不限面内——命题 4 的局部规则产物。"""
    out: set[tuple] = set()
    for ia in range(len(A.verts)):
        for fb in range(len(B.faces)):
            c = vf_cover(A, ia, B, fb, tol)
            if c is not None and c.strict:
                out.add(c.label())
    for fa in range(len(A.faces)):
        for ib in range(len(B.verts)):
            c = fv_cover(A, fa, B, ib, tol)
            if c is not None and c.strict:
                out.add(c.label())
    for ea in A.edges():
        for eb in B.edges():
            c = ee_cover(A, ea, B, eb, tol)
            if c is not None and c.strict:
                out.add(c.label())
    return out


def facet_normal3(A: Polyhedron, B: Polyhedron, label: tuple) -> Vec3:
    """facet 标签对应的 E 的**定向外法向**（B → A 的分离方向）。

    VF → n_B(face)；FV → −n_A(face)；EE → ±unit(t_B × t_A)，取落在 B 棱弧里的那一支。
    facet_gap3 与 G0 票二共用它（票二的另一侧不经它，见 g03.g0_convex3）。
    """
    kind, af, bf = label
    if kind == "VF":
        return B.face_normal(bf[1])
    if kind == "FV":
        return neg(A.face_normal(af[1]))
    if kind == "EE":
        ea = (af[1], af[2])
        eb = (bf[1], bf[2])
        n = unit(cross(B.edge_dir(eb), A.edge_dir(ea)))
        if edge_arc_contains(B, eb, n, 1e-9) < 0:        # 取与 B 的弧一致的朝向
            n = neg(n)
        return n
    raise ValueError(f"not a facet label: {label}")


def facet_gap3(A: Polyhedron, B: Polyhedron, label: tuple, x: Vec3) -> float:
    """E 的一条 facet 在平移 x 下的有符号间隙（>0 参考点在该 facet 外侧）。"""
    kind, af, bf = label
    n = facet_normal3(A, B, label)
    if kind == "VF":
        return dot(n, sub(add(A.verts[af[1]], x), B.verts[B.faces[bf[1]][0]]))
    if kind == "FV":
        return dot(n, sub(add(A.verts[A.faces[af[1]][0]], x), B.verts[bf[1]]))
    return dot(n, sub(add(A.verts[af[1]], x), B.verts[bf[1]]))           # EE


def support_gaps3(A: Polyhedron, B: Polyhedron, x: Vec3) -> list[float]:
    """E = B ⊕ (−A) 在 A、B **每个面法向**上的支撑半空间间隙（>0 参考点在外侧），与严格性无关。

    B 的面 fb（外法向 n）：取 a* = argmin_a n·a，间隙 n·(a* + x − b_f)；
    A 的面 fa（外法向 m）：E 的法向是 −m，取 b* = argmin_b m·b，间隙 (−m)·(a_f + x − b*)。
    每一条都是 E 的合法支撑半空间（含 E）；FF/FE 退化 facet 的法向恰好都在其中。
    """
    gaps: list[float] = []
    for fb in range(len(B.faces)):
        n = B.face_normal(fb)
        ia = min(range(len(A.verts)), key=lambda i: dot(n, A.verts[i]))
        gaps.append(dot(n, sub(add(A.verts[ia], x), B.verts[B.faces[fb][0]])))
    for fa in range(len(A.faces)):
        m = A.face_normal(fa)
        ib = min(range(len(B.verts)), key=lambda i: dot(m, B.verts[i]))
        gaps.append(dot(neg(m), sub(add(A.verts[A.faces[fa][0]], x), B.verts[ib])))
    return gaps


def membership_convex3(A: Polyhedron, B: Polyhedron, x: Vec3, tol: float = 0.0,
                       facets: set[tuple] | None = None) -> int:
    """参考点相对 E 的位置：1 内部（A+x 与 B 内部相交）/ 0 边界 / -1 外部。A、B 凸，**不要求一般位置**。

    E 的 facet 法向只有三类来源：B 的面法向、−(A 的面法向)、严格交叉棱-棱（命题 4）。
    前两类用 `support_gaps3` 的**全部**支撑半空间覆盖（含 FF/FE 退化 facet），第三类取 facets
    里的 EE 标签；facets 里的 VF/FV 标签也一并取 max（合法标签的间隙与支撑间隙相同，错标签只会
    把答案推向"外部"，于是被票一抓住）。

    2026-09-21 审查 C2（critical）：此前只对 strict facet 取 max——平行面生成的 facet 全被丢，
    四面体 vs 方块在 +x 侧恒判"相交"，两个轴对齐方块对空集取 max 崩溃。
    """
    if facets is None:
        facets = local_facets3(A, B, tol)
    g = max(support_gaps3(A, B, x) + [facet_gap3(A, B, lab, x) for lab in facets])
    if g > tol:
        return -1
    if g < -tol:
        return 1
    return 0
