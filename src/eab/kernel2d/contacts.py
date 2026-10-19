"""Exact pointwise contact assembly for polygonal rigid bodies.

Only raw vertex/edge incidences at zero displacement are enumerated.  A point's
free cone is computed from its two material cones, not from the whole body pair
or a clipped entrance boundary.  Nonconvex point cones are retained unless an
exact homogeneous feasibility test proves their forbidden open cone unreachable
in the actual masked rigid-body twist coordinates.  No mode enumeration occurs.

The mechanical profile is rigid, infinitesimal, noncohesive, unlimited in
compression, and associated-flow.  Its limit analysis is an unsafe-side upper
bound relative to nonassociated Coulomb friction; this module supplies only the
normal, nondilatant geometry constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import combinations, product

from eab import lp
from .exact import polygons_overlap_exact

from .assembly import Assembly2


def _sub(a: tuple[Fraction, Fraction], b: tuple[Fraction, Fraction]) -> tuple[Fraction, Fraction]:
    return (a[0] - b[0], a[1] - b[1])


def _neg(a: tuple[Fraction, Fraction]) -> tuple[Fraction, Fraction]:
    return (-a[0], -a[1])


def _cross(a: tuple[Fraction, Fraction], b: tuple[Fraction, Fraction]) -> Fraction:
    return a[0] * b[1] - a[1] * b[0]


def _dot(a: tuple[Fraction, Fraction], b: tuple[Fraction, Fraction]) -> Fraction:
    return a[0] * b[0] + a[1] * b[1]


def _rot(a: tuple[Fraction, Fraction]) -> tuple[Fraction, Fraction]:
    return (-a[1], a[0])


def _ray(a: tuple[Fraction, Fraction]) -> tuple[Fraction, Fraction]:
    scale = abs(a[0]) + abs(a[1])
    return (Fraction(a[0]) / scale, Fraction(a[1]) / scale)


def _on(p: tuple[Fraction, Fraction], a: tuple[Fraction, Fraction], b: tuple[Fraction, Fraction]) -> bool:
    return _cross(_sub(p, a), _sub(b, a)) == 0 and _dot(_sub(p, a), _sub(p, b)) <= 0


def _angle_cmp(a: tuple[Fraction, Fraction], b: tuple[Fraction, Fraction]) -> int:
    ha = 0 if a[1] > 0 or (a[1] == 0 and a[0] > 0) else 1
    hb = 0 if b[1] > 0 or (b[1] == 0 and b[0] > 0) else 1
    if ha != hb:
        return -1 if ha < hb else 1
    turn = _cross(a, b)
    return -1 if turn > 0 else 1 if turn < 0 else 0


@dataclass(frozen=True)
class ExactContact2:
    """One action/reaction pair; rot90(tangent) points into body a.

    Tangents are original directed edge vectors, never unit vectors.  All raw
    incidences at the point remain in sources, including endpoint associations
    which do not themselves generate a constraint.
    """

    a: int
    b: int
    point: tuple[Fraction, Fraction]
    tangent: tuple[Fraction, Fraction]
    sources: tuple
    label: tuple

    @property
    def normal(self) -> tuple[Fraction, Fraction]:
        return _rot(self.tangent)


@dataclass(frozen=True)
class ContactPoint2:
    """Local geometric cone and separate retention in the resolved constraint set.

    ``boundaries`` describes the point cone even when ``retained`` is false.
    Interior flat incidences of a maximal collinear segment are represented by
    its two endpoints. True vertex disjunctions are never force constraints;
    their unresolved/proved distinction remains in ``fp_type``.
    """
    a: int
    b: int
    point: tuple[Fraction, Fraction]
    fp_type: str
    boundaries: tuple[tuple[Fraction, Fraction], ...]
    sources: tuple
    forbidden: tuple[tuple[tuple[Fraction, Fraction], ...], ...]
    retained: bool = False


@dataclass(frozen=True)
class ContactSegment2:
    a: int
    b: int
    start: tuple[Fraction, Fraction]
    end: tuple[Fraction, Fraction]
    tangent: tuple[Fraction, Fraction]
    sources: tuple


@dataclass(frozen=True)
class ConeReachability2:
    """Exact alternative for H v >= rhs in free twist coordinates.

    If unreachable, multipliers >= 0 satisfy H.T multipliers = 0 and
    rhs.T multipliers = 1.  The last forbidden-cone rows have rhs=1: positive
    homogeneity makes this equivalent to strictly positive penetration without
    any epsilon.  A reachable result instead gives an exact twist witness.
    """

    point: ContactPoint2
    dofs: tuple
    matrix: tuple
    rhs: tuple
    unreachable: bool
    multipliers: tuple | None = None
    twist: tuple | None = None


@dataclass(frozen=True)
class ContactSet2:
    assembly: Assembly2
    constraints: tuple[ExactContact2, ...]
    points: tuple[ContactPoint2, ...]
    raw_sources: tuple
    unresolved: tuple[ContactPoint2, ...]
    redundancy_certificates: tuple[ConeReachability2, ...]
    status: str | None
    call_status: str
    mathematical_status: str
    completeness: str
    reason: str | None = None
    segments: tuple[ContactSegment2, ...] = ()
    pair_states: tuple = ()
    reachable_witnesses: tuple[ConeReachability2, ...] = ()


def _halfplane(edge: tuple[Fraction, Fraction]) -> tuple[tuple[Fraction, Fraction], ...]:
    return (edge, _neg(edge), _rot(edge))


def _material_pieces(poly, p):
    """Full-dimensional convex pieces of the local material cone at p."""
    for i, v in enumerate(poly):
        if v == p:
            before = _sub(v, poly[i - 1])
            after = _sub(poly[(i + 1) % len(poly)], v)
            turn = _cross(before, after)
            if turn > 0:
                return ((after, _neg(before)),)
            if turn == 0:
                return (_halfplane(after),)
            return (_halfplane(before), _halfplane(after))
    for i, v in enumerate(poly):
        edge = _sub(poly[(i + 1) % len(poly)], v)
        if _on(p, v, poly[(i + 1) % len(poly)]):
            return (_halfplane(edge),)
    raise ValueError("point is not on the polygon boundary")


def _cone_normals(gens):
    """Inward extreme normals of a full-dimensional generated convex cone."""
    normals = {}
    for g in gens:
        for n in (_rot(g), _neg(_rot(g))):
            if all(_dot(n, h) >= 0 for h in gens):
                normals.setdefault(_ray(n), n)
    return tuple(normals[k] for k in sorted(normals))


def _samples(normals):
    directions = set()
    for n in normals:
        directions.update((_ray(_rot(n)), _ray(_neg(_rot(n)))))
    rays = []
    for d in directions:
        i = 0
        while i < len(rays) and _angle_cmp(rays[i], d) < 0:
            i += 1
        rays.insert(i, d)
    samples = list(rays)
    for a, b in zip(rays, rays[1:] + rays[:1]):
        if _cross(a, b) > 0:
            samples.append((a[0] + b[0], a[1] + b[1]))
        else:
            samples.append(_rot(a))
    return tuple(samples)


def _free_direction(forbidden, d):
    return not any(all(_dot(n, d) > 0 for n in cone) for cone in forbidden)


def _point_cone(pa, pb, p):
    forbidden = []
    for ca, cb in product(_material_pieces(pa, p), _material_pieces(pb, p)):
        normals = _cone_normals((*cb, *(_neg(v) for v in ca)))
        if normals not in forbidden:
            forbidden.append(normals)
    forbidden = tuple(forbidden)
    all_normals = tuple(n for cone in forbidden for n in cone)
    samples = _samples(all_normals)
    free = tuple(d for d in samples if _free_direction(forbidden, d))
    kept = {}
    for n in all_normals:
        normal = _neg(n)
        if free and all(_dot(normal, d) >= 0 for d in free) and any(_dot(normal, d) == 0 for d in free):
            kept.setdefault(_ray(normal), normal)
    boundaries = tuple(kept[k] for k in sorted(kept))
    convex = bool(free) and all(
        _free_direction(forbidden, d) == all(_dot(n, d) >= 0 for n in boundaries)
        for d in samples
    )
    return ("CONVEX" if convex else "TRUE_VV", boundaries, forbidden)


def _raw_pair(pa, pb, a, b, ids_a=(), ids_b=()):
    """All zero-displacement original VE/EV incidences, including endpoints."""
    by_point = {}
    ids_a = ids_a or tuple(range(len(pa)))
    ids_b = ids_b or tuple(range(len(pb)))
    for i, p in enumerate(pa):
        for j, q in enumerate(pb):
            if _on(p, q, pb[(j + 1) % len(pb)]):
                by_point.setdefault(p, set()).add(("VE", a, ids_a[i], b, (ids_b[j], ids_b[(j + 1) % len(pb)])))
    for j, p in enumerate(pb):
        for i, q in enumerate(pa):
            if _on(p, q, pa[(i + 1) % len(pa)]):
                by_point.setdefault(p, set()).add(("EV", a, (ids_a[i], ids_a[(i + 1) % len(pa)]), b, ids_b[j]))
    return by_point


def _segments(pa, pb, a, b, ids_a=(), ids_b=(), body_ids=()):
    ids_a = ids_a or tuple(range(len(pa)))
    ids_b = ids_b or tuple(range(len(pb)))
    body_ids = body_ids or (a, b)
    found = []
    for i, p in enumerate(pa):
        q = pa[(i + 1) % len(pa)]
        e = _sub(q, p)
        for j, u in enumerate(pb):
            v = pb[(j + 1) % len(pb)]
            if _cross(e, _sub(v, u)) or _cross(e, _sub(u, p)):
                continue
            ends = sorted({w for w in (p, q, u, v) if _on(w, p, q) and _on(w, u, v)})
            if len(ends) >= 2 and ends[0] != ends[-1]:
                found.append([ends[0], ends[-1], e, {("EE", body_ids[0], (ids_a[i], ids_a[(i + 1) % len(pa)]), body_ids[1], (ids_b[j], ids_b[(j + 1) % len(pb)]))}])
    changed = True
    while changed:
        changed = False
        for i, j in combinations(range(len(found)), 2):
            s, t = found[i], found[j]
            if _cross(s[2], t[2]) or _cross(s[2], _sub(t[0], s[0])):
                continue
            if max(s[0], t[0]) <= min(s[1], t[1]):
                found[i] = [min(s[0], t[0]), max(s[1], t[1]), s[2], s[3] | t[3]]
                del found[j]
                changed = True
                break
    return tuple(ContactSegment2(a, b, s[0], s[1], s[2], tuple(sorted(s[3]))) for s in sorted(found, key=lambda v: (v[0], v[1])))


def _edge_candidates(pa, pb, p):
    out = []
    for side, poly in enumerate((pa, pb)):
        for i, v in enumerate(poly):
            end = poly[(i + 1) % len(poly)]
            if _on(p, v, end):
                e = _sub(end, v)
                out.append((e if side == 0 else _neg(e), side, i))
    return tuple(out)


def _point_constraints(point, pa, pb, segments, ids_a=(), ids_b=(), body_ids=()):
    ids_a = ids_a or tuple(range(len(pa)))
    ids_b = ids_b or tuple(range(len(pb)))
    body_ids = body_ids or (point.a, point.b)
    out = []
    for n in point.boundaries:
        # A straight segment's interior incidence remains provenance, not an
        # extra force application point.  Endpoints of maximal segments suffice.
        if any(point.point not in (s.start, s.end) and _on(point.point, s.start, s.end)
               and _cross(n, _rot(s.tangent)) == 0 for s in segments):
            continue
        for tangent, side, edge in _edge_candidates(pa, pb, point.point):
            if _cross(n, _rot(tangent)) == 0 and _dot(n, _rot(tangent)) > 0:
                ids = ids_a if side == 0 else ids_b
                label = (body_ids[0], body_ids[1], point.point, body_ids[side], (ids[edge], ids[(edge + 1) % len(ids)]))
                out.append(ExactContact2(point.a, point.b, point.point, tangent, point.sources, label))
                break
        else:
            raise RuntimeError("free-cone boundary lacks an incident directed edge")
    return out


def _dofs(assembly):
    return tuple((i, k) for i, body in enumerate(assembly.bodies)
                 for k in range(3) if body.boundary_type != "FIXED_BODY" and body.dof_mask[k])


def _velocity_row(assembly, a, b, p, normal, dofs):
    out = []
    for i, k in dofs:
        if i not in (a, b):
            out.append(Fraction(0))
            continue
        sign = 1 if i == a else -1
        value = normal[k] if k < 2 else _cross(_sub(p, assembly.bodies[i].dof_anchor), normal)
        out.append(sign * value)
    return tuple(out)


def constraint_matrix(assembly, constraints):
    """Return exact normal rows and ordered actual free twist coordinates.

    Each row is n dot (v_a(p)-v_b(p)); rotations use the declared dof_anchor,
    including a masked plate's actual kinematic anchor, not its load reference.
    """
    dofs = _dofs(assembly)
    rows = tuple(_velocity_row(assembly, c.a, c.b, c.point, c.normal, dofs) for c in constraints)
    return rows, dofs


def _solve_exact(A, b, c):
    # The zero display candidate deliberately provides no geometric information.
    # The existing LP layer validates it against exact= and solves rationally.
    return lp.solve([[0.0] * len(c) for _ in A], [0.0] * len(b), [0.0] * len(c), exact=(A, b, c))


def _reachable(assembly, constraints, point):
    rows, dofs = constraint_matrix(assembly, constraints)
    if len(point.forbidden) != 1 or not point.forbidden[0]:
        return None
    blocked = tuple(_velocity_row(assembly, point.a, point.b, point.point, n, dofs)
                    for n in point.forbidden[0])
    H = rows + blocked
    rhs = (Fraction(0),) * len(rows) + (Fraction(1),) * len(blocked)
    # Farkas alternative for free v: H.T y=0, rhs.T y=1, y>=0.
    A = [[row[k] for row in H] for k in range(len(dofs))] + [list(rhs)]
    b = [Fraction(0)] * len(dofs) + [Fraction(1)]
    cert = _solve_exact(A, b, [Fraction(0)] * len(H))
    if cert.status == lp.OPTIMAL and cert.exact_x is not None:
        weights = cert.exact_x
        if any(w < 0 for w in weights) or any(sum((v * w for v, w in zip(row, weights)), Fraction(0)) != target for row, target in zip(A, b)):
            raise RuntimeError("unreachable-cone certificate failed exact verification")
        return ConeReachability2(point, dofs, H, rhs, True, weights)
    if cert.status != lp.INFEASIBLE:
        return None
    # Obtain a witness rather than interpreting lack of a certificate as proof.
    size = len(dofs)
    A = [list(row) + [-v for v in row] + [Fraction(-1 if i == j else 0) for j in range(len(H))]
         for i, row in enumerate(H)]
    witness = _solve_exact(A, list(rhs), [Fraction(0)] * (2 * size + len(H)))
    if witness.status == lp.OPTIMAL and witness.exact_x is not None:
        v = tuple(witness.exact_x[k] - witness.exact_x[size + k] for k in range(size))
        if any(sum((h * x for h, x in zip(row, v)), Fraction(0)) < target for row, target in zip(H, rhs)):
            raise RuntimeError("reachable-cone witness failed exact verification")
        return ConeReachability2(point, dofs, H, rhs, False, twist=v)
    return None


def assemble_contact_set2(assembly: Assembly2) -> ContactSet2:
    """Assemble complete raw t=0 contacts and pointwise exact free cones.

    OVERLAP is an illegal initial state, returned without a mechanical status.
    OUTSIDE contributes no incidences.  Boundary endpoint incidences are kept
    only as provenance unless the point free cone supplies that halfplane.
    True vertex/vertex disjunctions are discarded only after the exact actual-
    twist alternative above proves the forbidden open cone unreachable.
    Flat vertices inside maximal collinear segments retain their geometric
    boundaries and sources, but not constraints: endpoint rows span them by
    convex combinations. Gate: test_maximal_collinear_segment_drops_interior_force_point_but_not_sources.
    """
    pairs = assembly.pairs
    if pairs is None:
        pairs = tuple(combinations(range(len(assembly.bodies)), 2))
    canon = sorted({(min(a, b), max(a, b)) for a, b in pairs})
    states = []
    points = []
    constraints = []
    segments = []
    raw = []
    for a, b in canon:
        if a == b or not (0 <= a < b < len(assembly.bodies)):
            return ContactSet2(assembly, (), (), (), (), (), None, "INVALID_INPUT", "UNPROVED", assembly.completeness, "invalid_body_pair")
        pa, pb = assembly.bodies[a].vertices, assembly.bodies[b].vertices
        state = polygons_overlap_exact(pa, pb)
        states.append((a, b, state))
        if state == 1:
            return ContactSet2(assembly, (), (), (), (), (), None, "OK", "OVERLAP", assembly.completeness, "overlap_initial_state", pair_states=tuple(states))
        if state == -1:
            continue
        ba, bb = assembly.bodies[a], assembly.bodies[b]
        sources = {}
        for left, right in sorted(set(pairs)):
            if {left, right} != {a, b}:
                continue
            first, second = assembly.bodies[left], assembly.bodies[right]
            for p, labels in _raw_pair(first.vertices, second.vertices, first.body_id, second.body_id, first.vertex_ids, second.vertex_ids).items():
                sources.setdefault(p, set()).update(labels)
        pair_segments = _segments(pa, pb, a, b, ba.vertex_ids, bb.vertex_ids, (ba.body_id, bb.body_id))
        segments.extend(pair_segments)
        for p in sorted(sources):
            at = tuple(sorted(sources[p]))
            raw.extend(at)
            kind, normals, forbidden = _point_cone(pa, pb, p)
            point = ContactPoint2(a, b, p, kind, normals, at, forbidden)
            if kind == "CONVEX":
                kept = _point_constraints(point, pa, pb, pair_segments, ba.vertex_ids, bb.vertex_ids, (ba.body_id, bb.body_id))
                constraints.extend(kept)
                point = replace(point, retained=bool(kept))
            points.append(point)
    unresolved = []
    certs = []
    witnesses = []
    for i, point in enumerate(points):
        if point.fp_type == "CONVEX":
            continue
        proof = _reachable(assembly, constraints, point)
        if proof is not None and proof.unreachable:
            certs.append(proof)
            points[i] = replace(point, fp_type="REDUNDANT_PROVED")
        else:
            unresolved.append(point)
            if proof is not None:
                witnesses.append(proof)
    status = "MECHANICAL_UNRESOLVED" if unresolved else "RESOLVED"
    return ContactSet2(assembly, tuple(constraints), tuple(points), tuple(sorted(set(raw))), tuple(unresolved),
                       tuple(certs), status, "OK", status, assembly.completeness,
                       "reachable_or_unproved_open_cone" if unresolved else None,
                       tuple(segments), tuple(states), tuple(witnesses))
