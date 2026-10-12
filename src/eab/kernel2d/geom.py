"""2D coordinate geometry; predicates are exact on supplied coordinates.

CCW edge normals point right. Zero-tolerance convexity, reflex turns, membership
and overlap have no implicit noise band. Positive angular/length tolerances are
explicit caller windows, never inflated by coordinate magnitude. Reporting-only
angle_floor/turn_floor/round_floor remain available, not predicate truth.
"""

from __future__ import annotations

import sys
from fractions import Fraction
from itertools import chain
from math import hypot

Point = tuple[float, float]
Poly = list[Point]

EPS = sys.float_info.epsilon
ROUND_C = 64.0          # 舍入误差放大系数（"c 几十"）：覆盖差分、叉积、投影各级的累积舍入


def coord_scale(*groups) -> float:
    """坐标量级 C = 各点集里 max |坐标|（点集可以是多边形，也可以是单点的列表）。"""
    return max(map(abs, chain.from_iterable(chain.from_iterable(groups))), default=0.0)


def round_floor(C: float) -> float:
    """坐标量级 C 下长度判定的舍入下限 c·eps·C。"""
    return ROUND_C * EPS * C


def eff_tol(tol: float, *groups) -> float:
    """长度容差抬到舍入下限：max(tol, c·eps·C)。"""
    return max(tol, round_floor(coord_scale(*groups)))


def angle_floor(C: float, ell: float) -> float:
    """边长 ℓ、坐标量级 C 下法向/转角的舍入下限 c·eps·C/ℓ（弧度）。ℓ = 0 时为 +inf（零长边另行报错）。"""
    return ROUND_C * EPS * C / ell if ell > 0.0 else float("inf")


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


