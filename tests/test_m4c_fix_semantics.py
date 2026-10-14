"""M4cFIX closed-form gates for a double-root graze and a pure EV event.

Primary oracle imports: fractions.Fraction and eab.kernel2d.g0_oracle.overlap
(whose imports are fractions, math.lcm and eab.oracle_construction). Expected
times, states and complete labels come from the explicit half-plane arguments
below. No production root, event polynomial, cone or geometric primitive is
used by the oracle. The motion module is imported only as the tested object;
inspect/textwrap are used only to compile internal defect variants.
"""
from fractions import Fraction as F
import inspect
import textwrap

import pytest

from eab.kernel2d import g0_oracle as oracle
from eab.kernel2d import motion as module


SQUARE = ((0, 0), (1, 0), (1, 1), (0, 1))


def _at(start, end, time):
    return tuple((F(x)+time*(u-x), F(y)+time*(v-y))
                 for (x, y), (u, v) in zip(start, end))


def _double_root_case():
    """A's tip (1-s, 1/4) grazes B's edge 2, y=s*x, only at s=1/2.

    Its signed height above that edge is (s-1/2)**2. B stays below the
    edge; A's two remaining vertices have y=9/4 and x <= 21/20, so their
    heights are >= 9/4-21/20 > 0 throughout [0,1]. Thus the bodies are
    disjoint except at the single interior vertex/edge contact. Both rings
    are nondegenerate CCW triangles throughout the step; no other incidence
    or cover exists at the contact. This is a quadratic double root, unlike
    the existing isolated VV graze with linear event roots.
    """
    A0 = ((1, F(1, 4)), (F(21, 20), F(9, 4)), (F(19, 20), F(9, 4)))
    A1 = tuple((x-1, y) for x, y in A0)
    B0 = ((0, 0), (1, -2), (1, 0))
    B1 = ((0, 0), (1, -2), (1, 1))
    return A0, B0, A1, B1


def _pure_ev_case():
    """B's only lowest vertex has height 2-2*s; A's top edge is edge 2.

    Contact at s=1/2 is strictly inside A's top edge, at (1/2,1).
    B's other vertices are at height 2 then, so no A-vertex/B-edge event
    shares that time. The only incidence and cover are EV(2,0).
    """
    B0 = ((F(1, 2), 2), (F(7, 10), 3), (F(3, 10), 3))
    B1 = tuple((x, y-2) for x, y in B0)
    return SQUARE, B0, SQUARE, B1


def _assert_double_root_contact():
    got = module.motion_first_entrance(*_double_root_case())
    assert got.exact_time == F(1, 2), "quadratic double-root grazing contact time"
    assert (got.initial_state, got.status) == (-1, "contact"), "double-root closed-contact state"
    assert got.incidences == got.features == (("VE", 0, 2),), "double-root complete incidence and cover sets"
    assert got.time == 0.5, "double-root display time"


def _assert_pure_ev_contact():
    got = module.motion_first_entrance(*_pure_ev_case())
    assert got.exact_time == F(1, 2), "pure EV first-contact time"
    assert (got.initial_state, got.status) == (-1, "contact"), "pure EV closed-contact state"
    assert got.incidences == got.features == (("EV", 2, 0),), "pure EV complete incidence and cover sets"
    assert got.time == 0.5, "pure EV display time"


def test_quadratic_double_root_graze_is_closed_contact_with_complete_cover():
    """Hand half-plane proof plus independent integer-winding state oracle."""
    _assert_double_root_contact()
    A0, B0, A1, B1 = _double_root_case()
    for time in (F(0), F(1, 4), F(49, 100), F(1, 2), F(51, 100), F(3, 4), F(1)):
        expected = 0 if time == F(1, 2) else -1
        assert oracle.overlap(_at(A0, A1, time), _at(B0, B1, time)) == expected


def test_pure_ev_first_entrance_matches_independent_closed_form():
    """Hand vertical-height proof plus independent integer-winding oracle."""
    _assert_pure_ev_contact()
    A0, B0, A1, B1 = _pure_ev_case()
    for time in (F(0), F(1, 4), F(49, 100), F(1, 2), F(51, 100), F(3, 4), F(1)):
        expected = -1 if time < F(1, 2) else (0 if time == F(1, 2) else 1)
        assert oracle.overlap(_at(A0, A1, time), _at(B0, B1, time)) == expected


@pytest.mark.parametrize("defect", ("drop_double_root", "drop_ev_events"))
def test_compiled_internal_mutation_fails_new_semantic_assertion_then_restores(monkeypatch, defect):
    """Control green, compiled defect red at named new assertion, restore green."""
    if defect == "drop_double_root":
        target, old, new = "_roots", "if discriminant < 0:", "if discriminant <= 0:"
        guard, message = _assert_double_root_contact, "quadratic double-root grazing contact time"
    else:
        target = "motion_first_entrance"
        old, new = "for p, q in ((a, b), (b, a)):", "for p, q in ((a, b),):"
        guard, message = _assert_pure_ev_contact, "pure EV first-contact time"
    module._validated_motion.cache_clear()
    guard()
    # Mutation scaffolding belongs to this test, not the callable geometry
    # helper inventory checked by the repository's closed-construction gate.
    function = getattr(module, target)
    source = textwrap.dedent(inspect.getsource(function))
    assert source.count(old) == 1, "internal mutation must have one source target"
    namespace = dict(vars(module))
    exec(compile(source.replace(old, new), function.__code__.co_filename + "::M4cFIX-mutant", "exec"), namespace)
    mutant = namespace[function.__name__]
    with monkeypatch.context() as patch:
        patch.setattr(module, target, mutant)
        module._validated_motion.cache_clear()
        with pytest.raises(AssertionError) as failure:
            guard()
        assert str(failure.value).splitlines()[0] == message, "mutant must fail the intended new semantic assertion"
    module._validated_motion.cache_clear()
    guard()
