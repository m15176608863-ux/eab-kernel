"""裕度层在贯入侧必须 fail-safe（审查 2026-09-21 · C14 ≡ C28）。

缺陷：`body_distance` 与 `margin_contacts` 没有 overlap 守卫。贯入位形上盖枚举的
|point_a − point_b| 是贯入深度一类的**正数**（实测 0.1 / 0.4 / 0.3 / 1.3），于是
`margin_contacts(delta)` 返回 []——"无广义接触闭合"＝裕度"安全"；同一输入
`inflated_membership` 却答 INSIDE。模块文档说的"贯入之后见证距离恒为 0"是假的。

oracle（纪律 A）：守卫本身用的是 `polyhedra_overlap`，所以"是否贯入"**不许**再用它来判。
每个输入都由**构造**保证贯入，用显式不等式核对（不经过 geom3 的任何谓词）：
  · "顶点在体内"类：A 的某个顶点严格落在 B 内部——方块用 |p − c| < half 逐轴比较；互锁下块用骨形块的
    解析顶面 z = lz/2 + amp·sin(2πu + phase) 沿 x 的分段线性插值（math.sin）；
  · **"无任何顶点在对方体内"类**（G6 minor[18] 补）：交叉方条，两体都是轴对齐方块，交集是三个区间交的
    乘积，贯入 ⟺ 三个区间重叠都为正；另逐顶点核对两体没有任何顶点严格在对方体内——只靠棱-棱穿越贯入。
    旧门只有前一类，把守卫换成"顶点在体内"检查全套照绿（见 test_guard_is_not_a_vertex_inside_check）。
  （等高 X 交叉——共面顶底面、谓词漏判——是 m2-geom 的 critical，不在这里重复。）

G6 minor[28]（亚容差贯入）：浅于 geom_tol 的贯入曾跳过哨兵，见证距离 ≈ 贯入深度被当距离报出，
δ < p 时答"安全"，比恰好相触还"安全"（不单调）。见 test_contact_resolution_is_monotone_in_depth。
"""

import math
from fractions import Fraction
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from osteomorphic import interlocking_pair  # noqa: E402

from eab.kernel3d.geom3 import box, tetra  # noqa: E402
from eab.margin import (INSIDE, ON_BOUNDARY, OUTSIDE, PENETRATING, body_distance,  # noqa: E402
                        inflated_membership, margin_contacts, contact_resolution)


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


_BARS = (((0.0, 0.0, 0.45), (2.0, 0.2, 0.1)), ((0.0, 0.0, 0.0), (0.2, 2.0, 0.4)))


def _box_verts(center, half):
    return [tuple(center[k] + sg[k] * half[k] for k in range(3))
            for sg in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                       (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))]


def _crossbars_case(s=1.0, swap=False):
    """交叉方条 A = box((0,0,0.45),(2,0.2,0.1))、B = box((0,0,0),(0.2,2,0.4))，几何 ×s。

    构造性证据（只用区间与逐轴不等式）：交集 = 三个轴区间交的乘积，贯入深度 = 三个重叠长度的最小值
    （z 向 [0.35, 0.55] ∩ [−0.4, 0.4] = 0.05，x、y 向各 0.4）；同时断言两体没有任何顶点严格在对方体内。"""
    (ca, ha), (cb, hb) = _BARS
    ca, ha, cb, hb = (tuple(s * c for c in v) for v in (ca, ha, cb, hb))
    overlap = [min(ca[k] + ha[k], cb[k] + hb[k]) - max(ca[k] - ha[k], cb[k] - hb[k]) for k in range(3)]
    for P, (c, h) in ((_box_verts(ca, ha), (cb, hb)), (_box_verts(cb, hb), (ca, ha))):
        assert not any(_strictly_inside_box(p, c, h, 0.0) for p in P), "构造不是'无顶点在体内'"
    A, B = box(ca, ha), box(cb, hb)
    return (B, A, min(overlap)) if swap else (A, B, min(overlap))


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
    # 无任何顶点在对方体内：交叉方条只靠棱-棱穿越贯入（G6 minor[18]）；外加 ×1e-3 与翻转参数次序
    "crossed bars (edge-edge only)": lambda: _crossbars_case(),
    "crossed bars x1e-3": lambda: _crossbars_case(1e-3),
    "crossed bars swapped": lambda: _crossbars_case(swap=True),
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
    """Given-data penetration below geom_tol remains exact penetration, never safety.

    Oracle: raw rational coordinate inequalities against the axis-aligned box;
    no tested predicate, normal, distance, or triangulation primitive is used.
    """
    A, B, depth = _convex_case((0.0, 0.0, 0.4 - 1e-12))
    assert depth > 0.0
    d, lab = body_distance(A, B)
    assert all(min(Fraction(v[k]) for v in B.verts) < Fraction(A.verts[0][k])
               < max(Fraction(v[k]) for v in B.verts) for k in range(3))
    assert (d, lab) == (0.0, (PENETRATING,))
    ms = margin_contacts(A, B, delta=0.05)
    assert ms and all(m.closed for m in ms)
    assert len(ms) == 1 and ms[0].label == (PENETRATING,) and ms[0].distance == 0
    assert ms[0].margin_gap == -0.05 and ms[0].normal is None
    assert inflated_membership(A, B, delta=0.05) == INSIDE
    assert inflated_membership(A, B, delta=0.0) == INSIDE


