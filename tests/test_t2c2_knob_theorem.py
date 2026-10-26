"""Named exact gates for the owner's T2c2 theorem, not a new theorem claim.

Primary oracle: hand-derived supports and affine horizontal-section minima
in Q(sqrt(5)); it shares no production erosion/path/geometry primitive.
Production erosion at rational points is explicitly only an affine-regime
cross-check. Mutations change an internal arithmetic constant, geometry
coordinate or critical-delta function before the semantic check executes.
"""
from fractions import Fraction as F
from unittest.mock import patch

from eab.adapters.tia2d import tolerance_knob
from eab.kernel2d.erosion import erode_polygon_exact

from tests import t2c2_knob_exact as exact
from tests.t2c2_knob_exact import Q5


ELEMENTS = ("square", "octagon")


class _rejects:
    def __init__(self, exception, message=None):
        self.exception, self.message = exception, message

    def __enter__(self):
        return self

    def __exit__(self, kind, exception, traceback):
        if exception is None:
            raise AssertionError("expected semantic rejection did not occur")
        matches = isinstance(exception, self.exception)
        if matches and self.message is not None:
            assert self.message in str(exception), "wrong assertion killed the mutation"
        return matches


def test_q5_exact_field_arithmetic_sign_and_order():
    root = Q5(0, 1)
    assert root*root == 5
    assert 1/root == Q5(0, F(1, 5))
    assert (2-root)*(2+root) == -1
    assert Q5(161, -72).sign() == 1
    assert Q5(-161, 72).sign() == -1
    assert Q5(-9, 4).sign() == -1
    assert Q5(-20, 9).sign() == 1
    assert Q5(0).sign() == 0
    assert not Q5(0) and Q5(1) and root and Q5(161, -72)
    assert Q5(1, 1) != Q5(1, 0)
    assert -root < 0 < root and root <= root and root >= root
    assert abs(-root) == root
    assert hash(Q5(F(1, 2))) == hash(F(1, 2))
    values = (Q5(0), Q5(1), root, Q5(F(2, 3), F(-7, 11)))
    for a in values:
        for b in values:
            assert (a+b)-b == a
            assert a*(b+1) == a*b+a
            if b != 0:
                assert (a/b)*b == a
        assert a**0 == 1 and a**3 == a*a*a
        if a != 0:
            assert a**-3*a**3 == 1
    # (2+sqrt(5))**n has norm (-1)**n.  Its conjugate is nonzero
    # even for Pell near-zero values beyond binary64 cancellation at n=14.
    p, q, expected_sign = 1, 0, 1
    for n in range(1, 33):
        p, q, expected_sign = 2*p+5*q, p+2*q, -expected_sign
        assert p*p-5*q*q == expected_sign
        if n >= 14:
            assert Q5(p, -q).sign() == expected_sign
            assert Q5(-p, q).sign() == -expected_sign
            assert Q5(p, -q) != 0


def test_q5_rejects_nonexact_inputs_zero_division_and_float_conversion():
    for bad in ("1/2", object(), [1, 2]):
        with _rejects(TypeError):
            Q5(bad)
        with _rejects(TypeError):
            Q5(0, bad)
        with _rejects(TypeError):
            Q5(Q5(1), bad)
    with _rejects(ZeroDivisionError):
        Q5(1)/0
    with _rejects(TypeError):
        Q5(1).__float__()
    with _rejects(TypeError):
        Q5(1).__pow__(F(1, 2))


def test_q5_float_comparisons_raise_instead_of_returning_false():
    # Deliberately nonexact boundary input: never used in arithmetic or a
    # geometric predicate, only to require every comparison to reject it.
    bad = F(1, 2).__float__()
    with _rejects(TypeError):
        Q5(1) == bad
    with _rejects(TypeError):
        bad == Q5(1)
    with _rejects(TypeError):
        Q5(1) != bad
    with _rejects(TypeError):
        bad != Q5(1)
    with _rejects(TypeError):
        Q5(1) < bad
    with _rejects(TypeError):
        bad < Q5(1)
    with _rejects(TypeError):
        Q5(1) <= bad
    with _rejects(TypeError):
        bad <= Q5(1)
    with _rejects(TypeError):
        Q5(1) > bad
    with _rejects(TypeError):
        bad > Q5(1)
    with _rejects(TypeError):
        Q5(1) >= bad
    with _rejects(TypeError):
        bad >= Q5(1)


