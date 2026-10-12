"""L2 裕度层：**安全距离即接触量**。这一层是"去岩石化"的铰链。

## 定理一 · 膨胀恒等式

把动体 A 按半径 δ 充气（Minkowski 加一个 δ-球 B_δ），入口块也只是充气同样一个球：

    E(A_δ, B) = B ⊕ (−A_δ) = B ⊕ (−(A ⊕ B_δ)) = B ⊕ (−A) ⊕ (−B_δ) = E(A,B) ⊕ B_δ

（末一步用球的对称性 −B_δ = B_δ。）于是

    「A 与 B 始终保持 δ 以上的间距」 ⟺ 「参考点不落进 E(A,B) 膨胀 δ 之后的集合」

**接触不再必须是物理挤压。** "离行人两米"与"不许贯入行人"是同一个几何命题，只差一次膨胀。

## 定理二 · 构型空间距离 = 工作空间距离

对 E 外的构型点 x：

    dist(x, E) = d(A + x, B)

（证：dist(x,E) = min{|x−u| : (A+u) ∩ B ≠ ∅} = 把两体推到相碰所需的最小平移 = 两体间距。）

这条把"构型点离障碍多远"与"两个物体离多远"划了等号，是裕度层全部数值内容的来源，
也是本层唯一需要**独立验证**的命题（凸情形可显式造出 E 直接量，见 `distance_to_convex_entrance`）。

## 定理三 · 裕度即接触

    margin_gap(x) = d(A+x, B) − δ  ；  ≤ 0 即「广义接触闭合」

于是约束 margin_gap ≥ 0 的 KKT 乘子就是**虚拟接触力**——整套接触力学（互补、摩擦、活动集）
原样适用于安全裕度问题，不需要另起炉灶。

## 定理四 · 球膨胀是 C^{1,1} 正则化

∂E 在顶点/棱处法向是**集值**的（法锥有非零立体角）；膨胀之后

    n(x) = (x − proj_E(x)) / |x − proj_E(x)|

处处**单值**，且因为凸集投影是非扩张映射，n 在 {dist ≥ δ} 上 Lipschitz，常数 ≤ 2/δ。
尖角变圆角，梯度不再跳——这对可微接触直接有用（见 `tests/test_margin.py` 的实测）。

## E5 契约：默认精确，显式局部贯入厚度窗口（非 PD）

给定二进制坐标按其精确有理值解释。默认 `contact_window=None` 不使用库内 ctol：
严格贯入给 `(0, ("PENETRATING",))` / INSIDE；真实正间隙即使小于旧分辨率也不钳零。
盖距离/δ/关注带/接触窗的分支以原始坐标构造的有理平方距比较；浮点只报告距离和见证。
门：`tests/test_margin_exact.py::test_default_has_no_hidden_contact_resolution` 与
`test_inflated_boundary_comparison_does_not_use_a_float_sqrt_or_implicit_band`。

调用方可以显式给 `contact_window=w`（局部贯入厚度窗口，参数名为兼容保留；不是整体最短
分离平移的欧氏贯入深度 PD）。分离侧精确距离 ≤ w 报距离零与相触；贯入侧必须有
精确证书证明窗口可接受：`exact_sweep.contact_models` 的六个 ±w 坐标轴平移，或经验证
星核的内核收缩证明贯入仅落在厚度 ≤ w 的表面壳层；原几何模型也保留。前者只证明内部
不相交距离的下确界 rho ≤ w，不证明闭集完全分离 PD_closed ≤ w（紧贴封闭空腔反例）；
后者是局部接触厚度上界。有限证书不是完整欧氏距离偏置，不把证书
失败说成 PD > w；无证书时保持 PENETRATING。六轴证书及 L1 半径构造依赖坐标系，可能漏掉
长度 ≤ w 的斜向脱离，不保证旋转不变性。互锁在完全相同的有限模型集上求最早根。
独立可靠性与限制反例门：`tests/test_perf_contact_window.py`。
窗口是调用方选择的报告模型，不是恢复被舍入丢失的理想几何。`geom_tol` 仅留兼容签名。
旧公式 `contact_resolution(A,B)` 只是调用方可选择的数值；库不隐式调用它。
门：`test_explicit_window_matches_exact_interval_oracle`；不变性文件的旧断言全部留在显式
窗口模式，并添加同一 touch/subtol 网格逐格的独立整数四面体并集 SAT 默认精确 oracle。

默认最小距离及并列用精确平方距；显式窗口模式保留旧的浮点见证输出与舍入并列报告顺序，
该排序不改变精确的贯入/接触/关注带判定。`atol=None` 不引入隐式 δ 边界带。
分离侧保留盖见证与不经法锥的全特征距离对拍；其舍入界仅审核浮点构造，不决定几何状态。
输入必须是有效闭合曲面。源面非共面的盖仍遵守 covers3 的源面描述符契约；冻结盖解析式
不自动钳零。贯入哨兵没有可冻结的盖。
"""

