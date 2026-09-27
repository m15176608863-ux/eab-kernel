"""M0.3 极限分析组的门（G6 第二轮，2026-09-27）：输入校验与"自带上下限自校验"。

G6 第二轮对 814fdea 的三条 major：
  · `LimitContact.normal` 不检查也不归一：三维摩擦与黏聚承载力随 |n| 缩放，自校验放行
    → `test_normal_length_does_not_change_the_capacity`；
  · 自校验只查机构一侧，不查静力平衡；LP 列代码丢了参考点时 α = 15（闭式 10）照样 ok，纪律 E 的参考点门因 limit_load
    总在形心（cb2 的对称中心）求解而失明 → `test_self_check_catches_columns_that_lose_the_reference_point`、
    `test_tipping_capacity_of_a_translated_block_matches_the_closed_form`；
  · 自校验在调用方坐标系里判定，尺度被 |ω|·|o′ − o| 放大，UTM 下放行 α×0.5、×2 与贯入的机构
    → `test_self_check_rejects_wrong_answers_at_engineering_coordinates`。
oracle 是闭式（倾覆 α = W·b/h、滑动 α = μW）与手工构造的错解；不经被测的列代码。
"""

from math import cos, pi, sin

import pytest

import eab.limit as LM
from eab.limit import LimitContact, check_duality, limit_load, mechanism_is_admissible, wrench


