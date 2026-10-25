"""Candidate acquisition and exact two-infinitesimal threshold sandwiches.

Nearby rational solves select bases only. The returned proof verifies every
original equation and ordered-field inequality, including the original
search domain. Finite resource bounds result in unresolved, never a slope.
"""
from fractions import Fraction as Q

from eab import lp
from .branch_field import (constant, add, sub, neg, mul, sign, evaluate, wire,
                           polynomial_family, solve_polynomial)
from .critical import _rank_columns
from .statics import _run
from .algebraic import p_derivative, p_divmod, p_gcd, p_eval, _root_count
from .critical import rational_candidate2

CANDIDATE_LIMIT = 64
RETRY_LIMIT = 6  # most recent witness bases retried per side; same in C++
TARGETED_LIMIT = 8  # extra probe vertices per failing component; same in C++
SCREEN_EPSILON, SCREEN_ETA = Q(1, 1 << 24), Q(1, 256)  # screening probe; same in C++
BISECTION_EXPONENT, BISECTION_STEPS = 24, 56  # probe-threshold candidates; same in C++
PROBE_EXPONENTS = (8, 16, 24, 32)
PROBE_ETA = (Q(1, 16), Q(1, 256), Q(1, 4096), Q(1, 65536))


def _rows(matrix):
    if not matrix:
        return ()
    return _rank_columns(tuple(zip(*matrix)), range(len(matrix)))


def _support_basis(matrix, values, excluded=()):
    rows = _rows(matrix)
    reduced = [matrix[i] for i in rows]
    order = [j for j in range(len(values)) if values[j] and j not in excluded]
    order += [j for j in range(len(values)) if j not in order and j not in excluded]
    return rows, _rank_columns(reduced, order)


def _dual_basis(matrix, objective, values):
    rows = _rows(matrix)
    active = [j for j in range(len(objective))
              if sum(matrix[i][j] * values[i] for i in range(len(matrix))) == objective[j]]
    return rows, _rank_columns([matrix[i] for i in rows], active)


def _basis_state(matrix, rhs):
    size = len(matrix)
    work = [[Q(v) for v in row] + [Q(rhs[i])] for i, row in enumerate(matrix)]
    for j in range(size):
        pivot = next((i for i in range(j, size) if work[i][j]), None)
        if pivot is None:
            return None
        work[j], work[pivot] = work[pivot], work[j]
        divisor = work[j][j]
        work[j] = [v / divisor for v in work[j]]
        for i in range(size):
            if i != j and work[i][j]:
                multiplier = work[i][j]
                work[i] = [a - multiplier * b for a, b in zip(work[i], work[j])]
    return tuple(row[-1] for row in work)


def candidate_components(problem, seed, mu_seed, rows, basis, kind, direction):
    """All first-order root candidates of a nonsingular original basis."""
    if len(rows) != len(basis):
        return None
    A = tuple(tuple(Q(v) for v in row) for row in problem.A)
    c = tuple(Q(v) for v in problem.c)
    direction = Q(direction)
    B = [[A[i][j] for j in basis] for i in rows]
    if kind == "dual":
        matrix = list(zip(*B))
        state = _basis_state(matrix, [c[j] for j in basis])
    else:
        matrix = B
        state = _basis_state(matrix, [-A[i][-1] for i in rows])
    if state is None:
        return None
    variations = []
    for jet, multiplier in ((seed, direction), (mu_seed, Q(1))):
        if kind == "dual":
            rhs = [multiplier * (Q(jet.dc[j]) - sum(Q(jet.dA[i][j]) * state[k] for k, i in enumerate(rows)))
                   for j in basis]
        else:
            rhs = [-multiplier * (Q(jet.dA[i][-1]) + sum(Q(jet.dA[i][j]) * state[k]
                                               for k, j in enumerate(basis))) for i in rows]
        variations.append(_basis_state(matrix, [Q(v) for v in rhs]))
    parameter_state, mu_state = variations
    components = []
    for k in range(len(c) if kind == "dual" else len(basis)):
        if kind == "dual":
            value = sum(A[i][k] * state[j] for j, i in enumerate(rows)) - c[k]
            dp = direction * (sum(seed.dA[i][k] * state[j] for j, i in enumerate(rows)) - seed.dc[k])
            dp += sum(A[i][k] * parameter_state[j] for j, i in enumerate(rows))
            dm = sum(mu_seed.dA[i][k] * state[j] + A[i][k] * mu_state[j] for j, i in enumerate(rows)) - mu_seed.dc[k]
            index = k
        else:
            value, dp, dm, index = state[k], parameter_state[k], mu_state[k], basis[k]
        if value == 0 and (dm < 0 if kind == "dual" else dm > 0):
            components.append({"label": problem.column_labels[index], "index": index,
                               "s": str(-dp / dm), "partial_mu": str(dm),
                               "partial_parameter": str(dp)})
    return {"kind": kind, "basis": list(basis), "rows": list(rows), "components": components}