from __future__ import annotations
from eab.construction import scalar_rational

import sys
import math
from fractions import Fraction
from functools import lru_cache
from dataclasses import dataclass

from .kernel3d import exact_geom as _exact
from .dual import Number
from .kernel3d.covers3 import Cover3, _qclosest_hull, enumerate_covers3
from .kernel3d.frozen import frozen_gap, frozen_normal, _normalized_difference
from .kernel3d.geom3 import (Polyhedron, Vec3, add, brute_feature_distance, convex_hull_3d, norm,
                             polyhedra_overlap, sub, unit)

OUTSIDE, ON_BOUNDARY, INSIDE = -1, 0, 1
PENETRATING = "PENETRATING"            # 贯入哨兵标签：("PENETRATING",)

_EPS = sys.float_info.epsilon
REL_GEOM_TOL = 1e-9                    # 相触分辨率：特征长度 L 的相对量
REL_BOUNDARY_TOL = 1e-12               # inflated_membership 的边界带：L 的相对量
ROUNDING_C = 64.0                      # 舍入地板 c·eps·C 的系数 c


# ------------------------------------------------------------------ 容差政策（纪律 F）

def characteristic_length(*bodies: Polyhedron) -> float:
    """特征长度 L：各体"首顶点到最远顶点的距离"取最小。刚体运动下不变（顶点编号不变），缩放下 ×s；
    介于半径与直径之间。不用 AABB（旋转会改变它）。"""
    out = float("inf")
    for P in bodies:
        v0 = P.verts[0]
        out = min(out, max(norm(_exact.sub(_exact.vector(v), _exact.vector(v0))) for v in P.verts))
    return out


def coordinate_magnitude(*bodies: Polyhedron) -> float:
    """坐标量级 C = 全部顶点坐标分量的最大绝对值（舍入地板用）。"""
    return max(abs(c) for P in bodies for v in P.verts for c in v)


def rounding_floor(*bodies: Polyhedron) -> float:
    """c·eps·max(C, L)：顶点坐标自身的舍入，以及由它引起的有符号距离、间隙的舍入量级。"""
    return ROUNDING_C * _EPS * max(coordinate_magnitude(*bodies), characteristic_length(*bodies))


def effective_geom_tol(A: Polyhedron, B: Polyhedron, geom_tol: float | None = None) -> float:
    """相触分辨率：geom_tol=None 时 max(1e-9·L, 64·eps·C)；显式给出时按绝对长度，但不低于舍入地板。"""
    base = REL_GEOM_TOL * characteristic_length(A, B) if geom_tol is None else scalar_rational(geom_tol)
    return max(base, rounding_floor(A, B))


def _tie_groups(items: list, keys: list, window: float) -> list:
    """按 key 升序；key 相差 ≤ window（舍入意义上的并列）的一组内按枚举序（items 的原次序）排。"""
    order = [i for _, i in sorted((key, i) for i, key in enumerate(keys))]
    out: list = []
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and keys[order[j + 1]] - keys[order[i]] <= window:
            j += 1
        out.extend(items[k] for k in sorted(order[i:j + 1]))
        i = j + 1
    return out


# ------------------------------------------------------------------ 见证与距离

