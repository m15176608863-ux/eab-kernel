"""三维几何原语与暴力多面体谓词（G0 的 oracle）。纯 Python，零依赖。

多面体表示 `Polyhedron`：顶点表 + 面表（每面一个顶点索引环，**从外部看为逆时针**，即右手法则
给出外法向）。允许非凸、允许非三角面（面必须平面且为简单多边形）。

审查（2026-09-18，二维版）的三条教训在此一并落实：
1. 反射/凹的判定用角度（atan2）不用 sin；
2. 面积/体积/质心相对第一个顶点累加，防远偏移抵消；
3. "内点"必须是**保证在内**的点，不能用质心（凹体质心可在体外）。

**容差政策（纪律 F，2026-09-24 G6 之后；2026-09-27 M0.3 改为逐特征）**：本模块与 covers3 / g03 不再有
"对坐标量纲裸用"的绝对阈值。一切判据的有效容差取
    长度  tol_eff = max(调用方 tol, c·eps·C)            C = 坐标量级 max|x_i|
    角度  被测特征自己的噪声：棱方向 c·eps·C/|e|（`edge_noise`）、面法向 c·eps·C·周长/(2·面积)（`face_noise`）、
          二面角 = 两相邻面法向噪声之和（`dihedral_noise`）
c = NOISE_ULPS（64）。调用方 tol 的语义不变（它是调用方想要的容差）；地板只吸收**舍入噪声**，
保证刚体运动（旋转 + 平移到工程坐标）与单位缩放不改变任何判决（tests/test_invariance_geom.py）。
M0.2 的角度地板取**整个物体的最短棱** c·eps·C/ℓ_min（`angular_floor`，已删）：一条极短的棱让全部特征的角容差
一起变大，二面转角 0.01 rad 的真棱脊被判平（G6 第二轮 critical，tests/test_margin_resolution.py）。
convex_hull_3d 的 tol 是**相对**容差（乘点集尺度 L）；g03 的 tol / band 亦然。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from itertools import combinations
import math
from math import atan2, hypot, sqrt

Vec3 = tuple[float, float, float]
Face = tuple[int, ...]

EPS = 2.220446049250313e-16          # float64 的机器 ε
NOISE_ULPS = 64.0                    # 舍入噪声地板的倍数 c（几十个 ulp）


def noise_floor(C: float) -> float:
    """坐标量级 C 处的舍入噪声地板 c·eps·C（长度量纲）。见模块文档的容差政策。"""
    return NOISE_ULPS * EPS * C


def coord_scale(*pts: Vec3) -> float:
    """点的坐标量级 max|x_i|。"""
    return max((abs(c) for p in pts for c in p), default=0.0)


_O3D_ERR = 7.771561172376096e-16          # Shewchuk orient3d 的过滤界系数 (7 + 56u)·u


def orient3d(a: Vec3, b: Vec3, c: Vec3, p: Vec3) -> int:
    """det[b − a, c − a, p − a] 的**精确**符号：+1 p 在 (a, b, c) 右手法向一侧 / 0 共面 / −1 另一侧。
    浮点快路 + Shewchuk 误差界过滤（相对项乘以置换和，另加次正规绝对项），界内退到 Fraction 精确算术。
    浮点输入是精确有理数，结果对这组坐标精确——凸包的可见性判定靠它（M0.3，"精确谓词、非精确构造"）。
    下面按 Shewchuk 的展开式算 det[a − p, b − p, c − p]，它与上式反号（p 在右手法向一侧时为负），返回时取反。"""
    adx, ady, adz = a[0] - p[0], a[1] - p[1], a[2] - p[2]
    bdx, bdy, bdz = b[0] - p[0], b[1] - p[1], b[2] - p[2]
    cdx, cdy, cdz = c[0] - p[0], c[1] - p[1], c[2] - p[2]
    bdxcdy, cdxbdy = bdx * cdy, cdx * bdy
    cdxady, adxcdy = cdx * ady, adx * cdy
    adxbdy, bdxady = adx * bdy, bdx * ady
    det = adz * (bdxcdy - cdxbdy) + bdz * (cdxady - adxcdy) + cdz * (adxbdy - bdxady)
    perm = ((abs(bdxcdy) + abs(cdxbdy)) * abs(adz) + (abs(cdxady) + abs(adxcdy)) * abs(bdz)
            + (abs(adxbdy) + abs(bdxady)) * abs(cdz))
    bound = _O3D_ERR * perm + 2.0 ** -1000
    if det > bound:
        return -1
    if -det > bound:
        return 1
    F = Fraction
    ax, ay, az = F(a[0]) - F(p[0]), F(a[1]) - F(p[1]), F(a[2]) - F(p[2])
    bx, by, bz = F(b[0]) - F(p[0]), F(b[1]) - F(p[1]), F(b[2]) - F(p[2])
    cx, cy, cz = F(c[0]) - F(p[0]), F(c[1]) - F(p[1]), F(c[2]) - F(p[2])
    d = az * (bx * cy - cx * by) + bz * (cx * ay - ax * cy) + cz * (ax * by - bx * ay)
    return (d < 0) - (d > 0)


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
    # 纯函数缓存（Polyhedron 视为不可变：translated / reflected 都新建对象）
    _normals: list | None = field(default=None, repr=False, compare=False)
    _face_noise: list | None = field(default=None, repr=False, compare=False)
    _vedges: dict | None = field(default=None, repr=False, compare=False)
    _metrics: tuple[float, float, float] | None = field(default=None, repr=False, compare=False)
    _interior: Vec3 | None = field(default=None, repr=False, compare=False)

    # ---------------- 尺度 ----------------
    def metrics(self) -> tuple[float, float, float]:
        """(C, L, ℓ)：坐标量级 max|x_i|、AABB 对角线（特征长度）、最短棱长。缓存。容差政策见模块文档。"""
        if self._metrics is None:
            C = coord_scale(*self.verts)
            lo, hi = self.aabb()
            L = norm(sub(hi, lo))
            ell = min((norm(sub(self.verts[b], self.verts[a])) for a, b in self.edges()), default=0.0)
            self._metrics = (C, L, ell if ell > 0.0 else (L if L > 0.0 else 1.0))
        return self._metrics

    def edge_noise(self, e: tuple[int, int]) -> float:
        """棱 e 的单位方向的舍入噪声 c·eps·C/|e|（弧度）：刚体运动把顶点挪动 ~eps·C，方向随之转这么多。
        只看**这条棱自己**的长度（纪律 F 的逐特征口径）。零长棱为 +inf。"""
        ell = norm(sub(self.verts[e[1]], self.verts[e[0]]))
        return noise_floor(self.metrics()[0]) / ell if ell > 0.0 else float("inf")

    def face_noise(self, fi: int) -> float:
        """面 fi 的单位外法向的舍入噪声（弧度）：顶点挪动 δ = c·eps·C 时 Newell 向量（= 2·面积·n）至多变
        δ·周长，方向至多转 δ·周长/(2·面积)。三角形上 2·面积/周长 是内切圆半径——细条三角的法向本来就不准。
        退化面（面积 0）为 +inf。缓存。"""
        cache = self._face_noise
        if cache is None:
            cache = self._face_noise = [None] * len(self.faces)
        v = cache[fi]
        if v is None:
            f = self.faces[fi]
            per = sum(norm(sub(self.verts[f[(i + 1) % len(f)]], self.verts[f[i]])) for i in range(len(f)))
            area2 = 2.0 * self.face_area(fi)
            v = cache[fi] = noise_floor(self.metrics()[0]) * per / area2 if area2 > 0.0 else float("inf")
        return v

    def dihedral_noise(self, e: tuple[int, int]) -> float:
        """棱 e 二面转角的舍入噪声：两相邻面法向噪声之和。平棱经刚体运动后转角在 ±它以内。"""
        return sum(self.face_noise(fi) for fi in self.edge_faces(e))

    # ---------------- 拓扑 ----------------
    def face_normal(self, fi: int) -> Vec3:
        """面的单位外法向（Newell 法，对非三角面与近退化面都稳）。缓存。"""
        cache = self._normals
        if cache is None:
            cache = self._normals = [None] * len(self.faces)
        n = cache[fi]
        if n is None:
            n = cache[fi] = self._newell_normal(fi)
        return n

    def _newell_normal(self, fi: int) -> Vec3:
        f = self.faces[fi]
        n = (0.0, 0.0, 0.0)
        o = self.verts[f[0]]
        k = len(f)
        for i in range(k):
            p = sub(self.verts[f[i]], o)
            q = sub(self.verts[f[(i + 1) % k]], o)
            n = add(n, cross(p, q))
        if n == (0.0, 0.0, 0.0):
            raise ValueError(f"face {fi} {f} has zero area (collinear or coincident vertices); "
                             f"strip duplicates at the reader boundary")
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

    def vertex_edges(self, vi: int) -> list[tuple[Vec3, float]]:
        """顶点 vi 的入射棱：(由 vi 指向邻点的单位方向, 该棱的方向噪声 `edge_noise`)。零长棱跳过。缓存。"""
        cache = self._vedges
        if cache is None:
            cache = self._vedges = {}
            for a, b in self.edges():
                cache.setdefault(a, []).append(b)
                cache.setdefault(b, []).append(a)
            fl = noise_floor(self.metrics()[0])
            for v, nbrs in cache.items():
                out = []
                for w in dict.fromkeys(nbrs):
                    d = sub(self.verts[w], self.verts[v])
                    ell = norm(d)
                    if ell > 0.0:
                        out.append((unit(d), fl / ell))
                cache[v] = out
        return cache.get(vi, [])

    def edge_dir(self, e: tuple[int, int]) -> Vec3:
        d = sub(self.verts[e[1]], self.verts[e[0]])
        if d == (0.0, 0.0, 0.0):
            raise ValueError(f"zero-length edge {e} (consecutive duplicate vertex at {self.verts[e[0]]}); "
                             f"strip duplicates at the reader boundary (readers.bdda_geom.strip_duplicate_vertices)")
        return unit(d)

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
        兜底退回体心（凸体总成立）。微退步长相对体的尺度（此前取 max(1, 尺度)：小于 1 的体会退出体外）。缓存。"""
        if self._interior is None:
            self._interior = self._find_interior_point()
        return self._interior

    def _find_interior_point(self) -> Vec3:
        scale = max(norm(sub(p, self.verts[0])) for p in self.verts) or 1.0
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
        for e in self.edges():
            if self.verts[e[0]] == self.verts[e[1]]:
                issues.append(f"edge {e}: zero length (consecutive duplicate vertex at {self.verts[e[0]]})")
        for e, trav in ((e, self.edge_traversals(e)) for e in self.edges()):
            if len(trav) != 2:
                issues.append(f"edge {e}: {len(trav)} traversals (need 2)")
                continue
            (_, a1, b1), (_, a2, b2) = trav
            if (a1, b1) == (a2, b2):
                issues.append(f"edge {e}: both faces traverse {a1}->{b1} (a face winding is reversed)")
        # 面多边形应平面（相对面尺度 tol，另加坐标舍入地板：远坐标下的"平面"四边形本身就被舍入扭曲）。
        # 三角形恒为平面，不检——对细长三角，由坐标算出的法向本身只准到 eps·ℓ/h，拿它量"平面度"
        # 量的是法向的条件数而不是几何（远坐标下 Minkowski 差点的凸包里会有这种合法的细条三角）。
        fl = 4.0 * noise_floor(coord_scale(*self.verts))
        for fi, f in enumerate(self.faces):
            if len(f) < 3:
                issues.append(f"face {fi}: only {len(f)} vertices")
                continue
            if self.face_area(fi) == 0.0:
                issues.append(f"face {fi}: zero area")
                continue
            if len(f) == 3:
                continue
            n = self.face_normal(fi)
            o = self.verts[f[0]]
            scale = max(norm(sub(self.verts[i], o)) for i in f) or 1.0
            for i in f:
                if abs(dot(n, sub(self.verts[i], o))) > tol * scale + fl:
                    issues.append(f"face {fi}: not planar (vertex {i} off by "
                                  f"{dot(n, sub(self.verts[i], o)):.3g})")
                    break
        v = self.volume()
        if v <= 0.0:
            issues.append(f"signed volume {v:.6g} <= 0 (global orientation is inward)")
        return issues

    def is_convex(self, tol: float = 1e-12) -> bool:
        """tol 是角度；另加该棱二面角的舍入噪声（平棱在旋转 / 远坐标下的转角是 ±噪声，不许判成反射）。"""
        for e in self.edges():
            if len(self.edge_faces(e)) != 2:
                return False
            if self.dihedral_turn(e) < -max(tol, self.dihedral_noise(e)):
                return False
        return True

    def reflex_edges(self, tol: float = 1e-12) -> list[tuple[int, int]]:
        out = []
        for e in self.edges():
            if len(self.edge_faces(e)) == 2 and self.dihedral_turn(e) < -max(tol, self.dihedral_noise(e)):
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


