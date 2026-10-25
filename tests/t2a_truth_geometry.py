"""WO-T2a hand-derived rational truth inputs, not production geometry.

All rings are counterclockwise. The doorway's eroded rectangle is obtained
directly from its four support lines; both the square and rational octagon
have coordinate support one. No production erosion or rotation is used.
"""
from fractions import Fraction as F


IDENTITY = (F(0), (F(0), F(0)), (F(0), F(0)))


def rectangle(x0, y0, x1, y1):
    return tuple((F(x), F(y)) for x, y in
                 ((x0, y0), (x1, y0), (x1, y1), (x0, y1)))


def quarter_turns(ring):
    """Four exact placements with unchanged vertex and edge identities."""
    result = []
    for _ in range(4):
        result.append(ring)
        ring = tuple((-y, x) for x, y in ring)
    return tuple(result)


def windmill():
    square = rectangle(-1, -1, 1, 1)
    wedge = ((F(1), F(1, 2)), (F(3), F(0)), (F(3), F(1)))
    return square, quarter_turns(wedge)


def midpoint_wedges():
    square = rectangle(-1, -1, 1, 1)
    wedge = ((F(1), F(0)), (F(3), F(-1, 2)), (F(3), F(1, 2)))
    return square, quarter_turns(wedge)


def diamond_plates():
    diamond = tuple((F(x), F(y)) for x, y in
                    ((1, 0), (0, 1), (-1, 0), (0, -1)))
    return diamond, quarter_turns(rectangle(1, F(-1, 4), 2, F(1, 4)))


def doorway(delta):
    """Exact octagon erosion of the moving rectangle; walls stay unchanged."""
    delta = F(delta)
    if not 0 <= delta < F(1, 2):
        raise ValueError("truth rectangle requires 0 <= delta < 1/2")
    moving = rectangle(F(-3, 2)+delta, delta, F(3, 2)-delta, 1-delta)
    obstacles = (
        rectangle(-4, -1, 4, 0), rectangle(-4, 0, -3, 6),
        rectangle(3, 0, 4, 6), rectangle(-4, 6, F(-3, 8), 7),
        rectangle(F(3, 8), 6, 4, 7),
    )
    return moving, obstacles


def doorway_motion_specs():
    """Lift into chamber, turn 90 degrees, pass through the doorway."""
    return (
        (F(0), (F(0), F(5, 2)), (F(0), F(1, 2))),
        (F(1), (F(0), F(0)), (F(0), F(3))),
        (F(0), (F(0), F(5)), (F(0), F(3))),
    )
