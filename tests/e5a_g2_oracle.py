"""Independent same-input G2 audit, no production geometry/tool imports.

Hull faces are found by exhaustive rational support triples (not incremental
hull construction). Local labels use e5a_cover_oracle's independent Newell,
Gram and Gordan-ray formulas. Float normals/gaps are construction outputs;
gaps are independently rounded from rational squared distance by bit search,
not a production construction helper or a dot product of rounded vectors.
The enumeration window itself compares exact rational squared feature distance.
"""
from functools import lru_cache
from itertools import combinations
import math
from fractions import Fraction
from construction_oracle import sqrt_exact, unit_exact

from e5a_cover_oracle import q, sub, add, scale, dot, cross, model, arc, cover_labels


@lru_cache(maxsize=128)
def support_sets(raw):
    p = tuple(map(q, raw))
    result = set()
    for i, j, k in combinations(range(len(p)), 3):
        n = cross(sub(p[j], p[i]), sub(p[k], p[i]))
        if not any(n):
            continue
        values = [dot(n, sub(v, p[i])) for v in p]
        if all(x <= 0 for x in values) or all(x >= 0 for x in values):
            result.add(frozenset(a for a, x in enumerate(values) if x == 0))
    return frozenset(result)


def assert_exact_hull(P):
    expected = support_sets(tuple(P.verts))
    assert {frozenset(f) for f in P.faces} == expected
    assert len(P.faces) == len(expected)
    p = tuple(map(q, P.verts))
    for face in P.faces:
        n = cross(sub(p[face[1]], p[face[0]]), sub(p[face[2]], p[face[0]]))
        assert any(n)
        assert all(dot(n, sub(v, p[face[0]])) <= 0 for v in p)


def _unit(n):
    # Display normal only; direction and window branches retain the exact model.
    return unit_exact(n, allow_underflow=True)


def _distance_display(squared):
    """Independent bit search with exact midpoint rounding, never a production constructor."""
    return sqrt_exact(squared)


def construction(A, B, label, tol, *, distance_squared=False):
    kind, fa, fb = label
    a = model(tuple(A.verts), tuple(A.faces))
    b = model(tuple(B.verts), tuple(B.faces))
    if kind in ("FV", "EV3"):
        if distance_squared:
            return construction(B, A, ("VF" if kind == "FV" else "VE3", fb, fa), tol,
                                distance_squared=True)
        gap, n = construction(B, A, ("VF" if kind == "FV" else "VE3", fb, fa), tol)
        return gap, tuple(-x for x in n)
    if kind == "VF":
        n = b[2][fb[1]]
        difference = sub(a[0][fa[1]], b[0][b[1][fb[1]][0]])
    elif kind == "EE":
        da, db = sub(a[0][fa[2]], a[0][fa[1]]), sub(b[0][fb[2]], b[0][fb[1]])
        n = cross(db, da)
        if arc(b, fb[1:], n, tol) < 0 or arc(a, fa[1:], scale(n, -1), tol) < 0:
            n = scale(n, -1)
        aa, ab, bb = dot(da, da), dot(da, db), dot(db, db)
        w = sub(b[0][fb[1]], a[0][fa[1]])
        aw, bw = dot(da, w), dot(db, w)
        s, t = (bb*aw-ab*bw)/(aa*bb-ab*ab), (ab*aw-aa*bw)/(aa*bb-ab*ab)
        difference = sub(add(a[0][fa[1]], scale(da, s)), add(b[0][fb[1]], scale(db, t)))
    elif kind == "VE3":
        w, d = sub(a[0][fa[1]], b[0][fb[1]]), sub(b[0][fb[2]], b[0][fb[1]])
        difference = n = sub(w, scale(d, dot(w, d)/dot(d, d)))
    else:
        assert kind == "VV3"
        difference = n = sub(a[0][fa[1]], b[0][fb[1]])
        if not any(n):
            return Fraction(0) if distance_squared else (0., None)
    numerator = dot(n, difference)
    squared = numerator**2 / dot(n, n)
    if distance_squared:
        return squared
    normal = _unit(n)
    magnitude = _distance_display(squared)
    gap = -magnitude if numerator < 0 else magnitude
    return gap, normal


