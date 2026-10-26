"""WO-T2c2 exact, hand-derived theorem oracle; only standard-library imports.

The oracle primitives are rational field arithmetic, support enumeration,
horizontal sections and affine interpolation. They do not call production
erosion, SE(2) paths, obstacle arrangements or either cage verifier. The
production erosion comparison belongs only to the separate test module.

All conclusions concern the specified finite 8-chord polygon, not a circle
limit or mechanical response. Algebraic values never pass through float.
"""
from fractions import Fraction as F


def _rational(value):
    if type(value) is int or isinstance(value, F):
        return F(value)
    raise TypeError("Q5 coefficients must be int or Fraction")


class Q5:
    """The ordered field Q(sqrt(5)); sign uses rational squared comparisons."""

    __slots__ = ("a", "b")

    def __init__(self, a=0, b=0):
        b = _rational(b)
        if isinstance(a, Q5) and b == 0:
            self.a, self.b = a.a, a.b
        else:
            self.a, self.b = _rational(a), _rational(b)

    def __repr__(self):
        return "Q5(" + str(self.a) + ", " + str(self.b) + ")"

    def __hash__(self):
        return hash(self.a) if self.b == 0 else hash((self.a, self.b))

    def __float__(self):
        raise TypeError("Q5 has no implicit or explicit floating conversion")

    def __add__(self, other):
        other = Q5(other)
        return Q5(self.a + other.a, self.b + other.b)

    def __radd__(self, other):
        return self + other

    def __neg__(self):
        return Q5(-self.a, -self.b)

    def __sub__(self, other):
        return self + -Q5(other)

    def __rsub__(self, other):
        return Q5(other) + -self

    def __mul__(self, other):
        other = Q5(other)
        return Q5(self.a * other.a + 5 * self.b * other.b,
                  self.a * other.b + self.b * other.a)

    def __rmul__(self, other):
        return self * other

    def __truediv__(self, other):
        other = Q5(other)
        norm = other.a * other.a - 5 * other.b * other.b
        if norm == 0:
            raise ZeroDivisionError("division by zero in Q5")
        return Q5((self.a * other.a - 5 * self.b * other.b) / norm,
                  (self.b * other.a - self.a * other.b) / norm)

    def __rtruediv__(self, other):
        return Q5(other) / self

    def __pow__(self, exponent):
        if not isinstance(exponent, int):
            raise TypeError("Q5 exponent must be an integer")
        if exponent < 0:
            inverse = Q5(1) / self
            return inverse ** -exponent
        result, factor = Q5(1), self
        while exponent:
            if exponent % 2:
                result = result * factor
            factor = factor * factor
            exponent //= 2
        return result

    def sign(self):
        a, b = self.a, self.b
        if a == 0:
            return (b > 0) - (b < 0)
        if b == 0 or a * b > 0:
            return (a > 0) - (a < 0)
        comparison = a * a - 5 * b * b
        return ((a > 0) - (a < 0)) * ((comparison > 0) - (comparison < 0))

    def __abs__(self):
        return -self if self.sign() < 0 else self

    def __eq__(self, other):
        if not isinstance(other, (Q5, F, int)):
            return NotImplemented
        other = Q5(other)
        return self.a == other.a and self.b == other.b

    def __lt__(self, other):
        return Q5.sign(self - other) < 0

    def __le__(self, other):
        return Q5.sign(self - other) <= 0

    def __gt__(self, other):
        return Q5.sign(self - other) > 0

    def __ge__(self, other):
        return Q5.sign(self - other) >= 0


SQRT5 = Q5(0, 1)
CENTER = (F(0), F(1))
MAIN_SUPPORT = {"square": F(3, 2), "octagon": F(29, 24)}
SECONDARY_BOUND = F(3)
ROTATION_COS_NUMERATOR = F(2)
OCTAGON_TOP_INTERCEPT = F(1, 3)
RADIUS_CAP_SQUARED = F(4, 5)
FLOOR_TOP = F(0)

MOVING_VERTICES = (
    (F(0), F(0)), (F(3, 5), F(1, 5)), (F(1), F(1)),
    (F(3, 5), F(9, 5)), (F(1, 2), F(11, 6)), (F(1, 2), F(2)),
    (F(-1, 2), F(2)), (F(-1, 2), F(11, 6)),
    (F(-3, 5), F(9, 5)), (F(-1), F(1)), (F(-3, 5), F(1, 5)),
)
Q_VERTICES = (
    (F(0), F(0)), (F(3, 5), F(1, 5)), (F(1), F(1)),
    (F(3, 5), F(9, 5)), (F(0), F(2)),
    (F(-3, 5), F(9, 5)), (F(-1), F(1)), (F(-3, 5), F(1, 5)),
)
CAVITY_PROFILE = (
    (F(0), F(0)), (F(1, 5), F(3, 5)), (F(1), F(1)),
    (F(9, 5), F(3, 5)), (F(11, 6), F(1, 2)), (F(2), F(1, 2)),
)


