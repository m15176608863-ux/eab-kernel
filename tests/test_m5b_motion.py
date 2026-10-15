"""P2 independent geometry/algebra gates and explicit consistency checks.

Primary oracle imports: fractions.Fraction; tests/m5b_independent_oracle
(independent complex products, Lagrange/Sturm, g0_oracle solid membership).
The Taylor oracle below uses integer factorials rather than production
alternating recurrence. Production algebraic/SE2/M4c imports are systems under
test or labelled degeneration consistency checks, never primary oracles.
"""
from fractions import Fraction as F
from math import factorial
from random import Random

import pytest
from mutation_support import mutated_function

from eab.kernel2d import dda_motion as module
from eab.kernel2d.algebraic import RealAlgebraic, roots_interval
from eab.kernel2d.dda_motion import (
    DDAAnchoredMotion, HalfAngleApproximation, area_centroid, dda_first_entrance, dda_motion_from_z,
    p2_p3_bound, projected_sweep, rational_half_angle,
)
from eab.kernel2d.motion import motion_first_entrance
from eab.kernel2d.se2 import SE2Motion, se2_first_entrance
from m5a_independent_oracle import multiply
from m5b_independent_oracle import (
    certificate_root, compare, event_polynomials, first_contact, point_at, value,
)


TRIANGLE = ((-3, 0), (-2, 0), (-F(11, 4), 1))
SQUARE = ((0, 0), (2, 0), (2, 2), (0, 2))
STRAIN_A = ((F(1, 30), F(-1, 50)), (F(-1, 50), F(-1, 40)))
STRAIN_B = ((F(-1, 25), F(1, 60)), (F(1, 60), F(1, 35)))


def specs(index=0):
    ma = (F(1, 2), (F(4), F(1, 7)), (-F(5, 2), F(1, 3)), STRAIN_A)
    mb = (F(-1, 3), (F(1, 5), F(-1, 7)), (F(1), F(1)), STRAIN_B)
    if index == 1:
        ma = (F(-1, 3), (F(5), F(1, 4)), (-F(5, 2), F(1, 3)), STRAIN_B)
        mb = (F(1, 4), (F(-1, 5), F(1, 9)), (F(1), F(1)), STRAIN_A)
    return ma, mb


def oracle_trig(x, count=32):
    """Taylor remainder |R_n| <= |x|^(n+1)/(n+1)!, independent of recurrence."""
    sine = sum(F((-1)**k, factorial(2*k+1))*x**(2*k+1) for k in range(count))
    cosine = sum(F((-1)**k, factorial(2*k))*x**(2*k) for k in range(count))
    es = abs(x)**(2*count+1)/factorial(2*count+1)
    ec = abs(x)**(2*count)/factorial(2*count)
    return (sine-es, sine+es), (cosine-ec, cosine+ec)


def test_area_centroid_is_area_weighted_and_frame_covariant():
    # Two exact rectangular laminae: area 4 at (2,1/2), area 2 at (1/2,2).
    ring = ((0, 0), (4, 0), (4, 1), (1, 1), (1, 3), (0, 3))
    expected = F(3, 2), F(1)
    assert area_centroid(ring) == area_centroid(tuple(reversed(ring))) == expected
    assert expected != tuple(sum(p[k] for p in ring)/len(ring) for k in (0, 1))
    results = []
    for scale, shift in ((F(1, 10**6), (10**6, -10**5)), (F(1), (0, 0)), (F(10**6), (10**3, -10**3))):
        def point(p):
            return (shift[0]+scale*(3*p[0]-4*p[1])/5,
                    shift[1]+scale*(4*p[0]+3*p[1])/5)
        transformed = tuple(point(p) for p in ring)
        assert area_centroid(transformed) == point(expected), "independent lamina center covariance"
        results.append(transformed)
    assert len(set(results)) == 3


@pytest.mark.parametrize("theta", (F(-1), F(-1, 200), F(0), F(1, 200), F(1)))
def test_half_angle_has_independent_taylor_enclosure_and_zero_exactness(theta):
    result = rational_half_angle(theta, bits=80)
    (sl, su), (cl, cu) = oracle_trig(theta)
    candidates = tuple(s/(1+c) for s in (sl, su) for c in (cl, cu))
    assert result.u1-result.error <= min(candidates) <= max(candidates) <= result.u1+result.error
    assert result.error <= F(1, 2**80), "certified dyadic approximation remains below one grid unit"
    if theta == 0:
        assert result.u1 == result.lower == result.upper == result.error == 0


