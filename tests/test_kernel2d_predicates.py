"""M0.3 二维核组的门（G6 第二轮，2026-09-27）：数值谓词与凸 E 构造。

G6 第二轮对 814fdea 的两条 major + 一条同类回归：
  · d78bb5f 声称的三处数值修复——耳切的闭三角判据、orient2d 的 Fraction 精确兜底、convex_hull 的舍入地板——
    没有任何测试直接调用，逐一变异全套照绿（4900 passed ×3）→ 下面 (a)(b)(c)(d)；
  · orient2d 的误差界不含次正规区的绝对项（minor，坐标差 ~1e-155 时错号）→ (c) 的回归例；
  · membership_convex 不给 eb 时把长度 tol 当弧度传给 convex_entrance_block：毫米单位下 57° 以内的边被并成 FF，
    方块压八边形判"分离"→ (e)；
  · 同一根因的另一处（G6 未点名，M0.3 自查）：convex_entrance_block 的平行边合并用**整个多边形最短边**的极角舍入
    下限 c·eps·C/ℓ_min，一条 1e-8 的短边放在 1e5 处就把夹角 0.1 rad 的长边并成 FF，成员判定答反 → (f)。
oracle 全部独立：Fraction 精确叉积/面积、网格多联骨牌的格子集合（接触与否由格子是否共角点决定，不经任何几何原语）。
"""

from __future__ import annotations

import math
import random
from fractions import Fraction

import pytest

from eab.kernel2d.covers import convex_entrance_block, membership_convex
from eab.kernel2d.g0 import g0_convex, random_convex_polygon
from eab.kernel2d.exact import convex_overlap_exact, polygons_overlap_exact
from eab.kernel2d.geom import convex_hull, orient2d, polygons_overlap, translate, triangulate


def _fr_cross(o, a, b):
    o, a, b = [(Fraction(p[0]), Fraction(p[1])) for p in (o, a, b)]
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _fr_area2(P):
    return sum(_fr_cross((0.0, 0.0), P[i], P[(i + 1) % len(P)]) for i in range(len(P)))


# ---------------------------------------------------------------- 网格多联骨牌（带大量平直顶点的简单多边形）

def _polyomino(rng, ncells, span=6):
    """随机生长的格子集合，边界是一条简单闭链（无洞、无角点相切）时返回 (格子集合, 边界多边形)，否则 None。
    边界按单位步长取点：每个格点都是顶点，直边中间的全是平直顶点（DDA 块边上的 T 形顶点就是这样）。"""
    cells = {(0, 0)}
    while len(cells) < ncells:
        i, j = rng.choice(sorted(cells))
        di, dj = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
        if abs(i + di) <= span and abs(j + dj) <= span:
            cells.add((i + di, j + dj))
    nxt = {}
    for i, j in cells:
        for inside, a, b in (((i, j - 1), (i, j), (i + 1, j)), ((i + 1, j), (i + 1, j), (i + 1, j + 1)),
                             ((i, j + 1), (i + 1, j + 1), (i, j + 1)), ((i - 1, j), (i, j + 1), (i, j))):
            if inside not in cells:
                if a in nxt:
                    return None                 # 角点相切：边界在此自触，不是简单多边形
                nxt[a] = b
    start = min(nxt)
    ring, p = [start], nxt[start]
    while p != start:
        ring.append(p)
        p = nxt[p]
    if len(ring) != len(nxt):
        return None                             # 有洞：不止一条边界链
    return cells, [(float(x), float(y)) for x, y in ring]


def _grid_truth(S1, S2):
    """1 内部相交（共格子）/ 0 仅边界接触（有格子共角点）/ −1 分离。只看格子集合。"""
    if S1 & S2:
        return 1
    corners = lambda S: {(i + di, j + dj) for i, j in S for di in (0, 1) for dj in (0, 1)}
    return 0 if corners(S1) & corners(S2) else -1


