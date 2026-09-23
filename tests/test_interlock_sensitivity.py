"""互锁力学量（逃逸高度、剪胀比）与 TIA 解析灵敏度的门。

两道 oracle：
  · 逃逸高度 —— 对暴力相交谓词二分（不可微，纯真值）；
  · 解析梯度 —— 中心差分 + 收敛阶（对非线性参数）。
"""

import functools
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from osteomorphic import interlocking_pair, interlocking_pair_generic  # noqa: E402
from tia_sensitivity import freeze_cover, profile, sensitivity_at  # noqa: E402
from test_interlock_escape import analytic_escape_height  # noqa: E402

from eab import dual as D  # noqa: E402
from eab.dual import Dual, central_difference, convergence_order, val  # noqa: E402
from eab.kernel3d.interlock import (escape_candidates, escape_height_brute,  # noqa: E402
                                    escape_height_covers, escape_height_from_frozen_cover,
                                    frozen_ee_sign)

DELTAS = [0.0, 0.05, 0.15, 0.25, 0.35, 0.45, 0.5, 0.6, 0.75, 0.9, 1.0]


@pytest.mark.parametrize("delta", DELTAS)
def test_escape_height_covers_matches_brute_force(delta):
    """盖提供完备候选集 + 谓词裁决，必须逐点等于二分真值。"""
    A, L = interlocking_pair(nx=4, ny=2, amp=0.25)
    off = (delta, 0.0, 0.0)
    sol = escape_height_covers(A, L, off)
    truth = escape_height_brute(A, L, off, hi=2.0, tol=1e-11)
    assert abs(sol.height - truth) < 1e-9, (sol.height, truth)


def test_candidate_set_contains_the_true_escape_height():
    """完备性：真值必在盖给出的候选集中 —— 这是盖系统的核心价值（G4 的结论）。"""
    A, L = interlocking_pair(nx=4, ny=2, amp=0.25)
    for delta in (0.1, 0.3, 0.45, 0.7):
        off = (delta, 0.0, 0.0)
        truth = escape_height_brute(A, L, off, hi=2.0, tol=1e-11)
        cands = [z for z, _ in escape_candidates(A, L, off)]
        assert any(abs(z - truth) < 1e-9 for z in cands), (delta, truth, cands[:6])


@functools.lru_cache(maxsize=None)
def _default_profile():
    """默认剖面（nx=4, amp=0.25, phase=0, δ=0.05..0.95）只算一次，供下面几道门共用。"""
    return tuple(profile())


def test_escape_profile_is_a_symmetric_ramp_with_peak_at_amplitude():
    rows = _default_profile()
    peak = max(rows, key=lambda r: r["h"])
    assert abs(peak["h"] - 0.25) < 1e-12 and abs(peak["delta"] - 0.5) < 1e-12
    for r in rows:
        assert abs(abs(r["tan_psi"]) - 0.5) < 1e-9            # 坡度恒定的锯齿剖面
    assert all(r["tan_psi"] > 0 for r in rows if r["delta"] < 0.5)
    assert all(r["tan_psi"] < 0 for r in rows if r["delta"] > 0.5)
    # 峰值行是折点：两侧斜率 ±0.5，工具必须把它标成 δ 方向不可微，而不是只报一侧
    (top,) = [r for r in rows if abs(r["delta"] - 0.5) < 1e-12]
    assert top["differentiable_by"]["tan_psi"] is False
    assert top["derivative_range"]["tan_psi"] == pytest.approx((-0.5, 0.5), abs=1e-9)


# ---------------------------------------------------------------- 不可微点必须被标出来（审查 C13）

