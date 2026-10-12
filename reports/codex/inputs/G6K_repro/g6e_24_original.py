import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
import sys
sys.path.insert(0,'src'); sys.path.insert(0,'tests')
from eab.kernel3d.geom3 import box, polyhedra_overlap
from eab.margin import body_distance, effective_geom_tol, characteristic_length
from test_invariance_geom import Motion
B = box(half=(10.0, 0.01, 1.0))                                  # thin wall, top face 20 m x 2 cm
A = box(center=(0.0, 0.0, 1.1), half=(0.25, 5.0, 0.1))          # 10 m beam lying exactly on it, across
for t in (1e6, 4e6):
    bad = []
    for r in range(1, 41):
        M = Motion(r, t, 1.0); Am, Bm = M.poly(A), M.poly(B)
        if polyhedra_overlap(Am, Bm, effective_geom_tol(Am, Bm)) == 1:
            bad.append((r, body_distance(Am, Bm)))
    print(t, 'L=', characteristic_length(Am, Bm), 'PENETRATING in', len(bad), '/40', bad[:1])