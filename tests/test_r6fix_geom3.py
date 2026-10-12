"""R6 geometry regressions; analytic oracles share no production primitives.

Box membership uses coordinate intervals, concavity uses the roof-midpoint
witness, and vertical escape uses independent interval endpoints. Mutation
checks replace an implementation inside the actual path, never its output.
"""
from fractions import Fraction as F
import inspect
import math
import textwrap

import pytest

from eab.kernel3d import geom3 as G
from eab.kernel3d import interlock as I
from eab.kernel3d.exact_sweep import translate_exact
from eab.kernel3d.covers3 import membership_convex3


def _triangulated_box():
    p = G.box(half=(1, 1, 1))
    return G.Polyhedron(list(p.verts),
                        [t for f in p.faces for t in
                         ((f[0], f[1], f[2]), (f[0], f[2], f[3]))])


def _assert_returned_view_isolation():
    p = _triangulated_box()
    source = (tuple(p.verts), tuple(p.faces))
    view = G.exact_convex_view(p)
    assert view is not p
    view.verts[:] = [(x + 100, y, z) for x, y, z in view.verts]
    assert (tuple(p.verts), tuple(p.faces)) == source
    assert G.exact_point_in_convex_polyhedron((0, 0, 0), p) == 1, 'source-membership-isolated'
    assert G.exact_convex_overlap(p, G.box(half=(.5, .5, .5))) == 1, 'source-overlap-isolated'


def test_g6f01_convex_view_mutation_cannot_poison_unchanged_source():
    _assert_returned_view_isolation()


@pytest.mark.parametrize('name,args', [
    ('edges', ()), ('vertex_faces', (0,)), ('edge_faces', ((0, 1),)),
    ('edge_traversals', ((0, 1),)), ('vertex_edges', (0,)),
])
def test_g6f01_topology_cache_results_are_isolated(name, args):
    p = G.box()
    expected = getattr(G.box(), name)(*args)
    received = getattr(p, name)(*args)
    received.clear()
    assert getattr(p, name)(*args) == expected, 'topology-result-isolated'


def _assert_face_hints_do_not_change_convex_membership(mode):
    p = G.box(half=(1, 1, 1))
    if mode == 'reverse':
        p.faces[1] = tuple(reversed(p.faces[1]))
    elif mode == 'crossed':
        a, b, c, d = p.faces[1]
        p.faces[1] = (a, c, b, d)
    elif mode == 'cycle':
        p.faces[1] = p.faces[1][1:] + p.faces[1][:1]
    else:
        p.faces = []
    assert G.exact_point_in_convex_polyhedron((0, 0, 0), p) == 1, 'convex-point-ignores-face-hints'
    assert membership_convex3(G.box(half=(.5, .5, .5)), p, (0, 0, 0)) == 1, 'convex-E-ignores-face-hints'


@pytest.mark.parametrize('mode', ['reverse', 'crossed', 'cycle', 'empty'])
def test_g6f02_convex_model_is_independent_of_face_hint_winding(mode):
    _assert_face_hints_do_not_change_convex_membership(mode)


def _prism(eps, translation=F(0), scale=F(1), floating=False):
    ring = [(F(0), F(0)), (F(2), F(0)), (F(2), F(1)),
            (F(1), F(1) - eps), (F(0), F(1))]
    n = len(ring)
    verts = [(translation + scale*x, scale*y, scale*z)
             for y in (F(-1), F(1)) for x, z in ring]
    if floating:
        verts = [tuple(map(float, p)) for p in verts]
    faces = [tuple(range(n)), tuple(reversed(range(n, 2*n)))]
    faces += [(i, n+i, n+(i+1) % n, (i+1) % n) for i in range(n)]
    return G.Polyhedron(verts, faces)


def _assert_exact_concavity(eps, translation=F(0), scale=F(1), floating=False):
    p = _prism(eps, translation, scale, floating)
    # Roof peaks belong to the boundary, but their midpoint is strictly above
    # the central roof vertex. This oracle never evaluates face normals.
    assert (p.verts[2][2] + p.verts[4][2])/2 > p.verts[3][2]
    assert not p.is_convex(tol=0), 'exact-midpoint-concavity'
    assert p.reflex_edges(tol=0) == [(3, 8)], 'exact-reflex-edge'


@pytest.mark.parametrize('eps,t,s,floating', [
    (F(1, 2**50), F(0), F(1), False),
    (F(1, 2**50), F(0), F(1), True),
    (F(1, 2**24), F(10**8), F(1), False),
    (F(1, 2**50), F(10**6), F(1, 2**300), False),
    (F(1, 2**50), F(0), F(2**300), False),
])
def test_g6f03_zero_band_convexity_keeps_every_exact_reflex(eps, t, s, floating):
    _assert_exact_concavity(eps, t, s, floating)


