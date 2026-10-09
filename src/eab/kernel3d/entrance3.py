"""三维首入（命题 7，M2）：沿给定的相对平动方向，A 的参考点首次触及 ∂E 的点定接触点与法向；已侵入时取最短出口。

正本（`D:\\E(A, B)\\01` 命题 7）：三维多面体的接触不确定性（v-v、v-e 接触时法向不唯一、面-面接触时接触点不唯一）恰在 ∂E 的
集值点（命题 6(iii)）上；石根华的**首入准则**是对集值性的一个确定性选择规则——它需要运动（"首次"），静态位形本身给不出。
本模块是三维的第一份实现（`docs/canon_map.md` 此前记"三维零实现"；二维 `covers.first_entrance_for_vertex` 是不接收运动方向的
静态简化版）。

定义。参考点沿射线 x(t) = x0 + t·d（t ≥ 0；A 平移 x(t)，B 固定）运动：
  · 首入时刻 t* = min{t ≥ 0 : x(t) ∈ E(A, B)}，首入点 x(t*) ∈ ∂E；接触法向 = 该点所在 facet 的外法向（B → A 的分离方向），
    接触点 = 该 facet 对应盖在 x(t*) 处的见证点对；
  · 首入点落在 E 的棱 / 顶点上（多个 facet 在分辨率内同时被触及）时法向集值：按**枚举序取第一个**作裁决，并把并列集如实报出
    （`tied_labels`），与 `interlock.escape_height_covers` 同一口径——不装作唯一；
  · x0 已在 E 内（已侵入）：取**最短出口**——在程的 facet 型盖里取间隙最大者（侵入最浅）作接触法向与出口方向（二维版同此规则；
    凸 E 时它就是 E 内侧的分片线性深度 min_i(面距) 的那个最小者，命题 6(ii)）。

算法（与逃逸高度同构：**盖提供完备候选集、精确谓词裁决**，纪律 A 的 oracle 是不经盖的 `first_entrance_brute`）：
  facet 型盖（VF/FV/EE）的间隙沿平移仿射：gap(t) = gap(x0) + t·(n·d)。只有 n·d < 0 的盖（前进能把它合上）给出候选 t_i = gap/|n·d|；
  候选升序，每个在**它自己的 t_i 处**重新求盖、要求 in_extent（投影落在面内 / 段内——x0 处的 in_extent 说明不了 t_i 处的情况，
  理由见 `interlock.escape_candidates`）；第一个在程的候选即首入。凸 E 时它恰是全部"进入型"facet 时刻里最大的那个（闭式可证：
  更早的候选在 t_i 处 x 仍在 E 外，投影必落在面外），凹体时靠谓词裁决。谓词核验两条：t* 处两体相触或相交（`polyhedra_overlap` ≥ 0，
  否则该候选不是真接触，跳过）；t* 之前一个分辨步处两体分离——否则候选集漏了更早的首入，抛 RuntimeError（不静默）。
  低维盖（VE3/EV3/VV3）不给候选（它们的间隙是无符号距离），首入点落在 E 的棱 / 顶点上时由对应的 facet 型盖代表。

退化族（M2 的另一半）：面-面（FF）、棱平行于面（FE）在局部规则里只以多个 facet 型盖出现（4 个 VF 之类）。`merge_degenerate`
  把法向一致（各自面 / 棱的方向噪声内）且共享同一张面的盖收成一个盖（kind FF / FE），`members` 保留展开视图——DDA
  （3-b-dda 的 np 入口 = 动块顶点 × 固定块面上的三角形）消费的正是展开视图；平行棱-棱（EEP）在局部规则里由 VF/FV 的边界态表达，
  并进 FE 或留作单个盖，不另立种类（本版如实记：EEP 没有自己的合并规则）。

容差（纪律 F）：谓词容差 geom_tol_eff 随尺度（`margin.effective_geom_tol`）；并列按法向间隙 ≤ geom_tol_eff + 舍入地板判；候选
  t_i 的舍入 ~ 地板/|n·d|；退化族的法向一致性用各自面的法向噪声（`Polyhedron.face_noise`）。
"""

from __future__ import annotations

from dataclasses import dataclass

from ..margin import characteristic_length, effective_geom_tol, rounding_floor
from .covers3 import Cover3, ee_cover, enumerate_covers3, fv_cover, vf_cover
from .geom3 import Polyhedron, Vec3, add, cross, dot, mul, neg, norm, polyhedra_overlap, sub

FACET_KINDS = ("VF", "FV", "EE")


