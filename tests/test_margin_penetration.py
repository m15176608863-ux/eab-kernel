"""裕度层在贯入侧必须 fail-safe（审查 2026-09-21 · C14 ≡ C28）。

缺陷：`body_distance` 与 `margin_contacts` 没有 overlap 守卫。贯入位形上盖枚举的
|point_a − point_b| 是贯入深度一类的**正数**（实测 0.1 / 0.4 / 0.3 / 1.3），于是
`margin_contacts(delta)` 返回 []——"无广义接触闭合"＝裕度"安全"；同一输入
`inflated_membership` 却答 INSIDE。模块文档说的"贯入之后见证距离恒为 0"是假的。

oracle（纪律 A）：守卫本身用的是 `polyhedra_overlap`，所以"是否贯入"**不许**再用它来判。
每个输入都由**构造**保证贯入：A 的某个顶点严格落在 B 内部，用显式不等式核对——
方块用 |p − c| < half 逐轴比较；互锁下块用骨形块的解析顶面 z = lz/2 + amp·sin(2πu + phase)
沿 x 的分段线性插值（math.sin，不经过 geom3 的任何谓词）。
"""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from osteomorphic import interlocking_pair  # noqa: E402

from eab.kernel3d.geom3 import box, tetra  # noqa: E402
from eab.margin import (INSIDE, ON_BOUNDARY, PENETRATING, body_distance,  # noqa: E402
                        inflated_membership, margin_contacts)


def _tetra(s=1.0):
    return tetra((0.0, 0.0, 0.0), (0.6 * s, 0.0, 0.0), (0.0, 0.5 * s, 0.0), (0.1 * s, 0.1 * s, 0.55 * s))


def _box(s=1.0):
    return box(center=(0.0, 0.0, 0.0), half=(0.5 * s, 0.45 * s, 0.4 * s))


def _strictly_inside_box(p, center, half, margin):
    return all(abs(p[k] - center[k]) < half[k] - margin for k in range(3))


def _convex_case(x, s=1.0):
    """tetra 平移 x 对方块；构造性证据：tetra 的某个顶点严格在方块内。"""
    A = _tetra(s).translated(x)
    B = _box(s)
    half = (0.5 * s, 0.45 * s, 0.4 * s)
    depth = max(min(half[k] - abs(p[k]) for k in range(3)) for p in A.verts)
    return A, B, depth


def _nested_case(s=1.0):
    A = box(half=(0.3 * s, 0.3 * s, 0.3 * s))
    B = box(half=(1.0 * s, 1.0 * s, 1.0 * s))
    depth = max(min(1.0 * s - abs(p[k]) for k in range(3)) for p in A.verts)
    return A, B, depth


def _interlock_case(dx, nx=4, amp=0.25, phase=0.0):
    """互锁上块横移 dx 咬进下块：上块底面 y=0 一行的某个顶点严格低于下块解析顶面。"""
    A, L = interlocking_pair(nx=nx, ny=2, amp=amp, phase=phase)
    lx, lz = 2.0, 1.0

    def top_of_lower(x):                       # 分段线性插值（面按网格列是平面四边形）
        u = (x + lx / 2) / lx
        i = min(int(u * nx), nx - 1)
        u0, u1 = i / nx, (i + 1) / nx
        h0 = amp * math.sin(2 * math.pi * u0 + phase)
        h1 = amp * math.sin(2 * math.pi * u1 + phase)
        return lz / 2 + h0 + (h1 - h0) * (u - u0) / (u1 - u0)

    depth = -1.0
    for i in range(nx + 1):
        u = i / nx
        x = -lx / 2 + lx * u + dx
        if not (-lx / 2 < x < lx / 2):
            continue
        z_bottom_of_upper = lz / 2 + amp * math.sin(2 * math.pi * u + phase)   # 上块中心 z = lz
        depth = max(depth, min(top_of_lower(x) - z_bottom_of_upper, x + lx / 2, lx / 2 - x))
    return A.translated((dx, 0.0, 0.0)), L, depth


