"""单纯形内核的门。独立 oracle = **枚举全部基本可行解**（小问题上的暴力真值）。"""

import itertools
import random

import pytest

from eab.lp import INFEASIBLE, OPTIMAL, UNBOUNDED, maximize, solve


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


@pytest.mark.parametrize("seed", range(12))
def test_against_brute_force_basic_feasible_solutions(seed):
    """随机小 LP：单纯形的最优值必须等于枚举全部基本可行解的最小值。"""
    rng = random.Random(seed)
    m, n = rng.choice([(2, 5), (3, 6), (2, 6)])
    A = [[float(rng.randint(-3, 4)) for _ in range(n)] for _ in range(m)]
    x0 = [float(rng.randint(0, 3)) for _ in range(n)]               # 保证可行
    b = [sum(A[i][j] * x0[j] for j in range(n)) for i in range(m)]
    c = [float(rng.randint(-3, 4)) for _ in range(n)]
    r = solve(A, b, c)
    bf = brute_min(A, b, c)
    if r.status == UNBOUNDED:
        return                                                       # 枚举顶点判不了无界
    assert r.status == OPTIMAL, (seed, r.status)
    assert bf is not None, seed
    assert r.obj == pytest.approx(bf[0], abs=1e-7), (seed, r.obj, bf[0])
    for i in range(m):                                               # 解确实可行
        assert sum(A[i][j] * r.x[j] for j in range(n)) == pytest.approx(b[i], abs=1e-7)
    assert all(v > -1e-9 for v in r.x)


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
