"""冻结盖的解析表达式（泛型标量：float 或对偶数）。

"片 + 划"里的**片**：组合结构（哪一对特征当家、EE 法向朝哪）已由 float 路径定好，
这里只做算术、不做择支。片内是解析的，所以对几何参数逐点可微——与 DDA 冻结活动集后
解析可微同构。

**这一层不许出现任何域词汇**（岩石、互锁、车辆……）。域的东西在 L5。
"""

from __future__ import annotations

from ..dual import Number, val
from .covers3 import edge_arc_contains
from .geom3 import Polyhedron


def face_normal_generic(P: Polyhedron, fi: int):
    """Newell 面法向，泛型标量（顶点坐标可为对偶数）。"""
    f = P.faces[fi]
    o = P.verts[f[0]]
    nx = ny = nz = 0.0
    k = len(f)
    for i in range(k):
        p = tuple(P.verts[f[i]][t] - o[t] for t in range(3))
        q = tuple(P.verts[f[(i + 1) % k]][t] - o[t] for t in range(3))
        nx = nx + (p[1] * q[2] - p[2] * q[1])
        ny = ny + (p[2] * q[0] - p[0] * q[2])
        nz = nz + (p[0] * q[1] - p[1] * q[0])
    ln = (nx * nx + ny * ny + nz * nz) ** 0.5
    return (nx / ln, ny / ln, nz / ln)


def ee_normal_generic(A: Polyhedron, ea, B: Polyhedron, eb, sign: float = 1.0):
    """交叉棱-棱的单位法向。`sign` 是**冻结组合结构的一部分**（由 float 路径定），
    不在这里择支——对偶路径里做分支会把导数带进 if，破坏片内解析性。"""
    tA = tuple(A.verts[ea[1]][i] - A.verts[ea[0]][i] for i in range(3))
    tB = tuple(B.verts[eb[1]][i] - B.verts[eb[0]][i] for i in range(3))
    nx = tB[1] * tA[2] - tB[2] * tA[1]
    ny = tB[2] * tA[0] - tB[0] * tA[2]
    nz = tB[0] * tA[1] - tB[1] * tA[0]
    ln = (nx * nx + ny * ny + nz * nz) ** 0.5
    return (sign * nx / ln, sign * ny / ln, sign * nz / ln)


def frozen_ee_sign(A: Polyhedron, B: Polyhedron, ea, eb, tol: float = 1e-9) -> float:
    """float 路径下定出的 EE 法向朝向，作为冻结组合结构的一部分交给对偶路径。"""
    n = ee_normal_generic(A, ea, B, eb, 1.0)
    probe = (val(n[0]), val(n[1]), val(n[2]))
    return -1.0 if edge_arc_contains(B, eb, probe, tol) < 0 else 1.0


# 冻结路径支持的盖种类 = `body_distance` / `escape_candidates` 可能给出的全部种类。
FACET_KINDS = ("VF", "FV", "EE")          # ∂E 的二维片：法向与平移无关，gap 沿平移仿射
LOW_DIM_KINDS = ("VE3", "EV3", "VV3")     # ∂E 的棱 / 顶点：法向 = 见证方向，随平移转动
FROZEN_KINDS = FACET_KINDS + LOW_DIM_KINDS


def _check_kind(label: tuple) -> str:
    kind = label[0] if label else None
    if kind not in FROZEN_KINDS:
        raise ValueError(f"cover kind not supported for the frozen path: {kind}")
    return kind


def _moved(P: Polyhedron, vi: int, x):
    """P 的第 vi 个顶点平移 x（x=None 即不平移）。泛型标量。"""
    p = P.verts[vi]
    if x is None:
        return p
    return (p[0] + x[0], p[1] + x[1], p[2] + x[2])


def _unit_generic(v):
    ln = (v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) ** 0.5
    return (v[0] / ln, v[1] / ln, v[2] / ln)


