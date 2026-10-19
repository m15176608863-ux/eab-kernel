"""Whole-arc radial-work oracle versus exact polygon judge, not convergence.

The smooth oracle uses only affine rigid velocities and a polynomial identity.
It shares neither ContactSet2 geometry nor LP/DD construction with the judge.
The rational inscription tests are finite counterexamples to treating these
polygons as a certified smooth-curve approximation, not a general refinement
theorem and not a finite SE(2) motion certificate.
"""
from fractions import Fraction as Q

import pytest

from eab.adapters.tia2d import morphology_geometry
from eab.kernel2d.exact import polygons_overlap_exact
from tia2d_curvature_probe import (CENTERS, RADIUS, inscribed_circle_chain,
                                   polygon_certificate, smooth_circle_witness)


def test_true_circle_grid_has_exact_zero_normal_work_and_zero_frictionless_capacity():
    witness = smooth_circle_witness()
    assert witness["relative_angular_rates"] == (1, -1, -1, 1)
    assert witness["up_twists_at_origin"][2] == (0, 2, 0)
    assert all(row["radial_velocity_coefficients"] == (0, 0, 0, 0)
               for row in witness["arc_identities"])
    assert witness["downward_load_work"] == 2
    assert witness["contact_work"] == witness["fixed_support_work"] == 0
    assert witness["zero_force_feasible"] and witness["exact_frictionless_capacity"] == 0


@pytest.mark.parametrize("chords", (2, 4, 8, 16))
def test_inscribed_circle_polygons_retain_false_smooth_interlock_at_four_refinements(chords):
    model = inscribed_circle_chain(chords)
    for i, j in model.pairs:
        assert polygons_overlap_exact(model.bodies[i].vertices, model.bodies[j].vertices) == (0 if j == i + 1 else -1)
    for index, center in enumerate(CENTERS):
        shared = set(model.bodies[index].vertices) & set(model.bodies[index + 1].vertices)
        assert len(shared) == chords + 1
        assert all((x - center[0]) ** 2 + (y - center[1]) ** 2 == RADIUS ** 2 for x, y in shared)
    certificate = polygon_certificate(model, "inscribed")
    assert certificate["first_order_status"] == "ZERO_CONE"
    assert len(certificate["zero_certificates"]) == 18


def test_tia_g3_true_circle_grid_frozen_polygon_is_not_a_smooth_curve_claim():
    geometry = morphology_geometry("TIA-G3", amplitude=Q(1, 4), wavelength=Q(1, 2))
    certificate = polygon_certificate(geometry.assembly, "TIA-G3-A3-W0")
    assert certificate["first_order_status"] == "ZERO_CONE"
    assert smooth_circle_witness()["exact_frictionless_capacity"] == 0
