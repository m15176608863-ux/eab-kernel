"""默认容差下的普通输入不许抛错（G6 复核 G2/G3 的回归门，2026-09-25）。

背景：M0.2 第一版把每列的虚功率除以**该列自己**的尺度 Σ|y_i w_ij| 做相对判定。与机构正交的列（例如倾覆时
基面上的黏聚列）精确功率与尺度都为 0，算出来是 噪声/噪声 ≈ ±1——正确的最优解被判"对偶不可行 / 不容许"，
limit_load 在单位尺度的普通块体上抛 RuntimeError（验证者物理模糊测试 69/2000，而修复前 0/2000，
且那 69 个修复前答案都经独立证书核验为最优）。修法见 lp._Revised.noise（范数型舍入噪声线）与
旧版 limit._speed_scale（机构特征速度 V̂）；E4 已由有理数自校验替代，不再用尺度判答案。

两道门：
  · 验证者抽出的两个具体反例，承载力必须等于修复前经独立证书核验的最优值；
  · 同一个物理模糊生成器（3–5 个不同基面接触、法向 +z、单位尺度、随机 μ / 黏聚 / 推力方向与高度；
    二维 2–3 个接触），固定种子，**零抛错**且每个结果过自校验。
"""

import random
from fractions import Fraction
from math import cos, pi, sin

import pytest

from eab.limit import LimitContact, check_duality, limit_load, wrench

# 验证者 regress_cases.json 原样（alpha = 修复前的答案，已由验证者用独立证书核验为最优）
REGRESS = {"24": {"cts": [[[0.5469846021808991, 0.4392188816736362, 0.0], [0.0, 0.0, 1.0], 0.9, 2.0, 0.5], [[1.1966915196876657, -0.06983067348564376, 0.0], [0.0, 0.0, 1.0], 0.9, 2.0, 0.5], [[0.774590180800578, -0.3926997358161415, 0.0], [0.0, 0.0, 1.0], 0.9, 2.0, 0.5], [[-1.490320629746732, 0.5579954450252667, 0.0], [0.0, 0.0, 1.0], 0.9, 2.0, 0.5]], "dead": [0.0, 0.0, -10.0, -1.336709793492794, 2.569864182306027, 0.0], "live": [-0.8698349233245408, -0.4933428890386384, 0.0, 0.4933428890386384, -0.8698349233245408, 0.12072382090652639], "dim": 3, "k": 6, "alpha": 3.600731029861168}, "14": {"cts": [[[1.1097337573834833, 0.3766739137438544, 0.0], [0.0, 0.0, 1.0], 0.9, 0.5, 0.5], [[1.4283665649058226, 0.9130329539528377, 0.0], [0.0, 0.0, 1.0], 0.9, 0.5, 0.5], [[0.054418291342069214, 0.058680161538791964, 0.0], [0.0, 0.0, 1.0], 0.9, 0.5, 0.5]], "dead": [0.0, 0.0, -10.0, -4.494623430784947, 8.641728712104584, 0.0], "live": [0.5026859039695168, 0.86446913302347, 0.0, -0.259340739907041, 0.15080577119085506, 0.7548391718956227], "dim": 3, "k": 4, "alpha": 6.809476475542803}}


@pytest.mark.parametrize("name", sorted(REGRESS))
def test_verifier_counterexamples_answer_with_the_certified_optimum(name):
    c = REGRESS[name]
    cts = [LimitContact(tuple(p), tuple(n), mu, cohesion=coh, area=area) for p, n, mu, coh, area in c["cts"]]
    r = limit_load(cts, c["dead"], c["live"], dim=c["dim"], k=c["k"])
    assert r.status == "optimal"
    assert r.alpha == pytest.approx(c["alpha"], rel=1e-9, abs=1e-12)


