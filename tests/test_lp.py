"""单纯形内核的门。独立 oracle（都不调用 lp.py）：

  · 有界时：**枚举全部基本可行解**（小问题上的暴力真值，本文件自带的浮点高斯消去）；
  · 无界时：**回收锥极射线证书**（`brute_unbounded`，fractions.Fraction 精确算）。
    可行域非空时，min cᵀx 无界 ⟺ 回收锥 {d : Ad = 0, d ≥ 0} 里有 cᵀd < 0 的方向
    ⟺ 截面 {Ad = 0, Σd = 1, d ≥ 0}（有界多面体）的某个顶点——即某条极射线——满足 cᵀd < 0。
    顶点 = 该增广系统的基本可行解，逐个 (m+1) 列基用有理数精确解出。
"""
from construction_oracle import scalar_exact

import itertools
import random
from fractions import Fraction

import pytest

from eab.lp import INFEASIBLE, OPTIMAL, UNBOUNDED, maximize, solve


def _rref_exact(T):
    """有理数行最简形（最后一列是右端项）。返回 (非零行, 主元列)。只用 Fraction，不共用 lp.py。"""
    T = [list(r) for r in T]
    ncol = len(T[0]) - 1
    piv, r = [], 0
    for col in range(ncol):
        p = next((i for i in range(r, len(T)) if T[i][col] != 0), None)
        if p is None:
            continue
        T[r], T[p] = T[p], T[r]
        pv = T[r][col]
        T[r] = [v / pv for v in T[r]]
        for i in range(len(T)):
            if i != r and T[i][col] != 0:
                f = T[i][col]
                T[i] = [a - f * bb for a, bb in zip(T[i], T[r])]
        piv.append(col)
        r += 1
    return T[:r], piv, T[r:]


def brute_unbounded(A, c):
    """精确判定 min cᵀx（可行域非空时）是否无界：返回一条 cᵀd < 0 的极射线 d，没有则 None。

    极射线 = 有界多面体 {Ad = 0, 1ᵀd = 1, d ≥ 0} 的顶点 = 其基本可行解。先把增广系统化成
    行满秩（秩亏的行直接删掉，A 行相关时也对），再逐个 r 列基精确求解。
    输入按 Fraction(float) 精确转换（本文件的随机数据是整数值浮点，转换无损）。
    """
    m, n = len(A), len(c)
    aug = [[Fraction(v) for v in row] + [Fraction(0)] for row in A] + [[Fraction(1)] * n + [Fraction(1)]]
    rows, _, zero_rows = _rref_exact(aug)
    if any(r[-1] != 0 for r in zero_rows):
        return None                                   # 截面为空 ⇒ 回收锥只有 0
    rk = len(rows)
    cq = [Fraction(v) for v in c]
    for cols in itertools.combinations(range(n), rk):
        sub = [[r[j] for j in cols] + [r[-1]] for r in rows]
        red, piv, _ = _rref_exact(sub)
        if len(piv) < rk:
            continue                                  # 这组列奇异，不是基
        z = [red[i][-1] for i in range(rk)]
        if any(v < 0 for v in z):
            continue
        if sum(cq[j] * v for j, v in zip(cols, z)) < 0:
            d = [Fraction(0)] * n
            for j, v in zip(cols, z):
                d[j] = v
            return d
    return None


def brute_min(A, b, c, tol=1e-9):
    """暴力：枚举所有 m 列组合解方程，取可行且目标最小者。只用于小问题的 oracle。"""
    m, n = len(A), len(c)
    best = None
    for cols in itertools.combinations(range(n), m):
        M = [[A[i][j] for j in cols] + [b[i]] for i in range(m)]
        # 高斯消去
        r = 0
        piv = []
        for col in range(m):
            p = max(range(r, m), key=lambda i: abs(M[i][col]))
            if abs(M[p][col]) <= tol:
                continue
            M[r], M[p] = M[p], M[r]
            pv = M[r][col]
            M[r] = [v / pv for v in M[r]]
            for i in range(m):
                if i != r and abs(M[i][col]) > 0:
                    f = M[i][col]
                    M[i] = [a - f * bb for a, bb in zip(M[i], M[r])]
            piv.append(col)
            r += 1
        if r < m:
            continue
        xs = [0.0] * m
        for i, col in enumerate(piv):
            xs[col] = M[i][-1]
        if any(v < -tol for v in xs):
            continue
        x = [0.0] * n
        for k, col in enumerate(cols):
            x[col] = xs[k]
        obj = sum(ci * xi for ci, xi in zip(c, x))
        if best is None or obj < best[0] - tol:
            best = (obj, x)
    return best


