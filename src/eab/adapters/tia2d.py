"""TIA-G1/G5 exact input families for the planar Python referee.

profile1: rigid, small-deformation, unlimited compression, no cohesion,
constant friction and associated flow; an unsafe-side upper-bound model
relative to non-associated Coulomb friction. No gravity. G5 alone has the
specified force-controlled dead preload. Tests: test_tia2d_families.py.
These generators do not infer locking from an unbounded load LP.
"""
from fractions import Fraction as Q
import struct

from ..construction import scalar_rational
from ..kernel2d.assembly import Assembly2, Body2, point2
from ..kernel2d.exact import polygons_overlap_exact


def _complete(bodies, mu):
    bodies = tuple(bodies)
    pairs = tuple((i, j) for i in range(len(bodies)) for j in range(i + 1, len(bodies)))
    return Assembly2(bodies, pairs, "complete", "profile1", Q(mu))


def g1(*, t=Q(1, 4), height=Q(1), orientation="koureas", mu=Q(0),
       origin=(Q(5, 8), Q(-3, 8))):
    """TIA-G1 five blocks, fixed blocks 1/5, central downward unit live force.

Shared faces are constructed once in exact arithmetic. Binary64 export must
separately check lossless representation; pure-rational inputs stay Python.
The label theta=atan(t) is deliberately not a geometry construction.
"""
    t, h, o = Q(t), Q(height), point2(origin)
    if t < 0 or h <= 0:
        raise ValueError("t must be nonnegative and height positive")
    if orientation == "koureas":
        slopes = (-t, -t, t, t)
    elif orientation == "unreversed":
        slopes = (t, -t, t, -t)
    elif orientation == "reverse_i1":
        slopes = (-t, -t, t, -t)
    else:
        raise ValueError("unknown TIA-G1 orientation")
    faces = [((Q(-5), Q(0)), (Q(-5), h))]
    for k, slope in enumerate(slopes, 1):
        faces.append(((Q(-5 + 2 * k) - slope * h / 2, Q(0)),
                      (Q(-5 + 2 * k) + slope * h / 2, h)))
    faces.append(((Q(5), Q(0)), (Q(5), h)))
    bodies = []
    for i, (left, right) in enumerate(zip(faces, faces[1:])):
        if left[0][0] >= right[0][0] or left[1][0] >= right[1][0]:
            raise ValueError("parameters create intersecting faces")
        fixed = i in (0, 4)
        live = (Q(0), Q(-1), o[0]) if i == 2 else (Q(0), Q(0), Q(0))
        bodies.append(Body2.from_vertices("block_" + str(i + 1),
            (left[0], right[0], right[1], left[1]), reference_point=o,
            boundary_type="FIXED_BODY" if fixed else None,
            dof_mask=(0, 0, 0) if fixed else (1, 1, 1), dof_anchor=o, live=live))
    return _complete(bodies, mu)


def g1_threshold(*, t=Q(1, 4), height=Q(1), orientation="koureas"):
    """Closed-form reference only, never a substitute for LP certificates.

    At t=0 every orientation has a zero OPEN threshold: horizontal frictionless
    normals cannot carry the vertical load, but every positive mu admits a
    clamping ray. This is the owner-approved work-order correction C03.
    """
    t, ratio = Q(t), Q(height) / 2
    if t < 0 or ratio <= 0:
        raise ValueError("t must be nonnegative and height positive")
    if orientation not in ("koureas", "unreversed", "reverse_i1"):
        raise ValueError("unknown TIA-G1 orientation")
    if t == 0:
        return Q(0), False
    if orientation == "koureas":
        return max(Q(0), t - ratio * (1 + t * t)), True
    if orientation == "unreversed":
        return t, False
    if orientation == "reverse_i1":
        return t, True
    raise ValueError("unknown TIA-G1 orientation")