def test_dda_z_mapping_uses_area_centroid_and_engineering_shear():
    ring = ((0, 0), (4, 0), (4, 1), (1, 1), (1, 3), (0, 3))
    z = (F(1, 9), F(-1, 7), F(1, 200), F(1, 100), F(-1, 200), F(1, 300))
    motion = dda_motion_from_z(ring, z)
    assert motion.center == (F(3, 2), F(1))
    assert motion.translation == z[:2]
    assert motion.strain == ((z[3], z[5]/2), (z[5]/2, z[4]))
    assert motion.u1 == rational_half_angle(z[2]).u1


def test_half_angle_record_rejects_inexact_fields_without_claiming_factory_provenance():
    for index in range(4):
        for bad in (True, 0.0, "0"):
            fields = [F(0), F(0), F(0), F(0)]
            fields[index] = bad
            with pytest.raises(ValueError, match="exact"):
                HalfAngleApproximation(*fields)
    with pytest.raises(ValueError, match="fields"):
        HalfAngleApproximation(0, 0, 1, -1)
    # A plain record does not verify transcendental provenance. Only the
    # rational_half_angle factory establishes the true tan enclosure.
    record = HalfAngleApproximation(1, 0, 0, 0)
    assert record.error == 0 and record != rational_half_angle(1)


def test_p2_coordinates_match_independent_complex_product_oracle():
    spec, _ = specs()
    motion = DDAAnchoredMotion(*spec)
    outcomes = []
    for s in (F(0), F(2, 7), F(1, 2), F(1)):
        got = tuple(motion.at(p, s) for p in TRIANGLE)
        assert got == tuple(point_at(p, spec, s) for p in TRIANGLE), "P2 independent complex-product coordinates"
        outcomes.append(got)
    assert len(set(outcomes)) == 4


def test_coordinate_polynomial_identity():
    for spec in specs():
        motion = DDAAnchoredMotion(*spec)
        for point in TRIANGLE:
            numerators, denominator = motion.coordinate_polynomials(point)
            assert len(denominator) <= 3 and max(map(len, numerators)) <= 4
            for s in (F(0), F(3, 11), F(1)):
                assert value(denominator, s) > 0
                got = tuple(value(n, s)/value(denominator, s) for n in numerators)
                assert got == point_at(point, spec, s), "coordinate polynomial denominator identity"


@pytest.mark.parametrize("theta", (F(-1), F(-1, 1000), F(0), F(1, 200), F(1)))
def test_p2_p3_uniform_bound_contains_independent_interval_trigonometry(theta):
    motion = DDAAnchoredMotion(rational_half_angle(theta, bits=24).u1,
                               (F(1, 7), -F(2, 9)), (F(5), -F(3)), STRAIN_A)
    bound = p2_p3_bound(TRIANGLE, motion, theta)
    assert bound["position"] == bound["radius_l1"]*(bound["time_law_angle"]+bound["parameter_angle"])
    for s in (F(0), F(1, 7), F(1, 2), F(4, 5), F(1)):
        (sl, su), (cl, cu) = oracle_trig(s*theta)
        for p in TRIANGLE:
            local = tuple(p[k]-motion.center[k] for k in (0, 1))
            x, y = local
            for k in (0, 1):
                offset = motion.center[k]+s*(motion.translation[k]+sum(motion.strain[k][j]*local[j] for j in (0, 1)))
                corners = tuple(offset+(c*x-t*y if k == 0 else t*x+c*y)
                                for c in (cl, cu) for t in (sl, su))
                got = motion.at(p, s)[k]
                assert max(abs(v-got) for v in corners) <= bound["position"], "rigorous P3 interval lies inside uniform P2 bound"
    if theta == 0:
        assert bound["position"] == 0


