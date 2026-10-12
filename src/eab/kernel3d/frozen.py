"""冻结盖的解析表达式（泛型标量：float 或对偶数）。

"片 + 划"里的**片**：组合结构（哪一对特征当家、EE 法向朝哪）已由精确谓词定好，
这里只做算术、不做择支。片内是解析的，所以对几何参数逐点可微——与 DDA 冻结活动集后
解析可微同构。

**这一层不许出现任何域词汇**（岩石、互锁、车辆……）。域的东西在 L5。
"""

from __future__ import annotations

from fractions import Fraction
import math
import struct

from ..construction import sqrt_rational
from ..dual import Dual, Number, val, _derivative_float
from .covers3 import _oriented_ee_normal
from .geom3 import Polyhedron, cross, dot, sub, add, exact_edge_vector, exact_surface


def _exact_jet_points(points):
    duals = [c for p in points for c in p if isinstance(c, Dual)]
    width = duals[0].width if duals else 0
    if any(c.width != width for c in duals):
        raise ValueError("dual width mismatch in frozen geometry")
    primal = [tuple(Fraction(c.v) if isinstance(c, Dual) else Fraction(c) for c in p) for p in points]
    derivative = [[tuple(Fraction(c.e[k]) if isinstance(c, Dual) else Fraction(0) for c in p)
                   for p in points] for k in range(width)]
    return primal, derivative


class _FrozenNormal(tuple):
    """Tuple-compatible display normal retaining its exact pre-normalization jet.

    Passing this object to frozen_gap retains that certificate. Converting it
    to a plain tuple deliberately supplies an arbitrary rounded-normal model.
    Gate: test_frozen_gap_and_jet_do_not_reinterpret_rounded_normals.
    """
    def __new__(cls, values, raw, derivatives):
        result = super().__new__(cls, values)
        result.raw = tuple(raw)
        result.derivatives = tuple(tuple(d) for d in derivatives)
        return result


def _unit_jet(n, derivatives, sign=1.0):
    """Exact polynomial value/derivative; sqrt and output conversion only float."""
    nn = dot(n, n)
    if not nn:
        raise ZeroDivisionError("zero normal in frozen geometry")

    def normalized(c):
        c = Fraction(sign) * c
        magnitude = sqrt_rational(c * c / nn)
        return -magnitude if c < 0 else magnitude

    # Do not round a scaled component or sqrt(nn) before the final quotient:
    # either intermediate can cross a subnormal output midpoint (R7 scan).
    value = [normalized(c) for c in n]
    if not derivatives:
        return _FrozenNormal(value, tuple(Fraction(sign)*c for c in n), ())
    result = []
    for i in range(3):
        channels = tuple(normalized(dn[i] - n[i] * dot(n, dn) / nn)
                         for dn in derivatives)
        result.append(Dual(value[i], channels))
    return _FrozenNormal(result, tuple(Fraction(sign)*c for c in n),
                         [tuple(Fraction(sign)*c for c in dn) for dn in derivatives])


def face_normal_generic(P: Polyhedron, fi: int, triangle=None):
    """Exact polynomial Newell jet, with floating square-root construction."""
    return _unit_jet(*_face_raw_jet(P, fi, triangle))


def _face_raw_jet(P, fi, triangle=None):
    face = P.faces[fi] if triangle is None else triangle
    points, channels = _exact_jet_points([P.verts[i] for i in face])
    zero = (Fraction(0),) * 3
    n = zero
    derivatives = [zero for _ in channels]
    for j in range(len(points)):
        k = (j + 1) % len(points)
        p, q = sub(points[j], points[0]), sub(points[k], points[0])
        n = add(n, cross(p, q))
        for w, deriv in enumerate(channels):
            dp, dq = sub(deriv[j], deriv[0]), sub(deriv[k], deriv[0])
            derivatives[w] = add(derivatives[w], add(cross(dp, q), cross(p, dq)))
    return n, derivatives


def ee_normal_generic(A: Polyhedron, ea, B: Polyhedron, eb, sign: float = 1.0):
    """Frozen EE jet, including nonzero micro-crosses lost by float subtraction."""
    return _unit_jet(*_ee_raw_jet(A, ea, B, eb), sign)


def _ee_raw_jet(A, ea, B, eb):
    points, channels = _exact_jet_points([A.verts[ea[0]], A.verts[ea[1]], B.verts[eb[0]], B.verts[eb[1]]])
    u, v = sub(points[1], points[0]), sub(points[3], points[2])
    derivatives = [add(cross(sub(e[3], e[2]), u), cross(v, sub(e[1], e[0]))) for e in channels]
    return cross(v, u), derivatives


