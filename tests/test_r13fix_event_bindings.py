"""R13: returned event constructions stay bound to independent exact answers.

The reference uses rational interval endpoints and axis-aligned inequalities,
not production geometry, overlap, surface events, or construction functions.
RN-even values have independent rational midpoint certificates; escape display
is instead the documented least binary64 upper bound. Source mutations execute
inside the real function, never by editing a returned result.
"""
from fractions import Fraction as F
import inspect
import math

import pytest

from r13_event_oracle import assert_event_binding, assert_scalar_binding
from eab.kernel2d import entrance as E2
from eab.kernel3d import entrance3 as E3
from eab.adapters import tia3d as I
from eab.kernel3d.geom3 import Polyhedron


FACES = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (3, 7, 6, 2), (0, 4, 7, 3), (1, 2, 6, 5))
SCALES = (F(2)**-1070, F(1), F(2)**1018)


def _slab(low, high, width=F(1)):
    return Polyhedron([(-width, -width, low), (width, -width, low),
                       (width, width, low), (-width, width, low),
                       (-width, -width, high), (width, -width, high),
                       (width, width, high), (-width, width, high)], list(FACES))


@pytest.mark.parametrize("scale", SCALES, ids=("subnormal", "ordinary", "upper_edge"))
def test_public_2d_event_fields_have_independent_extreme_scale_references(scale):
    a = [(-scale, 4*scale), (scale, 4*scale), (scale, 6*scale), (-scale, 6*scale)]
    b = [(-scale, -scale), (scale, -scale), (scale, scale), (-scale, scale)]
    start, direction = (scale/4, scale/2), (0, -scale)
    result = E2.first_entrance(a, b, start, direction, t_max=8)
    assert result.kind == "entrance"
    assert_event_binding(result.t, result.t_exact, result.x, start, direction, F(7, 2))
    assert result.normal == (0, 1) and result.gap == 0
    # Selected parallel-face contact is the right endpoint of the overlap.
    for point in (result.point_a, result.point_b):
        for actual in point:
            assert_scalar_binding(actual, scale, "2D entrance witness midpoint binding")
    entered = [(x, y-4*scale) for x, y in a]
    origin = (scale/4, scale/4)
    leave = E2.shortest_exit(entered, b, origin)
    assert leave.kind == "exit" and leave.t == leave.t_exact == 0
    assert leave.x == origin and leave.normal == (0, 1)
    assert_scalar_binding(leave.gap, -3*scale/4, "2D exit depth midpoint binding")
    for point, expected in ((leave.point_a, (-3*scale/4, scale/4)),
                            (leave.point_b, (-3*scale/4, scale))):
        for actual, exact in zip(point, expected):
            assert_scalar_binding(actual, exact, "2D exit witness midpoint binding")


@pytest.mark.parametrize("scale", SCALES, ids=("subnormal", "ordinary", "upper_edge"))
def test_public_3d_entrance_fields_have_independent_extreme_scale_references(scale):
    # Anisotropy keeps face areas representable even when the z output is huge.
    a, b = _slab(3*scale, 5*scale), _slab(-scale, 0)
    start, direction = (F(1, 4), F(-1, 4), scale/2), (0, 0, -scale)
    result = E3.first_entrance3(a, b, start, direction, t_max=8)
    assert result.kind == "entrance"
    assert_event_binding(result.t, result.exact_t, result.x, start, direction, F(7, 2))
    assert result.normal == (0, 0, 1) and result.gap == 0
    for point in (result.point_a, result.point_b):
        for actual, exact in zip(point, (F(-3, 4), F(3, 4), 0)):
            assert_scalar_binding(actual, exact, "3D entrance witness midpoint binding")


@pytest.mark.parametrize("scale", SCALES, ids=("subnormal", "ordinary", "upper_edge"))
def test_public_entrance_times_are_rounded_once_at_extreme_scales(scale):
    root = scale/3
    a, b = _slab(root, 2*max(F(1), scale)), _slab(-max(F(1), scale), 0)
    three = E3.first_entrance3(a, b, (0, 0, 0), (0, 0, -1), t_max=scale)
    assert_event_binding(three.t, three.exact_t, three.x, (0, 0, 0), (0, 0, -1), root)
    a2 = [(F(-1), root), (F(1), root), (F(1), 2*max(F(1), scale)), (F(-1), 2*max(F(1), scale))]
    b2 = [(F(-1), -max(F(1), scale)), (F(1), -max(F(1), scale)), (F(1), F(0)), (F(-1), F(0))]
    two = E2.first_entrance(a2, b2, (0, 0), (0, -1), t_max=scale)
    assert_event_binding(two.t, two.t_exact, two.x, (0, 0), (0, -1), root)


