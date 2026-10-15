"""Exact global translation obstacle for simple (possibly concave) polygons.

The finite convex-cell union represents E; the union of the *open* cell
interiors represents strict body overlap O. They must not be confused with
int(E), which can contain tight-fit contact seams. See
docs/m3_global_entrance_design.md, T1--T3, and test_m3_global2d.py.

All geometry/certificates stay rational. Only Distance2.point/distance and
RayHit2.point/time are binary64 displays, through construction.py. Input rings
are simple, nonzero-area, without repeated consecutive vertices; clockwise
rings are normalized. Local-cover labels index these normalized rings.
No overlap oracle, production triangulator or floating geometry is imported.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache
from math import lcm

from ..construction import scalar_rational, sqrt_rational, vector_rational

def _point(p):
    if len(p) != 2:
        raise ValueError("global entrance requires two-dimensional points")
    try:
        return tuple(F(v) for v in p)
    except (ValueError, OverflowError):
        raise ValueError("global entrance coordinate: nonfinite or invalid exact input") from None


def _sub(a, b):
    return a[0]-b[0], a[1]-b[1]


def _cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def _at(a, d, t):
    return a[0]+t*d[0], a[1]+t*d[1]


def _edges(poly):
    return zip(poly, poly[1:]+poly[:1])


def _on(p, a, b):
    return _cross(_sub(b, a), _sub(p, a)) == 0 and all(
        min(a[k], b[k]) <= p[k] <= max(a[k], b[k]) for k in (0, 1))


def _cuts(a, b, c, d):
    """Parameters on closed ab at intersections with closed cd, including overlap."""
    u, v, w = _sub(b, a), _sub(d, c), _sub(c, a)
    determinant = _cross(u, v)
    if determinant:
        s, t = _cross(w, v)/determinant, _cross(w, u)/determinant
        return (s,) if 0 <= s <= 1 and 0 <= t <= 1 else ()
    if _cross(w, u):
        return ()
    k = 0 if u[0] else 1
    return tuple((p[k]-a[k])/u[k] for p in (c, d) if _on(p, a, b))


def _ring(poly):
    p = tuple(_point(v) for v in poly)
    if len(p) < 3 or any(a == b for a, b in _edges(p)):
        raise ValueError("polygon needs at least three vertices and no zero-length edge")
    for i, (a, b) in enumerate(_edges(p)):
        for j, (c, d) in enumerate(_edges(p)):
            if j <= i or j == i+1 or (i == 0 and j == len(p)-1):
                continue
            if _cuts(a, b, c, d) or _cuts(c, d, a, b):
                raise ValueError("polygon is not simple")
    area = sum((_cross(_sub(a, p[0]), _sub(b, p[0])) for a, b in _edges(p)), F(0))
    if not area:
        raise ValueError("polygon has zero area")
    p = p if area > 0 else tuple(reversed(p))
    for i, b in enumerate(p):
        a, c = p[i-1], p[(i+1) % len(p)]
        if _cross(_sub(b, a), _sub(c, b)) == 0 and not _on(b, a, c):
            raise ValueError("polygon has a backtracking edge")
    return p


def _triangulate(p):
    """Independent exact ear removal; no oracle triangulation is reused."""
    indices = list(range(len(p)))
    triangles = []
    while len(indices) > 3:
        for k, i in enumerate(indices):
            h, j = indices[k-1], indices[(k+1) % len(indices)]
            turn = _cross(_sub(p[i], p[h]), _sub(p[j], p[i]))
            if turn == 0:
                del indices[k]
                break
            if turn < 0:
                continue
            triangle = (p[h], p[i], p[j])
            if any(all(_cross(_sub(b, a), _sub(p[m], a)) >= 0
                       for a, b in _edges(triangle))
                   for m in indices if m not in (h, i, j)):
                continue
            triangles.append(triangle)
            del indices[k]
            break
        else:
            raise ArithmeticError("exact ear decomposition did not find an ear")
    triangle = tuple(p[i] for i in indices)
    if _cross(_sub(triangle[1], triangle[0]), _sub(triangle[2], triangle[0])) > 0:
        triangles.append(triangle)
    return tuple(triangles)


def _hull(points):
    points = sorted(set(points))
    def half(seq):
        out = []
        for p in seq:
            while len(out) > 1 and _cross(_sub(out[-1], out[-2]), _sub(p, out[-1])) <= 0:
                out.pop()
            out.append(p)
        return out
    return tuple(half(points)[:-1]+half(reversed(points))[:-1])


def _y_at(a, b, x):
    a, b, x = _point(a), _point(b), F(x)
    return a[1]+(b[1]-a[1])*(x-a[0])/(b[0]-a[0])


def _cell_state(cell, x):
    state = 1
    for a, b in _edges(cell):
        value = _cross(_sub(b, a), _sub(x, a))
        if value < 0:
            return -1
        if value == 0:
            state = 0
    return state


def _angular_compare(a, b):
    ha = 0 if a[1] > 0 or (a[1] == 0 and a[0] > 0) else 1
    hb = 0 if b[1] > 0 or (b[1] == 0 and b[0] > 0) else 1
    if ha != hb:
        return ha-hb
    c = _cross(a, b)
    return -1 if c > 0 else (1 if c < 0 else 0)


def _bbox(poly):
    return tuple((min(p[k] for p in poly), max(p[k] for p in poly)) for k in (0, 1))


def _split_segments(segments):
    """All exact intersections; x-sweep rejects only disjoint closed AABBs.

    Homogeneous integer lines avoid Fraction arithmetic inside determinants.
    Gate: test_sweep_partition_matches_unpruned_all_pairs_including_collinear.
    """
    def line(a, b):
        row = (a[1]-b[1], b[0]-a[0], a[0]*b[1]-a[1]*b[0])
        denominator = lcm(*(v.denominator for v in row))
        return tuple(int(v*denominator) for v in row)
    ordered = sorted(((_bbox((a, b)), a, b, line(a, b)) for a, b in segments), key=lambda row: row[0][0][0])
    points = [{a, b} for _, a, b, _ in ordered]
    for i, (box, a, b, (ax, ay, ac)) in enumerate(ordered):
        for j in range(i+1, len(ordered)):
            other, c, d, (bx, by, bc) = ordered[j]
            if other[0][0] > box[0][1]:
                break
            if other[1][0] > box[1][1] or box[1][0] > other[1][1]:
                continue
            determinant = ax*by-ay*bx
            if determinant:
                p = (F(ay*bc-ac*by, determinant), F(ac*bx-ax*bc, determinant))
                if all(max(box[k][0], other[k][0]) <= p[k] <= min(box[k][1], other[k][1]) for k in (0, 1)):
                    points[i].add(p)
                    points[j].add(p)
            elif ax*bc-ac*bx == 0 and ay*bc-ac*by == 0:
                for p in (a, b, c, d):
                    if all(max(box[k][0], other[k][0]) <= p[k] <= min(box[k][1], other[k][1]) for k in (0, 1)):
                        points[i].add(p)
                        points[j].add(p)
    out = set()
    for cuts in points:
        values = sorted(cuts)
        out.update(zip(values, values[1:]))
    return tuple(sorted(out))


def _area2(poly):
    return sum((_cross(a, b) for a, b in _edges(poly)), F(0))


def _merge_convex_parts(parts):
    """Merge disjoint-interior pieces only with an exact equal-area hull proof.

    A,B are closed and inside H=conv(A union B). With disjoint interiors,
    area(H)=area(A)+area(B) excludes any missing open subset of H. Thus H is
    exactly A union B. Induction preserves coverage and disjoint interiors.
    Gate: test_certified_convex_merge_refuses_a_nonconvex_union.
    """
    parts = list(parts)
    while True:
        merged = False
        for i, a in enumerate(parts):
            for j in range(i+1, len(parts)):
                b = parts[j]
                if len(set(a) & set(b)) < 2:
                    continue
                hull = _hull(a+b)
                if _area2(hull) == _area2(a)+_area2(b):
                    parts[i] = hull
                    del parts[j]
                    merged = True
                    break
            if merged:
                break
        if not merged:
            return tuple(parts)


def _indexed_cell(cell):
    rows = []
    for a, b in _edges(cell):
        dx, dy = _sub(b, a)
        row = (-dy, dx, dy*a[0]-dx*a[1])
        denominator = lcm(*(v.denominator for v in row))
        rows.append(tuple(int(v*denominator) for v in row))
    return _bbox(cell), tuple(rows)


@dataclass(frozen=True)
class Distance2:
    squared: F
    exact_point: tuple[F, F]
    tied_exact_points: tuple[tuple[F, F], ...] = ()
    # The complete minimizer set is covariant. Its lexicographic representative
    # is deliberately deterministic, but cannot be rotation-covariant at ties.

    @property
    def distance(self):
        return sqrt_rational(self.squared)

    @property
    def point(self):
        return vector_rational(self.exact_point)


@dataclass(frozen=True)
class RayHit2:
    exact_time: F
    exact_point: tuple[F, F]

    @property
    def time(self):
        return scalar_rational(self.exact_time)

    @property
    def point(self):
        return vector_rational(self.exact_point)


@dataclass(frozen=True)
class CoverPiece2:
    label: tuple
    start: tuple[F, F]
    end: tuple[F, F]
    exposed: bool
    body_state: int
    side_points: tuple[tuple[F, F], tuple[F, F]]
    side_states: tuple[int, int]


@dataclass(frozen=True)
class Cell2:
    """Relative-open cell; its boundary lives in lower-dimensional cells."""
    vertices: tuple[tuple[F, F], ...]
    sample: tuple[F, F]
    state: int


@dataclass(frozen=True)
class Subdivision2:
    vertices: tuple[Cell2, ...]
    edges: tuple[Cell2, ...]
    faces: tuple[Cell2, ...]
    # Outside the finite bounding rectangle the point locator returns -1.
    exterior_state: int = -1


class GlobalEntrance2:
    """Finite exact cell union; lazy clipping and finite labelled subdivision.

    Membership is strict body three-state, topology is E three-state. Gates:
    test_global_body_and_topology_match_independent_oracle_without_skip and
    test_clipped_covers_are_exactly_boundary_and_cover_oracle_ray_exits.
    """
    def __init__(self: GlobalEntrance2, A, B, *, merge_convex=False, compact_subdivision=False):
        self.A, self.B = _ring(A), _ring(B)
        self._compact_subdivision = compact_subdivision
        self._contact_edges = None
        self.parts_a, self.parts_b = tuple(_triangulate(self.A)), tuple(_triangulate(self.B))
        if merge_convex:
            self.parts_a = _merge_convex_parts(self.parts_a)
            self.parts_b = _merge_convex_parts(self.parts_b)
        self.cells = tuple(_hull(_sub(b, a) for a in pa for b in pb)
                           for pa in self.parts_a for pb in self.parts_b)
        self._cell_edges = tuple(sorted({tuple(sorted((a, b))) for cell in self.cells for a, b in _edges(cell)}))
        self._indexed_cells = tuple(_indexed_cell(cell) for cell in self.cells)
        self._clipped_covers_cache = None
        self._boundary_cache = None
        self._subdivision_cache = None
        if not self.cells:
            raise ArithmeticError("empty full-dimensional convex decomposition")

    def membership(self: GlobalEntrance2, x=(0, 0)):
        """-1 outside E, 0 in E\\O, 1 in O; no body-intersection calls."""
        x = _point(x)
        denominator = lcm(x[0].denominator, x[1].denominator)
        xi, yi = int(x[0]*denominator), int(x[1]*denominator)
        state = -1
        for box, rows in self._candidate_cells(x):
            value = 1
            for a, b, c in rows:
                sign = a*xi+b*yi+c*denominator
                if sign < 0:
                    value = -1
                    break
                if sign == 0:
                    value = 0
            if value == 1:
                return 1
            state = max(state, value)
        return state

    def _candidate_cells(self, x):
        """Closed boxes: equality must not discard contact candidates.

        Gate: test_spatial_index_never_omits_an_exact_contact_candidate.
        """
        return (row for row in self._indexed_cells
                if all(lo <= x[k] <= hi for k, (lo, hi) in enumerate(row[0])))

    def topology(self: GlobalEntrance2, x=(0, 0)):
        """-1 outside E, 0 on boundary E, 1 in int E, including tight seams."""
        x = _point(x)
        state = self.membership(x)
        if state != 0:
            return state
        cones, rays = [], set()
        for cell in self.cells:
            if _cell_state(cell, x) < 0:
                continue
            active = tuple(_sub(b, a) for a, b in _edges(cell)
                           if _cross(_sub(b, a), _sub(x, a)) == 0)
            cones.append(active)
            for e in active:
                length = abs(e[0])+abs(e[1])
                u = e[0]/length, e[1]/length
                rays.update((u, (-u[0], -u[1])))
        ordered = []
        for ray in rays:
            index = len(ordered)
            while index and _angular_compare(ordered[index-1], ray) > 0:
                index -= 1
            ordered.insert(index, ray)
        for a, b in _edges(tuple(ordered)):
            direction = a[0]+b[0], a[1]+b[1]
            if direction == (0, 0):
                direction = -a[1], a[0]
            if not any(all(_cross(e, direction) >= 0 for e in cone) for cone in cones):
                return 0
        return 1

    @property
    def cell_edges(self: GlobalEntrance2):
        return self._cell_edges

    def side_probes(self: GlobalEntrance2, a, b):
        """Exact adjacent-face probes, before the nearest supporting-line event."""
        a, b = _point(a), _point(b)
        middle = ((a[0]+b[0])/2, (a[1]+b[1])/2)
        e = _sub(b, a)
        direction = -e[1], e[0]
        if direction == (0, 0):
            raise ValueError("side probes require a nonzero segment")
        step = F(1)
        probe_edges = (tuple(cell.vertices for cell in self._subdivision_cache.edges)
                       if self._compact_subdivision and self._subdivision_cache is not None else self.cell_edges)
        for p, q in probe_edges:
            edge = _sub(q, p)
            h, slope = _cross(edge, _sub(middle, p)), _cross(edge, direction)
            if h and slope:
                step = min(step, abs(h/slope)/2)
        return _at(middle, direction, step), _at(middle, direction, -step)

    @property
    def clipped_covers(self: GlobalEntrance2):
        if self._clipped_covers_cache is not None:
            return self._clipped_covers_cache
        from .exact import ve_side_exact, ev_side_exact
        raw = []
        for i, a in enumerate(self.A):
            for j, b in enumerate(self.B):
                if ve_side_exact(self.A, i, self.B, j) >= 0:
                    raw.append((("VE", i, j), _sub(b, a), _sub(self.B[(j+1) % len(self.B)], a)))
                if ev_side_exact(self.A, i, self.B, j) >= 0:
                    raw.append((("EV", i, j), _sub(b, a), _sub(b, self.A[(i+1) % len(self.A)])))
        result = []
        for label, a, b in raw:
            cuts = {F(0), F(1)}
            for c, d in self.cell_edges:
                cuts.update(_cuts(a, b, c, d))
            values, direction = sorted(cuts), _sub(b, a)
            for lo, hi in zip(values, values[1:]):
                p, q = _at(a, direction, lo), _at(a, direction, hi)
                probes = self.side_probes(p, q)
                states = tuple(self.membership(x) for x in probes)
                exposed = (states[0] >= 0) != (states[1] >= 0)
                middle = ((p[0]+q[0])/2, (p[1]+q[1])/2)
                result.append(CoverPiece2(label, p, q, exposed, self.membership(middle), probes, states))
        self._clipped_covers_cache = tuple(result)
        return self._clipped_covers_cache

    @property
    def boundary(self: GlobalEntrance2):
        """Boundary from the global convex union, independent of local covers.

        Every union-boundary point belongs to a cell boundary. Splitting all
        cell edges and retaining different adjacent E labels is therefore a
        complete construction, even without a local-cover completeness lemma.
        Gate: test_local_clipping_covers_the_independently_built_cell_boundary.
        """
        if self._boundary_cache is not None:
            return self._boundary_cache
        result = []
        for a, b in _split_segments(self.cell_edges):
            p, q = self.side_probes(a, b)
            if (self.membership(p) >= 0) != (self.membership(q) >= 0):
                result.append((a, b))
        self._boundary_cache = tuple(result)
        return self._boundary_cache

    @property
    def subdivision(self: GlobalEntrance2):
        """Exact vertical decomposition of the finite cell-union bounding box.

        Every relative-open 0/1/2-cell has the O/E body label. Exterior to the
        bounding rectangle is represented implicitly by exterior_state=-1.
        Gate: test_subdivision_has_all_dimensions_and_exact_oracle_labels.
        """
        if self._subdivision_cache is not None:
            return self._subdivision_cache
        if self._compact_subdivision:
            return self._contact_subdivision()
        split = _split_segments(self.cell_edges)
        xs = sorted({p[0] for segment in split for p in segment})
        faces, face_edges = [], set()
        for left, right in zip(xs, xs[1:]):
            middle = (F(left)+F(right))/2
            levels = {}
            for a, b in self.cell_edges:
                if min(a[0], b[0]) < middle < max(a[0], b[0]):
                    level = _y_at(a, b, middle)
                    left_y, right_y = _y_at(a, b, left), _y_at(a, b, right)
                    levels[level] = (left_y, right_y)
            ordered = sorted(levels)
            for low, high in zip(ordered, ordered[1:]):
                lo, hi = levels[low], levels[high]
                ring = ((left, lo[0]), (right, lo[1]), (right, hi[1]), (left, hi[0]))
                ring = tuple(p for i, p in enumerate(ring) if p != ring[i-1])
                sample = middle, (low+high)/2
                faces.append(Cell2(ring, sample, self.membership(sample)))
                face_edges.update(tuple(sorted((a, b))) for a, b in _edges(ring))
        # Include bounding-box faces outside the y-range at a given slab by
        # letting the finite enclosure use the global minimum/maximum y.
        ymin = min(p[1] for e in self.cell_edges for p in e)
        ymax = max(p[1] for e in self.cell_edges for p in e)
        for left, right in zip(xs, xs[1:]):
            middle = (F(left)+F(right))/2
            slab = [f for f in faces if f.sample[0] == middle]
            bottom = min(slab, key=lambda f: f.sample[1]).vertices
            top = max(slab, key=lambda f: f.sample[1]).vertices
            for bound, ring, above in ((ymin, bottom, False), (ymax, top, True)):
                values = [(p[0], p[1]) for p in ring]
                if above:
                    ly = max(y for x, y in values if x == left)
                    ry = max(y for x, y in values if x == right)
                else:
                    ly = min(y for x, y in values if x == left)
                    ry = min(y for x, y in values if x == right)
                polygon = ((left, bound), (right, bound), (right, ry), (left, ly))
                polygon = tuple(p for i, p in enumerate(polygon) if p != polygon[i-1])
                if len(polygon) >= 3:
                    sample = middle, (bound+(ly+ry)/2)/2
                    faces.append(Cell2(polygon, sample, self.membership(sample)))
                    face_edges.update(tuple(sorted((a, b))) for a, b in _edges(polygon))
        segments = _split_segments(tuple(face_edges))
        edges = tuple(Cell2((a, b), ((a[0]+b[0])/2, (a[1]+b[1])/2),
                            self.membership(((a[0]+b[0])/2, (a[1]+b[1])/2))) for a, b in segments)
        vertices = tuple(Cell2((p,), p, self.membership(p)) for p in sorted({p for e in segments for p in e}))
        self._subdivision_cache = Subdivision2(vertices, edges, tuple(faces))
        return self._subdivision_cache

    def _contact_subdivision(self: GlobalEntrance2):
        """Complete labelled subdivision after deleting strictly-overlap strata.

        All VE/EV contact segments (not just locally valid ones) are arranged
        before removing state-1 open edges; state-0 vertices are retained even
        if isolated. No E\\O point is omitted: a nonpenetrating intersection is
        a boundary contact, hence VE/EV or an endpoint of such a segment.
        Gates: test_contact_skeleton_subdivision_checks_every_stratum and
        test_contact_skeleton_preserves_an_isolated_tight_contact.
        """
        raw = set()
        for a in self.A:
            raw.update(tuple(sorted((_sub(b, a), _sub(c, a)))) for b, c in _edges(self.B))
        for b in self.B:
            raw.update(tuple(sorted((_sub(b, a), _sub(b, c)))) for a, c in _edges(self.A))
        arranged = _split_segments(tuple(raw))
        contacts = tuple((a, b) for a, b in arranged
                         if self.membership(((a[0]+b[0])/2, (a[1]+b[1])/2)) == 0)
        contact_points = {p for e in arranged for p in e if self.membership(p) == 0}
        if not contacts:
            raise ArithmeticError("contact skeleton has no boundary edges")
        self._contact_edges = contacts
        xs = sorted({p[0] for p in contact_points})
        ymin = min(p[1] for p in contact_points)
        ymax = max(p[1] for p in contact_points)
        faces, face_edges = [], set()
        for left, right in zip(xs, xs[1:]):
            middle = (left+right)/2
            levels = {ymin: (ymin, ymin), ymax: (ymax, ymax)}
            for a, b in contacts:
                if min(a[0], b[0]) < middle < max(a[0], b[0]):
                    level = _y_at(a, b, middle)
                    left_y, right_y = _y_at(a, b, left), _y_at(a, b, right)
                    levels[level] = (left_y, right_y)
            ordered = sorted(levels)
            for low, high in zip(ordered, ordered[1:]):
                lo, hi = levels[low], levels[high]
                ring = ((left, lo[0]), (right, lo[1]), (right, hi[1]), (left, hi[0]))
                ring = tuple(p for i, p in enumerate(ring) if p != ring[i-1])
                sample = middle, (low+high)/2
                faces.append(Cell2(ring, sample, self.membership(sample)))
                face_edges.update(tuple(sorted((a, b))) for a, b in _edges(ring))
        segments = _split_segments(tuple(face_edges))
        # State-0 isolated points may be inside a vertical event wall; insert
        # them explicitly, rather than silently regularizing O into int E.
        split = []
        for a, b in segments:
            values = sorted({a, b} | {p for p in contact_points if _on(p, a, b)})
            split.extend(zip(values, values[1:]))
        edges = tuple(Cell2((a, b), ((a[0]+b[0])/2, (a[1]+b[1])/2),
                            self.membership(((a[0]+b[0])/2, (a[1]+b[1])/2))) for a, b in split)
        vertices = tuple(Cell2((p,), p, self.membership(p)) for p in sorted({p for e in split for p in e}))
        self._subdivision_cache = Subdivision2(vertices, edges, tuple(faces))
        return self._subdivision_cache

    def ray_intervals(self: GlobalEntrance2, x, direction, *, strict=False):
        """Full-line convex-cell intervals. Open intervals retain distinct endpoints."""
        x, direction = _point(x), _point(direction)
        if direction == (0, 0):
            raise ValueError("direction must be nonzero")
        intervals = []
        for cell in self.cells:
            low, high = None, None
            for a, b in _edges(cell):
                e = _sub(b, a)
                h, slope = _cross(e, _sub(x, a)), _cross(e, direction)
                if slope > 0:
                    root = -h/slope
                    low = root if low is None else max(low, root)
                elif slope < 0:
                    root = -h/slope
                    high = root if high is None else min(high, root)
                elif h < 0 or (strict and h == 0):
                    break
            else:
                if low is not None and high is not None and (low < high if strict else low <= high):
                    intervals.append((low, high))
        return tuple(sorted(intervals))

    def first_entrance(self: GlobalEntrance2, x, direction, *, t_max=None):
        """First point of closed E on a forward ray; initial E gives time zero."""
        x, direction = _point(x), _point(direction)
        bound = None if t_max is None else F(t_max)
        if bound is not None and bound < 0:
            raise ValueError("t_max must be nonnegative")
        roots = [max(F(0), lo) for lo, hi in self.ray_intervals(x, direction)
                 if hi >= 0 and (bound is None or max(F(0), lo) <= bound)]
        if not roots:
            return None
        time = min(roots)
        return RayHit2(time, _at(x, direction, time))

    def _nearest_boundary(self: GlobalEntrance2, x):
        values = []
        for a, b in self.boundary:
            e, v = _sub(b, a), _sub(x, a)
            denominator = e[0]*e[0]+e[1]*e[1]
            t = min(F(1), max(F(0), (v[0]*e[0]+v[1]*e[1])/denominator))
            p = _at(a, e, t)
            square = (p[0]-x[0])**2+(p[1]-x[1])**2
            values.append((square, p))
        if not values:
            raise ArithmeticError("global boundary is empty")
        square, p = min(values)
        tied = tuple(sorted({q for distance, q in values if distance == square}))
        return Distance2(square, p, tied)

    def distance_to_e(self: GlobalEntrance2, x):
        """Distance to closed E. Gate: test_distance_to_e_matches_independent_features."""
        x = _point(x)
        return Distance2(F(0), x, (x,)) if self.membership(x) >= 0 else self._nearest_boundary(x)

    def shortest_exit(self: GlobalEntrance2, x):
        """PD_closed infimum and nearest boundary point, not PD_open.

        Boundary is a contact configuration, not a strictly separated one.
        Gate: test_global_shortest_exit_distinguishes_tight_contact_seam.
        """
        x = _point(x)
        if self.membership(x) < 0:
            raise ValueError("shortest exit requires a point of E")
        return self._nearest_boundary(x)


@lru_cache(maxsize=64)
def _cached(A, B):
    return GlobalEntrance2(A, B)


def global_entrance(A, B):
    """Reusable exact global construction; inputs are copied to immutable tuples."""
    return _cached(tuple(_point(p) for p in A), tuple(_point(p) for p in B))