def test_zero_angle_is_p1_and_zero_strain_is_same_center_se2():
    zero = DDAAnchoredMotion(0, (3, F(1, 7)), (-F(5, 2), F(1, 3)), STRAIN_A)
    rigid = DDAAnchoredMotion(F(1, 2), zero.translation, zero.center)
    se2 = SE2Motion(rigid.u1, rigid.translation, rigid.center)
    for s in (F(0), F(1, 5), F(7, 9), F(1)):
        for p in TRIANGLE:
            assert zero.at(p, s) == tuple((1-s)*p[k]+s*zero.endpoint(p)[k] for k in (0, 1)), "P2 theta-zero exact endpoint chord"
            assert rigid.at(p, s) == se2.at(p, s), "P2 zero-strain SE2 exact coordinate degeneration"
    chord = motion_first_entrance(TRIANGLE, SQUARE, tuple(zero.endpoint(p) for p in TRIANGLE), SQUARE)
    actual = dda_first_entrance(TRIANGLE, SQUARE, zero)
    rigid_result = dda_first_entrance(TRIANGLE, SQUARE, rigid)
    reference = se2_first_entrance(TRIANGLE, SQUARE, se2)
    for a, b in ((actual, chord), (rigid_result, reference)):
        assert (a.initial_state, a.status, a.exact_time, a.incidences, a.features) == (
            b.initial_state, b.status, b.exact_time, b.incidences, b.features), "all exact degeneration result fields"


def test_sixth_degree_events_match_independent_seven_sample_oracle():
    ma, mb = specs()
    a = module._validated_ring(TRIANGLE, DDAAnchoredMotion(*ma))
    b = module._validated_ring(SQUARE, DDAAnchoredMotion(*mb))
    degrees = set()
    for i in range(len(TRIANGLE)):
        for j in range(len(SQUARE)):
            got = module._line_polynomials(a, i, b, j)
            reference = event_polynomials(TRIANGLE[i], SQUARE[j], SQUARE[(j+1) % len(SQUARE)], ma, mb)
            assert got == reference, "independent seven-sample event coefficient oracle"
            degrees.update(len(poly)-1 for poly in got)
    assert max(degrees) == 6, "fixture genuinely exercises degree six, not merely a relaxed bound"


@pytest.mark.parametrize("index", (0, 1))
def test_complete_first_contact_matches_independent_oracle(index):
    ma, mb = specs(index)
    expected = first_contact(TRIANGLE, SQUARE, ma, mb)
    actual = dda_first_entrance(TRIANGLE, SQUARE, DDAAnchoredMotion(*ma), DDAAnchoredMotion(*mb))
    assert (actual.initial_state, actual.status) == (expected["initial"], expected["status"])
    assert set(actual.incidences) == expected["incidences"], "independent complete P2 incidence set"
    assert set(actual.features) == expected["features"], "independent complete P2 cover set"
    assert compare(certificate_root(actual.exact_time.certificate), expected["root"]) == 0, "independent P2 exact first-root identity"
    assert expected["probes"] and expected["max_degree"] == 6


def test_sixth_degree_root_isolation_has_independent_factor_and_bisection_oracles():
    root, = roots_interval((-1, 0, 0, 0, 0, 0, 2))
    lower, upper = F(0), F(1)
    for _ in range(100):
        mid = (lower+upper)/2
        if mid**6 < F(1, 2):
            lower = mid
        else:
            upper = mid
    assert lower < root < upper, "independent sixth-power bisection oracle"
    assert root.sign_polynomial(-1, 0, 0, 0, 0, 0, 2) == 0
    polynomial = (F(1),)
    for r in (F(0), F(1, 7), F(1, 7), F(1, 2), F(3, 4), F(1)):
        polynomial = multiply(polynomial, (-r, 1))
    assert roots_interval(polynomial) == (F(0), F(1, 7), F(1, 2), F(3, 4), F(1))
    with pytest.raises(ValueError, match="six"):
        roots_interval((-1, 0, 0, 0, 0, 0, 0, 2))
    with pytest.raises(ValueError, match="six"):
        RealAlgebraic((-1, 0, 0, 0, 0, 0, 0, 2), 0, 1)
    with pytest.raises(ValueError, match="isolate"):
        RealAlgebraic(polynomial, 0, 1)


