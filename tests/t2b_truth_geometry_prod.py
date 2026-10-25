"""WO-T2b production-side truth geometry, separate from the other verifier.

The room coordinates are copied from the owner's lemma, not inferred from a
proposed certificate. Existing four truth families retain their T2a source.
"""
from fractions import Fraction as F

from t2a_truth_geometry import (diamond_plates, doorway, midpoint_wedges,
                              rectangle, windmill)


def low_room():
    """The exact five fixed rings in cage lemma section 5, example 5."""
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
    """The taller control, with space for an in-place quarter turn."""
    moving = rectangle(F(-3, 2), F(-1, 2), F(3, 2), F(1, 2))
    obstacles = (
        rectangle(F(-13, 5), -3, F(13, 5), -2),
        rectangle(F(-13, 5), -2, F(-8, 5), 2),
        rectangle(F(8, 5), -2, F(13, 5), 2),
        rectangle(F(-13, 5), 2, F(-11, 20), 6),
        rectangle(F(11, 20), 2, F(13, 5), 6),
    )
    return moving, obstacles


def truth_instance(name, delta=F(0)):
    """Return independent input geometry and its prescribed rotation centre."""
    if name == "doorway":
        moving, obstacles = doorway(delta)
        center = (F(0), F(1, 2))
    else:
        if name == "windmill":
            moving, obstacles = windmill()
        elif name == "midpoint_wedges":
            moving, obstacles = midpoint_wedges()
        elif name == "diamond_plates":
            moving, obstacles = diamond_plates()
        elif name == "low_room":
            moving, obstacles = low_room()
        elif name == "high_room":
            moving, obstacles = high_room()
        else:
            raise ValueError("unknown truth geometry")
        center = (F(0), F(0))
    return {"moving": moving, "obstacles": obstacles}, center
