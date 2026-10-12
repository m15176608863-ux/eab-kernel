"""E5a2 exact windows, Euclidean report bands, and honest source-ring boundary.

Oracles use only Fraction scalar algebra, coordinate Newell identities, Gram
normal equations, and analytic boxes/tetrahedra. No production geometry helper
is used to compute an expected predicate or distance.
"""

from fractions import Fraction as F
from itertools import combinations
import math
import random

import pytest

from eab.kernel3d import covers3 as C
from eab.kernel3d.geom3 import Polyhedron, box, tetra


def _q(v):
    return tuple(F(c) for c in v)


def _minus(a, b):
    return tuple(x-y for x, y in zip(a, b))


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _ring_normal(P, fi):
    vertices = [_q(P.verts[i]) for i in P.faces[fi]]
    return tuple(sum((a[(k+1)%3]-b[(k+1)%3])*(a[(k+2)%3]+b[(k+2)%3])
                     for a, b in zip(vertices, vertices[1:]+vertices[:1])) for k in range(3))


def _distance2_oracle(A, B, label):
    """Independent feature projections; EE uses Gram, not a cross normal."""
    kind, a, b = label
    if kind in ("VF", "FV"):
        P, vertex, Q, face = (A, a[1], B, b[1]) if kind == "VF" else (B, b[1], A, a[1])
        w = _minus(_q(P.verts[vertex]), _q(Q.verts[Q.faces[face][0]]))
        n = _ring_normal(Q, face)
        return _dot(w, n)**2/_dot(n, n)
    if kind in ("VE3", "EV3"):
        P, vertex, Q, edge = (A, a[1], B, b[1:]) if kind == "VE3" else (B, b[1], A, a[1:])
        w = _minus(_q(P.verts[vertex]), _q(Q.verts[edge[0]]))
        d = _minus(_q(Q.verts[edge[1]]), _q(Q.verts[edge[0]]))
        parameter = _dot(w, d)/_dot(d, d)
        v = tuple(wi-parameter*di for wi, di in zip(w, d))
        return _dot(v, v)
    if kind == "VV3":
        v = _minus(_q(A.verts[a[1]]), _q(B.verts[b[1]]))
        return _dot(v, v)
    pa, pb = _q(A.verts[a[1]]), _q(B.verts[b[1]])
    da, db = _minus(_q(A.verts[a[2]]), pa), _minus(_q(B.verts[b[2]]), pb)
    w = _minus(pb, pa)
    aa, ab, bb = _dot(da, da), _dot(da, db), _dot(db, db)
    aw, bw, den = _dot(da, w), _dot(db, w), aa*bb-ab*ab
    s, t = (bb*aw-ab*bw)/den, (ab*aw-aa*bw)/den
    v = tuple(pa[k]+s*da[k]-pb[k]-t*db[k] for k in range(3))
    return _dot(v, v)


def _transform(P, scale, translation, rotate=True):
    # Exact orthogonal 3-4-5 rotation; no rounded-coordinate invariance premise.
    def point(v):
        x, y, z = _q(v)
        r = ((3*x-4*y)/5, (4*x+3*y)/5, z) if rotate else (x, y, z)
        return tuple(scale*c+translation[k] for k, c in enumerate(r))
    faces = [tuple(reversed(f)) for f in P.faces] if scale < 0 else list(P.faces)
    return Polyhedron([point(v) for v in P.verts], faces)


@pytest.mark.parametrize("scale", [F(1, 2**20), F(1), F(2**20)])
@pytest.mark.parametrize("origin", [0, 10**6])
def test_enumeration_windows_match_independent_rational_feature_distances(scale, origin):
    """Random/general, exact parallel/endpoint, engineering-coordinate cells."""
    rng = random.Random(522)
    pairs = [(box(center=(.25, .5, 2.25)), box()),
             (tetra((0, 0, 0), (2, .5, 0), (0, 1, .5), (.5, 0, 2)),
              tetra((1, 1, 1), (3, 1, 1), (1, 3, 1), (1, 1, 3)))]
    pairs.extend((box(center=tuple(rng.uniform(-2, 2) for _ in range(3))), box()) for _ in range(2))
    pairs.append((box(center=(10, 11, 12)), box()))
    kinds = set()
    for i, (A, B) in enumerate(pairs):
        A = _transform(A, scale, (origin, -origin, origin), i % 2 == 0)
        B = _transform(B, scale, (origin, -origin, origin), i % 2 == 1)
        all_covers = C.enumerate_covers3(A, B, window=math.inf, require_in_extent=False)
        kinds.update(c.kind for c in all_covers)
        distances = {c.label(): _distance2_oracle(A, B, c.label()) for c in all_covers}
        for window in (0, scale/4, scale, scale*3):
            expected = {label for label, d2 in distances.items() if d2 <= window*window}
            actual = {c.label() for c in C.enumerate_covers3(A, B, window=window, require_in_extent=False)}
            assert actual == expected, (i, window, actual ^ expected)
    assert kinds == {"VF", "FV", "EE", "VE3", "EV3", "VV3"}