def test_textbook_lp():
    # max 3x + 2y  s.t. x + y + s1 = 4, x + 3y + s2 = 6, x,y,s >= 0  → 最优 (4,0)，值 12
    A = [[1.0, 1.0, 1.0, 0.0], [1.0, 3.0, 0.0, 1.0]]
    b = [4.0, 6.0]
    c = [3.0, 2.0, 0.0, 0.0]
    r = maximize(A, b, c)
    assert r.status == OPTIMAL
    assert r.obj == pytest.approx(12.0, abs=1e-9)
    assert r.x[0] == pytest.approx(4.0, abs=1e-9) and r.x[1] == pytest.approx(0.0, abs=1e-9)


def test_infeasible_is_detected():
    # x = 1 且 x = 2 不可能
    A = [[1.0], [1.0]]
    assert solve(A, [1.0, 2.0], [1.0]).status == INFEASIBLE


def test_unbounded_is_detected():
    # min -x  s.t. x - s = 1, x,s >= 0  → x 可无限大
    A = [[1.0, -1.0]]
    assert solve(A, [1.0], [-1.0, 0.0]).status == UNBOUNDED


def _random_lp(seed):
    rng = random.Random(seed)
    m, n = rng.choice([(2, 5), (3, 6), (2, 6)])
    A = [[scalar_exact(rng.randint(-3, 4)) for _ in range(n)] for _ in range(m)]
    x0 = [scalar_exact(rng.randint(0, 3)) for _ in range(n)]               # 保证可行
    b = [sum(A[i][j] * x0[j] for j in range(n)) for i in range(m)]
    c = [scalar_exact(rng.randint(-3, 4)) for _ in range(n)]
    return A, b, c


# 由 oracle（不是求解器）判定的分类：12 个种子里 7 个无界、5 个有界。
_UNBOUNDED_SEEDS = {1, 3, 4, 5, 7, 8, 9}


@pytest.mark.parametrize("seed", range(12))
def test_against_brute_force_basic_feasible_solutions(seed):
    """随机小 LP，两个分支都有独立 oracle，没有静默返回：

    · 求解器说 UNBOUNDED ⟹ 必须存在 cᵀd < 0 的极射线（Fraction 精确证书）；
    · 求解器说 OPTIMAL ⟹ 必须不存在这样的射线，且最优值 == 枚举全部基本可行解的最小值。
    （旧版在 UNBOUNDED 时直接 return，7/12 个种子什么都不断言；"恒报 UNBOUNDED"的假求解器 12/12 通过。）
    """
    A, b, c = _random_lp(seed)
    m, n = len(A), len(c)
    r = solve(A, b, c)
    ray = brute_unbounded(A, c)
    if r.status == UNBOUNDED:
        assert ray is not None, (seed, "solver says UNBOUNDED but no improving extreme ray exists")
        assert all(sum(Fraction(A[i][j]) * ray[j] for j in range(len(c))) == 0
                   for i in range(len(A)))                           # 证书自检：Ad = 0
        return
    assert ray is None, (seed, "an improving extreme ray exists but solver said", r.status)
    bf = brute_min(A, b, c)
    assert r.status == OPTIMAL, (seed, r.status)
    assert bf is not None, seed
    assert r.obj == pytest.approx(bf[0], abs=1e-7), (seed, r.obj, bf[0])
    for i in range(m):                                               # 解确实可行
        assert sum(A[i][j] * r.x[j] for j in range(n)) == pytest.approx(b[i], abs=1e-7)
    assert all(v > -1e-9 for v in r.x)


