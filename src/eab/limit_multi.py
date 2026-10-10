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

自校验（与单体版同一结构，`check_duality_multi`）：静力一侧逐体平衡残差（力、力矩分块）**在各体自身的接触形心 o_i 判定**、
λ ≥ 0、黏聚行 ≤ 1、α ≥ 0；机构一侧逐列相对功率 ≥ 0（相对判据：尺度按**接触点处**两体的物理速度 |g_j|·(|v_a(p_j)| + |v_b(p_j)|)
+ |g_j|·V̂）、驱动 Σ y_iᵀW_live,i = 1（各体在自身形心处）、强对偶、互补。
各尺度是该体 / 该接触自己的物理尺度，不随装配体跨度放大（G6 第四轮 major：在 o′ 判定时跨度 1e4 的装配体把 α×0.999 静默放行，
与单体版第二轮"在调用方坐标系判定"同一根因）。可分辨性筛查沿返回的机构把全部体的活荷载推 ±16 倍舍入、精确重解，
与单体版同一规则。

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

from .limit import (_FLIP, _SELF_CHECK, _UNCERTAIN, LimitContact, _adot, _build_columns, _dot, _exact_shift,
                    _exact_wrench, _fl, _live_uncertainty, _norm, _shift_wrench, _twist_back, _twist_forward,
                    _wrench_rounding, wrench)
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


