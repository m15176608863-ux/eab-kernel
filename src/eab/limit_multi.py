"""L3 互补层第二块砖（M1）：**多体刚体极限分析**——各体的自由度并进同一组平衡方程。

单体版（`limit.py`）只做"一个动体对固定边界"。多体版里每个接触连接两个体 (a, b)，b 可以是固定边界（None）：
接触力 λ·g 作用在 a 上，反作用 −λ·g 作用在 b 上。LP：

    max α   s.t.   对每个体 i：Σ_{j: a_j = i} λ_j w_j − Σ_{j: b_j = i} λ_j w_j + W_dead,i + α·W_live,i = 0 ,  λ ≥ 0
                   每个黏聚接触：Σλ_coh + s = c·A

w_j = (g_j, (p_j − o′) × g_j) 关于**共同参考点** o′（全部接触点的形心）；各体的荷载旋量精确平移到 o′（`_exact_shift`），
接触列的力矩精确（`_exact_wrench`）——与单体版同一精确模型，LP 由 lp.py 对给定数据精确求解。

对偶：y = (y_1, …, y_nb, y_r)，y_i 是体 i 的虚速度旋量（关于 o′）。对偶可行性逐列是 (y_a − y_b)ᵀ w_j ≥ 0
（b 固定时 y_b = 0）：**相对速度不得贯入接触**；强对偶 α = −Σ_i y_iᵀW_dead,i + Σ y_r（外力功率 = 黏聚耗散）。
单体是 nb = 1、全部 b = None 的特例：`limit_load_multi` 对它给出与 `limit_load` 相同的 α（门：tests/test_limit_multi.py）。

自校验（`check_duality_multi`）：独立重建精确力矩列、逐体平衡、非负与黏聚上限；逐列相对功率、驱动、强对偶与互补全部用有理数核。
没有全局尺度、速度尺度或容差放宽，任意非零可表示错解都会拒绝。返回 float 视图附不可变 `exact` 见证，复制保留；算术/JSON 往返会丢失，
届时按新给定数核。`contact_forces` 与 `active` 只是截断显示（静力证书是 lambdas）。可分辨性筛查分别在各体接触形心/自身臂长上评估、
在本体舍入盒内推 ±16 倍舍入后精确移回 LP 公共参考点；其他体的跨度不计入本体噪声。
分辨性只报告 resolvability/resolvability_statuses，绝不改变原问题的精确 status/alpha；resolved 不是稳定性保证。

诚实条款（在单体版的基础上）：
- 刚体、小变形、接触位置不变——极限分析的标准前提；多体下"机构"是各体旋量的组合，**不唯一**（对偶最优面），读破坏模式要问
  候选机构是否属于最优面，不要读逐分量。
- 接触的 (a, b) 与法向约定：`normal` 是 b 推 a 的方向（b 固定时就是"固定体推动体"）。调用方给反了，LP 就在算另一个问题——
  本层无法察觉（法向的物理含义是输入）。`contacts_from_covers_multi` 给出的接触按盖的约定（B → A）自动取 a = A 体、b = B 体。
- 三维摩擦锥线性化、棱扇朝向、黏聚面积的条款与单体版相同。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
import math

from .limit import (_FLIP, _SELF_CHECK, _UNCERTAIN, LimitContact, _build_columns, _exact_shift,
                    _exact_wrench, _fl, _live_uncertainty, _norm, _twist_back, _twist_forward,
                    _wrench_rounding, wrench)
from .limit import _ExactFloat, _rational, _lp_values, _check_columns, _exact_duality_report
from .lp import OPTIMAL, UNBOUNDED, maximize

Vec = tuple[float, ...]


@dataclass(slots=True)
class LimitBody:
    """一个可动体：恒载与活荷载旋量（关于调用方的 origin，用 `limit.wrench` 造）。"""
    dead: list[float]
    live: list[float]
    label: str | None = None


@dataclass(slots=True)
class BodyContact:
    """多体接触：`contact` 的法向是 b 推 a 的方向；b = None 表示固定边界。"""
    contact: LimitContact
    body_a: int
    body_b: int | None = None


@dataclass(slots=True)
class MultiLimitResult:
    status: str
    alpha: float
    lambdas: list[float]                       # 列序 = 各接触依次的 `_build_columns` 列
    mechanisms: list[list[float]]              # 每个体的虚速度旋量（关于调用方的 origin）
    contact_forces: list[Vec] = field(default_factory=list)   # 作用在 a 上的合力
    active: list[tuple] = field(default_factory=list)
    iterations: int = 0
    row_duals: list[float] = field(default_factory=list)
    uncertainty: float = 0.0
    resolvability: str = "not_applicable"  # resolved / nearby_infeasible / unresolved; never changes status/alpha
    resolvability_statuses: tuple[str, ...] = ()  # exact statuses after minus/plus input-rounding perturbation


def contacts_from_covers_multi(covers, body_a: int, body_b: int | None, *, mu: float, side: str = "a") -> list[BodyContact]:
    """把一对体 (A = body_a, B = body_b) 之间的盖枚举接进来（盖法向 B → A，正是 b 推 a）。黏聚条款同单体版。"""
    from .limit import contacts_from_covers
    return [BodyContact(ct, body_a, body_b) for ct in contacts_from_covers(covers, mu=mu, side=side)]


def _centroid(bcs: list[BodyContact], origin: Vec, dim: int) -> Vec:
    if not bcs:
        return tuple(origin[:dim])
    return tuple(sum(bc.contact.point[i] for bc in bcs) / len(bcs) for i in range(dim))


def _check_bodies(bodies: list[LimitBody], bcs: list[BodyContact], dim: int) -> int:
    nw = 3 if dim == 2 else 6
    if not bodies:
        raise ValueError("need at least one body")
    for i, b in enumerate(bodies):
        if len(b.dead) != nw or len(b.live) != nw:
            raise ValueError(f"body {i}: dead/live must be {nw}-component wrenches for dim={dim}")
    for bc in bcs:
        if not 0 <= bc.body_a < len(bodies):
            raise ValueError(f"contact {bc.contact.label!r}: body_a={bc.body_a} out of range")
        if bc.body_b is not None and not 0 <= bc.body_b < len(bodies):
            raise ValueError(f"contact {bc.contact.label!r}: body_b={bc.body_b} out of range")
        if bc.body_b == bc.body_a:
            raise ValueError(f"contact {bc.contact.label!r}: a body cannot contact itself")
    return nw


def _pair_powers(y, yr, C, owners_ab, dim):
    """各体关于同一原点的有理数旋量，逐列精确相对功率；不存在全局速度容差。"""
    ys = [[_rational(v) for v in yi] for yi in y]
    rows = None if yr is None else [_rational(v) for v in yr]
    powers = []
    for j, (w, rj) in enumerate(zip(C.cols, C.row_of)):
        a, b = owners_ab[C.owner[j]]
        rel = [va - (ys[b][i] if b is not None else 0) for i,va in enumerate(ys[a])]
        extra = rows[rj] if rj is not None and rows is not None else 0
        powers.append(sum(v*wi for v,wi in zip(rel,w)) + extra)
    return powers


def _body_frames(contacts: list[BodyContact], nb: int, oc: Vec, dim: int):
    """各体自身的接触形心 o_i（无接触的体取 o′）、o_i − o′、臂长 max|p − o_i|。"""
    own = [[bc for bc in contacts if i in (bc.body_a, bc.body_b)] for i in range(nb)]
    oi = [_centroid(own[i], oc, dim) for i in range(nb)]
    di = [tuple(oi[i][q] - oc[q] for q in range(dim)) for i in range(nb)]
    arm = [max((_norm(tuple(bc.contact.point[q] - oi[i][q] for q in range(dim))) for bc in own[i]), default=0.0)
           for i in range(nb)]
    return oi, di, arm


def limit_load_multi(bodies: list[LimitBody], contacts: list[BodyContact], *, dim: int = 3,
                     origin: Vec | None = None, k: int = 8, tol: float = 1e-9,
                     lp_tol: float | None = None) -> MultiLimitResult:
    """多体极限荷载因子 α（见模块文档）。返回 optimal 前跑 `check_duality_multi`，不过即抛 RuntimeError。"""
    if origin is None:
        origin = (0.0,) * dim
    nw = _check_bodies(bodies, contacts, dim)
    nb = len(bodies)
    cts = [bc.contact for bc in contacts]
    owners_ab = [(bc.body_a, bc.body_b) for bc in contacts]
    oc = _centroid(contacts, origin, dim)
    dvec = tuple(oc[i] - origin[i] for i in range(dim))
    dead_x = [_exact_shift(list(b.dead), origin, oc, dim) for b in bodies]
    live_x = [_exact_shift(list(b.live), origin, oc, dim) for b in bodies]
    live_c = [[_fl(v) for v in lv] for lv in live_x]
    # 本体的形心与臂长；其他体的跨度不计入本体的输入噪声盒。
    oi, _, arms = _body_frames(contacts, nb, oc, dim)
    local_d = [tuple(Fraction(oi[i][q])-Fraction(oc[q]) for q in range(dim)) for i in range(nb)]
    local_live = [_exact_shift(b.live, origin, oi[i], dim) for i,b in enumerate(bodies)]
    radii = [arms[i] + _norm(tuple(oi[i][q]-origin[q] for q in range(dim))) for i in range(nb)]
    e_in = [_wrench_rounding(lv, dim, radii[i]) for i,lv in enumerate(local_live)]
    C = _build_columns(cts, oc, dim, k, unit_cohesion=True)
    Cx = [_exact_wrench(col[:dim], cts[C.owner[j]].point, oc, dim) for j, col in enumerate(C.cols)]
    capx = [Fraction(0)] * C.n_rows
    for j, rj in enumerate(C.row_of):
        if rj is not None:
            ct = cts[C.owner[j]]
            capx[rj] = Fraction(ct.cohesion) * Fraction(ct.area)
    ncols = len(C.cols)
    ia = ncols
    zero = Fraction(0)

    def _solve(live_v: list[list[Fraction]], sense: float = 1.0):
        ncol = ncols + 1 + C.n_rows
        AX = []
        bX = []
        for i in range(nb):
            for r in range(nw):
                row = [zero] * ncol
                for j in range(ncols):
                    a, b = owners_ab[C.owner[j]]
                    if a == i:
                        row[j] += Cx[j][r]
                    if b == i:
                        row[j] -= Cx[j][r]
                row[ia] = live_v[i][r]
                AX.append(row)
                bX.append(-dead_x[i][r])
        for r_i in range(C.n_rows):
            row = [zero] * ncol
            for j, rj in enumerate(C.row_of):
                if rj == r_i:
                    row[j] = Fraction(1)
            row[ia + 1 + r_i] = Fraction(1)
            AX.append(row)
            bX.append(capx[r_i])
        c = [0.0] * ncols + [sense] + [0.0] * C.n_rows
        A = [[_fl(v) for v in row] for row in AX]
        b = [_fl(v) for v in bX]
        kw = {} if lp_tol is None else {"tol": lp_tol}
        return maximize(A, b, c, exact=(AX, bX, c), **kw)

    def _ys(res):
        exact_y = _lp_values(res.y, res.exact_y)
        return [exact_y[i * nw:(i + 1) * nw] for i in range(nb)]

    def _U(ys):
        local_y = [_twist_forward(yi, di, dim) for yi,di in zip(ys,local_d)]
        flat_y = [v for yi in local_y for v in yi]
        flat_l = [v for lc in local_live for v in lc]
        flat_e = [v for ei in e_in for v in ei]
        return _live_uncertainty(flat_y, flat_l, flat_e)

    def _pushes(ys):
        local_y = [_twist_forward(yi, di, dim) for yi,di in zip(ys,local_d)]
        push_local = [[((yi > 0) - (yi < 0)) * Fraction(_FLIP) * ei
                       for yi,ei in zip(y,e)] for y,e in zip(local_y,e_in)]
        push = [_exact_shift(pv, oi[i], oc, dim) for i,pv in enumerate(push_local)]
        minus = [[li - pi for li, pi in zip(lv, pv)] for lv, pv in zip(live_x, push)]
        plus = [[li + pi for li, pi in zip(lv, pv)] for lv, pv in zip(live_x, push)]
        return _solve(minus), _solve(plus)

    r = _solve(live_x)
    if r.status == UNBOUNDED:
        rmin = _solve(live_x,-1.0)
        its = r.iterations+rmin.iterations
        U0, resolution, statuses = 0.0, "resolved", ()
        if rmin.status == OPTIMAL and _lp_values(rmin.x, rmin.exact_x)[ia] > 0:
            ys = _ys(rmin)
            U0 = _U(ys)
            if not math.isfinite(U0):
                resolution = "unresolved"
            elif U0 > _UNCERTAIN:
                rm,rp = _pushes(ys)
                its += rm.iterations+rp.iterations
                statuses = (rm.status,rp.status)
                resolution = ("nearby_infeasible" if "infeasible" in statuses else
                              "resolved" if rm.status == rp.status == UNBOUNDED else "unresolved")
        return MultiLimitResult(UNBOUNDED,float("inf"),[],[],iterations=its,uncertainty=U0,
                                resolvability=resolution,resolvability_statuses=statuses)
    if r.status != OPTIMAL:
        return MultiLimitResult(r.status,float("nan"),[],[],iterations=r.iterations)
    alpha = _lp_values(r.x, r.exact_x)[ia]
    ys = _ys(r)
    U = _U(ys)
    its, resolution, statuses = 0, "resolved", ()
    if not math.isfinite(U):
        resolution = "unresolved"
    elif U > _UNCERTAIN:
        rm,rp = _pushes(ys)
        its = rm.iterations+rp.iterations
        statuses = (rm.status,rp.status)
        if "infeasible" in statuses:
            resolution = "nearby_infeasible"
        elif rm.status == rp.status == OPTIMAL and alpha > 0.0:
            am = _lp_values(rm.x, rm.exact_x)[ia]
            ap = _lp_values(rp.x, rp.exact_x)[ia]
            U = _fl(max(abs(am-alpha), abs(ap-alpha))/(Fraction(_FLIP)*alpha))
            resolution = "resolved" if U <= _UNCERTAIN else "unresolved"
        else:
            resolution = "unresolved"
    rx, ry = _lp_values(r.x,r.exact_x), _lp_values(r.y,r.exact_y)
    alpha = _ExactFloat(rx[ia])
    raw = rx[:ncols]
    lam = [_ExactFloat(v / capx[rj] if rj is not None else v) for v, rj in zip(raw, C.row_of)]
    fvec = [tuple(raw[j] * C.cols[j][i] for i in range(dim)) for j in range(ncols)]
    fmag = [_norm(f) for f in fvec]
    fmax = max(fmag, default=0.0)
    on = [fm > tol * fmax for fm in fmag]
    forces: list[Vec] = [tuple(0.0 for _ in range(dim)) for _ in contacts]
    for j, ci in enumerate(C.owner):
        if on[j]:
            forces[ci] = tuple(forces[ci][i] + fvec[j][i] for i in range(dim))
    active = sorted({cts[C.owner[j]].label for j in range(ncols) if on[j] and cts[C.owner[j]].label is not None})
    dx = tuple(Fraction(oc[i])-Fraction(origin[i]) for i in range(dim))
    mechs = [[_ExactFloat(v) for v in _twist_back(y, dx, dim)] for y in ys]
    row_duals = [_ExactFloat(yv * cap) for yv, cap in zip(ry[nb * nw:], capx)]
    res = MultiLimitResult(OPTIMAL, alpha, lam, mechs, forces, active, r.iterations + its, row_duals=row_duals,
                           uncertainty=U,resolvability=resolution,resolvability_statuses=statuses)
    d = check_duality_multi(res, bodies, contacts, dim=dim, origin=origin, k=k, tol=_SELF_CHECK)
    if not d["ok"]:
        raise RuntimeError(f"limit_load_multi self-check failed: "
                           f"{ {key: d[key] for key in ('admissible', 'worst_power_rel', 'drive', 'duality_gap_rel', 'complementarity', 'static_residual_rel')} }")
    return res


def check_duality_multi(res: MultiLimitResult, bodies: list[LimitBody], contacts: list[BodyContact], *,
                        dim: int = 3, origin: Vec | None = None, k: int = 8, tol: float = 1e-7) -> dict:
    """逐体静力、逐列相对功率及全局强对偶在有理数上精确核；tol 兼容保留，不改答案。

    静力由 lambdas 核对；contact_forces/active 是按显示 tol 截断的展示字段，不是证书。
    力矩列独立于 LP 的 `_exact_wrench` 重建；反作用亦由检查器重新装配。
    """
    if res.status != OPTIMAL:
        raise ValueError(f"check_duality_multi needs an optimal result, got status={res.status!r}")
    if origin is None:
        origin = (0.0,) * dim
    nw = _check_bodies(bodies, contacts, dim)
    nb = len(bodies)
    C = _check_columns([bc.contact for bc in contacts], origin, dim, k)
    if len(res.lambdas) != len(C.cols) or len(res.mechanisms) != nb or any(len(m) != nw for m in res.mechanisms) \
            or len(res.row_duals) != C.n_rows:
        raise ValueError("result does not match these bodies/contacts/dim/k")
    cols = []
    for j,w in enumerate(C.cols):
        bc = contacts[C.owner[j]]
        cols.append([v*(int(i == bc.body_a)-int(i == bc.body_b)) for i in range(nb) for v in w])
    return _exact_duality_report(res.alpha,res.lambdas,res.row_duals,cols,C.row_of,
                                 [v for b in bodies for v in b.dead], [v for b in bodies for v in b.live],
                                 [v for m in res.mechanisms for v in m])


def mechanism_is_admissible_multi(mechanisms: list[list[float]], contacts: list[BodyContact], *, dim: int = 3,
                                  origin: Vec | None = None, k: int = 8, tol: float = 1e-7,
                                  row_duals: list[float] | None = None) -> bool:
    """每列相对功率在给定数上精确 >= 0；tol 只保留兼容，其他体速度不影响答案。"""
    if origin is None:
        origin = (0.0,) * dim
    nw = 3 if dim == 2 else 6
    if any(len(m) != nw for m in mechanisms):
        raise ValueError(f"each mechanism must have {nw} components for dim={dim}")
    C = _check_columns([bc.contact for bc in contacts], origin, dim, k)
    if row_duals is not None and len(row_duals) != C.n_rows:
        raise ValueError(f"row_duals has {len(row_duals)} entries, contacts give {C.n_rows} cohesion rows")
    owners_ab = [(bc.body_a,bc.body_b) for bc in contacts]
    powers = _pair_powers(mechanisms,row_duals,C,owners_ab,dim)
    if row_duals is not None and any(_rational(v) < 0 for v in row_duals):
        return False
    return all(p >= 0 for p,rj in zip(powers,C.row_of) if rj is None or row_duals is not None)
