"""M0.2 返修二（2026-09-27）的门：**求解器报出的每一种状态都带证书，判据里没有与问题无关的绝对量。**

复核者对 43d1e50 的结论（一条 critical、三条 major）逐条对应这里的门：
  · critical：舍入噪声线 ν ∝ κ(B) 在病态但合理的基上盖过真实约化成本——N-mm-MPa 单位的大岩块静默 infeasible、
    不变性格子 α 偏低 67%。→ `test_rock_block_in_n_mm_mpa_units_matches_the_closed_form`、
    `test_accuracy_against_the_exact_rational_optimum`；
  · major：可分辨性上限"α ≤ 1e10·α_nat"在恒载 ≥ 1e6 时漏掉舍入驱动的 α = 5.4e15。
    → `test_rounding_driven_load_factor_is_not_certified_at_any_dead_load`；
  · major：LP 层喂旧写法（c·A 乘进列、力矩关于全局原点）时静默给错，0/48。
    → `test_old_badly_scaled_limit_formulation_is_correct_or_loud`；
  · minor：`_norm` 平方溢出。→ `test_extreme_load_magnitudes_do_not_overflow`；
  · 新增契约：INFEASIBLE 必带经核验的 Farkas 证书。→ 前三个门。

oracle 与被测代码不共用原语（纪律 A）：精确 LP（`_exact_max`）只用 Fraction、自带 Bland 两阶段，不碰 lp.py；
极限分析的真值用闭式。唯一例外是精度门用 `_build_columns` 造同一个 LP——它核验的是**求解器**在给定 LP 上的精度，
不是建模。
"""

import random
from fractions import Fraction
from math import atan, cos, pi, sin, sqrt

import pytest

import eab.lp as lp
from eab.limit import LimitContact, _build_columns, _shift_wrench, limit_load, wrench
from eab.lp import INFEASIBLE, OPTIMAL, maximize, solve


# ---------------------------------------------------------------- 精确有理数 LP（独立 oracle）

def _exact_max(A, b, c):
    """max cᵀx s.t. Ax = b, x ≥ 0，Fraction 精确、Bland 两阶段。返回 (status, obj)。只用 Fraction，不共用 lp.py。"""
    m, n = len(A), len(c)
    A = [[Fraction(v) for v in row] for row in A]
    b = [Fraction(v) for v in b]
    c = [Fraction(v) for v in c]
    for i in range(m):
        if b[i] < 0:
            A[i] = [-v for v in A[i]]
            b[i] = -b[i]
    N = n + m
    T = [A[i] + [Fraction(int(k == i)) for k in range(m)] + [b[i]] for i in range(m)]
    basis = list(range(n, N))

    def run(cost, allowed):
        while True:
            cb = [cost[basis[i]] for i in range(m)]
            enter = -1
            for j in allowed:
                if j in basis:
                    continue
                if cost[j] - sum(cb[i] * T[i][j] for i in range(m)) < 0:
                    enter = j
                    break
            if enter < 0:
                return "opt"
            best, leave = None, -1
            for i in range(m):
                if T[i][enter] > 0:
                    rt = T[i][-1] / T[i][enter]
                    if best is None or rt < best or (rt == best and basis[i] < basis[leave]):
                        best, leave = rt, i
            if leave < 0:
                return "unb"
            p = T[leave][enter]
            T[leave] = [v / p for v in T[leave]]
            for i in range(m):
                if i != leave and T[i][enter] != 0:
                    f = T[i][enter]
                    T[i] = [a - f * bb for a, bb in zip(T[i], T[leave])]
            basis[leave] = enter

    run([Fraction(0)] * n + [Fraction(1)] * m, list(range(N)))
    if sum(T[i][-1] for i in range(m) if basis[i] >= n) != 0:
        return "infeasible", None
    for i in range(m):
        if basis[i] >= n:
            for j in range(n):
                if T[i][j] != 0 and j not in basis:
                    p = T[i][j]
                    T[i] = [v / p for v in T[i]]
                    for k in range(m):
                        if k != i and T[k][j] != 0:
                            f = T[k][j]
                            T[k] = [a - f * bb for a, bb in zip(T[k], T[i])]
                    basis[i] = j
                    break
    if run([-v for v in c] + [Fraction(0)] * m, list(range(n))) == "unb":
        return "unbounded", None
    x = [Fraction(0)] * n
    for i in range(m):
        if basis[i] < n:
            x[basis[i]] = T[i][-1]
    return "optimal", sum(ci * xi for ci, xi in zip(c, x))


