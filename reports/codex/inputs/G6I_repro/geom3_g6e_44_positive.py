import sys
sys.path[:0]=['src','tests']
import sys, math, itertools; sys.path.insert(0, 'src')
from fractions import Fraction as Fr
from eab.kernel3d.geom3 import Polyhedron
from eab.kernel3d.covers3 import cone_intersection_margin, cones_intersect_relint, vv3_cover
from eab.kernel3d.g03 import g0_convex3
def roof(h, yaw=0.0):
    sec = [(-1.0, -1.0), (1.0, -1.0), (1.0, 0.0), (0.0, h), (-1.0, 0.0)]
    V = [(-2.0, y, z) for y, z in sec] + [(2.0, y, z) for y, z in sec]
    F = [(4, 3, 2, 1, 0), (5, 6, 7, 8, 9)] + [(i, (i + 1) % 5, 5 + (i + 1) % 5, 5 + i) for i in range(5)]
    c, s = math.cos(yaw), math.sin(yaw)
    return Polyhedron([(c * x - s * y, s * x + c * y, z) for x, y, z in V], F)
B = roof(0.3); A = roof(0.3, -2.297344991164547e-09)
A = Polyhedron([(x, y, -z + 0.61) for x, y, z in A.verts], [tuple(reversed(f)) for f in A.faces])
def nb(P, i): return {f[(k + d) % len(f)] for f in P.faces for k in range(len(f)) if f[k] == i for d in (1, -1)}
def exact_relint(ia, ib):   # exact Gordan: exists u with u.g < 0 for all constraint vectors
    a = [tuple(map(Fr, v)) for v in A.verts]; b = [tuple(map(Fr, v)) for v in B.verts]
    G = [tuple(p - q for p, q in zip(b[j], b[ib])) for j in nb(B, ib)] + [tuple(p - q for p, q in zip(a[ia], a[j])) for j in nb(A, ia)]
    cr = lambda u, v: (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]); dt = lambda u, v: sum(x*y for x, y in zip(u, v))
    rays = [c for g, k in itertools.combinations(G, 2) for c in (cr(g, k), tuple(-x for x in cr(g, k))) if any(c) and all(dt(c, q) <= 0 for q in G)]
    u = [sum(r[i] / max(abs(x) for x in r) for r in rays) for i in range(3)]
    return all(dt(u, q) < 0 for q in G), min(-float(dt(u, q)) / math.sqrt(float(dt(u, u)) * float(dt(q, q))) for q in G)
for ia, ib in [(3, 9), (4, 8), (7, 3), (8, 2)]:
    assert exact_relint(ia,ib)[0] and cones_intersect_relint(A,ia,B,ib) and vv3_cover(A,ia,B,ib) is not None
    print((ia, ib), cone_intersection_margin(A, ia, B, ib), cones_intersect_relint(A, ia, B, ib), vv3_cover(A, ia, B, ib), exact_relint(ia, ib))
r = g0_convex3(A, B, samples=40, seed=1); assert r.passed and r.e_vertices_ambiguous==0 and r.hull_vertex_mismatch==0; print('g0 passed', r.passed, 'e_vertices_ambiguous', r.e_vertices_ambiguous)