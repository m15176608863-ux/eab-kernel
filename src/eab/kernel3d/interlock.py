"""Exact affine escape with explicit local contact-window certificates.

Default decisions use the exact rational values supplied by callers. Complete
triangulated VF/FV/EE events retain near-vertical features; exact_height and
exact_offset carry the first nonpenetrating root, with an explicit certificate
for every preceding open event interval. height is only a floating display:
reapplying it with per-vertex floating arithmetic is a different geometry and
requires a separate check. DDA/TIA adapters must consume the exact displacement
or explicitly choose and verify a local contact_window.

Reporting covers/ties retain their nominal extent/normal bands for derivative
compatibility. They never accept an intruding root in the default exact mode.
The explicit finite-certificate window proves local shell thickness or a
rigid displacement <= window; it is not the shortest
rigid-body translation. Gates: tests/test_interlock_exact.py,
tests/test_interlock_walls.py, tests/test_e5a2_interlock_bridge.py.
"""

from __future__ import annotations

import sys
import math
from fractions import Fraction as F
from functools import lru_cache
from dataclasses import dataclass, field

from ..dual import Dual, Number, val
from ..margin import characteristic_length, effective_geom_tol, rounding_floor
from .covers3 import ee_cover, enumerate_covers3, fv_cover, vf_cover
from . import covers3 as _covers
from .frozen import FACET_KINDS, frozen_ee_sign, frozen_gap, frozen_normal  # noqa: F401  (L5 转出的公共入口)
from .geom3 import Polyhedron, Vec3, cross, dot, norm, polyhedra_overlap, sub
from .geom3 import exact_edge_vector
from .exact_geom import sqrt_rational
from . import exact_geom as _exact
from .exact_sweep import surface_events, translate_exact, star_core, contact_models

_EPS = sys.float_info.epsilon
REL_BRUTE_GEOM_TOL = 1e-12         # oracle 的谓词容差：特征长度 L 的相对量
REL_BRUTE_TOL = 1e-10              # oracle 的二分终止宽度：L 的相对量


# ------------------------------------------------------------------ 暴力 oracle

def escape_height_brute(A: Polyhedron, B: Polyhedron, offset: Vec3, *,
                        hi: float, tol: float | None = None, geom_tol: float | None = None,
                        contact_window: float | None = None) -> float:
    """Certified earliest-root reference retaining the legacy bracket API.

    A monotone bisection can skip a lower separated interval in nonconvex data.
    Therefore it now uses the complete exact event partition; tol/geom_tol are
    accepted for compatibility but cannot change the root. This is a secondary
    check, not an independent oracle (it shares the exact surface predicate).
    """
    result=escape_height_covers(A,B,offset,geom_tol=geom_tol,contact_window=contact_window)
    if result.exact_height>F(hi):
        raise ValueError(f"still intruding at z={hi}; raise hi")
    return result.height


# ------------------------------------------------------------------ 盖路径（可微）

@dataclass(slots=True)
class EscapeSolution:
    height: float
    cover_label: tuple | None
    n_candidates: int
    # Legacy reporting ties are selected around nominal constructed roots.
    # They are not a claim that exact membership cannot distinguish the roots.
    tied_labels: tuple = ()
    exact_height: F = F(0)
    exact_offset: tuple = ()
    interval_certificate: tuple = ()
    nonpenetrating_state: int = 0
    window_core: str | None = None
    exact_contact_label: tuple | None = None
    exact_contact_normal: tuple = ()


