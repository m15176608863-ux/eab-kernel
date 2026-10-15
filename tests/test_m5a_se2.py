"""SE(2) semantic, degeneration, construction and covariance gates.

Primary oracle imports: fractions.Fraction, math.nextafter/inf, and
eab.kernel2d.g0_oracle (integer winding/intersections; its own construction).
Closed-form event equations and rational rotation coordinates below are
written independently of se2/algebraic production primitives. M3/M4c are
explicit consistency checks, not the independent oracle. FAMILIES contains
only the six established M3 shape/translation fixtures; E_hole is a hole in
configuration space, not a claim to support material multi-ring inputs.
"""
from fractions import Fraction as F
from math import inf, nextafter
from random import Random

import pytest

from eab.kernel2d import g0_oracle as oracle
from eab.kernel2d import se2 as module
from eab.kernel2d.global_entrance import GlobalEntrance2
from eab.kernel2d.motion import motion_first_entrance
from eab.kernel2d.se2 import SE2Motion, rotate_rational, se2_first_entrance, se2_slice
from test_m4c_motion import FAMILIES, PIN, SQ, TIERS, U, moved, scaled, _m3_unit_reference


def square_wall(u=F(1, 2)):
    return (((-1, -1), (1, -1), (1, 1), (-1, 1)),
            ((F(6, 5), -3), (3, -3), (3, 3), (F(6, 5), 3)), SE2Motion(u))


def independent_at(poly, motion, s):
    """Direct component formula, not production rotate/trajectory helpers."""
    u, c, d = s*motion.u1, motion.center, motion.translation
    cosine, sine = (1-u*u)/(1+u*u), 2*u/(1+u*u)
    return tuple((c[0]+s*d[0]+cosine*(x-c[0])-sine*(y-c[1]),
                  c[1]+s*d[1]+sine*(x-c[0])+cosine*(y-c[1])) for x, y in poly)


@pytest.mark.parametrize("scale", TIERS)
def test_rotation_is_rigid_and_endpoints_close(scale):
    c, d = (5*scale, -3*scale), (F(2, 7)*scale, -F(1, 5)*scale)
    points = scaled(((7, -4), (4, -2), (5, -3)), scale)
    motion = SE2Motion(F(1, 2), d, c)
    assert tuple(motion.at(p, 0) for p in points) == points, "trajectory initial endpoint"
    # u=1/2 is the exact 3-4-5 rotation, independently expanded.
    expected = tuple((c[0]+d[0]+F(3, 5)*(x-c[0])-F(4, 5)*(y-c[1]),
                      c[1]+d[1]+F(4, 5)*(x-c[0])+F(3, 5)*(y-c[1])) for x, y in points)
    assert tuple(motion.endpoint(p) for p in points) == expected, "trajectory final endpoint closure"
    outcomes = []
    for s in (F(0), F(1, 3), F(2, 3), F(1)):
        transformed = tuple(motion.at(p, s) for p in points)
        assert transformed == independent_at(points, motion, s), "exact trajectory coordinate construction"
        outcomes.append(transformed)
        for i in range(len(points)):
            for j in range(len(points)):
                assert sum((transformed[i][k]-transformed[j][k])**2 for k in (0, 1)) == sum(
                    (points[i][k]-points[j][k])**2 for k in (0, 1)), "rigid squared distances"
    assert len(set(outcomes)) == 4, "parameter products must be distinct"
    assert rotate_rational((2*scale, 3*scale), 1) == (-3*scale, 2*scale)
    assert rotate_rational((2*scale, 3*scale), -1) == (3*scale, -2*scale)


@pytest.mark.parametrize("scale", TIERS)
def test_fixed_slice_is_m3(scale):
    A = scaled(((0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2)), scale)
    B = scaled(((3, -2), (5, -2), (5, 3), (3, 3)), scale)
    transformed = tuple((F(3, 5)*x-F(4, 5)*y, F(4, 5)*x+F(3, 5)*y) for x, y in A)
    model = se2_slice(A, B, F(1, 2))
    reference = GlobalEntrance2(transformed, B)
    assert model.A == reference.A == transformed, "fixed slice exact rotated coordinates"
    assert model.cells == reference.cells, "fixed slice reuses M3 global construction"
    states = set()
    for shift in scaled(((0, 0), (3, 0), (4, 0), (5, 3), (20, 0)), scale):
        expected = oracle.overlap(moved(transformed, shift), B)
        assert model.membership(shift) == expected, "fixed slice independent solid state"
        states.add(expected)
    assert -1 in states and 1 in states