def _distance_to_face_polygon(x: Vec3, P: Polyhedron, fi: int) -> float:
    """x（已在面平面上）到面多边形的面内距离：在多边形内（含边界）为 0，否则是到边界折线的最短距离。"""
    if face_polygon_locate(x, P, fi, 0.0) >= 0:
        return 0.0
    f = P.faces[fi]
    V = P.verts
    return min(_point_segment_distance(x, V[f[i]], V[f[(i + 1) % len(f)]]) for i in range(len(f)))


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

    容差（纪律 F）：边界带取 max(tol, c·eps·C)，C 为 P 与 p 的坐标量级——远坐标下面平面上的点
    算出的 d0 是 ±eps·C 量级的噪声，tol=0 时不能拿它的符号当内外（G6 minor 7）。另有一条射线法自身的
    分辨率：离某个面平面 ≤ max(1e-12·diag, c·eps·C) 且投影在面内的点答 0（起点贴着表面时射线处处 t≈0 命中，
    奇偶无从谈起）——所以 1 的有效分辨率是 max(tol, 1e-12·diag, c·eps·C)。
    """
    C, diag, _ = P.metrics()
    fl = noise_floor(max(C, abs(p[0]), abs(p[1]), abs(p[2])))
    tol = max(tol, fl)
    normals = [P.face_normal(fi) for fi in range(len(P.faces))]
    # 边界：点到任一面**多边形**的欧氏距离 ≤ tol（投影在多边形内取 |d0|，在外取 √(d0² + 面内到边界的距离²)）。
    # 旧版分两步各用一个 tol 带（到平面 ≤ tol、投影点到多边形 ≤ tol），真实距离到 √2·tol 的点也判"相触"，
    # 与裕度层按 tol 一把尺的口径不一致（G6 第二轮 minor、第三轮 major 的一半）。
    for fi, f in enumerate(P.faces):
        n = normals[fi]
        d0 = dot(n, sub(p, P.verts[f[0]]))
        if abs(d0) <= tol and hypot(d0, _distance_to_face_polygon(add(p, mul(n, -d0)), P, fi)) <= tol:
            return 0
    diag = diag or 1.0
    eps_edge = max(1e-9 * diag, fl)  # 射线交点离棱这么近即视为退化命中（相对尺度）
    eps_t = max(1e-12 * diag, fl)    # 起点离面平面这么近即视为"就在表面上"
    for fi, f in enumerate(P.faces):
        n = normals[fi]
        d0 = dot(n, sub(p, P.verts[f[0]]))
        if abs(d0) <= eps_t and point_in_face_polygon(add(p, mul(n, -d0)), P, fi, tol):
            # 起点在射线法的分辨率之下就落在表面上：任何方向都会 t≈0 命中，奇偶无从谈起。
            # 返回"边界"是正确答案（2026-09-18 实测：偏移 3.3e-10 > tol=1e-12 的点）。
            # 面内判定的边界带是调用方的 tol：旧版用射线退化带 eps_edge = 1e-9·diag，顶点落在对方某面的平面上、
            # 面内却在多边形外 ≤ 1e-9·diag 的（块共用地板：DDA 最普通的位形）被判"边界"，裕度层再升成贯入（G6 第三轮 major）。
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
            if t <= eps_t:
                # 起点就在这个面的平面上：它在多边形内（含 tol 带）的情形上面的捷径已答 0；落在多边形外的（块共用地板、
                # 角点在对方底面之外 g > tol）这里不是交叉也不是退化——用调用方的 tol 判，不用 1e-9·diag 的射线退化带
                # （G6 第三轮 major：旧版把这种点当退化、所有方向退化后答"边界"，裕度层再升成贯入）
                if face_polygon_locate(p, P, fi, tol) < 0:
                    continue
                degenerate = True
                break
            loc = face_polygon_locate(add(p, mul(d, t)), P, fi, eps_edge)
            if loc < 0:
                continue
            if loc == 0:
                degenerate = True
                break
            crossings += 1
        if not degenerate:
            return 1 if crossings % 2 == 1 else -1
    # 所有方向都退化：起点贴着棱/顶点（距离 < eps_edge），同样只能答"边界"。
    return 0


def segment_crosses_face(p: Vec3, q: Vec3, P: Polyhedron, fi: int, tol: float = 0.0) -> bool:
    """线段 pq 的**内部**与面 fi 的**内部**真相交（不含端点触碰、不含共面、不含穿过棱的 tol 带）。

    面侧容差取 max(tol, c·eps·C)：躺在面平面里的棱，dp、dq 是符号随机的舍入噪声（G6 minor 7：
    tol=0 或远坐标下被当成严格穿面，面接触判成贯入）。"""
    tol = max(tol, noise_floor(max(P.metrics()[0], coord_scale(p, q))))
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
    **接触锥证人**（相触顶点与棱-棱交点处，沿两体切锥之交的内部方向微推）→
    相触顶点沿内法向微推 → AABB 交集里的网格与随机采样。**全程不用体心**（凹体体心可在体外）。

    · 网格一步是必需的：两个方块共享 y、z 范围时前四步全空，但交集体积为正（2026-09-18 实测）。
    · 微推一步也是必需的（2026-09-21 审查 C9）：L 块凹槽里咬进一层 e 厚的薄片、z 范围重合时，
      每个顶点都落在对方面平面上、没有棱严格穿面，网格撒在 ~2×2×1 的 AABB 交集里而真交集只有
      e×2×1——e ≲ 0.01 就漏判成"相触"。相触顶点沿关联面外法向和的反方向推进 ε·diam，
      若落在两体**严格**内部即是证人。它只可能修正假阴性：证人点经 point_in_polyhedron 复验。
    · 接触锥证人是**精确**的一步（2026-09-24 G6 critical 5）：两块等高板 X 形交叉时没有顶点在体内或
      体面上、棱交点全落在共面上，其余各步与网格都漏，旧实现判 −1（margin 层因此 fail-unsafe）。
      见 `_contact_cone_witness`：对凸体完备。棱-棱相交（距离 ≤ tol）也记为"相触"——闭包相交而
      内部不交、又没有顶点相触的交叉面接触，此前被判 −1。
    · 容差：tol_eff = max(tol, c·eps·C)，C 为两体坐标量级（纪律 F，G6 minor 7）。
    · **有效分辨率**是 max(tol_eff, 1e-12·diag)（diag 为 AABB 对角线）：每个证人都经 point_in_polyhedron 复验，
      它把离某个面平面 ≤ 1e-12·diag 的点判"在表面上"（射线奇偶在那个深度分辨不了，见其文档），所以贯入深度
      ≲ 1e-12·diag 的一对答 0（相触），从不答成假的 1 或 −1（G6 第二轮 minor；门：tests/test_geom3_overlap_witness.py
      ::test_overlap_resolution_is_documented）。
    · 完备性的诚实边界：**凸体**上"贯入深于上述分辨率的 **2 倍** ⟹ 判 1"是精确的（接触锥证人沿切锥内部方向走到交集
      最深处，深 p/2 的点要比分辨率带还深才算"严格在内"）；非凸体只在交集的某个
      角点落在两体的凸局部上时精确，否则仍依赖微推启发式与采样，薄交集可能漏判成 0 / −1。
      任何情形都不会误报 1（每个证人都经 point_in_polyhedron 严格复验）。
    """
    tol = max(tol, noise_floor(max(A.metrics()[0], B.metrics()[0])))
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

    # 精确证人：接触点处两切锥之交的内部方向（G6 critical 5：共面交叉）
    witness, edge_contact = _contact_cone_witness(A, B, tol, touch_verts)
    if witness is not None:
        return 1
    touching = touching or edge_contact

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


