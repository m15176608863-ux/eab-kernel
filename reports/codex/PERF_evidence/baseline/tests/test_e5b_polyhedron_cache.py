"""Content invalidation; analytic bounds are independent of production.

The membership oracle uses a known interior point / disjoint x interval of
the constructed body, not production hull or predicate helpers.
"""
import inspect
import textwrap

import pytest

from eab.kernel3d import geom3 as G


def _noncanonical_translation_check():
    p = G.box()
    p.verts[6] = (1., 1., 1.25)
    old = G.exact_convex_view(p)
    assert old is not p
    assert G.exact_point_in_convex_polyhedron((0., 0., 0.), p) == 1
    p.verts[:] = [(x + 10., y, z) for x, y, z in p.verts]
    assert G.exact_point_in_convex_polyhedron((0., 0., 0.), p) == -1, 'vertex-content invalidation'
    assert G.exact_point_in_convex_polyhedron((10., 0., 0.), p) == 1
    assert G.exact_convex_view(p) is not old


def test_noncanonical_convex_view_is_not_reused_after_inplace_vertex_edit():
    _noncanonical_translation_check()


def test_all_cached_geometry_tracks_vertex_and_face_content():
    p = G.box()
    def observations(body):
        return (body.metrics(), body.face_normal(1), body.face_noise(1),
                body.vertex_edges(6), body.edges(), body.vertex_faces(6),
                body.edge_faces((0, 1)), body.edge_traversals((0, 1)),
                body.interior_point())
    observations(p)
    p.verts[6] = (1., 1., 1.25)
    p.faces[1] = p.faces[1][1:] + p.faces[1][:1]
    fresh = G.Polyhedron([tuple(v) for v in p.verts], [tuple(f) for f in p.faces])
    assert observations(p) == observations(fresh), 'all-content caches'
    old = G.exact_convex_view(p)
    p.faces[1] = p.faces[1][1:] + p.faces[1][:1]
    assert G.exact_convex_view(p) is not old, 'face-content invalidation'


def test_cache_vertex_signature_mutation_is_caught(monkeypatch):
    source = textwrap.dedent(inspect.getsource(G.Polyhedron._sync_geometry_cache))
    needle = 'tuple(tuple(p) for p in self.verts)'
    assert source.count(needle) == 1
    namespace = {}
    exec(compile(source.replace(needle, '()'), '<cache-key-without-vertices>', 'exec'), namespace)
    monkeypatch.setattr(G.Polyhedron, '_sync_geometry_cache', namespace['_sync_geometry_cache'])
    with pytest.raises(AssertionError, match='vertex-content invalidation'):
        _noncanonical_translation_check()