@pytest.mark.parametrize("index", range(len(FAMILIES)), ids=[row[0] for row in FAMILIES])
def test_zero_rotation_is_exactly_m3_and_m4c_all_fields(index):
    _, A, B, origin, direction = FAMILIES[index]
    expected_time, expected_labels = _m3_unit_reference(index)
    constructed = []
    for scale in TIERS:
        a, b = scaled(moved(A, origin), scale), scaled(B, scale)
        common = (scale/F(7), -2*scale/F(5))
        da = tuple(scale*direction[k]+common[k] for k in (0, 1))
        ma, mb = SE2Motion(0, da, (13*scale, -7*scale)), SE2Motion(0, common, (-3*scale, 11*scale))
        got = se2_first_entrance(a, b, ma, mb)
        chord = motion_first_entrance(a, b, moved(a, da), moved(b, common))
        ray = GlobalEntrance2(a, b).first_entrance((0, 0), tuple(scale*v for v in direction), t_max=1)
        assert (got.initial_state, got.status) == (chord.initial_state, chord.status) == (-1, "contact")
        assert got.exact_time == chord.exact_time == expected_time == ray.exact_time, "zero rotation exact time"
        assert got.time == chord.time == ray.time, "zero rotation displayed time"
        assert got.incidences == chord.incidences, "zero rotation complete incidences"
        assert got.features == chord.features == got.tied_features, "zero rotation complete ties"
        assert set(got.features) == expected_labels, "zero rotation M3 clipped covers"
        constructed.append(a)
    assert len(set(constructed)) == len(TIERS)


def _closed_form_guard():
    A, B, m = square_wall(F(1))
    got = se2_first_entrance(A, B, m)
    assert got.status == "contact" and got.initial_state == -1, "pure rotation must contact wall"
    assert got.exact_time.sign_polynomial(1, -10, 11) == 0, "square-wall exact angle equation"
    assert F(1, 10) < got.exact_time < F(1, 8), "earliest square-wall real root"
    assert got.features == got.incidences == (("VE", 1, 3),), "square-wall complete first feature"
    return got


def test_square_center_rotation_closed_form_and_two_real_roots():
    got = _closed_form_guard()
    A, B, m = square_wall(F(1))
    for s in (F(0), F(1, 10), F(1, 8), F(1, 2), F(4, 5), F(1)):
        # Maximum x is (1+2s-s²)/(1+s²); wall at 6/5.
        f = 11*s*s-10*s+1
        assert oracle.overlap(independent_at(A, m, s), B) == (-1 if f > 0 else 1)
    lo = (F(nextafter(got.time, -inf))+F(got.time))/2
    hi = (F(nextafter(got.time, inf))+F(got.time))/2
    assert 11*lo*lo-10*lo+1 > 0 > 11*hi*hi-10*hi+1, "independent algebraic rounding cell"


@pytest.mark.parametrize("scale", TIERS)
def test_pivot_rotation_has_independent_lever_closed_form(scale):
    A = scaled(((0, 0), (2, 0), (0, F(1, 4))), scale)
    B = scaled(((-1, 1), (3, 1), (3, 2), (-1, 2)), scale)
    m = SE2Motion(F(1, 2))
    got = se2_first_entrance(A, B, m)
    assert got.exact_time.sign_polynomial(4, -8, 1) == 0, "lever exact angle equation"
    assert F(1, 2) < got.exact_time < F(3, 5), "lever first angle branch"
    assert got.incidences == got.features == (("VE", 1, 0),)
    for s, state in ((F(0), -1), (F(1, 2), -1), (F(3, 5), 1), (F(1), 1)):
        assert oracle.overlap(independent_at(A, m, s), B) == state
    assert m.at(A[0], F(7, 9)) == A[0], "pivot stays fixed"