def test_lemma_a_zero_critical_slack_and_exact_main_chord():
    assert exact.verify_a_zero() == (Q5(1), Q5(1))
    for element in ELEMENTS:
        assert exact.lemma_a_metrics(element, 0)["secondary_squared_margin"] == 1
        critical = exact.verify_a_critical(element)
        expected = (Q5(F(-1, 6), F(4, 9)) if element == "square"
                    else Q5(F(95, 3364), F(205, 841)))
        assert critical["secondary_squared_margin"] == expected
        assert critical["secondary_residual"] > 0 and expected > 0
        m = exact.verify_lemma_a(element)
        assert m == critical
        assert m["radius"] == F(1, 2)
        assert m["h3"] == (4 if element == "square" else F(41, 12))


def test_lemma_a_zero_rejects_internal_secondary_bound_mutation():
    for bound in (F(2), F(11, 4)):
        with patch.object(exact, "SECONDARY_BOUND", bound):
            with _rejects(AssertionError, "g(0)"):
                exact.verify_a_zero()


def test_lemma_a_critical_slack_rejects_internal_bound_mutation():
    with patch.object(exact, "SECONDARY_BOUND", F(5, 2)):
        for element in ELEMENTS:
            with _rejects(AssertionError, "g(delta critical)"):
                exact.verify_a_critical(element)


def test_lemma_a_main_rejects_internal_support_mutation():
    for element in ELEMENTS:
        with patch.dict(exact.MAIN_SUPPORT, {element: exact.MAIN_SUPPORT[element]+F(1, 1000)}):
            with _rejects(AssertionError, "declared support"):
                exact.verify_a_main(element)


def test_lemma_a_equality_rejects_internal_critical_delta_shift():
    for element in ELEMENTS:
        shifted = exact.critical_delta(element)+F(1, 2**20)
        with patch.object(exact, "critical_delta", return_value=shifted):
            with _rejects(AssertionError, "critical main-chord equality"):
                exact.verify_a_main(element)
        assert exact.lemma_a_metrics(element, shifted)["radius"] < F(1, 2)


def test_symbolic_erosion_exact_section_partition_and_rational_affine_crosscheck():
    geometry = tolerance_knob(segments=4)
    assert geometry["moving"] == exact.MOVING_VERTICES
    assert geometry["obstacles"] == exact.truth_obstacles()
    intervals = {"square": (F(29, 100), F(3, 10)),
                 "octagon": (F(9, 25), F(37, 100))}
    for element in ELEMENTS:
        cuts, checks = exact.verify_symbolic_erosion(element)
        assert (cuts, checks) == ((8, 15) if element == "square" else (12, 23))
        assert checks == 2*cuts-1
        lo, hi = intervals[element]
        assert lo < exact.critical_delta(element) < hi
        rings = []
        for d in (lo, (lo+hi)/2, hi):
            result = erode_polygon_exact(exact.MOVING_VERTICES, d, element)
            assert result.status == "ACCEPTED" and result.reason is None
            assert result.polygon == exact.symbolic_vertices(element, d)
            assert result.rings == (result.polygon,)
            rings.append(result.polygon)
        for a, middle, b in zip(*rings):
            assert middle == tuple((x+y)/2 for x, y in zip(a, b))


def test_symbolic_erosion_rejects_old_octagon_top_intercept_inside_model():
    with patch.object(exact, "OCTAGON_TOP_INTERCEPT", F(1, 2)):
        with _rejects(AssertionError, "independent section erosion"):
            exact.verify_symbolic_erosion("octagon")


def test_symbolic_erosion_rejects_underreported_octagon_widest_pair_at_midpoint():
    d = exact.critical_delta("octagon")
    right = exact._right_vertices("octagon", d)
    changed = right[:2]+((1-17*d/12, 1-5*d/12), (1-17*d/12, 1+5*d/12))+right[3:]
    with patch.object(exact, "_right_vertices", return_value=changed):
        with _rejects(AssertionError, "independent section erosion"):
            exact.verify_symbolic_erosion("octagon")


def test_symbolic_partition_rejects_one_missing_element_height_event():
    element = "octagon"
    d = exact.critical_delta(element)
    profile = tuple((y, x) for x, y in exact._right_vertices(element, d))
    lo, hi = profile[0][0], profile[-1][0]
    cuts = {y for y, _ in profile}
    events = {height-d*vy for height, _ in exact.CAVITY_PROFILE
              for _, vy in exact.element_vertices(element) if lo < height-d*vy < hi}
    cuts.update(events)
    assert exact.verify_section_partition(element, d, profile, sorted(cuts)) == 12
    removed = min(events-{y for y, _ in profile})
    with _rejects(AssertionError, "missing element-height event cut"):
        exact.verify_section_partition(element, d, profile, sorted(cuts-{removed}))


