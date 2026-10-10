"""M0.3 凸包组的门（G6 第二轮 major，geom3.py:1009）：Quickhull 在近退化输入上的正确性与它的牙。

G6 第二轮：厚平面规则不修复凹的地平线棱，1e-6 的棱脊 + 1 m 细针的差点集在 1e-9、1e-7 下造出非凸壳，只能靠
逐级放大容差（到 1e-6·L）自救、抹平真实特征；g0_convex3 在正确的凸对上报红；自检与噪声底都没有门
（逐一关掉全套照绿）。M0.3 的做法："精确谓词、非精确构造"——可见性用精确 orient3d 的闭判据，厚阈值只选外点；
外点按全局最远者优先、并列按离质心最远裁决（凸组合点输给生成点）；细条面兜底。
oracle：Fraction 精确叉积（独立于 geom3.orient3d 的实现）；闭式顶点数；brute "每个输入点都在每个面内侧"。
"""

from __future__ import annotations

import math
import random
from fractions import Fraction

import pytest

import eab.kernel3d.geom3 as G3
from eab.kernel3d.g03 import g0_convex3
from eab.kernel3d.geom3 import (HullNumericalFailure, Polyhedron, box, convex_hull_3d, cross, dot, norm, orient3d,
                                sub)


def _fr_orient(a, b, c, p):
    F = Fraction
    u = [F(b[i]) - F(a[i]) for i in range(3)]
    v = [F(c[i]) - F(a[i]) for i in range(3)]
    w = [F(p[i]) - F(a[i]) for i in range(3)]
    d = (u[0] * (v[1] * w[2] - v[2] * w[1]) - u[1] * (v[0] * w[2] - v[2] * w[0]) + u[2] * (v[0] * w[1] - v[1] * w[0]))
    return (d > 0) - (d < 0)


def _exact_worst_outside(H: Polyhedron, pts) -> float:
    """输入点越出凸包各面的最大有符号距离，Fraction 精确（法向 = 面前三点的叉积，距离 = 点积 / |n|）。"""
    worst = 0.0
    for f in H.faces:
        o, a, b = (tuple(Fraction(c) for c in H.verts[i]) for i in f[:3])
        u = tuple(x - y for x, y in zip(a, o))
        v = tuple(x - y for x, y in zip(b, o))
        n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        nn = n[0] * n[0] + n[1] * n[1] + n[2] * n[2]
        if nn == 0:
            continue
        top = max(sum(ni * (Fraction(pi) - oi) for ni, pi, oi in zip(n, p, o)) for p in pts)
        if top > 0:
            worst = max(worst, math.sqrt(float(top * top / nn)))
    return worst


def _worst_outside(H: Polyhedron, pts) -> float:
    return max(dot(H.face_normal(fi), sub(p, H.verts[H.faces[fi][0]])) for fi in range(len(H.faces)) for p in pts)


# ---------------------------------------------------------------- 精确谓词

def test_orient3d_matches_exact_arithmetic_on_near_coplanar_quadruples():
    rng = random.Random(5)
    bad = 0
    for _ in range(4000):
        a = (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))
        b = (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))
        c = (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))
        s, t = rng.uniform(-2, 2), rng.uniform(-2, 2)
        p0 = tuple(a[i] + s * (b[i] - a[i]) + t * (c[i] - a[i]) for i in range(3))     # 近共面（舍入级）
        p = tuple(x + rng.randint(-2, 2) * 2.0 ** -52 * max(1.0, abs(x)) for x in p0)
        if orient3d(a, b, c, p) != _fr_orient(a, b, c, p):
            bad += 1
    assert bad == 0


def test_orient3d_sign_convention():
    assert orient3d((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)) == 1        # p 在右手法向 +z 一侧
    assert orient3d((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, -1)) == -1
    assert orient3d((0, 0, 0), (1, 0, 0), (0, 1, 0), (0.3, 0.3, 0.0)) == 0


# ---------------------------------------------------------------- 棱脊 + 细针（G6 复核者的输入）

def _ridge_pair():
    sec = [(-1.0, -1.0), (1.0, -1.0), (1.0, 0.0), (0.0, 1e-6), (-1.0, 0.0)]
    B = Polyhedron([(-2.0, y, z) for y, z in sec] + [(2.0, y, z) for y, z in sec],
                   [(4, 3, 2, 1, 0), (5, 6, 7, 8, 9)] + [(i, (i + 1) % 5, 5 + (i + 1) % 5, 5 + i) for i in range(5)])
    A = convex_hull_3d([(0.3, 0.0, 0.050001)] + [(0.3 + 1e-3 * math.cos(t), 1e-3 * math.sin(t), 1.050001)
                                                 for t in (0.1, 2.1943951, 4.2887902)])
    return A, B