def test_initial_states_zero_motion_and_persistent_collinearity_equal_m4c():
    for A, B, da, db in (
        (SQ, SQ, (1, 2), (-1, 3)),
        (SQ, moved(SQ, (1, 1)), (0, 0), (0, 0)),
        (PIN, U, (0, 0), (0, 0)),
        (SQ, moved(SQ, (3, 0)), (0, 0), (0, 0)),
        (SQ, moved(SQ, (3, 1)), (0, 0), (-3, 0)),
        (SQ, moved(SQ, (3, -1)), (0, 0), (-4, 4)),
    ):
        got = se2_first_entrance(A, B, SE2Motion(0, da), SE2Motion(0, db))
        old = motion_first_entrance(A, B, moved(A, da), moved(B, db))
        assert (got.initial_state, got.status, got.exact_time, got.incidences, got.features) == (
            old.initial_state, old.status, old.exact_time, old.incidences, old.features), "all initial/degenerate fields"


def test_initial_pd_is_frozen():
    A, B = moved(SQ, (F(1, 4), F(1, 3))), SQ
    result = se2_first_entrance(A, B, SE2Motion(F(1, 2), (3, 1), (5, -3)))
    reference = GlobalEntrance2(A, B).shortest_exit((0, 0))
    assert result.status == "initial_overlap" and result.exact_time is None
    assert result.pd_closed == reference, "PD_closed is frozen at initial geometry, not a motion exit"
    assert result.pd_closed.squared == F(4, 9)
    assert result.pd_closed.tied_exact_points == ((F(0), F(2, 3)),)
    assert se2_first_entrance(SQ, moved(SQ, (1, 1))).pd_closed is None


def test_rotating_closed_endpoint_is_not_lost():
    A = ((0, 0), (2, 0), (0, F(1, 4)))
    B = ((-1, F(8, 5)), (3, F(8, 5)), (3, 3), (-1, 3))
    result = se2_first_entrance(A, B, SE2Motion(F(1, 2)))
    assert result.status == "contact" and result.exact_time == 1, "rotating closed-window endpoint"
    assert result.features == result.incidences == (("VE", 1, 0),)
    assert oracle.overlap(independent_at(A, SE2Motion(F(1, 2)), F(999, 1000)), B) == -1


def test_two_rotating_translating_bodies_transform_with_their_reference_points():
    # Shared shape parameters, but no shared oracle primitive; this is the
    # API's frame/unit meta-gate, not its independent correctness oracle.
    from test_m5a_oracle import CASES
    A, B, ma, mb = CASES[0]
    original = se2_first_entrance(A, B, SE2Motion(*ma), SE2Motion(*mb))
    assert original.status == "contact"
    for scale in (F(1, 10**9), F(1), F(10**8)):
        for c, s, t in ((F(0), F(1), 10**5), (F(3, 5), F(4, 5), 10**6)):
            def vector(v):
                return scale*(c*v[0]-s*v[1]), scale*(s*v[0]+c*v[1])
            def point(p):
                x, y = vector(p)
                return x+t, y-7*t
            def motion(m):
                return SE2Motion(m[0], vector(m[1]), point(m[2]))
            result = se2_first_entrance(tuple(map(point, A)), tuple(map(point, B)), motion(ma), motion(mb))
            assert result.initial_state == original.initial_state and result.status == original.status
            assert result.exact_time == original.exact_time, "two-body degree-five time covariance"
            assert set(result.features) == set(original.features), "two-body complete cover covariance"
            assert set(result.incidences) == set(original.incidences)


