"""L3 frame/unit gates and independent actual-binary64 matrix oracles.

Signed permutations use exact orthogonal covariance, including axial mask
permutation and moment pseudoscalar signs. Random rotations are NEW rounded
inputs: an independent shared-edge walk constructs forces and moments about
physical anchors without contact/statics construction helpers. The exact LP
solver is shared only to solve that independently assembled matrix; all its
certificates are separately rechecked. No old classification or closed form
is asserted after arbitrary rotation and RN.
"""
from dataclasses import replace
from fractions import Fraction as Q
import math
import random

import pytest

from eab.adapters.tia2d import g1, g5
from eab.kernel2d.assembly import Body2
from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.exact import polygons_overlap_exact
from eab.kernel2d.sensitivity import build_limit_seed2, evaluate_sensitivity2
from eab.kernel2d.statics import (critical_parameter, limit_load_ideal_exact_2d,
                                 solve_limit_problem2)
from eab.oracle_construction import scalar_exact
from test_tia2d_statics import _problem, _verify


FRAMES = ((1, False, Q(1), (2**10, -2**10)),
          (2, True, Q(64), (-2**17, 2**10)),
          (3, True, Q(1, 8), (2**17, -2**17)),
          (1, False, Q(1, 2**20), (2**17, -2**17)))


def _rotate(vector, turn, reflect):
    x, y = vector
    if reflect:
        x = -x
    for _ in range(turn):
        x, y = -y, x
    return x, y


def _point(point, frame):
    turn, reflect, scale, offset = frame
    vector = _rotate(point, turn, reflect)
    return tuple(scale * vector[k] + offset[k] for k in (0, 1))


def _rounded_point_wrench(force, application, reference):
    """New binary64 wrench: decode inputs, compute exactly, RN torque once."""
    fx, fy = tuple(Q(v) for v in force)
    p, o = tuple(Q(v) for v in application), tuple(Q(v) for v in reference)
    moment = (p[0] - o[0]) * fy - (p[1] - o[1]) * fx
    return fx, fy, scalar_exact(moment)


def _assert_binary64_inputs(model):
    values = [Q(model.mu)]
    for body in model.bodies:
        values.extend(v for point in body.vertices for v in point)
        values.extend((*body.reference_point, *body.dof_anchor, *body.dead, *body.live))
    assert all(Q(scalar_exact(value)) == value for value in values)


def _model_frame(model, frame, dead_unit=Q(1), live_unit=Q(1)):
    turn, reflect, scale, offset = frame
    determinant = -1 if reflect else 1
    bodies = []
    for body in model.bodies:
        loads = []
        for wrench, unit in ((body.dead, dead_unit), (body.live, live_unit)):
            force = _rotate(wrench[:2], turn, reflect)
            loads.append((unit * force[0], unit * force[1], unit * scale * determinant * wrench[2]))
        mask = body.dof_mask
        if turn % 2:
            mask = mask[1], mask[0], mask[2]
        bodies.append(Body2.from_vertices(body.body_id, tuple(_point(p, frame) for p in body.vertices),
            reference_point=_point(body.reference_point, frame), dof_anchor=_point(body.dof_anchor, frame),
            boundary_type=body.boundary_type, dof_mask=mask, dead=loads[0], live=loads[1]))
    return replace(model, bodies=tuple(bodies))