def test_concave_2d_and_3d_returns_stay_bound_to_the_analytic_riser_event():
    from test_kernel2d_entrance import STEP as step2
    from test_entrance3_concave import STEP as step3
    a2 = [(F(7, 5), F(9, 10)), (F(12, 5), F(9, 10)),
          (F(12, 5), F(19, 10)), (F(7, 5), F(19, 10))]
    two = E2.first_entrance(a2, step2, (0, 0), (-1, F(-1, 2)), t_max=3)
    assert two.kind == "entrance"
    assert_event_binding(two.t, two.t_exact, two.x, (0, 0), (-1, F(-1, 2)), F(2, 5))
    a3 = _slab(F(9, 10), F(19, 10), F(1, 2))
    a3 = Polyhedron([(x+F(19, 10), y, z) for x, y, z in a3.verts], a3.faces)
    three = E3.first_entrance3(a3, step3, (0, 0, 0), (-1, 0, F(-1, 2)), t_max=3)
    assert three.kind == "entrance"
    assert_event_binding(three.t, three.exact_t, three.x, (0, 0, 0), (-1, 0, F(-1, 2)), F(2, 5))


@pytest.mark.parametrize("scale", (F(2)**-1070, F(1), F(2)**508),
                         ids=("subnormal", "ordinary", "area_upper_edge"))
def test_public_3d_exit_fields_have_independent_extreme_scale_references(scale):
    a, b = _slab(0, 2*scale, scale), _slab(-scale, scale, scale)
    start = (scale/4, 0, scale/4)
    result = E3.shortest_exit3(a, b, start)
    assert result.kind == "exit" and result.t == result.exact_t == 0
    assert result.x == start and result.normal == (0, 0, 1)
    assert_scalar_binding(result.gap, -3*scale/4, "3D exit depth midpoint binding")
    for point, expected in ((result.point_a, (-3*scale/4, -scale, scale/4)),
                            (result.point_b, (-3*scale/4, -scale, scale))):
        for actual, exact in zip(point, expected):
            assert_scalar_binding(actual, exact, "3D exit witness midpoint binding")


def _assert_upper_view(actual, exact):
    assert math.isfinite(actual) and F(actual) >= exact, "escape outward display binding"
    assert F(math.nextafter(actual, -math.inf)) < exact, "escape outward display binding"


@pytest.mark.parametrize("scale", SCALES, ids=("subnormal", "ordinary", "upper_edge"))
@pytest.mark.parametrize("coefficient", (F(3, 4), F(1, 3)), ids=("dyadic", "rounded_up"))
def test_public_escape_height_offset_and_frozen_lift_match_independent_extreme_roots(scale, coefficient):
    root = scale*coefficient
    a, b = _slab(-root, max(F(1), scale)), _slab(-max(F(1), scale), 0)
    start = (F(1, 4), 0, 0)
    result = I.escape_height_covers(a, b, start)
    assert result.exact_height == root, "escape exact root binding"
    assert result.exact_offset == (start[0], start[1], root), "escape exact offset binding"
    _assert_upper_view(result.height, root)
    _assert_upper_view(I.escape_height_brute(a, b, start, hi=2*root), root)
    # Fixed horizontal source face: independent plane equation is z=-root.
    label = ("VF", ("vertex", 0), ("face", 1))
    frozen = I.escape_height_from_frozen_cover(a, b, label, start)
    assert frozen == root, "frozen escape exact root binding"


@pytest.mark.parametrize("scale", SCALES, ids=("subnormal", "ordinary", "upper_edge"))
def test_nominal_candidates_and_profile_have_valuewise_extreme_scale_references(scale):
    root = 3*scale/4
    a, b = _slab(-root, max(F(1), scale)), _slab(-max(F(1), scale), 0)
    candidates = I.escape_candidates(a, b, (F(1, 4), 0, 0))
    # Nominal labels can be suppressed by their declared normal-noise bound;
    # they are deliberately not the authoritative complete event list.
    if scale <= 1:
        assert candidates
    for height, _ in candidates:
        assert_scalar_binding(height, root, "nominal candidate height binding")
    rows = I.dilatancy_profile(a, b, deltas=[F(-1, 4), F(0), F(1, 4)])
    assert len(rows) == 3
    for row in rows:
        _assert_upper_view(row["h"], root)
    assert rows[1]["tan_psi"] == 0, "flat-profile derivative binding"
    assert rows[0]["tan_psi"] is rows[2]["tan_psi"] is None


