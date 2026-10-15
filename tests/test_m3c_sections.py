"""M3c closed interval, non-axis tangency and contact-start semantic gates.

Oracle inventory: fractions only for the analytic Cartesian results.  geom3
constructs raw input surfaces, never oracle geometry; expected E boxes below
are derived directly from the stated solid unions.  g03's separate audit
oracle imports g03_exit_oracle -> g03_surface_oracle -> fractions, itertools,
functools, math and kernel2d.g0_oracle.sqrt_display.  It shares no tested
global_entrance SAT, decomposition, interval, pruning or merge primitive.

Every mutant is compiled inside the actual function and installed only in
memory. These gates never invoke source hashes/frozen manifests, so the
observed red must be the named geometric assertion, not a hash tripwire.
"""
from fractions import Fraction as F

import pytest

from eab.kernel3d import geom3, g03
from eab.kernel3d import global_entrance as G
from tools.m3c_mutation_support import mutate as _mutate


def _combine(*parts):
    vertices, faces = [], []
    for part in parts:
        offset = len(vertices)
        vertices.extend(part.verts)
        faces.extend(tuple(offset+i for i in face) for face in part.faces)
    return geom3.Polyhedron(vertices, faces)


def _prism(profile):
    count = len(profile)
    vertices = [(F(x), F(y), z) for z in (F(-1, 2), F(1, 2))
                for x, y in profile]
    faces = [tuple(range(count-1, -1, -1)), tuple(range(count, 2*count))]
    faces += [(i, (i+1) % count, (i+1) % count+count, i+count)
              for i in range(count)]
    return geom3.Polyhedron(vertices, faces)


def _seam_case(kind):
    if kind == 'tight_pin':
        a = geom3.box(center=(F(3, 2), F(3, 2), 0),
                      half=(F(1, 2), F(1, 2), F(1, 4)))
        b = _prism([(0, 0), (3, 0), (3, 3), (2, 3),
                    (2, 1), (1, 1), (1, 3), (0, 3)])
        # The width-one pin exactly spans the pocket. Closed E fills its
        # internal contact seam: [-2,2]^2 x [-3/4,3/4].
        return a, b, F(3, 4)
    if kind == 'cavity':
        a = geom3.box(half=(F(1, 2),)*3)
        outer = geom3.box(half=(2,)*3)
        hole = geom3.Polyhedron(a.verts, [tuple(reversed(f)) for f in a.faces])
        # A exactly fills the hole; E is [-5/2,5/2]^3, including the contact
        # point at the centre. Every nonzero small displacement penetrates.
        return a, _combine(outer, hole), F(5, 2)
    assert kind == 'separated_slabs'
    a = geom3.box(half=(F(1, 2),)*3)
    b = _combine(geom3.box(center=(-F(3, 2), 0, 0), half=(1, 2, 2)),
                 geom3.box(center=(F(3, 2), 0, 0), half=(1, 2, 2)))
    # Independent Minkowski sums are [-3,0] and [0,3] in x, both with
    # y,z in [-5/2,5/2]. Their closed union does not end at x=0.
    return a, b, F(5, 2)


def _assert_seam_line(kind):
    a, b, end = _seam_case(kind)
    line = G.global_entrance(a, b).line_sections(direction=(1, 1, 1))
    assert line.closed == ((-end, end),), 'closed-E contact seam is not an interval endpoint'
    assert line.opened == ((-end, F(0)), (F(0), end)), 'open penetration retains the contact seam'
    assert line.classify(0) == 0, 'the interior seam is physical contact'
    assert line.first_nonpenetrating(F(-1, 8)) == 0, 'physical nonpenetration is distinct from closed-E exit'


@pytest.mark.parametrize('kind', ['tight_pin', 'cavity', 'separated_slabs'])
@pytest.mark.parametrize('base', [(0, 0, 0), (F(-1, 8),)*3])
def test_g03_closed_E_exit_crosses_internal_contact_seams(kind, base):
    a, b, end = _seam_case(kind)
    expected, direction, _ = g03.exit_oracle.closed_exit(a, b, base)
    assert direction == (1, 1, 1) and expected == end-base[0], 'independent surface oracle agrees with analytic closed-E exit'
    report = g03.g0_distance_completeness3(a, b, base=base, radius=0, samples=1)
    assert report.samples == 1 and report.skipped_intersecting == 0, 'g03 contact seam sample executes'
    assert report.passed, ('g03 closed-E exit must cross the internal contact seam',
                           kind, report.completeness_failures)


@pytest.mark.parametrize('kind', ['tight_pin', 'cavity', 'separated_slabs'])
def test_closed_E_merges_internal_contact_seams_in_line_sections(kind):
    _assert_seam_line(kind)


