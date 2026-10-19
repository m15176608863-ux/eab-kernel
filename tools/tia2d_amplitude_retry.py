"""Exact diagnostic retry of morphology amplitude threshold derivatives.

This is not a case.v1 exporter and does not synthesize a ThresholdProof2.
The signed-mu polynomial extension is diagnostic only: the input API still
requires mu >= 0. A feasible branch on both sides of zero, with no vanishing
basic component, is not a critical crossing branch. No slope is inferred
from a constant sampled threshold curve or from duplicate generator labels.
"""
import argparse
from collections import Counter
from fractions import Fraction as Q
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.adapters.tia2d import morphology_geometry, morphology_seed
from eab.kernel2d.algebraic import p_eval
from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.critical import affine_matrix2, improving_basis2, branch_signs2
from eab.kernel2d.mobility import first_order_free_twists
from eab.kernel2d.sensitivity import evaluate_sensitivity2
from eab.kernel2d.statics import build_limit_problem2, critical_parameter
from tia2d_cases import input_record, wire, _stable_body_references
from tia2d_morphology import FAMILIES, _json, _source_hashes, _measure
from tia2d_provenance import git_provenance


DELTA = Q(1, 1024)


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _sign(value):
    return (value > 0) - (value < 0)


def incidence_interval(geometry, lower_offset, upper_offset):
    """Input-only exact order-type certificate for this affine-x family.

Every original vertex against every original edge (including the same body)
and all vertex coordinate differences are affine in amplitude. Each scalar
has its coefficients and endpoint signs checked; identically zero scalars
    stay zero. These predicates retain edge incidences, endpoint ordering,
    nonzero edges, polygon simplicity and local vertex-cone types from the
    checked base geometry over the entire closed interval, not only its sample
    points. They do not read ContactSet2, entrance cells or LP coefficients.

The continuum here is the rational affine family. Binary64 queries remain
restricted to samples for which the adapter proves identity rounding.
"""
    vertices, edges = [], []
    for body, seeds in zip(geometry.assembly.bodies, geometry.vertex_seeds_amplitude):
        points = tuple(tuple(Q(v) for v in p) for p in body.original_vertices)
        for i, (point, seed) in enumerate(zip(points, seeds)):
            if seed[1] != 0:
                raise ValueError("this certificate requires fixed vertex y coordinates")
            vertices.append((body.body_id, i, point, seed))
            j = (i + 1) % len(points)
            edges.append((body.body_id, i, j, point, _sub(points[j], point),
                          seed, _sub(seeds[j], seed)))
    grouped = {}

    def record(kind, label, constant, linear):
        key = (constant, linear)
        if key not in grouped:
            low = constant + lower_offset * linear
            high = constant + upper_offset * linear
            signs = (_sign(constant), _sign(low), _sign(high))
            grouped[key] = dict(coefficients=key, signs=signs,
                constant_sign_on_interval=signs[0] == signs[1] == signs[2],
                count=0, kinds=Counter(), witness=label)
        grouped[key]["count"] += 1
        grouped[key]["kinds"][kind] += 1

    for bid, start, end, p, edge, dp, de in edges:
        for other, index, v, dv in vertices:
            offset, derivative = _sub(v, p), _sub(dv, dp)
            if _cross(de, derivative) != 0:
                raise ArithmeticError("vertex-edge orientation is not affine")
            record("vertex_edge", (bid, start, end, other, index),
                   _cross(edge, offset), _cross(de, offset) + _cross(edge, derivative))
    for i, (bid, index, p, dp) in enumerate(vertices):
        for other, j, v, dv in vertices[i + 1:]:
            for axis in (0, 1):
                record("coordinate_order", (bid, index, other, j, axis),
                       p[axis] - v[axis], dp[axis] - dv[axis])
    rows = tuple(grouped[key] for key in sorted(grouped))
    return dict(parameter="amplitude", base=geometry.amplitude,
        offset_interval=(lower_offset, upper_offset), coefficient_order="constant,linear",
        all_signs_constant=all(row["constant_sign_on_interval"] for row in rows),
        predicate_count=sum(row["count"] for row in rows), grouped_predicates=rows,
        validity="fixed table; fixed wavelength; shared affine vertices; identity-RN inputs only")


def _verify_limit(result):
    problem = result.problem
    for vector, rhs in ((result.feasible_point, problem.b),
                        (result.improving_ray, tuple(Q(0) for _ in problem.b))):
        if vector is None or any(v < 0 for v in vector):
            raise ArithmeticError("missing exact nonnegative limit certificate")
        if any(sum(a * x for a, x in zip(row, vector)) != value
               for row, value in zip(problem.A, rhs)):
            raise ArithmeticError("exact limit residual")
    if sum(a * x for a, x in zip(problem.c, result.improving_ray)) != 1:
        raise ArithmeticError("improvement must equal one")


