"""纪律 F（M0.2）· 刚体运动与单位不变性元门：m2-theory 组负责的全部几何 API。

G6（2026-09-24）的 6 条 critical 里 5 条同一根因：绝对容差遍布内核，而测试从不平移、从不旋转、
从不放到工程坐标上。本文件把本组的 API 放进同一张格子：

    平移 |t| ∈ {0, 1e3, 1e5}（沿一般方向 u）× 单位缩放 s ∈ {1e-3, 1, 1e3} × 旋转 R

结果必须按应有的方式变换：

  · 逃逸高度 h ×s，剪胀比 tanψ = ∂h/∂δ 与 ∂h/∂amp 不变（无量纲），∂h/∂phase ×s；
  · 两体间距 ×s；裕度 δ ×s 时 INSIDE / ON_BOUNDARY / OUTSIDE 与"有无闭合的广义接触"不变；
  · 状态不变（贯入 / 相触 / 分离；可微 / 不可微）；
  · 稳定胜出盖标签保留原变换检查；边界并列/裕度标签按每格给定舍入数据的完整独立精确 oracle 核对，
    不把运动前的理想共面/共线关系强加给运动后数据；枚举序裁决也独立核对。

旋转：互锁逃逸沿 ẑ 抬升，所以只绕 z 轴转（非轴对齐的 0.7 rad）；裕度层与方向无关，用两个固定种子的
一般三维旋转（每个矩阵元 |R_ij| > 0.05，确实不与坐标轴对齐）。

oracle（纪律 A）：
  · 逃逸高度：解析逃逸高度 `analytic_escape_height` ×s（只用 math.sin 与分段线性插值，与盖路径零共用）；
  · 剪胀比：参考位形（R = I、t = 0、s = 1）的冻结盖对偶导数，参考本身另由 tests/test_interlock_*.py 对解析
    单侧差商核对；
  · 裕度：参考位形的结果 ×s；参考位形本身在 `test_margin_reference_cases_are_what_they_claim` 里对构造
    （显式不等式、`brute_feature_distance`——枚举全部特征对、不看法锥、不经盖枚举）核对。
比较容差是舍入级：K·eps·C（C = 变换后坐标量级），逃逸高度再除以最陡上行面的 n_z——
**不是**把绝对容差放宽到能过。

跨组（纪律 F）：只因**别组文件**的缺陷而红的格子标 strict xfail，reason 写明依赖哪组哪条。
"""

import math
import random
import sys
from functools import lru_cache
from pathlib import Path

import pytest
import e5a_cover_oracle as independent_covers
import e5a_escape_oracle as independent_escape

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from osteomorphic import interlocking_pair  # noqa: E402
from tia_sensitivity import sensitivity_at  # noqa: E402
from test_interlock_escape import analytic_escape_height  # noqa: E402

from eab.dual import Dual  # noqa: E402
from eab.kernel3d.covers3 import enumerate_covers3  # noqa: E402
from eab.kernel3d.frozen import frozen_ee_sign  # noqa: E402
from eab.kernel3d.geom3 import Polyhedron, box, brute_feature_distance, norm, sub, tetra  # noqa: E402
from eab.adapters.tia3d import (dilatancy_profile, escape_candidates, escape_height_brute,  # noqa: E402
                                    escape_height_covers, escape_height_from_frozen_cover)
from eab.margin import (INSIDE, ON_BOUNDARY, OUTSIDE, PENETRATING, REL_GEOM_TOL,  # noqa: E402
                        body_distance, characteristic_length, effective_geom_tol, inflated_membership,
                        margin_contacts, margin_gap_from_frozen_cover, rounding_floor)

# E5b: old invariance assertions below are retained verbatim in the caller's
# explicitly requested legacy contact window. Default exact APIs are tested
# independently on every former touch/subtol grid cell below.
import eab.margin as exact_margin


def body_distance(A, B, **kwargs):
    return exact_margin.body_distance(A, B, contact_window=exact_margin.contact_resolution(A, B), **kwargs)


def margin_contacts(A, B, **kwargs):
    return exact_margin.margin_contacts(A, B, contact_window=exact_margin.contact_resolution(A, B), **kwargs)


def inflated_membership(A, B, **kwargs):
    return exact_margin.inflated_membership(A, B, contact_window=exact_margin.contact_resolution(A, B), **kwargs)


EPS = sys.float_info.epsilon
TS = (0.0, 1e3, 1e5)
SS = (1e-3, 1.0, 1e3)
U = (0.6, -0.48, 0.64)                 # |u| = 1，一般方向


# ------------------------------------------------------------------ 刚体运动与缩放

def _rot_z(th):
    c, s = math.cos(th), math.sin(th)
    return ((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0))