def _as_float(P: Polyhedron) -> Polyhedron:
    """Primal-only view for branching; retain exact non-Dual coordinates."""
    if not any(isinstance(c, Dual) for v in P.verts for c in v):
        return P
    return Polyhedron([tuple(val(c) if isinstance(c, Dual) else c for c in v) for v in P.verts], list(P.faces))


def _ee_topology_view(P: Polyhedron, edge):
    """Recover a folded-face diagonal's actual adjacent triangle normals.

    Existing source edges retain the selected general-ring contract. A diagonal
    absent from that topology can only be interpreted on the exact surface;
    feeding an absent edge to the cone predicate would choose a fallback sign.
    """
    if tuple(sorted(edge)) in P.edges():
        return P
    return exact_surface(P)


def frozen_ee_sign(A: Polyhedron, B: Polyhedron, ea, eb, tol: float = 1e-9) -> float:
    """Freeze the exact general-cover EE orientation on primal coordinates.

    Use the same exact two-sided cone rule as facet_normal3, on the supplied
    view and with the caller's explicit angular domain window. Canonical hull
    labels require that canonical view; general labels require the input rings.
    facet_normal3 uses the exact zero window; pass tol=0 for direct agreement.
    Folded-face diagonals absent from the original topology recover their
    actual adjacent triangles before the same exact orientation rule is used.
    The separate dual-through jet retains every exact polynomial derivative.
    """
    Af, Bf = _ee_topology_view(_as_float(A), ea), _ee_topology_view(_as_float(B), eb)
    raw = cross(exact_edge_vector(Bf, eb), exact_edge_vector(Af, ea))
    oriented = _oriented_ee_normal(Af, ea, Bf, eb, tol)
    return 1.0 if dot(raw, oriented) > 0 else -1.0



# 冻结路径支持的盖种类 = `body_distance` / `escape_candidates` 可能给出的全部种类。
FACET_KINDS = ("VF", "FV", "EE")          # ∂E 的二维片：法向与平移无关，gap 沿平移仿射
LOW_DIM_KINDS = ("VE3", "EV3", "VV3")     # ∂E 的棱 / 顶点：法向 = 见证方向，随平移转动
FROZEN_KINDS = FACET_KINDS + LOW_DIM_KINDS


def _check_kind(label: tuple) -> str:
    kind = label[0] if label else None
    if kind not in FROZEN_KINDS:
        raise ValueError(f"cover kind not supported for the frozen path: {kind}")
    return kind


def _affine_point_jets(points, offset, moved):
    """Convert before translation/subtraction, retaining all derivative channels."""
    primal, derivative = _exact_jet_points([*points, offset or (0, 0, 0)])
    for i in moved:
        primal[i] = add(primal[i], primal[-1])
        for channel in derivative:
            channel[i] = add(channel[i], channel[-1])
    return primal[:-1], [channel[:-1] for channel in derivative]


def _line_residual_jet(p, e0, e1, *, offset=None, moved=()):
    """点到直线的精确有理投影 jet；浮点仅构造最后的单位向量。

    残差为零（点在直线上，两体相触）时法向集值、无定义：除零照常抛出。
    不先计算浮点平方范数或全局平移；故短棱、工程坐标、primal 为零的导数均保留。
    门：test_frozen_line_normal_keeps_zero_primal_nonzero_derivative_without_square_range_loss。
    """
    points, channels = _affine_point_jets([p, e0, e1], offset, moved)
    p, e0, e1 = points
    d, w = sub(e1, e0), sub(p, e0)
    dd = dot(d, d)
    s = dot(w, d) / dd
    r = tuple(w[i] - s * d[i] for i in range(3))
    derivatives = []
    for channel in channels:
        dp, de0, de1 = channel
        dv, dw = sub(de1, de0), sub(dp, de0)
        ds = (dot(dw, d) + dot(w, dv) - 2 * s * dot(d, dv)) / dd
        derivatives.append(tuple(dw[i] - ds * d[i] - s * dv[i] for i in range(3)))
    return r, derivatives


def frozen_normal(A: Polyhedron, B: Polyhedron, label: tuple, ee_sign: float = 1.0, x=None):
    """冻结盖的单位法向（B → A），泛型标量。

    x 是 A 的平移（可为对偶数；None 即零平移）。VF/FV/EE 的法向与平移无关；
    低维盖（VV3 / VE3 / EV3）的法向是两特征间的见证方向，**随平移转动**，必须用平移后的 A 算
    ——否则 `margin_gap_from_frozen_cover(A, B, lab, x≠0, …)` 给的是 x=0 处的切平面而非距离。
    VE3（A 顶点 × B 棱）：顶点到 B 棱所在直线的投影残差；EV3（A 棱 × B 顶点）：B 顶点到 A 棱
    所在直线的投影残差取反（仍是 B → A）。两者都无择支，对偶数直接透传。
    """
    return _unit_jet(*_frozen_raw_normal(A, B, label, ee_sign, x))