def _box(T=(0.0, 0.0, 0.0), mu=0.6, W=10.0, h=2.0, cohesion=0.0, nscale=1.0):
    """底面 2 × 1.2、四角接触的方块，整体平移 T；推力沿 +x 作用在底面中心上方 h 处，恒载过底面中心。
    μ 大时倾覆控制：绕 +x 侧的棱转，α·h = W·1 ⇒ α = W/h；μ 小时滑动：α = μW（+ ΣcA）。"""
    n = (0.0, 0.0, nscale)
    cts = [LimitContact((T[0] + sx, T[1] + 0.6 * sy, T[2]), n, mu, cohesion=cohesion, area=(1.0 if cohesion else 0.0))
           for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    o = (0.0, 0.0, 0.0)
    dead = wrench((0.0, 0.0, -W), (T[0], T[1], T[2] + 0.5), o, 3)
    live = wrench((1.0, 0.0, 0.0), (T[0], T[1], T[2] + h), o, 3)
    return cts, dead, live


@pytest.mark.parametrize("nscale", [4.0, 1e-3, 1.0 + 2.0 ** -40])
def test_normal_length_does_not_change_the_capacity(nscale):
    """法向在构造时归一化：同一物理问题，法向只差长度，α 必须相同。旧版 |n| = 4 时三维摩擦 α 从 0.5 变 0.125，
    二维黏聚 |n| = 1e-3 时 α 从 1 变 0.001，自校验照样 ok。"""
    ref = limit_load(*_box(mu=0.05), dim=3, k=8).alpha
    r = limit_load(*_box(mu=0.05, nscale=nscale), dim=3, k=8)
    assert r.alpha == pytest.approx(ref, rel=1e-12) and ref == pytest.approx(0.5, rel=1e-12)
    o = (0.0, 0.0)
    cts1 = [LimitContact((0.0, 0.0), (0.0, 1.0), 0.0, cohesion=1.0, area=1.0)]
    ctsn = [LimitContact((0.0, 0.0), (0.0, nscale), 0.0, cohesion=1.0, area=1.0)]
    d, l = wrench((0.0, -1.0), o, o, 2), wrench((1.0, 0.0), o, o, 2)
    assert limit_load(ctsn, d, l, dim=2).alpha == pytest.approx(limit_load(cts1, d, l, dim=2).alpha, rel=1e-12)


@pytest.mark.parametrize("bad", [(0.0, 0.0, 0.0), (float("inf"), 0.0, 1.0), (float("nan"), 0.0, 1.0)])
def test_a_degenerate_normal_is_rejected(bad):
    with pytest.raises(ValueError, match="normal"):
        LimitContact((0.0, 0.0, 0.0), bad, 0.5)


@pytest.mark.parametrize("T", [(5.0, -3.0, 2.0), (-0.7, 0.4, -11.0), (5e5, 4.4e6, 100.0)])
def test_tipping_capacity_of_a_translated_block_matches_the_closed_form(T):
    """纪律 E：LP 实际在接触形心求解，所以参考点门要让**形心**离开原点（旧门只挪调用方原点，cb2 的形心就是对称中心，
    丢参考点的列代码不可见）。μ = 1 时倾覆控制：α = W/h = 5；μ = 0.05 时滑动：α = μW = 0.5。"""
    for mu, h, closed in ((1.0, 2.0, 5.0), (0.05, 2.0, 0.5)):
        r = limit_load(*_box(T=T, mu=mu, h=h), dim=3, k=8)
        assert r.status == "optimal" and r.alpha == pytest.approx(closed, rel=1e-9), (T, mu, r.alpha)


@pytest.mark.parametrize("T", [(0.3, 0.0, 0.0), (0.0, 0.0, 0.3), (0.5, 0.2, 0.1)])
@pytest.mark.parametrize("mu,h", [(1.0, 2.0), (0.05, 2.0), (0.4, 1.0)])
def test_self_check_catches_columns_that_lose_the_reference_point(monkeypatch, T, mu, h):
    """静力一侧的牙：把 LP 的精确列代码改成"力矩关于全局原点、忘了减形心"（G6 第二轮复核者的变异）。形心离原点不远时
    LP 仍报 optimal、α 却是错的，机构一侧与错列自洽，只有静力残差看得见——limit_load 必须抛错，不许返回。
    （形心离原点远时同一变异让 LP 直接报 infeasible，自校验只管 optimal，那一格由上面的平移倾覆闭式门看护。）"""
    real = LM._exact_wrench
    monkeypatch.setattr(LM, "_exact_wrench", lambda force, point, origin, dim: real(force, point, (0.0,) * dim, dim))
    with pytest.raises(RuntimeError, match="self-check"):
        limit_load(*_box(T=T, mu=mu, h=h), dim=3, k=8)


def _utm_block():
    T = (5e5, 4.4e6, 100.0)
    cts, dead, live = _box(T=T, mu=0.4, cohesion=2.0)
    r = limit_load(cts, dead, live, dim=3, k=8)
    assert r.status == "optimal"
    return T, cts, dead, live, r


@pytest.mark.parametrize("factor", [0.0, 0.5, 0.999, 1.001, 2.0])
def test_self_check_rejects_wrong_answers_at_engineering_coordinates(factor):
    """自校验在接触形心判定、用物理尺度：UTM 坐标下（块 2 m、离原点 4.4e6 m）错一个 α 也要抓到。
    旧版在调用方坐标系里判定，尺度被 ~|p|/L = 4e6 放大，α×0、×0.5、×2 全部放行。"""
    T, cts, dead, live, r = _utm_block()
    assert check_duality(r, cts, dead, live, dim=3, k=8)["ok"]
    r.alpha *= factor
    d = check_duality(r, cts, dead, live, dim=3, k=8)
    assert not d["ok"], (factor, d)


def test_self_check_rejects_a_penetrating_mechanism_at_engineering_coordinates():
    """机构叠加 30% 的法向贯入速度（沿 −z）：两个判据都必须拒绝。旧版在 UTM 坐标下两者都放行。"""
    T, cts, dead, live, r = _utm_block()
    v = max(abs(x) for x in r.mechanism[:3])
    r.mechanism = [r.mechanism[0], r.mechanism[1], r.mechanism[2] - 0.3 * v] + list(r.mechanism[3:])
    assert not mechanism_is_admissible(r.mechanism, cts, dim=3, k=8, row_duals=r.row_duals)
    assert not check_duality(r, cts, dead, live, dim=3, k=8)["ok"]


def test_the_limit_load_self_check_raises_on_an_injected_error_at_engineering_coordinates(monkeypatch):
    """limit_load 内置自检的牙：在 LP 结果上把 α 注入 ×0.999（真实调用路径），UTM 坐标下也必须抛错。"""
    real = LM.maximize

    def skew(A, b, c, **kw):
        res = real(A, b, c, **kw)
        if res.status == "optimal":
            ia = [j for j, cj in enumerate(c) if cj != 0.0][0]
            res.x = list(res.x)
            res.x[ia] *= 0.999
        return res

    T = (5e5, 4.4e6, 100.0)
    cts, dead, live = _box(T=T, mu=0.4, cohesion=2.0)
    monkeypatch.setattr(LM, "maximize", skew)
    with pytest.raises(RuntimeError, match="self-check"):
        limit_load(cts, dead, live, dim=3, k=8)


def _tipping_2d(T, s=1.0):
    """二维地面上的块：W = 10、宽 2s、高 3s、μ = 0.8，推力在顶部——倾覆控制，α = W·(宽/2)/高 = 10/3。"""
    W, BW, BH, mu = 10.0, 2.0 * s, 3.0 * s, 0.8
    o = (0.0, 0.0)
    cts = [LimitContact((T[0] - BW / 2, T[1]), (0.0, 1.0), mu), LimitContact((T[0] + BW / 2, T[1]), (0.0, 1.0), mu)]
    return cts, wrench((0.0, -W), (T[0], T[1] + BH / 2), o, 2), wrench((1.0, 0.0), (T[0], T[1] + BH), o, 2)


@pytest.mark.parametrize("T", [(0.0, 0.0), (5e5, 4.4e6)])
@pytest.mark.parametrize("s", [1.0, 0.01])
@pytest.mark.parametrize("frac", [0.01, 0.3])
def test_a_penetrating_tipping_mechanism_is_rejected_at_any_site(T, s, frac):
    """倾覆机构（有转动）叠加向下平动、两个接触都以 frac × 接触速度贯入：两个判据在任何场址都必须拒绝。
    G6 第二轮复核者的 cd2.py：旧版在调用方坐标系里判定，机构的平动分量 v = −ω × T ~ |ω|·|T| 把尺度放大 ~|p|/L，
    UTM 下 100% 贯入仍判容许（块缩小到 s = 0.01 时更甚）；现在在接触形心判定。"""
    import copy
    cts, dead, live = _tipping_2d(T, s)
    r = limit_load(cts, dead, live, dim=2)
    # 闭式对照放宽到 1e-6：2 cm 的块放在 5e5 m 处，接触点坐标的舍入（~u·5e5 = 6e-11）相对块宽已是 6e-9，是输入本身的精度
    assert r.alpha == pytest.approx(10.0 / 3.0, rel=1e-6)
    y = list(r.mechanism)
    # 接触速度量级：机构对各锥棱列的功率（功率与参考点无关，列在接触形心处按手算构造，不经被测的列代码）
    oc = (T[0], T[1])
    vo = (y[0] - y[2] * (oc[1] - 0.0), y[1] + y[2] * (oc[0] - 0.0))      # 机构平移到形心：v' = v − d × ω
    vmax = max(abs(vo[0] * g[0] + vo[1] * g[1] + y[2] * ((p[0] - oc[0]) * g[1] - (p[1] - oc[1]) * g[0]))
               for p in (ct.point for ct in cts) for g in ((0.8, 1.0), (-0.8, 1.0)))
    y[1] -= frac * vmax
    rr = copy.copy(r)
    rr.mechanism = y
    assert not mechanism_is_admissible(y, cts, dim=2)
    assert not check_duality(rr, cts, dead, live, dim=2)["ok"]