# ---------------------------------------------------------------- G6 minor[18]：守卫必须不是"顶点在体内"检查

def test_edge_edge_penetration_without_any_vertex_inside_is_constructed():
    """交叉方条的构造前提本身（区间 oracle）：深度 0.05·s > 0、无任何顶点严格在对方体内。"""
    for s in (1.0, 1e-3):
        _, _, depth = _crossbars_case(s)
        assert depth == pytest.approx(0.05 * s, rel=1e-12)


def test_guard_is_not_a_vertex_inside_check(monkeypatch):
    """牙（穿过被测路径）：把 margin 里的贯入守卫换成"A 的某顶点在 B 内"检查（G6 的变异原样），
    交叉方条必须红——它给出间距 0.05、EE 标签、margin_contacts []（fail-unsafe）；
    而"顶点在体内"那一类旧输入在同一变异下照绿（这正是旧门无牙的原因）。"""
    import eab.margin as M
    from eab.kernel3d.geom3 import point_in_polyhedron

    def vertex_inside_guard(A, B, tol=0.0):
        st = [point_in_polyhedron(v, B, tol) for v in A.verts]
        return 1 if 1 in st else (0 if 0 in st else -1)

    monkeypatch.setattr(M, "polyhedra_overlap", vertex_inside_guard)
    A, B, _ = _crossbars_case()
    d, lab = body_distance(A, B)
    assert lab[0] == "EE" and d == pytest.approx(0.05, abs=1e-12), (d, lab)       # 变异：把贯入深度当间距
    assert margin_contacts(A, B, delta=0.05) == []
    with pytest.raises(AssertionError):
        test_penetration_is_reported_as_a_violated_margin("crossed bars (edge-edge only)")
    test_penetration_is_reported_as_a_violated_margin("tetra+box (0,0,0.3)")        # 旧类输入看不见这个变异


# ---------------------------------------------------------------- G6 minor[28]：相触分辨率内的结果单调

_ORDER = {OUTSIDE: 0, ON_BOUNDARY: 1, INSIDE: 2}


def test_contact_resolution_is_monotone_in_depth():
    """把 tetra 沿 −z 压向方块顶面，深度 p（负 = 间隙）从 −1e-6 扫到 +1e-6，跨过 0 与 geom_tol：

      · 间距（贯入哨兵记 0）随 p 单调不增；每个 δ 下成员判定随 p 单调不减（OUTSIDE < ON_BOUNDARY < INSIDE），
        "有闭合的广义接触"也单调不减——修前 p = 5e-10、δ = 0 时答 OUTSIDE / []，而恰好相触答 ON_BOUNDARY；
      · E5a2：所有给定坐标下真贯入均为哨兵/INSIDE；恰好相触仍在 δ=0 的边界，分离侧报告带仍钳零。
    构造：深度由平移量给定（顶面 z = 0.4、tetra 底面 z = 0.4 − p），不经过任何谓词。
    牙：test_contact_resolution_gate_has_teeth。"""
    _check_monotone_contact_resolution()


_DEPTHS = (-1e-6, -1e-9, -2e-10, 0.0, 1e-12, 2e-10, 5e-10, 2e-9, 1e-6)
_DELTAS = (0.0, 1e-10, 1e-9, 0.05)


