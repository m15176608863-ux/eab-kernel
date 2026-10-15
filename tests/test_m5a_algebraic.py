"""Independent exact algebra gates for docs/m5a_se2_design.md, T4.

Oracle imports: fractions.Fraction, math.nextafter/inf, random.Random, pytest.
The oracle uses rational monomial bisection, known factorizations and direct
integer powers only. It does NOT import the production polynomial, Sturm,
gcd, interval or construction primitives to compute an expected answer.
Production imports below are exclusively the system under test. Geometry
oracles live separately in test_m5a_se2_oracle.py.
"""
from fractions import Fraction as F
import importlib.util
import inspect
from math import inf, nextafter
from pathlib import Path
from random import Random
from textwrap import dedent

import pytest
from mutation_support import mutated_function

from eab.kernel2d import algebraic as alg
from eab.kernel2d.algebraic import RealAlgebraic, roots_interval, sign_at
from eab.numeric_domain import ConstructionDomainError


def _oracle_monomial_bracket(power, value, steps=90):
    lo, hi = F(0), F(1)
    for _ in range(steps):
        mid = (lo+hi)/2
        if mid**power == value:
            return mid, mid
        if mid**power < value:
            lo = mid
        else:
            hi = mid
    return lo, hi


def _oracle_product(factors):
    coefficients = [F(1)]
    for factor in factors:
        new = [F(0)]*(len(coefficients)+len(factor)-1)
        for i in range(len(coefficients)):
            for j in range(len(factor)):
                new[i+j] += coefficients[i]*factor[j]
        coefficients = new
    return tuple(coefficients)


@pytest.mark.parametrize("power", (2, 3, 5))
def test_root_isolation_matches_independent_rational_bisection(power):
    polynomial = (-1,)+(0,)*(power-1)+(2,)
    root, = roots_interval(polynomial)
    lower, upper = _oracle_monomial_bracket(power, F(1, 2))
    assert lower < root < upper, "independent monomial root bracket"
    refined = root
    for _ in range(50):
        refined = refined.refine()
    assert refined.lower**power < F(1, 2) < refined.upper**power, "isolating interval contains the selected root"
    assert refined.upper-refined.lower <= F(1, 2**50), "each isolation bit is effective"
    assert refined == root, "refinement preserves root identity"


def test_multiple_real_branches_are_sorted_without_taking_the_wrong_root():
    # 10*x*x-10*x+1 has two irrational roots in (0,1), one below 1/2.
    roots = roots_interval((1, -10, 10))
    assert len(roots) == 2
    assert F(0) < roots[0] < F(1, 2) < roots[1] < F(1), "selected real root branch"
    assert roots[0] < roots[1] and roots[0] != roots[1]
    assert roots_interval((1, -10, 10), F(1, 2), 1) == (roots[1],)


def test_one_isolation_bit_keeps_the_selected_root():
    root, = roots_interval((-1, 0, 2))
    lower, upper = alg._bisect_root(root.polynomial, root.lower, root.upper)
    assert lower*lower < F(1, 2) < upper*upper, "isolation bit retains the selected root"
    assert upper-lower == F(1, 2)


def test_repeated_rational_and_closed_endpoint_roots_are_retained_once():
    polynomial = _oracle_product(((0, 1), (0, 1), (-F(1, 3), 1), (-1, 1), (-1, 1)))
    roots = roots_interval(polynomial)
    assert roots == (F(0), F(1, 3), F(1)), "closed endpoints and repeated roots"
    assert roots_interval(polynomial, 0, 0) == (F(0),)
    assert roots_interval(polynomial, 1, 1) == (F(1),)
    assert roots_interval(polynomial, F(1, 2), F(1, 2)) == ()


