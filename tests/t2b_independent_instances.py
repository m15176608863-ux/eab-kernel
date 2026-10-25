"""Independent exact T2a-table dovetail inputs for WO-T2b-V section P1.6.

Only the permitted ``tolerance_dovetail`` construction is transcribed, with
height and wall thickness fixed to two.  Convex erosion is implemented from
the defining shifted half-planes, independently of all production geometry.
The obstacle order is always left, right, floor; each individual ring is
canonicalized numerically, not by lexicographic rational-string order.

Every public geometry result is JSON compatible with canonical rational
strings. Empty erosion is [], a point is a one-point list, and a segment is
its two numerically sorted endpoints. Such outputs explicitly are not
full-dimensional polygon instances accepted by the cage verifier.
"""

import json
import sys
from fractions import Fraction as F
from pathlib import Path


SQUARE = ((F(-1), F(-1)), (F(1), F(-1)),
          (F(1), F(1)), (F(-1), F(1)))
OCTAGON = ((F(-5, 12), F(-1)), (F(5, 12), F(-1)),
           (F(1), F(-5, 12)), (F(1), F(5, 12)),
           (F(5, 12), F(1)), (F(-5, 12), F(1)),
           (F(-1), F(5, 12)), (F(-1), F(-5, 12)))

CASE_PARAMETERS = (
    ("d01", F(5, 2), F(3, 2), "square", 0, F(3, 10)),
    ("d02", F(7, 2), F(3, 2), "square", 0, F(2, 5)),
    ("d03", F(5, 2), F(1), "square", 0, F(21, 50)),
    ("d04", F(5, 2), F(1), "square", 1, F(1, 5)),
    ("d05", F(7, 2), F(3, 2), "octagon", 0, F(9, 20)),
    ("d06", F(3), F(1), "octagon", 0, F(11, 20)),
    ("d07", F(5, 2), F(3, 2), "octagon", 0, F(7, 20)),
    ("d08", F(3), F(3, 2), "octagon", 1, F(6, 25)),
)


def rational(value):
    """Accept exact integers, Fractions, or canonical rational strings only."""
    if isinstance(value, bool):
        raise TypeError("booleans are not rational coordinates")
    if isinstance(value, (int, F)):
        return F(value)
    if isinstance(value, str):
        if len(value) > 4096:
            raise ValueError("rational string exceeds the coordinate limit")
        result = F(value)
        if str(result) != value:
            raise ValueError("rational strings must have canonical ASCII spelling")
        return result
    raise TypeError("coordinates must be exact integers, Fractions, or rational strings")


def rational_points(ring):
    result = []
    for point in ring:
        if len(point) != 2:
            raise ValueError("a point must have two coordinates")
        result.append((rational(point[0]), rational(point[1])))
    return result


def encode_points(points):
    result = []
    for x, y in points:
        result.append([str(x), str(y)])
    return result


def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def area_twice(ring):
    total = F(0)
    for index, a in enumerate(ring):
        b = ring[(index + 1) % len(ring)]
        total += a[0] * b[1] - a[1] * b[0]
    return total


def between(a, b, c):
    """Whether b lies on the closed segment a--c, assuming collinearity."""
    product = (b[0] - a[0]) * (b[0] - c[0]) + (b[1] - a[1]) * (b[1] - c[1])
    return product <= 0


def canonical_ring(ring):
    """Preserve ring geometry, remove redundant points, orient and rotate.

    This is not a convex hull: a genuine concave corner is retained. Ordered
    simple full-dimensional input is required when there are at least three
    non-collinear vertices; non-simple input is outside this helper's scope.
    """
    points = rational_points(ring)
    compact = []
    for point in points:
        if not compact or point != compact[-1]:
            compact.append(point)
    if len(compact) > 1 and compact[0] == compact[-1]:
        compact.pop()
    if not compact:
        return []
    ordered = sorted(set(compact))
    if len(ordered) == 1:
        return encode_points(ordered)
    collinear = True
    for point in ordered[1:-1]:
        if cross(ordered[0], ordered[-1], point) != 0:
            collinear = False
            break
    if collinear:
        return encode_points([ordered[0], ordered[-1]])
    changed = True
    while changed:
        changed = False
        for index, point in enumerate(compact):
            previous = compact[index - 1]
            following = compact[(index + 1) % len(compact)]
            if cross(previous, point, following) == 0 and between(previous, point, following):
                compact.pop(index)
                changed = True
                break
    signed_area = area_twice(compact)
    if signed_area == 0:
        raise ValueError("non-collinear ring has zero signed area")
    if signed_area < 0:
        compact.reverse()
    start = 0
    for index, point in enumerate(compact):
        if point < compact[start]:
            start = index
    return encode_points(compact[start:] + compact[:start])


def canonical_instance(instance):
    """Canonicalize individual rings without permuting obstacle identities."""
    if set(instance) != {"moving", "obstacles"}:
        raise ValueError("an instance must contain exactly moving and obstacles")
    obstacles = []
    for ring in instance["obstacles"]:
        obstacles.append(canonical_ring(ring))
    return {"moving": canonical_ring(instance["moving"]), "obstacles": obstacles}


