"""Independent rational inputs for the owner-written T2b cage lemma.

The first four named examples are imported unchanged from the permitted T2a
truth-input module.  The two room examples reproduce lemma section 5, example
5, including each obstacle's vertex start, orientation, and list position.
This module does not import any production geometry or the ``eab`` package.
"""

from fractions import Fraction as F

from t2a_truth_geometry import (
    diamond_plates,
    doorway,
    midpoint_wedges,
    rectangle,
    windmill,
)


def low_room():
    """Return the exact low-room rings of lemma section 5, example 5."""
    moving = rectangle(F(-3, 2), F(-1, 2), F(3, 2), F(1, 2))
    obstacles = (
        rectangle(F(-13, 5), F(-8, 5), F(13, 5), F(-3, 5)),
        rectangle(F(-13, 5), F(-3, 5), F(-8, 5), F(3, 5)),
        rectangle(F(8, 5), F(-3, 5), F(13, 5), F(3, 5)),
        rectangle(F(-13, 5), F(3, 5), F(-11, 20), F(23, 5)),
        rectangle(F(11, 20), F(3, 5), F(13, 5), F(23, 5)),
    )
    return moving, obstacles


def high_room():
    """Return the exact escapable high-room control of lemma section 5."""
    moving = rectangle(F(-3, 2), F(-1, 2), F(3, 2), F(1, 2))
    obstacles = (
        rectangle(F(-13, 5), -3, F(13, 5), -2),
        rectangle(F(-13, 5), -2, F(-8, 5), 2),
        rectangle(F(8, 5), -2, F(13, 5), 2),
        rectangle(F(-13, 5), 2, F(-11, 20), 6),
        rectangle(F(11, 20), 2, F(13, 5), 6),
    )
    return moving, obstacles


def json_ring(ring):
    """Encode rational ring/line coordinates in the canonical JSON grammar."""
    result = []
    for x, y in ring:
        result.append([str(F(x)), str(F(y))])
    return result


def instance_json(moving, obstacles):
    """Return the geometry-only instance, independent of any certificate."""
    encoded_obstacles = []
    for obstacle in obstacles:
        encoded_obstacles.append(json_ring(obstacle))
    return {"moving": json_ring(moving), "obstacles": encoded_obstacles}
