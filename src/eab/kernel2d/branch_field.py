"""Complete sparse polynomials for the order 0 < epsilon << eta << 1.

No truncated series supplies a sign. Tests in test_threshold_branch.py
exercise the monomial order, exact division and full equation residuals.
"""
from fractions import Fraction as Q


def constant(value=0):
    return {(0, 0): Q(value)} if value else {}


def clean(terms):
    return {key: Q(value) for key, value in dict(terms).items() if value}


def add(left, right):
    result = dict(left)
    for key, value in dict(right).items():
        result[key] = result.get(key, Q(0)) + value
    return clean(result)


def neg(poly):
    return {key: -value for key, value in dict(poly).items()}


def sub(left, right):
    return add(left, neg(right))


def mul(left, right):
    result = {}
    for (e, h), a in dict(left).items():
        for (f, k), b in dict(right).items():
            key = (e + f, h + k)
            result[key] = result.get(key, Q(0)) + a * b
    return clean(result)


def scale(poly, value):
    return {key: Q(value) * a for key, a in dict(poly).items() if value * a}


def divide(numerator, denominator):
    """Exact multivariate division; any remainder is an implementation error."""
    divisor = dict(denominator)
    if not divisor:
        raise ZeroDivisionError("zero polynomial divisor")
    if len(divisor) == 1:
        a, b = next(key for key in divisor)
        value = divisor[a, b]
        if any(e < a or h < b for e, h in numerator):
            raise ArithmeticError("nonexact polynomial division")
        return clean({(e - a, h - b): v / value for (e, h), v in dict(numerator).items()})
    leading = max(divisor)
    remainder, answer = dict(numerator), {}
    while remainder:
        key = max(remainder)
        if key[0] < leading[0] or key[1] < leading[1]:
            raise ArithmeticError("nonexact polynomial division")
        shift = (key[0] - leading[0], key[1] - leading[1])
        factor = remainder[key] / divisor[leading]
        answer[shift] = answer.get(shift, Q(0)) + factor
        for (e, h), value in divisor.items():
            target = (e + shift[0], h + shift[1])
            remainder[target] = remainder.get(target, Q(0)) - factor * value
            if not remainder[target]:
                del remainder[target]
    return clean(answer)


def sign(poly):
    if not poly:
        return 0
    value = poly[min(poly)]
    return (value > 0) - (value < 0)


def evaluate(poly, epsilon, eta):
    return sum((v * epsilon ** e * eta ** h for (e, h), v in dict(poly).items()), Q(0))


def wire(poly):
    return [[e, h, str(poly[e, h])] for e, h in sorted(poly)]


def solve_polynomial(matrix, rhs):
    """Fraction-free Gauss-Jordan: a common denominator and full numerators."""
    size = len(matrix)
    if size == 0:
        return constant(1), []
    work = [[dict(v) for v in row] + [dict(rhs[i])] for i, row in enumerate(matrix)]
    previous = constant(1)
    for k in range(size):
        pivot = next((i for i in range(k, size) if work[i][k]), None)
        if pivot is None:
            return None
        if pivot != k:
            work[k], work[pivot] = work[pivot], work[k]
        diagonal = work[k][k]
        for i in range(size):
            if i == k:
                continue
            factor = work[i][k]
            for j in range(size + 1):
                if j != k:
                    work[i][j] = divide(sub(mul(diagonal, work[i][j]), mul(factor, work[k][j])), previous)
            work[i][k] = {}
        previous = diagonal
    denominator = work[0][0]
    if any(sub(work[i][i], denominator) for i in range(size)):
        raise ArithmeticError("fraction-free diagonal mismatch")
    return denominator, [row[-1] for row in work]


def polynomial_family(path, threshold, slope, side, direction):
    """Rebuild original force/moment formulas from affine geometric primitives."""
    problem = path["problem"]
    epsilon = {(1, 0): Q(direction)}
    mu = add(constant(threshold), clean({(1, 0): Q(slope), (1, 1): Q(side)}))
    contact_seeds, anchor_seeds = dict(path["contact_seeds"]), dict(path["anchor_seeds"])
    reference_seeds = dict(path["reference_seeds"])

    def affine(values, jets):
        return tuple(add(constant(v), scale(epsilon, d)) for v, d in zip(values, jets))

    def cross(a, b):
        return sub(mul(a[0], b[1]), mul(a[1], b[0]))

    bodies = problem.assembly.bodies
    anchors = [affine(body.dof_anchor, anchor_seeds.get(body.body_id, (0, 0))) for body in bodies]
    references = [affine(body.reference_point, reference_seeds.get(body.body_id, (0, 0))) for body in bodies]
    columns = []
    for contact in problem.contact_set.constraints:
        dp, dt = contact_seeds.get(contact.label, ((0, 0), (0, 0)))
        point, tangent = affine(contact.point, dp), affine(contact.tangent, dt)
        normal = (neg(tangent[1]), tangent[0])
        for sense_mu in (-1, 1):
            force = tuple(add(normal[k], scale(mul(mu, tangent[k]), sense_mu)) for k in range(2))
            column = []
            for i, body in enumerate(bodies):
                if body.boundary_type == "FIXED_BODY":
                    continue
                sense = int(i == contact.a) - int(i == contact.b)
                arm = tuple(sub(point[k], anchors[i][k]) for k in range(2))
                full = (scale(force[0], sense), scale(force[1], sense), scale(cross(arm, force), sense))
                column.extend(v for v, free in zip(full, body.dof_mask) if free)
            columns.append(column)

    def load_column(name):
        jets, column = dict(path[name + "_seeds"]), []
        for i, body in enumerate(bodies):
            if body.boundary_type == "FIXED_BODY":
                continue
            raw = body.live if name == "live" else body.dead
            load = affine(raw, jets.get(body.body_id, (0, 0, 0)))
            offset = tuple(sub(anchors[i][k], references[i][k]) for k in range(2))
            full = (load[0], load[1], sub(load[2], cross(offset, load)))
            column.extend(v for v, free in zip(full, body.dof_mask) if free)
        return column
    columns.append(load_column("live"))
    matrix = [[column[i] for column in columns] for i in range(len(problem.b))]
    return matrix, [neg(v) for v in load_column("dead")], [constant(v) for v in problem.c]
