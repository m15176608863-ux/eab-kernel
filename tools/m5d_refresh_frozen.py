"""Actually rerun affected frozen closures and compare before publication.

No replay source is loaded in this orchestrator. Clean `python -c` children
bind precisely the entrypoint's runtime closure, not unrelated orchestrator
imports. Existing complete --adopt batches are verified, never stitched.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/codex/M5d_evidence"
TMP = OUT / "tmp"
STAGED = OUT / "recomputed_research"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")


def execute(name, code):
    environment = dict(os.environ, TEMP=str(TMP), TMP=str(TMP), PYTHONDONTWRITEBYTECODE="1",
                       PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    command = [sys.executable, "-X", "utf8", "-c", "import sys; from pathlib import Path; sys.path.insert(0,'tools'); "+code]
    log = TMP / (name+".log")
    started = time.perf_counter()
    with log.open("wb") as stream:
        proc = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=stream, stderr=subprocess.STDOUT)
        while proc.poll() is None:
            write(TMP / (name+"_driver_progress.json"), dict(complete=False, pid=proc.pid,
                  command=command, elapsed_seconds=time.perf_counter()-started, interruption_invalidates=True))
            time.sleep(5)
    if proc.returncode:
        raise RuntimeError(f"{name} failed; batch invalid, see {log}")
    write(TMP / (name+"_driver_progress.json"), dict(complete=True, command=command,
          exit_code=proc.returncode, elapsed_seconds=time.perf_counter()-started))


def check_binding(data):
    assert data["complete"] and data["source_hashes"] == data["source_hashes_end"]
    for key in ("input_hashes",):
        for name, expected in data[key].items():
            path = (ROOT / name).resolve()
            assert path.is_relative_to(ROOT) and sha(path) == expected, name


def seal_candidates(publication):
    """Unify every declared source/input/inherited map before any publication."""
    bindings = {}
    for row in publication:
        data = read(ROOT / row["candidate"])
        if isinstance(data, dict):
            assert data.get("complete", True), row["candidate"]
            if "source_hashes" in data:
                assert data["source_hashes"] == data["source_hashes_end"], "candidate source start/end differ"
            for key in ("input_hashes", "inherited_hashes", "inherited_stream_hashes"):
                for name, expected in data.get(key, {}).items():
                    assert name not in bindings or bindings[name] == expected, "candidate closures disagree: "+name
                    bindings[name] = expected
        else:
            assert isinstance(data, list), "only diagnostic arrays may omit binding metadata"
        bindings[row["candidate"]] = row["after_sha256"]
        bindings[row["backup"]] = row["before_sha256"]
    assert not set(bindings) & {row["target"] for row in publication}, "publication targets cannot be immutable inputs"
    verify_seal(bindings)
    return bindings


def verify_seal(bindings):
    for name, expected in bindings.items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT) and path.relative_to(ROOT).as_posix() == name
        assert sha(path) == expected, "source/input/candidate changed during publication: "+name


def atomic_copy(source, target):
    temporary = target.with_name(target.name+".m5d_writing")
    assert not temporary.exists(), "unfinished publication must be investigated, not overwritten"
    temporary.write_bytes(source.read_bytes())
    temporary.replace(target)


def publish_sealed(publication, bindings):
    """Fail closed and restore only our just-written, unchanged output bytes."""
    written = []
    try:
        verify_seal(bindings)
        for row in publication:
            verify_seal(bindings)
            target = ROOT / row["target"]
            assert sha(target) == row["before_sha256"], "publication target changed"
            atomic_copy(ROOT / row["candidate"], target)
            written.append(row)
            verify_seal(bindings)
        verify_seal(bindings)
    except BaseException:
        for row in reversed(written):
            target, backup = ROOT / row["target"], ROOT / row["backup"]
            assert sha(target) == row["after_sha256"], "external output edit prevents safe rollback"
            assert sha(backup) == row["before_sha256"], "backup changed; automatic rollback refused"
            atomic_copy(backup, target)
        raise


def main():
    global STAGED
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--robust", default="robust_full_m5d_r1")
    parser.add_argument("--research", default="research_full_m5d_r1")
    parser.add_argument("--adopt-complete", action="store_true", help="Verify two complete fresh runs instead of rerunning them")
    parser.add_argument("--stage", default="recomputed_research", help="New distributed candidate directory under M5d evidence")
    parser.add_argument("--backup", default="recomputed_before", help="New backup directory; failed attempts must use a new name")
    args = parser.parse_args()
    for name in (args.robust, args.research, args.stage, args.backup):
        if Path(name).name != name or name in (".", ".."):
            parser.error("single new directory names required")
    STAGED = OUT / args.stage
    stage_relative = STAGED.relative_to(ROOT).as_posix()
    TMP.mkdir(parents=True, exist_ok=True)
    STAGED.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(TMP)
    backup = OUT / args.backup
    backup.mkdir(exist_ok=False)
    if not args.adopt_complete:
        execute(args.robust, "import m5b_robust_replay as r; r.TMP=Path.cwd()/'reports/codex/M5d_evidence/tmp'; "
                f"sys.argv=['replay','--name',{args.robust!r}]; raise SystemExit(r.main())")
        execute(args.research, "import m5c_diagnostics as r; r.TMP=Path.cwd()/'reports/codex/M5d_evidence/tmp'; "
                f"r.EVIDENCE=Path.cwd()/{stage_relative!r}; "
                f"sys.argv=['research','--name',{args.research!r}]; r.main()")
    fresh = read(TMP / args.robust / "summary.json")
    studied = read(STAGED / "research_summary.json")
    assert read(TMP / args.robust / "progress.json")["complete"]
    assert read(TMP / args.research / "progress.json")["complete"]
    check_binding(fresh)
    check_binding(studied)
    old_robust = read(ROOT / "reports/codex/M5b_evidence/robust_summary.json")
    old_research = read(ROOT / "reports/codex/M5c_evidence/research_summary.json")
    assert fresh["counts"] == old_robust["counts"] and fresh["references"] == old_robust["references"]
    assert studied["counts"] == old_research["counts"] and studied["references"] == old_research["references"]
    assert (STAGED / "research_diagnostics.json").read_bytes() == (ROOT / "reports/codex/M5c_evidence/research_diagnostics.json").read_bytes()
    for case, row in fresh["cases"].items():
        assert row["complete"] and row["counts"] == old_robust["cases"][case]["counts"]
        assert row["references"] == old_robust["cases"][case]["references"]
        check_binding(dict(row, input_hashes=fresh["input_hashes"]))
        assert sha(ROOT / fresh["raw_directory"] / case / "pairs.jsonl.gz") == row["raw_sha256"]
    (STAGED / "robust_summary.json").write_bytes((TMP / args.robust / "summary.json").read_bytes())
    execute("m5d_rebuild_combined", "import m5c_publish_combined as p; "
            f"p.publish(output={stage_relative+'/combined_summary.json'!r}, "
            f"fresh={stage_relative+'/robust_summary.json'!r}, "
            f"research={stage_relative+'/research_summary.json'!r}, "
            f"diagnostics={stage_relative+'/research_diagnostics.json'!r})")
    execute("m5d_rebuild_minimal", "import m5b_minimal_examples as p; "
            f"p.TARGET=Path.cwd()/{stage_relative+'/robust_minimal_examples.json'!r}; "
            "p.freeze(); print('RECOMPUTED',p.verify())")
    execute("m5d_rebuild_research_minimal", "import m5c_research_examples as p; "
            f"p.research.EVIDENCE=Path.cwd()/{stage_relative!r}; "
            "p.TARGET=p.research.EVIDENCE/'research_minimal_examples.json'; p.freeze(); print('RECOMPUTED',p.verify())")
    execute("m5d_rebuild_initial_witnesses", "import m5c_initial_tube_witnesses as p; "
            f"p.research.EVIDENCE=Path.cwd()/{stage_relative!r}; p.main()")
    targets = {"robust_summary.json": "M5b_evidence", "robust_minimal_examples.json": "M5b_evidence",
               "research_summary.json": "M5c_evidence", "research_diagnostics.json": "M5c_evidence",
               "research_minimal_examples.json": "M5c_evidence", "research_initial_tube_witnesses.json": "M5c_evidence",
               "combined_summary.json": "M5c_evidence"}
    publication = []
    for name, directory in targets.items():
        target = ROOT / "reports/codex" / directory / name
        candidate = STAGED / name
        assert candidate.stat().st_size <= 1_000_000
        previous = target.read_bytes()
        (backup / name).write_bytes(previous)
        old, new = json.loads(previous), read(candidate)
        if name == "combined_summary.json":
            for key in ("counts", "references", "by_case", "candidate_join", "exact_observation_pairs_compared"):
                assert old[key] == new[key], (name, key)
        if name in ("robust_minimal_examples.json", "research_minimal_examples.json"):
            assert old["examples"] == new["examples"], name
        if name == "research_initial_tube_witnesses.json":
            assert old["rows"] == new["rows"] and old["counts"] == new["counts"]
        publication.append(dict(target=target.relative_to(ROOT).as_posix(), candidate=candidate.relative_to(ROOT).as_posix(),
                                backup=(backup/name).relative_to(ROOT).as_posix(), before_sha256=sha(target), after_sha256=sha(candidate)))
    write(OUT / "frozen_refresh_progress.json", dict(complete=False, verified_candidates=True, publication=publication))
    bindings = seal_candidates(publication)
    publish_sealed(publication, bindings)
    write(OUT / "frozen_refresh.json", dict(complete=True, numerical_products_unchanged=True,
          all_observations_rejoined=64010, newly_resolved_first_contact_candidates=68,
          robust_seconds=fresh["seconds"], research_seconds=studied["seconds"],
          orchestrator_sha256=sha(__file__), publication=publication, publication_bindings=bindings,
          reason="Necessary raw-ID documentation correction inside frozen runtime closure; complete real recomputation, not hash-only patching"))
    write(OUT / "frozen_refresh_progress.json", dict(complete=True, publication_count=len(publication)))
    print("M5D_FROZEN_REFRESH_GREEN", len(publication), "products genuinely recomputed")


if __name__ == "__main__":
    main()
