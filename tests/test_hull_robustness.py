"""WO-E5a exact convex hull gates, retaining the historical test names and grids.

Independent oracle: Fraction determinant/support and rank of incident normals.
The hull neither flattens a sub-tolerance ridge nor retains nonextreme vertices.
Mutation gates act inside the construction or supporting-plane certificate.
"""

from __future__ import annotations
from construction_oracle import scalar_exact, sqrt_exact

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
            worst = max(worst, sqrt_exact(top * top / nn))
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


@pytest.mark.parametrize("tol,nverts", [(1e-12, 22), (1e-9, 22), (1e-7, 22)])
def test_ridge_and_needle_difference_hull_builds_at_the_requested_tolerance(tol, nverts):
    """Every historical tolerance cell preserves all 22 exact vertices; support is zero-band."""
    A, B = _ridge_pair()
    diffs = [sub(b, a) for a in A.verts for b in B.verts]
    H = G3._quickhull(diffs, tol)
    assert H.manifold_issues() == []
    L = norm(sub(*reversed(H.aabb())))
    _assert_exact_hull(H, diffs)
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
    """Historical name retained. Rounded rotated inputs need not have eight extreme vertices; exact support and extremality replace approximate topology."""
    R = _rot(seed)
    A = _rotated(box(half=(1.0, 1.0, 1.0)), R)
    B = _rotated(box(center=(0.3, 0.0, -0.2), half=(2.0, 0.5, 1.0)), R)
    diffs = [sub(b, a) for a in A.verts for b in B.verts]
    H, _, _ = G3._quickhull_once(diffs, 1e-12, set())
    _assert_exact_hull(H, diffs)
    assert len(H.verts) >= 8 and len(H.faces) == 2 * len(H.verts) - 4
    assert H.volume() == pytest.approx(6.0 * 3.0 * 4.0, rel=1e-12)


def test_sliver_fallback_removes_the_middle_of_three_collinear_vertices(monkeypatch):
    """Exact hull omits boundary-interior points; mutation keeps them as vertices."""
    import inspect
    pts=list(box().verts)+[(0.,0.,1.),(0.,1.,1.),(0.,0.,0.)]
    _assert_exact_hull(G3._quickhull(pts,0.),pts)
    src=inspect.getsource(G3._quickhull_once)
    old='used=sorted({i for f in rings for i in f})'
    assert old in src
    src=src.replace(old,'used=list(range(len(pts)))')
    ns=dict(vars(G3));exec(src,ns)
    monkeypatch.setattr(G3,'_quickhull_once',ns['_quickhull_once'])
    bad=G3._quickhull(pts,0.)
    with pytest.raises(AssertionError):
        _assert_exact_hull(bad,pts)



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
    """Engineering-coordinate input builds once and passes the independent exact hull certificate."""
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
    _assert_exact_hull(H, [sub(b,a) for a in A.verts for b in B.verts])
    assert H.manifold_issues() == []
    assert H.volume() == pytest.approx(72.0, rel=1e-7)


def test_noise_floor_in_the_hull_has_teeth(monkeypatch):
    """The retired noise floor cannot change a hull, even at engineering coordinates."""
    R=_rot(7)
    A=_rotated(box(half=(1.,1.,1.)),R)
    B=_rotated(box(center=(6e5+.3,-4.8e5,6.4e5-.2),half=(2.,.5,1.)),R)
    diffs=[sub(b,a) for a in A.verts for b in B.verts]
    before=G3._quickhull(diffs,1e-14)
    def forbidden(_):
        raise AssertionError('a noise floor changed exact hull topology')
    monkeypatch.setattr(G3,'noise_floor',forbidden)
    after=G3._quickhull(diffs,1e-14)
    assert after.verts == before.verts and after.faces == before.faces
    _assert_exact_hull(after,diffs)



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
    _assert_exact_hull(H, diffs)


@pytest.mark.parametrize("tm,s", [(0.0, 1.0), (1e3, 1.0), (1e5, 1e-3), (1e6, 1e3)])
@pytest.mark.parametrize("seed", range(30))
def test_rotated_ridge_needle_family_builds_without_escalation(seed, tm, s):
    """All 120 rotation/translation/scale cells preserve every exact supporting halfspace with no escalation."""
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
    _assert_exact_hull(H, diffs)
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
    """Numerical failure is never hidden by a larger answer-changing band."""
    calls=[]
    def flaky(points,tol):
        calls.append(tol)
        raise HullNumericalFailure('forced exact certificate failure')
    monkeypatch.setattr(G3,'_quickhull',flaky)
    for cap in (1e-10,1e-8):
        calls.clear()
        with pytest.raises(HullNumericalFailure):
            convex_hull_3d(list(box().verts),tol=1e-12,max_tol=cap)
        assert calls == [1e-12]



def test_exact_convexity_oracle_catches_a_point_the_build_was_made_to_ignore(monkeypatch):
    """An exact exterior point cannot escape the production certificate, at any depth."""
    pts=list(box().verts)
    pts.append((Fraction(0),Fraction(0),Fraction(1)+Fraction(1,2**80)))
    idx=len(pts)-1
    real=G3._quickhull_once
    def ignoring(points,tol,skip):
        return real(points,tol,set(skip)|{idx})
    monkeypatch.setattr(G3,'_quickhull_once',ignoring)
    with pytest.raises(HullNumericalFailure,match='exact supporting-plane certificate'):
        G3._quickhull(pts,1e-12)



def _assert_exact_hull(H,pts):
    """Independent Fraction determinant oracle: support, input fidelity, extreme vertices.

    No geom3/covers predicates, normals, tolerances, or hull implementation are used.
    """
    from itertools import combinations
    assert set(H.verts).issubset(set(pts))
    for f in H.faces:
        assert all(_fr_orient(*(H.verts[i] for i in f[:3]),p) <= 0 for p in pts)
    for vi,p in enumerate(H.verts):
        ns=[]
        for f in H.faces:
            if vi not in f:
                continue
            o,a,b=(tuple(Fraction(c) for c in H.verts[j]) for j in f[:3])
            u=tuple(a[k]-o[k] for k in range(3));v=tuple(b[k]-o[k] for k in range(3))
            ns.append((u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]))
        assert any(_fr_orient((0,0,0),a,b,c) != 0 for a,b,c in combinations(ns,3)), ('nonextreme vertex',vi,p)
