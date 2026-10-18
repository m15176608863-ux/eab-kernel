"""Focused H1-fix purity validation; no full suite and no policy writes."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
TMP = ROOT / "reports/codex/H1_evidence/tmp/fix_purity"


def run(name, args, *, cwd=ROOT, expected=0):
    start = time.perf_counter()
    completed = subprocess.run(args, cwd=cwd, env=os.environ.copy(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (OUT / (name + ".log")).write_bytes(completed.stdout)
    text = completed.stdout.decode("utf-8", errors="replace")
    assert completed.returncode == expected, (name, completed.returncode, text[-5000:])
    return {"command": args, "exit_code": completed.returncode, "seconds": time.perf_counter() - start,
            "last_line": text.rstrip().splitlines()[-1], "log": name + ".log"}


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    os.environ.update(TEMP=str(TMP), TMP=str(TMP), PYTHONIOENCODING="utf-8")
    base = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    pristine = run("pristine", base + ["--basetemp", str(TMP / "pristine"), "tests/test_kernel_purity.py"])
    run("collection", base + ["--basetemp", str(TMP / "collection"), "--collect-only", "tests/test_kernel_purity.py"])
    nodes = [line for line in (OUT / "collection.log").read_text("utf-8").splitlines() if line.startswith("tests/") and "::" in line]
    assert len(nodes) == 35
    (OUT / "nodes.json").write_text(json.dumps({"old_count": 6, "new_count": len(nodes), "added": len(nodes) - 6, "nodes": nodes}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    copy = TMP / "parent_bfs_mutant"
    copy.mkdir(exist_ok=False)
    shutil.copytree(ROOT / "src", copy / "src", ignore=shutil.ignore_patterns("__pycache__"))
    (copy / "tools").mkdir()
    (copy / "tests").mkdir()
    shutil.copy2(ROOT / "tests/test_kernel_purity.py", copy / "tests/test_kernel_purity.py")
    tool = (ROOT / "tools/h1_kernel_purity.py").read_text("utf-8")
    old = 'pending = deque([(module, (module,))] +\n                            [(".".join(parts[:i]), (module, ".".join(parts[:i]))) for i in range(1, len(parts))])'
    assert tool.count(old) == 1
    (copy / "tools/h1_kernel_purity.py").write_text(tool.replace(old, 'pending = deque([(module, (module,))])'), encoding="utf-8")
    mutant = run("parent_bfs_mutant", base + ["--basetemp", str(TMP / "parent_bfs_pytest"),
        "tests/test_kernel_purity.py::test_parent_package_imports_are_checked_for_every_kernel_module"], cwd=copy, expected=1)
    mutant_text = (OUT / "parent_bfs_mutant.log").read_text("utf-8")
    assert "assert reached == expected" in mutant_text and "eab/predicates.py" in mutant_text

    sys.path.insert(0, str(ROOT / "tools"))
    import check_exact_construction as scanner
    checked = ["tests/test_kernel_purity.py", "src/eab/contact_record.py", "src/eab/adapters/tf.py",
               "src/eab/adapters/bdda2d.py", "src/eab/adapters/bdda3d.py", "src/eab/kernel2d/affine_motion.py",
               "src/eab/kernel2d/geom.py", "src/eab/kernel2d/model_robustness.py"]
    issues = [issue for name in checked for issue in scanner.scan_text((ROOT / name).read_text("utf-8"), name, repository_root=ROOT)]
    summary = {"pristine": pristine, "parent_bfs_removal_mutant": mutant,
               "parent_mutant_failing_assertion": "assert reached == expected", "parent_kernel_module_count": 40,
               "lexical_module_count": 43, "new_nodes": 29, "current_nodes": 35,
               "static_paths": checked, "static_issues": issues,
               "scope": "Focused checks only. Full static and full four shards are performed by root."}
    (OUT / "validation.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
