"""All-chord translation thresholds cross-checked by production free space.

Primary erosion oracle is the independent rational section infimum and its
finite affine partition, not production Minkowski sums or contact segments.
Production translation_component independently checks rational path/barrier
certificates for that body. Small cases additionally compare the full ring
against the production arrangement erosion. No floating point is used.
"""
from fractions import Fraction as F
from unittest import TestCase
from unittest.mock import patch

from eab.adapters.tia2d import tolerance_knob
from eab.kernel2d.erosion import erode_polygon_exact
from eab.kernel2d.translation_space import critical_tolerance, translation_component
import tests.t2d_knob_family_exact as exact
import tests.t2d_sections_exact as sections


FAMILIES = (4, 8, 16, 32)
ELEMENTS = ("square", "octagon", "K16")


def _verify_threshold(n, element):
    data = tolerance_knob(segments=n)
    assert data["moving"] == exact.family_geometry(n)["A"]
    threshold = exact.family_values(n, element)["translation"]
    epsilon = F(1, 4096)
    outcomes = []
    for delta, status in ((threshold-epsilon, "TRAPPED_TRANSLATION"),
                          (threshold, "ESCAPABLE_TRANSLATION"),
                          (threshold+epsilon, "ESCAPABLE_TRANSLATION")):
        body = sections.eroded_polygon(n, element, delta)
        half_width = max(x for x, _ in body)
        assert half_width == sections.eroded_half_width(n, element, delta, F(1)), "widest horizontal section left y=1"
        if delta == threshold:
            assert half_width == F(1, 2), "critical translation seam is not width one"
        elif delta < threshold:
            assert half_width > F(1, 2), "subcritical translation section does not block neck"
        else:
            assert half_width < F(1, 2), "supercritical translation section does not fit neck"
        result = translation_component(body, data["obstacles"])
        assert result.status == status, (n, element, delta, result.status, result.reason)
        assert result.verification.valid, "production path/barrier certificate is invalid"
        if status == "TRAPPED_TRANSLATION":
            assert result.bounds_verification.valid
        outcomes.append((delta, body, result.status))
    assert len({body for _, body, _ in outcomes}) == 3, "distinct delta inputs collapsed to one body"
    return outcomes


def test_t2d_n4_translation_thresholds_match_exact_free_space():
    for element in ELEMENTS:
        _verify_threshold(4, element)


def test_t2d_n8_translation_thresholds_match_exact_free_space():
    for element in ELEMENTS:
        _verify_threshold(8, element)


def test_t2d_n16_translation_thresholds_match_exact_free_space():
    for element in ELEMENTS:
        _verify_threshold(16, element)


def test_t2d_n32_translation_thresholds_match_exact_free_space():
    for element in ELEMENTS:
        _verify_threshold(32, element)


def test_t2d_translation_threshold_rejects_internal_support_shift():
    original = exact.support

    def shifted(element, nx, ny):
        return original(element, nx, ny)+F(1, 4096)

    with patch.object(exact, "support", side_effect=shifted):
        with TestCase().assertRaisesRegex(AssertionError, "critical translation seam"):
            _verify_threshold(4, "square")


def test_t2d_full_production_critical_tolerance_has_exact_critical_upper_endpoint():
    data = tolerance_knob(segments=4)
    threshold = F(1, 3)
    result = critical_tolerance(data["moving"], data["obstacles"],
                                threshold-F(1, 4096), threshold+F(1, 4096),
                                iterations=1, erode_obstacles=False)
    assert result["status"] == "CERTIFIED_BRACKET"
    assert result["low"] == threshold-F(1, 4096) and result["high"] == threshold
    assert result["low_result"].verification.valid and result["high_result"].verification.valid
    assert result["attained"] is None


def test_t2d_sections_match_production_arrangement_erosion_on_all_elements():
    for n in (4, 8):
        data = exact.family_geometry(n)
        for element in ELEMENTS:
            threshold = exact.family_values(n, element)["translation"]
            for delta in (F(0), threshold-F(1, 4096), threshold):
                expected = sections.eroded_polygon(n, element, delta)
                actual = erode_polygon_exact(data["A"], delta, exact.convex_hull(exact.element_vertices(element)))
                assert actual.status == "ACCEPTED" and actual.reason is None
                assert actual.polygon == expected, "section oracle differs from production arrangement erosion"
                assert actual.rings == (expected,)


def test_t2d_section_partition_rejects_internal_affine_offset_mutation():
    original = sections._section_lines

    def shifted(cavity, shape, delta, middle):
        return tuple((slope, intercept+F(1, 4096))
                     for slope, intercept in original(cavity, shape, delta, middle))

    with patch.object(sections, "_section_lines", side_effect=shifted):
        with TestCase().assertRaisesRegex(AssertionError, "independent section infimum mismatch"):
            sections.eroded_polygon(4, "octagon", F(12, 29))


def test_t2d_section_partition_rejects_internal_event_omission():
    original = sections._verification_cuts

    def missing(cavity, shape, delta, profile):
        cuts = original(cavity, shape, delta, profile)
        return cuts[:1]+cuts[2:]

    with patch.object(sections, "_verification_cuts", side_effect=missing):
        with TestCase().assertRaisesRegex(AssertionError, "missing section .* event"):
            sections.eroded_polygon(4, "octagon", F(12, 29))


def test_t2d_section_partition_rejects_omitted_zero_width_remnant():
    original = sections.eroded_half_width

    def hidden_remnant(n, element, delta, height):
        if height == F(1, 3):
            return F(0)
        return original(n, element, delta, height)

    profile = sections._raw_profile(4, "square", F(1, 3))
    assert F(1, 3) < profile[0][0]
    with patch.object(sections, "eroded_half_width", side_effect=hidden_remnant):
        with TestCase().assertRaisesRegex(AssertionError, "omitted closed erosion slice"):
            sections.verify_section_profile(4, "square", F(1, 3), profile)


def test_t2d_section_lower_envelope_keeps_internal_crossing_and_zero_clip():
    lines = ((F(1), F(0)), (F(-1), F(2)), (F(0), F(3)))
    assert sections._lower_envelope(lines) == ((F(1), F(0), None), (F(-1), F(2), F(1)))
    for n in FAMILIES:
        for element in ELEMENTS:
            delta = exact.family_values(n, element)["translation"]
            profile = sections._raw_profile(n, element, delta)
            assert profile[0][1] == 0, "lower endpoint must be clipped at the exact zero"
            assert sections.eroded_half_width(n, element, delta, profile[0][0]) == 0
            assert sections.verify_section_profile(n, element, delta, profile)[1] > 0


def test_t2d_sections_reject_nonexact_and_degenerate_inputs():
    for bad in ("1/3", object(), [1, 3]):
        with TestCase().assertRaises(TypeError):
            sections.eroded_polygon(4, "square", bad)
    for bad in (F(-1), F(1, 2), F(2)):
        with TestCase().assertRaises(ValueError):
            sections.eroded_polygon(4, "square", bad)
