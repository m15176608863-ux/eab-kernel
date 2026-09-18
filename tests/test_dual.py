"""对偶数内核的门。纪律条款各有一个专门的测试看着。"""

import math

import pytest

from eab.dual import (Dual, atan2, central_difference, convergence_order, cos, grad,
                      is_exact_zero, seeded, sin, sqrt, val)


def test_arithmetic_matches_analytic_derivatives():
    x = Dual.seed(2.0, 2, 0)
    y = Dual.seed(3.0, 2, 1)
    f = x * y + x * x / y - 5.0 * y
    assert abs(f.v - (6.0 + 4.0 / 3.0 - 15.0)) < 1e-12
    # ∂f/∂x = y + 2x/y ; ∂f/∂y = x − x²/y² − 5
    assert abs(f.e[0] - (3.0 + 4.0 / 3.0)) < 1e-12
    assert abs(f.e[1] - (2.0 - 4.0 / 9.0 - 5.0)) < 1e-12


def test_transcendentals():
    x = Dual.seed(0.7, 1, 0)
    assert abs(sin(x).e[0] - math.cos(0.7)) < 1e-12
    assert abs(cos(x).e[0] + math.sin(0.7)) < 1e-12
    assert abs(sqrt(x).e[0] - 0.5 / math.sqrt(0.7)) < 1e-12
    y = Dual.seed(1.3, 1, 0)
    # d/dx atan2(x, c) = c/(x²+c²)
    assert abs(atan2(y, 2.0).e[0] - 2.0 / (1.3 ** 2 + 4.0)) < 1e-12


def test_is_exact_zero_is_the_only_legal_skip_criterion():
    """值为零但导数非零 —— 只看 primal 会静默丢掉这一整条导数通道。"""
    x = Dual(0.0, (1.0, 0.0))
    assert val(x) == 0.0
    assert not is_exact_zero(x)                 # 正确判据：不许跳过
    assert is_exact_zero(Dual(0.0, (0.0, 0.0)))
    assert is_exact_zero(0.0) and not is_exact_zero(1.0)


def test_val_only_branches_do_not_leak_into_arithmetic():
    a, b = Dual.seed(1.0, 1, 0), Dual.const(2.0, 1)
    assert (a < b) and (b > a)                  # 比较只看 primal
    picked = a if val(a) < val(b) else b        # 择支
    assert picked.e[0] == 1.0                   # 被选中的分支保留导数


def test_width_mismatch_is_an_error():
    with pytest.raises(ValueError):
        Dual.seed(1.0, 2, 0) + Dual.seed(1.0, 3, 0)


def test_convergence_order_criterion_on_a_nonlinear_function():
    """梯度正确性的判据是**收敛阶**（V 形 + 大端 O(h²)），不是某个 h 上的一致。"""
    def f(theta):
        return math.sin(theta[0]) * math.exp(theta[1])

    th = [0.6, 0.3]
    xs = seeded(th)
    analytic = list((sin(xs[0]) * Dual(math.exp(0.3), (0.0, math.exp(0.3)))).e)
    rep = convergence_order(f, th, analytic, hs=(1e-1, 5e-2, 2.5e-2, 1e-3, 1e-5, 1e-6))
    assert rep["large_h_order"] == pytest.approx(2.0, abs=0.15)   # 大端 O(h²)
    assert rep["errors"][1e-1] / rep["errors"][2.5e-2] == pytest.approx(16.0, rel=0.05)
    assert rep["valley_error"] < 1e-9                              # 谷底贴到机器精度


def test_central_difference_helper():
    def f(t):
        return t[0] ** 3
    assert central_difference(f, [2.0], 1e-4)[0] == pytest.approx(12.0, abs=1e-6)