def g5(*, n=3, height=Q(1), pressure=Q(1), mu=Q(0), width=Q(1),
       widths=None, dof_mask=(1, 0, 0), dof_anchor=None,
       origin=(Q(5, 8), Q(-3, 8))):
    """TIA-G5; main plate constraint anchor is the full-height face midpoint.

N moving blocks between two explicitly modelled boundary bodies. P acts at
the plate face midpoint. Wrenches and masks use independent fixed frames.
F=min(2*mu*P,4*P*h/(L-b)) only for mask [1,0,0], symmetric positive widths.
"""
    h, P, o = Q(height), Q(pressure), point2(origin)
    if n not in (3, 5, 7) or h <= 0 or P < 0:
        raise ValueError("unsupported block count or invalid height/pressure")
    sizes = (Q(width),) * n if widths is None else tuple(Q(w) for w in widths)
    if len(sizes) != n or any(w <= 0 for w in sizes) or sizes != tuple(reversed(sizes)):
        raise ValueError("widths must be positive and symmetric")
    x = [Q(0)]
    for w in sizes:
        x.append(x[-1] + w)
    L = x[-1]
    faces = tuple(((xx, Q(0)), (xx, h)) for xx in x)
    left = Body2.from_vertices("left_boundary", ((-sizes[0], 0), faces[0][0],
        faces[0][1], (-sizes[0], h)), reference_point=o, boundary_type="FIXED_BODY",
        dof_mask=(0, 0, 0), dof_anchor=o)
    bodies = [left]
    for i, (a, b) in enumerate(zip(faces, faces[1:])):
        live = (Q(0), Q(-1), -(L / 2 - o[0])) if i == n // 2 else (Q(0), Q(0), Q(0))
        bodies.append(Body2.from_vertices("block_" + str(i + 1),
            (a[0], b[0], b[1], a[1]), reference_point=o, dof_anchor=o, live=live))
    anchor = (L, h / 2) if dof_anchor is None else point2(dof_anchor)
    bodies.append(Body2.from_vertices("right_plate", (faces[-1][0], (L + sizes[-1], 0),
        (L + sizes[-1], h), faces[-1][1]), reference_point=o,
        boundary_type="FORCE_CONTROLLED_PLATE", dof_mask=tuple(dof_mask), dof_anchor=anchor,
        dead=(-P, Q(0), (h / 2 - o[1]) * P)))
    return _complete(bodies, mu)