# ---------------------------------------------------------------- Farkas 证书

INFEASIBLE_LPS = {
    "parallel rows": ([[1.0, 1.0], [1.0, 1.0]], [1.0, 2.0], [1.0, 0.0]),
    "tiny rhs": ([[1.0], [1.0]], [1e-11, 3e-11], [1.0]),
    "tiny rhs 2^-60": ([[1.0], [1.0]], [2.0 ** -60, 3 * 2.0 ** -60], [1.0]),
    "sign": ([[1.0, 2.0, 0.5]], [-3.0], [1.0, 1.0, 1.0]),
    "badly scaled": ([[1e8, 1e8, 0.0], [1e-6, 0.0, 1e-6], [0.0, 1.0, 1.0]], [1e8, 3e-6, 1.0], [1.0, 1.0, 1.0]),
}


@pytest.mark.parametrize("name", sorted(INFEASIBLE_LPS))
def test_infeasible_status_carries_a_farkas_certificate(name):
    """INFEASIBLE 必须带 y：yᵀA_j ≤ 0（到舍入）且 yᵀb > 0——任何 x ≥ 0 都给不出 Ax = b。在 Fraction 里精确核验。"""
    A, b, c = INFEASIBLE_LPS[name]
    assert _exact_max(A, b, c)[0] == "infeasible"          # 前提：真不可行
    r = solve(A, b, c)
    assert r.status == INFEASIBLE
    y = [Fraction(v) for v in r.y]
    yb = sum(yi * Fraction(bi) for yi, bi in zip(y, b))
    assert yb > 0, (name, r.y)
    ymax = max(abs(v) for v in y)
    for j in range(len(c)):
        v = sum(y[i] * Fraction(A[i][j]) for i in range(len(A)))
        scale = sum(abs(y[i] * Fraction(A[i][j])) for i in range(len(A))) + ymax * max(abs(Fraction(A[i][j])) for i in range(len(A)))
        assert v <= Fraction(1, 10 ** 9) * scale, (name, j, float(v))
        assert v * 10 ** 6 <= yb or v <= 0, (name, j)      # 容差版证书也要远离"可行"：违约 ≪ yᵀb


def test_farkas_verifier_rejects_non_certificates():
    """`_farkas_verifies` 本身有牙：真证书过，取反、某列变正、yᵀb = 0 都不过。"""
    A = [[1.0, 1.0], [1.0, 1.0]]
    b = [1.0, 2.0]
    ybar = [1.0, 1.0]
    assert lp._farkas_verifies(A, b, [-1.0, 1.0], ybar)
    assert not lp._farkas_verifies(A, b, [1.0, -1.0], ybar)          # yᵀb < 0
    assert not lp._farkas_verifies(A, b, [0.0, 1.0], ybar)           # yᵀA_j = 1 > 0
    assert not lp._farkas_verifies(A, [1.0, 1.0], [-1.0, 1.0], ybar)  # yᵀb = 0


def test_an_unverified_infeasibility_is_never_reported(monkeypatch):
    """接线的牙：证书核验不过时 solve 必须抛错，不许报 INFEASIBLE（旧版一阶段 Σ人工 > 1e-8 就直接报）。"""
    monkeypatch.setattr(lp, "_farkas_verifies", lambda *a: False)
    with pytest.raises(RuntimeError, match="Farkas"):
        solve(*INFEASIBLE_LPS["parallel rows"])


# ---------------------------------------------------------------- LP 层：旧写法（尺度极差）要么对、要么抛

def _block(L, c, mu, off, R):
    """G6 critical-0 的块体：底面 L × 0.6L、高 0.5L，四角接触，切向基架随推力方向（α 与刚体运动无关、精确等于闭式）。"""
    hx, hy, hz = L / 2, 0.3 * L, 0.5 * L
    W = 26000.0 * (2 * hx) * (2 * hy) * hz
    A = (2 * hx) * (2 * hy) / 4
    mv = lambda v: tuple(sum(R[i][j] * v[j] for j in range(3)) for i in range(3))
    P = lambda p: tuple(a + o for a, o in zip(mv(p), off))
    u = (cos(0.3), sin(0.3), 0.0)
    cts = [LimitContact(P((sx * hx, sy * hy, 0.0)), mv((0.0, 0.0, 1.0)), mu, cohesion=c, area=A, tangent=mv(u))
           for sx in (-1, 1) for sy in (-1, 1)]
    O = (0.0, 0.0, 0.0)
    return cts, wrench(mv((0.0, 0.0, -W)), P((0.0, 0.0, 0.5 * hz)), O, 3), wrench(mv(u), P((0.0, 0.0, 0.0)), O, 3), mu * W + 4 * c * A


