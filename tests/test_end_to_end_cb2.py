"""端到端：bdda3d 真夹具 → 几何重建 → 盖枚举 → 接触 → 极限分析，对纸笔闭式解。

2026-09-21 审查的盲区 6："没有任何跨层路径被测过；接缝处（非零窗口的 contacts_from_covers、
夹具几何 → 盖 → LP）正是这次发现静默错值的地方。" 本文件就是那条接缝。

位形（cb2 三例同一几何）：上块 A = [−1,1]²×[0,1]（体积 4），坐落下块 B = [−2,2]²×[−1,0] 顶面。
荷载：自重 W 作用于 A 的体心 (0,0,½)；活荷载 H 作用于 A 顶面中心 (0,0,1)。

**oracle 是纸笔闭式，不调用 eab 的任何函数**（纪律 A）：
  · 滑动：H = μW（四角法向力之和 = W，库仑）；
  · 沿 ±x / ±y 推的倾覆：绕前缘，H·1 = W·1 ⇒ H = W；
  · 沿对角推的倾覆：绕过角点且垂直于推力的支承线，力臂 √2 ⇒ H = √2·W；
  ⇒ α* = min(μ, 1)·W（轴向）、min(μ, √2)·W（对角）。
三维摩擦锥用 k 边内接棱锥；法向 +z 时 _tangents 给出 t1 = −ŷ、t2 = +x̂，k = 8 的棱方向恰含
±x̂、±ŷ 与四条对角——所以本文件所取方向上线性化是**精确的**，α 应与闭式逐位吻合到 1e-9。
"""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from g2_bdda3d import load_case  # noqa: E402

from eab.kernel3d.covers3 import enumerate_covers3  # noqa: E402
from eab.kernel3d.geom3 import Polyhedron  # noqa: E402
from eab.limit import check_duality, contacts_from_covers, limit_load, wrench  # noqa: E402

CASES = sorted((ROOT / "fixtures" / "bdda3d").glob("*.json"))
W = 10.0
DIRS_AXIAL = [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)]
DIR_DIAG = (math.sqrt(0.5), math.sqrt(0.5))


def _scaled(P: Polyhedron, s: float) -> Polyhedron:
    return Polyhedron([tuple(s * c for c in v) for v in P.verts], list(P.faces))


def _capacity(path, mu, direction, *, geom_scale=1.0, load_scale=1.0, side="a", drop=(),
              origin=(0.0, 0.0, 0.0)):
    _, _, blocks, _ = load_case(path)
    A, B = _scaled(blocks[2], geom_scale), _scaled(blocks[1], geom_scale)
    covs = [c for c in enumerate_covers3(A, B, window=1e-6 * geom_scale, tol=1e-9 * geom_scale)
            if c.in_extent]
    cts = [c for i, c in enumerate(contacts_from_covers(covs, mu=mu, side=side)) if i not in drop]
    s, w = geom_scale, W * load_scale
    dead = wrench((0.0, 0.0, -w), (0.0, 0.0, 0.5 * s), origin, 3)
    live = wrench((direction[0] * load_scale, direction[1] * load_scale, 0.0), (0.0, 0.0, 1.0 * s),
                  origin, 3)
    r = limit_load(cts, dead, live, dim=3, origin=origin, k=8)
    return r, cts, dead, live, covs


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_fixture_geometry_gives_exactly_four_corner_contacts(path):
    r, cts, *_, covs = _capacity(path, 0.3, (1.0, 0.0))
    assert len(covs) == 4 and {c.kind for c in covs} == {"VF"}
    assert sorted((round(c.point[0], 12), round(c.point[1], 12), round(c.point[2], 12)) for c in cts) == \
        [(-1.0, -1.0, 0.0), (-1.0, 1.0, 0.0), (1.0, -1.0, 0.0), (1.0, 1.0, 0.0)]


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
@pytest.mark.parametrize("mu", [0.1, 0.3, 0.6, 0.95, 1.0, 1.2, 2.0])   # μ = 1 是分界点
@pytest.mark.parametrize("d", DIRS_AXIAL, ids=["+x", "-x", "+y", "-y"])
def test_axial_push_slides_or_topples_exactly_as_closed_form(path, mu, d):
    r, *_ = _capacity(path, mu, d)
    assert r.status == "optimal"
    assert r.alpha == pytest.approx(min(mu, 1.0) * W, abs=1e-9)


@pytest.mark.parametrize("mu", [0.3, 1.0, 1.3, 1.5, 3.0])             # 对角分界在 √2
def test_diagonal_push_uses_the_sqrt2_tipping_line(mu):
    r, *_ = _capacity(CASES[0], mu, DIR_DIAG)
    assert r.status == "optimal"
    assert r.alpha == pytest.approx(min(mu, math.sqrt(2.0)) * W, abs=1e-9)