def _polyomino_pairs(seed, count):
    rng = random.Random(seed)
    out = []
    while len(out) < count:
        a = _polyomino(rng, rng.randint(3, 9))
        b = _polyomino(rng, rng.randint(3, 9))
        if a is None or b is None:
            continue
        di, dj = rng.randint(-4, 4), rng.randint(-4, 4)
        S2 = {(i + di, j + dj) for i, j in b[0]}
        out.append((a[0], a[1], S2, translate(b[1], (float(di), float(dj)))))
    return out


# ---------------------------------------------------------------- (a) 耳切

# G6 复核者的多边形 C：平直顶点与贴在对角线上的顶点；严格耳判据（> 0）在它上面找不到耳、抛错
POLY_C = [(0.0, -4.0), (6.0, 2.0), (6.0, 4.0), (2.0, 4.0), (-2.0, 4.0), (-2.0, 0.0), (0.0, 2.0), (0.0, 1.0),
          (0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (1.0, -1.0), (0.0, -2.0)]


def _check_triangulation(P):
    tris = triangulate(P)
    areas = [_fr_cross(P[i], P[j], P[k]) for i, j, k in tris]
    assert all(a > 0 for a in areas), [a for a in areas if a <= 0]
    assert sum(areas) == abs(_fr_area2(P))


def test_triangulate_polygon_with_flat_vertices_on_a_diagonal():
    """每个三角形精确面积 > 0，总和**精确**等于 |多边形面积|（Fraction），不许抛错。"""
    _check_triangulation(POLY_C)


def test_triangulate_polyominoes_exactly():
    """网格多联骨牌：边上每个格点都是平直顶点，耳切的闭三角判据（≥ 0）必须把贴边的顶点算作挡耳。"""
    rng = random.Random(4)
    n = 0
    while n < 300:
        r = _polyomino(rng, rng.randint(4, 12))
        if r is None:
            continue
        n += 1
        _check_triangulation(r[1])


# ---------------------------------------------------------------- (b) polygons_overlap：贴合与平直顶点

# G6 复核者的一对：在 (4,4) 处只接触，严格耳判据的变异判成内部相交
PAIR_A = [(4.0, 2.0), (8.0, 0.0), (12.0, -2.0), (8.0, 2.0), (8.0, 4.0), (4.0, 4.0), (4.0, 3.0)]
PAIR_B = [(2.0, 8.0), (1.0, 8.0), (0.0, 8.0), (1.0, 6.0), (2.0, 4.0), (1.0, 3.0), (0.0, 2.0), (0.0, 0.0), (1.0, 0.0),
          (2.0, 0.0), (4.0, 4.0), (8.0, 8.0)]


def test_touching_pair_with_flat_vertices_is_contact_both_ways():
    assert polygons_overlap(PAIR_A, PAIR_B, 1e-12) == 0
    assert polygons_overlap(PAIR_B, PAIR_A, 1e-12) == 0


def test_polygons_overlap_on_polyomino_pairs_against_the_cell_oracle():
    """多联骨牌对（整数平移，坐标精确）：大量样本恰好贴边或共角点。判定必须等于格子集合给出的真值，两个方向都是。"""
    wrong = []
    for S1, P1, S2, P2 in _polyomino_pairs(9, 400):
        truth = _grid_truth(S1, S2)
        for got in (polygons_overlap(P1, P2, 0.0), polygons_overlap(P2, P1, 0.0)):
            if got != truth:
                wrong.append((P1, P2, got, truth))
    assert wrong == [], (len(wrong), wrong[:1])


def test_polyomino_oracle_is_not_vacuous():
    counts = {1: 0, 0: 0, -1: 0}
    for S1, _, S2, _ in _polyomino_pairs(9, 400):
        counts[_grid_truth(S1, S2)] += 1
    assert min(counts.values()) >= 40, counts


# ---------------------------------------------------------------- (c) orient2d

def _exact_sign(a, b, c):
    d = _fr_cross(c, a, b)          # (a − c) × (b − c) = cross(b − a, c − a)
    return (d > 0) - (d < 0)


def test_orient2d_is_exact_on_near_collinear_triples():
    """y = x + k·2⁻⁵³ 的近共线三点（G6 复核者的构造）：浮点符号与精确符号不同的占 77%，必须零失配。"""
    rng = random.Random(1)
    bad = []
    for _ in range(20000):
        x = rng.uniform(0.0, 1.0)
        p = (x, x + rng.randint(-3, 3) * 2.0 ** -53)
        q = (rng.uniform(1.0, 10.0),) * 2
        r = (rng.uniform(10.0, 20.0),) * 2
        if orient2d(p, q, r) != _exact_sign(p, q, r):
            bad.append((p, q, r))
    assert bad == [], (len(bad), bad[:1])


@pytest.mark.parametrize("scale", [1.0, 1e5, 1e-3])
def test_orient2d_is_exact_on_rotated_collinear_triples(scale):
    """理想共线的三点旋转、平移后成舍入级近共线（工程坐标上的常态）。"""
    rng = random.Random(2)
    for _ in range(5000):
        th = rng.uniform(0.0, 2 * math.pi)
        u = (math.cos(th), math.sin(th))
        o = (rng.uniform(-scale, scale), rng.uniform(-scale, scale))
        pts = [(o[0] + t * u[0], o[1] + t * u[1]) for t in (rng.uniform(-scale, scale) for _ in range(3))]
        assert orient2d(*pts) == _exact_sign(*pts), pts


# 坐标差 ~1e-155：两个乘积落进次正规区，Shewchuk 的相对界下溢成 0，旧版把错号当真（误差是绝对的 2⁻¹⁰⁷⁵）
SUBNORMAL_TRIPLES = [
    ((4.3835938740543526e-155, 4.748577287763834e-155), (5.5006105444967045e-155, 6.113381595660325e-155),
     (8.866437824992651e-156, 4.758992913258887e-156)),
    ((3.766408200143816e-155, 3.829572129339662e-155), (9.155555035891093e-155, 9.456227572975972e-155),
     (7.568712855019712e-156, 6.873999488991764e-156)),
    ((1.6333856360573501e-155, 1.3944484498759818e-155), (3.2374948230728392e-155, 2.773561993326944e-155),
     (2.2141994142196485e-156, 1.8052795860146668e-156)),
]


@pytest.mark.parametrize("abc", SUBNORMAL_TRIPLES)
def test_orient2d_is_exact_when_the_products_are_subnormal(abc):
    assert orient2d(*abc) == _exact_sign(*abc)


def test_orient2d_is_exact_on_a_subnormal_sweep():
    rng = random.Random(3)
    for sc in (3e-155, 1e-155, 1e-160):
        for _ in range(3000):
            c = (rng.uniform(0.1, 0.3) * sc, rng.uniform(0.1, 0.3) * sc)
            t1, t2 = rng.uniform(1.0, 2.0), rng.uniform(2.0, 4.0)
            d = (rng.uniform(0.5, 1.0), rng.uniform(0.5, 1.0))
            a = (c[0] + t1 * d[0] * sc, c[1] + t1 * d[1] * sc)
            b = (c[0] + t2 * d[0] * sc, c[1] + t2 * d[1] * sc)
            assert orient2d(a, b, c) == _exact_sign(a, b, c), (a, b, c)


def test_orient2d_is_exact_when_the_products_overflow():
    a, b, c = (1e200, 1e200), (-1e200, -1e200 * (1.0 + 2.0 ** -52)), (3e199, 3e199)
    assert orient2d(a, b, c) == _exact_sign(a, b, c) != 0


# ---------------------------------------------------------------- (d) convex_hull

def test_hull_of_a_rotated_collinear_strip_matches_exact_support():
    """一条直线上的点（两端 ±1e5）加一条宽 1 的平行偏移上的两个端点，旋转、平移到 |坐标| ~ 1e5：
    E3 保留 3000 个点集，逐点核对独立 Fraction 全点支持线 oracle；不把舍入后的真极点伪装共线。"""
    rng = random.Random(7)
    sizes = {}
    for _ in range(3000):
        th = rng.uniform(0.0, 2 * math.pi)
        u, v = (math.cos(th), math.sin(th)), (-math.sin(th), math.cos(th))
        o = (rng.uniform(-1e5, 1e5), rng.uniform(-1e5, 1e5))
        ts = [rng.uniform(-1e5, 1e5) for _ in range(6)] + [-1e5, 1e5]
        pts = [(o[0] + t * u[0], o[1] + t * u[1]) for t in ts]
        pts += [(o[0] + e * 1e5 * u[0] + v[0], o[1] + e * 1e5 * u[1] + v[1]) for e in (1.0, -1.0)]
        hull=convex_hull(pts)
        from fractions import Fraction as F
        oracle=set()
        for a in pts:
            for b in pts:
                if a==b: continue
                ds=[(F(b[0])-F(a[0]))*(F(p[1])-F(a[1]))-(F(b[1])-F(a[1]))*(F(p[0])-F(a[0])) for p in pts]
                if min(ds)>=0:
                    line=[p for p,d in zip(pts,ds) if d==0]
                    oracle.update((min(line),max(line)))
        assert set(hull)==oracle
        sizes[len(hull)]=sizes.get(len(hull),0)+1
    assert sum(sizes.values())==3000 and len(sizes)>1, sizes


# ---------------------------------------------------------------- (e) membership_convex 不给 eb：单位缩放

SQUARE = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
OCTAGON = [(2 * math.cos(0.3 + k * math.pi / 4), 2 * math.sin(0.3 + k * math.pi / 4)) for k in range(8)]
X_CANARY = (1.2291069192440532, -2.2938209735925025)


def _scaled(P, s):
    return [(p[0] * s, p[1] * s) for p in P]


@pytest.mark.parametrize("s", [1e-3, 1.0, 1e3])
def test_membership_without_eb_square_over_octagon_canary(s):
    """G6 复核者的例：米制 tol = 1e-3 答 1（对）；毫米制 tol = 1（同一物理容差）旧版答 −1。"""
    A, B, x = _scaled(SQUARE, s), _scaled(OCTAGON, s), (X_CANARY[0] * s, X_CANARY[1] * s)
    assert polygons_overlap(translate(A, x), B, 1e-3 * s) == 1
    assert membership_convex(A, B, x, 1e-3 * s) == 1


@pytest.mark.parametrize("s", [1e-3, 1.0, 1e3])
def test_membership_without_eb_agrees_with_brute_force_in_any_unit(s):
    """旧门只核两侧非零的带外随机点；E2 用独立内联 Fraction SAT 核全部点（不舍入 A+x）。
    零容差逐点全等，另核调用方报告带只能把精确答案改成0，绝不能翻号；原有60×20点与尺度全部保留。"""
    rng = random.Random(21)
    nonzero = 0
    for _ in range(60):
        A0, B0 = random_convex_polygon(rng, rng.randint(3, 7)), random_convex_polygon(rng, rng.randint(3, 8))
        A, B, tol = _scaled(A0, s), _scaled(B0, s), 1e-3 * s
        for _ in range(20):
            x = (rng.uniform(-3.0, 3.0) * s, rng.uniform(-3.0, 3.0) * s)
            truth = convex_overlap_exact(A, B, x)
            assert membership_convex(A, B, x) == truth, (A0, B0, x)
            report = membership_convex(A, B, x, tol)
            assert report in (0, truth), (x, report, truth)
            nonzero += report != 0
    assert nonzero >= 600


# ---------------------------------------------------------------- (f) 凸 E 的平行边合并：逐对、按长度

def _chamfered_square(C, tiny):
    return [(C, C), (C + 1.0, C), (C + 1.0, C + 1.0 - tiny), (C + 1.0 - tiny, C + 1.0), (C, C + 1.0)]


TILTED_TRIANGLE = [(math.cos(0.1) * x - math.sin(0.1) * y, math.sin(0.1) * x + math.cos(0.1) * y)
                   for x, y in ((0.0, 0.0), (1.0, 0.0), (0.5, 0.8))]


@pytest.mark.parametrize("C", [0.0, 1e3, 1e5, 1e6])
@pytest.mark.parametrize("tiny", [1e-4, 1e-8, 1e-10])
def test_a_short_edge_elsewhere_does_not_merge_long_edges(C, tiny):
    """方块一角削去一条 tiny 的短边，三角的底边与方块顶边夹 0.1 rad。旧版的合并下限取整个多边形的最短边：
    tiny = 1e-8 放在 1e5 处下限 0.14 rad，这对长边被并成 FF，成员判定 16/2000 答反、g0 报红。
    E2 不再豁免短边合并或跳过0：全部1500点与独立 Fraction SAT 精确一致，比旧带外门更强。"""
    B = _chamfered_square(C, tiny)
    eb = convex_entrance_block(TILTED_TRIANGLE, B)
    # 旧门豁免短倒角的错误合并；现在连短边也不豁免：本例没有任何精确反向平行边。
    assert not any(f[0] == "FF" for f in eb.facets), eb.facets
    rng = random.Random(1)
    wrong, n = [], 0
    for _ in range(1500):
        x = (C + rng.uniform(-1.5, 1.5), C + rng.uniform(0.2, 2.0))
        m = membership_convex(TILTED_TRIANGLE, B, x, 0.0, eb=eb)
        b = convex_overlap_exact(TILTED_TRIANGLE, B, x)
        n += 1
        if m != b:
            wrong.append((x, m, b))
    assert n > 1000 and wrong == [], (n, wrong[:2])
    rep = g0_convex(TILTED_TRIANGLE, B, samples=400)
    assert rep.passed, (rep.mismatches[:2], rep.facet_symmetric_diff, rep.hull_vertex_mismatch)


@pytest.mark.parametrize("C", [0.0, 1e5])
def test_exact_parallel_edges_merge_independently_of_the_length_ratio(C):
    """旧说明以长度容差解释合并；E2只合并精确平行同向的B/−A边，长短边比不参与判定。
    原轴对齐4FF及真实倾斜3FF两组断言保留；tol内也不合并由test_length_tolerance_never_changes_exact_parallel_merging守护。"""
    big = [(C, C), (C + 1.0, C), (C + 1.0, C + 1.0), (C, C + 1.0)]
    small = [(0.0, 0.0), (1e-6, 0.0), (1e-6, 1e-6), (0.0, 1e-6)]
    assert sum(f[0] == "FF" for f in convex_entrance_block(small, big, tol=1e-9).facets) == 4
    d = 1e-6                                         # 长边（1）倾 1e-6 rad：远大于 1e-6 短边的方向噪声 c·eps·C/1e-6 ≈ 1.4e-8 rad
    tilted = [(0.0, 0.0), (1e-6, 0.0), (1e-6, 1e-6), (0.0, 1e-6)]
    big_t = [(C, C), (C + 1.0, C + d), (C + 1.0, C + 1.0), (C, C + 1.0)]
    labels = convex_entrance_block(tilted, big_t, tol=1e-9).facets
    assert sum(f[0] == "FF" for f in labels) == 3, labels     # 其余三对仍严格平行


ROW = [(0.0, 0.0), (2.0, 0.0), (4.0, 0.0), (4.0, 1.0), (2.0, 1.0), (0.0, 1.0)]
FLAT = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0), (3.0, 1.0), (1.5, 1.0), (0.0, 1.0)]


