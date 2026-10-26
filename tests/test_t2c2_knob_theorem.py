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
        Q5(1)**F(1, 2)


def test_lemma_a_zero_critical_slack_and_exact_main_chord():
    exact.verify_a_zero()
    for element in ELEMENTS:
        m = exact.verify_lemma_a(element)
        assert m["radius"] == F(1, 2)
        assert m["h3"] == (4 if element == "square" else F(41, 12))


def test_lemma_a_zero_rejects_internal_secondary_bound_mutation():
    with patch.object(exact, "SECONDARY_BOUND", F(2)):
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


def test_lemma_c_exact_farthest_vertices_and_all_eight_edge_distances():
    assert exact.verify_q_containment() == 6
    assert exact.verify_c_edges() == (F(9, 10), F(4, 5), F(4, 5), F(9, 10),
                                      F(9, 10), F(4, 5), F(4, 5), F(9, 10))
    for element in ELEMENTS:
        maximum, points = exact.verify_lemma_c(element)
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
        lo, hi = exact.verify_lemma_e(element)
        assert F(1, 6) < lo < hi < 2


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
