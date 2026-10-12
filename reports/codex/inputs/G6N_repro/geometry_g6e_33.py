# Original raw finding index 33; current HEAD replay, no repair.
import sys, math, random
sys.path.insert(0, 'src')
from eab.kernel3d.geom3 import Polyhedron, box
import eab.kernel3d.interlock as I
U_PROF = [(-2, -1), (2, -1), (2, 1), (1, 1), (1, 0), (-1, 0), (-1, 1), (-2, 1)]
def prism_xz(prof, y0, y1):
    n = len(prof)
    v = [(float(x), float(y0), float(z)) for x, z in prof] + [(float(x), float(y1), float(z)) for x, z in prof]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + [(i, (i+1)%n, (i+1)%n + n, i + n) for i in range(n)]
    P = Polyhedron(v, faces)
    return P if P.volume() > 0 else Polyhedron(v, [tuple(reversed(f)) for f in faces])
L0 = prism_xz(U_PROF, -1.0, 1.0)                        # U-channel: floor z=0 for |x|<1, walls x=+-1 up to z=1
A0 = box(center=(0.0, 0.0, 0.3), half=(1.0, 0.5, 0.5))   # key touching both walls, 0.2 into the floor
Am = Polyhedron([(-p[0], p[1], p[2]) for p in A0.verts], [tuple(reversed(f)) for f in A0.faces])  # vertex 0 at x=+1
U = (0.6, -0.48, 0.64)
def place(P, th, t, rng, ulps):
    c, s = math.cos(th), math.sin(th)
    return Polyhedron([tuple(x + rng.randint(-ulps, ulps) * math.ulp(x) for x in
        (c*p[0] - s*p[1] + t*U[0], s*p[0] + c*p[1] + t*U[1], p[2] + t*U[2])) for p in P.verts], list(P.faces))
for seed in (12, 16, 29):
    rng = random.Random(seed)
    A, L = place(Am, 0.7, 1e5, rng, 4), place(L0, 0.7, 1e5, rng, 4)
    sol = I.escape_height_covers(A, L, (0.0, 0.0, 0.0))
    print(seed, 'covers', sol.height, sol.cover_label, 'brute', I.escape_height_brute(A, L, (0.0, 0.0, 0.0), hi=2.0))
