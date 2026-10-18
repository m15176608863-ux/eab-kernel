"""R13FIXb public jet/report/adapter differential gates.

Oracle: raw Fraction polynomials and test-owned binary64-cell search; no
production derivatives, geometry, normalisation or LP assembly are reused.
Legacy tolerance diagnostics use their documented rounded-length input model.
"""
from fractions import Fraction as F
import inspect
import math
from types import SimpleNamespace

import pytest

from construction_oracle import scalar_exact, sqrt_exact
from eab import dual, margin, limit, limit_multi
from eab.kernel3d.geom3 import Polyhedron
from eab.adapters import tia3d as interlock
from eab.kernel3d.exact_sweep import translate_exact
from eab.numeric_domain import ConstructionDomainError


SCALES = (-397, 0, 397)


@pytest.mark.parametrize("exponent", [-400,0,400])
def test_dual_public_seed_constructors_and_accessors(exponent):
    s = F(2)**exponent
    values = [s,-s,0]
    lifted,seeded = dual.lift(values,3),dual.seeded(values)
    for i,v in enumerate(values):
        c = dual.Dual.const(v,3)
        d = dual.Dual.seed(v,3,i)
        assert c.v == d.v == scalar_exact(v), "seed constructor primal reference"
        assert c.e == (0.0,)*3 and d.e == tuple(float(j == i) for j in range(3))
        assert c == lifted[i] and d == seeded[i]
        assert dual.val(d) == scalar_exact(v) and dual.grad(d) == d.e and d.width == 3
    assert dual.grad(s,3) == (0.0,)*3


def test_dual_access_predicates_preserve_arbitrary_rational_values():
    q = F(2)**-2000
    assert dual.val(q) == q
    assert not dual.is_exact_zero(q)
    assert dual.Dual(0.0,(q,)).is_exact_zero() is False
    assert dual.Dual(0.0,()) < q and dual.Dual(0.0,()) <= q
    assert dual.Dual(0.0,()) > -q and dual.Dual(0.0,()) >= -q


@pytest.mark.parametrize("exponent", [-1100,1100])
def test_dual_seed_constructor_unrepresentable_primal_is_named(exponent):
    q = F(2)**exponent
    for call in (lambda: dual.Dual.const(q,1),lambda: dual.Dual.seed(q,1,0),
                 lambda: dual.lift([q],1),lambda: dual.seeded([q])):
        with pytest.raises(ConstructionDomainError,match="Dual"):
            call()


@pytest.mark.parametrize("exponent", SCALES)
def test_dual_algebra_each_channel_matches_independent_rational_reference(exponent):
    s = F(2)**exponent
    x, y = dual.Dual(3*s, (5*s, -7*s)), dual.Dual(2*s, (-s, 4*s))
    cases = [
        (x+y, 5*s, (4*s, -3*s)),
        (-x, -3*s, (-5*s, 7*s)),
        (x-y, s, (6*s, -11*s)),
        (2*s-x, -s, (-5*s, 7*s)),
        (x*y, 6*s*s, (7*s*s, -2*s*s)),
        (x/y, F(3, 2), (F(13, 4), F(-13, 2))),
        (2*s/x, F(2, 3), (F(-10, 9), F(14, 9))),
    ]
    for got, primal, channels in cases:
        assert got.v == scalar_exact(primal), "Dual primal exact expression"
        assert got.e == tuple(scalar_exact(q) for q in channels), "Dual derivative exact expression"


@pytest.mark.parametrize("exponent", SCALES)
def test_dual_mixed_scalar_is_not_rounded_before_arithmetic(exponent):
    s = F(2)**exponent
    # The omitted 2**-54 is below a standalone binary64 ulp, but not below
    # the final cancellation result. This is an input-domain failure at 1.
    q = (1+F(2)**-54)*s
    x = dual.Dual(-s, (s,))
    result = x+q
    assert result.v == scalar_exact(F(2)**-54*s), "mixed scalar retained before cancellation"
    assert result.e == (scalar_exact(s),)