@pytest.mark.parametrize("scale", (F(1, 10**9), F(1), F(10**8)))
@pytest.mark.parametrize("shift", (0, 10**3, 10**5, 10**6))
def test_se2_is_rigid_frame_and_unit_covariant(scale, shift):
    A, B, motion = square_wall()
    reference = se2_first_entrance(A, B, motion)
    u = F(Random(20261015).randrange(1, 19), 23)
    random_frame = ((1-u*u)/(1+u*u), 2*u/(1+u*u))
    frames = ((F(1), F(0)), (F(0), F(1)), (F(-1), F(0)), (F(0), F(-1)), (F(3, 5), F(4, 5)), random_frame)
    assert len(set(frames)) == 6, "fixed-seed frame must add a distinct rotation"
    for c, s in frames:
        def transform(poly):
            return tuple((scale*(c*x-s*y)+shift, scale*(s*x+c*y)-3*shift) for x, y in poly)
        center = transform(((0, 0),))[0]
        got = se2_first_entrance(transform(A), transform(B), SE2Motion(motion.u1, (0, 0), center),
                                 SE2Motion(0, (0, 0), center))
        assert got.exact_time == reference.exact_time, "SE(2) exact frame/unit time covariance"
        assert got.time == reference.time
        assert set(got.features) == set(reference.features), "SE(2) set-valued cover covariance"
        assert set(got.incidences) == set(reference.incidences)
        # Touching multi-feature sets test the set-valued, not lex representative, contract.
        tied = se2_first_entrance(transform(SQ), transform(moved(SQ, (1, 1))),
                                  SE2Motion(F(1, 2), (0, 0), center), SE2Motion(F(-1, 3), (0, 0), center))
        original = se2_first_entrance(SQ, moved(SQ, (1, 1)), SE2Motion(F(1, 2)), SE2Motion(F(-1, 3)))
        assert tied.exact_time == original.exact_time == 0
        assert len(tied.features) >= 3 and set(tied.features) == set(original.features)
        assert set(tied.incidences) == set(original.incidences)


def test_clockwise_feature_identity_and_unsupported_domains_are_explicit():
    A, B, m = square_wall()
    result = se2_first_entrance(A[::-1], B[::-1], m)
    assert result.features == (("VE", 2, 3),), "clockwise original edge and vertex identities"
    for u in (F(1000000), F(-1000000), F(1001, 1000), True, 0.5, "1/2"):
        with pytest.raises(ValueError):
            SE2Motion(u)
    for bad in ((SQ, SQ), ((0, 0), (1, 1), (0, 1), (1, 0)),
                ((0, 0), (1, 0), (1, 0), (0, 1)), ((0, 0), (1, 0), (2, 0))):
        with pytest.raises(ValueError):
            se2_first_entrance(bad, moved(SQ, (100, 100)), m)
    with pytest.raises(ValueError):
        m.at((1, 0), F(11, 10))


def test_translation_semantic_guard():
    A, B = moved(SQ, (-3, F(1, 3))), SQ
    got = se2_first_entrance(A, B, SE2Motion(0, (4, 0)))
    expected = motion_first_entrance(A, B, moved(A, (4, 0)), B)
    assert got.status == expected.status == "contact", "general path must retain translation events"
    assert got.exact_time == expected.exact_time == F(1, 2), "general path exact translation time"
    assert got.incidences == expected.incidences and got.features == expected.features


@pytest.mark.parametrize("mutation", ("wrong_real_root", "rotation_sign", "translation_bypass", "endpoint_not_closed"))
def test_internal_se2_mutations_hit_intended_semantic_assertions(monkeypatch, mutation):
    if mutation == "wrong_real_root":
        _closed_form_guard()
        old = module.roots_interval
        monkeypatch.setattr(module, "roots_interval", lambda p: old(p)[-1:])
        guard, message = _closed_form_guard, "earliest square-wall real root"
    elif mutation == "rotation_sign":
        _closed_form_guard()
        old = module._rotation_numerators
        def mutant(u, p):
            x, y = old(u, p)
            return (x[0], -x[1], x[2]), y
        monkeypatch.setattr(module, "_rotation_numerators", mutant)
        guard, message = _closed_form_guard, "square-wall complete first feature"
    elif mutation == "translation_bypass":
        test_translation_semantic_guard()
        old = module.roots_interval
        monkeypatch.setattr(module, "roots_interval", lambda p: () if len(p) <= 2 else old(p))
        guard, message = test_translation_semantic_guard, "general path must retain translation events"
    else:
        test_rotation_is_rigid_and_endpoints_close(F(1))
        old = module.rotate_rational
        monkeypatch.setattr(module, "rotate_rational", lambda p, u: old(p, u/2))
        guard = lambda: test_rotation_is_rigid_and_endpoints_close(F(1))
        message = "trajectory final endpoint closure"
    module._validated_ring.cache_clear()
    with pytest.raises(AssertionError, match=message):
        guard()
    # Cached intermediate vectors must not retain the injected defect for
    # later tests after monkeypatch restores the original function.
    module._validated_ring.cache_clear()
