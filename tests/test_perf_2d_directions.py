"""VE direction integer lift versus frozen Fraction expressions.

Oracle uses only test-local Fraction dot/cross, squared ratios and cone formulas;
none of the production sign, angle-window, cone or integerization primitives
is reused. Independent rational Pythagorean rays pin both window boundaries.
"""
from construction_oracle import scalar_exact
from fractions import Fraction as F
import inspect
import random

import pytest

from eab.kernel2d import covers as C


def _cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def _dot(a, b):
    return a[0]*b[0]+a[1]*b[1]


def _reference(lo, hi, e, tol, cone_tol):
    """Pre-optimization exact predicates, expanded into local Fraction arithmetic."""
    lo, hi, e = (tuple(F(component) for component in vector) for vector in (lo, hi, e))
    v = (-e[1], e[0])
    turn, c1, c2 = _cross(lo, hi), _cross(lo, v), _cross(v, hi)
    if turn >= 0 and (turn > 0 or _dot(lo, hi) > 0) and c1 >= 0 and c2 >= 0 and (turn > 0 or _dot(lo, v) > 0):
        return 1 if c1 > 0 and c2 > 0 else 0
    if tol <= 0 and (cone_tol is None or cone_tol <= 0):
        return -1
    w2 = (F(max(cone_tol, 0))**2 if cone_tol is not None
          else F(max(tol, 0))**2/min(_dot(x, x) for x in (lo, hi, e)))
    nonreflex = turn >= 0 and (turn > 0 or _dot(lo, hi) > 0) or (
        turn < 0 and _dot(lo, hi) > 0 and turn*turn <= w2*_dot(lo, lo)*_dot(hi, hi))
    a, b = _dot(lo, v), _dot(hi, v)
    if a >= 0 and b >= 0:
        bisector = a > 0 or b > 0
    elif a <= 0 and b <= 0:
        bisector = False
    else:
        cmp = a*a*_dot(hi, hi)-b*b*_dot(lo, lo)
        bisector = cmp > 0 if a > 0 else cmp < 0
    accepted = ((c1 >= 0 or c1*c1 <= w2*_dot(lo, lo)*_dot(v, v))
                and (c2 >= 0 or c2*c2 <= w2*_dot(v, v)*_dot(hi, hi)) and bisector)
    return 0 if w2 > 0 and nonreflex and accepted else -1


def direction_cases(kind, scale, offset):
    rng = random.Random(938421)
    for k in range(48):
        # Compute differences from the actual rounded engineering coordinates.
        origin = (scalar_exact(offset), scalar_exact(-2*offset))
        vectors = []
        for _ in range(3):
            raw = tuple(F(rng.randrange(-20, 21), rng.choice((1, 3, 7))) for _ in range(2))
            if raw == (0, 0):
                raw = (F(1), F(0))
            if offset:
                endpoint = tuple(scalar_exact(F(origin[j])+scale*raw[j]) for j in range(2))
                vector = tuple(F(endpoint[j])-F(origin[j]) for j in range(2))
            else:
                vector = tuple(scale*x for x in raw)
            vectors.append(vector)
        lo, hi, e = vectors
        if kind == "collinear":
            hi = tuple((F(-1) if k % 2 else F(3))*x for x in lo)
        elif kind == "boundary":
            e = (lo[1], -lo[0])
        elif kind == "almost_reflex":
            hi = (lo[0]+scale/F(2**90), lo[1]-scale/F(2**100))
        elif kind == "unequal_lengths":
            lo = tuple(x/F(101) for x in lo)
            hi = tuple(x*F(53) for x in hi)
        for tol, cone_tol in ((-scale, None), (F(0), None), (scale/F(100), None),
                              (scale*F(3, 5), None), (scale, F(-1)),
                              (scale, F(0)), (F(0), F(1, 100)), (F(0), F(3, 5))):
            yield lo, hi, e, tol, cone_tol


@pytest.mark.parametrize("kind", ["random", "collinear", "boundary", "almost_reflex", "unequal_lengths"])
@pytest.mark.parametrize("scale,offset", [(F(1), F(0)), (F(1, 10**8), F(10**6)),
                                         (F(1000), F(-10**5)), (F(1, 2**1074), F(0))])