def _singular_candidates(seed, threshold, rows, basis, kind, direction):
    """Keep every leading component; bounded rational roots are candidates only."""
    matrix, rhs, objective = polynomial_family(seed.affine_path, threshold, Q(0), 1, direction)
    labels = seed.affine_path["problem"].column_labels
    vector = _vector(matrix, objective if kind == "dual" else rhs, rows, basis,
                     kind, len(objective) - 1, labels, {})
    if vector is None:
        return (), None
    denominator, values, _ = vector
    polynomials = ([sub(_poly_dot([matrix[i][j] for i in range(len(matrix))], values),
                       mul(objective[j], denominator)) for j in range(len(objective))]
                   if kind == "dual" else values)
    roots, components = [], []
    indices = range(len(objective)) if kind == "dual" else basis
    for index in indices:
        polynomial = polynomials[index]
        if not polynomial or (kind == "ray" and index == len(objective) - 1):
            continue
        order = min(e for e, _ in polynomial)
        terms = {h: value for (e, h), value in dict(polynomial).items() if e == order}
        coefficient = tuple(terms.get(i, Q(0)) for i in range(max(terms) + 1))
        if len(coefficient) < 2:
            continue
        components.append({"label": labels[index], "index": index,
                           "leading_epsilon_order": order,
                           "leading_polynomial": [str(v / coefficient[-1]) for v in coefficient]})
        reduced = p_divmod(coefficient, p_gcd(coefficient, p_derivative(coefficient)))[0]
        if len(reduced) > 7:
            continue
        bound = Q(1) + max(abs(v / reduced[-1]) for v in reduced[:-1])
        for value in _rational_roots(reduced, -bound, bound):
            if value not in roots:
                roots.append(value)
    return tuple(roots), {"singular": True, "kind": kind, "basis": list(basis),
                          "rows": list(rows), "components": components}


def _matching_components(branch, slope):
    """A certified slope selects all matching labels, not just enumerated roots."""
    if branch.get("singular", False):
        return [dict(component, s=str(slope)) for component in branch["components"]
                if p_eval(tuple(Q(v) for v in component["leading_polynomial"]), slope) == 0]
    return [component for component in branch["components"] if Q(component["s"]) == slope]


def _rational_roots(polynomial, lower, upper):
    """Finite Sturm isolation followed by checked rational reconstruction."""
    pending, found, steps = [(polynomial, lower, upper, 0)], [], 0
    while pending and steps < 512:
        poly, lo, hi, depth = pending.pop()
        steps += 1
        for value in (lo, hi, (lo + hi) / Q(2), rational_candidate2(lo, hi)):
            if len(poly) > 1 and p_eval(poly, value) == 0:
                if value not in found:
                    found.append(value)
                poly = p_divmod(poly, (-value, Q(1)))[0]
        if len(poly) <= 1 or depth >= 64 or _root_count(poly, lo, hi) == 0:
            continue
        mid = (lo + hi) / Q(2)
        pending.append((poly, lo, mid, depth + 1))
        pending.append((poly, mid, hi, depth + 1))
    return tuple(found)


