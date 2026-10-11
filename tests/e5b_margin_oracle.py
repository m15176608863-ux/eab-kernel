"""Independent exact surface-cover values for the E5b margin migrations.

The oracle uses test-only projected ear cutting, cyclic Newell sums, Gram
coefficients and Gordan cones. No production geometry, predicate, witness,
triangulator or distance primitive participates in the expected answers.
"""
from fractions import Fraction as F
from functools import lru_cache
from types import SimpleNamespace

import e5a_cover_oracle as covers
from e5b_frozen_oracle import surface


def cover_squared(A, B):
    return dict(_cover_squared(tuple(A.verts), tuple(A.faces), tuple(B.verts), tuple(B.faces)))


@lru_cache(maxsize=512)
def _cover_squared(av, af, bv, bf):
    a, a_labels = surface(SimpleNamespace(verts=av, faces=af))
    b, b_labels = surface(SimpleNamespace(verts=bv, faces=bf))
    am, bm = covers._model(a), covers._model(b)
    answer = []
    for (kind, fa, fb), _ in covers.cover_labels(a, b):
        if kind == "VF":
            n = bm[2][fb[1]]
            w = covers.sub(am[0][fa[1]], bm[0][bm[1][fb[1]][0]])
            value = covers.dot(n, w)**2 / covers.dot(n, n)
        elif kind == "FV":
            n = am[2][fa[1]]
            w = covers.sub(bm[0][fb[1]], am[0][am[1][fa[1]][0]])
            value = covers.dot(n, w)**2 / covers.dot(n, n)
        elif kind == "EE":
            u = covers.sub(am[0][fa[2]], am[0][fa[1]])
            v = covers.sub(bm[0][fb[2]], bm[0][fb[1]])
            n = covers.cross(u, v)
            w = covers.sub(am[0][fa[1]], bm[0][fb[1]])
            value = covers.dot(n, w)**2 / covers.dot(n, n)
        elif kind in ("VE3", "EV3"):
            vertex, edge, vm, em = ((fa, fb, am, bm) if kind == "VE3" else (fb, fa, bm, am))
            u = covers.sub(em[0][edge[2]], em[0][edge[1]])
            w = covers.sub(vm[0][vertex[1]], em[0][edge[1]])
            value = covers.dot(w, w) - covers.dot(w, u)**2 / covers.dot(u, u)
        else:
            assert kind == "VV3"
            w = covers.sub(am[0][fa[1]], bm[0][fb[1]])
            value = covers.dot(w, w)
        if fa[0] == "face":
            fa = a_labels[fa[1]]
        if fb[0] == "face":
            fb = b_labels[fb[1]]
        answer.append(((kind, fa, fb), value))
    return tuple(answer)


def check_exact_margin(A, B, delta, *, state, minimum_squared=None):
    """Run default APIs against the independently computed rational answers.

    Only actual API calls below import production code; all expected geometry
    is generated above or supplied by the independent tetrahedral SAT oracle.
    Float distances are construction outputs (four ulps); labels, inclusion,
    closed state and both neighboring binary64 delta decisions are exact.
    """
    import math
    import eab.margin as production
    distance, label = production.body_distance(A, B)
    actual = production.margin_contacts(A, B, delta=delta)
    if state == 1:
        assert (distance, label) == (0.0, (production.PENETRATING,)), "default-exact penetration"
        assert len(actual) == 1 and actual[0].label == (production.PENETRATING,)
        assert actual[0].closed and actual[0].distance == 0
        assert production.inflated_membership(A, B, delta=0) == production.INSIDE
        assert production.inflated_membership(A, B, delta=delta) == production.INSIDE
        return
    expected = cover_squared(A, B)
    nearest = min(expected.values())
    if minimum_squared is not None:
        assert nearest == minimum_squared, "independent cover minimum vs independent all-surface distance"
    if state == 0:
        assert nearest == 0, "exact surface contact has a zero witness"
    assert label in {lab for lab, d2 in expected.items() if d2 == nearest}, "default-exact surface nearest label"
    want_distance = math.sqrt(float(nearest))
    assert abs(distance - want_distance) <= 4 * math.ulp(want_distance), "default-exact distance construction"
    selected = {lab: d2 for lab, d2 in expected.items() if delta >= 0 and d2 <= F(delta)**2}
    current = {m.label: m for m in actual}
    assert len(current) == len(actual), "default-exact no duplicate labels"
    assert current.keys() == selected.keys(), "default-exact complete surface label set"
    for lab, d2 in selected.items():
        want = math.sqrt(float(d2))
        assert abs(current[lab].distance-want) <= 4*math.ulp(want), "default-exact cover distance"
        assert current[lab].closed == (d2 <= F(delta)**2), "default-exact closed state"
    # Retain original delta and additionally straddle the exact boundary with
    # adjacent binary64 values. No distance-rounding band decides these states.
    for probe in (delta, 0.0, math.nextafter(want_distance, 0.0), want_distance,
                  math.nextafter(want_distance, math.inf)):
        comparison = F(probe)**2
        want = (production.INSIDE if nearest < comparison else
                production.OUTSIDE if nearest > comparison else production.ON_BOUNDARY)
        assert production.inflated_membership(A, B, delta=probe) == want, "default-exact delta classification"
