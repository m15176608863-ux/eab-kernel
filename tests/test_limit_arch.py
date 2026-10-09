"""M1 · 多块半圆拱：LP 的 α 对照**枚举四铰机构**的运动学上限（独立 oracle：刚体链相容性 + 虚功率，不经任何 LP 列代码）。

几何：半圆拱，内半径 1、外半径 r_out（薄拱 1.15，t/R ≈ 0.14：自重下能站住（Heyman 最小 t/R ≈ 0.106），拱顶集中荷载的直线索多边形
进不了环，所以有有限的铰机构承载；厚拱 1.5，t/R = 0.4：直线索整个落在环内，高摩擦下承载无限），N 块券石等分 180°，径向缝；
两端缝（0°、180°）是水平线，坐在固定基座上（基座推券石的方向 +y）。自重 = 10 × 面积；活荷载是拱顶外弧点 (0, r_out) 处的竖向集中力
（N 取奇数，拱顶落在中间那块上）。

上限定理：任一容许机构给出 α 的上限；四铰机构（任选 4 条缝，每条在内弧角或外弧角开铰、另一角张开，其余缝粘住）在关联流动下
总是容许的——绕铰转动在另一角给出**恰沿缝法向**的相对速度（切向分量为零），满足锥条件；铰上相对速度为零。
所以 min over 全部铰机构 ≥ α（LP），摩擦大到滑动机构都劣于铰机构时取等；摩擦小时 LP 取到滑动机构，α 严格更小；
摩擦再小，自重下就不平衡（infeasible）。

厚拱（r_out = 1.5）无论几块都**没有**四铰机构：枚举为空、LP 在 μ ≥ 1 下报 unbounded（直线索在环内、基座摩擦够传 45° 的推力）、
μ = 0.7 下由基座滑动控制——两条独立的路说的是同一件几何事实。第一版用过刚性竖直台肩之间的平拱，同样自锁
（关联极限分析对楔住体系的已知高估）。
"""

from __future__ import annotations

import itertools
import math

import pytest

from eab.limit import LimitContact, wrench
from eab.limit_multi import BodyContact, LimitBody, check_duality_multi, limit_load_multi, mechanism_is_admissible_multi

O = (0.0, 0.0)
RHO = 10.0
R_IN = 1.0


def _pt(r, th):
    return (r * math.cos(th), r * math.sin(th))


def _area_centroid(P):
    a = cx = cy = 0.0
    for i in range(len(P)):
        (x0, y0), (x1, y1) = P[i], P[(i + 1) % len(P)]
        w = x0 * y1 - x1 * y0
        a += w
        cx += (x0 + x1) * w
        cy += (y0 + y1) * w
    a *= 0.5
    return a, (cx / (6 * a), cy / (6 * a))


