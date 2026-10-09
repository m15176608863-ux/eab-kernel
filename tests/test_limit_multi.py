"""M1 · 多体极限分析的门。oracle：纸笔闭式（叠放块的滑/倾覆、成排块的整体滑动）、单体版（`limit_load`）、
刚体平移不变性（纪律 F）、注入错解的自校验（牙）。全部不经被测的列代码构造。"""

from __future__ import annotations

import pytest

import eab.limit_multi as LM
from eab.limit import LimitContact, limit_load, wrench
from eab.limit_multi import (BodyContact, LimitBody, check_duality_multi, limit_load_multi,
                             mechanism_is_admissible_multi)

O2 = (0.0, 0.0)
O3 = (0.0, 0.0, 0.0)


def _shift(p, T):
    return tuple(a + b for a, b in zip(p, T))


# ---------------------------------------------------------------- 单体退化：与 limit_load 相同

@pytest.mark.parametrize("mu,h", [(0.8, 3.0), (0.2, 3.0), (0.8, 0.5)])
def test_single_body_reduces_to_limit_load_2d(mu, h):
    cts = [LimitContact((-1.0, 0.0), (0.0, 1.0), mu), LimitContact((1.0, 0.0), (0.0, 1.0), mu)]
    dead, live = wrench((0.0, -10.0), (0.0, 1.5), O2, 2), wrench((1.0, 0.0), (0.0, h), O2, 2)
    r1 = limit_load(cts, dead, live, dim=2)
    r2 = limit_load_multi([LimitBody(dead, live)], [BodyContact(c, 0, None) for c in cts], dim=2)
    assert r2.status == "optimal" and r2.alpha == pytest.approx(r1.alpha, rel=1e-12)
    assert r2.alpha == pytest.approx(min(mu * 10.0, 10.0 / h), rel=1e-12)      # 滑动 μW 与倾覆 W·1/h 取小