@pytest.mark.parametrize("quarter", [0, 1, 2, 3])
def test_a_t_vertex_one_ulp_above_the_lowest_edge_uses_the_concave_path(quarter):
    """旧口径把一个ulp微凹吞成平直顶点并强制4FF；E2精确拒收，再走一般简单多边形路径。
    保留四朝向与300点，额外保留精确平直对照；全部答案对闭式矩形减三角缺口 oracle，零带内豁免。
    oracle只用内联 Fraction 区间/线性插值，与凸构造及凹相交的耳切/SAT零共用。"""
    C = 1e5
    bump = math.nextafter(C, math.inf)
    P = [(C, C), (C + 1.0, bump), (C + 2.0, C), (C + 2.0, C + 1.0), (C, C + 1.0)]
    flat = [(C, C), (C + 1.0, C), (C + 2.0, C), (C + 2.0, C + 1.0), (C, C + 1.0)]
    for _ in range(quarter):
        P = [(-y, x) for x, y in P]
        flat = [(-y, x) for x, y in flat]
    for tol in (0.0, 1e-9, 1.0):
        with pytest.raises(ValueError, match="reflex"):
            convex_entrance_block(SQUARE, P, tol=tol)
    eb = convex_entrance_block(SQUARE, flat)
    assert sorted(f[0] for f in eb.facets) == ["FF", "FF", "FF", "FF", "VE"]
    assert all(math.dist(eb.vertices[i], eb.vertices[(i + 1) % len(eb.vertices)]) > 0.5 for i in range(len(eb.vertices)))
    rng = random.Random(quarter)
    cx, cy = (sum(p[0] for p in P) / 5, sum(p[1] for p in P) / 5)
    xs = [(cx + rng.uniform(-2, 2), cy + rng.uniform(-2, 2)) for _ in range(300)]
    # 先在原坐标精确加x，再逆90度旋转，得到轴对齐方块的区间。
    for x in xs:
        points = [(Fraction(a) + Fraction(x[0]), Fraction(b) + Fraction(x[1])) for a, b in SQUARE]
        for _ in range(quarter):
            points = [(b, -a) for a, b in points]
        lo, hi = max(Fraction(C), min(p[0] for p in points)), min(Fraction(C + 2), max(p[0] for p in points))
        low_y, high_y = min(p[1] for p in points), max(p[1] for p in points)
        if lo > hi or low_y > C + 1:
            want = -1
        else:
            h = Fraction(bump) - Fraction(C)
            bottom = lambda z: Fraction(C) + h * min(z - C, C + 2 - z)
            floor = min(bottom(lo), bottom(hi))
            want = -1 if high_y < floor else (0 if lo == hi or high_y == floor or low_y == C + 1 else 1)
        assert membership_convex(SQUARE, P, x) == want, (quarter, x, want)


