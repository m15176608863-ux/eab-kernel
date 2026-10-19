"""Only the three valid L1/L3 implications, and the explicit G5 converse failure.

Every check assembles real geometry once and passes the identical ContactSet2
to mobility and statics. Independent oracles are exact force/moment identities,
signed coordinate wrench bases and hand-calculated wedge/three-block balance.
An unbounded load LP is never used to assert geometric locking. These finite
tests exercise the stated algebraic identities, not a universal sampling proof.
"""
from dataclasses import replace
from fractions import Fraction as F
from itertools import combinations

import pytest

from eab.adapters.tia2d import g1, g5
from eab.kernel2d.assembly import Assembly2, Body2
from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.mobility import first_order_free_twists
from eab.kernel2d.statics import limit_load_ideal_exact_2d


ORIGIN = (F(3, 8), F(-5, 8))


def _complete(bodies, mu=0):
    bodies = tuple(bodies)
    return Assembly2(bodies, tuple(combinations(range(len(bodies)), 2)), "complete", mu=F(mu))


def _body(name, ring, fixed=False, live=(0, 0, 0), dead=(0, 0, 0)):
    return Body2.from_vertices(name, ring, reference_point=ORIGIN, dof_anchor=ORIGIN,
        boundary_type="FIXED_BODY" if fixed else None,
        dof_mask=(0, 0, 0) if fixed else (1, 1, 1), live=live, dead=dead)


def _box(kind, live=(0, 0, 0), dead=(0, 0, 0), mu=0):
    rings = [((0, 0), (1, 0), (1, 1), (0, 1)),
             ((-1, 0), (0, 0), (0, 1), (-1, 1)),
             ((1, 0), (2, 0), (2, 1), (1, 1)),
             ((0, -1), (1, -1), (1, 0), (0, 0)),
             ((0, 1), (1, 1), (1, 2), (0, 2))]
    ids = {"free": (0,), "plane": (0, 3), "seam": (0, 1, 2), "cage": (0, 1, 2, 3, 4)}[kind]
    return _complete((_body(str(i), rings[i], i != 0,
                           live=live if i == 0 else (0, 0, 0),
                           dead=dead if i == 0 else (0, 0, 0)) for i in ids), mu)


def _single_moving(model, moving):
    """All others, including the force plate, become explicit fixed bodies."""
    bodies = tuple(body if i == moving else replace(body, boundary_type="FIXED_BODY",
                   dof_mask=(0, 0, 0), live=(F(0),) * 3, dead=(F(0),) * 3)
                   for i, body in enumerate(model.bodies))
    return replace(model, bodies=bodies)


def _verify_limit(result):
    p = result.problem
    assert result.call_status == "OK" and p is not None
    if result.status == "UNBOUNDED":
        x, r = result.feasible_point, result.improving_ray
        assert x is not None and r is not None and r[-1] == 1
        assert all(v >= 0 for v in (*x, *r))
        assert all(sum(a * b for a, b in zip(row, x)) == rhs for row, rhs in zip(p.A, p.b))
        assert all(sum(a * b for a, b in zip(row, r)) == 0 for row in p.A)
    elif result.status == "OPTIMAL":
        x, y = result.exact_x, result.exact_y
        assert all(v >= 0 for v in x)
        assert all(sum(a * b for a, b in zip(row, x)) == rhs for row, rhs in zip(p.A, p.b))
        assert all(sum(p.A[i][j] * y[i] for i in range(len(p.b))) >= cost
                   for j, cost in enumerate(p.c))
        assert sum(a * b for a, b in zip(p.c, x)) == result.exact_value
        assert sum(a * b for a, b in zip(p.b, y)) == result.exact_value
    else:
        raise AssertionError("hand cases expect an exact optimum or unbounded certificate")


def _query(model):
    contacts = assemble_contact_set2(model)
    assert contacts.status == "RESOLVED" and contacts.completeness == "complete"
    first = first_order_free_twists(model, contacts)
    limit = limit_load_ideal_exact_2d(model, contacts)
    assert first.call_status == "OK" and first.contact_set is contacts
    assert limit.problem is not None and limit.problem.contact_set is contacts
    _verify_limit(limit)
    return first, limit


@pytest.mark.parametrize("mu", (F(0), F(1, 4), F(5, 2)))
@pytest.mark.parametrize("live,dead", [
    ((F(1), F(2), F(3)), (F(0), F(0), F(0))),
    ((F(-3, 8), F(5, 4), F(-7, 16)), (F(1, 4), F(-3, 2), F(3, 8))),
])
def test_implication_1_single_zero_cone_supports_every_wrench_via_basis_certificate(mu, live, dead):
    """±e combinations plus (g+ + g-)/2=N supply any dead/live wrench.

The second load is an artificial LP oracle, not a gravity/TIA geometry case.
The symbolic cancellation of opposite friction terms makes this construction
valid for arbitrary nonnegative mu; the chosen values exercise its assembly.
"""
    first, result = _query(_box("cage", live=live, dead=dead, mu=mu))
    assert first.cone_is_zero is True and result.status == "UNBOUNDED"
    p, G = result.problem, first.matrix
    # Exact contact normal columns are present for every mu as equal averages.
    assert len(p.c) == 2 * len(G) + 1
    for j, normal in enumerate(G):
        for k, value in enumerate(normal):
            assert p.A[k][2 * j] + p.A[k][2 * j + 1] == 2 * value
    basis = {(c.coordinate, c.sign): c.multipliers for c in first.zero_certificates}
    def contact_force(target):
        weights = [F(0)] * len(G)
        for k, value in enumerate(target):
            if value:
                source = basis[k, 1 if value > 0 else -1]
                weights = [w + abs(value) * v for w, v in zip(weights, source)]
        return tuple(v / 2 for w in weights for v in (w, w))
    x0 = contact_force(p.b) + (F(0),)
    ray = contact_force(tuple(-row[-1] for row in p.A)) + (F(1),)
    assert all(v >= 0 for v in (*x0, *ray))
    assert all(sum(a * v for a, v in zip(row, x0)) == rhs for row, rhs in zip(p.A, p.b))
    assert all(sum(a * v for a, v in zip(row, ray)) == 0 for row in p.A)