def test_single_body_reduces_to_limit_load_3d():
    n = (0.0, 0.0, 1.0)
    cts = [LimitContact((sx, 0.6 * sy, 0.0), n, 0.05) for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    dead, live = wrench((0.0, 0.0, -10.0), (0.0, 0.0, 0.5), O3, 3), wrench((1.0, 0.0, 0.0), (0.0, 0.0, 2.0), O3, 3)
    r1 = limit_load(cts, dead, live, dim=3, k=8)
    r2 = limit_load_multi([LimitBody(dead, live)], [BodyContact(c, 0, None) for c in cts], dim=3, k=8)
    assert r2.alpha == pytest.approx(r1.alpha, rel=1e-12) and r1.alpha == pytest.approx(0.5, rel=1e-12)


# ---------------------------------------------------------------- 双层叠放块（纸笔闭式）

def _stack_2d(mu, W1, W2, T=(0.0, 0.0), push_h=2.0):
    """底块 2 × 1（重 W1）坐在地上，顶块 2 × 1（重 W2）坐在它上面，推力在顶块高 push_h 处。
    机构：顶块滑 α = μW2；整体滑 μ(W1+W2)；顶块倾覆 W2·1/1；整体倾覆 (W1+W2)·1/push_h。"""
    b1 = LimitBody(wrench((0.0, -W1), _shift((0.0, 0.5), T), O2, 2), [0.0] * 3)
    b2 = LimitBody(wrench((0.0, -W2), _shift((0.0, 1.5), T), O2, 2), wrench((1.0, 0.0), _shift((0.0, push_h), T), O2, 2))
    bcs = [BodyContact(LimitContact(_shift((sx, 0.0), T), (0.0, 1.0), mu), 0, None) for sx in (-1.0, 1.0)]
    bcs += [BodyContact(LimitContact(_shift((sx, 1.0), T), (0.0, 1.0), mu), 1, 0) for sx in (-1.0, 1.0)]
    return [b1, b2], bcs, min(mu * W2, mu * (W1 + W2), W2, (W1 + W2) / push_h)


@pytest.mark.parametrize("mu,W1,W2,push_h", [(0.3, 30.0, 10.0, 2.0), (0.8, 30.0, 10.0, 2.0), (1.2, 30.0, 10.0, 2.0),
                                              (0.5, 5.0, 10.0, 2.0), (2.0, 4.0, 10.0, 2.0), (0.9, 30.0, 10.0, 1.5)])
def test_two_stacked_blocks_match_the_closed_form(mu, W1, W2, push_h):
    bodies, bcs, want = _stack_2d(mu, W1, W2, push_h=push_h)
    r = limit_load_multi(bodies, bcs, dim=2)
    assert r.status == "optimal" and r.alpha == pytest.approx(want, rel=1e-12), (r.alpha, want)
    assert check_duality_multi(r, bodies, bcs, dim=2)["ok"]


def test_two_stacked_blocks_modes_are_read_off_the_mechanism():
    """μ = 0.3：顶块滑、底块不动；μ = 1.2：顶块绕自己的底角倾覆、底块不动；W1 很小时整体滑。"""
    bodies, bcs, _ = _stack_2d(0.3, 30.0, 10.0)
    r = limit_load_multi(bodies, bcs, dim=2)
    assert r.mechanisms[0] == pytest.approx([0.0, 0.0, 0.0], abs=1e-12)
    assert r.mechanisms[1][0] == pytest.approx(1.0) and r.mechanisms[1][2] == pytest.approx(0.0, abs=1e-12)
    bodies, bcs, _ = _stack_2d(1.2, 30.0, 10.0)
    r = limit_load_multi(bodies, bcs, dim=2)
    assert r.mechanisms[0] == pytest.approx([0.0, 0.0, 0.0], abs=1e-12) and abs(r.mechanisms[1][2]) > 0.1
    bodies, bcs, want = _stack_2d(0.5, 5.0, 10.0)                       # 整体滑 0.5·15 = 7.5 < 顶块滑 5？不——顶块滑 5 更小
    assert want == 5.0


@pytest.mark.parametrize("T", [(5e5, 4.4e6), (-3.0e3, 7.5e2)])
def test_stack_capacity_is_independent_of_where_the_blocks_sit(T):
    """纪律 F / E：整体平移到工程坐标，α 不变（内部参考点是接触形心，荷载精确平移）。"""
    for mu in (0.3, 1.2):
        bodies, bcs, want = _stack_2d(mu, 30.0, 10.0, T=T)
        r = limit_load_multi(bodies, bcs, dim=2)
        assert r.alpha == pytest.approx(want, rel=1e-9), (T, mu, r.alpha, want)


# ---------------------------------------------------------------- 成排块：接触力经相邻块传递

def _row_2d(mu, n=3, W=10.0):
    """n 个 1 × 1 的块并排坐在地上，推力作用在最左块左侧面中点、指向 +x。块间竖直面接触（两角点）。
    推力高 0.5，整体倾覆不可能先于滑动：α = μ·n·W。"""
    bodies = [LimitBody(wrench((0.0, -W), (i + 0.5, 0.5), O2, 2), wrench((1.0, 0.0), (0.0, 0.5), O2, 2) if i == 0 else [0.0] * 3)
              for i in range(n)]
    bcs = []
    for i in range(n):
        bcs += [BodyContact(LimitContact((i + sx, 0.0), (0.0, 1.0), mu), i, None) for sx in (0.0, 1.0)]
    for i in range(n - 1):
        # 块 i 与块 i+1 的竖直面：右块推左块的方向是 −x（a = i，b = i + 1）
        bcs += [BodyContact(LimitContact((i + 1.0, y), (-1.0, 0.0), mu), i, i + 1) for y in (0.0, 1.0)]
    return bodies, bcs, mu * n * W


@pytest.mark.parametrize("mu,n", [(0.5, 3), (0.2, 4), (0.7, 2)])
def test_a_row_of_blocks_slides_as_a_whole(mu, n):
    bodies, bcs, want = _row_2d(mu, n)
    r = limit_load_multi(bodies, bcs, dim=2)
    assert r.alpha == pytest.approx(want, rel=1e-12), (r.alpha, want)
    # 机构：全部块同速滑动——关联流动下滑动必带剪胀 v_y = μ·v_x（纯平动 (1, 0, 0) 对锥棱 n − μt 的功率是 −μ，不容许）；
    # 块间竖直面相对速度为零。这个机构必属对偶最优面：容许且上限 = ΣW·μ = α
    v = [[1.0, mu, 0.0]] * n
    assert mechanism_is_admissible_multi(v, bcs, dim=2)
    assert not mechanism_is_admissible_multi([[1.0, 0.0, 0.0]] * n, bcs, dim=2)
    ground_x = sum(f[0] for f, bc in zip(r.contact_forces, bcs) if bc.body_b is None)
    assert ground_x == pytest.approx(-want, rel=1e-9)                 # 地面总摩擦 = α


def test_row_side_contacts_carry_the_push_down_the_chain():
    """三块成排：第一个块间接触传递的水平力 F 在 μ·2W（块间无竖向摩擦）与 μ·2W/(1 − μ²)（块间竖向摩擦把法向荷载
    从块 0 挪到块 1、2，且 F ≤ μ(2W + μF)）之间——接触力分布**不唯一**，LP 给出其中一个可行的；
    第二个块间接触同理在 μW 与 μW/(1 − μ²) 之间。α 本身唯一。"""
    mu = 0.5
    bodies, bcs, want = _row_2d(mu, 3)
    r = limit_load_multi(bodies, bcs, dim=2)
    side01 = -sum(f[0] for f, bc in zip(r.contact_forces, bcs) if (bc.body_a, bc.body_b) == (0, 1))
    side12 = -sum(f[0] for f, bc in zip(r.contact_forces, bcs) if (bc.body_a, bc.body_b) == (1, 2))
    assert mu * 20.0 - 1e-9 <= side01 <= mu * 20.0 / (1 - mu * mu) + 1e-9, side01
    assert mu * 10.0 - 1e-9 <= side12 <= mu * 10.0 / (1 - mu * mu) + 1e-9, side12


# ---------------------------------------------------------------- 三维：叠放的两个方块

def _stack_3d(mu, W1=30.0, W2=10.0, push=(1.0, 0.0, 0.0)):
    n = (0.0, 0.0, 1.0)
    b1 = LimitBody(wrench((0.0, 0.0, -W1), (0.0, 0.0, 0.5), O3, 3), [0.0] * 6)
    b2 = LimitBody(wrench((0.0, 0.0, -W2), (0.0, 0.0, 1.5), O3, 3), wrench(push, (0.0, 0.0, 2.0), O3, 3))
    bcs = [BodyContact(LimitContact((sx, 0.6 * sy, 0.0), n, mu), 0, None) for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    bcs += [BodyContact(LimitContact((sx, 0.6 * sy, 1.0), n, mu), 1, 0) for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    return [b1, b2], bcs


@pytest.mark.parametrize("mu,want", [(0.3, 3.0), (0.8, 8.0), (1.5, 10.0)])
def test_two_stacked_boxes_3d(mu, want):
    """推力沿 +x 正对一条锥棱（默认切向基架 t₁ = x），滑动承载精确 μW2；倾覆 W2·1/1 = 10。"""
    bodies, bcs = _stack_3d(mu)
    r = limit_load_multi(bodies, bcs, dim=3, k=8)
    assert r.alpha == pytest.approx(want, rel=1e-12), (r.alpha, want)
    assert check_duality_multi(r, bodies, bcs, dim=3, k=8)["ok"]


# ---------------------------------------------------------------- 自校验的牙

def test_self_check_raises_on_an_injected_wrong_alpha(monkeypatch):
    real = LM.maximize

    def skew(A, b, c, **kw):
        res = real(A, b, c, **kw)
        if res.status == "optimal":
            ia = [j for j, cj in enumerate(c) if cj != 0.0][0]
            res.x = list(res.x)
            res.x[ia] *= 0.999
        return res
    monkeypatch.setattr(LM, "maximize", skew)
    bodies, bcs, _ = _stack_2d(0.8, 30.0, 10.0, T=(5e5, 4.4e6))
    with pytest.raises(RuntimeError, match="self-check"):
        limit_load_multi(bodies, bcs, dim=2)


def _mutant_module(old: str, new: str):
    """把缺陷注入 limit_multi 的源码（恰好命中一次），编译成独立模块。"""
    import sys
    import types
    from pathlib import Path
    src = Path(LM.__file__).read_text(encoding="utf-8")
    assert src.count(old) == 1, old
    mod = types.ModuleType("eab._limit_multi_mutant")
    mod.__package__ = "eab"
    mod.__file__ = LM.__file__
    sys.modules[mod.__name__] = mod
    exec(compile(src.replace(old, new), LM.__file__, "exec"), mod.__dict__)
    return mod


def test_self_check_catches_a_column_that_forgets_the_reaction():
    """变异：装配 LP 时忘了把反作用 −w 记到 b 体上（多体的核心）。LP 照样 optimal（顶块的方程完好，α = μW2），
    但底块的平衡在真实列下不成立——静力一侧必须抓到并抛错。"""
    mod = _mutant_module("                    if b == i:\n                        row[j] -= Cx[j][r]\n",
                         "                    if False:\n                        row[j] -= Cx[j][r]\n")
    bodies, bcs, _ = _stack_2d(0.8, 30.0, 10.0)
    with pytest.raises(RuntimeError, match="self-check"):
        mod.limit_load_multi(bodies, bcs, dim=2)
    assert limit_load_multi(bodies, bcs, dim=2).alpha == pytest.approx(8.0)


def test_penetrating_relative_motion_is_not_admissible():
    bodies, bcs, _ = _stack_2d(0.3, 30.0, 10.0)
    # 顶块向下压入底块（相对法向速度为负）
    assert not mechanism_is_admissible_multi([[0.0, 0.0, 0.0], [0.0, -1.0, 0.0]], bcs, dim=2)
    # 底块向上顶入顶块
    assert not mechanism_is_admissible_multi([[0.0, 1.0, 0.0], [0.0, 0.0, 0.0]], bcs, dim=2)
    # 两块一起向上平动：对地面分离、块间相对速度为零——容许
    assert mechanism_is_admissible_multi([[0.0, 1.0, 0.0], [0.0, 1.0, 0.0]], bcs, dim=2)


def test_bad_body_indices_are_rejected():
    bodies, bcs, _ = _stack_2d(0.3, 30.0, 10.0)
    with pytest.raises(ValueError):
        limit_load_multi(bodies, [BodyContact(bcs[0].contact, 2, None)], dim=2)
    with pytest.raises(ValueError):
        limit_load_multi(bodies, [BodyContact(bcs[0].contact, 1, 1)], dim=2)