def test_gcd_equality_means_the_same_selected_common_root_not_any_common_root():
    positive, = roots_interval((-1, 0, 2))
    extended = _oracle_product(((-1, 0, 2), (4, 1), (-F(1, 4), 1)))
    roots = roots_interval(extended)
    assert len(roots) == 2
    assert roots[1] == positive and positive == roots[1], "gcd selected common root"
    assert roots[0] != positive, "a shared factor does not make every root equal"
    negative, = roots_interval((-1, 0, 2), -1, 0)
    assert negative != positive and negative < positive
    # Repeated irrational roots remain represented after squarefree reduction.
    repeated = _oracle_product(((-1, 0, 2), (-1, 0, 2)))
    assert roots_interval(repeated) == (positive,)


def test_adjacent_algebraic_roots_do_not_become_equal_at_a_float_tolerance():
    delta = F(1, 2**90)
    first, = roots_interval((-1, 0, 2))
    second, = roots_interval((2*delta*delta-1, -4*delta, 2))
    assert first != second, "near roots are algebraically distinct"
    assert first < second and second > first, "near roots have exact strict order"
    assert first.time == second.time, "fixture intentionally shares a binary64 display"
    assert first.compare(F(1, 2)) > 0


def test_polynomial_sign_at_root_uses_exact_common_root_and_nonzero_remainder():
    root, = roots_interval((-1, 0, 2))
    assert sign_at((-1, 0, 2), root) == 0
    common = _oracle_product(((-1, 0, 2), (-4, 1)))
    assert sign_at(common, root) == 0, "exact zero from a nonminimal common factor"
    assert sign_at((0, -1), root) == -1
    assert sign_at((-F(7, 10), 1), root) == 1
    assert sign_at((-F(71, 100), 1), root) == -1
    assert root.sign_polynomial(-1, 0, 0, 0, 4) == 0
    assert sign_at((F(1, 2**300),), root) == 1
    assert sign_at((0,), root) == 0
    assert sign_at((-1, 2), F(1, 2)) == 0


def test_random_factored_polynomials_have_exact_known_root_sets():
    random = Random(531051)
    for _ in range(18):
        known = [F(random.randrange(-6, 15), 12) for _ in range(random.randrange(1, 6))]
        polynomial = _oracle_product(tuple((-r, 1) for r in known))
        expected = tuple(sorted(set(r for r in known if 0 <= r <= 1)))
        assert roots_interval(polynomial) == expected, "fixed-seed rational factor oracle"


@pytest.mark.parametrize("scale", (F(2)**-400, F(1), F(2)**397))
def test_polynomial_arithmetic_has_independent_substitution_identities(scale):
    a, b = (scale*F(2, 3), -4*scale, 3*scale), (scale*F(1, 7), 5*scale)
    product = alg.p_mul(a, b)
    quotient, remainder = alg.p_divmod(product, b)
    assert quotient == a and remainder == (0,)
    for x in (F(-5, 3), F(0), F(2, 7)):
        av, bv = scale*(F(2, 3)-4*x+3*x*x), scale*(F(1, 7)+5*x)
        assert alg.p_eval(product, x) == av*bv
        assert alg.p_eval(alg.p_add(a, b), x) == av+bv
        assert alg.p_eval(alg.p_sub(a, b), x) == av-bv
        assert alg.p_eval(alg.p_scale(a, -3), x) == -3*av
        assert alg.p_eval(alg.p_derivative(a), x) == scale*(-4+6*x)
    assert alg.p_gcd(product, b) == (F(1, 35), 1)


@pytest.mark.parametrize("scale", (F(2)**-1070, F(1), F(2)**1022))
def test_algebraic_display_is_in_its_independent_binary64_midpoint_cell(scale):
    for sign in (-1, 1):
        lower, upper = ((scale, 2*scale) if sign > 0 else (-2*scale, -scale))
        root = RealAlgebraic((-2*scale*scale, 0, 1), lower, upper)
        assert root.polynomial == (-2*scale*scale, 0, 1)
        assert root.lower == lower and root.upper == upper
        certificate = root.certificate
        assert tuple(F(x) for x in certificate["polynomial"]) == root.polynomial
        assert tuple(F(x) for x in certificate["interval"]) == (lower, upper)
        displayed = root.time
        previous, following = nextafter(displayed, -inf), nextafter(displayed, inf)
        cell_lo, cell_hi = (F(previous)+F(displayed))/2, (F(displayed)+F(following))/2
        if sign > 0:
            assert cell_lo*cell_lo < 2*scale*scale < cell_hi*cell_hi, "positive exact midpoint cell"
        else:
            assert cell_lo*cell_lo > 2*scale*scale > cell_hi*cell_hi, "negative exact midpoint cell"


