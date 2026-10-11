"""Three exact G0 votes for explicit convex models (WO-E5a).

The oracle in g03_exact imports no tested geometric primitive. Vote 1 uses
independent rational SAT, including every exact E vertex/edge midpoint/facet
centroid. Vote 2 compares complete support sets. Vote 3 compares exact extreme
points with local cone intersections. No band, ambiguous or low-height exemption
changes an answer. The compatibility counters for exemptions are always zero.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from fractions import Fraction
from functools import lru_cache
from .covers3 import local_facets3, membership_convex3
from .geom3 import (Polyhedron, Vec3, brute_feature_distance, noise_floor, norm,
                    polyhedra_overlap, sub, exact_convex_view)
from . import g03_exact as oracle


@dataclass(slots=True)
class G0Report3:
    samples: int = 0
    band_skipped: int = 0
    mismatches: list = field(default_factory=list)
    facet_local: int = 0
    facet_global: int = 0
    facet_degenerate: int = 0
    facet_ambiguous: int = 0
    facet_local_dropped: int = 0
    facet_symmetric_diff: list = field(default_factory=list)
    hull_vertex_mismatch: int = 0
    hull_vertices: int = 0
    e_vertices: int = 0
    e_vertices_ambiguous: int = 0
    boundary_probes: int = 0
    boundary_checked: int = 0
    boundary_kinds: tuple = (0, 0, 0)

    @property
    def passed(self):
        return (not self.mismatches and not self.facet_symmetric_diff
                and self.hull_vertex_mismatch == 0 and self.band_skipped == 0
                and self.boundary_checked == self.boundary_probes)


def _label_sets(A, B, lab):
    _,af,bf=lab
    sa=frozenset(A.faces[af[1]]) if af[0]=='face' else frozenset(af[1:])
    sb=frozenset(B.faces[bf[1]]) if bf[0]=='face' else frozenset(bf[1:])
    return sa,sb


def _hull_facets(A,B,diffs,hull,fl=0,area_tol=0,eps=0):
    """Exact supports; retained arguments cannot affect the theorem."""
    return _hull_facets_cached(tuple(A.verts),tuple(B.verts),tuple(hull.verts),tuple(hull.faces),tuple(diffs))


@lru_cache(maxsize=256)
def _hull_facets_cached(av,bv,hp,faces,ds):
    av,bv=tuple(map(oracle.qpoint,av)),tuple(map(oracle.qpoint,bv))
    hp=tuple(map(oracle.qpoint,hp));ds=tuple(map(oracle.qpoint,ds))
    out=[];seen=set()
    for f in faces:
        o=hp[f[0]]
        n=next((oracle.wedge(oracle.minus(hp[f[i]],o),oracle.minus(hp[f[i+1]],o))
                for i in range(1,len(f)-1)
                if any(oracle.wedge(oracle.minus(hp[f[i]],o),oracle.minus(hp[f[i+1]],o)))),None)
        if n is None:
            out.append(((0,0,0),-1,-1,False,frozenset(),frozenset(),None));continue
        h=oracle.scalar(n,o)
        values=[oracle.scalar(n,d) for d in ds]
        if min(values)>=h:n=tuple(-c for c in n);h=-h;values=[-v for v in values]
        ok=max(values)<=h and all(oracle.scalar(n,hp[i])==h for i in f)
        aa=[oracle.scalar(n,p) for p in av];bb=[oracle.scalar(n,p) for p in bv]
        amin,bmax=min(aa),max(bb)
        ia=frozenset(i for i,v in enumerate(aa) if v==amin)
        ib=frozenset(i for i,v in enumerate(bb) if v==bmax)
        key=oracle.plane_key(n,h)
        if key in seen:continue
        seen.add(key)
        ok=ok and bmax-amin==h
        out.append((key[0],oracle.dimension([av[i] for i in ia]),
                    oracle.dimension([bv[i] for i in ib]),ok,ia,ib,None))
    return tuple(out)


def facet_vote3(A,B,facets,hull,diffs,eps=None):
    """Full bidirectional combinatorial comparison; eps is ignored compatibility."""
    A,B=exact_convex_view(A),exact_convex_view(B)
    dims={'VF':(0,2),'FV':(2,0),'EE':(1,1)}
    strict=[];diff=[];degenerate=0
    for n,da,db,ok,ia,ib,_ in _hull_facets(A,B,diffs,hull):
        if not ok or (da,db) not in ((0,2),(2,0),(1,1),(1,2),(2,1),(2,2)):
            diff.append(('hull_anomaly',n,da,db))
        elif (da,db) in dims.values():strict.append((n,da,db,ia,ib))
        else:degenerate+=1
    matched=set()
    for lab in sorted(facets):
        sa,sb=_label_sets(A,B,lab)
        j=next((j for j,(_,da,db,ia,ib) in enumerate(strict)
                if (da,db)==dims.get(lab[0]) and sa==ia and sb==ib),None)
        if j is None:diff.append(('local_only',lab))
        elif j in matched:diff.append(('duplicate',lab))
        else:matched.add(j)
    for j,(n,da,db,_,_) in enumerate(strict):
        if j not in matched:diff.append(('hull_only',n,da,db))
    return len(strict),degenerate,0,0,sorted(diff)


def sample_translations3(A,B,n,rng,margin=0.25):
    lo_a,hi_a=A.aabb();lo_b,hi_b=B.aabb()
    lo=tuple(float(lo_b[i]-hi_a[i]) for i in range(3))
    hi=tuple(float(hi_b[i]-lo_a[i]) for i in range(3))
    return [tuple(rng.uniform(lo[i]-margin*(hi[i]-lo[i]),hi[i]+margin*(hi[i]-lo[i]))
                  for i in range(3)) for _ in range(n)]


def g0_convex3(A,B,*,samples=400,seed=0,tol=1e-12,band=1e-7):
    """Exact theorem check. tol/band are retained but never alter a vote."""
    from .covers3 import cones_intersect_relint
    # Freeze source coordinates BEFORE tested hull canonicalization. A defective
    # convex view must not erase its own counterexample from the oracle input.
    source_av,source_bv=tuple(A.verts),tuple(B.verts)
    A,B=exact_convex_view(A),exact_convex_view(B)
    av,bv=tuple(A.verts),tuple(B.verts)
    rep=G0Report3()
    facets=local_facets3(A,B,0)
    rep.facet_local=len(facets)
    points,faces,_=oracle.difference_hull(source_av,source_bv)
    hull=Polyhedron(list(points),list(faces))
    hv={points[i] for f in faces for i in f}
    ev={oracle.minus(oracle.qpoint(b),oracle.qpoint(a))
        for ia,a in enumerate(av) for ib,b in enumerate(bv)
        if cones_intersect_relint(A,ia,B,ib,0)}
    rep.hull_vertices,rep.e_vertices=len(hv),len(ev)
    rep.hull_vertex_mismatch=len(hv^ev)
    (rep.facet_global,rep.facet_degenerate,rep.facet_ambiguous,
     rep.facet_local_dropped,rep.facet_symmetric_diff)=facet_vote3(A,B,facets,hull,list(points))
    bnd,rep.boundary_kinds=oracle.boundary_probes(source_av,source_bv)
    rep.boundary_probes=len(bnd)
    random_probes=sample_translations3(A,B,samples,random.Random(seed))
    for i,x in enumerate(random_probes+bnd):
        cov=membership_convex3(A,B,x,0,facets)
        brute=oracle.overlap(source_av,source_bv,x)
        rep.samples+=1
        if i>=len(random_probes):rep.boundary_checked+=1
        if brute!=cov:rep.mismatches.append((x,brute,cov))
    return rep


@dataclass(slots=True)
class DistanceReport3:
    """凹块 G0：'法锥有效性筛选不丢最近特征对' 的完备性检验结果。"""
    samples: int = 0
    skipped_intersecting: int = 0
    worst_abs_error: float = 0.0
    failures: list[tuple[Vec3, float, float]] = field(default_factory=list)   # (x, 盖距离, 真距离)

    @property
    def passed(self) -> bool:
        return not self.failures


def g0_distance_completeness3(A: Polyhedron, B: Polyhedron, *, radius: float, samples: int = 200,
                              seed: int = 0, base: Vec3 = (0.0, 0.0, 0.0), tol: float = 1e-9,
                              atol: float = 1e-9) -> DistanceReport3:
    """凹块（也适用于凸块）的 G0 正确形式：**距离完备性**。

    命题：A、B 分离时，d(A,B) = min over 法锥有效且落在特征范围内的盖 of |特征间距|。
    即法锥筛选不会把实现最短距离的那一对特征滤掉。oracle 是 `brute_feature_distance`
    （枚举全部特征对、零法锥筛选、只用坐标）。

    纪律 A（共用与风险）：oracle 的点-面距离与盖的 in_extent 共用 geom3.point_in_face_polygon——
    它若错，两边一起错，本门看不见（2026-09-21 审查 C7 正是这样：两边都用半平面核，凹面上
    同错）。所以 point_in_face_polygon 另有不经 geom3 的独立门（tests/test_geom3_face_polygon.py：
    矩形并集、星形极坐标、闭式距离），本门只对"法锥筛选丢特征对"有牙。
    另：本门的采样区只在给定 base 附近，凹面臂上的最近对需要**定点探针**才会被采到
    （tests/test_geom3_face_polygon.py 的骨形块侧面探针）。

    **不要**用"最小盖间隙的符号"当成员谓词（2026-09-18 实测被推翻）：VF 盖的 gap 是顶点到
    面**所在平面**的有符号距离，分离的两块之间也常有顶点落在对方某个面平面的内侧，故 min 会
    报出 −2.7 这类假侵入。凸块的成员谓词是 facet 间隙取 **max**（见 membership_convex3）；
    凹块的 E 非凸，max 与 min 都不成立，成员判定需要入口块的**全局**构造（Phase 3 的目标）。

    容差（纪律 F，M0.3）：tol 是盖枚举的**角度**容差（无量纲）；atol 是**相对** L 的距离判据：
    |盖距离 − 真值| > atol·max(L, 真值) + c·eps·C 即失败（L = 两体 AABB 对角线之大者，C = 坐标量级）；贯入预筛带
    1e-12·L。旧版是绝对的 atol·max(1, 真值) 与 1e-12：同一个无量纲误差在 s = 1 报红、s = 1e-3 放行（G6 第二轮 minor）。
    """
    from .covers3 import enumerate_covers3
    rng = random.Random(seed)
    rep = DistanceReport3()
    L = max(A.metrics()[1], B.metrics()[1])
    drawn = 0
    while drawn < samples:
        v = (rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0))
        nv = norm(v)
        if nv > 1.0 or nv == 0.0:
            continue
        drawn += 1
        x = tuple(base[i] + radius * v[i] for i in range(3))
        At = A.translated(x)
        if polyhedra_overlap(At, B, 1e-12 * L) != -1:
            rep.skipped_intersecting += 1
            continue
        truth = brute_feature_distance(At, B)
        covs = [c for c in enumerate_covers3(At, B, window=float("inf"), tol=tol) if c.in_extent]
        cand = [norm(sub(c.point_a, c.point_b)) for c in covs
                if c.point_a is not None and c.point_b is not None]
        got = min(cand) if cand else float("inf")
        rep.samples += 1
        err = abs(got - truth)
        rep.worst_abs_error = max(rep.worst_abs_error, err)
        if err > atol * max(L, truth) + noise_floor(max(At.metrics()[0], B.metrics()[0])):
            rep.failures.append((x, got, truth))
    return rep