def _normal_noise(A: Polyhedron, B: Polyhedron, cover) -> float:
    """盖法向自身的方向噪声（弧度）：VF 取 B 那张面的、FV 取 A 那张面的面法向噪声；EE 取候选 unit(t_B × t_A) 的
    (n_A + n_B)/sinθ（与 covers3.ee_cover / facet_normal3 同一口径）。"""
    kind, af, bf = cover.label()
    if kind == "VF":
        return B.face_noise(bf[1])
    if kind == "FV":
        return A.face_noise(af[1])
    if kind == "EE":
        ea, eb = (af[1], af[2]), (bf[1], bf[2])
        sine = norm(cross(B.edge_dir(eb), A.edge_dir(ea)))
        if sine == 0.0:
            # E5a exact cones can retain a nonparallel pair whose rounded unit
            # vectors coincide. Preserve this legacy *resolution report* using
            # raw exact edges, rather than divide by the rounded zero. The
            # exact escape topology is handled separately by surface_events.
            a, b = exact_edge_vector(A, ea), exact_edge_vector(B, eb)
            n = cross(a, b)
            sine = sqrt_rational(dot(n, n) / (dot(a, a) * dot(b, b)))
            if sine == 0.0:
                return float("inf")  # below the representable angular range
        return (A.edge_noise(ea) + B.edge_noise(eb)) / sine
    return 0.0


def _cover_escape_z(cover, noise: float = 0.0) -> tuple[float, float] | None:
    """Nominal reporting root; near-vertical suppression affects labels only.

    The exact solver enumerates all supplied-surface events independently;
    this compatibility helper does not decide escape or penetration."""
    n = cover.normal
    if n is None:
        return None
    nz = n[2]
    if nz <= max(1e-12, noise):
        return None
    return -cover.gap / nz, nz


def _cover_at(Az: Polyhedron, B: Polyhedron, label: tuple, tol: float, extent_tol: float):
    """同一对特征（面盖）在 A 抬升后的位形 Az 上重新求盖。有效性只看法向与法锥，与平移无关。"""
    kind, af, bf = label
    if kind == "VF":
        return vf_cover(Az, af[1], B, bf[1], tol, extent_tol)
    if kind == "FV":
        return fv_cover(Az, af[1], B, bf[1], tol, extent_tol)
    if kind == "EE":
        return ee_cover(Az, (af[1], af[2]), B, (bf[1], bf[2]), tol, extent_tol)
    return None


@dataclass(frozen=True, slots=True)
class _CandidateSnapshot:
    signature: tuple
    arguments: tuple = field(compare=False, hash=False)


def _candidates(A: Polyhedron, B: Polyhedron, offset: Vec3, tol: float, extent_tol: float):
    """Reuse nominal reports only for identical complete, typed input content.

    Fresh list results protect the cache from callers. Source vertices, face
    rings, offset and both reporting bands are part of the key. Numeric types
    are retained in the reporting key; affine translation itself is exact.
    Direct cover implementations participate so injected defects remain visible.
    Exact escape decisions are independent of this nominal-report cache.
    """
    av, af = tuple(map(tuple, A.verts)), tuple(map(tuple, A.faces))
    bv, bf = tuple(map(tuple, B.verts)), tuple(map(tuple, B.faces))
    offset = tuple(offset)
    numeric_types = tuple(type(x) for vertices in (av, bv, (offset,))
                          for p in vertices for x in p) + (type(tol), type(extent_tol))
    implementations = (_candidates_uncached, enumerate_covers3, _cover_at,
                       _normal_noise, _cover_escape_z, rounding_floor,
                       _covers.vf_cover, _covers.fv_cover, _covers.ee_cover,
                       vf_cover, fv_cover, ee_cover)
    arguments = (av, af, bv, bf, offset, tol, extent_tol)
    signature = arguments + (numeric_types, implementations)
    rows, r = _candidates_cached(_CandidateSnapshot(signature, arguments))
    return list(rows), r


@lru_cache(maxsize=512)
def _candidates_cached(snapshot):
    av, af, bv, bf, offset, tol, extent_tol = snapshot.arguments
    implementation = snapshot.signature[-1][0]
    rows, r = implementation(Polyhedron(list(av), list(af)),
                             Polyhedron(list(bv), list(bf)), offset, tol, extent_tol)
    return tuple(rows), r


