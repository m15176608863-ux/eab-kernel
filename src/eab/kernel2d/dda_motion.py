"""DDA-anchored rational rotation plus symmetric constant strain (P2).

The parameters specify a chosen interpolant, not the solver's physical path.
The exact first-entrance domain is a single simple ring and the sufficient
non-inversion condition 2*||E||_infinity < 1. No rounded predicate is used.
Proofs and numerical contracts: docs/m5b_motion_theory.md and
docs/m5b_numeric_inventory.md. Semantic gates: tests/test_m5b_motion.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache

from .algebraic import RealAlgebraic, p_add, p_sub, p_mul, p_divmod
from .exact import polygons_overlap_exact
from .global_entrance import _ring
from .motion import QuadraticTime
from .se2 import SE2Entrance2, _event_times, _features


def _q(value):
    if not isinstance(value, (int, F)) or isinstance(value, bool):
        raise ValueError("DDA motion requires exact integers or Fractions")
    return F(value)


def _point(value):
    if len(value) != 2:
        raise ValueError("DDA motion requires two-dimensional points")
    return tuple(_q(v) for v in value)


def _matrix(value):
    if len(value) != 2:
        raise ValueError("DDA strain requires a two by two matrix")
    matrix = tuple(_point(row) for row in value)
    if matrix[0][1] != matrix[1][0]:
        raise ValueError("DDA strain must be symmetric")
    return matrix


def _apply(matrix, point):
    return tuple(sum(matrix[i][j]*point[j] for j in (0, 1)) for i in (0, 1))


def area_centroid(ring):
    """Exact signed-area centroid, not a vertex mean.

    Gate: test_area_centroid_is_area_weighted_and_frame_covariant.
    """
    points = _ring(tuple(_point(p) for p in ring))
    weights = tuple(p[0]*points[(i+1) % len(points)][1]
                    -p[1]*points[(i+1) % len(points)][0] for i, p in enumerate(points))
    twice_area = sum(weights)
    return tuple(sum((p[k]+points[(i+1) % len(points)][k])*w
                     for i, (p, w) in enumerate(zip(points, weights)))/(3*twice_area)
                 for k in (0, 1))


def _trig_bounds(theta, bits):
    """Alternating rational Taylor enclosures on |theta| <= 1."""
    theta = _q(theta)
    if abs(theta) > 1:
        raise ValueError("certified DDA angle approximation requires |theta|<=1")
    if not isinstance(bits, int) or isinstance(bits, bool) or not 8 <= bits <= 512:
        raise ValueError("angle approximation bits must be an integer in [8,512]")
    x, target = abs(theta), F(1, 1 << (bits+4))
    result = []
    for parity in (1, 0):
        term, total, index = (x if parity else F(1)), F(0), 0
        while True:
            total += term
            degree = 2*index+parity
            following = -term*x*x/((degree+1)*(degree+2))
            if abs(following) <= target:
                lower, upper = sorted((total, total+following))
                break
            term, index = following, index+1
        if parity and theta < 0:
            lower, upper = -upper, -lower
        result.append((lower, upper))
    return tuple(result)


@dataclass(frozen=True)
class HalfAngleApproximation:
    """Exact enclosure of tan(theta/2); not a binary64 tan evaluation."""
    theta: F
    u1: F
    lower: F
    upper: F

    def __post_init__(self):
        for name in ("theta", "u1", "lower", "upper"):
            object.__setattr__(self, name, _q(getattr(self, name)))
        if self.lower > self.upper or abs(self.theta) > 1 or abs(self.u1) > 1:
            raise ValueError("invalid certified half-angle fields")

    @property
    def error(self):
        return max(abs(self.u1-self.lower), abs(self.u1-self.upper))


def rational_half_angle(theta, bits=80):
    """Dyadic tan(theta/2) proposal with a rigorous absolute error enclosure.

    Gate: test_half_angle_has_independent_taylor_enclosure_and_zero_exactness.
    The returned enclosure uses sin(theta)/(1+cos(theta)); denominator > 1
    on the supported angle domain. Rounding occurs in rational arithmetic.
    """
    theta = _q(theta)
    (sl, su), (cl, cu) = _trig_bounds(theta, bits)
    quotients = tuple(s/(1+c) for s in (sl, su) for c in (cl, cu))
    lower, upper = min(quotients), max(quotients)
    grid = 1 << bits
    u = F(round((lower+upper)*grid/2), grid)
    return HalfAngleApproximation(theta, u, lower, upper)


@dataclass(frozen=True)
class DDAAnchoredMotion:
    """P2: c+s*d+[R(s*u1)+s*E](x-c), E symmetric and |u1|<=1.

    c is explicit here; dda_motion_from_z supplies the exact area centroid.
    Gate: test_p2_coordinates_match_independent_complex_product_oracle.
    """
    u1: F = F(0)
    translation: tuple = (F(0), F(0))
    center: tuple = (F(0), F(0))
    strain: tuple = ((F(0), F(0)), (F(0), F(0)))

    def __post_init__(self):
        object.__setattr__(self, "u1", _q(self.u1))
        object.__setattr__(self, "translation", _point(self.translation))
        object.__setattr__(self, "center", _point(self.center))
        object.__setattr__(self, "strain", _matrix(self.strain))
        if abs(self.u1) > 1:
            raise ValueError("DDA rational rotation requires |u1|<=1")

    @property
    def orientation_preserving_sufficient(self):
        return 2*max(sum(abs(x) for x in row) for row in self.strain) < 1

    def at(self, point, s):
        point, s = _point(point), _q(s)
        if not 0 <= s <= 1:
            raise ValueError("DDA time must be in the closed unit window")
        x, y = tuple(point[k]-self.center[k] for k in (0, 1))
        u, e = s*self.u1, _apply(self.strain, (x, y))
        denominator = 1+u*u
        return (self.center[0]+s*(self.translation[0]+e[0])+((1-u*u)*x-2*u*y)/denominator,
                self.center[1]+s*(self.translation[1]+e[1])+(2*u*x+(1-u*u)*y)/denominator)

    def endpoint(self, point):
        return self.at(point, F(1))

    def coordinate_polynomials(self, point):
        """Return ((Nx,Ny),D), ascending coefficients; X=(Nx,Ny)/D.

        Degree Nx,Ny<=3, D=1+u1**2*s**2>0. This exact certificate is suitable
        for rational interval bounds. Gate: test_coordinate_polynomial_identity.
        """
        point = _point(point)
        local = tuple(point[k]-self.center[k] for k in (0, 1))
        denominator = (F(1), F(0), self.u1*self.u1)
        vectors = _local_numerators(self, local)
        return (tuple(p_add(p_mul((self.center[k], self.translation[k]), denominator), vectors[k])
                      for k in (0, 1)), denominator)


def dda_motion_from_z(ring, z, bits=80):
    """Interpret z=(dx,dy,theta,ex,ey,gxy) with area centroid and E12=gxy/2.

    Gate: test_dda_z_mapping_uses_area_centroid_and_engineering_shear.
    """
    if len(z) != 6:
        raise ValueError("DDA z must contain exactly six components")
    dx, dy, theta, ex, ey, shear = tuple(_q(v) for v in z)
    approximation = rational_half_angle(theta, bits)
    return DDAAnchoredMotion(approximation.u1, (dx, dy), area_centroid(ring),
                             ((ex, shear/2), (shear/2, ey)))


def p2_p3_bound(ring, motion, theta, bits=80):
    """Uniform Euclidean (hence coordinatewise) P2/P3 displacement bound.

    P3 uses exactly the same c,d,E and angle theta. Gate:
    test_p2_p3_uniform_bound_contains_independent_interval_trigonometry.
    This bounds the specified P3 only, never an unknown physical trajectory.
    """
    if not isinstance(motion, DDAAnchoredMotion):
        raise ValueError("P2/P3 bound requires DDAAnchoredMotion")
    half = rational_half_angle(theta, bits)
    error = max(abs(motion.u1-half.lower), abs(motion.u1-half.upper))
    points = tuple(_point(p) for p in ring)
    if not points:
        raise ValueError("P2/P3 bound requires nonempty vertices")
    radius = max(sum(abs(p[k]-motion.center[k]) for k in (0, 1)) for p in points)
    time_law, parameter = abs(motion.u1)**3/2, 2*error
    return {"radius_l1": radius, "time_law_angle": time_law,
            "parameter_angle": parameter, "half_angle_error": error,
            "position": radius*(time_law+parameter)}


def _local_numerators(motion, local):
    x, y = local
    u, e = motion.u1, _apply(motion.strain, local)
    return ((x, -2*u*y+e[0], -u*u*x, u*u*e[0]),
            (y, 2*u*x+e[1], -u*u*y, u*u*e[1]))


def _pcross(a, b):
    return p_sub(p_mul(a[0], b[1]), p_mul(a[1], b[0]))


def _pdot(a, b):
    return p_add(p_mul(a[0], b[0]), p_mul(a[1], b[1]))


@dataclass(frozen=True)
class _DDARing:
    start: tuple
    motion: DDAAnchoredMotion
    local: tuple
    vectors: tuple
    edges: tuple
    denominator: tuple
    vertex_ids: tuple
    edge_ids: tuple


@lru_cache(maxsize=512)
def _validated_ring(start, motion):
    if not motion.orientation_preserving_sufficient:
        raise ValueError("DDA first entrance requires 2*||E||_infinity < 1; otherwise unsupported")
    normalized = _ring(start)
    n = len(start)
    if normalized == start:
        indices, edge_ids = tuple(range(n)), tuple(range(n))
    else:
        indices = tuple(reversed(range(n)))
        edge_ids = tuple((i-1) % n for i in indices)
    local = tuple(tuple(p[k]-motion.center[k] for k in (0, 1)) for p in normalized)
    vectors = tuple(_local_numerators(motion, p) for p in local)
    edges = tuple(_local_numerators(motion, tuple(local[(i+1) % n][k]-p[k] for k in (0, 1)))
                  for i, p in enumerate(local))
    return _DDARing(normalized, motion, local, vectors, edges,
                    (F(1), F(0), motion.u1*motion.u1), indices, edge_ids)


def _divide_positive_factor(poly, denominator):
    quotient, remainder = p_divmod(poly, denominator)
    if any(remainder):
        raise ArithmeticError("DDA positive denominator factor did not divide exactly")
    return quotient


def _line_polynomials(a, i, b, j):
    """Exact orientation and projection numerators over positive D_A*D_B.

    Every returned polynomial has degree <=6 after exact D_B cancellation.
    Gate: test_sixth_degree_events_match_independent_seven_sample_oracle.
    """
    m, n = a.motion, b.motion
    relative = tuple((m.center[k]-n.center[k], m.translation[k]-n.translation[k]) for k in (0, 1))
    w = tuple(p_add(p_mul(relative[k], a.denominator), a.vectors[i][k]) for k in (0, 1))
    edge, origin = b.edges[j], b.vectors[j]
    f = p_sub(_pcross(edge, w), p_mul(a.denominator, _divide_positive_factor(_pcross(edge, origin), b.denominator)))
    g = p_sub(_pdot(edge, w), p_mul(a.denominator, _divide_positive_factor(_pdot(edge, origin), b.denominator)))
    length = p_mul(a.denominator, _divide_positive_factor(_pdot(edge, edge), b.denominator))
    h = p_sub(length, g)
    if any(len(poly) > 7 for poly in (f, g, h)):
        raise ArithmeticError("DDA event exceeded the proved degree-six bound")
    return f, g, h


def projected_sweep(ring, motion, direction):
    """Conservative all-time projection enclosure, not a sampled minimum gap.

    Gate: test_projected_sweep_contains_all_independent_rational_probes.
    """
    if not isinstance(motion, DDAAnchoredMotion):
        raise ValueError("DDA sweep requires DDAAnchoredMotion")
    points, direction = tuple(_point(p) for p in ring), _point(direction)
    if not points or not any(direction):
        raise ValueError("DDA sweep requires nonempty points and nonzero direction")
    bounds = []
    for point in points:
        local = tuple(point[k]-motion.center[k] for k in (0, 1))
        strain = _apply(motion.strain, local)
        origin = sum(direction[k]*point[k] for k in (0, 1))
        shift = sum(direction[k]*(motion.translation[k]+strain[k]) for k in (0, 1))
        radius = sum(abs(v) for v in direction)*2*abs(motion.u1)*sum(abs(v) for v in local)
        bounds.append((origin+min(F(0), shift)-radius, origin+max(F(0), shift)+radius))
    return min(lo for lo, _ in bounds), max(hi for _, hi in bounds)


def dda_first_entrance(A0, B0, motion_a=DDAAnchoredMotion(), motion_b=DDAAnchoredMotion()):
    """Exact P2 closed-window first contact and complete original-ID cover set.

    Reuses the verified M5a incidence/normal-cone reconstruction and return
    protocol, but not its rigid event formula. Zero strain/rotation use this
    same general path. Gate: test_complete_first_contact_matches_independent_oracle.
    """
    if not isinstance(motion_a, DDAAnchoredMotion) or not isinstance(motion_b, DDAAnchoredMotion):
        raise ValueError("DDA first entrance requires explicit DDAAnchoredMotion parameters")
    original = tuple(_point(p) for p in A0), tuple(_point(p) for p in B0)
    a, b = _validated_ring(original[0], motion_a), _validated_ring(original[1], motion_b)
    for direction in ((1, 0), (0, 1)):
        lo_a, hi_a = projected_sweep(a.start, motion_a, direction)
        lo_b, hi_b = projected_sweep(b.start, motion_b, direction)
        if hi_a < lo_b or hi_b < lo_a:
            return SE2Entrance2(-1, "no_contact", None, (), ())
    state = polygons_overlap_exact(a.start, b.start)
    if state == 1:
        return SE2Entrance2(1, "initial_overlap", None, (), (), original)
    events = tuple((p, q, tag, i, j, _line_polynomials(p, i, q, j))
                   for p, q, tag in ((a, b, "VE"), (b, a, "EV"))
                   for i in range(len(p.start)) for j in range(len(q.start)))
    if state == 0:
        time = RealAlgebraic.from_rational(0)
    else:
        time = None
        for *_, polynomials in events:
            for candidate in _event_times(*polynomials):
                if time is None or candidate < time:
                    time = candidate
        if time is None:
            return SE2Entrance2(-1, "no_contact", None, (), ())
    incidences, features = _features(time, a, b, events)
    rational = time.as_rational()
    return SE2Entrance2(state, "contact", QuadraticTime(rational) if rational is not None else time,
                        incidences, features)