def test_sixth_degree_six_irrational_branches_have_exact_independent_brackets():
    # Each 1-k*x+k*x*x has exactly two roots symmetric about 1/2.
    # Direct integer evaluation fixes disjoint brackets for all six roots;
    # no production root solver computes the expected roots or brackets.
    polynomial = multiply(multiply((1, -100, 100), (1, -10, 10)), (1, -5, 5))
    branches = roots_interval(polynomial)
    brackets = ((F(0), F(1, 50), 100), (F(1, 10), F(1, 8), 10),
                (F(1, 4), F(3, 10), 5), (F(7, 10), F(3, 4), 5),
                (F(7, 8), F(9, 10), 10), (F(49, 50), F(1), 100))
    assert len(branches) == 6, "six distinct irrational degree-six branches"
    for root, (lo, hi, k) in zip(branches, brackets):
        assert (1-k*lo+k*lo*lo)*(1-k*hi+k*hi*hi) < 0
        assert lo < root < hi, "independent quadratic sign bracket for selected branch"
        assert root.sign_polynomial(1, -k, k) == 0


def test_p2_first_entrance_covaries_under_random_rotations_units_and_large_translations():
    ma, mb = specs()
    base = dda_first_entrance(TRIANGLE, SQUARE, DDAAnchoredMotion(*ma), DDAAnchoredMotion(*mb))
    rng, products = Random(20261015), []
    for scale, shift in ((F(1, 10**6), (10**6, -10**5)), (F(1), (0, 0)), (F(10**6), (10**3, -10**5))):
        u = F(rng.randrange(1, 10), 13)
        co, si = (1-u*u)/(1+u*u), 2*u/(1+u*u)
        rotation = ((co, -si), (si, co))
        def vector(p):
            return tuple(scale*sum(rotation[i][j]*p[j] for j in (0, 1)) for i in (0, 1))
        def point(p):
            v = vector(p)
            return tuple(v[k]+shift[k] for k in (0, 1))
        def transform(spec):
            u1, d, c, e = spec
            strain = tuple(tuple(sum(rotation[i][k]*e[k][l]*rotation[j][l] for k in (0, 1) for l in (0, 1))
                                 for j in (0, 1)) for i in (0, 1))
            return DDAAnchoredMotion(u1, vector(d), point(c), strain)
        a, b = tuple(map(point, TRIANGLE)), tuple(map(point, SQUARE))
        actual = dda_first_entrance(a, b, transform(ma), transform(mb))
        assert (actual.status, actual.exact_time, actual.incidences, actual.features) == (
            base.status, base.exact_time, base.incidences, base.features), "random rigid-frame and unit P2 covariance"
        products.append(a)
    assert len(set(products)) == 3


def test_projected_sweep_contains_all_independent_rational_probes():
    ma, _ = specs()
    motion = DDAAnchoredMotion(*ma)
    for direction in ((1, 0), (0, 1), (2, -3), (-1, 7)):
        lower, upper = projected_sweep(TRIANGLE, motion, direction)
        for i in range(13):
            for p in TRIANGLE:
                q = point_at(p, ma, F(i, 12))
                assert lower <= sum(direction[k]*q[k] for k in (0, 1)) <= upper


def test_p2_initial_states_persistent_collinearity_and_closed_endpoint():
    unit = ((0, 0), (1, 0), (1, 1), (0, 1))
    for delta, translation in (((0, 0), (0, 0)), ((1, 1), (0, 0)), ((2, 1), (-1, 0)), ((3, 0), (0, 0))):
        b = tuple((x+delta[0], y+delta[1]) for x, y in unit)
        actual = dda_first_entrance(unit, b, motion_b=DDAAnchoredMotion(0, translation))
        expected = motion_first_entrance(unit, b, unit, tuple((x+translation[0], y+translation[1]) for x, y in b))
        assert (actual.initial_state, actual.status, actual.exact_time, actual.features) == (
            expected.initial_state, expected.status, expected.exact_time, expected.features)
        if actual.initial_state == 1:
            assert actual.pd_closed == se2_first_entrance(unit, b).pd_closed


def test_unsupported_p2_domains_fail_loudly_before_event_enumeration():
    for bad in (True, 0.0, "0"):
        with pytest.raises(ValueError):
            DDAAnchoredMotion(bad)
    with pytest.raises(ValueError, match="symmetric"):
        DDAAnchoredMotion(strain=((0, 1), (0, 0)))
    with pytest.raises(ValueError, match="unsupported"):
        dda_first_entrance(TRIANGLE, SQUARE, DDAAnchoredMotion(strain=((F(1, 2), 0), (0, 0))))
    with pytest.raises(ValueError, match="theta"):
        rational_half_angle(F(11, 10))
    with pytest.raises(ValueError, match="window"):
        DDAAnchoredMotion().at((0, 0), 2)