def _rot3(seed):
    """固定种子的一般三维旋转（单位四元数）；断言不与任何坐标轴对齐。"""
    rng = random.Random(seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    R = ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
         (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
         (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))
    assert min(abs(R[i][j]) for i in range(3) for j in range(3)) > 0.05, R
    return R


I3 = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
ROT_Z = {"I": I3, "z0.7": _rot_z(0.7)}
ROT_3 = {"I": I3, "q4": _rot3(4), "q6": _rot3(6)}


def _app(R, v):
    return tuple(R[i][0] * v[0] + R[i][1] * v[1] + R[i][2] * v[2] for i in range(3))


def _vec(R, s, v):
    """位移/方向的变换：旋转与缩放，不平移。"""
    return _app(R, (s * v[0], s * v[1], s * v[2]))


def _rigid(P, R, t, s):
    """p ↦ R·(s·p) + t；面表原样（编号不变）。"""
    tv = (t * U[0], t * U[1], t * U[2])
    return Polyhedron([tuple(a + b for a, b in zip(_vec(R, s, p), tv)) for p in P.verts], list(P.faces))


def _mag(*Ps):
    return max(abs(c) for P in Ps for p in P.verts for c in p)


# ================================================================== 互锁：逃逸高度与剪胀比

KW = dict(nx=5, ny=2, amp=0.3, phase=1.0)          # 非对称块（纪律 B）
# 三个一般位置偏移 + 一个网格对齐偏移（峰谷对齐，大量盖并列——分界点）
OFFSETS = [(0.23, 0.07, 0.0), (-0.41, -0.12, 0.0), (0.13, 0.2, 0.0), (0.4, 0.0, 0.0)]


def _nz_min(nx, amp, phase, lx):
    """上行面的最小 n_z（解析：最陡一段的坡度）。逃逸高度的舍入 ∝ 1/n_z。"""
    m = max(abs(amp * (math.sin(2 * math.pi * (i + 1) / nx + phase) - math.sin(2 * math.pi * i / nx + phase)))
            / (lx / nx) for i in range(nx))
    return 1.0 / math.sqrt(1.0 + m * m)


NZ = _nz_min(5, 0.3, 1.0, 2.0)


def _tol_h(C, s):
    return 256.0 * EPS * (C + 3.0 * s) / NZ


@lru_cache(maxsize=None)
def _ilock(rot, t, s):
    A, L = interlocking_pair(**KW)
    return _rigid(A, ROT_Z[rot], t, s), _rigid(L, ROT_Z[rot], t, s)


def _ee_sign(A, L, lab):
    if lab[0] == "EE":
        return frozen_ee_sign(A, L, (lab[1][1], lab[1][2]), (lab[2][1], lab[2][2]))
    return 1.0


def _escape(rot, t, s, off):
    """变换后位形上的逃逸解 + 冻结胜出盖的对偶 δ 通道（沿旋转后的横移方向）。"""
    A, L = _ilock(rot, t, s)
    R = ROT_Z[rot]
    o = _vec(R, s, off)
    sol = escape_height_covers(A, L, o)
    tan = None
    if sol.cover_label is not None:
        W = 1
        d = Dual.seed(1.0, W, 0)                     # 横移量的缩放因子 λ：offset = λ·o
        od = tuple(d * c for c in o)
        At = A.translated(o)
        z = escape_height_from_frozen_cover(A, L, sol.cover_label, od,
                                            ee_sign=_ee_sign(At, L, sol.cover_label))
        # ∂h/∂λ = |o_xy|·tanψ（沿 o 方向的方向导数）；换回 ∂h/∂δ（δ = 横移长度）
        tan = (z.v, z.e[0] / math.hypot(o[0], o[1]))
    return sol, tan


@lru_cache(maxsize=None)
def _escape_ref(off):
    return _escape("I", 0.0, 1.0, off)


def _tol_tan(C, s):
    """剪胀比（无量纲）的比较容差：1e-9 加面法向的舍入 ~ eps·C / (s·L0)，除以 n_z。"""
    return 1e-9 + 64.0 * EPS * C / (s * NZ)


def _resolution(rot, t, s, off):
    """库声明的逃逸高度分辨率（竖向）：(geom_tol_eff + 2·舍入地板) / n_z_min，以及它是否由舍入地板主导。"""
    A, L = _ilock(rot, t, s)
    At = A.translated(_vec(ROT_Z[rot], s, off))
    g, r = effective_geom_tol(At, L), rounding_floor(At, L)
    return (g + 2.0 * r) / NZ, g > 1.000001 * REL_GEOM_TOL * characteristic_length(At, L)


# 只因 m2-geom 的缺陷而红的格子（纪律 F，strict xfail）：1e-3 尺度的块放到 1e5 坐标、绕 z 转 0.7，
# covers3 用绝对容差比较单位向量 / 棱参数（舍入 ≈ eps·C/棱长 ≈ 5e-8 ≫ tol = 1e-9），把一部分真实并列的接触盖
# 判成无效或"不在段内"（例：EE 棱参数 s = 1.0000000038 > 1 + 1e-9），候选集少了它们。
# scratch 里给 covers3 打上 G6 confirmed[6] 的修法（见证方向先减沿棱分量）+ 锥判据相对地板后：
# 偏移 0.23 / 0.13 转绿；网格对齐偏移 0.4 仍缺两个端点 EE（ee_cover 的 in_extent 参数容差），同一族。
_NEEDS_GEOM_COVERS = ("needs m2-geom: G6 confirmed[6] family (covers3 compares unit vectors / edge parameters "
                      "against absolute tol=1e-9; at C/L=4e7 genuinely tied contact covers drop out of the "
                      "escape candidate set)")


@pytest.mark.parametrize("s", SS)
@pytest.mark.parametrize("t", TS)
@pytest.mark.parametrize("rot", list(ROT_Z))
def test_escape_height_is_rigid_motion_and_unit_invariant(rot, t, s):
    """h ×s（对解析 oracle）；胜出盖标签逐字相同（并列组内按枚举序裁决）；冻结盖闭式复现 h；剪胀比不变。"""
    A, L = _ilock(rot, t, s)
    C = _mag(A, L)
    for off in OFFSETS:
        sol, tan = _escape(rot, t, s, off)
        ref, tan0 = _escape_ref(off)
        truth = s * analytic_escape_height(off[0], off[1], nx=5, amp=0.3, phase=1.0)
        assert abs(sol.height - truth) <= _tol_h(C, s), (off, sol.height, truth)
        assert sol.cover_label == ref.cover_label, (off, sol.cover_label, ref.cover_label)
        if tan is not None:
            assert abs(tan[0] - sol.height) <= _tol_h(C, s), (off, tan[0], sol.height)
            assert abs(tan[1] - tan0[1]) <= _tol_tan(C, s), (off, tan[1], tan0[1])


@pytest.mark.parametrize("s", SS)
@pytest.mark.parametrize("t", TS)
@pytest.mark.parametrize("rot", list(ROT_Z))
def test_escape_tied_set_is_invariant_up_to_the_declared_resolution(rot, t, s, request):
    """全部原格逐项核独立候选/并列清单；精确面环可因舍入新增有效 EE，不能按噪声删除。

    oracle 从所有源特征对自行枚举，循环 Newell/Gram 算有效性与在程；只重现 E5b 尚未迁移的
    公开逃逸窗口政策，不读取生产盖/候选来决定 expected。解析高度与原胜出标签另有原门。
    """
    if (rot, t, s) == ("z0.7", 1e5, 1e-3):
        pass  # 2026-09-27 合并：m2-geom 已修（该格 XPASS(strict)），xfail 摘除
    A, L = _ilock(rot, t, s)
    R = ROT_Z[rot]
    for off in OFFSETS:
        sol, _ = _escape(rot, t, s, off)
        ref, _ = _escape_ref(off)
        band, _ = _resolution(rot, t, s, off)
        got, want = set(sol.tied_labels), set(ref.tied_labels)
        offset = _vec(R, s, off)
        rows, _, _ = independent_escape.candidates(A, L, offset)
        expected_candidates = {lab: z for z, lab, _, _ in rows}
        actual_candidates = {lab: z for z, lab in escape_candidates(A, L, offset)}
        assert actual_candidates.keys() == expected_candidates.keys(), (off,
            actual_candidates.keys() - expected_candidates.keys(), expected_candidates.keys() - actual_candidates.keys())
        assert all(abs(z - expected_candidates[lab]) <= _tol_h(_mag(A, L), s)
                   for lab, z in actual_candidates.items())
        truth = s * analytic_escape_height(off[0], off[1], nx=5, amp=0.3, phase=1.0)
        expected = independent_escape.tied_labels(A, L, offset, truth)
        assert got == expected, (off, got - expected, expected - got)
        # The reference remains fully pinned to an independent oracle too.
        # At C/L~1e8 even its inclusion can be false for the rounded input;
        # completeness is checked against each input, never ideal topology.
        A0,L0=_ilock('I',0.,1.)
        truth0=analytic_escape_height(off[0],off[1],nx=5,amp=.3,phase=1.)
        assert want == independent_escape.tied_labels(A0,L0,off,truth0)
        assert all(abs(actual_candidates[lab] - sol.height) <= band for lab in got - want), (off, sorted(got - want))


def test_independent_escape_candidate_gate_catches_a_dropped_exact_edge_cover(monkeypatch):
    """Drop inside ee_cover, before enumeration; independent complete oracle stays fixed."""
    import eab.kernel3d.covers3 as covers
    A,L=_ilock('z0.7',0.,1.)
    offset=_vec(ROT_Z['z0.7'],1.,OFFSETS[0])
    label=('EE',('edge',25,27),('edge',26,32))
    rows,_,_=independent_escape.candidates(A,L,offset)
    expected={lab for _,lab,_,_ in rows}
    assert label in expected
    assert {lab for _,lab in escape_candidates(A,L,offset)} == expected
    original=covers.ee_cover
    def dropped(a,ea,b,eb,*args,**kwargs):
        return None if ('EE',('edge',*ea),('edge',*eb))==label else original(a,ea,b,eb,*args,**kwargs)
    monkeypatch.setattr(covers,'ee_cover',dropped)
    actual={lab for _,lab in escape_candidates(A,L,offset)}
    assert expected-actual == {label} and not actual-expected


def test_independent_escape_oracle_translation_preserves_exact_affine_data():
    """Oracle affine input must not round before its independent Newell/Gram work."""
    from fractions import Fraction as F
    vertices = ((2.**-40, 0., 0.), (0., 2.**-40, 0.))
    offset = (1e8, -1e8, 0.)
    expected = tuple(tuple(F(p[k])+F(offset[k]) for k in range(3)) for p in vertices)
    assert independent_escape.move(vertices, offset) == expected, 'oracle-exact-affine-input'


def test_independent_escape_oracle_float_translation_mutation_is_caught(monkeypatch):
    def rounded_move(vertices, offset):
        return tuple(tuple(p[k]+offset[k] for k in range(3)) for p in vertices)
    monkeypatch.setattr(independent_escape, 'move', rounded_move)
    with pytest.raises(AssertionError, match='oracle-exact-affine-input'):
        test_independent_escape_oracle_translation_preserves_exact_affine_data()


@pytest.mark.parametrize("rot,t,s", [("I", 0.0, 1.0), ("z0.7", 1e5, 1.0), ("I", 1e5, 1e3),
                                     ("z0.7", 1e5, 1e3), ("z0.7", 1e3, 1e-3)])
def test_brute_oracle_is_exact_zero_at_rest_and_scales(rot, t, s):
    """Given-data earliest roots match independent integer swept tetrahedron SAT.

    The original five inputs and two rest/flat-direction offsets are retained.
    Rounding may create real penetration; original exact-zero assertions remain
    in the unjittered homology gate below rather than being silently weakened.
    Float output is the least binary64 value not below the exact root.
    """
    A, L = _ilock(rot, t, s)
    R = ROT_Z[rot]
    from e5b_wall_oracle import earliest_star_escape
    from fractions import Fraction as F
    for offset in ((0.0, 0.0, 0.0), _vec(R, s, (0.0, 0.3, 0.0))):
        truth_exact = earliest_star_escape(A, L, offset)
        solution = escape_height_covers(A, L, offset)
        assert solution.exact_height == truth_exact, ("independent-exact-earliest", rot, t, s, offset)
        display = escape_height_brute(A, L, offset, hi=2.0*s)
        assert F(display) >= truth_exact
        assert display == 0 if truth_exact == 0 else F(math.nextafter(display, -math.inf)) < truth_exact
    off = OFFSETS[0]
    truth = s * analytic_escape_height(off[0], off[1], nx=5, amp=0.3, phase=1.0)
    h = escape_height_brute(A, L, _vec(R, s, off), hi=2.0 * s)
    assert abs(h - truth) <= 1e-9 * s + _tol_h(_mag(A, L), s), (h, truth)


@pytest.mark.parametrize("rot,t,s", [
    pytest.param("z0.7", 1e5, 1e-3),  # 2026-09-27 合并：m2-geom 已修，xfail 摘除
    ("I", 1e5, 1e-3), ("I", 0.0, 1e3), ("z0.7", 1e3, 1.0)])
def test_dilatancy_profile_is_rigid_motion_and_unit_invariant(rot, t, s):
    """dilatancy_profile：横移方向随旋转、δ 随缩放；h ×s、中心差分剪胀比不变、决定性盖标签逐字相同。
    z0.7 / 1e5 / 1e-3 格：covers3 丢掉了并列组里枚举序第一的那个盖（见 _NEEDS_GEOM_COVERS），胜出标签随之变。"""
    deltas = [0.1, 0.15, 0.2, 0.25]
    ref = dilatancy_profile(*_ilock("I", 0.0, 1.0), deltas=deltas)
    A, L = _ilock(rot, t, s)
    R = ROT_Z[rot]
    rows = dilatancy_profile(A, L, direction=_app(R, (1.0, 0.0, 0.0)), deltas=[s * d for d in deltas])
    C = _mag(A, L)
    for r, r0 in zip(rows, ref):
        assert abs(r["h"] - s * r0["h"]) <= _tol_h(C, s), (r, r0)
        assert r["cover"] == r0["cover"]
        if r0["tan_psi"] is not None:           # 中心差分：h 的舍入 / (2·0.05·s) 放大
            assert abs(r["tan_psi"] - r0["tan_psi"]) <= 1e-12 + _tol_h(C, s) / (0.05 * s), (r, r0)


# ------------------------------------------------------------------ TIA 灵敏度工具（平移 + 缩放）

# 默认剖面（nx=4, amp=0.25, lx=2）：δ=0.5 是峰值折点（两侧 ±0.5）；0.3 是一般点（phase 0 与 0.4）。
# 折点两侧各取一点 0.5 ± e：e = max(2e-8, 5 × 该格声明的分辨带 / s)——分辨带外必须判可微、取所在一侧的斜率。
# 分辨带不由舍入地板主导的格子上 e = 2e-8（修前 s = 1e-3 时绝对并列窗口 1e-9 = 相对 1e-6，把它判成不可微）；
# 1e5 坐标上 1e-3 的块，坐标舍入 64·eps·C ≈ 1.4e-9 = 相对 6e-7，e 随之放大到 ~2.4e-5（诚实的精度下限）。
TIA_POINTS = [(0.3, 0.0), (0.3, 0.4), (0.5, 0.0)]


def _tia_geom(t, s):
    return dict(nx=4, ny=2, amp=0.25 * s, lx=2.0 * s, ly=1.0 * s, lz=1.0 * s, center=(t * U[0], t * U[1], t * U[2]))


def _tia_kink_offset(t, s):
    kw = _tia_geom(t, s)
    A, L = interlocking_pair(**kw)
    At = A.translated((0.5 * s, 0.0, 0.0))
    band = (effective_geom_tol(At, L) + 2.0 * rounding_floor(At, L)) / _nz_min(4, 0.25, 0.0, 2.0)
    return max(2e-8, 5.0 * band / s)          # 两支斜率差 1：竖向带宽 / 1 = δ 带宽


@lru_cache(maxsize=None)
def _tia(delta0, phase, t, s):
    return sensitivity_at(s * delta0, phase=phase, **_tia_geom(t, s))


@pytest.mark.parametrize("s", SS)
@pytest.mark.parametrize("t", TS)
def test_tia_sensitivity_is_translation_and_unit_invariant(t, s):
    """可微标志逐通道不变；tanψ、∂h/∂amp 不变；h 与 ∂h/∂phase ×s；derivative_range 同样变换；胜出盖不变。"""
    C = t + 2.0 * s
    tol_len = 1e-9 * s + _tol_h(C, s)
    e = _tia_kink_offset(t, s)
    for delta0, phase in TIA_POINTS + [(0.5 - e, 0.0), (0.5 + e, 0.0)]:
        r0 = _tia(delta0, phase, 0.0, 1.0)
        r = _tia(delta0, phase, t, s)
        assert r["differentiable_by"] == r0["differentiable_by"], (delta0, phase, r["derivative_range"],
                                                                   r0["derivative_range"])
        assert abs(r["h"] - s * r0["h"]) <= tol_len, (delta0, phase, r["h"], r0["h"])
        dimless = _tol_tan(C, s)
        for name, scale in (("tan_psi", 1.0), ("dh_damp", 1.0), ("dh_dphase", s)):
            assert abs(r[name] - scale * r0[name]) <= dimless * scale, (delta0, phase, name, r[name], r0[name])
            lo, hi = r["derivative_range"][name]
            lo0, hi0 = r0["derivative_range"][name]
            assert abs(lo - scale * lo0) <= dimless * scale and abs(hi - scale * hi0) <= dimless * scale
        assert r["cover"] == r0["cover"], (delta0, phase, r["cover"], r0["cover"])   # 裁决确定（按枚举序）
    for delta0 in (0.5 - e, 0.5 + e):                       # 分辨带外：可微，且是所在一侧的斜率
        r = _tia(delta0, 0.0, t, s)
        assert r["differentiable_by"]["tan_psi"] and abs(r["tan_psi"] - (0.5 if delta0 < 0.5 else -0.5)) < 1e-6


# ================================================================== 裕度层：距离 ×s、δ ×s、状态与标签

def _tet():
    return tetra((0.0, 0.0, 0.0), (0.6, 0.0, 0.0), (0.0, 0.5, 0.0), (0.1, 0.1, 0.55))


def _box():
    return box(half=(0.5, 0.45, 0.4))


# 参考位形（R = I、t = 0、s = 1）。kind：sep（分离）/ contact（相触或亚容差贯入）/ pen（贯入）
# 第二列只存构造器名；数值构造由 _margin_pair_for_name 显式分派。
MARGIN_CASES = {
    # 一般位置的分离对：最近对分别是 VE3、EV3、VF（与平行面上另一顶点并列）、平行棱（VE3/EV3 并列）
    "sep_ve3": ("sep", "sep_ve3"),
    "sep_ev3": ("sep", "sep_ev3"),
    "sep_vf": ("sep", "sep_vf"),
    "sep_parallel_edges": ("sep", "sep_parallel_edges"),
    # 分界点：面面相触（深度恰为 0）与亚容差贯入（3e-10 < geom_tol）
    "touch": ("contact", "touch"),
    "subtol": ("contact", "subtol"),
    # 贯入：顶点在体内；棱-棱贯入（交叉方条，无任何顶点在对方体内）
    "deep": ("pen", "deep"),
    "crossbars": ("pen", "crossbars"),
    # 偏航 1e-5 rad 的方块叠在方块上方 0.06：最近对含 EE（候选法向恰在 B 顶棱弧的边界上，EE 冻结朝向的边界态；
    # G6 第五轮 major：frozen_ee_sign 漏了候选法向自身的噪声 /sinθ，一经旋转 + 平移就把朝向判反，冻结 gap 给 −d）
    "sep_ee_yaw": ("sep", "sep_ee_yaw"),
    # 凹体：互锁块（nx=3 以控制耗时）抬起后分离 / 横移咬进
    "ilock_sep": ("sep", "ilock_sep"),
    "ilock_bite": ("pen", "ilock_bite"),
}


def _yawed_stack(yaw, gap):
    c, sn = math.cos(yaw), math.sin(yaw)
    top = box(center=(0.0, 0.0, 1.0 + gap), half=(0.5, 0.5, 0.5))
    A = Polyhedron([(c * x - sn * y, sn * x + c * y, z) for x, y, z in top.verts], list(top.faces))
    return A, box(half=(0.5, 0.5, 0.5))


def _ilock_pair(off):
    A, L = interlocking_pair(nx=3, ny=1, amp=0.3, phase=1.0)
    return A.translated(off), L


def _margin_pair_for_name(name):
    """Build the same fixed fixture through transparent first-order calls."""
    if name == "sep_ve3":
        return (_tet().translated((0.291, 0.352, -1.217)), _box())
    if name == "sep_ev3":
        return (_tet().translated((0.84, -0.96, -0.87)), _box())
    if name == "sep_vf":
        return (_tet().translated((0.942, -0.066, 0.389)), _box())
    if name == "sep_parallel_edges":
        return (_tet().translated((0.065, 0.676, 0.48)), _box())
    if name == "touch":
        return (_tet().translated((0.0, 0.0, 0.4)), _box())
    if name == "subtol":
        return (_tet().translated((0.0, 0.0, 0.4 - 3e-10)), _box())
    if name == "deep":
        return (_tet().translated((0.0, 0.0, 0.3)), _box())
    if name == "crossbars":
        return (box((0.0, 0.0, 0.45), (2.0, 0.2, 0.1)), box((0.0, 0.0, 0.0), (0.2, 2.0, 0.4)))
    if name == "sep_ee_yaw":
        return _yawed_stack(1e-5, 0.06)
    if name == "ilock_sep":
        return _ilock_pair((0.11, -0.07, 0.3))
    if name == "ilock_bite":
        return _ilock_pair((0.12, 0.0, 0.0))
    raise KeyError(name)

@lru_cache(maxsize=None)
def _margin_ref(name):
    kind, make = MARGIN_CASES[name]
    A, B = _margin_pair_for_name(name)
    d0, lab0 = body_distance(A, B)
    ties = set()
    if kind == "sep":
        for c in enumerate_covers3(A, B, window=float("inf"), tol=1e-9):
            if c.in_extent and c.point_a is not None:
                if norm(sub(c.point_a, c.point_b)) <= d0 * (1.0 + 1e-9):
                    ties.add(c.label())
    return kind, A, B, d0, lab0, frozenset(ties)


def test_margin_reference_cases_are_what_they_claim():
    """参考位形自身对构造核对（纪律 A）：分离对的间距 = brute_feature_distance；相触 / 亚容差贯入的
    间距为 0；贯入给哨兵。凸对的构造性证据在 tests/test_margin_penetration.py。"""
    for name, (kind, _) in MARGIN_CASES.items():
        _, A, B, d0, lab0, ties = _margin_ref(name)
        if kind == "sep":
            assert abs(d0 - brute_feature_distance(A, B)) < 1e-12, name
            assert d0 > 0.05 and lab0 in ties, (name, d0, lab0)
        elif kind == "contact":
            assert d0 == 0.0 and lab0 is not None and lab0[0] != PENETRATING, (name, d0, lab0)
        else:
            assert (d0, lab0) == (0.0, (PENETRATING,)), name
    assert len(_margin_ref("sep_vf")[5]) > 1 and len(_margin_ref("sep_parallel_edges")[5]) > 1   # 真的有并列


# 只因 m2-geom 的缺陷而红的格子（纪律 F：strict xfail，别组修好后它们变 XPASS=失败，逼合并者摘标记）。
# 全在 1e-3 尺度的块放到 1e5 坐标（C/L ≈ 1e8，单位向量的舍入 ≈ eps·C/棱长 ≈ 2e-8 ≫ tol = 1e-9）：
#   · 凸对：covers3 的 ve3_cover / ev3_cover 由 unit(a − q) 造见证方向，q 的舍入给它一个沿棱分量，
#     edge_arc_contains 的绝对正交性判据（tol + 1e-12）把真最近的 VE3/EV3 拒掉，距离报成 1.6e-3 / inf
#     （真值 2.7e-4 / 4.8e-4）——G6 confirmed[6]。scratch 里只打 G6 给的修法 1（先减掉沿棱分量）即全绿。
#   · 凹对 ilock_sep：同一族——vertex_cone_contains / edge_arc_contains 把单位向量与绝对 tol 比较；
#     scratch 里只修 [6] 的修法 1 仍红，再给锥判据加相对地板 tol + c·eps·C/棱长 才绿（G6 未单列，记给 m2-geom）。
_NEEDS_GEOM_6 = ("needs m2-geom: G6 confirmed[6] (covers3 ve3_cover/ev3_cover witness direction vs the absolute "
                 "edge_arc_contains perpendicularity tol drops the true nearest VE3/EV3 at C/L=1e8)")
_NEEDS_GEOM_CONES = ("needs m2-geom: G6 confirmed[6] family (covers3 vertex_cone_contains/edge_arc_contains compare "
                     "unit vectors against an absolute tol; rounding eps*C/edge ~2e-8 at C/L=1e8)")
_MARGIN_XFAIL = {
    ("sep_ve3", "q4", 1e5, 1e-3): _NEEDS_GEOM_6,
    ("sep_ve3", "q6", 1e5, 1e-3): _NEEDS_GEOM_6,
    ("sep_ev3", "I", 1e5, 1e-3): _NEEDS_GEOM_6,
    ("sep_ev3", "q6", 1e5, 1e-3): _NEEDS_GEOM_6,
    ("sep_parallel_edges", "q4", 1e5, 1e-3): _NEEDS_GEOM_6,
    ("sep_parallel_edges", "q6", 1e5, 1e-3): _NEEDS_GEOM_6,
    ("ilock_sep", "q6", 1e5, 1e-3): _NEEDS_GEOM_CONES,
}


def _margin_xfail(name, rot, t, s):
    return _MARGIN_XFAIL.get((name, rot, t, s))


@pytest.mark.parametrize("s", SS)
@pytest.mark.parametrize("t", TS)
@pytest.mark.parametrize("rot", list(ROT_3))
@pytest.mark.parametrize("name", list(MARGIN_CASES))
def test_margin_layer_is_rigid_motion_and_unit_invariant(name, rot, t, s, request):
    """裕度层三个入口 + 冻结闭式在 27 格上的变换律：贯入 ⇒ 哨兵 / INSIDE（δ ×s）；相触与亚容差贯入 ⇒ 距离
    恰 0.0、δ = 0 时 ON_BOUNDARY、δ > 0 时 INSIDE、闭合接触非空；分离 ⇒ 距离 ×s（舍入级容差）、标签在参考
    并列集里、δ = 0.5d / 1.5d 时 OUTSIDE / INSIDE、有无闭合接触不变、冻结 gap 复现 d − δ 且 ∂/∂δ ≡ −1。
    修前红在：亚容差贯入（绝对 geom_tol：s = 1e3 时变成哨兵、s = 1 时把 3e-10 当间距报）、旋转后相触的
    舍入级间距（1e-14 ≠ 0）；绝对容差下 1e5 坐标上 1e-3 的块另有 m2-geom 的格子（strict xfail）。"""
    reason = _margin_xfail(name, rot, t, s)
    if reason:
        pass  # 2026-09-27 合并：m2-geom 已修（XPASS(strict)），xfail 摘除
    kind, A0, B0, d0, lab0, ties = _margin_ref(name)
    R = ROT_3[rot]
    A, B = _rigid(A0, R, t, s), _rigid(B0, R, t, s)
    C = _mag(A, B)
    tol = 256.0 * EPS * C + 1e-12 * s
    d, lab = body_distance(A, B)
    if kind == "pen":
        assert (d, lab) == (0.0, (PENETRATING,)), (d, lab)
        for delta in (0.0, 0.05 * s):
            ms = margin_contacts(A, B, delta=delta)
            assert len(ms) == 1 and ms[0].label == (PENETRATING,) and ms[0].margin_gap == -delta
            assert inflated_membership(A, B, delta=delta) == INSIDE
        return
    if kind == "contact":
        assert d == 0.0 and lab is not None and lab[0] != PENETRATING, (d, lab)
        assert inflated_membership(A, B, delta=0.0) == ON_BOUNDARY
        assert inflated_membership(A, B, delta=0.01 * s) == INSIDE
        for delta in (0.0, 0.01 * s):
            ms = margin_contacts(A, B, delta=delta)
            assert ms and all(m.closed for m in ms) and ms[0].distance == 0.0, (delta, ms[:2])
        return
    # 分离：距离 ×s、标签在并列集里、δ ×s 时成员判定与"有无闭合接触"不变、冻结闭式复现
    assert abs(d - s * d0) <= tol, (d, s * d0, lab)
    assert lab in ties, (lab, sorted(ties))
    assert inflated_membership(A, B, delta=0.0) == OUTSIDE
    assert inflated_membership(A, B, delta=0.5 * s * d0) == OUTSIDE
    assert inflated_membership(A, B, delta=1.5 * s * d0) == INSIDE
    assert margin_contacts(A, B, delta=0.5 * s * d0) == []
    ms = margin_contacts(A, B, delta=1.5 * s * d0)
    assert ms and all(m.closed for m in ms)
    assert abs(ms[0].distance - s * d0) <= tol and ms[0].label in ties
    sign = _ee_sign(A, B, lab)
    g = margin_gap_from_frozen_cover(A, B, lab, (0.0, 0.0, 0.0), Dual.seed(0.5 * s * d0, 1, 0), ee_sign=sign)
    assert abs(g.v - 0.5 * s * d0) <= tol and g.e[0] == -1.0, (g, s * d0)


_LABEL_XFAIL = dict(_MARGIN_XFAIL)
# 平行面并列（VF 顶点 0 / 顶点 2 对同一面）：并列组里枚举序第一的 VF(顶点 0) 在 C/L = 1e8 时被
# vertex_cone_contains 的绝对容差判成无效（−n 恰在顶点法锥边界上），胜出者随之变成 VF(顶点 2)；
# 距离与成员判定不受影响（主门照绿）。scratch 里给锥判据加相对地板后逐字相同。
_LABEL_XFAIL[("sep_vf", "q6", 1e5, 1e-3)] = _NEEDS_GEOM_CONES


@pytest.mark.parametrize("s", SS)
@pytest.mark.parametrize("t", TS)
@pytest.mark.parametrize("rot", list(ROT_3))
@pytest.mark.parametrize("name", [n for n, (k, _) in MARGIN_CASES.items() if k == "sep"])
def test_margin_labels_are_identical_under_rigid_motion(name, rot, t, s, request):
    """每个原运动格核独立完整盖集合、距离与枚举序裁决；不混用运动前后的精确法锥标签。

    非舍入理想几何的标签稳定性不能覆盖给定坐标的真实分支；原 identity 基准仍单独核对。
    oracle 用循环 Newell/Gram/极射线枚举和独立见证，不调用 margin/cover 函数。
    """
    reason = _LABEL_XFAIL.get((name, rot, t, s))
    if reason:
        pass  # 2026-09-27 合并：m2-geom 已修（XPASS(strict)），xfail 摘除
    _, A0, B0, d0, lab0, _ = _margin_ref(name)
    R = ROT_3[rot]
    A, B = _rigid(A0, R, t, s), _rigid(B0, R, t, s)
    delta=1.5*s*d0
    expected=independent_covers.margin_selection(A,B,delta)
    actual=margin_contacts(A,B,delta=delta)
    assert {m.label for m in actual} == set(expected)
    assert len(actual) == len(expected)
    for item in actual:
        assert abs(item.distance-expected[item.label]) <= 4*math.ulp(expected[item.label])
    _, rounding=independent_escape.windows(tuple(A.verts),tuple(B.verts))
    rank={'VF':0,'FV':1,'EE':2,'VE3':3,'EV3':4,'VV3':5}
    def first(offset):
        low=min(d-offset for d in expected.values())
        tied=[lab for lab,d in expected.items() if d-offset-low <= rounding]
        return min(tied,key=lambda lab:(rank[lab[0]],lab[1],lab[2]))
    assert body_distance(A,B)[1] == first(0.)
    assert actual[0].label == first(delta)
    if (rot,t,s)==('I',0.,1.):
        assert first(0.) == first(delta) == lab0


@pytest.mark.parametrize("s", SS)
@pytest.mark.parametrize("t", TS)
@pytest.mark.parametrize("rot", list(ROT_3))
@pytest.mark.parametrize("name", ["touch", "subtol"])
def test_margin_default_relation_matches_independent_exact_oracle(name, rot, t, s):
    """Integer tetrahedral-union SAT, not production overlap/cone/distance primitives.

    Each of the former 41 failures is represented; transformed coordinates,
    not the unrounded ideal touching construction, are the contract.
    """
    import e5a2_surface_oracle as oracle
    A0, B0 = _margin_pair_for_name(name)
    A, B = _rigid(A0, ROT_3[rot], t, s), _rigid(B0, ROT_3[rot], t, s)
    expected = oracle.star_relation(A, B, 0)
    d, label = exact_margin.body_distance(A, B)
    assert exact_margin.inflated_membership(A, B, delta=0) == expected, (name, rot, t, s, expected)
    if expected == INSIDE:
        assert (d, label) == (0., (PENETRATING,))
        for delta in (0., 0.01*s):
            contacts = exact_margin.margin_contacts(A, B, delta=delta)
            assert len(contacts) == 1 and contacts[0].label == (PENETRATING,)
            assert contacts[0].closed and contacts[0].margin_gap == -delta
    else:
        assert label is not None and label != (PENETRATING,)
        assert (d == 0) == (expected == ON_BOUNDARY)
        assert bool(exact_margin.margin_contacts(A, B, delta=0)) == (expected == ON_BOUNDARY)


@pytest.mark.parametrize("rot,t,s", [("I", 0.0, 1.0), ("z0.7", 1e5, 1.0), ("I", 1e5, 1e3),
                                     ("z0.7", 1e5, 1e3), ("z0.7", 1e3, 1e-3)])
def test_brute_oracle_ideal_unjittered_homology_is_exact_zero_at_rest_and_scales(rot, t, s):
    """Retain both original zero assertions on an exactly matching interface.

    Raw top heights are exact input data; lower/upper are extruded from that
    SAME interface with Fraction arithmetic. Signed-permutation rotations,
    scale and translation are exact, so no ideal relation is lost to jitter.
    Oracle uses independent integer tetrahedral-union swept SAT only.
    """
    from fractions import Fraction as F
    from e5b_wall_oracle import earliest_star_escape
    _, lower = interlocking_pair(**KW)
    top = [tuple(map(F, lower.verts[i])) for i in range(0, len(lower.verts), 2)]
    lo, up = [], []
    for x, y, z in top:
        lo.extend(((x, y, z), (x, y, z-1)))
        up.extend(((x, y, z+1), (x, y, z)))
    R = I3 if rot == "I" else ((0., -1., 0.), (1., 0., 0.), (0., 0., 1.))
    def move(vertices):
        return Polyhedron([tuple(F(t)*F(U[i])+F(s)*sum(F(R[i][j])*v[j] for j in range(3))
                                 for i in range(3)) for v in vertices], lower.faces)
    A, L = move(up), move(lo)
    for offset in ((0., 0., 0.), _vec(R, s, (0., .3, 0.))):
        assert earliest_star_escape(A, L, offset) == 0
    assert escape_height_brute(A, L, (0.0, 0.0, 0.0), hi=2.0 * s) == 0.0
    assert escape_height_brute(A, L, _vec(R, s, (0.0, 0.3, 0.0)), hi=2.0 * s) == 0.0