def _poly_dot(left, right):
    value = {}
    for a, b in zip(left, right):
        value = add(value, mul(a, b))
    return value


def _vector(matrix, rhs, rows, basis, kind, alpha, labels, probe):
    if len(rows) != len(basis):
        return None
    B = [[matrix[i][j] for j in basis] for i in rows]
    if kind == "dual":
        solved = solve_polynomial(list(zip(*B)), [rhs[j] for j in basis])
        count, positions = len(matrix), rows
    else:
        target = [neg(matrix[i][alpha]) for i in rows] if kind == "ray" else [rhs[i] for i in rows]
        solved = solve_polynomial(B, target)
        count, positions = len(matrix[0]) if matrix else len(labels), basis
    if solved is None:
        return None
    denominator, values = solved
    numerators = [{} for _ in range(count)]
    for i, value in zip(positions, values):
        numerators[i] = value
    if kind == "ray":
        numerators[alpha] = denominator
    if not _probe_consistent(kind, matrix, rhs, denominator, numerators, probe):
        return None
    return denominator, numerators, {"denominator": wire(denominator),
        "numerators": [wire(v) for v in numerators], "basis": list(basis), "rows": list(rows),
        "labels": [labels[j] for j in basis], "probe": probe}


def _verify_dual(matrix, objective, vector):
    if vector is None:
        return False
    denominator, values, _ = vector
    denominator_sign = sign(denominator)
    return denominator_sign != 0 and all(sign(sub(_poly_dot([matrix[i][j] for i in range(len(matrix))], values),
                mul(objective[j], denominator))) * denominator_sign >= 0 for j in range(len(objective)))


def _verify_primal(matrix, rhs, vector, alpha=None):
    if vector is None:
        return False
    denominator, values, _ = vector
    denominator_sign = sign(denominator)
    if denominator_sign == 0 or any(sign(v) * denominator_sign < 0 for v in values):
        return False
    if any(sub(_poly_dot(row, values), mul(b, denominator))
           for row, b in zip(matrix, rhs)):
        return False
    return alpha is None or not sub(values[alpha], denominator)


def _value_at(poly, epsilon, eta):
    """Exact rational value of a sparse (epsilon, eta) polynomial at a probe.

    Powers are built by repeated multiplication so that the closed static
    construction subset sees no rounding sink on the lifted coefficients.
    """
    total = Q(0)
    for (e, h), coefficient in dict(poly).items():
        term = Q(coefficient)
        for _ in range(e):
            term = term * epsilon
        for _ in range(h):
            term = term * eta
        total = total + term
    return total


def _probe_consistent(kind, matrix, rhs, denominator, numerators, probe):
    """A lifted witness must also hold at its recorded rational probe.

    The ordered-field checks are the proof; this keeps the recorded probe
    independently verifiable (a reused basis may be positive in K yet
    negative at the probe point it was not acquired at).
    """
    if "epsilon" not in probe:
        return True
    epsilon, eta = Q(probe["epsilon"]), Q(probe["eta"])
    d = _value_at(denominator, epsilon, eta)
    if d == 0:
        return False
    if kind == "dual":
        y = [_value_at(v, epsilon, eta) for v in numerators]
        for j in range(len(rhs)):
            slack = -_value_at(rhs[j], epsilon, eta) * d
            for i in range(len(matrix)):
                slack = slack + _value_at(matrix[i][j], epsilon, eta) * y[i]
            if slack * d < 0:
                return False
        return True
    for v in numerators:
        if _value_at(v, epsilon, eta) * d < 0:
            return False
    return True


