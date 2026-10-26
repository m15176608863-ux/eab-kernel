"""Whole-turn/whole-ray exact gates; no production path primitive is shared.

Negative controls mutate input geometry or arithmetic INSIDE the helper
before its semantic assertions run. No fake returned result is appended.
"""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from eab.adapters.tia2d import tolerance_knob

import tests.t2d_knob_family_exact as exact
import tests.t2d_critical_escape_exact as escape


CASES = tuple((n, k) for n in (4, 8, 16, 32) for k in ("square", "octagon", "K16")
              if k != "square" or n == 4)


def test_t2d_independent_whole_cavity_matches_production_generator():
    for n in (4, 8, 16, 32):
        actual = tolerance_knob(segments=n)
        assert actual["moving"] == exact.verify_family_geometry(n)["A"]
        assert actual["obstacles"] == escape.truth_obstacles(n)


def test_t2d_nine_exact_critical_rotations_and_projection_equalities():
    results = []
    for n, element in CASES:
        result = escape.verify_critical_escape(n, element)
        assert result["status"] == "EXACT_CRITICAL_ESCAPE"
        assert result["horizontal"] == (-F(1, 2), F(1, 2))
        assert result["radius_squared"] < result["wall_radius_squared"]
        assert result["disk_support_checks"] == 2*n
        assert result["rotated_witnesses"] == ((-F(1, 2), 1), (F(1, 2), 1))
        results.append((n, element, result["delta"], result["cosine"], result["sine"]))
    assert len(results) == 9
    # Parameterization must produce distinct exact thresholds, not one
    # reused N=4 calculation relabeled nine times.
    assert all(a[2] != b[2] for i, a in enumerate(results) for b in results[i+1:])


def test_t2d_square_finer_facets_do_not_pass_the_strip_theorem():
    for n in (8, 16, 32):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "S fails"):
            escape.verify_critical_escape(n, "square")


def test_t2d_rotation_coefficient_mutation_is_semantically_rejected():
    with patch.object(escape, "COSINE_FACTOR", F(2)):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "exactly orthogonal"):
            escape.verify_critical_escape(4, "square")


def test_t2d_active_normal_orientation_mutation_is_rejected():
    original = escape.rotation_to_horizontal

    def wrong_sense(edge):
        cosine, sine = original(edge)
        return cosine, -sine

    with patch.object(escape, "rotation_to_horizontal", wrong_sense):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "align the active normal"):
            escape.verify_critical_escape(8, "K16")


def test_t2d_disk_radius_numeric_mutation_is_rejected():
    with patch.object(escape, "HALF_NECK", F(51, 100)):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "disk is not contained"):
            escape.verify_critical_escape(16, "octagon")


def test_t2d_disk_subset_rejects_a_tiny_positive_threshold_excess():
    # The failure must be containment, not the later active-support equality.
    for n, element in tuple(exact.TABLE):
        delta = exact.family_values(n, element)["delta"] + F(1, 1 << 40)
        with unittest.TestCase().assertRaisesRegex(AssertionError, "disk is not contained"):
            escape.verify_disk_subset(n, element, delta)


def test_t2d_upward_ray_geometry_mutation_is_rejected():
    original = exact.family_geometry

    def pinched_neck(n):
        geometry = original(n)
        profile = list(geometry["right_profile"])
        y, _ = profile[-2]
        profile[-2] = (y, F(49, 100))
        geometry["right_profile"] = tuple(profile)
        return geometry

    with patch.object(exact, "family_geometry", pinched_neck):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "upper cavity violates"):
            escape.verify_upward_closure(32)


def test_t2d_lower_ray_monotonicity_mutation_is_rejected():
    original = exact.family_geometry

    def reversed_lower_width(n):
        geometry = original(n)
        profile = list(geometry["right_profile"])
        y, _ = profile[1]
        profile[1] = (y, F(2))
        geometry["right_profile"] = tuple(profile)
        return geometry

    with patch.object(exact, "family_geometry", reversed_lower_width):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "lower cavity narrows"):
            escape.verify_upward_closure(16)


def test_t2d_floor_intrusion_numeric_mutation_is_rejected():
    with patch.object(escape, "FLOOR_TOP", F(1)):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "floor intrudes"):
            escape.verify_upward_closure(8)