def truth_obstacles():
    """Hand-derived walls and floor; the open side is only above y=2."""
    left = ((F(-3), F(0)),) + tuple((-x, y) for x, y in MOVING_VERTICES[:6])
    left = left + ((F(-3), F(2)),)
    right = tuple((-x, y) for x, y in reversed(left))
    floor = ((F(-3), F(-2)), (F(3), F(-2)), (F(3), FLOOR_TOP), (F(-3), FLOOR_TOP))
    return left, right, floor


def element_vertices(element):
    if element == "square":
        return ((F(-1), F(-1)), (F(1), F(-1)),
                (F(1), F(1)), (F(-1), F(1)))
    if element == "octagon":
        a = F(5, 12)
        return ((-a, F(-1)), (a, F(-1)), (F(1), -a), (F(1), a),
                (a, F(1)), (-a, F(1)), (F(-1), a), (F(-1), -a))
    raise ValueError("unknown element")


def support(element, nx, ny):
    return max(nx * x + ny * y for x, y in element_vertices(element))


def critical_delta(element):
    return (4 - SQRT5) / (4 * MAIN_SUPPORT[element])


def critical_translation_delta(element):
    return F(1) / (2 * MAIN_SUPPORT[element])


def _right_vertices(element, delta):
    """Affine supports; octagon reflex line is x+y=7/3-17*delta/12.

    The octagon branch is the delta>2/7 branch at the critical point.
    In particular its top x intercept is 1/3, not the old draft's 1/2.
    """
    d = Q5(delta)
    if element == "square":
        return ((Q5(0), 4*d/3), (F(3, 5)-d, F(1, 5)+d),
                (1-3*d/2, Q5(1)), (F(3, 5)-d, F(9, 5)-d),
                (F(1, 2)-d, F(11, 6)-d), (F(1, 2)-d, 2-d))
    if element == "octagon":
        assert d > F(2, 7), "octagon symbolic branch requires delta>2/7"
        return ((Q5(0), 41*d/36),
                (F(3, 5)-23*d/30, F(1, 5)+53*d/60),
                (1-29*d/24, Q5(1)),
                (F(2, 3)-d, F(5, 3)-5*d/12),
                (OCTAGON_TOP_INTERCEPT-5*d/12, 2-d))
    raise ValueError("unknown element")


def symbolic_vertices(element, delta=None):
    d = critical_delta(element) if delta is None else Q5(delta)
    right = _right_vertices(element, d)
    polygon = right + tuple((-x, y) for x, y in reversed(right[1:]))
    start = min(range(len(polygon)), key=lambda index: polygon[index])
    return polygon[start:] + polygon[:start]


def _interpolate(profile, y):
    for (a, fa), (b, fb) in zip(profile, profile[1:]):
        if a <= y <= b:
            return fa + (fb-fa) * (y-a) / (b-a)
    raise ValueError("height outside closed profile")


def half_width(y):
    return _interpolate(CAVITY_PROFILE, Q5(y))


def _element_half_width(element, y):
    if element == "square":
        return Q5(1)
    if element == "octagon":
        return min(Q5(1), F(17, 12)-abs(y))
    raise ValueError("unknown element")


def eroded_half_width(element, delta, y):
    """Exact slice infimum over K, not only K's vertices.

    Include every cavity breakpoint crossing the element: this is what
    accounts for reflex-corner cuts missed by vertex-only containment.
    """
    d, y = Q5(delta), Q5(y)
    assert d <= y <= 2-d
    cuts = {Q5(vy) for _, vy in element_vertices(element)}
    for height, _ in CAVITY_PROFILE:
        vy = (height-y)/d
        if -1 <= vy <= 1:
            cuts.add(vy)
    return min(half_width(y+d*vy)-d*_element_half_width(element, vy)
               for vy in cuts)


