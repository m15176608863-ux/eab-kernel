"""Exact fixed-basis and bounded-optimal-face directional derivatives.

The associated profile1 model uses the original unnormalized matrices. A
nonzero optimal-face recession direction is reported conservatively as
singular, not as proof of a discontinuity. Tests: test_tia2d_sensitivity.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as Q

from eab import lp
from .statics import CriticalParameter2, LimitResult2, _cross, _dot, _project, _run
from .algebraic import p_derivative, p_eval


@dataclass(frozen=True)
class LimitSeed2:
    dA: tuple[tuple[Q, ...], ...]
    db: tuple[Q, ...]
    dc: tuple[Q, ...]
    parameter: str = "mu"


@dataclass(frozen=True)
class SensitivityResult2:
    call_status: str
    mathematical_status: str | None
    differentiability: str
    quality: str = "exact_jet"
    selected_piece: object = None
    tied_labels: tuple = ()
    near_labels: tuple = ()
    piece_jacobians: tuple = ()
    directional_derivative: Q | None = None
    left_derivative: Q | None = None
    right_derivative: Q | None = None
    reason: str | None = None
    validity_conditions: tuple = ("L1接触骨架不变",)
    sensitivity_model: str = "ideal_exact_2d"
    parameter: str = "mu"
    method: str | None = None
    primal_recession_ray: tuple | None = None
    dual_recession_ray: tuple | None = None
    forward_certificate: tuple | None = None
    reverse_certificate: tuple | None = None
    display_status: str = "NOT_APPLICABLE"
    implicit_components: tuple = ()

def build_limit_seed2(problem, *, mu_seed=0, contact_seeds=None, dead_seeds=None,
                      live_seeds=None, parameter="mu"):
    """Propagate exact point/tangent/load seeds, keeping both origins constant.