def _area2_exact(poly):
    P=[tuple(map(Fraction,p)) for p in poly];o=P[0]
    return sum(((a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
                for a,b in zip(P,P[1:]+P[:1])),Fraction(0))


def _display_fraction(value):
    out=float(value)
    if value and out==0:raise ArithmeticError('nonzero geometry construction below binary64 output range')
    return out


def signed_area(poly: Poly) -> float:
    """Exact shoelace followed by one checked float construction (not a sign oracle)."""
    return _display_fraction(_area2_exact(poly)/2)


def is_ccw(poly: Poly) -> bool:
    """Exact area sign, even when its float magnitude cannot be represented."""
    return _area2_exact(poly)>0


def ensure_ccw(poly: Poly) -> tuple[Poly, bool]:
    """返回 (CCW 多边形, 是否翻转过)。"""
    if is_ccw(poly):
        return list(poly), False
    return list(reversed(poly)), True


def edge(poly: Poly, i: int) -> tuple[Point, Point]:
    n = len(poly)
    return poly[i % n], poly[(i + 1) % n]


def outward_normal(poly: Poly, i: int) -> Point:
    """CCW 多边形第 i 条边 (i -> i+1) 的单位外法向。

    零长边（连续重复顶点）没有法向：抛 ValueError('zero-length edge ...')，而不是 unit() 的
    ZeroDivisionError（审查 C19）。输入归一化在读取器边界做（readers.bdda_geom.strip_duplicate_vertices）。
    """
    from ..construction import sqrt_rational
    p, q = edge(poly, i)
    ex,ey=(Fraction(q[k])-Fraction(p[k]) for k in (0,1))
    square=ex*ex+ey*ey
    if not square:
        raise ValueError(f"zero-length edge {i % len(poly)} (consecutive duplicate vertex at {p}); "
                         f"strip duplicates at the reader boundary")
    def component(value):
        return (1 if value>0 else -1)*sqrt_rational(value*value/square) if value else 0.0
    return component(ey),component(-ex)


def zero_length_edges(poly: Poly) -> list[int]:
    """零长边的下标（循环意义：含末点 → 首点那条）。"""
    n = len(poly)
    return [i for i in range(n) if poly[i] == poly[(i + 1) % n]]


def vertex_turn(poly: Poly, i: int) -> float:
    """顶点 i 处 cross(e_{i-1}, e_i)：CCW 多边形 >0 为凸顶点，<0 为凹（反射）顶点。"""
    n = len(poly)
    e_prev = sub(poly[i % n], poly[(i - 1) % n])
    e_next = sub(poly[(i + 1) % n], poly[i % n])
    return cross(e_prev, e_next)


def turn_angle(poly: Poly, i: int) -> float:
    """顶点 i 的转角（弧度，(-π, π]）：CCW 多边形凸顶点 >0、反射顶点 <0、平直 =0。

    用 atan2(cross, dot) 而不是 sin：sin 分不清 θ 与 π−θ（审查 r1：178° 窄缝会被 3° 容差放行）。
    """
    n = len(poly)
    e_prev = sub(poly[i % n], poly[(i - 1) % n])
    e_next = sub(poly[(i + 1) % n], poly[i % n])
    from math import atan2
    return atan2(cross(e_prev, e_next), dot(e_prev, e_next))


def turn_floor(poly: Poly, i: int) -> float:
    """Reporting-only angular roundoff estimate, never used to change a predicate.

    A rounded motion may change the supplied coordinates and hence a true turn;
    this estimate describes that representation effect, not geometric truth.
    """
    n = len(poly)
    a, b, c = poly[(i - 1) % n], poly[i % n], poly[(i + 1) % n]
    C = max(abs(a[0]), abs(a[1]), abs(b[0]), abs(b[1]), abs(c[0]), abs(c[1]))
    return angle_floor(C, min(hypot(b[0] - a[0], b[1] - a[1]), hypot(c[0] - b[0], c[1] - b[1])))


def is_convex(poly: Poly, tol: float = 0.0) -> bool:
    """CCW convexity; only the explicit angular window tol may suppress a turn."""
    return not reflex_vertices(poly, tol)


def reflex_vertices(poly: Poly, tol: float = 0.0) -> list[int]:
    """Exact right turns at tol=0; no coordinate-dependent hidden angle floor.

    Positive tol is an explicit angular sector whose sin/cos construction is
    rounded once, then compared by exact rational determinant.
    """
    from math import cos, sin, pi
    if tol < 0:raise ValueError('tol must be nonnegative')
    if tol >= pi:return []
    cosine, sine = Fraction(cos(tol)), Fraction(sin(tol))
    out=[]
    for i,b in enumerate(poly):
        a,c=poly[i-1],poly[(i+1)%len(poly)]
        if orient2d(a,b,c)>=0:continue
        if tol==0:
            out.append(i);continue
        u=tuple(Fraction(b[k])-Fraction(a[k]) for k in (0,1))
        v=tuple(Fraction(c[k])-Fraction(b[k]) for k in (0,1))
        determinant=u[0]*v[1]-u[1]*v[0]
        scalar=u[0]*v[0]+u[1]*v[1]
        if -cosine*determinant-sine*scalar>0:out.append(i)
    return out


def point_side(p: Point, a: Point, b: Point) -> float:
    """cross(b-a, p-a)：>0 在有向边 a->b 左侧。"""
    return cross(sub(b, a), sub(p, a))


def point_in_polygon(pt: Point, poly: Poly, tol: float = 0.0) -> int:
    """Exact winding; explicit tol is a closed-segment distance window only."""
    if tol < 0:raise ValueError('tol must be nonnegative')
    return _point_in_polygon(pt, poly, tol)


def _point_in_polygon(pt: Point, poly: Poly, tol: float) -> int:
    p=tuple(map(Fraction,pt));P=[tuple(map(Fraction,a)) for a in poly]
    window=Fraction(tol)**2
    winding=0
    for a,b in zip(P,P[1:]+P[:1]):
        ex,ey=b[0]-a[0],b[1]-a[1];wx,wy=p[0]-a[0],p[1]-a[1]
        length=ex*ex+ey*ey;projection=wx*ex+wy*ey;side=ex*wy-ey*wx
        if length:
            if projection<=0:near=wx*wx+wy*wy<=window
            elif projection>=length:near=(p[0]-b[0])**2+(p[1]-b[1])**2<=window
            else:near=side*side<=window*length
            if near:return 0
        if a[1]<=p[1]<b[1] and side>0:winding+=1
        elif b[1]<=p[1]<a[1] and side<0:winding-=1
    return 1 if winding else -1


def segments_properly_cross(p1: Point, p2: Point, q1: Point, q2: Point, tol: float = 0.0) -> bool:
    """Exact proper crossing; positive tol requires all endpoint heights > tol."""
    if tol < 0:raise ValueError('tol must be nonnegative')
    if tol==0:
        return orient2d(p1,p2,q1)*orient2d(p1,p2,q2)<0 and orient2d(q1,q2,p1)*orient2d(q1,q2,p2)<0
    p1,p2,q1,q2=[tuple(map(Fraction,p)) for p in (p1,p2,q1,q2)]
    window=Fraction(tol)**2
    for a,b,c,d in ((p1,p2,q1,q2),(q1,q2,p1,p2)):
        ex,ey=b[0]-a[0],b[1]-a[1];length=ex*ex+ey*ey
        v=ex*(c[1]-a[1])-ey*(c[0]-a[0]);w=ex*(d[1]-a[1])-ey*(d[0]-a[0])
        if v*w>=0 or v*v<=window*length or w*w<=window*length:return False
    return True


def centroid(poly: Poly) -> Point:
    """Rational area moments, divided before rounding the final centroid."""
    P=[tuple(map(Fraction,p)) for p in poly];o=P[0]
    relative=[(x-o[0],y-o[1]) for x,y in P]
    area2=Fraction(0);cx=cy=Fraction(0)
    for a,b in zip(relative,relative[1:]+relative[:1]):
        w=a[0]*b[1]-a[1]*b[0]
        area2+=w;cx+=(a[0]+b[0])*w;cy+=(a[1]+b[1])*w
    if not area2:
        return tuple(_display_fraction(sum(p[k] for p in P)/len(P)) for k in (0,1))
    return _display_fraction(o[0]+cx/(3*area2)),_display_fraction(o[1]+cy/(3*area2))


def orient2d(a: Point, b: Point, c: Point) -> int:
    """cross(b − a, c − a) 的**精确**符号（+1 左转 / 0 共线 / −1 右转）：浮点快路 + Shewchuk 误差界过滤，
    界内退到 Fraction 精确算术。浮点输入本身就是精确有理数，所以结果对这组浮点坐标是精确的。

    误差界 = Shewchuk 的相对项 (3u + 16u²)(|detleft| + |detright|) + 绝对项 2⁻¹⁰⁷³：相对项假设不下溢，乘积落进
    次正规区时舍入误差是绝对的（每个乘积至多 2⁻¹⁰⁷⁵），坐标差 ~1e-154 以下时只靠相对项会把错号当真（G6 第二轮 minor：
    两个 −3.46e-309 的乘积之差给出 +5e-324，精确值为负）。乘积上溢时界为 inf，照样退到 Fraction。"""
    if any(isinstance(v, Fraction) for p in (a, b, c) for v in p):
        ax, ay, bx, by, cx, cy = (Fraction(v) for p in (a, b, c) for v in p)
        det = (ax - cx) * (by - cy) - (ay - cy) * (bx - cx)
        return (det > 0) - (det < 0)
    detleft = (a[0] - c[0]) * (b[1] - c[1])
    detright = (a[1] - c[1]) * (b[0] - c[0])
    det = detleft - detright
    bound = 3.3306690738754716e-16 * (abs(detleft) + abs(detright)) + 2.0 ** -1073
    if det > bound:
        return 1
    if -det > bound:
        return -1
    ax, ay, bx, by, cx, cy = (Fraction(v) for v in (a[0], a[1], b[0], b[1], c[0], c[1]))
    d = (ax - cx) * (by - cy) - (ay - cy) * (bx - cx)
    return (d > 0) - (d < 0)


def interior_point(poly: Poly) -> Point:
    """保证在简单多边形内部的一点（O'Rourke《Computational Geometry in C》§1.6 的对角线法）。

    取最左（再最下）顶点 v——必为严格凸顶点；三角 (p, v, q)（p、q 为 v 的邻点）若不含其他顶点，返回其形心；
    否则取三角里**离直线 pq 最远**的顶点 x：从 v 出发、平行于 pq 的扫线最先碰到 x，扫过的小三角里没有别的顶点，
    也没有边能穿过线段 vx（边只能从扫线进出小三角，一条线段不能两次穿过同一条线段），所以 vx 是一条内对角线，
    返回其中点。多边形任意朝向；三角成员判定用精确谓词 `orient2d`。

    旧规则取"离 v 最远"的顶点（G6 major 12），vx 可以穿过缺口：V 形缺口六边形上返回体外点，2-opt 随机简单
    多边形 0.1–0.25% 失败。门：tests/test_kernel2d_review.py::test_g6_12_*（独立 oracle：Fraction 射线奇偶）。
    """
    poly = [tuple(map(Fraction, p)) for p in poly]
    n = len(poly)
    iv = min(range(n), key=lambda i: (poly[i][0], poly[i][1]))
    p, v, q = poly[(iv - 1) % n], poly[iv], poly[(iv + 1) % n]
    turn = orient2d(p, v, q)

    def in_tri(x: Point) -> bool:           # 闭三角（含边界），与三角朝向无关
        return all(t * turn >= 0 for t in (orient2d(p, v, x), orient2d(v, q, x), orient2d(q, p, x)))

    best = None
    best_d = Fraction(-1)
    for k in range(n):
        if k in (iv, (iv - 1) % n, (iv + 1) % n):
            continue
        x = poly[k]
        if in_tri(x):
            d = abs(point_side(x, p, q))     # ∝ 到直线 pq 的距离（同一条 pq，直接比较）
            if d > best_d:
                best, best_d = x, d
    if best is None:
        return ((p[0] + v[0] + q[0]) / 3, (p[1] + v[1] + q[1]) / 3)
    return ((v[0] + best[0]) / 2, (v[1] + best[1]) / 2)


def triangulate(poly: Poly) -> list[tuple[int, int, int]]:
    """简单多边形的耳切三角剖分（精确谓词 `orient2d`），返回 CCW 的顶点下标三元组；多边形任意朝向。

    耳 = 严格凸顶点，其闭三角不含其他剩余顶点。平直顶点（三点共线）不作耳；一轮找不到耳时删一个平直顶点
    （零面积，不丢面积）。剩余三点共线时不出三角。输入须是简单多边形，否则抛 ValueError（不挂死）。
    """
    n = len(poly)
    # exact.polygons_overlap_exact 依赖这里；朝向也必须精确，不能让面积下溢/上溢决定耳切方向。
    o = (Fraction(poly[0][0]), Fraction(poly[0][1]))
    F = [(Fraction(x) - o[0], Fraction(y) - o[1]) for x, y in poly]
    area2 = sum((F[k][0] * F[(k + 1) % n][1] - F[k][1] * F[(k + 1) % n][0] for k in range(n)), Fraction(0))
    idx = list(range(n)) if area2 > 0 else list(reversed(range(n)))
    tris: list[tuple[int, int, int]] = []
    guard = 0
    while len(idx) > 3:
        guard += 1
        if guard > 4 * n * n + 16:
            raise ValueError("triangulate: no ear found (input not a simple polygon?)")
        m = len(idx)
        clipped = False
        for k in range(m):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % m]
            a, b, c = poly[i0], poly[i1], poly[i2]
            if orient2d(a, b, c) <= 0:
                continue
            if any(orient2d(a, b, poly[j]) >= 0 and orient2d(b, c, poly[j]) >= 0 and orient2d(c, a, poly[j]) >= 0
                   for j in idx if j not in (i0, i1, i2)):
                continue
            tris.append((i0, i1, i2))
            idx.pop(k)
            clipped = True
            break
        if not clipped:
            flat = next((k for k in range(m)
                         if orient2d(poly[idx[k - 1]], poly[idx[k]], poly[idx[(k + 1) % m]]) == 0), None)
            if flat is None:
                raise ValueError("triangulate: no ear found (input not a simple polygon?)")
            idx.pop(flat)
    if orient2d(poly[idx[0]], poly[idx[1]], poly[idx[2]]) > 0:
        tris.append((idx[0], idx[1], idx[2]))
    return tris


