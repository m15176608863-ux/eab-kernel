"""逃逸高度的候选集完备性与公共入口（审查 2026-09-21 · C12、C15，及 C11 波及的冻结逃逸入口）。

C12：`escape_candidates` 的 docstring 说"不施加 in_extent 过滤"，代码却用了
`enumerate_covers3` 的默认 `require_in_extent=True`——抬升会让投影移进面内，z=0 处被丢掉的盖
恰是 z=z* 处的接触盖。旧门只测对称块 nx=4 的 y=0 直线（0/25 错）；非对称 nx=5 上 8–10/25 静默偏大
（例：0.44749 vs 真值 0.40054）。
C15：`escape_height_covers(verify=False)` 返回的正是 docstring 自己判定无效的纯盖规则（δ=0.4 → 0.300，真值 0.200）。

oracle（纪律 A）：
  · **解析逃逸高度**（主 oracle，零共用）。骨形块是沿 y 拉伸的剖面：下块顶面 z = lz/2 + h(x)，
    上块底面 z = lz/2 + h(x − dx) + z，h 是 amp·sin(2π·i/nx + phase) 在网格点上的分段线性插值。
    |dy| < ly 时两块内部相交 ⟺ 在公共 x 区间上某处 z < h(x) − h(x − dx)（竖向另一侧的条件在
    |h| < lz 时恒成立），故 h_escape = max(0, max_x [h(x) − h(x − dx)])，max 在分段线性的断点
    （两组网格点与区间端点）上取到。只用 math.sin 与插值，不碰 geom3 / covers3 的任何原语。
  · **暴力二分** `escape_height_brute` 只在少数偏移上作佐证：它与被测路径共用 `polyhedra_overlap`
    （谓词错时两者会一起错，见审查 exp_teeth D），且每次 ~1 s。scratch 实测解析值与二分在
    3 种块 × 25 个偏移上最大差 9e-12。
"""

import math
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from osteomorphic import interlocking_pair  # noqa: E402

from eab.kernel3d.frozen import FACET_KINDS, frozen_ee_sign  # noqa: E402
from eab.kernel3d.interlock import (escape_candidates, escape_height_brute,  # noqa: E402
                                    escape_height_covers, escape_height_from_frozen_cover)


def analytic_escape_height(dx, dy, *, nx, amp, phase=0.0, lx=2.0, ly=1.0, lz=1.0):
    assert abs(amp) < lz / 2
    if abs(dy) >= ly or abs(dx) >= lx:
        return 0.0

    def h(x):
        u = (x + lx / 2) / lx
        i = min(max(int(math.floor(u * nx)), 0), nx - 1)
        u0, u1 = i / nx, (i + 1) / nx
        h0 = amp * math.sin(2 * math.pi * u0 + phase)
        h1 = amp * math.sin(2 * math.pi * u1 + phase)
        return h0 + (h1 - h0) * (u - u0) / (u1 - u0)

    a, b = max(-lx / 2, -lx / 2 + dx), min(lx / 2, lx / 2 + dx)
    xs = [a, b] + [-lx / 2 + lx * i / nx for i in range(nx + 1)] + \
         [-lx / 2 + lx * i / nx + dx for i in range(nx + 1)]
    return max(0.0, max(h(x) - h(x - dx) for x in xs if a <= x <= b))


def _offsets(seed, n, s=1.0):
    rng = random.Random(seed)
    return [(rng.uniform(-0.6, 0.6) * s, rng.uniform(-0.3, 0.3) * s, 0.0) for _ in range(n)]


def _check_escape(A, L, off, truth, *, scale=1.0):
    sol = escape_height_covers(A, L, off)
    assert abs(sol.height - truth) < 1e-8 * scale, (off, sol.height, truth, sol.cover_label)
    if sol.cover_label is not None:
        # 决定逃逸高度的永远是面盖；冻结的闭式逃逸高度在它上面复现 float 路径
        lab = sol.cover_label
        assert lab[0] in FACET_KINDS, lab
        At = A.translated(off)
        sign = frozen_ee_sign(At, L, (lab[1][1], lab[1][2]), (lab[2][1], lab[2][2])) if lab[0] == "EE" else 1.0
        z = escape_height_from_frozen_cover(A, L, lab, off, ee_sign=sign)
        assert abs(z - sol.height) < 1e-9 * scale, (off, lab, z, sol.height)
    return sol


# ---------------------------------------------------------------- C12：非对称块、离开 y=0 直线

BLOCKS = {
    # 审查的块（一般位置：nx=5 非对称、phase=1.0）——修前 8/25 错
    "nx5 amp0.3 phase1.0": dict(nx=5, ny=2, amp=0.3, phase=1.0),
    # 计划原文的块（phase 默认 0）——修前 2/25 错
    "nx5 amp0.3 phase0": dict(nx=5, ny=2, amp=0.3),
}


@pytest.mark.parametrize("name", list(BLOCKS))
def test_escape_height_covers_is_complete_off_axis_on_asymmetric_blocks(name):
    """25 个确定性伪随机 (dx, dy) 偏移 vs 解析逃逸高度，零失配（阈值 1e-8）。"""
    kw = BLOCKS[name]
    A, L = interlocking_pair(**kw)
    for off in _offsets(7, 25):
        truth = analytic_escape_height(off[0], off[1], nx=kw["nx"], amp=kw["amp"], phase=kw.get("phase", 0.0))
        _check_escape(A, L, off, truth)