@pytest.mark.parametrize("P", [ROW, FLAT], ids=["row", "flat"])
@pytest.mark.parametrize("quarter", [0, 1, 2, 3])
@pytest.mark.parametrize("s", [1e-3, 1.0, 1e3])
@pytest.mark.parametrize("tmag", [0.0, 1e3, 1e5, 1e6])
def test_flat_vertices_survive_every_axis_aligned_rigid_motion(P, quarter, s, tmag):
    """复核者扫描的子集（2 × 4 × 3 × 4 = 96 格）：带平直顶点的凸块 × 四个朝向 × 三个单位 × 四个平移，两块一起缩放平移，
    convex_entrance_block 必须都能构造，
    facet 数与原位相同（平直顶点不产生 FF、也不产生零长 facet）。"""
    Q = [(s * x, s * y) for x, y in P]
    for _ in range(quarter):
        Q = [(-y, x) for x, y in Q]
    Q = [(x + 0.6 * tmag, y - 0.8 * tmag) for x, y in Q]
    ref = convex_entrance_block(SQUARE, P).facets
    # A 侧同样缩放、平移（旧版 `if False else SQUARE` 让 A 永远是原位单位方块——G6 第四轮 minor：门不测它声称的东西）
    got = convex_entrance_block([(s * x + 0.6 * tmag, s * y - 0.8 * tmag) for x, y in SQUARE], Q).facets
    assert len(got) == len(ref) and sorted(f[0] for f in got) == sorted(f[0] for f in ref), (got, ref)


