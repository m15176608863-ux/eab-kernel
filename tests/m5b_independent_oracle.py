"""Independent P2 oracle: complex-product motion, seven samples, Sturm/G0.

Imports: fractions.Fraction; polynomial/root primitives from the independent
m5a_independent_oracle (fractions, functools, g0_oracle only). No production
DDA, SE2, algebraic, motion, exact or construction primitive is used. The
same independent root code is applied to degree six; coordinate formulas and
normal cones below include independently evaluated symmetric strain.
"""
from fractions import Fraction as F
from m5a_independent_oracle import (
    Root, certificate_root, compare, determinant, difference, distinct, dot,
    interpolate, overlap, roots, value,
)


def point_at(p, spec, s):
    """Cayley rotation evaluated as two complex products, not production R."""
    u, d, c, strain = spec
    w = F(u)*s
    x, y = difference(p, c)
    # (x+i y)*(1+i w)*(1+i w)/(1+w²).
    first = x-w*y, y+w*x
    second = first[0]-w*first[1], first[1]+w*first[0]
    return tuple(c[k]+s*d[k]+second[k]/(1+w*w)
                 +s*(strain[k][0]*x+strain[k][1]*y) for k in (0, 1))


def ring_at(ring, spec, s):
    return tuple(point_at(p, spec, s) for p in ring)


def event_polynomials(p, q, r, mp, mq):
    def sample(s):
        vertex = point_at(p, mp, s)
        start, end = point_at(q, mq, s), point_at(r, mq, s)
        edge, offset = difference(end, start), difference(vertex, start)
        denominator = (1+(s*mp[0])**2)*(1+(s*mq[0])**2)
        projection = dot(edge, offset)
        return (denominator*determinant(edge, offset), denominator*projection,
                denominator*(dot(edge, edge)-projection))
    values = [sample(F(k)) for k in range(7)]
    answer = tuple(interpolate([v[k] for v in values]) for k in range(3))
    for s in (F(1, 7), F(13, 7)):
        assert tuple(value(p, s) for p in answer) == sample(s), "independent degree-six interpolation identity"
    return answer


def normal_cone(time, ring, i, other, j, own_spec, other_spec):
    before = difference(ring[i], ring[i-1])
    after = difference(ring[(i+1) % len(ring)], ring[i])
    turn = determinant(before, after)
    if turn < 0 or (turn == 0 and dot(before, after) <= 0):
        return False

    def sample(s):
        vertices = [point_at(ring[k % len(ring)], own_spec, s) for k in (i-1, i, i+1)]
        edge = difference(point_at(other[(j+1) % len(other)], other_spec, s),
                          point_at(other[j], other_spec, s))
        u, v = difference(vertices[1], vertices[0]), difference(vertices[2], vertices[1])
        den = (1+(s*own_spec[0])**2)*(1+(s*other_spec[0])**2)
        return den*determinant(edge, u), den*determinant(v, edge), den*dot(edge, u)
    values = [sample(F(k)) for k in range(7)]
    signs = [time.sign(interpolate([v[k] for v in values])) for k in range(3)]
    return signs[0] >= 0 and signs[1] >= 0 and (turn != 0 or signs[2] < 0)


def first_contact(A, B, ma, mb):
    """Independent complete event partition plus G0 rational interval probes."""
    inputs = tuple(x for ring in (A, B) for point in ring for x in point)
    inputs += tuple(x for spec in (ma, mb) for x in (spec[0], *spec[1], *spec[2], *spec[3][0], *spec[3][1]))
    assert all(isinstance(x, (int, F)) and not isinstance(x, bool) for x in inputs), \
        "oracle inputs must be exact int/Fraction values"
    state = overlap(A, B)
    if state == 1:
        return {"initial": state, "status": "initial_overlap", "root": None,
                "incidences": set(), "features": set(), "probes": [], "max_degree": 0}
    events, candidates = [], []
    for P, Q, mp, mq, tag in ((A, B, ma, mb, "VE"), (B, A, mb, ma, "EV")):
        for i, vertex in enumerate(P):
            for j, start in enumerate(Q):
                polys = event_polynomials(vertex, start, Q[(j+1) % len(Q)], mp, mq)
                orientation, g, h = polys
                event = (tag, i, j, polys)
                events.append(event)
                possible = roots(orientation) if orientation != (0,) else distinct(
                    roots(g)+roots(h)+[Root.rational(0), Root.rational(1)])
                candidates.extend(t for t in possible if t.sign(g) >= 0 and t.sign(h) >= 0)
    times = distinct(candidates)
    first = Root.rational(0) if state == 0 else (times[0] if times else None)
    labels, covers = set(), set()
    if first is not None:
        for tag, i, j, (f, g, h) in events:
            if first.sign(f) or first.sign(g) < 0 or first.sign(h) < 0:
                continue
            label = (tag, i, j) if tag == "VE" else (tag, j, i)
            labels.add(label)
            P, Q, mp, mq = (A, B, ma, mb) if tag == "VE" else (B, A, mb, ma)
            if normal_cone(first, P, i, Q, j, mp, mq):
                covers.add(label)
            for k, bound in ((j, g), ((j+1) % len(Q), h)):
                if first.sign(bound) == 0:
                    vv = ("VV", i, k) if tag == "VE" else ("VV", k, i)
                    labels.add(vv)
                    covers.add(vv)
    # Every open interval between valid VE roots has constant body state.
    # Independently classify one rational point in *every* such interval.
    cuts = distinct([Root.rational(0)]+times+[Root.rational(1)])
    probes = []
    for left, right in zip(cuts, cuts[1:]):
        while left.hi >= right.lo:
            left.refine()
            right.refine()
        s = (left.hi+right.lo)/2
        probes.append((s, overlap(ring_at(A, ma, s), ring_at(B, mb, s))))
    if state == -1:
        for s, body_state in probes:
            if first is None or first.sign((-s, 1)) > 0:
                assert body_state == -1, "independent interval partition excludes earlier contact"
    return {"initial": state, "status": "contact" if first is not None else "no_contact",
            "root": first, "incidences": labels, "features": covers, "probes": probes,
            "max_degree": max(len(p)-1 for _, _, _, polys in events for p in polys)}


