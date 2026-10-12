"""Three-dimensional contact covers with exact coordinate predicates.

For convex APIs the body is its exact vertex-set convex hull; labels index the
canonical views returned by geom3.exact_convex_view. General single-cover and
enumeration APIs retain the supplied surface topology. On exactly planar faces
all local cone, strictness and extent branches are rational. For a nonplanar
source face-ring the single-cover APIs are ONLY source-ring descriptors: the
Newell direction plus the plane anchored at its first vertex, projected winding
extent, and source-topology incident edges. They are NOT the normal cone or
contact witness of the triangulated folded solid. In particular, a cyclic ring
rotation may change that descriptor plane. No source feature label is silently
replaced by a canonical convex-view label. Gates: test_e5a2_covers.py tests
source_ring_descriptor_is_not_a_folded_surface_cover and
source_ring_descriptor_keeps_source_labels_separate_from_convex_views.

Original floating coordinates denote exact rational data. Derived unnormalised
normals, incident vectors, projections and parameters stay rational until the
construction output. A strict or zero-dimensional decision never uses a noise
floor. Positive caller tol / extent_tol may only expand closed domain windows;
strictness always reads the exact zero threshold. window is a caller distance
search window. Construction outputs (unit normals, points and gaps) are floats.

Public vertex/edge/cone APIs resolve the declared triangulated solid before
any cone test; only source-labelled single-cover helpers keep descriptor semantics.

Gordan cone feasibility is certified with an exact minimum-norm active-simplex
algorithm; no thin triangle/simplex or barycentric tolerance changes the answer.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from itertools import combinations
from math import gcd, lcm

from eab.construction import sqrt_rational, norm_rational, vector_rational, scalar_rational

from . import geom3
from .geom3 import (Polyhedron, Vec3, add, cross, dot, mul, neg, norm,
                    sub, unit)


def _qvector(v):
    """Preserve the exact value of each supplied coordinate (including Fraction)."""
    return _qvector_cached(tuple(v))


@lru_cache(maxsize=8192)
def _qvector_cached(v):
    return tuple(Fraction(c) for c in v)


def _qedge(P, e):
    direction = _qedge_vector_cached(tuple(P.verts[e[0]]), tuple(P.verts[e[1]]), _qvector)
    if not any(direction):
        raise ValueError(f"zero-length edge {e} (consecutive duplicate vertex)")
    return direction


@lru_cache(maxsize=8192)
def _qedge_vector_cached(a, b, vector_implementation):
    # Implementation arguments are cache-identity data only; calls stay named.
    return sub(_qvector(b), _qvector(a))


def _qnormal(P, fi):
    f = P.faces[fi]
    return _qnormal_cached(tuple(P.verts[i] for i in f))


@lru_cache(maxsize=4096)
def _qnormal_cached(points):
    o = _qvector(points[0])
    n = (Fraction(0),) * 3
    for a, b in zip(points, points[1:] + points[:1]):
        n = add(n, cross(sub(_qvector(a), o), sub(_qvector(b), o)))
    return n


def _qincident(P, vi):
    return _qincident_cached(tuple(P.verts), tuple(P.faces), vi, _qedge)


@lru_cache(maxsize=8192)
def _qincident_cached(vertices, faces, vi, edge_implementation):
    P = Polyhedron(list(vertices), list(faces))
    return tuple(_qedge(P, (vi, e[1] if e[0] == vi else e[0]))
                 for e in P.edges() if vi in e)


def _float_vector(v):
    return vector_rational(v, allow_underflow=True)


def _qunit(v, *, allow_underflow=False):
    """Final normalized components from the exact vector, never rounded first."""
    return unit(v, allow_underflow=allow_underflow)


def _outside_dot_band(value, a, b, tol):
    """Exact comparison with an explicit dimensionless normalized-dot window."""
    if value <= 0:
        return False
    if tol <= 0:
        return True
    threshold, aa, bb = _squared_tol(tol), _qnorm2(a, dot), _qnorm2(b, dot)
    # Cross-multiply positive denominators; do not construct four intermediate
    # Fractions (or approximate the angular reporting band by a float).
    return (value.numerator**2 * threshold.denominator * aa.denominator * bb.denominator
            > value.denominator**2 * threshold.numerator * aa.numerator * bb.numerator)


@lru_cache(maxsize=64)
def _squared_tol(tol):
    return Fraction(tol) ** 2


@lru_cache(maxsize=16384)
def _qnorm2(v, dot_implementation):
    return dot(v, v)


@lru_cache(maxsize=8192)
def _normalised_constraint(v):
    return mul(v, 1 / max(abs(x) for x in v))


def _qvertex_contains(P, vi, d, tol=0.0):
    """Internal source-ring cone; public solid APIs resolve exact_surface first."""
    edges = _qincident(P, vi)
    return _qvertex_state_cached(edges, tuple(d), tol, _outside_dot_band)


@lru_cache(maxsize=16384)
def _qvertex_state_cached(edges, d, tol, band_implementation):
    if not edges:
        return -1
    strict = True
    for e in edges:
        value = dot(d, e)
        if _outside_dot_band(value, d, e, tol):
            return -1
        if value >= 0:
            strict = False
    return 1 if strict else 0


def _integer_ray(v):
    """Exact positive rescaling of a Fraction/integer vector; preserve all signs."""
    den = lcm(*(c.denominator for c in v))
    result = tuple(c.numerator * (den // c.denominator) for c in v)
    divisor = gcd(*result)
    return tuple(c // divisor for c in result) if divisor else result


def _qedge_contains(P, e, d, tol=0.0):
    """Internal source-ring wedge; public solid APIs resolve exact_surface first.

    Integer rays preserve the normalized-dot window.

    Each vector is multiplied by its own strictly positive rational factor.
    Signs/zeros and value**2/(norm(a)**2*norm(b)**2) therefore do not change.
    Gate: test_perf_edge_frame::test_integer_edge_frame_matches_fraction_reference.
    """
    trav = P.edge_traversals(e)
    if len(trav) != 2:
        return -1
    (f1, a, b), (f2, _, _) = trav
    t = _qedge(P, (a, b))
    n1, n2 = _qnormal(P, f1), _qnormal(P, f2)
    convex, t, h1, h2 = _qedge_frame_cached(t, n1, n2, cross, dot)
    if not convex:
        return -1
    d = _integer_ray(d)
    axial = dot(d, t)
    if _outside_dot_band(abs(axial), d, t, tol):
        return -1
    s1, s2 = dot(h1, d), dot(h2, d)
    if _outside_dot_band(-s1, h1, d, tol) or _outside_dot_band(-s2, h2, d, tol):
        return -1
    return 1 if s1 > 0 and s2 > 0 and axial == 0 else 0


@lru_cache(maxsize=8192)
def _qedge_frame_cached(t, n1, n2, cross_implementation, dot_implementation):
    """Same content/implementation key; store positive-rescaled integer rays."""
    return (dot(cross(n1, n2), t) > 0,
            _integer_ray(t),
            _integer_ray(cross(t, n1)),
            _integer_ray(cross(n2, t)))


def _clamp01(s: float) -> float:
    # Integer endpoints preserve Fraction arithmetic for exact projections.
    return 0 if s < 0 else (1 if s > 1 else s)


def _closest_on_face_boundary(x: Vec3, P: Polyhedron, fi: int) -> Vec3:
    """面 fi 的边界折线上离 x 最近的点（x 已在面平面上、落在多边形外或边上时，它就是面多边形上的最近点）。"""
    f = P.faces[fi]
    best, bd = f and P.verts[f[0]], float("inf")
    for i in range(len(f)):
        a, b = _qvector(P.verts[f[i]]), _qvector(P.verts[f[(i + 1) % len(f)]])
        d = sub(b, a)
        dd = dot(d, d)
        q = a if dd <= 0.0 else add(a, mul(d, _clamp01(dot(sub(x, a), d) / dd)))
        w = sub(x, q)
        if dot(w, w) < bd:
            best, bd = q, dot(w, w)
    return best


def _face_witness(x: Vec3, g: float, P: Polyhedron, fi: int, lng: float) -> tuple[Vec3, bool]:
    """Exact projection extent; an explicit length window only expands acceptance."""
    if geom3.face_polygon_locate(x, P, fi, max(0.0, lng)) < 0:
        return _float_vector(x), False
    witness = x if geom3.face_polygon_locate(x, P, fi, 0.0) >= 0 else _closest_on_face_boundary(x, P, fi)
    return _float_vector(witness), True


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

    # Exact magnitude/sign certificates accompany the rounded displays, even
    # when a nonzero value is below binary64. They never replace source-based
    # cone/window decisions. Gate: test_cover_construction_exposes_exact_nonzero_gap_and_area.
    exact_gap_squared: Fraction | None = None
    exact_gap_sign: int | None = None
    exact_area_squared: Fraction | None = None
    exact_normal_direction: tuple[Fraction, ...] | None = None  # unnormalised display certificate

    # Projection parameters may display zero below binary64; exact values remain
    # available and control extent. Gate: test_cover_parameter_underflow_keeps_exact_certificate.
    exact_params: tuple[Fraction, ...] | None = None

    def label(self) -> tuple:
        return (self.kind, self.a_feature, self.b_feature)


# ------------------------------------------------------------------ 法锥判据

def vertex_cone_contains(P: Polyhedron, vi: int, d: Vec3, tol: float = 0.0) -> int:
    """Declared-solid vertex cone: 1 strict / 0 boundary / -1 outside.

    Resolve nonplanar rings to their declared triangles before collecting
    incident edges. exact_surface preserves every original vertex index.
    Positive tol expands only the closed cone, not strictness.
    Gate: test_public_vertex_cone_uses_declared_surface_while_source_single_cover_is_explicit.
    """
    return _qvertex_contains(geom3.exact_surface(P), vi, _qvector(d), tol)


def edge_arc_contains(P: Polyhedron, e: tuple[int, int], d: Vec3, tol: float = 0.0) -> int:
    """Declared-solid convex edge arc, with an explicit angular window.

    Actual adjacent triangle normals are used on folded rings, including
    internal diagonal edges; source vertex indices are preserved.
    Gate: test_public_edge_arc_uses_declared_adjacent_triangle_normal.
    """
    return _qedge_contains(geom3.exact_surface(P), e, _qvector(d), tol)


def _source_cone_constraints(A, ia, B, ib):
    """Source-ring descriptors only, used by explicitly source-labelled covers."""
    return [*_qincident(B, ib), *(neg(f) for f in _qincident(A, ia))]


def cone_constraints(A: Polyhedron, ia: int, B: Polyhedron, ib: int) -> list[Vec3]:
    """Exact incident constraints on the declared triangulated solids.

    Folded-ring internal diagonals are real incident edges. This public solid
    API is distinct from the explicitly source-labelled single-cover helpers.
    Gate: test_public_cone_constraints_include_folded_internal_incident_ridge.
    """
    return _source_cone_constraints(geom3.exact_surface(A), ia, geom3.exact_surface(B), ib)


def _closest_point_on_segment(a: Vec3, b: Vec3) -> Vec3:
    return _float_vector(_qclosest_segment(_qvector(a), _qvector(b)))


def _qclosest_segment(a, b):
    d = sub(b, a)
    dd = dot(d, d)
    if not dd:
        return a
    t = max(Fraction(0), min(Fraction(1), -dot(a, d) / dd))
    return add(a, mul(d, t))


def _qclosest_triangle(a, b, c):
    n = cross(sub(b, a), sub(c, a))
    nn = dot(n, n)
    if nn:
        p = mul(n, dot(a, n) / nn)
        if all(dot(cross(sub(u, p), sub(v, p)), n) >= 0
               for u, v in ((b, c), (c, a), (a, b))):
            return p
    candidates = [_qclosest_segment(a, b), _qclosest_segment(b, c), _qclosest_segment(c, a)]
    return min((dot(x, x), _rank_index, x) for _rank_index, x in enumerate(candidates))[2]


def _closest_point_on_triangle(a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    return _float_vector(_qclosest_triangle(*(_qvector(_mapped_value) for _mapped_value in (a, b, c))))


def _qtetra_contains_origin(a, b, c, d):
    def volume(p, q, r, s):
        return dot(sub(q, p), cross(sub(r, p), sub(s, p)))
    v = volume(a, b, c, d)
    if not v:
        return False
    zero = (0,) * 3
    numerators = (volume(zero, b, c, d), volume(a, zero, c, d),
                  volume(a, b, zero, d), volume(a, b, c, zero))
    return all(x * v >= 0 for x in numerators)


def _qclosest_simplex(points):
    """Exact nearest point/support, retaining historical candidate and tie order.

    Inputs are exact Fraction/integer vectors, as supplied by _qclosest_hull.
    A shared positive denominator maps the simplex to integer coordinates.
    Candidate squared norms are compared by integer cross multiplication; only
    the returned point is made into Fractions. Triangle projections outside the
    triangle cannot improve on its edges, all already considered. For an inside
    projection p parallel to n, cross(u-p,v-p).n equals cross(u,v).n exactly.
    Gate: test_perf_covers::test_integer_simplex_matches_fraction_reference.
    """
    scale = lcm(*(c.denominator for p in points for c in p))
    integer = tuple(tuple(c.numerator * (scale // c.denominator) for c in p) for p in points)
    indices = range(len(points))
    first = min((dot(integer[i], integer[i]), _rank_index, i) for _rank_index, i in enumerate(indices))[2]
    best, den, support = integer[first], 1, (points[first],)
    best_num, best_den2 = dot(best, best), 1
    for i, j in combinations(indices, 2):
        a, b = integer[i], integer[j]
        d = sub(b, a)
        dd = dot(d, d)
        ad = -dot(a, d)
        if dd and 0 < ad < dd:
            candidate = add(mul(a, dd), mul(d, ad))
            numerator, denominator2 = dot(candidate, candidate), dd * dd
            if numerator * best_den2 < best_num * denominator2:
                best, den, support = candidate, dd, (points[i], points[j])
                best_num, best_den2 = numerator, denominator2
    for i, j, k in combinations(indices, 3):
        a, b, c = integer[i], integer[j], integer[k]
        n = cross(sub(b, a), sub(c, a))
        nn = dot(n, n)
        if nn and all(dot(cross(u, v), n) >= 0 for u, v in ((b, c), (c, a), (a, b))):
            an = dot(a, n)
            numerator, denominator2 = an * an, nn
            if numerator * best_den2 < best_num * denominator2:
                best, den, support = mul(n, an), nn, (points[i], points[j], points[k])
                best_num, best_den2 = numerator, denominator2
    for subset in combinations(indices, 4):
        if _qtetra_contains_origin(*(integer[i] for i in subset)):
            return (Fraction(0),) * 3, tuple(points[i] for i in subset)
    return tuple(Fraction(c, den * scale) for c in best), support


@lru_cache(maxsize=2048)
def _qclosest_hull(pts):
    """Exact fully-corrective minimum-norm algorithm (simplex size <= 4).

    The support point minimizes the exact linear functional. A nonoptimal
    iterate strictly decreases its rational squared norm, and the projection
    always belongs to one of finitely many simplices. Thus there is no tolerance
    or iteration cap. KKT is checked against every original point before return.
    """
    if not pts:
        raise ValueError("empty point set")
    point = min((dot(x, x), _rank_index, x) for _rank_index, x in enumerate(pts))[2]
    support = (point,)
    while True:
        q = min((dot(x, point), _rank_index, x) for _rank_index, x in enumerate(pts))[2]
        if dot(q, point) >= dot(point, point):
            return point
        previous = dot(point, point)
        point, support = _qclosest_simplex((*support, q))
        if dot(point, point) >= previous:
            raise ArithmeticError("exact minimum-norm iteration did not decrease")


def closest_point_of_convex_hull_to_origin(pts: list[Vec3]) -> Vec3:
    """Nearest point construction, with exact simplex/degeneracy predicates.

    The internal zero predicate is exact; this public vector is a floating
    construction and may round below the representable range. The cone decision
    reads the rational result, never this rounded construction. There is no
    thickness or barycentric tolerance, including for thin simplices.
    """
    return _float_vector(_qclosest_hull(tuple(_qvector(_mapped_value) for _mapped_value in pts)))


def cone_relint_direction(g: list[Vec3], tol: float = 1e-12) -> Vec3 | None:
    """Construct a strict cone direction. tol is compatibility-only, not a cutoff."""
    points = tuple(_qvector(x) for x in g)
    if not points:
        return None
    p = _qclosest_hull(points)
    return _qunit(neg(p)) if any(p) else None


def cone_intersection_margin(A: Polyhedron, ia: int, B: Polyhedron, ib: int) -> tuple[float, float]:
    """Distance to an exact positively-rescaled constraint hull; noise is report-only."""
    A, B = geom3.exact_surface(A), geom3.exact_surface(B)
    g = _source_cone_constraints(A, ia, B, ib)
    # Rational normalization preserves whether zero is in the convex hull.
    points = tuple(_normalised_constraint(x) for x in g if any(x))
    noise = max((nz for _, nz in A.vertex_edges(ia) + B.vertex_edges(ib)), default=0.0)
    if not points:
        return 0.0, noise
    p = _qclosest_hull(points)
    return norm_rational(p), noise


def cones_intersect_relint(A: Polyhedron, ia: int, B: Polyhedron, ib: int, tol: float = 1e-12) -> bool:
    """Exact Gordan alternative: zero outside the constraint hull iff strict feasible.

    tol is retained for call compatibility but cannot discard a thin true cone.
    """
    return _cone_relint_cached(tuple(A.verts), tuple(A.faces), ia,
                              tuple(B.verts), tuple(B.faces), ib, False,
                              (cone_constraints, _qincident, _qedge, _qclosest_hull,
                               _qclosest_simplex, _qtetra_contains_origin, _normalised_constraint, geom3.exact_surface))


def _source_cones_intersect_relint(A, ia, B, ib):
    """Exact descriptor feasibility for source-labelled VV3, not solid API."""
    return _cone_relint_cached(tuple(A.verts), tuple(A.faces), ia,
                              tuple(B.verts), tuple(B.faces), ib, True,
                              (_source_cone_constraints, _qincident, _qedge, _qclosest_hull,
                               _qclosest_simplex, _qtetra_contains_origin, _normalised_constraint))


@lru_cache(maxsize=8192)
def _cone_relint_cached(av, af, ia, bv, bf, ib, source, implementations):
    A, B = Polyhedron(list(av), list(af)), Polyhedron(list(bv), list(bf))
    g = _source_cone_constraints(A, ia, B, ib) if source else cone_constraints(A, ia, B, ib)
    if not g:
        return False
    points = tuple(_normalised_constraint(x) for x in g if any(x))
    return bool(points) and any(_qclosest_hull(points))


def _signed_gap(numerator, denominator):
    squared = numerator*numerator/denominator
    magnitude = sqrt_rational(squared, allow_underflow=True)
    return -magnitude if numerator < 0 else magnitude


def _project_on_face(p: Vec3, P: Polyhedron, fi: int) -> tuple[Vec3, float]:
    n = _qnormal(P, fi)
    point, origin = _qvector(p), _qvector(P.verts[P.faces[fi][0]])
    h = dot(n, sub(point, origin)) / dot(n, n)
    projection = sub(point, mul(n, h))
    numerator = dot(n, sub(point, origin))
    gap = _signed_gap(numerator, dot(n, n))
    return projection, gap


# Facet constructions below use original rational coordinates for every branch.


def vf_cover(A: Polyhedron, ia: int, B: Polyhedron, fb: int, tol: float = 0.0, extent_tol: float = 0.0) -> Cover3 | None:
    """Vertex/face cover with exact local cone and exact projected extent."""
    n = _qnormal(B, fb)
    side = _qvertex_contains(A, ia, neg(n), tol)
    if side < 0:
        return None
    a = A.verts[ia]
    proj, g = _project_on_face(a, B, fb)
    wit, inside = _face_witness(proj, g, B, fb, extent_tol)
    numerator = dot(n, sub(_qvector(a), _qvector(B.verts[B.faces[fb][0]])))
    nn = dot(n, n)
    return Cover3("VF", ("vertex", ia), ("face", fb), _qunit(n, allow_underflow=True), g, a, wit, (),
                  sqrt_rational(nn/4, allow_underflow=True), side == 1, inside,
                  numerator*numerator/nn, (numerator > 0)-(numerator < 0), nn/4, n)


def fv_cover(A: Polyhedron, fa: int, B: Polyhedron, ib: int, tol: float = 0.0, extent_tol: float = 0.0) -> Cover3 | None:
    """Face/vertex cover with exact local cone and exact projected extent."""
    n = _qnormal(A, fa)
    side = _qvertex_contains(B, ib, neg(n), tol)
    if side < 0:
        return None
    b = B.verts[ib]
    proj, g = _project_on_face(b, A, fa)
    wit, inside = _face_witness(proj, g, A, fa, extent_tol)
    numerator = dot(n, sub(_qvector(b), _qvector(A.verts[A.faces[fa][0]])))
    nn = dot(n, n)
    return Cover3("FV", ("face", fa), ("vertex", ib), neg(_qunit(n, allow_underflow=True)), g, wit, b, (),
                  sqrt_rational(nn/4, allow_underflow=True), side == 1, inside,
                  numerator*numerator/nn, (numerator > 0)-(numerator < 0), nn/4, neg(n))


def _qclosest_params(p1, d1, p2, d2):
    n = cross(d1, d2)
    nn = dot(n, n)
    if not nn:
        return None
    w = sub(p2, p1)
    return dot(cross(w, d2), n) / nn, dot(cross(w, d1), n) / nn


def _closest_params(p1: Vec3, d1: Vec3, p2: Vec3, d2: Vec3) -> tuple[float, float] | None:
    """Exact parallel decision and rational line parameters, float output only."""
    result = _qclosest_params(*(_qvector(_mapped_value) for _mapped_value in (p1, d1, p2, d2)))
    return None if result is None else vector_rational(result)


def _qparameter_in_extent(s, d, extent_tol):
    if 0 <= s <= 1:
        return True
    if extent_tol <= 0:
        return False
    over = -s if s < 0 else s - 1
    return over * over * dot(d, d) <= Fraction(extent_tol) ** 2


def _qclamp(s):
    return max(Fraction(0), min(Fraction(1), s))


def ee_cover(A: Polyhedron, ea: tuple[int, int], B: Polyhedron, eb: tuple[int, int],
             tol: float = 0.0, extent_tol: float = 0.0) -> Cover3 | None:
    """Edge/edge cover: exact arc signs, parallelism, parameters and extent."""
    pa0, pb0 = _qvector(A.verts[ea[0]]), _qvector(B.verts[eb[0]])
    dA, dB = _qedge(A, ea), _qedge(B, eb)
    normal = cross(dB, dA)
    if not any(normal):
        return None
    for candidate in (normal, neg(normal)):
        sb = _qedge_contains(B, eb, candidate, tol)
        if sb < 0:
            continue
        sa = _qedge_contains(A, ea, neg(candidate), tol)
        if sa < 0:
            continue
        # The exact nonzero normal above proves nonparallel lines. Parameters
        # cannot change cone feasibility, so construct them only for survivors.
        params = _qclosest_params(pa0, dA, pb0, dB)
        if params is None:
            return None
        s, t = params
        # All classifications use the rational parameters. Output points are
        # consistently constructed from one exact witness pair, then rounded.
        qa, qb = add(pa0, mul(dA, s)), add(pb0, mul(dB, t))
        unit_normal = _qunit(candidate, allow_underflow=True)
        numerator, nn = dot(candidate, sub(qa, qb)), dot(candidate, candidate)
        gap = _signed_gap(numerator, nn)
        inside = (_qparameter_in_extent(s, dA, extent_tol)
                  and _qparameter_in_extent(t, dB, extent_tol))
        if not 0 <= s <= 1:
            qa = add(pa0, mul(dA, _qclamp(s)))
            qb = add(pb0, mul(dB, _qclamp(dot(sub(qa, pb0), dB) / dot(dB, dB))))
        elif not 0 <= t <= 1:
            qb = add(pb0, mul(dB, _qclamp(t)))
            qa = add(pa0, mul(dA, _qclamp(dot(sub(qb, pa0), dA) / dot(dA, dA))))
        return Cover3("EE", ("edge", *ea), ("edge", *eb), unit_normal, gap,
                      _float_vector(qa), _float_vector(qb), (scalar_rational(s, allow_underflow=True), scalar_rational(t, allow_underflow=True)), None,
                      sb == 1 and sa == 1, inside,
                      numerator*numerator/nn, (numerator > 0)-(numerator < 0), None, candidate, (s, t))
    return None


# Low-dimensional covers retain boundary states; strict is never a filter.


def ve3_cover(A: Polyhedron, ia: int, B: Polyhedron, eb: tuple[int, int], tol: float = 0.0,
              extent_tol: float = 0.0) -> Cover3 | None:
    """Exact vertex/edge cone and projection predicates, float construction."""
    a, p0 = _qvector(A.verts[ia]), _qvector(B.verts[eb[0]])
    d = _qedge(B, eb)
    w = sub(a, p0)
    s = dot(w, d) / dot(d, d)
    v = sub(w, mul(d, s))
    if not any(v):
        return None
    sb, sa = _qedge_contains(B, eb, v, tol), _qvertex_contains(A, ia, neg(v), tol)
    if sb < 0 or sa < 0:
        return None
    vv = dot(v, v)
    return Cover3("VE3", ("vertex", ia), ("edge", *eb), _qunit(v, allow_underflow=True), sqrt_rational(vv, allow_underflow=True),
                  A.verts[ia], _float_vector(add(p0, mul(d, _qclamp(s)))), (scalar_rational(s, allow_underflow=True),), None,
                  sb == 1 and sa == 1, _qparameter_in_extent(s, d, extent_tol), vv, 1, None, v, (s,))


def ev3_cover(A: Polyhedron, ea: tuple[int, int], B: Polyhedron, ib: int, tol: float = 0.0,
              extent_tol: float = 0.0) -> Cover3 | None:
    """Exact edge/vertex cover, symmetric to vertex/edge."""
    c = ve3_cover(B, ib, A, ea, tol, extent_tol)
    if c is None:
        return None
    return Cover3("EV3", ("edge", *ea), ("vertex", ib), neg(c.normal), c.gap,
                  c.point_b, c.point_a, c.params, None, c.strict, c.in_extent,
                  c.exact_gap_squared, c.exact_gap_sign, None,
                  neg(c.exact_normal_direction) if c.exact_normal_direction is not None else None, c.exact_params)


def vv3_cover(A: Polyhedron, ia: int, B: Polyhedron, ib: int, tol: float = 0.0) -> Cover3 | None:
    """VV3 existence uses exact Gordan; activity uses the exact separation vector."""
    if not _source_cones_intersect_relint(A, ia, B, ib):
        return None
    a, b = A.verts[ia], B.verts[ib]
    v = sub(_qvector(a), _qvector(b))
    if not any(v):
        return Cover3("VV3", ("vertex", ia), ("vertex", ib), None, 0.0, a, b, (), None, True, True, Fraction(0), 0)
    active = (_qvertex_contains(B, ib, v, tol) >= 0 and _qvertex_contains(A, ia, neg(v), tol) >= 0)
    vv = dot(v, v)
    return Cover3("VV3", ("vertex", ia), ("vertex", ib), _qunit(v, allow_underflow=True), sqrt_rational(vv, allow_underflow=True),
                  a, b, (), None, True, active, vv, 1, None, v)


# Enumeration


def _cover_in_window(c: Cover3, A: Polyhedron, B: Polyhedron, window: float) -> bool:
    """Exact feature distance window; never read the constructed c.gap.

    VF/FV use the specified source descriptor plane, EE its two infinite lines,
    VE3/EV3 the infinite line projection, and VV3 the vertex separation. Extent
    is a separate predicate. Original coordinates, not rounded witnesses, are
    the input to every squared-distance comparison.
    """
    if not window >= 0:
        return False
    if window == float("inf"):
        return True
    if c.kind in ("VF", "FV"):
        V, vi, P, fi = ((A, c.a_feature[1], B, c.b_feature[1]) if c.kind == "VF"
                       else (B, c.b_feature[1], A, c.a_feature[1]))
        n = _qnormal(P, fi)
        w = sub(_qvector(V.verts[vi]), _qvector(P.verts[P.faces[fi][0]]))
        numerator, denominator = dot(n, w) ** 2, dot(n, n)
    elif c.kind == "EE":
        ea, eb = c.a_feature[1:], c.b_feature[1:]
        n = cross(_qedge(A, ea), _qedge(B, eb))
        w = sub(_qvector(A.verts[ea[0]]), _qvector(B.verts[eb[0]]))
        numerator, denominator = dot(n, w) ** 2, dot(n, n)
    elif c.kind in ("VE3", "EV3"):
        V, vi, P, e = ((A, c.a_feature[1], B, c.b_feature[1:]) if c.kind == "VE3"
                      else (B, c.b_feature[1], A, c.a_feature[1:]))
        d = _qedge(P, e)
        w = sub(_qvector(V.verts[vi]), _qvector(P.verts[e[0]]))
        denominator = dot(d, d)
        numerator = dot(w, w) * denominator - dot(w, d) ** 2
    elif c.kind == "VV3":
        w = sub(_qvector(A.verts[c.a_feature[1]]), _qvector(B.verts[c.b_feature[1]]))
        numerator, denominator = dot(w, w), 1
    else:
        raise ValueError(f"unknown cover kind: {c.kind}")
    return numerator <= _squared_tol(window) * denominator


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
            if c is not None and (c.in_extent or not require_in_extent) and _cover_in_window(c, A, B, window):
                out.append(c)
    for fa in range(len(A.faces)):
        for ib in range(len(B.verts)):
            c = fv_cover(A, fa, B, ib, tol, extent_tol)
            if c is not None and (c.in_extent or not require_in_extent) and _cover_in_window(c, A, B, window):
                out.append(c)
    for ea in A.edges():
        for eb in B.edges():
            c = ee_cover(A, ea, B, eb, tol, extent_tol)
            if c is not None and (c.in_extent or not require_in_extent) and _cover_in_window(c, A, B, window):
                out.append(c)
    if include_low_dim:
        for ia in range(len(A.verts)):
            for eb in B.edges():
                c = ve3_cover(A, ia, B, eb, tol, extent_tol)
                if c is not None and (c.in_extent or not require_in_extent) and _cover_in_window(c, A, B, window):
                    out.append(c)
        for ea in A.edges():
            for ib in range(len(B.verts)):
                c = ev3_cover(A, ea, B, ib, tol, extent_tol)
                if c is not None and (c.in_extent or not require_in_extent) and _cover_in_window(c, A, B, window):
                    out.append(c)
        for ia in range(len(A.verts)):
            for ib in range(len(B.verts)):
                c = vv3_cover(A, ia, B, ib, tol)
                if c is not None and c.in_extent and _cover_in_window(c, A, B, window):
                    out.append(c)
    return out


def local_facets3(A: Polyhedron, B: Polyhedron, tol: float = 0.0) -> set[tuple]:
    """Strict local facets of the explicit exact convex views."""
    A, B = geom3.exact_convex_view(A), geom3.exact_convex_view(B)
    return set(_local_facets_cached(tuple(A.verts), tuple(A.faces), tuple(B.verts), tuple(B.faces),
                                   (_qnormal, _qedge, _qvertex_contains, _qedge_contains)))


@lru_cache(maxsize=128)
def _local_facets_cached(av, af, bv, bf, implementations):
    A, B = Polyhedron(list(av), list(af)), Polyhedron(list(bv), list(bf))
    out = []
    for ia in range(len(av)):
        for fb in range(len(bf)):
            if _qvertex_contains(A, ia, neg(_qnormal(B, fb))) == 1:
                out.append(("VF", ("vertex", ia), ("face", fb)))
    for fa in range(len(af)):
        for ib in range(len(bv)):
            if _qvertex_contains(B, ib, neg(_qnormal(A, fa))) == 1:
                out.append(("FV", ("face", fa), ("vertex", ib)))
    for ea in A.edges():
        for eb in B.edges():
            n = cross(_qedge(B, eb), _qedge(A, ea))
            if not any(n):
                continue
            for d in (n, neg(n)):
                if _qedge_contains(B, eb, d) == 1 and _qedge_contains(A, ea, neg(d)) == 1:
                    out.append(("EE", ("edge", *ea), ("edge", *eb)))
                    break
    return tuple(out)


def _oriented_ee_normal(A, ea, B, eb, tol=0.0):
    """One exact EE orientation rule for covers/facets/frozen evaluation.

    tol is an explicit dimensionless cone-report window. General surface labels
    and canonical-convex labels must still be supplied on their own view.
    """
    n = cross(_qedge(B, eb), _qedge(A, ea))
    if not any(n):
        raise ZeroDivisionError("parallel edges do not define an EE facet")
    for direction in (n, neg(n)):
        if (_qedge_contains(B, eb, direction, tol) >= 0
                and _qedge_contains(A, ea, neg(direction), tol) >= 0):
            return direction
    # Compatibility for explicitly requesting the normal of a non-valid label.
    return neg(n) if _qedge_contains(B, eb, n, tol) < 0 else n


def _facet_plane_on_views(A, B, label, tol=0.0):
    kind, af, bf = label
    if kind == "VF":
        n = _qnormal(B, bf[1])
        a, b = A.verts[af[1]], B.verts[B.faces[bf[1]][0]]
    elif kind == "FV":
        n = neg(_qnormal(A, af[1]))
        a, b = A.verts[A.faces[af[1]][0]], B.verts[bf[1]]
    elif kind == "EE":
        ea, eb = (af[1], af[2]), (bf[1], bf[2])
        n = _oriented_ee_normal(A, ea, B, eb, tol)
        a, b = A.verts[af[1]], B.verts[bf[1]]
    else:
        raise ValueError(f"not a facet label: {label}")
    return n, sub(_qvector(b), _qvector(a))


def facet_plane3(A: Polyhedron, B: Polyhedron, label: tuple):
    """Exact (outward unnormalised normal, point on E support plane).

    Labels are indexed on exact_convex_view; the point b-a is never rounded.
    """
    return _facet_plane_on_views(geom3.exact_convex_view(A), geom3.exact_convex_view(B), label)


def facet_normal3(A: Polyhedron, B: Polyhedron, label: tuple) -> Vec3:
    """Float normal construction from the exact oriented facet plane."""
    n, _ = facet_plane3(A, B, label)
    return _qunit(n)


def facet_gap3(A: Polyhedron, B: Polyhedron, label: tuple, x: Vec3) -> float:
    """Float signed distance construction; never reused for classification."""
    n, p = facet_plane3(A, B, label)
    numerator = dot(n, sub(_qvector(x), p))
    return (-1 if numerator < 0 else 1) * sqrt_rational(numerator*numerator / dot(n, n))


@lru_cache(maxsize=128)
def _support_planes_cached(av, af, bv, bf, labels, implementations):
    A, B = Polyhedron(list(av), list(af)), Polyhedron(list(bv), list(bf))
    aq, bq = tuple(_qvector(_mapped_value) for _mapped_value in av), tuple(_qvector(_mapped_value) for _mapped_value in bv)
    out = []
    for fi in range(len(bf)):
        n = _qnormal(B, fi)
        a = min((dot(n, x), _rank_index, x) for _rank_index, x in enumerate(aq))[2]
        b = bq[bf[fi][0]]
        out.append((n, sub(b, a)))
    for fi in range(len(af)):
        n = neg(_qnormal(A, fi))
        a = aq[af[fi][0]]
        b = max((dot(n, x), -_rank_index, x) for _rank_index, x in enumerate(bq))[2]
        out.append((n, sub(b, a)))
    # Caller-supplied labels are deliberately not sanitized: a false local
    # support plane must be exposed by the independent G0 membership vote.
    out.extend(_facet_plane_on_views(A, B, label) for label in labels)
    return tuple((n, p, _integer_plane(n, p)) for n, p in out)


def _integer_plane(n, p):
    """Positive homogeneous rescaling of n.(x-p)=0; no geometry is rounded."""
    coeffs = (*n, dot(n, p))
    den = lcm(*(c.denominator for c in coeffs))
    ints = tuple(c.numerator * (den // c.denominator) for c in coeffs)
    common = gcd(*ints)
    ints = tuple(v // common for v in ints)
    return ints, sum(v*v for v in ints[:3])


def _plane_data(A, B, facets):
    return _support_planes_cached(tuple(A.verts), tuple(A.faces), tuple(B.verts), tuple(B.faces), tuple(sorted(facets)),
                                  (_qnormal, _qedge, _qedge_contains, _integer_plane))


def _planes(A, B, facets):
    return tuple((n, p) for n, p, _ in _plane_data(A, B, facets))


def support_gaps3(A: Polyhedron, B: Polyhedron, x: Vec3) -> list[float]:
    """Face-support distances as constructions, not predicate inputs."""
    A, B = geom3.exact_convex_view(A), geom3.exact_convex_view(B)
    point = _qvector(x)
    out = []
    for n, p in _planes(A, B, ()):
        numerator = dot(n, sub(point, p))
        out.append((-1 if numerator < 0 else 1) * sqrt_rational(numerator*numerator / dot(n, n)))
    return out


def membership_convex3(A: Polyhedron, B: Polyhedron, x: Vec3, tol: float = 0.0,
                       facets: set[tuple] | None = None, *, ang_tol: float = 1e-12) -> int:
    """Exact convex E membership: 1 inside / 0 boundary / -1 outside.

    Positive tol only reports a nonzero state as 0 when its Euclidean distance
    to the complete boundary of E is <= tol. Inside, the nearest supporting
    plane realizes that distance. Outside, plane distances are only lower
    bounds: an exact minimum-norm point of conv({b-a-x}) certifies the distance.
    No rounded hull, constructed gap, or numerical thickness is used.
    Gates: test_e5a2_covers.py::test_membership_report_band_is_euclidean.
    """
    A, B = geom3.exact_convex_view(A), geom3.exact_convex_view(B)
    if facets is None:
        facets = local_facets3(A, B, 0.0)
    point = _qvector(x)
    if tol == float("inf"):
        return 0
    tol2 = Fraction(tol) ** 2 if tol > 0 else 0
    den = lcm(*(v.denominator for v in point))
    point_i = tuple(v.numerator * (den // v.denominator) for v in point)
    threshold = tol2.numerator * den * den if tol2 else 0
    divisor = tol2.denominator if tol2 else 1
    boundary = outside = near = False
    for _, _, (plane, normal2) in _plane_data(A, B, facets):
        value = (plane[0]*point_i[0] + plane[1]*point_i[1]
                 + plane[2]*point_i[2] - plane[3]*den)
        if value > 0:
            outside = True
            # A support-plane distance is a certified lower bound, not the
            # Euclidean distance itself (strictly different at exterior edges).
            if not tol2 or value * value * divisor > threshold * normal2:
                return -1
        elif value == 0:
            boundary = True
        if tol2 and value * value * divisor <= threshold * normal2:
            near = True
    if outside:
        aq, bq = tuple(_qvector(_mapped_value) for _mapped_value in A.verts), tuple(_qvector(_mapped_value) for _mapped_value in B.verts)
        nearest = _qclosest_hull(tuple(sub(sub(b, a), point) for a in aq for b in bq))
        return 0 if dot(nearest, nearest) <= tol2 else -1
    return 0 if boundary or near else 1