@pytest.mark.parametrize('kind', ['tight_pin', 'cavity', 'separated_slabs'])
def test_open_merge_mutant_fails_both_interval_and_g03_semantic_assertions(monkeypatch, kind):
    _assert_seam_line(kind)
    for base in ((0, 0, 0), (F(-1, 8),)*3):
        test_g03_closed_E_exit_crosses_internal_contact_seams(kind, base)
    with monkeypatch.context() as mutation:
        _mutate(mutation, G, G._merge, 'lo <= result[-1][1]', 'lo < result[-1][1]')
        with pytest.raises(AssertionError, match='closed-E contact seam is not an interval endpoint'):
            _assert_seam_line(kind)
        for base in ((0, 0, 0), (F(-1, 8),)*3):
            with pytest.raises(AssertionError, match='g03 closed-E exit must cross the internal contact seam'):
                test_g03_closed_E_exit_crosses_internal_contact_seams(kind, base)
    G._line_sections.cache_clear()
    _assert_seam_line(kind)
    for base in ((0, 0, 0), (F(-1, 8),)*3):
        test_g03_closed_E_exit_crosses_internal_contact_seams(kind, base)


def _assert_nonaxial_singleton_tangencies():
    outputs = []
    for index, (scale, shift) in enumerate(((F(1, 1024), 10**6),
                                           (F(1), 0), (F(1024), 1000))):
        centre = (F(shift), F(-2*shift), F(3*shift))
        a = geom3.box(center=centre, half=(scale/2,)*3)
        b = geom3.box(center=tuple(centre[k]+scale*(3, 1, 0)[k] for k in range(3)),
                     half=(scale/2,)*3)
        # E/scale = [2,4] x [0,2] x [-1,1]. Along (1,1,1), x>=2
        # and y<=2 force the single parameter 2+index, with z=0 there.
        start = tuple(scale*q for q in (-index, -index, -2-index))
        direction = (scale,)*3
        line = G.global_entrance(a, b).line_sections(start, direction)
        contact = F(2+index)
        assert line.closed == ((contact, contact),), 'nonaxial singleton tangency survives closed AABB pruning'
        assert line.opened == (), 'single-point tangency has no open penetration interval'
        assert tuple(line.classify(q) for q in (contact-F(1, 8), contact, contact+F(1, 8))) == (-1, 0, -1)
        outputs.append(line.closed)
    assert len(set(outputs)) == len(outputs), 'scaled translated parameter cases have distinct outputs'


def test_nonaxial_singleton_tangency_is_closed_at_three_scales_and_translations():
    _assert_nonaxial_singleton_tangencies()


def test_closed_AABB_equality_rejection_mutant_fails_singleton_semantics(monkeypatch):
    _assert_nonaxial_singleton_tangencies()
    with monkeypatch.context() as mutation:
        _mutate(mutation, G, G._line_candidate, 'if lower > upper:', 'if lower >= upper:')
        with pytest.raises(AssertionError, match='nonaxial singleton tangency survives closed AABB pruning'):
            _assert_nonaxial_singleton_tangencies()
    G._line_sections.cache_clear()
    _assert_nonaxial_singleton_tangencies()


@pytest.mark.parametrize('base', [(1, 0, 0), (1, 1, 0), (1, 1, 1), (-1, 0, 0)])
def test_g03_boundary_face_edge_vertex_start_uses_closed_zero_membership(base):
    cube = geom3.box(half=(F(1, 2),)*3)
    expected, direction, _ = g03.exit_oracle.closed_exit(cube, cube, base)
    # E=[-1,1]^3. Positive generic direction is (1,1,1): each positive
    # boundary face/edge/vertex has zero exit; the negative x face enters E.
    analytic = F(1) if base == (-1, 0, 0) else F(0)
    assert direction == (1, 1, 1) and expected == analytic, 'analytic boundary-start directional exit'
    report = g03.g0_distance_completeness3(cube, cube, base=base, radius=0, samples=1)
    assert report.samples == 1 and report.skipped_intersecting == 0, 'g03 boundary-start sample executes'
    assert report.passed, ('g03 boundary-start zero belongs to the closed interval',
                           base, analytic, report.completeness_failures)
@pytest.mark.parametrize('before,after,base', [
    ('lo <= 0 <= hi', 'lo <= 0 < hi', (1, 0, 0)),
    ('lo <= 0 <= hi', 'lo < 0 <= hi', (-1, 0, 0)),
])
def test_g03_open_zero_membership_mutants_fail_boundary_start_semantics(monkeypatch, before, after, base):
    test_g03_boundary_face_edge_vertex_start_uses_closed_zero_membership(base)
    with monkeypatch.context() as mutation:
        _mutate(mutation, g03, g03.g0_distance_completeness3, before, after)
        with pytest.raises(AssertionError, match='g03 boundary-start zero belongs to the closed interval'):
            test_g03_boundary_face_edge_vertex_start_uses_closed_zero_membership(base)
    test_g03_boundary_face_edge_vertex_start_uses_closed_zero_membership(base)
