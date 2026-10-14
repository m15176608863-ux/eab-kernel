"""Independent M4c differential oracle; no production motion primitive.

Complete import list: dataclasses.dataclass, fractions.Fraction, math.isqrt,
math.lcm, and eab.kernel2d.g0_oracle.overlap. The latter imports only
fractions.Fraction, math.lcm and eab.oracle_construction (display helpers;
overlap itself uses integer winding/intersection). In particular this module
never imports motion.py, exact.py, global_entrance.py or their primitives.

An event *superset* comes from supporting-line areas interpolated at -1, 0, 1.
Persistently collinear pairs additionally contribute coordinate-equality roots
against both segment endpoints. Integer discriminants give Q(sqrt(D)) roots;
all sorting, evaluation and midpoint isolation are rational/exact. Incidence
uses coordinate boxes, not production's dot-product segment test. Covers use
the two neighbor half-planes and convexity, independently of production cones.
Each open event interval is inspected with G0 at two rational interior points;
G0's exact body three-state must be constant there. This is an oracle, not a
time-grid approximation: every possible boundary change is in the event set.
"""
from dataclasses import dataclass
from fractions import Fraction as F
from math import isqrt, lcm

from eab.kernel2d.g0_oracle import overlap


def _sign(x):
    return (x > 0) - (x < 0)


def _surd_sign(a, b, d):
    if not b:
        return _sign(a)
    if not a:
        return _sign(b)
    if a > 0 and b > 0:
        return 1
    if a < 0 and b < 0:
        return -1
    square_difference = a*a - b*b*d
    return _sign(square_difference) if a > 0 else -_sign(square_difference)


@dataclass(frozen=True, eq=False)
class Root:
    """h + k sqrt(d); rational square discriminants are reduced immediately."""
    h: F
    k: F = F(0)
    d: int = 0

    def key(self):
        return (self.h, _sign(self.k), self.k*self.k*self.d)

    def __hash__(self):
        return hash(self.key())

    def __eq__(self, other):
        return (isinstance(other, Root)
                and self.key() == (other.h, _sign(other.k), other.k*other.k*other.d))

    def relative(self, rational):
        return _surd_sign(self.h-rational, self.k, self.d)

    def __lt__(self, other):
        if self == other:
            return False
        if not other.k:
            return self.relative(other.h) < 0
        if not self.k:
            return _surd_sign(other.h-self.h, other.k, other.d) > 0
        # Only unit-window roots are sorted. Bisect until a rational separator
        # distinguishes the two roots; equal algebraic roots were removed above.
        low, high = F(0), F(1)
        while True:
            mid = (low+high)/2
            left = self.relative(mid)
            right = _surd_sign(other.h-mid, other.k, other.d)
            if left != right:
                return left < right
            if left < 0:
                high = mid
            else:
                low = mid

    def evaluate_sign(self, polynomial):
        c, b, a = polynomial
        rational = c+b*self.h+a*(self.h*self.h+self.k*self.k*self.d)
        radical = b*self.k+2*a*self.h*self.k
        return _surd_sign(rational, radical, self.d)

    def certificate(self):
        if not self.k:
            return {"rational": str(self.h), "polynomial": None, "branch": 0}
        return {"rational": None,
                "polynomial": [str(self.h*self.h-self.k*self.k*self.d),
                               str(-2*self.h), "1"],
                "branch": _sign(self.k)}


def _roots(coefficients):
    den = lcm(*(v.denominator for v in coefficients))
    c, b, a = (int(v*den) for v in coefficients)
    if not a:
        roots = (Root(F(-c, b)),) if b else ()
    else:
        discriminant = b*b-4*a*c
        if discriminant < 0:
            return ()
        square = isqrt(discriminant)
        if square*square == discriminant:
            roots = (Root(F(-b-square, 2*a)), Root(F(-b+square, 2*a)))
        else:
            roots = (Root(F(-b, 2*a), F(-1, 2*a), discriminant),
                     Root(F(-b, 2*a), F(1, 2*a), discriminant))
    return tuple(t for t in roots if t.relative(0) >= 0 and t.relative(1) <= 0)


def at(start, end, t):
    return tuple(tuple(F(a)+(F(b)-F(a))*t for a, b in zip(p, q))
                 for p, q in zip(start, end))


def _area(a, b, c):
    return ((b[0]-a[0])*(c[1]-a[1])
            -(b[1]-a[1])*(c[0]-a[0]))