def verify_symbolic_erosion(element):
    """Prove the symbolic ring by piecewise-affine horizontal sections.

    Breakpoints include all cavity-height minus element-height events and
    every claimed boundary vertex. On each cell the infimum is the minimum
    of finitely many affine functions, and the claimed width is affine.
    Equality at both endpoints and the midpoint makes one affine candidate
    identical to that width; all candidates stay above it. Thus this is an
    exact finite partition argument, not sampled numerical geometry.
    """
    d = critical_delta(element)
    right = _right_vertices(element, d)
    profile = tuple((y, x) for x, y in right)
    assert all(a[0] < b[0] for a, b in zip(profile, profile[1:]))
    assert right[0][0] == 0 and all(x > 0 for x, _ in right[1:])
    lo, hi = profile[0][0], profile[-1][0]
    assert lo == support(element, 1, -3)*d/3
    assert hi == 2-d
    # The global lower cone |x|<=3y excludes all y below lo after erosion.
    assert all(abs(x) <= 3*y for x, y in MOVING_VERTICES)
    assert all(0 <= y <= 2 for _, y in MOVING_VERTICES)
    cuts = {y for y, _ in profile}
    for height, _ in CAVITY_PROFILE:
        for _, vy in element_vertices(element):
            y = height-d*vy
            if lo < y < hi:
                cuts.add(y)
    ordered = sorted(cuts)
    checks = ordered + [(a+b)/2 for a, b in zip(ordered, ordered[1:])]
    for y in checks:
        assert eroded_half_width(element, d, y) == _interpolate(profile, y), \
            "independent section erosion differs from the symbolic boundary"
    return len(ordered), len(checks)


def lemma_a_metrics(element, delta=None):
    d = critical_delta(element) if delta is None else Q5(delta)
    h = support(element, 1, F(1, 2))
    h3 = support(element, 1, 3)
    radius = 2*(1-h*d)/SQRT5
    residual = SECONDARY_BOUND-d*h3
    return dict(delta=d, h=h, h3=h3, radius=radius,
                secondary_residual=residual,
                secondary_squared_margin=residual**2-10*radius**2)


def verify_a_zero():
    assert SECONDARY_BOUND > 0
    assert SECONDARY_BOUND**2 > 8, "g(0)=b-2sqrt(2) must be strictly positive"


def verify_a_critical(element):
    m = lemma_a_metrics(element)
    assert all(support(element, sx, 3*sy) == m["h3"]
               for sx in (-1, 1) for sy in (-1, 1))
    assert m["secondary_residual"] > 0
    assert m["secondary_squared_margin"] > 0, "g(delta critical) must be positive"
    return m


def verify_a_main(element):
    m = lemma_a_metrics(element)
    assert MAIN_SUPPORT[element] == m["h"], "declared support differs from element vertices"
    assert all(support(element, sx, F(sy, 2)) == m["h"]
               for sx in (-1, 1) for sy in (-1, 1))
    assert m["radius"]*SQRT5/2+m["delta"]*m["h"] == 1
    assert m["radius"] == F(1, 2), "critical main-chord equality must be exact"
    return m


def verify_lemma_a(element):
    verify_a_zero()
    verify_a_critical(element)
    return verify_a_main(element)


def q_edge_distance_squares():
    distances = []
    for a, b in zip(Q_VERTICES, Q_VERTICES[1:]+Q_VERTICES[:1]):
        dx, dy = b[0]-a[0], b[1]-a[1]
        cross = dx*(CENTER[1]-a[1])-dy*(CENTER[0]-a[0])
        assert cross > 0, "center must be strictly inside the oriented edge"
        distances.append(cross*cross/(dx*dx+dy*dy))
    return tuple(distances)


def verify_c_edges():
    distances = q_edge_distance_squares()
    assert distances.count(F(4, 5)) == 4, "Q must have four main squared distances 4/5"
    assert distances.count(F(9, 10)) == 4, "Q must have four secondary squared distances 9/10"
    return distances


def verify_q_containment():
    """Q subset A by every breakpoint of their piecewise-linear sections."""
    assert tuple((y, x) for x, y in MOVING_VERTICES[:6]) == CAVITY_PROFILE
    profile = tuple((y, x) for x, y in Q_VERTICES[:5])
    assert all(a[0] < b[0] for a, b in zip(profile, profile[1:]))
    cuts = sorted({y for y, _ in CAVITY_PROFILE} | {y for y, _ in profile})
    assert all(0 <= _interpolate(profile, y) <= half_width(y) for y in cuts)
    return len(cuts)


def verify_c_radius(element):
    polygon = symbolic_vertices(element)
    squares = tuple(x*x+(y-1)*(y-1) for x, y in polygon)
    maximum = max(squares)
    assert maximum < RADIUS_CAP_SQUARED, "rotation disk must lie strictly inside Q"
    expected = (Q5(F(5, 12), F(1, 18)) if element == "square"
                else Q5(F(8509, 30276), F(175, 2523)))
    assert maximum == expected
    farthest = tuple(p for p, r in zip(polygon, squares) if r == maximum)
    assert len(farthest) == 2
    assert all(y == 2-critical_delta(element) for _, y in farthest)
    return maximum, farthest


def verify_lemma_c(element):
    verify_c_edges()
    verify_q_containment()
    return verify_c_radius(element)


