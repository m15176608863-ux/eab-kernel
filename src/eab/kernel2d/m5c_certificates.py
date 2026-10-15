"""R3 research certificate: exact same-time relative rational enclosures.

Proof and limits: docs/m5c_research_theory.md.  None means unproved, never
an empirical model difference.  The independent closed-form gates are in
tests/test_m5c_certificates.py.  No arbitrary path callbacks or float inputs.
"""
from fractions import Fraction as F

from . import model_robustness as base


def _relative(p, q):
    if p[2] == q[2]:
        return (base._add(p[0], base._scale(q[0], -1)),
                base._add(p[1], base._scale(q[1], -1)), p[2])
    denominator = base._mul_poly(p[2], q[2])
    return tuple(base._add(base._mul_poly(p[k], q[2]),
                           base._scale(base._mul_poly(q[k], p[2]), -1))
                 for k in (0, 1)) + (denominator,)


def _bilinear(u, w, lo, hi, *, cross):
    if cross:
        numerator = base._add(base._mul_poly(u[0], w[1]),
                              base._scale(base._mul_poly(u[1], w[0]), -1))
    else:
        numerator = base._add(base._mul_poly(u[0], w[0]), base._mul_poly(u[1], w[1]))
    return base._quotient(numerator, base._mul_poly(u[2], w[2]), lo, hi)


def _length1(u, lo, hi):
    return sum(max(abs(v) for v in base._quotient(u[k], u[2], lo, hi)) for k in (0, 1))


def _event(a, b, i, j, ra, rb, lo, hi):
    u = _relative(b[(j+1) % len(b)], b[j])
    w = _relative(a[i], b[j])
    v = _relative(a[i], b[(j+1) % len(b)])
    du, dw = 2*rb, ra+rb
    ew = du*_length1(w, lo, hi)+dw*_length1(u, lo, hi)+2*du*dw
    ev = du*_length1(v, lo, hi)+dw*_length1(u, lo, hi)+2*du*dw
    h = _bilinear(u, v, lo, hi, cross=False)
    return (_bilinear(u, w, lo, hi, cross=True),
            _bilinear(u, w, lo, hi, cross=False), (-h[1], -h[0]), ew, ev)


def _normals(a, b, time):
    normals = [(F(1), F(0)), (F(0), F(1))]
    for paths in (a, b):
        ring = tuple(base._value(p, time) for p in paths)
        normals.extend((q[1]-p[1], p[0]-q[0]) for p, q in zip(ring, ring[1:]+ring[:1])
                       if p != q)
    return tuple(normals)


def _separation(a, b, ra, rb, lo, hi, panels):
    witnesses = []
    relatives = tuple(_relative(q, p) for p in a for q in b)
    for lower, upper in base._panels(lo, hi, panels):
        best = None
        for n in _normals(a, b, (lower+upper)/2):
            norm = abs(n[0])+abs(n[1])
            bounds = tuple(base._quotient(base._add(base._scale(p[0], n[0]),
                                                    base._scale(p[1], n[1])),
                                           p[2], lower, upper) for p in relatives)
            gap = max(min(x[0] for x in bounds), -max(x[1] for x in bounds))/norm
            if best is None or gap > best["gap_lower"]:
                best = dict(window=(lower, upper), normal=n, gap_lower=gap)
        witnesses.append(best)
    gap = min(w["gap_lower"] for w in witnesses)
    return dict(passed=gap > ra+rb, gap_lower=gap, radius_sum=ra+rb, witnesses=tuple(witnesses))


def relative_separation_certificate(paths_a, paths_b, radius_a=0, radius_b=0, *,
                                    lo=0, hi=1, panels=4):
    """Strict same-time separation; gate: test_common_translation_cancels_exactly."""
    a, b = base._validate(paths_a), base._validate(paths_b)
    ra, rb = base._radii(radius_a, radius_b)
    lo, hi = base._window(lo, hi)
    result = _separation(a, b, ra, rb, lo, hi, panels)
    if not result["passed"]:
        return None
    result["kind"] = "ROBUST_NO_CONTACT_RELATIVE"
    return result


