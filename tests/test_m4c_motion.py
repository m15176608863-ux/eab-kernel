"""M4c exact trajectory gates, with an independent closed-form primary oracle.

Oracle import list: fractions.Fraction; math.nextafter/inf for display midpoint
checks; eab.kernel2d.g0_oracle (itself fractions, math.lcm and independent
oracle_construction). The primary oracle uses hand-derived t*t+t-1 and
(t-1/4)*(t-3/4), plus integer winding at rational times. It shares no event
root, line polynomial, normal cone, triangulator, SAT or geometry primitive
with motion.py. M2/M3 comparisons are consistency gates, not this oracle.
"""
from fractions import Fraction as F
from functools import lru_cache
from math import inf, nextafter

import pytest

from eab.kernel2d import g0_oracle as oracle
from eab.kernel2d import motion as module
from eab.kernel2d.entrance import first_entrance
from eab.kernel2d.global_entrance import GlobalEntrance2
from eab.kernel2d.motion import QuadraticTime, motion_first_entrance
from eab.oracle_construction import scalar_exact, sqrt_exact


SQ = ((0, 0), (1, 0), (1, 1), (0, 1))
THIN_L = ((0, 0), (3, 0), (3, F(1, 10)), (F(1, 10), F(1, 10)), (F(1, 10), 3), (0, 3))
CHANNEL = ((0, 0), (3, 0), (3, 1), (1, 1), (1, F(9, 5)), (3, F(9, 5)), (3, F(14, 5)), (0, F(14, 5)))
WEDGE = ((0, 0), (F(3, 5), F(1, 5)), (F(1, 5), F(3, 4)))
U = ((-1, -1), (2, -1), (2, 2), (1, 2), (1, 0), (0, 0), (0, 2), (-1, 2))
PIN = ((0, F(1, 2)), (1, F(1, 2)), (1, F(3, 2)), (0, F(3, 2)))
POCKET = ((0, 0), (6, 0), (6, 2), (5, 2), (5, 1), (1, 1), (1, 5), (5, 5), (5, 4), (6, 4), (6, 6), (0, 6))
INTERLOCK = ((0, 0), (4, 0), (4, 1), (3, 1), (3, 2), (2, 2), (2, 1), (1, 1), (1, 2), (0, 2))
TIERS = (F(2)**-400, F(1), F(2)**397)


def moved(poly, d):
    return tuple((F(x)+d[0], F(y)+d[1]) for x, y in poly)


def scaled(poly, scale):
    return tuple((scale*x, scale*y) for x, y in poly)


def at(start, end, s):
    return tuple((F(x)+s*(u-x), F(y)+s*(v-y)) for (x, y), (u, v) in zip(start, end))


FAMILIES = (
    ("thin_L", ((0, 0), (F(1, 2), 0), (F(1, 2), F(1, 20)), (0, F(1, 20))), THIN_L, (-2, F(1, 100)), (4, 0)),
    ("slot_wedge", WEDGE, CHANNEL, (-2, F(11, 10)), (4, 0)),
    ("interlock", scaled(SQ, F(1, 2)), INTERLOCK, (-2, F(6, 5)), (4, 0)),
    ("zero_clearance", PIN, U, (0, 3), (0, -4)),
    ("E_hole", scaled(SQ, F(5, 2)), POCKET, (F(3, 2), F(3, 2)), (4, 0)),
    ("collinear", ((0, 0), (F(1, 2), 0), (1, 0), (1, 1), (0, 1)), THIN_L, (-2, F(1, 20)), (4, 0)),
)


@lru_cache(maxsize=6)
def _m3_unit_reference(index):
    _, A, B, origin, direction = FAMILIES[index]
    A = moved(A, origin)
    g = GlobalEntrance2(A, B)
    hit = g.first_entrance((0, 0), direction, t_max=1)
    assert hit is not None and g.membership() == -1
    labels = {piece.label for piece in g.clipped_covers
              if oracle.on_segment(hit.exact_point, piece.start, piece.end)}
    translated = moved(A, hit.exact_point)
    labels.update(("VV", i, j) for i, p in enumerate(translated) for j, q in enumerate(B) if p == q)
    return hit.exact_time, frozenset(labels)