def _case(rng):
    dim = rng.choice([2, 3])
    mu = rng.choice([0.2, 0.4, 0.6, 0.9]); coh = rng.choice([0.0, 0.0, 0.5, 2.0])
    if dim == 3:
        nc = rng.randint(3, 5)
        pts = [(rng.uniform(-1.5, 1.5), rng.uniform(-1.0, 1.0), 0.0) for _ in range(nc)]
        cts = [LimitContact(p, (0.0, 0.0, 1.0), mu, cohesion=coh, area=(0.5 if coh else 0.0)) for p in pts]
        g = (sum(p[0] for p in pts) / nc, sum(p[1] for p in pts) / nc)
        o = (0.0, 0.0, 0.0)
        dead = wrench((0.0, 0.0, -10.0), (g[0], g[1], 0.6), o, 3)
        th = rng.uniform(0, 2 * pi); h = rng.choice([0.0, 0.3, 1.0])
        live = wrench((cos(th), sin(th), 0.0), (g[0] + rng.uniform(-0.3, 0.3), g[1] + rng.uniform(-0.3, 0.3), h), o, 3)
        k = rng.choice([4, 6, 8, 16])
    else:
        nc = rng.randint(2, 3)
        xs = sorted(rng.uniform(-1.5, 1.5) for _ in range(nc))
        cts = [LimitContact((x, 0.0), (0.0, 1.0), mu, cohesion=coh, area=(0.5 if coh else 0.0)) for x in xs]
        o = (0.0, 0.0)
        dead = wrench((0.0, -10.0), (sum(xs) / nc, 0.7), o, 2)
        sgn = rng.choice([1.0, -1.0])
        live = wrench((sgn, 0.0), (sum(xs) / nc + rng.uniform(-0.3, 0.3), rng.choice([0.0, 0.5, 1.5])), o, 2)
        k = 8
    return cts, dead, live, dim, k


@pytest.mark.parametrize("seed", [5, 11, 23])
def test_physical_fuzz_never_raises_at_the_default_tolerance(seed):
    """同一生成器、每个种子 300 例：零抛错；非 optimal 的只许是 infeasible（自重压在支承之外等真实不可承载情形）。"""
    rng = random.Random(seed)
    raised, bad = [], []
    for t in range(300):
        cts, dead, live, dim, k = _case(rng)
        try:
            r = limit_load(cts, dead, live, dim=dim, k=k)
        except RuntimeError as e:
            raised.append((t, str(e)[:80]))
            continue
        if r.status == "optimal":
            d = check_duality(r, cts, dead, live, dim=dim, k=k)
            if not d["ok"]:
                bad.append((t, d["worst_power_rel"], d["duality_gap_rel"], d["complementarity"]))
        else:
            assert r.status == "infeasible", (t, r.status)
    assert raised == [], raised[:5]
    assert bad == [], bad[:5]


def test_rounding_level_load_component_is_not_certified_as_capacity():
    """舍入级 sin(pi) 保留原问题精确 alpha=1/sin(pi)，邻域不可行另报，不篡改成 infeasible。"""
    cts = [LimitContact((1.0, 0.0), (sin(1.2), cos(1.2)), 1.0)]
    dead = wrench((0.0, -1.0), (0.0, 0.7), (0.0, 0.0), 2)
    live = wrench((cos(pi), sin(pi)), (0.0, 0.0), (0.0, 0.0), 2)
    assert sin(pi) != 0.0                                   # 前提：舍入级分量确实存在
    r = limit_load(cts, dead, live, dim=2, k=8)
    assert r.status == "optimal" and r.alpha.exact * Fraction(sin(pi)) == 1
    assert r.resolvability == "nearby_infeasible" and "infeasible" in r.resolvability_statuses
    assert check_duality(r,cts,dead,live,dim=2,k=8)["ok"]
    # 同一几何、推力写成精确水平 (−1, 0)：同样不可行（与舍入无关的物理答案）
    r0 = limit_load(cts, dead, wrench((-1.0, 0.0), (0.0, 0.0), (0.0, 0.0), 2), dim=2, k=8)
    assert r0.status == "infeasible"


@pytest.mark.parametrize("v,expect", [(1e-6, "optimal"), (1e-9, "optimal"), (1e-10, "raise"), (1e-11, "raise"),
                                      (1e-13, "raise"), (1e-14, "raise"), (3e-15, "infeasible"), (1e-15, "infeasible"),
                                      (5e-16, "infeasible"), (2e-16, "infeasible")])
