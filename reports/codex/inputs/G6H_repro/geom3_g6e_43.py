import sys
sys.path[:0]=['src','tests']
import sys; sys.path.insert(0, 'src')
from eab.kernel3d.geom3 import Polyhedron, convex_hull_3d, merge_coplanar, tetra, sub, dot
from eab.kernel3d import g03
e = 1e-6
pts = [(x, y, z) for x in (-1.0, 1.0) for y in (-1.0, 1.0) for z in (-1.0, 1.0)]
pts.remove((1.0, 1.0, 1.0)); pts += [(1.0 - e, 1.0, 1.0), (1.0, 1.0 - e, 1.0), (1.0, 1.0, 1.0 - e)]
ap = (1.08, 1.05, 1.033)
for tmag in (0.0, 100.0, 1e3, 1e4, 1e6):
    B = merge_coplanar(convex_hull_3d(pts))
    A = tetra(ap, (ap[0] + 1.0, ap[1] + 0.3, ap[2] + 0.2), (ap[0] + 0.2, ap[1] + 1.0, ap[2] + 0.4), (ap[0] + 0.3, ap[1] + 0.1, ap[2] + 1.0))
    mv = lambda P: Polyhedron([(x + 0.6 * tmag, y - 0.48 * tmag, z + 0.64 * tmag) for x, y, z in P.verts], list(P.faces))
    A, B = mv(A), mv(B)
    r = g03.g0_convex3(A, B, samples=40, seed=1)
    print('t', tmag, 'passed', r.passed, r.facet_symmetric_diff)
