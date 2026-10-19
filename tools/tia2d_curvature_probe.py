"""First-order smooth-circle counterexample, not a smooth-interface solver.

The analytic witness is rebuilt from rigid twist velocities and the radial
normal polynomial. It does not call ContactSet2, an entrance arrangement, DD
or an LP. Polygon queries separately use the production judge. Thus their
different answers exhibit a modelling limit, not a failed polygon solver.
No finite-motion, tolerance, elliptical-interface or sine-interface claim is
made. Rational inscribed vertices here are Python-only, not binary64 inputs.
"""
from dataclasses import asdict, is_dataclass
from fractions import Fraction as Q
from itertools import combinations
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.kernel2d.assembly import Assembly2, Body2
from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.mobility import first_order_free_twists


RADIUS = Q(1, 4)
CENTERS = tuple((Q(x), RADIUS) for x in (-3, -1, 1, 3))


def smooth_circle_witness():
    """Exact whole-arc normal-work identity using affine rigid velocities.

    Twists are expressed at global origin. Bodies 2/4 rotate about the outer
    circle centres; body 3 translates up at speed 2. For EVERY point p on
    each contact arc the relative velocity is omega*J(p-centre), so its dot
    product with the radial normal vanishes identically, not only at samples.
    The reversed twist has downward-load work 2. At mu=0 all admissible
    contact forces are radial and their virtual work vanishes, hence balance
    requires 2*F=0. Zero forces with F=0 are feasible; capacity is exactly 0.
    """
    twists = ((Q(0), Q(0), Q(0)), (RADIUS, Q(3), Q(1)),
              (Q(0), Q(2), Q(0)), (-RADIUS, Q(3), -Q(1)),
              (Q(0), Q(0), Q(0)))
    identities = []
    for center, left, right in zip(CENTERS, twists, twists[1:]):
        vx, vy, omega = (b - a for a, b in zip(left, right))
        cx, cy = center
        # (p-c) dot (dv + domega*J*p), coefficients [1,x,y,x*y].
        polynomial = (-cx * vx - cy * vy, vx - omega * cy,
                      vy + omega * cx, -omega + omega)
        assert polynomial == (0, 0, 0, 0)
        identities.append(dict(center=center, relative_origin_twist=(vx, vy, omega),
                               radial_velocity_coefficients=polynomial))
    reverse = tuple(tuple(-v for v in twist) for twist in twists)
    load_point = (Q(0), 2 * RADIUS)
    vx, vy, omega = reverse[2]
    load_velocity = (vx - omega * load_point[1], vy + omega * load_point[0])
    drive = -load_velocity[1]
    assert drive == 2 and all(not any(reverse[i]) for i in (0, 4))
    return dict(radius=RADIUS, centers=CENTERS, up_twists_at_origin=twists,
                down_twists_at_origin=reverse, arc_identities=tuple(identities),
                relative_angular_rates=tuple(row["relative_origin_twist"][2] for row in identities),
                downward_load_point=load_point, downward_load_velocity=load_velocity,
                downward_load_work=drive, contact_work=Q(0), fixed_support_work=Q(0),
                zero_force_feasible=True, exact_frictionless_capacity=Q(0),
                interpretation="first_order_only_not_finite_motion")


def inscribed_circle_chain(chords):
    """Build rational inscribed arcs, once per interface, without trigonometry."""
    if chords not in (2, 4, 8, 16):
        raise ValueError("probe chord count must be 2, 4, 8 or 16")
    arc = []
    for index in range(chords + 1):
        # Rational parametrization of the unit circle; t spans [-1,1].
        t = Q(2 * index - chords, chords)
        denominator = 1 + t * t
        arc.append((-RADIUS * (1 - t * t) / denominator,
                    RADIUS + 2 * RADIUS * t / denominator))
    faces = [((Q(-5), Q(0)), (Q(-5), 2 * RADIUS))]
    faces += [tuple((cx + x, y) for x, y in arc) for cx, _ in CENTERS]
    faces += [((Q(5), Q(0)), (Q(5), 2 * RADIUS))]
    origin = (Q(5, 8), -Q(3, 8))
    bodies = []
    for index, (left, right) in enumerate(zip(faces, faces[1:])):
        fixed = index in (0, 4)
        ring = (left[0], *right, *reversed(left[1:]))
        bodies.append(Body2.from_vertices("block_" + str(index + 1), ring,
            reference_point=origin, dof_anchor=origin,
            boundary_type="FIXED_BODY" if fixed else None,
            dof_mask=(0, 0, 0) if fixed else (1, 1, 1),
            live=(0, -1, origin[0]) if index == 2 else (0, 0, 0)))
    return Assembly2(tuple(bodies), tuple(combinations(range(5), 2)), "complete", mu=Q(0))


def polygon_certificate(assembly, label):
    start = perf_counter()
    contacts = assemble_contact_set2(assembly)
    answer = first_order_free_twists(assembly, contacts)
    seconds = perf_counter() - start
    assert contacts.status == "RESOLVED" and answer.cone_is_zero is True
    assert answer.exact_rank == 9 and len(answer.dofs) == 9
    # Independently recheck every +/- unit-coordinate combination.
    for proof in answer.zero_certificates:
        assert all(weight >= 0 for weight in proof.multipliers)
        actual = tuple(sum(row[k] * weight for row, weight in zip(answer.matrix, proof.multipliers))
                       for k in range(9))
        assert actual == tuple(proof.sign * int(k == proof.coordinate) for k in range(9))
    return dict(label=label, body_vertices=tuple(body.vertices for body in assembly.bodies),
                contact_status=contacts.status, first_order_status=answer.status,
                exact_rank=answer.exact_rank, dofs=answer.dofs, matrix=answer.matrix,
                zero_certificates=answer.zero_certificates, python_seconds=seconds)


def _wire(value):
    if isinstance(value, Q):
        return str(value.numerator) + "/" + str(value.denominator)
    if is_dataclass(value):
        return _wire(asdict(value))
    if isinstance(value, dict):
        return {key: _wire(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_wire(item) for item in value]
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    output.relative_to(ROOT / "reports" / "codex" / "T1a_evidence")
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    from eab.adapters.tia2d import morphology_geometry
    data = dict(format="tia2d.private-curvature-probe.v1", smooth=smooth_circle_witness(),
                polygon_results=[])
    data["polygon_results"].append(polygon_certificate(morphology_geometry("TIA-G3",
        amplitude=Q(1, 4), wavelength=Q(1, 2)).assembly, "TIA-G3-A3-W0_frozen_polygon"))
    for count in (2, 4, 8, 16):
        row = polygon_certificate(inscribed_circle_chain(count), "rational_inscribed_" + str(count))
        data["polygon_results"].append(row)
        print(row["label"], row["first_order_status"], flush=True)
    encoded = json.dumps(_wire(data), ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    assert len(encoded.encode("utf-8")) <= 1_000_000
    output.write_text(encoded, encoding="utf-8", newline="\n")
    print("smooth circle capacity 0; frozen G3 and 2/4/8/16 inscribed polygons ZERO_CONE")


if __name__ == "__main__":
    main()
