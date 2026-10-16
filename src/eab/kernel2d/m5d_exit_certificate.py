"""C1 sufficient certificate for a unique global shortest exit edge.

Proof and finite-domain qualifications: docs/m5d_c1_theory.md. Exact rational
input/output only; no binary64 predicate, tolerance, square root or sibling
dependency. UNPROVED never means actual instability. Gate:
test_c1_threshold_edge_nonrigid_perturbations_match_independent_hull_oracle.
"""
from fractions import Fraction as F


def _exact(value):
    if isinstance(value, bool) or not isinstance(value, (int, F)):
        raise ValueError("C1 requires exact rationals")
    return F(value)


def _ring(points):
    result = tuple(tuple(_exact(v) for v in p) for p in points)
    if len(result) < 3 or any(len(p) != 2 for p in result):
        raise ValueError("C1 requires rings of at least three 2D points")
    return result


def _sub(p, q):
    return p[0]-q[0], p[1]-q[1]


def _cross(p, q):
    return p[0]*q[1]-p[1]*q[0]


def _l1(p):
    return abs(p[0])+abs(p[1])


def _convex_guard(ring, radius):
    margins = []
    for i, p in enumerate(ring):
        end = (i+1) % len(ring)
        u = _sub(ring[end], p)
        for k, q in enumerate(ring):
            if k in (i, end):
                continue
            w = _sub(q, p)
            nominal = _cross(u, w)
            if nominal <= 0:
                return "RING_NOT_STRICTLY_CONVEX", nominal
            margins.append(nominal-2*radius*(_l1(u)+_l1(w))-8*radius*radius)
    margin = min(margins)
    return ("TUBE_CONVEXITY_UNPROVED" if margin <= 0 else None), margin


def _cross_guard(a, b, ra, rb):
    margins = []
    for p, q in zip(a, a[1:]+a[:1]):
        u = _sub(q, p)
        for s, t in zip(b, b[1:]+b[:1]):
            v = _sub(t, s)
            margins.append(abs(_cross(u, v))-2*ra*_l1(v)-2*rb*_l1(u)-8*ra*rb)
    return min(margins)


def _boundary(a, b):
    """All support edges of B-A; convexity/nonparallel guards precede this."""
    result = []
    for j, p in enumerate(b):
        q = b[(j+1) % len(b)]
        u = _sub(q, p)
        i = 0
        for k in range(1, len(a)):
            if _cross(u, a[k]) > _cross(u, a[i]):
                i = k
        result.append((("VE", i, j), _sub(p, a[i]), _sub(q, a[i])))
    for i, p in enumerate(a):
        q = a[(i+1) % len(a)]
        u = _sub(q, p)
        j = 0
        for k in range(1, len(b)):
            if _cross(u, b[k]) > _cross(u, b[j]):
                j = k
        result.append((("EV", i, j), _sub(b[j], p), _sub(b[j], q)))
    return tuple(result)


def _distance2(p, q, x):
    u, w = _sub(q, p), _sub(x, p)
    length = u[0]*u[0]+u[1]*u[1]
    dot = u[0]*w[0]+u[1]*w[1]
    parameter = min(F(1), max(F(0), dot/length))
    offset = p[0]+parameter*u[0]-x[0], p[1]+parameter*u[1]-x[1]
    return offset[0]*offset[0]+offset[1]*offset[1]


def _rank_guard(q, others, radius):
    if q <= 2*radius*radius:
        return "INTERIOR_PERSISTENCE_UNPROVED"
    for competitor in others:
        h = competitor-q-8*radius*radius
        if h <= 0 or h*h <= 32*q*radius*radius:
            return "EXIT_ORDER_UNPROVED"
    return None


def exit_order_certificate(A, B, radius_a=0, radius_b=0, x=(0, 0)):
    """Certify a fixed query's unique exit label for all vertex-box choices.

    Returns a reasoned UNPROVED record or CERTIFIED_UNIQUE_EXIT with its exact
    label, all nominal squared distances, and proof margins. It deliberately
    declines concavity, parallel edges and ties, including at zero radius.
    """
    a, b = _ring(A), _ring(B)
    ra, rb = _exact(radius_a), _exact(radius_b)
    point = tuple(_exact(v) for v in x)
    if min(ra, rb) < 0 or len(point) != 2:
        raise ValueError("C1 requires nonnegative radii and a 2D query")
    def refused(reason, **details):
        details["status"] = "UNPROVED"
        details["reason"] = reason
        return details
    convex = []
    for owner, ring, radius in (("A", a, ra), ("B", b, rb)):
        reason, margin = _convex_guard(ring, radius)
        if reason:
            return refused(reason, ring=owner, margin=margin)
        convex.append(margin)
    cross_margin = _cross_guard(a, b, ra, rb)
    if cross_margin <= 0:
        return refused("CROSS_NORMAL_ORDER_UNPROVED", margin=cross_margin)
    edges = _boundary(a, b)
    if any(_cross(_sub(q, p), _sub(point, p)) <= 0 for _, p, q in edges):
        return refused("QUERY_NOT_STRICTLY_INTERIOR")
    distances = tuple((label, _distance2(p, q, point)) for label, p, q in edges)
    best = min(value for _, value in distances)
    labels = tuple(label for label, value in distances if value == best)
    if len(labels) != 1:
        return refused("NOMINAL_EXIT_TIE", labels=labels, distance2=best)
    label = labels[0]
    reason = _rank_guard(best, tuple(value for key, value in distances if key != label), ra+rb)
    if reason:
        return refused(reason, label=label, distance2=best)
    return dict(status="CERTIFIED_UNIQUE_EXIT", label=label, distance2=best,
                distances2=distances, radius_sum=ra+rb,
                convex_margins=tuple(convex), cross_margin=cross_margin)