def _tri_axes(T) -> list[Point]:
    out = []
    for i in range(3):
        e = sub(T[(i + 1) % 3], T[i])
        le = norm(e)
        if le > 0.0:
            out.append((e[1] / le, -e[0] / le))
    return out


def _triangles_overlap(T, U, tol: float, o: Point) -> bool:
    """Triangle SAT with exact signed projection gaps and explicit length tol."""
    T,U=[tuple(map(Fraction,p)) for p in T],[tuple(map(Fraction,p)) for p in U]
    window=Fraction(tol)**2
    for P in (T,U):
        for a,b in zip(P,P[1:]+P[:1]):
            nx,ny=b[1]-a[1],a[0]-b[0];length=nx*nx+ny*ny
            if not length:continue
            t=[nx*p[0]+ny*p[1] for p in T];u=[nx*p[0]+ny*p[1] for p in U]
            overlap=min(max(t),max(u))-max(min(t),min(u))
            if overlap<=0 or overlap*overlap<=window*length:return False
    return True


def _interiors_overlap(A: Poly, B: Poly, tol: float) -> bool:
    """A、B 内部相交（深于 tol）⟺ 两份耳切里某对三角形内部相交：多边形内部 = 三角形内部 ∪ 对角线的相对内部，
    两内部之交是开集，非空即有正面积，必与某对三角形内部之交有公共部分。"""
    ta = [(A[i], A[j], A[k]) for i, j, k in triangulate(A)]
    tb = [(B[i], B[j], B[k]) for i, j, k in triangulate(B)]
    o = A[0]
    for T in ta:
        tx0, tx1 = min(p[0] for p in T), max(p[0] for p in T)
        ty0, ty1 = min(p[1] for p in T), max(p[1] for p in T)
        for U in tb:
            if min(tx1, max(p[0] for p in U)) - max(tx0, min(p[0] for p in U)) <= tol:
                continue
            if min(ty1, max(p[1] for p in U)) - max(ty0, min(p[1] for p in U)) <= tol:
                continue
            if _triangles_overlap(T, U, tol, o):
                return True
    return False


