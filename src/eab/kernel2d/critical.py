"""Exact polynomial continuation of planar load certificates.

Only rational threshold candidates with verified one-sided certificates are
accepted. Polynomial zero counts prove continuation; they do not approximate
an algebraic threshold or alter the binary64 query domain. Gates are in
test_tia2d_statics.py and test_tia2d_sensitivity.py.
"""
from dataclasses import dataclass
from fractions import Fraction as Q

from .algebraic import p_add, p_sub, p_mul, p_scale, p_divmod, p_eval, _root_count


@dataclass(frozen=True)
class CriticalBasis2:
    kind: str
    basis: tuple[int, ...]
    entering: int | None
    determinant: tuple[Q, ...]
    numerators: tuple[tuple[Q, ...], ...]
    labels: tuple
    sample_parameter: Q
    sample_values: tuple[Q, ...]


@dataclass(frozen=True)
class ThresholdProof2:
    exact_threshold: Q
    attained: bool
    lower_basis: CriticalBasis2 | None
    upper_basis: CriticalBasis2 | None
    lower_interval: tuple[Q, Q]
    upper_interval: tuple[Q, Q]
    lower_signs: tuple | None
    upper_signs: tuple | None
    reason: str = "exact_basis_continuation"


def _determinant(matrix):
    """Fraction-free Bareiss determinant over Q[mu], coefficients ascending."""
    n = len(matrix)
    if n == 0:
        return (Q(1),)
    work = [[tuple(Q(v) for v in item) for item in row] for row in matrix]
    previous, sign = (Q(1),), 1
    for k in range(n - 1):
        pivot = next((i for i in range(k, n) if any(work[i][k])), None)
        if pivot is None:
            return (Q(0),)
        if pivot != k:
            work[k], work[pivot] = work[pivot], work[k]
            sign = -sign
        value = work[k][k]
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                numerator = p_sub(p_mul(value, work[i][j]), p_mul(work[i][k], work[k][j]))
                quotient, remainder = p_divmod(numerator, previous)
                if any(remainder):
                    raise ArithmeticError("nonexact polynomial elimination")
                work[i][j] = quotient
            work[i][k] = (Q(0),)
        previous = value
    return p_scale(work[-1][-1], sign)


def _rank_columns(A, order):
    """Greedily retain independent columns using exact elimination."""
    vectors, pivots, basis = [], [], []
    for j in order:
        vector = [Q(row[j]) for row in A]
        for row, pivot in zip(vectors, pivots):
            factor = vector[pivot]
            vector = [a - factor * b for a, b in zip(vector, row)]
        pivot = next((i for i, v in enumerate(vector) if v), None)
        if pivot is None:
            continue
        factor = vector[pivot]
        vectors.append(tuple(v / factor for v in vector))
        pivots.append(pivot)
        basis.append(j)
        if len(basis) == len(A):
            break
    return tuple(basis)


def affine_matrix2(problem_zero, problem_one):
    if (len(problem_zero.A) != len(problem_one.A) or problem_zero.b != problem_one.b
            or problem_zero.c != problem_one.c):
        raise ValueError("fixed geometry and loads required")
    return tuple(tuple((Q(a), Q(b) - Q(a)) for a, b in zip(row, other))
                 for row, other in zip(problem_zero.A, problem_one.A))


def mechanism_basis2(result, matrix):
    """A complete exact dual branch y=B^-T c_B, with all column slacks."""
    if result.status != "OPTIMAL":
        return None
    A, c, y = result.problem.A, result.problem.c, result.exact_y
    m, n = len(A), len(c)
    active = [j for j in range(n) if sum(A[i][j] * y[i] for i in range(m)) == c[j]]
    basis = _rank_columns(A, active)
    if len(basis) != m:
        return None
    B = [[row[j] for j in basis] for row in matrix]
    determinant = _determinant(B)
    denominator = p_eval(determinant, result.problem.mu)
    if denominator == 0:
        return None
    numerators = []
    for j in range(n):
        if j in basis:
            numerators.append((Q(0),))
        else:
            bordered = [list(row) + [matrix[i][j]] for i, row in enumerate(B)]
            bordered.append([(Q(c[k]),) for k in basis] + [(Q(c[j]),)])
            numerators.append(p_scale(_determinant(bordered), -1))
    values = tuple(p_eval(poly, result.problem.mu) / denominator for poly in numerators)
    if any(value < 0 for value in values):
        return None
    return CriticalBasis2("mechanism", basis, None, determinant, tuple(numerators),
                          result.problem.column_labels, result.problem.mu, values)


