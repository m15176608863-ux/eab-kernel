"""Conservative exact certificates for specified continuous vertex tubes.

These are sufficient conditions, never a complete classifier. Unknown is not
contact and not robustness. Only a singleton, interior VE/EV cover is handled.
See docs/m5b_robustness_theory.md; gates: tests/test_m5b_robustness.py.
All radii are coordinate L-infinity bounds, not inferred physical-path errors.
"""
from fractions import Fraction as F
from math import comb
from .dda_motion import DDAAnchoredMotion


def _q(x):
    if not isinstance(x, (int, F)) or isinstance(x, bool):
        raise ValueError("certificate inputs must be exact rationals")
    return F(x)


def _window(lo, hi):
    lo, hi = _q(lo), _q(hi)
    if not 0 <= lo <= hi <= 1:
        raise ValueError("certificate window must lie in [0,1]")
    return lo, hi


def _add(a, b):
    return tuple((a[i] if i < len(a) else F(0)) +
                 (b[i] if i < len(b) else F(0)) for i in range(max(len(a), len(b))))


def _scale(a, k):
    return tuple(k*x for x in a)


def polynomial_range(coefficients, lo, hi):
    """Exact Bernstein convex-hull enclosure; test_bernstein_independent_oracle."""
    p = tuple(_q(c) for c in coefficients)
    if not p:
        raise ValueError("empty polynomial")
    lo, hi = _window(lo, hi)
    n = len(p)-1
    shifted = tuple((hi-lo)**j*sum(p[k]*comb(k, j)*lo**(k-j)
                                  for k in range(j, n+1)) for j in range(n+1))
    b = tuple(sum(shifted[j]*F(comb(i, j), comb(n, j)) for j in range(i+1))
              for i in range(n+1))
    return min(b), max(b)


def chord_paths(start, end):
    """Coordinate numerator pairs and positive denominator for snapshot P1."""
    if len(start) != len(end) or len(start) < 3:
        raise ValueError("equal rings of at least three vertices required")
    paths = []
    for p, q in zip(start, end):
        if len(p) != 2 or len(q) != 2:
            raise ValueError("two-dimensional points required")
        p, q = tuple(_q(x) for x in p), tuple(_q(x) for x in q)
        paths.append(((p[0], q[0]-p[0]), (p[1], q[1]-p[1]), (F(1),)))
    return tuple(paths)


def dda_paths(start, motion):
    """Adapter to the explicit DDA rational path, not a fit."""
    if type(motion) is not DDAAnchoredMotion:
        raise ValueError("DDAAnchoredMotion required, not an arbitrary callback")
    result = []
    for point in start:
        numerators, denominator = motion.coordinate_polynomials(point)
        result.append((*numerators, denominator))
    return tuple(result)


def _validate(paths):
    if len(paths) < 3:
        raise ValueError("at least three vertex paths required")
    result = []
    for path in paths:
        if len(path) != 3 or any(not p for p in path):
            raise ValueError("expected Nx, Ny, D polynomials")
        path = tuple(tuple(_q(x) for x in p) for p in path)
        if polynomial_range(path[2], 0, 1)[0] <= 0:
            raise ValueError("positive denominator certificate required")
        result.append(path)
    return tuple(result)


def _quotient(numerator, denominator, lo, hi):
    a, b = polynomial_range(numerator, lo, hi), polynomial_range(denominator, lo, hi)
    if b[0] <= 0:
        raise ValueError("positive denominator required")
    values = tuple(x/y for x in a for y in b)
    return min(values), max(values)


def _projection(path, normal, lo, hi, origin):
    numerator = _add(_scale(path[0], normal[0]), _scale(path[1], normal[1]))
    numerator = _add(numerator, _scale(path[2], -origin))
    low, high = _quotient(numerator, path[2], lo, hi)
    return low+origin, high+origin


def _value(path, time):
    return tuple(_quotient(path[k], path[2], time, time)[0] for k in (0, 1))


def _panels(lo, hi, count):
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise ValueError("positive integer panel count required")
    return tuple((lo+(hi-lo)*F(i, count), lo+(hi-lo)*F(i+1, count)) for i in range(count))


def _normals(a, b):
    normals = [(F(1), F(0)), (F(0), F(1))]
    for paths in (a, b):
        ring = tuple(_value(p, F(0)) for p in paths)
        normals.extend((q[1]-p[1], p[0]-q[0]) for p, q in zip(ring, ring[1:]+ring[:1])
                       if p != q)
    return tuple(normals)