def _segment_closest_points(p1: Vec3, p2: Vec3, q1: Vec3, q2: Vec3) -> tuple[Vec3, Vec3]:
    """两线段上的最近点对（Ericson《Real-Time Collision Detection》5.1.9；平行判据是相对的）。"""
    d1, d2, r = sub(p2, p1), sub(q2, q1), sub(p1, q1)
    a, e, f = dot(d1, d1), dot(d2, d2), dot(d2, r)
    if a <= 0.0 and e <= 0.0:
        return p1, q1
    if a <= 0.0:
        s, t = 0.0, min(1.0, max(0.0, f / e))
    else:
        c = dot(d1, r)
        if e <= 0.0:
            s, t = min(1.0, max(0.0, -c / a)), 0.0
        else:
            b = dot(d1, d2)
            den = a * e - b * b
            s = min(1.0, max(0.0, (b * f - c * e) / den)) if den > 1e-24 * a * e else 0.0
            t = (b * s + f) / e
            if t < 0.0:
                s, t = min(1.0, max(0.0, -c / a)), 0.0
            elif t > 1.0:
                s, t = min(1.0, max(0.0, (b - c) / a)), 1.0
    return add(p1, mul(d1, s)), add(q1, mul(d2, t))


def _edge_edge_contacts(A: Polyhedron, B: Polyhedron, tol: float) -> list[Vec3]:
    """A 的棱与 B 的棱相交（最近距离 ≤ tol）处的点（两最近点的中点）。先按两体 AABB 之交筛棱。"""
    (ax0, ay0, az0), (ax1, ay1, az1) = A.aabb()
    (bx0, by0, bz0), (bx1, by1, bz1) = B.aabb()
    lo = (max(ax0, bx0) - tol, max(ay0, by0) - tol, max(az0, bz0) - tol)
    hi = (min(ax1, bx1) + tol, min(ay1, by1) + tol, min(az1, bz1) + tol)

    def boxed(P: Polyhedron):
        out = []
        for e in P.edges():
            p, q = P.verts[e[0]], P.verts[e[1]]
            elo = (min(p[0], q[0]), min(p[1], q[1]), min(p[2], q[2]))
            ehi = (max(p[0], q[0]), max(p[1], q[1]), max(p[2], q[2]))
            if all(elo[i] <= hi[i] and ehi[i] >= lo[i] for i in range(3)):
                out.append((p, q, elo, ehi))
        return out

    EA, EB = boxed(A), boxed(B)
    pts: list[Vec3] = []
    for p, q, alo, ahi in EA:
        for u, v, blo, bhi in EB:
            if any(alo[i] > bhi[i] + tol or blo[i] > ahi[i] + tol for i in range(3)):
                continue
            xa, xb = _segment_closest_points(p, q, u, v)
            if norm(sub(xa, xb)) <= tol:
                pts.append(mul(add(xa, xb), 0.5))
    return pts