def _verify_zero_cone(result):
    size = len(result.dofs)
    if result.status != "ZERO_CONE" or len(result.zero_certificates) != 2 * size:
        raise ArithmeticError("complete zero-cone certificate unavailable")
    for cert in result.zero_certificates:
        if any(v < 0 for v in cert.multipliers):
            raise ArithmeticError("negative zero-cone multiplier")
        actual = tuple(sum(w * row[k] for w, row in zip(cert.multipliers, result.matrix))
                       for k in range(size))
        expected = tuple(Q(cert.sign if k == cert.coordinate else 0) for k in range(size))
        if actual != expected:
            raise ArithmeticError("zero-cone residual")


def branch_attempt(result, matrix):
    """Return examined branch evidence; never promote it to threshold proof."""
    branch = improving_basis2(result, matrix)
    if branch is None:
        return dict(certified=False, reason="improving_basis_unavailable", branch=None)
    determinant_at_zero = p_eval(branch.determinant, Q(0))
    zero_components = tuple(k for k, p in enumerate(branch.numerators) if p_eval(p, Q(0)) == 0)
    # A strictly positive branch has no closed-threshold crossing component.
    left = branch_signs2(branch, -DELTA, Q(0))
    right = branch_signs2(branch, Q(0), DELTA)
    A, c = result.problem.A, result.problem.c
    swapped = []
    for j in branch.basis:
        partner = next((k for k in range(len(c)) if k != j and k not in branch.basis
                       and result.problem.column_labels[k][0] == result.problem.column_labels[j][0]
                       and all(row[k] == row[j] for row in A)), None)
        if partner is not None:
            swapped.append((j, partner))
    if not swapped:
        raise ArithmeticError("expected distinct coincident generator labels at mu=0")
    original, replacement = swapped[0]
    alternative = tuple(replacement if j == original else j for j in branch.basis)
    if alternative == branch.basis or any(tuple(row[j] for j in branch.basis) !=
                                        tuple(row[j] for j in alternative) for row in A):
        raise ArithmeticError("alternative labeled basis equality failed")
    positive = all(v > 0 for v in branch.sample_values)
    no_crossing = determinant_at_zero != 0 and positive and not zero_components
    reason = ("domain_boundary_without_crossing_basis" if no_crossing and left is not None
              and right is not None else "no_unique_critical_crossing_certified")
    return dict(certified=False, reason=reason, branch=branch,
        determinant_at_zero=determinant_at_zero, zero_components=zero_components,
        all_basic_components_strictly_positive=positive,
        signed_mu_extension_only=True, left_interval=(-DELTA, Q(0)), right_interval=(Q(0), DELTA),
        left_sign_certificate=left, right_sign_certificate=right,
        alternative_labeled_basis=dict(basis=alternative, replaced=(original, replacement),
            exact_matrix_equal=True, sample_values=branch.sample_values,
            determinant_at_zero=determinant_at_zero),
        uniqueness_claim="distinct labels; crossing-basis contract does not certify a boundary-pinned threshold",
        threshold_proof_created=False)