@pytest.mark.parametrize("index", range(len(FAMILIES)), ids=[x[0] for x in FAMILIES])
def test_translation_is_exactly_m3_with_complete_features(index):
    """18 exact trajectory samples; three scales for each of the six M3 families."""
    _, A, B, origin, direction = FAMILIES[index]
    reference_time, reference_labels = _m3_unit_reference(index)
    for scale in TIERS:
        A0, B0 = scaled(moved(A, origin), scale), scaled(B, scale)
        common = scale/F(7), -2*scale/F(5)
        A1 = moved(A0, (scale*direction[0]+common[0], scale*direction[1]+common[1]))
        B1 = moved(B0, common)
        got = motion_first_entrance(A0, B0, A1, B1)
        ray = GlobalEntrance2(A0, B0).first_entrance((0, 0),
            (scale*direction[0], scale*direction[1]), t_max=1)
        assert got.initial_state == -1 and got.status == "contact"
        assert got.exact_time == reference_time == ray.exact_time, "translation exact time"
        assert got.time == ray.time, "translation displayed time"
        assert set(got.features) == reference_labels, "translation complete cover set"
        assert set(got.features) <= set(got.incidences)


def _m2_expanded_labels(A, B, hit, direction):
    shift = tuple(hit.t_exact*x for x in direction)
    P = moved(A, shift)
    labels = set()
    for tag, i, j in hit.tied_labels:
        if tag != "FF":
            labels.add((tag, i, j))
            continue
        for k in (i, (i+1) % len(A)):
            if oracle.on_segment(P[k], B[j], B[(j+1) % len(B)]):
                labels.add(("VE", k, j))
        for k in (j, (j+1) % len(B)):
            if oracle.on_segment(B[k], P[i], P[(i+1) % len(A)]):
                labels.add(("EV", i, k))
    labels.update(("VV", i, j) for i, p in enumerate(P) for j, q in enumerate(B) if p == q)
    return labels


@pytest.mark.parametrize("kind", ("parallel", "corner", "general"))
def test_translation_convex_m2_has_exact_time_and_same_expanded_tied_set(kind):
    """Nine convex samples; FF is expanded to its closed endpoint incidences."""
    if kind == "parallel":
        A, B, d = moved(SQ, (F(1, 3), 2)), ((-2, -1), (3, -1), (3, 0), (-2, 0)), (0, -4)
    elif kind == "corner":
        A, B, d = moved(SQ, (2, 2)), SQ, (-2, -2)
    else:
        A, B, d = moved(WEDGE, (-3, F(1, 7))), ((0, 0), (2, F(1, 5)), (F(1, 2), 2)), (5, 0)
    for scale in TIERS:
        P, Q, direction = scaled(A, scale), scaled(B, scale), tuple(scale*x for x in d)
        got = motion_first_entrance(P, Q, moved(P, direction), Q)
        old = first_entrance(P, Q, (0, 0), direction, t_max=1)
        assert old.kind == "entrance" and got.status == "contact"
        assert got.exact_time == old.t_exact and got.time == old.t, "M2 exact convex time"
        assert set(got.features) == _m2_expanded_labels(P, Q, old, direction), "M2 expanded complete tie set"


def irrational_example():
    A0 = ((0, 0), (-F(1, 10), -1), (F(1, 10), -1))
    A1 = moved(A0, (1, 0))
    B0 = ((-1, F(1, 2)), (1, F(1, 2)), (1, 3))
    B1 = ((-1, F(1, 2)), (1, -F(1, 2)), (1, 3))
    return A0, B0, A1, B1


def two_roots_example():
    A0 = ((1, F(3, 16)), (F(21, 20), F(35, 16)), (F(19, 20), F(35, 16)))
    return A0, ((0, 0), (1, -2), (1, 0)), moved(A0, (-1, 0)), ((0, 0), (1, -2), (1, 1))


def _assert_irrational_report(got):
    assert got.initial_state == -1 and got.status == "contact"
    t = got.exact_time
    assert (t.rational, t.b, t.c, t.branch) == (None, F(1), F(-1), 1), "closed form golden-root certificate"
    assert got.features == got.incidences == (("VE", 0, 0),), "closed form contact feature"
    # Independent midpoint certificate: x*x+x-1 is strictly increasing on
    # positive rationals. This never invokes the tested sign/root primitive.
    lo = (F(nextafter(got.time, -inf))+F(got.time))/2
    hi = (F(nextafter(got.time, inf))+F(got.time))/2
    assert lo*lo+lo-1 < 0 < hi*hi+hi-1, "single-rounded algebraic display"