contact_seeds maps labels to (dp,dT). Loads are exact wrench derivatives
about the same frozen reference points. Shared geometric parameters must be
seeded consistently by the caller; no finite differences are used here.
"""
    dmu = Q(mu_seed)
    contact_seeds = {} if contact_seeds is None else contact_seeds
    dead_seeds = {} if dead_seeds is None else dead_seeds
    live_seeds = {} if live_seeds is None else live_seeds
    assembly = problem.assembly
    columns = []
    for contact in problem.contact_set.constraints:
        dp, dt = contact_seeds.get(contact.label, ((0, 0), (0, 0)))
        dp, dt = tuple(Q(v) for v in dp), tuple(Q(v) for v in dt)
        if len(dp) != 2 or len(dt) != 2:
            raise ValueError("point and tangent seeds need two components")
        tangent = contact.tangent
        normal, dn = (-tangent[1], tangent[0]), (-dt[1], dt[0])
        for sign in (-1, 1):
            force = tuple(normal[k] + sign * problem.mu * tangent[k] for k in range(2))
            df = tuple(dn[k] + sign * (dmu * tangent[k] + problem.mu * dt[k]) for k in range(2))
            column = []
            for i, body in enumerate(assembly.bodies):
                sense = int(i == contact.a) - int(i == contact.b)
                arm = tuple(p - o for p, o in zip(contact.point, body.reference_point))
                dm = _cross(dp, force) + _cross(arm, df)
                column.extend(_project(body, (sense * df[0], sense * df[1], sense * dm)))
            columns.append(tuple(column))
    live = tuple(v for body in assembly.bodies
                 for v in _project(body, tuple(Q(x) for x in live_seeds.get(body.body_id, (0, 0, 0)))))
    dead = tuple(-v for body in assembly.bodies
                 for v in _project(body, tuple(Q(x) for x in dead_seeds.get(body.body_id, (0, 0, 0)))))
    columns.append(live)
    dA = tuple(tuple(col[i] for col in columns) for i in range(len(problem.b)))
    return LimitSeed2(dA, dead, (Q(0),) * len(problem.c), parameter)


def _inverse(matrix):
    n = len(matrix)
    work = [[Q(v) for v in row] + [Q(i == k) for k in range(n)] for i, row in enumerate(matrix)]
    for j in range(n):
        pivot = next((i for i in range(j, n) if work[i][j]), None)
        if pivot is None:
            return None
        work[j], work[pivot] = work[pivot], work[j]
        scale = work[j][j]
        work[j] = [v / scale for v in work[j]]
        for i in range(n):
            if i != j and work[i][j]:
                scale = work[i][j]
                work[i] = [a - scale * b for a, b in zip(work[i], work[j])]
    return tuple(tuple(row[n:]) for row in work)


def _null_vector(matrix, n):
    """One exact null vector, or None when the columns are independent."""
    work = [[Q(v) for v in row] for row in matrix]
    pivots = []
    for j in range(n):
        pivot = next((i for i in range(len(pivots), len(work)) if work[i][j]), None)
        if pivot is None:
            continue
        row = len(pivots)
        work[row], work[pivot] = work[pivot], work[row]
        scale = work[row][j]
        work[row] = [v / scale for v in work[row]]
        for i in range(len(work)):
            if i != row and work[i][j]:
                scale = work[i][j]
                work[i] = [a - scale * b for a, b in zip(work[i], work[row])]
        pivots.append(j)
    free = next((j for j in range(n) if j not in pivots), None)
    if free is None:
        return None
    ray = [Q(0)] * n
    ray[free] = 1
    for i, j in enumerate(pivots):
        ray[j] = -work[i][free]
    return tuple(ray)


def _feasible(A, b, n):
    result = _run(A, b, [Q(0)] * n)
    if result.status == lp.INFEASIBLE:
        return None
    if result.status != lp.OPTIMAL:
        raise ArithmeticError("zero objective feasibility state")
    return tuple(result.exact_x)


def optimal_face_recession2(problem):
    """Exact recession witnesses for the original primal and dual optima."""
    A, b, c = problem.A, problem.b, problem.c
    m, n = len(b), len(c)
    primal = _feasible(list(A) + [c, (Q(1),) * n], [Q(0)] * (m + 1) + [Q(1)], n)
    transposed = tuple(tuple(A[i][j] for i in range(m)) for j in range(n))
    dual = _null_vector(transposed, m)
    if dual is None:
        rows = []
        for j in range(n):
            column = transposed[j]
            rows.append(list(column) + [-v for v in column]
                        + [-Q(j == k) for k in range(n)])
        rows.append(list(b) + [-v for v in b] + [Q(0)] * n)
        rows.append([Q(0)] * (2 * m) + [Q(1)] * n)
        witness = _feasible(rows, [Q(0)] * (n + 1) + [Q(1)], 2 * m + n)
        if witness is not None:
            dual = tuple(witness[i] - witness[m + i] for i in range(m))
    if dual is not None and (_dot(b, dual) != 0 or not any(dual)
                             or any(_dot(column, dual) < 0 for column in transposed)):
        raise ArithmeticError("dual recession verification failed")
    return primal, dual


def _stable(result):
    A, c = result.problem.A, result.problem.c
    m, n = len(A), len(c)
    basis = result.basis
    if len(basis) != m or len(set(basis)) != m or any(j >= n for j in basis):
        return False
    B = tuple(tuple(A[i][j] for j in basis) for i in range(m))
    if _inverse(B) is None or any(result.exact_x[j] <= 0 for j in basis):
        return False
    return all(sum(A[i][j] * result.exact_y[i] for i in range(m)) != c[j]
               for j in range(n) if j not in basis)


def _mills(result, seed, sign):
    """Maximum-form Mills/Freund LP; s is represented by two nonnegative parts."""
    A, b, c, value = result.problem.A, result.problem.b, result.problem.c, result.exact_value
    m, n = len(b), len(c)
    rows = [list(row) + [Q(0)] * (n + 2) for row in A]
    rows.append(list(c) + [Q(0)] * (n + 2))
    rhs = list(b) + [value] + [sign * Q(v) for v in seed.db]
    for i in range(m):
        rows.append([sign * v for v in seed.dA[i]] + list(A[i]) + [b[i], -b[i]])
    objective = [sign * v for v in seed.dc] + list(c) + [value, -value]
    answer = _run(rows, rhs, objective)
    if answer.status != lp.OPTIMAL:
        return None, None
    x, y = tuple(answer.exact_x), tuple(answer.exact_y)
    derivative = _dot(objective, x)
    if (_dot(rhs, y) != derivative or any(v < 0 for v in x)
            or any(_dot(row, x) != v for row, v in zip(rows, rhs))
            or any(sum(rows[i][j] * y[i] for i in range(len(rows))) < objective[j]
                   for j in range(len(objective)))):
        raise ArithmeticError("directional LP certificate failed")
    return derivative, (x, y)


def evaluate_sensitivity2(result: LimitResult2 | CriticalParameter2, seed: LimitSeed2 | None = None,
                          *, parameter="mu", tied_labels=(),
                          validity_conditions=("L1接触骨架不变",),
                          positive_direction_valid=True, negative_direction_valid=True,
                          threshold_mu_seed: LimitSeed2 | None = None):
    """Return a direction derivative, never an arbitrary optimal basis slope.

