"""Exact explicit boundary of a finite convex-pair entrance union.

All constructions are Fraction values.  Pair facets are cut by every pair
support plane; only patches with different *closed occupancy* on their two
open sides survive.  Physical touching (0) is not exterior (-1).  The output
is a finite closed polygon cover, not a globally welded manifold mesh.
Theorem and support domain: docs/m3b_boundary3d_design.md.
Gates: tests/test_m3b_boundary3d.py.
"""
from dataclasses import dataclass
from fractions import Fraction as F

from . import global_entrance as G


def _hull(points, normal):
    """Planar exact monotone hull; discard collinear interior vertices only."""
    points = sorted(set(points))
    drop = max(range(3), key=lambda k: abs(normal[k]))
    axes = tuple(k for k in range(3) if k != drop)
    points = [p for projection, p in sorted((tuple(p[k] for k in axes), p) for p in points)]
    def turn(a, b, c):
        u, v = axes
        return (b[u]-a[u])*(c[v]-a[v])-(b[v]-a[v])*(c[u]-a[u])
    def half(rows):
        out = []
        for p in rows:
            while len(out) > 1 and turn(out[-2], out[-1], p) <= 0:
                out.pop()
            out.append(p)
        return out
    result = tuple(half(points)[:-1]+half(points[::-1])[:-1])
    if len(result) < 3:
        return ()
    return result if G._dot(G._normal(result), normal) > 0 else result[::-1]


def _plane(normal, height):
    axis = G._axis(normal)
    k = next(k for k in range(3) if axis[k])
    return axis, F(height)*F(axis[k])/normal[k]


def _split(polygons, normal, height):
    out = []
    for polygon in polygons:
        values = [G._dot(normal, p)-height for p in polygon]
        if min(values) < 0 < max(values):
            out.extend((G._clip_polygon(polygon, normal, height),
                        G._clip_polygon(polygon, normal, height, True)))
        else:
            out.append(polygon)
    return out


def _closed_side(state):
    return state >= 0


@dataclass(frozen=True)
class BoundaryPatch3D:
    polygon: tuple
    normal: tuple
    side_points: tuple
    side_states: tuple
    sources: tuple


@dataclass(frozen=True)
class ExplicitBoundary3D:
    model: G.GlobalEntrance3D
    patches: tuple
    candidate_facets: int
    arranged_patches: int
    planes: tuple
    arrangement: tuple

    def contains(self, point):
        p = G._point(point)
        return any(_in_polygon(p, patch.polygon, patch.normal) for patch in self.patches)

    def shortest_exit(self, point=(0, 0, 0)):
        """Squared PD_closed infimum and all tied rational minimizers.

        The minimizing boundary point still touches; strict closed-set
        separation attains only the distance infimum, not this endpoint.
        """
        point = G._point(point)
        if G.GlobalEntrance3D.classify(self.model, point) < 0:
            raise ValueError('shortest_exit requires a point in closed E')
        candidates = []
        for patch in self.patches:
            n, polygon = patch.normal, patch.polygon
            t = G._dot(n, G._sub(point, polygon[0]))/G._dot(n, n)
            projected = tuple(point[k]-t*n[k] for k in range(3))
            if _in_polygon(projected, polygon, n):
                candidates += [projected]
            for a, b in zip(polygon, polygon[1:]+polygon[:1]):
                d = G._sub(b, a)
                u = max(F(0), min(F(1), G._dot(G._sub(point, a), d)/G._dot(d, d)))
                candidates.append(tuple(a[k]+u*d[k] for k in range(3)))
        rows = [(G._dot(G._sub(p, point), G._sub(p, point)), p) for p in candidates]
        minimum = min(square for square, p in rows)
        return BoundaryDistance3D(minimum, tuple(sorted({p for square, p in rows if square == minimum})))

    def probes(self):
        """Every arranged vertex/edge midpoint/face centre and both event sides."""
        out = {'vertex': set(), 'edge': set(), 'face': set(), 'side': set()}
        for patch in self.arrangement:
            poly = patch.polygon
            out['vertex'].update(poly)
            out['edge'].update(tuple((a[k]+b[k])/2 for k in range(3))
                               for a, b in zip(poly, poly[1:]+poly[:1]))
            out['face'].add(G._mean(poly))
            out['side'].update(patch.side_points)
        return {key: tuple(sorted(value)) for key, value in out.items()}


