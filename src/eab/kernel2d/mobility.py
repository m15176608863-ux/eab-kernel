"""Exact first-order normal cones for explicitly constrained planar bodies.

Only normal relative velocity is constrained; friction and associated-flow
dilatancy do not enter this geometric query. Unresolved vertex disjunctions
remain unresolved, with no mode enumeration. The precise interpretation is
"锥 = {0} 推出不可动；锥非零推不出可动". Tests: test_tia2d_mobility.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F

from eab import lp
from .assembly import Assembly2, free_dofs
from .contacts import ContactSet2, assemble_contact_set2, constraint_matrix


@dataclass(frozen=True)
class NormalizedConeLP2:
    """Primal/dual proof for max sum(Gv), Gv>=0, sum(Gv)<=1.

The nonnegative variables are v_plus, v_minus, Gv, and one cap slack, in that
order. Original rows, right side, objective and both exact solutions are kept.
"""
    matrix: tuple
    rhs: tuple
    objective: tuple
    exact_x: tuple
    exact_y: tuple


@dataclass(frozen=True)
class ZeroConeCombination2:
    coordinate: int
    sign: int
    multipliers: tuple


@dataclass(frozen=True)
class FirstOrderResult2:
    """A zero/nonzero first-order cone, not a finite-motion certificate.

lineality is an independent basis; generators includes BOTH signs of that
basis in addition to all pointed quotient rays. A nonzero cone deliberately
is not named movable. No boolean mathematical answer accompanies unresolved,
incomplete, invalid or overlapping inputs.
"""
    call_status: str
    mathematical_status: str | None
    cone_is_zero: bool | None = None
    display_status: str = "NOT_APPLICABLE"
    dofs: tuple = ()
    matrix: tuple | None = None
    exact_rank: int | None = None
    normalized_value: F | None = None
    normalization_certificate: NormalizedConeLP2 | None = None
    rays: tuple | None = None
    lineality: tuple | None = None
    generators: tuple | None = None
    zero_certificates: tuple | None = None
    contact_set: ContactSet2 | None = None
    reason: str | None = None
    interpretation: str = "锥 = {0} 推出不可动；锥非零推不出可动"

    @property
    def status(self):
        return self.mathematical_status


def _dot(a, b):
    return sum((u * v for u, v in zip(a, b)), F(0))


def _rank(rows, size):
    values = [[F(v) for v in row] for row in rows]
    if any(len(row) != size for row in values):
        raise ValueError("matrix width mismatch")
    rank = 0
    for column in range(size):
        pivot = next((i for i in range(rank, len(values)) if values[i][column]), None)
        if pivot is None:
            continue
        values[rank], values[pivot] = values[pivot], values[rank]
        factor = values[rank][column]
        values[rank] = [v / factor for v in values[rank]]
        for i in range(rank + 1, len(values)):
            factor = values[i][column]
            if factor:
                values[i] = [u - factor * v for u, v in zip(values[i], values[rank])]
        rank += 1
    return rank


def _ray(direction):
    size = sum((abs(v) for v in direction), F(0))
    return tuple(v / size for v in direction) if size else ()


def _unique_rays(values):
    return tuple(sorted({_ray(v) for v in values if any(v)}))


def _double_description(rows, size):
    """Incremental exact double description, including unconstrained lines.

When a new row sees a free line, project old rays and other lines along it
onto the row, retaining its positive half as one ray. Otherwise use the usual
positive/negative adjacent-ray pairs. Two rays are adjacent modulo free lines
exactly when their common active rows have rank >= n-dim(lineality)-2. All
implicit equalities remain among the processed rows, including lower-rank
faces. Positive L1 normalization never reverses a ray.

