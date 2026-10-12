"""M4a offline T1-style reconciliation; no executable or sibling import.

The oracle below uses its own Fraction edge algebra and linear halfspaces,
not the production cover/cone/projection/normal primitives. It validates
local-cover eligibility, not the physical correctness of legacy selection.
Legacy geometry is reconstructed at detection time; df22 o3 is a different
observable (post-solve), and first-step contacts o3/o4 are uninitialised.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from fractions import Fraction as F
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.adapters.bdda2d import detect_step, load_window
from eab.construction import scalar_rational
from eab.readers import bdda_df
from eab.readers.bdda_geom import load_step_geometries
from eab.oracle_construction import sqrt_exact, scalar_exact

CLASSIFICATIONS = frozenset({
    "MATCH", "EXACT_LOCAL_COVER_NOT_SELECTED", "ANGULAR_WINDOW_COVER_NOT_SELECTED",
    "VV_IDENTITY_MATCH_TWO_REFERENCE_NORMAL",
    "LEGACY_DUPLICATE_PRIMARY_REFERENCE", "LEGACY_OUTSIDE_DISTANCE_WINDOW",
    "LEGACY_OUTSIDE_FINITE_EDGE_WINDOW", "LEGACY_OUTSIDE_LOCAL_CONE_WINDOW",
    "LEGACY_VV_REFERENCE_WITHOUT_COMMON_OPEN_CONE", "LEGACY_VV_DIRECTION_OUTSIDE_OPEN_CONE",
})

def sub(a, b):
    return (a[0]-b[0], a[1]-b[1])


def dot(a, b):
    return a[0]*b[0]+a[1]*b[1]


def det(a, b):
    return a[0]*b[1]-a[1]*b[0]


def point(p):
    return tuple(map(F, p))


def positive_unit_sum(a, a2, b, b2):
    """Sign of a/sqrt(a2)+b/sqrt(b2), exact squared comparison."""
    if a >= 0 and b >= 0:
        return a > 0 or b > 0
    if a <= 0 and b <= 0:
        return False
    cmp = a*a*b2-b*b*a2
    return cmp > 0 if a > 0 else cmp < 0


def support(poly, i, inward, sine=0):
    """Neighbour halfspaces plus nonreflex topology; explicit angle policy."""
    p, prev, nxt = (point(poly[k % len(poly)]) for k in (i, i-1, i+1))
    incoming, outgoing = sub(p, prev), sub(nxt, p)
    aa, bb, nn = dot(incoming, incoming), dot(outgoing, outgoing), dot(inward, inward)
    assert aa and bb and nn, "oracle: degenerate incident edge/normal"
    turn, parallel = det(incoming, outgoing), dot(incoming, outgoing)
    w2 = F(sine)**2
    convex = turn >= 0 and (turn > 0 or parallel > 0)
    expanded = turn < 0 and parallel > 0 and turn*turn <= w2*aa*bb
    if not (convex or expanded):
        return False
    h = (dot(sub(prev, p), inward), dot(sub(nxt, p), inward))
    if not all(v >= 0 or v*v <= w2*length*nn for v, length in zip(h, (aa, bb))):
        return False
    # Exclude the antipodal branch when a large window touches both sides.
    na, nb = (-incoming[1], incoming[0]), (-outgoing[1], outgoing[0])
    return positive_unit_sum(dot(na, inward), aa, dot(nb, inward), bb)


def record_key(r, sg):
    assert r.feature_a is not None and r.feature_b is not None, "unresolved feature"
    fa, fb = r.feature_a, r.feature_b
    assert fa.block == r.block_a and fb.block == r.block_b, "feature block mismatch"
    assert fa.kind == "vertex" and fa.index in sg.blocks[fa.block].vidx, "vertex identity"
    if r.cover.value == "VV":
        assert fb.kind == "vertex" and fb.index in sg.blocks[fb.block].vidx, "VV identity"
        return ("VV", *sorted((fa.index, fb.index)))
    assert r.cover.value == "VE" and fb.kind == "edge", "unexpected cover type"
    vs = sg.blocks[fb.block].vidx
    assert fb.index in vs, "edge identity"
    j = vs.index(fb.index)
    return ("VE", fa.index, *sorted((vs[j], vs[(j+1) % len(vs)])))


def geometry(key, sg):
    pos, owners = sg.vertex_pos(), sg.vertex_block()
    kind, v, q, *end = key
    A, B = sg.blocks[owners[v]], sg.blocks[owners[q]]
    assert A.block != B.block, "self contact"
    p, b = point(pos[v]), point(pos[q])
    if kind == "VV":
        n = sub(p, b)
        return dict(A=A, B=B, ai=A.vidx.index(v), bi=B.vidx.index(q),
                    p=p, q=b, n=n, l2=dot(n, n), g=dot(n, n), t=None)
    assert owners[end[0]] == B.block, "edge crosses blocks"
    j, k = B.vidx.index(q), B.vidx.index(end[0])
    assert (j+1) % len(B.vidx) == k or (k+1) % len(B.vidx) == j, "edge not adjacent"
    if (j+1) % len(B.vidx) != k:
        j, k = k, j
    b, c = point(B.poly[j]), point(B.poly[k])
    e, delta = sub(c, b), sub(p, b)
    n = (e[1], -e[0])
    l2 = dot(e, e)
    assert l2 > 0, "zero edge"
    return dict(A=A, B=B, ai=A.vidx.index(v), bi=j, p=p, q=b,
                n=n, l2=l2, g=dot(n, delta), t=dot(e, delta))


def vv_cones_intersect(g):
    """Strict feasibility of four 2-D halfspaces, by boundary-ray pairs."""
    constraints = []
    for block, idx, sign in ((g["A"], g["ai"], 1), (g["B"], g["bi"], -1)):
        p = point(block.poly[idx])
        u, v = (sub(point(block.poly[k % len(block.poly)]), p) for k in (idx-1, idx+1))
        if det(u, v) >= 0:
            return False
        constraints.extend((tuple(sign*x for x in u), tuple(sign*x for x in v)))
    rays = [(sign*v[1], -sign*v[0]) for v in constraints for sign in (-1, 1)]
    feasible = [r for r in rays if all(dot(v, r) >= 0 for v in constraints)]
    return any(all(dot(v, (r[0]+s[0], r[1]+s[1])) > 0 for v in constraints)
               for r in feasible for s in feasible)


def eligibility(key, sg, window, *, strict_window=False):
    """Return the first failed exact criterion; None means eligible."""
    g = geometry(key, sg)
    d0, seg, sine = F(window.d0), F(window.seg_tol), (0 if strict_window else window.cone_tol)
    if key[0] == "VE":
        if g["g"]**2 > d0*d0*g["l2"]:
            return "OUTSIDE_DISTANCE_WINDOW"
        t, ll = g["t"], g["l2"]
        if (t < 0 and t*t > seg*seg*ll) or (t > ll and (t-ll)**2 > seg*seg*ll):
            return "OUTSIDE_FINITE_EDGE_WINDOW"
        if not support(g["A"].poly, g["ai"], g["n"], sine):
            return "OUTSIDE_LOCAL_CONE_WINDOW"
        return None
    if g["l2"] > d0*d0:
        return "OUTSIDE_DISTANCE_WINDOW"
    if not vv_cones_intersect(g):
        return "VV_REFERENCE_WITHOUT_COMMON_OPEN_CONE"
    if not g["l2"]:
        return None
    direction = g["n"]
    # VV strict activity excludes cone boundaries, unless expanded by h1.
    strict = True
    for block, idx, sign in ((g["A"], g["ai"], 1), (g["B"], g["bi"], -1)):
        p = point(block.poly[idx])
        ds = tuple(sign*x for x in direction)
        strict &= all(dot(sub(point(block.poly[k % len(block.poly)]), p), ds) > 0
                      for k in (idx-1, idx+1))
    if strict:
        return None
    if sine > 0 and support(g["A"].poly, g["ai"], direction, sine) and support(
            g["B"].poly, g["bi"], tuple(-x for x in direction), sine):
        return None
    return "VV_DIRECTION_OUTSIDE_OPEN_CONE"


def check_metric(record, key, sg, window):
    """Compare type, signed gap and directed normal against raw exact edges."""
    g = geometry(key, sg)
    assert record.gap is not None, "missing detection gap"
    expected = (sqrt_exact(g["l2"]) if key[0] == "VV" else
                ((g["g"] > 0)-(g["g"] < 0))*sqrt_exact(g["g"]**2/g["l2"]))
    assert abs(F(record.gap)-F(expected)) <= F(window.fit_tol), "gap outside fit precision"
    if not g["l2"]:
        assert record.normal is None, "coincident VV is set-valued"
        return
    assert record.normal is not None, "missing normal"
    n = point(record.normal)
    # VV key is sorted; account for the record's directed block order.
    sign = -1 if key[0] == "VV" and record.feature_a.index != key[1] else 1
    raw = tuple(sign*x for x in g["n"])
    assert dot(n, raw) > 0, "normal direction reversed"
    assert det(n, raw)**2 <= F(1e-12)**2*dot(n, n)*dot(raw, raw), "normal not parallel"
    assert abs(dot(n, n)-1) <= F(1e-12), "normal not unit"


def classify_extra(key, sg, window):
    """An unmatched cover is accepted only with an independent eligibility proof.

    No claim that legacy ought to select all valid local covers: df05/df06
    deliberately choose an ordered subset. Physical equivalence is unresolved.
    """
    failure = eligibility(key, sg, window)
    if failure is not None:
        return "UNCLASSIFIED_EAB_"+failure
    exact_failure = eligibility(key, sg, window, strict_window=True)
    return "EXACT_LOCAL_COVER_NOT_SELECTED" if exact_failure is None else "ANGULAR_WINDOW_COVER_NOT_SELECTED"


def classify_missing(key, sg, window):
    failure = eligibility(key, sg, window)
    if failure is None:
        return "UNCLASSIFIED_EAB_MISSING_VALID_COVER"
    return "LEGACY_"+failure


def compare_step(sg, window, legacy, eab=None):
    eab = detect_step(sg, window) if eab is None else eab
    ld, ed, duplicates = {}, {}, []
    for records, target in ((legacy, ld), (eab, ed)):
        for record in records:
            key = record_key(record, sg)
            if key in target:
                assert target is ld, "duplicate eab normalized contact"
                first = target[key]
                assert all(first.extra.get(k) == record.extra.get(k) for k in
                           ("raw_p1", "raw_p2", "p3")), "unclassified normalized alias duplicate"
                assert any(first.extra.get(k) != record.extra.get(k) for k in
                           ("m4", "m5", "m6")), "unclassified identical secondary duplicate"
                duplicates.append(dict(key=key, category="LEGACY_DUPLICATE_PRIMARY_REFERENCE",
                                       legacy_contact=record.contact_index,
                                       first_contact=first.contact_index))
                continue
            target[key] = record
    counts = Counter({"LEGACY_DUPLICATE_PRIMARY_REFERENCE": len(duplicates)}) if duplicates else Counter()
    differences = list(duplicates)
    observed_metrics = 0
    for record in legacy:
        key = record_key(record, sg)
        if key[0] == "VE" and "df18_cs1" in record.extra:
            s = record.extra["df18_s"]
            assert len(s) >= 2, "legacy df18 normal missing"
            check_metric(replace(record, gap=scalar_rational(record.extra["df18_cs1"], quantity="M4 legacy cs1"), normal=tuple(s[:2])),
                         key, sg, window)
            observed_metrics += 1
    for key, record in ed.items():
        check_metric(record, key, sg, window)
        assert eligibility(key, sg, window) is None, ("invalid eab cover", key)
    for key in sorted(ld.keys() | ed.keys()):
        if key in ld and key in ed:
            category = "MATCH" if key[0] == "VE" else "VV_IDENTITY_MATCH_TWO_REFERENCE_NORMAL"
        elif key in ed:
            category = classify_extra(key, sg, window)
        else:
            category = classify_missing(key, sg, window)
        counts[category] += 1
        if category != "MATCH":
            differences.append(dict(key=key, category=category,
                                    legacy_contact=ld[key].contact_index if key in ld else None))
    return dict(step=sg.step, legacy=len(legacy), legacy_unique=len(ld), eab=len(ed), counts=dict(sorted(counts.items())),
                legacy_ve_metrics_observed=observed_metrics,
                legacy_metrics_geometry_only=len(legacy)-observed_metrics,
                differences=differences, window=dict(d0=window.d0, h1=window.h1_degrees,
                seg_tol=window.seg_tol, fit_tol=window.fit_tol))


def compare_fixture(path, *, expected_steps=3):
    geoms = load_step_geometries(path / "bdda_debug_verts.csv")
    legacy = bdda_df.load_records(path)
    wanted = set(range(1, expected_steps+1))
    assert set(geoms) == wanted, "missing/extra geometry step"
    assert {r.step for r in legacy} == wanted, "missing/extra legacy contact step"
    params = (path / "bdda_debug_detparams.csv").read_text(encoding="utf-8").splitlines()
    param_steps = [int(line.split(",")[0]) for line in params[1:] if line]
    assert len(param_steps) == len(wanted) and set(param_steps) == wanted, "missing/extra parameter step"
    rows = []
    for step, sg in sorted(geoms.items()):
        rows.append(compare_step(sg, load_window(path, step), [r for r in legacy if r.step == step]))
    return rows


def assert_classified(rows):
    assert rows, "no detection steps compared"
    bad = [(r["step"], c, n) for r in rows for c, n in r["counts"].items() if c not in CLASSIFICATIONS]
    assert not bad, ("unclassified differences", bad)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fixtures", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = {path.name: compare_fixture(path) for path in args.fixtures}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    for name, rows in result.items():
        for row in rows:
            print(name, row["step"], row["counts"])
        assert_classified(rows)


if __name__ == "__main__":
    main()
