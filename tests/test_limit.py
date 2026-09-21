"""L3 极限分析的门。

三类 oracle，逐层加强：
  1. **解析解**：滑动/倾覆的经典闭式；锯齿节理的 Patton 剪胀律；
  2. **对偶自校验**：静力下限 == 运动上限，机构容许、互补成立；
  3. **跨层交叉验证**：无摩擦互锁块的横向承载比，必须等于 L5 逃逸剖面给出的剪胀比
     ——两条毫不相干的计算路径（静力 LP vs 入口块几何 + 对偶数）。
"""

import sys
from math import atan, tan
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
                                    (0.25, 0.1), (0.25, 0.35)])
def test_interlock_with_friction_reproduces_pattons_law(amp, mu):
    """锯齿节理的 Patton 剪胀律 τ = σ·tan(φ + i)，i = 齿面倾角、tan i = 2·amp。

    引擎没有被告知这条公式——它是平衡方程 + 摩擦锥 + 单边约束的后果。
    """
    r, *_ = _interlock_capacity(amp, mu)
    psi, phi = atan(2.0 * amp), atan(mu)
    assert r.alpha / 100.0 == pytest.approx(tan(psi + phi), abs=1e-9)


def test_interlock_duality_holds_in_three_dimensions():
    r, cts, dead, live, _ = _interlock_capacity(0.25, 0.2)
    d = check_duality(r, cts, dead, live, dim=3, origin=(0.0, 0.0, 0.0), k=16)
    assert d["admissible"] and d["duality_gap"] < 1e-9 and d["complementarity"] < 1e-8


# ---------------------------------------------------------------- 线性化与牙

@pytest.mark.parametrize("k", [4, 6, 8, 12, 16, 24])
def test_three_d_cone_linearisation_is_conservative_and_converges(k):
    """三维摩擦锥用内接棱锥 ⇒ 容许集变小 ⇒ 承载力**偏安全**，且随 k 单调逼近真值。"""
    r, *_ = _interlock_capacity(0.25, 0.2, k=k)
    exact = tan(atan(0.5) + atan(0.2))
    assert r.alpha / 100.0 <= exact + 1e-9
    if k >= 8:
        assert r.alpha / 100.0 > exact - 0.02


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