@dataclass(slots=True)
class Entrance3:
    kind: str                       # "entrance"（沿射线首入）| "exit"（已侵入，最短出口）| "none"（射线在 t_max 内不触及 E）
    t: float                        # 首入参数（exit / none 时 0）
    x: Vec3 | None                  # 首入位形的平移 x0 + t·d（exit 时 x0）
    label: tuple | None             # 裁决出的盖标签（退化族合并后为 FF / FE 标签）
    normal: Vec3 | None             # 接触法向（B → A 的分离方向）
    point_a: Vec3 | None            # 代表盖在该位形下的见证点对
    point_b: Vec3 | None
    gap: float = 0.0                # 代表盖在该位形下的有符号间隙（entrance ≈ 0；exit 为负，|gap| = 最浅侵入深度）
    tied_labels: tuple = ()         # 分辨率内并列的全部局部盖标签（集值点），代表盖的成员排在前
    members: tuple = ()             # 代表盖的退化族展开（局部规则的原始盖标签；非退化时就是 (label,)）
    n_candidates: int = 0


def _facet_covers(At: Polyhedron, B: Polyhedron, tol: float) -> list[Cover3]:
    return enumerate_covers3(At, B, window=float("inf"), tol=tol, require_in_extent=False, include_low_dim=False)


def _cover_at(At: Polyhedron, B: Polyhedron, label: tuple, tol: float, extent_tol: float) -> Cover3 | None:
    """同一对特征在平移后的位形上重新求盖（有效性只看法锥，与平移无关；in_extent 随平移变）。"""
    kind, af, bf = label
    if kind == "VF":
        return vf_cover(At, af[1], B, bf[1], tol, extent_tol)
    if kind == "FV":
        return fv_cover(At, af[1], B, bf[1], tol, extent_tol)
    if kind == "EE":
        return ee_cover(At, (af[1], af[2]), B, (bf[1], bf[2]), tol, extent_tol)
    return None


def _cover_noise(A: Polyhedron, B: Polyhedron, c: Cover3) -> float:
    """盖法向自身的方向噪声（弧度）：VF 取 B 面、FV 取 A 面、EE 取两棱噪声 / sinθ。"""
    if c.kind == "VF":
        return B.face_noise(c.b_feature[1])
    if c.kind == "FV":
        return A.face_noise(c.a_feature[1])
    ea, eb = (c.a_feature[1], c.a_feature[2]), (c.b_feature[1], c.b_feature[2])
    s = norm(cross(B.edge_dir(eb), A.edge_dir(ea)))
    return (A.edge_noise(ea) + B.edge_noise(eb)) / max(s, 1e-300)


def _coplanar_face_with_normal(P: Polyhedron, n: Vec3, verts: set[int], ang: float, lt: float) -> int | None:
    """P 里外法向与 n 平行（夹角 ≤ ang）、至少含 verts 中一个顶点、且 verts 全部落在其平面上（|n·(v − v_f0)| ≤ lt）的面，
    取最小下标。三角化的面（夹具经凸包重建）会把一张几何面拆成几片，所以不要求一片含全部顶点。"""
    best = None
    for fi, f in enumerate(P.faces):
        if not (verts & set(f)) or norm(sub(P.face_normal(fi), n)) > ang:
            continue
        o = P.verts[f[0]]
        if all(abs(dot(n, sub(P.verts[v], o))) <= lt for v in verts):
            if best is None or fi < best:
                best = fi
    return best


def _edge_of(P: Polyhedron, verts: set[int]) -> tuple[int, int] | None:
    if len(verts) != 2:
        return None
    for e in P.edges():
        if set(e) == verts:
            return e
    return None