def cover_witness(c) -> tuple[float, Vec3 | None] | None:
    """显示见证自检：(已舍入 point_a/point_b 的间距, 单位方向 B→A)。

    该显示距离只用于见证构造误差自检，不是精确源特征的最终距离。
    body_distance / margin_contacts 的最终标量从原坐标精确距离平方构造。
    保留点误差诊断，不能用证书距离替换后让坏显示见证逃过旧自检门。
    """
    if c.point_a is None or c.point_b is None:
        return None
    v = sub(c.point_a, c.point_b)
    d = norm(v)
    if c.in_extent and c.exact_gap_sign is not None and c.normal is not None:
        # For an in-extent cover, its exact signed gap orients the exact-source
        # normal from B to A. Global display points can coincide or rotate this
        # vector after rounding; they remain only a construction self-check.
        n = tuple(c.exact_gap_sign*x for x in c.normal) if c.exact_gap_sign else None
    else:
        n = unit(v) if d > 0.0 else None
    return d, n


def _surface_view(vertices, faces):
    """Fresh mutable view over an immutable, content-keyed cache payload."""
    vertices, faces, labels = _surface_payload(vertices, faces)
    return Polyhedron(list(vertices), list(faces)), labels


@lru_cache(maxsize=1024)
def _surface_payload(vertices, faces):
    """Only folded rings are expanded; exact planar source labels are retained."""
    points = tuple(_exact.vector(_mapped_value) for _mapped_value in vertices)
    folded = set()
    for fi, face in enumerate(faces):
        p = tuple(points[i] for i in face)
        n = _exact.normal(p)
        if any(_exact.dot(n, _exact.sub(q, p[0])) for q in p[1:]):
            folded.add(fi)
    if not folded:
        return vertices, faces, tuple(("face", fi) for fi in range(len(faces)))
    triangles = _exact.triangulate(vertices, faces)
    out, labels = [], []
    for fi, face in enumerate(faces):
        if fi not in folded:
            out.append(face)
            labels.append(("face", fi))
        else:
            for source, tri in triangles:
                if source == fi:
                    out.append(tri)
                    labels.append(("face", fi, "triangle", *tri))
    return vertices, tuple(out), tuple(labels)


def _witnesses(A: Polyhedron, B: Polyhedron, tol: float, *, exact_surface=False) -> list[tuple]:
    """Cover witnesses; default exact path uses actual triangles of folded rings."""
    if exact_surface:
        A, af = _surface_view(tuple(A.verts), tuple(A.faces))
        B, bf = _surface_view(tuple(B.verts), tuple(B.faces))
    out = []
    for c in enumerate_covers3(A, B, window=float("inf"), tol=tol):
        if not c.in_extent:
            continue
        w = cover_witness(c)
        if w is not None:
            if exact_surface:
                if c.a_feature[0] == "face":
                    c.a_feature = af[c.a_feature[1]]
                if c.b_feature[0] == "face":
                    c.b_feature = bf[c.b_feature[1]]
            out.append((c, w[0], w[1]))
    return out


def contact_resolution(A: Polyhedron, B: Polyhedron, geom_tol: float | None = None) -> float:
    """Legacy caller-selectable window, never an implicit default in E5b.

    max(geom_tol_eff, 1e-12 * max AABB diagonal) + rounding_floor.
    Pass this value explicitly as contact_window to request old contact reports.
    """
    diag = max(A.metrics()[1], B.metrics()[1])
    return max(effective_geom_tol(A, B, geom_tol), 1e-12 * diag) + rounding_floor(A, B)


def _contact_window(contact_window):
    """No implicit tolerance: None and zero both mean exact contact."""
    if contact_window is None:
        return Fraction(0)
    if not math.isfinite(contact_window) or contact_window < 0:
        raise ValueError("contact_window must be finite and nonnegative")
    return Fraction(contact_window)