def test_motion_matches_independent_closed_form_and_integer_oracle():
    """Primary oracle: hand algebra plus g0 integer winding, no shared primitive."""
    A0, B0, A1, B1 = irrational_example()
    _assert_irrational_report(motion_first_entrance(A0, B0, A1, B1))
    for s in (F(0), F(1, 3), F(3, 5), F(5, 8), F(3, 4), F(1)):
        expected = -1 if s*s+s-1 < 0 else 1
        assert oracle.overlap(at(A0, A1, s), at(B0, B1, s)) == expected
    A0, B0, A1, B1 = two_roots_example()
    got = motion_first_entrance(A0, B0, A1, B1)
    assert got.exact_time == F(1, 4), "earliest quadratic branch"
    assert got.features == (("VE", 0, 2),)
    for s in (F(0), F(1, 8), F(1, 4), F(1, 2), F(3, 4), F(7, 8), F(1)):
        polynomial = (s-F(1, 4))*(s-F(3, 4))
        expected = -1 if polynomial > 0 else (0 if polynomial == 0 else 1)
        assert oracle.overlap(at(A0, A1, s), at(B0, B1, s)) == expected


def test_quadratic_numbers_are_exact():
    low, high = module._roots((F(-1), F(1), F(1)))
    same = module._roots((F(-7), F(7), F(7)))[1]
    other = module._roots((F(-2), F(0), F(1)))[1]
    close = module._roots((F(-1)-F(1, 2**150), F(1), F(1)))[1]
    assert low < 0 < F(3, 5) < high < F(5, 8) < other
    assert high == same and hash(high) == hash(same) and len({high, same}) == 1
    assert high < close and not close < high and close != high
    assert high.sign_polynomial(-1, 1, 1) == 0
    assert high.sign_polynomial(1, -1, -1) == 0
    assert high.sign_polynomial(F(1, 2**500)-1, 1, 1) == 1
    assert high.sign_polynomial(-F(1, 2**500)-1, 1, 1) == -1
    assert QuadraticTime(F(1, 4)) == F(1, 4)
    assert hash(QuadraticTime(F(1, 4))) == hash(F(1, 4))
    for args in ((None, 0, 1, 1), (None, 0, -1, 1), (None, 0, -2, 0), (F(1), 1, 0, 0)):
        with pytest.raises(ValueError):
            QuadraticTime(*args)


def test_quadratic_numeric_equality_hash_and_string_set_contract():
    for exact, equivalents in ((F(1), (1, F(1), 1.0, True)),
                               (F(0), (0, F(0), 0.0, False)),
                               (F(1, 2), (F(1, 2), 0.5))):
        t = QuadraticTime(exact)
        for other in equivalents:
            assert t == other and other == t, "supported numeric equality is symmetric"
            assert hash(t) == hash(other), "equal numeric values must have equal hashes"
            assert len({t, other}) == 1 and {t: "same"}[other] == "same"
    one = QuadraticTime(F(1))
    for text in ("1", "1/1", b"1"):
        assert one != text and text != one, "parseable text is not numeric equality"
        assert len({one, text}) == 2
        assert len({one: "number", text: "text"}) == 2
        with pytest.raises(TypeError, match="supported finite number"):
            one < text
        with pytest.raises(TypeError, match="supported finite number"):
            text < one
    for nonfinite in (inf, -inf, float("nan")):
        assert one != nonfinite and nonfinite != one
        with pytest.raises(TypeError, match="supported finite number"):
            one < nonfinite
    tenth = QuadraticTime(F(1, 10))
    assert tenth != 0.1 and 0.1 != tenth, "float comparison uses its exact binary value"
    binary_tenth = QuadraticTime(F(0.1))
    assert binary_tenth == 0.1 and hash(binary_tenth) == hash(0.1)
    assert False < QuadraticTime(F(1, 2)) < True
    assert 0.1 < QuadraticTime(F(1, 2)) < 1.0