def _rot(seed):
    rng = random.Random(seed)
    q = [rng.gauss(0, 1) for _ in range(4)]
    n = sqrt(sum(x * x for x in q))
    w, x, y, z = (v / n for v in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def _old_formulation(cts, dead, live):
    """旧写法：黏聚列乘 c·A、上限行右端 1、力矩关于全局原点——与 limit_load 现用的写法数学等价，尺度极差。"""
    C = _build_columns(cts, (0.0, 0.0, 0.0), 3, 8)
    cols = C.cols + [live]
    ncol = len(cols) + C.n_rows
    A = [[cols[j][i] if j < len(cols) else 0.0 for j in range(ncol)] for i in range(6)]
    b = [-v for v in dead]
    for r_i in range(C.n_rows):
        row = [0.0] * ncol
        for j, rj in enumerate(C.row_of):
            if rj == r_i:
                row[j] = 1.0
        row[len(cols) + r_i] = 1.0
        A.append(row)
        b.append(1.0)
    return A, b, [0.0] * len(C.cols) + [1.0] + [0.0] * C.n_rows, len(C.cols)


OLD_GRID = [(L, c, seed, off) for L in (20.0, 200.0) for c in (1e5, 1e6, 1e7) for seed in (None, 7)
            for off in ((0.0, 0.0, 0.0), (1000.0, 2000.0, 300.0), (-3.1e4, 7.3e3, 1.2e3), (5e5, 4.2e6, 300.0))]


def test_old_badly_scaled_limit_formulation_is_correct_or_loud():
    """lp.py 的契约对任何调用方成立，不靠 limit_load 的形心平移兜底：48 个旧写法 LP，每个要么 α 对到 1e-7，
    要么抛 RuntimeError，**绝不**静默给出错的 optimal / infeasible / unbounded（43d1e50：0/48 对、静默 infeasible；
    本次返修前一版：静默 unbounded——射线核验的噪声项 1e-14·max(行尺度) 吞掉了右端项 1 的黏聚上限行）。
    另外要求原点处、不转动的 6 例全对：不能靠"一律抛错"过这道门。"""
    silent, correct = [], 0
    must = []
    for L, c, seed, off in OLD_GRID:
        R = _rot(seed) if seed is not None else ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
        cts, dead, live, full = _block(L, c, 0.6, off, R)
        A, b, cc, ia = _old_formulation(cts, dead, live)
        try:
            r = maximize(A, b, cc)
        except RuntimeError:
            continue
        ok = r.status == OPTIMAL and abs(r.x[ia] - full) <= 1e-7 * full
        correct += ok
        if not ok:
            silent.append((L, c, seed, off, r.status, r.x[ia] if r.status == OPTIMAL else None, full))
        if seed is None and off == (0.0, 0.0, 0.0):
            must.append(ok)
    assert silent == [], silent[:4]
    assert must and all(must), must


# ---------------------------------------------------------------- 可分辨性：舍入驱动的 α 在任何恒载下都不认证

@pytest.mark.parametrize("W", [1.0, 1e3, 1e6, 1e7, 1e9, 1e12])
def test_rounding_driven_load_factor_is_not_certified_at_any_dead_load(W):
    """无摩擦地面，恒载带 1 的水平分量，活荷载 θ = 3π/2（实数里竖直向下，浮点里水平分量 cos(3π/2) = −1.8e-16）。
    物理答案 infeasible（水平恒载无物可挡）；浮点 LP 给 α = 1/1.8e-16 = 5.4e15。旧判据"α ≤ 1e10·α_nat"里
    α_nat 含整个恒载，W ≥ 1e6 时漏过（43d1e50 实测 optimal 5443746451065123）。三维同理（θ = π 的"竖直"推力）。"""
    assert cos(3 * pi / 2) != 0.0
    o2 = (0.0, 0.0)
    r = limit_load([LimitContact((0.0, 0.0), (0.0, 1.0), 0.0)], wrench((1.0, -W), o2, o2, 2),
                   wrench((cos(3 * pi / 2), sin(3 * pi / 2)), o2, o2, 2), dim=2)
    assert r.status == "infeasible", (W, r.status, r.alpha)
    o3 = (0.0, 0.0, 0.0)
    r3 = limit_load([LimitContact(o3, (0.0, 0.0, 1.0), 0.0)], wrench((-1.0, 0.0, -W), o3, o3, 3),
                    wrench((sin(pi), 0.0, cos(pi)), o3, o3, 3), dim=3)
    assert r3.status == "infeasible", (W, r3.status, r3.alpha)


MU, WL = 0.5, 10.0


def _lock_case(margin, rot, t, s):
    """二维近自锁：μ = 0.5 的地面上斜向下推，离自锁角差 margin；闭式 α = μW / (cos b − μ sin b)。"""
    b = pi / 2 - atan(MU) - margin
    r2 = lambda p: (cos(rot) * p[0] - sin(rot) * p[1], sin(rot) * p[0] + cos(rot) * p[1])
    P = lambda p: tuple(s * r2(p)[i] + t[i] for i in range(2))
    n = r2((0.0, 1.0))
    cts = [LimitContact(P((x, 0.0)), n, MU) for x in (-1.0, 1.0)]
    o = (0.0, 0.0)
    return (cts, wrench(r2((0.0, -WL)), P((0.0, 0.0)), o, 2), wrench(r2((cos(b), -sin(b))), P((0.0, 0.0)), o, 2),
            MU * WL / (cos(b) - MU * sin(b)))


FRAMES = [(0.0, (0.0, 0.0), 1.0), (0.37, (3e4, -2e3), 1.0), (0.0, (0.0, 0.0), 1e3), (-1.1, (5e5, 4e6), 0.01)]


@pytest.mark.parametrize("frame", FRAMES)
@pytest.mark.parametrize("margin", [1e-3, 1e-6, 1e-8, 1e-9, 1e-10, 1e-11, 1e-13])
def test_near_self_locking_is_certified_within_its_reported_uncertainty_or_loud(margin, frame):
    """真实的大荷载因子（离自锁 margin，α ≈ 1.34/margin 量级）照常认证，且误差不超过报告的不确定度 U；
    余量小到 U > 1e-6 时抛错，不给假精度。U ≈ 4u·κ，κ ≈ 1.34/margin（09-27 实测标定）。
    余量 ≥ 1e-9 必须认证——包括 2 cm 的块体放在离原点 4000 km 处（C/L = 4e8；本次返修中途，调用方坐标系自校验
    把驱动 1 + 2⁻²³ 的点积舍入判成违约，曾对这一例抛错）。"""
    cts, dead, live, exact = _lock_case(margin, *frame)
    try:
        r = limit_load(cts, dead, live, dim=2, k=8)
    except RuntimeError as e:                               # loud：不确定度超标、自校验或基奇异，都允许
        assert margin < 1e-9, (margin, frame, str(e)[:120])
        return
    assert r.status == "optimal"
    assert r.uncertainty <= 1e-6
    assert abs(r.alpha - exact) <= (r.uncertainty + 1e-9) * exact, (margin, frame, r.alpha, exact, r.uncertainty)


# ---------------------------------------------------------------- N-mm-MPa、极端量级

def _nmm_block(Lm, c_MPa, off_m):
    """岩块用 N-mm-MPa 单位（长度 mm、力 N、黏聚 N/mm²），四角等黏聚、推力过底面形心——闭式 μW + Σc·A。"""
    s = 1000.0
    hx, hy, hz = Lm / 2 * s, 0.3 * Lm * s, 0.5 * Lm * s
    W = 26000.0 * Lm * (0.6 * Lm) * (0.5 * Lm)
    A = (2 * hx) * (2 * hy) / 4
    o = tuple(v * s for v in off_m)
    tg = (cos(0.3), sin(0.3), 0.0)
    cts = [LimitContact((o[0] + sx * hx, o[1] + sy * hy, o[2]), (0.0, 0.0, 1.0), 0.6, cohesion=c_MPa, area=A, tangent=tg)
           for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    O = (0.0, 0.0, 0.0)
    return cts, wrench((0.0, 0.0, -W), (o[0], o[1], o[2] + hz / 2), O, 3), wrench(tg, o, O, 3), 0.6 * W + 4 * c_MPa * A


@pytest.mark.parametrize("Lm", [200.0, 300.0, 1000.0])
@pytest.mark.parametrize("c_MPa", [0.05, 0.5])
@pytest.mark.parametrize("off", [(0.0, 0.0, 0.0), (3e3, 5e3, 200.0)])
def test_rock_block_in_n_mm_mpa_units_matches_the_closed_form(Lm, c_MPa, off):
    """复核者的 critical：43d1e50 上 300–1000 m 的岩块静默报 infeasible、200 m 的抛自校验错（58752a5 答对）。
    根因是噪声线 ν ∝ κ(B) 盖过真约化成本；现在最优性按"目标的相对改进量"判（`_Revised.dual_violation`）。"""
    cts, dead, live, full = _nmm_block(Lm, c_MPa, off)
    r = limit_load(cts, dead, live, dim=3, k=8)
    assert r.status == "optimal" and r.alpha == pytest.approx(full, rel=1e-9), (r.status, r.alpha, full)


@pytest.mark.parametrize("H", [1e150, 1e160, 1e200])
def test_extreme_load_magnitudes_do_not_overflow(H):
    """`_norm` 先按最大分量归一再平方：|活荷载| = 1e160 不溢出、|恒载| = 1e-200 不下溢（43d1e50 抛"自然荷载尺度 0"）。"""
    cts = [LimitContact((-1.0, 0.0), (0.0, 1.0), 0.2), LimitContact((1.0, 0.0), (0.0, 1.0), 0.2)]
    o = (0.0, 0.0)
    r = limit_load(cts, wrench((0.0, -10.0), (0.0, 1.5), o, 2), wrench((H, 0.0), (0.0, 3.0), o, 2), dim=2)
    assert r.status == "optimal" and r.alpha * H == pytest.approx(2.0, rel=1e-12)
    w = 1.0 / H
    r = limit_load(cts, wrench((0.0, -10.0 * w), (0.0, 1.5), o, 2), wrench((1.0, 0.0), (0.0, 3.0), o, 2), dim=2)
    assert r.status == "optimal" and r.alpha / w == pytest.approx(2.0, rel=1e-12)


# ---------------------------------------------------------------- 精度：对精确有理数最优

def _si_case(seed, index):
    """复核者的 SI 模糊生成器（sifuzz.py，原样），重放到第 index 例：旋转块体、0.1–300 m、场址偏移至 1e6 m、
    黏聚 0–1e7 Pa（各接触不等）、μ 0.2–0.9、底面内或倾斜的推力、随机高度；二维与三维。"""
    def rot3(rng):
        q = [rng.gauss(0, 1) for _ in range(4)]
        n = sqrt(sum(x * x for x in q))
        w, x, y, z = (v / n for v in q)
        return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
                (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
                (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))
    mv = lambda R, v: tuple(sum(R[i][j] * v[j] for j in range(len(v))) for i in range(len(v)))
    rng = random.Random(seed)
    for t in range(index + 1):
        dim = rng.choice([2, 3]); L = 10 ** rng.uniform(-1, 2.5); mu = rng.uniform(0.2, 0.9)
        off = tuple(rng.choice([0.0, 1e3, 1e5, 1e6]) * rng.uniform(-1, 1) for _ in range(dim))
        gam = 26000.0; cmax = rng.choice([0.0, 1e4, 1e5, 1e6, 1e7])
        if dim == 3:
            R = rot3(rng) if rng.random() < 0.7 else ((1.0, 0, 0), (0, 1.0, 0), (0, 0, 1.0))
            nc = rng.randint(3, 6)
            pts = [(rng.uniform(-L / 2, L / 2), rng.uniform(-L / 3, L / 3), 0.0) for _ in range(nc)]
            V = L * (2 * L / 3) * (L / 2); W = gam * V; Ab = L * (2 * L / 3) / nc
            P = lambda p, R=R, off=off: tuple(mv(R, p)[i] + off[i] for i in range(3))
            n = mv(R, (0.0, 0.0, 1.0))
            cts = [LimitContact(P(p), n, mu, cohesion=cmax * rng.uniform(0, 1), area=Ab) for p in pts]
            g = (sum(p[0] for p in pts) / nc, sum(p[1] for p in pts) / nc)
            o = (0.0, 0.0, 0.0)
            dead = wrench(mv(R, (0.0, 0.0, -W)), P((g[0], g[1], L / 4)), o, 3)
            th = rng.uniform(0, 2 * pi); tilt = rng.choice([0.0, 0.0, -0.3, 0.2])
            d = (cos(th) * cos(tilt), sin(th) * cos(tilt), sin(tilt))
            live = wrench(mv(R, d), P((g[0] + rng.uniform(-L / 5, L / 5), g[1] + rng.uniform(-L / 5, L / 5),
                                       rng.choice([0.0, L / 4, L / 2]))), o, 3)
            k = rng.choice([4, 8, 16])
        else:
            a = rng.uniform(-pi, pi) if rng.random() < 0.7 else 0.0
            R = ((cos(a), -sin(a)), (sin(a), cos(a)))
            nc = rng.randint(2, 4)
            xs = sorted(rng.uniform(-L / 2, L / 2) for _ in range(nc))
            W = gam * L * L / 2; Ab = L / nc
            P = lambda p, R=R, off=off: tuple(mv(R, p)[i] + off[i] for i in range(2))
            n = mv(R, (0.0, 1.0))
            cts = [LimitContact(P((x, 0.0)), n, mu, cohesion=cmax * rng.uniform(0, 1), area=Ab) for x in xs]
            o = (0.0, 0.0); gx = sum(xs) / nc
            dead = wrench(mv(R, (0.0, -W)), P((gx, L / 4)), o, 2)
            tilt = rng.choice([0.0, 0.0, -0.3, 0.2]); sg = rng.choice([1.0, -1.0])
            live = wrench(mv(R, (sg * cos(tilt), sin(tilt))), P((gx + rng.uniform(-L / 5, L / 5), rng.choice([0.0, L / 4, L / 2]))), o, 2)
            k = 8
    return cts, dead, live, dim, k


def _exact_alpha(cts, dead, live, dim, k):
    """同一个 LP（形心参考点、黏聚列取力的单位——即 limit_load 内部的写法）的精确最优值。"""
    nw = 3 if dim == 2 else 6
    oc = tuple(sum(ct.point[i] for ct in cts) / len(cts) for i in range(dim))
    dead_c = _shift_wrench(list(dead), oc, dim)
    live_c = _shift_wrench(list(live), oc, dim)
    C = _build_columns(cts, oc, dim, k, unit_cohesion=True)
    cols = C.cols + [live_c]
    ncol = len(cols) + C.n_rows
    A = [[cols[j][i] if j < len(cols) else 0.0 for j in range(ncol)] for i in range(nw)]
    b = [-v for v in dead_c]
    for r_i in range(C.n_rows):
        row = [0.0] * ncol
        for j, rj in enumerate(C.row_of):
            if rj == r_i:
                row[j] = 1.0
        row[len(cols) + r_i] = 1.0
        A.append(row)
        b.append(C.cap[r_i])
    st, obj = _exact_max(A, b, [0.0] * len(C.cols) + [1.0] + [0.0] * C.n_rows)
    assert st == "optimal"
    return float(obj)


# 09-27 对 3000 例做精确对照时误差最大的几例（43d1e50 在其中最多偏低 5.3e-7，58752a5 最多 1.07e-7；
# 最优性判据改为"目标的相对改进量"之后最多偏低 1.03e-8、偏高 7.5e-13）
SI_WORST = [(1, 1149), (1, 1455), (1, 1071), (1, 1333), (1, 14), (2, 92), (2, 1033), (2, 1058), (2, 261), (2, 64)]


@pytest.mark.parametrize("seed,index", SI_WORST)
def test_accuracy_against_the_exact_rational_optimum(seed, index):
    """α 与同一 LP 的精确有理数最优值比：偏低 ≤ 3e-8，偏高（不安全一侧）≤ 1e-11。"""
    cts, dead, live, dim, k = _si_case(seed, index)
    exact = _exact_alpha(cts, dead, live, dim, k)
    r = limit_load(cts, dead, live, dim=dim, k=k)
    assert r.status == "optimal"
    rel = (r.alpha - exact) / exact
    assert -3e-8 <= rel <= 1e-11, (seed, index, r.alpha, exact, rel)