def _exact_boxes():
    p = G.box(half=(.5, .5, .5))
    size, origin = F(1, 10**9), F(10**8)
    a = G.Polyhedron([tuple(origin + size*F(x) for x in p0) for p0 in p.verts], list(p.faces))
    b = G.Polyhedron([tuple(origin + size*(F(x) + (F(3, 4) if k == 2 else 0))
                                  for k, x in enumerate(p0)) for p0 in p.verts], list(p.faces))
    return a, b, size


@pytest.mark.parametrize('offset', [(0, 0, 0), (0., 0., 0.), (F(0), 0., 0)])
def test_g6f09_escape_exact_root_is_independent_of_equivalent_offset_types(offset):
    a, b, size = _exact_boxes()
    result = I.escape_height_covers(a, b, offset)
    assert result.exact_height == F(7, 4)*size, 'exact-interval-escape'
    assert result.nonpenetrating_state == 0


@pytest.mark.parametrize('offset', [(0., 0., 0.), (F(0), 0., .125)])
def test_g6f09_mixed_fraction_translation_preserves_exact_affine_coordinates(offset):
    a, _, _ = _exact_boxes()
    expected = [tuple(F(x) + F(d) for x, d in zip(p, offset)) for p in a.verts]
    assert a.translated(offset).verts == expected, 'exact-mixed-affine-translation'


@pytest.mark.parametrize('scale', [2.**-600, 2.**600, F(1, 2**600), F(2**600)])
def test_r6fix_norm_does_not_lose_representable_result_to_intermediate_square(scale):
    assert G.norm((scale, 0, 0)) == float(scale), 'representable-norm'


def test_g6f01_mutation_restoring_cached_alias_is_caught(monkeypatch):
    source = inspect.getsource(G.exact_convex_view)
    needle = 'verts, faces, source_vertices, source_faces = P._convex_view'
    source = source.replace(needle, 'return P._convex_view\n        ' + needle)
    source = source.replace('P._convex_view = (tuple(out.verts), tuple(out.faces), out.source_vertices, out.source_faces)',
                            'P._convex_view = out')
    namespace = dict(vars(G))
    exec(compile(source, '<r6fix-mutation-cached-alias>', 'exec'), namespace)
    monkeypatch.setattr(G, 'exact_convex_view', namespace['exact_convex_view'])
    with pytest.raises(AssertionError, match='source-membership-isolated'):
        _assert_returned_view_isolation()


def test_g6f01_mutation_returning_raw_topology_cache_is_caught(monkeypatch):
    source = textwrap.dedent(inspect.getsource(G.Polyhedron.edges))
    assert source.count('return list(self._edges)') == 1
    namespace = dict(vars(G))
    exec(compile(source.replace('return list(self._edges)', 'return self._edges'),
                 '<r6fix-mutation-topology-alias>', 'exec'), namespace)
    monkeypatch.setattr(G.Polyhedron, 'edges', namespace['edges'])
    with pytest.raises(AssertionError, match='topology-result-isolated'):
        test_g6f01_topology_cache_results_are_isolated('edges', ())


def test_g6f02_mutation_dropping_oriented_ring_check_is_caught(monkeypatch):
    monkeypatch.setattr(G, '_same_oriented_ring', lambda a, b: set(a) == set(b))
    with pytest.raises(AssertionError, match='convex-point-ignores-face-hints'):
        _assert_face_hints_do_not_change_convex_membership('reverse')


def test_g6f03_mutation_restoring_hidden_dihedral_band_is_caught(monkeypatch):
    def noisy_sign(self, e):
        return self.dihedral_turn(e) + self.dihedral_noise(e)
    monkeypatch.setattr(G.Polyhedron, '_exact_dihedral_orientation', noisy_sign)
    with pytest.raises(AssertionError, match='exact-midpoint-concavity'):
        _assert_exact_concavity(F(1, 2**50))


def test_g6f09_mutation_rounding_mixed_translation_is_caught(monkeypatch):
    def old_translated(self, x):
        return G.Polyhedron([G.add(p, x) for p in self.verts], list(self.faces))
    monkeypatch.setattr(G.Polyhedron, 'translated', old_translated)
    with pytest.raises(AssertionError, match='exact-mixed-affine-translation'):
        test_g6f09_mixed_fraction_translation_preserves_exact_affine_coordinates((0., 0., 0.))