def _edge_columns(model, contacts):
    """Independent endpoint/CCW-edge oracle; no production normal/moment helpers."""
    endpoints = {}
    for i in range(len(model.bodies) - 1):
        left, right = model.bodies[i], model.bodies[i + 1]
        shared = set(left.vertices) & set(right.vertices)
        assert len(shared) == 2
        incident = [(a, b) for a, b in zip(left.vertices, left.vertices[1:] + left.vertices[:1])
                    if a in shared and b in shared]
        assert len(incident) == 1
        a, b = incident[0]
        tangent = b[0] - a[0], b[1] - a[1]
        for point in shared:
            endpoints[(i, i + 1, point)] = tangent
    assert {(c.a, c.b, c.point) for c in contacts.constraints} == set(endpoints)
    columns = []
    for contact in contacts.constraints:
        tangent = endpoints[(contact.a, contact.b, contact.point)]
        assert contact.tangent == tangent
        for sign in (-1, 1):
            fx = -tangent[1] + sign * model.mu * tangent[0]
            fy = tangent[0] + sign * model.mu * tangent[1]
            column = []
            for i, body in enumerate(model.bodies):
                sense = 1 if i == contact.a else -1 if i == contact.b else 0
                dx = contact.point[0] - body.dof_anchor[0]
                dy = contact.point[1] - body.dof_anchor[1]
                wrench = sense * fx, sense * fy, sense * (dx * fy - dy * fx)
                column.extend(wrench[k] for k in range(3) if body.dof_mask[k])
            columns.append(tuple(column))
    loads = []
    for name in ("dead", "live"):
        values = []
        for body in model.bodies:
            fx, fy, moment = body.dead if name == "dead" else body.live
            dx, dy = (body.dof_anchor[k] - body.reference_point[k] for k in (0, 1))
            at_anchor = fx, fy, moment - dx * fy + dy * fx
            values.extend(at_anchor[k] for k in range(3) if body.dof_mask[k])
        loads.append(tuple(values))
    columns.append(loads[1])
    A = tuple(tuple(column[i] for column in columns) for i in range(len(loads[0])))
    return A, tuple(-v for v in loads[0]), (Q(0),) * (len(columns) - 1) + (Q(1),)


@pytest.mark.parametrize("frame", FRAMES)
@pytest.mark.parametrize("mu", (Q(1, 4), Q(2)))
def test_limit_exact_frames_keep_capacity_masks_anchors_and_mu_derivatives(frame, mu):
    base = g5(mu=mu, pressure=Q(3, 2))
    model = _model_frame(base, frame)
    _assert_binary64_inputs(model)
    contacts = assemble_contact_set2(model)
    assert contacts.status == "RESOLVED"
    result = limit_load_ideal_exact_2d(model, contacts)
    assert result.exact_value == min(3 * mu, Q(3))
    assert model.bodies[-1].reference_point != model.bodies[-1].dof_anchor
    expected_mask = (0, 1, 0) if frame[0] % 2 else (1, 0, 0)
    assert model.bodies[-1].dof_mask == expected_mask
    assert (result.problem.A, result.problem.b, result.problem.c) == _edge_columns(model, contacts)
    _verify(result)
    derivative = evaluate_sensitivity2(result)
    assert derivative.left_derivative == derivative.right_derivative == (3 if mu < 1 else 0)
    assert derivative.method == "mills_freund"


@pytest.mark.parametrize("frame", (FRAMES[0], FRAMES[-1]))
def test_released_rotation_physical_anchor_transforms_separately_from_reference(frame):
    model = _model_frame(g5(mu=2, dof_mask=(1, 0, 1), dof_anchor=(0, 0)), frame)
    _assert_binary64_inputs(model)
    result = limit_load_ideal_exact_2d(model)
    assert result.exact_value == Q(1, 3)
    assert (result.problem.A, result.problem.b, result.problem.c) == _edge_columns(model, result.problem.contact_set)
    _verify(result)


@pytest.mark.parametrize("geometry_scale", (Q(1, 2**20), Q(32)))
@pytest.mark.parametrize("dead_unit,live_unit", ((Q(8), Q(1)), (Q(1), Q(1, 4))))
def test_geometry_and_force_units_scale_independently(geometry_scale, dead_unit, live_unit):
    frame = 3, True, geometry_scale, (2**17, -2**10)
    model = _model_frame(g5(mu=Q(1, 4)), frame, dead_unit, live_unit)
    _assert_binary64_inputs(model)
    result = limit_load_ideal_exact_2d(model)
    assert result.exact_value == Q(1, 2) * dead_unit / live_unit
    derivative = evaluate_sensitivity2(result)
    assert derivative.left_derivative == derivative.right_derivative == 2 * dead_unit / live_unit
    _verify(result)


