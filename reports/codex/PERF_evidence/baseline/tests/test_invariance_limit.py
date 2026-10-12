"""纪律 F · 刚体运动与单位不变性元门（L3 极限分析）。

G6（reports/g6_20260924.md）的 critical 19 / 0 与 major 1 / 2 是同一根因：LP 与极限分析里的阈值是绝对的，
而旧门从不平移、从不旋转、从不放到工程坐标上（块体永远在原点附近、轴对齐、荷载与黏聚同比放大）。
本文件把"结果必须按应有方式随刚体运动与单位变换"钉成门，作为那批缺陷的统一复现。

**变换**（参考问题在参考单位 m、N 里给出，块体尺寸 ~2）：
  · 刚体运动：点 p → R·p + t（R 为固定种子的非轴对齐转动，t 的模 ∈ {0, 1e3, 1e5}，单位同参考单位——
    "块体放在离坐标原点 1 km / 100 km 处"），法向、切向基架、力一起转；
  · 单位：长度 ×s（s ∈ {1e-3, 1, 1e3}：km / m / mm），力 ×f（f ∈ {1e-2, 1, 1e4}）⇒ 黏聚强度 ×f/s²、面积 ×s²；
    恒载、活荷载、黏聚力一致缩放，所以荷载因子 α 是**不变量**；
  · 力矩参考点两种：调用方用默认原点（None ⇒ 坐标原点，力臂 ~|t|·s，G6 critical 0 的调用路径），
    或调用方带一个随块体移动的局部参考点。
**应有的变换**：状态不变；α 不变；唯一原问题解时活动集与接触合力（×f·R）不变；
破坏机构按旋量规律变回参考系后，仍是**参考问题**的最优对偶（容许、驱动 = 1、上限 = α）；
`check_duality` 在变换后的问题上自己也必须过。

**oracle（纪律 A）**：
  · 解析闭式：二维滑动 μW、倾覆 W·w/(2h)、纯黏聚 ΣcA；三维平底块沿切向基架第一条棱推 μW + ΣcA
    （棱与推力对齐 ⇒ 内接棱锥在该方向精确）；
  · 其余位形（楔形槽、混合）用蜕变关系：变换前后互比，参考值本身另用对偶三项（本文件自算功率）核对；
  · 机构核对用本文件自己的刚体速度场 v(p) = v_o + ω × (p − o) 与自己写的锥棱/黏聚方向（锥棱约定
    g_j = n + μ(cos a_j t₁ + sin a_j t₂)、t₂ = n × t₁，与库的约定相同——这是**被测契约**，不是共用实现；
    k 取偶数，t₂ 取反时棱集合不变）；旋量与平移公式也是本文件自写，不调用 `eab.limit.wrench`。
**共用声明**：参考值 α_ref 也来自 `limit_load`；若它在参考问题上就错、且错得与变换无关，蜕变关系抓不到——
所以参考值在有闭式的位形上先对闭式，其余位形先过本文件自算的对偶三项。

**三维的切向基架**：库默认的棱扇朝向由全局基架 `_tangents(n)` 决定，**不随转动协变**（球面上不存在处处连续的
切向场），整体转动模型时 α 只能保证落在内接棱锥夹逼 [cos(π/k), 1]·精确值 内——第二个门就钉这个诚实界。
第一个门的三维位形给每个接触显式的 `LimitContact.tangent`（随模型一起转），因而要求 α 严格不变。

**容差**：变换后坐标的量级 C 与块体尺寸 L 之比最大 5e4（|t| = 1e5 时），输入本身就只有 eps·C/L ~ 1e-11 的相对精度；
α 的门取 rel 1e-9 + 1e-12·C/L（最坏 5e-8），比任何真缺陷（α = 0、∞、抛错、差 1e-3 以上）小几个量级。
"""

from __future__ import annotations

import random
from functools import lru_cache
from math import cos, pi, sin, sqrt

import pytest

from eab.limit import LimitContact, check_duality, limit_load

EPS = 2.220446049250313e-16