_N_ARC = 8000
BAD_INPUTS = {
    "clockwise_square": [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)],
    # 五角星：顶点都在凸包上（凸包深度 0），绕两圈
    "pentagram": [(math.cos(math.pi / 2 + 4 * math.pi * k / 5), math.sin(math.pi / 2 + 4 * math.pi * k / 5))
                  for k in range(5)],
    # 凹弧离散成 8000 小段：每个顶点离邻点弦 ~4e-10 < t = 1e-9、极角下降 ~1e-5 rad，逐顶点看都是舍入级微凹；
    # 整体下凹 0.01，只有凸包深度看得见
    "shallow_concave_arc": [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
                           + [(0.01 * math.sin(math.pi * k / _N_ARC), 1.0 - k / _N_ARC) for k in range(1, _N_ARC)],
}


@pytest.mark.parametrize("name", sorted(BAD_INPUTS))
def test_non_convex_or_clockwise_input_is_refused(name):
    bad = BAD_INPUTS[name]
    with pytest.raises(ValueError, match="not"):
        convex_entrance_block(bad, SQUARE, tol=1e-9)
    with pytest.raises(ValueError, match="not"):
        convex_entrance_block(SQUARE, bad, tol=1e-9)


@pytest.mark.parametrize("seed", range(10))
def test_parallel_edges_with_length_ratio_1000_merge_only_if_exact_after_rotation(seed):
    """旧门无视输入舍入强制4FF；E2以独立内联 Fraction 反平行边对为oracle，逐标签相等而非放松计数。
    原种子/尺度/平移全保留，精确G0三票不跳样本，tiny折点不再豁免。"""
    RECT = [(0.0, 0.0), (1000.0, 0.0), (1000.0, 1.0), (0.0, 1.0)]
    rng = random.Random(seed)
    s, tm = 1e-3, 1e3
    th, phi = rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi)
    c, sn = math.cos(th), math.sin(th)
    f = lambda P: [(s * (c * p[0] - sn * p[1]) + tm * math.cos(phi), s * (sn * p[0] + c * p[1]) + tm * math.sin(phi)) for p in P]
    A, B = f(SQUARE), f(RECT)
    eb = convex_entrance_block(A, B)
    expected = set()
    for i in range(4):
        ax, ay = (Fraction(A[(i + 1) % 4][k]) - Fraction(A[i][k]) for k in (0, 1))
        for j in range(4):
            bx, by = (Fraction(B[(j + 1) % 4][k]) - Fraction(B[j][k]) for k in (0, 1))
            if ax * by == ay * bx and ax * bx + ay * by < 0:
                expected.add(("FF", i, j))
    assert {l for l in eb.facets if l[0] == "FF"} == expected
    assert len(eb.facets) == 8 - len(expected)
    rep = g0_convex(A, B, samples=100, seed=1)
    assert rep.passed, (rep.mismatches[:2], rep.facet_symmetric_diff, rep.hull_vertex_mismatch)
    assert rep.band_skipped == rep.hull_vertex_ambiguous == 0
    assert rep.samples == 100 + rep.boundary_probes