def _interpolate(values):
    negative, zero, positive = values
    return zero, (positive-negative)/2, (positive+negative-2*zero)/2


def _incidence_models(A0, B0, A1, B1):
    models = []
    for P0, Q0, P1, Q1, tag in ((A0, B0, A1, B1, "VE"),
                                (B0, A0, B1, A1, "EV")):
        samples = [(at(P0, P1, t), at(Q0, Q1, t)) for t in (-1, 0, 1)]
        for i in range(len(P0)):
            for j in range(len(Q0)):
                polynomials = []
                for P, Q in samples:
                    prev, p, following = P[i-1], P[i], P[(i+1) % len(P)]
                    a, b = Q[j], Q[(j+1) % len(Q)]
                    # 0 area; 1..4 independent axis bounds; 5 local turn;
                    # 6/7 neighbors' B half-planes; 8 flat support orientation.
                    polynomials.append((_area(a, b, p), p[0]-a[0], p[0]-b[0],
                                        p[1]-a[1], p[1]-b[1],
                                        _area(prev, p, following),
                                        _area(a, b, prev), _area(a, b, following),
                                        (b[0]-a[0])*(following[0]-p[0])
                                        +(b[1]-a[1])*(following[1]-p[1])))
                polys = tuple(_interpolate(values) for values in zip(*polynomials))
                label = (tag, i, j) if tag == "VE" else (tag, j, i)
                models.append((label, polys))
    return tuple(models)


def _features(time, models, A0, B0, A1, B1):
    incidences, covers = set(), set()
    for label, polys in models:
        if time.evaluate_sign(polys[0]):
            continue
        signs = tuple(time.evaluate_sign(p) for p in polys[1:])
        if signs[0]*signs[1] > 0 or signs[2]*signs[3] > 0:
            continue
        incidences.add(label)
        turn, previous_side, following_side, flat_direction = signs[4:]
        if (turn >= 0 and previous_side <= 0 and following_side <= 0
                and (turn > 0 or flat_direction < 0)):
            covers.add(label)
    for i, (a, end_a) in enumerate(zip(A0, A1)):
        for j, (b, end_b) in enumerate(zip(B0, B1)):
            if all(time.evaluate_sign((F(a[k])-F(b[k]),
                                       F(end_a[k])-F(a[k])-F(end_b[k])+F(b[k]),
                                       F(0))) == 0 for k in (0, 1)):
                incidences.add(("VV", i, j))
                covers.add(("VV", i, j))
    return tuple(sorted(incidences)), tuple(sorted(covers))


def _between(left, right):
    """Return an exact dyadic rational strictly between distinct unit roots."""
    denominator = 2
    numerator = 1
    while True:
        middle = F(numerator, denominator)
        if left.relative(middle) < 0 and right.relative(middle) > 0:
            return middle
        numerator = 2*numerator + (1 if left.relative(middle) >= 0 else -1)
        denominator *= 2


def entrance(A0, B0, A1, B1):
    """Independent exact expected answer and interval-state evidence (CCW only)."""
    models = _incidence_models(A0, B0, A1, B1)
    events = {Root(F(0)), Root(F(1))}
    for _, polys in models:
        events.update(_roots(polys[0]))
        if not any(polys[0]):
            for endpoint_coordinate in polys[1:5]:
                events.update(_roots(endpoint_coordinate))
    ordered = sorted(events)
    states = []
    for left, right in zip(ordered, ordered[1:]):
        sample = _between(left, right)
        second = _between(left, Root(sample))
        first_state = overlap(at(A0, A1, sample), at(B0, B1, sample))
        second_state = overlap(at(A0, A1, second), at(B0, B1, second))
        assert first_state == second_state, "independent event partition lost a body-state change"
        states.append((sample, first_state))
    initial = overlap(A0, B0)
    if initial > 0:
        return initial, "initial_overlap", None, (), (), tuple(states)
    for time in ordered:
        incidences, covers = _features(time, models, A0, B0, A1, B1)
        if incidences:
            assert all(state == -1 for t, state in states if time.relative(t) > 0), \
                "a separated start has no overlap before its first boundary incidence"
            if not time.k:
                assert overlap(at(A0, A1, time.h), at(B0, B1, time.h)) == 0
            return initial, "contact", time.certificate(), incidences, covers, tuple(states)
    assert initial == -1 and all(state == -1 for _, state in states)
    return initial, "no_contact", None, (), (), tuple(states)
