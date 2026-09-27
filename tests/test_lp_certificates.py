"""M0.2 LP 返修的门。契约（返修三，2026-09-27）：**LP 的答案对给定的浮点数据精确成立**。

浮点修正单纯形只负责给候选（状态 + 基），有理数层在原始数据上精确核验：OPTIMAL 核原始可行 + 对偶可行
（弱对偶即最优）、UNBOUNDED 核可行 + 射线、INFEASIBLE 核 Farkas；核验不过就用有理数单纯形从候选基接着走完。
浮点层的一切阈值只影响速度。这一步之前的两轮（返修一：噪声线 ∝ κ(B)；返修二：六类相对阈值 + 容差版证书）
都在复核里被找到了静默错——浮点阈值兑现不了"绝不静默给错"，这里不再尝试。

复核者 reverify3（6fbc369）的发现逐条对应这里的门：
  · critical（新回归）：荷载清洗用 |M|/|F| 当长度，近纯力偶把它撑到 1e16，恒载偏心被清零、α 静默偏高 2–3.8 倍
    → `test_near_pure_couple_does_not_erase_the_dead_load_moment`（荷载清洗已撤回）；
  · major：纯对角缩放把有界 LP 报 UNBOUNDED；残差/间隙噪声项放过行违约 67%、目标错 3.4 倍的解
    → `test_reverify3_lp_counterexamples_are_answered_exactly`；
  · major：最优性证书 ν ≤ 1 封顶，静默次优 1e-5..50% → `test_optimality_is_exact_when_the_step_is_huge`；
  · major：容差版 Farkas 把相对差 1e-10 的可行 LP 报 INFEASIBLE → `test_nearly_parallel_rows_are_feasible_exactly`；
  · major：可分辨性只查 optimal，UTM 与旋转框架下倾覆/无物可挡的块体报 unbounded
    → `test_rounding_driven_unbounded_status_is_not_certified`、`test_status_is_frame_invariant_on_a_frictionless_floor`；
  · major：工程坐标下的普通问题假抛错 → `test_far_site_ordinary_problems_do_not_raise`；
  · 门的牙：精确层的每一种证书都有"浮点层说谎"的注入门（`test_a_lying_float_layer_cannot_change_the_answer`）。
更早的（43d1e50 的 critical、res_probe、_norm 溢出）门保留。

oracle 与被测代码不共用原语（纪律 A）：精确 LP（`_exact_max`）只用 Fraction、自带 Bland 两阶段，不碰 lp.py；
极限分析的真值用闭式。精度门与三维扭转门用 `_build_columns` 造同一个 LP——它核验的是**求解器**在给定 LP 上的
精度，不是建模。
"""

import random
from fractions import Fraction
from math import atan, cos, pi, sin, sqrt

import pytest

import eab.lp as lp
from eab.limit import LimitContact, _build_columns, _shift_wrench, limit_load, wrench
from eab.lp import INFEASIBLE, OPTIMAL, UNBOUNDED, maximize, solve


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
        assert v <= Fraction(1, 10 ** 9) * scale, (name, j, float(v))       # y 是精确证书舍入成浮点，只差舍入


def test_exact_certificate_rejects_wrong_candidates():
    """`_Exact.certify` 本身有牙：对的候选过，错的状态、次优基、不可行基、错的入基列都不过（返回 None）。"""
    A = [[1.0, 1.0, 1.0, 0.0], [1.0, 3.0, 0.0, 1.0]]
    b = [4.0, 6.0]
    c = [-3.0, -2.0, 0.0, 0.0]                      # 最优基 {x1, s2}：x = (4, 0, 0, 2)，obj = −12
    X = lp._Exact(A, b, c)
    good = X.certify(OPTIMAL, [0, 3], -1, 0)
    assert good is not None and good.obj == -12.0 and good.x == [4.0, 0.0, 0.0, 2.0]
    assert X.certify(OPTIMAL, [2, 3], -1, 0) is None           # 可行但次优（x1 的约化成本 −3）
    assert X.certify(OPTIMAL, [1, 3], -1, 0) is None           # x2 = 4、s2 = −6：不可行
    assert X.certify(INFEASIBLE, [0, 3], -1, 0) is None        # 可行问题没有 Farkas 证书
    assert X.certify(UNBOUNDED, [0, 3], 1, 0) is None          # 有界问题没有无界射线
    Xi = lp._Exact([[1.0, 1.0], [1.0, 1.0]], [1.0, 2.0], [1.0, 0.0])
    assert Xi.certify(INFEASIBLE, [0, 3], -1, 0) is not None   # y = (−1, 1)：yᵀA = 0、yᵀb = 1 > 0
    assert Xi.certify(INFEASIBLE, [2, 3], -1, 0) is None       # 人工基的 y = (1, 1)：yᵀA_j = 2 > 0，不是证书
    assert Xi.certify(OPTIMAL, [0, 3], -1, 0) is None          # 人工变量 = 1 ≠ 0
    # UNBOUNDED 候选的基里有值为 0 的人工变量、且它沿射线要变化（d_i ≠ 0）：射线不成立（G6 第二轮 minor：这一子检查
    # 删掉全套照绿，说谎的候选能让有界 LP（min −x0，−x0 + x1 = 0，x1 = 0，最优 0）被认证为无界）
    Xa = lp._Exact([[-1.0, 1.0], [0.0, 1.0]], [0.0, 0.0], [-1.0, 0.0])
    assert Xa.certify(UNBOUNDED, [2, 3], 0, 0) is None
    assert solve([[-1.0, 1.0], [0.0, 1.0]], [0.0, 0.0], [-1.0, 0.0]).obj == 0.0


LIES = ["infeasible", "unbounded", "suboptimal", "raise", "raise-overflow", "raise-value", "garbage-basis"]