def _active_normals(P: Polyhedron, x: Vec3, tol: float) -> list[Vec3]:
    """x（在 P 的边界上）处的活动面外法向：面平面距离 ≤ tol + |x − v₀|·面法向噪声、且投影落在面多边形（含 tol 带）内。

    面平面距离 d = n·(x − v₀) 的舍入不只是长度地板：n 的方向噪声（`face_noise`）乘力臂 |x − v₀|。旧版只用长度地板，
    细长板（20 × 0.02 × 1）X 形交叉、刚体旋转后，薄面在棱-棱交点处的平面距离 2.7e-13 > 地板 1.2e-13，薄面掉出活动集，
    Gordan 方向不是真内部方向，tol = 0 时 polyhedra_overlap 把贯入答成"接触"（G6 第二轮 minor）。"""
    out = []
    for fi, f in enumerate(P.faces):
        n = P.face_normal(fi)
        w = sub(x, P.verts[f[0]])
        d = dot(n, w)
        if abs(d) <= tol + norm(w) * P.face_noise(fi) and face_polygon_locate(add(x, mul(n, -d)), P, fi, tol) >= 0:
            out.append(n)
    return out


def _gordan_direction(ns: list[Vec3], margin: float = 1e-9) -> tuple[Vec3, float] | None:
    """{d : d·n < 0, ∀n ∈ ns} 的一个内部方向（Gordan：存在 ⟺ 0 ∉ conv(ns)）。

    d = −p/|p|，p = conv(ns) 上离原点最近的点；此时 max_n d·n = −|p|（内部裕度）。p 由 ≤ 3 点子集的
    仿射包投影逐一枚举、按 KKT 条件 p·n ≥ |p|²（∀n）核对得到——**独立实现**，不与 covers3 的
    cone_relint_direction 共用代码（polyhedra_overlap 是 G0 的 oracle，纪律 A）。
    |p| ≤ margin（锥无内部或几乎无内部）返回 None。返回 (d, |p|)。
    """
    uniq: list[Vec3] = []
    for n in ns:
        if not any(norm(sub(n, m)) <= 1e-12 for m in uniq):
            uniq.append(n)
    k = len(uniq)
    if k == 0:
        return None
    for size in (1, 2, 3):
        for S in combinations(range(k), size):
            p = _min_norm_on_simplex([uniq[i] for i in S])
            if p is None:
                continue
            pp = dot(p, p)
            if all(dot(p, n) >= pp - 1e-12 for n in uniq):
                r = sqrt(pp)
                return (mul(p, -1.0 / r), r) if r > margin else None
    return None


