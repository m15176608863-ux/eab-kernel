"""T1b acceptance supplement: exact thickness bands for in-phase sawteeth.

This is an adapter-side diagnostic, not a frozen public or tia2d-2 contract.
The zero-friction band reference uses elementary contact-wrench convexity,
independently of the production contact constructor and LP solver. Exact
positive threshold candidates still need the existing critical-basis and LP
certificates; a two-point thrust-line guess alone is never accepted.
"""
import argparse
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

from eab.adapters.tia2d import g1_morphology
from eab.kernel2d.critical import ThresholdProof2, branch_signs2, candidate_is_boundary2
from eab.kernel2d.statics import critical_parameter, limit_load_ideal_exact_2d
from tia2d_t1b_morphology import certificate_arithmetic, wire


TILT = Q(3, 32)
SPACING = Q(2)
MAX_RATIO = Q(3, 16)
PRIMARY_FAMILIES = ((Q(1, 64), 1, Q(1, 2)),
                    (Q(1, 128), 1, Q(1, 4)),
                    (Q(1, 256), 2, Q(1, 2)),
                    (Q(1, 256), 2, Q(1, 4)))
CONTROL_FAMILIES = ((Q(1, 64), 2, Q(1, 2)),
                    (Q(1, 64), 2, Q(1, 4)))


def zero_friction_band(relative_amplitude, periods, asymmetry):
    """Analytic zero-mu boundary for phase zero, 0 < h/ell <= 3/16.

For one side block normalize the positive horizontal resultant to one.
Its wrench is encoded by (q,b), where q=Fy/Fx and b=z+q*g(z),
g=t*(z-1/2)+a*f(z). At mu=0 there are only two possible q values,
s_up and s_down. The vertical section width D(q) of their endpoint
convex hull is affine in q. Side equilibrium is r*D(q)>=q, so the
minimum admissible r is attained at an endpoint q=s_up or s_down.
Reflection supplies central-body force and moment balance. All slopes
are positive in the accepted domain, excluding an unbounded zero-load
self-stress as mu tends to zero. Thus r below this boundary has a
strictly positive threshold, not merely an unattained zero threshold.
"""
    a, eta = Q(relative_amplitude), Q(asymmetry)
    if (periods not in (1, 2) or eta not in (Q(1, 2), Q(1, 4))
            or not 0 < a <= Q(1, 64)):
        raise ValueError("band reference requires the stated positive-amplitude scan domain")
    up = TILT + a * periods / eta
    down = TILT - a * periods / (1 - eta)
    if down <= 0:
        raise ValueError("positive facet slopes required for the closed-zero proof")
    rise_up = 1 - (1 - eta) / periods
    rise_down = 1 - eta / periods
    width_up = rise_up * (1 + up * TILT) + up * a
    width_down = rise_down * (1 + down * TILT) - down * a
    upper = min(up / width_up, down / width_down)
    lower = TILT / (1 + TILT * TILT)
    return dict(relative_amplitude=a, periods=periods, asymmetry=eta,
                phase=Q(0), tilt=TILT, spacing=SPACING, ratio_domain=(Q(0), MAX_RATIO),
                slopes=(up, down), wrench_widths=(width_up, width_down),
                facet_zero_boundaries=(up / width_up, down / width_down),
                flat_zero_boundary=lower, toothed_zero_boundary=upper,
                nonempty=upper > lower,
                morphology_creates_threshold_interval=(lower, upper) if upper > lower else None,
                interval_closed=(True, False) if upper > lower else None,
                zero_at_toothed_boundary_attained=True)


def descending_strut_candidate(ratio, relative_amplitude, periods, asymmetry):
    """Candidate only: first descending peak to the last trough, same facet slope."""
    r, a, eta = Q(ratio), Q(relative_amplitude), Q(asymmetry)
    slope = TILT - a * periods / (1 - eta)
    rise = 1 - eta / periods
    shift = TILT * rise - a
    return max(Q(0), (slope - r * (rise + slope * shift))
               / (1 + r * (slope * rise - shift)))


