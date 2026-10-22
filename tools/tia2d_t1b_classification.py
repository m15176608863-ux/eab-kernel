"""T1b acceptance: classify saved critical bases, upgrade three rational roots.

No threshold is inferred from a narrow interval. Polynomial identities and
Sturm counts classify the saved bases; the unchanged ``critical_parameter``
contract performs 48-step exact rational/basis certification for upgrades.
Old outputs are read-only. This is an analysis tool, not a public kernel API.
"""
import argparse
from fractions import Fraction as Q
import gzip
import hashlib
import json
from math import gcd, isqrt, lcm
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.adapters.tia2d import g1_morphology
from eab.kernel2d.algebraic import (p_derivative, p_divmod, p_eval, p_gcd,
                                    p_scale, _root_count)
from eab.kernel2d.critical import rational_candidate2
from tia2d_t1b_morphology import diagnose, plot_curves, scan_parameters, source_manifest, wire


def _primitive(poly):
    denominator = lcm(*(v.denominator for v in poly))
    integers = tuple(int(v * denominator) for v in poly)
    common = gcd(*integers)
    return tuple(v // common for v in integers)


def _divide_fully(poly, factor):
    power = 0
    while len(poly) >= len(factor):
        quotient, remainder = p_divmod(poly, factor)
        if any(remainder):
            break
        poly, power = quotient, power + 1
    return poly, power


def root_factor(critical):
    """Extract the unique bracket root from exact critical-basis polynomials.

The factors mu and mu^2+1 have no roots in these positive brackets and are
removed by exact division. All other factors must be accounted for by an
exact rational root or a degree-two/three irreducibility witness.
"""
    lo, hi = Q(critical["mu_lo"]), Q(critical["mu_hi"])
    changing = []
    for branch in critical["critical_polynomials"]:
        for coefficients in [branch["determinant"]] + list(branch["numerators"]):
            poly = tuple(map(Q, coefficients))
            if any(poly) and p_eval(poly, lo) * p_eval(poly, hi) < 0:
                changing.append(poly)
    if not changing:
        raise ArithmeticError("no critical-basis sign change")
    common = changing[0]
    for poly in changing[1:]:
        common = p_gcd(common, poly)
    common, _ = _divide_fully(common, (Q(0), Q(1)))
    common, _ = _divide_fully(common, (Q(1), Q(0), Q(1)))
    common = p_divmod(common, p_gcd(common, p_derivative(common)))[0]
    common = p_scale(common, 1 / common[-1])
    if _root_count(common, lo, hi) != 1:
        raise ArithmeticError("critical root is not uniquely isolated")
    # Candidate generation only: acceptance requires exact polynomial zero.
    a, b = lo, hi
    rational = None
    for _ in range(80):
        candidate = rational_candidate2(a, b)
        if p_eval(common, candidate) == 0:
            rational = candidate
            common = (-candidate, Q(1))
            break
        middle = (a + b) / 2
        if _root_count(common, a, middle):
            b = middle
        else:
            a = middle
    integers = _primitive(common)
    degree = len(common) - 1
    witness = None
    if rational is not None:
        witness = {"rational_root": wire(rational)}
    elif degree == 2:
        discriminant = integers[1] ** 2 - 4 * integers[0] * integers[2]
        if discriminant <= 0 or isqrt(discriminant) ** 2 == discriminant:
            raise ArithmeticError("quadratic irrationality not established")
        witness = {"discriminant": discriminant, "integer_square": False}
    elif degree == 3:
        # A degree-preserving cubic with no root mod p is irreducible over Q.
        for prime in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97):
            residues = [sum(v * pow(x, k, prime) for k, v in enumerate(integers)) % prime
                        for x in range(prime)]
            if integers[-1] % prime and all(residues):
                witness = {"prime": prime, "nonzero_evaluation_residues": residues}
                break
        if witness is None:
            raise ArithmeticError("no modular cubic irreducibility witness")
    else:
        raise ArithmeticError("unclassified critical polynomial")
    return common, dict(degree=degree, coefficients_ascending=integers,
                       isolating_interval=[wire(lo), wire(hi)], root_count=1,
                       classification="rational" if rational is not None else "irrational",
                       irreducibility=witness)


