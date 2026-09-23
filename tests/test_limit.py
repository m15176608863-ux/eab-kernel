"""L3 极限分析的门。

三类 oracle，逐层加强：
  1. **解析解**：滑动/倾覆的经典闭式；锯齿节理的 Patton 剪胀律；
  2. **对偶自校验**：静力下限 == 运动上限，机构容许、互补成立；
  3. **跨层交叉验证**：无摩擦互锁块的横向承载比，必须等于 L5 逃逸剖面给出的剪胀比
     ——两条毫不相干的计算路径（静力 LP vs 入口块几何 + 对偶数）。
"""

import sys
from math import atan, cos, pi, sin, tan
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from osteomorphic import interlocking_pair  # noqa: E402
from tia_sensitivity import sensitivity_at  # noqa: E402

from eab.kernel3d.covers3 import enumerate_covers3  # noqa: E402
from eab.limit import (LimitContact, check_duality, contacts_from_covers,  # noqa: E402
                       friction_generators, limit_load, mechanism_is_admissible, wrench)

W, BW, BH = 10.0, 2.0, 3.0            # 自重、宽、高；倾覆/滑动分界在 mu = BW/(2*BH) = 1/3


def _block_on_ground(mu):
    cts = [LimitContact((-BW / 2, 0.0), (0.0, 1.0), mu, label=("L",)),
           LimitContact((BW / 2, 0.0), (0.0, 1.0), mu, label=("R",))]
    dead = wrench((0.0, -W), (0.0, BH / 2), (0.0, 0.0), 2)
    live = wrench((1.0, 0.0), (0.0, BH), (0.0, 0.0), 2)
    return cts, dead, live


# ---------------------------------------------------------------- 解析解

@pytest.mark.parametrize("mu", [0.05, 0.1, 0.2, 0.3, 1 / 3, 0.4, 0.5, 0.8, 2.0])
def test_slide_versus_topple_matches_the_closed_form(mu):
    """经典算例：α* = min(μW, W·w/(2h))。摩擦大到一定程度后倾覆接管，值不再增长。"""
    cts, dead, live = _block_on_ground(mu)
    r = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0))
    assert r.status == "optimal"
    assert r.alpha == pytest.approx(min(mu * W, W * BW / (2 * BH)), abs=1e-9)


@pytest.mark.parametrize("mu,topples", [(0.1, False), (0.3, False), (0.4, True), (0.9, True)])
def test_the_failure_mode_is_read_off_the_dual(mu, topples):
    """破坏模式由对偶解（机构）判定：滑动是平动（ω=0，两角都受力），倾覆是绕趾转动。"""
    cts, dead, live = _block_on_ground(mu)
    r = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0))
    vx, vy, omega = r.mechanism
    if topples:
        assert abs(omega) > 1e-6
        assert r.active == [("R",)]                       # 只剩右趾支承
        # 绕右趾 (w/2, 0) 转动 ⇒ 该点速度为零。
        # 二维旋量在点 p 的速度是 (vx − ω·p_y, vy + ω·p_x)——符号别写反（我写反过一次）。
        v_toe = (vx - omega * 0.0, vy + omega * (BW / 2))
        assert abs(v_toe[0]) < 1e-9 and abs(v_toe[1]) < 1e-9
    else:
        assert abs(omega) < 1e-9
        assert r.active == [("L",), ("R",)]
        assert vy == pytest.approx(mu * vx, abs=1e-9)     # 关联流动：剪胀角 = 摩擦角


@pytest.mark.parametrize("mu", [0.05, 0.2, 1 / 3, 0.5, 1.2])
def test_lower_and_upper_bounds_coincide(mu):
    """这一层的自校验结构：静力下限 == 运动上限，且机构容许、互补成立。"""
    cts, dead, live = _block_on_ground(mu)
    r = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0))
    d = check_duality(r, cts, dead, live, dim=2, origin=(0.0, 0.0))
    assert d["admissible"] and d["worst_power"] > -1e-9
    assert d["duality_gap"] < 1e-9
    assert d["complementarity"] < 1e-9
    assert d["drive"] > 1.0 - 1e-9
    assert mechanism_is_admissible(r.mechanism, cts, dim=2, origin=(0.0, 0.0))