def test_small_load_component_resolvability_has_three_regimes(v, expect):
    """三个分辨性报告区间不改任何原问题答案；每格均精确核 alpha*v=1 和静力/对偶证书。"""
    cts = [LimitContact((1.0, 0.0), (sin(1.2), cos(1.2)), 1.0)]
    dead = wrench((0.0, -1.0), (0.0, 0.7), (0.0, 0.0), 2)
    live = wrench((-1.0, v), (0.0, 0.0), (0.0, 0.0), 2)
    r = limit_load(cts,dead,live,dim=2,k=8)
    assert r.status == "optimal" and r.alpha.exact*Fraction(v) == 1
    assert check_duality(r,cts,dead,live,dim=2,k=8)["ok"]
    report={"optimal":"resolved","raise":"unresolved","infeasible":"nearby_infeasible"}[expect]
    assert r.resolvability == report
    if report == "resolved":
        assert r.uncertainty <= 1e-6
    elif report == "nearby_infeasible":
        assert "infeasible" in r.resolvability_statuses
    else:
        assert r.uncertainty > 1e-6 and r.resolvability_statuses == ("optimal","optimal")


def test_a_large_first_order_uncertainty_alone_does_not_reject(monkeypatch):
    """一阶 U 只是按**一个**最优机构算的界；对偶退化时最优机构不唯一，近奇异基上的机构分量可达 ~1e16，一阶 U 会虚高
    （09-27 宽模糊种子 11 #495：普通推力 (cos 1, sin 1) 的一阶 U = 28）。所以 U 超标时要推 ±16 倍舍入、精确重解，
    看 α 的**实际**变化再下结论。这里把一阶 U 强行设成 1（模拟退化机构），对一个本来稳定的问题（μ = 0.5 的地面上
    平推，α = μW）必须仍然认证，且报告的是实测不确定度。牙：只用一阶 U（不做精确重解），这道门就红。
    反面：同样注入之下，sin π 的原问题仍 optimal，但报告 nearby_infeasible（邻域不可行）。"""
    import eab.limit as LM
    monkeypatch.setattr(LM, "_live_uncertainty", lambda y, live, e: 1.0)
    o = (0.0, 0.0)
    cts = [LimitContact((-1.0, 0.0), (0.0, 1.0), 0.5), LimitContact((1.0, 0.0), (0.0, 1.0), 0.5)]
    r = limit_load(cts, wrench((0.0, -10.0), (0.3, 0.2), o, 2), wrench((1.0, 0.0), (0.0, 0.0), o, 2), dim=2, k=8)
    assert r.status == "optimal" and r.alpha == pytest.approx(5.0, rel=1e-15) and r.uncertainty <= 1e-6, r
    cts = [LimitContact((1.0, 0.0), (sin(1.2), cos(1.2)), 1.0)]
    r = limit_load(cts, wrench((0.0, -1.0), (0.0, 0.7), o, 2), wrench((cos(pi), sin(pi)), o, o, 2), dim=2, k=8)
    assert r.status == "optimal" and r.alpha.exact*Fraction(sin(pi)) == 1
    assert r.resolvability == "nearby_infeasible" and "infeasible" in r.resolvability_statuses


def _exact_status_alpha(cts, dead, live, dim, k):
    """同一 LP（形心参考点、黏聚列取力的单位、力矩精确）的精确状态与最优值；oracle 只用 Fraction
    （test_lp_certificates._exact_limit_lp / _exact_max）。"""
    from test_lp_certificates import _exact_limit_lp, _exact_max
    st, obj = _exact_max(*_exact_limit_lp(cts, dead, live, dim, k))
    return st, (float(obj) if obj is not None else None)