def verify_lemma_d():
    assert len(MOVING_VERTICES) == 11
    projections = tuple(x+(y-1)/2 for x, y in MOVING_VERTICES)
    assert min(projections) == -1 and max(projections) == 1, \
        "all eleven vertices must satisfy the strip with both sides attained"
    assert all(abs(v) <= 1 for v in projections), "all eleven vertices must satisfy the strip"
    return projections


def rotate_minus_phi(vertices):
    cosine, sine = ROTATION_COS_NUMERATOR/SQRT5, -1/SQRT5
    return tuple((cosine*x-sine*(y-1), 1+sine*x+cosine*(y-1))
                 for x, y in vertices)


def verify_e_vertical(element):
    polygon = rotate_minus_phi(symbolic_vertices(element))
    lo, hi = min(y for _, y in polygon), max(y for _, y in polygon)
    assert Q5(F(1, 2), F(-1, 25)) <= lo <= hi <= Q5(F(3, 2), F(1, 10)), \
        "rotated polygon must lie inside the stated common vertical envelope"
    expected = ((Q5(F(1, 2), F(-1, 25)), Q5(F(3, 2), F(1, 10)))
                if element == "square" else
                (Q5(F(69, 145), F(-3, 145)), Q5(F(3, 2), F(1, 15))))
    assert (lo, hi) == expected
    assert lo > F(1, 6)
    return lo, hi


def verify_e_cavity():
    # An affine function's minimum is attained at an endpoint on every cell.
    left, right, floor = truth_obstacles()
    inner_left = tuple((-width, height) for height, width in CAVITY_PROFILE)
    assert all(y <= F(1, 6) for _, y in floor), "floor interior must stay below the exit strip"
    cuts = (F(1, 6),) + tuple(y for y, _ in CAVITY_PROFILE if y > F(1, 6))
    widths = tuple(half_width(y) for y in cuts)
    assert all(w >= F(1, 2) for w in widths), "the infinite exit strip must be wall-free"
    assert min(widths) == F(1, 2)
    assert left[1:-1] == inner_left
    assert right == tuple((-x, y) for x, y in reversed(left))
    assert all(0 <= y <= 2 for wall in (left, right) for _, y in wall)
    assert left[0][0] == left[-1][0] == -3
    assert cuts[0] > 0 and cuts[-1] == 2
    return cuts, widths


def verify_lemma_e(element):
    verify_e_cavity()
    return verify_e_vertical(element)


def verify_critical_horizontal(element):
    polygon = rotate_minus_phi(symbolic_vertices(element))
    horizontal = min(x for x, _ in polygon), max(x for x, _ in polygon)
    assert horizontal == (Q5(F(-1, 2)), Q5(F(1, 2))), \
        "critical horizontal projection must be exactly [-1/2,1/2]"
    return horizontal


def verify_translation(element):
    h = support(element, 1, F(1, 2))
    threshold = critical_translation_delta(element)
    assert 1-h*threshold == F(1, 2), "translation threshold must exactly fit the neck"
    assert all(abs(x)+(abs(y-1)/2) <= 1 for x, y in MOVING_VERTICES)
    assert support(element, 1, -3)*threshold/3 > F(1, 6)
    verify_e_cavity()
    # Direct slice minimization, independent of erode_polygon_exact, proves
    # the claimed horizontal endpoints are present at and around threshold.
    for d in (threshold-F(1, 128), threshold, threshold+F(1, 128)):
        assert eroded_half_width(element, d, 1) == 1-h*d
        if d < threshold:
            assert 2*(1-h*d) > 1
        else:
            assert 2*(1-h*d) <= 1
    assert critical_delta(element)/threshold == Q5(2, F(-1, 2))
    return threshold


def verify_critical_escape(element):
    """Whole-turn disk containment followed by a whole-ray strip argument.

    A polygon lies in the disk if all its vertices do, by disk
    convexity. Rotation preserves that disk. After the exact turn every
    vertex is in the closed vertical strip, hence every polygon point is;
    adding any nonnegative height preserves that strip. Boundary contact is
    permitted. No SE(2) verifier, rational angle proxy or time sample is used.
    """
    sections = verify_symbolic_erosion(element)
    verify_lemma_a(element)
    radius, farthest = verify_lemma_c(element)
    verify_lemma_d()
    vertical = verify_lemma_e(element)
    cosine, sine = ROTATION_COS_NUMERATOR/SQRT5, -1/SQRT5
    assert cosine*cosine+sine*sine == 1
    polygon = rotate_minus_phi(symbolic_vertices(element))
    horizontal = verify_critical_horizontal(element)
    assert all(F(-1, 2) <= x <= F(1, 2) and y > F(1, 6) for x, y in polygon)
    return dict(vertices=len(polygon), sections=sections, radius_squared=radius,
                farthest=farthest, horizontal=horizontal, vertical=vertical,
                status="EXACT_CRITICAL_ESCAPE")