def test_random_gate_exercises_both_branches_as_counted():
    """覆盖面如实计数（纪律 C）：上一个门的 12 个种子里，oracle 判 7 个无界、5 个有界——
    两个分支都真的被走到，报告里的"12 组"应写作"5 组对顶点枚举 + 7 组对极射线证书"。"""
    unbounded = {s for s in range(12) if brute_unbounded(*_random_lp(s)[::2]) is not None}
    assert unbounded == _UNBOUNDED_SEEDS
    assert len(unbounded) == 7 and 12 - len(unbounded) == 5


def test_unbounded_oracle_has_teeth():
    """oracle 自身的牙：教科书无界例必须给出射线；c ≥ 0 的有界例必须给不出。"""
    ray = brute_unbounded([[1.0, -1.0]], [-1.0, 0.0])                # min −x, x − s = 1
    assert ray == [Fraction(1, 2), Fraction(1, 2)]
    assert brute_unbounded([[1.0, 1.0, 1.0, 0.0], [1.0, 3.0, 0.0, 1.0]], [0.0, 1.0, 2.0, 0.0]) is None
    # 行相关（第二行 = 2 × 第一行）也必须正确处理：秩亏不许把射线漏掉
    assert brute_unbounded([[1.0, -1.0, 0.0], [2.0, -2.0, 0.0]], [-1.0, 0.0, 0.0]) is not None


@pytest.mark.parametrize("seed", range(12))
def test_weak_and_strong_duality(seed):
    """对偶必须成立：yᵀb == cᵀx（强对偶），且 cⱼ − yᵀA_j ≥ 0（对偶可行）。

    极限分析里对偶解就是破坏机构，所以它的正确性和原问题一样要紧。
    """
    rng = random.Random(100 + seed)
    m, n = 3, 7
    A = [[scalar_exact(rng.randint(-3, 4)) for _ in range(n)] for _ in range(m)]
    x0 = [scalar_exact(rng.randint(0, 3)) for _ in range(n)]
    b = [sum(A[i][j] * x0[j] for j in range(n)) for i in range(m)]
    c = [scalar_exact(rng.randint(0, 4)) for _ in range(n)]                 # c ≥ 0 ⇒ 有下界
    r = solve(A, b, c)
    assert r.status == OPTIMAL, seed
    assert sum(y * bi for y, bi in zip(r.y, b)) == pytest.approx(r.obj, abs=1e-7), seed
    for j in range(n):
        red = c[j] - sum(r.y[i] * A[i][j] for i in range(m))
        assert red > -1e-7, (seed, j, red)


def test_degenerate_problem_terminates():
    """高度退化（多行冗余 + 平局）：Bland 规则必须保证终止，不循环。"""
    A = [[1.0, 1.0, 1.0, 0.0, 0.0],
         [1.0, 1.0, 0.0, 1.0, 0.0],
         [1.0, 1.0, 0.0, 0.0, 1.0],
         [2.0, 2.0, 1.0, 1.0, 0.0]]
    b = [1.0, 1.0, 1.0, 2.0]
    c = [-1.0, -1.0, 0.0, 0.0, 0.0]
    r = solve(A, b, c)
    assert r.status == OPTIMAL
    assert r.obj == pytest.approx(-1.0, abs=1e-9)


def test_redundant_rows_are_tolerated():
    """冗余等式（一行是另一行的倍数）不应判成不可行。"""
    A = [[1.0, 1.0], [2.0, 2.0]]
    r = solve(A, [3.0, 6.0], [1.0, 2.0])
    assert r.status == OPTIMAL
    assert r.obj == pytest.approx(3.0, abs=1e-9)


# ---------------------------------------------------------------- G6（2026-09-24）的 LP 级回归门

def test_tiny_rhs_infeasibility_is_detected_at_any_scale():
    """G6 minor 4：右端项旧实现只在 max b > 1 时归一，max|b| ≲ 1e-10 的不可行系统（x = 1e-11 与 x = 3e-11）
    被判 OPTIMAL。现在右端项双向归一：任何 2 的幂缩放下都必须 INFEASIBLE；同量级的可行系统仍 OPTIMAL、解精确按比例。"""
    for p in (-80, -40, -20, 0, 20, 40):
        s = 2.0 ** p
        assert solve([[1.0], [1.0]], [1e-11 * s, 3e-11 * s], [1.0]).status == INFEASIBLE, p
        r = solve([[1.0], [1.0]], [1e-11 * s, 1e-11 * s], [1.0])
        assert r.status == OPTIMAL and r.x == [1e-11 * s], (p, r.x)


