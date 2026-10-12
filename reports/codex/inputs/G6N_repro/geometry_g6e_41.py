# Original raw finding index 41; current HEAD replay, no repair.
import sys, math; sys.path.insert(0, 'src')
from eab.kernel3d.geom3 import Polyhedron, sub, convex_hull_3d_eps
from eab.kernel3d import g03
def roof(h, yaw=0.0):
    sec = [(-1.0, -1.0), (1.0, -1.0), (1.0, 0.0), (0.0, h), (-1.0, 0.0)]
    V = [(-2.0, y, z) for y, z in sec] + [(2.0, y, z) for y, z in sec]
    F = [(4, 3, 2, 1, 0), (5, 6, 7, 8, 9)] + [(i, (i + 1) % 5, 5 + (i + 1) % 5, 5 + i) for i in range(5)]
    c, s = math.cos(yaw), math.sin(yaw)
    return Polyhedron([(c * x - s * y, s * x + c * y, z) for x, y, z in V], F)
yaw, h = 10 ** -8.75, 0.1
B = roof(h); A = roof(h, yaw)
A = Polyhedron([(x, y, -z + 0.61) for x, y, z in A.verts], [tuple(reversed(f)) for f in A.faces])
print('supplied exact convexity',A.is_convex(),B.is_convex(),'explicit convex-model G0 follows')
r = g03.g0_convex3(A, B, samples=40, seed=1)
print('passed', r.passed, r.facet_symmetric_diff[:3])