@lru_cache(maxsize=16384)
def _witness_squared(vertices_a, faces_a, vertices_b, faces_b, label):
    """Squared local-cover distance on exact input coordinates, before construction."""
    kind, fa, fb = label
    av, bv = tuple(_exact.vector(_mapped_value) for _mapped_value in vertices_a), tuple(_exact.vector(_mapped_value) for _mapped_value in vertices_b)
    if kind == "FV":
        return _witness_squared(vertices_b, faces_b, vertices_a, faces_a, ("VF", fb, fa))
    if kind == "EV3":
        return _witness_squared(vertices_b, faces_b, vertices_a, faces_a, ("VE3", fb, fa))
    if kind == "VF":
        face = tuple(bv[i] for i in (fb[3:] if len(fb) == 6 else faces_b[fb[1]]))
        n = _exact.normal(face)
        h = _exact.dot(n, _exact.sub(av[fa[1]], face[0]))
        return h*h/_exact.dot(n, n)
    if kind == "EE":
        n = _exact.cross(_exact.sub(av[fa[2]], av[fa[1]]), _exact.sub(bv[fb[2]], bv[fb[1]]))
        h = _exact.dot(n, _exact.sub(av[fa[1]], bv[fb[1]]))
        return h*h/_exact.dot(n, n)
    if kind == "VE3":
        u, w = _exact.sub(bv[fb[2]], bv[fb[1]]), _exact.sub(av[fa[1]], bv[fb[1]])
        n = _exact.cross(u, w)
        return _exact.dot(n, n)/_exact.dot(u, u)
    if kind == "VV3":
        d = _exact.sub(av[fa[1]], bv[fb[1]])
        return _exact.dot(d, d)
    raise ValueError(f"unsupported margin cover {label!r}")



def _surface_feature_squared(A, B, label):
    """Actual source feature distance, including every triangle of a folded face."""
    kind, fa, fb = label
    if kind == "FV":
        return _surface_feature_squared(B, A, ("VF", fb, fa))
    if kind == "VF" and len(fb) == 2:
        _, labels = _surface_view(tuple(B.verts), tuple(B.faces))
        pieces = [f[3:] for f in labels if len(f) == 6 and f[1] == fb[1]]
        if pieces:
            point = _exact.vector(A.verts[fa[1]])
            return min(_exact.point_triangle_distance_squared(point, tuple(_exact.vector(B.verts[i]) for i in tri))
                       for tri in pieces)
    return _witness_squared(tuple(A.verts), tuple(A.faces), tuple(B.verts), tuple(B.faces), label)


def _repair_folded_construction(A, B, c, w, n, squared, rounding):
    """Replace an invalid folded-ring plane witness, not a rounding-level report."""
    target = _exact.sqrt_rational(squared, allow_underflow=True)
    if c.kind not in ("VF", "FV"):
        return w, n
    from .kernel3d.covers3 import _qclosest_triangle
    X, Y, fa, fb = (A, B, c.a_feature, c.b_feature) if c.kind == "VF" else (B, A, c.b_feature, c.a_feature)
    if len(fb) != 2:
        return w, n
    _, faces = _surface_view(tuple(Y.verts), tuple(Y.faces))
    pieces = [f[3:] for f in faces if len(f) == 6 and f[1] == fb[1]]
    if not pieces:
        return w, n
    point = _exact.vector(X.verts[fa[1]])
    vectors = [_qclosest_triangle(*(_exact.sub(_exact.vector(Y.verts[i]), point) for i in tri))
               for tri in pieces]
    delta = min((_exact.dot(v, v), _rank_index, v) for _rank_index, v in enumerate(vectors))[2]
    projected = _exact.add(point, delta)
    a, b = tuple(scalar_rational(_mapped_value) for _mapped_value in point), tuple(scalar_rational(_mapped_value) for _mapped_value in projected)
    if c.kind == "FV":
        a, b = b, a
    c.point_a, c.point_b = a, b
    direction = _exact.mul(delta, -1 if c.kind == "VF" else 1)
    c.exact_normal_direction = direction
    c.exact_gap_sign = 1 if any(direction) else 0
    scale = max(abs(_mapped_value) for _mapped_value in direction)
    n = unit(direction, allow_underflow=True) if scale else None
    return target, n