def improving_basis2(result, matrix):
    """A contact basis with alpha entering and alpha normalized to exactly one."""
    if result.status != "UNBOUNDED":
        return None
    A, c, ray = result.problem.A, result.problem.c, result.improving_ray
    m, n = len(A), len(c)
    objective = [j for j, value in enumerate(c) if value]
    if len(objective) != 1 or c[objective[0]] != 1:
        return None
    entering = objective[0]
    order = [j for j in range(n) if j != entering and ray[j] > 0]
    order += [j for j in range(n) if j != entering and j not in order]
    basis = _rank_columns(A, order)
    if len(basis) != m:
        return None
    B = [[row[j] for j in basis] for row in matrix]
    determinant = _determinant(B)
    denominator = p_eval(determinant, result.problem.mu)
    if denominator == 0:
        return None
    numerators = []
    for k in range(m):
        replaced = [list(row) for row in B]
        for i in range(m):
            replaced[i][k] = p_scale(matrix[i][entering], -1)
        numerators.append(_determinant(replaced))
    values = tuple(p_eval(poly, result.problem.mu) / denominator for poly in numerators)
    if any(value < 0 for value in values):
        return None
    return CriticalBasis2("improving_ray", basis, entering, determinant, tuple(numerators),
                          tuple(result.problem.column_labels[j] for j in basis),
                          result.problem.mu, values)


def _remove_endpoint_roots(poly, lower, upper):
    reduced = poly
    orders = []
    for point in (lower, upper):
        order = 0
        while len(reduced) > 1 and p_eval(reduced, point) == 0:
            reduced, remainder = p_divmod(reduced, (-point, Q(1)))
            if any(remainder):
                raise ArithmeticError("endpoint factor verification failed")
            order += 1
        orders.append(order)
    return reduced, tuple(orders)


def branch_signs2(branch, lower, upper):
    """Prove all ratios nonnegative on an OPEN interval, retaining proof data.

Endpoint factors are removed before exact Sturm zero counting. Interior
zeros conservatively decline this branch, even if an even-order zero might
leave its sign unchanged. This is a certificate, not a full sign classifier.
"""
    if branch is None:
        return None
    lower, upper = Q(lower), Q(upper)
    if lower > upper:
        return None
    if lower == upper:
        return ()
    sample = (lower + upper) / 2
    reduced, endpoint_orders = _remove_endpoint_roots(branch.determinant, lower, upper)
    if not any(reduced) or _root_count(reduced, lower, upper):
        return None
    denominator = p_eval(branch.determinant, sample)
    proofs = [("denominator", endpoint_orders, denominator)]
    for k, poly in enumerate(branch.numerators):
        if not any(poly):
            proofs.append((k, (0, 0), Q(0)))
            continue
        reduced, endpoint_orders = _remove_endpoint_roots(poly, lower, upper)
        if _root_count(reduced, lower, upper):
            return None
        value = p_eval(poly, sample) / denominator
        if value < 0:
            return None
        proofs.append((k, endpoint_orders, value))
    return tuple(proofs)


def rational_candidate2(lower, upper):
    """A simple rational in the bracket; acceptance needs polynomial proofs."""
    lower, upper = Q(lower), Q(upper)
    if lower == upper:
        return lower
    shifts = []
    lo, hi = lower, upper
    while True:
        a, b = lo.numerator // lo.denominator, hi.numerator // hi.denominator
        if lo == a:
            value = Q(a)
            break
        if a < b:
            value = Q(a + 1)
            break
        shifts.append(a)
        lo, hi = 1 / (hi - a), 1 / (lo - a)
    for shift in reversed(shifts):
        value = Q(shift) + 1 / value
    return value


def candidate_is_boundary2(candidate, lower_branch, upper_branch):
    if candidate == 0:
        return True
    for branch in (lower_branch, upper_branch):
        if branch is not None:
            for polynomial in (branch.determinant,) + branch.numerators:
                if any(polynomial) and p_eval(polynomial, candidate) == 0:
                    return True
    return False