def test_homogeneous_system_is_solved_and_its_ray_certified():
    """b ≡ 0（齐次）单独处理：可行（x = 0）；有改进射线时报 UNBOUNDED，返回的射线由本文件 Fraction 精确核验。"""
    A = [[1.0, -1.0, 0.0], [0.0, 1.0, -1.0]]
    r = solve(A, [0.0, 0.0], [1.0, 1.0, 1.0])
    assert r.status == OPTIMAL and r.obj == 0.0
    r = solve(A, [0.0, 0.0], [-1.0, 0.0, 0.0])
    assert r.status == UNBOUNDED and r.ray is not None
    d = [Fraction(v) for v in r.ray]
    assert all(v >= 0 for v in d) and any(v > 0 for v in d)
    assert all(sum(Fraction(a) * v for a, v in zip(row, d)) == 0 for row in A)
    assert -d[0] < 0


@pytest.mark.parametrize("W", [1.0, 1e6, 1e10, 1e12, 1e15, 1e-12])
def test_objective_magnitude_does_not_hide_an_improving_column(W):
    """G6 critical 19 的 LP 级复现：变量序 (s, α)，max α s.t. s + W·α = W ⇒ α = 1。
    松弛列排在前面，旧实现（Bland）一阶段就停在 {s} 上，二阶段 α 列的目标系数只随列因子缩放（c_α·2^−e ~ 1/W），
    入基检验用绝对 1e-10：W ≳ 1e10 时 α 列永远进不了基，报 OPTIMAL 且 α = 0。"""
    r = maximize([[1.0, W]], [W], [0.0, 1.0])
    assert r.status == OPTIMAL
    assert r.x[1] == pytest.approx(1.0, rel=1e-12), (W, r.x)
    assert r.obj == pytest.approx(1.0, rel=1e-12)
    assert r.y[0] * W == pytest.approx(1.0, rel=1e-12)          # 对偶：y·W ≥ c_α = 1 取等


@pytest.mark.parametrize("seed", range(12))
def test_objective_scaling_by_a_power_of_two_is_bitwise_invariant(seed):
    """c → 2^p·c：目标归一因子是 2 的幂，求解逐位不变——x、基、迭代数相同，y 与最优值逐位乘 2^p。
    （旧实现 p = −40 时约化成本全在绝对阈值以下，直接在初始基上报"最优"。p = −1070 看护目标归一本身：
    入基判据已是相对的，只有到了次正规数的量级（y·A 的舍入是绝对的 2^−1074），不归一才会出错——
    2026-09-24 的变异实验里，去掉目标归一时只有这一格报红。规整因子记成指数、用 ldexp 施加，
    因子本身（如 2^1072）不可表示也不上溢。）"""
    rng = random.Random(100 + seed)
    m, n = 3, 7
    A = [[scalar_exact(rng.randint(-3, 4)) for _ in range(n)] for _ in range(m)]
    x0 = [scalar_exact(rng.randint(0, 3)) for _ in range(n)]
    b = [sum(A[i][j] * x0[j] for j in range(n)) for i in range(m)]
    c = [scalar_exact(rng.randint(0, 4)) for _ in range(n)]
    ref = solve(A, b, c)
    assert ref.status == OPTIMAL
    for p in (-1070, -1000, -60, -40, 40, 1000):           # −1070：c 落进次正规数
        s = 2.0 ** p
        r = solve(A, b, [s * v for v in c])
        assert r.status == OPTIMAL, (seed, p)
        assert r.x == ref.x and r.basis == ref.basis and r.iterations == ref.iterations, (seed, p)
        assert r.y == [s * v for v in ref.y], (seed, p)


