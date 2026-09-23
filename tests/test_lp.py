"""单纯形内核的门。独立 oracle（都不调用 lp.py）：

  · 有界时：**枚举全部基本可行解**（小问题上的暴力真值，本文件自带的浮点高斯消去）；
  · 无界时：**回收锥极射线证书**（`brute_unbounded`，fractions.Fraction 精确算）。
    可行域非空时，min cᵀx 无界 ⟺ 回收锥 {d : Ad = 0, d ≥ 0} 里有 cᵀd < 0 的方向
    ⟺ 截面 {Ad = 0, Σd = 1, d ≥ 0}（有界多面体）的某个顶点——即某条极射线——满足 cᵀd < 0。
    顶点 = 该增广系统的基本可行解，逐个 (m+1) 列基用有理数精确解出。
"""

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
    A = [[float(rng.randint(-3, 4)) for _ in range(n)] for _ in range(m)]
    x0 = [float(rng.randint(0, 3)) for _ in range(n)]               # 保证可行
    b = [sum(A[i][j] * x0[j] for j in range(n)) for i in range(m)]
    c = [float(rng.randint(-3, 4)) for _ in range(n)]
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
    A = [[float(rng.randint(-3, 4)) for _ in range(n)] for _ in range(m)]
    x0 = [float(rng.randint(0, 3)) for _ in range(n)]
    b = [sum(A[i][j] * x0[j] for j in range(n)) for i in range(m)]
    c = [float(rng.randint(0, 4)) for _ in range(n)]                 # c ≥ 0 ⇒ 有下界
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