def test_quadratic_constructor_rejects_inexact_and_boolean_fields():
    for args in ((None, 0, -2, 1.0), (None, 0, -2, True), (None, 0, -2, F(1)),
                 (None, 0.0, -2, 1), (None, 0, -2.0, 1), (None, False, -2, 1),
                 (True,), (F(1), 0, 0, False), (0.25,), (None, inf, -2, 1),
                 (None, 0, float("nan"), 1), (float("nan"),)):
        with pytest.raises(ValueError):
            QuadraticTime(*args)
    # Severe exact cancellation would silently become zero with branch=1.0.
    t = QuadraticTime(None, 0, -2, 1)
    huge = 10**100
    floor = 14142135623730950488016887242096980785696718753769480731766797379907324784621070388503875343276415727
    assert floor*floor < 2*huge*huge < (floor+1)*(floor+1)
    assert t.sign_polynomial(-F(floor, huge), 1) == 1
    assert t.sign_polynomial(-F(floor+1, huge), 1) == -1


def _independent_root_interval(b, c, branch):
    """Rational sqrt bisection; no production root/sign/construction import."""
    d = b*b-4*c
    low, high = F(0), F(1)+d
    for _ in range(100):
        middle = (low+high)/2
        if middle*middle < d:
            low = middle
        else:
            high = middle
    return ((-b+low)/2, (-b+high)/2) if branch == 1 else ((-b-high)/2, (-b-low)/2)


def test_polynomial_sign_and_order_match_independent_rational_intervals():
    """324 signs, 132 cross-domain orderings; oracle uses only Fraction."""
    roots = []
    for b, c in ((F(0), F(-2)), (F(1), F(-1)), (F(-3), F(1)),
                 (F(1, 3), F(-2, 7)), (F(0), F(-3)), (F(-7, 5), F(2, 9))):
        for branch in (-1, 1):
            t = QuadraticTime(None, b, c, branch)
            lo, hi = _independent_root_interval(b, c, branch)
            roots.append((t, lo, hi))
            for p0 in (F(-2), F(0), F(3)):
                for p1 in (F(-2), F(0), F(3)):
                    for p2 in (F(-2), F(0), F(3)):
                        if p0 == p2*c and p1 == p2*b:
                            expected = 0
                        else:
                            samples = [p0+p1*x+p2*x*x for x in (lo, hi)]
                            if p2 and lo <= -p1/(2*p2) <= hi:
                                samples.append(p0-p1*p1/(4*p2))
                            assert min(samples) > 0 or max(samples) < 0, "oracle interval must certify sign"
                            expected = 1 if min(samples) > 0 else -1
                        assert t.sign_polynomial(p0, p1, p2) == expected, "independent interval polynomial sign"
    for t, lo, hi in roots:
        for u, lower, upper in roots:
            if t is u:
                continue
            assert hi < lower or upper < lo, "independent root isolation must separate domains"
            assert (t < u) == (hi < lower), "independent cross-domain root order"


@pytest.mark.parametrize("scale", TIERS)
def test_every_public_motion_numeric_field_has_three_tier_independent_reference(scale):
    data = tuple(scaled(p, scale) for p in irrational_example())
    got = motion_first_entrance(*data)
    _assert_irrational_report(got)
    assert got.exact_time.certificate == {"rational": None, "polynomial": ["-1", "1", "1"], "branch": 1}
    rational = motion_first_entrance(*(scaled(p, scale) for p in two_roots_example()))
    t = rational.exact_time
    assert (t.rational, t.b, t.c, t.branch) == (F(1, 4), 0, 0, 0)
    assert t.certificate == {"rational": "1/4", "polynomial": None, "branch": 0}
    assert t.time == rational.time == 0.25
    assert rational.incidences == rational.features == (("VE", 0, 2),)
    # The standalone exact-number API also covers low/ordinary/high *time*
    # magnitudes, rather than testing only a scale-invariant motion time.
    root = QuadraticTime(None, F(0), -2*scale*scale, 1)
    assert root.time == sqrt_exact(2*scale*scale)
    assert (root.rational, root.b, root.c, root.branch) == (None, 0, -2*scale*scale, 1)
    assert QuadraticTime(scale).time == scalar_exact(scale)


