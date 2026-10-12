"""R9 topology gates with independent Cartesian solid and shell-depth oracles.

Truth uses only the explicit roof equation, coordinate intervals, and the known
nesting order of cubes. No production triangulator, normal, convexity, volume,
membership, or cone primitive is used to construct an expected result.
"""
from fractions import Fraction as F
import inspect
import math
import textwrap

import pytest

from eab.kernel3d import geom3 as G


FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def _folded_roof(h=F(1, 2), scale=F(1), translated=False, rotated=False):
    raw = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
           (0, 0, 1), (1, 0, 1), (1, 1, 1 + h), (0, 1, 1)]
    def inside(p):
        x, y, z = p
        return 0 <= x <= 1 and 0 <= y <= 1 and 0 <= z <= 1 + h*max(0, x+y-1)
    midpoint = (F(1, 2), F(1, 2), 1+h/2)
    assert inside(raw[4]) and inside(raw[6]) and not inside(midpoint)
    shift = (10**8, -2*10**8, 3*10**8) if translated else (0, 0, 0)
    def transform(p):
        x, y, z = (F(_r12_item) for _r12_item in p)
        if rotated:
            x, y = (3*x-4*y)/5, (4*x+3*y)/5
        return tuple(F(t) + scale*c for t, c in zip(shift, (x, y, z)))
    return G.Polyhedron([transform(p) for p in raw], list(FACES))


@pytest.mark.parametrize('h', [F(1, 2), F(1, 2**80)])
@pytest.mark.parametrize('scale', [F(1), F(1, 2**30), F(2**30)])
@pytest.mark.parametrize('translated,rotated', [(False, False), (False, True),
                                               (True, False), (True, True)])
def test_g6i02_declared_folded_surface_is_not_convex(h, scale, translated, rotated):
    p = _folded_roof(h, scale, translated, rotated)
    assert p.is_convex(0) is False, 'declared-roof-midpoint-concavity'


@pytest.mark.parametrize('h', [F(1, 2), F(1, 2**80)])
@pytest.mark.parametrize('scale', [F(1), F(1, 2**30), F(2**30)])
@pytest.mark.parametrize('translated,rotated', [(False, False), (False, True),
                                               (True, False), (True, True)])
def test_g6i02_reflex_edges_include_declared_internal_ridge(h, scale, translated, rotated):
    p = _folded_roof(h, scale, translated, rotated)
    # Roof normals (0,0,1), (-h,-h,1), edge 5->7=(-1,1,0)
    # have triple product -2*h. The other edges have nonnegative turns.
    assert -2*h < 0
    assert p.reflex_edges(0) == [(5, 7)], 'declared-folded-reflex-ridge'


@pytest.mark.parametrize('scale', [F(1), F(1, 2**30), F(2**30)])
@pytest.mark.parametrize('translated,rotated', [(False, False), (False, True),
                                               (True, False), (True, True)])
def test_g6i02_dihedral_uses_incident_declared_triangles(scale, translated, rotated):
    p = _folded_roof(F(1, 2), scale, translated, rotated)
    assert p.dihedral_turn((4, 5)) == math.pi/2, 'actual-surface-right-angle'
    assert p.dihedral_turn((5, 7)) < 0, 'actual-surface-internal-reflex-angle'


def test_g6i02_flat_boundary_and_geometry_edit_use_fresh_surface_topology():
    p = _folded_roof()
    assert p.reflex_edges(0) == [(5, 7)]
    p.verts[6] = (F(1), F(1), F(1))
    assert p.is_convex(0) is True, 'flat-roof-boundary-remains-convex'
    assert p.reflex_edges(0) == [], 'surface-view-tracks-vertex-content'
    assert p.dihedral_turn((4, 5)) == math.pi/2