def retry_case(family, amplitude=Q(1, 8), wavelength=Q(1)):
    clocks = {}
    geometry = _measure(clocks, "geometry", morphology_geometry, family,
                        amplitude=amplitude, wavelength=wavelength)
    contacts = _measure(clocks, "contacts", assemble_contact_set2, geometry.assembly)
    critical = _measure(clocks, "critical", critical_parameter, geometry.assembly,
                        contact_set=contacts, mu_max=1.0, max_steps=8)
    multi = _measure(clocks, "first_order", first_order_free_twists, geometry.assembly, contacts)
    l1 = _measure(clocks, "L1_interval", incidence_interval, geometry,
                  -DELTA if amplitude else Q(0), DELTA)
    seed = morphology_seed(critical.threshold_certificate.problem, geometry, "amplitude")
    sensitivity = evaluate_sensitivity2(critical, seed, parameter="amplitude",
        validity_conditions=("L1接触骨架不变",),
        positive_direction_valid=bool(amplitude), negative_direction_valid=bool(amplitude))
    if amplitude:
        if not l1["all_signs_constant"]:
            raise ArithmeticError("positive amplitude interval changed incidence signs")
        result = critical.threshold_certificate
        _verify_limit(result)
        _verify_zero_cone(multi)
        one = build_limit_problem2(geometry.assembly, contacts, Q(1))
        matrix = affine_matrix2(result.problem, one)
        attempt = _measure(clocks, "exact_basis_retry", branch_attempt, result, matrix)
        problem = wire(result.problem)
        problem_one = wire(one)
        certificate = wire(result)
    else:
        changed = morphology_geometry(family, amplitude=DELTA, wavelength=wavelength)
        changed_contacts = assemble_contact_set2(changed.assembly)
        if l1["all_signs_constant"] or len(contacts.constraints) == len(changed_contacts.constraints):
            raise ArithmeticError("zero-amplitude control must show a contact-skeleton change")
        attempt = dict(certified=False, reason="L1_skeleton_changes_at_zero_amplitude", branch=None,
            constraint_counts=(len(contacts.constraints), len(changed_contacts.constraints)),
            maximal_segment_counts=(len(contacts.segments), len(changed_contacts.segments)),
            threshold_proof_created=False)
        problem = wire(critical.threshold_certificate.problem)
        problem_one, certificate = None, wire(critical.threshold_certificate)
    record = _stable_body_references(wire(dict(
        diagnostic_format="tia2d.amplitude-retry.v1", case_v1_export=False,
        family=family, amplitude=amplitude, wavelength=wavelength,
        assembly=input_record(geometry.assembly), local_table=geometry.table,
        vertex_amplitude_seeds=geometry.vertex_seeds_amplitude,
        contact_status=contacts.status, contact_points=contacts.points,
        L1_interval=l1, first_order=multi, exact_threshold=critical.exact_threshold,
        attained=critical.attained, limit_problem_zero=problem, limit_problem_one=problem_one,
        threshold_certificate=certificate, retry=attempt,
        amplitude_seed=seed, production_sensitivity=sensitivity,
        retry_sensitivity=dict(differentiability="unresolved", directional_derivative=None,
            left_derivative=None, right_derivative=None, reason=attempt["reason"]),
        interpretation="The crossing-basis contract does not apply at this domain boundary; the referee certifies no slope, but mu_crit stays locally zero wherever first-order immobility persists."
        )), [body.body_id for body in geometry.assembly.bodies])
    record["python_wallclock"] = clocks
    return record


def source_hashes():
    result = _source_hashes()
    for name in ("tools/tia2d_amplitude_retry.py", "tests/test_tia2d_amplitude_retry.py"):
        result[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    return result


def run_retry(directory):
    target = Path(directory).resolve()
    if not target.is_relative_to(ROOT / "reports/codex/T1a_evidence") or target.exists():
        raise ValueError("use a new evidence directory; interrupted retries cannot resume")
    target.mkdir(parents=True)
    sources = source_hashes()
    provenance = dict(source_sha256=sources, command=list(sys.argv),
        **git_provenance(ROOT),
        scope="diagnostic retry only; not a case.v1 export")
    _json(target / "run_status.json", dict(valid=False, state="running", provenance=provenance))
    rows, manifest = [], []
    start = time.perf_counter()
    try:
        for family in FAMILIES:
            for amplitude in (Q(1, 8), Q(0)):
                case = retry_case(family, amplitude)
                name = family + ("-positive" if amplitude else "-zero")
                path = target / (name + ".json")
                _json(path, case)
                row = dict(case_id=name, family=family, amplitude=case["amplitude"],
                    wavelength=case["wavelength"], exact_threshold=case["exact_threshold"],
                    attained=case["attained"], L1_interval_unchanged=case["L1_interval"]["all_signs_constant"],
                    first_order=case["first_order"]["mathematical_status"],
                    derivative=case["retry_sensitivity"],
                    wall_seconds=sum(value["seconds"] for value in case["python_wallclock"].values()))
                rows.append(row)
                manifest.append(dict(path=path.name, bytes=path.stat().st_size,
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
                with (target / "progress.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
                    stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
                print(name, row["derivative"]["reason"], round(row["wall_seconds"], 4), flush=True)
        if sources != source_hashes():
            raise RuntimeError("source changed during retry; invalidate and rerun")
        _json(target / "summary.json", rows)
        _json(target / "manifest.json", manifest)
        _json(target / "run_status.json", dict(state="complete", valid=True, cases=len(rows),
            wall_seconds=time.perf_counter() - start, provenance=provenance))
    except BaseException as error:
        _json(target / "run_status.json", dict(state="failed_or_interrupted", valid=False,
            completed=len(rows), reason=str(error), provenance=provenance))
        raise
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    temporary = ROOT / "reports/codex/T1a_evidence/tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    rows = run_retry(args.output)
    print("amplitude exact-basis retry:", len(rows), "complete; no invented derivatives", flush=True)


if __name__ == "__main__":
    main()