def test_zero_friction_block_cannot_take_any_lateral_load():
    cts, dead, live = _block_on_ground(0.0)
    r = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0))
    assert r.alpha == pytest.approx(0.0, abs=1e-12)


def test_cohesion_carries_lateral_load_without_normal_force():
    """黏聚力是与法向压力无关的抗剪：两个接触各 c·A，总承载 2cA。"""
    cts = [LimitContact((-BW / 2, 0.0), (0.0, 1.0), 0.0, cohesion=3.0, area=1.0, label=("L",)),
           LimitContact((BW / 2, 0.0), (0.0, 1.0), 0.0, cohesion=3.0, area=1.0, label=("R",))]
    dead = wrench((0.0, -W), (0.0, 0.0), (0.0, 0.0), 2)      # 荷载作用在基面上，排除倾覆
    live = wrench((1.0, 0.0), (0.0, 0.0), (0.0, 0.0), 2)
    r = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0))
    assert r.alpha == pytest.approx(6.0, abs=1e-9)


# ---------------------------------------------------------------- 互锁块：跨层交叉验证

def _interlock_capacity(amp, mu, k=16, N=100.0):
    A, L = interlocking_pair(nx=4, ny=2, amp=amp)
    cv = [c for c in enumerate_covers3(A, L, window=1e-6, tol=1e-9)
          if c.in_extent and c.normal]
    cts = contacts_from_covers(cv, mu=mu)
    c0 = A.centroid()
    dead = wrench((0.0, 0.0, -N), c0, (0.0, 0.0, 0.0), 3)
    live = wrench((1.0, 0.0, 0.0), c0, (0.0, 0.0, 0.0), 3)
    r = limit_load(cts, dead, live, dim=3, origin=(0.0, 0.0, 0.0), k=k)
    return r, cts, dead, live, N


@pytest.mark.parametrize("amp", [0.10, 0.20, 0.25, 0.30])
def test_frictionless_interlock_capacity_equals_the_dilatancy_ratio(amp):
    """**跨层交叉验证**：静力极限分析给出的横向承载比，必须等于 L5 由入口块几何 +
    对偶数算出的剪胀比 tanψ = 2·amp。两条计算路径毫无共用代码。
    """
    r, *_ = _interlock_capacity(amp, 0.0)
    assert r.status == "optimal"
    assert r.alpha / 100.0 == pytest.approx(2.0 * amp, abs=1e-9)
    assert sensitivity_at(0.30, amp=amp)["tan_psi"] == pytest.approx(2.0 * amp, abs=1e-9)


@pytest.mark.parametrize("amp,mu", [(0.10, 0.2), (0.20, 0.2), (0.25, 0.2), (0.30, 0.2),
                                    (0.25, 0.1), (0.25, 0.35),
                                    (0.20, 0.1), (0.30, 0.1)])       # 审查 C0：这两格曾假不可行
def test_interlock_with_friction_reproduces_pattons_law(amp, mu):
    """锯齿节理的 Patton 剪胀律 τ = σ·tan(φ + i)，i = 齿面倾角、tan i = 2·amp。

    引擎没有被告知这条公式——它是平衡方程 + 摩擦锥 + 单边约束的后果。
    全格扫描（amp × μ × k）见 test_limit_scale.py。
    """
    r, *_ = _interlock_capacity(amp, mu)
    psi, phi = atan(2.0 * amp), atan(mu)
    assert r.status == "optimal", (amp, mu, r.status)
    assert r.alpha / 100.0 == pytest.approx(tan(psi + phi), abs=1e-9)


def test_interlock_duality_holds_in_three_dimensions():
    r, cts, dead, live, _ = _interlock_capacity(0.25, 0.2)
    d = check_duality(r, cts, dead, live, dim=3, origin=(0.0, 0.0, 0.0), k=16)
    assert d["admissible"] and d["duality_gap"] < 1e-9 and d["complementarity"] < 1e-8


