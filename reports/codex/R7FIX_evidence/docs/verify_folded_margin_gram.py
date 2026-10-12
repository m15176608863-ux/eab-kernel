"""Independent review of the 16 failed legacy margin-distance grid cells.

Only input generation and the observed API calls come from the test module.
For a selected contact, this file derives the distance from raw coordinates:
exact projected-convexity proof -> fixed first-ear quad triangulation -> own
Fraction Gram/barycentric projection or clamped segment minima -> Decimal sqrt.
No production or pre-existing test geometry helper supplies the oracle distance.
The old test witness_distance is called solely to reproduce the OLD expectation,
not to certify the corrected distance. This audits construction values, not
complete enumeration (the unchanged label/count gate handles that separately).
"""
from decimal import Decimal, localcontext
from fractions import Fraction as F
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / name) for name in ("tests", "src", "tools")]
import test_invariance_interlock as T
import e5a_cover_oracle as OLD


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def segment_squared(p, a, b):
    u, v = sub(b, a), sub(p, a)
    t = max(F(0), min(F(1), dot(u, v)/dot(u, u)))
    d = sub(v, tuple(t*x for x in u))
    return dot(d, d)


def triangle_squared(p, a, b, c):
    """Constrained quadratic minimum on one exact triangle, with edge fallback."""
    u, v, w = sub(b, a), sub(c, a), sub(p, a)
    uu, uv, vv = dot(u, u), dot(u, v), dot(v, v)
    determinant = uu*vv-uv*uv
    assert determinant > 0
    s = (dot(w, u)*vv-dot(w, v)*uv)/determinant
    t = (dot(w, v)*uu-dot(w, u)*uv)/determinant
    if s >= 0 and t >= 0 and s+t <= 1:
        d = tuple(w[k]-s*u[k]-t*v[k] for k in range(3))
        return dot(d, d)
    return min(segment_squared(p, a, b), segment_squared(p, b, c), segment_squared(p, c, a))


def sqrt_display(q):
    with localcontext() as context:
        context.prec = 100
        return float((Decimal(q.numerator)/Decimal(q.denominator)).sqrt())


def first_ear_quad_squared(point, points):
    """Prove the first-ear split required by the declared surface convention.

    Convex projection makes the first vertex a valid ear. The deterministic
    source-order split is therefore (3,0,1), (1,2,3), without calling ear clipping.
    This is intentionally scoped to these quad counterexamples, not general rings.
    """
    triple = dot(cross(sub(points[1], points[0]), sub(points[2], points[0])),
                 sub(points[3], points[0]))
    assert triple != 0, "the old plane descriptor differs only for a folded source ring"
    newell = (F(0),)*3
    for a, b in zip(points, points[1:]+points[:1]):
        newell = tuple(x+y for x, y in zip(newell, cross(sub(a, points[0]), sub(b, points[0]))))
    dropped = max(range(3), key=lambda k: abs(newell[k]))
    i, j = [k for k in range(3) if k != dropped]
    def orientation(a, b, c):
        return (b[i]-a[i])*(c[j]-a[j])-(b[j]-a[j])*(c[i]-a[i])
    turns = [orientation(points[k-1], points[k], points[(k+1)%4]) for k in range(4)]
    assert all(x > 0 for x in turns) or all(x < 0 for x in turns), "projection is strictly convex"
    candidates = [triangle_squared(point, *(points[k] for k in tri))
                  for tri in ((3, 0, 1), (1, 2, 3))]
    return min(candidates), triple, dropped, turns, candidates


def main():
    records, cells = [], []
    for name, rotation, translation, scale in product(
            ("sep_vf", "ilock_sep"), ("q4", "q6"), (1000., 100000.), (.001, 1., 1000.)):
        _, a0, b0, d0, _, _ = T._margin_ref(name)
        a, b = (T._rigid(p, T.ROT_3[rotation], translation, scale) for p in (a0, b0))
        affected = 0
        # Exactly the existing grid input and delta; neither chooses the oracle
        # distance, which is computed below only from raw input coordinates.
        for item in T.margin_contacts(a, b, delta=1.5*scale*d0):
            old_distance = OLD.witness_distance(a, b, item.label)
            if abs(item.distance-old_distance) <= 4*math.ulp(old_distance):
                continue
            kind, fa, fb = item.label
            if kind == "VF":
                x, y, vertex, face = a, b, fa[1], fb[1]
            elif kind == "FV":
                x, y, vertex, face = b, a, fb[1], fa[1]
            else:
                raise AssertionError(("unexpected changed contact type", item.label))
            ring = y.faces[face]
            assert len(ring) == 4
            points = [tuple(F(c) for c in y.verts[i]) for i in ring]
            point = tuple(F(c) for c in x.verts[vertex])
            squared, triple, dropped, turns, candidates = first_ear_quad_squared(point, points)
            expected = sqrt_display(squared)
            assert item.exact_distance_squared == squared, (name, rotation, translation, scale, item.label)
            assert item.distance == expected, (name, rotation, translation, scale, item.distance, expected)
            records.append(dict(case=[name, rotation, translation, scale], label=item.label,
                                source_ring=ring, point=point, ring_points=points,
                                exact_nonplanarity_triple_product=triple,
                                dropped_axis=dropped, exact_projected_turns=turns,
                                triangles=[(ring[3],ring[0],ring[1]),(ring[1],ring[2],ring[3])],
                                triangle_distance_squared=candidates,
                                independent_distance_squared=squared,
                                production_distance_squared=item.exact_distance_squared,
                                old_newell_display_distance=old_distance,
                                production_distance=item.distance, independent_distance=expected,
                                old_error_ulp=abs(old_distance-expected)/math.ulp(expected),
                                production_error_ulp=0., exact_squared_equal=True))
            affected += 1
        cells.append(dict(case=[name, rotation, translation, scale], affected_contacts=affected))
    assert len(cells) == 24
    assert sum(bool(row["affected_contacts"]) for row in cells) == 16
    assert len(records) == 29
    sources = ["tests/test_invariance_interlock.py", "tests/e5a_cover_oracle.py",
               "src/eab/margin.py", "src/eab/kernel3d/covers3.py"]
    result = dict(scope="construction-only independent given-data Gram audit; not an enumeration completeness proof",
                  checked_grid_cells=24, affected_cells=16, affected_contacts=29,
                  oracle_production_geometry_helpers_used=[],
                  oracle_existing_test_geometry_helpers_used=[],
                  exact_squared_equal_for_all=True, maximum_production_error_ulp=0,
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  observed_sources_sha256={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sources},
                  cells=cells, records=records)
    (OUT/"independent_folded_margin_gram.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("24 cells checked; 16 affected cells; 29 affected contacts")
    print("29/29 exact squared distances equal independent Gram oracle; max error = 0 ULP")


if __name__ == "__main__":
    main()