@dataclass(frozen=True)
class BoundaryDistance3D:
    squared: F
    tied_exact_points: tuple


def _in_polygon(point, polygon, normal):
    if G._dot(normal, G._sub(point, polygon[0])):
        return False
    return all(G._dot(normal, G._cross(G._sub(b, a), G._sub(point, a))) >= 0
               for a, b in zip(polygon, polygon[1:]+polygon[:1]))


def _sides(model, polygon, normal, planes):
    centre = G._mean(polygon)
    events = []
    for n, h in planes:
        speed = G._dot(n, normal)
        if speed:
            event = (h-G._dot(n, centre))/speed
            if event:
                events.append(abs(event))
    step = min(events)/2 if events else F(1)
    points = tuple(tuple(centre[k]+sign*step*normal[k] for k in range(3))
                   for sign in (-1, 1))
    return points, tuple(G.GlobalEntrance3D.classify(model, p) for p in points)


def explicit_boundary(model):
    """Construct all exposed pair-facet pieces, including their closed edges."""
    planes = set()
    candidates = {}
    for i, a in enumerate(model.parts_a):
        for j, b in enumerate(model.parts_b):
            points = {G._sub(y, x) for x in a.vertices for y in b.vertices}
            for normal, low, high in G._pair_slabs(a, b):
                for bound in (low, high):
                    n, h = _plane(normal, bound)
                    planes.add((n, h))
                    polygon = _hull((p for p in points if G._dot(n, p) == h), n)
                    if polygon:
                        key = (n, h, tuple(sorted(polygon)))
                        candidates.setdefault(key, (polygon, []))[1].append((i, j))
    planes = tuple(sorted(planes))
    patches = {}
    arrangement = {}
    arranged = 0
    for (normal, _, _), (polygon, sources) in sorted(candidates.items()):
        pieces = [polygon]
        for n, h in planes:
            pieces = _split(pieces, n, h)
        arranged += len(pieces)
        for piece in pieces:
            side_points, side_states = _sides(model, piece, normal, planes)
            arrangement[tuple(sorted(piece))] = BoundaryPatch3D(
                piece, normal, side_points, side_states, tuple(sources))
            if _closed_side(side_states[0]) == _closed_side(side_states[1]):
                continue
            normal_out = normal if _closed_side(side_states[0]) else tuple(-x for x in normal)
            piece = _hull(piece, normal_out)
            key = tuple(sorted(piece))
            local_sources = sources
            if key in patches:
                previous = patches[key]
                local_sources = sorted(set(previous.sources) | set(sources))
            patches[key] = BoundaryPatch3D(piece, normal_out, side_points, side_states, tuple(local_sources))
    return ExplicitBoundary3D(model, tuple(patches[k] for k in sorted(patches)),
                              len(candidates), arranged, planes,
                              tuple(arrangement[k] for k in sorted(arrangement)))


@dataclass(frozen=True)
class LocalCoverPatch3D:
    label: tuple
    polygon: tuple
    normal: tuple


def _edge_closed(P, edge, direction):
    """Zero-tolerance closed edge wedge in raw Fraction source coordinates."""
    incident = [(face, i, j) for face in P.faces for i, j in zip(face, face[1:]+face[:1])
                if tuple(sorted((i, j))) == tuple(edge)]
    if len(incident) != 2:
        return False
    (face, i, j), (other, _, _) = incident
    t = G._sub(G._point(P.verts[j]), G._point(P.verts[i]))
    n1 = G._normal(tuple(G._point(P.verts[v]) for v in face))
    n2 = G._normal(tuple(G._point(P.verts[v]) for v in other))
    return (G._dot(G._cross(n1, n2), t) > 0 and G._dot(direction, t) == 0
            and G._dot(G._cross(t, n1), direction) >= 0
            and G._dot(G._cross(n2, t), direction) >= 0)


