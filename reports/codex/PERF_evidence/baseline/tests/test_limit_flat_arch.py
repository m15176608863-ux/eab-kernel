"""M1 · 刚性竖直台肩之间的平拱：关联流动下自锁、承载无限（README L3 行的声称此前没有门，G6 第五轮 minor）。

几何：跨度 2、厚 0.3 的平拱由 3 块矩形块组成，竖缝在 x = 2/3、4/3；两端贴着刚性竖直台肩（x = 0、x = 2）。自重 = 10 × 面积，
活荷载是中间块顶面中点的竖向集中力。

独立论证（不经 LP）：关联流动下缝上的滑动必伴随张开（法向速度 ≥ |切向速度|/μ … 精确地说，相对速度落在锥里），
跨度被两道刚性台肩卡死，各缝与两端的张开量之和必须为零 ⇒ 每处张开都为零 ⇒ 没有滑动；转动在一个角点张开就在另一个角点闭合（贯入），
也不容许——不存在非零的容许机构，上限定理给不出有限上限，LP 报 unbounded。μ = 0 时没有锥宽，竖缝可以无张开地滑动，
自重都传不到台肩，LP 报 infeasible。这是关联极限分析对楔住体系的已知高估（真实的平拱由压碎或台肩变形控制）。
"""

from __future__ import annotations

import pytest

from eab.limit import LimitContact, wrench
from eab.limit_multi import BodyContact, LimitBody, limit_load_multi
from eab.lp import INFEASIBLE, UNBOUNDED

O = (0.0, 0.0)
SPAN, DEPTH, N = 2.0, 0.3, 3


def _problem(mu):
    w = SPAN / N
    bodies = []
    for i in range(N):
        area = w * DEPTH
        c = ((i + 0.5) * w, 0.5 * DEPTH)
        bodies.append(LimitBody(wrench((0.0, -10.0 * area), c, O, 2), [0.0] * 3))
    bodies[N // 2].live = wrench((0.0, -1.0), (0.5 * SPAN, DEPTH), O, 2)
    bcs = []
    for y in (0.0, DEPTH):
        bcs.append(BodyContact(LimitContact((0.0, y), (1.0, 0.0), mu), 0, None))             # 左台肩 → 块 0
        bcs.append(BodyContact(LimitContact((SPAN, y), (-1.0, 0.0), mu), N - 1, None))      # 右台肩 → 末块
        for j in range(1, N):
            bcs.append(BodyContact(LimitContact((j * w, y), (1.0, 0.0), mu), j, j - 1))      # 竖缝：块 j−1 → 块 j
    return bodies, bcs


@pytest.mark.parametrize("mu", (0.3, 0.7, 2.0))
def test_flat_arch_between_rigid_abutments_is_self_locking(mu):
    bodies, bcs = _problem(mu)
    res = limit_load_multi(bodies, bcs, dim=2)
    assert res.status == UNBOUNDED, (mu, res.status, res.alpha)


def test_frictionless_flat_arch_cannot_carry_its_own_weight():
    bodies, bcs = _problem(0.0)
    res = limit_load_multi(bodies, bcs, dim=2)
    assert res.status == INFEASIBLE, (res.status, res.alpha)