@pytest.mark.parametrize("exponent", SCALES)
def test_dual_cancelled_products_keep_complete_expression(exponent):
    s = math.ldexp(1.0, exponent)
    u, v = 1+2.0**-27, 1-2.0**-27
    x, y = dual.Dual(u, (-u*s,)), dual.Dual(v, (s,))
    expected = F(-u*s)*F(v)+F(u)*F(s)
    assert (x*y).e == (scalar_exact(expected),), "Dual derivative exact expression"
    quotient = (F(-u*s)*F(v)-F(u)*F(s))/(F(v)*F(v))
    assert (x/y).e == (scalar_exact(quotient),), "Dual quotient complete expression"


@pytest.mark.parametrize("exponent", [-400, 0, 400])
@pytest.mark.parametrize("power", [2, -1, 0.5, 1.5])
def test_dual_integer_and_half_power_complete_values(exponent, power):
    value = math.ldexp(1.0, exponent)
    seed = value
    got = dual.Dual(value, (seed, -seed, 0.0))**power
    if float(power).is_integer():
        expected = scalar_exact(F(value)**int(power))
        derivative = scalar_exact(F(power)*F(value)**(int(power)-1)*F(seed))
    else:
        expected = sqrt_exact(F(value)**int(2*power))
        derivative = sqrt_exact((F(power)*F(seed))**2*F(value)**(int(2*power)-2))
    assert got.v == expected, "power primal exact reference"
    assert got.e == (derivative, -derivative, 0.0), "power derivative exact reference"


@pytest.mark.parametrize("operation", [
    lambda: dual.Dual(F(2)**1023, (0,))+F(2)**1023,
    lambda: dual.Dual(-F(2)**1023, (0,))-F(2)**1023,
    lambda: dual.Dual(F(2)**-600, (0,))*F(2)**-600,
    lambda: dual.Dual(F(2)**-600, (0,))/F(2)**600,
    lambda: F(2)**-600/dual.Dual(F(2)**600, (0,)),
    lambda: dual.Dual(F(2)**-400, (1,))**3,
])
def test_dual_unrepresentable_output_is_a_named_domain_error(operation):
    with pytest.raises(ConstructionDomainError, match="scalar|Dual"):
        operation()


@pytest.mark.parametrize("exponent", [-395, 0, 397])
def test_public_difference_reports_against_independent_sample_model(exponent):
    s = F(2)**exponent
    theta, h = [3*s], s/8
    f = lambda t: F(t[0])**2
    got = dual.central_difference(f, theta, h)
    assert got == [scalar_exact(6*s)], "finite difference complete sample quotient"
    hs = [s/8, s/16, s/32]
    cubic = lambda t: F(t[0])**3/(s*s)
    report = dual.convergence_order(cubic, theta, [27.0], hs)
    expected_errors = {step: scalar_exact((step/s)**2) for step in hs}
    assert report["errors"] == expected_errors, "diagnostic per-step rational error"
    assert report["valley_h"] == hs[-1]
    assert report["valley_error"] == expected_errors[hs[-1]]
    assert report["large_h_order"] == 2.0, "diagnostic independent exact convergence order"


@pytest.mark.parametrize("exponent", [-401, 401])
def test_public_difference_input_domain_fails_loudly(exponent):
    with pytest.raises(ConstructionDomainError, match="central_difference.theta"):
        dual.central_difference(lambda t: t[0], [F(2)**exponent], F(1))
    with pytest.raises(ConstructionDomainError, match="central_difference.h"):
        dual.central_difference(lambda t: t[0], [F(1)], F(2)**exponent)
    with pytest.raises(ConstructionDomainError, match="convergence_order.analytic"):
        dual.convergence_order(lambda t: t[0], [F(1)], [F(2)**exponent], [F(1)])


@pytest.mark.parametrize("bad", [math.inf,math.nan])
def test_difference_nonfinite_callback_is_a_named_domain_error(bad):
    with pytest.raises(ConstructionDomainError,match="central_difference.f"):
        dual.central_difference(lambda t: bad,[1.0],0.5)


def test_convergence_report_does_not_overflow_the_intermediate_error_ratio():
    def f(t):
        return F(t[0])*F(2)**(800 if abs(t[0]) == 0.5 else -800)
    report = dual.convergence_order(f,[0.0],[0.0],[0.5,0.25])
    assert report["errors"] == {0.5: scalar_exact(F(2)**800), 0.25: scalar_exact(F(2)**-800)}
    assert report["large_h_order"] == 1600.0, "finite log ratio report"


