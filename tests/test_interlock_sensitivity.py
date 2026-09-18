"""互锁力学量（逃逸高度、剪胀比）与 TIA 解析灵敏度的门。

两道 oracle：
  · 逃逸高度 —— 对暴力相交谓词二分（不可微，纯真值）；
  · 解析梯度 —— 中心差分 + 收敛阶（对非线性参数）。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from osteomorphic import interlocking_pair, interlocking_pair_generic  # noqa: E402
from tia_sensitivity import freeze_cover, profile, sensitivity_at  # noqa: E402

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


def test_escape_profile_is_a_symmetric_ramp_with_peak_at_amplitude():
    rows = profile()
    peak = max(rows, key=lambda r: r["h"])
    assert abs(peak["h"] - 0.25) < 1e-12 and abs(peak["delta"] - 0.5) < 1e-12
    for r in rows:
        assert abs(abs(r["tan_psi"]) - 0.5) < 1e-9            # 坡度恒定的锯齿剖面
    assert all(r["tan_psi"] > 0 for r in rows if r["delta"] < 0.5)
    assert all(r["tan_psi"] < 0 for r in rows if r["delta"] > 0.5)


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
    for r in profile():
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