def _min_norm_on_simplex(V: list[Vec3]) -> Vec3 | None:
    """原点在 conv(V)（|V| ≤ 3，单位向量）的仿射包上的正交投影，若它落在 conv(V) 内；否则 None。"""
    a = V[0]
    if len(V) == 1:
        return a
    e1 = sub(V[1], a)
    if len(V) == 2:
        ee = dot(e1, e1)
        if ee <= 1e-24:
            return None
        t = -dot(a, e1) / ee
        return add(a, mul(e1, t)) if 0.0 <= t <= 1.0 else None
    e2 = sub(V[2], a)
    g11, g12, g22 = dot(e1, e1), dot(e1, e2), dot(e2, e2)
    det = g11 * g22 - g12 * g12
    if det <= 1e-20 * g11 * g22:
        return None
    r1, r2 = -dot(a, e1), -dot(a, e2)
    u = (r1 * g22 - r2 * g12) / det
    v = (r2 * g11 - r1 * g12) / det
    if u < 0.0 or v < 0.0 or u + v > 1.0:
        return None
    return add(a, add(mul(e1, u), mul(e2, v)))


def _contact_cone_witness(A: Polyhedron, B: Polyhedron, tol: float,
                          touch_verts: list[tuple[Polyhedron, Polyhedron, list[int]]]
                          ) -> tuple[Vec3 | None, bool]:
    """精确证人（G6 critical 5）：在两体边界的接触点 x 处找 int(A) ∩ int(B) 的点。

    候选 x = 相触顶点（某体顶点落在另一体边界上）∪ 棱-棱交点。x 处凸体的切锥是全部活动面
    半空间 {d·n ≤ 0} 之交；两切锥之交有内部 ⟺ Gordan 方向 d 存在（`_gordan_direction`）。沿 d 推进
    ε（从 0.1·diam 到 1e-9·diam 逐级），point_in_polyhedron **严格**在两体内即为证人——只可能修正
    假阴性，不可能造出假阳性。

    完备性（凸体）：若 int(A ∩ B) ≠ ∅，cl(int(A ∩ B)) 是有顶点的多面体，取其一顶点 v，v 处局部锥有内部；
    v 必为某体顶点、棱穿面点或棱-棱交点——棱**严格**穿面在前一步已判 1，其余两类都在候选里。
    所以两块等高板的 X 形交叉（交点全在共面上）与共面同向面的二维重叠（交多边形的角点也是棱-棱
    交点或顶点）都由这一步精确抓住。非凸体的反射棱 / 反射顶点处，活动半空间之交只是真切锥的子集：
    可能漏（留给后面的启发式与采样），不会误报。

    返回 (证人或 None, 是否存在棱-棱接触)。
    """
    cands: list[Vec3] = []
    for P, _, tv in touch_verts:
        cands.extend(P.verts[vi] for vi in tv)
    ee = _edge_edge_contacts(A, B, tol)
    cands.extend(ee)
    if not cands:
        return None, False
    step = min(A.metrics()[1], B.metrics()[1])
    for x in cands:
        g = _gordan_direction(_active_normals(A, x, tol) + _active_normals(B, x, tol))
        if g is None:
            continue
        d, depth = g
        # 沿 d 能走多远不出任一体：对两体每个 n·d > 0、x 不在其平面上的面，平面距离 (n·v₀ − n·x)/(n·d) 取最小。
        # 凸体上取它的一半就是沿 d 最深的点（薄片贯入 p 时深 ~p/2）；旧版只按 10 倍阶梯试探、eps·depth ≤ 2·tol 即停，
        # 一般朝向下 p ∈ (tol, ~20·tol) 的贯入一个探针都落不进去、答"相触"（G6 第三轮 major）。
        emax = step
        for P in (A, B):
            for fi, f in enumerate(P.faces):
                n = P.face_normal(fi)
                nd = dot(n, d)
                if nd > 0.0:
                    h = dot(n, sub(P.verts[f[0]], x))
                    if h > 0.0:
                        emax = min(emax, h / nd)
        probes = [0.5 * emax, 0.25 * emax] + [e for e in (step * 10.0 ** (-k) for k in range(1, 10)) if e < emax]
        for eps in probes:
            if eps * depth <= tol:              # 探针离各活动面平面 eps·depth，要比边界带 tol 深才算"严格在内"
                continue
            q = add(x, mul(d, eps))
            if point_in_polyhedron(q, A, tol) == 1 and point_in_polyhedron(q, B, tol) == 1:
                return q, bool(ee)
    return None, bool(ee)


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