def _box(s):
    vertices = [(x*s, y*s, z*s) for x,y,z in
                [(0,0,0),(3,0,0),(3,4,0),(0,4,0),(0,0,12),(3,0,12),(3,4,12),(0,4,12)]]
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    return Polyhedron(vertices, faces)


@pytest.mark.parametrize("exponent", [-400, 0, 395])
def test_margin_public_diagnostics_each_value_against_rational_report_model(exponent):
    s = F(2)**exponent
    a, b = _box(s), _box(2*s)
    length, magnitude = 13*s, 24*s
    floor = F(64)*F(2)**-52*magnitude
    assert margin.characteristic_length(a, b) == scalar_exact(length), "margin characteristic rational length"
    assert margin.coordinate_magnitude(a, b) == magnitude, "margin coordinate magnitude exact selection"
    assert margin.rounding_floor(a, b) == scalar_exact(floor), "margin rounding-floor exact report"
    geom = max(F(1e-9)*length, floor)
    band = max(F(1e-12)*length, floor)
    assert margin.effective_geom_tol(a, b) == scalar_exact(geom), "margin geometry-tolerance report"
    assert margin.boundary_band(a, b) == scalar_exact(band), "margin boundary-band report"
    expected = max(F(scalar_exact(geom)), F(1e-12)*26*s)+F(scalar_exact(floor))
    assert margin.contact_resolution(a, b) == scalar_exact(expected), "margin contact-resolution complete sum"
    for explicit in (s/8, 16*s):
        assert margin.effective_geom_tol(a,b,explicit) == scalar_exact(max(explicit,floor))
        assert margin.boundary_band(a,b,explicit) == scalar_exact(max(explicit,floor))


@pytest.mark.parametrize("exponent", [-400,0,385])
def test_contact_resolution_rounds_after_both_report_terms(exponent):
    s = F(2)**exponent
    a,b = _box(s),_box(1132*s)
    floor = F(64)*F(2)**-52*12*1132*s
    geom = max(F(scalar_exact(F(1e-9)*13*s)),F(scalar_exact(floor)))
    expected = scalar_exact(max(geom,F(1e-12)*13*1132*s)+F(scalar_exact(floor)))
    assert margin.contact_resolution(a,b) == expected, "resolution final complete expression"


@pytest.mark.parametrize("exponent", SCALES)
def test_cover_witness_final_distance_and_direction(exponent):
    s = F(2)**exponent
    c = SimpleNamespace(point_a=(3*s,4*s,0), point_b=(0,0,0),
                        in_extent=False, exact_gap_sign=None, normal=None)
    d,n = margin.cover_witness(c)
    assert d == scalar_exact(5*s), "witness independent rational length"
    assert n == (scalar_exact(F(3,5)), scalar_exact(F(4,5)), 0.0), "witness rational direction"
    c.in_extent, c.exact_gap_sign, c.normal = True, -1, (0.0,1.0,0.0)
    assert margin.cover_witness(c) == (scalar_exact(5*s), (0.0,-1.0,0.0))
    c.point_a = None
    assert margin.cover_witness(c) is None


@pytest.mark.parametrize("exponent", [-1100, 1100])
def test_margin_quantitative_output_outside_range_is_named(exponent):
    s = F(2)**exponent
    p = _box(s)
    for function in (lambda: margin.characteristic_length(p), lambda: margin.rounding_floor(p),
                     lambda: margin.effective_geom_tol(p,p), lambda: margin.boundary_band(p,p),
                     lambda: margin.contact_resolution(p,p)):
        with pytest.raises(ConstructionDomainError):
            function()
    c = SimpleNamespace(point_a=(s,0,0), point_b=(0,0,0),
                        in_extent=False, exact_gap_sign=None, normal=None)
    with pytest.raises(ConstructionDomainError):
        margin.cover_witness(c)