def _penetration_within_window(A, B, window):
    """Local penetration-thickness window, not Euclidean whole-body depth (PD).

    See exact_sweep.contact_models: original solids, six exact axis shifts of
    length window, and either body's certified inner star core. Any model's
    nonpenetration is sufficient. An axis certificate proves only the infimum
    rho for disjoint interiors <= window, not closed-set separation PD_closed
    <= window (a tight enclosed cavity disproves that). A core certificate
    bounds local radial shell thickness only. Failure does not prove PD > window. Coordinate dependence and missed oblique exits are
    intentional limitations, not rotation-invariant PD decisions.
    interlock solves the first accepted height over this very same model set.
    """
    if not window:
        return False
    from .kernel3d.exact_sweep import contact_models
    return any(polyhedra_overlap(ca, cb, 0) <= 0
               for _, ca, cb in contact_models(A, B, window))


def _resolve(A: Polyhedron, B: Polyhedron, tol: float, geom_tol: float | None,
             contact_window: float | None = None):
    """Exact relation/threshold decisions; floats are only witness constructions.

    geom_tol remains a compatibility argument. The legacy resolution is never
    inferred: the caller must pass contact_window=contact_resolution(A, B).
    The self-check separately certifies exact cover completeness and bounds
    floating witness construction error.
    """
    ctol = _contact_window(contact_window)
    state = polyhedra_overlap(A, B, 0)
    if state == 1 and not _penetration_within_window(A, B, ctol):
        return ctol, 0.0, None, True, Fraction(0)
    wits = []
    rnd = rounding_floor(A, B)
    for c, w, n in _witnesses(A, B, tol, exact_surface=contact_window is None or not ctol):
        d2 = _surface_feature_squared(A, B, c.label())
        w, n = _repair_folded_construction(A, B, c, w, n, d2, rnd)
        wits.append((c, w, n, d2))
    rnd = rounding_floor(A, B)
    if state >= 0:
        return ctol, rnd, wits, True, Fraction(0)
    dmin = min((w for _, w, _, _ in wits), default=float("inf"))
    view_a, _ = _surface_view(tuple(A.verts), tuple(A.faces))
    view_b, _ = _surface_view(tuple(B.verts), tuple(B.faces))
    truth2 = brute_feature_distance(view_a, view_b, squared=True)
    truth = _exact.sqrt_rational(truth2, allow_underflow=True)
    minimum2 = min((row[3] for row in wits), default=None)
    if contact_window is not None:
        # Window mode may retain source-ring labels for legacy reporting, but
        # its contact/inside decisions must use the actual folded surface.
        _, af = _surface_view(tuple(A.verts), tuple(A.faces))
        _, bf = _surface_view(tuple(B.verts), tuple(B.faces))
        if any(len(f) == 6 for f in (*af, *bf)):
            actual = _witnesses(A, B, tol, exact_surface=True)
            minimum2 = min((_surface_feature_squared(A, B, c.label()) for c, _, _ in actual), default=None)
    # G6H-06: completeness is exact; coordinate noise belongs only to the
    # separately retained floating-witness construction check below.
    if minimum2 != truth2 or abs(dmin - truth) > 4.0 * rnd:
        raise RuntimeError(f"margin self-check failed: the covers give distance {dmin!r} but the nearest feature pair "
                           f"is {truth!r} apart (rounding {rnd:.3g}); the cover enumeration "
                           + ("missed the nearest pair (exact squared-distance mismatch)"
                              if minimum2 is None or minimum2 > truth2 else
                              "returned an invalid nearest-feature certificate (exact squared-distance mismatch)"
                              if minimum2 < truth2 else
                              "missed the nearest pair" if dmin > truth else "returned witnesses off the bodies"))
    return ctol, rnd, wits, minimum2 is not None and minimum2 <= ctol*ctol, minimum2


def _resolved(A, B, tol, geom_tol, contact_window):
    """Content-keyed equivalent reuse; no mutable object identity is cached."""
    ctol, rnd, wits, contact, minimum2 = _resolved_cached(tuple(A.verts), tuple(A.faces), tuple(B.verts), tuple(B.faces),
                            tol, geom_tol, contact_window, _resolve, enumerate_covers3,
                            polyhedra_overlap, brute_feature_distance, _witnesses,
                            _penetration_within_window, cover_witness)
    fresh = None if wits is None else [(Cover3(*values), w, n, d2) for values, w, n, d2 in wits]
    return ctol, rnd, fresh, contact, minimum2


