import sys
sys.path[:0]=['src','tests']
import sys, math, random
sys.path.insert(0, 'src')
from eab.kernel3d.geom3 import Polyhedron, box, dot
from eab.kernel3d.covers3 import ee_cover, facet_normal3
from eab.kernel3d.frozen import frozen_ee_sign, ee_normal_generic
from eab.margin import body_distance, margin_gap_from_frozen_cover, inflated_membership
def rot_z(th):
    c, s = math.cos(th), math.sin(th); return ((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0))
def rot3(seed):
    rng = random.Random(seed); q = [rng.gauss(0, 1) for _ in range(4)]
    n = math.sqrt(sum(c*c for c in q)); w, x, y, z = (c/n for c in q)
    return ((1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)), (2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)), (2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)))
def app(R, v): return tuple(R[i][0]*v[0]+R[i][1]*v[1]+R[i][2]*v[2] for i in range(3))
def xf(P, R, t): return Polyhedron([tuple(a+b for a, b in zip(app(R, p), t)) for p in P.verts], list(P.faces))
for (yaw, gap, seed, t) in [(1e-5, 1e-3, 6, 1e3), (1e-4, 1e-3, 4, 1e5), (1e-4, 1e-6, 6, 1e6)]:
    tv = (t*0.6, -t*0.48, t*0.64)
    A = xf(xf(box(center=(0, 0, 1 + gap), half=(.5, .5, .5)), rot_z(yaw), (0, 0, 0)), rot3(seed), tv)
    B = xf(box(half=(.5, .5, .5)), rot3(seed), tv)
    d, lab = body_distance(A, B)
    ea, eb = (lab[1][1], lab[1][2]), (lab[2][1], lab[2][2])
    s = frozen_ee_sign(A, B, ea, eb)
    g = margin_gap_from_frozen_cover(A, B, lab, (0.0, 0.0, 0.0), 0.0, ee_sign=s)
    cov = ee_cover(A, ea, B, eb, 1e-9)
    print(f"yaw={yaw:g} gap={gap:g} |t|={t:g}: d={d:.6g} label={lab} frozen_ee_sign={s:+.0f} frozen gap={g:+.6g} (should be +d)")
    print("   ee_cover.normal . frozen normal =", round(dot(cov.normal, tuple(s*c for c in ee_normal_generic(A, ea, B, eb))), 3),
          "; ee_cover.normal . facet_normal3 =", round(dot(cov.normal, facet_normal3(A, B, lab)), 3), "; strict =", cov.strict)
    print("   inflated_membership(delta=0.5d) =", inflated_membership(A, B, delta=0.5*d), "; frozen gap at delta=0.5d =", margin_gap_from_frozen_cover(A, B, lab, (0,0,0), 0.5*d, ee_sign=s))