class Arch:
    def __init__(self, n: int, r_out: float = 1.15):
        self.n = n
        self.r_out = r_out
        self.crown = (0.0, r_out)
        self.ang = [math.pi * j / n for j in range(n + 1)]
        self.blocks = [[_pt(R_IN, self.ang[i]), _pt(r_out, self.ang[i]), _pt(r_out, self.ang[i + 1]), _pt(R_IN, self.ang[i + 1])]
                       for i in range(n)]
        self.weights = [RHO * _area_centroid(P)[0] for P in self.blocks]
        self.cents = [_area_centroid(P)[1] for P in self.blocks]
        self.crown_body = n // 2

    def joint(self, j: int):
        """缝 j：(角点 [内弧, 外弧], 法向 b → a, a 体, b 体)。缝在体 j−1（θ 小的一侧）与体 j 之间；两端是基座。"""
        th = self.ang[j]
        corners = [_pt(R_IN, th), _pt(self.r_out, th)]
        if j == 0:
            return corners, (0.0, 1.0), 0, None
        if j == self.n:
            return corners, (0.0, 1.0), self.n - 1, None
        return corners, (-math.sin(th), math.cos(th)), j, j - 1

    def problem(self, mu: float):
        bodies = [LimitBody(wrench((0.0, -w), c, O, 2), [0.0] * 3) for w, c in zip(self.weights, self.cents)]
        bodies[self.crown_body].live = wrench((0.0, -1.0), self.crown, O, 2)
        bcs = []
        for j in range(self.n + 1):
            corners, nrm, a, b = self.joint(j)
            bcs += [BodyContact(LimitContact(p, nrm, mu), a, b) for p in corners]
        return bodies, bcs

    def hinge_mechanisms(self):
        """枚举：4 条铰缝 j1 < j2 < j3 < j4、各自的角点、朝向。链：体 j1..j2−1 绕固定铰 p1 转（ω = ±1），体 j2..j3−1 自由
        (v, ω)，体 j3..j4−1 绕固定铰 p4 转（ω_R）；其余体不动。p2、p3 处速度相容。返回 [(α 上限, 各体旋量, 铰位)]，
        只收 α > 0 且各铰缝另一角张开的。"""
        out = []
        n = self.n
        for js in itertools.combinations(range(n + 1), 4):
            for cs in itertools.product((0, 1), repeat=4):
                p = [self.joint(j)[0][c] for j, c in zip(js, cs)]
                pA, pB, pC, pD = p
                M = [[1.0, 0.0, -pB[1], 0.0], [0.0, 1.0, pB[0], 0.0],
                     [1.0, 0.0, -pC[1], (pC[1] - pD[1])], [0.0, 1.0, pC[0], -(pC[0] - pD[0])]]
                rhs = [-(pB[1] - pA[1]), (pB[0] - pA[0]), 0.0, 0.0]
                sol = _solve4(M, rhs)
                if sol is None:
                    continue
                for sgn in (1.0, -1.0):
                    vKx, vKy, wK, wR = (sgn * v for v in sol)
                    links = [(pA[1] * sgn, -pA[0] * sgn, sgn), (vKx, vKy, wK), (pD[1] * wR, -pD[0] * wR, wR)]
                    tw = [(0.0, 0.0, 0.0)] * n
                    for i in range(js[0], js[1]):
                        tw[i] = links[0]
                    for i in range(js[1], js[2]):
                        tw[i] = links[1]
                    for i in range(js[2], js[3]):
                        tw[i] = links[2]

                    def vel(t, q):
                        return (t[0] - t[2] * q[1], t[1] + t[2] * q[0])
                    ok = True
                    for j in range(n + 1):
                        corners, nrm, a, b = self.joint(j)
                        for ci, q in enumerate(corners):
                            va = vel(tw[a], q)
                            vb = vel(tw[b], q) if b is not None else (0.0, 0.0)
                            rel = (va[0] - vb[0]) * nrm[0] + (va[1] - vb[1]) * nrm[1]
                            if j in js and ci == cs[js.index(j)]:
                                continue                                    # 铰本身：相对速度为零（相容性保证）
                            if rel < -1e-12:
                                ok = False
                    if not ok:
                        continue
                    dead_power = sum(-w * vel(t, c)[1] for w, t, c in zip(self.weights, tw, self.cents))
                    live_power = -vel(tw[self.crown_body], self.crown)[1]
                    if live_power <= 1e-12:
                        continue
                    alpha = -dead_power / live_power
                    if alpha > 0.0:
                        out.append((alpha, [list(t) for t in tw], (js, cs, sgn)))
        return sorted(out)


def _solve4(M, rhs):
    A = [list(row) + [r] for row, r in zip(M, rhs)]
    n = 4
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(A[r][c]))
        if abs(A[piv][c]) < 1e-12:
            return None
        A[c], A[piv] = A[piv], A[c]
        for r in range(n):
            if r != c:
                f = A[r][c] / A[c][c]
                for k in range(c, n + 1):
                    A[r][k] -= f * A[c][k]
    return [A[i][n] / A[i][i] for i in range(n)]


ARCH5 = Arch(5)
ARCH7 = Arch(7)


def test_hinge_enumeration_is_not_vacuous():
    mechs = ARCH5.hinge_mechanisms()
    assert len(mechs) >= 2 and mechs[0][0] > 0.0, len(mechs)


