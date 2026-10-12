"""Test-only folded surface cover/distance oracle, independent of production.

Raw rings use the separately implemented projected ear-cut in
e5a2_surface_oracle.  Exact Fraction Gram/projection minimizes all vertex-face
and edge-edge distances.  No production geometry primitive is imported.
"""
from fractions import Fraction
from functools import lru_cache
from types import SimpleNamespace

import e5a_cover_oracle as covers
import e5a2_surface_oracle as geometry


def surface(P):
    return _surface(tuple(P.verts), tuple(P.faces))


@lru_cache(maxsize=64)
def _surface(vertices, faces):
    points = tuple(tuple(map(Fraction, p)) for p in vertices)
    indices = {point: i for i, point in enumerate(points)}
    rings, labels = [], []
    for fi, face in enumerate(faces):
        origin = points[face[0]]
        normal = (0, 0, 0)
        for i, j in zip(face, face[1:] + face[:1]):
            cross = geometry._times(geometry._minus(points[i], origin),
                                    geometry._minus(points[j], origin))
            normal = tuple(normal[k] + cross[k] for k in range(3))
        folded = any(geometry._scalar(normal, geometry._minus(points[i], origin))
                     for i in face)
        if not folded:
            rings.append(face)
            labels.append(("face", fi))
        else:
            for triangle in geometry._ring_triangles(points, face):
                ids = tuple(indices[p] for p in triangle)
                rings.append(ids)
                labels.append(("face", fi, "triangle", *ids))
    return SimpleNamespace(verts=points, faces=tuple(rings)), tuple(labels)


def cover_labels(A, B):
    a, af = surface(A)
    b, bf = surface(B)
    answer = set()
    for (kind, fa, fb), strict in covers.cover_labels(a, b):
        if fa[0] == "face":
            fa = af[fa[1]]
        if fb[0] == "face":
            fb = bf[fb[1]]
        answer.add(((kind, fa, fb), strict))
    return answer


def distance_squared(A, B):
    a, _ = surface(A)
    b, _ = surface(B)
    aa = [tri for face in a.faces for tri in geometry._ring_triangles(a.verts, face)]
    bb = [tri for face in b.faces for tri in geometry._ring_triangles(b.verts, face)]
    ae = {tuple(sorted((p, q))) for tri in aa for p, q in zip(tri, tri[1:] + tri[:1])}
    be = {tuple(sorted((p, q))) for tri in bb for p, q in zip(tri, tri[1:] + tri[:1])}
    values = [geometry._point_tri_sq(p, tri) for p in a.verts for tri in bb]
    values.extend(geometry._point_tri_sq(p, tri) for p in b.verts for tri in aa)
    values.extend(geometry._edge_edge_sq(p, q, u, v) for p, q in ae for u, v in be)
    return min(values)