def test_lemma_c_exact_farthest_vertices_and_all_eight_edge_distances():
    assert exact.verify_q_containment() == 6
    assert exact.verify_c_edges() == (F(9, 10), F(4, 5), F(4, 5), F(9, 10),
                                      F(9, 10), F(4, 5), F(4, 5), F(9, 10))
    for element in ELEMENTS:
        maximum, points = exact.verify_c_radius(element)
        expected = (Q5(F(5, 12), F(1, 18)) if element == "square"
                    else Q5(F(8509, 30276), F(175, 2523)))
        top_x, top_y = ((Q5(F(-1, 6), F(1, 6)), Q5(F(4, 3), F(1, 6)))
                       if element == "square" else
                       (Q5(F(-1, 87), F(5, 58)), Q5(F(34, 29), F(6, 29))))
        assert maximum == expected
        assert points == ((top_x, top_y), (-top_x, top_y))
        assert exact.verify_lemma_c(element) == (maximum, points)
        assert maximum < F(4, 5)
        assert points[0][0] == -points[1][0]


def test_lemma_c_radius_rejects_internal_disk_bound_mutation():
    with patch.object(exact, "RADIUS_CAP_SQUARED", F(2, 5)):
        for element in ELEMENTS:
            with _rejects(AssertionError, "rotation disk"):
                exact.verify_c_radius(element)


def test_lemma_c_edge_distance_rejects_internal_q_vertex_mutation():
    changed = ((F(0), F(1, 1000)),)+exact.Q_VERTICES[1:]
    with patch.object(exact, "Q_VERTICES", changed):
        with _rejects(AssertionError, "Q must have four"):
            exact.verify_c_edges()


def test_q_containment_rejects_outside_vertex_even_when_both_chains_mirror():
    changed = tuple((F(11, 10)*x, y) if abs(x) == 1 else (x, y)
                    for x, y in exact.Q_VERTICES)
    with patch.object(exact, "Q_VERTICES", changed):
        with _rejects(AssertionError, "Q must stay inside A"):
            exact.verify_q_containment()


def test_q_containment_rejects_an_unchecked_left_chain_vertex():
    changed = exact.Q_VERTICES[:6]+((F(-11, 10), F(1)),)+exact.Q_VERTICES[7:]
    with patch.object(exact, "Q_VERTICES", changed):
        with _rejects(AssertionError, "Q left chain must mirror"):
            exact.verify_q_containment()
    changed = exact.MOVING_VERTICES[:9]+((F(-9, 10), F(1)),)+exact.MOVING_VERTICES[10:]
    with patch.object(exact, "MOVING_VERTICES", changed):
        with _rejects(AssertionError, "A left chain must mirror"):
            exact.verify_q_containment()


def test_lemma_d_all_eleven_strip_projections():
    assert exact.verify_lemma_d() == (F(-1, 2), F(1, 5), F(1), F(1),
                                      F(11, 12), F(1), F(0), F(-1, 12),
                                      F(-1, 5), F(-1), F(-1))


def test_lemma_d_rejects_one_internal_vertex_coordinate_mutation():
    changed = exact.MOVING_VERTICES[:2]+((F(1001, 1000), F(1)),)+exact.MOVING_VERTICES[3:]
    with patch.object(exact, "MOVING_VERTICES", changed):
        with _rejects(AssertionError, "all eleven vertices"):
            exact.verify_lemma_d()


def test_lemma_e_vertical_extrema_and_piecewise_cavity_width():
    cuts, widths = exact.verify_e_cavity()
    assert cuts == (F(1, 6), F(1, 5), F(1), F(9, 5), F(11, 6), F(2))
    assert widths == (F(1, 2), F(3, 5), F(1), F(3, 5), F(1, 2), F(1, 2))
    for element in ELEMENTS:
        lo, hi = exact.verify_e_vertical(element)
        expected = ((Q5(F(1, 2), F(-1, 25)), Q5(F(3, 2), F(1, 10)))
                    if element == "square" else
                    (Q5(F(69, 145), F(-3, 145)), Q5(F(3, 2), F(1, 15))))
        assert (lo, hi) == expected
        assert exact.verify_lemma_e(element) == expected
        assert F(1, 6) < lo < hi < 2