def test_enumeration_window_does_not_read_a_gap_rounded_to_zero():
    """A genuine constructor underflow, not a fake cover appended afterward."""
    scale = F(1, 2**1100)
    base = box()
    A = Polyhedron([tuple((F(c)+3)*scale for c in p) for p in base.verts], list(base.faces))
    B = Polyhedron([tuple(F(c)*scale for c in p) for p in base.verts], list(base.faces))
    full = C.enumerate_covers3(A, B, window=math.inf)
    assert {c.kind for c in full} == {"VV3"}
    assert all(c.gap == 0 and _distance2_oracle(A, B, c.label()) > 0 for c in full)
    assert all(c.exact_gap_squared == _distance2_oracle(A, B, c.label())
               and c.exact_gap_sign == 1 for c in full)
    assert C.enumerate_covers3(A, B, window=0) == [], "a rounded zero gap must not admit a separated cover"


def test_binary64_window_boundary_uses_exact_distance_not_rounded_sqrt():
    """Original binary64 data; sqrt(3) rounds down, so that float window is
    strictly shorter than the exact vertex separation. Next float admits it.
    Also checks the migrated G2 oracle, which shares no production primitive.
    """
    from e5a_g2_oracle import construction
    A, B = box(center=(3., 3., 3.)), box()
    window = math.sqrt(3.)
    assert F(window)**2 < 3 < F(math.nextafter(window, math.inf))**2
    full = C.enumerate_covers3(A, B, window=math.inf)
    assert len(full) == 1 and full[0].kind == "VV3"
    cover = full[0]
    assert cover.gap == window
    assert construction(A, B, cover.label(), 0, distance_squared=True) == 3
    assert C.enumerate_covers3(A, B, window=window) == []
    assert [c.label() for c in C.enumerate_covers3(A, B, window=math.nextafter(window, math.inf))] == [cover.label()]


@pytest.mark.parametrize("scale", [F(1, 2**20), F(1), F(2**20)])
@pytest.mark.parametrize("origin", [0, 10**6])
def test_membership_report_band_is_euclidean(scale, origin):
    """Closed-form orthogonal box distance; includes outside edge/corner, both
    band boundaries, nonsymmetric reference points, random and scaled cells."""
    A = _transform(box(half=(1, 2, 3)), scale, (origin, -origin, origin))
    B = _transform(box(half=(2, 3, 4)), scale, (origin+7, -origin+11, origin-5))
    rng = random.Random(523)
    points = [(F(13, 4), F(21, 4), 0), (F(13, 4), F(21, 4), F(29, 4)),
              (F(27, 8), F(11, 2), 0), (F(11, 4), 0, 0), (3, 0, 0), (0, 0, 0)]
    points.extend(tuple(F(rng.randint(-64, 64), 8) for _ in range(3)) for _ in range(40))
    seen = set()
    for p in points:
        x, y, z = p
        query = (scale*(3*x-4*y)/5+7, scale*(4*x+3*y)/5+11, scale*z-5)
        excess = [abs(F(c))-h for c, h in zip(p, (3, 5, 7))]
        state = -1 if max(excess) > 0 else (0 if max(excess) == 0 else 1)
        d2 = sum(max(F(0), e)**2 for e in excess) if state == -1 else min(e*e for e in excess)
        for tol in (F(0), F(1, 4), F(5, 16), F(5, 8), F(1)):
            want = 0 if d2 <= tol*tol else state
            seen.add(want)
            assert C.membership_convex3(A, B, query, scale*tol) == want, (p, tol, d2, want)
    assert seen == {-1, 0, 1}


