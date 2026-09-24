"""默认容差下的普通输入不许抛错（G6 复核 G2/G3 的回归门，2026-09-25）。

背景：M0.2 第一版把每列的虚功率除以**该列自己**的尺度 Σ|y_i w_ij| 做相对判定。与机构正交的列（例如倾覆时
基面上的黏聚列）精确功率与尺度都为 0，算出来是 噪声/噪声 ≈ ±1——正确的最优解被判"对偶不可行 / 不容许"，
limit_load 在单位尺度的普通块体上抛 RuntimeError（验证者物理模糊测试 69/2000，而修复前 0/2000，
且那 69 个修复前答案都经独立证书核验为最优）。修法见 lp._Revised.noise（范数型舍入噪声线）与
limit._speed_scale（机构特征速度 V̂）。

两道门：
  · 验证者抽出的两个具体反例，承载力必须等于修复前经独立证书核验的最优值；
  · 同一个物理模糊生成器（3–5 个不同基面接触、法向 +z、单位尺度、随机 μ / 黏聚 / 推力方向与高度；
    二维 2–3 个接触），固定种子，**零抛错**且每个结果过自校验。
"""

import random
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
    """sin(π) = 1.22e-16：θ = π 的"水平"推力在浮点里带一个舍入级的竖向分量。单点接触撑不住偏心自重
    （物理上不可行），浮点 LP 却能用 α = 1/1.22e-16 = 8.17e15 让 α·1.22e-16 = 1 托住单位自重——
    浮点意义上的真最优，物理上的荒谬值（验证者模糊测试 limfuzz 种子 11 的 7 例，修复前基线答 infeasible，
    M0.2 返修前曾静默返回 optimal α ≈ 8e15）。可分辨性判据必须把它判回 infeasible，而不是给一个天文数字。"""
    cts = [LimitContact((1.0, 0.0), (sin(1.2), cos(1.2)), 1.0)]
    dead = wrench((0.0, -1.0), (0.0, 0.7), (0.0, 0.0), 2)
    live = wrench((cos(pi), sin(pi)), (0.0, 0.0), (0.0, 0.0), 2)
    assert sin(pi) != 0.0                                   # 前提：舍入级分量确实存在
    r = limit_load(cts, dead, live, dim=2, k=8)
    assert r.status == "infeasible", (r.status, r.alpha)
    # 同一几何、推力写成精确水平 (−1, 0)：同样不可行（与舍入无关的物理答案）
    r0 = limit_load(cts, dead, wrench((-1.0, 0.0), (0.0, 0.0), (0.0, 0.0), 2), dim=2, k=8)
    assert r0.status == "infeasible"


@pytest.mark.parametrize("seed", [11])
def test_broad_fuzz_has_no_astronomical_load_factors(seed):
    """验证者的宽模糊生成器（1–5 个任意朝向接触、带黏聚、W ∈ {1, 10}）：optimal 的荷载因子不许超过
    自然尺度的 1e10 倍——那种数只可能来自舍入级的荷载分量。1000 例，零抛错。"""
    rng = random.Random(seed)
    raised, huge = [], []
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
            raised.append((t, str(e)[:80])); continue
        if r.status == "optimal" and r.alpha > 1e10 * (W + 2.5 * nc):
            huge.append((t, r.alpha))
    assert raised == [], raised[:5]
    assert huge == [], huge[:5]