def _pair_powers(y: list[list[float]], yr: list[float] | None, C, owners_ab, dim: int, loads=(),
                 points=None, oc=None):
    """逐列相对功率 p_j = (y_a − y_b)ᵀw_j (+ y_r)，按**接触点处的物理速度**算与判尺度。

    各体旋量 y（关于共同参考点 o′）平移到接触点 p_j：v_a(p_j)、v_b(p_j)，p_j = g_j·(v_a − v_b) + y_r（与 (y_a − y_b)ᵀw_j 精确相等），
    尺度 s_j = |g_j|·(|v_a(p_j)| + |v_b(p_j)|) + |y_r|；V̂ = 各接触点处两体速度与各体**自身**形心处速度（含 |ω|·臂长）的最大者，
    列尺度再加 |g_j|·V̂，黏聚行尺度 cap·V̂。
    G6 第四轮 major：此前尺度取在 o′（全部接触的形心），离 o′ 远的体其 ω·|o′ − o_i| 把尺度放大装配体跨度/体尺寸倍——
    跨度 1e4 时 α×0.999 的注入静默放行、顶块贯入自己接触的机构被判容许；这是单体版第二轮"在调用方坐标系判定"的同一根因。
    loads：[(体 i 的旋量(关于 o′), 荷载旋量(关于 o′), 该体自身形心相对 o′ 的向量 d_i)]。points / oc 不给时退回 o′ 处的口径（只供旧调用）。"""
    p, s = [], []
    vmax = 0.0
    for j, (w, rj) in enumerate(zip(C.cols, C.row_of)):
        a, b = owners_ab[C.owner[j]]
        extra = yr[rj] if (rj is not None and yr is not None) else 0.0
        if points is not None:
            g = w[:dim]
            dp = tuple(points[C.owner[j]][q] - oc[q] for q in range(dim))
            va = _twist_forward(list(y[a]), dp, dim)[:dim]
            vb = _twist_forward(list(y[b]), dp, dim)[:dim] if b is not None else (0.0,) * dim
            pj = sum(gq * (vaq - vbq) for gq, vaq, vbq in zip(g, va, vb)) + extra
            sj = _norm(g) * (_norm(va) + _norm(vb)) + abs(extra)
            vmax = max(vmax, _norm(va), _norm(vb))
        else:
            pj = _dot(y[a], w) + extra
            sj = _adot(y[a], w) + abs(extra)
            if b is not None:
                pj -= _dot(y[b], w)
                sj += _adot(y[b], w)
        p.append(pj)
        s.append(sj)
    V = vmax
    if points is None:
        for w, sj in zip(C.cols, s):
            f = _norm(w[:dim])
            if f > 0.0:
                V = max(V, sj / f)
    for item in loads:
        yi, W = item[0], item[1]
        di = item[2] if len(item) > 2 else (0.0,) * dim
        yo = _twist_forward(list(yi), di, dim)
        Wo = _shift_wrench(list(W), di, dim)
        f = _norm(Wo[:dim])
        if f > 0.0:
            V = max(V, _adot(yo, Wo) / f)
    scale = [sj + _norm(w[:dim]) * V for w, sj in zip(C.cols, s)]
    rscale = [cap * V for cap in C.cap]
    return p, scale, rscale, V


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
    Rmag = max((_norm(tuple(bc.contact.point[i] - origin[i] for i in range(dim))) for bc in contacts), default=0.0)
    e_in = [_wrench_rounding(lc, dim, Rmag) for lc in live_c]
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
        return [list(res.y[i * nw:(i + 1) * nw]) for i in range(nb)]

    def _U(ys):
        flat_y = [v for yi in ys for v in yi]
        flat_l = [v for lc in live_c for v in lc]
        flat_e = [v for ei in e_in for v in ei]
        return _live_uncertainty(flat_y, flat_l, flat_e)

    def _pushes(ys):
        push = [[(1.0 if yi > 0.0 else -1.0 if yi < 0.0 else 0.0) * _FLIP * ei for yi, ei in zip(y, e)]
                for y, e in zip(ys, e_in)]
        minus = [[li - Fraction(pi) for li, pi in zip(lv, pv)] for lv, pv in zip(live_x, push)]
        plus = [[li + Fraction(pi) for li, pi in zip(lv, pv)] for lv, pv in zip(live_x, push)]
        return _solve(minus), _solve(plus)

    r = _solve(live_x)
    if r.status == UNBOUNDED:
        rmin = _solve(live_x, -1.0)
        its = r.iterations + rmin.iterations
        if rmin.status == OPTIMAL and rmin.x[ia] > 0.0:
            ys = _ys(rmin)
            U0 = _U(ys)
            if U0 > _UNCERTAIN:
                rm, rp = _pushes(ys)
                its += rm.iterations + rp.iterations
                if "infeasible" in (rm.status, rp.status):
                    return MultiLimitResult("infeasible", float("nan"), [], [], iterations=its, uncertainty=U0)
                if not (rm.status == rp.status == UNBOUNDED):
                    raise RuntimeError(f"limit_load_multi: unbounded capacity is not certified: pushing the live loads by "
                                       f"{_FLIP:g}x their input rounding gives {rm.status}/{rp.status}")
        return MultiLimitResult(UNBOUNDED, float("inf"), [], [], iterations=its)
    if r.status != OPTIMAL:
        return MultiLimitResult(r.status, float("nan"), [], [], iterations=r.iterations)
    alpha = r.x[ia]
    ys = _ys(r)
    U = _U(ys)
    its = 0
    if U > _UNCERTAIN:
        rm, rp = _pushes(ys)
        its = rm.iterations + rp.iterations
        if "infeasible" in (rm.status, rp.status):
            return MultiLimitResult("infeasible", float("nan"), [], [], iterations=r.iterations + its, uncertainty=U)
        if rm.status == OPTIMAL and rp.status == OPTIMAL and alpha > 0.0:
            U = max(abs(rm.x[ia] - alpha), abs(rp.x[ia] - alpha)) / (_FLIP * alpha)
        if not (rm.status == OPTIMAL and rp.status == OPTIMAL and alpha > 0.0 and U <= _UNCERTAIN):
            raise RuntimeError(f"limit_load_multi: load factor {alpha:.6e} has relative uncertainty {U:.1e} from input "
                               f"rounding (> {_UNCERTAIN:.0e}) and is not certified")
    raw = r.x[:ncols]
    lam = [v / C.cap[rj] if rj is not None else v for v, rj in zip(raw, C.row_of)]
    fvec = [tuple(raw[j] * C.cols[j][i] for i in range(dim)) for j in range(ncols)]
    fmag = [_norm(f) for f in fvec]
    fmax = max(fmag, default=0.0)
    on = [fm > tol * fmax for fm in fmag]
    forces: list[Vec] = [tuple(0.0 for _ in range(dim)) for _ in contacts]
    for j, ci in enumerate(C.owner):
        if on[j]:
            forces[ci] = tuple(forces[ci][i] + fvec[j][i] for i in range(dim))
    active = sorted({cts[C.owner[j]].label for j in range(ncols) if on[j] and cts[C.owner[j]].label is not None})
    mechs = [_twist_back(list(y), dvec, dim) for y in ys]
    row_duals = [yv * cap for yv, cap in zip(r.y[nb * nw:], C.cap)]
    res = MultiLimitResult(OPTIMAL, alpha, lam, mechs, forces, active, r.iterations + its, row_duals=row_duals,
                           uncertainty=U)
    d = check_duality_multi(res, bodies, contacts, dim=dim, origin=origin, k=k, tol=_SELF_CHECK)
    if not d["ok"]:
        raise RuntimeError(f"limit_load_multi self-check failed: "
                           f"{ {key: d[key] for key in ('admissible', 'worst_power_rel', 'drive', 'duality_gap_rel', 'complementarity', 'static_residual_rel')} }")
    return res


