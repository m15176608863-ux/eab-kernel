"""Independent contact-allowed interval oracle for WO-T2a.

The imported M5a test oracle reconstructs event polynomials by rational
sampling/interpolation, isolates roots by its own Sturm implementation and
uses G0 integer-lifted winding, crossings and collinear-edge overlap. This helper
imports no production se2, algebraic, motion, exact, or construction code.
It explicitly calls first_contact, retains all of that oracle's probes,
and independently reconstructs their interval LEFT endpoints. A probe is
never reported as an entrance time. Root equality is exact polynomial gcd
plus isolating intervals, never a float or a production comparison.
"""
from fractions import Fraction as F

from m5a_independent_oracle import (
    Root, certificate_root, compare, event_polynomials,
    first_contact, normal_cone, overlap, ring_at, roots,
)


IDENTITY = (F(0), (F(0), F(0)), (F(0), F(0)))


def _exact_point(point):
    if len(point) != 2 or any(not isinstance(value, (int, F)) or isinstance(value, bool)
                              for value in point):
        raise ValueError("oracle coordinates must be exact integer or Fraction pairs")
    return tuple(F(value) for value in point)


def _exact_motion(spec):
    u = spec[0]
    if not isinstance(u, (int, F)) or isinstance(u, bool):
        raise ValueError("oracle turn parameter must be exact integer or Fraction")
    return F(u), _exact_point(spec[1]), _exact_point(spec[2])


def _side_cuts(p, q, mp, mq):
    """Event roots only; labels never share the mutable root container."""
    p = tuple(_exact_point(point) for point in p)
    q = tuple(_exact_point(point) for point in q)
    mp = _exact_motion(mp)
    mq = _exact_motion(mq)
    candidates = []
    for i in range(len(p)):
        for j in range(len(q)):
            f, g, h = event_polynomials(p[i], q[j], q[(j+1) % len(q)], mp, mq)
            if f != (0,):
                possible = roots(f)
            else:
                possible = roots(g)
                possible.extend(roots(h))
                possible.append(Root.rational(0))
                possible.append(Root.rational(1))
            for time in possible:
                if time.sign(g) >= 0 and time.sign(h) >= 0:
                    candidates.append(time)
    return candidates


def _compare_roots(a: Root, b: Root):
    """Compare copied certificates so refinement never mutates candidate roots."""
    first = Root(a.p, a.lo, a.hi)
    second = Root(b.p, b.lo, b.hi)
    return compare(first, second)


def _cuts(a, b, ma, mb):
    candidates = [Root.rational(0), Root.rational(1)]
    candidates.extend(_side_cuts(a, b, ma, mb))
    candidates.extend(_side_cuts(b, a, mb, ma))
    ordered = []
    for candidate in candidates:
        following = []
        placed = False
        for previous in ordered:
            comparison = _compare_roots(candidate, previous)
            if not placed and comparison < 0:
                following.append(candidate)
                placed = True
            if comparison == 0:
                placed = True
            following.append(previous)
        if not placed:
            following.append(candidate)
        ordered = following
    return ordered


def _side_labels(time, p, q, mp, mq, tag):
    incidences = set()
    features = set()
    for i in range(len(p)):
        for j in range(len(q)):
            f, g, h = event_polynomials(p[i], q[j], q[(j+1) % len(q)], mp, mq)
            if time.sign(f) or time.sign(g) < 0 or time.sign(h) < 0:
                continue
            label = (tag, i, j) if tag == "VE" else (tag, j, i)
            incidences.add(label)
            if normal_cone(time, p, i, q, j, mp, mq):
                features.add(label)
            for k, bound in ((j, g), ((j+1) % len(q), h)):
                if time.sign(bound) == 0:
                    vv = ("VV", i, k) if tag == "VE" else ("VV", k, i)
                    incidences.add(vv)
                    features.add(vv)
    return incidences, features


def _labels(time, a, b, ma, mb):
    incidences, features = _side_labels(time, a, b, ma, mb, "VE")
    other_incidences, other_features = _side_labels(time, b, a, mb, ma, "EV")
    incidences.update(other_incidences)
    features.update(other_features)
    return incidences, features


def first_penetration(a, b, ma, mb=IDENTITY):
    """Return independent tau_P and complete labels at that interval boundary."""
    contact = first_contact(a, b, ma, mb)
    end_state = overlap(ring_at(a, ma, F(1)), ring_at(b, mb, F(1)))
    answer = dict(initial_state=contact["initial"], status="FREE", root=None,
                  immediate=False, incidences=set(), features=set(),
                  touches_end=end_state == 0, end_state=end_state,
                  probes=contact["probes"], contact_status=contact["status"],
                  max_degree=contact["max_degree"], cuts=())
    if contact["initial"] == 1:
        time = Root.rational(0)
        incidences, features = _labels(time, a, b, ma, mb)
        answer.update(status="INITIAL_OVERLAP", root=time, immediate=True,
                      incidences=incidences, features=features)
        return answer
    positive = next((i for i, (_, state) in enumerate(contact["probes"])
                     if state == 1), None)
    if positive is None:
        assert end_state != 1, "closed endpoint overlap has an overlapping left neighborhood"
        return answer
    cuts = _cuts(a, b, ma, mb)
    assert len(cuts)-1 == len(contact["probes"]), "independent complete partition cardinality"
    for (left, right), (probe, _) in zip(zip(cuts, cuts[1:]), contact["probes"]):
        sample = Root.rational(probe)
        assert compare(left, sample) < 0 < compare(right, sample), "probe is strictly inside its own cell"
    time = cuts[positive]
    incidences, features = _labels(time, a, b, ma, mb)
    answer.update(status="PENETRATES", root=time,
                  immediate=compare(time, Root.rational(0)) == 0,
                  incidences=incidences, features=features, cuts=tuple(cuts))
    return answer


def time_matches(certificate, expected):
    """Check a public lossless certificate using only oracle-private roots."""
    return compare(certificate_root(certificate), expected) == 0

