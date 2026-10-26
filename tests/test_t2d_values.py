"""G0 family gates: rational/surd oracle, independent of production geometry.

Oracle primitives are exact integer signs, rational chord sampling and
half-plane intersections; none call production erosion or SE(2) routines.
Mutation tests replace one internal numerical constant or primitive before
verification, not a completed certificate or a source integrity checksum.
"""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

import tests.t2d_knob_family_exact as exact


CASES = tuple(exact.TABLE)


def test_t2d_cross_field_order_signs_and_scaled_equalities():
    s = exact.Surd
    assert s(0, 1, 2) < s(0, 1, 3) < s(0, 1, 5)
    assert s(2, -1, 2) > s(2, -1, 3) > s(2, -1, 5)
    assert s(0, 1, 8) == s(0, 2, 2)
    assert s(1, F(1, 3), F(27, 4)) == s(1, F(1, 2), 3)
    assert s(1, -1, 2).compare(s(1, -1, 3)) == 1
    assert s(0, 1, 2)+s(0, F(1, 2), 8) == s(0, 2, 2)
    assert s(3, 2, 2)*s(3, -2, 2) == 1
    assert s(3, 2, 2)/s(3, 2, 2) == 1
    # Independent isqrt rational enclosures certify all unequal decisions.
    samples = tuple(s(a, b, q) for a in (-2, 0, 3) for b in (-1, 1) for q in (2, 3, 5, 7))
    for a in samples:
        assert a.compare(a) == 0
        alo, ahi = a.bounds(100)
        assert alo <= a <= ahi
        for b in samples:
            blo, bhi = b.bounds(100)
            if ahi < blo:
                assert a < b
            elif bhi < alo:
                assert b < a
            else:
                assert a == b
            assert a.compare(b) == -b.compare(a)


def test_t2d_comparison_one_sign_mutation_is_rejected():
    with patch.object(exact, "COMPARE_SQUARE_SIGN", -1):
        with unittest.TestCase().assertRaises(AssertionError):
            assert exact.Surd(0, 1, 2) < exact.Surd(0, 1, 3)


def test_t2d_algebra_rejects_nonexact_or_mixed_field_operations():
    with unittest.TestCase().assertRaises(TypeError):
        exact.Surd("1")
    with unittest.TestCase().assertRaises(TypeError):
        exact.Surd(0, 1, 2).__float__()
    with unittest.TestCase().assertRaises(TypeError):
        _ = exact.Surd(0, 1, 2)+exact.Surd(0, 1, 3)
    with unittest.TestCase().assertRaises(ZeroDivisionError):
        _ = exact.Surd(1)/0
    with unittest.TestCase().assertRaises(ValueError):
        exact.Surd(0, 1, -1)


def test_t2d_q_symmetry_containment_and_neck_heights():
    for n in (4, 8, 16, 32):
        exact.verify_family_geometry(n)

def test_t2d_q_circle_coordinate_mutation_is_rejected():
    with patch.object(exact, "ARC_VERTICAL_FACTOR", F(3)):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "unit circle"):
            exact.verify_family_geometry(4)


def test_t2d_q_symmetry_internal_reflection_mutation_is_rejected():
    with patch.object(exact, "Q_REFLECTION_SIGN", 1):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "central symmetry"):
            exact.verify_family_geometry(4)


def test_t2d_q_containment_neck_width_mutation_is_rejected():
    with patch.object(exact, "CLIPPED_NECK_WIDTH", F(1, 3)):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "containment"):
            exact.verify_family_geometry(4)


def test_t2d_neck_height_one_number_mutation_is_rejected():
    with patch.dict(exact.NECK_HEIGHTS, {4: F(10, 6)}):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "neck height"):
            exact.verify_family_geometry(4)


def test_t2d_theorem_table_all_fields_exact():
    for n, element in CASES:
        values = exact.verify_values(n, element)
        assert all(values["delta"] <= edge["delta"] for edge in exact.edge_candidates(n, element))
        assert values["delta"] > 0
        assert values["G"] >= values["G_facet"]

def test_t2d_disk_threshold_internal_radius_mutation_is_rejected():
    with patch.object(exact, "DISK_RADIUS", F(1, 3)):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "disk threshold"):
            exact.verify_values(8, "octagon")


def test_t2d_minimizing_chord_internal_parameter_mutation_is_rejected():
    d, t, s, _ = exact.TABLE[16, "K16"]
    with patch.dict(exact.TABLE, {(16, "K16"): (d, t, s, (F(0), F(3, 8)))}):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "minimizing chord"):
            exact.verify_values(16, "K16")


def test_t2d_strip_bound_one_number_mutation_is_rejected():
    with patch.object(exact, "STRIP_BOUND_SCALE", F(1, 2)):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "strip condition"):
            exact.verify_values(4, "square")


def test_t2d_translation_all_chord_numerator_mutation_is_rejected():
    with patch.object(exact, "TRANSLATION_INTERCEPT", F(2)):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "translation threshold"):
            exact.verify_values(32, "octagon")


def test_t2d_ratio_internal_numerator_mutation_is_rejected():
    with patch.object(exact, "RATIO_SCALE", F(2)):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "ratio"):
            exact.verify_values(4, "square")


def test_t2d_C_by_convex_hull_outer_erosion():
    for n, element in CASES:
        exact.verify_family_geometry(n)
        proof = exact.verify_C(n, element)
        assert proof["radius_squared"] < proof["wall_radius_squared"]

def test_t2d_C_one_number_in_rotation_radius_is_rejected():
    with patch.object(exact, "EROSION_SUPPORT_SCALE", F(0)):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "rotation radius"):
            exact.verify_C(4, "square")


def test_t2d_circle_limit_exact_roots_and_ratios():
    for element in ("square", "octagon", "K16"):
        exact.circle_limits(element)

def test_t2d_circle_root_one_coefficient_mutation_is_rejected():
    with patch.object(exact, "CIRCLE_POLYNOMIAL_FACTOR", F(4)):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "circle translation root"):
            exact.circle_limits("K16")


def test_t2d_circle_ratio_one_coefficient_mutation_is_rejected():
    with patch.object(exact, "CIRCLE_RATIO_K16_A", F(98, 303)):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "circle ratio identity"):
            exact.circle_limits("K16")


def test_t2d_facet_exact_decomposition_and_n64_n128_trend():
    # G-G_facet is the exact two-surd difference (never rounded for decisions).
    main_count = 0
    for n, element in CASES:
        values = exact.family_values(n, element)
        main = any(edge["u1"] == 0 for edge in values["e_star"])
        if main:
            main_count += 1
            assert values["G"] == values["G_facet"]
        else:
            assert values["G"] > values["G_facet"]
    assert main_count == 5
    for element in ("square", "octagon", "K16"):
        limit = exact.circle_limits(element)
        a, b = exact.family_values(64, element), exact.family_values(128, element)
        assert a["delta"] < b["delta"] < limit["disk"]
        assert a["translation"] < b["translation"] < limit["translation"]
        assert all(a["S"]) == (element != "square")
        assert all(b["S"]) == (element != "square")


def test_t2d_facet_one_number_mutation_is_rejected():
    with patch.object(exact, "FACET_RADICAND_ADDEND", 5):
        values = exact.family_values(4, "square")
        with unittest.TestCase().assertRaises(AssertionError):
            assert values["G"] == values["G_facet"]
