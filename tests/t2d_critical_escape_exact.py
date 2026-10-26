"""Exact whole-motion strip proof for the nine WO-T2d critical escapes.

The independent primitives are support inequalities, quadratic-field
arithmetic, convexity of a disk and piecewise-affine horizontal sections.
No erosion implementation, SE(2) path code or verifier is called. We do
NOT identify erosion(conv(A)) with erosion(A): the former is only an outer
radius bound, while erosion(Q) provides the contained half-unit disk.
"""
from fractions import Fraction as F

import tests.t2d_knob_family_exact as exact


HALF_NECK = F(1, 2)
COSINE_FACTOR = F(1)
FLOOR_TOP = F(0)


def truth_obstacles(n):
    """Independent walls from the checked cavity profile and fixed wall=2."""
    profile = exact.family_geometry(n)["right_profile"]
    left = ((F(-3), F(0)),)+tuple((-width, height) for height, width in profile)+((F(-3), F(2)),)
    right = tuple((-x, y) for x, y in reversed(left))
    floor = ((F(-3), F(-2)), (F(3), F(-2)), (F(3), FLOOR_TOP), (F(-3), FLOOR_TOP))
    return left, right, floor


def rotation_to_horizontal(edge):
    root = exact.Surd(0, 1, edge["norm_squared"])
    mx, my = edge["normal"]
    return COSINE_FACTOR*mx/root, -my/root


def rotated_point(point, cosine, sine):
    x, y = point
    return cosine*x-sine*(y-1), 1+sine*x+cosine*(y-1)


def verify_disk_subset(n, element, delta):
    """Check every support of B(c,1/2)+delta*K subset Q subset A.

    All right-half-circle edges and their x reflections are included.
    Squaring is justified by the separately checked positive residual.
    The strict lower-delta case follows since every support of K is >0.
    """
    exact.verify_family_geometry(n)
    margins = []
    for edge in exact.edge_candidates(n, element):
        mx, my = edge["normal"]
        for sx in (-1, 1):
            h = exact.support(element, sx*mx, my)
            assert h > 0, "disk containment requires positive K supports"
            residual = edge["offset"]-delta*h
            assert residual > 0, "disk support residual must be positive"
            margin = residual*residual-HALF_NECK*HALF_NECK*edge["norm_squared"]
            assert margin >= 0, "half-unit disk is not contained in the erosion"
            margins.append(margin)
    assert any(margin == 0 for margin in margins), "critical disk must touch an active support"
    return tuple(margins)


def verify_upward_closure(n):
    """Every cavity point with |x|<=1/2 has a free upward ray.

    Below y=1, cavity half-width is nondecreasing. Above y=1, every
    affine section has width at least 1/2. These endpoint checks cover
    whole segments, not a sample of times or heights. Above y=2 there
    are no side walls, and upward motion cannot meet the floor y<=0.
    """
    profile = exact.family_geometry(n)["right_profile"]
    left, right, floor = truth_obstacles(n)
    assert all(y <= 0 for _, y in floor), "floor intrudes into upward cavity rays"
    assert left[1:-1] == tuple((-width, height) for height, width in profile)
    assert right == tuple((-x, y) for x, y in reversed(left))
    assert all(0 <= y <= 2 for wall in (left, right) for _, y in wall)
    assert profile[0] == (0, 0) and profile[-1] == (2, HALF_NECK), \
        "upward-closure cavity endpoints changed"
    assert (F(1), F(1)) in profile, "maximum-width level missing"
    for (ya, wa), (yb, wb) in zip(profile, profile[1:]):
        assert ya < yb and wa >= 0 and wb >= 0
        if yb <= 1:
            assert wa <= wb, "lower cavity narrows along an upward ray"
        else:
            assert ya >= 1 and min(wa, wb) >= HALF_NECK, \
                "upper cavity violates the half-unit free strip"
    return profile


def verify_critical_escape(n, element):
    """Enclose the entire true eroded body and exhibit exact support points.

    Let E=A eroded by delta K. A centered disk of radius 1/2 is inside E;
    S bounds E by a strip with half-width 1/2 in the active normal; C
    bounds E inside a rotation-invariant disk strictly inside Q subset A.
    The full turn is therefore free. Rotated E has projection EXACTLY
    [-1/2,1/2], with equality witnessed by the contained disk, and its
    full upward ray is free by verify_upward_closure. Empty bodies and
    convex-hull substitution cannot make these checks pass vacuously.
    """
    values = exact.family_values(n, element)
    edge = next(e for e in values["e_star"] if e["u1"] >= 0)
    delta = values["delta"]
    assert exact.strip_condition(n, edge), "S fails: this is not a strip escape case"
    disk_margins = verify_disk_subset(n, element, delta)
    radius = exact.verify_C(n, element, delta)
    cosine, sine = rotation_to_horizontal(edge)
    assert cosine*cosine+sine*sine == 1, "rotation must be exactly orthogonal"
    mx, my = edge["normal"]
    root = exact.Surd(0, 1, edge["norm_squared"])
    assert cosine*root == mx and -sine*root == my, "rotation does not align the active normal"
    width = (edge["offset"]-delta*edge["support"])/root
    assert width == HALF_NECK, "critical strip half-width is not exactly 1/2"
    # These are actual points of E, because the WHOLE half-unit disk is
    # inside E. They are not merely vertices of an outer approximation.
    witnesses = tuple((sign*HALF_NECK*cosine, 1-sign*HALF_NECK*sine)
                      for sign in (-1, 1))
    for x, y in witnesses:
        assert x*x+(y-1)*(y-1) == F(1, 4), "support witness left the half-unit disk"
    endpoints = tuple(rotated_point(p, cosine, sine) for p in witnesses)
    assert endpoints == ((-HALF_NECK, 1), (HALF_NECK, 1)), \
        "rotated contained witnesses must attain both strip boundaries"
    profile = verify_upward_closure(n)
    return dict(status="EXACT_CRITICAL_ESCAPE", delta=delta,
                chord=(edge["u1"], edge["u2"]), cosine=cosine, sine=sine,
                horizontal=(-width, width), witnesses=witnesses,
                rotated_witnesses=endpoints, disk_support_checks=len(disk_margins),
                radius_squared=radius["radius_squared"],
                wall_radius_squared=radius["wall_radius_squared"],
                upward_cells=len(profile)-1,
                body_scope="true nonconvex erosion, via separate inner and outer inclusions")