def test_a_vertex_fifty_tolerances_inside_the_hull_is_rejected():
    """G6 第三轮 minor：凸性前提"顶点在凸包以内深度 ≤ t"的牙——旧门深50t拒收、半t接收；E2二者均精确拒收，t不再作为凸性豁免。
    保留两个原样本并收紧旧接受分支；精确平直可接受另由96格门守护。"""
    from eab.kernel2d.geom import coord_scale, round_floor
    t = round_floor(coord_scale(SQUARE))
    P = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.5, 1.0 - 50.0 * t), (0.0, 1.0)]
    with pytest.raises(ValueError, match="not convex"):
        convex_entrance_block(SQUARE, P)
    P2 = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.5, 1.0 - 0.5 * t), (0.0, 1.0)]       # 半个旧容差：仍必须拒收
    with pytest.raises(ValueError, match="reflex"):
        convex_entrance_block(SQUARE, P2)


@pytest.mark.parametrize("C", [1.0, 1e5])
def test_length_tolerance_never_changes_exact_parallel_merging(C):
    """旧门 δ=tol/2合并、2tol不并；E2非零精确叉积一律不并，tol只兼容参数。
    保留原两倾角，新增δ=0边界与tol=0/1e-7/1，要求标签与顶点都不依tol变化，三组几何产物必须互异。"""
    tol = 1e-7
    products = []
    for d, n_ff in ((0.0, 4), (0.5 * tol, 3), (2.0 * tol, 3)):
        big = [(C, C), (C + 1.0, C + d), (C + 1.0, C + 1.0), (C, C + 1.0)]
        ref = convex_entrance_block(SQUARE, big)
        for window in (0.0, tol, 1.0):
            got = convex_entrance_block(SQUARE, big, tol=window)
            assert got == ref
            assert sum(f[0] == "FF" for f in got.facets) == n_ff, (C, d, got.facets)
        products.append(tuple(ref.vertices))
    assert len(set(products)) == 3
