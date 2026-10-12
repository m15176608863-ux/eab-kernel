"""Three exact G0 votes for explicit convex models (WO-E5a).

The oracle in g03_exact imports no tested geometric primitive. Vote 1 uses
independent rational SAT, including every exact E vertex/edge midpoint/facet
centroid. Vote 2 compares complete support sets. Vote 3 compares exact extreme
points with local cone intersections. No band, ambiguous or low-height exemption
changes an answer. The compatibility counters for exemptions are always zero.
Support-domain policy: docs/exact_predicates_plan.md (R13FIXb). Exact rational
outputs remain unrestricted; final float displays reject unrepresentable values.
"""
from __future__ import annotations
from eab.construction import scalar_rational

import random
import math
from dataclasses import dataclass, field
from fractions import Fraction
from functools import lru_cache
from .covers3 import local_facets3, membership_convex3
from .geom3 import Polyhedron, Vec3, noise_floor, norm, sub, exact_convex_view
from . import g03_exact as oracle
from . import g03_surface_oracle as surface_oracle


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
    av,bv=tuple(oracle.qpoint(_mapped_value) for _mapped_value in av),tuple(oracle.qpoint(_mapped_value) for _mapped_value in bv)
    hp=tuple(oracle.qpoint(_mapped_value) for _mapped_value in hp);ds=tuple(oracle.qpoint(_mapped_value) for _mapped_value in ds)
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
    lo=tuple(Fraction(lo_b[i])-Fraction(hi_a[i]) for i in range(3))
    hi=tuple(Fraction(hi_b[i])-Fraction(lo_a[i]) for i in range(3))
    padding=tuple(Fraction(margin)*(hi[i]-lo[i]) for i in range(3))
    bounds=tuple((lo[i]-padding[i], hi[i]+padding[i]) for i in range(3))
    return [tuple(scalar_rational(a+Fraction(rng.random())*(b-a))
                  for a,b in bounds) for _ in range(n)]


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

    completeness_failures: list = field(default_factory=list)  # exact (x, candidate squared, true squared)
    construction_failures: list = field(default_factory=list)  # displayed witness failures

    @property
    def passed(self) -> bool:
        return not self.failures


def _display_witness_distance(point_a, point_b):
    """Report invalid displays as failures, never feed them to a finite constructor.

    This only audits constructed coordinates; exact feature completeness is
    evaluated independently. Gate: test_g03_invalid_display_is_reported_without_calling_finite_constructor.
    """
    if point_a is None or point_b is None or not all(
            math.isfinite(x) for x in (*point_a, *point_b)):
        return math.inf
    try:
        return norm(tuple(Fraction(a)-Fraction(b) for a,b in zip(point_a, point_b)))
    except ArithmeticError:
        # A finite but unrepresentable display distance is likewise a failed
        # construction, not a reason for an audit to abort without a report.
        return math.inf


def g0_distance_completeness3(A: Polyhedron, B: Polyhedron, *, radius: float, samples: int = 200,
                              seed: int = 0, base: Vec3 = (0.0, 0.0, 0.0), tol: float = 1e-9,
                              atol: float = 1e-9) -> DistanceReport3:
    """Exact nonconvex separation and independent rational distance oracle.

    Oracle primitives: integer planes/ring winding and generic-ray parity,
    rational vertex/face and edge/edge squared distances; zero production
    geometry is shared. No implicit band excludes a strict positive gap.
    Exact nearest-feature completeness has no tolerance or coordinate floor.
    Float witness construction separately retains the relative/rounding allowance.
    """
    from .covers3 import enumerate_covers3
    from ..margin import _surface_view, _witness_squared
    if not math.isfinite(atol) or atol < 0:
        raise ValueError("atol must be finite and nonnegative")
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
        x = tuple(Fraction(base[i]) + Fraction(radius) * Fraction(v[i]) for i in range(3))
        At = Polyhedron([tuple(Fraction(v[i]) + Fraction(x[i]) for i in range(3))
                         for v in A.verts], list(A.faces))
        truth2 = surface_oracle.separated_distance(At.verts, At.faces, B.verts, B.faces, squared=True)
        if truth2 is None:
            rep.skipped_intersecting += 1
            continue
        truth = surface_oracle.sqrt_display(truth2)
        va,_ = _surface_view(tuple(At.verts),tuple(At.faces))
        vb,_ = _surface_view(tuple(B.verts),tuple(B.faces))
        covs = [c for c in enumerate_covers3(va, vb, window=float("inf"), tol=tol) if c.in_extent]
        exact_candidates = [_witness_squared(tuple(va.verts),tuple(va.faces),tuple(vb.verts),tuple(vb.faces),c.label())
                            for c in covs]
        minimum2 = min(exact_candidates,default=None)
        incomplete = minimum2 != truth2
        if incomplete:
            rep.completeness_failures.append((x,minimum2,truth2))
        cand = [_display_witness_distance(c.point_a, c.point_b) for c in covs]
        got = min(cand) if cand and all(math.isfinite(v) for v in cand) else float("inf")
        rep.samples += 1
        err = abs(got - truth)
        rep.worst_abs_error = max(rep.worst_abs_error, err)
        # A missing/nonfinite construction is a failure independently of the
        # tolerance; inf > inf and NaN > bound must never make this gate green.
        # Keep the acceptance expression rational as well: large finite atol
        # need not become an infinite floating threshold (R7 same-family scan).
        failed = not cand or not all(math.isfinite(v) for v in (*cand, truth, err))
        if not failed:
            rounding = noise_floor(max(At.metrics()[0], B.metrics()[0]))
            failed = Fraction(err) > Fraction(atol)*max(Fraction(L), Fraction(truth)) + Fraction(rounding)
        if failed:
            rep.construction_failures.append((x, got, truth))
        if failed or incomplete:
            rep.failures.append((x, got, truth))
    return rep