def certified_thickness_sample(ratio, relative_amplitude, periods, asymmetry, *, max_steps=32):
    """Retain exact LP arithmetic and one-sided basis continuation at a candidate.

The candidate formula is not advertised over an unverified parameter cell.
Every positive value returned here is certified for this exact input.
"""
    r, a, eta = Q(ratio), Q(relative_amplitude), Q(asymmetry)
    if not 0 < r <= MAX_RATIO:
        raise ValueError("thickness ratio outside the stated scan domain")
    h = SPACING * r
    geometry = g1_morphology(height=h, amplitude=a * h, tilt=TILT,
                             periods=periods, phase=Q(0), asymmetry=eta)
    flat = g1_morphology(height=h, amplitude=Q(0), tilt=TILT)
    flat_critical = critical_parameter(flat.assembly, max_steps=max_steps)
    critical = critical_parameter(geometry.assembly, max_steps=max_steps)
    candidate = descending_strut_candidate(r, a, periods, eta)
    proof = critical.threshold_proof
    threshold = critical.threshold_certificate
    if critical.exact_threshold != candidate:
        if critical.exact_threshold is not None or candidate <= 0:
            raise ArithmeticError("descending strut is not the certified critical branch")
        lower, upper = critical.critical_polynomials
        lo, hi = Q(critical.mu_lo), Q(critical.mu_hi)
        if not lo < candidate <= hi or not candidate_is_boundary2(candidate, lower, upper):
            raise ArithmeticError("candidate is not an exact critical-basis root in the bracket")
        below = branch_signs2(lower, lo, candidate)
        if below is None:
            raise ArithmeticError("no lower-side dual continuation certificate")
        threshold = limit_load_ideal_exact_2d(geometry.assembly, mu=candidate)
        if threshold.status != "UNBOUNDED":
            raise ArithmeticError("this scan requires a closed rational threshold")
        proof = ThresholdProof2(candidate, True, lower, upper, (lo, candidate),
                                (candidate, hi), below, branch_signs2(upper, candidate, hi))
    certificates = tuple(c for c in (flat_critical.lower_certificate,
        flat_critical.upper_certificate, flat_critical.threshold_certificate,
        critical.lower_certificate, critical.upper_certificate, threshold) if c is not None)
    if not certificates or not all(certificate_arithmetic(c) for c in certificates):
        raise ArithmeticError("independent exact matrix certificate arithmetic failed")
    expected_flat = max(Q(0), TILT - r * (1 + TILT * TILT))
    if flat_critical.exact_threshold != expected_flat or not flat_critical.attained:
        raise ArithmeticError("flat T1a threshold check failed")
    if threshold.status != "UNBOUNDED":
        raise ArithmeticError("threshold itself must be feasible and closed")
    record = dict(format="tia2d.t1b.thickness.diagnostic.v1", formal_schema_export=False,
        ratio=r, relative_amplitude=a, periods=periods, asymmetry=eta,
        geometry=geometry, assembly=geometry.assembly.bodies,
        exact_threshold=candidate, attained=True,
        flat_threshold=expected_flat, flat_critical=flat_critical,
        critical_bracket=critical, threshold_certificate=threshold,
        threshold_proof=proof, certificate_arithmetic=True)
    return record


def certified_thick_control(ratio, relative_amplitude, periods, asymmetry):
    """A discrete thick-body zero-mu query, not a claim for all thick bodies."""
    r, a, eta = Q(ratio), Q(relative_amplitude), Q(asymmetry)
    geometry = g1_morphology(height=SPACING * r, amplitude=SPACING * r * a,
                             tilt=TILT, periods=periods, phase=Q(0), asymmetry=eta)
    certificate = limit_load_ideal_exact_2d(geometry.assembly, mu=Q(0))
    if certificate.status != "UNBOUNDED" or not certificate_arithmetic(certificate):
        raise ArithmeticError("thick control did not certify a closed zero threshold")
    return dict(ratio=r, relative_amplitude=a, periods=periods, asymmetry=eta,
                exact_threshold=Q(0), attained=True, certificate=certificate,
                certificate_arithmetic=True)