@pytest.mark.parametrize("orientation,height,threshold,attained,slope", (
    ("koureas", Q(1, 4), Q(15, 128), True, Q(15, 16)),
    ("unreversed", Q(1), Q(1, 4), False, Q(1)),
))
@pytest.mark.parametrize("frame", (FRAMES[1], FRAMES[-1]))
def test_critical_open_closed_threshold_and_shared_t_seed_exact_frame_covariance(
        orientation, height, threshold, attained, slope, frame):
    base = g1(t=Q(1, 4), height=height, orientation=orientation)
    base_contacts = assemble_contact_set2(base)
    model = _model_frame(base, frame)
    _assert_binary64_inputs(model)
    contacts = assemble_contact_set2(model)
    result = critical_parameter(model, contact_set=contacts, max_steps=10)
    assert result.exact_threshold == threshold and result.attained is attained
    assert result.threshold_proof and result.critical_polynomials
    for certificate in (result.lower_certificate, result.upper_certificate, result.threshold_certificate):
        _verify(certificate)
        actual_model = replace(model, mu=certificate.problem.mu)
        assert (certificate.problem.A, certificate.problem.b, certificate.problem.c) == _edge_columns(actual_model, contacts)
    lookup = {(c.a, c.b, _point(c.point, frame)): c for c in base_contacts.constraints}
    turn, reflect, scale, offset = frame
    determinant = -1 if reflect else 1
    seeds = {}
    for contact in result.threshold_certificate.problem.contact_set.constraints:
        original = lookup[(contact.a, contact.b, contact.point)]
        face_slope = original.tangent[0] / original.tangent[1]
        dp = (4 * face_slope * (original.point[1] - height / 2), Q(0))
        dt = (4 * original.tangent[0], Q(0))
        seeds[contact.label] = (tuple(scale * v for v in _rotate(dp, turn, reflect)),
                                tuple(determinant * scale * v for v in _rotate(dt, turn, reflect)))
    seed = build_limit_seed2(result.threshold_certificate.problem, contact_seeds=seeds, parameter="t")
    derivative = evaluate_sensitivity2(result, seed, parameter="t")
    assert derivative.left_derivative == derivative.right_derivative == slope
    assert derivative.method == "implicit_certificate"


def test_random_rotated_rn_inputs_use_actual_edge_and_wrench_oracle_not_old_threshold():
    rng = random.Random(20261019)
    for _ in range(2):
        angle = rng.uniform(-2, 2)
        co, si = Q(math.cos(angle)), Q(math.sin(angle))
        source = g1(t=Q(1, 4), height=Q(1, 4), mu=Q(1, 8))
        shared = {p: (scalar_exact(co * p[0] - si * p[1] + 2**10),
                      scalar_exact(si * p[0] + co * p[1] - 2**17))
                  for body in source.bodies for p in body.vertices}
        force = Q(scalar_exact(si)), Q(scalar_exact(-co))
        application = (Q(scalar_exact(-si * Q(1, 8) + 2**10)),
                       Q(scalar_exact(co * Q(1, 8) - 2**17)))
        bodies = []
        for body in source.bodies:
            x, y = body.reference_point
            reference = Q(scalar_exact(co * x - si * y + 2**10)), Q(scalar_exact(si * x + co * y - 2**17))
            live = _rounded_point_wrench(force, application, reference) if any(body.live) else (0, 0, 0)
            bodies.append(Body2.from_vertices(body.body_id, tuple(shared[p] for p in body.vertices),
                reference_point=reference, dof_anchor=reference, boundary_type=body.boundary_type,
                dof_mask=body.dof_mask, live=live))
        model = replace(source, bodies=tuple(bodies))
        _assert_binary64_inputs(model)
        assert all(polygons_overlap_exact(model.bodies[i].vertices, model.bodies[j].vertices)
                   == (0 if j == i + 1 else -1) for i, j in model.pairs)
        # Original parallelism and the aligned G1 closed-form hypothesis are
        # not assumed after RN. Check the NEW exact matrix instead.
        contacts = assemble_contact_set2(model)
        assert contacts.status == "RESOLVED"
        result = limit_load_ideal_exact_2d(model, contacts)
        A, b, c = _edge_columns(model, contacts)
        assert (result.problem.A, result.problem.b, result.problem.c) == (A, b, c)
        independent = solve_limit_problem2(_problem(A, b, c))
        assert result.status == independent.status and result.exact_value == independent.exact_value
        _verify(result)
        _verify(independent)
        critical = critical_parameter(model, contact_set=contacts, max_steps=2)
        assert critical.lower_certificate is not None and critical.upper_certificate is not None
        for endpoint in (critical.lower_certificate, critical.upper_certificate):
            _verify(endpoint)
            new_model = replace(model, mu=endpoint.problem.mu)
            assert (endpoint.problem.A, endpoint.problem.b, endpoint.problem.c) == _edge_columns(new_model, contacts)