@pytest.mark.parametrize("lie", LIES)
@pytest.mark.parametrize("case", ["optimal", "infeasible", "unbounded"])
def test_a_lying_float_layer_cannot_change_the_answer(monkeypatch, lie, case):
    """精确层的牙：把浮点层换成一个**说谎**的候选（报错状态、次优基、抛错、编号越界的基），solve 的答案仍须
    与真实答案逐位相同。去掉精确核验（直接信候选）这道门就红。"""
    LPS = {"optimal": ([[1.0, 1.0, 1.0, 0.0], [1.0, 3.0, 0.0, 1.0]], [4.0, 6.0], [-3.0, -2.0, 0.0, 0.0]),
           "infeasible": ([[1.0, 1.0], [1.0, 1.0]], [1.0, 2.0], [1.0, 0.0]),
           "unbounded": ([[1.0, -1.0, 0.0], [0.0, 1.0, -1.0]], [1.0, 0.0], [-1.0, 0.0, 0.0])}
    A, b, c = LPS[case]
    truth = solve(A, b, c)
    assert truth.status == case and _exact_max(A, b, [-v for v in c])[0] == {"optimal": "optimal", "infeasible":
                                                                              "infeasible", "unbounded": "unbounded"}[case]
    m, n = len(A), len(c)

    def liar(*a, **k):
        if lie == "raise":
            raise RuntimeError("float layer broke down")
        if lie == "raise-overflow":
            raise OverflowError("ldexp overflow in the float layer")
        if lie == "raise-value":
            raise ValueError("max() arg is an empty sequence")
        if lie == "infeasible":
            return INFEASIBLE, list(range(n, n + m)), -1, 0
        if lie == "unbounded":
            return UNBOUNDED, list(range(m)), 0, 0
        if lie == "suboptimal":
            return OPTIMAL, list(range(n, n + m)), -1, 0
        return OPTIMAL, [n + m + 5] * m, -1, 0

    monkeypatch.setattr(lp, "_float_solve", liar)
    r = solve(A, b, c)
    assert r.status == truth.status and r.x == truth.x and (r.obj == truth.obj or case != "optimal"), (lie, case, r)


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


