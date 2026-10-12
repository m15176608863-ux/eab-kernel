"""M4a: copy-only legacy capture for the 15-case verify_cpp FAMILY.

Run only from this repository; no sibling Python code is imported or executed.
The copied executable runs under reports/codex/M4a_evidence/sandbox.  Three steps
cover initialization and two transfers, not the full 400-step family horizon.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from run_bdda_kernel import BDDA, KERNEL, ROOT, run, sha256

sys.path.insert(0, str(ROOT / "src"))
from eab.readers.bdda_df import load_records  # noqa: E402
from eab.readers.bdda_geom import load_step_geometries  # noqa: E402

FAMILY = [(c, c, "golden") for c in ("52", "12", "50", "51", "03", "05", "06", "09", "10")]
FAMILY += [("v01", "v01", "golden"), ("v01", "v01a", "golden"),
           ("v02", "v02", "golden"), ("v02", "v02a", "golden"),
           ("F038", "F038", "bench"), ("S038", "S038", "bench")]
KEEP = ("bdda_debug_contacts.csv", "bdda_debug_verts.csv", "bdda_debug_detparams.csv",
        "bdda_debug_df18.csv", "bdda_debug_df22.csv", "bdda_debug_cand.csv")
EVIDENCE = ROOT / "reports" / "codex" / "M4a_evidence"
MANIFEST = EVIDENCE / "family_manifest.json"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def fixture_summary(path: Path, steps: int) -> list[dict]:
    """Check step completeness/references; record rather than erase raw duplicates."""
    geom = load_step_geometries(path / "bdda_debug_verts.csv")
    contacts = rows(path / "bdda_debug_contacts.csv")
    params = rows(path / "bdda_debug_detparams.csv")
    expected = list(range(1, steps + 1))
    assert sorted(geom) == expected, (path.name, sorted(geom))
    assert sorted(int(r["step"]) for r in params) == expected, path.name
    assert sorted({int(r["step"]) for r in contacts}) == expected, path.name
    records = load_records(path)
    assert records, path.name
    per_step = []
    for step in expected:
        cs = [c for c in contacts if int(c["step"]) == step]
        recs = [r for r in records if r.step == step]
        keys = [r.canonical_key() for r in recs]
        duplicates = [[r.contact_index for r in recs if r.canonical_key() == key]
                      for key, count in Counter(keys).items() if count > 1]
        vs = geom[step].vertex_block()
        for c in cs:
            assert int(c["mtype"]) in (0, 1), (path.name, c)
            for field in ("p1", "p2", "p3"):
                assert geom[step].canon(int(c[field])) in vs, (path.name, step, field, c)
        dpar = next(r for r in params if int(r["step"]) == step)
        per_step.append({"step": step, "blocks": len(geom[step].blocks),
                         "vertices": len(vs), "contacts": len(cs),
                         "unique_canonical_keys": len(set(keys)), "duplicate_contact_groups": duplicates,
                         "types": dict(sorted(Counter(c["mtype"] for c in cs).items())),
                         "detparams": {k: float(v) for k, v in dpar.items() if k != "step"}})
    return per_step


def compare_repeat(first: Path, second: Path) -> dict:
    """All selected cells except documented first-step o3/o4 must reproduce."""
    differences = []
    nonrepro_differences = []
    nonrepro_counts: dict[str, int] = {}
    byte_identical = []
    for name in KEEP:
        a, b = rows(first / name), rows(second / name)
        assert len(a) == len(b), (name, "repeat row count", len(a), len(b))
        ignored = 0
        for index, (ra, rb) in enumerate(zip(a, b), 2):
            assert ra.keys() == rb.keys(), (name, "repeat header")
            for col in ra:
                if ra[col] == rb[col]:
                    continue
                initial_refs = name in ("bdda_debug_contacts.csv", "bdda_debug_df18.csv") and ra["step"] == "1" and col in ("o3", "o4")
                # df.c:3994 jumps over the only assignment at :4030 for open/VV.
                skipped_shear_update = (name == "bdda_debug_df22.csv" and ra["step"] == "1" and col == "o4"
                                        and (ra["mtype"] == "1" or ra["m0_new"] == "0"))
                if initial_refs or skipped_shear_update:
                    ignored += 1
                    nonrepro_differences.append({"file": name, "line": index, "column": col,
                                                "first": ra[col], "repeat": rb[col],
                                                "rule": "initial_uninitialized_reference" if initial_refs else "df22_skipped_shear_update"})
                else:
                    differences.append({"file": name, "line": index, "column": col,
                                        "first": ra[col], "repeat": rb[col]})
        if ignored:
            nonrepro_counts[name] = ignored
        if sha256(first / name) == sha256(second / name):
            byte_identical.append(name)
    return {"byte_identical_files": byte_identical, "documented_nonreproducible_cells": nonrepro_counts,
            "documented_differences": nonrepro_differences,
            "unexplained_differences": differences}


def verify_manifest() -> dict:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert len(data["cases"]) == 15
    assert {(c["bb"], c["db"], c["source"]) for c in data["cases"]} == {(f"bb{b}", f"db{d}", source) for b, d, source in FAMILY}
    for case in data["cases"]:
        folder = ROOT / case["fixture"]
        for name, info in case["files"].items():
            assert sha256(folder / name) == info["sha256"], (case["case"], name)
            assert (folder / name).stat().st_size == info["bytes"]
        assert fixture_summary(folder, case["steps"]) == case["per_step"], case["case"]
        assert not case["repeat"]["unexplained_differences"], case["case"]
    return {"cases": len(data["cases"]), "steps": sum(c["steps"] for c in data["cases"]),
            "fixture_bytes": sum(f["bytes"] for c in data["cases"] for f in c["files"].values()),
            "status": "verified"}


def capture(steps: int, resume: bool = False) -> dict:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S_%f")
    sandbox = EVIDENCE / "sandbox" / stamp
    data = {"schema": "m4_bdda_capture_v1", "captured_at_local": datetime.now().isoformat(),
            "family_source": "D:/b-DDA/tools/bdda/verify_cpp.py:33-37; _dir:49-50",
            "family_source_sha256": sha256(BDDA / "tools" / "bdda" / "verify_cpp.py"),
            "kernel_source": str(KERNEL), "kernel_sha256": sha256(KERNEL),
            "run_protocol": {"BDDA_KERNEL_MODE": "1", "BDDA_DF17_DEBUG": "1", "BDDA_DUMP_STEPS": str(steps)},
            "inherited_bdda_environment": {k: v for k, v in os.environ.items() if k.startswith("BDDA_")},
            "step_rationale": f"{steps} steps: initialization plus {steps - 1} state transfers; not full-history or engineering validation.",
            "observable": "static_detection_at_step_start_before_df25_update; not current-step first-entrance motion",
            "motion_limit": "Successive vertices are previous-step motion and may include rotation/strain; zsto2 first solve is not guaranteed final after retries.",
            "window_source": "Per-step detparams: d0,h1,h5,f1,f0,w0,hh,g0; no bb52 fallback used.",
            "screen_limit": "Legacy w0 depends on GetSystemMetrics; screen dimensions not fixed by this capture. Preserve actual per-step detparams.",
            "retention": {"csv": list(KEEP), "inputs": "frozen bb/db original bytes", "pruned_columns": [],
                          "omitted": "Other raw debug outputs, executable and progress wall_clock remain only in sandbox."},
            "cases": []}
    if resume:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert data["run_protocol"]["BDDA_DUMP_STEPS"] == str(steps)
        for case in data["cases"]:
            case["repeat"] = compare_repeat(ROOT / case["sandbox_capture"], ROOT / case["sandbox_repeat"])
            case["per_step"] = fixture_summary(ROOT / case["fixture"], case["steps"])
            assert not case["repeat"]["unexplained_differences"], case["repeat"]
    for bbc, dbc, source in FAMILY:
        bb, db = f"bb{bbc}", f"db{dbc}"
        tag = f"{bb}_N{steps}" if bbc == dbc else f"{bb}_{db}_N{steps}"
        if any(c["bb"] == bb and c["db"] == db for c in data["cases"]):
            continue
        dest = ROOT / "fixtures" / "bdda_df" / tag
        if dest.exists() and not resume:
            raise FileExistsError(f"Refusing to replace existing fixture: {dest}")
        source_dir = BDDA / "df" / ("bench" if source == "bench" else "")
        inputs = {name: sha256(source_dir / name) for name in (bb, db)}
        start = time.perf_counter()
        if dest.exists():
            # Recover an interrupted capture only when every frozen byte matches.
            candidates = [p for p in (EVIDENCE / "sandbox").glob(f"*/capture/{tag}")
                          if all((p / n).exists() and sha256(p / n) == sha256(dest / n)
                                 for n in (*KEEP, bb, db))]
            assert len(candidates) == 1, (tag, "ambiguous capture recovery", candidates)
            first_work = candidates[0]
            repeat = first_work.parent.parent / "repeat" / tag
            assert repeat.exists(), (tag, "missing repeat")
            captured = dest
        else:
            captured = run(bb, db, steps, source, sandbox=sandbox / "capture", tag=tag,
                           keep=KEEP, include_inputs=True)
            repeat = run(bb, db, steps, source, sandbox=sandbox / "repeat", tag=tag, ingest=False)
            first_work = sandbox / "capture" / tag
        for path in (first_work, repeat):
            assert sha256(path / KERNEL.name) == data["kernel_sha256"]
            assert {name: sha256(path / name) for name in inputs} == inputs
        assert {name: sha256(source_dir / name) for name in inputs} == inputs
        result = {"case": bbc if bbc == dbc else f"{bbc}/{dbc}",
                  "fixture": captured.relative_to(ROOT).as_posix(), "bb": bb, "db": db,
                  "source": source, "steps": steps, "input_sha256": inputs,
                  "sandbox_capture": first_work.relative_to(ROOT).as_posix(),
                  "sandbox_repeat": repeat.relative_to(ROOT).as_posix(),
                  "elapsed_seconds": time.perf_counter() - start,
                  "files": {p.name: {"sha256": sha256(p), "bytes": p.stat().st_size}
                            for p in sorted(captured.iterdir()) if p.is_file()},
                  "per_step": fixture_summary(captured, steps),
                  "repeat": compare_repeat(first_work, repeat)}
        data["cases"].append(result)
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        assert not result["repeat"]["unexplained_differences"], result["repeat"]
        print(f"VERIFIED {result['case']}: {[x['contacts'] for x in result['per_step']]} contacts", flush=True)
    return verify_manifest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--resume", action="store_true", help="keep completed capture pairs and append remaining cases")
    args = parser.parse_args()
    result = verify_manifest() if args.verify_only else capture(args.steps, args.resume)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