# ---------------------------------------------------------------- 线性化与牙

_LIN_AMP, _LIN_MU = 0.25, 0.2
_LIN_EXACT = tan(atan(2.0 * _LIN_AMP) + atan(_LIN_MU))


@pytest.mark.parametrize("k", [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 22, 24])
def test_three_d_cone_linearisation_is_conservative_within_the_inradius_bound(k):
    """三维摩擦锥用内接 k 棱锥 ⇒ 容许集变小 ⇒ 承载力**偏安全**（≤ 精确值）。

    量化（解析 oracle，不看代码的切向基架）：正 k 边形的内切圆半径是外接圆的 cos(π/k) 倍，
    所以内接棱锥 ⊇ 摩擦系数 μ·cos(π/k) 的精确圆锥 ⇒ 承载比 ≥ tan(ψ + atan(μ·cos(π/k)))，
    相对短缺 ≤ 1 − cos(π/k)（k → ∞ 时 → 0：这就是"收敛"的全部含义，**不是单调**）。
    k 序列必须含非 4 的倍数：本几何在 4|k 时恰好精确（见下一个门），只测 4 的倍数的门没有牙。
    k = 7 在未修的 LP 阈值下曾假不可行（审查 C21）。
    """
    r, *_ = _interlock_capacity(_LIN_AMP, _LIN_MU, k=k)
    assert r.status == "optimal", (k, r.status)
    ratio = r.alpha / 100.0
    assert ratio <= _LIN_EXACT + 1e-9
    assert (_LIN_EXACT - ratio) / _LIN_EXACT <= (1.0 - cos(pi / k)) + 1e-9
    assert ratio >= tan(atan(2.0 * _LIN_AMP) + atan(_LIN_MU * cos(pi / k))) - 1e-9


def test_three_d_cone_error_depends_on_frame_alignment_not_monotone_in_k():
    """误差由滑动方向相对 `_tangents` 切向基架的夹角决定，**不随 k 单调**。

    本几何的齿面法向在 x-z 平面，`_tangents` 给出 t1 = −ŷ、t2 在 x-z 平面（即荷载平面）内，
    棱角 2πj/k 在 4|k 时恰有一条落在 ±t2 上 ⇒ 4|k 精确；k=5 反而明显变差（承载比短缺 ≈ 0.045，非单调的见证）。
    包络仍随 k 收紧：k ∈ {14, 18, 22} 的最大误差小于 k ∈ {5, 6} 的最小误差。
    """
    from eab.limit import _tangents                   # 只用来钉住上面那句关于基架的陈述

    _, cts, *_ = _interlock_capacity(_LIN_AMP, _LIN_MU, k=16)
    tooth = [ct.normal for ct in cts if abs(ct.normal[0]) > 1e-6]
    assert tooth and all(abs(n[1]) < 1e-12 for n in tooth)          # 齿面法向在 x-z 平面
    for n in tooth:
        t1, t2 = _tangents(n, 3)
        assert t1 == pytest.approx((0.0, -1.0, 0.0), abs=1e-12) and abs(t2[1]) < 1e-12
    err = {}
    for k in (4, 5, 6, 8, 12, 14, 16, 18, 22):
        r, *_ = _interlock_capacity(_LIN_AMP, _LIN_MU, k=k)
        assert r.status == "optimal", (k, r.status)
        err[k] = _LIN_EXACT - r.alpha / 100.0
    for k in (4, 8, 12, 16):
        assert abs(err[k]) < 1e-9, (k, err[k])
    assert err[5] > err[4] + 1e-3                     # 4 → 5 变差：不单调
    assert 0.04 < err[5] < 0.05
    assert max(err[k] for k in (14, 18, 22)) < min(err[k] for k in (5, 6))