def local_cover_candidates(A, B):
    """VF/FV necessary-condition candidates and closed-valid nonparallel EE.

    Planar simple face rings are required; nonplanar rings must first be
    explicitly triangulated by the caller.  The incident-edge VF/FV test is
    necessary, not a sufficiency claim for arbitrary concave source vertices;
    its candidate superset is subsequently clipped to the global boundary.
    EE uses closed edge wedges; strictness is deliberately not a filter.
    """
    from .covers3 import _qnormal, _qvertex_contains, _qedge
    # Use the cached exact input certificate at this public construction entry
    # too; unreferenced vertex-buffer rows are not physical source features.
    G.convex_decomposition(A)
    G.convex_decomposition(B)
    av, bv = tuple(G._point(p) for p in A.verts), tuple(G._point(p) for p in B.verts)
    out = []
    for V, P, vv, pv, kind in ((A, B, av, bv, 'VF'), (B, A, bv, av, 'FV')):
        for fi, face in enumerate(P.faces):
            normal = _qnormal(P, fi)
            if any(G._dot(normal, G._sub(pv[i], pv[face[0]])) for i in face):
                raise ValueError('boundary local covers require explicitly planar face rings')
            triangles = G._triangulate(pv, (tuple(face),))
            used = sorted({i for ring in V.faces for i in ring})
            for vi in used:
                vertex = vv[vi]
                if _qvertex_contains(V, vi, tuple(-x for x in normal), 0) < 0:
                    continue
                label = (kind, ('vertex', vi), ('face', fi)) if kind == 'VF' else (kind, ('face', fi), ('vertex', vi))
                for triangle in triangles:
                    polygon = tuple(G._sub(p, vertex) if kind == 'VF' else G._sub(vertex, p) for p in triangle)
                    n = normal if kind == 'VF' else tuple(-x for x in normal)
                    out.append(LocalCoverPatch3D(label, _hull(polygon, n), n))
    edges_a = sorted({tuple(sorted((i, j))) for face in A.faces for i, j in zip(face, face[1:]+face[:1])})
    edges_b = sorted({tuple(sorted((i, j))) for face in B.faces for i, j in zip(face, face[1:]+face[:1])})
    for ea in edges_a:
        for eb in edges_b:
            n = G._cross(_qedge(B, eb), _qedge(A, ea))
            if not any(n):
                continue
            for normal in (n, tuple(-x for x in n)):
                if (_edge_closed(B, eb, normal) and
                        _edge_closed(A, ea, tuple(-x for x in normal))):
                    differences = tuple(tuple(F(bv[j][k])-F(av[i][k]) for k in range(3)) for i in ea for j in eb)
                    exact_normal = tuple(F(x) for x in normal)
                    polygon = _hull(differences, exact_normal)
                    out += [LocalCoverPatch3D(('EE', ('edge', *ea), ('edge', *eb)), polygon, exact_normal)]
                    break
    return tuple(out)


def clip_local_covers(boundary, candidates):
    """Intersect each source cover with every coplanar exposed global patch."""
    out = []
    for candidate in candidates:
        for patch in boundary.patches:
            n = patch.normal
            if any(G._dot(n, G._sub(p, patch.polygon[0])) for p in candidate.polygon):
                continue
            polygon = candidate.polygon
            for a, b in zip(patch.polygon, patch.polygon[1:]+patch.polygon[:1]):
                inward = G._cross(n, G._sub(b, a))
                polygon = G._clip_polygon(polygon, inward, G._dot(inward, a), True)
                if not polygon:
                    break
            if polygon:
                out.append(LocalCoverPatch3D(candidate.label, _hull(polygon, n), n))
    return tuple(out)
