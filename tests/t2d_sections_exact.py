"""Independent exact erosion from horizontal sections, for the T2d family.

If A has slices [-a(y),a(y)] and the symmetric convex element K has slices
[-k(v),k(v)], then A minus delta K has half-width
min_v(a(y+delta*v)-delta*k(v)). The objective is piecewise affine in v,
so only element-height vertices and cavity-height crossings are needed.
Between y=h-delta*v events every candidate is affine in y. We build its
exact lower envelope, then independently validate the resulting partition
at endpoints and midpoints. No production geometric primitive is imported.
"""
from fractions import Fraction as F

import tests.t2d_knob_family_exact as exact


def element_profile(element):
    vertices = exact.element_vertices(element)
    heights = sorted({y for _, y in vertices})
    return tuple((y, max(x for x, v in vertices if v == y)) for y in heights)


def _line_at(profile, height):
    for (a, fa), (b, fb) in zip(profile, profile[1:]):
        if a <= height <= b:
            slope = (fb-fa)/(b-a)
            return slope, fa-slope*a
    raise ValueError("height outside the closed profile")


def eroded_half_width(n, element, delta, height):
    """Direct slice infimum, independent of the envelope implementation."""
    d, y = exact.rational(delta), exact.rational(height)
    cavity = exact.family_geometry(n)["right_profile"]
    shape = element_profile(element)
    if d == 0:
        return exact.interpolate(cavity, y)
    assert cavity[0][0]-d*shape[0][0] <= y <= cavity[-1][0]-d*shape[-1][0]
    cuts = {v for v, _ in shape}
    for h, _ in cavity:
        v = (h-y)/d
        if shape[0][0] <= v <= shape[-1][0]:
            cuts.add(v)
    return min(exact.interpolate(cavity, y+d*v)-d*exact.interpolate(shape, v) for v in cuts)


def _section_lines(cavity, shape, d, middle):
    """All active affine candidates on one open y-event cell."""
    lines = []
    for v, width in shape:
        slope, intercept = _line_at(cavity, middle+d*v)
        lines.append((slope, intercept+d*slope*v-d*width))
    for h, width in cavity:
        v = (h-middle)/d
        if shape[0][0] < v < shape[-1][0]:
            slope, intercept = _line_at(shape, v)
            lines.append((slope, width-slope*h-d*intercept))
    return tuple(lines)


def _lower_envelope(lines):
    """Descending slopes give the exact min-envelope from left to right."""
    grouped = {}
    for slope, intercept in lines:
        grouped[slope] = min(grouped.get(slope, intercept), intercept)
    envelope = []
    for slope in sorted(grouped, reverse=True):
        intercept = grouped[slope]
        crossing = None
        while envelope:
            old_slope, old_intercept, start = envelope[-1]
            crossing = (intercept-old_intercept)/(old_slope-slope)
            if start is None or start < crossing:
                break
            envelope.pop()
        envelope.append((slope, intercept, crossing if envelope else None))
    return tuple(envelope)


def _raw_profile(n, element, delta):
    d = exact.rational(delta)
    if d < 0:
        raise ValueError("nonnegative erosion required")
    cavity = exact.family_geometry(n)["right_profile"]
    if d == 0:
        return cavity
    shape = element_profile(element)
    lo, hi = cavity[0][0]-d*shape[0][0], cavity[-1][0]-d*shape[-1][0]
    if lo >= hi:
        raise ValueError("empty or lower-dimensional erosion")
    cuts = sorted({lo, hi} | {h-d*v for h, _ in cavity for v, _ in shape if lo < h-d*v < hi})
    right, zero_heights = [], set()
    for left, end in zip(cuts, cuts[1:]):
        lines = _section_lines(cavity, shape, d, (left+end)/2)
        envelope = _lower_envelope(lines)
        nodes = sorted({left, end} | {start for _, _, start in envelope
                                     if start is not None and left < start < end})
        for a, b in zip(nodes, nodes[1:]):
            slope, intercept = min(lines, key=lambda line: line[0]*(a+b)/2+line[1])
            va, vb = slope*a+intercept, slope*b+intercept
            if va == vb == 0:
                raise ValueError("lower-dimensional erosion remnant")
            if va < 0 and vb > 0:
                a, va = -intercept/slope, F(0)
            elif va > 0 and vb < 0:
                b, vb = -intercept/slope, F(0)
            if va == 0:
                zero_heights.add(a)
            if vb == 0:
                zero_heights.add(b)
            if va+vb <= 0:
                continue
            assert va >= 0 and vb >= 0, "positive envelope cell was not clipped at zero"
            if right:
                assert right[-1] == (a, va), "erosion has disconnected sections"
            else:
                right.append((a, va))
            right.append((b, vb))
    if len(right) < 2:
        raise ValueError("empty or lower-dimensional erosion")
    if any(y < right[0][0] or y > right[-1][0] for y in zero_heights):
        raise ValueError("isolated lower-dimensional erosion remnant")
    return tuple(right)


