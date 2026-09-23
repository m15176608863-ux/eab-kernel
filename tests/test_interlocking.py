"""互锁块（osteomorphic）几何与 Phase 3 凹块 G0 自证——TIA 方向的第一个真实算例。

凹块没有 legacy 可对，唯一 oracle 是 G0 的暴力多面体谓词（设计文档 §五）。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from osteomorphic import interlocking_pair, osteomorphic_block  # noqa: E402

from eab.kernel3d.covers3 import enumerate_covers3  # noqa: E402
from eab.kernel3d.g03 import g0_distance_completeness3  # noqa: E402
from eab.kernel3d.geom3 import box, point_in_polyhedron, polyhedra_overlap, tetra  # noqa: E402


@pytest.mark.parametrize("P,name", [(box(), "box"),
                                    (tetra((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)), "tetra"),
                                    (osteomorphic_block(nx=4, ny=2, amp=0.25), "osteo_4x2"),
                                    (osteomorphic_block(nx=6, ny=3, amp=0.15), "osteo_6x3"),
                                    (osteomorphic_block(nx=4, ny=2, amp=0.0), "osteo_flat")])
def test_manifold_and_orientation(P, name):
    """闭合定向流形自检：面绕向错会静默污染所有盖的法向，这道门必须在几何进内核前拦住。"""
    assert P.manifold_issues() == [], (name, P.manifold_issues()[:5])


def test_osteomorphic_is_genuinely_concave_with_exact_prism_volume():
    B = osteomorphic_block(nx=4, ny=2, lx=2.0, ly=1.0, lz=1.0, amp=0.25)
    assert not B.is_convex(1e-12)
    assert len(B.reflex_edges(1e-9)) > 0
    # 顶底同相位起伏 ⇒ 厚度恒为 lz ⇒ 体积恰为 lx·ly·lz
    assert abs(B.volume() - 2.0) < 1e-12
    assert point_in_polyhedron(B.interior_point(), B, 0.0) == 1
    # amp=0 退化为长方体
    flat = osteomorphic_block(nx=4, ny=2, amp=0.0)
    assert flat.is_convex(1e-9) and abs(flat.volume() - 2.0) < 1e-12


def test_interlock_blocks_lateral_motion_but_not_vertical():
    """互锁的定义性质：竖向可分离、侧向被咬合锁死。"""
    A, L = interlocking_pair(nx=4, ny=2, amp=0.25)
    assert polyhedra_overlap(A, L, 1e-9) == 0                     # 就位：面面贴合
    assert polyhedra_overlap(A.translated((0.0, 0.0, 0.05)), L, 1e-12) == -1   # 抬起：分离
    for dx in (0.08, 0.12, 0.2):
        assert polyhedra_overlap(A.translated((dx, 0.0, 0.0)), L, 1e-12) == 1, dx
    # 沿 y（无起伏方向）平移不被锁
    assert polyhedra_overlap(A.translated((0.0, 0.3, 0.0)), L, 1e-9) in (0, -1)


def test_covers_at_seated_interlock_are_complete_and_zero_gap():
    A, L = interlocking_pair(nx=4, ny=2, amp=0.25)
    covs = [c for c in enumerate_covers3(A, L, window=0.4, tol=1e-9) if c.in_extent]
    assert covs
    assert max(abs(c.gap) for c in covs) < 1e-12                  # 就位时全部零间隙
    kinds = {c.kind for c in covs}
    assert {"VF", "FV"} <= kinds                                  # 互补面 ⇒ 双向顶点-面盖


def test_lifted_interlock_normal_gap_is_lift_times_cos_slope():
    """抬起 h 后法向间隙 = h·cos(坡角)，不是 h——起伏面是斜的。"""
    from math import atan, cos, pi
    amp, lx, nx = 0.25, 2.0, 4
    A, L = interlocking_pair(nx=nx, ny=2, amp=amp, lx=lx)
    h = 0.03
    covs = [c for c in enumerate_covers3(A.translated((0.0, 0.0, h)), L, window=0.4, tol=1e-9)
            if c.in_extent]
    g = min(c.gap for c in covs)
    # 第一段坡：Δz = amp·sin(2π/nx) 对应 Δx = lx/nx
    slope = atan(amp * abs(__import__("math").sin(2 * pi / nx)) / (lx / nx))
    assert abs(g - h * cos(slope)) < 1e-9, (g, h * cos(slope))


@pytest.mark.parametrize("seed", range(3))
def test_g0_distance_completeness_on_concave_interlocking_pair(seed):
    """Phase 3 的核心门：凹块上，**法锥有效性筛选不丢最近特征对**（距离完备性）。

    独立 oracle 是 brute_feature_distance（枚举全部特征对、零法锥筛选、只用坐标）。
    """
    A, L = interlocking_pair(nx=4, ny=2, amp=0.25)
    rep = g0_distance_completeness3(A, L, radius=0.35, samples=60, seed=seed, atol=1e-9)
    assert rep.samples > 15, rep
    assert rep.failures == [], rep.failures[:3]
    assert rep.worst_abs_error < 1e-9


def test_g0_distance_completeness_on_merged_interlocking_pair():
    """归并后的互锁块：y = ±0.5 侧面是**凹十边形**（审查 C7 的现场）。

    纪律 A：本门的 oracle brute_feature_distance 与盖的 in_extent 共用 point_in_face_polygon，
    且采样区里的最近对不落在凹臂上——所以它只是一致性检查；对凹面的独立门是
    tests/test_geom3_face_polygon.py 里的骨形块侧面探针（闭式真值）。
    """
    from eab.kernel3d.geom3 import merge_coplanar
    A, L = interlocking_pair(nx=4, ny=2, amp=0.25)
    Am, Lm = merge_coplanar(A), merge_coplanar(L)
    assert max(len(f) for f in Lm.faces) == 10 and Lm.manifold_issues() == []
    rep = g0_distance_completeness3(Am, Lm, radius=0.35, samples=60, seed=0, atol=1e-9)
    assert rep.samples > 15, rep
    assert rep.failures == [], rep.failures[:3]


def test_min_cover_gap_is_not_a_membership_rule_for_concave_bodies():
    """把边界钉死：分离的凹块之间也存在深负 gap 的有效盖（顶点落在对方某面平面内侧）。

    这条负结果是"凸块用 facet 间隙取 max、凹块需要全局入口块构造"的理由，
    必须有门看着，否则以后有人会误用 min 当成员谓词（2026-09-18 我就误用过一次）。
    """
    from eab.kernel3d.covers3 import enumerate_covers3
    A, L = interlocking_pair(nx=4, ny=2, amp=0.25)
    sep = A.translated((0.008, -0.01, 0.048))
    assert polyhedra_overlap(sep, L, 1e-12) == -1          # 确实分离
    covs = [c for c in enumerate_covers3(sep, L, window=float("inf"), tol=1e-9,
                                         include_low_dim=False) if c.in_extent]
    assert min(c.gap for c in covs) < -2.0                 # 却有 gap ≈ −2.7 的有效盖
    # 而距离形式给出正确答案
    from eab.kernel3d.geom3 import brute_feature_distance, norm as _n, sub as _s
    got = min(_n(_s(c.point_a, c.point_b)) for c in
              enumerate_covers3(sep, L, window=float("inf"), tol=1e-9) if c.in_extent)
    assert abs(got - brute_feature_distance(sep, L)) < 1e-9
