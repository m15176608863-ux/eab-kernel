"""三维首入：给定数据精确，浮点仅构造输出（WO-E5b）。

非共面输入环按 geom3.exact_surface 的确定性三角面解释。候选根、方向号、
t_max、排序、并列、最短出口平方距离和退化族共面都用 Fraction 精确比较。
完整 surface_events 分割运动参数轴；前一个候选区间内的有理中点精确核验
首入之前分离，遗漏可见的真接触时抛 RuntimeError，不以浮点步长冒充证书。

Entrance3.label/members 是兼容源面编号；surface_label/surface_members 才是
非共面源环上的精确三角限定标签，冻结时应使用后者。exact_t 是精确时刻；
t、x、normal 和 witness 点是浮点构造，不能回流为组合判据。

tol 仅是显式法锥域窗口，geom_tol 为兼容参数、不再隐式加厚集合。
first_entrance_brute 共用生产重叠谓词，只是抽样佐证，不是独立主 oracle。
门：tests/test_entrance3_exact.py；随机凸对的主 oracle 为独立整数 SAT。
"""

from __future__ import annotations
from eab.construction import scalar_rational

from dataclasses import dataclass
from fractions import Fraction
from math import isfinite
from .entrance_topology import entrance_membership3

from ..margin import characteristic_length, effective_geom_tol
from .covers3 import (Cover3, ee_cover, enumerate_covers3, fv_cover, vf_cover,
                      _facet_plane_on_views, _qvector)
from .geom3 import Polyhedron, Vec3, add, cross, dot, mul, neg, norm, polyhedra_overlap, sub, exact_surface

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
    tied_labels: tuple = ()         # 精确同一时刻并列的全部局部盖标签（集值点），代表盖的成员排在前
    members: tuple = ()             # 代表盖的退化族展开（局部规则的原始盖标签；非退化时就是 (label,)）
    n_candidates: int = 0
    exact_t: Fraction | None = None  # exact event; t and x are constructions only
    surface_label: tuple | None = None  # exact triangle-qualified frozen feature
    surface_members: tuple = ()


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


def _same_direction(a, b):
    """Exact positive parallelism, not a normalized-vector angle test."""
    return not any(cross(a, b)) and dot(a, b) > 0


def _same_plane(n, a, b):
    """Exact coplanarity of the supplied data (mutation gate names this helper)."""
    return dot(n, sub(a, b)) == 0


def _coplanar_face_with_normal(P, n, verts):
    from .geom3 import exact_face_normal
    for fi, f in enumerate(P.faces):
        if not verts.intersection(f) or not _same_direction(exact_face_normal(P, fi), n):
            continue
        o = _qvector(P.verts[f[0]])
        if all(_same_plane(n, _qvector(P.verts[v]), o) for v in verts):
            return fi
    return None


def _edge_of(P: Polyhedron, verts: set[int]) -> tuple[int, int] | None:
    if len(verts) != 2:
        return None
    for e in P.edges():
        if set(e) == verts:
            return e
    return None


def merge_degenerate(A: Polyhedron, B: Polyhedron, covers: list[Cover3], tol: float = 1e-9) -> list[tuple[tuple, tuple]]:
    """把法向一致、落在同一平面上的局部盖收成退化盖：返回 [(代表标签, 成员标签元组)]（非退化的盖 members = (自身,)）。

    规则。精确同向法向分组，VF 按 B 面、FV 按 A 面的精确平面方程分簇。
    只有给定数据严格共面才合并；tol 不改变退化关系。每簇：
      · 只有 VF（≥ 2 个）：A 有一张面以 −n 为外法向、含其中顶点且全部顶点落在其平面上 → ("FF", ("face", fa), ("face", fb))
        （fa、fb 取簇内最小下标）；A 没有这样的面但这些顶点恰是 A 的一条棱 → ("FE", ("edge", a0, a1), ("face", fb))；
      · 只有 FV 对称 → FF 或 ("FE", ("face", fa), ("edge", b0, b1))；
      · VF 与 FV 都有（两张面互相平行且共面、两边顶点都在程）→ 一个 FF；
      · EE 与收不成的簇各自保留。
    """
    groups: list[list[Cover3]] = []
    normals = {}
    for c in covers:
        if c.normal is None:
            groups.append([c])
            continue
        n, _ = _facet_plane_on_views(A, B, c.label(), tol)
        normals[c.label()] = n
        for g in groups:
            if g[0].normal is not None and _same_direction(n, normals[g[0].label()]):
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
        n = normals[g[0].label()]
        clusters: list[list] = []                      # [偏移, [盖]]
        for c in g:
            if c.kind == "VF":
                o = _qvector(B.verts[B.faces[c.b_feature[1]][0]])
            elif c.kind == "FV":
                o = _qvector(A.verts[A.faces[c.a_feature[1]][0]])
            else:
                out.append((c.label(), (c.label(),)))
                continue
            for cl in clusters:
                if _same_plane(n, cl[0], o):
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
                fa2 = _coplanar_face_with_normal(A, neg(n), va)
                if fa2 is not None:
                    rep = ("FF", ("face", fa2), ("face", fb))
                else:
                    ea = _edge_of(A, va)
                    if ea is not None:
                        rep = ("FE", ("edge", ea[0], ea[1]), ("face", fb))
            elif fv and not vf:
                fb2 = _coplanar_face_with_normal(B, n, vb)
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