def polygons_overlap(A: Poly, B: Poly, tol: float = 0.0) -> int:
    """Simple-polygon overlap: exact at tol=0, explicit distance window otherwise.

    No roundoff/coordinate floor is added. A positive tol deliberately reports
    near-contact instead of strict overlap/separation; all its comparisons use
    rational projections and squared distances on the supplied coordinates.
    """
    if tol < 0:raise ValueError('tol must be nonnegative')
    t=Fraction(tol)
    A=[tuple(map(Fraction,p)) for p in A]
    B=[tuple(map(Fraction,p)) for p in B]
    ax0, ax1 = min(p[0] for p in A), max(p[0] for p in A)
    ay0, ay1 = min(p[1] for p in A), max(p[1] for p in A)
    bx0, bx1 = min(p[0] for p in B), max(p[0] for p in B)
    by0, by1 = min(p[1] for p in B), max(p[1] for p in B)
    if bx0 - ax1 > t or ax0 - bx1 > t or by0 - ay1 > t or ay0 - by1 > t:
        return -1
    touching = False
    for P, Q in ((A, B), (B, A)):
        for p in P:
            s = _point_in_polygon(p, Q, t)
            if s == 1:
                return 1
            if s == 0:
                touching = True
    na, nb = len(A), len(B)
    for i in range(na):
        for j in range(nb):
            if segments_properly_cross(A[i], A[(i + 1) % na], B[j], B[(j + 1) % nb], t):
                return 1
    if not touching:
        return -1
    return 1 if _interiors_overlap(A, B, t) else 0


def translate(poly: Poly, x: Point) -> Poly:
    return [add(p, x) for p in poly]


def reflect(poly: Poly) -> Poly:
    """点反射 p -> -p（保持 CCW 朝向；顶点索引不变）。"""
    return [neg(p) for p in poly]


def convex_hull(points: list[Point], tol: float = 0.0) -> Poly:
    """给定数据的精确凸包顶点（CCW，浮点输出）；共线点不作为顶点。
    tol 为兼容参数，已不参与判定或简化：隐式容差单调链会非传递地丢掉远超 tol 的真极点。
    若需简化，调用方应另行显式简化已构造的精确凸包，不可把简化结果用于几何真值判定。
    门：tests/test_kernel2d_covers_e3.py::test_convex_hull_keeps_true_extreme_point_not_transitive_tolerance_pop。
    """
    from .exact import hull_exact
    return [(float(p[0]), float(p[1])) for p in hull_exact(points)]
