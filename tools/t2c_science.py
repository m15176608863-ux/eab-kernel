"""WO-T2c1 evidence orchestration, not a geometric verifier.

Only calls the unchanged production and independent checkers. Search failures
bound a proposer search frontier, NEVER the mathematical escape threshold.
Every probe is journalled; a source-changing or interrupted run is not final.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / name) for name in ("src", "tools", "tests")]

from eab.kernel2d.se2_cage import verify_se2_cage
from eab.kernel2d.translation_space import translation_component
from t2_se2_grid import CASES
from t2b_cage_proposer import encode, scientific_instance, write_json
from t2b_independent_cage_verifier import _load_result
from t2b_independent_instances import OCTAGON, SQUARE, canonical_instance, dovetail_instance


OLD = Path("D:/eab-evidence/reports/codex/T2b_evidence/certificates")
DEFAULT_OUTPUT = Path("D:/eab-evidence/reports/codex/T2c1_evidence/certificates")


def journal(output, **row):
    row["epoch"] = time.time()
    with (output / "progress.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(encode(row), ensure_ascii=False) + "\n")
        stream.flush()
    print(json.dumps(encode(row), ensure_ascii=False), flush=True)


def instance_comparison(case_id, delta, instance):
    case = next(row for row in CASES if row[0] == case_id)
    if case[1] != "dovetail":
        return {"applicable": False, "reason": "no independent knob generator; unchanged production input"}
    other = dovetail_instance(F(case[2]), F(case[3]), OCTAGON if case[4] == "octagon" else SQUARE,
                              case[5], delta)
    equal = canonical_instance(instance) == canonical_instance(other)
    if not equal:
        raise AssertionError("independent instance mismatch; stop: " + case_id)
    return {"applicable": True, "equal": equal}


def check_cage_files(instance_path, certificate_path):
    """Both original text entries; no replacement or relaxed acceptance logic."""
    production = verify_se2_cage(instance_path.read_text("utf-8"), certificate_path.read_text("utf-8"))
    independent = _load_result(instance_path, certificate_path)
    result = {"production": asdict(production), "independent": independent,
              "independent_entry": "load_json(instance_path), load_json(certificate_path)"}
    if production.valid != independent["valid"]:
        raise AssertionError("cage verifier disagreement; stop and preserve inputs")
    if not production.valid or not independent["valid"]:
        raise AssertionError("proposer emitted a rejected cage; stop and preserve inputs")
    if production.condition != "ACCEPTED" or independent["condition"] != "OK":
        raise AssertionError("unexpected successful cage status")
    return result


def freeze_sources(output):
    names = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                                    cwd=ROOT).decode("utf-8").split("\0")
    names = sorted({name for name in names if name and (ROOT / name).is_file()
                    and (name.endswith(".py") or name == "docs/t2b_cage_lemma.md")})
    manifest = []
    with zipfile.ZipFile(output / "tested_source.zip", "w", zipfile.ZIP_DEFLATED) as bundle:
        for name in names:
            data = (ROOT / name).read_bytes()
            bundle.writestr(name, data)
            manifest.append({"path": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    write_json(output / "source_manifest.json", {"source_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(), "tool_version": "t2c1-science-1",
        "dirty_bytes_preserved_in_zip": True, "files": manifest})
    return manifest


def check_frozen(manifest):
    changed = [row["path"] for row in manifest if not (ROOT / row["path"]).is_file()
               or hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() != row["sha256"]]
    return changed


def baseline_case(row, output):
    """Copy accepted historical evidence unchanged and recheck current checkers."""
    case_id = row["case_id"]
    source = Path(row.get("certificate_directory", OLD / "science_02" / case_id))
    destination = output / case_id / "baseline"
    destination.mkdir(parents=True)
    origins = {}
    for name in ("instance.json", "certificate.json"):
        shutil.copyfile(source / name, destination / name)
        origins[name] = {"path": str(source / name), "sha256": hashlib.sha256((source / name).read_bytes()).hexdigest()}
    for name in ("escape_instance.json", "escape_candidate.json"):
        path = OLD / "science_02" / case_id / name
        shutil.copyfile(path, destination / name)
        origins[name] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    check = check_cage_files(destination / "instance.json", destination / "certificate.json")
    instance, _ = scientific_instance(case_id, F(row["delta_cage"]))
    frozen = json.loads((destination / "instance.json").read_text("utf-8"))
    if canonical_instance(instance) != canonical_instance(frozen):
        raise AssertionError("historical lower geometry mismatch")
    compare = instance_comparison(case_id, F(row["delta_cage"]), instance)
    translation = translation_component(instance["moving"], instance["obstacles"])
    if translation.status != "TRAPPED_TRANSLATION":
        raise AssertionError("cage/translation contradiction")
    check.update(instance_comparison=compare, translation_status=translation.status, origins=origins)
    write_json(destination / "recheck.json", check)
    return destination, check


def cage_probe(case_id, delta, destination, resources, modes, halfwidths):
    from t2c_cage_proposer import propose_cage
    instance, center = scientific_instance(case_id, delta)
    comparison = instance_comparison(case_id, delta, instance)
    destination.mkdir(parents=True)
    started = time.perf_counter()
    result = propose_cage(instance, center=center, resources=resources, modes=modes, halfwidths=halfwidths)
    record = {"delta": delta, "status": result["status"], "seconds": time.perf_counter() - started,
              "instance_comparison": comparison, "attempts": result["attempts"], "diagnostic": result["diagnostic"]}
    if result["status"] == "CERTIFIED_CAGE":
        write_json(destination / "instance.json", instance)
        write_json(destination / "certificate.json", result["certificate"])
        record["dual_verification"] = check_cage_files(destination / "instance.json", destination / "certificate.json")
        translation = translation_component(instance["moving"], instance["obstacles"])
        record["translation_status"] = translation.status
        if translation.status != "TRAPPED_TRANSLATION":
            raise AssertionError("cage/translation contradiction")
    write_json(destination / "probe.json", record)
    return record


def grid_middle(low, high, exponent):
    """An interior binary-grid point, or None if none exists."""
    denominator = 2 ** exponent
    tick = ((low + high) * denominator / 2).__floor__()
    if F(tick, denominator) <= low:
        tick = (low * denominator).__floor__() + 1
    middle = F(tick, denominator)
    return middle if low < middle < high else None


def escape_probe(case_id, delta, seed, destination, resources):
    from t2c_escape_proposer import audit_proposal, propose_escape
    instance, _ = scientific_instance(case_id, delta)
    comparison = instance_comparison(case_id, delta, instance)
    candidate = propose_escape(case_id, delta, seed, resources=resources, output=destination)
    record = {"delta": delta, "status": candidate["status"], "attempts": candidate["attempts"],
              "instance_comparison": comparison, "t2b_scope_accepted": False}
    if candidate["status"] == "PROPOSAL_UNVERIFIED":
        audit = audit_proposal(instance, candidate)
        record["audit"] = audit
        record["audit_status"] = audit["status"]
        # This is the explicit inherited T2b scope, NOT an independent proof of
        # the infinite tail. Strict eligibility in the proposal tool stays false.
        record["t2b_scope_accepted"] = audit["finite_and_production_valid"]
    write_json(destination / "probe.json", record)
    return record, candidate


def run(output, identifiers, *, exponent=12, max_probes=32, seconds=30, max_intervals=128,
        modes=("disk", "capped", "closed"), halfwidths=None, baseline_only=False,
        escape_seconds=45, accept_t2b_escape_scope=False):
    if not 12 <= exponent <= 16 or max_probes < 0:
        raise ValueError("grid exponent must be 12..16 and probes nonnegative")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "state.json", {"complete": False, "phase": "STARTING"})
    manifest = freeze_sources(output)
    rows = json.loads((ROOT / "reports/codex/T2b_evidence/scientific_summary.json").read_text("utf-8"))["rows"]
    results = []
    for old in rows:
        if old["case_id"] not in identifiers:
            continue
        case_id = old["case_id"]
        destination, baseline_check = baseline_case(old, output)
        lower, upper, threshold = F(old["delta_cage"]), F(old["delta_escape"]), F(old["delta_translation_star"])
        best_dir = destination
        best_escape_dir = destination
        seed = json.loads((destination / "escape_candidate.json").read_text("utf-8"))
        probes = []
        search_failure_frontier = upper
        escape_failure_frontier = lower
        if not baseline_only:
            from t2c_cage_proposer import CageResources
            from t2c_escape_proposer import EscapeResources, audit_proposal
            resources = CageResources(max_seconds=seconds, max_intervals=max_intervals,
                                      max_loop_vertices=2049, max_cells=256, max_cap_steps=256,
                                      max_refinements=10)
            escape_resources = EscapeResources(max_seconds=escape_seconds, max_cells=2000000,
                max_path_nodes=200000, steps=(F(1, 400),), tube_radii=(1, 3))
            escape_instance, _ = scientific_instance(case_id, upper)
            old_escape_audit = audit_proposal(escape_instance, seed)
            old_escape_audit["instance_comparison"] = instance_comparison(case_id, upper, escape_instance)
            if not old_escape_audit["finite_and_production_valid"]:
                raise AssertionError("historical escape no longer passes original checkers")
            write_json(destination / "escape_recheck.json", old_escape_audit)
            for index in range(max_probes):
                cage_delta = grid_middle(lower, min(upper, search_failure_frontier), exponent)
                escape_delta = grid_middle(max(lower, escape_failure_frontier), upper, exponent)
                if cage_delta is None and escape_delta is None:
                    break
                kind = "cage" if (index % 2 == 0 and cage_delta is not None) or escape_delta is None else "escape"
                delta = cage_delta if kind == "cage" else escape_delta
                target = output / case_id / (kind + "_" + str(index).zfill(3))
                journal(output, case_id=case_id, phase=kind+"_start", delta=delta)
                if kind == "cage":
                    record = cage_probe(case_id, delta, target, resources, modes, halfwidths)
                    if record["status"] == "CERTIFIED_CAGE":
                        lower, best_dir = delta, target
                    else:
                        search_failure_frontier = delta
                else:
                    record, candidate = escape_probe(case_id, delta, seed, target, escape_resources)
                    if record["t2b_scope_accepted"] and accept_t2b_escape_scope:
                        upper, best_escape_dir, seed = delta, target, candidate
                    else:
                        escape_failure_frontier = delta
                if lower >= upper:
                    raise AssertionError("cage/escape endpoint contradiction; stop and preserve all inputs")
                probes.append({"kind": kind, "directory": str(target), **record})
                journal(output, case_id=case_id, phase=kind+"_end", delta=delta,
                        status=record["status"], lower=lower, upper=upper)
        certificate = json.loads((best_dir / "certificate.json").read_text("utf-8"))
        if not lower < upper <= threshold:
            raise AssertionError("bracket order violated")
        width = upper - lower
        row = {"case_id": case_id, "delta_disk": old["delta_disk"], "old_delta_cage": old["delta_cage"],
               "new_delta_cage": lower, "old_delta_escape": old["delta_escape"], "new_delta_escape": upper,
               "delta_translation_star": threshold, "width": width,
               "relative_width": width / threshold, "target_met": width / threshold <= F(1, 256),
               "intervals": len(certificate["intervals"]), "uses_caps": bool(certificate["caps"]),
               "full_circle": certificate["chain"]["kind"] == "closed", "cage_directory": str(best_dir),
               "escape_directory": str(best_escape_dir), "baseline_cage_recheck": baseline_check,
               "grid_exponent": exponent, "search_failure_frontier_not_a_bound": search_failure_frontier,
               "escape_failure_frontier_not_a_bound": escape_failure_frontier,
               "cage_search_frontier_grid_resolved": grid_middle(lower, min(upper, search_failure_frontier), exponent) is None,
               "escape_search_frontier_grid_resolved": grid_middle(max(lower, escape_failure_frontier), upper, exponent) is None,
               "probes": probes, "outside_bracket": "UNPROVED",
               "escape_scope": "T2b: production full path and infinite tail; independent finite path and ray prefix" if accept_t2b_escape_scope
                               else "historical accepted upper retained; fresh escape search recorded separately"}
        write_json(output / case_id / "summary.json", row)
        results.append(row)
        write_json(output / "summary.json", {"complete": False, "rows": results})
    changed = check_frozen(manifest)
    summary = {"complete": not changed, "rows": results, "source_changed": changed,
               "configuration": {"exponent": exponent, "max_probes": max_probes, "seconds": seconds,
                                 "max_intervals": max_intervals, "modes": modes, "halfwidths": halfwidths,
                                 "escape_seconds": escape_seconds, "accept_t2b_escape_scope": accept_t2b_escape_scope},
               "nonclaim": "Search-frontier bisection does not shrink a certified bracket after an UNPROVED result."}
    write_json(output / "summary.json", summary)
    write_json(output / "state.json", {"complete": not changed, "phase": "FINISHED" if not changed else "INVALID_SOURCE_CHANGED"})
    if changed:
        raise RuntimeError("source changed during run; this run cannot be final evidence")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cases", nargs="+", default=[row[0] for row in CASES])
    parser.add_argument("--grid-exponent", type=int, default=12)
    parser.add_argument("--max-probes", type=int, default=32)
    parser.add_argument("--seconds", type=float, default=30)
    parser.add_argument("--max-intervals", type=int, default=128)
    parser.add_argument("--modes", nargs="+", default=["disk", "capped", "closed"])
    parser.add_argument("--halfwidths", nargs="+", type=F)
    parser.add_argument("--baseline-only", action="store_true")
    parser.add_argument("--escape-seconds", type=float, default=45)
    parser.add_argument("--accept-t2b-escape-scope", action="store_true",
                        help="explicitly use the accepted T2b finite independent oracle scope; never claim independent infinite verification")
    args = parser.parse_args()
    result = run(args.output, args.cases, exponent=args.grid_exponent, max_probes=args.max_probes,
                 seconds=args.seconds, max_intervals=args.max_intervals, modes=tuple(args.modes),
                 halfwidths=args.halfwidths, baseline_only=args.baseline_only,
                 escape_seconds=args.escape_seconds, accept_t2b_escape_scope=args.accept_t2b_escape_scope)
    print(json.dumps({"complete": result["complete"], "cases": len(result["rows"])}))


if __name__ == "__main__":
    main()