@lru_cache(maxsize=1024)
def _resolved_cached(av, af, bv, bf, tol, geom_tol, contact_window,
                     implementation, covers, predicate, distance, witnesses, window_test, construction):
    # Implementation pointers remain key material for deliberate fault injection.
    # Cache only immutable data; even internal callers cannot corrupt later reads
    # by editing their returned covers. Gate: test_margin_internal_cached_records_are_isolated.
    ctol, rnd, wits, contact, minimum2 = _resolve(Polyhedron(av, af), Polyhedron(bv, bf), tol, geom_tol, contact_window)
    payload = None if wits is None else tuple(((c.kind, c.a_feature, c.b_feature, c.normal,
                                               c.gap, c.point_a, c.point_b, c.params, c.area,
                                               c.strict, c.in_extent, c.exact_gap_squared,
                                               c.exact_gap_sign, c.exact_area_squared,
                                               c.exact_normal_direction, c.exact_params), w, n, d2)
                                           for c, w, n, d2 in wits)
    return ctol, rnd, payload, contact, minimum2


def body_distance(A: Polyhedron, B: Polyhedron, *, tol: float = 1e-9, geom_tol: float | None = None,
                  contact_window: float | None = None) -> tuple[float, tuple | None]:
    """Exact default relation and nearest-cover comparison; floating distance output.

    Penetration returns (0, (PENETRATING,)). An explicit contact_window accepts
    certified local penetration thickness and exact separated distance <= w.
    It is not a whole-body Euclidean penetration-depth (PD) threshold: a shell
    certificate does not bound PD, and rejection does not imply PD > w.
    Six-axis sampling/L1 radial shells do not guarantee rotation invariance.
    Window mode retains the historical tie reporting order, while each returned
    distance is constructed from its exact source-feature squared distance.
    """
    ctol, rnd, wits, contact, minimum2 = _resolved(A, B, tol, geom_tol, contact_window)
    if wits is None:
        return 0.0, (PENETRATING,)
    if not wits:
        return (0.0 if contact else float("inf")), None
    if contact_window is None or not ctol:
        c, w, _, d2 = min(wits, key=lambda row: row[3])
        return (0.0 if contact else _exact.sqrt_rational(d2)), c.label()
    c, w, _, d2 = _tie_groups(wits, [t[1] for t in wits], rnd)[0]
    # Retain the caller-requested tie window, not an inaccurate scalar display:
    # global witness points were rounded separately and are only a self-check.
    return (0.0 if contact else _exact.sqrt_rational(d2)), c.label()


# ------------------------------------------------------------------ 裕度接触

@dataclass(slots=True)
class MarginContact:
    label: tuple
    distance: float          # 两体特征对间距（工作空间）；相触分辨率内钳为 0
    margin_gap: float        # distance − delta；≤0 即广义接触闭合
    normal: Vec3 | None      # 单位见证方向 B→A，**单值**（C^{1,1}）；贯入哨兵与相触（distance 0）为 None
    point_a: Vec3 | None     # 贯入哨兵为 None
    point_b: Vec3 | None
    _exact_closed: bool | None = None
    exact_distance_squared: Fraction | None = None  # certificate even below the display range
    exact_normal_direction: tuple[Fraction, ...] | None = None  # B-to-A unnormalised certificate

    @property
    def closed(self) -> bool:
        return self.margin_gap <= 0.0 if self._exact_closed is None else self._exact_closed


