
import sys, copy; sys.path.insert(0, 'src')
from eab.limit import LimitContact, wrench, limit_load, check_duality
for D in (0.0, 1e4, 1e5, 1e6):
    cts = [LimitContact((sx, 0.0), (0, 1), 0.6) for sx in (-1, 1)] + [LimitContact((D, 0.0), (0, 1), 0.6)]
    dead = wrench((0.0, -10.0), (0.0, 0.5), (0.0, 0.0), 2); live = [0.0, 0.0, 1.0]
    r = limit_load(cts, dead, live, dim=2)
    out = []
    for f in (0.999, 0.99, 0.9):
        r2 = copy.copy(r); r2.alpha = r.alpha * f
        out.append((f, check_duality(r2, cts, dead, live, dim=2)['ok']))
    print('D', D, 'alpha', r.alpha, out)