def _check_monotone_contact_resolution():
    rows = []
    for p in _DEPTHS:
        A, B, _ = _convex_case((0.0, 0.0, 0.4 - p))
        # Retain the old separated-side report-band assertion explicitly;
        # penetration remains default-exact, and test_margin_exact separately
        # gates default positive gaps below this same legacy window.
        options = dict(contact_window=contact_resolution(A, B)) if p < 0 else {}
        d, lab = body_distance(A, B, **options)
        mem = [_ORDER[inflated_membership(A, B, delta=dl, **options)] for dl in _DELTAS]
        closed = [bool(margin_contacts(A, B, delta=dl, **options)) for dl in _DELTAS]
        rows.append((p, d, lab, mem, closed))
        if p > 0:
            assert d == 0.0 and lab == (PENETRATING,), ("exact-penetration", p, d, lab)
    for (p0, d0, _, m0, c0), (p1, d1, _, m1, c1) in zip(rows, rows[1:]):
        assert d1 <= d0, (p0, d0, p1, d1)
        assert all(b >= a for a, b in zip(m0, m1)), (p0, m0, p1, m1)
        assert all(b >= a for a, b in zip(c0, c1)), (p0, c0, p1, c1)
    by_p = {p: (d, lab, mem, closed) for p, d, lab, mem, closed in rows}
    touch = by_p[0.0]
    assert touch[0] == 0 and touch[1][0] != PENETRATING
    assert touch[2] == [1, 2, 2, 2] and touch[3] == [True] * 4
    # Preserve the separated-side report-band contract, independently of the
    # new exact penetration guard. This gives the old no-clamp mutation teeth.
    assert by_p[-2e-10][0] == 0, ("separated-report-band", by_p[-2e-10])
    for p in (1e-12, 2e-10, 5e-10, 2e-9, 1e-6):
        assert Fraction(0.4) - Fraction(0.4 - p) > 0  # raw-coordinate certificate
        d, lab, mem, closed = by_p[p]
        assert d == 0.0 and lab == (PENETRATING,), ("exact-penetration", p, d, lab)
        assert mem == [2] * 4 and closed == [True] * 4, (p, mem, closed)
    assert by_p[-1e-6][2] == [0, 0, 0, 2]                 # 间隙 1e-6：δ ≤ 1e-9 仍在外
    assert by_p[-1e-6][0] == pytest.approx(1e-6, rel=1e-9)


def test_contact_resolution_gate_has_teeth(monkeypatch):
    """Disable the actual margin clamp: separated-side band assertion must fail.

    Separately reintroduce swallowing true penetration into contact. The exact
    sentinel assertion, not a solver/order-dependent assertion, must then fail.
    """
    import eab.margin as M
    import inspect
    true_resolve = M._resolve
    original_source = inspect.getsource(true_resolve)

    def compiled_mutant(source):
        namespace = dict(M.__dict__)
        exec(compile(source, "<E5a2 internal margin._resolve mutant>", "exec"), namespace)
        return namespace["_resolve"]

    no_clamp = original_source.replace("return ctol, rnd, wits, True",
                                       "return ctol, rnd, wits, False").replace(
        "return ctol, rnd, wits, minimum2 is not None and minimum2 <= ctol*ctol, minimum2", "return ctol, rnd, wits, False, minimum2")
    assert no_clamp != original_source
    monkeypatch.setattr(M, "_resolve", compiled_mutant(no_clamp))
    with pytest.raises(AssertionError) as ei:
        _check_monotone_contact_resolution()
    assert "separated-report-band" in str(ei.value), str(ei.value)
    swallowed_source = original_source.replace(
        "state = polyhedra_overlap(A, B, 0)",
        "state = min(0, polyhedra_overlap(A, B, 0))")
    assert swallowed_source != original_source
    monkeypatch.setattr(M, "_resolve", compiled_mutant(swallowed_source))
    with pytest.raises(AssertionError) as swallowed:
        _check_monotone_contact_resolution()
    assert "exact-penetration" in str(swallowed.value), str(swallowed.value)



@pytest.mark.parametrize("s", [1e-9, 1e-6])
def test_nested_bodies_at_nanometre_scale_are_penetrating(s):
    """G6 minor[28](b)：旧守卫用绝对 geom_tol = 1e-9，边长 1e-9 量级的整体嵌套掉进盖枚举、答 OUTSIDE
    （C14 的尺度变体）。容差随特征长度缩放后，任何尺度上嵌套都是贯入。"""
    A, B, depth = _nested_case(s)
    assert depth > 0.0
    assert body_distance(A, B) == (0.0, (PENETRATING,))
    assert inflated_membership(A, B, delta=0.0) == INSIDE
    ms = margin_contacts(A, B, delta=0.0)
    assert len(ms) == 1 and ms[0].label == (PENETRATING,) and ms[0].closed