def _simple(a, radius, lo, hi):
    # A finite exhaustive edge-pair proof, not just a local turning test.
    n, margins = len(a), []
    for j in range(n):
        u = _relative(a[(j+1) % n], a[j])
        components = tuple(base._quotient(u[k], u[2], lo, hi) for k in (0, 1))
        margins.append(max(max(x[0], -x[1]) for x in components)-2*radius)
        v = _relative(a[(j-1) % n], a[j])
        error = 2*radius*(_length1(u, lo, hi)+_length1(v, lo, hi))+8*radius*radius
        cross, dot = _bilinear(u, v, lo, hi, cross=True), _bilinear(u, v, lo, hi, cross=False)
        margins.append(max(cross[0], -cross[1], -dot[1])-error)
        for k in range(j+1, n):
            if k == (j+1) % n or j == (k+1) % n:
                continue
            possibilities = []
            for edge, other in ((j, k), (k, j)):
                e0 = _event(a, a, other, edge, radius, radius, lo, hi)
                e1 = _event(a, a, (other+1) % n, edge, radius, radius, lo, hi)
                possibilities.extend((min(e0[0][0]-e0[3], e1[0][0]-e1[3]),
                                      min(-e0[0][1]-e0[3], -e1[0][1]-e1[3])))
            # Disjoint collinear edges cannot be separated by either edge's
            # own line.  Fixed tangent/axis projections cover that case.
            directions = [(F(1), F(0)), (F(0), F(1))]
            for edge in (j, k):
                first = base._value(a[edge], (lo+hi)/2)
                second = base._value(a[(edge+1) % n], (lo+hi)/2)
                if first != second:
                    directions.append((second[0]-first[0], second[1]-first[1]))
            for direction in directions:
                bounds = []
                for left in (j, (j+1) % n):
                    for right in (k, (k+1) % n):
                        vector = _relative(a[right], a[left])
                        numerator = base._add(base._scale(vector[0], direction[0]),
                                              base._scale(vector[1], direction[1]))
                        bounds.append(base._quotient(numerator, vector[2], lo, hi))
                budget = 2*radius*(abs(direction[0])+abs(direction[1]))
                possibilities.append(max(min(x[0] for x in bounds), -max(x[1] for x in bounds))-budget)
            margins.append(max(possibilities))
    return min(margins)


def diagnose_single_cover(paths_a, paths_b, label, bracket, radius_a=0,
                          radius_b=0, *, panels=4):
    """Exhaustively expose R3 guards, including failed guards, without signing."""
    a, b = base._validate(paths_a), base._validate(paths_b)
    ra, rb = base._radii(radius_a, radius_b)
    lo, hi = base._window(*bracket)
    if lo == hi or len(label) != 3 or label[0] not in ("VE", "EV"):
        raise ValueError("strict bracket and singleton VE/EV label required")
    tag, first, second = label
    if tag == "VE":
        p, q, rp, rq, i, j = a, b, ra, rb, first, second
    else:
        p, q, rp, rq, i, j = b, a, rb, ra, second, first
    if not (isinstance(i, int) and not isinstance(i, bool) and isinstance(j, int)
            and not isinstance(j, bool) and 0 <= i < len(p) and 0 <= j < len(q)):
        raise ValueError("invalid feature indices")
    for ring in (a, b):
        points = tuple(base._value(path, F(0)) for path in ring)
        if sum(x*v-y*u for (x, y), (u, v) in zip(points, points[1:]+points[:1])) <= 0:
            raise ValueError("CCW nominal ring required")
    early = _separation(a, b, ra, rb, F(0), lo, panels)
    begin = _event(p, q, i, j, rp, rq, lo, lo)
    end = _event(p, q, i, j, rp, rq, hi, hi)
    guards = dict(early_separation=early["gap_lower"]-ra-rb,
                  endpoint_begin=-begin[0][1]-begin[3], endpoint_end=end[0][0]-end[3])
    errors = dict(early_separation=ra+rb, endpoint_begin=begin[3], endpoint_end=end[3])
    for lower, upper in base._panels(lo, hi, panels):
        simple = min(_simple(a, ra, lower, upper), _simple(b, rb, lower, upper))
        guards["simple_rings"] = min(guards.get("simple_rings", simple), simple)
        for pp, qq, rr, ss, kind in ((a, b, ra, rb, "VE"), (b, a, rb, ra, "EV")):
            for ii in range(len(pp)):
                for jj in range(len(qq)):
                    key = (kind, ii, jj) if kind == "VE" else (kind, jj, ii)
                    f, g, h, ew, ev = _event(pp, qq, ii, jj, rr, ss, lower, upper)
                    if key == tuple(label):
                        name, margin = "interior_projection", min(g[0]-ew, h[0]-ev)
                    else:
                        name = "competitor_"+kind
                        margin = max(f[0]-ew, -f[1]-ew, -g[1]-ew, -h[1]-ev)
                    if name not in guards or margin < guards[name]:
                        guards[name], errors[name] = margin, max(ew, ev)
    return dict(guards=guards, errors=errors, failed=tuple(k for k, v in guards.items() if v <= 0),
                early=early, label=tuple(label), bracket=(lo, hi), radius_sum=ra+rb)


def single_cover_certificate(paths_a, paths_b, label, bracket, radius_a=0,
                             radius_b=0, *, panels=4):
    """R3 first identity only; gate: test_concave_single_cover_matches_closed_form_oracle."""
    result = diagnose_single_cover(paths_a, paths_b, label, bracket, radius_a, radius_b, panels=panels)
    if result["failed"]:
        return None
    result["kind"] = "ROBUST_SINGLE_FIRST_COVER_RELATIVE_SIMPLE"
    return result
