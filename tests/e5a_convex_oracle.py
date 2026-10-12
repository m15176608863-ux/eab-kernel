"""Independent raw-coordinate canonical hull model for migrated convex gates.

Only g03_exact's independent rational hull/planes are used; no geom3 normal,
hull, cache, view, or production canonical numbering routine enters this oracle.
"""
from functools import lru_cache
from types import SimpleNamespace
from eab.kernel3d import g03_exact as Q


@lru_cache(maxsize=256)
def canonical_payload(vertices, hints):
    points, facets, _ = Q.hull(vertices)
    original = {Q.qpoint(p):i for i,p in enumerate(vertices)}
    rings = tuple(tuple(original[points[i]] for i in f) for f in facets)
    extremes = sorted({i for f in rings for i in f})
    def same_cycle(a,b):
        return len(a)==len(b) and any(tuple(a)==tuple(b[k:]+b[:k]) for k in range(len(b)))
    retain = (len(extremes)==len(vertices) and len(rings)==len(hints)
              and all(any(same_cycle(r,h) for h in hints) for r in rings))
    if retain:
        return vertices, hints, (), ()
    remap = {old:new for new,old in enumerate(extremes)}
    ordered = sorted(rings,key=lambda ring:tuple(sorted(ring)))
    return (tuple(vertices[i] for i in extremes),
            tuple(tuple(remap[i] for i in ring) for ring in ordered),
            tuple(extremes),
            tuple(tuple(i for i,hint in enumerate(hints) if set(ring)<=set(hint)) for ring in ordered))


def canonical_view(vertices, faces):
    vertices,faces,sv,sf = canonical_payload(tuple(vertices),tuple(faces))
    return SimpleNamespace(verts=vertices,faces=faces,source_vertices=sv,source_faces=sf)


def assert_raw_coordinate_view(actual, expected):
    assert tuple(actual.verts)==expected.verts, "raw-coordinate convex view lost or reordered extreme vertices"
    assert tuple(frozenset(_mapped_value) for _mapped_value in actual.faces)==tuple(frozenset(_mapped_value) for _mapped_value in expected.faces), "raw-coordinate convex view changed source face numbering"
    assert actual.source_vertices==expected.source_vertices, "raw-coordinate source-vertex map"
    assert actual.source_faces==expected.source_faces, "raw-coordinate source-face map"