def test_r6fix_mutation_rounding_squared_norm_is_caught(monkeypatch):
    monkeypatch.setattr(G, 'norm', lambda a: math.sqrt(G.dot(a, a)))
    with pytest.raises(AssertionError, match='representable-norm'):
        test_r6fix_norm_does_not_lose_representable_result_to_intermediate_square(2.**-600)


def test_r6fix_ray_direction_cache_first_result_is_isolated(monkeypatch):
    monkeypatch.setattr(G, '_RAY_DIRS', [])
    received = G._ray_directions(4)
    expected = list(received)
    received[:] = [(1., 0., 0.)] * 4
    assert G._ray_directions(4) == expected, 'ray-direction-cache-isolated'


def test_r6fix_exact_translation_faces_do_not_alias_source():
    a = G.box()
    expected = list(a.faces)
    translated = translate_exact(a, (1, 2, 3))
    translated.faces.clear()
    assert a.faces == expected, 'translated-faces-isolated'


def test_r6fix_point_segment_distance_keeps_tiny_interior_projection():
    s = 2.**-600
    assert G._point_segment_distance((s/2, s, 0), (0, 0, 0), (s, 0, 0)) == s, 'tiny-segment-distance'


def test_r6fix_segment_distance_keeps_exact_local_difference_at_large_coordinates():
    t, s = F(10**8), F(1, 10**9)
    p, a, b = (t+s/2, t+s, 0), (t, t, 0), (t+s, t, 0)
    assert G._seg_seg_distance(p, p, a, b) == float(s), 'local-segment-distance'


def test_r6fix_face_projection_keeps_exact_in_extent_at_large_coordinates():
    t, s = F(10**8), F(1, 10**9)
    face = G.Polyhedron([(t+s, t+s, t+s), (t+3*s, t+s, t+s), (t+s, t+3*s, t+s)], [(0, 1, 2)])
    p = (t+3*s/2, t+3*s/2, t)
    assert G._point_face_distance(p, face, 0) == float(s), 'exact-face-projection-extent'


def test_r6fix_brute_distance_does_not_subtract_rounded_global_projections():
    a, _, s = _exact_boxes()
    b = a.translated((3*s, 0, 0))
    assert G.brute_feature_distance(a, b) == float(2*s), 'exact-brute-feature-distance'


@pytest.mark.parametrize('t,s', [(F(10**8), F(1, 10**9)), (0., 2.**-600), (0., 2.**600)])
def test_r6fix_closest_points_do_not_drop_nonzero_segments(t, s):
    p, a, b = (t+s/2, t+s, 0), (t, t, 0), (t+s, t, 0)
    expected = (p, (F(t)+F(s)/2, F(t), F(0)))
    assert G._segment_closest_points(p, p, a, b) == expected, 'exact-segment-projection-points'


def test_g6f09_nominal_report_cannot_collapse_float_body_under_large_offset():
    s = 2.**-40
    a = G.box(half=(s/2,)*3)
    b = translate_exact(a, (10**8, 0, F(3)*F(s)/4))
    try:
        result = I.escape_height_covers(a, b, (1e8, 0., 0.))
    except ValueError as error:
        raise AssertionError('exact-large-offset-escape blocked by nominal construction') from error
    assert result.exact_height == F(7)*F(s)/4, 'exact-large-offset-escape'


def test_g6f09_mutation_rounding_nominal_report_before_exact_solve_is_caught(monkeypatch):
    source = inspect.getsource(I._candidates_uncached)
    assert source.count('At = translate_exact(A, offset)') == 1
    namespace = dict(vars(I))
    exec(compile(source.replace('At = translate_exact(A, offset)', 'At = A.translated(offset)'),
                 '<r6fix-mutation-rounded-nominal-body>', 'exec'), namespace)
    monkeypatch.setattr(I, '_candidates_uncached', namespace['_candidates_uncached'])
    with pytest.raises(AssertionError, match='exact-large-offset-escape'):
        test_g6f09_nominal_report_cannot_collapse_float_body_under_large_offset()


@pytest.mark.parametrize('translation', [F(10**3), F(10**5), F(10**6)])
@pytest.mark.parametrize('scale', [F(1, 2**300), F(1), F(2**300)])
def test_g6f03_exact_concavity_survives_rational_rotation_translation_and_units(translation, scale):
    p = _prism(F(1, 2**50), scale=scale)
    # Rational orthogonal rotation keeps supplied-data equivalence exact.
    c, s = F(5, 13), F(12, 13)
    p.verts = [(c*x-s*y+translation, s*x+c*y-3*translation, z+2*translation)
               for x, y, z in p.verts]
    assert not p.is_convex(tol=0), 'rotated-exact-concavity'
    assert p.reflex_edges(tol=0) == [(3, 8)], 'rotated-exact-reflex-edge'
