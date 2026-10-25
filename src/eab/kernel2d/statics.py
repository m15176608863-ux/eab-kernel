"""Exact, unnormalized planar associated limit analysis.

Profile 1 assumes rigid bodies, infinitesimal motion, unlimited compression,
no cohesion and constant friction. Associated flow is an unsafe-side upper
bound relative to non-associated Coulomb friction. UNBOUNDED is neither a
finite capacity nor a geometric lock. Gates: test_tia2d_statics.py.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
import struct

from eab import lp
from eab.construction import scalar_rational
from .assembly import Assembly2
from .contacts import ContactSet2, assemble_contact_set2
from .critical import (ThresholdProof2, affine_matrix2, branch_signs2, candidate_is_boundary2,
                       improving_basis2, mechanism_basis2, rational_candidate2)


@dataclass(frozen=True)
class LimitProblem2:
    A: tuple[tuple[Fraction, ...], ...]
    b: tuple[Fraction, ...]
    c: tuple[Fraction, ...]
    row_labels: tuple
    column_labels: tuple
    reference_points: tuple
    dof_anchors: tuple
    mu: Fraction
    assembly: object
    contact_set: object
    profile: str = "profile1"
    sensitivity_model: str = "ideal_exact_2d"


@dataclass(frozen=True)
class LimitResult2:
    call_status: str
    mathematical_status: str | None
    display_status: str = "NOT_APPLICABLE"
    exact_value: Fraction | None = None
    exact_x: tuple[Fraction, ...] | None = None
    exact_y: tuple[Fraction, ...] | None = None
    feasible_point: tuple[Fraction, ...] | None = None
    improving_ray: tuple[Fraction, ...] | None = None
    farkas: tuple[Fraction, ...] | None = None
    problem: LimitProblem2 | None = None
    reason: str | None = None
    basis: tuple[int, ...] = ()
    sensitivity_model: str = "ideal_exact_2d"
    validity_conditions: tuple = ()

    @property
    def status(self):
        return self.mathematical_status


@dataclass(frozen=True)
class CriticalParameter2:
    call_status: str
    mathematical_status: str
    mu_lo: float | None = None
    mu_hi: float | None = None
    attained: bool | None = None
    lower_certificate: LimitResult2 | None = None
    upper_certificate: LimitResult2 | None = None
    reason: str | None = None
    exact_threshold: Fraction | None = None
    critical_polynomials: tuple = ()
    queries: int = 0
    threshold_certificate: LimitResult2 | None = None
    threshold_proof: ThresholdProof2 | None = None
    bisection_termination: str | None = None
    threshold_proof_reason: str | None = None
    validity_conditions: tuple = ()
    search_domain: object = None
    _search_domain_binding: tuple = ()

    @property
    def status(self):
        return self.mathematical_status


def _dot(a, b):
    return sum((x * y for x, y in zip(a, b)), Fraction(0))


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _run(A, b, c):
    """The existing exact LP accepts rationals; no rounded matrix is needed."""
    return lp.maximize([list(row) for row in A], list(b), list(c), exact=(A, b, c))


def _point(A, b, n):
    result = _run(A, b, [Fraction(0)] * n)
    if result.status != lp.OPTIMAL or result.exact_x is None:
        raise ArithmeticError("exact feasible point unavailable")
    x = tuple(result.exact_x)
    if any(v < 0 for v in x) or any(_dot(row, x) != v for row, v in zip(A, b)):
        raise ArithmeticError("exact feasible point verification failed")
    return x


def _farkas(A, b, n):
    """Find y with A^T y <= 0 and b^T y = 1, without decoding float y."""
    m = len(b)
    rows = []
    for j in range(n):
        column = [A[i][j] for i in range(m)]
        rows.append(column + [-v for v in column]
                    + [Fraction(int(j == k)) for k in range(n)])
    rows.append(list(b) + [-v for v in b] + [Fraction(0)] * n)
    x = _point(rows, [Fraction(0)] * n + [Fraction(1)], 2 * m + n)
    y = tuple(x[i] - x[m + i] for i in range(m))
    if _dot(b, y) != 1 or any(sum(A[i][j] * y[i] for i in range(m)) > 0 for j in range(n)):
        raise ArithmeticError("exact infeasibility verification failed")
    return y


def _project(body, wrench):
    """Project about the physical DOF anchor, not the algebraic origin."""
    if body.boundary_type == "FIXED_BODY":
        return ()
    offset = tuple(a - o for a, o in zip(body.dof_anchor, body.reference_point))
    moved = (wrench[0], wrench[1], wrench[2] - _cross(offset, wrench[:2]))
    return tuple(v for v, free in zip(moved, body.dof_mask) if free)


def build_limit_problem2(assembly, contact_set, mu):
    """Build exact action/reaction columns; the live load is a matrix column."""
    q = Fraction(mu)
    if q < 0:
        raise ValueError("mu must be nonnegative")
    if assembly.profile != "profile1":
        raise ValueError("unsupported profile")
    rows = tuple((body.body_id, k) for body in assembly.bodies
                 if body.boundary_type != "FIXED_BODY"
                 for k, free in enumerate(body.dof_mask) if free)
    columns, labels = [], []
    for contact in contact_set.constraints:
        tangent = contact.tangent
        normal = (-tangent[1], tangent[0])
        if normal == (0, 0):
            raise ValueError("zero contact direction")
        for sign in (-1, 1):
            force = tuple(normal[k] + sign * q * tangent[k] for k in range(2))
            column = []
            for i, body in enumerate(assembly.bodies):
                sense = int(i == contact.a) - int(i == contact.b)
                arm = tuple(p - o for p, o in zip(contact.point, body.reference_point))
                wrench = (sense * force[0], sense * force[1], sense * _cross(arm, force))
                column.extend(_project(body, wrench))
            columns.append(tuple(column))
            labels.append((contact.label, sign))
    live = tuple(v for body in assembly.bodies for v in _project(body, body.live))
    dead = tuple(-v for body in assembly.bodies for v in _project(body, body.dead))
    columns.append(live)
    labels.append(("alpha", 1))
    A = tuple(tuple(column[i] for column in columns) for i in range(len(rows)))
    c = (Fraction(0),) * (len(columns) - 1) + (Fraction(1),)
    return LimitProblem2(A, dead, c, rows, tuple(labels),
                         tuple(body.reference_point for body in assembly.bodies),
                         tuple(body.dof_anchor for body in assembly.bodies),
                         q, assembly, contact_set)


def solve_limit_problem2(problem):
    """Solve and independently recheck exact point/ray/Farkas certificates."""
    A, b, c = problem.A, problem.b, problem.c
    conditions = (("true_vv_excluded_from_statics",)
                  if problem.contact_set is not None and any(point.fp_type == "REDUNDANT_PROVED"
                         for point in problem.contact_set.points) else ())
    result = _run(A, b, c)
    if result.status == lp.OPTIMAL:
        x, y = tuple(result.exact_x), tuple(result.exact_y)
        value = _dot(c, x)
        if (any(v < 0 for v in x) or any(_dot(row, x) != rhs for row, rhs in zip(A, b))
                or any(sum(A[i][j] * y[i] for i in range(len(b))) < c[j] for j in range(len(c)))
                or _dot(b, y) != value):
            raise ArithmeticError("exact optimum verification failed")
        return LimitResult2("OK", "OPTIMAL", "EXACT", value, x, y,
                            problem=problem, basis=tuple(result.basis), validity_conditions=conditions)
    if result.status == lp.UNBOUNDED:
        x0 = _point(A, b, len(c))
        ray = _point(list(A) + [c], [Fraction(0)] * len(b) + [Fraction(1)], len(c))
        return LimitResult2("OK", "UNBOUNDED", feasible_point=x0, improving_ray=ray,
                            problem=problem, basis=tuple(result.basis), validity_conditions=conditions)
    if result.status == lp.INFEASIBLE:
        return LimitResult2("OK", "INFEASIBLE", farkas=_farkas(A, b, len(c)),
                            problem=problem, basis=tuple(result.basis), validity_conditions=conditions)
    raise ArithmeticError("unknown exact solver state")


def limit_load_ideal_exact_2d(assembly, contact_set=None, *, mu=None):
    """Associated profile1 limit; unresolved geometry is not a zero capacity.