def classify_saved_critical(critical):
    """Prove both saved branches continue up to the same isolated root.

Every determinant/numerator, after removal of the common root's factor,
has no remaining zero in the bracket. Endpoint ratios are nonnegative.
Thus the lower dual and upper primal ray extend on their respective sides;
the retained exact endpoint LP certificates establish the transition.
This deliberately does not claim attainedness for an irrational endpoint.
"""
    factor, result = root_factor(critical)
    lo, hi = map(Q, result["isolating_interval"])
    branches = []
    for branch in critical["critical_polynomials"]:
        sample = lo if branch["kind"] == "mechanism" else hi
        denominator = tuple(map(Q, branch["determinant"]))
        if p_eval(denominator, sample) == 0:
            raise ArithmeticError("singular endpoint basis")
        powers = []
        for index, coefficients in enumerate([branch["determinant"]] + list(branch["numerators"])):
            poly = tuple(map(Q, coefficients))
            if not any(poly):
                powers.append(None)
                continue
            residual, order = _divide_fully(poly, factor)
            if _root_count(residual, lo, hi):
                raise ArithmeticError("unaccounted branch root")
            if index and p_eval(poly, sample) / p_eval(denominator, sample) < 0:
                raise ArithmeticError("negative endpoint branch ratio")
            powers.append(order)
        branches.append(dict(kind=branch["kind"], sample=wire(sample),
                             factor_orders=powers, residual_root_counts=0))
    if {b["kind"] for b in branches} != {"mechanism", "improving_ray"}:
        raise ArithmeticError("both critical branches required")
    result["branch_continuation"] = branches
    # Algebraic root classification alone does not prove endpoint feasibility.
    result["attained"] = None
    return result


def _vertex_normals(face):
    for i, point in enumerate(face):
        normals = []
        for j in (i - 1, i):
            if 0 <= j < len(face) - 1:
                a, b = face[j:j + 2]
                normals.append((b[1] - a[1], a[0] - b[0]))
        yield point, normals


def _side_thrust(first, second, direction):
    best = None
    for p, first_normals in _vertex_normals(first):
        for q, second_normals in _vertex_normals(second):
            chord = (q[0] - p[0], q[1] - p[1])
            if chord[1] < 0:
                continue
            requirements = []
            for normals in (first_normals, second_normals):
                candidates = []
                for normal in normals:
                    dot = direction * (normal[0] * chord[0] + normal[1] * chord[1])
                    if dot > 0:
                        candidates.append(abs(normal[0] * chord[1] - normal[1] * chord[0]) / dot)
                if not candidates:
                    break
                requirements.append(min(candidates))
            if len(requirements) == 2:
                need = max(requirements)
                key = (need, -chord[1])
                if best is None or key < best[0]:
                    best = key, dict(mu=need, first=p, second=q, rise=chord[1],
                                     rise_span=chord[1] / abs(chord[0]))
    if best is None:
        raise ArithmeticError("no two-point thrust line")
    return best[1]


def thrust_line_prediction(geometry):
    """Vertex-force angle rule; not an independent geometry/LP oracle."""
    faces = geometry.interfaces
    left = _side_thrust(faces[0], faces[1], 1)
    right = _side_thrust(faces[3], faces[2], -1)
    return dict(mu=max(left["mu"], right["mu"]), left=left, right=right)


def branch_switch(tilt=Q(3, 32), height=Q(1, 16), span=Q(2)):
    def branches(amplitude):
        lower_slope = tilt + 2 * amplitude / height
        upper_slope = tilt - 2 * amplitude / height
        chord = height / (span - tilt * height)
        lower = (lower_slope - chord) / (1 + lower_slope * chord)
        upper = upper_slope - height / (2 * span) * (1 + upper_slope ** 2)
        return lower, upper
    lo, hi = Q(1, 4096), Q(1, 2048)
    for _ in range(80):
        mid = (lo + hi) / 2
        a, b = branches(mid)
        if a < b:
            lo = mid
        else:
            hi = mid
    return dict(amplitude_interval=(lo, hi), relative_to_1_over_4096=(lo * 4096, hi * 4096),
                one_sided_window_above_1_over_4096=(lo - Q(1, 4096), hi - Q(1, 4096)),
                threshold_interval=(branches(lo)[0], branches(hi)[0]))