class HullNumericalFailure(ValueError):
    """convex_hull_3d 在给定容差下自检失败（数值问题，不是输入退化）。"""


_HULL_TOL_MAX = 1e-6                 # 自适应放大容差的上限（相对 L）


def convex_hull_3d(points: list[Vec3], tol: float = 1e-12, *, max_tol: float = _HULL_TOL_MAX) -> Polyhedron:
    """凸包（面为三角形，外看 CCW）。Quickhull：初始单形取良态，逐次加入离当前凸包最远的外点。

    自适应：tol 是**最小**相对容差。自检失败时按 ×100 放大重建，至多 max_tol（缺省 1e-6·L）；仍失败则抛
    HullNumericalFailure（ValueError 的子类）。放大只改变"哪些点算共面"，不移动任何顶点，但会**抹平**高度低于
    容差的真实特征——不能接受的调用方（G0 门）把 max_tol 设为自己的分辨率，越过就抛错而不是静默变粗。
    M0.3 之前放大是常态：厚平面规则把"离每个面都 ≤ eps_d"的点永久丢掉，面被替换后它们可能远在新面之外
    （1e-6 的棱脊 + 1 m 细针的 Minkowski 差点上差 1e-3），干净的原点输入也要放大到 1e-6·L 才过自检，g0_convex3
    因此在正确的凸对上报红（G6 第二轮 major）。现在这些点留在待查池里、最后对全部面复查（见 `_quickhull`）。
    """
    if not 0.0 <= tol < 1e-3:
        raise ValueError(f"convex_hull_3d: tol is a relative tolerance (fraction of the point-set diameter), "
                         f"got {tol!r}")
    t = tol
    while True:
        try:
            return _quickhull(points, t)
        except HullNumericalFailure:
            if t >= max_tol:
                raise
            t = min(max(t, 1e-14) * 100.0, max_tol)


def _quickhull(points: list[Vec3], tol: float) -> Polyhedron:
    """convex_hull_3d 的一次构建（固定容差）：`_quickhull_once` 加细条面兜底。

    兜底（M0.3）：若结果里有"细条三角"——最短高 ≤ 4·eps_d，即一个顶点落在另两个顶点所在直线的容差带里——
    那个居中的顶点是冗余顶点（它在另两点之间，离凸包 ≤ 容差），把它排除后重建；至多重建 64 次。
    细条面的法向是舍入噪声，精确谓词对共线三点对任何点都答"共面"，自检也看不出来——所以必须按几何消掉。
    全局最远者优先的加点顺序让它极少触发（见 `_quickhull_once`）。
    """
    pts = list(dict.fromkeys(points))
    skip: set[int] = set()
    for _ in range(64):
        P, vidx, eps_d = _quickhull_once(pts, tol, skip)
        bad = _sliver_middle_vertex(P, eps_d)
        if bad is None:
            break
        skip.add(vidx[bad])
    else:
        raise HullNumericalFailure("convex_hull_3d: could not eliminate sliver faces (numerical failure)")
    # 自检（在兜底之后）：每个输入点在每个面的 eps_d 内侧（容许 4 倍），再加该面**自己的法向噪声 × 力臂**——
    # 细条三角（高只略大于兜底阈值）的法向只准到 c·eps·C·周长/(2·面积)，远点对它的平面距离带着这个噪声；旋转过的
    # 脊 + 针差点集上 300 例里 47 例因此在 1e-12 下自检失败、只能放大容差（G6 第三轮 major）。流形闭合在构建里已查。
    # 法向用三角自己的叉积，不经 Polyhedron.face_normal（凸包是 G0 的 oracle 之一，不许与被测的法向代码共用）
    C = coord_scale(*pts)
    fl = noise_floor(C)
    for f in P.faces:
        o, a, b = P.verts[f[0]], P.verts[f[1]], P.verts[f[2]]
        cr = cross(sub(a, o), sub(b, o))
        area2 = norm(cr)
        n = unit(cr)
        fn = fl * (norm(sub(a, o)) + norm(sub(b, a)) + norm(sub(o, b))) / area2
        if max(dot(n, sub(q, o)) - fn * norm(sub(q, o)) for q in pts) > 4.0 * eps_d + fl:
            raise HullNumericalFailure("convex_hull_3d: result is not convex within tolerance (numerical failure)")
    return P


def _sliver_middle_vertex(P: Polyhedron, eps_d: float) -> int | None:
    """P 的第一个细条三角（最短高 ≤ 4·eps_d）里居中的那个顶点的下标；没有细条面返回 None。"""
    for f in P.faces:
        a, b, c = (P.verts[i] for i in f)
        area2 = norm(cross(sub(b, a), sub(c, a)))
        edges = [(norm(sub(b, a)), f[2]), (norm(sub(c, b)), f[0]), (norm(sub(a, c)), f[1])]   # (边长, 对顶点)
        emax, _ = max(edges)
        if emax > 0.0 and area2 / emax <= 4.0 * eps_d:
            # 三点近共线：沿最长边方向取参数，居中者冗余
            i_far, j_far = [i for i in f if i != max(edges)[1]]
            u = sub(P.verts[j_far], P.verts[i_far])
            t = sorted(((dot(sub(P.verts[i], P.verts[i_far]), u), i) for i in f))
            return t[1][1]
    return None


