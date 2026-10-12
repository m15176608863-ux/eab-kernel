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


@pytest.mark.parametrize("wy,wx", [(2, 3), (3, 2), (1, 4)])
def test_atan2_width_mismatch_is_an_error(wy, wx):
    """atan2 与 `_pair` 同一纪律：两个对偶操作数宽度不同必须报错，不许 zip 静默截断。

    审查实测（2026-09-21）：atan2(seed(1,2,0), seed(1,3,2)) 返回 2 通道结果，x 在第 2 通道的
    种子被静默丢掉。宽度两个方向都测（y 宽 / x 宽），外加 1 对 4 的悬殊情形。
    """
    with pytest.raises(ValueError):
        atan2(Dual.seed(1.0, wy, 0), Dual.seed(1.0, wx, wx - 1))


@pytest.mark.parametrize("y,x", [(1.3, 2.0), (-0.7, -3.1), (1e-6, 1e-6), (4e3, -2e3)])
def test_atan2_equal_width_matches_the_closed_form_partials(y, x):
    """宽度一致时照常工作：∂atan2/∂y = x/(x²+y²)，∂/∂x = −y/(x²+y²)（一般位置、第三象限、尺度 1e-6 与 1e3）。"""
    r = atan2(Dual.seed(y, 2, 0), Dual.seed(x, 2, 1))
    den = x * x + y * y
    assert r.v == math.atan2(y, x)
    assert r.e[0] == pytest.approx(x / den, rel=1e-12)
    assert r.e[1] == pytest.approx(-y / den, rel=1e-12)


@pytest.mark.parametrize("base,p", [(-2.0, 0.5), (-1e-300, 0.5), (-1e6, 1.5), (-3.0, -0.25)])
def test_pow_of_a_negative_base_to_a_fractional_power_is_an_error(base, p):
    """负底非整数幂在实数里无定义；float.__pow__ 会给复数并静默流进后续对偶运算——必须当场报错。

    分界点（−1e-300）、一般位置（−2 的 0.5 次）、尺度（−1e6 的 1.5 次）、负分数指数各一格。
    """
    with pytest.raises(ValueError):
        Dual.seed(base, 1, 0) ** p


@pytest.mark.parametrize("base,p", [(-2.0, 3), (-2.0, 2.0), (-1e3, 2), (2.0, 0.5), (1e-300, 1.0)])
def test_pow_stays_legal_and_real_where_it_is_defined(base, p):
    """整数幂（含写成 2.0 的整数）对负底合法，正底的分数幂合法；值与导数都必须是实数且等于闭式。"""
    r = Dual.seed(base, 1, 0) ** p
    assert isinstance(r.v, float) and isinstance(r.e[0], float)
    assert r.v == pytest.approx(base ** p, rel=1e-15)
    assert r.e[0] == pytest.approx(p * base ** (p - 1), rel=1e-15)


# ---------------------------------------------------------------- float 协议：必然报错，不许静默丢导数

@pytest.mark.parametrize("fn", [math.sin, math.cos, math.sqrt, math.exp, float])
def test_implicit_float_conversion_of_a_dual_is_a_type_error(fn):
    """`Dual.__float__` 曾让 math.sin(Dual) 静默返回 float（导数通道被清零、primal 逐位不变，
    任何值门都抓不到）。现在它必须 TypeError；择支请显式用 val()。"""
    with pytest.raises(TypeError):
        fn(Dual.seed(0.4, 1, 0))


def test_percent_formatting_of_a_dual_is_a_type_error():
    with pytest.raises(TypeError):
        "%.3f" % Dual.seed(0.4, 1, 0)


def test_val_and_comparisons_still_work_without_float_protocol():
    """删掉隐式 float 之后，择支的合法通道（val、比较、is_exact_zero、与 float 混算）不受影响。"""
    x = Dual.seed(0.4, 2, 1)
    assert val(x) == 0.4
    assert x < 1.0 and x > 0 and x <= 0.4 and x >= Dual.const(0.4, 2)
    assert not is_exact_zero(x)
    y = 2.0 * x + 1
    assert y.v == pytest.approx(1.8) and y.e == (0.0, 2.0)
    s = sin(x)
    assert s.v == math.sin(0.4) and s.e[1] == pytest.approx(math.cos(0.4))


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
