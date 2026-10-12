import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
import sys, math; sys.path.insert(0,'src')
from eab.kernel2d.geom import convex_hull
from eab.kernel2d.g0 import g0_convex
pts = [(0.0, 0.0), (1e-15, -1e-3), (1e-15, 1.0), (1e-3, -1e-3), (2.0, -1e-3), (2.0, 1.0)]
H = convex_hull(pts)
out = lambda p: max(((p[0]-a[0])*(b[1]-a[1]) - (p[1]-a[1])*(b[0]-a[0]))/math.dist(a, b) for a, b in zip(H, H[1:]+H[:1]))
print(H, 'worst outside', max(map(out, pts)))
def sq(c, h, tilt):
    ct, st = math.cos(tilt), math.sin(tilt)
    return [(c[0]+ct*x-st*y, c[1]+st*x+ct*y) for x, y in ((-h,-h),(h,-h),(h,h),(-h,h))]
A = sq((3.0, 1e-3+2e-9), 1e-3, 1e-6); B = [(-1e3,-1e3),(1e3,-1e3),(1e3,0.0),(-1e3,0.0)]
print('identity', g0_convex(A, B, samples=200, seed=2).passed)
T = lambda p: (1e-3*p[0] + 600.0, 1e-3*p[1] - 800.0)
r = g0_convex([T(p) for p in A], [T(p) for p in B], samples=200, seed=2)
print('translated+scaled', r.passed, 'hull_vertex_mismatch', r.hull_vertex_mismatch, 'ambiguous', r.hull_vertex_ambiguous)