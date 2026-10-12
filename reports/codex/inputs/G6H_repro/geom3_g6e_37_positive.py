import sys
sys.path[:0]=['src','tests']
import sys; sys.path.insert(0,'src'); sys.path.insert(0,'tests')
from test_invariance_geom import Motion
from eab.kernel3d.geom3 import box
from eab.kernel3d.entrance3 import first_entrance3
B0 = box(half=(50.0, 50.0, 50.0)); h = 0.02
A0 = box(center=(1.3, -2.1, 50.0 + h + 1.0), half=(h, h, h))
for rot in (0, 7, 11):
    M = Motion(rot, 0.0, 1.0)
    try:
        r = first_entrance3(M.poly(A0), M.poly(B0), (0.0, 0.0, 0.0), M.vec((0.0, 0.0, -1.0)))
        assert r.kind=='entrance' and abs(r.t-1)<1e-14 and r.exact_t is not None
        print(rot, r.kind, r.t, r.label)
    except RuntimeError as e:
        raise AssertionError('original false-crash scenario persists') from e