def merge_degenerate(A: Polyhedron, B: Polyhedron, covers: list[Cover3], tol: float = 1e-9) -> list[tuple[tuple, tuple]]:
    """把法向一致、落在同一平面上的局部盖收成退化盖：返回 [(代表标签, 成员标签元组)]（非退化的盖 members = (自身,)）。

    规则。先按法向分组（组内法向夹角 ≤ tol + 两盖法向噪声之和），组内 VF 按 B 面平面偏移、FV 按 A 面平面偏移聚成"同一平面簇"
    （偏移差 ≤ lt = 4·舍入地板 + 法向容差 × 特征长度；三角化的面在这里重新合成一张几何面）；每簇：
      · 只有 VF（≥ 2 个）：A 有一张面以 −n 为外法向、含其中顶点且全部顶点落在其平面上 → ("FF", ("face", fa), ("face", fb))
        （fa、fb 取簇内最小下标）；A 没有这样的面但这些顶点恰是 A 的一条棱 → ("FE", ("edge", a0, a1), ("face", fb))；
      · 只有 FV 对称 → FF 或 ("FE", ("face", fa), ("edge", b0, b1))；
      · VF 与 FV 都有（两张面互相平行且共面、两边顶点都在程）→ 一个 FF；
      · EE 与收不成的簇各自保留。
    """
    L = characteristic_length(A, B)
    rfl = rounding_floor(A, B)
    groups: list[list[Cover3]] = []
    for c in covers:
        if c.normal is None:
            groups.append([c])
            continue
        for g in groups:
            g0 = g[0]
            if g0.normal is not None and norm(sub(c.normal, g0.normal)) <= tol + _cover_noise(A, B, c) + _cover_noise(A, B, g0):
                g.append(c)
                break
        else:
            groups.append([c])
    out: list[tuple[tuple, tuple]] = []
    for g in groups:
        if len(g) < 2 or g[0].normal is None:
            for c in g:
                out.append((c.label(), (c.label(),)))
            continue
        n = g[0].normal
        ang = tol + max(_cover_noise(A, B, c) for c in g)
        lt = 4.0 * rfl + ang * L
        clusters: list[list] = []                      # [偏移, [盖]]
        for c in g:
            if c.kind == "VF":
                o = dot(n, B.verts[B.faces[c.b_feature[1]][0]])
            elif c.kind == "FV":
                o = dot(n, A.verts[A.faces[c.a_feature[1]][0]])
            else:
                out.append((c.label(), (c.label(),)))
                continue
            for cl in clusters:
                if abs(cl[0] - o) <= lt:
                    cl[1].append(c)
                    break
            else:
                clusters.append([o, [c]])
        for _, cs in clusters:
            labels = tuple(c.label() for c in cs)
            if len(cs) < 2:
                out.append((labels[0], labels))
                continue
            vf = [c for c in cs if c.kind == "VF"]
            fv = [c for c in cs if c.kind == "FV"]
            va = {c.a_feature[1] for c in vf}
            vb = {c.b_feature[1] for c in fv}
            fb = min((c.b_feature[1] for c in vf), default=None)
            fa = min((c.a_feature[1] for c in fv), default=None)
            rep = None
            if vf and not fv:
                fa2 = _coplanar_face_with_normal(A, neg(n), va, ang, lt)
                if fa2 is not None:
                    rep = ("FF", ("face", fa2), ("face", fb))
                else:
                    ea = _edge_of(A, va)
                    if ea is not None:
                        rep = ("FE", ("edge", ea[0], ea[1]), ("face", fb))
            elif fv and not vf:
                fb2 = _coplanar_face_with_normal(B, n, vb, ang, lt)
                if fb2 is not None:
                    rep = ("FF", ("face", fa), ("face", fb2))
                else:
                    eb = _edge_of(B, vb)
                    if eb is not None:
                        rep = ("FE", ("face", fa), ("edge", eb[0], eb[1]))
            else:
                rep = ("FF", ("face", fa), ("face", fb))
            if rep is None:
                for c in cs:
                    out.append((c.label(), (c.label(),)))
            else:
                out.append((rep, labels))
    return out


def _representative(merged: list[tuple[tuple, tuple]], label: tuple) -> tuple[tuple, tuple]:
    """裁决出的盖所在的退化族（代表标签, 成员）。"""
    for rep, members in merged:
        if label in members:
            return rep, members
    return label, (label,)


