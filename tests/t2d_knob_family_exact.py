"""WO-T2d independent rational and quadratic-field family oracle.

Primitives are rational chord construction, support enumeration, exact sign
algebra and half-plane intersections. No production geometry, erosion,
SE(2) path code or verifier is imported. Hull erosion is only an OUTER
bound for the nonconvex erosion, never asserted to be the erosion itself.
"""
from fractions import Fraction as F
from math import isqrt

COMPARE_SQUARE_SIGN = 1


def rational(value):
    if type(value) is int or isinstance(value, F):
        return F(value)
    raise TypeError("only exact rational coefficients are accepted")


def _sign(value):
    return (value > 0) - (value < 0)


def _one_root_sign(a, b, q):
    if not b:
        return _sign(a)
    if not a:
        return _sign(b)
    if _sign(a) == _sign(b):
        return _sign(a)
    return _sign(a) * _sign(a*a-b*b*q)


class Surd:
    """a+b sqrt(q), with exact comparisons even across quadratic fields.

    For x=A+B sqrt(q), y=C sqrt(r), matching signs determine sign(x+y).
    Opposite signs reduce to sign(x)*sign(x*x-y*y); the second factor
    contains only sqrt(q). This also terminates for exact equalities.
    Multiplication and division deliberately require one common field.
    """

    __slots__ = ("a", "b", "q")
    __hash__ = None

    def __init__(self, a=0, b=0, q=1):
        if isinstance(a, Surd) and b == 0:
            self.a, self.b, self.q = a.a, a.b, a.q
            return
        self.a, self.b, self.q = rational(a), rational(b), rational(q)
        if self.q <= 0:
            raise ValueError("positive radicand required")
        numerator = isqrt(self.q.numerator)
        denominator = isqrt(self.q.denominator)
        if numerator*numerator == self.q.numerator and denominator*denominator == self.q.denominator:
            self.a += self.b*F(numerator, denominator)
            self.b, self.q = F(0), F(1)
        if not self.b:
            self.q = F(1)

    def __repr__(self):
        return "Surd(" + str(self.a) + ", " + str(self.b) + ", " + str(self.q) + ")"

    def __float__(self):
        raise TypeError("Surd forbids floating conversion")

    def __bool__(self):
        return self.sign() != 0

    def sign(self):
        return _one_root_sign(self.a, self.b, self.q)

    def compare(self, other):
        other = Surd(other)
        a, b, c = self.a-other.a, self.b, -other.b
        sx, sy = _one_root_sign(a, b, self.q), _sign(c)
        if not sx:
            return sy
        if not sy or sx == sy:
            return sx
        return COMPARE_SQUARE_SIGN*sx*_one_root_sign(a*a+b*b*self.q-c*c*other.q, 2*a*b, self.q)

    def __eq__(self, other):
        return self.compare(other) == 0

    def __lt__(self, other):
        return self.compare(other) < 0

    def __le__(self, other):
        return self.compare(other) <= 0

    def __gt__(self, other):
        return self.compare(other) > 0

    def __ge__(self, other):
        return self.compare(other) >= 0

    def __neg__(self):
        return Surd(-self.a, -self.b, self.q)

    def __abs__(self):
        return -self if self.sign() < 0 else self

    def _in_field(self, q):
        ratio = self.q/q
        numerator, denominator = isqrt(ratio.numerator), isqrt(ratio.denominator)
        if numerator*numerator != ratio.numerator or denominator*denominator != ratio.denominator:
            raise TypeError("arithmetic requires the same quadratic field")
        return Surd(self.a, self.b*F(numerator, denominator), q)

    def __add__(self, other):
        other = Surd(other)
        if not self.b:
            return Surd(self.a+other.a, other.b, other.q)
        if not other.b:
            return Surd(self.a+other.a, self.b, self.q)
        if self.q != other.q:
            other = other._in_field(self.q)
        return Surd(self.a+other.a, self.b+other.b, self.q)

    def __radd__(self, other):
        return self+other

    def __sub__(self, other):
        return self+-Surd(other)

    def __rsub__(self, other):
        return Surd(other)+-self

    def __mul__(self, other):
        other = Surd(other)
        if not self.b:
            return Surd(self.a*other.a, self.a*other.b, other.q)
        if not other.b:
            return Surd(self.a*other.a, self.b*other.a, self.q)
        if self.q != other.q:
            other = other._in_field(self.q)
        return Surd(self.a*other.a+self.b*other.b*self.q,
                    self.a*other.b+self.b*other.a, self.q)

    def __rmul__(self, other):
        return self*other

    def __truediv__(self, other):
        other = Surd(other)
        norm = other.a*other.a-other.b*other.b*other.q
        if not norm:
            raise ZeroDivisionError("zero algebraic divisor")
        return self*Surd(other.a/norm, -other.b/norm, other.q)

    def __rtruediv__(self, other):
        return Surd(other)/self

    def bounds(self, bits=80):
        """Closed rational enclosure, solely integer isqrt and division."""
        scale = 1 << bits
        lower = F(isqrt(self.q.numerator*scale*scale//self.q.denominator), scale)
        upper = lower if lower*lower == self.q else lower+F(1, scale)
        endpoints = self.a+self.b*lower, self.a+self.b*upper
        return min(endpoints), max(endpoints)


CENTER = (F(0), F(1))
NECK_HEIGHTS = {4: F(11, 6), 8: F(37, 20), 16: F(67, 36), 32: F(567, 304)}
ARC_VERTICAL_FACTOR = F(2)
Q_REFLECTION_SIGN = -1
CLIPPED_NECK_WIDTH = F(1, 2)
DISK_RADIUS = F(1, 2)
STRIP_BOUND_SCALE = F(1)
TRANSLATION_INTERCEPT = F(1)
EROSION_SUPPORT_SCALE = F(1)
RATIO_SCALE = F(1)
FACET_RADICAND_ADDEND = 4
CIRCLE_POLYNOMIAL_FACTOR = F(3)
CIRCLE_RATIO_K16_A = F(99, 303)


def element_vertices(element):
    if element == "square":
        return tuple((F(x), F(y)) for x in (-1, 1) for y in (-1, 1))
    if element == "octagon":
        pairs = ((F(1), F(5, 12)), (F(5, 12), F(1)))
    elif element == "K16":
        pairs = ((F(99, 101), F(20, 101)), (F(20, 101), F(99, 101)),
                 (F(91, 109), F(60, 109)), (F(60, 109), F(91, 109)))
    else:
        raise ValueError("unknown tolerance element")
    return tuple((sx*x, sy*y) for x, y in pairs for sx in (-1, 1) for sy in (-1, 1))


def support(element, nx, ny):
    return max(nx*x+ny*y for x, y in element_vertices(element))


def full_arc(n):
    if not isinstance(n, int) or isinstance(n, bool) or n < 4 or n % 4:
        raise ValueError("a multiple of four is required")
    parameters = tuple(F(2*i, n)-1 for i in range(n+1))
    return tuple(((1-u*u)/(1+u*u), 1+ARC_VERTICAL_FACTOR*u/(1+u*u)) for u in parameters)


def family_geometry(n):
    full = full_arc(n)
    kept = []
    for p in full:
        if kept and p[1] > 1 and p[0] <= F(1, 2):
            x, y = kept[-1]
            t = (F(1, 2)-x)/(p[0]-x)
            kept.append((CLIPPED_NECK_WIDTH, y+t*(p[1]-y)))
            break
        kept.append(p)
    neck = kept[-1][1]
    right = tuple(kept)+((F(1, 2), F(2)),)
    moving = right+tuple((-x, y) for x, y in reversed(right[1:]))
    polygon = full+tuple((Q_REFLECTION_SIGN*x, y) for x, y in reversed(full[1:-1]))
    return dict(A=moving, Q=polygon, right_profile=tuple((y, x) for x, y in right),
                q_profile=tuple((y, x) for x, y in full), neck_height=neck)


def interpolate(profile, height):
    for (a, fa), (b, fb) in zip(profile, profile[1:]):
        if a <= height <= b:
            return fa+(fb-fa)*(height-a)/(b-a)
    raise ValueError("height outside the profile")


def verify_family_geometry(n):
    g = family_geometry(n)
    q, a = g["Q"], g["A"]
    assert len(q) == 2*n, "Q must retain every distinct circle sample"
    assert all(x*x+(y-1)*(y-1) == 1 for x, y in q), "Q sample left the unit circle"
    assert set(q) == {(-x, 2-y) for x, y in q}, "Q central symmetry failed"
    assert set(q) == {(-x, y) for x, y in q}, "Q reflection symmetry failed"
    assert len(set(q)) == len(q), "Q samples must remain distinct"
    assert all(_cross(q[i-2], q[i-1], q[i]) > 0 for i in range(len(q))), "Q vertex order is not strictly convex"
    assert a == tuple((width, height) for height, width in g["right_profile"])+tuple(
        (-width, height) for height, width in reversed(g["right_profile"][1:])), "A chain mismatch"
    cuts = sorted({y for y, _ in g["right_profile"]} | {y for y, _ in g["q_profile"]})
    assert all(0 <= interpolate(g["q_profile"], y) <= interpolate(g["right_profile"], y)
               for y in cuts), "Q containment failed at a linear-section breakpoint"
    assert interpolate(g["q_profile"], g["neck_height"]) == F(1, 2), "neck is not on Q"
    if n in NECK_HEIGHTS:
        assert g["neck_height"] == NECK_HEIGHTS[n], "neck height differs from theorem table"
    return g


def edge_candidates(n, element):
    parameters = tuple(F(2*i, n)-1 for i in range(n+1))
    out = []
    for u, v in zip(parameters, parameters[1:]):
        m, r = (1-u*v, u+v), 1+u*v
        q = m[0]*m[0]+m[1]*m[1]
        h = support(element, *m)
        out.append(dict(delta=Surd(r/h, -DISK_RADIUS/h, q), u1=u, u2=v,
                        normal=m, offset=r, norm_squared=q, support=h,
                        translation=(TRANSLATION_INTERCEPT+3*u*v)/(2*h)))
    return tuple(out)


def strip_condition(n, edge):
    m, r = edge["normal"], edge["offset"]
    return all(abs(m[0]*x+m[1]*(y-1)) <= STRIP_BOUND_SCALE*r for x, y in family_geometry(n)["A"])


def _cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def convex_hull(points):
    ordered = sorted(set(points))
    lower, upper = [], []
    for p in ordered:
        while len(lower) > 1 and _cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(ordered):
        while len(upper) > 1 and _cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return tuple(lower[:-1]+upper[:-1])


def hull_constraints(n, element, delta):
    """Centered support inequalities for conv(A) eroded by delta K."""
    polygon = convex_hull(family_geometry(n)["A"])
    constraints = []
    for a, b in zip(polygon, polygon[1:]+polygon[:1]):
        normal = (b[1]-a[1], a[0]-b[0])
        offset = normal[0]*a[0]+normal[1]*(a[1]-1)
        constraints.append((normal, offset-EROSION_SUPPORT_SCALE*delta*support(element, *normal)))
    return tuple(constraints)


def eroded_convex_hull(n, element, delta):
    """Exact OUTER-bound vertices, in original coordinates (center=(0,1))."""
    constraints = hull_constraints(n, element, Surd(delta))
    vertices = []
    for i, (m, r) in enumerate(constraints):
        for v, s in constraints[i+1:]:
            det = m[0]*v[1]-m[1]*v[0]
            if not det:
                continue
            x, y = (r*v[1]-s*m[1])/det, (m[0]*s-v[0]*r)/det
            if all(u[0]*x+u[1]*y <= b for u, b in constraints):
                p = (x, y+1)
                if p not in vertices:
                    vertices.append(p)
    assert vertices, "empty hull bound is not a radius certificate"
    return tuple(vertices)


def verify_C(n, element, delta=None):
    edges = edge_candidates(n, element)
    d = min(edge["delta"] for edge in edges) if delta is None else Surd(delta)
    vertices = eroded_convex_hull(n, element, d)
    radius_squared = max(x*x+(y-1)*(y-1) for x, y in vertices)
    wall_radius_squared = min(edge["offset"]*edge["offset"]/edge["norm_squared"] for edge in edges)
    assert radius_squared < wall_radius_squared, "C rotation radius is not strictly below the wall bound"
    return dict(radius_squared=radius_squared, wall_radius_squared=wall_radius_squared,
                vertices=vertices)


TABLE = {
    (4, "square"): (Surd(F(2, 3), F(-1, 6), 5), F(1, 3), True, (F(0), F(1, 2))),
    (4, "octagon"): (Surd(F(24, 29), F(-6, 29), 5), F(12, 29), True, (F(0), F(1, 2))),
    (4, "K16"): (Surd(F(109, 121), F(-109, 484), 5), F(109, 242), True, (F(0), F(1, 2))),
    (8, "square"): (Surd(F(9, 13), F(-1, 26), 85), F(2, 5), False, (F(1, 4), F(1, 2))),
    (8, "octagon"): (Surd(F(48, 53), F(-6, 53), 17), F(24, 53), True, (F(0), F(1, 4))),
    (8, "K16"): (Surd(F(101, 104), F(-101, 832), 17), F(101, 208), True, (F(0), F(1, 4))),
    (16, "square"): (Surd(F(19, 27), F(-1, 54), 365), F(35, 86), False, (F(3, 8), F(1, 2))),
    (16, "octagon"): (Surd(F(11, 12), F(-1, 72), 1105), F(48, 101), True, (F(1, 8), F(1, 4))),
    (16, "K16"): (Surd(F(3815, 3839), F(-109, 7678), 1241), F(101, 203), True, (F(1, 4), F(3, 8))),
    (32, "square"): (Surd(F(149, 211), F(-1, 422), 22265), F(73, 178), False, (F(3, 8), F(7, 16))),
    (32, "octagon"): (Surd(F(201, 218), F(-3, 436), 4505), F(131, 274), True, (F(3, 16), F(1, 4))),
    (32, "K16"): (Surd(F(4343, 4351), F(-101, 26106), 16705), F(202, 401), True, (F(1, 16), F(1, 8))),
}


def family_values(n, element):
    edges = edge_candidates(n, element)
    delta = min(edge["delta"] for edge in edges)
    minima = tuple(edge for edge in edges if edge["delta"] == delta)
    translation = min(edge["translation"] for edge in edges)
    ratio = RATIO_SCALE*delta/translation
    return dict(delta=delta, e_star=minima, translation=translation,
                S=tuple(strip_condition(n, edge) for edge in minima), ratio=ratio,
                G=1-ratio, G_facet=Surd(-1, F(1, n), n*n+FACET_RADICAND_ADDEND))


def verify_values(n, element):
    values = family_values(n, element)
    delta, translation, strip, chord = TABLE[n, element]
    assert values["delta"] == delta, "disk threshold differs from theorem table"
    assert values["translation"] == translation, "all-chord translation threshold differs from theorem table"
    assert all(s == strip for s in values["S"]), "strip condition differs from theorem table"
    assert any((edge["u1"], edge["u2"]) == chord for edge in values["e_star"]), "minimizing chord differs from theorem table"
    assert values["ratio"] == delta/translation, "ratio differs from theorem table"
    return values


def circle_limits(element):
    """Exact circle-model limit; square SE(2) equality remains conjectural.

    (1/2,0)+delta*k first touches the unit circle at the smallest positive
    root of |k|^2 delta^2+k_x delta-3/4=0, minimized over all K vertices.
    A ratio with two radical terms is returned as a tuple, not rounded.
    """
    vertices = element_vertices(element)
    squared_radius = max(x*x+y*y for x, y in vertices)
    disk = Surd(0, F(1, 2)/squared_radius, squared_radius)
    candidates = tuple(Surd(-x/(2*(x*x+y*y)), F(1, 2)/(x*x+y*y),
                            x*x+CIRCLE_POLYNOMIAL_FACTOR*(x*x+y*y)) for x, y in vertices)
    translation = min(candidates)
    if element == "square":
        expected = Surd(F(-1, 4), F(1, 4), 7)
        ratio_terms = (Surd(0, F(1, 6), 14), Surd(0, F(1, 6), 2))
    elif element == "octagon":
        expected = Surd(F(-72, 169), F(6, 169), 651)
        ratio_terms = (Surd(F(12, 39), F(1, 39), 651),)
    else:
        expected = Surd(F(-99, 202), F(1, 101), 10101)
        ratio_terms = (Surd(CIRCLE_RATIO_K16_A, F(2, 303), 10101),)
    assert translation == expected, "circle translation root differs from theorem table"
    # The expected formula's polynomial identity and positive-root branch.
    active = tuple(k for k, candidate in zip(vertices, candidates) if candidate == translation)
    assert active
    for x, y in active:
        assert (x*x+y*y)*translation*translation+x*translation-F(3, 4) == 0
        assert translation > 0
    if element != "square":
        assert ratio_terms[0]*translation == disk, "circle ratio identity failed"
    else:
        # ((sqrt(14)+sqrt(2))/6)^2=(4+sqrt(7))/9.
        # With disk^2=1/8 this proves the positive ratio without mixed fields.
        first, second = ratio_terms
        assert first.a == second.a == 0
        ratio_squared = Surd(first.b*first.b*first.q+second.b*second.b*second.q,
                             2*first.b*second.b, first.q*second.q)
        assert ratio_squared*translation*translation == F(1, 8)
        assert all(term > 0 for term in ratio_terms)
    return dict(disk=disk, translation=translation, ratio_terms=ratio_terms, active_vertices=active)