@pytest.mark.parametrize("tol,nverts", [(1e-12, 22), (1e-9, 20), (1e-7, 20)])
def test_ridge_and_needle_difference_hull_builds_at_the_requested_tolerance(tol, nverts):
    """单次构建（不放大）必须成功，每个输入点在每个面的 4·eps_d 内侧，1e-6 高的棱脊在三个容差下都保留。
    顶点数：1e-12 下 22；两个"针尖级"E 顶点（针底顶点 × 棱脊顶点，两侧 EE facet 法向只差 2e-9 rad，离凸包
    ~2e-12）在 1e-9·L 的容差里本来就该被吸掉，剩 20——容差的含义就是这个，不是抹平。"""
    A, B = _ridge_pair()
    diffs = [sub(b, a) for a in A.verts for b in B.verts]
    H = G3._quickhull(diffs, tol)
    assert H.manifold_issues() == []
    L = norm(sub(*reversed(H.aabb())))
    assert _worst_outside(H, diffs) <= 4.0 * max(tol * L, G3.noise_floor(5.0))
    assert len(H.verts) == nverts
    assert max(v[2] for v in H.verts) == pytest.approx(1e-6 - 0.050001, abs=1e-12)     # 棱脊顶点仍是凸包顶点


def test_ridge_and_needle_pass_the_three_votes():
    A, B = _ridge_pair()
    rep = g0_convex3(A, B, samples=50, seed=1)
    assert rep.passed, rep
    assert rep.hull_vertices == rep.e_vertices == 22 and rep.facet_symmetric_diff == [], rep


# ---------------------------------------------------------------- 旋转方块对：共线/共面差点不成为顶点