def _line_residual_normal(p, e0, e1):
    """点 p 到直线 e0e1 的正交投影残差之单位向量（从直线指向 p）。泛型标量、无择支。

    残差为零（点在直线上，两体相触）时法向集值、无定义：除零照常抛出。
    """
    d = (e1[0] - e0[0], e1[1] - e0[1], e1[2] - e0[2])
    w = (p[0] - e0[0], p[1] - e0[1], p[2] - e0[2])
    s = (w[0] * d[0] + w[1] * d[1] + w[2] * d[2]) / (d[0] * d[0] + d[1] * d[1] + d[2] * d[2])
    return _unit_generic((w[0] - s * d[0], w[1] - s * d[1], w[2] - s * d[2]))


def frozen_normal(A: Polyhedron, B: Polyhedron, label: tuple, ee_sign: float = 1.0, x=None):
    """冻结盖的单位法向（B → A），泛型标量。

    x 是 A 的平移（可为对偶数；None 即零平移）。VF/FV/EE 的法向与平移无关；
    低维盖（VV3 / VE3 / EV3）的法向是两特征间的见证方向，**随平移转动**，必须用平移后的 A 算
    ——否则 `margin_gap_from_frozen_cover(A, B, lab, x≠0, …)` 给的是 x=0 处的切平面而非距离。
    VE3（A 顶点 × B 棱）：顶点到 B 棱所在直线的投影残差；EV3（A 棱 × B 顶点）：B 顶点到 A 棱
    所在直线的投影残差取反（仍是 B → A）。两者都无择支，对偶数直接透传。
    """
    kind = _check_kind(label)
    _, af, bf = label
    if kind == "VF":
        return face_normal_generic(B, bf[1])
    if kind == "FV":
        nA = face_normal_generic(A, af[1])
        return (-nA[0], -nA[1], -nA[2])
    if kind == "EE":
        return ee_normal_generic(A, (af[1], af[2]), B, (bf[1], bf[2]), ee_sign)
    if kind == "VV3":
        a, b = _moved(A, af[1], x), B.verts[bf[1]]
        return _unit_generic((a[0] - b[0], a[1] - b[1], a[2] - b[2]))
    if kind == "VE3":
        return _line_residual_normal(_moved(A, af[1], x), B.verts[bf[1]], B.verts[bf[2]])
    # EV3
    n = _line_residual_normal(B.verts[bf[1]], _moved(A, af[1], x), _moved(A, af[2], x))
    return (-n[0], -n[1], -n[2])


def frozen_gap(A: Polyhedron, B: Polyhedron, label: tuple, x, n) -> Number:
    """冻结盖沿给定法向的有符号间隙，A 平移 x。泛型标量。

    注意口径：VF/FV 的 gap 是顶点到面**所在平面**的有符号距离，**不是**两体间距——
    分离的凹体之间也常有顶点落在对方某面平面内侧（2026-09-18 实测 −2.7）。
    只有当这个盖正是实现最短距离的那一对特征时，gap 才等于见证距离。

    低维盖取 A、B 特征上的任一参考点即可：VE3 / EV3 的法向垂直于棱，故 n·(a − 棱起点)
    恰是点到棱所在直线的距离；VV3 的 n 与 a − b 同向，故即 |a − b|。
    （n 须按同一平移 x 由 `frozen_normal(..., x=x)` 给出。）
    """
    kind = _check_kind(label)
    _, af, bf = label
    if kind == "VF":
        a = tuple(A.verts[af[1]][i] + x[i] for i in range(3))
        b0 = B.verts[B.faces[bf[1]][0]]
        return sum(n[i] * (a[i] - b0[i]) for i in range(3))
    if kind == "FV":
        a0 = tuple(A.verts[A.faces[af[1]][0]][i] + x[i] for i in range(3))
        b = B.verts[bf[1]]
        return sum(n[i] * (a0[i] - b[i]) for i in range(3))
    # EE / VV3 / VE3 / EV3：af[1] 是 A 的顶点或 A 棱的起点，bf[1] 是 B 的顶点或 B 棱的起点
    a = tuple(A.verts[af[1]][i] + x[i] for i in range(3))
    b = B.verts[bf[1]]
    return sum(n[i] * (a[i] - b[i]) for i in range(3))