def test_integer_ve_state_matches_fraction_reference(kind, scale, offset):
    outcomes = set()
    for args in direction_cases(kind, scale, offset):
        result = C._ve_side_directions.__wrapped__(*args)
        assert result == _reference(*args), ("complete VE state", kind, args)
        outcomes.add(result)
    assert outcomes <= {-1, 0, 1}


@pytest.mark.parametrize("scale", [F(1, 7), F(1), F(1000), F(1, 2**1074)])
def test_integer_ve_length_and_angle_boundaries_have_independent_pythagorean_oracle(scale):
    """The exterior ray (4,-3) has exact sin 3/5 relative to the lower side."""
    lo, hi, e = (scale, F(0)), (F(0), scale), (-3*scale, -4*scale)
    threshold = F(3, 5)
    delta = F(1, 2**90)
    results = []
    for w, expected in ((threshold-delta, -1), (threshold, 0), (threshold+delta, 0)):
        got = C._ve_side_directions(lo, hi, e, scale*w, None)
        assert got == expected, "length window retains exact scale and boundary"
        assert C._ve_side_directions(lo, hi, e, F(0), w) == expected, "dimensionless cone window"
        results.append(got)
    assert results == [-1, 0, 0]
    assert C._ve_side_directions(lo, hi, (-scale, scale), F(0), None) == -1
    assert C._ve_side_directions(lo, hi, (scale, -scale), F(0), None) == 1
    assert C._ve_side_directions(lo, hi, (F(0), -scale), F(0), None) == 0


def test_integer_ve_shared_scale_preserves_the_shortest_direction_length():
    lo, hi, e = (F(1, 100), F(0)), (F(0), F(10)), (F(-3), F(-4))
    for tol, expected in ((F(3, 500)-F(1, 2**90), -1), (F(3, 500), 0)):
        assert C._ve_side_directions(lo, hi, e, tol, None) == expected, "minimum vector length is not normalized away"
    assert C._ve_side_directions(lo, hi, e, F(1), F(0)) == -1, "explicit cone window overrides length tol"


def test_integer_ve_binary64_subnormal_length_window_is_scaled_without_float_product():
    tiny = F(1, 2**1074)
    lo, hi, e = (tiny, F(0)), (F(0), tiny), (-3*tiny, -4*tiny)
    # The exact ratio tol/min_length is 1 even though D cannot convert to float.
    assert C._ve_side_directions(lo, hi, e, scalar_exact(tiny), None) == 0, "no premature float rescaling"


def test_integer_ve_length_rescaling_mutation_has_teeth(monkeypatch):
    source = inspect.getsource(C._ve_side_directions.__wrapped__)
    needle = "tol = Fraction(tol) * den"
    assert source.count(needle) == 1
    namespace = dict(vars(C))
    exec(compile(source.replace(needle, "tol = Fraction(tol)"), "<PERF-VE-length-mutant>", "exec"), namespace)
    monkeypatch.setattr(C, "_ve_side_directions", namespace["_ve_side_directions"])
    with pytest.raises(AssertionError, match="length window retains exact scale and boundary"):
        test_integer_ve_length_and_angle_boundaries_have_independent_pythagorean_oracle(F(1, 7))


def test_integer_ve_strict_boundary_mutation_has_teeth(monkeypatch):
    source = inspect.getsource(C._ve_side_directions.__wrapped__)
    needle = "return 1 if c1 > 0 and c2 > 0 else 0"
    assert source.count(needle) == 1
    namespace = dict(vars(C))
    exec(compile(source.replace(needle, "return 1 if c1 >= 0 and c2 >= 0 else 0"),
                 "<PERF-VE-strict-mutant>", "exec"), namespace)
    monkeypatch.setattr(C, "_ve_side_directions", namespace["_ve_side_directions"])
    lo, hi, e = (F(1), F(0)), (F(0), F(1)), (F(0), F(-1))
    with pytest.raises(AssertionError, match="exact boundary cannot become strict"):
        assert C._ve_side_directions(lo, hi, e, F(0), None) == _reference(lo, hi, e, F(0), None), "exact boundary cannot become strict"
