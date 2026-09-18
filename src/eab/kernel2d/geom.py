"""二维几何原语。纯 Python，零依赖。所有多边形以顶点列表表示，内部统一为逆时针（CCW）。

约定：
- CCW 多边形边 p->q 的外法向 = 右法向 (dy, -dx)/|e|。
- 谓词带绝对容差 tol（长度量纲），调用方按几何尺度给。
"""

from __future__ import annotations

from math import hypot

Point = tuple[float, float]
Poly = list[Point]


def sub(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1])


def add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def neg(a: Point) -> Point:
    return (-a[0], -a[1])


def dot(a: Point, b: Point) -> float:
    return a[0] * b[0] + a[1] * b[1]


def cross(a: Point, b: Point) -> float:
    return a[0] * b[1] - a[1] * b[0]


def norm(a: Point) -> float:
    return hypot(a[0], a[1])


def unit(a: Point) -> Point:
    n = norm(a)
    if n == 0.0:
        raise ZeroDivisionError("unit of zero vector")
    return (a[0] / n, a[1] / n)


def signed_area(poly: Poly) -> float:
    s = 0.0
    n = len(poly)
    for i in range(n):
        s += cross(poly[i], poly[(i + 1) % n])
    return 0.5 * s


def is_ccw(poly: Poly) -> bool:
    return signed_area(poly) > 0.0


def ensure_ccw(poly: Poly) -> tuple[Poly, bool]:
    """返回 (CCW 多边形, 是否翻转过)。"""
    if is_ccw(poly):
        return list(poly), False
    return list(reversed(poly)), True


def edge(poly: Poly, i: int) -> tuple[Point, Point]:
    n = len(poly)
    return poly[i % n], poly[(i + 1) % n]


def outward_normal(poly: Poly, i: int) -> Point:
    """CCW 多边形第 i 条边 (i -> i+1) 的单位外法向。"""
    p, q = edge(poly, i)
    e = sub(q, p)
    return unit((e[1], -e[0]))


def vertex_turn(poly: Poly, i: int) -> float:
    """顶点 i 处 cross(e_{i-1}, e_i)：CCW 多边形 >0 为凸顶点，<0 为凹（反射）顶点。"""
    n = len(poly)
    e_prev = sub(poly[i % n], poly[(i - 1) % n])
    e_next = sub(poly[(i + 1) % n], poly[i % n])
    return cross(e_prev, e_next)


def is_convex(poly: Poly, tol: float = 0.0) -> bool:
    return all(vertex_turn(poly, i) >= -tol for i in range(len(poly)))


def reflex_vertices(poly: Poly, tol: float = 0.0) -> list[int]:
    return [i for i in range(len(poly)) if vertex_turn(poly, i) < -tol]


def point_side(p: Point, a: Point, b: Point) -> float:
    """cross(b-a, p-a)：>0 在有向边 a->b 左侧。"""
    return cross(sub(b, a), sub(p, a))


def point_in_polygon(pt: Point, poly: Poly, tol: float = 0.0) -> int:
    """1 严格内部 / 0 在边界（容差 tol 内）/ -1 外部。绕数法，多边形任意朝向。"""
    n = len(poly)
    # 边界检测
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        e = sub(b, a)
        le = norm(e)
        if le == 0.0:
            continue
        d = abs(point_side(pt, a, b)) / le
        if d <= tol:
            t = dot(sub(pt, a), e) / (le * le)
            if -tol / le <= t <= 1.0 + tol / le:
                return 0
    wn = 0
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if a[1] <= pt[1]:
            if b[1] > pt[1] and point_side(pt, a, b) > 0:
                wn += 1
        else:
            if b[1] <= pt[1] and point_side(pt, a, b) < 0:
                wn -= 1
    return 1 if wn != 0 else -1


def segments_properly_cross(p1: Point, p2: Point, q1: Point, q2: Point, tol: float = 0.0) -> bool:
    """两线段在各自内部相交（不含端点触碰、不含共线重叠）。"""
    d1 = point_side(q1, p1, p2)
    d2 = point_side(q2, p1, p2)
    d3 = point_side(p1, q1, q2)
    d4 = point_side(p2, q1, q2)
    lp = norm(sub(p2, p1))
    lq = norm(sub(q2, q1))
    if lp == 0.0 or lq == 0.0:
        return False
    # 用距离量纲比较
    d1, d2 = d1 / lp, d2 / lp
    d3, d4 = d3 / lq, d4 / lq
    return ((d1 > tol and d2 < -tol) or (d1 < -tol and d2 > tol)) and \
           ((d3 > tol and d4 < -tol) or (d3 < -tol and d4 > tol))


def centroid(poly: Poly) -> Point:
    a = signed_area(poly)
    if a == 0.0:
        n = len(poly)
        return (sum(p[0] for p in poly) / n, sum(p[1] for p in poly) / n)
    cx = cy = 0.0
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        w = cross(p, q)
        cx += (p[0] + q[0]) * w
        cy += (p[1] + q[1]) * w
    return (cx / (6.0 * a), cy / (6.0 * a))


def polygons_overlap(A: Poly, B: Poly, tol: float = 0.0) -> int:
    """暴力谓词：1 内部相交 / 0 仅边界接触 / -1 分离。任意简单多边形。

    判据：任一顶点严格在对方内部 → 1；任一边对内部相交 → 1；任一边中点或形心严格在对方内部 → 1
    （覆盖全等/包含等无顶点严格内部的情形）；否则若有顶点落在对方边界 → 0；否则 -1。
    """
    touching = False
    for P, Q in ((A, B), (B, A)):
        for p in P:
            s = point_in_polygon(p, Q, tol)
            if s == 1:
                return 1
            if s == 0:
                touching = True
        n = len(P)
        for i in range(n):
            a, b = P[i], P[(i + 1) % n]
            m = ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5)
            s = point_in_polygon(m, Q, tol)
            if s == 1:
                return 1
            if s == 0:
                touching = True
        if point_in_polygon(centroid(P), Q, tol) == 1:
            return 1
    na, nb = len(A), len(B)
    for i in range(na):
        for j in range(nb):
            if segments_properly_cross(A[i], A[(i + 1) % na], B[j], B[(j + 1) % nb], tol):
                return 1
    return 0 if touching else -1


def translate(poly: Poly, x: Point) -> Poly:
    return [add(p, x) for p in poly]


def reflect(poly: Poly) -> Poly:
    """点反射 p -> -p（保持 CCW 朝向；顶点索引不变）。"""
    return [neg(p) for p in poly]


def convex_hull(points: list[Point]) -> Poly:
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts
    lower: list[Point] = []
    for p in pts:
        while len(lower) >= 2 and cross(sub(lower[-1], lower[-2]), sub(p, lower[-2])) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[Point] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(sub(upper[-1], upper[-2]), sub(p, upper[-2])) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]