@pytest.mark.parametrize("kind", ("free", "plane", "seam", "cage"))
def test_implication_2_zero_dead_mu_zero_equivalent_to_six_unbounded_basis_loads(kind):
    answers = []
    for k in range(3):
        for sign in (-1, 1):
            live = tuple(F(sign * (j == k)) for j in range(3))
            first, result = _query(_box(kind, live=live))
            assert all(body.dead == (0, 0, 0) for body in result.problem.assembly.bodies)
            assert result.problem.mu == 0
            answers.append(result.status == "UNBOUNDED")
            if result.status == "OPTIMAL":
                assert result.exact_value == 0
    assert first.cone_is_zero == all(answers)
    assert first.cone_is_zero == (kind == "cage")


@pytest.mark.parametrize("orientation,mu", [("koureas", F(0)), ("unreversed", F(1, 2)),
                                                ("reverse_i1", F(1, 4))])
def test_implication_3_multi_unbounded_central_load_implies_single_body_unbounded(orientation, mu):
    model = g1(t=F(1, 4), height=F(1), orientation=orientation, mu=mu)
    moving = 2
    assert all(body.live == (0, 0, 0) for i, body in enumerate(model.bodies) if i != moving)
    first, multi = _query(model)
    assert first.cone_is_zero is not None and multi.status == "UNBOUNDED"
    single_model = _single_moving(model, moving)
    assert all(body.boundary_type == "FIXED_BODY" and body.dead == (0, 0, 0)
               for i, body in enumerate(single_model.bodies) if i != moving)
    _, single = _query(single_model)
    assert single.status == "UNBOUNDED"


@pytest.mark.parametrize("mu,expected", [(F(1, 4), F(1, 2)), (F(2), F(2))])
def test_g5_converse_of_implication_3_is_false_single_unbounded_multi_finite(mu, expected):
    model = g5(n=3, height=1, pressure=1, width=1, mu=mu)
    _, multi = _query(model)
    single_model = _single_moving(model, 2)
    assert single_model.bodies[-1].boundary_type == "FIXED_BODY"
    assert all(b.dead == (0, 0, 0) for b in single_model.bodies)
    first, single = _query(single_model)
    assert multi.status == "OPTIMAL" and multi.exact_value == expected
    assert single.status == "UNBOUNDED"
    # Explicitly forbid reading its unbounded force cone as geometric locking.
    assert first.cone_is_zero is False and set(first.generators) == {(0, 1, 0), (0, -1, 0)}


@pytest.mark.parametrize("mu,expected", [(F(0), "OPTIMAL"), (F(1, 4), "OPTIMAL"),
                                         (F(1, 2), "UNBOUNDED"), (F(3, 4), "UNBOUNDED")])
def test_single_wedge_hand_threshold_half_with_no_dead_load(mu, expected):
    """e=(2,1), N=(-1,2): vertical support enters at mu=1/2, closed.

The downward live force is at the shared edge midpoint x=1. Endpoint force
splitting balances its moment; below the threshold all reactions point left.
"""
    live = (F(0), F(-1), -(F(1) - ORIGIN[0]))
    moving = _body("wedge", ((0, 0), (2, 1), (0, 2)), live=live)
    fixed = _body("support", ((-1, -2), (3, -2), (2, 1), (0, 0)), True)
    first, result = _query(_complete((moving, fixed), mu))
    assert first.cone_is_zero is False and result.status == expected
    if expected == "OPTIMAL":
        assert result.exact_value == 0
    if mu == F(1, 2):
        assert any(column[:2] == (0, F(5, 2)) for column in tuple(zip(*result.problem.A))[:-1])


def test_symmetric_three_blocks_hand_balance_unbounded_but_upward_first_order_ray():
    """Two support normals (1,1),(-1,1) sum to the vertical unit load.

At mu=0 equal endpoint reactions at the common lower point balance force and
moment exactly. The center can lift in first order, so this is not a lock.
"""
    moving = _body("middle", ((-1, 1), (0, 0), (1, 1)), live=(F(0), F(-1), ORIGIN[0]))
    left = _body("left", ((-2, -1), (0, -1), (0, 0), (-1, 1), (-2, 1)), True)
    right = _body("right", ((0, -1), (2, -1), (2, 1), (1, 1), (0, 0)), True)
    first, result = _query(_complete((moving, left, right)))
    assert result.status == "UNBOUNDED" and first.cone_is_zero is False
    assert all(row[1] >= 0 for row in first.matrix)  # twist (0,1,0) is admissible.
    reaction = {c.normal for c in result.problem.contact_set.constraints if c.point == (0, 0) and c.a == 0}
    assert reaction == {(1, 1), (-1, 1)}
    assert (F(1, 2) * 1 + F(1, 2) * -1, F(1, 2) * 1 + F(1, 2) * 1) == (0, 1)
