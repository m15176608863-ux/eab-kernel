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


def frozen_normal(A: Polyhedron, B: Polyhedron, label: tuple, ee_sign: float = 1.0):
    """冻结盖的单位法向（B → A），泛型标量。"""
    kind, af, bf = label
    if kind == "VF":
        return face_normal_generic(B, bf[1])
    if kind == "FV":
        nA = face_normal_generic(A, af[1])
        return (-nA[0], -nA[1], -nA[2])
    if kind == "EE":
        return ee_normal_generic(A, (af[1], af[2]), B, (bf[1], bf[2]), ee_sign)
    if kind == "VV3":
        a, b = A.verts[af[1]], B.verts[bf[1]]
        d = tuple(a[i] - b[i] for i in range(3))
        ln = (d[0] * d[0] + d[1] * d[1] + d[2] * d[2]) ** 0.5
        return (d[0] / ln, d[1] / ln, d[2] / ln)
    raise ValueError(f"cover kind not supported for the frozen path: {kind}")


def frozen_gap(A: Polyhedron, B: Polyhedron, label: tuple, x, n) -> Number:
    """冻结盖沿给定法向的有符号间隙，A 平移 x。泛型标量。

    注意口径：VF/FV 的 gap 是顶点到面**所在平面**的有符号距离，**不是**两体间距——
    分离的凹体之间也常有顶点落在对方某面平面内侧（2026-09-18 实测 −2.7）。
    只有当这个盖正是实现最短距离的那一对特征时，gap 才等于见证距离。
    """
    kind, af, bf = label
    if kind == "VF":
        a = tuple(A.verts[af[1]][i] + x[i] for i in range(3))
        b0 = B.verts[B.faces[bf[1]][0]]
        return sum(n[i] * (a[i] - b0[i]) for i in range(3))
    if kind == "FV":
        a0 = tuple(A.verts[A.faces[af[1]][0]][i] + x[i] for i in range(3))
        b = B.verts[bf[1]]
        return sum(n[i] * (a0[i] - b[i]) for i in range(3))
    if kind in ("EE", "VV3"):
        a = tuple(A.verts[af[1]][i] + x[i] for i in range(3))
        b = B.verts[bf[1]]
        return sum(n[i] * (a[i] - b[i]) for i in range(3))
    raise ValueError(f"cover kind not supported for the frozen path: {kind}")