def _translated_exact(P, x):
    return Polyhedron([add(_qvector(p), _qvector(x)) for p in P.verts], list(P.faces))


def _ray_shift(x0, d, t):
    return add(_qvector(x0), mul(_qvector(d), t))


def _preceding_probe(t, events):
    """An exact interior point of the immediately preceding event interval."""
    previous = max((q for q in events if q < t), default=Fraction(0))
    return (previous + t) / 2


def _source_label(label, A, B, *, qualify=False):
    if label is None:
        return None
    kind, af, bf = label
    def feature(f, P):
        if f[0] != "face":
            return f
        fi = f[1]
        source = P.source_faces[fi][0]
        # Nonplanar source rings are not geometric planes: record the actual
        # triangle so frozen evaluation cannot silently use its Newell vector.
        if qualify and len(P.faces[fi]) == 3 and sum(source in fs for fs in P.source_faces) > 1:
            return ("face", source, "triangle", *P.faces[fi])
        return ("face", source)
    return kind, feature(af, A), feature(bf, B)


def _restore_sources(result, A, B):
    result.surface_label = _source_label(result.label, A, B, qualify=True)
    result.surface_members = tuple(dict.fromkeys(_source_label(lab, A, B, qualify=True) for lab in result.members))
    result.label = _source_label(result.label, A, B)
    result.members = tuple(dict.fromkeys(_source_label(lab, A, B) for lab in result.members))
    result.tied_labels = tuple(dict.fromkeys(_source_label(lab, A, B) for lab in result.tied_labels))
    return result