@pytest.mark.parametrize("n", [3, 5, 7])
def test_a_thick_ring_has_no_hinge_mechanism_and_unbounded_capacity_at_high_friction(n):
    """厚拱 t/R = 0.4：拱顶点荷载的直线索（拱顶外弧 → 基座外角）离圆心最近 1.5/√2 = 1.06 > 1，整个落在环内——
    枚举为空（任何让拱顶下降的转动都贯入），LP 在 μ = 2 下报 unbounded（推力线 45°，基座摩擦够）；μ = 0.4 时由滑动控制、有限
    （三块的拱在 μ = 0.7 就已无界：拱心石太胖，连滑动机构都没有）。"""
    thick = Arch(n, 1.5)
    assert thick.hinge_mechanisms() == []
    assert limit_load_multi(*thick.problem(2.0), dim=2).status == "unbounded"
    r = limit_load_multi(*thick.problem(0.4), dim=2)
    assert r.status == "optimal" and r.alpha < 1e3


@pytest.mark.parametrize("arch", [ARCH5, ARCH7], ids=["N5", "N7"])
@pytest.mark.parametrize("mu", [2.0, 5.0])
def test_high_friction_arch_collapses_by_the_best_hinge_mechanism(arch, mu):
    """摩擦大：滑动机构劣于铰机构，LP 的 α 恰等于全部铰机构上限的最小者；该机构对 LP 的接触容许，且上限 = α。"""
    bodies, bcs = arch.problem(mu)
    r = limit_load_multi(bodies, bcs, dim=2)
    best, twists, hinges = arch.hinge_mechanisms()[0]
    assert r.status == "optimal" and r.alpha == pytest.approx(best, rel=1e-9), (r.alpha, best, hinges)
    assert mechanism_is_admissible_multi(twists, bcs, dim=2)
    assert check_duality_multi(r, bodies, bcs, dim=2)["ok"]


@pytest.mark.parametrize("mu", [0.4, 0.7, 1.0])
def test_any_friction_arch_is_bounded_above_by_every_hinge_mechanism(mu):
    """上限定理：LP 的 α ≤ 每一个容许铰机构的上限。"""
    bodies, bcs = ARCH5.problem(mu)
    r = limit_load_multi(bodies, bcs, dim=2)
    assert r.status == "optimal", r.status
    for alpha_k, twists, _ in ARCH5.hinge_mechanisms():
        assert r.alpha <= alpha_k * (1 + 1e-9)
        assert mechanism_is_admissible_multi(twists, bcs, dim=2)


def test_capacity_is_monotone_in_friction_and_saturates_at_the_hinge_bound():
    """摩擦小时 LP 找到滑动机构（α 严格小于最佳铰上限），摩擦更小时自重下就不平衡；α 随 μ 单调不减，到铰机构主导为止。"""
    best = ARCH5.hinge_mechanisms()[0][0]
    statuses, alphas = [], []
    for mu in (0.1, 0.4, 0.7, 1.0, 2.0):
        bodies, bcs = ARCH5.problem(mu)
        r = limit_load_multi(bodies, bcs, dim=2)
        statuses.append(r.status)
        alphas.append(r.alpha)
    assert statuses[0] == "infeasible" and all(s == "optimal" for s in statuses[1:]), statuses
    assert alphas[1] < best * (1 - 1e-6)
    assert all(a0 <= a1 * (1 + 1e-12) for a0, a1 in zip(alphas[1:], alphas[2:]))
    assert alphas[-1] == pytest.approx(best, rel=1e-9)


def test_arch_thrust_line_stays_inside_every_joint():
    """下限定理的几何读法：每条缝上两个角点接触力的合力作用点（推力线）落在缝段之内。"""
    bodies, bcs = ARCH5.problem(2.0)
    r = limit_load_multi(bodies, bcs, dim=2)
    for j in range(ARCH5.n + 1):
        i0, i1 = 2 * j, 2 * j + 1
        n = bcs[i0].contact.normal
        n0, n1 = (r.contact_forces[i][0] * n[0] + r.contact_forces[i][1] * n[1] for i in (i0, i1))
        assert n0 >= -1e-12 and n1 >= -1e-12 and n0 + n1 > 0.0
        assert 0.0 <= n1 / (n0 + n1) <= 1.0