@pytest.mark.parametrize("exponent", SCALES)
@pytest.mark.parametrize("side", ["a", "b", "mid"])
def test_contact_adapters_each_field_against_rational_reference(exponent, side):
    s = F(2)**exponent
    pa, pb = (s,2*s,3*s), (-s,4*s,7*s)
    c = SimpleNamespace(point_a=pa,point_b=pb,normal=(3*s,4*s,0),label=lambda: ("VF",1,2))
    rows = limit.contacts_from_covers([c],mu=F(3,8),side=side)
    multi = limit_multi.contacts_from_covers_multi([c],7,3,mu=F(3,8),side=side)
    expected = pa if side == "a" else pb if side == "b" else tuple(scalar_exact((a+b)/2) for a,b in zip(pa,pb))
    for got in [rows[0],multi[0].contact]:
        assert got.point == expected, "adapter exact final midpoint/selected coordinates"
        assert got.normal == (scalar_exact(F(3,5)),scalar_exact(F(4,5)),0.0), "adapter rational unit normal"
        assert (got.mu,got.cohesion,got.area,got.label,got.tangent) == (F(3,8),0.0,0.0,("VF",1,2),None)
    assert (multi[0].body_a,multi[0].body_b) == (7,3)


@pytest.mark.parametrize("exponent", [-1100, 1100])
def test_adapter_unrepresentable_midpoint_is_named(exponent):
    c = SimpleNamespace(point_a=(F(2)**exponent,0),point_b=(F(2)**exponent,0),
                        normal=(0,1),label=lambda: ("VF",1,2))
    for call in (lambda: limit.contacts_from_covers([c],mu=0,side="mid"),
                 lambda: limit_multi.contacts_from_covers_multi([c],0,None,mu=0,side="mid")):
        with pytest.raises(ConstructionDomainError):
            call()


def test_witness_and_adapter_keep_domain_internal_cancellation():
    c = SimpleNamespace(point_a=(F(1)+F(2)**-54,0,0),point_b=(1.0,0,0),
                        in_extent=False,exact_gap_sign=None,normal=None)
    assert margin.cover_witness(c)[0] == scalar_exact(F(2)**-54), "witness cancellation retained"
    c.point_b,c.normal,c.label = (-1.0,0,0),(0,1,0),lambda:("VF",1,2)
    assert limit.contacts_from_covers([c],mu=0,side="mid")[0].point[0] == scalar_exact(F(2)**-55), "adapter cancellation retained"


@pytest.mark.parametrize("exponent", [-400,0,400])
def test_duality_reports_have_independent_analytic_values(exponent):
    s = F(2)**exponent
    contacts = [limit.LimitContact((x,0),(0,1),0.5) for x in (-1,1)]
    dead,live = [0,-s,0],[1,0,0]
    lambdas,mechanism = [s/2,0,s/2,0],[1,F(1,2),0]
    result = limit.LimitResult("optimal",s/2,lambdas,mechanism)
    multi = limit_multi.MultiLimitResult("optimal",s/2,lambdas,[mechanism])
    body_contacts = [limit_multi.BodyContact(c,0) for c in contacts]
    reports = [limit.check_duality(result,contacts,dead,live,dim=2),
               limit_multi.check_duality_multi(multi,[limit_multi.LimitBody(dead,live)],body_contacts,dim=2)]
    expected = {"admissible":True,"worst_power":0.0,"worst_power_rel":0.0,"drive":1.0,
                "upper_bound":scalar_exact(s/2),"alpha":scalar_exact(s/2),"duality_gap":0.0,
                "duality_gap_rel":0.0,"complementarity":0.0,"static_residual_rel":0.0,
                "static_ok":True,"static_residual_exact":("0","0","0"),"duality_gap_exact":"0",
                "complementarity_exact":("0","0","0","0","0"),"ok":True}
    for report in reports:
        assert report == expected, "duality all report fields independent analytic reference"
    assert limit.mechanism_is_admissible(mechanism,contacts,dim=2)
    assert limit_multi.mechanism_is_admissible_multi([mechanism],body_contacts,dim=2)


@pytest.mark.parametrize("exponent", [-1100,-400,0,400,1100])
def test_entrance_block_is_exact_rational_geometry_not_float_construction(exponent):
    s = F(2)**exponent
    p = Polyhedron([(0,0,0),(s,0,0),(0,2*s,0),(0,0,3*s)],
                   [(0,2,1),(0,1,3),(1,2,3),(0,3,2)])
    result = margin.entrance_block_convex(p,p)
    exact = {tuple(F(b[i])-F(a[i]) for i in range(3)) for a in p.verts for b in p.verts if a != b}
    assert set(result.verts) == exact, "entrance block exact difference vertices"
    assert all(isinstance(v,F) for p in result.verts for v in p)