def _candidates_uncached(A: Polyhedron, B: Polyhedron, offset: Vec3, tol: float, extent_tol: float
                ) -> tuple[list[tuple], float]:
    """Legacy nominal report candidates and their floating construction band.

    These feed derivative labels/ties, not the complete exact event partition.
    Affine coordinates are formed exactly before nominal reporting, so a large
    offset cannot collapse a valid small body before the authoritative solve.
    Gate: test_g6f09_nominal_report_cannot_collapse_float_body_under_large_offset.
    Extent is checked at each candidate construction as in the public report."""
    At = translate_exact(A, offset)
    r = rounding_floor(At, B)
    raw: list[tuple] = []
    for idx, c in enumerate(enumerate_covers3(At, B, window=float("inf"), tol=tol, require_in_extent=False,
                                              include_low_dim=False)):
        zn = _cover_escape_z(c, _normal_noise(At, B, c))
        if zn is None:
            continue
        z, nz = zn
        if z * nz >= -r:                  # 法向间隙在舍入以内的负高度 = 已接触，记 0
            raw.append((max(z, 0.0), c.label(), nz, idx))
    raw.sort(key=lambda t: t[0])
    out: list[tuple] = []
    z_prev, Az = None, None
    for z, lab, nz, idx in raw:
        if z <= 0.0:
            out.append((z, lab, nz, idx))     # 已接触/已分离：由调用方的谓词裁决，无需抬升
            continue
        if z_prev is None or z - z_prev > r:
            z_prev, Az = z, translate_exact(At, (0.0, 0.0, z))
        c = _cover_at(Az, B, lab, tol, extent_tol)
        if c is not None and c.in_extent:
            out.append((z, lab, nz, idx))
    return out, r


def escape_candidates(A: Polyhedron, B: Polyhedron, offset: Vec3, *, tol: float = 1e-9,
                      geom_tol: float | None = None) -> list[tuple[float, tuple]]:
    """Nominal cover-report candidates, sorted by constructed height.

    Preserves the documented extent/normal report band for frozen derivatives.
    It is not the complete exact kinetic event list: use exact_sweep.surface_events
    for that list. escape_height_covers uses the latter for all decisions."""
    gtol = effective_geom_tol(translate_exact(A, offset), B, geom_tol)
    return [(z, lab) for z, lab, _, _ in _candidates(A, B, offset, tol, gtol)[0]]


def _nonpenetrating_at(A, B, offset, height):
    """An exact certificate on the exact affine input, not a rounded probe."""
    displacement=(F(offset[0]),F(offset[1]),F(offset[2])+height)
    return polyhedra_overlap(translate_exact(A,displacement),B,0)


def _prior_intervals(times, height):
    """Every candidate interval below height, without resolution clustering."""
    left=F(0)
    for right in sorted({t for t in times if 0<t<=height}):
        yield left,right,(left+right)/2
        left=right


def _exact_escape(A, B, offset, cap=None):
    return _exact_escape_cached(tuple(A.verts),tuple(A.faces),tuple(B.verts),tuple(B.faces),
                                tuple(map(F,offset)),cap,_nonpenetrating_at,_prior_intervals,surface_events)


@lru_cache(maxsize=512)
def _exact_escape_cached(av,af,bv,bf,offset,cap,predicate,intervals,event_source):
    A,B=Polyhedron(av,af),Polyhedron(bv,bf)
    initial=predicate(A,B,offset,F(0))
    if initial != 1:
        return F(0),None,(),initial,()
    events=event_source(A,B,start=offset,t_max=cap)
    groups={}
    for event in events:
        if event.time>0:
            groups.setdefault(event.time,[]).append(event)
    for height, group in sorted(groups.items()):
        state=predicate(A,B,offset,height)
        if state == 1:
            continue
        proof=[]
        for left,right,mid in intervals(groups,height):
            inside=predicate(A,B,offset,mid)
            if inside != 1:
                raise AssertionError('event completeness: an earlier interval is nonpenetrating')
            proof.append((left,right,mid,inside))
        witness=next((e for e in group if e.normal[2]),group[0])
        return height,witness,tuple(proof),state,events
    if cap is not None:
        return None,None,(),1,events
    raise ValueError('exact surface event set did not contain a separating height')