def _cube(center, half, inward=False):
    x, y, z = (F(_r12_item) for _r12_item in center)
    h = F(half)
    verts = [(x-h, y-h, z-h), (x+h, y-h, z-h), (x+h, y+h, z-h), (x-h, y+h, z-h),
             (x-h, y-h, z+h), (x+h, y-h, z+h), (x+h, y+h, z+h), (x-h, y+h, z+h)]
    faces = [tuple(reversed(f)) if inward else f for f in FACES]
    return G.Polyhedron(verts, faces)


def _join(*shells):
    verts, faces = [], []
    for shell in shells:
        offset = len(verts)
        faces.extend(tuple(offset+i for i in face) for face in shell.faces)
        verts.extend(shell.verts)
    return G.Polyhedron(verts, faces)


def _assert_disconnected_inward_detected(scale=F(1)):
    p = _join(_cube((0, 0, 0), 2*scale), _cube((10*scale, 0, 0), scale, True))
    assert any('component 1' in issue and 'orientation is inward' in issue
               for issue in p.manifold_issues(0)), 'disconnected-inward-component'


@pytest.mark.parametrize('scale', [F(1), F(1, 2**600), F(2**600)])
def test_g6i05_disconnected_inward_component_is_not_hidden_by_total_volume(scale):
    _assert_disconnected_inward_detected(scale)


@pytest.mark.parametrize('directions,valid', [
    ((False, True), True), ((False, False), False),
    ((False, True, False), True), ((False, True, True), False),
    ((True, True), False),
])
def test_g6i05_component_orientation_obeys_nested_cavity_parity(directions, valid):
    p = _join(*(_cube((0, 0, 0), 4-i, inward) for i, inward in enumerate(directions)))
    assert (p.manifold_issues(0) == []) is valid, 'shell-nesting-orientation-parity'


def test_g6i05_valid_disconnected_solids_remain_accepted_but_not_convex():
    p = _join(_cube((0, 0, 0), 2), _cube((10, 0, 0), 1))
    assert p.manifold_issues(0) == [], 'valid-separated-outward-shells'
    assert p.is_convex(0) is False, 'disconnected-union-is-not-convex'


@pytest.mark.parametrize('offset', [F(3), F(4)])
def test_g6i05_component_contact_and_crossing_do_not_claim_shell_nesting(offset):
    p = _join(_cube((0, 0, 0), 2), _cube((offset, 0, 0), 2))
    assert any('nesting undefined' in issue for issue in p.manifold_issues(0)), 'non-nested-shells-rejected'


@pytest.mark.parametrize('method,check,message', [
    ('is_convex', lambda: test_g6i02_declared_folded_surface_is_not_convex(F(1, 2), F(1), False, False),
     'declared-roof-midpoint-concavity'),
    ('reflex_edges', lambda: test_g6i02_reflex_edges_include_declared_internal_ridge(F(1, 2), F(1), False, False),
     'declared-folded-reflex-ridge'),
    ('dihedral_turn', lambda: test_g6i02_dihedral_uses_incident_declared_triangles(F(1), False, False),
     'actual-surface-right-angle'),
])
def test_g6i02_restoring_source_ring_topology_mutant_is_caught(monkeypatch, method, check, message):
    source = textwrap.dedent(inspect.getsource(getattr(G.Polyhedron, method)))
    needle = 'P = exact_surface(self)'
    assert source.count(needle) == 1
    namespace = dict(vars(G))
    exec(compile(source.replace(needle, 'P = self'), '<r9-source-ring-topology>', 'exec'), namespace)
    monkeypatch.setattr(G.Polyhedron, method, namespace[method])
    with pytest.raises(AssertionError, match=message):
        check()


def test_g6i05_restoring_total_volume_orientation_mutant_is_caught(monkeypatch):
    def global_volume_only(p):
        volume6, _ = G._mass_properties(tuple(p.verts), tuple(p.faces))
        return ['global orientation is inward'] if volume6 <= 0 else []
    monkeypatch.setattr(G, '_component_orientation_issues', global_volume_only)
    with pytest.raises(AssertionError, match='disconnected-inward-component'):
        _assert_disconnected_inward_detected()