def _frozen_raw_normal(A, B, label, ee_sign=1.0, x=None):
    """Raw rational normal/residual and jet; never re-exactify a unit display."""
    kind = _check_kind(label)
    _, af, bf = label
    sign = Fraction(1)
    if kind == "VF":
        return _face_raw_jet(B, bf[1], bf[3:] if len(bf) > 2 else None)
    if kind == "FV":
        n, dn = _face_raw_jet(A, af[1], af[3:] if len(af) > 2 else None)
        sign = Fraction(-1)
    elif kind == "EE":
        n, dn = _ee_raw_jet(A, (af[1], af[2]), B, (bf[1], bf[2]))
        sign = Fraction(ee_sign)
    elif kind == "VV3":
        points, channels = _affine_point_jets([A.verts[af[1]], B.verts[bf[1]]], x, (0,))
        return sub(points[0], points[1]), [sub(e[0], e[1]) for e in channels]
    elif kind == "VE3":
        return _line_residual_jet(A.verts[af[1]], B.verts[bf[1]], B.verts[bf[2]], offset=x, moved=(0,))
    else:  # EV3
        n, dn = _line_residual_jet(B.verts[bf[1]], A.verts[af[1]], A.verts[af[2]], offset=x, moved=(1, 2))
        sign = Fraction(-1)
    return tuple(sign*c for c in n), [tuple(sign*c for c in d) for d in dn]


def _frozen_gap_polynomial(A, B, label, x, raw, derivatives):
    """Exact raw plane/residual dot relative displacement, with aligned jets."""
    kind = _check_kind(label)
    _, af, bf = label
    if kind == "VF":
        a, b = A.verts[af[1]], B.verts[bf[3] if len(bf) > 2 else B.faces[bf[1]][0]]
    elif kind == "FV":
        a, b = A.verts[af[3] if len(af) > 2 else A.faces[af[1]][0]], B.verts[bf[1]]
    else:
        a, b = A.verts[af[1]], B.verts[bf[1]]
    points, channels = _affine_point_jets([a, b], x, (0,))
    if channels and derivatives and len(channels) != len(derivatives):
        raise ValueError("dual width mismatch in frozen geometry")
    width = max(len(channels), len(derivatives))
    zero = (Fraction(0),)*3
    channels = channels or [[zero, zero] for _ in range(width)]
    derivatives = derivatives or [zero for _ in range(width)]
    delta = sub(points[0], points[1])
    value = dot(raw, delta)
    derivative = [dot(dn, delta) + dot(raw, sub(e[0], e[1]))
                  for dn, e in zip(derivatives, channels)]
    return value, derivative, derivatives


def _normalized_difference(c, nn, offset, *, allow_underflow=False):
    """Round c/sqrt(nn)-offset once; exact comparisons certify float midpoints.

    The usual adjacent-float candidate is constant work. Severe cancellation,
    including a nonrepresentable intermediate gap, falls back to a bounded
    63-step binary64 search, never a precision guess or an absolute threshold.
    allow_underflow is only for displays carrying a separate exact certificate.
    Gates: test_frozen_margin_irrational_cancellation_has_exact_midpoint_certificate,
    test_frozen_margin_rounds_after_subtracting_the_margin_parameter.
    """
    c, offset = Fraction(c), Fraction(offset)
    if not offset:
        magnitude = sqrt_rational(c*c/nn, allow_underflow=allow_underflow)
        return -magnitude if c < 0 else magnitude

    def compare_root(r):
        if c >= 0 > r:
            return 1
        if c < 0 <= r:
            return -1
        difference = c*c-r*r*nn
        order = (difference > 0)-(difference < 0)
        return -order if c < 0 else order

    sign = compare_root(offset)
    if not sign:
        return 0.0
    if sign < 0:
        return -_normalized_difference(-c, nn, -offset, allow_underflow=allow_underflow)

    def compare(value):
        return compare_root(offset + Fraction(value))

    def from_bits(bits):
        return struct.unpack(">d", struct.pack(">Q", bits))[0]

    try:
        root = sqrt_rational(c*c/nn, allow_underflow=True)
        candidate = (-root if c < 0 else root)-float(offset)
    except (ArithmeticError, OverflowError):
        candidate = math.inf
    lower = None
    if math.isfinite(candidate) and candidate >= 0:
        order = compare(candidate)
        if not order:
            return candidate
        if order > 0:
            upper = math.nextafter(candidate, math.inf)
            if math.isfinite(upper) and compare(upper) <= 0:
                lower = candidate
        else:
            below = math.nextafter(candidate, -math.inf)
            if below >= 0 and compare(below) >= 0:
                lower, upper = below, candidate
    if lower is None:
        lo, hi = 0, 0x7fefffffffffffff
        if compare(from_bits(hi)) > 0:
            raise OverflowError("exact frozen difference exceeds finite binary64 range")
        while lo < hi:
            mid = (lo+hi+1)//2
            if compare(from_bits(mid)) >= 0:
                lo = mid
            else:
                hi = mid-1
        lower = from_bits(lo)
        if not compare(lower):
            return lower
        upper = from_bits(lo+1)
    midpoint = (Fraction(lower)+Fraction(upper))/2
    order = compare(midpoint)
    even = not (struct.unpack(">Q", struct.pack(">d", lower))[0] & 1)
    result = lower if order < 0 or (not order and even) else upper
    if not result and not allow_underflow:
        raise ArithmeticError("nonzero exact frozen difference is below binary64 output range")
    return result