def _internal_mutant(monkeypatch, module, name, old, new):
    source = inspect.getsource(getattr(module,name))
    assert source.count(old) == 1, "mutation anchor is uniquely pinned"
    scope = dict(vars(module))
    exec(compile(source.replace(old,new), f"<r13fixb-{name}-mutant>", "exec"), scope)
    monkeypatch.setattr(module,name,scope[name])


def test_dual_product_early_rounding_mutant_fails_value_assertion(monkeypatch):
    _internal_mutant(monkeypatch,dual,"_product_derivative",
                     "_derivative_float(Fraction(a) * Fraction(v) + Fraction(u) * Fraction(b))", "a*v+u*b")
    with pytest.raises(AssertionError,match="Dual derivative exact expression"):
        test_dual_cancelled_products_keep_complete_expression(0)


def test_difference_early_sample_rounding_mutant_fails_value_assertion(monkeypatch):
    _internal_mutant(monkeypatch,dual,"central_difference",
                     'exact_input(fp, "central_difference.f(tp)") - exact_input(fm, "central_difference.f(tm)")',
                     "Fraction(float(fp)) - Fraction(float(fm))")
    s = F(1)
    f = lambda t: (F(t[0])-s)*F(2)**-54+s
    # f(1 +/- 1/8) rounds to the same float, but the exact callback sample
    # model has the representable derivative 2**-54.
    with pytest.raises(AssertionError,match="sample callback exact quotient"):
        assert dual.central_difference(f,[s],s/8) == [scalar_exact(F(2)**-54)], "sample callback exact quotient"


def test_difference_domain_guard_removal_fails_rejection_assertion(monkeypatch):
    monkeypatch.setattr(dual,"check_inputs",lambda values,quantity: None)
    with pytest.raises(pytest.fail.Exception,match="DID NOT RAISE"):
        test_public_difference_input_domain_fails_loudly(401)


def test_cover_witness_early_difference_mutant_fails_value_assertion(monkeypatch):
    _internal_mutant(monkeypatch,margin,"cover_witness",
                     "_exact.sub(_exact.vector(c.point_a), _exact.vector(c.point_b))",
                     "tuple(float(a)-float(b) for a,b in zip(c.point_a,c.point_b))")
    a = (F(1)+F(2)**-54,0,0)
    # One rational and one binary64 operand makes the legacy raw subtraction
    # round before cancellation; no extreme exponent is necessary.
    c = SimpleNamespace(point_a=a,point_b=(1.0,0,0),in_extent=False,exact_gap_sign=None,normal=None)
    with pytest.raises(AssertionError,match="witness cancellation retained"):
        assert margin.cover_witness(c)[0] == scalar_exact(F(2)**-54), "witness cancellation retained"


def test_adapter_early_midpoint_mutant_fails_value_assertion(monkeypatch):
    _internal_mutant(monkeypatch,limit,"contacts_from_covers",
                     "_construction_float((Fraction(a) + Fraction(b))/2)", "(a+b)/2")
    c = SimpleNamespace(point_a=(F(1)+F(2)**-54,0),point_b=(-1.0,0),normal=(0,1),label=lambda:("VF",1,2))
    with pytest.raises(AssertionError,match="adapter cancellation retained"):
        result = limit.contacts_from_covers([c],mu=0,side="mid")
        assert result[0].point[0] == scalar_exact(F(2)**-55), "adapter cancellation retained"


def test_resolution_early_product_mutant_fails_value_assertion(monkeypatch):
    _internal_mutant(monkeypatch,margin,"contact_resolution",
                     "Fraction(1e-12) * Fraction(diag)","Fraction(1e-12 * diag)")
    with pytest.raises(AssertionError,match="resolution final complete expression"):
        test_contact_resolution_rounds_after_both_report_terms(0)