def test_old_badly_scaled_limit_formulation_is_answered_exactly():
    """lp.py 的契约对任何调用方成立，不靠 limit_load 的形心平移兜底：48 个旧写法 LP（c·A 乘进列、力矩关于全局原点，
    尺度跨 ~20 个量级）**全部**答对到 1e-9，不许抛错（43d1e50：0/48 对——用当前夹具重放是 28 格错值 optimal、11 格 unbounded、4 格 infeasible、5 格抛错，G6 第二轮订正，
    原写"静默 infeasible"不准；返修二：28 对 20 抛错）。"""
    wrong = []
    for L, c, seed, off in OLD_GRID:
        R = _rot(seed) if seed is not None else ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
        cts, dead, live, full = _block(L, c, 0.6, off, R)
        A, b, cc, ia = _old_formulation(cts, dead, live)
        r = maximize(A, b, cc)
        if not (r.status == OPTIMAL and abs(r.x[ia] - full) <= 1e-9 * full):
            wrong.append((L, c, seed, off, r.status, r.x[ia] if r.status == OPTIMAL else None, full))
    assert wrong == [], wrong[:4]


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
    根因是噪声线 ν ∝ κ(B) 盖过真约化成本；现在 LP 层对给定数据精确。"""
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


def _exact_limit_lp(cts, dead, live, dim, k):
    """limit_load 内部那个 LP 的**精确**版（形心参考点、黏聚列取力的单位、力矩与荷载平移精确）：
    锥棱方向取自 `_build_columns`（它就是模型定义：锥的 k 边形线性化），其余全在这里用 Fraction 独立算——
    力矩 (p − oc) × g、荷载 m − (oc − 0) × f 都不经被测代码的 `_exact_wrench` / `_exact_shift`。"""
    nw = 3 if dim == 2 else 6
    oc = tuple(sum(ct.point[i] for ct in cts) / len(cts) for i in range(dim))
    X = lambda v: Fraction(v)

    def cross(r, g):
        if dim == 2:
            return [r[0] * g[1] - r[1] * g[0]]
        return [r[1] * g[2] - r[2] * g[1], r[2] * g[0] - r[0] * g[2], r[0] * g[1] - r[1] * g[0]]

    def shift(w):
        W = [X(v) for v in w]
        f = W[:dim]
        mo = cross([X(oc[i]) for i in range(dim)], f)
        return f + [W[dim + i] - mo[i] for i in range(nw - dim)]

    C = _build_columns(cts, oc, dim, k, unit_cohesion=True)
    cols = []
    for j, col in enumerate(C.cols):
        g = [X(v) for v in col[:dim]]
        r = [X(cts[C.owner[j]].point[i]) - X(oc[i]) for i in range(dim)]
        cols.append(g + cross(r, g))
    cols.append(shift(live))
    ncol = len(cols) + C.n_rows
    A = [[cols[j][i] if j < len(cols) else Fraction(0) for j in range(ncol)] for i in range(nw)]
    b = [-v for v in shift(dead)]
    for r_i in range(C.n_rows):
        row = [Fraction(0)] * ncol
        for j, rj in enumerate(C.row_of):
            if rj == r_i:
                row[j] = Fraction(1)
        row[len(cols) + r_i] = Fraction(1)
        A.append(row)
        b.append(X(C.cap[r_i]))
    return A, b, [0.0] * len(C.cols) + [1.0] + [0.0] * C.n_rows


def _exact_alpha(cts, dead, live, dim, k):
    """同一个 LP 的精确最优值（见 `_exact_limit_lp`）。"""
    st, obj = _exact_max(*_exact_limit_lp(cts, dead, live, dim, k))
    assert st == "optimal"
    return float(obj)


# 09-27 对 3000 例做精确对照时误差最大的几例（43d1e50 在其中最多偏低 5.3e-7，58752a5 最多 1.07e-7；
# 返修二在全部 3000 例上最多偏低 2.56e-8——seed 2 #1314；返修二的提交说明写"1.03e-8"只对 344 例子集成立，那是错的）
SI_WORST = [(1, 1149), (1, 1455), (1, 1071), (1, 1333), (1, 14), (2, 92), (2, 1033), (2, 1058), (2, 261), (2, 64), (2, 1314)]


@pytest.mark.parametrize("seed,index", SI_WORST)
def test_accuracy_against_the_exact_rational_optimum(seed, index):
    """α 与同一 LP 的精确有理数最优值比：只差最后一次舍入（≤ 4e-16）。"""
    cts, dead, live, dim, k = _si_case(seed, index)
    exact = _exact_alpha(cts, dead, live, dim, k)
    r = limit_load(cts, dead, live, dim=dim, k=k)
    assert r.status == "optimal"
    rel = (r.alpha - exact) / exact
    assert abs(rel) <= 4e-16, (seed, index, r.alpha, exact, rel)


# ---------------------------------------------------------------- reverify3（6fbc369 的复核）

REVERIFY3_LPS = {
    'garbage_rowscaled_value_3.4x': ([[-8.368754207750232e-12, 6831982296.599667, 8201.28523767056, 26030.844651961896, 0.0, 631541088.217536, 302777439689654.2, 4.573089731011056e-09], [-1.347377950984315e-10, -1.0064598389061568e-05, 7.684668012815144e-12, 0.0, 7.882424472748099e-15, 9.303606395853716e-07, -4.652650149358183e-13, 1.347377950984315e-10], [0.0, 2.744347610749496e-11, 0.11406848400927411, 0.0, -3.900130356638073e-05, 2761.9886132341853, 1.2686536340010844e-06, -4.0]],
        [981440.6126003581, 4.181001142174844e-10, -10.801702031015154],
        [2.0, 149395.3256650662, 0.22813696801854821, 2.0, -4.6185326022636316e-05, -2761.9886132341853, 13812457435.44855, -1.0]),
    'garbage_rowscaled_value_13pct': ([[0.04957547721837632, 0.0, 0.0, 0.0387647679846757, -1.7357993092318347e-06, 0.3874393396707602, 0.0], [4.608321653021526e-11, 4.4356506397002795e-22, -5.066942811348993e-13, 3.494455185457507e-13, -3.49501655919656e-15, -5.221858797978847e-10, 1.3943811976221881e-08], [-19293.85956831491, 6.49340484246648e-07, -53.03497151655614, 0.0, 3.9742141583131487, -88706.50547086835, 0.0], [-7.519248443658545e-11, 1.0122500183621948e-21, 1.0334457074888127e-13, 9.017367238279508e-11, -6.1953604500650626e-15, 1.0371272541543693e-09, 2.63876062441034e-24], [-314.5973558671834, -7.427400942273327e-09, -1.2219675661763816, 184.63815033856812, 0.06818783681375735, 2529.550340366131, 0.0]],
        [5132212.064735526, -0.025378898724736098, 36368394286113.66, 0.058858236355711774, -155371213176.41406],
        [0.0, -1.34621169382412e-11, 0.0027488005356715735, 1.0, -8.239334684159824e-05, 17.442411566726367, 382.07924347702243]),
    'pure_scaling_bounded_reported_unbounded_A': ([[-2407427058840.042, -2.0, 2.9418126137105775e-12, -676085418712.8226, 0.5, 0.0, -2.0, 6.493052856440445e-05, 16951.97540822329], [-1.4130265688361896e+20, 134158790.09181298, 0.0003946700209322451, -4.535140088661453e+19, -234777882.66067272, 0.0, 134158790.09181298, -8711.001152222403, 284282063804.17554], [-18.284938064468314, 0.0, 8.937485560187618e-23, -0.6418771838829093, -3.0380879864793826e-11, -5.3166539763389195e-11, -3.0380879864793826e-11, 1.7260657643886435e-15, 0.0], [-9.128466657813816e+16, -37917.93659664247, -1.7847594266540918e-06, 4.486258707116774e+16, 151671.74638656987, 0.0, -303343.49277313973, -39.392506644665126, 642783928.716853]],
        [-0.025043375347237183, -1414647.9732212536, -6.106740322083484e-13, -2998.7151113130267],
        [335624119848.9495, 0.8364717475859764, 0.0, 0.0, 1.3941195793099606, 0.2788239158619921, -0.06970597896549803, 5.4312552699948543e-05, 0.0]),
    'pure_scaling_bounded_reported_unbounded_B': ([[-140260389997.24377, -1122083119977.9502, 1790315942278021.2, 0.0, 1016480.2598825705, 0.0, -958050.809908178], [1.2257174598462264e-10, -2.451434919692453e-10, 0.0, 0.012739675793535464, 5.55180618950751e-16, 176.82383769074397, -5.980201767926822e-17], [0.5, 0.5, -1595.528807449846, 0.0, -9.058867759302405e-07, -120217915549.72736, 0.0], [2.0, -4.0, -1595.528807449846, 0.0, -9.058867759302405e-07, 2404358310994.547, 2.4394699283622322e-06]],
        [-4838983454904.91, 2.1450055547308964e-10, -0.25, 5.75],
        [-6.720386958197493e-09, -6.720386958197493e-09, 5.361285494507172e-06, 0.17462334073563945, 0.0, 2423.732735406226, 0.0]),
}


@pytest.mark.parametrize("name", sorted(REVERIFY3_LPS))
def test_reverify3_lp_counterexamples_are_answered_exactly(name):
    """复核者的 LP 层反例（来源 reverify3/lp_defect_cases.json）：纯对角缩放的有界 LP 曾报 UNBOUNDED；
    垃圾元 + 行缩放 6.7e-11 时残差/间隙噪声项放过行违约 67%、目标错 3.4 倍（另一例错 13%）。答案须与精确最优逐位一致。"""
    A, b, c = REVERIFY3_LPS[name]
    st, obj = _exact_max(A, b, [-v for v in c])
    r = solve(A, b, c)
    assert st == "optimal" and r.status == OPTIMAL
    assert r.obj == float(-obj), (name, r.obj, float(-obj))


@pytest.mark.parametrize("eta", [1e-5, 1e-8, 1e-10])
@pytest.mark.parametrize("d", [1e-10, 5e-11, 1e-11])
def test_optimality_is_exact_when_the_step_is_huge(eta, d):
    """min −x1 + x2 + (1−d)x3，x1 − x2 − x3 = 1，ηx2 + ηx3 + s = 1：约化成本 −d 的列步长 1/η。返修二的最优性证书
    把"还能改进多少"估成 |r_j|·ν_j（ν ≤ 1），漏掉 d/η 的改进，静默次优 1e-5..50%。"""
    A = [[1.0, -1.0, -1.0, 0.0], [0.0, eta, eta, 1.0]]
    for c in ([-1.0, 1.0, 1.0 - d, 0.0], [-1.0, 1.0 - d, 1.0, 0.0]):              # 两种列序
        st, obj = _exact_max(A, [1.0, 1.0], [-v for v in c])
        r = solve(A, [1.0, 1.0], c)
        assert st == "optimal" and r.status == OPTIMAL and r.obj == float(-obj), (eta, d, r.obj, float(-obj))


@pytest.mark.parametrize("d", [1e-6, 1e-8, 1e-10, 1e-11, 1e-12, 1e-13])
def test_nearly_parallel_rows_are_feasible_exactly(d):
    """x1 − x2 = 1、−x1 + (1+d)x2 − s = 0、min x2：浮点数据上精确最优 1/((1+d) − 1)。返修二的容差版 Farkas
    （列判据 1e-9 相对）把 d ≤ 1e-10 报成 INFEASIBLE。"""
    A = [[1.0, -1.0, 0.0], [-1.0, 1.0 + d, -1.0]]
    st, obj = _exact_max(A, [1.0, 0.0], [0.0, -1.0, 0.0])
    r = solve(A, [1.0, 0.0], [0.0, 1.0, 0.0])
    assert st == "optimal" and r.status == OPTIMAL and r.obj == float(-obj), (d, r.status, r.obj)


@pytest.mark.parametrize("xg", [0.5, 0.2, -0.3])
@pytest.mark.parametrize("sign", [1.0, -1.0])
def test_near_pure_couple_does_not_erase_the_dead_load_moment(xg, sign):
    """复核者的 critical：活荷载 = 一个力 + 它转 π 后的力（合力只剩 sin π 的舍入残差、力偶 ∓1）。返修二的荷载清洗
    用 L = |M|/|F| ~ 1e16 当长度，把恒载偏心的真实力矩当噪声清零，α 静默偏高 2 倍。闭式：绕一个支点倾覆，
    α·1 = W·(1 − sign·xg)。"""
    W, o = 10.0, (0.0, 0.0)
    cts = [LimitContact((-1.0, 0.0), (0.0, 1.0), 0.5), LimitContact((1.0, 0.0), (0.0, 1.0), 0.5)]
    dead = wrench((0.0, -W), (xg, 0.7), o, 2)
    g = (cos(pi), sin(pi))
    live = [a + bb for a, bb in zip(wrench((sign, 0.0), (0.0, 0.5), o, 2), wrench((sign * g[0], sign * g[1]), (0.0, -0.5), o, 2))]
    assert live[1] != 0.0                                   # 前提：合力确实只剩舍入残差
    r = limit_load(cts, dead, live, dim=2, k=8)
    assert r.status == "optimal" and r.alpha == pytest.approx(W * (1.0 - sign * xg), rel=1e-12), (r.status, r.alpha)


@pytest.mark.parametrize("xg,yg", [(0.0, 0.0), (0.7, 0.0), (0.7, 0.4), (-0.8, 0.5)])
@pytest.mark.parametrize("off", [(0.0, 0.0, 0.0), (1e3, 2e3, 100.0)])
def test_near_pure_torsion_does_not_erase_the_dead_load_moment(xg, yg, off):
    """三维版：扭矩由一个力与它转 π 后的力构成，恒载偏心。真值用同一 LP 的精确有理数最优（返修二返回 6.788，真值 1.8）。"""
    o = (0.0, 0.0, 0.0)
    cts = [LimitContact((off[0] + sx, off[1] + 0.6 * sy, off[2]), (0.0, 0.0, 1.0), 0.6) for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    dead = wrench((0.0, 0.0, -10.0), (off[0] + xg, off[1] + yg, off[2] + 0.5), o, 3)
    g = (cos(pi), sin(pi), 0.0)
    live = [a + bb for a, bb in zip(wrench((1.0, 0.0, 0.0), (off[0], off[1] + 0.5, off[2] + 0.3), o, 3),
                                   wrench(g, (off[0], off[1] - 0.5, off[2] + 0.3), o, 3))]
    exact = _exact_alpha(cts, dead, live, 3, 8)
    r = limit_load(cts, dead, live, dim=3, k=8)
    assert r.status == "optimal" and abs(r.alpha - exact) <= 4e-16 * exact, (r.alpha, exact)


def _floor(W, H, a, T, press):
    """无摩擦地面双接触，恒载 (H, −W)，活荷载沿地面法向压（θ = 3π/2 的舍入分量）或向上提；整体转 a、平移 T。"""
    Rm = lambda v: (cos(a) * v[0] - sin(a) * v[1], sin(a) * v[0] + cos(a) * v[1])
    P = lambda q: (Rm(q)[0] + T[0], Rm(q)[1] + T[1])
    o = (0.0, 0.0)
    cts = [LimitContact(P((x, 0.0)), Rm((0.0, 1.0)), 0.0) for x in (-1.0, 1.0)]
    lv = (cos(3 * pi / 2), sin(3 * pi / 2)) if press else (0.0, 1.0)
    return cts, wrench(Rm((H, -W)), P((0.0, 0.5)), o, 2), wrench(Rm(lv), P((0.0, 0.0)), o, 2)


@pytest.mark.parametrize("W,H", [(1e6, 1e-3), (10.0, 1e-8), (1e6, 1e-1)])
@pytest.mark.parametrize("a,T", [(0.0, (0.0, 0.0)), (0.7, (0.0, 0.0)), (0.7, (3e3, -2e3)), (-2.0, (0.0, 0.0))])
@pytest.mark.parametrize("press", [True, False])
def test_status_is_frame_invariant_on_a_frictionless_floor(W, H, a, T, press):
    """水平恒载 H 无物可挡：物理上对任何 α 都不可行。返修二在旋转框架下报 unbounded（press）或 optimal α = W（lift），
    地面框架下报 infeasible——状态随坐标系变。现在任何框架都是 infeasible。"""
    cts, dead, live = _floor(W, H, a, T, press)
    r = limit_load(cts, dead, live, dim=2, k=8)
    assert r.status == "infeasible", (W, H, a, T, press, r.status, r.alpha)


@pytest.mark.parametrize("frame", [(0.0, (0.0, 0.0), 1.0, 1.0), (-2.2145790363256497, (0.0, 0.0), 1.0, 1.0),
                                   (0.0, (456126.84150283627, 6015705.33931258), 1.0, 1.0),
                                   (-2.2145790363256497, (456126.84150283627, 6015705.33931258), 0.8333772175908678, 1273009.369168711),
                                   (-2.2145790363256497, (456126.84150283627, 6015705.33931258), 1.0, 1.0)])
def test_rounding_driven_unbounded_status_is_not_certified(frame):
    """57° 斜坡上的双接触块体，重心在底外——自重下必倾覆，对任何 α 都不可行；活荷载沿底面线水平推，对接触点
    没有力矩。放到 UTM 坐标（并旋转、换单位）后，内部平移带进舍入级的力矩，浮点数据的精确 LP 变成"大 α 可行且无界"，
    返修二报 unbounded（α = ∞，不安全）。无界结论要对最小可行荷载因子做可分辨性检查。"""
    a, T, s, f = frame
    raw = [((1.0, 0.0), (-0.8414709848078965, 0.5403023058681398), 1.0, 0.0),
           ((1.5, 0.0), (-0.8414709848078965, 0.5403023058681398), 0.2, 1.0)]
    Rm = lambda v: (cos(a) * v[0] - sin(a) * v[1], sin(a) * v[0] + cos(a) * v[1])
    P = lambda q: tuple(s * Rm(q)[i] + T[i] for i in range(2))
    o = (0.0, 0.0)
    cts = [LimitContact(P(pp), Rm(n), mu, cohesion=(c * f / (s * s) if c else 0.0), area=(s * s if c else 0.0)) for pp, n, mu, c in raw]
    dead = wrench(tuple(f * v for v in Rm((0.0, -10.0))), P((0.0, 0.7)), o, 2)
    live = wrench(tuple(f * v for v in Rm((1.0, 0.0))), P((0.0, 0.0)), o, 2)
    r = limit_load(cts, dead, live, dim=2, k=4)
    assert r.status == "infeasible", (frame, r.status, r.alpha)


def test_genuine_self_locking_stays_unbounded():
    """反面：真正的自锁（μ = 0.5 的地面上向下压，陡于摩擦角）在任何框架下都是 unbounded，不许被可分辨性检查误伤。"""
    for rot, t in ((0.0, (0.0, 0.0)), (0.37, (3e4, -2e3)), (-1.1, (5e5, 4e6))):
        for b in (1.3, 1.5707963267948966):
            r2 = lambda q: (cos(rot) * q[0] - sin(rot) * q[1], sin(rot) * q[0] + cos(rot) * q[1])
            P = lambda q: tuple(r2(q)[i] + t[i] for i in range(2))
            cts = [LimitContact(P((x, 0.0)), r2((0.0, 1.0)), 0.5) for x in (-1.0, 1.0)]
            o = (0.0, 0.0)
            r = limit_load(cts, wrench(r2((0.0, -10.0)), P((0.0, 0.0)), o, 2),
                           wrench(r2((cos(b), -sin(b))), P((0.0, 0.0)), o, 2), dim=2, k=8)
            assert r.status == "unbounded", (rot, t, b, r.status, r.alpha)


def test_far_site_ordinary_problems_do_not_raise():
    """返修二在工程坐标下对普通问题假抛错（"lost feasibility"、"phase 2 could not reach a verified optimal basis"），
    58752a5 能答对。(1) limfuzz 种子 11 #428 缩到 0.3 m、放到 (69103, 632, −686) m、力 ×673；
    (2) 1.6 km 块体在 ~3.7e5 m、旋转、离自锁 1e-6。"""
    raw = [((-1.0, 0.6, 0.0), (0.29552020666133955, 0.0, 0.955336489125606), 0.5, 1.0),
           ((1.0, 0.0, 0.0), (0.29552020666133955, 0.0, 0.955336489125606), 0.0, 0.0),
           ((1.0, -0.6, 0.0), (0.0, 0.0, 1.0), 0.2, 1.0),
           ((1.0, 0.0, 0.0), (0.22602632124962302, 0.19037934406737264, 0.955336489125606), 0.0, 0.0),
           ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0.5, 0.0)]
    T, s_, f = (69103.39558006787, 631.9118509093739, -686.3994450252582), 0.1588708301703475, 672.7007425936694
    P = lambda q: tuple(s_ * q[i] + T[i] for i in range(3))
    o = (0.0, 0.0, 0.0)
    cts = [LimitContact(P(pp), n, mu, cohesion=(c * f / (s_ * s_) if c else 0.0), area=(s_ * s_ if c else 0.0)) for pp, n, mu, c in raw]
    dead = wrench((0.0, 0.0, -10.0 * f), P((0.1, 0.0, 0.5)), o, 3)
    live = wrench((0.5403023058681398 * f, 0.8414709848078965 * f, 0.0), P((0.0, 0.0, 0.0)), o, 3)
    r = limit_load(cts, dead, live, dim=3, k=5)
    assert r.status == "optimal" and r.alpha == pytest.approx(5.0851978197377745, rel=1e-9)
    c446 = {"dead": [5.418618323048547, -1.1061630817624266, 8.33156520142934, -2045.4953791880591, 3074612.9626349164, 409539.74748117576],
            "live": [0.4465721357977319, -0.5432124825482392, 0.7109806792964424, 222.71060203906802, 262360.5074112805, 200312.11867136968],
            "n": (-0.5418618323048547, 0.11061630817624266, -0.8331565201429341),
            "tg": (-0.08515729993178223, -0.9934255446176218, -0.07651092451088154),
            "p": [(-367720.3723412959, 406.83661235054404, 508.7967332916722), (-369055.97619069595, 453.943791558735, 1383.6906502196396),
                  (-367856.3975299352, -1180.0020640040568, 386.5827487255254), (-369192.00137933524, -1132.894884795866, 1261.4766656534928)]}
    cts = [LimitContact(pp, c446["n"], 0.5, tangent=c446["tg"]) for pp in c446["p"]]
    bb = pi / 2 - atan(0.5) - 1e-6
    exact = 0.5 * 10 / (cos(bb) - 0.5 * sin(bb))
    r = limit_load(cts, c446["dead"], c446["live"], dim=3, k=8)
    assert r.status == "optimal" and abs(r.alpha - exact) <= (r.uncertainty + 1e-9) * exact, (r.alpha, exact, r.uncertainty)


# ---------------------------------------------------------------- reverify4（26c2259 的复核）

@pytest.mark.parametrize("name", ["beale", "kuhn", "chvatal"])
def test_exact_simplex_terminates_on_classic_cycling_examples(monkeypatch, name):
    """有理数单纯形用 Dantzig 定价，连续 2m + 10 次退化换基后改 Bland——Dantzig 在精确算术里会真的循环。
    复核者 reverify4：删掉这个切换，全套照绿，而 Beale、Chvátal 例从松弛基热启动永不终止。这里从松弛基热启动，
    换基上限压到 1000（变异下会抛"exceeded"而不是挂死），答案须等于独立精确 LP 的最优值。"""
    monkeypatch.setattr(lp, "_EXACT_PIVOT_CAP", 1000)
    LPS = {"beale": ([[1, 0, 0, 0.25, -8, -1, 9], [0, 1, 0, 0.5, -12, -0.5, 3], [0, 0, 1, 0, 0, 1, 0]],
                     [0, 0, 1], [0, 0, 0, -0.75, 20, -0.5, 6], [0, 1, 2]),
           "kuhn": ([[-2, -9, 1, 9, 1, 0, 0], [Fraction(1, 3), 1, Fraction(-1, 3), -2, 0, 1, 0], [2, 3, -1, -12, 0, 0, 1]],
                    [0, 0, 2], [-2, -3, 1, 12, 0, 0, 0], [4, 5, 6]),
           "chvatal": ([[0.5, -5.5, -2.5, 9, 1, 0, 0], [0.5, -1.5, -0.5, 1, 0, 1, 0], [1, 0, 0, 0, 0, 0, 1]],
                       [0, 0, 1], [-10, 57, 9, 24, 0, 0, 0], [4, 5, 6])}
    A, b, c, start = LPS[name]
    Af = [[float(v) for v in row] for row in A]
    X = lp._Exact(Af, [float(v) for v in b], [float(v) for v in c], (A, b, c))
    st, basis, e, piv = lp._exact_simplex(X, start)
    res = X.certify(st, basis, e, piv)
    ex_st, ex_obj = _exact_max(A, b, [-Fraction(v) for v in c])
    assert res is not None and st == ex_st == "optimal" and res.obj == float(-ex_obj), (name, st, piv)


def test_unbounded_certificate_requires_a_descent_direction(monkeypatch):
    """UNBOUNDED 证书除了"射线可行"还要"目标沿射线下降"（c_e − c_Bᵀd < 0）。复核者：删掉下降条件全套照绿，
    此时说谎的候选能让有界 LP 报 unbounded。min x2，x1 − x2 = 1：最优 0；基 {x1}、入基 x2 时 d = −1 ≤ 0 是一条可行射线，
    但约化成本 +1，不是下降方向。"""
    A, b, c = [[1.0, -1.0]], [1.0], [0.0, 1.0]
    assert solve(A, b, c).status == OPTIMAL
    assert lp._Exact(A, b, c).certify(UNBOUNDED, [0], 1, 0) is None
    monkeypatch.setattr(lp, "_float_solve", lambda *a, **k: (UNBOUNDED, [0], 1, 0))
    r = solve(A, b, c)
    assert r.status == OPTIMAL and r.obj == 0.0 and r.x == [1.0, 0.0]


def test_values_beyond_the_float_range_and_float_layer_overflow_do_not_raise():
    """(1) 精确解超出浮点范围（x·1e-300 = 1e10 ⇒ x = 1e310）：状态照报、值给 inf，不抛 OverflowError（26c2259 的 `_fl`，
    复核者：删掉它全套照绿）；(2) 浮点层自己的 ldexp 溢出（OverflowError，复核者 32000 例里 427 例）只算"没有候选"，
    由有理数层答出 x = 1、目标 1e10；(3) 次正规/下溢的对偶：A = 1e300、c = (1e-25, 5e-26) 时 y ~ 1e-325 下溢成 0，
    浮点过滤若不计绝对误差会静默错 2 倍、反号时死循环（复核者 reverify4）。"""
    r = solve([[1e-300, 1.0, -1.0]], [1e10], [0.0, 1.0, 1.0])
    assert r.status == OPTIMAL and r.x[0] == float("inf") and r.obj == 0.0
    r = solve([[1e-300]], [1e-300], [1e10])
    assert r.status == OPTIMAL and r.x == [1.0] and r.obj == 1e10
    r = solve([[1e300, 1e300]], [1e300], [1e-25, 5e-26])
    assert r.status == OPTIMAL and r.obj == 5e-26 and r.x == [0.0, 1.0]
    r = solve([[1e300, 1e300]], [1e300], [-1e-25, -5e-26])
    assert r.status == OPTIMAL and r.obj == -1e-25 and r.x == [1.0, 0.0]


def test_redundant_and_degenerate_rows_through_the_exact_path(monkeypatch):
    """有理数单纯形里冗余行的人工变量：一阶段后值为 0 的人工变量要换出基（drive-out），换不出的（行冗余）在二阶段必须
    留在 0（比值检验把它的任何非零分量当 0 步长挡住）。复核者：两处一起删全套照绿，而 366/3000 个退化 LP 的输出过不了
    自身证书。这里强制走有理数路径（浮点层抛错），200 个带重复行/零右端项的随机 LP，状态与目标须等于独立精确 LP。"""
    monkeypatch.setattr(lp, "_float_solve", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("forced")))
    rng = random.Random(4)
    for t in range(200):
        m, n = rng.randint(2, 4), rng.randint(2, 6)
        base = [[float(rng.randint(-2, 2)) for _ in range(n)] for _ in range(m)]
        rows = base + [[2.0 * v for v in base[rng.randrange(m)]]]          # 一行冗余（另一行的 2 倍）
        x0 = [float(rng.randint(0, 1)) for _ in range(n)]                  # 右端项取一个 0/1 解，大量退化
        b = [sum(a * x for a, x in zip(row, x0)) for row in rows]
        c = [float(rng.randint(-3, 3)) for _ in range(n)]
        st, obj = _exact_max(rows, b, [-v for v in c])
        r = solve(rows, b, c)
        assert r.status == st, (t, r.status, st)
        if st == "optimal":
            assert r.obj == float(-obj), (t, r.obj, float(-obj))


@pytest.mark.parametrize("th,mu", [(0.1, 0.4), (0.2, 0.4), (0.3, 0.6), (0.1, 0.6), (0.25, 0.5)])
def test_a_pinched_vertex_has_no_rounding_driven_capacity(th, mu):
    """复核者 reverify4 的 critical：块体尖端 V = (0, 0) 卡在 V 槽里（两个接触在同一点，槽壁离竖直 th、tan th < μ，
    两条摩擦锥含相反方向），另有一个左墙接触，自重过 V，水平推力作用在 (0, 1)。V 点抵不了力矩，答案 α = 0。
    26c2259 报 unbounded（α = ∞）：每列的力矩 r × g 各自在浮点里舍入，3e16 的夹持力拼出一个舍入级的力矩。
    现在力矩列精确（limit._exact_wrench），夹持力对的合力矩精确为 0。"""
    o = (0.0, 0.0)
    nL, nR = (cos(th), sin(th)), (-cos(th), sin(th))
    cts = [LimitContact((0.0, 0.0), nL, mu), LimitContact((0.0, 0.0), nR, mu), LimitContact((-1.0, 0.5), (1.0, 0.0), 0.3)]
    dead = wrench((0.0, -10.0), (0.0, 0.8), o, 2)
    live = wrench((1.0, 0.0), (0.0, 1.0), o, 2)
    r = limit_load(cts, dead, live, dim=2, k=8)
    ex = _exact_alpha(cts, dead, live, 2, 8)
    assert r.status == "optimal" and r.alpha == ex, (th, mu, r.status, r.alpha, ex)


# ---------------------------------------------------------------- reverify5（13397ab 的复核）

UB_UTM_CASES = [{'cts': [((4416687.448694521, -4817901.321769641, 4987255.658956827), (0.6350947199624724, 0.7440502595399601, -0.20747025799932628), 0.8038952677519826, 0.0, 0.0, (-0.07483722228800269, -0.2036741711229122, 0.976174278588414)), ((4416690.159802262, -4817901.692093945, 4987257.345604637), (-0.626061257408404, 0.3622464355781065, -0.690525033494923), 0.7920556681196997, 0.0, 0.0, None), ((4416689.6955302805, -4817902.287485453, 4987257.396351473), (-0.5257805902083094, 0.3387476844017914, -0.7802594294672933), 0.8005830330196995, 0.0, 0.0, (0.29670500995232085, 0.7970362927554553, 0.5260221336596336))], 'dead': [-161716.4466457288, -125801.93347276539, 70474.47248731428, 287867421591.67236, -1117785088572.018, -1334761730092.3452], 'live': [0.13110764635652244, -0.7717950597166818, 0.6222083018280746, 851401.7570292493, -2094232.8337675075, -2777114.722496259], 'k': 5}, {'cts': [((2366427.645202079, 2933892.617719097, 3751401.895993816), (-0.34294346036274637, 0.6559545784729424, -0.6723937640808473), 0.8038952677519826, 0.0, 0.0, (0.2505292795342841, -0.8845564445643057, -0.39343992740415484)), ((2366425.5456478554, 2933891.1790282945, 3751399.9328160486), (0.5077310575291093, 0.7402940334676616, 0.4406516960509207), 0.7920556681196997, 0.0, 0.0, None), ((2366425.750330096, 2933890.744534398, 3751400.517568129), (0.38593614155833195, 0.7980767613685457, 0.4627383468036343), 0.8005830330196995, 0.0, 0.0, (0.17287755993650178, 0.11231633005637981, -0.9785184675176386))], 'dead': [115717.92607509761, -140124.49041117993, 117980.82736384569, 871806247137.8657, 154911311544.5484, -671098381305.8387], 'live': [-0.23827658830563755, -0.9658835818524076, 0.1014552796723226, 3921075.3428647085, -1133957.5015472996, -1586615.0938191665], 'k': 5}, {'cts': [((1332985.1710467746, -5561306.533155317, 4693685.390465043), (0.6034949934080208, -0.7315771637847291, -0.3171571319711174), 0.8038952677519826, 0.0, 0.0, (0.46618851195928396, 0.6977083010591602, 0.5439406198753027)), ((1332987.076308732, -5561307.500997472, 4693687.791565738), (-0.4522879872528093, -0.007222784434999659, -0.8918427036040648), 0.7920556681196997, 0.0, 0.0, None), ((1332986.5362838092, -5561307.02112763, 4693688.01676072), (-0.48630782012172824, -0.13635895891785207, -0.8630822315465034), 0.8005830330196995, 0.0, 0.0, (0.9786363681223603, -0.023159048325505225, -0.20429027747040018))], 'dead': [-100490.88773461999, 187395.66108781353, 41586.47065262341, -1110851447612.7659, -527106815344.346, -309064890211.7877], 'live': [-0.05445032297489351, 0.4074759676529677, 0.9115911902345301, -6982202.720970675, -1470711.1957072401, 240344.8790674021], 'k': 5}, {'cts': [((417520.65789050213, 4896348.164782172, 3608910.7592971306), (0.8278411882597435, -0.4394830982086308, -0.3486166568161061), 0.8038952677519826, 0.0, 0.0, (-0.8401117669107598, -0.3230808604283626, -0.43569596821975476)), ((417520.5633036354, 4896348.038685608, 3608907.5488175573), (0.37710998341585256, -0.05746144221184837, 0.9243842507675202), 0.7920556681196997, 0.0, 0.0, None), ((417520.0048849584, 4896348.454212814, 3608907.8456685017), (0.47808575915268775, 0.022015032491593478, 0.8780372117625723), 0.8005830330196995, 0.0, 0.0, (0.16420286434953862, -0.8996907167720727, -0.4044675926369887))], 'dead': [-191557.37770712996, 48712.15613382096, 88757.4433179232, 258789520704.13538, -728371432175.3291, 958269883766.8451], 'live': [-0.7714588436805175, 0.3689566911183336, -0.5183842325786241, -3869720.7999723246, -2567688.959460092, 3931377.89178517], 'k': 5}]


@pytest.mark.parametrize("i", range(len(UB_UTM_CASES)))
def test_a_stable_unbounded_conclusion_is_not_rejected_at_engineering_coordinates(i):
    """普通三维块体（一个底面接触 + 两个墙面接触、单位推力），精确模型无界，所有输入做 1e-7 相对扰动仍无界。
    13397ab 在 UTM 坐标下对它抛"unbounded capacity is not certified"（40 个摆放里 14 个）：当时要求最小可行荷载因子
    α_min 的相对精度 ≤ 1e-6，而 α_min 既不报给调用方、也不影响无界结论。现在查的是"推 ±16 倍舍入后是否仍无界"。
    这里是 13397ab 上抛错的 4 个摆放（reverify5/ub_false_raise.py 的场景），答案须等于独立精确模型的状态。"""
    cs = UB_UTM_CASES[i]
    cts = [LimitContact(p, n, mu, cohesion=co, area=ar, tangent=tg) for p, n, mu, co, ar, tg in cs["cts"]]
    st, _ = _exact_max(*_exact_limit_lp(cts, cs["dead"], cs["live"], 3, cs["k"]))
    r = limit_load(cts, cs["dead"], cs["live"], dim=3, k=cs["k"])
    assert st == "unbounded" and r.status == "unbounded", (st, r.status)


def test_exact_data_whose_float_rounding_changes_signs():
    """`exact=` 的数据以精确符号为准（reverify5）：精确 b = −1e-400 而浮点 b = −0.0 时，两层曾按各自的符号取负行，
    有理数冷启动的人工基不可行，抛内部错误；m = 0 时曾完全忽略 exact=，精确 c = −1e-400 静默报 optimal 0。"""
    t = Fraction(1, 10 ** 400)
    r = solve([[1.0, -1.0]], [-0.0], [1.0, 0.0], exact=([[1, -1]], [-t], [1, 0]))
    assert r.status == OPTIMAL and r.obj == 0.0
    r = solve([[1.0, -1.0]], [0.0], [1.0, 0.0], exact=([[1, -1]], [-t], [1, 0]))
    assert r.status == OPTIMAL and r.obj == 0.0
    assert solve([[1.0]], [-0.0], [1.0], exact=([[1]], [-t], [1])).status == INFEASIBLE
    assert solve([], [], [0.0], exact=([], [], [-t])).status == UNBOUNDED
    r = solve([[1.0]], [0.3333333333333333], [1.0], exact=([[3]], [1], [1]))    # 1/3 不可表示：以精确数据为准
    assert r.status == OPTIMAL and r.x == [1 / 3] and r.obj == 1 / 3


def test_cohesion_capacity_is_the_exact_product():
    """黏聚上限 c·A 用精确乘积（reverify5：曾用浮点 fl(c·A)）。无摩擦黏聚单点支承，c = 0.1、A = 3，恒载力矩
    −fl(0.1·3) 迫使 α = fl(0.1·3) = 0.30000000000000004，剪力 = α 超过精确容量 0.1·3 = 0.3000000000000000166…，
    调用方数据的精确模型不可行；旧版报 optimal 0.30000000000000004。"""
    c, A = 0.1, 3.0
    assert Fraction(c) * Fraction(A) < Fraction(c * A)
    cts = [LimitContact((0.0, 0.0), (0.0, 1.0), 0.0, cohesion=c, area=A)]
    r = limit_load(cts, [0.0, -10.0, -(c * A)], [1.0, 0.0, 1.0], dim=2, k=4)
    assert r.status == "infeasible", (r.status, r.alpha)


# ---------------------------------------------------------------- reverify6（259741c 的聚焦复核）

def test_an_unbounded_conclusion_that_turns_finite_within_rounding_is_not_certified():
    """无界规则的"推后变有限值 ⇒ 不认证"分支（reverify6：可达、却没有门——改成"照样认证无界"或"报不可行"全套照绿）。
    1 mm 的块体放在 UTM (−2.68e6, −1.17e6)，活荷载作用线过两个接触点：浮点数据的精确模型无界，最小可行荷载因子 2.40，
    但活荷载在自己的 ±16 倍舍入盒内一动，精确 α 就变成有限值（复核者实测 6.9e4）。这里先用独立 oracle 在盒的 8 个角上
    求精确解、确认确有有限值（舍入模型按文档独立写：力 4u|F|、力矩 4u(|M_c| + |F|·R)），再要求 limit_load 抛"不认证"。"""
    import itertools
    cts = [LimitContact((-2683300.084913029, -1166311.8482405145), (0.9854095035625761, 0.1702002064879991), 1.0),
           LimitContact((-2683300.085281646, -1166311.8485783334), (0.9854095035625761, 0.1702002064879991), 0.2,
                        cohesion=1000000.0, area=1e-06)]
    dead = [-6.756375623672026, 7.372339413771618, -27662239.917033132]
    live = [-0.7372339413771618, -0.6756375623672026, 953093.6477171098]
    A, b, c = _exact_limit_lp(cts, dead, live, 2, 4)
    assert _exact_max(A, b, c)[0] == "unbounded"
    ia = [j for j, cj in enumerate(c) if cj == 1.0][0]
    u = Fraction(4) * Fraction(2) ** -53
    F = [A[i][ia] for i in range(2)]
    Fn = Fraction(sqrt(float(F[0] ** 2 + F[1] ** 2)))
    R = Fraction(max(sqrt(sum(v * v for v in ct.point)) for ct in cts))
    e = [u * Fn, u * Fn, u * (abs(A[2][ia]) + Fn * R)]
    finite = []
    for sg in itertools.product((-1, 1), repeat=3):
        A2 = [row[:] for row in A]
        for i in range(3):
            A2[i][ia] = A[i][ia] + sg[i] * 16 * e[i]
        st, obj = _exact_max(A2, b, c)
        if st == "optimal":
            finite.append(float(obj))
    assert finite, "the ±16e box should contain a finite capacity"
    with pytest.raises(RuntimeError, match="unbounded capacity is not certified"):
        limit_load(cts, dead, live, dim=2, k=4)


def test_float_filter_never_decides_a_sign_from_an_overflowed_estimate():
    """`_Exact.reduced_sign` 用浮点估值 s 与误差界 E 比较，只在 |s| **严格**超过 E 时定论。浮点求和溢出时 s = ±inf、
    a = inf ⇒ E = inf，严格比较不成立，于是落到有理数（非有限值守卫因此是冗余的，reverify6 核实）；但把比较改成 ≥ 就会
    拿溢出的估值定符号（复核者实测 2 万次里错 171 次）。这里构造两列：浮点里 s 分别溢出成 +inf / −inf，精确符号相反。"""
    A = [[1.0], [1.0], [1.0]]
    X = lp._Exact(A, [1.0, 1.0, 1.0], [1.7e308])
    y = [Fraction(-1.7e308), Fraction(1.79e308), Fraction(1.79e308)]         # r = 1.7 + 1.7 − 1.79 − 1.79 (e308) < 0
    sg, s = X.reduced_sign(X.c, X.cf, y, [float(v) for v in y], 0)
    assert sg == -1, (sg, s)
    X2 = lp._Exact(A, [1.0, 1.0, 1.0], [-1.7e308])
    y2 = [Fraction(1.7e308), Fraction(-1.79e308), Fraction(-1.79e308)]      # r = −1.7 − 1.7 + 1.79 + 1.79 (e308) > 0
    sg2, s2 = X2.reduced_sign(X2.c, X2.cf, y2, [float(v) for v in y2], 0)
    assert sg2 == 1, (sg2, s2)