def _flat_block_ratio(k, theta, *, mu=0.5, s=1.0, g=1.0):
    """三维扁块：四个角点接触，法向 +z；横向荷载在基面内沿方向 u = (cos θ, sin θ, 0)、过原点 ⇒ 无倾覆力矩。

    精确锥下承载力 = μW（与 θ 无关）。k 棱锥下：各接触切向力 ∈ N_i·P（P = 外接圆半径 μ 的正 k 边形），
    ΣN_i = W，切向合力 = α·u ⇒ α·u ∈ W·P（凸）⇒ α ≤ W·ρ_P(u)（P 沿 u 的径向函数）；
    取 N_i = W/4、每个接触都取 ρ_P(u)·u，扭矩因角点关于原点对称而为零 ⇒ 上界可达。
    ρ_P(u) = μ·cos(π/k)/cos(δ)，δ = u 与最近边法向的夹角 ∈ [0, π/k] ⇒ 比值 ∈ [cos(π/k), 1]：
    u 正对边法向（两棱正中）时取下界，正对棱时取上界。上下界都与切向基架无关。
    """
    W = 10.0 * s
    hx, hy = 1.0 * g, 0.6 * g                            # 非正方形底面：一般位置
    cts = [LimitContact((sx * hx, sy * hy, 0.0), (0.0, 0.0, 1.0), mu)
           for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    o = (0.0, 0.0, 0.0)
    dead = wrench((0.0, 0.0, -W), (0.0, 0.0, 0.7 * g), o, 3)
    live = wrench((cos(theta), sin(theta), 0.0), o, o, 3)
    r = limit_load(cts, dead, live, dim=3, origin=o, k=k)
    assert r.status == "optimal", (k, theta, s, g, r.status)
    return r.alpha / (mu * W)


@pytest.mark.parametrize("s,g", [(1.0, 1.0), (1e2, 1.0), (1e4, 1e-3)])
@pytest.mark.parametrize("k", [4, 5, 7, 8, 12])
def test_three_d_cone_bound_is_tight_for_loads_in_every_direction(k, s, g):
    """一般位置荷载（θ 取 181 个方向，与任何棱扇都不对齐）：承载比处处 ∈ [cos(π/k), 1]，
    且两端都被取到（采样分辨率 π/181 内）——下界 1 − cos(π/k) 是**紧**的（荷载平分两棱时），
    上界 1 在荷载对准棱时取到。平面内荷载的互锁算例测不到面外母线的错误，这个门测得到。
    """
    n = 181
    ratios = [_flat_block_ratio(k, 2.0 * pi * i / n, s=s, g=g) for i in range(n)]
    lo, hi = cos(pi / k), 1.0
    assert min(ratios) >= lo - 1e-9, (k, min(ratios))
    assert max(ratios) <= hi + 1e-9, (k, max(ratios))
    # 采样间距 2π/n ⇒ 离任一边法向 / 任一棱都至多 π/n；代入 ρ = cos(π/k)/cos(δ)：
    assert min(ratios) <= lo / cos(pi / n) + 1e-9, (k, min(ratios), lo)
    assert max(ratios) >= lo / cos(pi / k - pi / n) - 1e-9, (k, max(ratios))


def test_two_d_cone_is_exact_two_generators():
    g = friction_generators((0.0, 1.0), 0.3, 2)
    assert len(g) == 2
    assert g[0] == pytest.approx((-0.3, 1.0)) and g[1] == pytest.approx((0.3, 1.0))


def test_gate_has_teeth_flipping_a_normal_changes_the_answer():
    cts, dead, live = _block_on_ground(0.5)
    good = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0)).alpha
    cts[1] = LimitContact(cts[1].point, (0.0, -1.0), 0.5, label=("R",))    # 法向反号
    bad = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0))
    assert bad.status != "optimal" or abs(bad.alpha - good) > 1e-3


def test_gate_has_teeth_removing_a_contact_changes_the_answer():
    cts, dead, live = _block_on_ground(0.2)
    good = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0)).alpha
    bad = limit_load(cts[:1], dead, live, dim=2, origin=(0.0, 0.0))
    assert bad.status != "optimal" or abs(bad.alpha - good) > 1e-3