def test_algebraic_display_resolves_exact_ties_underflow_and_overflow():
    quantum = F(2)**-1074
    assert RealAlgebraic.from_rational(quantum/2).time == 0
    assert RealAlgebraic.from_rational(3*quantum/2).time == nextafter(nextafter(0., inf), inf)
    assert RealAlgebraic.from_rational(-quantum/2).time == 0
    assert RealAlgebraic.from_rational(F(1)+F(1, 2**53)).time == 1
    assert RealAlgebraic.from_rational(F(1)+F(3, 2**53)).time == nextafter(nextafter(1., inf), inf)
    with pytest.raises(ConstructionDomainError):
        _ = RealAlgebraic.from_rational(F(2)**1024).time


def test_invalid_algebraic_domains_fail_loudly():
    for polynomial in ((0,), (1, 0, 0, 0, 0, 0, 0, 1)):
        with pytest.raises(ValueError):
            roots_interval(polynomial)
    assert roots_interval((3,)) == ()
    assert roots_interval((1, 0, 1)) == ()
    for polynomial, lo, hi in (((1, 0, 1), 0, 1), ((-1, 0, 2), -1, 1), ((-1, 1), 2, 1)):
        with pytest.raises(ValueError, match="isolate"):
            RealAlgebraic(polynomial, lo, hi)
    for invalid in (True, 0.5, "1/2"):
        with pytest.raises(ValueError):
            RealAlgebraic.from_rational(invalid)
    with pytest.raises(ValueError):
        roots_interval((-1, 1), 2, 1)
    with pytest.raises(ZeroDivisionError):
        alg.p_divmod((1, 2), (0,))
    root, = roots_interval((-1, 0, 2))
    assert root != "0.707" and root != inf
    with pytest.raises(TypeError):
        _ = root < inf
    with pytest.raises(TypeError):
        hash(root)


def test_certificate_is_lossless_and_numeric_equality_has_no_implicit_cast():
    root, = roots_interval((-1, 0, 2))
    certificate = root.certificate
    restored = RealAlgebraic(tuple(F(x) for x in certificate["polynomial"]),
                            *(F(x) for x in certificate["interval"]))
    assert restored == root
    rational = RealAlgebraic.from_rational(F(1, 2))
    assert rational == F(1, 2) == rational
    assert rational == 0.5 and rational <= 0.5 and rational >= 0.5
    assert rational.rational == F(1, 2)
    assert not hasattr(root, "__float__")


def test_exact_interval_rejection_is_conservative_and_preserves_endpoint_roots(monkeypatch):
    def forbidden_sturm(_):
        raise AssertionError("strict sign certificate must avoid Sturm")
    with monkeypatch.context() as context:
        context.setattr(alg, "_squarefree", forbidden_sturm)
        assert roots_interval((1, F(1, 10**100), -F(1, 10**90))) == ()
        assert roots_interval((-1, -F(1, 10**100), F(1, 10**90))) == ()
    assert roots_interval((-1, 1)) == (F(1),), "interval touching zero is not rejected"
    assert roots_interval((0, 1)) == (F(0),), "initial endpoint root remains"
    roots = roots_interval((1, -10, 10))
    assert len(roots) == 2, "uncertain Horner interval must retain interior roots"