def _probe(matrix, rhs, objective, epsilon, eta):
    A = [[evaluate(v, epsilon, eta) for v in row] for row in matrix]
    b = [evaluate(v, epsilon, eta) for v in rhs]
    c = [evaluate(v, epsilon, eta) for v in objective]
    answer = _run(A, b, c)
    data = {}
    m, n = len(b), len(c)
    if answer.status == lp.OPTIMAL:
        data["dual"] = _dual_basis(A, c, answer.exact_y)
    elif answer.status == lp.UNBOUNDED:
        ray_answer = _run(A + [c], [Q(0)] * m + [Q(1)], [Q(0)] * n)
        if ray_answer.status == lp.OPTIMAL:
            data["ray"] = _support_basis(A, ray_answer.exact_x, (n - 1,))
        point = _run(A, b, [Q(0)] * n)
        if point.status == lp.OPTIMAL:
            data["point"] = _support_basis(A, point.exact_x)
    elif answer.status == lp.INFEASIBLE:
        # A dual feasible point may exist even when the primal is infeasible.
        # max c.x over {Ax = 0, x >= 0} is OPTIMAL exactly when A^T y >= c is
        # solvable, and its exact dual is a basic point with m independent
        # tight columns; a split-variable witness LP need not return a vertex.
        homogeneous = _run(A, [Q(0)] * m, c)
        if homogeneous.status == lp.OPTIMAL:
            data["dual"] = _dual_basis(A, c, homogeneous.exact_y)
    return data


def _negative_components(vector):
    """Indices whose lifted numerator is negative in K relative to the denominator."""
    denominator, values, _ = vector
    d = sign(denominator)
    return [j for j, v in enumerate(values) if sign(v) * d < 0]


def _probe_targeted(matrix, rhs, objective, epsilon, eta, failing, alpha, ray):
    """Further vertices of the probe polyhedron, one per failing component.

    A degenerate critical face has many vertices and the LP core returns only
    one of them per probe; maximizing the failing coordinate visits a vertex
    where that coordinate is positive. Bases only select; K decides.
    """
    A = [[evaluate(v, epsilon, eta) for v in row] for row in matrix]
    b = [evaluate(v, epsilon, eta) for v in rhs]
    c = [evaluate(v, epsilon, eta) for v in objective]
    n = len(c)
    out = []
    count = 0
    for j in failing:
        if count >= TARGETED_LIMIT:
            break
        count += 1
        goal = [Q(1) if k == j else Q(0) for k in range(n)]
        if ray:
            answer = _run(A + [c], [Q(0)] * len(b) + [Q(1)], goal)
        else:
            answer = _run(A, b, goal)
        if answer.status != lp.OPTIMAL:
            continue
        if ray:
            out.append(_support_basis(A, answer.exact_x, (alpha,)))
        else:
            out.append(_support_basis(A, answer.exact_x))
    return out


def _unbounded_at(A0, A1, b, c, mu):
    """L3 status of the probed geometry at mu; entries are affine in mu."""
    A = [[a0 + mu * (a1 - a0) for a0, a1 in zip(r0, r1)] for r0, r1 in zip(A0, A1)]
    return _run(A, b, c).status == lp.UNBOUNDED


def _probe_threshold_candidates(seed, threshold, domain, direction):
    """Candidate generation only: the exact threshold of the probed geometry
    at a fixed small epsilon, bisected in mu over the original domain (the
    feasible force cone nests in mu), then the simplest rational of the
    quotient bracket. Candidate roots of one LP vertex are basis dependent on
    degenerate critical faces; this route does not depend on which vertex the
    LP returns. Whether the slope is the derivative is decided by K alone."""
    out, mu_max = [], Q(domain["exact_mu_max"])
    for exponent in (BISECTION_EXPONENT,):
        epsilon = Q(1, 1 << exponent)
        # Every matrix entry is affine in mu, so two evaluated families give
        # A(mu) = A0 + mu (A1 - A0) without rebuilding polynomials per step.
        zero = polynomial_family(seed.affine_path, Q(0), Q(0), 0, direction)
        one = polynomial_family(seed.affine_path, Q(1), Q(0), 0, direction)
        A0 = [[evaluate(v, epsilon, Q(0)) for v in row] for row in zero[0]]
        A1 = [[evaluate(v, epsilon, Q(0)) for v in row] for row in one[0]]
        b = [evaluate(v, epsilon, Q(0)) for v in zero[1]]
        c = [evaluate(v, epsilon, Q(0)) for v in zero[2]]

        lo, hi = Q(0), mu_max
        if not _unbounded_at(A0, A1, b, c, hi) or _unbounded_at(A0, A1, b, c, lo):
            continue
        for _ in range(BISECTION_STEPS):
            mid = (lo + hi) / 2
            if _unbounded_at(A0, A1, b, c, mid):
                hi = mid
            else:
                lo = mid
        out.append(rational_candidate2((lo - threshold) / epsilon, (hi - threshold) / epsilon))
    return out


