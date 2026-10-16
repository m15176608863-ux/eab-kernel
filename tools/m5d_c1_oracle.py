"""Independent C1 oracle: Fraction only; no production geometry imports.

Cartesian vertex differences -> monotone-chain hull -> determinant projection.
The production implementation instead constructs support faces directly.
For convex input this oracle enumerates ALL closed boundary segments and ties.
"""
from fractions import Fraction as F


def exit_oracle(a, b, x=(0, 0)):
    points = sorted({(F(v[0])-u[0], F(v[1])-u[1]) for u in a for v in b})
    def orient(p, q, r):
        return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    lower, upper = [], []
    for p in points:
        while len(lower) >= 2 and orient(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper) >= 2 and orient(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1]+upper[:-1]
    rows = []
    inside = True
    for p, q in zip(hull, hull[1:]+hull[:1]):
        det = orient(p, q, x)
        inside = inside and det > 0
        dx, dy = q[0]-p[0], q[1]-p[1]
        t = (x[0]-p[0])*dx+(x[1]-p[1])*dy
        length = dx*dx+dy*dy
        if t < 0:
            squared = (x[0]-p[0])**2+(x[1]-p[1])**2
        elif t > length:
            squared = (x[0]-q[0])**2+(x[1]-q[1])**2
        else:
            squared = det*det/length
        labels = []
        for i, av in enumerate(a):
            for j, bv in enumerate(b):
                start = bv[0]-av[0], bv[1]-av[1]
                be = b[(j+1) % len(b)]
                ae = a[(i+1) % len(a)]
                if start == p and (be[0]-av[0], be[1]-av[1]) == q:
                    labels.append(("VE", i, j))
                if start == p and (bv[0]-ae[0], bv[1]-ae[1]) == q:
                    labels.append(("EV", i, j))
        rows.append((squared, tuple(labels)))
    best = min(q for q, _ in rows)
    return dict(inside=inside, distance2=best,
                labels=tuple(sorted(label for q, labels in rows if q == best for label in labels)),
                edges=len(hull))
