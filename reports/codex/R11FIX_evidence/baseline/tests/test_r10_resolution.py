"""R10/J05: analytic force balance and rational ratios, no LP/helper oracle."""
from fractions import Fraction as F
import math

import pytest

import eab.limit as L
import eab.limit_multi as M


def _unbounded(multi, live_scale):
    contacts = [L.LimitContact((-1, 0), (0, 1), .5),
                L.LimitContact((1, 0), (0, 1), .5)]
    dead, live = [0., 1., 0.], [0., -live_scale, 0.]
    if multi:
        return M.limit_load_multi([M.LimitBody(dead, live)],
                                 [M.BodyContact(c, 0) for c in contacts], dim=2)
    return L.limit_load(contacts, dead, live, dim=2)


@pytest.mark.parametrize("multi", [False, True])
@pytest.mark.parametrize("live_scale", [math.ulp(0.0), 2.**-1000, 1., 2.**1000])
def test_unbounded_capacity_reports_finite_analytic_uncertainty_bounds(multi, live_scale):
    # N = alpha*live_scale - 1 >= 0, equal contacts cancel moment. No upper cap.
    result = _unbounded(multi, live_scale)
    assert result.status == "unbounded" and result.alpha == math.inf
    assert math.isfinite(result.uncertainty), "display range must not produce NaN U"
    # Dual optimum: y_y=1/s, |y_x|/2+|omega|<=1/s. Thus U in [u,3u].
    # The solver may select different vertices of this face; U is not invariant.
    assert 4*2.**-53 <= result.uncertainty <= 12*2.**-53
    assert result.resolvability == "resolved"


@pytest.mark.parametrize("multi", [False, True])
@pytest.mark.parametrize("bad", [math.nan, math.inf])
def test_nonfinite_uncertainty_is_never_reported_resolved(monkeypatch, multi, bad):
    # Source-side diagnostic failure injection, before the resolution branches.
    monkeypatch.setattr(M if multi else L, "_live_uncertainty", lambda *args: bad)
    result = _unbounded(multi, 1.)
    assert result.status == "unbounded"
    assert result.resolvability == "unresolved", "unknown U cannot certify resolved"


def test_uncertainty_ratio_completes_before_binary64_display():
    huge = F(2)**2000
    assert L._live_uncertainty([huge], [1/huge], [F(1, 8)/huge]) == .125
    # Exact cancellation leaves a tiny but nonzero drive, not rounded zero.
    assert L._live_uncertainty([huge, -huge+1], [F(1), F(1)], [1/huge]*2) == 2.


def test_rounding_budget_keeps_subnormal_load_information():
    u = F(math.ulp(0.0))
    budget = L._wrench_rounding([0, -u, 0], 2, 1)
    assert budget == [F(4*2.**-53)*u]*3


@pytest.mark.parametrize("multi", [False, True])
@pytest.mark.parametrize("bad", [None, math.nan, math.inf])
def test_optimal_capacity_does_not_use_overflowed_dual_display(monkeypatch, multi, bad):
    contacts = [L.LimitContact((-1, 0), (0, 1), .5),
                L.LimitContact((1, 0), (0, 1), .5)]
    if bad is not None:
        monkeypatch.setattr(M if multi else L, "_live_uncertainty", lambda *args: bad)
    dead, live = [0, -1, 0], [math.ulp(0.0), 0, 0]
    if multi:
        result = M.limit_load_multi([M.LimitBody(dead, live)],
                                   [M.BodyContact(c, 0) for c in contacts], dim=2)
    else:
        result = L.limit_load(contacts, dead, live, dim=2)
    # Independent force sum: alpha*u <= mu*N = 1/2, equality feasible.
    assert result.status == "optimal"
    assert L._rational(result.alpha) == F(1, 2)/F(math.ulp(0.0))
    if bad is None:
        assert math.isfinite(result.uncertainty) and result.uncertainty > 0
        assert result.resolvability == "resolved"
    else:
        assert result.resolvability == "unresolved"


@pytest.mark.parametrize("multi", [False, True])
def test_resolution_gate_kills_premature_noise_display_mutation(monkeypatch, multi):
    # Reinstate the pre-fix arithmetic INSIDE the estimator consumed by the LP
    # report, not a fabricated alteration of the returned LimitResult.
    def premature_budget(w, dim, radius):
        fl, ml = L._norm(w[:dim]), L._norm(w[dim:])
        return [L._U_IN*fl]*dim + [L._U_IN*(ml+fl*radius)]*(len(w)-dim)
    monkeypatch.setattr(M if multi else L, "_wrench_rounding", premature_budget)
    result = _unbounded(multi, math.ulp(0.0))
    assert result.uncertainty == 0.0
    with pytest.raises(AssertionError):
        test_unbounded_capacity_reports_finite_analytic_uncertainty_bounds(multi, math.ulp(0.0))