def test_beale_cycling_example_reaches_the_optimum():
    """Beale（1955）的经典循环例：Dantzig 规则 + 最小下标平局在精确算术里就会 6 步一周期。
    现在的实现检测到基重复即扰动右端项，必须终止并给出暴力枚举的最优值 −1/20。"""
    A = [[0.25, -60.0, -1.0 / 25.0, 9.0, 1.0, 0.0, 0.0],
         [0.5, -90.0, -1.0 / 50.0, 3.0, 0.0, 1.0, 0.0],
         [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]]
    b = [0.0, 0.0, 1.0]
    c = [-0.75, 150.0, -0.02, 6.0, 0.0, 0.0, 0.0]
    bf = brute_min(A, b, c)
    assert bf is not None and bf[0] == pytest.approx(-0.05, abs=1e-12)
    r = solve(A, b, c)
    assert r.status == OPTIMAL
    assert r.obj == pytest.approx(bf[0], abs=1e-12)
    for j in range(len(c)):
        red = c[j] - sum(r.y[i] * A[i][j] for i in range(len(A)))
        assert red > -1e-9, (j, red)


def test_a_dropped_bounding_row_is_never_reported_as_unbounded(monkeypatch):
    """契约：UNBOUNDED 只在射线经原始 A 核验后才报。牙：把比值检验的两条噪声线都抬到顶（全局线 = max|d|、
    逐分量线 = Σ|B⁻¹_ik||A_ke| ≥ |d_i|，**每一行**都被当成噪声——
    G6 critical 0 里黏聚上限行掉出比值检验的机制推到极端），有界问题仍须 OPTIMAL 且值对：射线核验不过，
    退回最大正元换基（间谍确认这条退路真的被走到）。"""
    import eab.lp as lp

    A = [[1.0, 1.0, 1.0, 0.0], [1.0, 3.0, 0.0, 1.0]]
    b = [4.0, 6.0]
    c = [3.0, 2.0, 0.0, 0.0]
    assert brute_unbounded(A, [-v for v in c]) is None
    assert maximize(A, b, c).obj == pytest.approx(12.0, abs=1e-12)
    calls = []
    real = lp._Revised.ratio

    def spy(self, d, x, dn, *, noise=None):
        calls.append(noise)
        return real(self, d, x, dn, noise=noise)

    monkeypatch.setattr(lp, "_PIV_NOISE", 1.0)
    monkeypatch.setattr(lp, "_PIV_NOISE_GLOBAL", 1.0)
    monkeypatch.setattr(lp._Revised, "ratio", spy)
    r = maximize(A, b, c)
    assert r.status == OPTIMAL and r.obj == pytest.approx(12.0, abs=1e-9)
    assert 0.0 in calls                                    # 退路（noise = 0）被走到


def test_anti_cycling_breaks_the_classic_beale_cycle(monkeypatch):
    """防循环的门（G6 major 2：旧实现 k=128 时 Bland 在浮点下 409 步一周期，与"保证有限步终止"的文档不符）。

    Beale（1955）的例子从松弛基 {x5, x6, x7} 出发、用 Dantzig 入基 + 教科书比值检验（最小比值、平局取最小行号），
    精确算术里 6 步回到原基。这里把 `_Revised.ratio` 换成教科书规则（注入到被测路径内部），
    `optimize` 必须检测到基重复、扰动右端项、撤扰动后用对偶单纯形修复，最终停在最优值 −1/20。
    间谍确认：基序列确实回到过起点（真循环）、对偶单纯形确实被调用。"""
    import eab.lp as lp

    A = [[0.25, -60.0, -1.0 / 25.0, 9.0, 1.0, 0.0, 0.0],
         [0.5, -90.0, -1.0 / 50.0, 3.0, 0.0, 1.0, 0.0],
         [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]]
    b = [0.0, 0.0, 1.0]
    c = [-0.75, 150.0, -0.02, 6.0, 0.0, 0.0, 0.0]

    def textbook_ratio(self, d, x, dn, *, noise=None):
        best, p = None, -1
        for i, di in enumerate(d):
            if di > 1e-12:
                t = max(x[i], 0.0) / di
                if best is None or t < best:
                    best, p = t, i
        return p

    hist, cleanups = [], []
    real_pivot, real_ds = lp._Revised.pivot, lp._Revised.dual_simplex

    def pivot(self, p, e, d):
        real_pivot(self, p, e, d)
        hist.append(tuple(sorted(self.basis)))

    def ds(self, *a, **k):
        cleanups.append(1)
        return real_ds(self, *a, **k)

    monkeypatch.setattr(lp._Revised, "ratio", textbook_ratio)
    monkeypatch.setattr(lp._Revised, "pivot", pivot)
    monkeypatch.setattr(lp._Revised, "dual_simplex", ds)
    S = lp._Revised(A, b, 1000)
    S.basis = [4, 5, 6]
    S.inbasis = [j in (4, 5, 6) for j in range(10)]
    S.reinvert()
    cost = c + [0.0, 0.0, 0.0]
    st, _ = S.optimize(cost, [True] * 7 + [False] * 3, 1e-10, None)
    assert st == OPTIMAL
    assert hist[5] == (4, 5, 6)                            # 第 6 次换基回到起点：真循环
    assert cleanups                                        # 扰动 → 撤扰动 → 对偶单纯形
    x = S.xB(b)
    assert min(x) >= -1e-12
    assert sum(cost[S.basis[i]] * x[i] for i in range(3)) == pytest.approx(-0.05, abs=1e-12)