@pytest.mark.parametrize("mu,topples", [(0.4, False), (0.95, False), (1.05, True), (2.0, True)])
def test_failure_mode_is_read_off_the_dual_mechanism(mu, topples):
    """滑动 = 纯平动（角速度为零）；倾覆 = 绕 y 轴转动，且前缘（x = +1, z = 0）速度为零。"""
    r, cts, dead, live, _ = _capacity(CASES[0], mu, (1.0, 0.0))
    vx, vy, vz, wx, wy, wz = r.mechanism
    if topples:
        assert abs(wy) > 1e-6 and abs(wx) < 1e-9 and abs(wz) < 1e-9
        v_edge = (vx + wy * 0.0 - wz * 0.0, vy, vz + wx * 0.0 - wy * 1.0)   # v + ω×r，r=(1,0,0)
        assert abs(v_edge[0]) < 1e-9 and abs(v_edge[2]) < 1e-9
    else:
        # 纯平动；但**切向速度方向不唯一**：推力方向恰落在八边形内接锥的一条棱上时，
        # 对偶最优面是该棱两侧 ±π/k 的一整段，求解器返回其中一个端点（实测偏 −22.5°，
        # vy = −tan(π/8)）。承载力与对偶间隙不受影响。所以只断言：无转动、偏角 ≤ π/k、
        # 沿推力方向的关联流动 vz = μ·vx（上限功率平衡 α = vz·W / vx 即由此给出 μW）。
        assert max(abs(wx), abs(wy), abs(wz)) < 1e-9
        assert vx > 0 and abs(math.atan2(vy, vx)) <= math.pi / 8 + 1e-9
        assert vz == pytest.approx(mu * vx, abs=1e-9)


@pytest.mark.parametrize("mu", [0.3, 1.5])
def test_lower_and_upper_bounds_coincide_end_to_end(mu):
    r, cts, dead, live, _ = _capacity(CASES[0], mu, (1.0, 0.0))
    d = check_duality(r, cts, dead, live, dim=3, origin=(0.0, 0.0, 0.0), k=8)
    assert d["admissible"] and d["duality_gap"] < 1e-9 * max(1.0, r.alpha)
    assert d["complementarity"] < 1e-9 * max(1.0, r.alpha)


@pytest.mark.parametrize("geom_scale,load_scale", [(1.0, 1.0), (1e-3, 1.0), (1.0, 100.0),
                                                   (1e-3, 1e4), (1e3, 1e-2)])
def test_capacity_ratio_is_invariant_to_units(geom_scale, load_scale):
    """纪律 B 的尺度格子：几何 ×1e-3/×1e3、荷载 ×1e2/×1e4，承载比 α/(W·load_scale) 不变。"""
    for mu in (0.3, 1.5):
        r, *_ = _capacity(CASES[0], mu, (1.0, 0.0), geom_scale=geom_scale, load_scale=load_scale)
        assert r.status == "optimal"
        # 恒载与活荷载同乘 load_scale ⇒ 荷载因子 α 本身就是不变量（不要再除 load_scale）
        assert r.alpha == pytest.approx(min(mu, 1.0) * W, rel=1e-9)


@pytest.mark.parametrize("side", ["a", "b", "mid"])
def test_contact_point_side_is_irrelevant_at_zero_gap(side):
    r, *_ = _capacity(CASES[0], 1.5, (1.0, 0.0), side=side)
    assert r.alpha == pytest.approx(W, abs=1e-9)


def test_gate_has_teeth_removing_the_rear_edge_makes_the_block_unsupportable():
    """牙：去掉后缘（x = −1）两个角，自重的作用线落在支承面边上/外，结果必须变。"""
    _, cts, *_ = _capacity(CASES[0], 0.3, (1.0, 0.0))
    rear = tuple(i for i, c in enumerate(cts) if c.point[0] < 0)
    assert len(rear) == 2
    r, *_ = _capacity(CASES[0], 0.3, (1.0, 0.0), drop=rear)
    assert r.status != "optimal" or abs(r.alpha - 0.3 * W) > 1e-3


@pytest.mark.parametrize("origin", [(0.0, 0.0, 0.0), (5.0, -3.0, 2.0), (-0.7, 0.4, -11.0)])
@pytest.mark.parametrize("mu", [0.3, 1.5])
def test_capacity_is_independent_of_the_moment_reference_point(origin, mu):
    """极限荷载与力矩参考点无关（物理不变量）。

    为什么要这条：cb2 的四个接触点关于原点**中心对称**，把接触列的力矩整体反号等价于把每个力挪到 −p，
    四角互相置换、列集合不变——所以"接触侧力矩写反 / 接触列忘了减参考点"这类缺陷在原点取对称中心时
    **根本不可见**（2026-09-24 实测：该变异下本文件其余测试全绿）。参考点挪到非对称处，它们就露馅。
    """
    r, *_ = _capacity(CASES[0], mu, (1.0, 0.0), origin=origin)
    assert r.status == "optimal"
    assert r.alpha == pytest.approx(min(mu, 1.0) * W, abs=1e-9)