def _analytic_one_sided(delta, *, nx=4, amp=0.25, phase=0.0, eps=1e-7):
    """解析逃逸高度（与盖路径零共用，见 tests/test_interlock_escape.py）的单侧差商：
    {tan_psi, dh_damp, dh_dphase} → (左, 右)。ε=1e-7：截断误差 ~ε·|h''| ≲ 1e-7，舍入 ~1e-9。"""
    def H(d, a, p):
        return analytic_escape_height(d, 0.0, nx=nx, amp=a, phase=p)
    th = [delta, amp, phase]
    h0 = H(*th)
    out = {}
    for name, k in (("tan_psi", 0), ("dh_damp", 1), ("dh_dphase", 2)):
        tp, tm = list(th), list(th)
        tp[k] += eps
        tm[k] -= eps
        out[name] = ((h0 - H(*tm)) / eps, (H(*tp) - h0) / eps)
    return out


def test_phase_derivative_at_phase_zero_is_flagged_on_every_default_row():
    """默认剖面 phase=0：h(δ, φ) 关于 φ 是偶函数、在 0 处 V 形（h(+φ)=h(−φ)>h(0)），∂h/∂phase 不存在。
    旧工具在每一行报一个裸数 +0.5δ（并列盖里恰被选中那支的单侧值）。现在每行必须 differentiable=False，
    且报出的区间 = 解析 oracle 的两个单侧差商 (−0.5δ, +0.5δ)。"""
    rows = _default_profile()
    assert len(rows) == 19
    for r in rows:
        left, right = _analytic_one_sided(r["delta"])["dh_dphase"]
        assert right > 1e-3 and abs(left + right) < 1e-6, (r["delta"], left, right)   # V 形前提
        assert r["differentiable"] is False, r
        assert r["differentiable_by"]["dh_dphase"] is False, r
        lo, hi = r["derivative_range"]["dh_dphase"]
        assert abs(lo - left) < 1e-6 and abs(hi - right) < 1e-6, (r["delta"], lo, hi, left, right)


def test_phase_evenness_premise_holds_for_the_brute_force_oracle():
    """V 形前提对暴力二分也成立（不只是解析 oracle 的性质）：h(δ,±φ) 相等且大于 h(δ,0)。"""
    delta, phi = 0.30, 0.02
    hs = []
    for ph in (phi, -phi, 0.0):
        A, L = interlocking_pair(nx=4, ny=2, amp=0.25, phase=ph)
        hs.append(escape_height_brute(A, L, (delta, 0.0, 0.0), hi=2.0, tol=1e-11))
    assert abs(hs[0] - hs[1]) < 1e-9 and hs[0] > hs[2] + 1e-3, hs


def test_generic_point_is_differentiable_and_matches_central_differences():
    """一般位置（phase=0.4, δ=0.3）：三个通道都可微，AD 与解析 oracle 的中心差分一致，
    也与 float 路径（盖 + 谓词）的中心差分一致。"""
    r = sensitivity_at(0.30, phase=0.4)
    assert r["differentiable"] is True and all(r["differentiable_by"].values()), r
    orc = _analytic_one_sided(0.30, phase=0.4)
    for name in ("tan_psi", "dh_damp", "dh_dphase"):
        left, right = orc[name]
        assert abs(r[name] - 0.5 * (left + right)) < 1e-6, (name, r[name], left, right)
        assert r["derivative_range"][name][1] - r["derivative_range"][name][0] <= 1e-9

    def h_float(phase):
        A, L = interlocking_pair(nx=4, ny=2, amp=0.25, phase=phase)
        return escape_height_covers(A, L, (0.30, 0.0, 0.0)).height

    cd = (h_float(0.4 + 1e-5) - h_float(0.4 - 1e-5)) / 2e-5
    assert abs(r["dh_dphase"] - cd) < 1e-6, (r["dh_dphase"], cd)