def test_unbounded_ray_is_verified_against_the_unscaled_matrix():
    """真无界：返回的射线满足 d ≥ 0、Ad = 0（Fraction 精确）、cᵀd < 0；列量级悬殊（1e-8 与 1e8）不影响。"""
    A = [[1e8, -1e-8, 0.0], [0.0, 2.0, -1.0]]
    c = [-1.0, 0.0, 0.0]
    r = solve(A, [1e8, 0.0], c)
    assert r.status == UNBOUNDED and r.ray is not None
    d = r.ray
    assert min(d) >= 0.0
    for row in A:
        assert abs(sum(a * v for a, v in zip(row, d))) <= 1e-12 * sum(abs(a * v) for a, v in zip(row, d))
    assert sum(ci * v for ci, v in zip(c, d)) < 0.0


def test_tiny_objective_coefficients_are_not_ignored():
    """入基判据相对于列自己的量级（|c_j| + Σ|y_i A_ij|），不是绝对阈值：目标系数跨 12 个量级（混合单位）时，
    1e-12 的那一项同样要被最优化。变量序 (s1, s2, x1, x2)，max x1 + 1e-12·x2，x1 + s1 = 1，x2 + s2 = 1
    ⇒ x = (0, 0, 1, 1)。松弛列排在前面，一阶段结束在 {s1, s2} 上，二阶段必须把两列都换进来；
    绝对阈值（目标归一之后 1e-10）会把 x2 的约化成本 −5e-13 当成 0，停在 x2 = 0 的次优基上（核验会抓到，
    但清理用的仍是绝对阈值，只能抛错）。"""
    A = [[1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0]]
    r = maximize(A, [1.0, 1.0], [0.0, 0.0, 1.0, 1e-12])
    assert r.status == OPTIMAL
    assert r.x == [0.0, 0.0, 1.0, 1.0]
    assert r.y == pytest.approx([1.0, 1e-12], rel=1e-12)


def test_a_small_but_genuine_pivot_bounds_the_step():
    """比值检验的阈值相对于入基方向的最大元，且有一层噪声线：一条真正约束步长的行，其元比同列最大元小 11 个量级
    （1e-11，在稳定线 1e-9 之下、噪声线 1e-13 之上）时仍须约束步长。max x s.t. 1e-11·x + s1 = 1、−x + s2 = 0
    ⇒ x = 1e11。旧实现的绝对阈值 1e-10 把第一行漏掉，报 UNBOUNDED（G6 critical 0 在 LP 层的机制）。"""
    A = [[1e-11, 1.0, 0.0], [-1.0, 0.0, 1.0]]
    r = maximize(A, [1.0, 0.0], [1.0, 0.0, 0.0])
    assert r.status == OPTIMAL
    assert r.x[0] == pytest.approx(1e11, rel=1e-12)