def margin_contacts(A: Polyhedron, B: Polyhedron, *, delta: float, band: float = 0.0,
                    tol: float = 1e-9, geom_tol: float | None = None,
                    contact_window: float | None = None) -> list[MarginContact]:
    """Generalized contacts with exact squared-distance inclusion <= delta+band.

    Default penetration returns one closed sentinel; explicit contact_window
    accepts certified local penetration thickness and separated distances <= w.
    This is not a Euclidean whole-body PD threshold; see body_distance.
    Accepted contact distances are zero, normal is None, margin_gap=-delta.
    margin_gap rounds the exact distance-minus-delta expression, not the
    subtraction of two display floats. Display underflow is accompanied by
    exact_distance_squared and the separately exact closed classification.
    Gate: test_margin_contact_difference_is_constructed_before_display_rounding.
    Default ordering uses exact squared distances. Window-mode tie reporting
    retains the historical convention, not distances from rounded global points.
    Gate: test_window_contact_distance_rounds_exact_scalar_not_global_witness_points.
    """
    ctol, rnd, wits, contact, minimum2 = _resolved(A, B, tol, geom_tol, contact_window)
    if wits is None:
        return [MarginContact((PENETRATING,), 0.0, 0.0 - delta, None, None, None)]
    out: list[MarginContact] = []
    ranked = []
    nearest2 = min((row[3] for row in wits), default=None)
    threshold = Fraction(delta) + Fraction(band)
    for c, w, n, d2 in wits:
        if contact and (d2 <= ctol*ctol or d2 == nearest2):
            w, n, d2 = 0.0, None, Fraction(0)
        else:
            w = _exact.sqrt_rational(d2, allow_underflow=True)
        if threshold < 0 or d2 > threshold*threshold:
            continue
        # The display distance may lose a representable margin difference.
        # Keep the exact squared-distance certificate through the subtraction;
        # permitted display underflow cannot affect _exact_closed below.
        gap = _normalized_difference(d2, d2 or Fraction(1), Fraction(delta), allow_underflow=True)
        direction = c.exact_normal_direction
        direction = (tuple(c.exact_gap_sign*x for x in direction)
                     if direction is not None and n is not None else None)
        out.append(MarginContact(c.label(), w, gap, n, c.point_a, c.point_b,
                                 delta >= 0 and d2 <= Fraction(delta)**2, d2, direction))
        ranked.append((d2, out[-1]))
    if contact_window is None or not ctol:
        return [m for _, m in sorted(ranked, key=lambda item: item[0])]
    return _tie_groups(out, [m.margin_gap for m in out], rnd)


def boundary_band(A: Polyhedron, B: Polyhedron, atol: float | None = None) -> float:
    """Legacy caller-selectable boundary band; not used by the exact default.

    Callers wanting the old delta band may explicitly pass atol=boundary_band(A,B).
    """
    base = REL_BOUNDARY_TOL * characteristic_length(A, B) if atol is None else scalar_rational(atol)
    return max(base, rounding_floor(A, B))


def inflated_membership(A: Polyhedron, B: Polyhedron, *, delta: float, tol: float = 1e-9,
                        geom_tol: float | None = None, atol: float | None = None,
                        contact_window: float | None = None) -> int:
    """Exact squared-distance comparison against δ; optional explicit boundary band.

    At exact zero margin, physical contact can still be topological int(E),
    as at a tight-fit seam. Classify that state after the existing distance
    self-check, without changing body_distance or physical-contact reporting.
    Gate: test_r8fix_initial_state3.

    atol=None means zero (no implicit rounding floor). contact_window changes
    only contact reporting by the local penetration-thickness policy (not PD).
    Axis acceptance certifies only disjoint-interior infimum rho <= w, not
    closed-set separation PD_closed <= w; shell acceptance certifies only a
    local radial thickness <= w. Rejection does not certify PD > w.
    """
    ctol, _, wits, contact, minimum2 = _resolved(A, B, tol, geom_tol, contact_window)
    if wits is None:
        return INSIDE
    if contact and delta == 0 and (atol is None or atol == 0) and (contact_window is None or contact_window == 0):
        from .kernel3d.entrance_topology import entrance_membership3
        return entrance_membership3(A, B)
    if not wits:
        return ON_BOUNDARY if contact and delta == 0 else (INSIDE if contact else OUTSIDE)
    d2 = minimum2
    if contact:
        d2 = Fraction(0)
    band = Fraction(0 if atol is None else atol)
    if band < 0:
        raise ValueError("atol must be nonnegative")
    lower, upper = Fraction(delta)-band, Fraction(delta)+band
    if lower > 0 and d2 < lower*lower:
        return INSIDE
    if upper < 0 or d2 > upper*upper:
        return OUTSIDE
    return ON_BOUNDARY