def convex_hull(points):
    """Hull of unordered feasible intersections, retaining degenerate sets."""
    ordered = sorted(set(points))
    if len(ordered) <= 2:
        return ordered
    lower = []
    for point in ordered:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(ordered):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def erode_convex(ring, kernel, delta):
    """Enumerate vertices of {y: n.y <= b - support_(delta K)(n)}.

    The scale multiplies each kernel point before taking the maximum. Thus
    negative delta is never silently interpreted as outward dilation. For
    the two centrally symmetric supplied kernels, +/-delta give equal sets.
    """
    vertices = rational_points(ring)
    kernel_points = rational_points(kernel)
    scale = rational(delta)
    if not kernel_points:
        raise ValueError("the erosion kernel must be nonempty")
    halfplanes = []
    for index, a in enumerate(vertices):
        b = vertices[(index + 1) % len(vertices)]
        normal = (b[1] - a[1], a[0] - b[0])
        if normal == (0, 0):
            raise ValueError("zero-length edge is not a half-plane")
        bound = normal[0] * a[0] + normal[1] * a[1]
        first = kernel_points[0]
        support = normal[0] * scale * first[0] + normal[1] * scale * first[1]
        for point in kernel_points[1:]:
            value = normal[0] * scale * point[0] + normal[1] * scale * point[1]
            if value > support:
                support = value
        halfplanes.append((normal[0], normal[1], bound - support))
    feasible = []
    for first_index, first in enumerate(halfplanes):
        a, b, c = first
        for second in halfplanes[first_index + 1:]:
            d, e, f = second
            determinant = a * e - b * d
            if determinant == 0:
                continue
            point = ((c * e - b * f) / determinant,
                     (a * f - c * d) / determinant)
            inside = True
            for nx, ny, bound in halfplanes:
                if nx * point[0] + ny * point[1] > bound:
                    inside = False
                    break
            if inside:
                feasible.append(point)
    return canonical_ring(convex_hull(feasible))


def dovetail_instance(wk, wn, K, e, delta):
    """Construct an exact eroded dovetail with fixed h=w=2.

    ``e`` must be integer 0 or 1: zero keeps the original obstacles, one
    erodes them by the same delta K as the moving trapezoid. The input kernel
    is a nonempty point sequence; its support is evaluated without assuming
    axis alignment, strict convexity, or central symmetry.
    """
    wk = rational(wk)
    wn = rational(wn)
    delta = rational(delta)
    if not isinstance(e, int) or isinstance(e, bool) or e not in (0, 1):
        raise ValueError("e must be integer zero or one")
    if not 0 < wn < wk:
        raise ValueError("widths must satisfy 0 < wn < wk")
    kernel = rational_points(K)
    if not kernel:
        raise ValueError("the erosion kernel must be nonempty")
    height = F(2)
    thickness = F(2)
    outside = wk / 2 + thickness
    moving = ((-wk / 2, F(0)), (wk / 2, F(0)),
              (wn / 2, height), (-wn / 2, height))
    left = ((-outside, F(0)), (-wk / 2, F(0)),
            (-wn / 2, height), (-outside, height))
    right_points = []
    for x, y in reversed(left):
        right_points.append((-x, y))
    right = tuple(right_points)
    floor = ((-outside, -thickness), (outside, -thickness),
             (outside, F(0)), (-outside, F(0)))
    obstacles = []
    for obstacle in (left, right, floor):
        if e == 1:
            obstacles.append(erode_convex(obstacle, kernel, delta))
        else:
            obstacles.append(canonical_ring(obstacle))
    return {"moving": erode_convex(moving, kernel, delta), "obstacles": obstacles}


def build_independent_instances():
    result = {}
    for name, wk, wn, kernel_name, wall_erosion, delta in CASE_PARAMETERS:
        kernel = SQUARE
        if kernel_name == "octagon":
            kernel = OCTAGON
        result[name] = dovetail_instance(wk, wn, kernel, wall_erosion, delta)
    return result


def write_independent_instances(destination):
    """Write the eight geometry-only JSONs into an existing directory."""
    destination = Path(destination)
    paths = []
    for name, instance in build_independent_instances().items():
        path = destination / (name + ".json")
        content = json.dumps(instance, ensure_ascii=True, indent=2) + "\n"
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        paths.append(path)
    return paths


def generate_independent_instances():
    destination = Path(__file__).parent / "data" / "t2b_independent_instances"
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--output-dir":
        destination = Path(args[1])
    elif args:
        raise ValueError("expected --output-dir PATH or no arguments")
    paths = write_independent_instances(destination)
    with open(1, "w", encoding="utf-8", closefd=False) as handle:
        for path in paths:
            handle.write(str(path) + "\n")
    return 0


STATUS = generate_independent_instances() if __name__ == "__main__" else 0
if STATUS:
    raise ValueError("independent instance generation failed")