@pytest.mark.parametrize("nx,amp,phase,delta", [
    (5, 0.3, 1.0, 0.07), (5, 0.3, 1.0, 0.29), (5, 0.3, 1.0, 0.4), (5, 0.3, 1.0, 0.55),
    (5, 0.3, 1.0, 0.8), (5, 0.3, 1.0, 0.83),              # 非对称块；0.4 / 0.8 是网格折点
    (4, 0.25, 0.4, 0.5),                                   # 一般相位下的峰值折点
    (5, 3e-3, 1.0, 0.29), (5, 3e-3, 1.0, 0.4),            # 幅值尺度 ×1e-2
])
def test_differentiability_flag_agrees_with_one_sided_quotients(nx, amp, phase, delta):
    """标志与区间逐通道对照解析 oracle：两个单侧差商相等 ⟺ differentiable_by 为真；区间 = {左, 右}。"""
    r = sensitivity_at(delta, nx=nx, ny=2, amp=amp, phase=phase)
    orc = _analytic_one_sided(delta, nx=nx, amp=amp, phase=phase)
    for name, (left, right) in orc.items():
        smooth = abs(left - right) < 1e-5 * max(1.0, abs(right))
        assert r["differentiable_by"][name] is smooth, (name, left, right, r["derivative_range"][name])
        lo, hi = r["derivative_range"][name]
        assert abs(lo - min(left, right)) < 1e-5, (name, lo, hi, left, right)
        assert abs(hi - max(left, right)) < 1e-5, (name, lo, hi, left, right)
    assert r["differentiable"] is all(r["differentiable_by"].values())


def test_dilatancy_ratio_equals_twice_amplitude_closed_form():
    """该块型的闭式设计关系：tanψ = 2·amp（lx=2, nx=4 时坡长 lx/4 = 0.5）。"""
    for amp in (0.10, 0.15, 0.20, 0.25, 0.30):
        r = sensitivity_at(0.30, amp=amp)
        assert abs(r["tan_psi"] - 2.0 * amp) < 1e-9, (amp, r["tan_psi"])
        assert abs(r["dh_damp"] - 0.6) < 1e-9                  # ∂h/∂amp = 2δ，与 amp 无关


@pytest.mark.parametrize("delta", [0.05, 0.20, 0.30, 0.45])
def test_dh_damp_is_two_delta_on_the_rising_branch(delta):
    r = sensitivity_at(delta, amp=0.25)
    assert abs(r["dh_damp"] - 2.0 * delta) < 1e-9


def test_dual_path_value_matches_float_path():
    for r in _default_profile():
        assert abs(r["h"] - r["h_float"]) < 1e-12


def test_g3_gradient_vs_central_difference_with_convergence_order():
    """G3：对**非线性**参数（phase 经 sin 进入）检验收敛阶，而不是某个 h 上的一致。"""
    delta, amp, phase = 0.30, 0.25, 0.4
    lab, sign, _ = freeze_cover(delta, nx=4, ny=2, amp=amp, phase=phase)
    assert lab is not None

    def h_of(theta):
        A, L = interlocking_pair_generic(nx=4, ny=2, amp=theta[0], phase=theta[1])
        return val(escape_height_from_frozen_cover(A, L, lab, (delta, 0.0, 0.0), ee_sign=sign))

    W = 2
    A, L = interlocking_pair_generic(nx=4, ny=2, amp=Dual.seed(amp, W, 0),
                                     phase=Dual.seed(phase, W, 1), sin_fn=D.sin)
    z = escape_height_from_frozen_cover(A, L, lab, (delta, 0.0, 0.0), ee_sign=sign)
    analytic = list(z.e)
    assert abs(z.v - h_of([amp, phase])) < 1e-12
    # h 必须扫到谷底才谈得上"谷底误差"；只扫到 2.5e-2 时还稳在 O(h²) 段上（误差 8e-6）
    rep = convergence_order(h_of, [amp, phase], analytic,
                            hs=(1e-1, 5e-2, 2.5e-2, 1e-3, 1e-4, 1e-5, 1e-6))
    assert rep["large_h_order"] == pytest.approx(2.0, abs=0.1), rep
    assert rep["valley_error"] < 1e-9, rep
    assert rep["errors"][1e-1] / rep["errors"][2.5e-2] == pytest.approx(16.0, rel=0.05)