# ------------------------------------------------------------------ 凸情形的独立 oracle

def entrance_block_convex(A: Polyhedron, B: Polyhedron) -> Polyhedron:
    """Exact E(A,B) = conv{b-a} for convex bodies.

    Fractions are formed before subtraction, so no floating derived point is
    ever treated as original data by the exact hull.
    Gate: test_margin_exact::test_entrance_block_forms_differences_before_any_float_rounding.
    """
    pts = [_exact.sub(_exact.vector(b), _exact.vector(a)) for a in A.verts for b in B.verts]
    return convex_hull_3d(pts)


def nearest_point_on_convex_entrance(E: Polyhedron, x: Vec3, *, exact: bool = False) -> Vec3:
    """Nearest point on conv(E.verts); exact=True returns the rational witness.

    The default is a rounded display point, which may equal x at engineering
    coordinates even when the exact distance is nonzero. Distance/normal must
    use the exact witness, never subtract the rounded global display point.
    Gate: test_r6fix_construction::test_g6f08_distance_and_normal_use_exact_relative_projection.
    """
    X = _exact.vector(x)
    displacement = _qclosest_hull(tuple(_exact.sub(_exact.vector(e), X) for e in E.verts))
    point = _exact.add(X, displacement)
    return point if exact else tuple(scalar_rational(_mapped_value) for _mapped_value in point)


def distance_to_convex_entrance(E: Polyhedron, x: Vec3) -> float:
    """Distance constructed from the exact relative projection, rounded once."""
    displacement = _exact.sub(nearest_point_on_convex_entrance(E, x, exact=True), _exact.vector(x))
    return _exact.sqrt_rational(_exact.dot(displacement, displacement))


def inflated_normal(E: Polyhedron, x: Vec3) -> Vec3 | None:
    """Outward unit(x-proj_E(x)); None only for an exact zero displacement.

    Difference coordinates exactly, then scale before normalization. Global
    display rounding cannot erase this vector or change its sign. The normal
    is single-valued and Lipschitz on dist(x,E)>=delta>0; see test_margin's gates.
    Gate: test_r6fix_construction::test_g6f08_distance_and_normal_use_exact_relative_projection.
    """
    v = _exact.sub(_exact.vector(x), nearest_point_on_convex_entrance(E, x, exact=True))
    scale = max(abs(_mapped_value) for _mapped_value in v)
    if not scale:
        return None
    return unit(v)


# ------------------------------------------------------------------ 可微路径

def margin_gap_from_frozen_cover(A: Polyhedron, B: Polyhedron, label: tuple, x, delta,
                                 *, ee_sign: float = 1.0) -> Number:
    """冻结盖下的裕度间隙闭式：n·(a − b) − δ，支持对偶数（δ 也可以是一个导数通道）。

    仅当冻结的盖**正是实现最短距离的那一对特征**时，沿盖法向的 gap 等于见证距离——
    这由 float 路径的 `body_distance` 选出，是冻结组合结构的一部分。
    冻结路径接得住 `body_distance` 可能给出的全部盖种类：VF / FV / EE / VV3 / VE3 / EV3
    （低维盖的法向随平移 x 转动，按 x 计算；门：tests/test_frozen_lowdim.py）。
    显式接触窗口内（`body_distance` 报 0.0）这里给的是该盖的**有符号**间隙（浅贯入时为负），
    不是钳过的 0——冻结路径是解析式，不做择支。
    贯入哨兵 ("PENETRATING",) 没有冻结盖，抛 ValueError。
    """
    if label and label[0] == PENETRATING:
        raise ValueError("bodies interpenetrate: there is no frozen cover (margin already violated)")
    return frozen_gap(A, B, label, x, ee_sign=ee_sign, delta=delta)
