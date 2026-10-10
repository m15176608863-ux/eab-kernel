"""三维接触盖：∂E(A,B) 的语义化分解。

记号与二维版一致：**B 固定，A 平移，参考点取自 A**，E(A,B) = a0 + (B ⊕ (−A))。

盖类型（命题 4 的三维分类，一般位置下）：
  facet（二维面）  VF  A 的顶点 × B 的面
                   FV  A 的面   × B 的顶点
                   EE  交叉棱-棱（两棱方向不平行）
  edge（一维）     VE3 A 的顶点 × B 的棱 ／ EV3 A 的棱 × B 的顶点
  vertex（零维）   VV3 A 的顶点 × B 的顶点
  退化            FF（平行贴面）、FE（棱平行于面）、EEP（平行棱-棱）

有效性 = **局部**法锥条件（命题 5）：闭条件成立即给出盖，相对内部是否严格成立记在 `strict`
字段——枚举**不按 strict 过滤**（边界态盖是 FF/FE/EEP 退化族的唯一表达）。局部化的两个理由：
(1) 与石根华的"角"概念一致；(2) Phase 3 的凹块可以沿用同一实现——反射顶点/凹棱的局部锥为空，
自动被排除。凸成员谓词 `membership_convex3` 另用 E 的全部支撑半空间，不依赖一般位置。

法锥的表示与判据（这是三维版与二维版唯一实质不同的地方）：
  顶点 v：N(v) = {d : d·e_i ≤ 0, e_i 为 v 的所有入射棱方向}；relint ⟺ 全部严格 <0。
  棱 e：  N(e) = {d ⊥ t_e} ∩ {两相邻面法向张成的楔}；relint ⟺ 严格在两法向之间（要求凸二面角）。
  面 f：  N(f) = 外法向单条射线。

容差（纪律 F；2026-09-27 M0.3 改为逐特征、量纲分明）：
  · 调用方的 `tol` **只是角度**（单位向量点积、弧、锥），只会放宽"闭条件成立"（多收边界态的盖），从不当长度用；
  · 每个判据另加**被测特征自己**的方向噪声（geom3：棱 c·eps·C/|e|、面法向 c·eps·C·周长/(2·面积)、
    二面角 = 两相邻面之和）——平行面 / 平行棱这类**精确**退化关系在旋转、平移到工程坐标、单位缩放之后
    仍判为同一边界态，盖标签与 strict 字段不变（tests/test_invariance_geom.py）；
  · "丢弃型"判定（平棱、平行棱、顶点落在棱线上）只用舍入噪声，不用调用方 tol；噪声之外另加 1e-12 的无量纲下限
    （轴对齐、原点处噪声估计可为 0，严格比较会把恰好相等的退化判反；这是 ulp 级的保护，不是容差，G6 第三轮 minor 记）；
  · 长度容差是另一个参数 `extent_tol`（调用方单位，缺省 0），只用于"投影落在面内 / 最近点落在段内"的边界带，
    抬到两体坐标量级处的舍入地板 c·eps·C（`_pair_floor`）。棱参数带是它除以**该棱的长度**，面内判定的边界带
    再加上"间隙 × 面法向噪声"（投影点随法向噪声的漂移）。裕度层用缺省（只有舍入），互锁层传它的谓词分辨率；
  · 见证点（point_a / point_b）一律**落在两体上**：棱参数钳进 [0, 1]，投影落在面外时取面多边形上的最近点。于是
    任何被收下的盖，见证距离都不小于真实间距；平棱被判平时，相邻面上的 VF 见证点钳到那条棱上，恰是它的距离。
M0.2 的 `_pair_tols` 把整对物体的最短棱当 ℓ（一条极短的棱让全部特征的角容差变大，真棱脊被判平、盖被丢）、
把调用方 tol 同时当长度用（裕度层的 1e-9 成了绝对长度，小模型的真最近 VE3 被丢），棱参数带 −ang ≤ s ≤ 1 + ang
把长度当无量纲带（大块体角点处见证点越出棱端 ang·|棱|）——G6 第二轮两条 critical、一条 major。
门：tests/test_margin_resolution.py。
"""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2

from . import geom3
from .geom3 import (Polyhedron, Vec3, _exact_line_params, add, angle_between, cross, dot, mul, neg, noise_floor, norm,
                    sub, unit)


def _pair_floor(A: Polyhedron, B: Polyhedron) -> float:
    """两体坐标量级处的长度舍入地板 c·eps·C（见模块文档"容差"）。"""
    return noise_floor(max(A.metrics()[0], B.metrics()[0]))


def _clamp01(s: float) -> float:
    return 0.0 if s < 0.0 else (1.0 if s > 1.0 else s)


def _closest_on_face_boundary(x: Vec3, P: Polyhedron, fi: int) -> Vec3:
    """面 fi 的边界折线上离 x 最近的点（x 已在面平面上、落在多边形外或边上时，它就是面多边形上的最近点）。"""
    f = P.faces[fi]
    best, bd = f and P.verts[f[0]], float("inf")
    for i in range(len(f)):
        a, b = P.verts[f[i]], P.verts[f[(i + 1) % len(f)]]
        d = sub(b, a)
        dd = dot(d, d)
        q = a if dd <= 0.0 else add(a, mul(d, _clamp01(dot(sub(x, a), d) / dd)))
        w = sub(x, q)
        if dot(w, w) < bd:
            best, bd = q, dot(w, w)
    return best