@pytest.mark.parametrize("scale", (F(1, 10**9), F(1), F(10**8)))
@pytest.mark.parametrize("translation", (0, 10**3, 10**5, 10**6))
def test_public_motion_is_rigid_motion_and_unit_covariant(scale, translation):
    data = irrational_example()
    original = motion_first_entrance(*data)
    for c, s in ((F(0), F(1)), (F(3, 5), F(4, 5))):
        def transform(poly):
            return tuple((scale*(c*x-s*y)+translation,
                          scale*(s*x+c*y)-3*translation) for x, y in poly)
        got = motion_first_entrance(*(transform(p) for p in data))
        assert got.exact_time == original.exact_time, "exact rigid/unit time covariance"
        assert set(got.features) == set(original.features), "set-valued feature covariance"
        assert set(got.incidences) == set(original.incidences)
        assert got.time == original.time


def test_initial_states_closed_endpoints_and_stationary_window_are_explicit():
    far = moved(SQ, (3, 0))
    none = motion_first_entrance(SQ, far, SQ, far)
    assert (none.initial_state, none.status, none.exact_time, none.time, none.features, none.incidences) == (-1, "no_contact", None, None, (), ())
    overlap = motion_first_entrance(SQ, SQ, SQ, SQ)
    assert overlap.initial_state == 1 and overlap.status == "initial_overlap" and overlap.exact_time is None
    touch = moved(SQ, (1, 1))
    got = motion_first_entrance(SQ, touch, SQ, touch)
    assert got.initial_state == 0 and got.exact_time == 0 and ("VV", 2, 0) in got.features
    corner = moved(SQ, (2, 2))
    end = motion_first_entrance(SQ, corner, SQ, touch)
    assert end.exact_time == 1 and ("VV", 2, 0) in end.features, "closed window endpoint"


def test_persistent_collinear_sliding_and_isolated_grazing_are_closed_contact():
    B = moved(SQ, (3, 1))
    slide = motion_first_entrance(SQ, B, SQ, moved(B, (-3, 0)))
    assert slide.exact_time == F(2, 3) and ("VV", 2, 0) in slide.features
    for s in (F(0), F(1, 2), F(2, 3), F(3, 4), F(1)):
        assert oracle.overlap(SQ, moved(B, (-3*s, 0))) == (-1 if s < F(2, 3) else 0)
    B0, B1 = moved(SQ, (3, -1)), moved(SQ, (-1, 3))
    graze = motion_first_entrance(SQ, B0, SQ, B1)
    assert graze.exact_time == F(1, 2) and ("VV", 2, 0) in graze.features
    for s in (F(0), F(49, 100), F(1, 2), F(51, 100), F(1)):
        assert oracle.overlap(SQ, at(B0, B1, s)) == (0 if s == F(1, 2) else -1)
    # Swept boxes overlap, but the trajectory misses the actual polygons.
    A0, A1 = moved(SQ, (-3, 0)), moved(SQ, (3, 4))
    assert motion_first_entrance(A0, SQ, A1, SQ).status == "no_contact"


@pytest.mark.parametrize("kind", ("face", "corner", "tight_fit"))
def test_complete_multi_feature_sets_are_covariant_not_only_single_ve(kind):
    if kind == "face":
        data = (moved(SQ, (-2, 0)), SQ, SQ, SQ)
    elif kind == "corner":
        data = (SQ, moved(SQ, (2, 2)), SQ, moved(SQ, (1, 1)))
    else:
        data = (moved(PIN, (0, 3)), U, moved(PIN, (0, -1)), U)
    reference = motion_first_entrance(*data)
    assert len(reference.features) >= 3 and any(x[0] == "VV" for x in reference.features)
    for scale in (F(1, 10**9), F(1), F(10**8)):
        for translation in (0, 10**5, 10**6):
            for c, s in ((F(0), F(1)), (F(3, 5), F(4, 5))):
                def transform(poly):
                    return tuple((scale*(c*x-s*y)+translation,
                                  scale*(s*x+c*y)-7*translation) for x, y in poly)
                got = motion_first_entrance(*(transform(p) for p in data))
                assert got.exact_time == reference.exact_time
                assert set(got.features) == set(reference.features), "full multi-cover covariance"
                assert set(got.incidences) == set(reference.incidences), "full multi-incidence covariance"