def g5_closed_form(*, n=3, height=Q(1), pressure=Q(1), mu=Q(0), width=Q(1), widths=None):
    sizes = (Q(width),) * n if widths is None else tuple(Q(w) for w in widths)
    L, b = sum(sizes, Q(0)), sizes[n // 2]
    return min(2 * Q(mu) * Q(pressure), 4 * Q(pressure) * Q(height) / (L - b))


def _shared_faces(assembly):
    faces = []
    for a, b in zip(assembly.bodies, assembly.bodies[1:]):
        shared = sorted(set(a.vertices) & set(b.vertices), key=lambda p: (p[1], p[0]))
        if len(shared) != 2 or shared[0][1] == shared[1][1]:
            raise ValueError("chain needs full-height shared endpoint faces")
        faces.append(tuple(shared))
    return tuple(faces)


def _height(assembly):
    lows = {min(p[1] for p in b.vertices) for b in assembly.bodies}
    highs = {max(p[1] for p in b.vertices) for b in assembly.bodies}
    if len(lows) != 1 or len(highs) != 1:
        raise ValueError("chain bodies must share their lower and upper levels")
    lo, hi = min(lows), max(highs)
    if hi <= lo or any(len(b.vertices) != 4 or any(p[1] not in (lo, hi) for p in b.vertices)
                      for b in assembly.bodies):
        raise ValueError("reference formula requires straight full-height faces")
    return lo, hi


def g1_reference_from_vertices(assembly):
    """Closed-form reference recomputed from actual vertices, not generator args.

This is NOT an LP threshold certificate. It checks the supported beam family,
boundary and unit central load, and returns its elementary reference value.
The zero-slope open-threshold correction is preserved after geometry decoding.
"""
    if len(assembly.bodies) != 5:
        raise ValueError("TIA-G1 reference needs five bodies")
    lo, hi = _height(assembly)
    faces = _shared_faces(assembly)
    height = hi - lo
    slopes = tuple((b[0] - a[0]) / height for a, b in faces)
    t = abs(slopes[0])
    patterns = {"koureas": (-t, -t, t, t), "unreversed": (t, -t, t, -t),
                "reverse_i1": (-t, -t, t, -t)}
    orientation = next((name for name, pattern in patterns.items() if slopes == pattern), None)
    if orientation is None:
        raise ValueError("actual interface slopes do not match a supported orientation")
    centers = tuple((a[0] + b[0]) / 2 for a, b in faces)
    spacing = centers[1] - centers[0]
    if spacing <= 0 or any(b - a != spacing for a, b in zip(centers, centers[1:])):
        raise ValueError("actual interface centers are not uniformly spaced")
    mid = (centers[1] + centers[2]) / 2
    for i, body in enumerate(assembly.bodies):
        fixed = i in (0, 4)
        if (body.boundary_type == "FIXED_BODY") != fixed or body.dof_mask != ((0, 0, 0) if fixed else (1, 1, 1)):
            raise ValueError("TIA-G1 reference boundary differs from fixed ends")
        live = (Q(0), Q(-1), body.reference_point[0] - mid) if i == 2 else (Q(0),) * 3
        if body.dead != (0, 0, 0) or body.live != live:
            raise ValueError("TIA-G1 reference needs no dead load and one central unit load")
    ratio = height / spacing
    threshold, closed = g1_threshold(t=t, height=2 * ratio, orientation=orientation)
    slender = t > 0 and ratio < t / (1 + t * t)
    gamma = ratio / (1 - ratio * t) if slender else None
    return dict(source="actual_vertices_closed_form_reference", certified=False, t=t,
                height=height, l=spacing, h_over_l=ratio, orientation=orientation,
                degenerate_orientation=t == 0, threshold=threshold, attained=closed,
                tan_gamma_max=gamma,
                tan_theta_minus_gamma=(t - gamma) / (1 + t * gamma) if gamma is not None else None)


def g5_reference_from_vertices(assembly):
    """Read actual L/b/h, explicit preload and live wrench before applying F.

Released-plate masks retain a counterfactual baseline value but are explicitly
not applicable to the closed form. The shear/hinge switch is not mu_crit.
"""
    n = len(assembly.bodies) - 2
    if n not in (3, 5, 7):
        raise ValueError("TIA-G5 reference needs three, five or seven inner bodies")
    lo, hi = _height(assembly)
    faces = _shared_faces(assembly)
    if any(a[0] != b[0] for a, b in faces):
        raise ValueError("TIA-G5 faces must be exactly vertical")
    for body in assembly.bodies:
        xs = {p[0] for p in body.vertices}
        if len(xs) != 2 or set(body.vertices) != {(x, y) for x in xs for y in (lo, hi)}:
            raise ValueError("TIA-G5 reference needs actual rectangles")
    widths = tuple(faces[i + 1][0][0] - faces[i][0][0] for i in range(n))
    if min(widths) <= 0 or widths != tuple(reversed(widths)):
        raise ValueError("TIA-G5 actual widths must be positive and symmetric")
    height, length, middle = hi - lo, sum(widths, Q(0)), widths[n // 2]
    center = (faces[0][0][0] + faces[-1][0][0]) / 2
    left, plate = assembly.bodies[0], assembly.bodies[-1]
    if left.boundary_type != "FIXED_BODY" or plate.boundary_type != "FORCE_CONTROLLED_PLATE":
        raise ValueError("TIA-G5 requires explicit fixed and force-controlled boundaries")
    pressure = -plate.dead[0]
    if pressure < 0 or plate.dead != (-pressure, 0, ((lo + hi) / 2 - plate.reference_point[1]) * pressure):
        raise ValueError("preload must act leftward at the actual plate face midpoint")
    for i, body in enumerate(assembly.bodies):
        live = (Q(0), Q(-1), body.reference_point[0] - center) if i == 1 + n // 2 else (Q(0),) * 3
        if body.live != live or (i != len(assembly.bodies) - 1 and body.dead != (0, 0, 0)):
            raise ValueError("TIA-G5 requires only the central unit live load and plate preload")
        if 0 < i < len(assembly.bodies) - 1 and (body.boundary_type is not None or body.dof_mask != (1, 1, 1)):
            raise ValueError("inner rectangles must be free bodies")
    mu = Q(assembly.mu)
    slide, hinge = 2 * mu * pressure, 4 * pressure * height / (length - middle)
    applicable = plate.dof_mask == (1, 0, 0)
    return dict(source="actual_vertices_and_explicit_load_closed_form_reference", certified=False,
                applicable=applicable, reason=None if applicable else "released_plate_mask",
                n=n, h=height, L=length, b=middle, h_over_L=height / length,
                widths=widths, pressure=pressure, mu=mu, capacity=min(slide, hinge),
                sliding=slide, hinging=hinge, mu_switch=2 * height / (length - middle),
                mode="tie" if slide == hinge else "sliding" if slide < hinge else "hinging")


def _edge_vector(a, b):
    """Decode supplied binary64 endpoints before any derived subtraction."""
    u, v = point2(a), point2(b)
    return v[0] - u[0], v[1] - u[1]


def _cross2(a, b):
    u, v = point2(a), point2(b)
    return u[0] * v[1] - u[1] * v[0]


def _ring_turns(vertices):
    ring = tuple(point2(p) for p in vertices)
    return tuple(_cross2(_edge_vector(ring[i - 1], p), _edge_vector(p, ring[(i + 1) % len(ring)]))
                 for i, p in enumerate(ring))


def audit_binary64_chain(assembly):
    """Round shared vertices once, then audit actual contact, turns and parallels.

Nonidentity rounding marks Python-only, never a binary64-certified input.
Original binary64 signed zeros are kept in xy_bits. Exact predicates operate
on decoded coordinates, not formatted displays or an inferred tolerance.
"""
    shared, bodies = {}, []
    numeric_identity = True
    for body in assembly.bodies:
        for p in body.vertices:
            if p not in shared:
                shared[p] = tuple(scalar_rational(Q(v), allow_underflow=True) for v in p)
        bits = []
        for p in body.original_vertices or body.vertices:
            values = tuple(v if isinstance(v, float) else scalar_rational(Q(v), allow_underflow=True) for v in p)
            bits.append(tuple(f"{struct.unpack('>Q', struct.pack('>d', v))[0]:016x}" for v in values))
        ring = tuple(tuple(Q(v) for v in shared[p]) for p in body.vertices)
        fields = (*body.reference_point, *body.dof_anchor, *body.dead, *body.live)
        numeric_identity = numeric_identity and all(Q(scalar_rational(Q(v), allow_underflow=True)) == Q(v) for v in fields)
        old_turns, new_turns = _ring_turns(body.vertices), _ring_turns(ring)
        bodies.append(dict(body_id=body.body_id, xy_bits=tuple(bits), rounded_vertices=ring,
                           rn_identity=ring == body.vertices,
                           no_new_concave_vertices=all(not (a >= 0 and b < 0) for a, b in zip(old_turns, new_turns))))
    numeric_identity = numeric_identity and Q(scalar_rational(Q(assembly.mu), allow_underflow=True)) == Q(assembly.mu)
    states = []
    for i in range(len(bodies)):
        for j in range(i + 1, len(bodies)):
            state = polygons_overlap_exact(bodies[i]["rounded_vertices"], bodies[j]["rounded_vertices"])
            states.append((i, j, state, state == (0 if j == i + 1 else -1)))
    faces = _shared_faces(assembly)
    vectors = tuple((b[0] - a[0], b[1] - a[1]) for a, b in faces)
    rounded = tuple(_edge_vector(shared[a], shared[b]) for a, b in faces)
    parallels = []
    for i, u in enumerate(vectors):
        for j in range(i + 1, len(vectors)):
            v, ru, rv = vectors[j], rounded[i], rounded[j]
            old = u[0] * v[1] - u[1] * v[0]
            new = _cross2(ru, rv)
            parallels.append((i, j, old, new))
    identity = numeric_identity and all(b["rn_identity"] for b in bodies)
    passed = (identity and all(s[3] for s in states) and all(b["no_new_concave_vertices"] for b in bodies)
              and all((a == 0) == (b == 0) for _, _, a, b in parallels))
    return dict(binary64_subset=passed, rn_identity=identity, bodies=tuple(bodies),
                pair_states=tuple(states), face_cross_products=tuple(parallels),
                shared_point_count=len(shared), no_new_concave_vertices=all(b["no_new_concave_vertices"] for b in bodies),
                reason=None if passed else "python_only_or_exact_contact_audit_failed")


def g5_seed(problem, parameter):
    """Exact G5 mu/P/h jet from actual geometry, with frozen reference points.

Only the axial-only plate mask is supported. Its height-dependent midpoint
anchor has no effect on the retained x row. Height scales about the actual
fixed lower level; both sides share dp and dT. Preload differentiation is
defined at P=0 and never divides a dead wrench by its current magnitude.
"""
    from ..kernel2d.sensitivity import build_limit_seed2
    reference = g5_reference_from_vertices(problem.assembly)
    if not reference["applicable"]:
        raise ValueError("G5 sensitivity seed supports only the axial plate mask")
    plate = problem.assembly.bodies[-1]
    lo, hi = _height(problem.assembly)
    h, pressure = hi - lo, reference["pressure"]
    if parameter == "mu":
        return build_limit_seed2(problem, mu_seed=1, parameter=parameter)
    if parameter == "P":
        return build_limit_seed2(problem, dead_seeds={plate.body_id:
            (Q(-1), Q(0), (lo + hi) / 2 - plate.reference_point[1])}, parameter=parameter)
    if parameter == "h":
        contact_seeds = {c.label: ((Q(0), (c.point[1] - lo) / h), tuple(v / h for v in c.tangent))
                         for c in problem.contact_set.constraints}
        return build_limit_seed2(problem, contact_seeds=contact_seeds,
            dead_seeds={plate.body_id: (Q(0), Q(0), pressure / 2)}, parameter=parameter)
    raise ValueError("G5 seed parameter must be mu, P or h")


from dataclasses import dataclass


@dataclass(frozen=True)
class Morphology2:
    """Fixed-table polygon data, not a smooth-curve contact approximation claim.

Local p=(wavelength*u, amplitude*s) is mapped by the exact +90 degree frame
to (x_k-amplitude*s, wavelength*u). All four faces have the same phase and
orientation. In the frozen design grid the threshold is identically zero;
wavelength is also the block height (one full profile per face). This is a
degenerate shape-design family, not evidence of a morphology threshold trend.
"""
    assembly: Assembly2
    family: str
    amplitude: Q
    wavelength: Q
    table: tuple
    interfaces: tuple
    vertex_seeds_amplitude: tuple
    vertex_seeds_wavelength: tuple
    frame: tuple = ((Q(0), Q(-1)), (Q(1), Q(0)))


def morphology_table(family):
    """Return frozen binary rational (u,s) samples for one vertical period.

TIA-G2 is a two-segment triangular tooth. TIA-G3 uses eight chords of a
normalized semicircular arch, ordinates rounded to multiples of 1/256;
independent amplitude/wavelength scaling is an affine image, not generally
a circle. TIA-G4 uses eight chords of one sine period with sqrt(1/2) replaced
by 181/256. No runtime trigonometry or independently rounded mating face is
used. All conclusions concern these polygons only. In the true circular grid
A=1/4, wavelength=1/2, smooth radial contacts admit a first-order mechanism,
while the frozen polygon and exact-rational 2/4/8/16-chord inscriptions have
zero cones. Refining those four polygon cases does not remove false smooth-
interface interlock. No smooth-circle, ellipse or sine convergence follows.
Gate: test_tia2d_curvature.py (whole-arc radial work versus polygon queries).
"""
    if family == "TIA-G2":
        return ((Q(0), Q(0)), (Q(1, 2), Q(1)), (Q(1), Q(0)))
    if family == "TIA-G3":
        values = (0, 169, 222, 248, 256, 248, 222, 169, 0)
    elif family == "TIA-G4":
        values = (0, 181, 256, 181, 0, -181, -256, -181, 0)
    else:
        raise ValueError("unknown morphology family")
    return tuple((Q(i, 8), Q(s, 256)) for i, s in enumerate(values))


def _morphology_face(x, amplitude, wavelength, table, shared):
    points, da, dw = [], [], []
    for u, s in table:
        exact = (Q(x) - amplitude * s, wavelength * u)
        if exact not in shared:
            rounded = tuple(scalar_rational(v, allow_underflow=True) for v in exact)
            if tuple(Q(v) for v in rounded) != exact:
                raise ValueError("morphology binary64 subset requires identity rounding")
            shared[exact] = rounded
        points.append(shared[exact])
        da.append((-s, Q(0)))
        dw.append((Q(0), u))
    return tuple(points), tuple(da), tuple(dw)


def morphology_geometry(family, *, amplitude=Q(1, 8), wavelength=Q(1), mu=Q(0),
                        origin=(Q(5, 8), Q(-3, 8))):
    """Five CCW bodies with shared-once binary64 polygonal interfaces.

The first/last bodies are explicitly fixed, all other twists are free, and
the central top point x=0 carries the downward unit live force. No dead load.
One wavelength equals the full height; no hidden repeated cycles are added.
The amplitude=0 control changes the L1 skeleton and is not assigned a
two-sided amplitude sensitivity. Seed arrays follow original vertex IDs.
"""
    amplitude, wavelength, mu = Q(amplitude), Q(wavelength), Q(mu)
    if amplitude < 0 or amplitude >= 1 or wavelength <= 0 or mu < 0:
        raise ValueError("require 0 <= amplitude < 1, wavelength > 0 and mu >= 0")
    table = morphology_table(family)
    shared = {}
    straight = ((Q(0), Q(0)), (Q(1), Q(0)))
    faces = [_morphology_face(-5, amplitude, wavelength, straight, shared)]
    faces.extend(_morphology_face(-5 + 2 * k, amplitude, wavelength, table, shared)
                 for k in range(1, 5))
    faces.append(_morphology_face(5, amplitude, wavelength, straight, shared))
    bodies, amplitude_seeds, wavelength_seeds = [], [], []
    o = point2(origin)
    for i, (left, right) in enumerate(zip(faces, faces[1:])):
        ring = (left[0][0],) + right[0] + tuple(reversed(left[0][1:]))
        da = (left[1][0],) + right[1] + tuple(reversed(left[1][1:]))
        dw = (left[2][0],) + right[2] + tuple(reversed(left[2][1:]))
        fixed = i in (0, 4)
        live = (Q(0), Q(-1), o[0]) if i == 2 else (Q(0), Q(0), Q(0))
        bodies.append(Body2.from_vertices("block_" + str(i + 1), ring,
            reference_point=o, dof_anchor=o, boundary_type="FIXED_BODY" if fixed else None,
            dof_mask=(0, 0, 0) if fixed else (1, 1, 1), live=live))
        amplitude_seeds.append(da)
        wavelength_seeds.append(dw)
    assembly = _complete(bodies, mu)
    for i, j in assembly.pairs:
        state = polygons_overlap_exact(assembly.bodies[i].vertices, assembly.bodies[j].vertices)
        if state != (0 if j == i + 1 else -1):
            raise ArithmeticError("rounded morphology changed expected CONTACT skeleton")
    return Morphology2(assembly, family, amplitude, wavelength, table,
                       tuple(face[0] for face in faces[1:-1]), tuple(amplitude_seeds), tuple(wavelength_seeds))


def morphology_seed(problem, geometry, parameter):
    """Propagate original vertex jets to p,T,N, moments and live-load columns.

References/anchors are parameter-independent. The live force remains vertical
at x=0, so its frozen-reference wrench seed is identically zero, even when
the loading point's height changes. Shared vertex jets are checked, not
inferred independently for each side. No threshold finite differences occur.
"""
    from ..kernel2d.sensitivity import build_limit_seed2
    if problem.assembly != geometry.assembly:
        raise ValueError("morphology and load problem must share the same assembly")
    if parameter == "amplitude":
        vertex_seeds = geometry.vertex_seeds_amplitude
    elif parameter == "wavelength":
        vertex_seeds = geometry.vertex_seeds_wavelength
    else:
        raise ValueError("morphology seed parameter must be amplitude or wavelength")
    by_point, by_body = {}, {}
    for body, seeds in zip(geometry.assembly.bodies, vertex_seeds):
        by_body[body.body_id] = (body, seeds)
        for p, seed in zip(body.original_vertices, seeds):
            point = point2(p)
            if point in by_point and by_point[point] != seed:
                raise ArithmeticError("inconsistent shared vertex seed")
            by_point[point] = seed
    contact_seeds = {}
    for contact in problem.contact_set.constraints:
        body, seeds = by_body[contact.label[3]]
        i, j = contact.label[4]
        edge = _edge_vector(body.original_vertices[i], body.original_vertices[j])
        sign = 1 if edge == contact.tangent else -1
        if tuple(sign * v for v in edge) != contact.tangent:
            raise ArithmeticError("contact tangent does not match its original edge")
        dt = tuple(sign * (seeds[j][k] - seeds[i][k]) for k in (0, 1))
        contact_seeds[contact.label] = (by_point[contact.point], dt)
    live = {body.body_id: (Q(0), Q(0), Q(0)) for body in geometry.assembly.bodies}
    return build_limit_seed2(problem, contact_seeds=contact_seeds, live_seeds=live, parameter=parameter)
