"""M3c test-owned Cartesian-union oracle; imports fractions/itertools only.

No production module, BSP output, SAT plane, hull, clipper or distance routine
is consumed. Input boxes are a hand-declared exact solid decomposition.
Common rational rotations are undone before these Cartesian calculations.
"""
from fractions import Fraction as F
from itertools import product


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def mean(points):
    return tuple(sum(p[k] for p in points)/len(points) for k in range(3))


IDENTITY = ((F(1), F(0), F(0)), (F(0), F(1), F(0)), (F(0), F(0), F(1)))
ROTATION = tuple(tuple(F(x, 30) for x in row)
                 for row in ((-20, 4, 22), (20, -10, 20), (10, 28, 4)))


def rotate(point, matrix):
    return tuple(dot(row, point) for row in matrix)


def inverse(point, matrix):
    return tuple(sum(matrix[j][k]*point[j] for j in range(3)) for k in range(3))


def occupied(boxes, point):
    return any(all(low[k] <= point[k] <= high[k] for k in range(3)) for low, high in boxes)


def adjacent_sides(boxes, polygon, sides):
    """Both probes precede every nonzero support-plane event on their line."""
    centre = mean(polygon)
    delta = sub(sides[1], centre)
    assert any(delta), 'independent adjacent-open-cell side probes are nonzero'
    assert sub(centre, sides[0]) == delta, 'independent adjacent-open-cell probes are opposite'
    for low, high in boxes:
        for k in range(3):
            if delta[k]:
                for height in (low[k], high[k]):
                    event = (height-centre[k])/delta[k]
                    assert not event or abs(event) > 1, 'independent adjacent-open-cell side probe crossed a support event'


def ray_sections(boxes, start, direction):
    intervals = []
    for low, high in boxes:
        lower = upper = None
        for k in range(3):
            if not direction[k]:
                if not low[k] <= start[k] <= high[k]:
                    break
            else:
                a, b = sorted(((low[k]-start[k])/direction[k], (high[k]-start[k])/direction[k]))
                lower = a if lower is None else max(lower, a)
                upper = b if upper is None else min(upper, b)
        else:
            if lower <= upper:
                intervals.append((lower, upper))
    merged = []
    for low, high in sorted(intervals):
        if merged and low <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], high))
        else:
            merged.append((low, high))
    return tuple(merged)


def boundary_rectangles(boxes):
    """Complete exposed rectangles from the independent Cartesian grid.

    The two open neighbours of each grid rectangle have constant occupancy;
    their XOR is the exact boundary criterion, including tight internal seams.
    """
    coordinates = [sorted({bound[k] for box in boxes for bound in box}) for k in range(3)]
    rectangles = []
    for axis in range(3):
        other = tuple(k for k in range(3) if k != axis)
        steps = [b-a for a, b in zip(coordinates[axis], coordinates[axis][1:])]
        step = min(steps)/2
        for height in coordinates[axis]:
            for spans in product(*(tuple(zip(coordinates[k], coordinates[k][1:])) for k in other)):
                lo, hi = [F(0)]*3, [F(0)]*3
                lo[axis] = hi[axis] = height
                for k, (a, b) in zip(other, spans):
                    lo[k], hi[k] = a, b
                centre = tuple((a+b)/2 for a, b in zip(lo, hi))
                sides = [tuple(centre[k]+sign*step if k == axis else centre[k] for k in range(3)) for sign in (-1, 1)]
                if occupied(boxes, sides[0]) != occupied(boxes, sides[1]):
                    rectangles.append((tuple(lo), tuple(hi)))
    return tuple(rectangles)


def shortest_exit(rectangles, point):
    rows = []
    for low, high in rectangles:
        closest = tuple(max(low[k], min(high[k], point[k])) for k in range(3))
        delta = sub(closest, point)
        rows.append((dot(delta, delta), closest))
    minimum = min(square for square, point in rows)
    return minimum, tuple(sorted({point for square, point in rows if square == minimum}))


def in_polygon(point, polygon):
    """Closed planar convex membership using only this module's arithmetic."""
    if len(polygon) < 3:
        return False
    origin = polygon[0]
    normal = next((cross(sub(a, origin), sub(b, origin))
                   for a, b in zip(polygon[1:], polygon[2:])
                   if any(cross(sub(a, origin), sub(b, origin)))), None)
    if normal is None or dot(normal, sub(point, origin)):
        return False
    turns = [dot(normal, cross(sub(b, a), sub(point, a)))
             for a, b in zip(polygon, polygon[1:]+polygon[:1])]
    return min(turns) >= 0 or max(turns) <= 0