def _canonical(polygon):
    points = list(dict.fromkeys(polygon))
    changed = True
    while changed and len(points) > 2:
        changed = False
        for index in range(len(points)):
            if exact._cross(points[index-1], points[index], points[(index+1) % len(points)]) == 0:
                del points[index]
                changed = True
                break
    assert len(points) >= 3, "erosion must have positive area"
    start = min(range(len(points)), key=lambda index: points[index])
    return tuple(points[start:]+points[:start])


def _verification_cuts(cavity, shape, delta, profile):
    lo, hi = profile[0][0], profile[-1][0]
    return sorted({y for y, _ in profile} | {h-delta*v for h, _ in cavity for v, _ in shape if lo < h-delta*v < hi})


def verify_section_profile(n, element, delta, profile):
    """Finite affine proof; not unlabelled point sampling.

    The event partition fixes every candidate's affine formula. On each
    common refinement cell the claimed profile is affine. Agreement at
    both endpoints puts every candidate above it; agreement at the midpoint
    forces an active candidate to coincide throughout that entire cell.
    """
    d = exact.rational(delta)
    cavity, shape = exact.family_geometry(n)["right_profile"], element_profile(element)
    assert all(a < b for (a, _), (b, _) in zip(profile, profile[1:])), "profile heights must increase"
    assert all(width >= 0 for _, width in profile), "negative erosion width"
    lo, hi = profile[0][0], profile[-1][0]
    cuts = _verification_cuts(cavity, shape, d, profile)
    assert cuts == sorted(set(cuts)), "section cuts are not strictly ordered"
    assert all(y in cuts for y, _ in profile), "missing section vertex event"
    assert all(h-d*v in cuts for h, _ in cavity for v, _ in shape if lo < h-d*v < hi), "missing section formula-change event"
    checks = cuts+[(a+b)/2 for a, b in zip(cuts, cuts[1:])]
    for y in checks:
        assert exact.interpolate(profile, y) == eroded_half_width(n, element, d, y), "independent section infimum mismatch"
    feasible_lo, feasible_hi = cavity[0][0]-d*shape[0][0], cavity[-1][0]-d*shape[-1][0]
    outside = sorted({feasible_lo, feasible_hi, lo, hi} | {h-d*v for h, _ in cavity for v, _ in shape
                                                       if feasible_lo < h-d*v < feasible_hi})
    # The omitted lower/upper intervals have no nonnegative interior width.
    # A finite concave minimum of affines cannot hide a positive bump if its
    # full min-envelope intersections are also checked; rebuild only those
    # exterior intervals, leaving interior validation independent.
    for a, b in zip(outside, outside[1:]):
        if b <= lo or a >= hi:
            if a == b:
                continue
            lines = _section_lines(cavity, shape, d, (a+b)/2) if d else ()
            probes = [a, b]+[start for _, _, start in _lower_envelope(lines)
                            if start is not None and a < start < b]
            for y in probes:
                width = eroded_half_width(n, element, d, y)
                if y < lo or y > hi:
                    assert width < 0, "omitted closed erosion slice, including a zero-width remnant"
                else:
                    assert width <= 0, "omitted positive erosion slice"
    return len(cuts), len(checks)


def eroded_polygon(n, element, delta):
    """Return the exact single-ring rational erosion in CCW canonical order."""
    profile = _raw_profile(n, element, delta)
    verify_section_profile(n, element, delta, profile)
    right = tuple((width, height) for height, width in profile)
    return _canonical(right+tuple((-x, y) for x, y in reversed(right)))
