"""Recompute all 68 new-contact candidates, diagnose R2, independently try R3.

The full 1810-step frozen pair stream is traversed and bound, but only its
new-contact candidates are re-solved.  This is NOT a second all-pairs P2 root
replay.  Interrupted runs are invalid; a fresh --name is mandatory.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
from fractions import Fraction as F
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
import m5b_robust_replay as replay
from eab.kernel2d import model_robustness as old
from eab.kernel2d import m5c_certificates as new

EVIDENCE = ROOT / "reports/codex/M5c_evidence"
TMP = EVIDENCE / "tmp"


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _sources():
    # Actual imported local closure, captured before and after the computation.
    files = {Path(__file__).resolve()}
    for module in tuple(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if filename:
            path = Path(filename).resolve()
            if path.suffix == ".py" and path.is_relative_to(ROOT):
                files.add(path)
    return {p.relative_to(ROOT).as_posix(): _sha(p) for p in sorted(files)}


def _write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str)+"\n", encoding="utf-8")


def _display(value):
    return format(Decimal(value.numerator)/Decimal(value.denominator), ".9g")


def _compact(report):
    return dict(failed=report["failed"], guards={key: dict(
        surplus=_display(value),
        margin_over_error=(_display(1+value/report["errors"][key])
                           if report["errors"].get(key) else None))
        for key, value in report["guards"].items()})


def _old_diagnose(a, b, label, bracket, ra, rb, panels=4):
    lo, hi = bracket
    normals, gaps = old._normals(a, b), []
    for lower, upper in old._panels(F(0), lo, panels):
        best = None
        for normal in normals:
            norm = abs(normal[0])+abs(normal[1])
            anchor = old._value(a[0], lower)
            origin = sum(x*y for x, y in zip(anchor, normal))
            aa = tuple(old._projection(p, normal, lower, upper, origin) for p in a)
            bb = tuple(old._projection(p, normal, lower, upper, origin) for p in b)
            gap = max(min(x[0] for x in bb)-max(x[1] for x in aa),
                      min(x[0] for x in aa)-max(x[1] for x in bb))/norm
            best = gap if best is None else max(best, gap)
        gaps.append(best)
    if label[0] == "VE":
        p, q, rp, rq, i, j = a, b, ra, rb, label[1], label[2]
    else:
        p, q, rp, rq, i, j = b, a, rb, ra, label[2], label[1]
    begin = old._event(old._boxes(p, lo, lo), old._boxes(q, lo, lo), i, j, rp, rq)
    end = old._event(old._boxes(p, hi, hi), old._boxes(q, hi, hi), i, j, rp, rq)
    guards = dict(early_separation=min(gaps)-ra-rb,
                  endpoint_begin=-begin[0][1]-begin[3], endpoint_end=end[0][0]-end[3],
                  nominal_derivative=old._event_derivative(p, q, i, j, lo, hi)[0])
    errors = dict(early_separation=ra+rb, endpoint_begin=begin[3], endpoint_end=end[3])
    for lower, upper in old._panels(lo, hi, panels):
        aa, bb = old._boxes(a, lower, upper), old._boxes(b, lower, upper)
        for ring, radius in ((aa, ra), (bb, rb)):
            for edge, point in enumerate(ring):
                following = (edge+1) % len(ring)
                u = old._diff(ring[following], point)
                for k, other in enumerate(ring):
                    if k in (edge, following):
                        continue
                    v = old._diff(other, point)
                    error = 2*radius*(old._length1(u)+old._length1(v))+8*radius*radius
                    margin = old._cross(u, v)[0]-error
                    if "strict_convexity" not in guards or margin < guards["strict_convexity"]:
                        guards["strict_convexity"], errors["strict_convexity"] = margin, error
        for pp, qq, rr, ss, kind in ((aa, bb, ra, rb, "VE"), (bb, aa, rb, ra, "EV")):
            for ii in range(len(pp)):
                for jj in range(len(qq)):
                    key = (kind, ii, jj) if kind == "VE" else (kind, jj, ii)
                    f, g, h, ew, ev = old._event(pp, qq, ii, jj, rr, ss)
                    if key == tuple(label):
                        name, margin = "interior_projection", min(g[0]-ew, h[0]-ev)
                    else:
                        name = "competitor_"+kind
                        margin = max(f[0]-ew, -f[1]-ew, -g[1]-ew, -h[1]-ev)
                    if name not in guards or margin < guards[name]:
                        guards[name], errors[name] = margin, max(ew, ev)
    return dict(guards=guards, errors=errors, failed=tuple(k for k, v in guards.items() if v <= 0))


def _bracket(value, bits=30):
    lo, hi = F(0), F(1)
    for _ in range(bits):
        mid = (lo+hi)/2
        if value < mid:
            hi = mid
        else:
            lo = mid
    return lo, hi


def _pair(row, blocks, legacy):
    a, b = (replay.prepare(block) for block in blocks)
    one = replay.motion_first_entrance(a["start"], b["start"], a["end"], b["end"])
    two = replay.dda_first_entrance(a["start"], b["start"], a["motion"], b["motion"])
    assert one.initial_state == two.initial_state == -1
    assert one.status == two.status == "contact" and one.features == two.features
    assert len(one.features) == 1 and one.features[0][0] != "VV"
    p1, p2 = replay.record(one, a, b), replay.record(two, a, b)
    assert json.loads(json.dumps(p1, default=str)) == row["result"]["p1"]
    assert json.loads(json.dumps(p2, default=str)) == row["result"]["p2"]
    bounds = (replay._bracket(one.exact_time), replay._bracket(two.exact_time))
    r2_trials, old_pass = [], False
    for pad in (F(1, 256), F(1, 1024), F(1, 4096)):
        bracket = max(F(0), min(x[0] for x in bounds)-pad), min(F(1), max(x[1] for x in bounds)+pad)
        diagnostics = [_old_diagnose(a[key], b[key], one.features[0], bracket, a["radius"], b["radius"])
                       for key in ("paths1", "paths2")]
        production = [old.single_cover_certificate(a[key], b[key], one.features[0], bracket,
                                                   a["radius"], b["radius"]) for key in ("paths1", "paths2")]
        assert all(bool(value) == (not diag["failed"]) for value, diag in zip(production, diagnostics))
        passed = all(production)
        r2_trials.append(dict(bracket=bracket, diagnostics=diagnostics, passed=passed))
        old_pass |= passed
    assert old_pass == (row["result"]["classification"] == "ROBUST_SINGLE_FIRST_COVER")
    bounds = (_bracket(one.exact_time), _bracket(two.exact_time))
    center_low, center_high = min(x[0] for x in bounds), max(x[1] for x in bounds)
    # A tight enough bracket must not erase the required early separation.
    initial_pad = min(F(1, 256), center_low/4, (1-center_high)/4)
    r3_trials, new_certificate = [], None
    if initial_pad > 0:
        for divisor in (1, 4, 16, 64):
            pad = initial_pad/divisor
            bracket = center_low-pad, center_high+pad
            diagnostics = [new.diagnose_single_cover(a[key], b[key], one.features[0], bracket,
                                                      a["radius"], b["radius"])
                           for key in ("paths1", "paths2")]
            passed = all(not diag["failed"] for diag in diagnostics)
            r3_trials.append(dict(bracket=bracket, diagnostics=diagnostics, passed=passed))
            if passed:
                # Sign via the public production entrypoint, not the diagnostic.
                new_certificate = [new.single_cover_certificate(a[key], b[key], one.features[0], bracket,
                                                                  a["radius"], b["radius"])
                                   for key in ("paths1", "paths2")]
                assert all(new_certificate)
                break
            if all(diag["failed"] == ("early_separation",) for diag in diagnostics):
                # A conservative search policy, not a completeness claim:
                # squeezing the crossing bracket cannot generally fix global
                # convex-hull inseparability in a deeply interleaved concave pair.
                break
    signed = old_pass or bool(new_certificate)
    selected = {phase: replay.canonical_legacy_rows(
        [item for item in legacy[phase] if item["pair"] == row["pair"]], blocks) for phase in replay.PHASES}
    result = dict(classification="ROBUST_SINGLE_FIRST_COVER" if signed else "MODEL_SENSITIVE_OR_UNPROVED", p1=p1, p2=p2)
    return dict(case=row["case"], step=row["step"], pair=row["pair"],
                label=one.features[0], features=p1["features"], radius_sum=a["radius"]+b["radius"],
                r2_pass=old_pass, r3_pass=bool(new_certificate), certified_union=signed,
                r2_trials=r2_trials, r3_trials=r3_trials,
                legacy_counts=dict(replay.legacy_counts(result, selected)), legacy=selected,
                blocks=blocks, certificate=new_certificate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--summary", default="reports/codex/M5c_evidence/robust_full_m5c_r2_robust_summary_before.json")
    args = parser.parse_args()
    if Path(args.name).name != args.name or args.name in (".", ".."):
        raise ValueError("fresh single-directory name required")
    os.environ["TEMP"] = os.environ["TMP"] = str(TMP)
    out = TMP / args.name
    out.mkdir(parents=True, exist_ok=False)
    sources, inputs = _sources(), replay.input_hashes()
    summary_path = ROOT / args.summary
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    raw = ROOT / summary["raw_directory"]
    raw_paths = sorted(raw.glob("*/pairs.jsonl.gz"))
    inherited = {p.relative_to(ROOT).as_posix(): _sha(p) for p in [summary_path, *raw_paths]}
    counts, steps, candidates = Counter(), set(), []
    for path in raw_paths:
        for line in gzip.open(path, "rt", encoding="utf-8"):
            row = json.loads(line)
            counts["traversed_pairs"] += 1
            steps.add((row["case"], row["step"]))
            if row["result"].get("initial_state") == -1 and row["result"]["p1"]["status"] == "contact":
                candidates.append(row)
    assert counts["traversed_pairs"] == 64010 and len(steps) == 1810 and len(candidates) == 68
    wanted = {(r["case"], r["step"], block) for r in candidates for block in r["pair"]}
    blocks = {(r["case"], r["step"], r["block"]): r for r in replay.endpoint.iter_inputs()
              if (r["case"], r["step"], r["block"]) in wanted}
    legacy = {}
    for case in sorted({r["case"] for r in candidates}):
        legacy[case] = {r["step"]: r for r in (json.loads(line) for line in gzip.decompress(
            (replay.LEGACY / (case+".jsonl.gz")).read_bytes()).decode().splitlines())}
    started, results, compact_rows, references, by_case, failures = time.perf_counter(), [], [], Counter(), {}, Counter()
    _write(out / "progress.json", dict(complete=False, recomputed=0, interruption_invalidates=True))
    with gzip.open(out / "exact_diagnostics.jsonl.gz", "wt", encoding="utf-8", newline="\n") as stream:
        for row in candidates:
            result = _pair(row, [blocks[(row["case"], row["step"], block)] for block in row["pair"]],
                           legacy[row["case"]][row["step"]])
            results.append(result)
            stream.write(json.dumps(result, default=str, separators=(",", ":"))+"\n")
            stream.flush()
            for key in ("r2_pass", "r3_pass", "certified_union"):
                counts[key] += result[key]
            references.update(result["legacy_counts"])
            case_counts = by_case.setdefault(row["case"], Counter())
            case_counts.update({"candidates": 1, "r2_pass": result["r2_pass"], "r3_pass": result["r3_pass"],
                                "certified_union": result["certified_union"]})
            failed = sorted({name for trial in result["r2_trials"] for diag in trial["diagnostics"] for name in diag["failed"]})
            failures.update(failed)
            small = {key: result[key] for key in ("case", "step", "pair", "label", "features", "r2_pass", "r3_pass", "certified_union", "legacy_counts")}
            small["radius_sum"] = _display(result["radius_sum"])
            for key in ("r2_trials", "r3_trials"):
                small[key] = [dict(bracket=trial["bracket"], passed=trial["passed"],
                                   p1=_compact(trial["diagnostics"][0]), p2=_compact(trial["diagnostics"][1]))
                              for trial in result[key]]
            compact_rows.append(small)
            _write(out / "progress.json", dict(complete=False, recomputed=len(results), counts=counts,
                                                seconds=time.perf_counter()-started, interruption_invalidates=True))
            print(row["case"], row["step"], row["pair"], "R2", result["r2_pass"], "R3", result["r3_pass"], flush=True)
    assert len(results) == 68 and counts["r2_pass"] == 2
    after = _sources()
    assert after == sources and replay.input_hashes() == inputs
    assert inherited == {name: _sha(ROOT / name) for name in inherited}
    full = dict(schema="eab.m5c-independent-recertification.v1", complete=True,
                scope="1810-step/64010-pair stream traversed; only 68 new-contact pairs re-solved for P1/P2 and R2/R3; not a second all-pairs root replay",
                counts=dict(counts, recomputed_pairs=len(results), traversed_steps=len(steps)),
                by_case=by_case, r2_failed_condition_pair_counts=failures, references=references,
                source_hashes=sources, source_hashes_end=after, input_hashes=inputs, inherited_stream_hashes=inherited,
                exact_diagnostics_sha256=_sha(out / "exact_diagnostics.jsonl.gz"),
                exact_diagnostics_path=(out / "exact_diagnostics.jsonl.gz").relative_to(ROOT).as_posix(),
                seconds=time.perf_counter()-started,
                limits=["R3 is a sufficient research certificate, not independent G6 acceptance",
                        "uncertified pairs are not extrapolated", "C positive-radius exit ordering remains unproved"])
    _write(out / "summary.json", full)
    _write(out / "diagnostics.json", compact_rows)
    _write(out / "progress.json", dict(complete=True, counts=full["counts"]))
    for filename, payload in (("research_summary.json", full), ("research_diagnostics.json", compact_rows)):
        target = EVIDENCE / filename
        if target.exists():
            raise ValueError("refuse to overwrite frozen research evidence")
        _write(target, payload)
        if target.stat().st_size > 1_000_000:
            raise AssertionError("public evidence exceeds 1 MB; keep detailed rows only in tmp")
    print("M5C_RESEARCH_COMPLETE", full["counts"], flush=True)


if __name__ == "__main__":
    main()