def _dump(path, value):
    data = (json.dumps(wire(value), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if path.suffix == ".gz":
        data = gzip.compress(data, mtime=0)
    path.write_bytes(data)
    return dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def _sources():
    paths = sorted((ROOT / "src/eab").rglob("*.py"))
    paths += [Path(__file__).resolve(), ROOT / "tools/tia2d_t1b_morphology.py"]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("fresh output directory required")
    args.output.mkdir(parents=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    tmp = ROOT / "reports/codex/T1b_evidence/tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(tmp)
    before = _sources()
    _dump(args.output / "source_before.json", before)
    started = time.perf_counter()
    bands, rows, files = [], [], []
    for family_index, (a, n, eta) in enumerate(PRIMARY_FAMILIES + CONTROL_FAMILIES):
        band = zero_friction_band(a, n, eta)
        bands.append(band)
        lo, hi = band["flat_zero_boundary"], band["toothed_zero_boundary"]
        if band["nonempty"]:
            ratios = (lo - Q(1, 4096), lo, (3 * lo + hi) / 4,
                      (lo + hi) / 2, (lo + 3 * hi) / 4, hi,
                      hi + Q(1, 4096), MAX_RATIO)
            if family_index == 0:
                ratios += (Q(3, 32),)
        else:
            ratios = (lo, (lo + MAX_RATIO) / 2, MAX_RATIO)
        for sample_index, r in enumerate(ratios):
            record = certified_thickness_sample(r, a, n, eta)
            name = f"thickness_{family_index:02d}_{sample_index:02d}.json.gz"
            metadata = _dump(args.output / name, record)
            files.append(metadata)
            rows.append(dict(family_index=family_index, ratio=r, relative_amplitude=a,
                periods=n, asymmetry=eta, exact_threshold=record["exact_threshold"],
                attained=record["attained"], flat_threshold=record["flat_threshold"],
                case=name, sha256=metadata["sha256"]))
            progress = dict(completed=len(rows), family=family_index, sample=sample_index,
                            elapsed_seconds=time.perf_counter() - started)
            with (args.output / "progress.jsonl").open("a", encoding="utf-8", newline="") as stream:
                stream.write(json.dumps(progress) + "\n")
            print(f"THICKNESS {len(rows)} n={n} eta={eta} r={r} mu={record['exact_threshold']}", flush=True)
    thick_controls = []
    for a, n, eta in PRIMARY_FAMILIES + CONTROL_FAMILIES:
        for r in (Q(3, 16), Q(1, 4), Q(1, 2)):
            thick_controls.append(certified_thick_control(r, a, n, eta))
    files.append(_dump(args.output / "thick_controls.json.gz", thick_controls))
    after = _sources()
    _dump(args.output / "source_after.json", after)
    if before != after:
        raise SystemExit("source changed during scan; no completion marker")
    summary = dict(format="tia2d.t1b.thickness.summary.v1", complete=True,
        source_revision=args.source_revision, source_pre_post_equal=True,
        source_sha256=before, bands=bands, rows=rows, files=files,
        thick_controls=[{k: v for k, v in row.items() if k != "certificate"}
                        for row in thick_controls],
        threshold_claim="samplewise exact LP and one-sided basis certificates",
        band_claim="analytic all-ratio zero-friction boundary on the stated six fixed families",
        elapsed_seconds=time.perf_counter() - started)
    _dump(args.summary, summary)
    _dump(args.output / "manifest.json", summary)
    (args.output / "THICKNESS_COMPLETE").write_text("THICKNESS_COMPLETE\n", encoding="utf-8")
    print(f"THICKNESS_COMPLETE {len(rows)} samples; {summary['elapsed_seconds']:.3f} seconds")


if __name__ == "__main__":
    main()
