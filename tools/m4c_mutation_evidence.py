"""Run actual internal M4c mutants in isolated processes and preserve RED logs.

No source file is overwritten. Each guard first passes in an unmodified child;
a separate child injects the defect inside the tested path and must fail at
the named assertion/domain check, not merely somewhere in the test suite.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M4c_evidence"
CASES = {
    "wrong_quadratic_branch": ("AssertionError", "earliest quadratic branch"),
    "open_endpoint": ("AssertionError", "closed endpoint event lost"),
    "lost_tie": ("AssertionError", "complete simultaneous cover set"),
    "translation_bypass": ("AssertionError", "general event path translation consistency"),
    "ledger_fold_into_match": ("AssertionError", "motion category preserves earlier other feature"),
    "step_pairing_shift": ("ValueError", "motion geometry pairing mismatch"),
}


def child(kind, guard, control):
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests"), str(ROOT / "tools")]
    import pytest
    from eab.kernel2d import motion
    import m4c_motion_replay as replay
    if not control:
        if kind == "wrong_quadratic_branch":
            original = motion._roots
            def mutant(poly):
                roots = original(poly)
                return roots[-1:] if poly[2] and len(roots) == 2 else roots
            motion._roots = mutant
        elif kind == "open_endpoint":
            def mutant(t, orient, between):
                return t.sign_polynomial(*orient) == 0 and t.sign_polynomial(*between) < 0
            motion._contains = mutant
        elif kind == "lost_tie":
            original = motion._cone
            def mutant(t, paths, vertex, other_edge):
                return vertex != 1 and original(t, paths, vertex, other_edge)
            motion._cone = mutant
        elif kind == "translation_bypass":
            original = motion._roots
            def mutant(poly):
                return () if poly[2] == 0 else original(poly)
            motion._roots = mutant
        elif kind == "ledger_fold_into_match":
            replay.classify_reference = lambda *args: "FIRST_COVER_MATCH"
        elif kind == "step_pairing_shift":
            original = replay._pair_frames
            def mutant(frames, terminal):
                for start, end in original(frames, terminal):
                    yield start, {**end, "geometry": start["geometry"]}
            replay._pair_frames = mutant
    os.environ["M4C_MUTANT"] = kind
    return pytest.main([str(guard), "-q", "-p", "no:cacheprovider"])


GUARD = '''import os
import test_m4c_motion as motion_tests
import test_m4c_replay as replay_tests

def test_specific_contract_after_internal_injection():
    kind = os.environ["M4C_MUTANT"]
    guards = {
        "wrong_quadratic_branch": motion_tests._assert_two_root_guard,
        "open_endpoint": motion_tests._assert_endpoint_guard,
        "lost_tie": motion_tests._assert_tie_guard,
        "translation_bypass": motion_tests._assert_translation_guard,
        "ledger_fold_into_match": replay_tests.test_guard_category_not_folded_into_match,
        "step_pairing_shift": replay_tests.test_guard_step_pairing,
    }
    guards[kind]()
'''


def hashes():
    paths = [ROOT / "src/eab/kernel2d/motion.py", ROOT / "tools/m4c_motion_replay.py",
             ROOT / "tests/test_m4c_motion.py", ROOT / "tests/test_m4c_replay.py", Path(__file__)]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="mutations")
    parser.add_argument("--child", choices=CASES)
    parser.add_argument("--guard", type=Path)
    parser.add_argument("--control", action="store_true")
    args = parser.parse_args()
    if args.child:
        return child(args.child, args.guard, args.control)
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("name must be a single new directory")
    out = EVIDENCE / args.name
    if out.exists():
        parser.error("evidence directory must be new")
    out.mkdir(parents=True)
    temp = EVIDENCE / "tmp" / (args.name + "_guards")
    temp.mkdir(parents=True)
    guard = temp / "test_m4c_external_guards.py"
    guard.write_text(GUARD, encoding="utf-8")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", TEMP=str(temp), TMP=str(temp))
    initial = hashes()
    rows = []
    started = time.perf_counter()
    for kind, (exception, assertion) in CASES.items():
        outcomes = {}
        for control in (True, False):
            command = [sys.executable, "-X", "utf8", str(Path(__file__)), "--child", kind, "--guard", str(guard)]
            if control:
                command.append("--control")
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output = result.stdout.decode("utf-8", errors="replace")
            label = "control" if control else "mutant"
            log = out / f"{kind}_{label}.txt"
            log.write_text(output, encoding="utf-8")
            exact_lines = re.findall(r"^E\s+"+exception+r":.*$", output, re.MULTILINE)
            outcomes[label] = dict(exit_code=result.returncode, last_line=output.splitlines()[-1] if output else "",
                                   expected_exception_lines=exact_lines, log=log.name)
        killed = outcomes["control"]["exit_code"] == 0 and outcomes["mutant"]["exit_code"] == 1 and any(
            assertion in line for line in outcomes["mutant"]["expected_exception_lines"])
        rows.append(dict(mutant_name=kind, expected_exception=exception, expected_assertion=assertion,
                         killed_at_expected_check=killed, **outcomes))
        (out / "progress.json").write_text(json.dumps(dict(complete=False, rows=rows), indent=2)+"\n", encoding="utf-8")
        print(kind, killed, outcomes["mutant"]["last_line"], flush=True)
    unchanged = hashes() == initial
    passed = unchanged and all(r["killed_at_expected_check"] for r in rows)
    (out / "summary.json").write_text(json.dumps(dict(complete=True, audit="GREEN" if passed else "RED",
        source_hashes=initial, source_unchanged=unchanged, seconds=time.perf_counter()-started, rows=rows), indent=2)+"\n", encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