def test_losing_the_sixth_event_term_is_killed_by_the_first_root_semantic_assertion(monkeypatch):
    ma, mb = specs()
    expected = first_contact(TRIANGLE, SQUARE, ma, mb)
    changed = mutated_function(module._line_polynomials, module, [
        ("return f, g, h", "return (f[:-1] if len(f) == 7 else f), g, h"),
    ])
    monkeypatch.setattr(module, "_line_polynomials", changed)
    actual = dda_first_entrance(TRIANGLE, SQUARE, DDAAnchoredMotion(*ma), DDAAnchoredMotion(*mb))
    assert actual.status == "contact", "real event path received the sixth-term mutation"
    with pytest.raises(AssertionError, match="sixth-term semantic"):
        assert compare(certificate_root(actual.exact_time.certificate), expected["root"]) == 0, "sixth-term semantic first-root identity"


def test_shear_mutation_is_killed_by_coordinate_semantics(monkeypatch):
    ma, _ = specs()
    changed = mutated_function(module._apply, module, [
        ("matrix[i][j]*point[j]", "(2 if i != j else 1)*matrix[i][j]*point[j]"),
    ])
    monkeypatch.setattr(module, "_apply", changed)
    with pytest.raises(AssertionError, match="shear semantic"):
        assert DDAAnchoredMotion(*ma).at(TRIANGLE[0], F(1, 3)) == point_at(TRIANGLE[0], ma, F(1, 3)), "shear semantic coordinate identity"


def test_area_centroid_mutation_is_killed_by_independent_lamina_moments(monkeypatch):
    changed = mutated_function(module.area_centroid, module, [
        ("points = _ring(tuple(_point(p) for p in ring))",
         "points = _ring(tuple(_point(p) for p in ring))\n    return tuple(sum(p[k] for p in points)/len(points) for k in (0, 1))"),
    ])
    monkeypatch.setattr(module, "area_centroid", changed)
    ring = ((0, 0), (4, 0), (4, 1), (1, 1), (1, 3), (0, 3))
    with pytest.raises(AssertionError, match="area-lamina semantic"):
        assert module.area_centroid(ring) == (F(3, 2), F(1)), "area-lamina semantic centroid identity"


def test_missing_time_law_bound_is_killed_by_independent_p3_interval(monkeypatch):
    changed = mutated_function(module.p2_p3_bound, module, [
        ("time_law, parameter = abs(motion.u1)**3/2, 2*error", "time_law, parameter = F(0), 2*error"),
    ])
    monkeypatch.setattr(module, "p2_p3_bound", changed)
    motion = dda_motion_from_z(TRIANGLE, (0, 0, 1, 0, 0, 0))
    bound = module.p2_p3_bound(TRIANGLE, motion, F(1))
    (sl, su), (cl, cu) = oracle_trig(F(1, 2))
    x, y = tuple(TRIANGLE[0][k]-motion.center[k] for k in (0, 1))
    possible = tuple(motion.center[0]+c*x-s*y for c in (cl, cu) for s in (sl, su))
    coordinate = motion.at(TRIANGLE[0], F(1, 2))[0]
    with pytest.raises(AssertionError, match="time-law semantic"):
        assert max(abs(v-coordinate) for v in possible) <= bound["position"], "time-law semantic all-time deviation bound"


def test_concave_p2_first_contact_has_independent_complete_cover_oracle():
    a = ((-3, 0), (-F(3, 2), 0), (-F(3, 2), F(1, 2)),
         (-F(5, 2), F(1, 2)), (-F(5, 2), F(3, 2)), (-3, F(3, 2)))
    ma, mb = specs(1)
    reference = first_contact(a, SQUARE, ma, mb)
    actual = dda_first_entrance(a, SQUARE, DDAAnchoredMotion(*ma), DDAAnchoredMotion(*mb))
    assert actual.status == reference["status"] == "contact"
    assert set(actual.incidences) == reference["incidences"]
    assert set(actual.features) == reference["features"]
    assert compare(certificate_root(actual.exact_time.certificate), reference["root"]) == 0
    assert reference["probes"] and reference["max_degree"] == 6