CASES = {
    # 审查的四个复现输入（一般位置）
    "tetra+box (0,0,0.3)": lambda: _convex_case((0.0, 0.0, 0.3)),
    "tetra+box (0,0,0)": lambda: _convex_case((0.0, 0.0, 0.0)),
    "tetra+box (0.2,0.1,-0.1)": lambda: _convex_case((0.2, 0.1, -0.1)),
    "nested boxes": lambda: _nested_case(),
    # 尺度格（纪律 B）
    "nested boxes x1e3": lambda: _nested_case(1e3),
    "tetra+box x1e-3": lambda: _convex_case((0.0, 0.0, 0.3e-3), 1e-3),
    # 浅贯入 1e-6（远大于 geom_tol=1e-9，必须判贯入）
    "tetra+box shallow 1e-6": lambda: _convex_case((0.0, 0.0, 0.4 - 1e-6)),
    # 凹的互锁块：横移 dx 咬进（审查 C28 的三个 dx），外加非对称 nx=5
    "interlock dx=0.08": lambda: _interlock_case(0.08),
    "interlock dx=0.12": lambda: _interlock_case(0.12),
    "interlock dx=0.2": lambda: _interlock_case(0.2),
    "interlock nx=5 dx=0.15": lambda: _interlock_case(0.15, nx=5, amp=0.3, phase=1.0),
}


@pytest.mark.parametrize("name", list(CASES))
def test_penetration_is_reported_as_a_violated_margin(name):
    """贯入 ⇒ body_distance 给哨兵 (0, PENETRATING)；margin_contacts 非空且全部闭合
    （单个哨兵：distance 0、margin_gap −δ、normal None）；与 inflated_membership == INSIDE 一致。"""
    A, B, depth = CASES[name]()
    assert depth > 0.0, f"构造没有保证贯入：{name} depth={depth}"
    assert body_distance(A, B) == (0.0, (PENETRATING,))
    for delta in (0.0, 0.05):
        for band in (0.0, 1.0):
            ms = margin_contacts(A, B, delta=delta, band=band)
            assert ms, f"贯入时 margin_contacts 返回 []（= 裕度安全），fail-unsafe：{name}"
            assert all(m.closed for m in ms)
            assert len(ms) == 1 and ms[0].label == (PENETRATING,)
            assert ms[0].distance == 0.0 and ms[0].margin_gap == -delta and ms[0].normal is None
        assert inflated_membership(A, B, delta=delta) == INSIDE


def test_touching_is_not_penetration_and_still_closes_the_margin():
    """分界点：面面相触（tetra 底面落在方块顶面上，深度恰为 0）不是贯入——见证距离 0、
    标签是真实的盖；δ > 0 时裕度闭合（INSIDE），δ = 0 时恰在边界上（ON_BOUNDARY）。"""
    A, B, depth = _convex_case((0.0, 0.0, 0.4))
    assert depth == 0.0
    d, lab = body_distance(A, B)
    assert lab is not None and lab[0] != PENETRATING
    assert abs(d) < 1e-12
    ms = margin_contacts(A, B, delta=0.05)
    assert ms and all(m.closed for m in ms) and all(m.label[0] != PENETRATING for m in ms)
    assert inflated_membership(A, B, delta=0.05) == INSIDE
    assert inflated_membership(A, B, delta=0.0) == ON_BOUNDARY


def test_penetration_below_geom_tol_is_still_fail_safe():
    """分界点的另一侧：贯入 1e-12 < geom_tol=1e-9，按相触处理——不管走哪条路，裕度都必须闭合。"""
    A, B, depth = _convex_case((0.0, 0.0, 0.4 - 1e-12))
    assert depth > 0.0
    d, _ = body_distance(A, B)
    assert 0.0 <= d < 1e-9
    ms = margin_contacts(A, B, delta=0.05)
    assert ms and all(m.closed for m in ms)
    assert inflated_membership(A, B, delta=0.05) == INSIDE
