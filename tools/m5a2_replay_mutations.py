"""M5a2 internal replay/bounds mutations, with source-hash tripwires disabled.

Functions are compiled from their REAL source after one anchored replacement;
no fake row is appended after the tested production path. Ledger mutants are
serialized and re-frozen with freshly computed frame/file hashes before the
new independent semantic guard is run. Original fixtures/sources are read-only.
Each child has a finite timeout; incomplete runs may not be resumed.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M5a2_evidence"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools"), str(ROOT / "tests")]

MUTATIONS = {
    "swapped_stat_buckets": ("frame_result",
        '"separated_chord_same" if record["same_chord_status_and_cover"] else "separated_chord_different"',
        '"separated_chord_different" if record["same_chord_status_and_cover"] else "separated_chord_same"',
        "M5a2 frame independent stats"),
    "wrong_block_center": ("RigidFit.record", '"center": list(map(str, self.motion.center))',
        '"center": list(map(str, self.motion.translation))', "M5a2 frame independent blocks"),
    "phase_counts_use_chord": ("frame_result", 'counts[category] += 1',
        'counts[row["category"]] += 1', "M5a2 frame independent phase counts"),
    "swapped_models": ("frame_result", '\"rigid\": result, \"chord\": baseline_result',
                       '\"rigid\": baseline_result, \"chord\": result', "M5a2 ledger rigid status"),
    "chord_no_contact_shortcut": ("frame_result", "elif separation:",
        'elif separation or (prior is not None and prior["actual"]["status"] == "no_contact"):',
        "M5a2 ledger rigid status"),
    "classifier_uses_chord": ("frame_result",
        'category = classify_reference(pair["initial_state"], row["primary_reference"], pair["rigid"], pair["pd"])',
        'category = classify_reference(pair["initial_state"], row["primary_reference"], pair["chord"], pair["pd"])',
        "M5a2 ledger independently classified category"),
    "sweep_nine_fifths": ("_swept_bounds", "2*abs(m.u1)", "F(9, 5)*abs(m.u1)",
                          "M5a2 small-angle swept bounds contain path"),
    "same_time_wrong_branch": ("same_time", 'certificate["branch"] == -1', 'certificate["branch"] == 1',
                               "M5a2 same_time irrational matching branch"),
    "same_time_ignores_polynomial": ("same_time", "if time.sign_polynomial(c, b, F(1)):", "if False:",
                                    "M5a2 same_time rejects different irrational polynomial"),
}


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def inject(kind, monkeypatch):
    import m5a_se2_replay as replay
    from eab.kernel2d import se2
    expected = json.loads((ROOT / "fixtures/m5a_se2/expected.json").read_text(encoding="utf-8"))
    # Real source hashes are deliberately hidden BEFORE injecting the defect.
    monkeypatch.setattr(replay, "code_hashes", lambda: expected["code_hashes"])
    name, old, new, _ = MUTATIONS[kind]
    module = se2 if name == "_swept_bounds" else replay
    owner, field = (replay.RigidFit, "record") if name == "RigidFit.record" else (module, name)
    original = getattr(owner, field)
    source = dedent(inspect.getsource(original.fget if isinstance(original, property) else original))
    if isinstance(original, property):
        source = source.replace("@property\n", "", 1)
    assert source.count(old) == 1, "internal mutation anchor must be unique"
    mutated = source.replace(old, new)
    namespace = dict(vars(module))
    exec(compile(mutated, "<m5a2-internal-"+kind+">", "exec"), namespace)
    monkeypatch.setattr(owner, field, property(namespace[field]) if isinstance(original, property) else namespace[field])
    return {"function": module.__name__+"."+name,
            "original_function_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "mutant_function_sha256": hashlib.sha256(mutated.encode()).hexdigest(),
            "hash_tripwire_masked_before_mutation": True, "replacement": [old, new]}


def run_guard(kind, out, *, full_freeze=True):
    import test_m5a2_replay as gates
    import m5a_se2_replay as replay
    from fractions import Fraction as F
    if kind in ("swapped_stat_buckets", "wrong_block_center", "phase_counts_use_chord"):
        # The default suite guards the complete focused frame in well below
        # one second; long historical production-freeze checks stay separate.
        gates.test_live_focused_frame_aggregates_and_blocks_match_independent_semantics(*gates.CASES[0])
    elif kind.startswith("same_time_"):
        gates.test_same_time_irrational_uses_polynomial_and_correct_root_branch()
    elif kind == "sweep_nine_fifths":
        gates.test_small_angle_swept_bounds_contain_independent_asymmetric_paths(F(1, 10**6))
    else:
        case = gates.CASES[0]
        if not full_freeze:
            frame, sg, eg, baseline, _ = gates.real_inputs(*case)
            value = replay.frame_result(frame, sg, eg, baseline)
            payload = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
            frozen = out / "refrozen.jsonl.gz"
            frozen.write_bytes(gzip.compress(payload+b"\n", mtime=0))
            manifest = {"code_hashes": replay.code_hashes(), "frame_sha256": hashlib.sha256(payload).hexdigest(),
                        "normalized_sha256": hashlib.sha256(frozen.read_bytes()).hexdigest()}
            dump(out / "refrozen_expected.json", manifest)
            with gzip.open(frozen, "rb") as stream:
                readback = stream.read().rstrip(b"\n")
            assert hashlib.sha256(readback).hexdigest() == manifest["frame_sha256"]
            assert hashlib.sha256(frozen.read_bytes()).hexdigest() == manifest["normalized_sha256"]
            assert replay.code_hashes() == manifest["code_hashes"]
            gates.assert_ledger_semantics(*case, json.loads(readback))
            return
        # Recompute every actual bb05 prefix frame through the mutant, not
        # just one row and not a post-hoc fake value, then call REAL freeze().
        import pytest
        import ingest_fixtures
        source = ROOT / "fixtures/m4b_shadow/bb05.jsonl.gz"
        _, frames, _ = replay.chord.snapshot.read_snapshot(source)
        terminal = replay.chord.load_endpoint(ROOT / "fixtures/m4c_motion/endpoints.json", "bb05", source, frames)
        geometries = replay.chord.paired_geometries(frames, terminal)
        with gzip.open(ROOT / "reports/codex/M4c_evidence/fix_frozen_replay/bb05/normalized.jsonl.gz",
                       "rt", encoding="utf-8") as stream:
            baselines = list(map(json.loads, stream))
        records = [replay.frame_result(frame, sg, eg, baseline)
                   for (frame, sg, eg), baseline in zip(geometries, baselines)]
        sandbox = out / "freeze_sandbox"
        target_source = sandbox / "fixtures/m4b_shadow/bb05.jsonl.gz"
        target_source.parent.mkdir(parents=True)
        target_source.write_bytes(source.read_bytes())
        batch = sandbox / "batch"
        case_dir = batch / "bb05"
        case_dir.mkdir(parents=True)
        normalized = case_dir / "normalized.jsonl.gz"
        normalized.write_bytes(gzip.compress("".join(json.dumps(r, ensure_ascii=False)+"\n" for r in records).encode("utf-8"), mtime=0))
        audit = {"normalized_sha256": replay.file_hash(normalized),
                 "frame_sha256": [replay.digest(r) for r in records]}
        dump(case_dir / "audit.json", audit)
        dump(batch / "summary.json", {"complete": True, "code_hashes": replay.code_hashes(),
             "cases": {"bb05": {"audit_sha256": replay.file_hash(case_dir / "audit.json")}}})
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(replay, "ROOT", sandbox)
            patch.setattr(replay, "CASES", ("bb05",))
            patch.setattr(ingest_fixtures, "FIX", sandbox / "fixtures")
            manifest = replay.freeze(batch)
        frozen = sandbox / "fixtures/m5a_se2/bb05.jsonl.gz"
        with gzip.open(frozen, "rt", encoding="utf-8") as stream:
            readback = list(map(json.loads, stream))
        assert len(readback) == 30
        assert replay.file_hash(frozen) == manifest["cases"]["bb05"]["normalized_sha256"]
        assert [replay.digest(row) for row in readback] == manifest["cases"]["bb05"]["frame_sha256"]
        assert replay.code_hashes() == manifest["code_hashes"]
        dump(out / "refreeze_proof.json", {"production_freeze_called": True, "recomputed_frames": 30,
             "source_hash_tripwire_masked": True, "all_fresh_freeze_hash_checks_green": True,
             "frozen_file_sha256": replay.file_hash(frozen), "scoped_case": "bb05"})
        gates.assert_ledger_semantics(*case, next(r for r in readback if r["step"] == case[1]))



def child(kind, phase, out):
    import pytest
    out.mkdir(parents=True, exist_ok=False)
    guard = out / "test_replay_semantic_guard.py"
    guard.write_text("from m5a2_replay_mutations import run_guard\n"
                     "from pathlib import Path\n"
                     "def test_specific_semantic_guard():\n"
                     "    run_guard("+repr(kind)+", Path("+repr(str(out))+"))\n", encoding="utf-8")
    with pytest.MonkeyPatch.context() as patch:
        if phase == "mutant":
            dump(out / "injection.json", inject(kind, patch))
        else:
            # The control takes exactly the same hash-blind route.
            import m5a_se2_replay as replay
            original = json.loads((ROOT / "fixtures/m5a_se2/expected.json").read_text(encoding="utf-8"))
            patch.setattr(replay, "code_hashes", lambda: original["code_hashes"])
        return pytest.main(["-q", "-p", "no:cacheprovider", "--basetemp="+str(out / "pytest"), str(guard)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="replay_mutations_r1")
    parser.add_argument("--child", choices=tuple(MUTATIONS))
    parser.add_argument("--phase", choices=("control", "mutant"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.child:
        return child(args.child, args.phase, args.out)
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("name must be one new directory name")
    out = EVIDENCE / args.name
    scratch = EVIDENCE / "tmp" / args.name
    if out.exists() or scratch.exists():
        parser.error("fresh output directories required; interrupted runs must be discarded")
    out.mkdir(parents=True); scratch.mkdir(parents=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
               TEMP=str(EVIDENCE / "tmp"), TMP=str(EVIDENCE / "tmp"))
    rows = []; started = time.perf_counter()
    source_paths = (Path(__file__), ROOT / "tests/test_m5a2_replay.py",
                    ROOT / "tools/m5a_se2_replay.py", ROOT / "src/eab/kernel2d/se2.py")
    source_hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    dump(out / "progress.json", {"complete": False, "rows": rows})
    for kind, (_, _, _, expected) in MUTATIONS.items():
        outcomes = {}
        for phase in ("control", "mutant"):
            command = [sys.executable, "-X", "utf8", str(Path(__file__)), "--child", kind, "--phase", phase,
                       "--out", str(scratch / (kind+"_"+phase))]
            try:
                result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                        encoding="utf-8", errors="replace", timeout=60)
                text = result.stdout+result.stderr
                outcomes[phase] = {"exit_code": result.returncode,
                                   "assertions": re.findall(r"^E\s+AssertionError:.*$", text, re.MULTILINE),
                                   "last_line": text.strip().splitlines()[-1] if text.strip() else ""}
            except subprocess.TimeoutExpired:
                text = "TIMEOUT: semantic assertion not reached; mutation evidence RED\n"
                outcomes[phase] = {"exit_code": "TIMEOUT", "assertions": [], "last_line": text.strip()}
            (out / (kind+"_"+phase+".log")).write_text(text, encoding="utf-8")
        killed = (outcomes["control"]["exit_code"] == 0 and outcomes["mutant"]["exit_code"] == 1
                  and any(expected in line for line in outcomes["mutant"]["assertions"]))
        injection = json.loads((scratch / (kind+"_mutant/injection.json")).read_text(encoding="utf-8"))
        rows.append({"kind": kind, "semantic_kill": killed, "expected_assertion": expected,
                     "refrozen_before_guard": kind in ("swapped_models", "chord_no_contact_shortcut", "classifier_uses_chord"),
                     **injection, **outcomes})
        dump(out / "progress.json", {"complete": False, "rows": rows})
        print(kind, "SEMANTIC_RED" if killed else "NO_TEETH", flush=True)
    unchanged = all(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == sha for rel, sha in source_hashes.items())
    green = unchanged and all(r["semantic_kill"] for r in rows)
    dump(out / "summary.json", {"complete": True, "audit": "GREEN" if green else "RED", "rows": rows,
         "seconds": time.perf_counter()-started, "source_files_modified": False,
         "source_hashes": source_hashes, "source_snapshot_unchanged_during_run": unchanged,
         "oracle_imports": ["fractions.Fraction", "math.isqrt", "random.Random", "gzip", "json", "pathlib.Path",
                            "functools.lru_cache", "types.SimpleNamespace"],
         "oracle_scope": "Replay semantics: directly recomputed kernels, independent test fit/id mapping/classification; not independent geometry verification"})
    dump(out / "progress.json", {"complete": True, "audit": "GREEN" if green else "RED", "mutants": len(rows)})
    return 0 if green else 1


if __name__ == "__main__":
    raise SystemExit(main())