def test_scale_grid_produces_distinct_constructed_outputs():
    jets,distances,diagnostics,adapters = [],[],[],[]
    for e in SCALES:
        s = F(2)**e
        jets.append((dual.Dual(3*s,(s,))*dual.Dual(2*s,(s,))).v)
        p = _box(s)
        distances.append(margin.characteristic_length(p))
        diagnostics.append(margin.rounding_floor(p))
        c = SimpleNamespace(point_a=(s,2*s),point_b=(3*s,4*s),normal=(0,1),label=lambda:("VF",1,2))
        adapters.append(limit.contacts_from_covers([c],mu=0,side="mid")[0].point)
    assert all(len(set(values)) == 3 for values in (jets,distances,diagnostics,adapters)), "scale grid must change numerical products"


def test_subnormal_escape_keeps_internal_thresholds_exact_and_public_reports_strict(monkeypatch):
    """Oracle is an axis-box z interval and raw Fraction diagnostic formulas.

    No production overlap, cover, root or tolerance primitive computes the
    reference. The spy observes thresholds actually reaching the candidate
    path, rather than substituting manufactured output after enumeration.
    """
    s = F(2)**-1070
    a,b = _box(s),_box(s)
    offset = (s/4,0,s/4)
    observed = []
    actual_candidates = interlock._candidates

    def observe(a,b,offset,tol,extent_tol):
        rows,r = actual_candidates(a,b,offset,tol,extent_tol)
        observed.append((extent_tol,r))
        return rows,r

    monkeypatch.setattr(interlock,"_candidates",observe)
    result = interlock.escape_height_covers(a,b,offset)
    candidates = interlock.escape_candidates(a,b,offset)
    root = 47*s/4
    assert result.exact_height == root and result.height == scalar_exact(root) > 0, "subnormal independent exact escape root"
    assert candidates and any(z == scalar_exact(root) for z,_ in candidates)
    expected_r = F(64)*F(2)**-52*13*s
    expected_g = max(F(1e-9)*13*s,expected_r)
    assert observed and all(isinstance(g,F) and g == expected_g > 0 for g,_ in observed), "internal gtol must not round to zero"
    assert all(isinstance(r,F) and r == expected_r > 0 for _,r in observed), "internal rounding floor must not round to zero"
    at = translate_exact(a,offset)
    with pytest.raises(ConstructionDomainError,match="effective_geom_tol result"):
        margin.effective_geom_tol(at,b)
    with pytest.raises(ConstructionDomainError,match="rounding_floor result"):
        margin.rounding_floor(at,b)


def test_public_max_window_does_not_construct_a_rejected_smaller_operand():
    s = F(2)**-1070
    p = translate_exact(_box(s),(F(1),0,0))
    expected = scalar_exact(F(64)*F(2)**-52*(1+3*s))
    assert margin.effective_geom_tol(p,p) == expected, "only final maximum is a construction"
    assert margin.boundary_band(p,p) == expected, "only final boundary maximum is a construction"


@pytest.mark.parametrize("name,message", [
    ("_effective_geom_tol_exact","internal gtol must not round to zero"),
    ("_rounding_floor_exact","internal rounding floor must not round to zero"),
])
def test_subnormal_internal_threshold_early_rounding_mutant_is_caught(monkeypatch,name,message):
    source = inspect.getsource(getattr(margin,name))
    if name == "_effective_geom_tol_exact":
        old,new = "return max(base, _rounding_floor_exact(A, B))", "return float(max(base, _rounding_floor_exact(A, B)))"
    else:
        old = "return (Fraction(ROUNDING_C) * Fraction(_EPS) *\n            max(Fraction(coordinate_magnitude(*bodies)), Fraction(characteristic_length(*bodies))))"
        new = "return float(Fraction(ROUNDING_C) * Fraction(_EPS) *\n            max(Fraction(coordinate_magnitude(*bodies)), Fraction(characteristic_length(*bodies))))"
    assert source.count(old) == 1
    scope = dict(vars(margin))
    exec(compile(source.replace(old,new),f"<r13fixb-subnormal-{name}>","exec"),scope)
    # The imported callable identity is part of _candidates' cache key.
    monkeypatch.setattr(interlock,name,scope[name])
    with pytest.raises(AssertionError,match=message):
        test_subnormal_escape_keeps_internal_thresholds_exact_and_public_reports_strict(monkeypatch)