def _quickhull_once(pts: list[Vec3], tol: float, skip: set[int]) -> tuple[Polyhedron, list[int], float]:
    """convex_hull_3d 的一次构建（固定容差）。返回 (凸包, 每个凸包顶点对应的 pts 下标, eps_d)。
    skip 里的点不作顶点（细条面兜底排除的冗余点），但仍参加收尾自检。

    **tol 是相对容差**（2026-09-24 G6 major 27 / minor 9）：距离判据用 eps_d = max(tol·L, c·eps·C)，
    L 为点集 AABB 对角线、C 为坐标量级（纪律 F）。此前三处绝对 1e-12——基四面体体积（∝ s³）、
    重复点距离与可见性（∝ s）——在旋转 ×1e3 的退化 Minkowski 点集上给出非流形凸包（体积 1387 vs 144）
    或 face_normal 除零；尺度 ≤ 1e-5 时报"共面"。
      · 初始单形：离 AABB 最长轴一端最远的点 → 离该线最远 → 离该面最远（良态，不取"前四个非退化点"）；
      · 每步取**全局**离面最远的外点（不是某个面自己的最远点），并列（距离差 ≤ eps_d）时取**离全体点质心最远**者
        （`pick`）：到凸集的距离是凸函数、|q − c|² 是严格凸函数，凸组合点在前者上不超过、在后者上严格小于它的
        生成点——所以棱/面内部的点永远不会先于端点成为顶点，端点都加入之后它落进容差带、不再成为顶点。
        旧版按面取最远点、并列按下标：棱中间的差点与端点到面的距离只差舍入，中点先成为顶点，留下三点近共线的
        细条三角（旋转的方块对上 9 个顶点、法向垃圾）。初始单形的四个点同样按此裁决。
        从该面出发 BFS 可见面，视界成环、补锥。可见性是**精确谓词**
        `orient3d` 的闭判据（p 在面平面上或外侧即可见）：当前面集恰是已加入顶点的精确凸包，闭可见区是一个
        拓扑圆盘，视界棱的另一侧严格不可见，锥面永不退化。厚阈值 eps_d **只**用来选外点（> eps_d 才算外点）。
        旧版用厚阈值判可见性，可见区里 0 < dist ≤ eps_d 的面被判"不可见"、挖出洞，视界成两圈，锥面横穿凸包
        （G6 第二轮 major：1e-6 棱脊 + 细针的差点集要放大到 1e-6·L 才过自检）；
      · 距任何面都 ≤ eps_d 的点暂不加入（共面/共线点不成为三角网格顶点），但**不丢**：进待查池。主循环结束后
        待查池对全部最终面复查，越出 eps_d 的重新作为外点继续构建，直到没有（qhull 的"共面点"处理；旧版厚平面
        规则永久丢弃）；
      · 收尾自检：流形闭合、每个输入点都在每个面的 eps_d 内侧，否则**抛错**——不静默返回坏凸包。
    """
    if len(pts) < 4:
        raise ValueError("need >= 4 non-degenerate points")
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    lo, hi = (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))
    L = norm(sub(hi, lo))
    eps_d = max(tol * L, noise_floor(coord_scale(lo, hi)))
    if L <= eps_d:
        raise ValueError("points are coincident")
    cen = (sum(xs) / len(pts), sum(ys) / len(pts), sum(zs) / len(pts))

    def pick(cands, key) -> int:
        """key 最大者；并列（差 ≤ eps_d）时取离质心最远者（严格凸的裁决，凸组合点输给生成点）。"""
        vals = [(key(i), i) for i in cands]
        top = max(v for v, _ in vals)
        tied = [i for v, i in vals if v >= top - eps_d]
        return max(tied, key=lambda i: dot(sub(pts[i], cen), sub(pts[i], cen)))

    # ---- 良态初始单形
    ax = max(range(3), key=lambda i: hi[i] - lo[i])
    cand = [i for i in range(len(pts)) if i not in skip]
    i0 = pick(cand, lambda i: -pts[i][ax])
    p0 = pts[i0]
    i1 = pick(cand, lambda i: norm(sub(pts[i], p0)))
    if norm(sub(pts[i1], p0)) <= eps_d:
        raise ValueError("points are coincident")
    u = unit(sub(pts[i1], p0))

    def off_line(p: Vec3) -> float:
        w = sub(p, p0)
        return norm(sub(w, mul(u, dot(w, u))))
    i2 = pick(cand, lambda i: off_line(pts[i]))
    if off_line(pts[i2]) <= eps_d:
        raise ValueError("points are collinear")
    nrm = unit(cross(sub(pts[i1], p0), sub(pts[i2], p0)))
    i3 = pick(cand, lambda i: abs(dot(nrm, sub(pts[i], p0))))
    if abs(dot(nrm, sub(pts[i3], p0))) <= eps_d:
        raise ValueError("points are coplanar")

    verts: list[Vec3] = [pts[i0], pts[i1], pts[i2], pts[i3]]
    base = [i0, i1, i2, i3]
    vidx: list[int] = list(base)
    if dot(nrm, sub(pts[i3], p0)) > 0.0:          # 第四点在 (0,1,2) 的正侧 ⇒ (0,2,1) 朝外
        tri0 = [(0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)]
    else:
        tri0 = [(0, 1, 2), (0, 3, 1), (1, 3, 2), (2, 3, 0)]

    faces: dict[int, tuple[int, int, int]] = {}
    planes: dict[int, tuple[Vec3, Vec3]] = {}          # 面 id → (单位外法向, 面上一点)
    owner: dict[tuple[int, int], int] = {}             # 有向棱 → 面 id
    outside: dict[int, list[int]] = {}                 # 面 id → 外点（verts 之外的输入下标）
    next_id = 0

    def plane_of(f: tuple[int, int, int]) -> tuple[Vec3, Vec3]:
        P3 = (verts[f[0]], verts[f[1]], verts[f[2]])
        # 以最长棱的对角顶点为原点做叉积（两条较短棱相叉，法向的舍入误差最小）
        k = (max(range(3), key=lambda j: norm(sub(P3[(j + 1) % 3], P3[j]))) + 2) % 3
        o, a, b = P3[k], P3[(k + 1) % 3], P3[(k + 2) % 3]
        n = cross(sub(a, o), sub(b, o))
        ln = norm(n)
        if ln == 0.0:
            raise HullNumericalFailure("convex_hull_3d: degenerate face (numerical failure)")
        g = mul(add(add(P3[0], P3[1]), P3[2]), 1.0 / 3.0)
        return mul(n, 1.0 / ln), g

    def add_face(f: tuple[int, int, int]) -> int:
        nonlocal next_id
        fid = next_id
        next_id += 1
        faces[fid] = f
        planes[fid] = plane_of(f)
        for i in range(3):
            owner[(f[i], f[(i + 1) % 3])] = fid
        outside[fid] = []
        return fid

    def dist(fid: int, p: Vec3) -> float:
        n, g = planes[fid]
        return dot(n, sub(p, g))

    def above(fid: int, p: Vec3) -> int:
        f = faces[fid]
        return orient3d(verts[f[0]], verts[f[1]], verts[f[2]], p)

    # 暂判"在包上/内"的点：不加入，待外点耗尽后按当前各面再核一遍。凸包只增不减，闭判据下这些点不会变成"清楚在外"，
    # 复查只防面平面的舍入；审查者 300 例（旋转 + 平移 + 缩放）扫描在有无复查下结果逐项相同——它是保险，不是修复，
    # 也没有一颗能让它变红的牙（2026-10-10 G6 第三轮订正：bcb30f4 提交说明"复查在 47 例里起作用"不成立）
    pending: set[int] = set()

    def assign(i: int, fids) -> None:
        if i in skip:
            return
        best, bd = None, eps_d
        for fid in fids:
            d = dist(fid, pts[i])
            if d > bd:
                best, bd = fid, d
        if best is not None:
            outside[best].append(i)
        else:
            pending.add(i)

    for f in tri0:
        add_face(f)
    for i in range(len(pts)):
        if i not in base:
            assign(i, list(faces))

    guard = 0
    in_hull = set(base)
    def farthest() -> tuple[int, int] | None:
        """全局最远的外点 (面, 点)；并列按离质心最远裁决（见函数文档）。"""
        ds = [(dist(fid, pts[i]), fid, i) for fid, lst in outside.items() for i in lst]
        if not ds:
            return None
        top = max(d for d, _, _ in ds)
        tied = [(fid, i) for d, fid, i in ds if d >= top - eps_d]
        return max(tied, key=lambda t: dot(sub(pts[t[1]], cen), sub(pts[t[1]], cen)))

    while True:
        pick = farthest()
        if pick is None:
            recheck = [i for i in pending if i not in in_hull]
            pending.clear()
            for i in recheck:
                assign(i, list(faces))
            pick = farthest()
            if pick is None:
                break
        guard += 1
        if guard > 4 * len(pts) + 16:
            raise HullNumericalFailure("convex_hull_3d: did not converge (numerical failure)")
        fid0, ip = pick
        p = pts[ip]
        # BFS 可见面（连通）：精确谓词的闭判据 orient3d ≥ 0（见函数文档）。
        visible = {fid0}
        stack = [fid0]
        while stack:
            fid = stack.pop()
            f = faces[fid]
            for i in range(3):
                nb = owner[(f[(i + 1) % 3], f[i])]
                if nb not in visible and above(nb, p) >= 0:
                    visible.add(nb)
                    stack.append(nb)
        horizon = []
        for fid in visible:
            f = faces[fid]
            for i in range(3):
                a, b = f[i], f[(i + 1) % 3]
                if owner[(b, a)] not in visible:
                    horizon.append((a, b))
        starts = [a for a, _ in horizon]
        if len(set(starts)) != len(starts):
            raise HullNumericalFailure("convex_hull_3d: visible region is not a disk (numerical failure)")
        orphans: list[int] = []
        for fid in visible:
            orphans.extend(outside.pop(fid))
            f = faces.pop(fid)
            planes.pop(fid)
            for i in range(3):
                e = (f[i], f[(i + 1) % 3])
                if owner.get(e) == fid:
                    del owner[e]
        verts.append(p)
        vidx.append(ip)
        in_hull.add(ip)
        pending.discard(ip)
        vp = len(verts) - 1
        new = [add_face((a, b, vp)) for a, b in horizon]
        for i in orphans:
            if i != ip:
                assign(i, new)            # 不在新面外侧的孤儿进待查池，最后对全部面复查

    # 流形闭合自检；"每个输入点在每个面内侧"的自检在 _quickhull 里、细条面兜底之后做
    for (a, b) in owner:
        if (b, a) not in owner:
            raise HullNumericalFailure("convex_hull_3d: open surface (numerical failure)")
    flist = list(faces.values())
    used = sorted({i for f in flist for i in f})
    remap = {old: new_ for new_, old in enumerate(used)}
    return (Polyhedron([verts[i] for i in used], [tuple(remap[i] for i in f) for f in flist]),
            [vidx[i] for i in used], eps_d)


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

    共面判据（2026-09-24 G6 minor 8，纪律 F）：法向差 < ang（单位向量）；平面偏移**相对首顶点**量取
    d = n·(v − v_0)，差 < ang·L + c·eps·C。ang = max(tol, 两个面各自的法向噪声之和)（M0.3 改为逐面：M0.2 用
    整体最短棱 c·eps·C/ℓ_min，一条极短的棱让真实的缓棱脊两侧被并成一个面）。此前用 d = n·v 与绝对 1e-9：
    d 的舍入 ∝ |v|，旋转过的方块放到 1e4 以外就把同一平面的两个三角留成两个面（12 而非 6）。
    """
    C, Ldiag, _ = P.metrics()
    o = P.verts[0]
    groups: list[tuple[Vec3, float, float, list[int]]] = []
    for fi in range(len(P.faces)):
        n = P.face_normal(fi)
        d = dot(n, sub(P.verts[P.faces[fi][0]], o))
        fn = P.face_noise(fi)
        hit = None
        for gi, (gn, gd, gfn, _) in enumerate(groups):
            ang = max(tol, fn + gfn)
            if norm(sub(gn, n)) < ang and abs(gd - d) < ang * Ldiag + noise_floor(C):
                hit = gi
                break
        if hit is None:
            groups.append((n, d, fn, [fi]))
        else:
            groups[hit][3].append(fi)

    faces: list[Face] = []
    for _, _, _, fis in groups:
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
