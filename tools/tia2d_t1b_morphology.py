"""WO-T1b rational polygon scans; diagnostics, not a new tia2d-2 schema.

Interrupted runs have no completion marker and must be rerun in a fresh
directory. No Git executable is required, and no literature number is used.
"""
import argparse
from dataclasses import fields, is_dataclass
from fractions import Fraction as Q
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.adapters.tia2d import g1_morphology, g1_morphology_seed, morphology_geometry
from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.mobility import first_order_free_twists
from eab.kernel2d.sensitivity import evaluate_sensitivity2
from eab.kernel2d.statics import critical_parameter


def wire(value):
    """Lossless diagnostic projection, including original LP matrices."""
    if isinstance(value, Q):
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, float):
        return wire(Q(value))
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if is_dataclass(value):
        return {f.name: wire(getattr(value, f.name)) for f in fields(value)
                if not f.name.startswith("_") and f.name not in ("assembly", "contact_set")}
    if isinstance(value, dict):
        return {str(k): wire(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [wire(v) for v in value]
    raise TypeError(type(value).__name__)


def certificate_arithmetic(result):
    """Independent matrix arithmetic only, not the production LP validator."""
    A, b, c = result.problem.A, result.problem.b, result.problem.c
    dot = lambda a, x: sum((u * v for u, v in zip(a, x)), Q(0))
    def feasible(x, rhs):
        return (x is not None and len(x) == len(c) and min(x) >= 0
                and all(dot(row, x) == v for row, v in zip(A, rhs)))
    if result.status == "OPTIMAL":
        x, y = result.exact_x, result.exact_y
        return (feasible(x, b) and y is not None and len(y) == len(b)
                and all(sum(A[i][j] * y[i] for i in range(len(b))) >= c[j] for j in range(len(c)))
                and dot(c, x) == dot(b, y) == result.exact_value)
    if result.status == "UNBOUNDED":
        return (feasible(result.feasible_point, b)
                and feasible(result.improving_ray, (Q(0),) * len(b))
                and dot(c, result.improving_ray) > 0)
    return False


def diagnose(*, max_steps=40, mobility=True, **parameters):
    start = time.perf_counter()
    geometry = g1_morphology(**parameters)
    assembly = geometry.assembly
    contacts = assemble_contact_set2(assembly)
    critical = critical_parameter(assembly, contact_set=contacts, max_steps=max_steps)
    certificates = tuple(c for c in (critical.lower_certificate, critical.upper_certificate,
                                     critical.threshold_certificate) if c is not None)
    if critical.call_status != "OK" or not certificates or not all(certificate_arithmetic(c) for c in certificates):
        raise ArithmeticError("profile threshold certificates failed independent arithmetic")
    derivatives = {}
    for parameter in ("amplitude", "tilt"):
        seed = None
        if critical.threshold_certificate is not None:
            seed = g1_morphology_seed(critical.threshold_certificate.problem, geometry, parameter)
        unchanged_skeleton = geometry.amplitude > 0 or parameter == "tilt"
        derivatives[parameter] = evaluate_sensitivity2(critical, seed, parameter=parameter,
            positive_direction_valid=unchanged_skeleton,
            negative_direction_valid=unchanged_skeleton,
            validity_conditions=("L1 contact skeleton unchanged", "fixed A/t parameter direction"))
    first_order = first_order_free_twists(assembly, contacts) if mobility else None
    lower = critical.lower_certificate
    mechanism = None
    mode = "no_lower_mechanism_certificate"
    if lower is not None and lower.exact_y is not None:
        mechanism = tuple((label, value) for label, value in zip(lower.problem.row_labels, lower.exact_y) if value)
        rotation = any(label[1] == 2 for label, value in mechanism)
        mode = "associated_translation_rotation" if rotation else "associated_translation"
    record = dict(format="tia2d.t1b.morphology.diagnostic.v1", case_v1_export=False,
        profile="profile1", geometry=wire(geometry), assembly=wire(assembly.bodies),
        contact_status=contacts.status, constraint_count=len(contacts.constraints),
        critical=wire(critical), derivatives=wire(derivatives), first_order=wire(first_order),
        mechanism_below_threshold=wire(mechanism), mode=mode,
        certificate_arithmetic=True, seconds=time.perf_counter() - start)
    row = dict(family=geometry.family, amplitude=wire(geometry.amplitude),
        wavelength=wire(geometry.wavelength), amplitude_over_wavelength=wire(geometry.amplitude / geometry.wavelength),
        height=wire(geometry.height), tilt=wire(geometry.tilt), phase=wire(geometry.phase),
        asymmetry=wire(geometry.asymmetry), periods=geometry.periods,
        mu_lo=wire(critical.mu_lo), mu_hi=wire(critical.mu_hi),
        mu_exact=wire(critical.exact_threshold), attained=critical.attained,
        mode=mode, first_order=first_order.status if first_order is not None else "not_queried",
        derivatives={p: dict(status=d.differentiability, left=wire(d.left_derivative),
            right=wire(d.right_derivative), reason=d.reason) for p, d in derivatives.items()},
        seconds=record["seconds"])
    return record, row


def scan_parameters():
    """One-dimensional design curves plus targeted cross-parameter controls."""
    cases = []
    for tilt in (Q(3, 32), Q(11, 128)):
        for amplitude in (Q(1, 4096), Q(1, 2048), Q(1, 1024)):
            for phase in (Q(0), Q(1, 4), Q(1, 2)):
                cases.append(dict(tilt=tilt, amplitude=amplitude, phase=phase))
    for periods in (2, 4):
        for phase in (Q(0), Q(1, 4), Q(1, 2)):
            cases.append(dict(periods=periods, phase=phase))
    for tilt in (Q(3, 32), Q(11, 128)):
        for asymmetry in (Q(1, 4), Q(3, 4)):
            cases.append(dict(tilt=tilt, asymmetry=asymmetry))
        for amplitude in (Q(1, 4096), Q(1, 2048), Q(1, 1024)):
            cases.append(dict(family="kinked", tilt=tilt, amplitude=amplitude))
        cases.append(dict(tilt=tilt, amplitude=Q(0)))
    return tuple(cases)


def _dump(path, payload):
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    if path.suffix == ".gz":
        data = gzip.compress(data, mtime=0)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def plot_curves(rows, output):
    """Ordinary engineering plots; exact source values remain in the summary."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    output.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
    def line(ax, subset, field, label):
        selected = sorted(subset, key=lambda row: Q(row[field]))
        if not selected:
            return
        xx = [float(Q(row[field])) for row in selected]
        yy = [float(Q(row["mu_exact"])) if row["mu_exact"] is not None
              else float((Q(row["mu_lo"]) + Q(row["mu_hi"])) / 2) for row in selected]
        ax.plot(xx, yy, "o-", label=label, linewidth=1.3, markersize=4)
        for x, y, row in zip(xx, yy, selected):
            if row["mu_exact"] is None:
                ax.plot(x, y, "o", markerfacecolor="white", markeredgecolor="black", markersize=5)
            elif row["attained"] is False:
                ax.plot(x, y, "x", color="black", markersize=8, markeredgewidth=1.5)
    saw = [r for r in rows if r["family"] == "sawtooth"]
    for t in (Q(3, 32), Q(11, 128)):
        subset = [r for r in saw if Q(r["tilt"]) == t and r["periods"] == 1
                  and Q(r["phase"]) == 0 and Q(r["asymmetry"]) == Q(1, 2)]
        line(axes[0, 0], subset, "amplitude_over_wavelength", f"t={t}")
        subset = [r for r in saw if Q(r["tilt"]) == t and r["periods"] == 1
                  and Q(r["phase"]) == 0 and Q(r["amplitude"]) == Q(1, 2048)]
        line(axes[1, 1], subset, "asymmetry", f"t={t}")
    for amplitude in (Q(1, 4096), Q(1, 2048), Q(1, 1024)):
        subset = [r for r in saw if Q(r["amplitude"]) == amplitude and r["periods"] == 1
                  and Q(r["phase"]) == 0 and Q(r["asymmetry"]) == Q(1, 2)]
        line(axes[0, 1], subset, "tilt", f"A={amplitude}")
        subset = [r for r in saw if Q(r["amplitude"]) == amplitude and r["periods"] == 1
                  and Q(r["tilt"]) == Q(3, 32) and Q(r["asymmetry"]) == Q(1, 2)]
        line(axes[1, 0], subset, "phase", f"A={amplitude}")
    for ax, xlabel in zip(axes.flat, ("A / wavelength", "tilt t", "adjacent phase / cycle", "tooth peak fraction")):
        ax.set_xlabel(xlabel)
        ax.set_ylabel("critical friction coefficient")
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8)
    fig.suptitle("T1b true polygon profiles: h=1/16, fixed ends, associated flow\n"
                 "Filled: exact closed; cross: exact open; hollow: certified bracket", fontsize=10)
    fig.savefig(output / "p1_design_curves.png", dpi=160)
    fig.savefig(output / "p1_design_curves.svg")
    plt.close(fig)


def source_manifest():
    """Hash the full Python implementation, not merely visible direct imports."""
    paths = sorted((ROOT / "src/eab").rglob("*.py")) + [Path(__file__).resolve()]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--max-steps", type=int, default=40)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--figures", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("fresh output directory required; interrupted runs must be rerun")
    args.output.mkdir(parents=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    tmp = ROOT / "reports/codex/T1b_evidence/tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(tmp)
    before = source_manifest()
    _dump(args.output / "p1_source_before.json", before)
    started = time.perf_counter()
    rows, files = [], []
    parameters = scan_parameters()
    progress = args.output / "progress.jsonl"
    for index, params in enumerate(parameters):
        record, row = diagnose(max_steps=args.max_steps, **params)
        name = f"p1_case_{index:03d}.json.gz"
        digest = _dump(args.output / name, record)
        row.update(case=name, sha256=digest)
        rows.append(row)
        files.append(dict(path=str(args.output / name), sha256=digest, bytes=(args.output / name).stat().st_size))
        with progress.open("a", encoding="utf-8", newline="") as stream:
            stream.write(json.dumps(dict(completed=index + 1, total=len(parameters), case=name,
                elapsed_seconds=time.perf_counter() - started)) + "\n")
        print(f"P1 {index + 1}/{len(parameters)} {row['family']} mu={row['mu_exact']} bracket=({row['mu_lo']},{row['mu_hi']})", flush=True)
    controls = []
    for family in ("TIA-G2", "TIA-G3", "TIA-G4"):
        geometry = morphology_geometry(family)
        critical = critical_parameter(geometry.assembly, max_steps=args.max_steps)
        controls.append(dict(family=family, amplitude=wire(geometry.amplitude),
            wavelength=wire(geometry.wavelength), mu_exact=wire(critical.exact_threshold), attained=critical.attained,
            certificate_arithmetic=certificate_arithmetic(critical.threshold_certificate)))
    after = source_manifest()
    _dump(args.output / "p1_source_after.json", after)
    if before != after:
        raise SystemExit("source changed during scan: invalid run, no completion marker")
    summary = dict(format="tia2d.t1b.morphology.summary.v1", complete=True,
        source_revision=args.source_revision, revision_is_baseline_not_dirty_bytes=True,
        source_sha256=before, source_pre_post_equal=True,
        max_steps=args.max_steps, rows=rows, t1a_controls=controls, files=files,
        elapsed_seconds=time.perf_counter() - started)
    _dump(args.summary, summary)
    _dump(args.output / "p1_manifest.json", summary)
    plot_curves(rows, args.figures or args.summary.parent / "p1_figures")
    (args.output / "P1_COMPLETE").write_text("P1_COMPLETE\n", encoding="utf-8")
    print(f"P1_COMPLETE {len(rows)} cases; {summary['elapsed_seconds']:.3f} seconds")


if __name__ == "__main__":
    main()