References and physical DOF anchors remain frozen. The no-cohesion contact
generators are N +/- mu T without normalization. Tests cover exact matrices,
free-plate masks, load transformations and all three LP certificates.
"""
    if not isinstance(assembly, Assembly2):
        return LimitResult2("INVALID_INPUT", None, reason="expected_assembly")
    if contact_set is None:
        contact_set = assemble_contact_set2(assembly)
    if not isinstance(contact_set, ContactSet2):
        return LimitResult2("INVALID_INPUT", None, reason="expected_contact_set")
    if contact_set.call_status != "OK":
        return LimitResult2(contact_set.call_status, None, reason=contact_set.reason)
    if contact_set.assembly != assembly:
        return LimitResult2("INVALID_INPUT", None, reason="assembly_mismatch")
    if contact_set.status != "RESOLVED":
        return LimitResult2("OK", contact_set.mathematical_status, reason="contact_set_unresolved")
    if contact_set.completeness != "complete":
        return LimitResult2("OK", "UNPROVED", reason="completeness_unknown")
    try:
        problem = build_limit_problem2(assembly, contact_set, assembly.mu if mu is None else mu)
    except (ValueError, OverflowError, TypeError) as exc:
        return LimitResult2("INVALID_INPUT", None, reason=str(exc))
    return solve_limit_problem2(problem)


def critical_parameter(assembly, param="mu", *, mu_max=1.0, max_steps=64, contact_set=None):
    """Bind the original closed binary64 search domain, not a narrowed bracket."""
    result = _critical_parameter(assembly, param, mu_max=mu_max,
                                 max_steps=max_steps, contact_set=contact_set)
    try:
        upper = Fraction(mu_max)
        if upper < 0 or not _is_binary64(upper):
            return result
        displayed = mu_max if isinstance(mu_max, float) else scalar_rational(upper, allow_underflow=True)
        digits = "0123456789abcdef"
        domain = {"mu_min": 0.0, "mu_max": displayed,
                  "exact_mu_min": "0/1", "exact_mu_max": str(upper.numerator) + "/" + str(upper.denominator),
                  "mu_min_binary64": "0000000000000000",
                  "mu_max_binary64": "".join(digits[byte >> 4] + digits[byte & 15]
                                             for byte in struct.pack(">d", displayed))}
        binding = (Fraction(0), upper, domain["mu_min_binary64"], domain["mu_max_binary64"])
        return replace(result, search_domain=domain, _search_domain_binding=binding)
    except (ValueError, OverflowError, TypeError):
        return result


def _critical_parameter(assembly, param="mu", *, mu_max=1.0, max_steps=64, contact_set=None):
    """Certified binary64 bracket; no exact threshold is inferred from width.