def _face_witness(x: Vec3, g: float, P: Polyhedron, fi: int, lng: float) -> tuple[Vec3, bool]:
    """顶点在面 fi 平面上的投影 x（有符号间隙 g）→ (面多边形上的见证点, in_extent)。
    in_extent 的边界带 = lng + |g|·面法向噪声（投影点随法向噪声的漂移）；见证点：投影严格在内取投影，否则取边界最近点。"""
    locate = geom3.face_polygon_locate          # 经模块属性调用：面内判定只有这一个实现（tests/test_geom3_face_polygon.py）
    if locate(x, P, fi, lng + abs(g) * P.face_noise(fi)) < 0:
        return x, False
    return (x if locate(x, P, fi, 0.0) == 1 else _closest_on_face_boundary(x, P, fi)), True


def _orth(v: Vec3, t: Vec3) -> Vec3:
    """v 去掉沿单位向量 t 的分量后单位化——**按构造正交**（做两遍，余量到 eps 量级）。"""
    v = sub(v, mul(t, dot(v, t)))
    v = sub(v, mul(t, dot(v, t)))
    return unit(v)


@dataclass(slots=True)
class Cover3:
    kind: str                     # VF | FV | EE | VE3 | EV3 | VV3 | FF | FE | EEP
    a_feature: tuple[str, ...]    # ("vertex", i) | ("face", i) | ("edge", i, j)
    b_feature: tuple[str, ...]
    normal: Vec3 | None           # B → A 的分离方向（单位）
    gap: float                    # 沿 normal 的有符号间隙（>0 分离）
    point_a: Vec3 | None          # A 侧代表点
    point_b: Vec3 | None          # B 侧代表点
    params: tuple[float, ...]     # VF/FV: 面内重心参数留空；EE: (s, t) 两棱参数
    area: float | None            # 代表面积（VF/FV 取面面积；EE 为 None）
    strict: bool                  # 法锥相对内部条件严格成立
    in_extent: bool               # 投影/最近点落在面内或段内

    def label(self) -> tuple:
        return (self.kind, self.a_feature, self.b_feature)


# ------------------------------------------------------------------ 法锥判据

def vertex_cone_contains(P: Polyhedron, vi: int, d: Vec3, tol: float = 0.0) -> int:
    """d 相对顶点 vi 的局部法锥：1 严格内部 / 0 边界 / -1 外部。

    判据 d·e_i ≤ 0（e_i 为入射棱单位方向）：全严格则在相对内部。反射顶点的锥自动为空或退化。
    tol 是角度（调用方的容差，含 d 自身的方向噪声——由调用方算进来）；每条入射棱另加**它自己**的方向噪声
    c·eps·C/|e_i|（M0.3：M0.2 用整体最短棱）。
    """
    edges = P.vertex_edges(vi)
    if not edges:
        return -1
    strict = True
    for e, noise in edges:
        m = dot(d, e)
        t = tol + noise
        if m > t:
            return -1
        if m >= -t:
            strict = False
    return 1 if strict else 0


def edge_arc_contains(P: Polyhedron, e: tuple[int, int], d: Vec3, tol: float = 0.0) -> int:
    """d 相对棱 e 的局部法锥（两相邻面法向之间的球面弧）：1 严格内 / 0 边界 / -1 外。

    要求 d ⊥ t_e（容差内），且 d 严格落在两法向张成的凸楔中；凹二面角（反射棱）返回 -1。
    tol 是角度（调用方的容差）；两法向各加**自己面**的法向噪声，正交性加这条棱的方向噪声（M0.3 逐特征）。
    "平棱"（丢弃型判定）只用这条棱的二面角噪声，不用调用方 tol：真实的缓棱脊（二面转角 2e-6 rad）必须保留。
    正交性判据对单位向量是无量纲的；调用方（ve3 / ev3 / ee / facet_normal3 / frozen_ee_sign）一律**按构造**
    把 d 对 t_e 正交化后再传进来（G6 critical 6：此前 d = unit(a − q) 带着 ∝ eps·|坐标|/间隙 的棱向分量，
    小间隙或远坐标下真最近对被这里拒掉）。
    """
    fs = P.edge_faces(e)
    if len(fs) != 2:
        return -1
    if P.dihedral_turn(e) <= P.dihedral_noise(e):          # 平棱（噪声内）或凹棱：弧退化/为空
        return -1
    t = P.edge_dir(e)
    if abs(dot(d, t)) > tol + P.edge_noise(e) + 1e-12:
        return -1
    n1, n2 = P.face_normal(fs[0]), P.face_normal(fs[1])
    f1, f2 = P.face_noise(fs[0]), P.face_noise(fs[1])
    # 在垂直于 t 的平面内比较极角：d 必须严格在 n1 与 n2 之间（走凸的那一侧）
    w = angle_between(n1, n2)
    a1 = angle_between(n1, d)
    a2 = angle_between(n2, d)
    if a1 + a2 <= w + tol + f1 + f2 + 1e-12:
        if a1 > tol + f1 and a2 > tol + f2:
            return 1
        return 0
    return -1