def certify_direction(critical, seed, mu_seed, direction):
    """Try a finite candidate/probe queue; the ordered-field checks are proof."""
    problem = critical.threshold_certificate.problem
    threshold, domain = critical.exact_threshold, critical.search_domain
    slopes, branches, visited = [], [], set()
    seen = {"dual": [], "point": [], "ray": []}

    def add_candidate(rows, basis, kind):
        key = (tuple(rows), tuple(basis), kind)
        if key in visited:
            return
        visited.add(key)
        branch = candidate_components(problem, seed, mu_seed, rows, basis, kind, direction)
        if branch is None:
            candidates, singular = _singular_candidates(seed, threshold, rows, basis, kind, direction)
            if singular is not None:
                branches.append(singular)
            for value in candidates:
                if value not in slopes and len(slopes) < CANDIDATE_LIMIT:
                    slopes.append(value)
            return
        branches.append(branch)
        for component in branch["components"]:
            value = Q(component["s"])
            if value not in slopes and len(slopes) < CANDIDATE_LIMIT:
                slopes.append(value)

    proof = critical.threshold_proof
    if proof is not None:
        branch = proof.upper_basis if critical.attained else proof.lower_basis
        if branch is not None:
            add_candidate(tuple(range(len(problem.b))), branch.basis,
                          "dual" if branch.kind == "mechanism" else "ray")
    if Q(0) not in slopes and len(slopes) < CANDIDATE_LIMIT:
        slopes.append(Q(0))
    attempts, position, boundary_seen, extended = 0, 0, False, False
    while position < len(slopes) and position < CANDIDATE_LIMIT:
        slope = slopes[position]
        position += 1
        lower_mu = add(constant(threshold), {(1, 0): slope, (1, 1): -Q(1)})
        upper_mu = add(constant(threshold), {(1, 0): slope, (1, 1): Q(1)})
        domain_ok = sign(lower_mu) >= 0 and sign(sub(constant(Q(domain["exact_mu_max"])), upper_mu)) >= 0
        if not domain_ok:
            boundary_seen = True
        # Domain-invalid trial slopes can still expose an inward branch at a
        # nearby rational point. Only final K certification needs the sandwich
        # inside the original search domain; probing is candidate generation.
        lower = polynomial_family(seed.affine_path, threshold, slope, -1, direction)
        upper = polynomial_family(seed.affine_path, threshold, slope, 1, direction)
        # Screening probe (same in C++): one LP pair at a small point. Only a
        # candidate whose lower side is bounded and whose upper side is
        # unbounded there can carry a sandwich; the others still contribute
        # their bases as candidates but skip the probe grid and the lifts.
        attempts += 1
        screen = [_probe(family[0], family[1], family[2], SCREEN_EPSILON, SCREEN_ETA) for family in (lower, upper)]
        for data in screen:
            for kind in ("dual", "ray"):
                if kind in data:
                    add_candidate(data[kind][0], data[kind][1], kind)
        screened = "dual" not in screen[0] or "ray" not in screen[1]
        for eta in PROBE_ETA:
            if screened:
                break
            for exponent in PROBE_EXPONENTS:
                epsilon = Q(1, 1 << exponent)
                attempts += 1
                probes = [_probe(family[0], family[1], family[2], Q(epsilon), Q(eta)) for family in (lower, upper)]
                below, above = probes
                for data, kinds in ((below, ("dual",)), (above, ("point", "ray"))):
                    for kind in kinds:
                        if kind in data and data[kind] not in seen[kind]:
                            seen[kind].append(data[kind])
                sample = {"epsilon": str(epsilon), "eta": str(eta)}
                alpha = len(problem.c) - 1
                # Witness acquisition is basis dependent on degenerate probes: the
                # formula lifted from this probe's basis may fail in K while a
                # basis seen at another probe passes here. Bases only select; the
                # ordered-field checks are the proof, and a reused basis must also
                # be nonnegative at this rational probe so the recorded probe
                # stays verifiable.
                dual = point = ray = None
                for rb in reversed(seen["dual"][-RETRY_LIMIT:]):
                    v = _vector(lower[0], lower[2], *rb, "dual", alpha, problem.column_labels, sample)
                    if _verify_dual(lower[0], lower[2], v):
                        dual = v
                        break
                for rb in reversed(seen["point"][-RETRY_LIMIT:]):
                    v = _vector(upper[0], upper[1], *rb, "point", alpha, problem.column_labels, sample)
                    if _verify_primal(upper[0], upper[1], v):
                        point = v
                        break
                for rb in reversed(seen["ray"][-RETRY_LIMIT:]):
                    v = _vector(upper[0], upper[1], *rb, "ray", alpha, problem.column_labels, sample)
                    if _verify_primal(upper[0], [{} for _ in problem.b], v, alpha):
                        ray = v
                        break
                # The LP core may return the same degenerate vertex on every
                # probe; visit further vertices along the failing coordinates.
                for kind, have, lifted in (("point", point, "point"), ("ray", ray, "ray")):
                    if have is not None or kind not in above:
                        continue
                    own = _vector(upper[0], upper[1], *above[kind], kind, alpha, problem.column_labels, sample)
                    if own is None:
                        continue
                    # Vertices are acquired at the fixed screening point; they
                    # are only candidates and are lifted and verified at the
                    # current probe like every other basis.
                    for rb in _probe_targeted(upper[0], upper[1], upper[2], SCREEN_EPSILON, SCREEN_ETA,
                                              _negative_components(own), alpha, kind == "ray"):
                        if rb in seen[kind]:
                            continue
                        seen[kind].append(rb)
                        v = _vector(upper[0], upper[1], *rb, kind, alpha, problem.column_labels, sample)
                        ok = (_verify_primal(upper[0], upper[1], v) if kind == "point" else
                              _verify_primal(upper[0], [{} for _ in problem.b], v, alpha))
                        if ok:
                            if kind == "point":
                                point = v
                            else:
                                ray = v
                            break
                if dual is None or point is None or ray is None:
                    for data in probes:
                        for kind in ("dual", "ray"):
                            if kind in data:
                                add_candidate(data[kind][0], data[kind][1], kind)
                    continue
                if not domain_ok:
                    return {"status": "unresolved", "reason": "threshold_search_domain_boundary",
                            "s": None, "lower": None, "upper": None,
                            "candidate_count": len(slopes), "attempts": attempts, "candidate_branches": []}
                matching = []
                for branch in branches:
                    components = _matching_components(branch, slope)
                    if components:
                        matching.append(dict(branch, components=components))
                return {"status": "certified", "reason": None, "s": str(slope),
                        "lower": dual[2], "upper": {"point": point[2], "ray": ray[2]},
                        "candidate_count": len(slopes), "attempts": attempts, "candidate_branches": matching}
        if position == len(slopes) and not extended:
            # All vertex-derived candidates failed: extend once with the probed
            # geometry's own exact thresholds (on a boundary threshold this can
            # still expose the inward branch; outward sandwiches stay refused).
            extended = True
            for value in _probe_threshold_candidates(seed, threshold, domain, direction):
                if value not in slopes and len(slopes) < CANDIDATE_LIMIT:
                    slopes.append(value)
    return {"status": "unresolved", "reason": ("threshold_search_domain_boundary" if boundary_seen
            else "threshold_branch_certificate_unavailable"), "s": None, "lower": None, "upper": None,
            "candidate_count": len(slopes), "attempts": attempts, "candidate_branches": []}
