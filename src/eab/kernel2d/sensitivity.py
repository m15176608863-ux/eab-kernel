"""Exact fixed-basis and bounded-optimal-face directional derivatives.

The associated profile1 model uses the original unnormalized matrices. A
nonzero optimal-face recession direction is reported conservatively as
singular, not as proof of a discontinuity. Tests: test_tia2d_sensitivity.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as Q
import struct

from eab import lp
from .statics import CriticalParameter2, LimitResult2, _cross, _dot, _project, _run
from .algebraic import p_derivative, p_eval


@dataclass(frozen=True)
class LimitSeed2:
    dA: tuple[tuple[Q, ...], ...]
    db: tuple[Q, ...]
    dc: tuple[Q, ...]
    parameter: str = "mu"
    _affine_path: object = None
    _mu_seed: Q = Q(0)

    @property
    def affine_path(self):
        return self._affine_path

    @property
    def mu_seed(self):
        return self._mu_seed


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
    branch_certificate: object = None

def build_limit_seed2(problem, *, mu_seed=0, contact_seeds=None, dead_seeds=None,
                      live_seeds=None, anchor_seeds=None, reference_seeds=None, parameter="mu"):
    """Propagate exact affine primitives and retain their full polynomial path.

contact_seeds maps labels to (dp,dT). Loads are exact wrench derivatives
about the supplied references. Anchors/references stay constant unless their
own seeds are provided. Shared parameters must be seeded consistently by the
caller. Threshold certificates rebuild products of these affine primitives,
not just their first derivatives. Gates: test_threshold_branch.py.
"""
    dmu = Q(mu_seed)
    contact_seeds = {} if contact_seeds is None else contact_seeds
    dead_seeds = {} if dead_seeds is None else dead_seeds
    live_seeds = {} if live_seeds is None else live_seeds
    anchor_seeds = {} if anchor_seeds is None else anchor_seeds
    reference_seeds = {} if reference_seeds is None else reference_seeds
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
                do = tuple(Q(v) for v in reference_seeds.get(body.body_id, (0, 0)))
                da = tuple(Q(v) for v in anchor_seeds.get(body.body_id, (0, 0)))
                dm = _cross(tuple(dp[k] - do[k] for k in range(2)), force) + _cross(arm, df)
                dm -= _cross(tuple(da[k] - do[k] for k in range(2)), force)
                column.extend(_project(body, (sense * df[0], sense * df[1], sense * dm)))
            columns.append(tuple(column))
    def load_jet(body, values, original):
        jet = tuple(Q(x) for x in values.get(body.body_id, (0, 0, 0)))
        da = anchor_seeds.get(body.body_id, (0, 0))
        do = reference_seeds.get(body.body_id, (0, 0))
        correction = _cross(tuple(Q(da[k]) - Q(do[k]) for k in range(2)), original[:2])
        return _project(body, (jet[0], jet[1], jet[2] - correction))
    live = tuple(v for body in assembly.bodies for v in load_jet(body, live_seeds, body.live))
    dead = tuple(-v for body in assembly.bodies for v in load_jet(body, dead_seeds, body.dead))
    columns.append(live)
    dA = tuple(tuple(col[i] for col in columns) for i in range(len(problem.b)))
    path = {"problem": problem,
            "contact_seeds": {key: tuple(tuple(Q(v) for v in vector) for vector in value)
                              for key, value in contact_seeds.items()},
            "dead_seeds": {key: tuple(Q(v) for v in value) for key, value in dead_seeds.items()},
            "live_seeds": {key: tuple(Q(v) for v in value) for key, value in live_seeds.items()},
            "anchor_seeds": {key: tuple(Q(v) for v in value) for key, value in anchor_seeds.items()},
            "reference_seeds": {key: tuple(Q(v) for v in value) for key, value in reference_seeds.items()}}
    return LimitSeed2(dA, dead, (Q(0),) * len(problem.c), parameter, path, dmu)


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


def _threshold_singular_diagnostic(critical):
    """Diagnose a singular certificate only after all ordered-field proofs fail."""
    proof = critical.threshold_proof
    if proof is None:
        return None
    branch = proof.upper_basis if critical.attained else proof.lower_basis
    if branch is None:
        return None
    problem, point = critical.threshold_certificate.problem, critical.exact_threshold
    basis, m, n = branch.basis, len(critical.threshold_certificate.problem.A), len(problem.c)
    if len(basis) != m or len(set(basis)) != m or any(j < 0 or j >= n for j in basis):
        return "critical_basis_singular"
    denominator = p_eval(branch.determinant, point)
    if denominator == 0 or _inverse(tuple(tuple(problem.A[i][j] for j in basis) for i in range(m))) is None:
        return "critical_basis_singular"
    side = -1 if critical.attained else 1
    for numerator in branch.numerators:
        if p_eval(numerator, point) != 0:
            continue
        order, current = 0, numerator
        while any(current) and p_eval(current, point) == 0:
            order, current = order + 1, p_derivative(current)
        if not any(current):
            continue
        leading = p_eval(current, point) / denominator
        outside_sign = ((leading > 0) - (leading < 0)) * side ** order
        if outside_sign < 0 and p_eval(p_derivative(numerator), point) == 0:
            return "zero_implicit_denominator"
    return None


def _valid_original_domain(critical):
    """Keep public domain data bound to the immutable original input copy."""
    domain, binding = critical.search_domain, critical._search_domain_binding
    if not isinstance(domain, dict) or not isinstance(binding, tuple) or len(binding) != 4:
        return False
    try:
        lower, upper = Q(domain["exact_mu_min"]), Q(domain["exact_mu_max"])
        if lower != 0 or upper < 0 or not lower <= critical.exact_threshold <= upper:
            return False
        if (lower, upper, domain["mu_min_binary64"], domain["mu_max_binary64"]) != binding:
            return False
        digits = "0123456789abcdef"
        for name, exact in (("mu_min", lower), ("mu_max", upper)):
            displayed = domain[name]
            if not isinstance(displayed, float) or Q(displayed) != exact:
                return False
            bits = "".join(digits[byte >> 4] + digits[byte & 15]
                           for byte in struct.pack(">d", displayed))
            if bits != domain[name + "_binary64"]:
                return False
        return True
    except (KeyError, ValueError, TypeError, OverflowError, struct.error):
        return False


def _threshold_sensitivity2(critical, seed, mu_seed, parameter, tied_labels, conditions,
                            positive_direction_valid, negative_direction_valid):
    """Certify both directions by a domain-bound ordered-field sandwich."""
    from .branch_certificate import certify_direction
    def unavailable(reason, status="OK"):
        return SensitivityResult2(status, critical.status, "unresolved", quality="approximate",
                                  reason=reason, parameter=parameter, validity_conditions=conditions,
                                  method="branch_certificate")

    if seed is not None:
        try:
            if Q(seed.mu_seed) != 0:
                return unavailable("threshold_mu_seed_not_allowed", "INVALID_INPUT")
            for row in seed.dA:
                tuple(Q(v) for v in row)
            tuple(Q(v) for v in seed.db)
            tuple(Q(v) for v in seed.dc)
        except (ValueError, TypeError, OverflowError):
            return unavailable("invalid_exact_seed", "INVALID_INPUT")
    if not (positive_direction_valid or negative_direction_valid):
        return unavailable("no_valid_direction")
    if critical.exact_threshold is None or critical.threshold_certificate is None or seed is None:
        return unavailable("exact_threshold_basis_and_seed_required")
    problem = critical.threshold_certificate.problem
    if (len(seed.dA) != len(problem.b) or any(len(row) != len(problem.c) for row in seed.dA)
            or len(seed.db) != len(problem.b) or len(seed.dc) != len(problem.c)):
        return unavailable("seed_shape_mismatch", "INVALID_INPUT")
    if seed.affine_path is None:
        return unavailable("threshold_affine_primitives_required")
    if not _valid_original_domain(critical):
        return unavailable("threshold_branch_certificate_unavailable")
    from .branch_field import polynomial_family
    family = polynomial_family(seed.affine_path, critical.exact_threshold, Q(0), 0, 1)
    if (any(dict(poly).get((0, 0), Q(0)) != problem.A[i][j]
            or dict(poly).get((1, 0), Q(0)) != seed.dA[i][j]
            for i, row in enumerate(family[0]) for j, poly in enumerate(row))
            or any(dict(poly).get((0, 0), Q(0)) != original
                   or dict(poly).get((1, 0), Q(0)) != jet
                   for values, originals, jets in ((family[1], problem.b, seed.db),
                                                   (family[2], problem.c, seed.dc))
                   for poly, original, jet in zip(values, originals, jets))):
        return unavailable("affine_seed_mismatch", "INVALID_INPUT")
    mu_seed = build_limit_seed2(problem, mu_seed=1)
    certificate = {"version": 1, "order": "epsilon_then_eta", "search_domain": critical.search_domain}
    for name, direction, valid in (("forward", 1, positive_direction_valid),
                                    ("reverse", -1, negative_direction_valid)):
        certificate[name] = (certify_direction(critical, seed, mu_seed, direction) if valid else
            {"status": "unresolved", "reason": "direction_outside_validity_conditions", "s": None,
             "lower": None, "upper": None, "candidate_count": 0, "attempts": 0, "candidate_branches": []})
    forward, reverse = certificate["forward"], certificate["reverse"]
    for value in (forward, reverse):
        # Invariant: a certified direction carries all three ordered-field
        # witnesses. A value without them is never emitted (acceptance gate).
        upper = value.get("upper") or {}
        if value["status"] == "certified" and not (value.get("lower") and upper.get("point") and upper.get("ray")):
            value.update(status="unresolved", reason="internal_certificate_shape", s=None, lower=None, upper=None,
                         candidate_branches=[])
    right = Q(forward["s"]) if forward["status"] == "certified" else None
    left = -Q(reverse["s"]) if reverse["status"] == "certified" else None
    reasons = [value["reason"] for value in (forward, reverse) if value["reason"] is not None]
    reason = ("threshold_search_domain_boundary" if "threshold_search_domain_boundary" in reasons
              else reasons[0] if reasons else None)
    kind = ("smooth" if right is not None and left is not None and right == left else
            "one_sided" if right is not None or left is not None else "unresolved")
    if kind == "unresolved" and reason == "threshold_branch_certificate_unavailable":
        diagnostic = _threshold_singular_diagnostic(critical)
        if diagnostic is not None:
            kind, reason = "singular", diagnostic
    labels, components = [], []
    for value in (forward, reverse):
        for branch in value["candidate_branches"]:
            for component in branch["components"]:
                label = component["label"]
                if label not in labels:
                    labels.append(label)
                if not branch.get("singular", False):
                    item = (label, Q(component["s"]), Q(component["partial_mu"]),
                            Q(component["partial_parameter"]), component["index"])
                    if item not in components:
                        components.append(item)
    return SensitivityResult2("OK", critical.status, kind,
        quality="exact_jet" if right is not None or left is not None else "approximate",
        right_derivative=right, left_derivative=left, directional_derivative=right,
        display_status="EXACT" if right is not None or left is not None else "NOT_APPLICABLE",
        reason=reason, tied_labels=tuple(labels), implicit_components=tuple(components),
        branch_certificate=certificate, parameter=parameter, validity_conditions=conditions,
        method="branch_certificate")