def cone_constraints(A: Polyhedron, ia: int, B: Polyhedron, ib: int) -> list[Vec3]:
    """N_B(b) ∩ N_{−A}(−a) 的约束法向集 g：该锥 = {d : d·g ≤ 0, ∀g}。

    N_B(b) = {d : d·e_i ≤ 0}（e_i 为 B 在 ib 的入射棱方向）；
    N_{−A}(−a) = {d : d·(−f_j) ≤ 0}（f_j 为 A 在 ia 的入射棱方向，因 −A 的棱方向取反）。
    """
    return [*B.vertex_edge_dirs(ib), *(neg(f) for f in A.vertex_edge_dirs(ia))]


def _closest_point_on_segment(a: Vec3, b: Vec3) -> Vec3:
    d = sub(b, a)
    dd = dot(d, d)
    if dd <= 0.0:
        return a
    t = -dot(a, d) / dd
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return add(a, mul(d, t))


_TRI_DEGENERATE = 1e-10      # 三角"厚度" |n| / L_max² 低于它按三条边处理（相对判据）
_SIMPLEX_DEGENERATE = 1e-12  # 四点单形 |v0| / L_max³ 低于它不做"原点在内"判定（相对判据）


def _closest_point_on_triangle(a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    """原点到三角 abc 的最近点（含退化情形回退到边）。

    退化判据是相对的（2026-09-24 G6 critical 26 同类）：|n| ≤ 1e-10·L_max²（三角的宽 ≤ 1e-10·L_max）
    按三条边处理——此前 |n|² ≤ 1e-300 的绝对阈值让舍入级的"细条三角"去做平面投影。
    """
    n = cross(sub(b, a), sub(c, a))
    nn = dot(n, n)
    lmax2 = max(dot(sub(b, a), sub(b, a)), dot(sub(c, a), sub(c, a)), dot(sub(c, b), sub(c, b)))
    if nn <= (_TRI_DEGENERATE * lmax2) ** 2:
        best = _closest_point_on_segment(a, b)
        for cand in (_closest_point_on_segment(b, c), _closest_point_on_segment(a, c)):
            if dot(cand, cand) < dot(best, best):
                best = cand
        return best
    # 原点在三角平面上的投影
    p = mul(n, dot(a, n) / nn)
    u = dot(cross(sub(b, p), sub(c, p)), n)
    v = dot(cross(sub(c, p), sub(a, p)), n)
    w = dot(cross(sub(a, p), sub(b, p)), n)
    if u >= 0.0 and v >= 0.0 and w >= 0.0:
        return p
    best = _closest_point_on_segment(a, b)
    for cand in (_closest_point_on_segment(b, c), _closest_point_on_segment(a, c)):
        if dot(cand, cand) < dot(best, best):
            best = cand
    return best


def closest_point_of_convex_hull_to_origin(pts: list[Vec3]) -> Vec3:
    """原点到 conv(pts) 的最近点（3D，点数少时枚举单形；原点在内则返回零向量）。

    依据：多胞形上离原点最近的点落在某个 ≤2 维面的相对内部，即 ≤3 个点的凸包上；
    若原点落在某个四点单形内部，则距离为 0。

    退化四点单形（|v0| ≤ 1e-12·L_max³，L_max 为单形从首点出发的最长棱）**跳过**"原点在内"判定
    （2026-09-24 G6 critical 26）：此前阈值是绝对的 1e-300，平行到舍入的锥生成元给出 v0 ~ 1e-17，
    原点又恰与它们共面时四个重心坐标都是噪声/噪声，可以报"在内"——VV3 与别的 E 顶点消失、
    body_distance 返回 (inf, None)。跳过的单形若真含原点，原点离其某个三角面 ≤ 1e-12·L_max，
    由下面的三角枚举给出 ≤ 该量级的距离。重心坐标的符号检验容许 −1e-12（原点落在单形面上）。
    """
    n = len(pts)
    if n == 0:
        raise ValueError("empty point set")
    # 四点含原点？（有符号体积同号）
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                for l in range(k + 1, n):
                    a, b, c, d = pts[i], pts[j], pts[k], pts[l]
                    def vol(p, q, r, s):
                        return dot(sub(q, p), cross(sub(r, p), sub(s, p)))
                    v0 = vol(a, b, c, d)
                    lmax = max(norm(sub(b, a)), norm(sub(c, a)), norm(sub(d, a)))
                    if abs(v0) <= _SIMPLEX_DEGENERATE * lmax ** 3:
                        continue
                    o = (0.0, 0.0, 0.0)
                    s1 = vol(o, b, c, d) / v0
                    s2 = vol(a, o, c, d) / v0
                    s3 = vol(a, b, o, d) / v0
                    s4 = vol(a, b, c, o) / v0
                    if min(s1, s2, s3, s4) >= -1e-12:
                        return (0.0, 0.0, 0.0)
    best = pts[0]
    bd = dot(best, best)
    for i in range(n):
        for j in range(i + 1, n):
            cand = _closest_point_on_segment(pts[i], pts[j])
            d2 = dot(cand, cand)
            if d2 < bd:
                best, bd = cand, d2
            for k in range(j + 1, n):
                cand = _closest_point_on_triangle(pts[i], pts[j], pts[k])
                d2 = dot(cand, cand)
                if d2 < bd:
                    best, bd = cand, d2
    for p in pts:
        d2 = dot(p, p)
        if d2 < bd:
            best, bd = p, d2
    return best


def cone_relint_direction(g: list[Vec3], tol: float = 1e-12) -> Vec3 | None:
    """在 {d : d·g_k ≤ 0} 的**相对内部**里找一个方向；空（或降维）则返回 None。

    严格判据（Gordan 定理）：∃d 使全部 d·g_k < 0 ⟺ 原点 ∉ conv{g_k}。且最优方向为
    −unit(p)，p = 原点到 conv{g_k} 的最近点；此时 max_k d·g_k = −|p|。
    启发式候选集（负平均、极射线平均等）会漏判——2026-09-18 实测 43 个 E 顶点只找到 31 个。
    """
    if not g:
        return None
    gs = [unit(x) for x in g if norm(x) > 1e-300]
    if not gs:
        return None
    p = closest_point_of_convex_hull_to_origin(gs)
    dist = norm(p)
    if dist <= tol:
        return None
    return unit(neg(p))


def cone_intersection_margin(A: Polyhedron, ia: int, B: Polyhedron, ib: int) -> tuple[float, float]:
    """(ia, ib) 的锥相交裕度：(原点到约束法向凸包的距离 |p|, 两顶点入射棱方向噪声的最大者)。
    |p| > 噪声 ⟺ N_B(b) 与 −N_A(a) 的相对内部相交（命题 4 的零维盖条件，Gordan）；|p| 落在噪声量级以内时
    "是不是 E 的顶点"在这组坐标的精度下说不清（G0 票三把这种对两边都不计，见 g03）。"""
    noise = max((nz for _, nz in A.vertex_edges(ia) + B.vertex_edges(ib)), default=0.0)
    gs = [unit(x) for x in cone_constraints(A, ia, B, ib) if norm(x) > 1e-300]
    if not gs:
        return 0.0, noise
    return norm(closest_point_of_convex_hull_to_origin(gs)), noise


def cones_intersect_relint(A: Polyhedron, ia: int, B: Polyhedron, ib: int, tol: float = 1e-12) -> bool:
    """(ia, ib) 是否给出 ∂E 的一个顶点（命题 4 的零维盖条件）。tol 是角度，另加两个顶点入射棱方向噪声的最大者
    （平行棱在旋转 / 远坐标下只平行到 eps·C/ℓ，锥的交恰退化成低维时不许被噪声判成有内部）。"""
    dist, noise = cone_intersection_margin(A, ia, B, ib)
    return dist > max(tol, noise)


def _project_on_face(p: Vec3, P: Polyhedron, fi: int) -> tuple[Vec3, float]:
    n = P.face_normal(fi)
    o = P.verts[P.faces[fi][0]]
    g = dot(n, sub(p, o))
    return add(p, mul(n, -g)), g


# ------------------------------------------------------------------ 三类 facet 盖
#
# in_extent（投影落在面多边形内）一律用 geom3.face_polygon_locate：面可以非凸
# （merge_coplanar 归并出的十边形侧面、L 块顶底面）。此前这里自带一份半平面核判据，
# 只对凸面正确（2026-09-21 审查 C7：L 块臂上的 VF 盖 in_extent=False 被丢）。

def vf_cover(A: Polyhedron, ia: int, B: Polyhedron, fb: int, tol: float = 0.0, extent_tol: float = 0.0) -> Cover3 | None:
    """A 的顶点 ia 对 B 的面 fb。有效 ⟺ −n_f ∈ relint N_A(ia)。锥判据的方向是 B 的面法向，加上它的噪声。"""
    nB = B.face_normal(fb)
    side = vertex_cone_contains(A, ia, neg(nB), tol + B.face_noise(fb))
    if side < 0:
        return None
    a = A.verts[ia]
    proj, g = _project_on_face(a, B, fb)
    wit, inside = _face_witness(proj, g, B, fb, max(extent_tol, _pair_floor(A, B)))
    return Cover3("VF", ("vertex", ia), ("face", fb), nB, g, a, wit, (), B.face_area(fb), side == 1, inside)


def fv_cover(A: Polyhedron, fa: int, B: Polyhedron, ib: int, tol: float = 0.0, extent_tol: float = 0.0) -> Cover3 | None:
    """A 的面 fa 对 B 的顶点 ib。有效 ⟺ −n_A(fa) ∈ relint N_B(ib)。分离法向 = −n_A。"""
    nA = A.face_normal(fa)
    side = vertex_cone_contains(B, ib, neg(nA), tol + A.face_noise(fa))
    if side < 0:
        return None
    b = B.verts[ib]
    proj, g = _project_on_face(b, A, fa)     # g = n_A·(b − a0)：>0 表示 B 顶点在 A 面外侧
    wit, inside = _face_witness(proj, g, A, fa, max(extent_tol, _pair_floor(A, B)))
    return Cover3("FV", ("face", fa), ("vertex", ib), neg(nA), g, wit, b, (), A.face_area(fa), side == 1, inside)


def _closest_params(p1: Vec3, d1: Vec3, p2: Vec3, d2: Vec3) -> tuple[float, float] | None:
    """两直线最近点参数（d1、d2 为方向向量，非单位亦可）；平行返回 None。

    **叉积式**：n = d1 × d2，s = ((p2 − p1) × d2)·n / |n|²，t = ((p2 − p1) × d1)·n / |n|²。|n|² = a·c·sin²θ 直接算出、
    不经 a·c − b² 的抵消——旧式 den = a·c − b² 在 θ ≲ 1e-7 时是舍入垃圾，参数相对误差 eps/sin²θ 达 0.02 … 2，见证距离在
    gap ≲ θ·|e| 时一阶错、in_extent 也按垃圾参数判（G6 第四轮 major：θ = 1e-8、间隙 1e-9 的两条脊棱 body_distance 报 1.8e-9，
    真值 1.0e-9，膨胀成员判定 fail-unsafe）。平行判据按 |n|² ≤ 1e-24·a·c（sin²θ ≤ 1e-24）。"""
    a, c = dot(d1, d1), dot(d2, d2)
    n = cross(d1, d2)
    nn = dot(n, n)
    if nn <= 1e-24 * a * c:
        return None
    if nn <= 1e-12 * a * c:                         # sin²θ ≤ 1e-12：浮点参数不可信，按坐标精确算（geom3._exact_line_params）
        return _exact_line_params(p1, d1, p2, d2)
    w = sub(p2, p1)
    return dot(cross(w, d2), n) / nn, dot(cross(w, d1), n) / nn


def ee_cover(A: Polyhedron, ea: tuple[int, int], B: Polyhedron, eb: tuple[int, int],
             tol: float = 0.0, extent_tol: float = 0.0) -> Cover3 | None:
    """A 的棱 ea 对 B 的棱 eb（交叉）。候选法向 ±unit(t_B × t_A)，取落在两条弧相对内部者。

    弧判据的输入对各自的棱**按构造正交化**（叉积对近平行棱只正交到 eps/sinθ）。平行判据（丢弃型）只用两条棱的
    方向噪声：噪声内平行的一对由 VE3/EV3 表达（平行时距离沿重叠段为常数，端点垂足恰是最短距离）。参数段判据按
    **各自的棱长**：s ∈ [−λ/|e_A|, 1 + λ/|e_A|]（λ = extent_tol 抬到长度舍入地板）。见证点钳进两条棱段。"""
    tA, tB = A.edge_dir(ea), B.edge_dir(eb)
    c = cross(tB, tA)
    if norm(c) <= A.edge_noise(ea) + B.edge_noise(eb) + 1e-12:     # 平行棱（噪声内）：退化盖，另行处理
        return None
    n = unit(c)
    fl = max(extent_tol, _pair_floor(A, B))
    # 候选法向 ±unit(t_B × t_A) 自己带着两条棱的方向噪声（短棱主导：1.7 mm 的棱在 1e6 处 8e-6 rad）——弧判据的
    # 角容差要把它算进去，否则局部侧会把按自己的噪声分不清的 facet 判成"严格"，与凸包侧说不清的口径不一致（G6 第三轮 major）
    # 候选法向 unit(t_B × t_A) **自身**的方向噪声：叉积只正交到 eps/sinθ，两棱的方向噪声被 1/|c| = 1/sinθ 放大。
    # G6 第三轮 major：偏航 1e-5 rad 的叠放方块，恒等位形下候选恰是面法向、判边界；一经旋转叉积被舍入倾斜 ~1e-11 rad
    # ≫ tol + 面噪声，翻成 strict，local_facets3 多出假 strict EE，G0 票二报 local_only（不变性网格 22/35 格不同于恒等格）
    ang = tol + (A.edge_noise(ea) + B.edge_noise(eb)) / norm(c)
    best: Cover3 | None = None
    for cand in (n, neg(n)):
        sb = edge_arc_contains(B, eb, _orth(cand, tB), ang)
        sa = edge_arc_contains(A, ea, _orth(neg(cand), tA), ang)
        if sb < 0 or sa < 0:
            continue
        pa0, pb0 = A.verts[ea[0]], B.verts[eb[0]]
        dA = sub(A.verts[ea[1]], pa0)
        dB = sub(B.verts[eb[1]], pb0)
        pr = _closest_params(pa0, dA, pb0, dB)
        if pr is None:
            continue
        s, _ = pr
        # 一致的见证对：qa 取 A 棱直线上的 s 处，qb 取 **qa 在 B 棱直线上的垂足**（t 由 qa 定，不独立求）。
        # 近平行棱（夹角 θ）上 _closest_params 的 s、t 各带 ~eps/sin²θ 的误差且互不相关，独立求出的两点沿棱错位
        # (Δs − Δt)·|e|，见证距离偏大 (Δs − Δt)²|e|²/(2d)（θ = 1e-5、d = 1e-3 时 2e-10，远超自校验窗口；G6 第三轮 major）。
        # 距离对"沿棱滑动"不敏感（θ²Δs²/2d）只在 gap ≫ θ·|e| 时成立；gap ≲ θ·|e| 时 s 的误差一阶地进见证距离，
        # 所以 s 本身也要稳（_closest_params 的叉积式，G6 第四轮 major）。gap 沿 facet 法向，与 s、t 无关。
        qa = add(pa0, mul(dA, s))
        t = dot(sub(qa, pb0), dB) / dot(dB, dB)
        qb = add(pb0, mul(dB, t))
        g = dot(cand, sub(qa, qb))
        # 棱参数带 = 长度带 / 棱长 + 杠杆项：棱方向噪声 rfl/|e| × 到对方见证点的距离 |g|，再除以棱长（投影点随方向噪声的漂移，
        # 与面内判定的"间隙 × 面法向噪声"同一口径）。远离的棱对（|g| = 101、|e| = 1）参数舍入 ~ rfl·|g|/|e|² 是 rfl/|e| 的百倍，
        # 恰在段端点上的边界态盖在工程坐标下曾被判出程（不变性元门 2026-10-10 加入尺寸比 100 的对后暴露）
        rfl = _pair_floor(A, B)
        ba = (fl + abs(g) * rfl / norm(dA)) / norm(dA)
        bb = (fl + abs(g) * rfl / norm(dB)) / norm(dB)
        in_ext = (-ba <= s <= 1.0 + ba) and (-bb <= t <= 1.0 + bb)
        if not 0.0 <= s <= 1.0:
            qa = add(pa0, mul(dA, _clamp01(s)))                     # 钳到棱段端点，另一点重取垂足（仍一致）
            qb = add(pb0, mul(dB, _clamp01(dot(sub(qa, pb0), dB) / dot(dB, dB))))
        elif not 0.0 <= t <= 1.0:
            qb = add(pb0, mul(dB, _clamp01(t)))
            qa = add(pa0, mul(dA, _clamp01(dot(sub(qb, pa0), dA) / dot(dA, dA))))
        cov = Cover3("EE", ("edge", ea[0], ea[1]), ("edge", eb[0], eb[1]), cand, g, qa, qb,
                     (s, t), None, sb == 1 and sa == 1, in_ext)
        if best is None or abs(cov.gap) < abs(best.gap):
            best = cov
    return best


# ------------------------------------------------------------------ 低维与退化盖

def ve3_cover(A: Polyhedron, ia: int, B: Polyhedron, eb: tuple[int, int], tol: float = 0.0,
              extent_tol: float = 0.0) -> Cover3 | None:
    """A 的顶点 × B 的棱 → ∂E 的棱（一维盖）。有效 ⟺ N_B(eb) 的弧与 −N_A(ia) 的锥相交（闭）。

    实现上取分离方向 = 顶点到棱的最短向量（若最近点在段内），再验它同时落在两个锥里。
    strict = 两个判据**都**严格（相对内部）；任一为边界（0）即 False——与 ee_cover 同一口径
    （2026-09-21 审查 C10：此前写死 True）。边界态盖**照样返回**：平行棱-棱最近对（EEP 退化）
    只能由它表达，见 enumerate_covers3。

    分离方向**按构造垂直于棱**（2026-09-24 G6 critical 6）：v 由 w = a − p0 减去沿棱分量得到（不经过
    q 的绝对坐标），再对棱方向正交化一遍。此前 v = a − q，q = p0 + d·s 的舍入给 unit(v) 一个
    ∝ eps·|坐标|/间隙 的棱向分量，间隙 < 1e-7（原点）或 < 1e-5（坐标 1e3）时被弧判据拒掉，
    body_distance 跳到远处的盖（2.0000001 而非 1e-7），裕度层判"安全"。

    M0.3：顶点落在棱线上（丢弃型）只看长度舍入地板 fl，不看调用方 tol（裕度层的 1e-9 曾在这里成了绝对长度，
    间隙 1e-9 的真最近对被丢）；棱参数带 λ/|e|（λ = extent_tol 抬到地板，除以**这条棱**的长度）；见证点钳进棱段。
    """
    fl = _pair_floor(A, B)
    a = A.verts[ia]
    p0 = B.verts[eb[0]]
    d = sub(B.verts[eb[1]], p0)
    w = sub(a, p0)
    s = dot(w, d) / dot(d, d)
    v = sub(w, mul(d, s))
    t = unit(d)
    v = sub(v, mul(t, dot(v, t)))
    gap = norm(v)
    if gap <= fl:
        return None
    n = _orth(v, t)
    # 见证方向**自身**的舍入噪声：v 由坐标 ~C 相减得到，绝对误差 ~fl，方向只准到 fl/|v|（尺寸比 100 的对平移到 1e3、
    # 间隙 1e-6 时 1e-5 rad）；恰落在弧 / 锥边界上的真实盖（小方块底面与大方块顶面共面）此前在工程坐标下被丢，
    # 原点处却保留——不变性元门 2026-10-10 加入该对后暴露。与 ee_cover 的候选噪声 /sinθ 同一政策：判据加被测方向自己的噪声
    dn = fl / gap
    sb = edge_arc_contains(B, eb, n, tol + dn)
    sa = vertex_cone_contains(A, ia, neg(n), tol + dn)
    if sb < 0 or sa < 0:
        return None
    band = (max(extent_tol, fl) + gap * fl / norm(d)) / norm(d)      # 长度带 + 杠杆项（同 ee_cover）
    return Cover3("VE3", ("vertex", ia), ("edge", eb[0], eb[1]), n, gap, a, add(p0, mul(d, _clamp01(s))), (s,), None,
                  sb == 1 and sa == 1, -band <= s <= 1.0 + band)


def ev3_cover(A: Polyhedron, ea: tuple[int, int], B: Polyhedron, ib: int, tol: float = 0.0,
              extent_tol: float = 0.0) -> Cover3 | None:
    """A 的棱 × B 的顶点 → ∂E 的棱。strict、按构造正交、丢弃判据、参数带与见证点的口径同 ve3_cover。"""
    fl = _pair_floor(A, B)
    b = B.verts[ib]
    p0 = A.verts[ea[0]]
    d = sub(A.verts[ea[1]], p0)
    w = sub(b, p0)
    s = dot(w, d) / dot(d, d)
    v = neg(sub(w, mul(d, s)))              # q − b
    t = unit(d)
    v = sub(v, mul(t, dot(v, t)))
    gap = norm(v)
    if gap <= fl:
        return None
    n = _orth(v, t)
    dn = fl / gap                                  # 见证方向自身的噪声，同 ve3_cover
    sb = vertex_cone_contains(B, ib, n, tol + dn)
    sa = edge_arc_contains(A, ea, neg(n), tol + dn)
    if sb < 0 or sa < 0:
        return None
    band = (max(extent_tol, fl) + gap * fl / norm(d)) / norm(d)      # 长度带 + 杠杆项（同 ee_cover）
    return Cover3("EV3", ("edge", ea[0], ea[1]), ("vertex", ib), n, gap, add(p0, mul(d, _clamp01(s))), b, (s,), None,
                  sb == 1 and sa == 1, -band <= s <= 1.0 + band)


def vv3_cover(A: Polyhedron, ia: int, B: Polyhedron, ib: int, tol: float = 0.0) -> Cover3 | None:
    """A 的顶点 × B 的顶点 → ∂E 的顶点（零维盖，法向集值）。

    两个判据必须分开（2026-09-18 实测混为一谈会让 E 顶点数恒为 0）：
      strict    = 两锥**相对内部相交** ⟺ 这对顶点确实给出 ∂E 的一个顶点（命题 4）；
      in_extent = 分离方向 a − b 落在交锥内 ⟺ 参考点到 E 的最近特征正是这个顶点（活跃）。
    """
    a, b = A.verts[ia], B.verts[ib]
    is_vertex = cones_intersect_relint(A, ia, B, ib, max(tol, 1e-12))
    if not is_vertex:
        return None
    v = sub(a, b)
    if norm(v) <= _pair_floor(A, B):
        return Cover3("VV3", ("vertex", ia), ("vertex", ib), None, 0.0, a, b, (), None, True, True)
    n = unit(v)
    dn = _pair_floor(A, B) / norm(v)               # 分离方向自身的噪声，同 ve3_cover
    active = (vertex_cone_contains(B, ib, n, tol + dn) >= 0 and vertex_cone_contains(A, ia, neg(n), tol + dn) >= 0)
    return Cover3("VV3", ("vertex", ia), ("vertex", ib), n, norm(v), a, b, (), None, True, active)


# ------------------------------------------------------------------ 枚举

def enumerate_covers3(A: Polyhedron, B: Polyhedron, *, window: float, tol: float = 0.0,
                      require_in_extent: bool = True, include_low_dim: bool = True,
                      extent_tol: float = 0.0) -> list[Cover3]:
    """当前位形下所有有效且在距离窗口内的三维盖。

    有效 = 法锥**闭**条件成立（判据 ≥ 0）；strict 只是盖上的一个字段，**任何一类盖都不按
    strict 过滤**。低维盖尤其不能过滤（2026-09-21 审查 C10 实测）：平行棱-棱最近对
    （EEP 退化，ee_cover 对平行棱返回 None）只由边界态 VE3/EV3 表达，一旦按 strict 过滤，
    margin.body_distance 的距离完备性就丢（tests/test_margin.py 三例红）。
    tol 是角度（法锥判据），extent_tol 是长度（in_extent 的边界带），见模块文档"容差"。
    """
    out: list[Cover3] = []
    for ia in range(len(A.verts)):
        for fb in range(len(B.faces)):
            c = vf_cover(A, ia, B, fb, tol, extent_tol)
            if c is not None and abs(c.gap) <= window and (c.in_extent or not require_in_extent):
                out.append(c)
    for fa in range(len(A.faces)):
        for ib in range(len(B.verts)):
            c = fv_cover(A, fa, B, ib, tol, extent_tol)
            if c is not None and abs(c.gap) <= window and (c.in_extent or not require_in_extent):
                out.append(c)
    for ea in A.edges():
        for eb in B.edges():
            c = ee_cover(A, ea, B, eb, tol, extent_tol)
            if c is not None and abs(c.gap) <= window and (c.in_extent or not require_in_extent):
                out.append(c)
    if include_low_dim:
        for ia in range(len(A.verts)):
            for eb in B.edges():
                c = ve3_cover(A, ia, B, eb, tol, extent_tol)
                if c is not None and abs(c.gap) <= window and (c.in_extent or not require_in_extent):
                    out.append(c)
        for ea in A.edges():
            for ib in range(len(B.verts)):
                c = ev3_cover(A, ea, B, ib, tol, extent_tol)
                if c is not None and abs(c.gap) <= window and (c.in_extent or not require_in_extent):
                    out.append(c)
        for ia in range(len(A.verts)):
            for ib in range(len(B.verts)):
                c = vv3_cover(A, ia, B, ib, tol)
                if c is not None and c.in_extent and c.gap <= window:
                    out.append(c)
    return out


def local_facets3(A: Polyhedron, B: Polyhedron, tol: float = 0.0) -> set[tuple]:
    """严格有效的 facet 型盖（VF/FV/EE），不设窗口、不限面内——命题 4 的局部规则产物。"""
    out: set[tuple] = set()
    for ia in range(len(A.verts)):
        for fb in range(len(B.faces)):
            c = vf_cover(A, ia, B, fb, tol)
            if c is not None and c.strict:
                out.add(c.label())
    for fa in range(len(A.faces)):
        for ib in range(len(B.verts)):
            c = fv_cover(A, fa, B, ib, tol)
            if c is not None and c.strict:
                out.add(c.label())
    for ea in A.edges():
        for eb in B.edges():
            c = ee_cover(A, ea, B, eb, tol)
            if c is not None and c.strict:
                out.add(c.label())
    return out


def facet_normal3(A: Polyhedron, B: Polyhedron, label: tuple) -> Vec3:
    """facet 标签对应的 E 的**定向外法向**（B → A 的分离方向）。

    VF → n_B(face)；FV → −n_A(face)；EE → ±unit(t_B × t_A)，取落在 B 棱弧里的那一支。
    facet_gap3 与 G0 票二共用它（票二的另一侧不经它，见 g03.g0_convex3）。
    """
    kind, af, bf = label
    if kind == "VF":
        return B.face_normal(bf[1])
    if kind == "FV":
        return neg(A.face_normal(af[1]))
    if kind == "EE":
        ea = (af[1], af[2])
        eb = (bf[1], bf[2])
        tB, tA = B.edge_dir(eb), A.edge_dir(ea)
        c = cross(tB, tA)
        n = unit(c)
        ctol = 1e-9 + (A.edge_noise(ea) + B.edge_noise(eb)) / norm(c)     # 候选自身的方向噪声（同 ee_cover）
        if edge_arc_contains(B, eb, _orth(n, tB), ctol) < 0:   # 取与 B 的弧一致的朝向（按构造正交后判）
            n = neg(n)
        return n
    raise ValueError(f"not a facet label: {label}")


def facet_gap3(A: Polyhedron, B: Polyhedron, label: tuple, x: Vec3) -> float:
    """E 的一条 facet 在平移 x 下的有符号间隙（>0 参考点在该 facet 外侧）。"""
    kind, af, bf = label
    n = facet_normal3(A, B, label)
    if kind == "VF":
        return dot(n, sub(add(A.verts[af[1]], x), B.verts[B.faces[bf[1]][0]]))
    if kind == "FV":
        return dot(n, sub(add(A.verts[A.faces[af[1]][0]], x), B.verts[bf[1]]))
    return dot(n, sub(add(A.verts[af[1]], x), B.verts[bf[1]]))           # EE


def support_gaps3(A: Polyhedron, B: Polyhedron, x: Vec3) -> list[float]:
    """E = B ⊕ (−A) 在 A、B **每个面法向**上的支撑半空间间隙（>0 参考点在外侧），与严格性无关。

    B 的面 fb（外法向 n）：取 a* = argmin_a n·a，间隙 n·(a* + x − b_f)；
    A 的面 fa（外法向 m）：E 的法向是 −m，取 b* = argmin_b m·b，间隙 (−m)·(a_f + x − b*)。
    每一条都是 E 的合法支撑半空间（含 E）；FF/FE 退化 facet 的法向恰好都在其中。
    """
    gaps: list[float] = []
    for fb in range(len(B.faces)):
        n = B.face_normal(fb)
        ia = min(range(len(A.verts)), key=lambda i: dot(n, A.verts[i]))
        gaps.append(dot(n, sub(add(A.verts[ia], x), B.verts[B.faces[fb][0]])))
    for fa in range(len(A.faces)):
        m = A.face_normal(fa)
        ib = min(range(len(B.verts)), key=lambda i: dot(m, B.verts[i]))
        gaps.append(dot(neg(m), sub(add(A.verts[A.faces[fa][0]], x), B.verts[ib])))
    return gaps


def membership_convex3(A: Polyhedron, B: Polyhedron, x: Vec3, tol: float = 0.0,
                       facets: set[tuple] | None = None, *, ang_tol: float = 1e-12) -> int:
    """参考点相对 E 的位置：1 内部（A+x 与 B 内部相交）/ 0 边界 / -1 外部。A、B 凸，**不要求一般位置**。

    E 的 facet 法向只有三类来源：B 的面法向、−(A 的面法向)、严格交叉棱-棱（命题 4）。
    前两类用 `support_gaps3` 的**全部**支撑半空间覆盖（含 FF/FE 退化 facet），第三类取 facets
    里的 EE 标签；facets 里的 VF/FV 标签也一并取 max（合法标签的间隙与支撑间隙相同，错标签只会
    把答案推向"外部"，于是被票一抓住）。

    2026-09-21 审查 C2（critical）：此前只对 strict facet 取 max——平行面生成的 facet 全被丢，
    四面体 vs 方块在 +x 侧恒判"相交"，两个轴对齐方块对空集取 max 崩溃。

    tol 是**长度**（边界带，调用方单位，抬到舍入地板）；不给 facets 时用**角度** ang_tol 求局部 facet。旧版把同一个
    tol 两处都用：tol = 1e-3·s、s = 1e3 时角容差 1 rad，严格 EE facet 全被丢，分离的一对判"相交"（G6 第二轮 minor）。
    """
    if facets is None:
        facets = local_facets3(A, B, ang_tol)
    g = max(support_gaps3(A, B, x) + [facet_gap3(A, B, lab, x) for lab in facets])
    # 边界带加舍入地板（纪律 F）：间隙由量级 C 的坐标相减得到，恰相触的位形在远坐标下是 ±eps·C 的噪声
    tol = max(tol, noise_floor(max(A.metrics()[0] + max(abs(c) for c in x), B.metrics()[0])))
    if g > tol:
        return -1
    if g < -tol:
        return 1
    return 0
