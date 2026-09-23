"""三维几何原语与暴力多面体谓词（G0 的 oracle）。纯 Python，零依赖。

多面体表示 `Polyhedron`：顶点表 + 面表（每面一个顶点索引环，**从外部看为逆时针**，即右手法则
给出外法向）。允许非凸、允许非三角面（面必须平面且为简单多边形）。

审查（2026-09-18，二维版）的三条教训在此一并落实：
1. 反射/凹的判定用角度（atan2）不用 sin；
2. 面积/体积/质心相对第一个顶点累加，防远偏移抵消；
3. "内点"必须是**保证在内**的点，不能用质心（凹体质心可在体外）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
import math
from math import atan2, hypot, sqrt

Vec3 = tuple[float, float, float]
Face = tuple[int, ...]


def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def neg(a: Vec3) -> Vec3:
    return (-a[0], -a[1], -a[2])


def mul(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a: Vec3) -> float:
    return sqrt(dot(a, a))


def unit(a: Vec3) -> Vec3:
    n = norm(a)
    if n == 0.0:
        raise ZeroDivisionError("unit of zero vector")
    return (a[0] / n, a[1] / n, a[2] / n)


def angle_between(a: Vec3, b: Vec3) -> float:
    """两向量夹角（弧度，[0, π]）。用 atan2(|a×b|, a·b) 而非 acos，小角与近 π 都稳。"""
    c = cross(a, b)
    return atan2(norm(c), dot(a, b))


@dataclass(slots=True)
class Polyhedron:
    verts: list[Vec3]
    faces: list[Face]                                     # 每面顶点索引环，外看 CCW
    _edges: list[tuple[int, int]] | None = field(default=None, repr=False)
    _vf: dict[int, list[int]] | None = field(default=None, repr=False)
    _ef: dict[tuple[int, int], list[int]] | None = field(default=None, repr=False)
    # 每条无向棱在各相邻面里的**遍历方向**：key -> [(face, a, b), ...]，a→b 为该面环里的走向。
    # 二面角的符号完全由它定（闭合且一致朝向的多面体，同一棱在两个面里走向相反）。
    _edir: dict[tuple[int, int], list[tuple[int, int, int]]] | None = field(default=None, repr=False)

    # ---------------- 拓扑 ----------------
    def face_normal(self, fi: int) -> Vec3:
        """面的单位外法向（Newell 法，对非三角面与近退化面都稳）。"""
        f = self.faces[fi]
        n = (0.0, 0.0, 0.0)
        o = self.verts[f[0]]
        k = len(f)
        for i in range(k):
            p = sub(self.verts[f[i]], o)
            q = sub(self.verts[f[(i + 1) % k]], o)
            n = add(n, cross(p, q))
        return unit(n)

    def face_area(self, fi: int) -> float:
        f = self.faces[fi]
        o = self.verts[f[0]]
        n = (0.0, 0.0, 0.0)
        for i in range(len(f)):
            n = add(n, cross(sub(self.verts[f[i]], o), sub(self.verts[f[(i + 1) % len(f)]], o)))
        return 0.5 * norm(n)

    def edges(self) -> list[tuple[int, int]]:
        if self._edges is None:
            self._build_topology()
        assert self._edges is not None
        return self._edges

    def vertex_faces(self, vi: int) -> list[int]:
        if self._vf is None:
            self._build_topology()
        assert self._vf is not None
        return self._vf.get(vi, [])

    def edge_faces(self, e: tuple[int, int]) -> list[int]:
        if self._ef is None:
            self._build_topology()
        assert self._ef is not None
        return self._ef.get((min(e), max(e)), [])

    def _build_topology(self) -> None:
        vf: dict[int, list[int]] = {}
        ef: dict[tuple[int, int], list[int]] = {}
        edir: dict[tuple[int, int], list[tuple[int, int, int]]] = {}
        for fi, f in enumerate(self.faces):
            k = len(f)
            for i in range(k):
                a, b = f[i], f[(i + 1) % k]
                vf.setdefault(a, []).append(fi)
                key = (min(a, b), max(a, b))
                ef.setdefault(key, []).append(fi)
                edir.setdefault(key, []).append((fi, a, b))
        self._vf = vf
        self._ef = ef
        self._edir = edir
        self._edges = sorted(ef)

    def edge_traversals(self, e: tuple[int, int]) -> list[tuple[int, int, int]]:
        if self._edir is None:
            self._build_topology()
        assert self._edir is not None
        return self._edir.get((min(e), max(e)), [])

    def vertex_edge_dirs(self, vi: int) -> list[Vec3]:
        """顶点 vi 的**入射棱方向**（由 vi 指向邻点，单位化）。局部法锥由它们定义。"""
        out: list[Vec3] = []
        seen: set[int] = set()
        for e in self.edges():
            if vi in e:
                other = e[1] if e[0] == vi else e[0]
                if other in seen:
                    continue
                seen.add(other)
                d = sub(self.verts[other], self.verts[vi])
                if norm(d) > 0.0:
                    out.append(unit(d))
        return out

    def edge_dir(self, e: tuple[int, int]) -> Vec3:
        return unit(sub(self.verts[e[1]], self.verts[e[0]]))

    def dihedral_turn(self, e: tuple[int, int]) -> float:
        """棱 e 的二面转角（弧度）：凸棱 >0、平棱 =0、反射（凹）棱 <0。需恰好两个相邻面。

        判据：取棱在第一个面环里的遍历方向 t = a→b，n1 该面外法向，n2 另一面外法向，
        转角 = atan2((n1×n2)·t, n1·n2)。闭合且一致朝向（外看 CCW）的多面体上此式恒正确。

        **不要用"沿两外法向的角平分线探测实体内外"**：凸棱实体占小角、凹棱占大角，
        平分线在两种情形下都指向实体外，区分不了（2026-09-18 实测 L 块凹棱被误判为凸）。
        """
        trav = self.edge_traversals(e)
        if len(trav) != 2:
            raise ValueError(f"edge {e} has {len(trav)} incident face traversals, need 2")
        (f1, a1, b1), (f2, _, _) = trav
        t = unit(sub(self.verts[b1], self.verts[a1]))
        n1, n2 = self.face_normal(f1), self.face_normal(f2)
        return atan2(dot(cross(n1, n2), t), dot(n1, n2))

    # ---------------- 体积与内点 ----------------
    def volume(self) -> float:
        """有符号体积（外看 CCW 的闭合多面体为正）。相对首顶点累加防抵消。"""
        o = self.verts[0]
        v = 0.0
        for fi, f in enumerate(self.faces):
            a = sub(self.verts[f[0]], o)
            for i in range(1, len(f) - 1):
                b = sub(self.verts[f[i]], o)
                c = sub(self.verts[f[i + 1]], o)
                v += dot(a, cross(b, c))
        return v / 6.0

    def centroid(self) -> Vec3:
        """体心。注意：凹多面体的体心可能在体外，**不可**当内点用。"""
        o = self.verts[0]
        vol = 0.0
        acc = (0.0, 0.0, 0.0)
        for f in self.faces:
            a = sub(self.verts[f[0]], o)
            for i in range(1, len(f) - 1):
                b = sub(self.verts[f[i]], o)
                c = sub(self.verts[f[i + 1]], o)
                w = dot(a, cross(b, c))
                vol += w
                acc = add(acc, mul(add(add(a, b), c), w))
        if vol == 0.0:
            n = len(self.verts)
            return (sum(p[0] for p in self.verts) / n, sum(p[1] for p in self.verts) / n,
                    sum(p[2] for p in self.verts) / n)
        return add(o, mul(acc, 1.0 / (4.0 * vol)))

    def interior_point(self) -> Vec3:
        """保证在多面体内部的一点：取各面三角形质心沿内法向微退，取第一个通过内点测试者；
        兜底退回体心（凸体总成立）。"""
        scale = max(1.0, max(norm(sub(p, self.verts[0])) for p in self.verts) or 1.0)
        for fi, f in enumerate(self.faces):
            n = self.face_normal(fi)
            for i in range(1, len(f) - 1):
                tri = (self.verts[f[0]], self.verts[f[i]], self.verts[f[i + 1]])
                g = mul(add(add(tri[0], tri[1]), tri[2]), 1.0 / 3.0)
                for eps in (1e-3, 1e-4, 1e-5, 1e-2, 1e-1):
                    p = add(g, mul(n, -eps * scale))
                    if point_in_polyhedron(p, self, 0.0) == 1:
                        return p
        c = self.centroid()
        if point_in_polyhedron(c, self, 0.0) == 1:
            return c
        raise ValueError("interior_point: failed to find an interior point")

    def aabb(self) -> tuple[Vec3, Vec3]:
        xs = [p[0] for p in self.verts]
        ys = [p[1] for p in self.verts]
        zs = [p[2] for p in self.verts]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    def translated(self, x: Vec3) -> "Polyhedron":
        return Polyhedron([add(p, x) for p in self.verts], list(self.faces))

    def reflected(self) -> "Polyhedron":
        """点反射 p → −p。面环需反向以保持外法向（反射是非保向的）。"""
        return Polyhedron([neg(p) for p in self.verts], [tuple(reversed(f)) for f in self.faces])

    def manifold_issues(self, tol: float = 1e-9) -> list[str]:
        """闭合性与朝向一致性自检。空列表 = 合法的闭合定向流形（外法向朝外）。

        三项：① 每条棱恰好两个面遍历；② 两次遍历方向**相反**（同向 ⇒ 有面绕反）；
        ③ 有符号体积为正（整体朝向朝外）。面绕向错会静默污染所有盖的法向，必须有门。
        """
        issues: list[str] = []
        for e, trav in ((e, self.edge_traversals(e)) for e in self.edges()):
            if len(trav) != 2:
                issues.append(f"edge {e}: {len(trav)} traversals (need 2)")
                continue
            (_, a1, b1), (_, a2, b2) = trav
            if (a1, b1) == (a2, b2):
                issues.append(f"edge {e}: both faces traverse {a1}->{b1} (a face winding is reversed)")
        # 面多边形应平面
        for fi, f in enumerate(self.faces):
            if len(f) < 3:
                issues.append(f"face {fi}: only {len(f)} vertices")
                continue
            n = self.face_normal(fi)
            o = self.verts[f[0]]
            scale = max(norm(sub(self.verts[i], o)) for i in f) or 1.0
            for i in f:
                if abs(dot(n, sub(self.verts[i], o))) > tol * scale:
                    issues.append(f"face {fi}: not planar (vertex {i} off by "
                                  f"{dot(n, sub(self.verts[i], o)):.3g})")
                    break
        v = self.volume()
        if v <= 0.0:
            issues.append(f"signed volume {v:.6g} <= 0 (global orientation is inward)")
        return issues

    def is_convex(self, tol: float = 1e-12) -> bool:
        for e in self.edges():
            if len(self.edge_faces(e)) != 2:
                return False
            if self.dihedral_turn(e) < -tol:
                return False
        return True

    def reflex_edges(self, tol: float = 1e-12) -> list[tuple[int, int]]:
        out = []
        for e in self.edges():
            if len(self.edge_faces(e)) == 2 and self.dihedral_turn(e) < -tol:
                out.append(e)
        return out


# ------------------------------------------------------------------ 面多边形内点（唯一实现）

def _point_segment_distance(x: Vec3, a: Vec3, b: Vec3) -> float:
    d = sub(b, a)
    dd = dot(d, d)
    if dd <= 0.0:
        return norm(sub(x, a))
    t = dot(sub(x, a), d) / dd
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return norm(sub(x, add(a, mul(d, t))))


def face_polygon_locate(x: Vec3, P: Polyhedron, fi: int, tol: float = 0.0) -> int:
    """x 相对面 fi 的**多边形**：1 严格内部（离每条棱段都 > tol）/ 0 边界带（≤ tol）/ -1 外部。

    前提：x 已在（或投影到）该面平面上——调用方负责投影。面可以**非凸**（简单多边形即可）。
    判据：先量 x 到各棱段的三维距离（边界容差语义）；不在边界带则把面环与 x 投影到去掉法向
    主分量的坐标平面（仿射单射，保拓扑），用非零环绕数判内外。

    这是本仓库**唯一**的"点在面内"实现（2026-09-21 审查 C6/C7）：此前五处各写一份，
    半平面核（只对凸面对）与从 f[0] 扇形三角化（三角溢出非凸多边形）两种错法各占一半。
    covers3 的 in_extent 与本模块的暴力谓词（G0 oracle）因此**共用**它——它的独立门见
    tests/test_geom3_face_polygon.py（矩形并集与星形极坐标两个不经本模块的 oracle）。
    """
    f = P.faces[fi]
    V = P.verts
    k = len(f)
    for i in range(k):
        if _point_segment_distance(x, V[f[i]], V[f[(i + 1) % k]]) <= tol:
            return 0
    n = P.face_normal(fi)
    an = (abs(n[0]), abs(n[1]), abs(n[2]))
    ax = 0 if an[0] >= an[1] and an[0] >= an[2] else (1 if an[1] >= an[2] else 2)
    i1, i2 = (ax + 1) % 3, (ax + 2) % 3
    px, py = x[i1], x[i2]
    wn = 0
    for i in range(k):
        a, b = V[f[i]], V[f[(i + 1) % k]]
        ay, by = a[i2], b[i2]
        if ay <= py:
            if by > py and (b[i1] - a[i1]) * (py - ay) - (px - a[i1]) * (by - ay) > 0.0:
                wn += 1
        elif by <= py and (b[i1] - a[i1]) * (py - ay) - (px - a[i1]) * (by - ay) < 0.0:
            wn -= 1
    return 1 if wn != 0 else -1


def point_in_face_polygon(x: Vec3, P: Polyhedron, fi: int, tol: float = 0.0) -> bool:
    """x（已在面平面上）落在面 fi 的多边形内或其 tol 边界带内。见 `face_polygon_locate`。"""
    return face_polygon_locate(x, P, fi, tol) >= 0


# ------------------------------------------------------------------ 点与线段谓词

_RAY_DIRS: list[Vec3] = []


def _ray_directions(n: int = 64) -> list[Vec3]:
    """球面上的确定性方向序列（黄金角螺旋 + 无理数偏置）。

    退化命中（射线正好穿过三角形的边或顶点）会让奇偶计数出错，必须换方向重试；
    5 个固定方向不够——互锁块这类含大量共面/轴对齐特征的几何会把它们全撞掉
    （2026-09-18 实测二分过程中触发）。
    """
    global _RAY_DIRS
    if len(_RAY_DIRS) >= n:
        return _RAY_DIRS[:n]
    ga = 2.39996322972865332          # 黄金角
    out: list[Vec3] = []
    for i in range(n):
        z = 1.0 - 2.0 * (i + 0.5) / n
        r = sqrt(max(0.0, 1.0 - z * z))
        th = ga * i + 0.123456789      # 偏置：避开与坐标面对齐
        out.append(unit((r * math.cos(th), r * math.sin(th), z)))
    _RAY_DIRS = out
    return out


def point_in_polyhedron(p: Vec3, P: Polyhedron, tol: float = 0.0) -> int:
    """1 严格内部 / 0 在边界（容差 tol）/ -1 外部。先测边界，再用射线奇偶。

    射线与每个面**平面**求交，交点用 `face_polygon_locate` 判是否落在面多边形内（非凸面正确）；
    交点落在棱的边界带里（或 t≈0）即退化命中，换方向重试。**不做扇形三角化**——从 f[0] 扇出的
    三角会溢出非凸多边形（2026-09-21 审查 C6：L 块凹口里落在底面平面上的点被判"边界"）。
    """
    normals = [P.face_normal(fi) for fi in range(len(P.faces))]
    # 边界：点到任一面多边形的距离 ≤ tol（先投影到面平面，再判多边形）
    for fi, f in enumerate(P.faces):
        n = normals[fi]
        d0 = dot(n, sub(p, P.verts[f[0]]))
        if abs(d0) <= tol and point_in_face_polygon(add(p, mul(n, -d0)), P, fi, tol):
            return 0
    lo, hi = P.aabb()
    diag = norm(sub(hi, lo)) or 1.0
    eps_edge = 1e-9 * diag           # 射线交点离棱这么近即视为退化命中（相对尺度）
    eps_t = 1e-12 * diag             # 起点离面平面这么近即视为"就在表面上"
    for fi, f in enumerate(P.faces):
        n = normals[fi]
        d0 = dot(n, sub(p, P.verts[f[0]]))
        if abs(d0) <= eps_t and point_in_face_polygon(add(p, mul(n, -d0)), P, fi, eps_edge):
            # 起点在射线法的分辨率之下就落在表面上：任何方向都会 t≈0 命中，奇偶无从谈起。
            # 返回"边界"是正确答案（2026-09-18 实测：偏移 3.3e-10 > tol=1e-12 的点）。
            return 0
    for d in _ray_directions():
        crossings = 0
        degenerate = False
        for fi, f in enumerate(P.faces):
            n = normals[fi]
            den = dot(n, d)
            if den == 0.0:
                continue                                  # 射线平行于面平面：不相交
            t = dot(n, sub(P.verts[f[0]], p)) / den
            if t < -eps_t:
                continue
            loc = face_polygon_locate(add(p, mul(d, t)), P, fi, eps_edge)
            if loc < 0:
                continue
            if loc == 0 or t <= eps_t:
                degenerate = True
                break
            crossings += 1
        if not degenerate:
            return 1 if crossings % 2 == 1 else -1
    # 所有方向都退化：起点贴着棱/顶点（距离 < eps_edge），同样只能答"边界"。
    return 0


def segment_crosses_face(p: Vec3, q: Vec3, P: Polyhedron, fi: int, tol: float = 0.0) -> bool:
    """线段 pq 的**内部**与面 fi 的**内部**真相交（不含端点触碰、不含共面、不含穿过棱的 tol 带）。"""
    n = P.face_normal(fi)
    o = P.verts[P.faces[fi][0]]
    dp, dq = dot(n, sub(p, o)), dot(n, sub(q, o))
    L = norm(sub(q, p))
    if L == 0.0:
        return False
    if not ((dp > tol and dq < -tol) or (dp < -tol and dq > tol)):
        return False
    t = dp / (dp - dq)
    x = add(p, mul(sub(q, p), t))
    return face_polygon_locate(x, P, fi, tol) == 1


def _inward_vertex_direction(P: Polyhedron, vi: int) -> Vec3 | None:
    """顶点 vi 处关联面外法向之和的反方向（凸角指向体内；反射角可能指向体外——调用方必须复验）。"""
    s = (0.0, 0.0, 0.0)
    for fi in P.vertex_faces(vi):
        s = add(s, P.face_normal(fi))
    if norm(s) <= 1e-12:
        return None
    return neg(unit(s))


def polyhedra_overlap(A: Polyhedron, B: Polyhedron, tol: float = 0.0) -> int:
    """暴力谓词：1 内部相交 / 0 仅边界接触 / -1 分离。任意（含非凸）闭合多面体。

    证人搜索按代价递增：AABB 早退 → 顶点在内 → 棱穿面 → 各自内点在对方内 →
    **相触顶点沿内法向微推** → AABB 交集里的网格与随机采样。**全程不用体心**（凹体体心可在体外）。

    · 网格一步是必需的：两个方块共享 y、z 范围时前四步全空，但交集体积为正（2026-09-18 实测）。
    · 微推一步也是必需的（2026-09-21 审查 C9）：L 块凹槽里咬进一层 e 厚的薄片、z 范围重合时，
      每个顶点都落在对方面平面上、没有棱严格穿面，网格撒在 ~2×2×1 的 AABB 交集里而真交集只有
      e×2×1——e ≲ 0.01 就漏判成"相触"。相触顶点沿关联面外法向和的反方向推进 ε·diam，
      若落在两体**严格**内部即是证人。它只可能修正假阴性：证人点经 point_in_polyhedron 复验。
    """
    (ax0, ay0, az0), (ax1, ay1, az1) = A.aabb()
    (bx0, by0, bz0), (bx1, by1, bz1) = B.aabb()
    lo = (max(ax0, bx0), max(ay0, by0), max(az0, bz0))
    hi = (min(ax1, bx1), min(ay1, by1), min(az1, bz1))
    if any(hi[i] < lo[i] - tol for i in range(3)):
        return -1

    touching = False
    touch_verts: list[tuple[Polyhedron, Polyhedron, list[int]]] = []
    for P, Q in ((A, B), (B, A)):
        tv: list[int] = []
        for vi, p in enumerate(P.verts):
            s = point_in_polyhedron(p, Q, tol)
            if s == 1:
                return 1
            if s == 0:
                touching = True
                tv.append(vi)
        touch_verts.append((P, Q, tv))
        for e in P.edges():
            for fi in range(len(Q.faces)):
                if segment_crosses_face(P.verts[e[0]], P.verts[e[1]], Q, fi, tol):
                    return 1
        if point_in_polyhedron(P.interior_point(), Q, tol) == 1:
            return 1

    # 证人：相触顶点沿内法向微推（薄片交集）
    for P, Q, tv in touch_verts:
        plo, phi = P.aabb()
        diam = norm(sub(phi, plo))
        for vi in tv:
            d = _inward_vertex_direction(P, vi)
            if d is None:
                continue
            for eps in (1e-3, 1e-5, 1e-7):
                q = add(P.verts[vi], mul(d, eps * diam))
                if point_in_polyhedron(q, Q, tol) == 1 and point_in_polyhedron(q, P, tol) == 1:
                    return 1

    # 证人搜索：AABB 交集内的确定性网格 + 少量伪随机点
    import random as _random
    span = tuple(hi[i] - lo[i] for i in range(3))
    if all(s >= 0.0 for s in span):
        pts: list[Vec3] = []
        g = 5
        for i in range(g):
            for j in range(g):
                for k in range(g):
                    pts.append((lo[0] + span[0] * (i + 0.5) / g,
                                lo[1] + span[1] * (j + 0.5) / g,
                                lo[2] + span[2] * (k + 0.5) / g))
        rng = _random.Random(0xE4B)
        pts.extend((rng.uniform(lo[0], hi[0]), rng.uniform(lo[1], hi[1]), rng.uniform(lo[2], hi[2]))
                   for _ in range(60))
        for p in pts:
            if point_in_polyhedron(p, A, tol) == 1 and point_in_polyhedron(p, B, tol) == 1:
                return 1
    return 0 if touching else -1


def _seg_seg_distance(p1: Vec3, p2: Vec3, q1: Vec3, q2: Vec3) -> float:
    d1, d2 = sub(p2, p1), sub(q2, q1)
    a, b, c = dot(d1, d1), dot(d1, d2), dot(d2, d2)
    w = sub(p1, q1)
    d, e = dot(d1, w), dot(d2, w)
    den = a * c - b * b
    if den > 1e-300:
        s = max(0.0, min(1.0, (b * e - c * d) / den))
    else:
        s = 0.0
    t = (b * s + e) / c if c > 1e-300 else 0.0
    t = max(0.0, min(1.0, t))
    s = (b * t - d) / a if a > 1e-300 else 0.0
    s = max(0.0, min(1.0, s))
    return norm(sub(add(p1, mul(d1, s)), add(q1, mul(d2, t))))


def _point_face_distance(p: Vec3, P: Polyhedron, fi: int) -> float | None:
    """点到面**多边形**的距离；投影落在多边形外则返回 None（由顶点/棱对覆盖）。

    多边形内点用 `point_in_face_polygon`（非凸面正确）。此前用半平面核（审查 C7：L 块臂上的
    投影被判"面外"，距离高估 0.673 vs 0.5）。边界带取 0：落在棱上的投影由顶点/棱对同样给出。
    """
    n = P.face_normal(fi)
    o = P.verts[P.faces[fi][0]]
    g = dot(n, sub(p, o))
    proj = add(p, mul(n, -g))
    if not point_in_face_polygon(proj, P, fi, 0.0):
        return None
    return abs(g)


def brute_feature_distance(A: Polyhedron, B: Polyhedron) -> float:
    """两个（可非凸）分离多面体的距离：对**全部**特征对取最小，**不施加任何法锥筛选**。

    这是 G0 的独立 oracle：多面体间距离必由顶-顶、顶-棱、顶-面、棱-棱之一实现，
    枚举全部即得真值。它只用坐标，不用法向、不用法锥——因此可以检验"法锥有效性筛选
    是否会丢掉最近特征对"这条完备性命题。
    """
    best = float("inf")
    for a in A.verts:
        for b in B.verts:
            best = min(best, norm(sub(a, b)))
    for P, Q in ((A, B), (B, A)):
        for p in P.verts:
            for e in Q.edges():
                best = min(best, _seg_seg_distance(p, p, Q.verts[e[0]], Q.verts[e[1]]))
            for fi in range(len(Q.faces)):
                d = _point_face_distance(p, Q, fi)
                if d is not None:
                    best = min(best, d)
    for ea in A.edges():
        for eb in B.edges():
            best = min(best, _seg_seg_distance(A.verts[ea[0]], A.verts[ea[1]],
                                               B.verts[eb[0]], B.verts[eb[1]]))
    return best


# ------------------------------------------------------------------ 构造器

def box(center: Vec3 = (0.0, 0.0, 0.0), half: Vec3 = (1.0, 1.0, 1.0)) -> Polyhedron:
    cx, cy, cz = center
    hx, hy, hz = half
    v = [(cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz), (cx + hx, cy + hy, cz - hz),
         (cx - hx, cy + hy, cz - hz), (cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz),
         (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return Polyhedron(v, f)


def tetra(a: Vec3, b: Vec3, c: Vec3, d: Vec3) -> Polyhedron:
    P = Polyhedron([a, b, c, d], [(0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)])
    if P.volume() < 0:
        P = Polyhedron([a, b, c, d], [tuple(reversed(f)) for f in P.faces])
    return P


def convex_hull_3d(points: list[Vec3], tol: float = 1e-12) -> Polyhedron:
    """增量凸包（面为三角形，外看 CCW）。点数少时足够（本仓库用于校验，不追求性能）。"""
    pts = list(dict.fromkeys(points))
    if len(pts) < 4:
        raise ValueError("need >= 4 non-degenerate points")
    # 找一个非退化四面体
    base = None
    for combo in combinations(range(len(pts)), 4):
        a, b, c, d = (pts[i] for i in combo)
        if abs(dot(sub(b, a), cross(sub(c, a), sub(d, a)))) > tol:
            base = combo
            break
    if base is None:
        raise ValueError("points are coplanar")
    hull = tetra(pts[base[0]], pts[base[1]], pts[base[2]], pts[base[3]])
    verts = list(hull.verts)
    faces = list(hull.faces)
    for p in pts:
        if any(norm(sub(p, v)) <= tol for v in verts):
            continue
        vis = []
        for fi, f in enumerate(faces):
            n = Polyhedron(verts, faces).face_normal(fi)
            if dot(n, sub(p, verts[f[0]])) > tol:
                vis.append(fi)
        if not vis:
            continue
        # 视界：只属于一个可见面的有向边
        cnt: dict[tuple[int, int], int] = {}
        for fi in vis:
            f = faces[fi]
            for i in range(len(f)):
                a, b = f[i], f[(i + 1) % len(f)]
                key = (min(a, b), max(a, b))
                cnt[key] = cnt.get(key, 0) + 1
        horizon = []
        for fi in vis:
            f = faces[fi]
            for i in range(len(f)):
                a, b = f[i], f[(i + 1) % len(f)]
                if cnt[(min(a, b), max(a, b))] == 1:
                    horizon.append((a, b))
        faces = [f for fi, f in enumerate(faces) if fi not in set(vis)]
        verts.append(p)
        ip = len(verts) - 1
        for a, b in horizon:
            faces.append((a, b, ip))
    # 只保留被面引用的顶点并重新编号：增量过程中先入的极点可能在后续加点后变成内点，
    # 若不剔除，verts 就是顶点集的**超集**（2026-09-18 实测 43 vs 真实 31，让 G0 票三误红）。
    used = sorted({i for f in faces for i in f})
    remap = {old: new for new, old in enumerate(used)}
    return Polyhedron([verts[i] for i in used], [tuple(remap[i] for i in f) for f in faces])

def merge_coplanar(P: "Polyhedron", tol: float = 1e-9) -> "Polyhedron":
    """把共面的相邻面归并成一个多边形面，**保留顶点编号**。

    为什么必须有它：三角化的输入（凸包、STL、大多数网格导出）会让**同一个几何平面**
    被拆成多个三角形，于是一个顶点对同一个平面产生**多个 VF 盖**——2026-09-20 的 G2 对账
    实测：cb2 的 4×4 顶面被凸包拆成两个三角形后，上块 4 个底角给出 **6** 个有效盖
    （落在公共对角线上的两个角各被数两次），而四边形面的同一位形恰好给 4 个。
    归并之后盖数才是几何决定的，与网格划分无关。

    做法：按支撑平面分组 → **组内按共棱分连通分量**（并查集）→ 每个分量内有向边相消
    （内部边正反成对出现）→ 剩余边串成边界环。环的朝向自动正确（源面都是外看 CCW）。
    **共线顶点保留**（与二维版的 legacy 兼容纪律一致）。

    只归并**共棱**的共面面（2026-09-21 审查 C8）：只按平面分组时，U 形棱柱的两个端面
    （共面、不共棱）被强行归并而报错；两个共面面只在一个顶点相触（pinch）时边界字典静默
    丢边、走环死循环。现在：不共棱的共面面各自保留；分量内部的边界若在某顶点出现两条出边
    （洞贴着外边界的 pinch）或多于一个环（面上有洞），该区域不是简单多边形、Polyhedron 表示
    不了，**明确抛 ValueError**；走环有步数上界，任何输入都不会挂死。
    """
    groups: list[tuple[Vec3, float, list[int]]] = []
    for fi in range(len(P.faces)):
        n = P.face_normal(fi)
        d = dot(n, P.verts[P.faces[fi][0]])
        hit = None
        for gi, (gn, gd, _) in enumerate(groups):
            if norm(sub(gn, n)) < tol and abs(gd - d) < tol:
                hit = gi
                break
        if hit is None:
            groups.append((n, d, [fi]))
        else:
            groups[hit][2].append(fi)

    faces: list[Face] = []
    for _, _, fis in groups:
        for comp in _edge_connected_components(P, fis):
            if len(comp) == 1:
                faces.append(P.faces[comp[0]])
            else:
                faces.append(_merge_component_ring(P, comp))
    return Polyhedron(list(P.verts), faces)


def _edge_connected_components(P: Polyhedron, fis: list[int]) -> list[list[int]]:
    """面下标集合按"共享一条无向棱"分连通分量（并查集）。分量按最小面下标排序，分量内保持原序。"""
    parent = {fi: fi for fi in fis}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    owner: dict[tuple[int, int], int] = {}
    for fi in fis:
        f = P.faces[fi]
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            key = (min(a, b), max(a, b))
            if key in owner:
                ra, rb = find(owner[key]), find(fi)
                if ra != rb:
                    parent[max(ra, rb)] = min(ra, rb)
            else:
                owner[key] = fi
    comps: dict[int, list[int]] = {}
    for fi in fis:
        comps.setdefault(find(fi), []).append(fi)
    return sorted(comps.values(), key=lambda c: min(c))


def _merge_component_ring(P: Polyhedron, comp: list[int]) -> Face:
    """一个共面、共棱连通的面集合 → 其并集的边界环（必须是单个简单环，否则抛错）。"""
    directed: dict[tuple[int, int], int] = {}
    for fi in comp:
        f = P.faces[fi]
        for i in range(len(f)):
            e = (f[i], f[(i + 1) % len(f)])
            directed[e] = directed.get(e, 0) + 1
    boundary: dict[int, int] = {}
    for (a, b), c in directed.items():
        if directed.get((b, a), 0) == 0 and c == 1:
            if a in boundary:
                raise ValueError(
                    f"merge_coplanar: vertex {a} has two outgoing boundary edges ({a}->{boundary[a]}, "
                    f"{a}->{b}) in coplanar faces {sorted(comp)} — a pinch: the merged region is not a "
                    "simple polygon (a hole touches its outer boundary)")
            boundary[a] = b
    if not boundary:
        raise ValueError("merge_coplanar: coplanar group has no boundary (degenerate)")
    start = next(iter(boundary))                  # 与旧实现同一起点：凸输入的面环逐位不变
    ring = [start]
    cur = boundary[start]
    while cur != start:
        if len(ring) > len(boundary):
            raise ValueError(f"merge_coplanar: boundary walk from vertex {start} did not close "
                             f"in faces {sorted(comp)}")
        ring.append(cur)
        nxt = boundary.get(cur)
        if nxt is None:
            raise ValueError(f"merge_coplanar: boundary ring broken at vertex {cur}")
        cur = nxt
    if len(ring) != len(boundary):
        raise ValueError("merge_coplanar: coplanar group has more than one boundary ring "
                         f"({len(ring)} of {len(boundary)} edges used) — face with a hole?")
    return tuple(ring)