def _radii(ra, rb):
    ra, rb = _q(ra), _q(rb)
    if ra < 0 or rb < 0:
        raise ValueError("tube radii must be nonnegative")
    return ra, rb


def separation_certificate(paths_a, paths_b, radius_a=0, radius_b=0, *,
                           lo=0, hi=1, panels=4):
    """Strict swept projection gap in every panel proves robust no contact.

    Returns None when this sufficient test is inconclusive. The gap is a lower
    bound in coordinate L-infinity distance, not an exact global minimum.
    Gate: test_no_contact_requires_strict_margin_and_covers_whole_window.
    """
    a, b = _validate(paths_a), _validate(paths_b)
    ra, rb = _radii(radius_a, radius_b)
    lo, hi = _window(lo, hi)
    normals, witnesses = _normals(a, b), []
    for lower, upper in _panels(lo, hi, panels):
        best = None
        for normal in normals:
            norm = abs(normal[0])+abs(normal[1])
            anchor = _value(a[0], lower)
            origin = sum(x*y for x, y in zip(anchor, normal))
            aa = tuple(_projection(p, normal, lower, upper, origin) for p in a)
            bb = tuple(_projection(p, normal, lower, upper, origin) for p in b)
            gap = max(min(x[0] for x in bb)-max(x[1] for x in aa),
                      min(x[0] for x in aa)-max(x[1] for x in bb))/norm
            if gap > ra+rb and (best is None or gap > best["gap_lower"]):
                best = dict(window=(lower, upper), normal=normal, gap_lower=gap)
        if best is None:
            return None
        witnesses.append(best)
    return dict(kind="ROBUST_NO_CONTACT", radius_sum=ra+rb,
                gap_lower=min(w["gap_lower"] for w in witnesses), witnesses=tuple(witnesses))


def _minus(a, b):
    return a[0]-b[1], a[1]-b[0]


def _times(a, b):
    p = tuple(x*y for x in a for y in b)
    return min(p), max(p)


def _plus(a, b):
    return a[0]+b[0], a[1]+b[1]


def _cross(a, b):
    return _minus(_times(a[0], b[1]), _times(a[1], b[0]))


def _dot(a, b):
    return _plus(_times(a[0], b[0]), _times(a[1], b[1]))


def _boxes(paths, lo, hi):
    anchor = _value(paths[0], lo)
    return tuple(tuple(_projection(p, ((1, 0), (0, 1))[k], lo, hi, anchor[k])
                       for k in (0, 1)) for p in paths)


def _diff(a, b):
    return tuple(_minus(x, y) for x, y in zip(a, b))


def _length1(box):
    return sum(max(abs(x), abs(y)) for x, y in box)


def _event(a, b, i, j, ra, rb):
    """Cross and both segment projections with vertex-tube error budgets."""
    u = _diff(b[(j+1) % len(b)], b[j])
    w = _diff(a[i], b[j])
    v = _diff(a[i], b[(j+1) % len(b)])
    du, dw = 2*rb, ra+rb
    error_w = du*_length1(w)+dw*_length1(u)+2*du*dw
    error_v = du*_length1(v)+dw*_length1(u)+2*du*dw
    h = _dot(u, v)
    return _cross(u, w), _dot(u, w), (-h[1], -h[0]), error_w, error_v


def _strict_convex(boxes, radius):
    for j, point in enumerate(boxes):
        following = (j+1) % len(boxes)
        u = _diff(boxes[following], point)
        for k, other in enumerate(boxes):
            if k in (j, following):
                continue
            v = _diff(other, point)
            error = 2*radius*(_length1(u)+_length1(v))+8*radius*radius
            if _cross(u, v)[0] <= error:
                return False
    return True


def swept_axis_bounds(paths, *, lo=0, hi=1):
    """Whole-window coordinate enclosures, useful for cached batch certificates.

    Gate: test_no_contact_requires_strict_margin_and_covers_whole_window.
    """
    paths = _validate(paths)
    lo, hi = _window(lo, hi)
    boxes = _boxes(paths, lo, hi)
    return tuple((min(p[k][0] for p in boxes), max(p[k][1] for p in boxes)) for k in (0, 1))


