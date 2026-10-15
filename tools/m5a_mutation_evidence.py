"""Seven actual M5a source mutants, isolated under this worktree's tmp.

Every copied baseline must pass one semantic guard before an internal source
mutation makes that same guard fail at its named assertion. No hash test is
selected: source digests are provenance only and cannot kill a mutant.
No source in the real tree is overwritten, and interrupted runs are not resumed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M5a_evidence"
ALG = "src/eab/kernel2d/algebraic.py"
SE2 = "src/eab/kernel2d/se2.py"
CASES = (
    ("isolation_bit", ALG, "        return middle, upper\n", "        return lower, middle\n",
     "isolation bit retains the selected root"),
    ("wrong_real_root", SE2, "        candidates = roots_interval(f)\n",
     "        candidates = roots_interval(f)[-1:]\n", "earliest square-wall real root"),
    ("approximate_equality", ALG, "            return self.compare(other) == 0\n",
     "            return abs(self.time-other.time) <= 1e-12\n", "near roots are algebraically distinct"),
    ("rotation_sign", SE2, "    return (x, -2*u*y, -u*u*x), (y, 2*u*x, -u*u*y)\n",
     "    return (x, 2*u*y, -u*u*x), (y, 2*u*x, -u*u*y)\n", "square-wall complete first feature"),
    ("translation_bypass", SE2, "        candidates = roots_interval(f)\n",
     "        candidates = () if len(f) <= 2 else roots_interval(f)\n",
     "general path must retain translation events"),
    ("endpoint_not_closed", SE2, "        return self.at(point, F(1))\n",
     "        return self.at(point, F(1, 2))\n", "trajectory final endpoint closure"),
    ("lost_degree_five", SE2, "    return f, g, h\n",
     "    return (f[:-1] if len(f) == 6 else f), g, h\n",
     "independent first-root identity rejects lost degree-five term"),
)
TESTS = (
    "tests/test_m5a_algebraic.py", "tests/test_m5a_se2.py", "tests/test_m5a_oracle.py",
    "tests/m5a_independent_oracle.py", "tests/test_m4c_motion.py",
)
GUARD = '''from fractions import Fraction as F
import os
import test_m5a_algebraic as algebra_tests
import test_m5a_se2 as se2_tests
import test_m5a_oracle as oracle_tests

def test_specific_contract_after_actual_source_mutation():
    kind = os.environ["M5A_MUTANT"]
    if kind == "isolation_bit":
        algebra_tests.test_one_isolation_bit_keeps_the_selected_root()
    elif kind == "wrong_real_root":
        se2_tests._closed_form_guard()
    elif kind == "approximate_equality":
        algebra_tests.test_adjacent_algebraic_roots_do_not_become_equal_at_a_float_tolerance()
    elif kind == "rotation_sign":
        se2_tests._closed_form_guard()
    elif kind == "translation_bypass":
        se2_tests.test_translation_semantic_guard()
    elif kind == "endpoint_not_closed":
        se2_tests.test_rotation_is_rigid_and_endpoints_close(F(1))
    elif kind == "lost_degree_five":
        a, b, ma, mb = oracle_tests.CASES[0]
        expected = oracle_tests.first_contact(a, b, ma, mb)
        actual = oracle_tests.se2_first_entrance(a, b, oracle_tests.SE2Motion(*ma), oracle_tests.SE2Motion(*mb))
        assert actual.status == "contact", "degree-five mutant reaches semantic contact path"
        got = oracle_tests.certificate_root(actual.exact_time.certificate)
        assert oracle_tests.compare(got, expected["root"]) == 0, "independent first-root identity rejects lost degree-five term"
    else:
        raise AssertionError("unknown mutation kind")
'''


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="mutation_evidence")
    args = parser.parse_args()
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("name must be one new directory name")
    out = EVIDENCE / args.name
    scratch = EVIDENCE / "tmp" / (args.name+"_source_copies")
    if out.exists() or scratch.exists():
        parser.error("both evidence and scratch directories must be new; interrupted runs are not resumed")
    out.mkdir(parents=True)
    scratch.mkdir(parents=True)
    frozen = scratch / "unmodified_snapshot"
    frozen.mkdir()
    shutil.copytree(ROOT / "src", frozen / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (frozen / "tests").mkdir()
    for rel in TESTS + ("pyproject.toml",):
        shutil.copy2(ROOT / rel, frozen / rel)
    guard = frozen / "tests/test_m5a_mutant_guard.py"
    guard.write_text(GUARD, encoding="utf-8")
    originals = {p.relative_to(frozen).as_posix(): digest(p) for p in frozen.rglob("*") if p.is_file()}
    actual_sources = {rel: digest(ROOT / rel) for rel in originals if rel != "tests/test_m5a_mutant_guard.py"}
    rows = []
    started = time.perf_counter()
    dump(out / "progress.json", {"complete": False, "rows": rows})
    for kind, relative, old, new, expected in CASES:
        copied = scratch / kind
        shutil.copytree(frozen, copied)
        temporary = copied / "local_temp"
        temporary.mkdir()
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
                   TEMP=str(temporary), TMP=str(temporary), M5A_MUTANT=kind)
        env["PYTHONPATH"] = str(copied / "src")
        outcomes = {}
        source_file = copied / relative
        source_before = digest(source_file)
        source_after = None
        for label in ("control", "mutant"):
            if label == "mutant":
                with source_file.open("r", encoding="utf-8", newline="") as stream:
                    source = stream.read()
                newline = "\r\n" if "\r\n" in source else "\n"
                find, replace = old.replace("\n", newline), new.replace("\n", newline)
                if source.count(find) != 1:
                    dump(out / "summary.json", {"complete": False, "audit": "RED", "rows": rows,
                         "reason": "source mutation anchor must occur once", "kind": kind})
                    return 1
                with source_file.open("w", encoding="utf-8", newline="") as stream:
                    stream.write(source.replace(find, replace))
                source_after = digest(source_file)
            command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                       "--basetemp="+str(temporary / (label+"_pytest")), "tests/test_m5a_mutant_guard.py"]
            try:
                result = subprocess.run(command, cwd=copied, env=env, capture_output=True,
                                        text=True, encoding="utf-8", errors="replace", timeout=180)
            except subprocess.TimeoutExpired:
                dump(out / "summary.json", {"complete": False, "audit": "RED", "rows": rows,
                     "reason": "mutation child timeout", "kind": kind, "phase": label})
                return 1
            output = result.stdout+result.stderr
            log = out / (kind+"_"+label+".log")
            log.write_text(output, encoding="utf-8")
            assertion_lines = re.findall(r"^E\s+AssertionError:.*$", output, re.MULTILINE)
            outcomes[label] = {"exit_code": result.returncode,
                "last_line": output.strip().splitlines()[-1] if output.strip() else "",
                "assertion_lines": assertion_lines, "log": log.name}
        killed = (outcomes["control"]["exit_code"] == 0 and outcomes["mutant"]["exit_code"] == 1
                  and any(expected in line for line in outcomes["mutant"]["assertion_lines"]))
        rows.append({"kind": kind, "source": relative, "expected_assertion": expected,
                     "source_before": source_before, "source_after": source_after,
                     "semantic_kill": killed, **outcomes})
        dump(out / "progress.json", {"complete": False, "rows": rows})
        print(kind, killed, outcomes["mutant"]["last_line"], flush=True)
    unchanged = all(digest(ROOT / rel) == sha for rel, sha in actual_sources.items())
    green = unchanged and all(row["semantic_kill"] for row in rows)
    summary = {"complete": True, "audit": "GREEN" if green else "RED", "rows": rows,
               "all_original_sources_unchanged": unchanged, "source_snapshot": actual_sources,
               "hash_guard_selected": False, "hash_role": "provenance only, no hash can kill any mutant",
               "seconds": time.perf_counter()-started, "tool_sha256": digest(Path(__file__))}
    dump(out / "summary.json", summary)
    return 0 if green else 1


if __name__ == "__main__":
    raise SystemExit(main())
