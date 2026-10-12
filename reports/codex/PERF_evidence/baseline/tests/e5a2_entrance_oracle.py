"""Independent integer SAT and exact continuous ray interval for convex inputs.

No production primitive is imported. All vertex triples and all pairs of chord
directions deliberately form a superset of the facet/edge SAT axes. Extra axes
cannot separate overlapping convex sets; the necessary axes are all present.
There is no triangulation, production hull, cover enumeration, noise band, or
time sampling in this oracle. Input coordinates are lifted to common integers.
"""
from fractions import Fraction as F
from itertools import combinations
from math import gcd, lcm


def _sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _canonical(v):
    divisor = gcd(*v)
    if not divisor:
        return None
    first = next(x for x in v if x)
    divisor = divisor if first > 0 else -divisor
    return tuple(x//divisor for x in v)


def _model(av, bv, start=(0, 0, 0), velocity=(0, 0, 0)):
    a = [tuple(F(c)+F(t) for c, t in zip(p, start)) for p in av]
    b = [tuple(map(F, p)) for p in bv]
    velocity = tuple(map(F, velocity))
    denominator = lcm(*(x.denominator for p in a+b+[velocity] for x in p))
    a, b, (velocity,) = [tuple(tuple(int(x*denominator) for x in p) for p in seq)
                         for seq in (a, b, [velocity])]
    axes = set()
    for vertices in (a, b):
        axes.update(_canonical(_cross(_sub(q, p), _sub(r, p)))
                    for p, q, r in combinations(vertices, 3))
    ad = {_canonical(_sub(q, p)) for p, q in combinations(a, 2)} - {None}
    bd = {_canonical(_sub(q, p)) for p, q in combinations(b, 2)} - {None}
    axes.update(_canonical(_cross(u, v)) for u in ad for v in bd)
    axes.discard(None)
    return a, b, velocity, axes


def convex_overlap(av, bv):
    a, b, _, axes = _model(av, bv)
    boundary = False
    for n in axes:
        x, y = [_dot(n, p) for p in a], [_dot(n, p) for p in b]
        separation = max(min(x)-max(y), min(y)-max(x))
        if separation > 0:
            return -1
        boundary |= separation == 0
    return 0 if boundary else 1


def assert_supporting_surface(vertices, faces):
    """Check the convex-oracle precondition on supplied faces, exactly."""
    v = [tuple(map(F, p)) for p in vertices]
    denominator = lcm(*(x.denominator for p in v for x in p))
    v = [tuple(int(x*denominator) for x in p) for p in v]
    for face in faces:
        a, b, c = (v[i] for i in face[:3])
        n = _cross(_sub(b, a), _sub(c, a))
        assert any(n), "oracle requires nondegenerate supporting faces"
        assert all(_dot(n, _sub(v[i], a)) == 0 for i in face)
        assert all(_dot(n, _sub(p, a)) <= 0 for p in v), "input surface is not its convex hull"


def convex_ray_interval(av, bv, start, velocity, t_max):
    """The complete closed interval of exact convex intersection on [0,t_max]."""
    a, b, d, axes = _model(av, bv, start, velocity)
    lower, upper = F(0), F(t_max)
    for n in axes:
        x, y = [_dot(n, p) for p in a], [_dot(n, p) for p in b]
        lo, hi, speed = min(y)-max(x), max(y)-min(x), _dot(n, d)
        if not speed:
            if lo > 0 or hi < 0:
                return None
            continue
        p, q = F(lo, speed), F(hi, speed)
        lower, upper = max(lower, min(p, q)), min(upper, max(p, q))
        if lower > upper:
            return None
    return lower, upper
