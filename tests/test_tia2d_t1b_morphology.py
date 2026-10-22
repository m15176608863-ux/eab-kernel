"""T1b geometry, independent rational jets, and hand-wrench branch oracles.

The main threshold reference is hand elimination of the side block's two
collinear resultants on the upper tooth segments, not another call to the
production geometry or LP. Its applicable finite cells also retain full
production primal/dual certificates; no all-parameter closed form is claimed.
"""
from dataclasses import replace
from fractions import Fraction as Q
import random

import pytest

from eab.adapters.tia2d import (g1_morphology, g1_morphology_seed, g1_threshold,
                              morphology_geometry, tolerance_dovetail, tolerance_knob)
from eab.kernel2d.assembly import Body2
from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.exact import polygons_overlap_exact, signed_area2
from eab.kernel2d.sensitivity import evaluate_sensitivity2
from eab.kernel2d.statics import (build_limit_problem2, critical_parameter,
                                 limit_load_ideal_exact_2d)
from tia2d_t1b_morphology import certificate_arithmetic, diagnose, scan_parameters


@pytest.mark.parametrize("family,phase,periods,asymmetry", [
    ("sawtooth", Q(0), 1, Q(1, 2)), ("sawtooth", Q(1, 4), 2, Q(1, 4)),
    ("sawtooth", Q(1, 2), 4, Q(3, 4)), ("kinked", Q(0), 1, Q(1, 4))])
def test_t1b_profiles_are_true_shared_rational_polygons(family, phase, periods, asymmetry):
    g = g1_morphology(family=family, phase=phase, periods=periods, asymmetry=asymmetry)
    assert g.wavelength * periods == g.height
    assert all(body.dead == (0, 0, 0) for body in g.assembly.bodies)
    assert g.assembly.bodies[2].live == (0, -1, Q(5, 8))
    for i, j in g.assembly.pairs:
        assert polygons_overlap_exact(g.assembly.bodies[i].vertices, g.assembly.bodies[j].vertices) == (0 if j == i + 1 else -1)
    for k, face in enumerate(g.interfaces):
        for point in face:
            assert any(p is point for p in g.assembly.bodies[k].original_vertices)
            assert any(p is point for p in g.assembly.bodies[k + 1].original_vertices)
    assert g.assembly.bodies[0].boundary_type == g.assembly.bodies[-1].boundary_type == "FIXED_BODY"
    assert len({g1_morphology(periods=n).interfaces for n in (1, 2, 4)}) == 3


def test_t1b_profile_input_guards_and_period_independence():
    assert g1_morphology(height=Q(1, 8), wavelength=Q(1, 32)).periods == 4
    for parameters in ({"family": "smooth"}, {"phase": Q(1, 3)}, {"amplitude": -1},
                       {"asymmetry": 0}, {"periods": 3}, {"height": 0},
                       {"wavelength": 0}, {"wavelength": Q(1, 7)},
                       {"periods": 2, "wavelength": Q(1, 16)},
                       {"family": "kinked", "phase": Q(1, 4)}):
        with pytest.raises(ValueError):
            g1_morphology(**parameters)


@pytest.mark.parametrize("family,phase", [("sawtooth", Q(1, 4)), ("kinked", Q(0))])
@pytest.mark.parametrize("parameter", ("amplitude", "tilt"))
def test_t1b_profile_jets_match_exact_affine_matrix_derivatives(family, phase, parameter):
    g = g1_morphology(family=family, phase=phase)
    contacts = assemble_contact_set2(g.assembly)
    problem = build_limit_problem2(g.assembly, contacts, Q(1, 8))
    seed = g1_morphology_seed(problem, g, parameter)
    step = Q(1, 2**20)
    matrices = []
    features = lambda cs: tuple((c.label[0], c.label[1], c.label[3], c.label[4]) for c in cs.constraints)
    for sign in (-1, 1):
        other = g1_morphology(family=family, phase=phase,
            **{parameter: getattr(g, parameter) + sign * step})
        cs = assemble_contact_set2(other.assembly)
        assert features(cs) == features(contacts)
        matrices.append(build_limit_problem2(other.assembly, cs, Q(1, 8)).A)
    # The moment is at most quadratic, so the centered difference is an exact
    # algebraic jet oracle, not a finite-difference threshold derivative.
    assert seed.dA == tuple(tuple((hi - lo) / (2 * step) for lo, hi in zip(a, b))
                           for a, b in zip(*matrices))
    assert not any(seed.db) and not any(seed.dc)


@pytest.mark.parametrize("tilt", (Q(3, 32), Q(11, 128)))
@pytest.mark.parametrize("amplitude", (Q(1, 2048), Q(3, 4096), Q(1, 1024)))
def test_t1b_upper_tooth_hand_wrench_threshold_and_implicit_derivatives(tilt, amplitude):
    g = g1_morphology(tilt=tilt, amplitude=amplitude)
    h, ell = g.height / 2, Q(2)
    slope = tilt - 2 * amplitude / g.height
    # Side block collinearity: q=H/(ell-slope*H). Coulomb resultant:
    # q=(slope-mu)/(1+slope*mu). Eliminate q, not production LP data.
    q = h / (ell - slope * h)
    expected = (slope - q) / (1 + slope * q)
    assert expected == slope - h / ell * (1 + slope * slope)
    c = critical_parameter(g.assembly, max_steps=32)
    assert c.exact_threshold == expected and c.attained is True
    for cert in (c.lower_certificate, c.upper_certificate, c.threshold_certificate):
        assert certificate_arithmetic(cert)
    for parameter, derivative in (("tilt", 1 - 2 * h / ell * slope),
                                  ("amplitude", -2 / g.height * (1 - 2 * h / ell * slope))):
        seed = g1_morphology_seed(c.threshold_certificate.problem, g, parameter)
        answer = evaluate_sensitivity2(c, seed, parameter=parameter)
        assert answer.method == "implicit_certificate"
        assert answer.differentiability == "smooth"
        assert answer.left_derivative == answer.right_derivative == derivative