def frozen_gap(A: Polyhedron, B: Polyhedron, label: tuple, x, n=None, *, ee_sign=1.0, delta=0) -> Number:
    """冻结盖沿给定法向的有符号间隙，A 平移 x。泛型标量。

    注意口径：VF/FV 的 gap 是顶点到面**所在平面**的有符号距离，**不是**两体间距——
    分离的凹体之间也常有顶点落在对方某面平面内侧（2026-09-18 实测 −2.7）。
    只有当这个盖正是实现最短距离的那一对特征时，gap 才等于见证距离。

    低维盖取 A、B 特征上的任一参考点即可：VE3 / EV3 的法向垂直于棱，故 n·(a − 棱起点)
    恰是点到棱所在直线的距离；VV3 的 n 与 a − b 同向，故即 |a − b|。
    （n 须按同一平移 x 由 `frozen_normal(..., x=x)` 给出。）
    With n=None, construct from the exact feature jet. A frozen_normal display
    tuple retains that jet; an ordinary externally supplied n instead defines
    its own exact-input dot-product model. delta and all derivative channels
    are subtracted before final construction, not from an already rounded gap.
    Gate: test_frozen_gap_and_jet_do_not_reinterpret_rounded_normals.
    """
    if n is None:
        raw, dn = _frozen_raw_normal(A, B, label, ee_sign, x)
    elif isinstance(n, _FrozenNormal):
        raw, dn = n.raw, n.derivatives
    else:
        # An explicitly supplied arbitrary normal is its own input model.
        # Only normals returned by frozen_normal carry an exact feature jet.
        points, channels = _exact_jet_points([n])
        value, derivative, _ = _frozen_gap_polynomial(A, B, label, x, points[0],
                                                      [e[0] for e in channels])
        return _gap_difference(value, Fraction(1), derivative,
                               [(Fraction(0),)*3 for _ in derivative], (Fraction(0),)*3, delta)
    value, derivative, dn = _frozen_gap_polynomial(A, B, label, x, raw, dn)
    nn = dot(raw, raw)
    if not nn:
        raise ZeroDivisionError("zero normal in frozen geometry")
    return _gap_difference(value, nn, derivative, dn, raw, delta)


def _gap_difference(value, nn, derivative, dn, raw, delta):
    """Keep delta and its jet inside the same final algebraic construction."""
    if isinstance(delta, Dual):
        if derivative and len(derivative) != delta.width:
            raise ValueError("dual width mismatch in frozen geometry")
        if not derivative:
            derivative = [Fraction(0)]*delta.width
            dn = [(Fraction(0),)*3 for _ in derivative]
        offset, d_offset = Fraction(delta.v), tuple(map(Fraction, delta.e))
    else:
        offset, d_offset = Fraction(delta), (Fraction(0),)*len(derivative)
    primal = _normalized_difference(value, nn, offset)
    if not derivative:
        return primal
    return Dual(primal, tuple(_normalized_difference(dg-value*dot(raw, d)/nn, nn, dd)
                              for dg, d, dd in zip(derivative, dn, d_offset)))


def frozen_lift(A: Polyhedron, B: Polyhedron, label: tuple, offset, ee_sign=1.0):
    """One exact raw-plane ratio model for ordinary and Dual frozen lifts.

    Orientation/normalization cancel before any floating construction. Gate:
    test_frozen_lift_plain_and_dual_share_exact_raw_plane_ratio.
    """
    raw, dn = _frozen_raw_normal(A, B, label, ee_sign)
    value, derivative, dn = _frozen_gap_polynomial(A, B, label, offset, raw, dn)
    result = -value/raw[2]
    if not derivative:
        return result
    return Dual(_derivative_float(result),
                tuple(_derivative_float((-dg-result*d[2])/raw[2])
                      for dg, d in zip(derivative, dn)))