def check_duality_multi(res: MultiLimitResult, bodies: list[LimitBody], contacts: list[BodyContact], *,
                        dim: int = 3, origin: Vec | None = None, k: int = 8, tol: float = 1e-7) -> dict:
    """多体版的下限/上限自校验（判据与单体版 `check_duality` 一一对应，见模块文档）。"""
    if res.status != OPTIMAL:
        raise ValueError(f"check_duality_multi needs an optimal result, got status={res.status!r}")
    if origin is None:
        origin = (0.0,) * dim
    nw = _check_bodies(bodies, contacts, dim)
    nb = len(bodies)
    cts = [bc.contact for bc in contacts]
    owners_ab = [(bc.body_a, bc.body_b) for bc in contacts]
    oc = _centroid(contacts, origin, dim)
    dvec = tuple(oc[i] - origin[i] for i in range(dim))
    C = _build_columns(cts, oc, dim, k)
    if len(res.lambdas) != len(C.cols) or len(res.mechanisms) != nb or any(len(m) != nw for m in res.mechanisms) \
            or len(res.row_duals) != C.n_rows:
        raise ValueError("result does not match these bodies/contacts/dim/k")
    dead = [_shift_wrench(list(b.dead), dvec, dim) for b in bodies]
    live = [_shift_wrench(list(b.live), dvec, dim) for b in bodies]
    ys = [_twist_forward(list(m), dvec, dim) for m in res.mechanisms]
    yr = res.row_duals
    lam = list(res.lambdas)
    # 静力一侧：逐体平衡残差，**在各体自身的接触形心 o_i 判定**（力矩块与臂长都是该体自己的物理尺度；G6 第四轮 major：
    # 在共同形心 o′ 判定时离 o′ 远的体力矩尺度被 fsc·|o′ − o_i| 放大，远处体合力挪 1e-3·L 静默放行）
    static_rel = 0.0
    oi, di, arms = _body_frames(contacts, nb, oc, dim)
    for i in range(nb):
        dead_i = _shift_wrench(list(dead[i]), di[i], dim)
        live_i = _shift_wrench(list(live[i]), di[i], dim)
        resid = [dead_i[q] + res.alpha * live_i[q] for q in range(nw)]
        fsc = _norm(dead_i[:dim]) + abs(res.alpha) * _norm(live_i[:dim])
        msc = _norm(dead_i[dim:]) + abs(res.alpha) * _norm(live_i[dim:])
        for j, (l, w) in enumerate(zip(lam, C.cols)):
            a, b = owners_ab[C.owner[j]]
            sgn = 1.0 if a == i else (-1.0 if b == i else 0.0)
            if sgn == 0.0:
                continue
            wi = _shift_wrench(list(w), di[i], dim)
            for q in range(nw):
                resid[q] += sgn * l * wi[q]
            fsc += abs(l) * _norm(wi[:dim])
            msc += abs(l) * _norm(wi[dim:])
        msc += fsc * arms[i]
        static_rel = max(static_rel,
                         _norm(resid[:dim]) / fsc if fsc > 0.0 else _norm(resid[:dim]),
                         _norm(resid[dim:]) / msc if msc > 0.0 else _norm(resid[dim:]))
    rows_ok = all(sum(l for l, rj in zip(lam, C.row_of) if rj == r_i) <= 1.0 + tol for r_i in range(C.n_rows))
    static_ok = static_rel <= tol and min(lam, default=0.0) >= 0.0 and rows_ok and res.alpha >= 0.0
    # 机构一侧：功率在接触点处按物理速度判，荷载功率在各体自身形心处判
    loads = [(ys[i], dead[i], di[i]) for i in range(nb)] + [(ys[i], live[i], di[i]) for i in range(nb)]
    power, pscale, rscale, V = _pair_powers(ys, yr, C, owners_ab, dim, loads,
                                             points=[bc.contact.point for bc in contacts], oc=oc)
    yo = [_twist_forward(list(ys[i]), di[i], dim) for i in range(nb)]
    dead_o = [_shift_wrench(list(dead[i]), di[i], dim) for i in range(nb)]
    live_o = [_shift_wrench(list(live[i]), di[i], dim) for i in range(nb)]
    drive = sum(_dot(yo[i], live_o[i]) for i in range(nb))
    dscale = max(1.0, sum(_adot(yo[i], live_o[i]) for i in range(nb)))
    upper = -sum(_dot(yo[i], dead_o[i]) for i in range(nb)) + sum(yr)
    G = (abs(res.alpha) + sum(_adot(yo[i], dead_o[i]) for i in range(nb)) + sum(abs(v) for v in yr)
         + sum(_norm(dead_o[i][:dim]) for i in range(nb)) * V)
    worst_rel = 0.0
    for pj, sj in zip(power, pscale):
        if pj < 0.0:
            worst_rel = min(worst_rel, pj / sj if sj > 0.0 else -1.0)
    for v, sr in zip(yr, rscale):
        if v < 0.0:
            worst_rel = min(worst_rel, v / sr if sr > 0.0 else -1.0)
    admissible = worst_rel >= -tol and drive >= 1.0 - tol * dscale
    fmag = [abs(l) * _norm(w[:dim]) for l, w in zip(lam, C.cols)]
    fmax = max(fmag, default=0.0)
    comp = 0.0
    for fm, pj, sj in zip(fmag, power, pscale):
        if fm > tol * fmax and sj > 0.0:
            comp = max(comp, abs(pj) / sj)
    for r_i in range(C.n_rows):
        slack = 1.0 - sum(l for l, rj in zip(lam, C.row_of) if rj == r_i)
        if slack > tol and yr[r_i] != 0.0:
            comp = max(comp, abs(yr[r_i]) / rscale[r_i] if rscale[r_i] > 0.0 else 1.0)
    if res.alpha * abs(drive) > tol * G:
        comp = max(comp, abs(drive - 1.0) / dscale)
    gap = abs(upper - res.alpha)
    gap_rel = gap / G if G > 0.0 else gap
    return {"admissible": admissible, "worst_power_rel": worst_rel, "drive": drive, "upper_bound": upper,
            "alpha": res.alpha, "duality_gap": gap, "duality_gap_rel": gap_rel, "complementarity": comp,
            "static_residual_rel": static_rel, "static_ok": static_ok,
            "ok": admissible and gap_rel <= tol and comp <= tol and static_ok}


