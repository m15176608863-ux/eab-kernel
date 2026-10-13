"""O01: independent equilibrium oracle, not LP/geometry/construction helpers.

A single contact at (1,0[,0]) with pure live couple fixes alpha=W and
the reaction=(-H,W) / (-H,0,W). Fraction balance is the oracle; float
is used only for its final expected display. No production columns are
used to compute expected forces. Internal mutants exercise real solvers.
"""
from fractions import Fraction as F
import inspect
import math

import pytest

import eab.limit as single
import eab.limit_multi as multi
from eab.numeric_domain import ConstructionDomainError


def _solve(api, dim, weight, shear, tol=0, mu=F(1, 2)):
    if dim == 2:
        ct = single.LimitContact((1, 0), (0, 1), mu)
        dead, live = [shear, -weight, 0], [0, 0, -1]
    else:
        ct = single.LimitContact((1, 0, 0), (0, 0, 1), mu)
        dead, live = [shear, 0, -weight, 0, 0, 0], [0, 0, 0, 0, 1, 0]
    if api == "single":
        r = single.limit_load([ct], dead, live, dim=dim, k=4, tol=tol)
        proof = single.check_duality(r, [ct], dead, live, dim=dim, k=4)
    else:
        bodies, contacts = [multi.LimitBody(dead, live)], [multi.BodyContact(ct, 0)]
        r = multi.limit_load_multi(bodies, contacts, dim=dim, k=4, tol=tol)
        proof = multi.check_duality_multi(r, bodies, contacts, dim=dim, k=4)
    assert r.status == "optimal" and r.alpha.exact == weight and proof["ok"]
    return r


@pytest.mark.parametrize("api", ["single", "multi"])
@pytest.mark.parametrize("dim", [2, 3])
@pytest.mark.parametrize("weight,shear", [(F(10), F(2)**-60), (F(2)**60, F(1)),
                                          (F(2)**400, F(1)), (F(3, 2), F(1, 8))])
def test_contact_force_report_rounds_complete_exact_sum(api, dim, weight, shear):
    r = _solve(api, dim, weight, shear)
    exact = (-shear, weight) if dim == 2 else (-shear, F(0), weight)
    assert r.contact_forces == [tuple(float(x) for x in exact)], (
        "O01 complete exact resultant", api, dim, exact, r.contact_forces)
    assert r.exact_contact_forces == (exact,)
    assert not r.contact_force_display_underflow
    assert all(type(x) is float for x in r.contact_forces[0])


@pytest.mark.parametrize("api", ["single", "multi"])
@pytest.mark.parametrize("tiny", [F(0), F(2)**-1100, -F(2)**-1100, F(2)**-1075, -F(2)**-1075, F(2)**-1074])
def test_contact_force_nonzero_final_underflow_has_explicit_exact_certificate(api, tiny):
    r = _solve(api, 2, F(10), tiny)
    assert r.exact_contact_forces == ((-tiny, F(10)),), "O01 exact underflow resultant certificate"
    expected = float(-tiny)
    assert r.contact_force_display_underflow == (bool(tiny) and expected == 0), "O01 nonzero force display underflow must be flagged"
    assert r.contact_forces == [(expected, 10.0)]
    assert math.copysign(1.0, r.contact_forces[0][0]) == (-1.0 if tiny > 0 else 1.0)


@pytest.mark.parametrize("api", ["single", "multi"])
def test_contact_force_final_overflow_still_has_named_error(api):
    with pytest.raises(ConstructionDomainError, match="contact force"):
        _solve(api, 2, F(2)**1024, F(1))


@pytest.mark.parametrize("api", ["single", "multi"])
@pytest.mark.parametrize("tol", [0, 1])
def test_contact_force_selection_boundary_and_outputs_differ(api, tol):
    r = _solve(api, 2, F(10), F(0), tol=tol)
    assert r.contact_forces == [(0.0, 10.0 if tol == 0 else 0.0)]
    assert r.exact_contact_forces == ((F(0), F(10) if tol == 0 else F(0)),)
    assert not r.contact_force_display_underflow
    assert _solve(api, 2, F(10), F(0), tol=0).contact_forces != _solve(
        api, 2, F(10), F(0), tol=1).contact_forces


@pytest.mark.parametrize("api", ["single", "multi"])
def test_force_selection_does_not_round_overflowing_intermediate_columns(api):
    # Independent statics: intermediate opposite shear forces exceed maxfloat,
    # but the complete resultant is (-1, 2**1010), inside the output domain.
    try:
        r = _solve(api, 2, F(2)**1010, F(1), mu=F(2)**20)
    except OverflowError as exc:
        pytest.fail(f"O01 selected intermediates must not be constructed: {exc}")
    assert r.contact_forces == [(-1.0, float(F(2)**1010))]


@pytest.mark.parametrize("api", ["single", "multi"])
@pytest.mark.parametrize("mutation", ["product", "accumulator", "unchecked_output", "intermediate_norm", "silent_underflow", "missing_certificate"])
def test_force_report_internal_mutants_hit_resultant_or_domain_assertion(monkeypatch, api, mutation):
    module = single if api == "single" else multi
    name = "limit_load" if api == "single" else "limit_load_multi"
    source = inspect.getsource(getattr(module, name))
    old, new = {
        "product": ("raw[j] * Fraction(C.cols[j][i])", "raw[j] * C.cols[j][i]"),
        "accumulator": ("tuple(Fraction(0) for _ in range(dim))", "tuple(0.0 for _ in range(dim))"),
        "unchecked_output": ('scalar_rational(v, allow_underflow=True, quantity="contact force")', "_fl(v)"),
        "intermediate_norm": ("sum(x*x for x in f)", "Fraction(_norm(f))**2"),
        "silent_underflow": ("contact_force_display_underflow=force_underflow", "contact_force_display_underflow=False"),
        "missing_certificate": ("exact_contact_forces=exact_forces", "exact_contact_forces=()"),
    }[mutation]
    assert source.count(old) == 1
    namespace = dict(vars(module))
    exec(compile(source.replace(old, new), "<O01 actual internal mutant>", "exec"), namespace)
    monkeypatch.setattr(module, name, namespace[name])
    if mutation == "intermediate_norm":
        with pytest.raises(pytest.fail.Exception, match="O01 selected intermediates must not be constructed"):
            test_force_selection_does_not_round_overflowing_intermediate_columns(api)
    elif mutation == "missing_certificate":
        with pytest.raises(AssertionError, match="O01 exact underflow resultant certificate"):
            test_contact_force_nonzero_final_underflow_has_explicit_exact_certificate(api, F(2)**-1100)
    elif mutation == "silent_underflow":
        with pytest.raises(AssertionError, match="O01 nonzero force display underflow must be flagged"):
            test_contact_force_nonzero_final_underflow_has_explicit_exact_certificate(api, F(2)**-1100)
    elif mutation == "unchecked_output":
        with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
            test_contact_force_final_overflow_still_has_named_error(api)
    else:
        with pytest.raises(AssertionError, match="O01 complete exact resultant"):
            test_contact_force_report_rounds_complete_exact_sum(api, 2, F(10), F(2)**-60)
