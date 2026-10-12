"""3D geometry: exact convex hull plus explicit exact surface primitives.

Exact topology APIs: orient3d, convex_hull_3d, merge_coplanar,
exact_convex_view, exact_point_in_polyhedron, exact_point_in_convex_polyhedron,
exact_segment_crosses_face, exact_triangle_intersection, exact_convex_overlap.
Input floats denote their exact rational values; derived Fraction coordinates
are preserved. Hull tolerance parameters do not flatten real features.

General surface membership and overlap use exact triangulated input semantics.
Positive tolerance is an explicit Euclidean reporting band, never a noise floor.
Contact construction helpers retain their separately documented limitations;
general APIs never silently convexify concave input. See docs/exact_3d_design.md and the E5a report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from eab import rational3 as _rational3
from itertools import combinations
from functools import lru_cache
import math
from math import atan2, hypot, sqrt
from . import exact_geom as _eg

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


from eab.predicates import orient3d


def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def neg(a: Vec3) -> Vec3:
    return (-a[0], -a[1], -a[2])


def mul(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a: Vec3, b: Vec3) -> float:
    if _rational3.fraction_vectors(a, b):
        return _rational3.dot(a, b)
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec3, b: Vec3) -> Vec3:
    if _rational3.fraction_vectors(a, b):
        return _rational3.cross(a, b)
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a: Vec3) -> float:
    """Primal construction avoiding a rounded intermediate squared norm.

    Gate: test_r6fix_norm_does_not_lose_representable_result_to_intermediate_square.
    """
    if any(isinstance(x, Fraction) for x in a):
        q = _eg.vector(a)
        return _eg.sqrt_rational(_eg.dot(q, q))
    result = hypot(*a)
    if not math.isfinite(result) and all(math.isfinite(x) for x in a):
        raise OverflowError("exact geometric norm exceeds finite binary64 range")
    return result


def unit(a: Vec3, *, allow_underflow: bool = False) -> Vec3:
    """Round each exact normalized component once, without a rounded norm.

    allow_underflow is for displays accompanied by the exact direction vector,
    as carried by Cover3 and MarginContact. Other callers fail loudly.
    Gate: test_r7fix_unit_retains_extreme_components_before_normalization.
    """
    return _unit_cached(tuple(a), allow_underflow)


@lru_cache(maxsize=16384)
def _unit_cached(a, allow_underflow):
    q = _eg.vector(a)
    squared = _eg.dot(q, q)
    if not squared:
        raise ZeroDivisionError("unit of zero vector")
    return tuple((-1 if x < 0 else 1) * _eg.sqrt_rational(x*x/squared, allow_underflow=allow_underflow) for x in q)


def angle_between(a: Vec3, b: Vec3) -> float:
    """Angle from exact cross/dot before a common homogeneous rescaling.

    Gate: test_r7fix_angle_between_avoids_intermediate_cross_range_loss.
    """
    a, b = _eg.vector(a), _eg.vector(b)
    c, d = _eg.cross(a, b), _eg.dot(a, b)
    scale = max(abs(d), *map(abs, c))
    if not scale:
        return 0.0
    sine = _eg.sqrt_rational(_eg.dot(c, c)/(scale*scale), allow_underflow=d <= 0)
    return atan2(sine, float(d/scale))


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
    # Derived caches: all source vertex/face content participates in invalidation.
    _normals: list | None = field(default=None, repr=False, compare=False)
    _face_noise: list | None = field(default=None, repr=False, compare=False)
    _vedges: dict | None = field(default=None, repr=False, compare=False)
    _metrics: tuple[float, float, float] | None = field(default=None, repr=False, compare=False)
    _interior: Vec3 | None = field(default=None, repr=False, compare=False)
    _convex_view: object | None = field(default=None, repr=False, compare=False)
    _geometry_signature: tuple | None = field(default=None, repr=False, compare=False)
    source_vertices: tuple[int, ...] = field(default=(), repr=False, compare=False)
    source_faces: tuple[tuple[int, ...], ...] = field(default=(), repr=False, compare=False)

    def _sync_geometry_cache(self) -> None:
        """Invalidate derived data after vertex/face content edits.

        Content, not container identity, defines the cached geometry. Regression
        and internal vertex-key mutation: tests/test_e5b_polyhedron_cache.py.
        """
        signature = (tuple(tuple(p) for p in self.verts),
                     tuple(tuple(f) for f in self.faces))
        if signature != self._geometry_signature:
            for name in ("_edges", "_vf", "_ef", "_edir", "_normals",
                         "_face_noise", "_vedges", "_metrics", "_interior", "_convex_view"):
                setattr(self, name, None)
            self._geometry_signature = signature

    # ---------------- 尺度 ----------------
    def metrics(self) -> tuple[float, float, float]:
        """(C, L, ℓ)：坐标量级 max|x_i|、AABB 对角线（特征长度）、最短棱长。缓存。容差政策见模块文档。"""
        self._sync_geometry_cache()
        if self._metrics is None:
            C = coord_scale(*self.verts)
            lo, hi = self.aabb()
            L = norm(_eg.sub(exact_vector(hi), exact_vector(lo)))
            ell = min((norm(exact_edge_vector(self, (a, b))) for a, b in self.edges()), default=0.0)
            self._metrics = (C, L, ell if ell > 0.0 else (L if L > 0.0 else 1.0))
        return self._metrics

    def edge_noise(self, e: tuple[int, int]) -> float:
        """棱 e 的单位方向的舍入噪声 c·eps·C/|e|（弧度）：刚体运动把顶点挪动 ~eps·C，方向随之转这么多。
        只看**这条棱自己**的长度（纪律 F 的逐特征口径）。零长棱为 +inf。"""
        ell = norm(exact_edge_vector(self, e))
        return noise_floor(self.metrics()[0]) / ell if ell > 0.0 else float("inf")

    def face_noise(self, fi: int) -> float:
        """面 fi 的单位外法向的舍入噪声（弧度）：顶点挪动 δ = c·eps·C 时 Newell 向量（= 2·面积·n）至多变
        δ·周长，方向至多转 δ·周长/(2·面积)。三角形上 2·面积/周长 是内切圆半径——细条三角的法向本来就不准。
        退化面（面积 0）为 +inf。缓存。"""
        self._sync_geometry_cache()
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
        self._sync_geometry_cache()
        cache = self._normals
        if cache is None:
            cache = self._normals = [None] * len(self.faces)
        n = cache[fi]
        if n is None:
            n = cache[fi] = self._newell_normal(fi)
        return n

    def _newell_normal(self, fi: int) -> Vec3:
        try:
            return unit(exact_face_normal(self, fi))
        except ValueError:
            raise ValueError(f"face {fi} {self.faces[fi]} has zero area (collinear or coincident vertices); "
                             f"strip duplicates at the reader boundary") from None

    def face_area(self, fi: int) -> float:
        """Newell area, with exact final halving before the sole rounding.

        Gate: test_g6g05_face_area_rounds_after_final_halving.
        """
        try:
            n = exact_face_normal(self, fi)
        except ValueError:
            return 0.0
        return _eg.sqrt_rational(_eg.dot(n, n) / 4)

    def edges(self) -> list[tuple[int, int]]:
        self._sync_geometry_cache()
        if self._edges is None:
            self._build_topology()
        assert self._edges is not None
        return list(self._edges)

    def vertex_faces(self, vi: int) -> list[int]:
        self._sync_geometry_cache()
        if self._vf is None:
            self._build_topology()
        assert self._vf is not None
        return list(self._vf.get(vi, ()))

    def edge_faces(self, e: tuple[int, int]) -> list[int]:
        self._sync_geometry_cache()
        if self._ef is None:
            self._build_topology()
        assert self._ef is not None
        return list(self._ef.get((min(e), max(e)), ()))

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
        self._sync_geometry_cache()
        if self._edir is None:
            self._build_topology()
        assert self._edir is not None
        return list(self._edir.get((min(e), max(e)), ()))

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
                d = exact_edge_vector(self, (vi, other))
                if norm(d) > 0.0:
                    out.append(unit(d))
        return out

    def vertex_edges(self, vi: int) -> list[tuple[Vec3, float]]:
        """顶点 vi 的入射棱：(由 vi 指向邻点的单位方向, 该棱的方向噪声 `edge_noise`)。零长棱跳过。缓存。"""
        self._sync_geometry_cache()
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
                    d = exact_edge_vector(self, (v, w))
                    ell = norm(d)
                    if ell > 0.0:
                        out.append((unit(d), fl / ell))
                cache[v] = out
        return list(cache.get(vi, ()))

    def edge_dir(self, e: tuple[int, int]) -> Vec3:
        d = exact_edge_vector(self, e)
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
        t = unit(exact_edge_vector(self, (a1, b1)))
        n1, n2 = self.face_normal(f1), self.face_normal(f2)
        return atan2(dot(cross(n1, n2), t), dot(n1, n2))

    # ---------------- 体积与内点 ----------------
    def volume(self) -> float:
        """Signed volume of the triangulated surface; round only the final sum.

        Gate: test_g6g08_mass_properties_use_exact_products_before_final_rounding.
        """
        volume6, _ = _mass_properties(tuple(self.verts), tuple(self.faces))
        return _checked_scalar(volume6 / 6)

    def centroid(self) -> Vec3:
        """Exact first moments, then one final coordinate rounding (not an interior point).

        Gate: test_g6g08_centroid_retains_cancellation_even_when_volume_is_representable.
        """
        volume6, moments = _mass_properties(tuple(self.verts), tuple(self.faces))
        points = tuple(map(exact_vector, self.verts))
        if not volume6:
            return tuple(_checked_scalar(sum(p[k] for p in points) / len(points)) for k in range(3))
        return tuple(_checked_scalar(points[0][k] + moments[k] / (4*volume6)) for k in range(3))

    def interior_point(self) -> Vec3:
        """保证在多面体内部的一点：取各面三角形质心沿内法向微退，取第一个通过内点测试者；
        兜底退回体心（凸体总成立）。微退步长相对体的尺度（此前取 max(1, 尺度)：小于 1 的体会退出体外）。缓存。"""
        self._sync_geometry_cache()
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
        raise ValueError("interior_point: failed to find an interior point — the body is thinner than the coordinate "
                         "resolution (~2·c·eps·C) or is not a closed manifold; margin / overlap predicates cannot "
                         "resolve it at these coordinates")

    def aabb(self) -> tuple[Vec3, Vec3]:
        xs = [p[0] for p in self.verts]
        ys = [p[1] for p in self.verts]
        zs = [p[2] for p in self.verts]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    def translated(self, x: Vec3) -> "Polyhedron":
        """Preserve exact affine values when coordinates or offsets are Fraction.

        Ordinary float construction retains its historical rounding order;
        mixed rational/float input is rationalised before any addition.
        Gate: test_g6f09_mixed_fraction_translation_preserves_exact_affine_coordinates.
        """
        if any(isinstance(c, Fraction) for p in (*self.verts, x) for c in p):
            q = exact_vector(x)
            return Polyhedron([_eg.add(exact_vector(p), q) for p in self.verts], list(self.faces))
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
        try:
            v = self.volume()
        except ValueError as error:
            issues.append(f"invalid volume surface: {error}")
            return issues
        if v <= 0.0:
            issues.append(f"signed volume {v:.6g} <= 0 (global orientation is inward)")
        return issues

    def is_convex(self, tol: float = 1e-12) -> bool:
        """Exact local convexity for a closed outward polyhedron.

        tol is a retained compatibility argument, not a geometric noise band.
        Supplied coordinates, including roundoff in a transformed model, define
        the geometry. Gate: test_g6f03_zero_band_convexity_keeps_every_exact_reflex.
        """
        for e in self.edges():
            if len(self.edge_faces(e)) != 2:
                return False
            if self._exact_dihedral_orientation(e) < 0:
                return False
        return True

    def reflex_edges(self, tol: float = 1e-12) -> list[tuple[int, int]]:
        """Exact negative dihedral signs; tol is compatibility-only, as is_convex."""
        return [e for e in self.edges()
                if len(self.edge_faces(e)) == 2 and self._exact_dihedral_orientation(e) < 0]

    def _exact_dihedral_orientation(self, e: tuple[int, int]):
        """Unnormalised exact sign; neither coordinate scale nor angle noise enters."""
        (f1, a, b), (f2, _, _) = self.edge_traversals(e)
        t = _eg.sub(exact_vector(self.verts[b]), exact_vector(self.verts[a]))
        n1, n2 = exact_face_normal(self, f1), exact_face_normal(self, f2)
        return _eg.dot(_eg.cross(n1, n2), t)


# ------------------------------------------------------------------ 面多边形内点（唯一实现）

def _point_segment_distance(x: Vec3, a: Vec3, b: Vec3) -> float:
    x, a, b = map(exact_vector, (x, a, b))
    return _eg.sqrt_rational(_eg.point_segment_distance_squared(x, a, b))


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
    return _eg.polygon_locate(x, tuple(P.verts[i] for i in P.faces[fi]), tol)


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
    return list(out)


def point_in_polyhedron(p: Vec3, P: Polyhedron, tol: float = 0.0) -> int:
    """Exact supplied-surface membership, with an explicit Euclidean boundary band.

    Nonplanar rings mean deterministic ear-triangulated folded surfaces. Zero
    tolerance adds no noise floor; positive tolerance reports 0 exactly when the
    squared distance to a surface triangle is at most tol**2.
    """
    return _eg.point_in_surface(p, P, tol)


def segment_crosses_face(p: Vec3, q: Vec3, P: Polyhedron, fi: int, tol: float = 0.0) -> bool:
    """Exact transverse open-segment/source-face-interior crossing.

    P must be a valid outward-oriented closed embedded surface, not a single
    open face: crossings on internal fold edges require the solid's two-sided
    membership. An open face-only query is outside this API's contract.
    Coplanar overlap is not a transverse crossing. With positive tol, both
    endpoints must be farther than tol from the crossed triangle's plane and
    the crossing point farther than tol from the source ring boundary.
    """
    return _eg.segment_crosses(p, q, P, fi, tol)


def _inward_vertex_direction(P: Polyhedron, vi: int) -> Vec3 | None:
    """顶点 vi 处关联面外法向之和的反方向（凸角指向体内；反射角可能指向体外——调用方必须复验）。"""
    s = (0.0, 0.0, 0.0)
    for fi in P.vertex_faces(vi):
        s = add(s, P.face_normal(fi))
    if norm(s) <= 1e-12:
        return None
    return neg(unit(s))


def polyhedra_overlap(A: Polyhedron, B: Polyhedron, tol: float = 0.0) -> int:
    """Exact closed-surface relation: interior overlap 1, contact 0, disjoint -1.

    Inputs must be valid outward-oriented closed embedded surfaces; invalid
    topology is outside this API contract. No implicit convexification,
    resolution floor, grid, or random witness is
    used. The general certificate partitions triangle interiors by the other
    surface's planes, including coplanar edge lines; rational inward witnesses
    resolve both coplanar contact and common-edge penetration. Convex SAT is
    used only after exact support certificates for the supplied surface.

    Positive tol is a reporting band only on the disjoint side: true interior
    overlap remains 1, while exact surface distance <= tol reports 0.
    """
    return _eg.surface_overlap(A, B, tol)


def _segment_closest_points(p1: Vec3, p2: Vec3, q1: Vec3, q2: Vec3) -> tuple[Vec3, Vec3]:
    """Exact affine closest-point witnesses; no implicit parallel window.

    Gate: test_r6fix_closest_points_do_not_drop_nonzero_segments.
    """
    p1, p2, q1, q2 = map(exact_vector, (p1, p2, q1, q2))
    zero, one = Fraction(0), Fraction(1)
    d1, d2, r = sub(p2, p1), sub(q2, q1), sub(p1, q1)
    a, e, f = dot(d1, d1), dot(d2, d2), dot(d2, r)
    if a <= 0.0 and e <= 0.0:
        return p1, q1
    if a <= 0.0:
        s, t = zero, min(one, max(zero, f / e))
    else:
        c = dot(d1, r)
        if e <= 0.0:
            s, t = min(one, max(zero, -c / a)), zero
        else:
            b = dot(d1, d2)
            den = a * e - b * b
            s = min(one, max(zero, (b * f - c * e) / den)) if den else zero
            t = (b * s + f) / e
            if t < 0.0:
                s, t = min(one, max(zero, -c / a)), zero
            elif t > 1.0:
                s, t = min(one, max(zero, (b - c) / a)), one
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


def _exact_line_params(p1: Vec3, d1: Vec3, p2: Vec3, d2: Vec3) -> tuple[float, float] | None:
    """两直线最近点参数的**有理数精确**求法（对给定的浮点坐标精确）：n = d1 × d2，s = ((p2 − p1) × d2)·n/|n|²，
    t = ((p2 − p1) × d1)·n/|n|²。近平行（sin²θ ≲ 1e-12）时浮点里 |n|² 与分子都被舍入吞掉（叉积式也只把 eps/sin²θ 降到
    eps/sinθ，旋转后的棱向量自带舍入，θ = 1e-9 时 s 仍是垃圾）——信息只在坐标的全部位里，所以用 Fraction 算（G6 第四轮 major）。
    平行（|n|² = 0）返回 None。"""
    from fractions import Fraction as F
    P1, D1, P2, D2 = ([F(x) for x in v] for v in (p1, d1, p2, d2))
    n = [D1[1] * D2[2] - D1[2] * D2[1], D1[2] * D2[0] - D1[0] * D2[2], D1[0] * D2[1] - D1[1] * D2[0]]
    nn = sum(c * c for c in n)
    if nn == 0:
        return None
    w = [a - b for a, b in zip(P2, P1)]
    wd2 = [w[1] * D2[2] - w[2] * D2[1], w[2] * D2[0] - w[0] * D2[2], w[0] * D2[1] - w[1] * D2[0]]
    wd1 = [w[1] * D1[2] - w[2] * D1[1], w[2] * D1[0] - w[0] * D1[2], w[0] * D1[1] - w[1] * D1[0]]
    return float(sum(a * b for a, b in zip(wd2, n)) / nn), float(sum(a * b for a, b in zip(wd1, n)) / nn)


def _seg_seg_distance(p1: Vec3, p2: Vec3, q1: Vec3, q2: Vec3) -> float:
    """Exact relative squared distance, rounded only after the minimum is known.

    No projected global point is rounded then subtracted. Shared production
    arithmetic: this construction helper is not an independent G0 oracle.
    Gate: test_r6fix_segment_distance_keeps_exact_local_difference_at_large_coordinates.
    """
    return _eg.sqrt_rational(_eg.segment_distance_squared(p1, p2, q1, q2))


def _point_face_distance(p: Vec3, P: Polyhedron, fi: int) -> float | None:
    """点到面**多边形**的距离；投影落在多边形外则返回 None（由顶点/棱对覆盖）。

    多边形内点用 `point_in_face_polygon`（非凸面正确）。此前用半平面核（审查 C7：L 块臂上的
    投影被判"面外"，距离高估 0.673 vs 0.5）。边界带取 0：落在棱上的投影由顶点/棱对同样给出。
    """
    p = exact_vector(p)
    n = exact_face_normal(P, fi)
    o = exact_vector(P.verts[P.faces[fi][0]])
    nn = _eg.dot(n, n)
    g = _eg.dot(n, _eg.sub(p, o))
    proj = _eg.sub(p, _eg.mul(n, g / nn))
    if not point_in_face_polygon(proj, P, fi, 0.0):
        return None
    return _eg.sqrt_rational(g*g / nn)


def _checked_scalar(value):
    """Final rational construction must not silently overflow or erase a nonzero."""
    result = float(value)
    if not math.isfinite(result):
        raise OverflowError("exact construction exceeds finite binary64 range")
    if value and not result:
        raise ArithmeticError("nonzero exact construction is below binary64 output range")
    return result


@lru_cache(maxsize=1024)
def _mass_properties(vertices, faces):
    """Six times signed volume and its relative first moment, on the actual surface."""
    points = tuple(map(exact_vector, vertices))
    origin = points[0]
    relative = tuple(_eg.sub(p, origin) for p in points)
    volume6, moments = Fraction(0), (Fraction(0),)*3
    for _, tri in _eg.triangulate(vertices, faces):
        a, b, c = (relative[i] for i in tri)
        weight = _eg.dot(a, _eg.cross(b, c))
        volume6 += weight
        moments = _eg.add(moments, _eg.mul(_eg.add(_eg.add(a, b), c), weight))
    return volume6, moments


def _surface_distance_edges(P):
    """All geometric surface edges, including interior ridges of folded rings.

    Coplanar triangulation diagonals are not geometric ridges and cannot add a
    smaller minimum than the face projections and boundary edges already tested.
    Gate: test_g6g04_folded_internal_ridges_attain_slab_distance.
    """
    return exact_surface(P).edges()


def _surfaces_intersect(triangles_a, triangles_b):
    """Exact triangle crossings, after exact per-triangle AABB rejection."""
    bounds = lambda tri: tuple((min(p[k] for p in tri), max(p[k] for p in tri)) for k in range(3))
    first = tuple((tri, bounds(tri)) for _, tri in triangles_a)
    second = tuple((tri, bounds(tri)) for _, tri in triangles_b)
    for a, ba in first:
        for b, bb in second:
            if any(ha < lb or hb < la for (la, ha), (lb, hb) in zip(ba, bb)):
                continue
            if _eg.triangle_intersection(a, b):
                return True
    return False


def brute_feature_distance(A: Polyhedron, B: Polyhedron, *, allow_underflow: bool = False) -> float:
    """Exact all-feature surface distance, with one final floating construction.

    Triangulated face projections include vertex/edge endpoints; all geometric
    surface-edge pairs (including folded-ring ridges) provide remaining minima. This is internal corroboration,
    not an independent G0 oracle: it shares exact_geom primitives with production.
    G0 uses the separate g03_surface_oracle. Explicit allow_underflow is only for
    display callers retaining an exact squared-distance certificate.
    Gate: test_r6fix_brute_distance_does_not_subtract_rounded_global_projections.
    """
    vertices = (tuple(map(exact_vector, A.verts)), tuple(map(exact_vector, B.verts)))
    triangles = (_eg.triangles(A), _eg.triangles(B))
    if _surfaces_intersect(*triangles):
        return 0.0
    best = None
    for points, faces in ((vertices[0], triangles[1]), (vertices[1], triangles[0])):
        for p in points:
            for _, tri in faces:
                value = _eg.point_triangle_distance_squared(p, tri)
                best = value if best is None else min(best, value)
    edges_a, edges_b = _surface_distance_edges(A), _surface_distance_edges(B)
    for ea in edges_a:
        for eb in edges_b:
            value = _eg.segment_distance_squared(vertices[0][ea[0]], vertices[0][ea[1]],
                                                 vertices[1][eb[0]], vertices[1][eb[1]])
            best = value if best is None else min(best, value)
    return float('inf') if best is None else _eg.sqrt_rational(best, allow_underflow=allow_underflow)


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
    if orient3d(a, b, c, d) < 0:
        P = Polyhedron([a, b, c, d], [tuple(reversed(f)) for f in P.faces])
    return P


class HullNumericalFailure(ValueError):
    """convex_hull_3d 在给定容差下自检失败（数值问题，不是输入退化）。"""


_HULL_TOL_MAX = 1e-6                 # 自适应放大容差的上限（相对 L）


def convex_hull_3d(points: list[Vec3], tol: float = 1e-12, *, max_tol: float = _HULL_TOL_MAX) -> Polyhedron:
    """Exact convex hull of the supplied points; tol/max_tol are compatibility arguments.

    No coordinate is moved and no feature is flattened. The result has triangular
    faces and only extreme vertices. Exact coplanar merging is a separate API.
    """
    return convex_hull_3d_eps(points, tol, max_tol=max_tol)[0]


def convex_hull_3d_eps(points: list[Vec3], tol: float = 1e-12, *, max_tol: float = _HULL_TOL_MAX) -> tuple[Polyhedron, float]:
    """Exact hull and zero construction band (the former adaptive band is removed)."""
    if not 0.0 <= tol < 1e-3:
        raise ValueError(f"convex_hull_3d: invalid compatibility tolerance {tol!r}")
    return _quickhull(points, tol), 0.0


def _quickhull(points: list[Vec3], tol: float) -> Polyhedron:
    """Build once, then independently certify every input against every exact plane."""
    pts = list(dict.fromkeys(points))
    P, _, _ = _quickhull_once(pts, tol, set())
    # Fraction reference is deliberately independent of the filtered orient3d
    # used by construction; a corrupt visibility predicate must fail closed.
    for face in P.faces:
        a,b,c = (_eg.vector(P.verts[i]) for i in face[:3])
        n = _eg.cross(_eg.sub(b,a),_eg.sub(c,a))
        if not any(n) or any(_eg.dot(n,_eg.sub(_eg.vector(q),a)) > 0 for q in pts):
            raise HullNumericalFailure('convex_hull_3d: exact supporting-plane certificate failed')
    if any(len(P.edge_traversals(e)) != 2 for e in P.edges()):
        raise HullNumericalFailure('convex_hull_3d: open surface')
    return P


def _sliver_middle_vertex(P: Polyhedron, eps_d: float) -> int | None:
    """Compatibility diagnostic: only an exactly collinear middle point is redundant."""
    for f in P.faces:
        if len(f) != 3:
            continue
        a,b,c = (_eg.vector(P.verts[i]) for i in f)
        if not any(_eg.cross(_eg.sub(b,a),_eg.sub(c,a))):
            axis=max(range(3),key=lambda k:max(p[k] for p in (a,b,c))-min(p[k] for p in (a,b,c)))
            return sorted(f,key=lambda i:P.verts[i][axis])[1]
    return None


def _quickhull_once(pts: list[Vec3], tol: float, skip: set[int]) -> tuple[Polyhedron, list[int], float]:
    """Exact incremental hull. Floating distances may order work but never reject a point."""
    cand = [i for i in range(len(pts)) if i not in skip]
    if len(cand) < 4:
        raise ValueError('need >= 4 non-degenerate points')
    v = [_eg.vector(p) for p in pts]
    i0 = min(cand,key=lambda i:v[i])
    i1 = max(cand,key=lambda i:_eg.dot(_eg.sub(v[i],v[i0]),_eg.sub(v[i],v[i0])))
    u = _eg.sub(v[i1],v[i0])
    if not any(u):
        raise ValueError('points are coincident')
    def off_line(i):
        n=_eg.cross(u,_eg.sub(v[i],v[i0]))
        return _eg.dot(n,n)
    i2 = max(cand,key=off_line)
    if off_line(i2) == 0:
        raise ValueError('points are collinear')
    n=_eg.cross(u,_eg.sub(v[i2],v[i0]))
    i3=max(cand,key=lambda i:abs(_eg.dot(n,_eg.sub(v[i],v[i0]))))
    if _eg.dot(n,_eg.sub(v[i3],v[i0])) == 0:
        raise ValueError('points are coplanar')
    base=[i0,i1,i2,i3]
    faces=[]
    for tri,opposite in (((i0,i1,i2),i3),((i0,i3,i1),i2),((i1,i3,i2),i0),((i2,i3,i0),i1)):
        if orient3d(*(pts[i] for i in tri),pts[opposite]) > 0:
            tri=(tri[0],tri[2],tri[1])
        faces.append(tri)
    for ip in cand:
        if ip in base:
            continue
        signs=[orient3d(*(pts[i] for i in f),pts[ip]) for f in faces]
        if max(signs) <= 0:
            continue
        visible={j for j,s in enumerate(signs) if s >= 0}
        owner={ (f[k],f[(k+1)%3]):j for j,f in enumerate(faces) for k in range(3) }
        horizon=[]
        for j in visible:
            f=faces[j]
            for k in range(3):
                a,b=f[k],f[(k+1)%3]
                if owner.get((b,a)) not in visible:
                    horizon.append((a,b))
        if not horizon or len({a for a,b in horizon}) != len(horizon):
            raise HullNumericalFailure('convex_hull_3d: exact horizon is not a disk')
        faces=[f for j,f in enumerate(faces) if j not in visible]+[(a,b,ip) for a,b in horizon]
    # Merge exact coplanar triangles, then strip collinear ring points. This is
    # essential: a simplex seed can contain a point in a final facet/edge interior.
    P=merge_coplanar(Polyhedron(list(pts),faces),0.0)
    rings=[]
    for f in P.faces:
        ring=list(f)
        changed=True
        while changed and len(ring)>3:
            changed=False
            for k,b in enumerate(ring):
                a,c=ring[k-1],ring[(k+1)%len(ring)]
                if not any(_eg.cross(_eg.sub(v[b],v[a]),_eg.sub(v[c],v[b]))):
                    ring.pop(k);changed=True;break
        rings.append(tuple(ring))
    used=sorted({i for f in rings for i in f})
    remap={i:j for j,i in enumerate(used)}
    tris=[(remap[f[0]],remap[f[k]],remap[f[k+1]]) for f in rings for k in range(1,len(f)-1)]
    return Polyhedron([pts[i] for i in used],tris,source_vertices=tuple(used)),used,0.0


def merge_coplanar(P: "Polyhedron", tol: float = 1e-9) -> "Polyhedron":
    """Merge edge-connected faces only when their supporting planes are exactly equal.

    Vertex numbering and collinear boundary vertices are retained. ``tol`` is a
    compatibility argument, never a near-coplanarity test. Disconnected coplanar
    patches stay separate; holes and pinched non-simple merged rings raise.
    """
    groups = []
    for fi, face in enumerate(P.faces):
        verts = [_eg.vector(P.verts[i]) for i in face]
        n = _eg.normal(verts)
        if any(_eg.dot(n, _eg.sub(p, verts[0])) != 0 for p in verts):
            # A Newell vector is not a supporting plane of a folded polygon.
            # Preserve its surface hint separately; exact_surface triangulates it.
            groups.append((n, None, [fi]))
            continue
        hit = None
        for gi, (gn, go, fis) in enumerate(groups):
            if go is None:
                continue
            if (_eg.dot(n, gn) > 0 and not any(_eg.cross(n, gn))
                    and all(_eg.dot(gn, _eg.sub(p, go)) == 0 for p in verts)):
                hit = gi
                break
        if hit is None:
            groups.append((n, verts[0], [fi]))
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


def exact_vector(p):
    """The exact rational coordinates, without a float round trip."""
    return _eg.vector(p)


def exact_edge_vector(P: Polyhedron, e):
    return _eg.sub(exact_vector(P.verts[e[1]]), exact_vector(P.verts[e[0]]))


def exact_face_normal(P: Polyhedron, fi: int):
    """Exact unnormalised Newell vector (a direction, not a fitted supporting plane)."""
    return _eg.normal([exact_vector(P.verts[i]) for i in P.faces[fi]])


def exact_surface(P: Polyhedron) -> Polyhedron:
    """Triangulate only nonplanar faces; retain input vertices and face provenance."""
    all_tris = _eg.triangulate(tuple(P.verts), tuple(P.faces))
    faces, sources = [], []
    for fi, face in enumerate(P.faces):
        n = exact_face_normal(P, fi)
        o = exact_vector(P.verts[face[0]])
        if all(_eg.dot(n, _eg.sub(exact_vector(P.verts[i]), o)) == 0 for i in face):
            faces.append(face)
            sources.append((fi,))
        else:
            for fidx, tri in all_tris:
                if fidx == fi:
                    faces.append(tri)
                    sources.append((fi,))
    return Polyhedron(list(P.verts), faces, source_vertices=tuple(range(len(P.verts))),
                      source_faces=tuple(sources))


def exact_convex_view(P: Polyhedron) -> Polyhedron:
    """Explicit convex API semantics: conv(input vertices), with source maps.

    If every input face already is a complete exact supporting facet the input
    numbering is retained. Otherwise canonical facets are ordered deterministically
    and source_faces lists the input face hints containing that facet's vertices.
    General surface APIs never call this implicitly. Non-self cached views are
    immutable coordinate/ring payloads and every public result is isolated;
    source content is checked before reuse. Gate: test_g6f01_convex_view_mutation_cannot_poison_unchanged_source.
    """
    P._sync_geometry_cache()
    if P._convex_view is not None:
        if P._convex_view is P:
            return P
        verts, faces, source_vertices, source_faces = P._convex_view
        out = Polyhedron(list(verts), list(faces), source_vertices=source_vertices,
                         source_faces=source_faces)
        out._sync_geometry_cache()
        out._convex_view = out
        return out
    H = merge_coplanar(convex_hull_3d(P.verts), 0.0)
    original = {p:i for i,p in enumerate(P.verts)}
    source = tuple(original[p] for p in H.verts)
    rings = [tuple(source[i] for i in f) for f in H.faces]
    matches = {frozenset(f):i for i,f in enumerate(P.faces)}
    if (len(source) == len(P.verts) and len(rings) == len(P.faces)
            and all(frozenset(f) in matches
                    and _same_oriented_ring(f, P.faces[matches[frozenset(f)]]) for f in rings)):
        P._convex_view = P
        return P
    order = sorted(range(len(H.verts)), key=lambda i: source[i])
    remap = {old:new for new,old in enumerate(order)}
    faced = sorted(zip(H.faces, rings), key=lambda item: tuple(sorted(item[1])))
    out = Polyhedron([H.verts[i] for i in order],
                     [tuple(remap[i] for i in f) for f,_ in faced],
                     source_vertices=tuple(source[i] for i in order),
                     source_faces=tuple(tuple(fi for fi,hint in enumerate(P.faces)
                                              if set(ring).issubset(hint)) for _,ring in faced))
    out._sync_geometry_cache()
    out._convex_view = out
    P._convex_view = (tuple(out.verts), tuple(out.faces), out.source_vertices, out.source_faces)
    return out


def _same_oriented_ring(first, second):
    """Cyclic equality, not vertex-set equality: reversed/crossed hints are not facets.

    Gate: test_g6f02_convex_model_is_independent_of_face_hint_winding.
    """
    first, second = tuple(first), tuple(second)
    return len(first) == len(second) and any(first == second[k:] + second[:k]
                                           for k in range(len(second)))


def exact_point_in_polyhedron(p: Vec3, P: Polyhedron) -> int:
    """Zero-band membership in the deterministic triangulated input surface."""
    return _eg.point_in_surface(p, P)


def exact_segment_crosses_face(p: Vec3, q: Vec3, P: Polyhedron, fi: int) -> bool:
    """Zero-band transverse crossing of the open segment and input face interior."""
    return _eg.segment_crosses(p, q, P, fi)


def exact_point_in_convex_polyhedron(p: Vec3, P: Polyhedron) -> int:
    """Membership in conv(P.verts), independently of the input face hints."""
    P = exact_convex_view(P)
    p = exact_vector(p)
    boundary = False
    for fi, face in enumerate(P.faces):
        d = _eg.dot(exact_face_normal(P, fi), _eg.sub(p, exact_vector(P.verts[face[0]])))
        if d > 0:
            return -1
        boundary |= d == 0
    return 0 if boundary else 1


def exact_convex_overlap(A: Polyhedron, B: Polyhedron) -> int:
    """Exact SAT: interiors intersect=1, boundary only=0, disjoint=-1.

    Explicitly convex: both bodies mean the convex hull of their input vertices.
    Axes are exact unnormalised facet normals and pairwise edge cross products.
    """
    A, B = exact_convex_view(A), exact_convex_view(B)
    av, bv = [exact_vector(p) for p in A.verts], [exact_vector(p) for p in B.verts]
    axes = [exact_face_normal(P, fi) for P in (A, B) for fi in range(len(P.faces))]
    axes.extend(_eg.cross(exact_edge_vector(A, ea), exact_edge_vector(B, eb))
                for ea in A.edges() for eb in B.edges())
    boundary = False
    for axis in axes:
        if not any(axis):
            continue
        x, y = [_eg.dot(axis, p) for p in av], [_eg.dot(axis, p) for p in bv]
        gap = max(min(x)-max(y), min(y)-max(x))
        if gap > 0:
            return -1
        boundary |= gap == 0
    return 0 if boundary else 1


def exact_triangle_intersection(first, second):
    """Exact closed triangle intersection vertices; empty if disjoint."""
    return _eg.triangle_intersection(first, second)
