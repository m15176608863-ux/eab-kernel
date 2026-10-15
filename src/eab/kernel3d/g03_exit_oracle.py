"""Independent exact closed-E directional exit oracle for intersecting G0.

Import inventory: fractions, itertools, g03_surface_oracle.  Surface winding,
parity, distances and this module's contact-plane events share no primitives
with global_entrance, boundary, covers3 or exact_sweep.  Candidate events are a
superset: no finite-feature/cone filtering can silently omit a boundary event.
"""
from fractions import Fraction as F
from itertools import count
from . import g03_surface_oracle as S


def _features(P):
    vertices = tuple(tuple(F(x) for x in p) for p in P.verts)
    faces = tuple(piece for face in P.faces for piece in S.face_pieces(vertices, tuple(face)))
    edges = tuple(sorted({tuple(sorted((i, j))) for face in faces
                          for i, j in zip(face, face[1:]+face[:1])}))
    planes = []
    for face in faces:
        origin = vertices[face[0]]
        normal = next(S.cross(S.minus(vertices[face[i]], origin), S.minus(vertices[face[i+1]], origin))
                      for i in range(1, len(face)-1)
                      if any(S.cross(S.minus(vertices[face[i]], origin), S.minus(vertices[face[i+1]], origin))))
        planes.append((normal, origin))
    return vertices, tuple(planes), tuple((vertices[i], S.minus(vertices[j], vertices[i])) for i, j in edges)


def contact_planes(A, B):
    av, ap, ae = _features(A)
    bv, bp, be = _features(B)
    rows = set()
    for n, q in bp:
        rows.update((n, S.dot(n, S.minus(q, p))) for p in av)
    for n, p in ap:
        rows.update((n, S.dot(n, S.minus(q, p))) for q in bv)
    for p, u in ae:
        for q, v in be:
            n = S.cross(u, v)
            if any(n):
                rows.add((n, S.dot(n, S.minus(q, p))))
    return tuple(sorted(rows))


def generic_direction(planes):
    for k in count(1):
        direction = (F(1), F(k), F(k*k))
        if all(S.dot(n, direction) for n, h in planes):
            return direction


def closed_exit(A, B, start=(0, 0, 0), *, planes=None, direction=None):
    """Infimum positive translation parameter that leaves closed E.

    The input is assumed in E; returns 0 at an outward-facing starting contact.
    Each consecutive positive contact-plane event interval is classified with
    original-surface separated_distance, including the unbounded last interval.
    """
    planes = contact_planes(A, B) if planes is None else planes
    direction = generic_direction(planes) if direction is None else direction
    start = tuple(F(x) for x in start)
    events = {F(0)}
    for n, height in planes:
        speed = S.dot(n, direction)
        if not speed:
            raise ValueError('exit oracle requires generic direction')
        t = (height-S.dot(n, start))/speed
        if t > 0:
            events.add(t)
    events = sorted(events)
    checks = 0
    for i, lower in enumerate(events):
        t = (lower+events[i+1])/2 if i+1 < len(events) else lower+1
        vertices = tuple(tuple(F(p[k])+start[k]+t*direction[k] for k in range(3)) for p in A.verts)
        checks += 1
        if S.separated_distance(vertices, A.faces, B.verts, B.faces, squared=True) is not None:
            return lower, direction, checks
    raise AssertionError('bounded solids must eventually separate')