def test_clockwise_input_preserves_original_vertex_and_edge_ids():
    A0, B0, A1, B1 = irrational_example()
    got = motion_first_entrance(A0[::-1], B0[::-1], A1[::-1], B1[::-1])
    assert got.features == got.incidences == (("VE", 2, 1),)
    assert got.exact_time == motion_first_entrance(A0, B0, A1, B1).exact_time


def test_invalid_motion_is_rejected_between_valid_snapshots():
    far = moved(SQ, (10, 10))
    # Both endpoint triangles are valid CCW. Their area polynomial changes
    # sign twice; no edge shrinks to zero, so endpoint-only checks miss this.
    begin, end = ((0, 0), (1, 0), (1, F(3, 16))), ((0, 0), (1, 1), (0, F(3, 16)))
    for p in (begin, end):
        assert oracle.overlap(p, far) == -1
    with pytest.raises(ValueError, match="within the step"):
        motion_first_entrance(begin, far, end, far)
    # Same endpoint shape and orientation, wrong vertex correspondence.
    with pytest.raises(ValueError, match="zero-length edge"):
        motion_first_entrance(SQ, far, SQ[2:]+SQ[:2], far)
    bad = (SQ[:-1], ((0, 0), (1, 0), (1, 0), (0, 1)),
           ((0, 0), (1, 1), (0, 1), (1, 0)), ((0, 0), (1, 0), (inf, 1), (0, 1)),
           (SQ, SQ))
    for ring in bad:
        with pytest.raises(ValueError):
            motion_first_entrance(SQ, far, ring, far)


def _assert_two_root_guard():
    assert motion_first_entrance(*two_roots_example()).exact_time == F(1, 4), "earliest quadratic branch"


def _assert_endpoint_guard():
    A, B = SQ, moved(SQ, (2, 2))
    got = motion_first_entrance(A, B, A, moved(B, (-1, -1)))
    assert got.exact_time == 1 and ("VV", 2, 0) in got.features, "closed endpoint event lost"


def _assert_tie_guard():
    A, B = moved(SQ, (F(1, 3), 2)), ((-2, -1), (3, -1), (3, 0), (-2, 0))
    got = motion_first_entrance(A, B, moved(A, (0, -4)), B)
    assert set(got.features) == {("VE", 0, 2), ("VE", 1, 2)}, "complete simultaneous cover set"


def _assert_translation_guard():
    A, B = moved(WEDGE, (-3, F(1, 7))), ((0, 0), (2, F(1, 5)), (F(1, 2), 2))
    got = motion_first_entrance(A, B, moved(A, (5, 0)), B)
    expected = GlobalEntrance2(A, B).first_entrance((0, 0), (5, 0), t_max=1)
    assert got.exact_time == expected.exact_time, "general event path translation consistency"


@pytest.mark.parametrize("mutation", ("wrong_quadratic_branch", "open_endpoint", "lost_tie", "translation_bypass"))
def test_internal_mutations_fail_the_intended_guard(monkeypatch, mutation):
    """Inject inside roots/segment/cone predicates, never append fake outputs."""
    guards = {"wrong_quadratic_branch": (_assert_two_root_guard, "earliest quadratic branch"),
              "open_endpoint": (_assert_endpoint_guard, "closed endpoint event lost"),
              "lost_tie": (_assert_tie_guard, "complete simultaneous cover set"),
              "translation_bypass": (_assert_translation_guard, "general event path translation consistency")}
    guard, message = guards[mutation]
    guard()
    if mutation == "wrong_quadratic_branch":
        original = module._roots
        def mutant(poly):
            roots = original(poly)
            return roots[-1:] if poly[2] and len(roots) == 2 else roots
        monkeypatch.setattr(module, "_roots", mutant)
    elif mutation == "open_endpoint":
        def mutant(time, orient, between):
            return time.sign_polynomial(*orient) == 0 and time.sign_polynomial(*between) < 0
        monkeypatch.setattr(module, "_contains", mutant)
    elif mutation == "lost_tie":
        original = module._cone
        def mutant(time, paths, vertex, other_edge):
            return vertex != 1 and original(time, paths, vertex, other_edge)
        monkeypatch.setattr(module, "_cone", mutant)
    else:
        original = module._roots
        def mutant(poly):
            return () if poly[2] == 0 else original(poly)
        monkeypatch.setattr(module, "_roots", mutant)
    with pytest.raises(AssertionError, match=message):
        guard()