def test_bernstein_sign_exclusion_keeps_degree_five_interior_repeated_roots(monkeypatch):
    def forbidden_sturm(_):
        raise AssertionError("Bernstein strict sign certificate must avoid Sturm")
    with monkeypatch.context() as context:
        context.setattr(alg, "_squarefree", forbidden_sturm)
        # Horner spans zero, but (x-1/2)^2+1/2 is strictly positive.
        assert roots_interval((F(3, 4), -1, 1)) == ()
        assert roots_interval((-F(3, 4), 1, -1)) == ()
    repeated = _oracle_product(((-F(1, 2), 1), (-F(1, 2), 1), (1, 1), (1, 1), (1, 1)))
    assert roots_interval(repeated) == (F(1, 2),), "Bernstein must retain isolated tangencies"
    assert roots_interval(repeated, F(-1), F(1)) == (F(-1), F(1, 2)), "arbitrary interval endpoints retained"


def test_sign_interval_certificate_avoids_polynomial_division(monkeypatch):
    root, = roots_interval((-1, 0, 2))
    def forbidden_division(*_):
        raise AssertionError("strict interval sign needs no polynomial remainder")
    monkeypatch.setattr(alg, "p_divmod", forbidden_division)
    assert sign_at((2, F(1, 100), -F(1, 1000)), root) == 1
    assert sign_at((-2, -F(1, 100), F(1, 1000)), root) == -1


@pytest.mark.parametrize("name", ("isolation_bit", "wrong_real_root", "approximate_equality"))
def test_semantic_algebra_mutants_fail_the_intended_value_assertion(monkeypatch, name):
    """Inject defects INSIDE the SUT, without any file/hash oracles.

    inspect/textwrap are mutation instrumentation, not numerical oracles.
    Each unchanged regression below must fail its specific semantic assertion.
    """
    if name == "isolation_bit":
        original = alg._bisect_root
        old, new = "return middle, upper", "return lower, middle"
        regression = test_one_isolation_bit_keeps_the_selected_root
        message = "isolation bit retains the selected root"
    elif name == "wrong_real_root":
        original = alg.roots_interval
        old, new = "return tuple(sorted(roots))", "return tuple(reversed(sorted(roots)))"
        regression = test_multiple_real_branches_are_sorted_without_taking_the_wrong_root
        message = "selected real root branch"
    else:
        original = RealAlgebraic.__eq__
        old, new = "return self.compare(other) == 0", "return abs(self.time-other.time) <= 1e-12"
        regression = test_adjacent_algebraic_roots_do_not_become_equal_at_a_float_tolerance
        message = "near roots are algebraically distinct"
    changed = mutated_function(original, alg, [(old, new)])
    if name == "approximate_equality":
        monkeypatch.setattr(RealAlgebraic, "__eq__", changed)
    else:
        monkeypatch.setattr(alg, original.__name__, changed)
        if name == "wrong_real_root":
            monkeypatch.setitem(globals(), "roots_interval", changed)
    with pytest.raises(AssertionError, match=message):
        regression()


def test_algebraic_display_boundary_retains_rounded_provenance_in_static_gate():
    """Admitting a final display must not admit a rounded intermediate root."""
    path = Path(__file__).resolve().parents[1]/"tools/check_exact_construction.py"
    specification = importlib.util.spec_from_file_location("m5a_static_gate", path)
    gate = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(gate)
    for source, rule in (("return sqrt_rational(scalar_algebraic(compare))", "rounded-root"),
                         ("return norm_rational((scalar_algebraic(compare),))", "rounded-vector"),
                         ("x = scalar_algebraic(compare)\n    return sqrt_rational(x*x)", "rounded-root")):
        issues = gate.scan_text("def bad(compare):\n    "+source+"\n")
        assert any(row[3] == rule for row in issues), "new construction keeps intermediate rounding visible"
    forged = "def scalar_algebraic(q):\n    return q*1.0\ndef bad(q):\n    return sqrt_rational(scalar_algebraic(q))\n"
    issues = gate.scan_text(forged)
    assert any("rounded" in row[3] for row in issues), "new intrinsic spelling cannot launder a shadowing helper"