def first_entrance3(A: Polyhedron, B: Polyhedron, x0: Vec3, d: Vec3, *, tol: float = 1e-9,
                    geom_tol: float | None = None, t_max: float = float("inf")) -> Entrance3:
    """沿 x(t) = x0 + t·d 的首入（见模块文档）。tol 是法锥判据的角度容差；geom_tol 是谓词的长度容差（None 随尺度）。"""
    dn = norm(d)
    if dn == 0.0:
        raise ValueError("direction must be nonzero")
    At = A.translated(x0)
    gtol = effective_geom_tol(At, B, geom_tol)
    r = rounding_floor(At, B)
    if polyhedra_overlap(At, B, gtol) == 1:
        return shortest_exit3(A, B, x0, tol=tol, geom_tol=geom_tol)
    raw: list[tuple[float, Cover3, float, int]] = []
    for idx, c in enumerate(_facet_covers(At, B, tol)):
        nd = dot(c.normal, d)
        if nd >= -1e-12 * dn:                 # 前进不合上这个 facet
            continue
        if c.gap < -r:                        # 这个 facet 的平面已在身后
            continue
        t = max(0.0, c.gap / (-nd))
        if t <= t_max + r / (-nd):            # t_max 带候选自身的舍入（gap 的地板 / |n·d|）
            raw.append((t, c, nd, idx))
    raw.sort(key=lambda q: (q[0], q[3]))
    for t, c, nd, idx in raw:
        x = add(x0, mul(d, t))
        Ax = A.translated(x)
        cc = _cover_at(Ax, B, c.label(), tol, gtol)
        if cc is None or not cc.in_extent:
            continue
        if polyhedra_overlap(Ax, B, gtol) < 0:       # 盖说相触、谓词说分离：不是真接触
            continue
        step = 2.0 * (gtol + r) / (-nd)
        if t - step > 0.0 and polyhedra_overlap(A.translated(add(x0, mul(d, t - step))), B, gtol) >= 0:
            raise RuntimeError(f"first_entrance3: bodies already touch at t = {t - step!r} < candidate {t!r} "
                               f"({c.label()}); the facet-cover candidate set missed an earlier entrance")
        # 并列：法向间隙在 gtol + r 以内、且在 x 处在程的候选
        tied: list[Cover3] = []
        for t2, c2, nd2, idx2 in raw:
            if abs(t2 - t) * (-nd2) <= gtol + r:
                c2x = _cover_at(Ax, B, c2.label(), tol, gtol)
                if c2x is not None and c2x.in_extent:
                    tied.append(c2x)
        tied.sort(key=lambda q: 0 if q.label() == cc.label() else 1)
        rep_label, members = _representative(merge_degenerate(Ax, B, tied, tol), cc.label())
        return Entrance3("entrance", t, x, rep_label, cc.normal, cc.point_a, cc.point_b, cc.gap,
                         tuple(q.label() for q in tied), members, len(raw))
    # 没有在程的候选：答"不触及"之前用谓词核一遍候选时刻与相邻候选的中点——候选集若漏了真首入（局部规则在凹体上到不了、
    # 或盖枚举被改坏），两体会在某个候选时刻已相触/相交，那就抛错，不许静默答"none"
    ts = sorted({q[0] for q in raw})
    probes = ts + [0.5 * (a + b) for a, b in zip(ts, ts[1:])]
    for tp in probes:
        if polyhedra_overlap(A.translated(add(x0, mul(d, tp))), B, gtol) >= 0:
            raise RuntimeError(f"first_entrance3: no in-extent facet-cover candidate, yet the bodies touch at t = {tp!r}; "
                               f"the candidate set missed an earlier entrance")
    return Entrance3("none", 0.0, None, None, None, None, None, 0.0, (), (), len(raw))


def shortest_exit3(A: Polyhedron, B: Polyhedron, x0: Vec3, *, tol: float = 1e-9,
                   geom_tol: float | None = None) -> Entrance3:
    """已侵入位形的最短出口：在程的 facet 型盖里取间隙最大者（侵入最浅）。并列按 gtol + 舍入判、枚举序裁决。"""
    At = A.translated(x0)
    gtol = effective_geom_tol(At, B, geom_tol)
    r = rounding_floor(At, B)
    cands = [c for c in _facet_covers(At, B, tol) if c.in_extent and c.gap <= gtol + r]
    if not cands:
        raise RuntimeError("shortest_exit3: penetrating configuration with no in-extent facet cover "
                           "(concave pair outside the local rule's reach?)")
    best = max(cands, key=lambda c: c.gap)
    tied = [c for c in cands if best.gap - c.gap <= gtol + r]
    tied.sort(key=lambda q: 0 if q.label() == best.label() else 1)
    rep_label, members = _representative(merge_degenerate(At, B, tied, tol), best.label())
    return Entrance3("exit", 0.0, x0, rep_label, best.normal, best.point_a, best.point_b, best.gap,
                     tuple(q.label() for q in tied), members, len(cands))


def first_entrance_brute(A: Polyhedron, B: Polyhedron, x0: Vec3, d: Vec3, *, t_max: float, steps: int = 400,
                         geom_tol: float | None = None) -> float | None:
    """纪律 A 的 oracle：只用谓词。把 [0, t_max] 均分扫描，找到第一个 `polyhedra_overlap` ≥ 0 的步，再在前一步与它之间二分到
    1e-10·L。扫描步长必须小于 A 沿 d 穿过 B 的最短时间（否则跳过一次穿越）——这是 oracle 的前提，由测试负责（steps 取大）。
    返回 None 表示扫描内不触及；x0 已相触/相交时返回 0。"""
    At = A.translated(x0)
    gtol = effective_geom_tol(At, B, geom_tol)
    L = characteristic_length(At, B)

    def state(t: float) -> int:
        return polyhedra_overlap(A.translated(add(x0, mul(d, t))), B, gtol)

    if state(0.0) >= 0:
        return 0.0
    prev = 0.0
    hit = None
    for k in range(1, steps + 1):
        t = t_max * k / steps
        if state(t) >= 0:
            hit = t
            break
        prev = t
    if hit is None:
        return None
    lo, up = prev, hit
    ztol = max(1e-10 * L, 8.0 * 2.220446049250313e-16 * t_max)
    while up - lo > ztol:
        mid = 0.5 * (lo + up)
        if state(mid) >= 0:
            up = mid
        else:
            lo = mid
    return up