@pytest.mark.parametrize("off", [(0.0, 0.0, 0.0), (0.4, 0.0, 0.0), (-0.4, 0.25, 0.0), (0.2, -0.3, 0.0)])
def test_escape_height_covers_at_grid_aligned_offsets(off):
    """分界点（纪律 B）：dx 为网格间距 lx/nx 的整数倍（峰谷对齐，大量盖并列）与零偏移（互补贴合，h=0）。"""
    kw = BLOCKS["nx5 amp0.3 phase1.0"]
    A, L = interlocking_pair(**kw)
    truth = analytic_escape_height(off[0], off[1], nx=5, amp=0.3, phase=1.0)
    _check_escape(A, L, off, truth)


@pytest.mark.parametrize("s", [1e-2, 1e2])
def test_escape_height_covers_is_complete_under_scaling(s):
    """尺度格（纪律 B）：几何 × s、偏移 × s，逃逸高度 × s。"""
    A, L = interlocking_pair(nx=5, ny=2, amp=0.3 * s, phase=1.0, lx=2.0 * s, ly=1.0 * s, lz=1.0 * s)
    for off in _offsets(7, 8, s):
        truth = analytic_escape_height(off[0], off[1], nx=5, amp=0.3 * s, phase=1.0,
                                       lx=2.0 * s, ly=1.0 * s, lz=1.0 * s)
        _check_escape(A, L, off, truth, scale=s)


def test_audit_offset_matches_brute_and_the_truth_is_a_candidate():
    """审查的具体反例：interlocking_pair(5,2,0.3,1.0)、off=(−0.52473,−0.23870,0)：
    修前盖路径静默给 0.44749，真值 0.40054。三方（解析 / 暴力二分 / 盖路径）一致，且真值在候选集里。"""
    A, L = interlocking_pair(nx=5, ny=2, amp=0.3, phase=1.0)
    off = (-0.5247287610704319, -0.2386957665910207, 0.0)
    truth = analytic_escape_height(off[0], off[1], nx=5, amp=0.3, phase=1.0)
    brute = escape_height_brute(A, L, off, hi=2.5, tol=1e-11)
    assert abs(truth - 0.40053820200) < 1e-9 and abs(brute - truth) < 1e-9
    _check_escape(A, L, off, truth)
    assert any(abs(z - truth) < 1e-9 for z, _ in escape_candidates(A, L, off))


@pytest.mark.parametrize("seed_index", [3, 11, 19])
def test_analytic_oracle_agrees_with_brute_bisection(seed_index):
    """解析 oracle 本身的佐证：与暴力二分在三个偏移上一致（其余偏移在 scratch 全量核对过）。"""
    A, L = interlocking_pair(nx=5, ny=2, amp=0.3, phase=1.0)
    off = _offsets(7, 25)[seed_index]
    truth = analytic_escape_height(off[0], off[1], nx=5, amp=0.3, phase=1.0)
    assert abs(escape_height_brute(A, L, off, hi=2.5, tol=1e-11) - truth) < 1e-9


# ---------------------------------------------------------------- C15：没有"不裁决"的公共入口

@pytest.mark.parametrize("delta", [0.2, 0.4, 0.6])
def test_public_escape_entry_matches_brute_on_the_documented_counterexample(delta):
    """docstring 记载的纯盖规则反例（δ=0.4/0.6 给 0.300，真值 0.200）不许从公共入口回来。"""
    A, L = interlocking_pair(nx=4, ny=2, amp=0.25)
    off = (delta, 0.0, 0.0)
    truth = analytic_escape_height(delta, 0.0, nx=4, amp=0.25)
    assert abs(escape_height_brute(A, L, off, hi=2.0, tol=1e-11) - truth) < 1e-9
    _check_escape(A, L, off, truth)


def test_unverified_escape_branch_is_gone():
    """`verify=False`（返回纯盖规则的最大候选）已删除：传它必须 TypeError，不许静默给错值。"""
    A, L = interlocking_pair(nx=4, ny=2, amp=0.25)
    with pytest.raises(TypeError):
        escape_height_covers(A, L, (0.4, 0.0, 0.0), verify=False)


# ---------------------------------------------------------------- 冻结逃逸入口只接面盖

@pytest.mark.parametrize("lab", [("VE3", ("vertex", 0), ("edge", 12, 18)),
                                 ("EV3", ("edge", 0, 1), ("vertex", 12)),
                                 ("VV3", ("vertex", 0), ("vertex", 12))])
def test_frozen_escape_height_rejects_low_dimensional_covers(lab):
    """低维盖（VE3/EV3/VV3）的 gap 是无符号距离、沿竖线不是仿射的，z = −gap/n_z 不是逃逸高度
    （盖路径也从不让它们胜出：gap ≥ 0 ⇒ z ≤ 0）。冻结入口必须拒收，而不是算出一个数。"""
    A, L = interlocking_pair(nx=4, ny=2, amp=0.25)
    with pytest.raises(ValueError):
        escape_height_from_frozen_cover(A, L, lab, (0.3, 0.0, 0.0))