def _mul_poly(a, b):
    result = [F(0)]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i+j] += x*y
    return tuple(result)


def _derivative(p):
    return tuple(i*p[i] for i in range(1, len(p))) or (F(0),)


def _event_derivative(a, b, i, j, lo, hi):
    """Exact interval of derivative of the rational line-side function."""
    p, q, r = a[i], b[j], b[(j+1) % len(b)]
    # General denominators, including the independent snapshot chord family.
    ux = _add(_mul_poly(r[0], q[2]), _scale(_mul_poly(q[0], r[2]), -1))
    uy = _add(_mul_poly(r[1], q[2]), _scale(_mul_poly(q[1], r[2]), -1))
    wx = _add(_mul_poly(p[0], q[2]), _scale(_mul_poly(q[0], p[2]), -1))
    wy = _add(_mul_poly(p[1], q[2]), _scale(_mul_poly(q[1], p[2]), -1))
    num = _add(_mul_poly(ux, wy), _scale(_mul_poly(uy, wx), -1))
    den = _mul_poly(_mul_poly(r[2], p[2]), _mul_poly(q[2], q[2]))
    dn = _add(_mul_poly(_derivative(num), den), _scale(_mul_poly(num, _derivative(den)), -1))
    return _quotient(dn, _mul_poly(den, den), lo, hi)


def single_cover_certificate(paths_a, paths_b, label, bracket, radius_a=0,
                             radius_b=0, *, panels=4):
    """Sufficient singleton first-cover identity certificate for CCW convex rings.

    Requires early separation, interior projection, nominal strict crossing,
    robust endpoint signs and exclusion of every competitor until bracket end.
    Certifies identity, NOT an unchanged first time or perturbed derivatives.
    Gate: test_single_cover_certificate_has_independent_closed_form_oracle.
    """
    a, b = _validate(paths_a), _validate(paths_b)
    ra, rb = _radii(radius_a, radius_b)
    lo, hi = _window(*bracket)
    if lo == hi or len(label) != 3 or label[0] not in ("VE", "EV"):
        raise ValueError("strict bracket and singleton VE/EV label required")
    tag, first, second = label
    if tag == "VE":
        p, q, rp, rq, i, j = a, b, ra, rb, first, second
    else:
        p, q, rp, rq, i, j = b, a, rb, ra, second, first
    if not (isinstance(i, int) and isinstance(j, int) and 0 <= i < len(p) and 0 <= j < len(q)):
        raise ValueError("invalid feature indices")
    early = separation_certificate(a, b, ra, rb, lo=0, hi=lo, panels=panels)
    if early is None:
        return None
    begin = _event(_boxes(p, lo, lo), _boxes(q, lo, lo), i, j, rp, rq)
    end = _event(_boxes(p, hi, hi), _boxes(q, hi, hi), i, j, rp, rq)
    if not (begin[0][1] < -begin[3] and end[0][0] > end[3]):
        return None
    derivative = _event_derivative(p, q, i, j, lo, hi)
    if derivative[0] <= 0:
        return None
    margins = []
    for lower, upper in _panels(lo, hi, panels):
        aa, bb = _boxes(a, lower, upper), _boxes(b, lower, upper)
        if not _strict_convex(aa, ra) or not _strict_convex(bb, rb):
            return None
        for pp, qq, rr, ss, kind in ((aa, bb, ra, rb, "VE"), (bb, aa, rb, ra, "EV")):
            for ii in range(len(pp)):
                for jj in range(len(qq)):
                    key = (kind, ii, jj) if kind == "VE" else (kind, jj, ii)
                    f, g, h, ew, ev = _event(pp, qq, ii, jj, rr, ss)
                    if key == tuple(label):
                        margin = min(g[0]-ew, h[0]-ev)
                    else:
                        # A line-side or either segment projection may exclude
                        # an incidence. Do not confuse line crossing with contact.
                        margin = max(f[0]-ew, -f[1]-ew, -g[1]-ew, -h[1]-ev)
                    if margin <= 0:
                        return None
                    margins.append(margin)
    return dict(kind="ROBUST_SINGLE_FIRST_COVER", label=tuple(label), bracket=(lo, hi),
                radius_sum=ra+rb, early=early, derivative_lower=derivative[0],
                event_margin_lower=min(margins),
                endpoints_margin=min(-begin[0][1]-begin[3], end[0][0]-end[3]))
