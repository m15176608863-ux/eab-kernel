"""Kill source-internal certificate-checker defects with named semantic gates.

Each fresh child loads an isolated source copy under the real checker module
name before pytest imports its tests. No result is edited by this runner and no
production/checker source is rewritten. The tests supply invalid certificates;
the mutants remove real verifier safeguards, so accepting those inputs must
produce a semantic pytest failure, never an import/hash failure.
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
SOURCE = ROOT / "tools/eab2_c3l4_diff.py"
TEST = "tests/test_eab2_c3l4_harness.py"
FALSE_RESULT = TEST + "::test_c3l4_each_threshold_side_rejects_false_labels_and_slopes"
FALSE_PROOF = TEST + "::test_c3l4_each_threshold_side_rechecks_full_critical_proof"
POSITIVE = TEST + "::test_c3l4_original_geometry_seeds_and_independent_certificates[g1_slender]"
HISTORICAL = TEST + "::test_c3l4_historical_alternate_basis_is_not_a_branch_complete_derivative_proof"
CALLER = TEST + "::test_c3l4_declared_threshold_labels_preserve_caller_contract"

# name, exact source edits, target pytest nodes, required semantic failure text
MUTATIONS = (
    ("skip_python_sensitivity_certificate", (
        ('    verify_sensitivity(case["model"], case["contacts"], expected_base, query, expected_channel(query), mu_max_binary64=case["bases"][kind].get("mu_max_bits"))',
         '    # Mutant: trust the expected-side sensitivity certificate.'),),
     (FALSE_RESULT + "[component_slope-python]",), "DID NOT RAISE"),
    ("skip_cpp_sensitivity_certificate", (
        ('    problem, seed = verify_sensitivity(case["model"], case["contacts"], base, query, channel, mu_max_binary64=case["bases"][kind].get("mu_max_bits"))',
         '    problem, seed = None, None  # Mutant: trust the actual-side certificate.'),),
     (FALSE_RESULT + "[component_slope-cpp]",), "DID NOT RAISE"),
    ("set_dedup_hides_duplicate_crossing", (
        ('require(len(result["tied_labels"]) == len(label_set(result["tied_labels"])) and\n'
         '            label_set(result["tied_labels"]) == label_set(expected_labels),',
         'require(label_set(result["tied_labels"]) == label_set(expected_labels),'),),
     (FALSE_RESULT + "[duplicate-cpp]",), "DID NOT RAISE"),
    ("omit_crossing_label_exactness", (
        ('label_set(result["tied_labels"]) == label_set(expected_labels),',
         'True,  # Mutant: do not require exactly all crossing labels.'),),
     (FALSE_RESULT + "[extra-cpp]", FALSE_RESULT + "[missing-cpp]"), "DID NOT RAISE"),
    ("omit_component_slope_equations", (
        ('    require(result["implicit_components"] == components, "implicit components/phi derivatives")',
         '    # Mutant: omit the full component/phi/slope equality.'),),
     (FALSE_RESULT + "[component_slope-cpp]",), "DID NOT RAISE"),
    ("skip_python_critical_certificate", (
        ('        verify_critical(case["model"], case["contacts"], expected_base)',
         '        # Mutant: trust the expected-side LP/polynomial/Sturm proof.'),),
     (FALSE_PROOF + "[polynomial-python]",), "DID NOT RAISE"),
    ("skip_cpp_critical_certificate", (
        ('        verify_critical(case["model"], case["contacts"], base)',
         '        # Mutant: trust the actual-side LP/polynomial/Sturm proof.'),),
     (FALSE_PROOF + "[sturm-cpp]",), "DID NOT RAISE"),
    ("ignore_non_threshold_tied_labels", (
        ('    if basis_dependent:',
         '    if True:  # Mutant: waive ties for every result family.'),),
     (TEST + "::test_c3l4_non_threshold_tied_labels_remain_strict",), "AssertionError"),
)

CHILD = '''import sys, types
from pathlib import Path
source, original, *arguments = sys.argv[1:]
module = types.ModuleType("eab2_c3l4_diff")
module.__file__ = original
sys.modules[module.__name__] = module
exec(compile(Path(source).read_text(encoding="utf-8"), source, "exec"), module.__dict__)
import pytest
raise SystemExit(pytest.main(arguments))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="A new directory below eab2/build/tmp")
    args = parser.parse_args()
    out = args.output.resolve()
    allowed = (ROOT / "eab2/build/tmp").resolve()
    if out == allowed or not out.is_relative_to(allowed) or out.exists():
        parser.error("--output must be a NEW descendant of eab2/build/tmp")
    out.mkdir(parents=True)
    watched = [SOURCE, Path(__file__), ROOT / TEST, ROOT / "tools/eab2_branch_verify.py",
               ROOT / "tools/eab2_c3l1_diff.py", ROOT / "tools/eab2_c3l3_diff.py",
               ROOT / "src/eab/kernel2d/sensitivity.py", ROOT / "src/eab/kernel2d/critical.py",
               ROOT / "tests/data/eab2_c3l4_threshold_basis_witness.json"]
    hashes = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in watched}
    raw = SOURCE.read_text(encoding="utf-8")
    driver = out / "isolated_checker_driver.py"
    driver.write_text(CHILD, encoding="utf-8", newline="\n")
    baseline_nodes = tuple(dict.fromkeys((POSITIVE, HISTORICAL, CALLER, *(node for _, _, nodes, _ in MUTATIONS for node in nodes))))
    plan = (("baseline", (), baseline_nodes, None), *MUTATIONS,
            ("restored_baseline", (), baseline_nodes, None))
    records = []
    started = time.perf_counter()
    for name, replacements, nodes, failure in plan:
        folder = out / name
        folder.mkdir()
        temp = folder / "tmp"
        temp.mkdir()
        mutated = raw
        for before, after in replacements:
            if mutated.count(before) != 1:
                raise AssertionError(name + ": source replacement must have exactly one site")
            mutated = mutated.replace(before, after)
        candidate = folder / "checker.py"
        candidate.write_text(mutated, encoding="utf-8", newline="\n")
        # A syntax error is an environment/strategy failure, never a killed mutant.
        compile(mutated, str(candidate), "exec")
        command = [sys.executable, str(driver), str(candidate), str(SOURCE), "-q",
                   "-p", "no:cacheprovider", "--basetemp", str(temp / "pytest"), *nodes]
        environment = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1",
                           TEMP=str(temp), TMP=str(temp))
        run = subprocess.run(command, cwd=ROOT, env=environment, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             timeout=180, check=False)
        log = folder / "pytest.log"
        log.write_bytes(run.stdout)
        output = run.stdout.decode("utf-8", errors="replace")
        lines = output.rstrip().splitlines()
        last = lines[-1] if lines else ""
        failed = re.search(r"\b(\d+) failed\b", last)
        if failure is None:
            good = run.returncode == 0 and re.search(rf"\b{len(nodes)} passed\b", last) is not None
        else:
            good = (run.returncode == 1 and failed is not None and int(failed.group(1)) == len(nodes)
                    and failure in output and "ERROR collecting" not in output
                    and "SyntaxError" not in output and "ImportError" not in output)
            if failure == "AssertionError":
                good = good and 'assert delta and all(row["path"].startswith("result.tied_labels")' in output
        unchanged = all(hashlib.sha256((ROOT / key).read_bytes()).hexdigest() == value
                        for key, value in hashes.items())
        good = good and unchanged
        row = dict(name=name, source=SOURCE.relative_to(ROOT).as_posix(),
                   source_sha256=hashes[SOURCE.relative_to(ROOT).as_posix()],
                   mutant_sha256=hashlib.sha256(mutated.encode("utf-8")).hexdigest(),
                   replacements=[dict(before=before, after=after) for before, after in replacements],
                   gates=list(nodes), expected_semantic_failure=failure,
                   command=command, exit_code=run.returncode, last_line=last,
                   source_pre_post_equal=unchanged, semantic_outcome_verified=good,
                   log=log.relative_to(out).as_posix())
        records.append(row)
        (out / "progress.json").write_text(json.dumps(dict(complete=False, cases=records),
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        with (out / "run.log").open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(name + ": " + last + "\n")
        print(name + ": " + last, flush=True)
        if not good:
            raise AssertionError(name + ": expected named semantic red/green was not observed; see " + str(log))
    mutants = [row for row in records if row["replacements"]]
    if len({row["mutant_sha256"] for row in mutants}) != len(MUTATIONS):
        raise AssertionError("source-internal mutants must be distinct")
    last = f"C3L4_CERTIFICATE_MUTATIONS_OK baseline=2 rejected={len(mutants)} semantic_failures={sum(len(row['gates']) for row in mutants)}"
    result = dict(format="eab2.c3l4.certificate-mutations.v1", complete=True,
                  source_sha256=hashes, source_pre_post_equal=True,
                  independent_checker_not_production_solver=True,
                  cases=records, seconds=time.perf_counter() - started, last_line=last)
    (out / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "progress.json").write_text(json.dumps(dict(complete=True, cases=len(records))) + "\n", encoding="utf-8")
    with (out / "run.log").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(last + "\n")
    print(last, flush=True)


if __name__ == "__main__":
    main()
