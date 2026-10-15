"""M5a independent complete-root differential gates.

Oracle imports: fractions.Fraction, functools.cmp_to_key/lru_cache,
eab.kernel2d.g0_oracle.overlap (integer solid-state only). The helper imports
NO se2/algebraic/motion/exact/global_entrance/production construction module.
This wrapper alone imports the tested APIs. Interpolation, Sturm, root sign,
normal-cone reconstruction and interval G0 checks are independent code paths.
"""
from fractions import Fraction as F
from random import Random

import pytest

from eab.kernel2d import se2 as tested_module
from eab.kernel2d.se2 import SE2Motion, se2_first_entrance
from m5a_independent_oracle import (
    Root, certificate_root, compare, first_contact, point_at, roots,
)


TRIANGLE = ((0, 0), (1, 0), (F(1, 4), 1))
PENTAGON = ((0, 0), (1, 0), (F(3, 2), F(1, 2)), (1, 1), (0, 1))
L_SHAPE = ((0, 0), (F(3, 2), 0), (F(3, 2), F(1, 2)),
           (F(1, 2), F(1, 2)), (F(1, 2), F(3, 2)), (0, F(3, 2)))
SQUARE = ((0, 0), (2, 0), (2, 2), (0, 2))
CHANNEL = ((0, 0), (2, 0), (2, 2), (F(3, 2), 2),
           (F(3, 2), 1), (F(1, 2), 1), (F(1, 2), 2), (0, 2))


def center(ring):
    return tuple(sum(F(p[k]) for p in ring)/len(ring) for k in (0, 1))


def seeded_cases():
    rng = Random(20261015)
    cases = []
    ua = (F(1, 2), F(-1, 3), F(2, 3), F(-1, 4))
    ub = (F(-1, 5), F(1, 4), F(1, 3))
    for i in range(10):
        shape = (TRIANGLE, PENTAGON, L_SHAPE)[i % 3]
        height = F(rng.randrange(-2, 7), 4)
        a = tuple((F(x)-3, F(y)+height) for x, y in shape)
        b = (SQUARE, CHANNEL)[i % 2]
        ma = (ua[i % 4], (F(rng.randrange(15, 23), 4), F(rng.randrange(-2, 3), 5)), center(a))
        mb = (ub[i % 3], (F(rng.randrange(-1, 2), 5), F(rng.randrange(-1, 2), 7)), center(b))
        cases.append((a, b, ma, mb))
    # Controls are outside random luck: genuine no-contact and exact VV ties.
    cases.append((TRIANGLE, tuple((x+20, y) for x, y in SQUARE),
                  (F(1, 2), (F(1), F(0)), center(TRIANGLE)),
                  (F(-1, 3), (F(0), F(0)), (F(21), F(1)))))
    small = ((2, 2), (3, 2), (3, 3), (2, 3))
    unit = ((0, 0), (1, 0), (1, 1), (0, 1))
    cases.append((small, unit, (F(0), (F(-2), F(-2)), center(small)),
                  (F(0), (F(0), F(0)), center(unit))))
    return tuple(cases)


CASES = seeded_cases()


@pytest.mark.parametrize("index", range(len(CASES)))
def test_random_complete_events_match_independent_sturm_and_g0(index):
    """Exact first root and complete sets, not a sampling-only differential."""
    a, b, ma, mb = CASES[index]
    expected = first_contact(a, b, ma, mb)
    actual = se2_first_entrance(a, b, SE2Motion(*ma), SE2Motion(*mb))
    assert actual.initial_state == expected["initial"], "independent initial entity three-state"
    assert actual.status == expected["status"], "independent full-window contact status"
    assert set(actual.incidences) == expected["incidences"], "independent complete closed incidence set"
    assert set(actual.features) == expected["features"], "independent complete normal-cone cover set"
    if expected["root"] is None:
        assert actual.exact_time is None, "independent absent first contact"
    else:
        got = certificate_root(actual.exact_time.certificate)
        assert compare(got, expected["root"]) == 0, "independent gcd and isolating interval identify first root"
    assert expected["probes"], "every seeded separated case has nonempty interval audit"
    if index < 10:
        assert expected["max_degree"] == 5, "both-body rotation really exercises degree five"
    if index == 10:
        assert actual.status == "no_contact", "fixed no-contact positive control"
    if index == 11:
        assert actual.exact_time == F(1, 2), "fixed simultaneous rational contact control"
        assert len(actual.incidences) > 1 and ("VV", 0, 2) in actual.features, "fixed complete tied feature control"


def test_independent_oracle_is_self_checked_on_repeated_adjacent_and_irrational_roots():
    """Oracle root machinery has controls independent of tested algebraic code."""
    # (x-1/4)^2*(x-3/4), including a no-sign-change root.
    got = roots((F(-3, 64), F(7, 16), F(-5, 4), F(1)))
    assert len(got) == 2
    assert compare(got[0], Root.rational(F(1, 4))) == 0
    assert compare(got[1], Root.rational(F(3, 4))) == 0
    irrational = roots((F(-1, 2), 0, 0, 1))[0]
    lo, hi = F(0), F(1)
    for _ in range(90):
        mid = (lo+hi)/2
        if mid**3 < F(1, 2):
            lo = mid
        else:
            hi = mid
    assert irrational.sign((-lo, 1)) > 0 and irrational.sign((-hi, 1)) < 0
    assert irrational.sign((F(-1, 2), 0, 0, 1)) == 0
    epsilon = F(1, 2**100)
    adjacent = roots((F(1, 16)+epsilon/4, -F(1, 2)-epsilon, 1))
    assert len(adjacent) == 2 and compare(adjacent[0], adjacent[1]) < 0
    assert compare(adjacent[0], Root.rational(F(1, 4))) == 0
    assert compare(adjacent[1], Root.rational(F(1, 4)+epsilon)) == 0


def test_independent_cayley_path_closes_without_production_rotation():
    """Known 3-4-5 rotation checks the oracle's path, not just its endpoints."""
    spec = F(1, 3), (F(2), F(-1)), (F(5), F(7))
    p = F(10), F(7)
    assert point_at(p, spec, F(0)) == p
    assert point_at(p, spec, F(1)) == (F(11), F(9))
    # u=1/3 gives cos=4/5, sin=3/5, preserving squared radius 25.
    for s in (F(1, 7), F(2, 5), F(3, 4)):
        q = point_at(p, spec, s)
        moving_center = (spec[2][0]+s*spec[1][0], spec[2][1]+s*spec[1][1])
        assert sum((q[k]-moving_center[k])**2 for k in (0, 1)) == 25


def test_independent_oracle_detects_lost_degree_five_term_inside_kernel(monkeypatch):
    """The semantic root assertion, not a source hash, kills truncation."""
    a, b, ma, mb = CASES[0]
    expected = first_contact(a, b, ma, mb)
    original = tested_module._line_polynomials
    injections = []

    def truncate(*args):
        f, g, h = original(*args)
        if len(f) == 6:
            injections.append(f[-1])
            f = f[:-1]
        return f, g, h

    monkeypatch.setattr(tested_module, "_line_polynomials", truncate)
    actual = se2_first_entrance(a, b, SE2Motion(*ma), SE2Motion(*mb))
    assert injections and actual.status == "contact", "injected degree-five bug reaches contact path"
    got = certificate_root(actual.exact_time.certificate)
    with pytest.raises(AssertionError, match="independent first-root identity rejects lost degree-five term"):
        assert compare(got, expected["root"]) == 0, "independent first-root identity rejects lost degree-five term"
