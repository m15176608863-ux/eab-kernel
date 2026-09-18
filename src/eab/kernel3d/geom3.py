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


# ------------------------------------------------------------------ 点与线段谓词

def _tri_ray_hit(p: Vec3, d: Vec3, a: Vec3, b: Vec3, c: Vec3, tol: float) -> tuple[bool, float, bool]:
    """射线 p+t·d 与三角 abc：返回 (是否命中, t, 是否命中边界)。Möller–Trumbore。"""
    e1, e2 = sub(b, a), sub(c, a)
    h = cross(d, e2)
    det = dot(e1, h)
    if abs(det) < 1e-300:
        return False, 0.0, False
    inv = 1.0 / det
    s = sub(p, a)
    u = dot(s, h) * inv
    q = cross(s, e1)
    v = dot(d, q) * inv
    t = dot(e2, q) * inv
    edge_hit = abs(u) < tol or abs(v) < tol or abs(u + v - 1.0) < tol
    if u < -tol or v < -tol or u + v > 1.0 + tol or t < 0.0:
        return False, t, edge_hit
    return True, t, edge_hit


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

    射线方向取多个伪随机方向：命中三角边界时换方向重试（避免奇偶计数在退化命中上出错）。
    """
    # 边界：点到任一面三角形的距离 ≤ tol
    for fi, f in enumerate(P.faces):
        n = P.face_normal(fi)
        d0 = dot(n, sub(p, P.verts[f[0]]))
        if abs(d0) <= tol:
            # 投影落在面多边形内？用面内二维绕数
            if _point_on_face(p, P, fi, tol):
                return 0
    for d in _ray_directions():
        crossings = 0
        degenerate = False
        for fi, f in enumerate(P.faces):
            for i in range(1, len(f) - 1):
                hit, t, edge_hit = _tri_ray_hit(p, d, P.verts[f[0]], P.verts[f[i]], P.verts[f[i + 1]], 1e-9)
                if hit:
                    if edge_hit or t < 1e-12:
                        degenerate = True
                        break
                    crossings += 1
            if degenerate:
                break
        if not degenerate:
            return 1 if crossings % 2 == 1 else -1
    # 所有方向都退化 ⟺ 射线起点实际就落在表面上（每条射线 t≈0 即命中）。
    # 这在调用方给的边界容差小于实际浮点偏移时会发生：实测点 (−0.95,−0.5,0.525) 到面的
    # 偏移 3.3e-10 > tol=1e-12，边界判定没认出它，却又无法用奇偶法。返回"边界"是正确答案。
    return 0


def _point_on_face(p: Vec3, P: Polyhedron, fi: int, tol: float) -> bool:
    """p 在面 fi 的多边形内（含边界，容差 tol）；假定 p 已在该面平面上。"""
    f = P.faces[fi]
    for i in range(1, len(f) - 1):
        a, b, c = P.verts[f[0]], P.verts[f[i]], P.verts[f[i + 1]]
        n = cross(sub(b, a), sub(c, a))
        an = norm(n)
        if an < 1e-300:
            continue
        # 重心坐标（带容差）
        u = dot(cross(sub(b, a), sub(p, a)), n) / (an * an)
        v = dot(cross(sub(p, a), sub(c, a)), n) / (an * an)
        w = 1.0 - u - v
        s = tol / sqrt(an) if an > 0 else tol
        if u >= -s and v >= -s and w >= -s:
            return True
    return False


def segment_crosses_face(p: Vec3, q: Vec3, P: Polyhedron, fi: int, tol: float = 0.0) -> bool:
    """线段 pq 的**内部**与面 fi 的**内部**真相交（不含端点触碰、不含共面）。"""
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
    f = P.faces[fi]
    for i in range(1, len(f) - 1):
        a, b, c = P.verts[f[0]], P.verts[f[i]], P.verts[f[i + 1]]
        nn = cross(sub(b, a), sub(c, a))
        an2 = dot(nn, nn)
        if an2 < 1e-300:
            continue
        u = dot(cross(sub(b, a), sub(x, a)), nn) / an2
        v = dot(cross(sub(x, a), sub(c, a)), nn) / an2
        w = 1.0 - u - v
        if u > tol and v > tol and w > tol:
            return True
    return False


def polyhedra_overlap(A: Polyhedron, B: Polyhedron, tol: float = 0.0) -> int:
    """暴力谓词：1 内部相交 / 0 仅边界接触 / -1 分离。任意（含非凸）闭合多面体。

    证人搜索按代价递增：AABB 早退 → 顶点在内 → 棱穿面 → 各自内点在对方内 →
    **AABB 交集里的网格与随机采样**。最后一步是必需的：两个方块共享 y、z 范围时前四步全空，
    但交集体积为正（2026-09-18 实测 (0.75,0,0) 是证人）。**全程不用体心**（凹体体心可在体外）。
    """
    (ax0, ay0, az0), (ax1, ay1, az1) = A.aabb()
    (bx0, by0, bz0), (bx1, by1, bz1) = B.aabb()
    lo = (max(ax0, bx0), max(ay0, by0), max(az0, bz0))
    hi = (min(ax1, bx1), min(ay1, by1), min(az1, bz1))
    if any(hi[i] < lo[i] - tol for i in range(3)):
        return -1

    touching = False
    for P, Q in ((A, B), (B, A)):
        for p in P.verts:
            s = point_in_polyhedron(p, Q, tol)
            if s == 1:
                return 1
            if s == 0:
                touching = True
        for e in P.edges():
            for fi in range(len(Q.faces)):
                if segment_crosses_face(P.verts[e[0]], P.verts[e[1]], Q, fi, tol):
                    return 1
        if point_in_polyhedron(P.interior_point(), Q, tol) == 1:
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
    """点到面**多边形**的距离；投影落在多边形外则返回 None（由顶点/棱对覆盖）。"""
    n = P.face_normal(fi)
    o = P.verts[P.faces[fi][0]]
    g = dot(n, sub(p, o))
    proj = add(p, mul(n, -g))
    f = P.faces[fi]
    k = len(f)
    for i in range(k):
        a, b = P.verts[f[i]], P.verts[f[(i + 1) % k]]
        e = sub(b, a)
        le = norm(e)
        if le == 0.0:
            continue
        if dot(cross(e, sub(proj, a)), n) < -1e-12 * le:
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