def _rot(seed):
    rng = random.Random(9100 + seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def _rotated(P, R):
    return Polyhedron([tuple(sum(R[i][j] * p[j] for j in range(3)) for i in range(3)) for p in P.verts], list(P.faces))


@pytest.mark.parametrize("seed", range(12))
def test_rotated_box_pair_hull_has_exactly_eight_vertices_on_the_first_build(seed):
    """box ⊕ (−box) 的 64 个差点里 56 个落在面内/棱上（旋转后只差舍入）：凸包必须恰有 8 个顶点，而且**一次**
    构建就对（不靠细条面兜底重建）。旧版（按面取最远点、并列按下标）棱中点先于端点成为顶点：9 个顶点、细条面。"""
    R = _rot(seed)
    A = _rotated(box(half=(1.0, 1.0, 1.0)), R)
    B = _rotated(box(center=(0.3, 0.0, -0.2), half=(2.0, 0.5, 1.0)), R)
    diffs = [sub(b, a) for a in A.verts for b in B.verts]
    H, _, _ = G3._quickhull_once(diffs, 1e-12, set())
    assert len(H.verts) == 8 and len(H.faces) == 12, (len(H.verts), len(H.faces))
    assert H.volume() == pytest.approx(6.0 * 3.0 * 4.0, rel=1e-12)


def test_sliver_fallback_removes_the_middle_of_three_collinear_vertices(monkeypatch):
    """兜底的牙：把并列裁决换回"按下标"（旧版），旋转方块对一次构建得到 9 个顶点与一个细条面（法向是垃圾，
    有输入点"外露" 0.16）；外壳必须排除居中的那个顶点、重建成 8 个顶点。再把兜底关掉，细条面就留下来了。"""
    import inspect
    R = _rot(3)
    A = _rotated(box(half=(1.0, 1.0, 1.0)), R)
    B = _rotated(box(center=(0.3, 0.0, -0.2), half=(2.0, 0.5, 1.0)), R)
    diffs = [sub(b, a) for a in A.verts for b in B.verts]
    src = inspect.getsource(G3._quickhull_once)
    src = src.replace("return max(tied, key=lambda i: dot(sub(pts[i], cen), sub(pts[i], cen)))", "return tied[0]")
    src = src.replace("return max(tied, key=lambda t: dot(sub(pts[t[1]], cen), sub(pts[t[1]], cen)))", "return tied[0]")
    assert src != inspect.getsource(G3._quickhull_once)
    ns = dict(vars(G3))
    exec(src, ns)
    H9, _, eps_d = ns["_quickhull_once"](list(dict.fromkeys(diffs)), 1e-12, set())
    assert len(H9.verts) == 9 and _worst_outside(H9, diffs) > 1e4 * eps_d   # 旧裁决：棱中点成了顶点，细条面法向是垃圾
    assert G3._sliver_middle_vertex(H9, eps_d) is not None
    monkeypatch.setattr(G3, "_quickhull_once", ns["_quickhull_once"])
    H = G3._quickhull(diffs, 1e-12)                                    # 兜底把它修回 8 个（不放大容差）
    assert len(H.verts) == 8 and H.volume() == pytest.approx(72.0, rel=1e-12)
    monkeypatch.setattr(G3, "_sliver_middle_vertex", lambda P, eps: None)
    assert len(G3._quickhull(diffs, 1e-12).verts) == 9                 # 没有兜底就带着细条面返回（自检按面噪声放宽，看不见它）


# ---------------------------------------------------------------- 自检与噪声底的牙（G6 第二轮点名"关掉照绿"）

def test_self_check_raises_on_a_non_convex_result(monkeypatch):
    """注入：BFS 把每个面都判"不可见"（视界为空 → 新点挂不上去 → 结果不含该点、不凸）。自检必须抛
    HullNumericalFailure，而不是返回一个把输入点留在外面的"凸包"。"""
    monkeypatch.setattr(G3, "orient3d", lambda a, b, c, p: -1)
    rng = random.Random(2)
    pts = [(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(30)]
    with pytest.raises(HullNumericalFailure):
        convex_hull_3d(pts)


@pytest.mark.parametrize("C", [1e5, 1e6])
def test_far_coordinate_minkowski_hulls_build_without_escalation(C):
    """两体都在 1e5 / 1e6 处：差点 ~L 量级，噪声却是 eps·|原坐标|。`entrance_block_convex` 把原坐标的舍入地板
    折算成相对容差传给凸包，一次构建成功（旧版靠 ×100 逐级放大自救）。"""
    from eab.margin import entrance_block_convex
    R = _rot(7)
    t = (0.6 * C, -0.48 * C, 0.64 * C)
    A = _rotated(box(center=t, half=(1.0, 1.0, 1.0)), R)
    B = _rotated(box(center=(t[0] + 0.3, t[1], t[2] - 0.2), half=(2.0, 0.5, 1.0)), R)
    calls = []
    real = G3._quickhull
    monkeypatch_target = G3

    def spy(points, tol):
        calls.append(tol)
        return real(points, tol)
    monkeypatch_target._quickhull, saved = spy, monkeypatch_target._quickhull
    try:
        H = entrance_block_convex(A, B)
    finally:
        monkeypatch_target._quickhull = saved
    assert len(calls) == 1, calls
    assert len(H.verts) == 8 and H.manifold_issues() == []
    assert H.volume() == pytest.approx(72.0, rel=1e-7)


def test_noise_floor_in_the_hull_has_teeth(monkeypatch):
    """凸包自己的地板 c·eps·C（按**差点**坐标）：两体相距 1e6 时差点坐标本身 ~1e6，tol = 1e-14 的容差带 6e-14 小于
    差点的舍入噪声 2e-10——没有地板就造不出凸包（自检抛错），有地板一次成功。"""
    R = _rot(7)
    A = _rotated(box(half=(1.0, 1.0, 1.0)), R)
    B = _rotated(box(center=(6e5 + 0.3, -4.8e5, 6.4e5 - 0.2), half=(2.0, 0.5, 1.0)), R)
    diffs = [sub(b, a) for a in A.verts for b in B.verts]
    assert len(G3._quickhull(diffs, 1e-14).verts) == 8
    monkeypatch.setattr(G3, "noise_floor", lambda C: 0.0)
    try:
        H = G3._quickhull(diffs, 1e-14)
    except (HullNumericalFailure, ValueError):
        return                                                       # 自检抓到噪声级的"非凸"
    assert len(H.verts) > 8, len(H.verts)                            # 或者把舍入噪声点都收成了顶点


# ---------------------------------------------------------------- 随机家族：脊 + 针（G6 复核者的 300 抽样）

@pytest.mark.parametrize("seed", range(40))
def test_ridge_needle_family_never_needs_tolerance_escalation(seed):
    rng = random.Random(100 + seed)
    h = 10 ** rng.uniform(-9, -4)
    r = 10 ** rng.uniform(math.log10(3e-4), -1)
    sec = [(-1.0, -1.0), (1.0, -1.0), (1.0, 0.0), (0.0, h), (-1.0, 0.0)]
    B = Polyhedron([(-2.0, y, z) for y, z in sec] + [(2.0, y, z) for y, z in sec],
                   [(4, 3, 2, 1, 0), (5, 6, 7, 8, 9)] + [(i, (i + 1) % 5, 5 + (i + 1) % 5, 5 + i) for i in range(5)])
    A = convex_hull_3d([(0.3, 0.0, h + 0.05)] + [(0.3 + r * math.cos(t), r * math.sin(t), h + 1.05)
                                                 for t in (0.1, 2.1943951, 4.2887902)])
    diffs = [sub(b, a) for a in A.verts for b in B.verts]
    calls = []
    real = G3._quickhull

    def spy(points, tol):
        calls.append(tol)
        return real(points, tol)
    G3_convex = convex_hull_3d
    import eab.kernel3d.geom3 as mod
    mod._quickhull, saved = spy, mod._quickhull
    try:
        H = G3_convex(diffs, tol=1e-12)
    finally:
        mod._quickhull = saved
    assert calls == [1e-12], calls                                  # 一次成功，不放大
    assert _worst_outside(H, diffs) <= 4.0 * max(1e-12 * 6.0, G3.noise_floor(5.0)) + 1e-15


@pytest.mark.parametrize("tm,s", [(0.0, 1.0), (1e3, 1.0), (1e5, 1e-3), (1e6, 1e3)])
@pytest.mark.parametrize("seed", range(30))
def test_rotated_ridge_needle_family_builds_without_escalation(seed, tm, s):
    """G6 第三轮 major：同一家族加一个一般旋转后，旧版 300 例里 47 例 _quickhull(1e-12) 自检失败、靠放大容差自救——
    细条三角的法向噪声没进自检。现在自检按面自己的法向噪声放宽，一次建成；平移到 1e3–1e6、缩放 1e-3–1e3 同样
    （审查者的 300 例旋转+平移+缩放扫描在修后 0 例放大）。"""
    rng = random.Random(500 + seed)
    h = 10 ** rng.uniform(-9, -4)
    r = 10 ** rng.uniform(math.log10(3e-4), -1)
    sec = [(-1.0, -1.0), (1.0, -1.0), (1.0, 0.0), (0.0, h), (-1.0, 0.0)]
    B = Polyhedron([(-2.0, y, z) for y, z in sec] + [(2.0, y, z) for y, z in sec],
                   [(4, 3, 2, 1, 0), (5, 6, 7, 8, 9)] + [(i, (i + 1) % 5, 5 + (i + 1) % 5, 5 + i) for i in range(5)])
    A = convex_hull_3d([(0.3, 0.0, h + 0.05)] + [(0.3 + r * math.cos(t), r * math.sin(t), h + 1.05)
                                                 for t in (0.1, 2.1943951, 4.2887902)])
    R = _rot(seed + 1)
    t = (0.6 * tm, -0.48 * tm, 0.64 * tm)
    mv = lambda P: Polyhedron([tuple(t[i] + s * sum(R[i][j] * p[j] for j in range(3)) for i in range(3)) for p in P.verts],
                              list(P.faces))
    A, B = mv(A), mv(B)
    diffs = [sub(b, a) for a in A.verts for b in B.verts]
    H = G3._quickhull(diffs, 1e-12)                                   # 不经 convex_hull_3d 的放大
    assert H.manifold_issues() == []
    assert len(H.verts) >= 20
    # 精确凸性 oracle（G6 第四轮 minor：旧门没有凸性断言，把自检的面噪声放宽项放大 100 倍全套照绿）：每个输入点在每个面的
    # 内侧，越界不超过 4·eps_d（Fraction 精确算；120 格实测最大 0.99·eps_d）
    eps_d = G3._quickhull_once(list(dict.fromkeys(diffs)), 1e-12, set())[2]
    assert _exact_worst_outside(H, diffs) <= 4.0 * eps_d, (seed, tm, s, _exact_worst_outside(H, diffs), eps_d)
    calls = []
    real = G3._quickhull
    monkey = lambda p, tol: (calls.append(tol), real(p, tol))[1]
    import eab.kernel3d.geom3 as mod
    mod._quickhull = monkey
    try:
        convex_hull_3d(diffs, tol=1e-12)
    finally:
        mod._quickhull = real
    assert calls == [1e-12], calls


def test_max_tol_cap_raises_instead_of_escalating_forever(monkeypatch):
    """max_tol 封顶的牙：让 _quickhull 在 tol < 1e-8 时一律自检失败，convex_hull_3d(tol=1e-12, max_tol=1e-10) 必须抛
    HullNumericalFailure，max_tol=1e-8 时放大到 1e-8 建成。"""
    import eab.kernel3d.geom3 as mod
    real = mod._quickhull
    calls = []

    def flaky(points, tol):
        calls.append(tol)
        if tol < 1e-8:
            raise HullNumericalFailure("forced")
        return real(points, tol)
    monkeypatch.setattr(mod, "_quickhull", flaky)
    pts = list(box(half=(1.0, 0.5, 0.3)).verts)
    with pytest.raises(HullNumericalFailure):
        convex_hull_3d(pts, tol=1e-12, max_tol=1e-10)
    assert max(calls) <= 1e-10
    calls.clear()
    assert len(convex_hull_3d(pts, tol=1e-12, max_tol=1e-8).verts) == 8
    assert calls[-1] == pytest.approx(1e-8)


def test_exact_convexity_oracle_catches_a_point_the_build_was_made_to_ignore(monkeypatch):
    """放宽尺度的牙：把一个离最细条面 10·eps_d 的点加进输入、再让构建忽略它（monkeypatch _quickhull_once 的 skip），
    返回的"凸包"要么被自检抛错，要么被精确 oracle 判越界——两者都不发生才是门失效（自检按面噪声放宽后对细条面附近
    ≤ fn·力臂 的越界不敏感，凸性由这里的精确 oracle 把关）。"""
    rng = random.Random(777)
    h = 10 ** rng.uniform(-9, -4)
    r = 10 ** rng.uniform(math.log10(3e-4), -1)
    sec = [(-1.0, -1.0), (1.0, -1.0), (1.0, 0.0), (0.0, h), (-1.0, 0.0)]
    B = Polyhedron([(-2.0, y, z) for y, z in sec] + [(2.0, y, z) for y, z in sec],
                   [(4, 3, 2, 1, 0), (5, 6, 7, 8, 9)] + [(i, (i + 1) % 5, 5 + (i + 1) % 5, 5 + i) for i in range(5)])
    A = convex_hull_3d([(0.3, 0.0, h + 0.05)] + [(0.3 + r * math.cos(t), r * math.sin(t), h + 1.05) for t in (0.1, 2.1943951, 4.2887902)])
    R = _rot(5)
    A, B = _rotated(A, R), _rotated(B, R)
    pts = list(dict.fromkeys(sub(b, a) for a in A.verts for b in B.verts))
    H0, _, eps_d = G3._quickhull_once(pts, 1e-12, set())
    # 最细条的面：面噪声 fl·周长/面积最大者
    fl = G3.noise_floor(G3.coord_scale(*pts))
    worst_face, worst_fn = None, -1.0
    for f in H0.faces:
        o, a, b = (H0.verts[i] for i in f[:3])
        n = G3.cross(sub(a, o), sub(b, o))
        area2 = G3.norm(n)
        per = G3.norm(sub(a, o)) + G3.norm(sub(b, a)) + G3.norm(sub(o, b))
        fn = fl * per / area2 if area2 > 0 else float("inf")
        if fn > worst_fn:
            worst_face, worst_fn = f, fn
    o, a, b = (H0.verts[i] for i in worst_face[:3])
    n = G3.unit(G3.cross(sub(a, o), sub(b, o)))
    cen = tuple((o[i] + a[i] + b[i]) / 3.0 for i in range(3))
    p_star = tuple(cen[i] + 10.0 * eps_d * n[i] for i in range(3))
    pts2 = pts + [p_star]
    idx = len(pts2) - 1
    real_once = G3._quickhull_once

    def ignoring(points, tol, skip):
        return real_once(points, tol, set(skip) | {idx})
    monkeypatch.setattr(G3, "_quickhull_once", ignoring)
    try:
        H = G3._quickhull(pts2, 1e-12)
    except HullNumericalFailure:
        return                                                      # 自检抓到了
    assert _exact_worst_outside(H, pts2) > 4.0 * eps_d, "被忽略的外点既没被自检抓到、精确 oracle 也看不见——门失效"