def escape_height_covers(A: Polyhedron, B: Polyhedron, offset: Vec3, *,
                         tol: float = 1e-9, geom_tol: float | None = None,
                         contact_window: float | None = None) -> EscapeSolution:
    """Exact first nonpenetrating affine lift, plus floating display and labels.

    exact_height/exact_offset are the decision data. height is a binary64 display
    rounded upward; it is not a substituted topology predicate. Every preceding
    open event interval is certified penetrating, and the exact root itself is
    independently tested nonpenetrating. No near-vertical event is suppressed.

    Explicit contact_window is the local penetration-thickness reporting
    window, not Euclidean rigid-body penetration depth (PD). A rejected window
    is not evidence that PD > window; coordinate-axis and L1 shell construction
    do not guarantee rotation invariance. It uses the same rational certificate
    models as margin: original geometry, two available star cores, and six
    coordinate-axis shifts by +/-window. The earliest root is the minimum over
    those complete event partitions; the winner carries its exact proof. This
    sufficient bound is not a global minimum rigid-body penetration distance.
    interval_certificate is the winning model's interval proof. Other window
    models are excluded by exact initial/root checks on their complete event
    partitions up to the current best (cap); they can be rerun via contact_models.
    exact_contact_label/normal index that winning model, not necessarily A/B
    when a core or displacement certificate won. cover_label/tied_labels remain
    original-geometry nominal derivative reports. geom_tol changes only these
    reports, never the exact root.
    """
    if contact_window is not None and F(contact_window)<0:
        raise ValueError('contact_window must be nonnegative')
    report_A=translate_exact(A,offset)
    gtol=effective_geom_tol(report_A,B,geom_tol)
    cands,r=_candidates(A,B,offset,tol,gtol)
    choices=(('exact',A,B),) if contact_window is None else contact_models(A,B,contact_window)
    solved=[]
    best=None
    for name,ca,cb in choices:
        root,event,proof,state,events=_exact_escape(ca,cb,offset,cap=best)
        if root is None:
            continue
        marker={'exact':None,'core_A':'A','core_B':'B'}.get(name,name)
        solved.append((root,event,proof,state,events,marker))
        best=root if best is None else min(best,root)
        if root==0:
            break
    root,event,proof,state,events,name=min(solved,key=lambda row:row[0])
    display=float(root)
    if F(display)<root:
        display=math.nextafter(display,math.inf)
    lab=None; tied=()
    if root>0:
        usable=[c for c in cands if c[0]>0]
        if usable:
            nearest=min(usable,key=lambda c:abs(F(c[0])-root)*F(c[2]))
            if abs(F(nearest[0])-root)*F(nearest[2]) <= F(gtol)+F(r)*4:
                report=_escape_solution(nearest[0],nearest[2],cands,gtol,r)
                lab,tied=report.cover_label,report.tied_labels
        if lab is None and event is not None:
            lab=event.label
            tied=tuple(dict.fromkeys(e.label for e in events if e.time==root))
    return EscapeSolution(display,lab,len(cands),tied,root,
                          (F(offset[0]),F(offset[1]),F(offset[2])+root),proof,state,name,
                          event.label if event is not None else None,
                          tuple(-n for n in event.normal) if event is not None and event.normal[2]<0
                          else (event.normal if event is not None else ()))


def _escape_solution(z: float, nz: float, cands: list[tuple], gtol: float, r: float) -> EscapeSolution:
    """Select nominal-cluster winner and legacy geometric reporting ties.

    These gtol/r bands only label the candidate construction. The caller must
    separately verify and return its actual nonpenetrating constructed height.
    """
    pos = [t for t in cands if t[0] > 0.0]
    exact = [t for t in pos if abs(t[0] - z) * t[2] <= r * (1.0 + t[2] / nz)]
    _, win, _, iw = min(exact, key=lambda t: t[3])
    band = sorted((t for t in pos if abs(t[0] - z) * t[2] <= gtol + r * (1.0 + t[2] / nz)), key=lambda t: t[3])
    tied = (win,) + tuple(t[1] for t in band if t[3] != iw)
    return EscapeSolution(z, win, len(cands), tied)