def first_entrance3(A: Polyhedron, B: Polyhedron, x0: Vec3, d: Vec3, *, tol: float = 1e-9,
                    geom_tol: float | None = None, t_max: float = float("inf")) -> Entrance3:
    """Exact supplied-data first event; floating normal/point/time are outputs only.

    An initial topological int(E) configuration, including a tight-fit seam
    without body-interior overlap, uses shortest_exit3. This is the existing
    local-facet policy, not global nonconvex penetration depth: a seam's local
    exit gap can be zero without asserting that it lies on the true boundary E.
    Gate: test_r8fix_initial_state3. An initial boundary E configuration
    returns exact_t=0, including tangential/departing motion and t_max=0;
    finite zero-gap facets are collected independently of motion direction.
    Gate: test_r10_initial_boundary.

    geom_tol is retained for source compatibility but never thickens the set.
    Candidate roots, ordering, t_max and ties are rational. The complete surface
    event partition supplies an exact preceding interval for the self-check.
    """
    if not any(d):
        raise ValueError("direction must be nonzero")
    A, B = exact_surface(A), exact_surface(B)
    At = _translated_exact(A, x0)
    initial = entrance_membership3(At, B)
    if initial == 1:
        return _restore_sources(shortest_exit3(A, B, x0, tol=tol, geom_tol=geom_tol), A, B)
    if initial == 0:
        # Closed first entrance already occurred, independent of d and its
        # approaching/tangential/departing signs. Keep all finite zero-gap
        # facets; filtering nd < 0 here would lose tangential/departing touch.
        tied = []
        for c in _facet_covers(At, B, tol):
            n, p = _facet_plane_on_views(At, B, c.label(), tol)
            if c.in_extent and dot(n, p) == 0:
                tied.append(c)
        if not tied:
            raise RuntimeError("first_entrance3: initial boundary has no in-extent zero-gap facet cover")
        best = tied[0]
        rep_label, members = _representative(merge_degenerate(At, B, tied, tol), best.label())
        return _restore_sources(Entrance3(
            "entrance", 0.0, tuple(map(scalar_rational, x0)), rep_label, best.normal,
            tuple(map(scalar_rational, best.point_a)), tuple(map(scalar_rational, best.point_b)),
            best.gap, tuple(c.label() for c in tied), members, len(tied), Fraction(0)), A, B)
    raw = []
    for idx, c in enumerate(_facet_covers(At, B, tol)):
        n, p = _facet_plane_on_views(At, B, c.label(), tol)
        nd, gap = dot(n, _qvector(d)), -dot(n, p)
        if nd >= 0 or gap < 0:
            continue
        t = -gap / nd
        if not isfinite(t_max) or t <= Fraction(t_max):
            raw.append((t, c, nd, idx))
    raw.sort(key=lambda q: (q[0], q[3]))
    # Import locally to avoid a circular dependency with domain-level callers.
    from .exact_sweep import surface_events
    events = tuple(event.time for event in surface_events(
        A, B, direction=d, start=x0, t_min=0,
        t_max=Fraction(t_max) if isfinite(t_max) else None))
    for t, c, nd, idx in raw:
        exact_x = _ray_shift(x0, d, t)
        Ax = _translated_exact(A, exact_x)
        cc = _cover_at(Ax, B, c.label(), tol, 0.0)
        if cc is None or not cc.in_extent:
            continue
        if polyhedra_overlap(Ax, B, 0.0) < 0:
            continue
        earlier = min(events, default=t)
        if earlier < t and polyhedra_overlap(_translated_exact(A, _ray_shift(x0, d, earlier)), B, 0.0) >= 0:
            raise RuntimeError("first_entrance3: the facet-cover candidate set missed an earlier entrance "
                               f"at exact surface event {earlier!r} before {t!r}")
        before = _preceding_probe(t, events)
        if t > 0 and polyhedra_overlap(_translated_exact(A, _ray_shift(x0, d, before)), B, 0.0) >= 0:
            raise RuntimeError(f"first_entrance3: bodies already touch at t = {before!r} < candidate {t!r} "
                               f"({c.label()}); the facet-cover candidate set missed an earlier entrance")
        tied = []
        for t2, c2, _, _ in raw:
            if t2 == t:
                c2x = _cover_at(Ax, B, c2.label(), tol, 0.0)
                if c2x is not None and c2x.in_extent:
                    tied.append(c2x)
        tied.sort(key=lambda q: 0 if q.label() == cc.label() else 1)
        rep_label, members = _representative(merge_degenerate(Ax, B, tied, tol), cc.label())
        return _restore_sources(Entrance3("entrance", scalar_rational(t), tuple(map(scalar_rational, exact_x)), rep_label, cc.normal,
                         cc.point_a, cc.point_b, cc.gap, tuple(q.label() for q in tied),
                         members, len(raw), t), A, B)
    # No valid local cover must never silently hide a genuine surface event.
    for tp in events:
        if polyhedra_overlap(_translated_exact(A, _ray_shift(x0, d, tp)), B, 0.0) >= 0:
            raise RuntimeError(f"first_entrance3: no in-extent facet-cover candidate, yet the bodies touch at t = {tp!r}; "
                               "the candidate set missed an earlier entrance")
    return Entrance3("none", 0.0, None, None, None, None, None, 0.0, (), (), len(raw))


def shortest_exit3(A: Polyhedron, B: Polyhedron, x0: Vec3, *, tol: float = 1e-9,
                   geom_tol: float | None = None) -> Entrance3:
    """Local-facet minimum exact squared depth; exact ties, stable enumeration.

    Tight-fit seams may have local depth zero inside E. This is a contact
    normal/initial-state policy, not global distance to the nonconvex boundary.
    """
    A, B = exact_surface(A), exact_surface(B)
    At = _translated_exact(A, x0)
    candidates = []
    for c in _facet_covers(At, B, tol):
        n, p = _facet_plane_on_views(At, B, c.label(), tol)
        gap = -dot(n, p)
        if c.in_extent and gap <= 0:
            candidates.append((gap * gap / dot(n, n), c))
    if not candidates:
        raise RuntimeError("shortest_exit3: penetrating configuration with no in-extent facet cover "
                           "(concave pair outside the local rule's reach?)")
    distance2, best = min(candidates, key=lambda item: item[0])
    tied = [c for depth2, c in candidates if depth2 == distance2]
    tied.sort(key=lambda q: 0 if q.label() == best.label() else 1)
    rep_label, members = _representative(merge_degenerate(At, B, tied, tol), best.label())
    return _restore_sources(Entrance3("exit", 0.0, x0, rep_label, best.normal, best.point_a, best.point_b, best.gap,
                     tuple(q.label() for q in tied), members, len(candidates), Fraction(0)), A, B)


def first_entrance_brute(A: Polyhedron, B: Polyhedron, x0: Vec3, d: Vec3, *, t_max: float, steps: int = 400,
                         geom_tol: float | None = None) -> float | None:
    """共用生产重叠谓词的抽样佐证（不是独立主 oracle）。把 [0, t_max] 均分扫描，找到第一个 `polyhedra_overlap` ≥ 0 的步，再在前一步与它之间二分到
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