Only nested exact friction cones justify monotonicity. Both endpoints retain
full certificates. A binary64 resolution limit preserves, rather than
invalidates, the bracket. The endpoint domain is closed and finite.
"""
    if param != "mu":
        return CriticalParameter2("UNSUPPORTED", "UNPROVED", reason="only_mu_is_monotone")
    if not isinstance(assembly, Assembly2):
        return CriticalParameter2("INVALID_INPUT", "UNPROVED", reason="expected_assembly")
    try:
        hi = Fraction(mu_max)
        if hi < 0 or not _is_binary64(hi) or not isinstance(max_steps, int) or max_steps < 0:
            raise ValueError("invalid search domain")
    except (ValueError, OverflowError, TypeError) as exc:
        return CriticalParameter2("INVALID_INPUT", "UNPROVED", reason=str(exc))
    if contact_set is None:
        contact_set = assemble_contact_set2(assembly)
    low = limit_load_ideal_exact_2d(assembly, contact_set, mu=Fraction(0))
    if low.status == "UNBOUNDED":
        return CriticalParameter2("OK", "CERTIFIED", 0.0, 0.0, True,
                                  upper_certificate=low, exact_threshold=Fraction(0), queries=1,
                                  threshold_certificate=low, validity_conditions=low.validity_conditions)
    if low.status not in ("OPTIMAL", "INFEASIBLE"):
        return CriticalParameter2(low.call_status, "UNPROVED", reason=low.reason or "lower_certificate_unavailable", queries=1,
                                  validity_conditions=low.validity_conditions)
    high = low if hi == 0 else limit_load_ideal_exact_2d(assembly, contact_set, mu=Fraction(hi))
    count = 1 + int(hi != 0)
    if high.status == "INFEASIBLE":
        return CriticalParameter2("OK", "INFEASIBLE", scalar_rational(hi, allow_underflow=True), None, None,
                                  lower_certificate=high, reason="infeasible_on_domain", queries=count,
                                  validity_conditions=high.validity_conditions)
    if high.status == "OPTIMAL":
        return CriticalParameter2("OK", "CERTIFIED", scalar_rational(hi, allow_underflow=True), None, None,
                                  lower_certificate=high, reason="bounded_on_domain", queries=count,
                                  validity_conditions=high.validity_conditions)
    if high.status != "UNBOUNDED":
        return CriticalParameter2(high.call_status, "UNPROVED", reason=high.reason or "upper_certificate_unavailable", queries=count,
                                  validity_conditions=high.validity_conditions)
    lo = Fraction(0)
    for _ in range(max_steps):
        mid = _binary_midpoint(lo, hi)
        if mid is None:
            return _finish_critical(assembly, contact_set, lo, hi, low, high,
                                    "input_resolution_limit", count)
        probe = limit_load_ideal_exact_2d(assembly, contact_set, mu=mid)
        count += 1
        if probe.status == "UNBOUNDED":
            hi, high = mid, probe
        elif probe.status in ("OPTIMAL", "INFEASIBLE"):
            lo, low = mid, probe
        else:
            return CriticalParameter2(probe.call_status, "UNPROVED", scalar_rational(lo, allow_underflow=True),
                                      scalar_rational(hi, allow_underflow=True), None, low, high,
                                      "query_certificate_unavailable", queries=count,
                                      validity_conditions=low.validity_conditions)
    reason = "input_resolution_limit" if _binary_midpoint(lo, hi) is None else "iteration_limit"
    return _finish_critical(assembly, contact_set, lo, hi, low, high, reason, count)


def _finish_critical(assembly, contact_set, lo, hi, low, high, reason, count):
    """Preserve the bracket while attempting an exact rational threshold proof."""
    answer = CriticalParameter2("OK", "CERTIFIED", scalar_rational(lo, allow_underflow=True),
                                scalar_rational(hi, allow_underflow=True), None, low, high,
                                reason, queries=count, bisection_termination=reason,
                                validity_conditions=low.validity_conditions)
    if low.problem.assembly != assembly or high.problem.assembly != assembly:
        return answer
    zero = build_limit_problem2(assembly, contact_set, Fraction(0))
    one = build_limit_problem2(assembly, contact_set, Fraction(1))
    matrix = affine_matrix2(zero, one)
    lower_basis = mechanism_basis2(low, matrix)
    upper_basis = improving_basis2(high, matrix)
    polynomials = tuple(branch for branch in (lower_basis, upper_basis) if branch is not None)
    answer = replace(answer, critical_polynomials=polynomials)
    candidates = tuple(dict.fromkeys((lo, hi, rational_candidate2(lo, hi))))
    for candidate in candidates:
        if not candidate_is_boundary2(candidate, lower_basis, upper_basis):
            continue
        at = limit_load_ideal_exact_2d(assembly, contact_set, mu=candidate)
        count += 1
        below = branch_signs2(lower_basis, lo, candidate)
        above = branch_signs2(upper_basis, candidate, hi)
        # A dual branch approaching the candidate from below excludes earlier
        # unboundedness. At the candidate itself the full exact query decides.
        closed = at.status == "UNBOUNDED" and (candidate == 0 or below is not None)
        # For zero dead load x0=0 is feasible throughout the upper interval;
        # its normalized ray branch proves unbounded points arbitrarily close.
        opened = (at.status == "OPTIMAL" and not any(zero.b) and above is not None
                  and candidate < hi)
        if not (closed or opened):
            continue
        proof = ThresholdProof2(candidate, closed, lower_basis, upper_basis,
                                (lo, candidate), (candidate, hi),
                                below, above)
        return replace(answer, attained=closed, exact_threshold=candidate,
                       threshold_certificate=at, threshold_proof=proof,
                       threshold_proof_reason="exact_basis_continuation", queries=count)
    return replace(answer, queries=count)


def _is_binary64(q):
    q = Fraction(q)
    if q == 0:
        return True
    n, d = abs(q.numerator), q.denominator
    trailing = _bits(n & -n) - 1
    width = _bits(n) - trailing
    exponent = trailing - (_bits(d) - 1)
    return not (d & (d - 1)) and width <= 53 and exponent >= -1074 and exponent + width - 1 <= 1023


def _binary_midpoint(lo, hi):
    """Select an interior binary64 grid point entirely in rational arithmetic.

An exact midpoint can require 54 bits. Round downward to its local grid, then
move one grid unit if necessary. Returning None certifies adjacent endpoints;
no rounded display number is ever fed back into the exact LP.
"""
    mid = (Fraction(lo) + Fraction(hi)) / 2
    if _is_binary64(mid):
        return mid
    exponent = _bits(mid.numerator) - _bits(mid.denominator)
    power = Fraction(2 ** exponent) if exponent >= 0 else Fraction(1, 2 ** -exponent)
    if mid < power:
        exponent -= 1
    exponent = max(exponent - 52, -1074)
    unit = Fraction(2 ** exponent) if exponent >= 0 else Fraction(1, 2 ** -exponent)
    candidate = (mid // unit) * unit
    if candidate <= lo:
        candidate += unit
    return candidate if lo < candidate < hi else None


def _bits(n):
    count = 0
    while n:
        n //= 2
        count += 1
    return count