def test_rotate_minus_phi_actual_matrix_is_orthogonal_with_unit_determinant():
    origin, x_axis, y_axis = exact.rotate_minus_phi(((F(0), F(1)), (F(1), F(1)), (F(0), F(2))))
    assert origin == exact.CENTER
    u = tuple(a-b for a, b in zip(x_axis, origin))
    v = tuple(a-b for a, b in zip(y_axis, origin))
    assert u[0]*u[0]+u[1]*u[1] == 1
    assert v[0]*v[0]+v[1]*v[1] == 1
    assert u[0]*v[0]+u[1]*v[1] == 0, "actual rotation columns must be orthogonal"
    assert u[0]*v[1]-u[1]*v[0] == 1, "actual rotation must have determinant one"


def test_lemma_e_vertical_rejects_internal_rotation_number_mutation():
    with patch.object(exact, "ROTATION_COS_NUMERATOR", F(3)):
        for element in ELEMENTS:
            with _rejects(AssertionError, "common vertical envelope"):
                exact.verify_e_vertical(element)


def test_lemma_e_strip_rejects_internal_neck_width_mutation():
    changed = exact.CAVITY_PROFILE[:-1]+((F(2), F(499, 1000)),)
    with patch.object(exact, "CAVITY_PROFILE", changed):
        with _rejects(AssertionError, "infinite exit strip"):
            exact.verify_e_cavity()


def test_lemma_e_strip_rejects_internal_floor_top_mutation():
    with patch.object(exact, "FLOOR_TOP", F(1)):
        with _rejects(AssertionError, "floor interior"):
            exact.verify_e_cavity()


def test_translation_threshold_and_universal_relative_reduction():
    assert exact.verify_translation("square") == F(1, 3)
    assert exact.verify_translation("octagon") == F(12, 29)
    for element in ELEMENTS:
        ratio = exact.critical_delta(element)/exact.critical_translation_delta(element)
        assert 1-ratio == Q5(-1, F(1, 2))
        assert F(117, 1000) < 1-ratio < F(119, 1000)


def test_translation_threshold_rejects_internal_threshold_shift():
    for element in ELEMENTS:
        changed = exact.critical_translation_delta(element)+F(1, 2**20)
        with patch.object(exact, "critical_translation_delta", return_value=changed):
            with _rejects(AssertionError, "translation threshold"):
                exact.verify_translation(element)


def test_t2c1_knob_brackets_strictly_straddle_theorem_value():
    assert F(301, 1024) < exact.critical_delta("square") < F(1209, 4096)
    assert F(747, 2048) < exact.critical_delta("octagon") < F(375, 1024)


def test_exact_critical_escape_disk_turn_closed_strip_and_infinite_lift():
    for element, count in (("square", 11), ("octagon", 9)):
        result = exact.verify_critical_escape(element)
        assert result["status"] == "EXACT_CRITICAL_ESCAPE"
        assert result["vertices"] == count
        assert result["horizontal"] == (F(-1, 2), F(1, 2))
        assert result["sections"] == ((8, 15) if element == "square" else (12, 23))
        assert result["radius_squared"] is not None and result["farthest"] is not None, \
            "critical escape needs the rotation-disk proof"
        assert (result["radius_squared"], result["farthest"]) == exact.verify_c_radius(element)
        assert result["vertical"] == exact.verify_e_vertical(element)


def test_composite_proofs_execute_each_required_semantic_gate():
    # Wiring check, separate from the direct exact-value and geometry-negative
    # gates above: each wrapped call still executes the real semantic checker.
    with patch.object(exact, "verify_a_critical", wraps=exact.verify_a_critical) as checked:
        exact.verify_lemma_a("square")
        checked.assert_called_once_with("square")
    with patch.object(exact, "verify_q_containment", wraps=exact.verify_q_containment) as checked:
        exact.verify_lemma_c("square")
        checked.assert_called_once_with()
    with patch.object(exact, "verify_c_edges", wraps=exact.verify_c_edges) as checked:
        exact.verify_lemma_c("square")
        checked.assert_called_once_with()
    with patch.object(exact, "verify_e_cavity", wraps=exact.verify_e_cavity) as checked:
        exact.verify_lemma_e("square")
        checked.assert_called_once_with()


def test_exact_horizontal_projection_rejects_internal_rotation_mutation():
    for element in ELEMENTS:
        assert exact.verify_critical_horizontal(element) == (F(-1, 2), F(1, 2))
    with patch.object(exact, "ROTATION_COS_NUMERATOR", F(3)):
        for element in ELEMENTS:
            with _rejects(AssertionError, "critical horizontal projection"):
                exact.verify_critical_horizontal(element)


def test_exact_escape_rejects_internal_rotation_mutation_not_fake_output():
    with patch.object(exact, "ROTATION_COS_NUMERATOR", F(3)):
        for element in ELEMENTS:
            with _rejects(AssertionError, "common vertical envelope"):
                exact.verify_critical_escape(element)
