"""Read-only peer probes: independent barycentric intersection and cache scope."""
from fractions import Fraction as F
from itertools import combinations
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]
from eab.kernel3d import global_entrance as G
from eab.kernel3d import interlock as I
from eab.kernel3d import geom3


def unique_solution(rows):
    rows = [list(map(F, row)) for row in rows]
    pivots = []
    for k in range(4):
        pick = next((i for i in range(len(pivots), len(rows)) if rows[i][k]), None)
        if pick is None:
            continue
        at = len(pivots)
        rows[at], rows[pick] = rows[pick], rows[at]
        divisor = rows[at][k]
        rows[at] = [x/divisor for x in rows[at]]
        for i in range(len(rows)):
            if i != at:
                factor = rows[i][k]
                rows[i] = [x-factor*y for x, y in zip(rows[i], rows[at])]
        pivots.append(k)
    if any(not any(row[:4]) and row[4] for row in rows) or len(pivots) != 4:
        return None
    return tuple(rows[i][4] for i in range(4))


def independent_meeting(a, b):
    # a0+u(a1-a0)+v(a2-a0)=b0+w(b1-b0)+z(b2-b0),
    # u,v,w,z>=0; u+v<=1,w+z<=1. Enumerate simplex-face active sets.
    equalities = [(a[1][k]-a[0][k], a[2][k]-a[0][k],
                   b[0][k]-b[1][k], b[0][k]-b[2][k], b[0][k]-a[0][k]) for k in range(3)]
    facets = [(1, 0, 0, 0, 0), (0, 1, 0, 0, 0), (1, 1, 0, 0, 1),
              (0, 0, 1, 0, 0), (0, 0, 0, 1, 0), (0, 0, 1, 1, 1)]
    result = set()
    for count in (1, 2):
        for active in combinations(facets, count):
            solution = unique_solution(equalities+list(active))
            if solution is None:
                continue
            u, v, w, z = solution
            if min(solution) >= 0 and u+v <= 1 and w+z <= 1:
                result.add(tuple(a[0][k]+u*(a[1][k]-a[0][k])+v*(a[2][k]-a[0][k]) for k in range(3)))
    return result


def nondegenerate(tri):
    a, b, c = tri
    return any((b[i]-a[i])*(c[j]-a[j]) != (b[j]-a[j])*(c[i]-a[i])
               for i, j in ((0, 1), (0, 2), (1, 2)))


def main():
    rng = random.Random(20261015)
    rows = []
    for coplanar in (True, False):
        for _ in range(200):
            triangles = []
            while len(triangles) < 2:
                tri = tuple(tuple(F(rng.randrange(-2, 3)) if k < 2 or not coplanar else F(0)
                                  for k in range(3)) for j in range(3))
                if nondegenerate(tri):
                    triangles.append(tri)
            a, b = triangles
            expected, actual = independent_meeting(a, b), G._triangle_meeting(a, b)
            rows.append(dict(coplanar=coplanar, match=actual == expected,
                             expected_size=len(expected), actual_size=len(actual)))
            assert actual == expected, (a, b, expected, actual)
    body = geom3.box(half=(F(1),)*3)
    offset = (F(0),)*3
    warm = I._exact_escape(body, body, offset)[0]
    original = G._line_candidate
    try:
        G._line_candidate = lambda *args: False
        direct_label = I._nonpenetrating_at(body, body, offset, F(0))
        cached = I._exact_escape(body, body, offset)[0]
        I._exact_escape_cached.cache_clear()
        cold = I._exact_escape(body, body, offset)[0]
    finally:
        G._line_candidate = original
        I._exact_escape_cached.cache_clear()
    result = dict(triangle_pairs=len(rows), coplanar_pairs=200, noncoplanar_generation_pairs=200,
                  mismatches=sum(not r["match"] for r in rows),
                  oracle="independent 4-variable barycentric polytope active-set enumeration with exact Gaussian elimination",
                  oracle_imports=["fractions.Fraction", "itertools.combinations"],
                  cache_scope=dict(warm_exact_root=warm, direct_mutated_initial_label=direct_label,
                                   warm_outer_cache_root_after_mutation=cached,
                                   root_after_clearing_outer_cache=cold,
                                   classification="test-harness cache caveat, not a fixed-function production result defect"))
    Path(__file__).with_suffix(".json").write_text(json.dumps(result, default=str, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