@pytest.mark.parametrize("scale", (F(2)**-1070, F(1), F(2)**508),
                         ids=("subnormal", "ordinary", "area_upper_edge"))
def test_escape_reporting_does_not_construct_an_unrepresentable_intermediate_face_area(scale):
    # Regression for the additional scan finding: face_noise used to call
    # face_area, whose underflow aborted an otherwise representable height.
    a, b = _slab(0, 2*scale, scale), _slab(-scale, scale, scale)
    result = I.escape_height_covers(a, b, (scale/4, 0, scale/4))
    root = 3*scale/4
    assert result.exact_height == root
    _assert_upper_view(result.height, root)
    candidates = I.escape_candidates(a, b, (scale/4, 0, scale/4))
    assert candidates, "uniform-scale nominal candidates survive diagnostic range"
    for height, _ in candidates:
        assert_scalar_binding(height, root, "uniform-scale candidate height binding")


def test_g6m02_internal_return_start_mutant_is_rejected_by_the_migrated_3d_gate(monkeypatch):
    import test_entrance3 as original
    source = inspect.getsource(E3.first_entrance3)
    needle = "tuple(scalar_rational(_mapped_value) for _mapped_value in exact_x)"
    assert source.count(needle) == 1
    namespace = dict(vars(E3))
    exec(compile(source.replace(needle, "tuple(scalar_rational(_mapped_value) for _mapped_value in x0)"),
                 "<r13-internal-3d-return-start>", "exec"), namespace)
    monkeypatch.setattr(original, "first_entrance3", namespace["first_entrance3"])
    with pytest.raises(AssertionError, match="event position midpoint binding"):
        original.test_first_entrance_agrees_with_the_predicate_only_oracle_on_random_convex_pairs(0)


def test_internal_return_start_mutant_is_rejected_by_the_migrated_2d_gate(monkeypatch):
    import test_kernel2d_entrance as original
    source = inspect.getsource(E2._first_entrance_convex)
    needle = "x = vector_rational(exact_x)"
    assert source.count(needle) == 1
    namespace = dict(vars(E2))
    exec(compile(source.replace(needle, "x = vector_rational(x0)"),
                 "<r13-internal-2d-return-start>", "exec"), namespace)
    monkeypatch.setattr(E2, "_first_entrance_convex", namespace["_first_entrance_convex"])
    with pytest.raises(AssertionError, match="event position midpoint binding"):
        original.test_first_entrance_agrees_with_the_predicate_only_oracle_on_random_convex_pairs(0)


def test_internal_concave_return_start_mutant_is_rejected(monkeypatch):
    source = inspect.getsource(E2._first_entrance_concave)
    needle = 'return Entrance2("entrance", scalar_rational(t), vector_rational(x),'
    assert source.count(needle) == 1
    namespace = dict(vars(E2))
    exec(compile(source.replace(needle, 'return Entrance2("entrance", scalar_rational(t), vector_rational(x0),'),
                 "<r13-internal-concave-return-start>", "exec"), namespace)
    monkeypatch.setattr(E2, "_first_entrance_concave", namespace["_first_entrance_concave"])
    with pytest.raises(AssertionError, match="event position midpoint binding"):
        test_concave_2d_and_3d_returns_stay_bound_to_the_analytic_riser_event()


def test_escape_display_rounding_step_removal_is_rejected_in_the_real_function(monkeypatch):
    source = inspect.getsource(I.escape_height_covers)
    needle = "display=math.nextafter(display,math.inf)"
    assert source.count(needle) == 1
    namespace = dict(vars(I))
    exec(compile(source.replace(needle, "display=display"),
                 "<r13-remove-escape-outward-rounding>", "exec"), namespace)
    monkeypatch.setattr(I, "escape_height_covers", namespace["escape_height_covers"])
    with pytest.raises(AssertionError, match="escape outward display binding"):
        test_public_escape_height_offset_and_frozen_lift_match_independent_extreme_roots(F(1), F(1, 3))


def test_escape_exact_offset_drop_height_mutant_is_rejected_in_the_real_function(monkeypatch):
    source = inspect.getsource(I.escape_height_covers)
    needle = "F(offset[2])+root"
    assert source.count(needle) == 1
    namespace = dict(vars(I))
    exec(compile(source.replace(needle, "F(offset[2])"),
                 "<r13-remove-escape-height-from-offset>", "exec"), namespace)
    monkeypatch.setattr(I, "escape_height_covers", namespace["escape_height_covers"])
    with pytest.raises(AssertionError, match="escape exact offset binding"):
        test_public_escape_height_offset_and_frozen_lift_match_independent_extreme_roots(F(1), F(3, 4))
