"""R13 event-output oracle: Fraction SAT and independent midpoint certificates.

No production geometric primitive, constructor, predicate, or event helper is
used. The shared reference midpoint checker imports no production primitives.
"""
from fractions import Fraction as F

from construction_oracle import assert_sqrt_rounding


def assert_scalar_binding(actual, exact, message="event output midpoint binding"):
    exact = F(exact)
    assert (actual > 0) == (exact > 0), message
    assert (actual < 0) == (exact < 0), message
    assert_sqrt_rounding(abs(actual), exact*exact, message)


def assert_event_binding(time, exact_time, position, start, velocity, oracle_time):
    assert exact_time == oracle_time, "independent earliest event time"
    assert_scalar_binding(time, oracle_time, "event time midpoint binding")
    expected = tuple(F(a)+oracle_time*F(d) for a, d in zip(start, velocity))
    assert len(position) == len(expected), "event position dimensionality"
    for actual, exact in zip(position, expected):
        assert_scalar_binding(actual, exact, "event position midpoint binding")


def convex_ray_interval_2d(a, b, start, velocity, upper):
    """Independent exact temporal SAT over all supplied convex edge normals."""
    a = [tuple(F(c) for c in p) for p in a]
    b = [tuple(F(c) for c in p) for p in b]
    start, velocity = tuple(F(c) for c in start), tuple(F(c) for c in velocity)
    a = [(x+start[0], y+start[1]) for x, y in a]
    lower, upper = F(0), F(upper)
    for polygon in (a, b):
        for p, q in zip(polygon, polygon[1:]+polygon[:1]):
            nx, ny = p[1]-q[1], q[0]-p[0]
            ap = [nx*x+ny*y for x, y in a]
            bp = [nx*x+ny*y for x, y in b]
            left, right = min(bp)-max(ap), max(bp)-min(ap)
            speed = nx*velocity[0]+ny*velocity[1]
            if not speed:
                if left > 0 or right < 0:
                    return None
                continue
            roots = (left/speed, right/speed)
            lower, upper = max(lower, min(roots)), min(upper, max(roots))
            if lower > upper:
                return None
    return lower, upper