def assert_comparison(result, loaded, *, window, band, tol):
    """Check every row field, including actual exact-input disagreements."""
    blocks, entrances = loaded["blocks"], loaded["entrances"]
    for P in blocks.values():
        assert_exact_hull(P)
    expected_rows = {}
    legacy_pairs = {(e["bi"], e["bj"]) for e in entrances}
    for lo, hi in combinations(sorted(blocks), 2):
        pair = next((p for p in legacy_pairs if set(p) == {lo, hi}), (hi, lo))
        bi, bj = pair
        A, B = blocks[bi], blocks[bj]
        all_covers = []
        for label, strict in cover_labels(A, B, tol):
            gap, normal = construction(A, B, label, tol)
            if construction(A, B, label, tol, distance_squared=True) <= Fraction(max(window, band))**2:
                all_covers.append((label, strict, gap, normal))
        if not all_covers and pair not in legacy_pairs:
            continue
        legacy, detail, violations = set(), [], []
        for e in entrances:
            if (e["bi"], e["bj"]) != pair:
                continue
            assert e["etype"] == "np"
            refs = [(int(block), loaded["aliases"][int(block)].get(int(index), int(index)))
                    for block, index in e["refs"]]
            vb, vi = refs[0]
            hb = refs[1][0]
            tri = tuple(i for _, i in refs[1:])
            gi = next((k for k, f in enumerate(blocks[hb].faces) if set(tri) <= set(f)), None)
            if gi is None:
                n = len(blocks[hb].verts)
                x, y, z = sorted(tri)
                gi = -1-x*n*n-y*n-z
                violations.append(("legacy triangle not on exact hull face", hb, tri))
            legacy.add((vb, vi, gi))
            detail.append((vb, vi, tri, gi))
        mine, mine_detail, band_covers, penetration = set(), [], [], []
        count = reconciled = 0
        for (kind, fa, fb), strict, gap, normal in all_covers:
            record = (kind, fa, fb, round(gap, 12))
            if window < abs(gap) <= band:
                band_covers.append(record)
                if gap < -window:
                    penetration.append(record)
            if abs(gap) > window:
                continue
            count += 1
            if kind in ("VF", "FV"):
                key = (bi, fa[1], fb[1]) if kind == "VF" else (bj, fb[1], fa[1])
                mine.add(key)
                reconciled += 1
                mine_detail.append((kind, key, round(gap, 12), tuple(round(x, 12) for x in normal), strict))
            else:
                mine_detail.append((*record, strict))
                violations.append(("kernel cover kind not reconciled by this gate", *record))
        if reconciled != len(mine):
            violations.append(("kernel VF/FV covers collapse onto fewer keys", reconciled, len(mine)))
        expected_rows[pair] = dict(pair=pair, legacy=sorted(legacy), mine=sorted(mine),
            legacy_only=sorted(legacy-mine), mine_only=sorted(mine-legacy), legacy_detail=detail,
            mine_detail=mine_detail, n_covers=count, violations=violations, window=window,
            band=sorted(band_covers), penetration=sorted(penetration), band_limit=band,
            enumerated_window=max(window, band))
    assert result["case"] == loaded["case"] and result["step"] == loaded["step"]
    actual_rows = {tuple(r["pair"]): r for r in result["rows"]}
    assert len(actual_rows) == len(result["rows"])
    assert actual_rows.keys() == expected_rows.keys()
    for pair, expected in expected_rows.items():
        actual = dict(actual_rows[pair])
        for key in ("mine_detail", "violations"):
            actual[key] = sorted(actual[key], key=repr)
            expected[key] = sorted(expected[key], key=repr)
        assert actual == expected, (pair, {k: (actual[k], expected[k]) for k in expected if actual[k] != expected[k]})
