import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
import sys; sys.path.insert(0,'src'); sys.path.insert(0,'tests')
from test_invariance_geom import Motion
from eab.kernel3d.geom3 import box, convex_hull_3d
from eab.margin import margin_contacts
from eab.kernel3d.covers3 import enumerate_covers3
d = 2.0**-10
B = box(half=(1.0, 1.0, 0.5))
pts = [(0.0, -1-d, 0.6), (2.0, -1+d, 0.6), (2.0, 1+d, 0.6), (0.0, 1-d, 0.6)]
A = convex_hull_3d(pts + [(x, y, 1.6) for x, y, _ in pts])
lab = lambda A, B: {(c.label(), c.strict) for c in enumerate_covers3(A, B, window=float('inf'), tol=1e-9) if c.in_extent}
m0 = {m.label for m in margin_contacts(A, B, delta=0.2)}; c0 = lab(A, B)
M = Motion(7, 0.0, 1.0)   # pure rotation
A1, B1 = M.poly(A), M.poly(B)
print('covers lost', sorted(c0 - lab(A1, B1)))
print('margin contacts lost', sorted(m0 - {m.label for m in margin_contacts(A1, B1, delta=0.2)}))