def _solve(matrix, rhs):
    rows = [list(row)+[v] for row, v in zip(matrix, rhs)]
    for col in range(len(rows)):
        pivot = next((i for i in range(col, len(rows)) if rows[i][col]), None)
        if pivot is None:
            return None
        rows[pivot], rows[col] = rows[col], rows[pivot]
        den = rows[col][col]
        rows[col] = [x/den for x in rows[col]]
        for i in range(len(rows)):
            if i != col:
                coeff = rows[i][col]
                rows[i] = [a-coeff*b for a, b in zip(rows[i], rows[col])]
    return [row[-1] for row in rows]


def _simplex_boundary_distance2(vertices, point):
    """Brute affine Gram projections of every face subset, no tested primitive."""
    candidates = []
    for size in (1, 2, 3):
        for subset in combinations(vertices, size):
            vv = [_minus(v, point) for v in subset]
            matrix = [[_dot(a, b) for b in vv]+[F(1)] for a in vv]+[[F(1)]*size+[F(0)]]
            solution = _solve(matrix, [F(0)]*size+[F(1)])
            if solution is not None and all(w >= 0 for w in solution[:-1]):
                q = tuple(sum(w*v[k] for w, v in zip(solution, vv)) for k in range(3))
                candidates.append(_dot(q, q))
    return min(candidates)


@pytest.mark.parametrize("scale", [F(1, 1024), F(1), F(1024)])
def test_membership_euclidean_band_matches_independent_tetrahedron_gram_oracle(scale):
    """E(-T,T)=2T; all boundary subsets use independent exact Gram solves."""
    base = tetra((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
    A = _transform(base, -scale, (10**6, -10**6, 10**6))
    B = _transform(base, scale, (10**6+7, -10**6+11, 10**6-5))
    vertices = [tuple(F(c)*2 for c in p) for p in base.verts]
    rng = random.Random(524)
    points = [(F(-1, 4), F(-1, 4), F(1, 2)), (F(1, 2),)*3, (F(2), F(0), F(0))]
    points += [tuple(F(rng.randint(-8, 24), 8) for _ in range(3)) for _ in range(30)]
    for p in points:
        state = -1 if min(p) < 0 or sum(p) > 2 else (0 if min(p) == 0 or sum(p) == 2 else 1)
        d2 = _simplex_boundary_distance2(vertices, p)
        x, y, z = p
        query = (scale*(3*x-4*y)/5+7, scale*(4*x+3*y)/5+11, scale*z-5)
        for tol in (F(0), F(5, 16), F(3, 4)):
            want = 0 if d2 <= tol*tol else state
            assert C.membership_convex3(A, B, query, scale*tol) == want, (p, tol, d2)


def _folded_pair():
    B = box()
    B.verts[6] = (1., 1., 2.)
    A = tetra((.25, -.25, 3.), (1.25, -.25, 4.), (.25, .75, 4.), (-.75, -1.25, 4.))
    return A, B


def test_source_ring_descriptor_is_not_a_folded_surface_cover():
    """A deliberate counterexample prevents promoting source descriptors to
    folded-surface contacts: the projection lies on no triangle of the ring."""
    A, B = _folded_pair()
    c = C.vf_cover(A, 0, B, 1)
    assert c is not None and c.strict and c.in_extent
    expected = (F(7, 12), F(1, 12), F(5, 3))
    assert c.point_b == tuple(map(float, expected))
    ring = [_q(B.verts[i]) for i in B.faces[1]]
    # Covers both choices of diagonal, without calling production triangulation.
    for a, b, d in combinations(ring, 3):
        assert _dot(_cross(_minus(b, a), _minus(d, a)), _minus(expected, a)) != 0
    cyclic = Polyhedron(list(B.verts), list(B.faces))
    cyclic.faces[1] = cyclic.faces[1][1:] + cyclic.faces[1][:1]
    other = C.vf_cover(A, 0, cyclic, 1)
    assert other is not None and other.normal == c.normal
    assert other.gap != c.gap and other.point_b != c.point_b


def test_source_ring_descriptor_keeps_source_labels_separate_from_convex_views(monkeypatch):
    A, B = _folded_pair()
    canonical = C.geom3.exact_convex_view(B)
    assert len(canonical.faces) == 7 and len(B.faces) == 6
    assert sum(source == (1,) for source in canonical.source_faces) == 2
    def forbidden(_):
        raise AssertionError("single-cover source API must not convexify or relabel")
    monkeypatch.setattr(C.geom3, "exact_convex_view", forbidden)
    cover = C.vf_cover(A, 0, B, 1)
    assert cover is not None and cover.label() == ("VF", ("vertex", 0), ("face", 1))