def test_t1b_nondegenerate_shape_and_t1a_zero_control():
    rows = [diagnose(amplitude=a, mobility=False, max_steps=36)[1]
            for a in (Q(1, 4096), Q(1, 2048), Q(1, 1024))]
    assert len({row["mu_exact"] for row in rows}) == 3
    assert all(Q(row["mu_exact"]) > 0 for row in rows)
    for family in ("TIA-G2", "TIA-G3", "TIA-G4"):
        old = critical_parameter(morphology_geometry(family).assembly, max_steps=4)
        assert old.exact_threshold == 0 and old.attained is True
    flat = critical_parameter(g1_morphology(amplitude=0).assembly, max_steps=24)
    assert (flat.exact_threshold, flat.attained) == g1_threshold(t=Q(3, 32), height=Q(1, 16))
    row = diagnose(amplitude=0, mobility=False, max_steps=24)[1]
    assert row["derivatives"]["amplitude"]["right"] is None
    assert Q(row["derivatives"]["tilt"]["right"]) == 1 - Q(1, 16) * Q(3, 32)


def test_t1b_phase_changes_actual_threshold_and_preserves_an_open_endpoint():
    rows = [diagnose(phase=phase, mobility=False, max_steps=36)[1]
            for phase in (Q(0), Q(1, 4), Q(1, 2))]
    intervals = [(Q(r["mu_lo"]), Q(r["mu_hi"])) for r in rows]
    assert all(a[1] < b[0] or b[1] < a[0] for i, a in enumerate(intervals) for b in intervals[i + 1:])
    g = g1_morphology(tilt=Q(11, 128), amplitude=Q(1, 1024), phase=Q(1, 2))
    c = critical_parameter(g.assembly, max_steps=32)
    assert c.exact_threshold == Q(7, 128) and c.attained is False
    assert c.threshold_certificate.status == "OPTIMAL"
    assert certificate_arithmetic(c.threshold_certificate)


def _rotate_exact(p, c, s):
    return c * p[0] - s * p[1], s * p[0] + c * p[1]


def _transform_point(p, c, s, scale, offset):
    rotated = _rotate_exact(p, c, s)
    return tuple(scale * v + d for v, d in zip(rotated, offset))


def _frame(assembly, u, scale, offset, force_unit):
    c, s = (1 - u * u) / (1 + u * u), 2 * u / (1 + u * u)
    bodies = []
    for body in assembly.bodies:
        loads = []
        for load in (body.dead, body.live):
            force = _rotate_exact(load[:2], c, s)
            loads.append((force_unit * force[0], force_unit * force[1], force_unit * scale * load[2]))
        bodies.append(Body2.from_vertices(body.body_id,
            tuple(_transform_point(p, c, s, scale, offset) for p in body.vertices),
            reference_point=_transform_point(body.reference_point, c, s, scale, offset),
            dof_anchor=_transform_point(body.dof_anchor, c, s, scale, offset),
            boundary_type=body.boundary_type, dof_mask=body.dof_mask, dead=loads[0], live=loads[1]))
    return replace(assembly, bodies=tuple(bodies))


@pytest.mark.parametrize("translation,scale,force_unit", [(Q(0), Q(1), Q(1)), (Q(1000), Q(8), Q(3, 2)),
                                               (Q(100000), Q(1, 2**20), Q(11))])
def test_t1b_rational_rotation_large_translation_and_units(translation, scale, force_unit):
    u = Q(random.Random(601).randint(1, 7), 8)
    model = _frame(g1_morphology().assembly, u, scale, (translation, -translation), force_unit)
    threshold = Q(16359, 262144)
    for mu, expected in ((threshold - Q(1, 2**20), "OPTIMAL"),
                         (threshold, "UNBOUNDED"), (threshold + Q(1, 2**20), "UNBOUNDED")):
        result = limit_load_ideal_exact_2d(model, mu=mu)
        assert result.status == expected
        assert certificate_arithmetic(result)


@pytest.mark.parametrize("generator", (tolerance_dovetail, tolerance_knob))
def test_t1b_tolerance_generators_have_zero_clearance_and_positive_rings(generator):
    case = generator()
    assert signed_area2(case["moving"]) > 0
    assert all(signed_area2(p) > 0 for p in case["obstacles"])
    assert [polygons_overlap_exact(case["moving"], p) for p in case["obstacles"]] == [0, 0, 0]


@pytest.mark.slow
@pytest.mark.parametrize("parameters", scan_parameters())
def test_t1b_design_curve_cases_have_exact_certificates_and_mobility(parameters):
    case, row = diagnose(**parameters)
    assert case["contact_status"] == "RESOLVED" and case["certificate_arithmetic"]
    assert row["first_order"] in ("ZERO_CONE", "NONZERO_CONE")
    assert row["mu_hi"] is not None
    if row["mu_exact"] is None:
        assert Q(row["mu_hi"]) - Q(row["mu_lo"]) <= Q(1, 2**40)
        assert row["attained"] is None