# ------------------------------------------------------------------ 本文件自带的小线代（不调用 eab）

def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _norm(a):
    return sqrt(_dot(a, a))


def _unit(a):
    n = _norm(a)
    return tuple(x / n for x in a)


def _matvec(R, v):
    return tuple(sum(R[i][j] * v[j] for j in range(len(v))) for i in range(len(R)))


def _matTvec(R, v):
    return tuple(sum(R[j][i] * v[j] for j in range(len(v))) for i in range(len(R)))


def _rot3(seed):
    """固定种子的随机转动（单位四元数），非轴对齐。"""
    rng = random.Random(seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    n = sqrt(sum(x * x for x in q))
    w, x, y, z = (v / n for v in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def _rot2(theta):
    return ((cos(theta), -sin(theta)), (sin(theta), cos(theta)))


ROT = {2: {"I": ((1.0, 0.0), (0.0, 1.0)), "R": _rot2(0.7137)},
       3: {"I": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), "R": _rot3(20260924)}}
TDIR = {2: _unit((0.6, -0.8)), 3: _unit((0.48, 0.64, -0.6))}


def _w(force, point, origin, dim):
    """旋量（力 + 对 origin 的力矩），本文件自写。"""
    r = tuple(point[i] - origin[i] for i in range(dim))
    if dim == 2:
        return [force[0], force[1], r[0] * force[1] - r[1] * force[0]]
    return list(force) + list(_cross(r, force))


def _vel(y, origin, p, dim):
    """刚体速度场：旋量 y = (v_o, ω) 在点 p 的速度。"""
    if dim == 2:
        vx, vy, om = y
        r = (p[0] - origin[0], p[1] - origin[1])
        return (vx - om * r[1], vy + om * r[0])
    v, om = y[:3], y[3:]
    r = tuple(p[i] - origin[i] for i in range(3))
    wr = _cross(om, r)
    return tuple(v[i] + wr[i] for i in range(3))


# ------------------------------------------------------------------ 参考位形

class Case:
    def __init__(self, name, dim, contacts, dead, live, k=8, closed=None, unique_primal=False):
        self.name, self.dim, self.contacts, self.dead, self.live = name, dim, contacts, dead, live
        self.k, self.closed, self.unique_primal = k, closed, unique_primal

    @property
    def size(self):
        pts = [c["p"] for c in self.contacts]
        return max(max(abs(a[i] - b[i]) for i in range(self.dim)) for a in pts for b in pts)


def _c(p, n, mu, coh=0.0, area=0.0, label=None, tangent=None):
    return dict(p=p, n=_unit(n), mu=mu, coh=coh, area=area, label=label, tangent=tangent)


def _cases():
    out = []
    # 二维方块（W=10、宽 2、高 3），接触 L/R，荷载作用在块顶：α = min(μW, W·w/(2h))
    for mu, name in ((0.2, "2d_slide"), (0.8, "2d_topple")):
        cts = [_c((-1.0, 0.0), (0.0, 1.0), mu, label=("L",)), _c((1.0, 0.0), (0.0, 1.0), mu, label=("R",))]
        out.append(Case(name, 2, cts, [((0.0, -10.0), (0.0, 1.5))], [((1.0, 0.0), (0.0, 3.0))],
                        closed=min(mu * 10.0, 10.0 / 3.0), unique_primal=True))
    # 二维纯黏聚、两接触不等 cA（3 与 2），荷载在基面（无倾覆）：α = ΣcA = 5
    cts = [_c((-1.0, 0.0), (0.0, 1.0), 0.0, coh=3.0, area=1.0, label=("L",)),
           _c((1.5, 0.0), (0.0, 1.0), 0.0, coh=1.0, area=2.0, label=("R",))]
    out.append(Case("2d_cohesion", 2, cts, [((0.0, -10.0), (0.2, 0.0))], [((1.0, 0.0), (0.0, 0.0))],
                    closed=5.0))
    # 二维混合：三个接触，中间带黏聚，荷载偏高——无闭式，蜕变 + 自算对偶
    cts = [_c((-1.0, 0.0), (0.0, 1.0), 0.3, label=("L",)),
           _c((0.2, 0.0), (0.1, 1.0), 0.4, coh=2.0, area=0.5, label=("M",)),
           _c((1.3, 0.1), (-0.05, 1.0), 0.3, label=("R",))]
    out.append(Case("2d_mixed", 2, cts, [((0.0, -10.0), (0.1, 1.2))], [((1.0, 0.0), (0.0, 1.7))]))

    # 三维平底块：不对称四边形底（不关于形心对称，纪律 E），法向 +z，推力沿 θ=0.3 且与切向基架第一条棱对齐
    th = 0.3
    u = (cos(th), sin(th), 0.0)
    quad = [(-1.0, -0.6, 0.0), (1.2, -0.5, 0.0), (0.9, 0.7, 0.0), (-0.8, 0.6, 0.0)]
    cts = [_c(p, (0.0, 0.0, 1.0), 0.5, label=(f"c{i}",), tangent=u) for i, p in enumerate(quad)]
    out.append(Case("3d_flat_friction", 3, cts, [((0.0, 0.0, -10.0), (0.1, 0.05, 0.7))],
                    [(u, (0.1, 0.05, 0.0))], closed=5.0))
    # 黏聚不等（c·A = 1, 2, 1.5, 0.5）：全部抗剪同时沿 u 发挥的合力作用线过 q = (μW·g + Σ cA_i p_i)/(μW + ΣcA)
    # （g = 恒载作用点的水平投影；ΣN_i p_i = W·g 可由四角法向力取到），推力作用在 q、基面高度 ⇒ 无扭转、无倾覆，
    # α = μW + ΣcA 精确。推力点不在 q 时扭转平衡限制黏聚发挥，α 更小（2026-09-24 初稿即因此把闭式写错）。
    cA = [(1.0, 1.0), (4.0, 0.5), (1.5, 1.0), (0.25, 2.0)]
    mu_c, W_c, g_c = 0.2, 10.0, (0.1, 0.05)
    tot = mu_c * W_c + sum(c * a for c, a in cA)
    q = tuple((mu_c * W_c * g_c[i] + sum(c * a * p[i] for p, (c, a) in zip(quad, cA))) / tot for i in range(2))
    cts = [_c(p, (0.0, 0.0, 1.0), mu_c, coh=c, area=a, label=(f"c{i}",), tangent=u)
           for i, (p, (c, a)) in enumerate(zip(quad, cA))]
    out.append(Case("3d_flat_cohesion", 3, cts, [((0.0, 0.0, -W_c), (g_c[0], g_c[1], 0.7))],
                    [(u, (q[0], q[1], 0.0))], closed=tot))
    # 三维楔形槽：两斜面（法向在 x-z 面内，倾角 35°/50°，非对称），3 + 2 个接触，沿槽轴 y 推；
    # 切向基架取 ŷ（槽轴），无闭式（非对称楔），蜕变 + 自算对偶
    b1, b2 = 35.0 * pi / 180.0, 50.0 * pi / 180.0
    n1, n2 = (sin(b1), 0.0, cos(b1)), (-sin(b2), 0.0, cos(b2))
    left = [(-0.8, y, 0.8 * sin(b1) / cos(b1)) for y in (-1.0, 0.3, 1.2)]
    right = [(0.6, y, 0.6 * sin(b2) / cos(b2)) for y in (-0.7, 0.9)]
    ey = (0.0, 1.0, 0.0)
    cts = ([_c(p, n1, 0.35, label=(f"l{i}",), tangent=ey) for i, p in enumerate(left)]
           + [_c(p, n2, 0.5, label=(f"r{i}",), tangent=ey) for i, p in enumerate(right)])
    out.append(Case("3d_wedge", 3, cts, [((0.0, 0.0, -10.0), (-0.05, 0.1, 1.0))], [(ey, (-0.05, 0.1, 0.8))]))
    cts = ([_c(p, n1, 0.35, coh=c, area=0.4, label=(f"l{i}",), tangent=ey)
            for i, (p, c) in enumerate(zip(left, (2.0, 0.0, 5.0)))]
           + [_c(p, n2, 0.5, coh=c, area=0.3, label=(f"r{i}",), tangent=ey)
              for i, (p, c) in enumerate(zip(right, (0.0, 3.0)))])
    out.append(Case("3d_wedge_cohesion", 3, cts, [((0.0, 0.0, -10.0), (-0.05, 0.1, 1.0))],
                    [(ey, (-0.05, 0.1, 0.8))]))
    return {c.name: c for c in out}


CASES = _cases()


# ------------------------------------------------------------------ 变换与求解

def _transform(case, rot, tmag, s, f, *, keep_tangent=True):
    dim = case.dim
    R = ROT[dim][rot]
    t = tuple(tmag * v for v in TDIR[dim])

    def P(p):
        q = _matvec(R, p)
        return tuple(s * (q[i] + t[i]) for i in range(dim))

    cts = []
    for c in case.contacts:
        tan = c["tangent"]
        cts.append(LimitContact(P(c["p"]), _matvec(R, c["n"]), c["mu"], cohesion=c["coh"] * f / (s * s),
                                area=c["area"] * s * s, label=c["label"],
                                tangent=(_matvec(R, tan) if (tan is not None and keep_tangent) else None)))
    dead = [(tuple(f * v for v in _matvec(R, F)), P(p)) for F, p in case.dead]
    live = [(tuple(f * v for v in _matvec(R, F)), P(p)) for F, p in case.live]
    return cts, dead, live, P, R


def _wrench_sum(loads, origin, dim):
    tot = [0.0] * (3 if dim == 2 else 6)
    for F, p in loads:
        tot = [a + b for a, b in zip(tot, _w(F, p, origin, dim))]
    return tot


def _solve(cts, dead, live, dim, k, origin):
    o = origin if origin is not None else (0.0,) * dim
    W_dead, W_live = _wrench_sum(dead, o, dim), _wrench_sum(live, o, dim)
    r = limit_load(cts, W_dead, W_live, dim=dim, k=k, origin=origin)
    return r, W_dead, W_live


@lru_cache(maxsize=None)
def _reference(name):
    case = CASES[name]
    cts, dead, live, _, _ = _transform(case, "I", 0.0, 1.0, 1.0)
    r, Wd, Wl = _solve(cts, dead, live, case.dim, case.k, None)
    return r


# ------------------------------------------------------------------ 本文件自算的对偶核对

def _generators(n, mu, tangent, dim, k):
    if dim == 2:
        t = (-n[1], n[0])
        return [tuple(n[i] + mu * t[i] for i in range(2)), tuple(n[i] - mu * t[i] for i in range(2))], [t, (-t[0], -t[1])]
    t1 = _unit(tuple(tangent[i] - _dot(tangent, n) * n[i] for i in range(3)))
    t2 = _cross(n, t1)
    dirs = [tuple(cos(2 * pi * j / k) * t1[i] + sin(2 * pi * j / k) * t2[i] for i in range(3)) for j in range(k)]
    return [tuple(n[i] + mu * d[i] for i in range(3)) for d in dirs], dirs


def _dual_residuals(case, y, yr, alpha):
    """在**参考问题**上核对一个 (y, y_r) 是否最优对偶：返回 (最差相对功率, 驱动, 上限)。"""
    dim, k = case.dim, case.k
    o = (0.0,) * dim
    worst = 0.0
    row = 0
    for c in case.contacts:
        gens, dirs = _generators(c["n"], c["mu"], c["tangent"], dim, k)
        v = _vel(y, o, c["p"], dim)
        # 舍入尺度取 |v_o| + |ω|·|r|（v(p) 的计算量级），不取 |v(p)|：支点处 v(p) 本身就是舍入噪声
        om = abs(y[2]) if dim == 2 else _norm(y[3:])
        scale = _norm(y[:dim]) + om * _norm(c["p"]) + 1e-300
        for g in gens:
            worst = min(worst, _dot(v, g) / (scale * _norm(g)))
        if c["coh"] > 0.0 and c["area"] > 0.0:
            cA = c["coh"] * c["area"]
            for d in dirs:
                p = cA * _dot(v, d) + yr[row]
                worst = min(worst, p / (cA * scale + abs(yr[row]) + 1e-300))
            worst = min(worst, yr[row] / (cA * scale + abs(yr[row]) + 1e-300))
            row += 1
    drive = sum(_dot(_vel(y, o, p, dim), F) for F, p in case.live)
    upper = -sum(_dot(_vel(y, o, p, dim), F) for F, p in case.dead) + sum(yr)
    return worst, drive, upper


def _map_back(case, y, origin_used, s, f, R, P):
    """变换后问题的机构（关于 origin_used 的旋量）→ 参考系里关于参考原点的旋量。
    幂守恒：y_ref = (f·Rᵀ v_q, f·s·Rᵀ ω)，q = 参考原点的像。"""
    dim = case.dim
    q = P((0.0,) * dim)
    vq = _vel(y, origin_used, q, dim)
    if dim == 2:
        return [f * v for v in _matTvec(R, vq)] + [f * s * y[2]]
    return [f * v for v in _matTvec(R, vq)] + [f * s * v for v in _matTvec(R, tuple(y[3:]))]


def _rtol(case, tmag):
    return 1e-9 + 1e-12 * (tmag + case.size) / case.size


# ------------------------------------------------------------------ 门 1：显式基架，全部量严格不变

TMAGS = [0.0, 1e3, 1e5]
SCALES = [1e-3, 1.0, 1e3]
FORCES = [1e-2, 1.0, 1e4]


@pytest.mark.parametrize("f", FORCES)
@pytest.mark.parametrize("s", SCALES)
@pytest.mark.parametrize("tmag", TMAGS)
@pytest.mark.parametrize("rot", ["I", "R"])
@pytest.mark.parametrize("name", list(CASES))
def test_limit_load_is_invariant_under_rigid_motion_and_units(name, rot, tmag, s, f):
    case = CASES[name]
    ref = _reference(name)
    assert ref.status == "optimal", ref.status
    if case.closed is not None:
        assert ref.alpha == pytest.approx(case.closed, rel=1e-12, abs=1e-12)
    w0, d0, u0 = _dual_residuals(case, ref.mechanism, ref.row_duals, ref.alpha)
    assert w0 > -1e-12 and abs(d0 - 1.0) < 1e-12 and abs(u0 - ref.alpha) < 1e-12 * max(1.0, ref.alpha)

    cts, dead, live, P, R = _transform(case, rot, tmag, s, f)
    tol = _rtol(case, tmag)
    local = P((0.0,) * case.dim)
    for origin in (None, local):
        r, Wd, Wl = _solve(cts, dead, live, case.dim, case.k, origin)
        tag = (name, rot, tmag, s, f, "default" if origin is None else "local")
        assert r.status == "optimal", (tag, r.status, r.alpha)
        assert r.alpha == pytest.approx(ref.alpha, rel=tol), (tag, r.alpha, ref.alpha)
        # 变换后问题上，库自己的对偶自校验必须过（相对判据）
        d = check_duality(r, cts, Wd, Wl, dim=case.dim, k=case.k, origin=origin)
        assert d["admissible"], (tag, d)
        assert d["duality_gap_rel"] < 1e-7 and d["complementarity"] < 1e-7, (tag, d)
        # 机构按旋量规律变回参考系后，仍是参考问题的最优对偶（本文件自算）
        o_used = origin if origin is not None else (0.0,) * case.dim
        y_ref = _map_back(case, r.mechanism, o_used, s, f, R, P)
        worst, drive, upper = _dual_residuals(case, y_ref, r.row_duals, r.alpha)
        assert worst > -1e-7, (tag, worst)
        assert abs(drive - 1.0) < 1e-7, (tag, drive)
        assert abs(upper - ref.alpha) < 1e-7 * max(1.0, ref.alpha), (tag, upper, ref.alpha)
        if case.unique_primal:
            assert r.active == ref.active, (tag, r.active, ref.active)
            for F, F0 in zip(r.contact_forces, ref.contact_forces):
                expect = tuple(f * v for v in _matvec(R, F0))
                assert _norm(tuple(a - b for a, b in zip(F, expect))) <= 1e-7 * f * 10.0, (tag, F, expect)


# ------------------------------------------------------------------ 门 2：默认基架，转动后落在内接棱锥夹逼里

FLAT = ["3d_flat_friction", "3d_flat_cohesion"]


@pytest.mark.parametrize("k", [5, 8])
@pytest.mark.parametrize("f", [1e-2, 1e4])
@pytest.mark.parametrize("s", SCALES)
@pytest.mark.parametrize("tmag", TMAGS)
@pytest.mark.parametrize("name", FLAT)
def test_default_frame_rotation_stays_inside_the_inscribed_cone_bracket(name, tmag, s, f, k):
    """库默认基架不随转动协变：α 只保证 ∈ [cos(π/k), 1]·(μW + ΣcA)（纯滑动的径向夹逼，与基架无关）。"""
    case = CASES[name]
    full = case.closed
    cts, dead, live, P, R = _transform(case, "R", tmag, s, f, keep_tangent=False)
    for origin in (None, P((0.0, 0.0, 0.0))):
        r, Wd, Wl = _solve(cts, dead, live, 3, k, origin)
        tag = (name, tmag, s, f, k, origin is None)
        assert r.status == "optimal", (tag, r.status, r.alpha)
        tol = _rtol(case, tmag)
        assert cos(pi / k) * full * (1 - tol) <= r.alpha <= full * (1 + tol), (tag, r.alpha, full)
        d = check_duality(r, cts, Wd, Wl, dim=3, k=k, origin=origin)
        assert d["admissible"] and d["duality_gap_rel"] < 1e-7, (tag, d)


# ------------------------------------------------------------------ 门 3：只放大活荷载，α 反比缩放（G6 critical 19）

@pytest.mark.parametrize("live_scale", [1e-6, 1e9, 1e12])
@pytest.mark.parametrize("name", list(CASES))
def test_live_load_magnitude_scales_alpha_inversely(name, live_scale):
    """活荷载 ×λ ⇒ α ×1/λ。G6：max|W_live| > 2^33 时 α 列永远进不了基，报 optimal、α = 0。"""
    case = CASES[name]
    ref = _reference(name)
    cts, dead, live, P, R = _transform(case, "R", 1e3, 1.0, 1.0)
    live = [(tuple(live_scale * v for v in F), p) for F, p in live]
    for origin in (None, P((0.0,) * case.dim)):
        r, Wd, Wl = _solve(cts, dead, live, case.dim, case.k, origin)
        tag = (name, live_scale, origin is None)
        assert r.status == "optimal", (tag, r.status)
        assert r.alpha * live_scale == pytest.approx(ref.alpha, rel=_rtol(case, 1e3)), (tag, r.alpha)
        d = check_duality(r, cts, Wd, Wl, dim=case.dim, k=case.k, origin=origin)
        assert d["admissible"] and d["duality_gap_rel"] < 1e-7, (tag, d)


def test_the_grid_really_moves_the_block_far_and_off_axis():
    """格子自证（纪律 B）：转动非轴对齐、平移到 1e5、坐标/尺寸比达到 ~5e4。"""
    R = ROT[3]["R"]
    assert min(abs(R[i][j]) for i in range(3) for j in range(3)) > 0.05
    case = CASES["3d_wedge_cohesion"]
    cts, *_ = _transform(case, "R", 1e5, 1e3, 1.0)
    C = max(abs(v) for c in cts for v in c.point)
    assert C > 5e7 and C / (case.size * 1e3) > 2e4
    assert len({c.name for c in CASES.values()}) == 8