def _genuinely_unresolvable(cts, dead, live, dim, k, rng):
    """独立判定"活荷载差 1e-12 相对就答案大变"：四次**各分量独立**的随机扰动（力分量 ±1e-12·|F|，
    力矩分量 ±1e-12·(|M| + |F|·R)），精确状态有变或精确 α 的相对跳动 > 1e-6 即为真不可分辨。
    只转动荷载方向不够——绕作用点转保持"作用线过接触点"这种刀刃（宽模糊种子 11 #127 正是这样）。"""
    Fn = sum(v * v for v in live[:dim]) ** 0.5
    Mn = sum(v * v for v in live[dim:]) ** 0.5
    R = max(sum(v * v for v in ct.point) ** 0.5 for ct in cts)
    sc = [Fn] * dim + [Mn + Fn * R] * (len(live) - dim)
    base = _exact_status_alpha(cts, dead, live, dim, k)
    for _ in range(4):
        pert = [v + rng.choice((-1.0, 1.0)) * 1e-12 * s for v, s in zip(live, sc)]
        st = _exact_status_alpha(cts, dead, pert, dim, k)
        if st[0] != base[0]:
            return True
        if st[0] == "optimal" and abs(st[1] - base[1]) > 1e-6 * max(abs(base[1]), 1e-300):
            return True
    return False


@pytest.mark.parametrize("seed", [11])
def test_broad_fuzz_has_no_astronomical_load_factors(seed):
    """保留1000输入：精确答案可有天文值，但必须报告不可分辨，不得伪装稳定或改原status。
    原先可抛错的至多1%改为 unresolved 报告；每个大值与 unresolved 用独立 oracle 核原问题及邻域。
    """
    rng = random.Random(seed)
    raised, huge, unresolved = [], [], []
    for t in range(1000):
        dim = rng.choice([2, 3]); nc = rng.randint(1, 5); cts = []
        for i in range(nc):
            if dim == 2:
                p = (rng.choice([-1.0, -0.5, 0.0, 0.5, 1.0, 1.5]), rng.choice([0.0, 0.0, 0.5]))
                a = rng.choice([0.0, 0.0, 0.3, -0.4, 1.2, -1.0]); nrm = (sin(a), cos(a))
            else:
                p = (rng.choice([-1.0, 0.0, 1.0, 1.3]), rng.choice([-0.6, 0.0, 0.6]), rng.choice([0.0, 0.0, 0.4]))
                a, bb = rng.choice([0.0, 0.0, 0.3, -0.5, 1.0]), rng.choice([0.0, 0.0, 0.7, -0.2])
                nrm = (sin(a) * cos(bb), sin(a) * sin(bb), cos(a))
            coh = rng.choice([0.0, 0.0, 1.0, 2.5])
            cts.append(LimitContact(p, nrm, rng.choice([0.0, 0.2, 0.5, 1.0]), cohesion=coh, area=(1.0 if coh else 0.0)))
        o = (0.0,) * dim; W = rng.choice([1.0, 10.0])
        if dim == 2:
            dead = wrench((0.0, -W), (rng.choice([0.0, 0.2]), 0.7), o, 2); th = rng.choice([0.0, pi, 0.3, 2.0])
            live = wrench((cos(th), sin(th)), (0.0, rng.choice([0.0, 1.0])), o, 2)
        else:
            dead = wrench((0.0, 0.0, -W), (0.1, 0.0, 0.5), o, 3); th = rng.choice([0.0, 0.3, 1.0, 2.5])
            live = wrench((cos(th), sin(th), 0.0), (0.0, 0.0, rng.choice([0.0, 0.8])), o, 3)
        k = rng.choice([4, 5, 8])
        try:
            r = limit_load(cts, dead, live, dim=dim, k=k)
        except RuntimeError as e:
            raised.append((t, str(e)[:80], cts, dead, live, dim, k)); continue
        if r.status == "optimal" and r.alpha > 1e10 * (W + 2.5 * nc):
            huge.append((t,r,cts,dead,live,dim,k))
        if r.resolvability == "unresolved":
            unresolved.append((t,r,cts,dead,live,dim,k))
    assert raised == [],[x[:2] for x in raised]
    assert len(unresolved) <= 10,[x[:2] for x in unresolved]
    orng=random.Random(1000+seed)
    for t,r,cts,dead,live,dim,k in huge+unresolved:
        assert r.resolvability != "resolved",(t,r)
        assert _genuinely_unresolvable(cts,dead,live,dim,k,orng),(t,r)
        st,alpha=_exact_status_alpha(cts,dead,live,dim,k)
        assert r.status == st and r.alpha == pytest.approx(alpha,rel=4e-16),(t,r,st,alpha)