@pytest.mark.parametrize("nx,amp,phase", [(4, 0.25, 0.4), (5, 0.3, 1.0), (4, 2.5e-4, -0.7)])
def test_generic_block_default_sin_keeps_the_phase_derivative(nx, amp, phase):
    """不传 sin_fn 时导数通道不许静默清零（审查 2026-09-21：默认 math.sin 把 ∂/∂phase 从 0.23 变 0）。

    oracle 是闭式 ∂z_i/∂phase = amp·cos(2π·i/nx + phase)（math.cos，不经过对偶 sin），
    与被测的 eab.dual.sin 不共用实现。一般位置（phase 0.4 / 1.0 / −0.7）、非对称 nx=5、
    幅值尺度 ×1e-3 各一格。
    """
    import math
    lz = 1.0
    A, L = interlocking_pair_generic(nx=nx, ny=2, amp=amp, phase=Dual.seed(phase, 1, 0))
    # 下块顶面网格点：第 i 列 j=0 的顶点下标 = i·2(ny+1)（rt/rb 交替加入）
    for i in range(nx + 1):
        v = L.verts[i * 2 * 3]
        assert isinstance(v[2], Dual), "默认 sin_fn 把对偶相位降成了 float"
        want = amp * math.cos(2 * math.pi * i / nx + phase)
        assert v[2].e[0] == pytest.approx(want, rel=1e-12, abs=1e-18)
        assert v[2].v == pytest.approx(lz / 2 + amp * math.sin(2 * math.pi * i / nx + phase), rel=1e-15)
    # 同一冻结盖下，省略 sin_fn 与显式 sin_fn=D.sin 的逃逸高度导数逐位相同且非零
    lab, sign, _ = freeze_cover(0.30, nx=4, ny=2, amp=0.25, phase=0.4)
    Ad, Ld = interlocking_pair_generic(nx=4, ny=2, amp=0.25, phase=Dual.seed(0.4, 1, 0))
    Ae, Le = interlocking_pair_generic(nx=4, ny=2, amp=0.25, phase=Dual.seed(0.4, 1, 0), sin_fn=D.sin)
    zd = escape_height_from_frozen_cover(Ad, Ld, lab, (0.30, 0.0, 0.0), ee_sign=sign)
    ze = escape_height_from_frozen_cover(Ae, Le, lab, (0.30, 0.0, 0.0), ee_sign=sign)
    assert zd.e == ze.e and abs(zd.e[0]) > 1e-3


def test_gate_has_teeth_wrong_gradient_is_caught():
    """门要有牙：故意把梯度乘 1.5，收敛阶检验必须报红。"""
    delta, amp, phase = 0.30, 0.25, 0.4
    lab, sign, _ = freeze_cover(delta, nx=4, ny=2, amp=amp, phase=phase)

    def h_of(theta):
        A, L = interlocking_pair_generic(nx=4, ny=2, amp=theta[0], phase=theta[1])
        return val(escape_height_from_frozen_cover(A, L, lab, (delta, 0.0, 0.0), ee_sign=sign))

    W = 2
    A, L = interlocking_pair_generic(nx=4, ny=2, amp=Dual.seed(amp, W, 0),
                                     phase=Dual.seed(phase, W, 1), sin_fn=D.sin)
    bad = [1.5 * g for g in escape_height_from_frozen_cover(
        A, L, lab, (delta, 0.0, 0.0), ee_sign=sign).e]
    rep = convergence_order(h_of, [amp, phase], bad,
                            hs=(1e-1, 5e-2, 2.5e-2, 1e-3, 1e-4, 1e-5, 1e-6))
    assert rep["valley_error"] > 1e-3            # 谷底误差不再趋零 ⇒ 梯度错