def escape_height_from_frozen_cover(A: Polyhedron, B: Polyhedron, label: tuple,
                                    offset, *, ee_sign: float = 1.0) -> Number:
    """冻结盖下的逃逸高度闭式：z = −gap(offset) / (n·ẑ)，支持对偶数（∂z/∂θ）。

    这是"片 + 划"里的**片**：组合结构（哪个盖当家、EE 法向朝哪）已由 float 路径冻结，
    片内是纯解析表达式，对几何参数逐点可微——与 DDA 冻结活动集后解析可微同构。

    只接**面盖**（VF / FV / EE）：它们的 gap 沿平移仿射，z = −gap/(n·ẑ) 才是零间隙高度。
    低维盖（VE3 / EV3 / VV3）的 gap 是无符号距离，沿竖线非仿射，上式不是逃逸高度——拒收
    （`escape_height_covers` 也从不让它们胜出：gap ≥ 0 ⇒ z ≤ 0）。
    """
    if not label or label[0] not in FACET_KINDS:
        raise ValueError(f"escape height is defined by facet covers (VF/FV/EE) only, got {label[:1]}")
    if not any(isinstance(c,Dual) for P in (A,B) for p in P.verts for c in p) and not any(isinstance(c,Dual) for c in offset):
        kind,af,bf=label
        if kind=='VF':
            face=bf[3:] if len(bf)>2 else B.faces[bf[1]]
            n=_exact.normal([_exact.vector(B.verts[i]) for i in face])
            a,b=_exact.vector(A.verts[af[1]]),_exact.vector(B.verts[face[0]])
        elif kind=='FV':
            face=af[3:] if len(af)>2 else A.faces[af[1]]
            n=_exact.normal([_exact.vector(A.verts[i]) for i in face])
            a,b=_exact.vector(A.verts[face[0]]),_exact.vector(B.verts[bf[1]])
        else:
            n=_exact.cross(exact_edge_vector(B,(bf[1],bf[2])),exact_edge_vector(A,(af[1],af[2])))
            a,b=_exact.vector(A.verts[af[1]]),_exact.vector(B.verts[bf[1]])
        # Orientation and normalization cancel in this ratio. Keeping the raw
        # rational plane avoids magnifying rounded unit-normal error by 1/n_z.
        return -_exact.dot(n,_exact.sub(_exact.add(a,_exact.vector(offset)),b))/n[2]
    n = frozen_normal(A, B, label, ee_sign)
    g = frozen_gap(A, B, label, offset, n)
    return -g / n[2]


def dilatancy_profile(A: Polyhedron, B: Polyhedron, *, direction: Vec3 = (1.0, 0.0, 0.0),
                      deltas: list[float] | None = None, tol: float = 1e-9) -> list[dict]:
    """逃逸高度剖面 h(δ) 与剪胀比 tanψ = dh/dδ（中心差分于 δ）。

    tanψ 在无摩擦极限下即横向承载与法向压力之比（Rowe 剪胀关系）。
    `deltas` 是模型单位下的横移量（默认 0.02·i 只适合 lx≈2 的示例块；换尺度请传缩放后的 δ），
    `direction` 应为单位向量。h ×s、tanψ 不变（门：tests/test_invariance_interlock.py）。
    """
    if deltas is None:
        deltas = [i * 0.02 for i in range(1, 16)]
    out = []
    for d in deltas:
        off = (d * direction[0], d * direction[1], d * direction[2])
        sol = escape_height_covers(A, B, off, tol=tol)
        out.append({"delta": d, "h": sol.height, "cover": sol.cover_label,
                    "n_covers": sol.n_candidates})
    for i, row in enumerate(out):
        if 0 < i < len(out) - 1:
            row["tan_psi"] = (out[i + 1]["h"] - out[i - 1]["h"]) / (out[i + 1]["delta"] - out[i - 1]["delta"])
        else:
            row["tan_psi"] = None
    return out
