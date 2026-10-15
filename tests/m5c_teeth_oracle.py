"""Independent exact translation oracle. Imports: fractions only.

No production geometry, root, projection, interval or overlap primitive is used.
The callers construct initially disjoint CCW polygons and rigid translations.
"""
from fractions import Fraction as F


def translation_first_events(a, b, velocity_a=(0, 0), velocity_b=(0, 0)):
    """Enumerate linear incidence roots and closed-segment membership exactly."""
    events = []
    for p, q, vp, vq, tag in ((a, b, velocity_a, velocity_b, "VE"),
                              (b, a, velocity_b, velocity_a, "EV")):
        for i, vertex in enumerate(p):
            for j, edge_start in enumerate(q):
                edge_end = q[(j+1) % len(q)]
                ex, ey = (edge_end[k]-edge_start[k] for k in (0, 1))
                wx, wy = (vertex[k]-edge_start[k] for k in (0, 1))
                dx, dy = (vp[k]-vq[k] for k in (0, 1))
                slope = ex*dy-ey*dx
                if slope == 0:
                    continue
                t = -F(ex*wy-ey*wx)/slope
                projection = ex*(wx+t*dx)+ey*(wy+t*dy)
                if 0 <= t <= 1 and 0 <= projection <= ex*ex+ey*ey:
                    label = (tag, i, j) if tag == "VE" else (tag, j, i)
                    events.append((t, label))
    if not events:
        return None, ()
    first = min(t for t, _ in events)
    return first, tuple(sorted(label for t, label in events if t == first))


def point_strictly_inside(point, polygon):
    """Direct signed determinants for a caller-constructed convex CCW polygon."""
    return all((q[0]-p[0])*(point[1]-p[1])-(q[1]-p[1])*(point[0]-p[0]) > 0
               for p, q in zip(polygon, polygon[1:]+polygon[:1]))


def rotate_rational(point, u):
    """Independent complex product (1+iu)^2/(1+u^2)."""
    x, y = point
    return (((1-u*u)*x-2*u*y)/(1+u*u), (2*u*x+(1-u*u)*y)/(1+u*u))