def _write(path, value):
    data = (json.dumps(wire(value), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if path.suffix == ".gz":
        data = gzip.compress(data, mtime=0)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("fresh external output required")
    args.output.mkdir(parents=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    original = json.loads(args.source.read_text(encoding="utf-8"))
    before = source_manifest()
    before[Path(__file__).relative_to(ROOT).as_posix()] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    rows = [dict(row) for row in original["rows"]]
    parameters = scan_parameters()
    classifications, predictions, upgrades = [], [], []
    for index, row in enumerate(rows):
        old_path = next(Path(f["path"]) for f in original["files"] if Path(f["path"]).name == row["case"])
        if hashlib.sha256(old_path.read_bytes()).hexdigest() != row["sha256"]:
            raise ArithmeticError("frozen source integrity mismatch")
        prediction = thrust_line_prediction(g1_morphology(**parameters[index]))
        if row["mu_exact"] is None:
            saved = json.loads(gzip.decompress(old_path.read_bytes()))
            classification = classify_saved_critical(saved["critical"])
            classification["case_index_zero_based"] = index
            if classification["classification"] == "rational":
                record, updated = diagnose(max_steps=48, **parameters[index])
                expected = Q(classification["irreducibility"]["rational_root"])
                if Q(updated["mu_exact"]) != expected or updated["attained"] is not True:
                    raise ArithmeticError("unchanged critical_parameter did not certify rational root")
                classification["attained"] = True
                classification["attained_source"] = "48_step_critical_parameter_exact_basis_continuation"
                name = f"p1_case_{index:03d}_exact.json.gz"
                digest = _write(args.output / name, record)
                updated.update(case=name, sha256=digest,
                               predecessor_case=row["case"], predecessor_sha256=row["sha256"])
                rows[index] = row = updated
                upgrades.append(dict(case_index_zero_based=index, path=str(args.output / name), sha256=digest))
            classifications.append(classification)
        exact = Q(row["mu_exact"]) if row["mu_exact"] is not None else None
        lo, hi = (exact, exact) if exact is not None else (Q(row["mu_lo"]), Q(row["mu_hi"]))
        predictions.append(dict(case_index_zero_based=index, prediction=prediction,
                               lp_minus_thrust_interval=(lo - prediction["mu"], hi - prediction["mu"]),
                               relative_gap_interval=((lo - prediction["mu"]) / lo, (hi - prediction["mu"]) / hi)))
        print(f"P1 acceptance {index + 1}/36", flush=True)
    after = source_manifest()
    after[Path(__file__).relative_to(ROOT).as_posix()] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if before != after:
        raise ArithmeticError("source changed during acceptance processing")
    summary = dict(format="tia2d.t1b.acceptance.morphology.v1", complete=True,
                   source_pre_post_equal=True, source_sha256=before,
                   original_summary=str(args.source), original_summary_sha256=hashlib.sha256(args.source.read_bytes()).hexdigest(),
                   copied_rows_are_frozen_evidence_not_rerun=True, rows=rows, upgrades=upgrades,
                   critical_basis_classification=classifications, two_point_thrust_predictions=predictions,
                   branch_switch=branch_switch(), t1a_controls=original["t1a_controls"])
    _write(args.summary, summary)
    _write(args.output / "p1_acceptance_summary.json", summary)
    plot_curves(rows, args.summary.parent / "p1_figures")
    (args.output / "P1_ACCEPTANCE_COMPLETE").write_text("P1_ACCEPTANCE_COMPLETE\n", encoding="utf-8")


if __name__ == "__main__":
    main()
