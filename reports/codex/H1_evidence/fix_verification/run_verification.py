"""Bounded H1-fix verification: real copied-source mutants, no frozen replay."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
TMP = ROOT / "reports/codex/H1_evidence/tmp/fix_verification"
TMP.mkdir(parents=True, exist_ok=True)
ENV = dict(os.environ, TEMP=str(TMP), TMP=str(TMP), PYTHONIOENCODING="utf-8")
M1 = [
    "tests/test_m5c_policy_binding.py::test_new_runtime_import_after_start_invalidates_the_sealed_closure",
    "tests/test_m5c_policy_binding.py::test_source_binding_rejects_parent_traversal_even_with_matching_content",
    "tests/test_m5c_policy_binding.py::test_runtime_source_closure_matches_independent_import_origins_and_kills_omission",
    "tests/test_m4c_fix_replay.py::test_frozen_hash_scope_is_exact_replay_import_closure_with_posix_keys",
]
PLUGIN = TMP / "fix_records.py"
PLUGIN.write_text('''import json, os
from pathlib import Path
rows=[]
def pytest_runtest_logreport(report):
    if report.when == "call":
        rows.append(dict(nodeid=report.nodeid,outcome=report.outcome,longrepr=str(report.longrepr) if report.failed else None))
def pytest_sessionfinish(session, exitstatus):
    Path(os.environ["FIX_RECORD"]).write_text(json.dumps(dict(collected=session.testscollected,exitstatus=int(exitstatus),rows=rows),indent=2),encoding="utf-8")
''', encoding="utf-8", newline="")


def run(name, nodes, root=ROOT, extra=()):
    log, record = OUT / (name + ".log"), OUT / (name + ".json")
    env = dict(ENV, FIX_RECORD=str(record), PYTHONPATH=str(TMP))
    command = [sys.executable, "-X", "utf8", "-m", "pytest", "-v", "-p", "no:cacheprovider",
               "-p", "fix_records", "--basetemp", str(TMP / (name + "_temp")), *extra, *nodes]
    started = time.monotonic()
    with log.open("wb") as stream:
        process = subprocess.run(command, cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                 timeout=180)
    result = json.loads(record.read_text("utf-8"))
    result.update(command=command, cwd=str(root), seconds=time.monotonic()-started,
                  returncode=process.returncode, last_line=log.read_text("utf-8").strip().splitlines()[-1])
    record.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8", newline="")
    return result


def replace(path, old, new):
    text = path.read_text("utf-8")
    assert text.count(old) == 1, (path, old)
    path.write_text(text.replace(old, new), encoding="utf-8", newline="")


control = run("m1_control", M1, extra=("--runslow",))
assert control["returncode"] == 0 and len(control["rows"]) == 7
copy = TMP / "m1_combined_mutant"
assert not copy.exists(), "Use a new scratch run instead of overwriting a prior mutant"
for folder in ("src", "tools", "tests"):
    shutil.copytree(ROOT / folder, copy / folder, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
shutil.copyfile(ROOT / "pyproject.toml", copy / "pyproject.toml")
replace(copy / "tools/m5c_source_binding.py", "    root = Path(root).resolve()\n    if not expected:",
        "    return  # injected early return in retained live guard\n    root = Path(root).resolve()\n    if not expected:")
replace(copy / "tools/m5c_source_binding.py", "for path in sorted(paths)}",
        "for path in sorted(paths) if path.name != 'numeric_domain.py'}")
replace(copy / "tools/m4c_motion_replay.py", '    "src/eab/numeric_domain.py",\n', "")
mutant = run("m1_combined_mutant", M1, root=copy, extra=("--runslow",))
assert mutant["returncode"] == 1 and len(mutant["rows"]) == 7
assert all(row["outcome"] == "failed" for row in mutant["rows"])
for row in mutant["rows"]:
    node = row["nodeid"]
    target = ("DID NOT RAISE" if "new_runtime_import" in node or "parent_traversal" in node
              else "independent import origins require every transitive source" if "import_origins" in node
              else "live source manifest must equal the replay import closure")
    assert target in row["longrepr"], (node, target)
    row["intended_failure"] = target
(OUT / "m1_combined_mutant.json").write_text(json.dumps(mutant, indent=2)+"\n", encoding="utf-8", newline="")

targeted = run("retained_guards_r3_integrity", [
    "tests/test_m5c_policy_binding.py", "tests/test_m4c_fix_replay.py",
    "tests/test_h1_frozen_semantics.py", "tests/test_h1_frozen_data.py", "tests/test_m5c_replay_scope.py",
], extra=("--runslow",))
assert targeted["returncode"] == 0 and len(targeted["rows"]) == 30
policy = json.loads((ROOT / "tests/slow_tests.json").read_text("utf-8"))
promoted = policy["fast_nodes"]
assert len(promoted) == 20
fast = run("m2_fast_promoted", promoted)
assert fast["returncode"] == 0 and fast["collected"] == 20
assert {row["nodeid"] for row in fast["rows"]} == set(promoted)
summary = dict(status="PASS", m1_control=control["last_line"], m1_mutant=mutant["last_line"],
               m1_intended_assertions=7, m2_fast_promoted=fast["last_line"], promoted=promoted,
               targeted=targeted["last_line"], restored_nodes=7, retired_relative_to_pre_H1=5,
               renamed_r3={"old":"test_fixed_real_r3_subset_reexecutes_exact_certificate_labels_and_counts",
                           "new":"test_fixed_real_r3_subset_reexecutes_certificates_and_counts_at_frozen_label_and_interval"},
               no_external_archive_reads=True, no_full_replay=True)
(OUT / "summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8", newline="")
print(json.dumps(summary, indent=2))