def mechanism_is_admissible_multi(mechanisms: list[list[float]], contacts: list[BodyContact], *, dim: int = 3,
                                  origin: Vec | None = None, k: int = 8, tol: float = 1e-7,
                                  row_duals: list[float] | None = None) -> bool:
    """多体机构的容许性：每列相对功率 (y_a − y_b)ᵀw ≥ −tol·尺度（固定边界 y_b = 0）；黏聚列按单体版的口径。"""
    if origin is None:
        origin = (0.0,) * dim
    nw = 3 if dim == 2 else 6
    if any(len(m) != nw for m in mechanisms):
        raise ValueError(f"each mechanism must have {nw} components for dim={dim}")
    cts = [bc.contact for bc in contacts]
    owners_ab = [(bc.body_a, bc.body_b) for bc in contacts]
    oc = _centroid(contacts, origin, dim)
    dvec = tuple(oc[i] - origin[i] for i in range(dim))
    ys = [_twist_forward(list(m), dvec, dim) for m in mechanisms]
    C = _build_columns(cts, oc, dim, k)
    if row_duals is not None and len(row_duals) != C.n_rows:
        raise ValueError(f"row_duals has {len(row_duals)} entries, contacts give {C.n_rows} cohesion rows")
    p, s, rs, _ = _pair_powers(ys, row_duals, C, owners_ab, dim, points=[bc.contact.point for bc in contacts], oc=oc)
    if row_duals is not None and any(v < -tol * sr for v, sr in zip(row_duals, rs)):
        return False
    for pj, sj, rj in zip(p, s, C.row_of):
        if rj is not None and row_duals is None:
            continue
        if pj < -tol * sj:
            return False
    return True