Gates: the independent cofactor ray oracle, redundant-row/order tests and the
lineality/halfplane/zero-cone examples in test_tia2d_mobility.py.
"""
    rows = tuple(tuple(F(v) for v in row) for row in rows)
    if any(len(row) != size for row in rows):
        raise ValueError("matrix width mismatch")
    lines = tuple(tuple(F(int(j == k)) for j in range(size)) for k in range(size))
    rays = ()
    processed = []
    for row in rows:
        pivot = next((k for k, line in enumerate(lines) if _dot(row, line)), None)
        if pivot is not None:
            line = lines[pivot]
            value = _dot(row, line)
            if value < 0:
                line = tuple(-v for v in line)
                value = -value
            kept_lines = []
            for k, old in enumerate(lines):
                if k != pivot:
                    ratio = _dot(row, old) / value
                    kept_lines.append(tuple(v - ratio * w for v, w in zip(old, line)))
            projected = []
            for old in rays:
                ratio = _dot(row, old) / value
                projected.append(tuple(v - ratio * w for v, w in zip(old, line)))
            lines = _unique_rays(kept_lines)
            rays = _unique_rays((*projected, line))
        else:
            positive, negative, zero = [], [], []
            for ray in rays:
                value = _dot(row, ray)
                if value > 0:
                    positive.append((ray, value))
                elif value < 0:
                    negative.append((ray, value))
                else:
                    zero.append(ray)
            added = []
            for a, av in positive:
                for b, bv in negative:
                    common = [old for old in processed if _dot(old, a) == _dot(old, b) == 0]
                    if _rank(common, size) >= size - len(lines) - 2:
                        added.append(tuple(av * v - bv * u for u, v in zip(a, b)))
            rays = _unique_rays((*zero, *(a for a, _ in positive), *added))
        processed.append(row)
    if any(_dot(row, ray) < 0 for row in rows for ray in rays):
        raise ArithmeticError("ray failed exact feasibility")
    if any(_dot(row, line) != 0 for row in rows for line in lines):
        raise ArithmeticError("free line failed exact feasibility")
    if _rank(lines, size) != size - _rank(rows, size):
        raise ArithmeticError("free line basis has incorrect rank")
    return rays, lines


def _run_exact(A, b, c):
    # Rounded zero data is merely a candidate; exact= supplies the full model.
    return lp.maximize([[0.0] * len(c) for _ in A], [0.0] * len(b),
                       [0.0] * len(c), exact=(A, b, c))


def _normalized_lp(rows, size):
    count = len(rows)
    A = tuple(tuple(row) + tuple(-v for v in row)
              + tuple(F(-int(i == j)) for j in range(count)) + (F(0),)
              for i, row in enumerate(rows))
    A += ((F(0),) * (2 * size) + (F(1),) * (count + 1),)
    b = (F(0),) * count + (F(1),)
    c = (F(0),) * (2 * size) + (F(1),) * count + (F(0),)
    result = _run_exact(A, b, c)
    if result.status != lp.OPTIMAL or result.exact_x is None or result.exact_y is None:
        raise ArithmeticError("normalized cone LP lacks exact optimum")
    x, y = tuple(result.exact_x), tuple(result.exact_y)
    value = _dot(c, x)
    if (value not in (0, 1) or any(v < 0 for v in x)
            or any(_dot(row, x) != rhs for row, rhs in zip(A, b))
            or any(sum((A[i][j] * y[i] for i in range(len(b))), F(0)) < c[j]
                   for j in range(len(c))) or _dot(b, y) != value):
        raise ArithmeticError("normalized cone certificate failed exact verification")
    return value, NormalizedConeLP2(A, b, c, x, y)


def _zero_combinations(rows, size):
    A = tuple(tuple(row[k] for row in rows) for k in range(size))
    proofs = []
    for coordinate in range(size):
        for sign in (-1, 1):
            target = tuple(F(sign * int(k == coordinate)) for k in range(size))
            result = _run_exact(A, target, (F(0),) * len(rows))
            if result.status != lp.OPTIMAL or result.exact_x is None:
                raise ArithmeticError("zero cone combination unavailable")
            weights = tuple(result.exact_x)
            if any(v < 0 for v in weights) or any(_dot(row, weights) != v for row, v in zip(A, target)):
                raise ArithmeticError("zero cone combination failed exact verification")
            proofs.append(ZeroConeCombination2(coordinate, sign, weights))
    return tuple(proofs)


def first_order_free_twists(assembly, contact_set=None):
    """Exact single-body or multi-body cone in actual free twist coordinates.

To request a single-body cone, explicitly fix every other body in Assembly2.
The same complete resolved ContactSet2 must be used for geometric/static
implication checks. Masks and rotation columns use the declared DOF anchors.
Zero requires BOTH full column rank and normalized optimum zero; a free line
is invisible to that objective. No friction-dependent dilation is added.
"""
    if not isinstance(assembly, Assembly2):
        return FirstOrderResult2("INVALID_INPUT", None, reason="expected_assembly")
    dofs = free_dofs(assembly)
    if contact_set is None:
        contact_set = assemble_contact_set2(assembly)
    if not isinstance(contact_set, ContactSet2) or contact_set.assembly != assembly:
        return FirstOrderResult2("INVALID_INPUT", None, dofs=dofs, reason="assembly_mismatch")
    if contact_set.call_status != "OK":
        return FirstOrderResult2(contact_set.call_status, None, reason=contact_set.reason,
                                 contact_set=contact_set, dofs=dofs)
    if contact_set.status == "MECHANICAL_UNRESOLVED" or contact_set.unresolved:
        return FirstOrderResult2("OK", "MECHANICAL_UNRESOLVED", contact_set=contact_set,
                                 reason="contact_set_unresolved", dofs=dofs)
    if contact_set.status != "RESOLVED":
        return FirstOrderResult2("OK", contact_set.mathematical_status,
                                 contact_set=contact_set, reason=contact_set.reason, dofs=dofs)
    if contact_set.completeness != "complete":
        return FirstOrderResult2("OK", "UNPROVED", contact_set=contact_set,
                                 reason="completeness_unknown", dofs=dofs)
    rows, dofs = constraint_matrix(assembly, contact_set.constraints)
    size = len(dofs)
    try:
        rank = _rank(rows, size)
        value, proof = _normalized_lp(rows, size)
        rays, lines = _double_description(rows, size)
        zero = rank == size and value == 0
        if zero != (not rays and not lines):
            raise ArithmeticError("double description and normalized rank test disagree")
        combinations = _zero_combinations(rows, size) if zero else ()
    except (ArithmeticError, RuntimeError) as error:
        return FirstOrderResult2("INTERNAL_ERROR", None, dofs=dofs, matrix=rows,
                                 contact_set=contact_set, reason=str(error))
    generators = _unique_rays((*rays, *lines, *(tuple(-v for v in line) for line in lines)))
    return FirstOrderResult2("OK", "ZERO_CONE" if zero else "NONZERO_CONE", zero,
                             display_status="EXACT", dofs=dofs, matrix=rows, exact_rank=rank,
                             normalized_value=value, normalization_certificate=proof,
                             rays=rays, lineality=lines, generators=generators,
                             zero_certificates=combinations, contact_set=contact_set)