At mu=0 the original dual optimal face may have nonzero recession; the
contract then returns singular/possibly_discontinuous, even if a closed-form
right derivative happens to exist. Left slopes are minus the reverse-query
derivative, not the reverse-query value itself.
"""
    conditions = tuple(dict.fromkeys(("L1接触骨架不变",) + tuple(validity_conditions)
                                     + result.validity_conditions))
    if isinstance(result, CriticalParameter2):
        return _threshold_sensitivity2(result, seed, threshold_mu_seed, parameter, tuple(tied_labels),
                                       conditions, positive_direction_valid, negative_direction_valid)
    if result.call_status != "OK" or result.status != "OPTIMAL":
        return SensitivityResult2(result.call_status, result.status, "unresolved",
                                  reason="finite_optimum_required", parameter=parameter, tied_labels=tuple(tied_labels), validity_conditions=conditions)
    if seed is None:
        if parameter != "mu":
            return SensitivityResult2("UNSUPPORTED", result.status, "unsupported",
                                      reason="exact_seed_required", parameter=parameter, tied_labels=tuple(tied_labels), validity_conditions=conditions)
        seed = build_limit_seed2(result.problem, mu_seed=1)
    try:
        seed = LimitSeed2(tuple(tuple(Q(v) for v in row) for row in seed.dA),
                          tuple(Q(v) for v in seed.db), tuple(Q(v) for v in seed.dc), seed.parameter)
    except (ValueError, TypeError, OverflowError):
        return SensitivityResult2("INVALID_INPUT", result.status, "unresolved",
                                  reason="invalid_exact_seed", parameter=parameter, tied_labels=tuple(tied_labels), validity_conditions=conditions)
    m, n = len(result.problem.b), len(result.problem.c)
    if (len(seed.dA) != m or any(len(row) != n for row in seed.dA)
            or len(seed.db) != m or len(seed.dc) != n):
        return SensitivityResult2("INVALID_INPUT", result.status, "unresolved",
                                  reason="seed_shape_mismatch", parameter=parameter, tied_labels=tuple(tied_labels), validity_conditions=conditions)
    if not (positive_direction_valid or negative_direction_valid):
        return SensitivityResult2("OK", result.status, "unresolved", reason="no_valid_direction",
                                  parameter=parameter, tied_labels=tuple(tied_labels), validity_conditions=conditions)
    if _stable(result) is True:
        rhs_seed = tuple(Q(seed.db[i]) - sum((Q(a) * Q(x) for a, x in zip(seed.dA[i], result.exact_x)), Q(0))
                         for i in range(m))
        derivative = (sum((Q(x) * Q(d) for x, d in zip(result.exact_x, seed.dc)), Q(0))
                      + sum((Q(y) * Q(r) for y, r in zip(result.exact_y, rhs_seed)), Q(0)))
        kind = "smooth" if positive_direction_valid and negative_direction_valid else "one_sided"
        return SensitivityResult2("OK", result.status, kind, selected_piece=result.basis,
                                  display_status="EXACT",
                                  directional_derivative=derivative if positive_direction_valid else None,
                                  right_derivative=derivative if positive_direction_valid else None,
                                  left_derivative=derivative if negative_direction_valid else None,
                                  piece_jacobians=((result.basis, derivative),), method="stable_basis", parameter=parameter, tied_labels=tuple(tied_labels), validity_conditions=conditions)
    primal, dual = optimal_face_recession2(result.problem)
    if primal is not None or dual is not None:
        return SensitivityResult2("OK", result.status, "singular", reason="possibly_discontinuous",
                                  primal_recession_ray=primal, dual_recession_ray=dual,
                                  method="optimal_face_recession", parameter=parameter, tied_labels=tuple(tied_labels), validity_conditions=conditions)
    forward, fcert = _mills(result, seed, 1) if positive_direction_valid else (None, None)
    reverse, rcert = _mills(result, seed, -1) if negative_direction_valid else (None, None)
    if ((positive_direction_valid and forward is None) or (negative_direction_valid and reverse is None)
            or not (positive_direction_valid or negative_direction_valid)):
        return SensitivityResult2("OK", result.status, "unresolved", reason="directional_problem_not_finite",
                                  method="mills_freund", parameter=parameter, tied_labels=tuple(tied_labels), validity_conditions=conditions)
    left = -reverse if reverse is not None else None
    kind = "smooth" if forward is not None and left is not None and forward == left else "one_sided"
    return SensitivityResult2("OK", result.status, kind, directional_derivative=forward,
                              display_status="EXACT",
                              right_derivative=forward, left_derivative=left,
                              forward_certificate=fcert, reverse_certificate=rcert,
                              method="mills_freund", parameter=parameter, tied_labels=tuple(tied_labels), validity_conditions=conditions)


def _local_polynomial_sign(poly, point, side):
    """Sign on a sufficiently small side, from the first nonzero Taylor term."""
    order = 0
    current = poly
    while any(current):
        value = p_eval(current, point)
        if value:
            return ((value > 0) - (value < 0)) * (side ** order)
        current = p_derivative(current)
        order += 1
    return 0


def _basis_variation(A, basis, inverse, state, seed, entering, dual):
    """Derivative of a certified ray basis or a certified mechanism basis."""
    m = len(A)
    if dual:
        rhs = tuple(Q(seed.dc[basis[k]]) - sum(Q(seed.dA[i][basis[k]]) * state[i] for i in range(m))
                    for k in range(m))
        return tuple(sum(inverse[k][i] * rhs[k] for k in range(m)) for i in range(m))
    rhs = tuple(-Q(seed.dA[i][entering]) - sum(Q(seed.dA[i][basis[k]]) * state[k] for k in range(m))
                for i in range(m))
    return tuple(sum(inverse[k][i] * rhs[i] for i in range(m)) for k in range(m))


def _threshold_sensitivity2(critical, seed, mu_seed, parameter, tied_labels, conditions,
                            positive_direction_valid, negative_direction_valid):
    """Differentiate the still-valid endpoint certificate, not diverging forces."""
    if critical.exact_threshold == 0 and critical.attained and critical.threshold_proof is None:
        return SensitivityResult2("OK", critical.status, "unresolved", parameter=parameter,
                                  reason="threshold_on_domain_boundary_without_proof", validity_conditions=conditions)
    if (critical.exact_threshold is None or critical.threshold_certificate is None
            or critical.threshold_proof is None or seed is None):
        return SensitivityResult2("OK", critical.status, "unresolved", parameter=parameter,
                                  reason="exact_threshold_basis_and_seed_required", validity_conditions=conditions)
    if not (positive_direction_valid or negative_direction_valid):
        return SensitivityResult2("OK", critical.status, "unresolved", parameter=parameter,
                                  reason="no_valid_direction", validity_conditions=conditions)
    proof, point = critical.threshold_proof, critical.exact_threshold
    branch = proof.upper_basis if critical.attained else proof.lower_basis
    if branch is None:
        return SensitivityResult2("OK", critical.status, "unresolved", parameter=parameter,
                                  reason="critical_basis_unavailable", validity_conditions=conditions)
    problem = critical.threshold_certificate.problem
    A, c, basis = problem.A, problem.c, branch.basis
    m, n = len(A), len(c)
    if mu_seed is None:
        mu_seed = build_limit_seed2(problem, mu_seed=1)
    try:
        directions = tuple(LimitSeed2(tuple(tuple(Q(v) for v in row) for row in direction.dA),
                                     tuple(Q(v) for v in direction.db), tuple(Q(v) for v in direction.dc),
                                     direction.parameter) for direction in (seed, mu_seed))
    except (ValueError, TypeError, OverflowError):
        return SensitivityResult2("INVALID_INPUT", critical.status, "unresolved", parameter=parameter,
                                  reason="invalid_exact_seed", validity_conditions=conditions)
    seed, mu_seed = directions
    for direction in directions:
        if (len(direction.dA) != m or any(len(row) != n for row in direction.dA)
                or len(direction.db) != m or len(direction.dc) != n):
            return SensitivityResult2("INVALID_INPUT", critical.status, "unresolved", parameter=parameter,
                                      reason="seed_shape_mismatch", validity_conditions=conditions)
    if len(basis) != m or any(j < 0 or j >= n for j in basis):
        return SensitivityResult2("OK", critical.status, "singular", parameter=parameter,
                                  reason="critical_basis_singular", validity_conditions=conditions)
    B = tuple(tuple(A[i][j] for j in basis) for i in range(m))
    inverse = _inverse(B)
    if inverse is None or p_eval(branch.determinant, point) == 0:
        return SensitivityResult2("OK", critical.status, "singular", parameter=parameter,
                                  reason="critical_basis_singular", validity_conditions=conditions)
    signs = proof.upper_signs if critical.attained else proof.lower_signs
    interval = proof.upper_interval if critical.attained else proof.lower_interval
    if signs is None or (interval[0] != interval[1] and not signs):
        return SensitivityResult2("OK", critical.status, "unresolved", parameter=parameter,
                                  reason="critical_basis_continuation_unproved", validity_conditions=conditions)
    denominator = p_eval(branch.determinant, point)
    if any(p_eval(poly, point) / denominator < 0 for poly in branch.numerators):
        return SensitivityResult2("OK", critical.status, "unresolved", parameter=parameter,
                                  reason="critical_basis_infeasible_at_threshold", validity_conditions=conditions)
    dual = not critical.attained
    if dual:
        state = tuple(sum(inverse[k][i] * c[basis[k]] for k in range(m)) for i in range(m))
    else:
        state = tuple(-sum(inverse[k][i] * A[i][branch.entering] for i in range(m)) for k in range(m))
    mu_state = _basis_variation(A, basis, inverse, state, mu_seed, branch.entering, dual)
    parameter_state = _basis_variation(A, basis, inverse, state, seed, branch.entering, dual)
    denominator = p_eval(branch.determinant, point)
    crossings = []
    for k, polynomial in enumerate(branch.numerators):
        if p_eval(polynomial, point) != 0:
            continue
        side = 1 if dual else -1
        sign = _local_polynomial_sign(polynomial, point, side) * ((denominator > 0) - (denominator < 0))
        if sign >= 0:
            continue
        if dual:
            partial_mu = (sum(Q(mu_seed.dA[i][k]) * state[i] + A[i][k] * mu_state[i] for i in range(m))
                          - Q(mu_seed.dc[k]))
            partial_parameter = (sum(Q(seed.dA[i][k]) * state[i] + A[i][k] * parameter_state[i] for i in range(m))
                                 - Q(seed.dc[k]))
        else:
            partial_mu, partial_parameter = mu_state[k], parameter_state[k]
        label = branch.labels[k]
        if partial_mu == 0:
            return SensitivityResult2("OK", critical.status, "singular", parameter=parameter,
                                      reason="zero_implicit_denominator", tied_labels=tied_labels + (label,),
                                      validity_conditions=conditions)
        slope = -Q(partial_parameter) / Q(partial_mu)
        crossings.append((label, slope, partial_mu, partial_parameter, k))
    if not crossings:
        return SensitivityResult2("OK", critical.status, "unresolved", parameter=parameter,
                                  reason="no_certified_crossing_component", validity_conditions=conditions)
    labels = tuple(dict.fromkeys(tied_labels + tuple(item[0] for item in crossings)))
    slopes = tuple(item[1] for item in crossings)
    pieces = tuple((item[0], item[1]) for item in crossings)
    selected = (branch.kind, basis, branch.entering)
    conditions = conditions + ("临界证书基非奇异", "所列越零分量及方向保持有效")
    if len(set(slopes)) != 1:
        return SensitivityResult2("OK", critical.status, "tie", parameter=parameter,
                                  reason="competing_threshold_slopes", selected_piece=selected,
                                  tied_labels=labels, piece_jacobians=pieces, implicit_components=tuple(crossings),
                                  method="implicit_certificate", validity_conditions=conditions)
    slope = slopes[0]
    kind = "smooth" if positive_direction_valid and negative_direction_valid else "one_sided"
    return SensitivityResult2("OK", critical.status, kind, parameter=parameter,
                              display_status="EXACT",
                              selected_piece=selected, tied_labels=labels, piece_jacobians=pieces,
                              directional_derivative=slope if positive_direction_valid else None,
                              right_derivative=slope if positive_direction_valid else None,
                              left_derivative=slope if negative_direction_valid else None,
                              implicit_components=tuple(crossings), method="implicit_certificate",
                              validity_conditions=conditions)
