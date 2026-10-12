"""G6 第四轮 major：近平行棱对（θ ≲ 1e-7）的最近点参数——盖路径 covers3._closest_params 与 oracle geom3._seg_seg_distance 曾用同一个
den = a·c − b² 的公式，两边同错同值（自校验失明），body_distance 报出 1.8 … 7 倍于真值的距离、膨胀成员判定 fail-unsafe。
这里的 oracle 是**有理数候选枚举**（内点候选叉积式 + 四条边上的钳位候选，全部 Fraction 精确），与两条被测路径的算法都不同。"""

from __future__ import annotations

import math
import random
from fractions import Fraction

import pytest
from e5b_margin_oracle import check_exact_margin
from construction_oracle import sqrt_exact
import eab.margin as exact_margin

from eab.kernel3d.geom3 import Polyhedron, _seg_seg_distance, brute_feature_distance, tetra
from eab.margin import INSIDE, PENETRATING, body_distance, contact_resolution, inflated_membership, rounding_floor


def _fv(p):
    return tuple(Fraction(x) for x in p)


def _fsub(u, v):
    return tuple(a - b for a, b in zip(u, v))


def _fadd(u, v):
    return tuple(a + b for a, b in zip(u, v))


def _fmul(u, s):
    return tuple(a * s for a in u)


def _fdot(u, v):
    return sum(a * b for a, b in zip(u, v))


def _fcross(u, v):
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def exact_seg_seg(p1, p2, q1, q2, *, squared=False):
    """两线段最短距离的精确候选枚举（Fraction），最后开一次方。"""
    P1, P2, Q1, Q2 = map(_fv, (p1, p2, q1, q2))
    d1, d2, w = _fsub(P2, P1), _fsub(Q2, Q1), _fsub(Q1, P1)
    a, c = _fdot(d1, d1), _fdot(d2, d2)
    cands = []
    n = _fcross(d1, d2)
    nn = _fdot(n, n)
    if nn:
        s, t = _fdot(_fcross(w, d2), n) / nn, _fdot(_fcross(w, d1), n) / nn
        if 0 <= s <= 1 and 0 <= t <= 1:
            cands.append((s, t))
    for s in (Fraction(0), Fraction(1)):
        t = _fdot(_fsub(_fadd(P1, _fmul(d1, s)), Q1), d2) / c
        cands.append((s, min(max(t, Fraction(0)), Fraction(1))))
    for t in (Fraction(0), Fraction(1)):
        s = _fdot(_fsub(_fadd(Q1, _fmul(d2, t)), P1), d1) / a
        cands.append((min(max(s, Fraction(0)), Fraction(1)), t))
    best = min(_fdot(v, v) for v in (_fsub(_fadd(P1, _fmul(d1, s)), _fadd(Q1, _fmul(d2, t))) for s, t in cands))
    return best if squared else sqrt_exact(best)


def _quat(seed: int):
    rng = random.Random(9100 + seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    k = math.sqrt(sum(x * x for x in q))
    w, x, y, z = (v / k for v in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def _move(P: Polyhedron, R, t=(0.0, 0.0, 0.0)) -> Polyhedron:
    return Polyhedron([tuple(t[i] + sum(R[i][j] * p[j] for j in range(3)) for i in range(3)) for p in P.verts], list(P.faces))


I3 = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def _ridge_pair(theta: float, gap: float, half: float):
    """B 的顶棱沿 x（长 2），A 的底棱长 2·half、在 z = gap 处绕 z 转 θ；真最近对是两棱内部点，距离恰 gap。"""
    B = tetra((-1.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, -0.8, -1.5), (0.0, 0.9, -1.4))
    c, s = math.cos(theta), math.sin(theta)
    x0 = 0.1
    A = tetra((x0 - half * c, -half * s, gap), (x0 + half * c, half * s, gap),
              (x0 - 0.1, -0.7, 1.3 + gap), (x0 + 0.2, 0.8, 1.2 + gap))
    return A, B


@pytest.mark.parametrize("rot", [0, 3, 11])
@pytest.mark.parametrize("half", [0.3, 1.4])
@pytest.mark.parametrize("gap", [1e-9, 1e-6])
@pytest.mark.parametrize("theta", [1e-6, 1e-7, 1e-8, 1e-9])
def test_near_parallel_ridge_edges_match_the_exact_rational_distance(theta, gap, half, rot):
    A0, B0 = _ridge_pair(theta, gap, half)
    R = _quat(rot) if rot else I3
    A, B = _move(A0, R), _move(B0, R)
    ea = (A.verts[0], A.verts[1])
    eb = (B.verts[0], B.verts[1])
    exact = exact_seg_seg(*ea, *eb)
    rnd = rounding_floor(A, B)
    assert exact == pytest.approx(gap, rel=1e-6)
    d_ab = _seg_seg_distance(*ea, *eb)
    d_ba = _seg_seg_distance(*eb, *ea)
    assert abs(d_ab - exact) <= 4.0 * rnd + 1e-15 and abs(d_ba - exact) <= 4.0 * rnd + 1e-15, (theta, gap, d_ab, d_ba, exact)
    assert abs(brute_feature_distance(A, B) - exact) <= 4.0 * rnd + 1e-15
    check_exact_margin(A, B, 1.5 * exact, state=-1,
                       minimum_squared=exact_seg_seg(*ea, *eb, squared=True))
    d, lab = body_distance(A, B, contact_window=contact_resolution(A, B))                         # 自校验不许误抛；距离在相触分辨率以内才钳 0
    ctol = contact_resolution(A, B)
    assert lab != (PENETRATING,)
    if exact > ctol:
        assert abs(d - exact) <= 8.0 * rnd + 1e-15, (theta, gap, d, exact, lab)
    else:
        assert d == 0.0
    # Retain the original assertion text through an explicit-window adapter.
    inflated_membership = lambda A, B, **kw: exact_margin.inflated_membership(
        A, B, contact_window=contact_resolution(A, B), **kw)
    assert inflated_membership(A, B, delta=1.5 * exact) == INSIDE
