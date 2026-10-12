"""Read-only original test/fixture/input and Git state audit; retain local evidence."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


baseline = json.loads((HERE / "baseline_manifest.json").read_text(encoding="utf-8"))
inputs = json.loads((HERE / "input_manifest.json").read_text(encoding="utf-8"))
changed, missing = [], []
for name, original_hash in baseline["files"].items():
    path = ROOT / name
    if not path.is_file():
        missing.append(name)
    elif digest(path) != original_hash:
        changed.append(name)
allowed = {"src/eab/kernel2d/geom.py", "src/eab/predicates.py",
           "tools/check_exact_construction.py", "README.md", "docs/canon_map.md",
           "docs/exact_3d_design.md", "docs/exact_predicates_plan.md"}
input_drift = [name for name, sha in inputs.items()
               if not (ROOT / name).is_file() or digest(ROOT / name) != sha]
findings = json.loads((ROOT / "reports/codex/inputs/G6K_findings.json").read_text(encoding="utf-8-sig"))
reviewer_integrity = []
for finding in findings["findings"]:
    path = ROOT / "reports/codex/inputs/G6K_repro" / Path(finding["repro_script"]).name
    reviewer_integrity.append({"finding": finding["id"], "path": path.relative_to(ROOT).as_posix(),
                               "matches_reviewer_sha256": digest(path) == finding["repro_sha256"]})
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
diff_check = subprocess.run(["git", "-c", "core.whitespace=cr-at-eol", "diff", "--check"],
                            cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
report = {"head": head, "branch": branch, "head_unchanged": head == baseline["head"],
          "baseline_tracked_count": len(baseline["files"]),
          "modified_tracked": changed, "missing_tracked": missing,
          "scope_violations": sorted(set(changed)-allowed),
          "baseline_test_files_checked": sum(n.startswith("tests/") for n in baseline["files"]),
          "existing_test_rewrites": [n for n in changed if n.startswith("tests/")],
          "baseline_fixture_files_checked": sum(n.startswith("fixtures/") for n in baseline["files"]),
          "fixture_changes": [n for n in changed+missing if n.startswith("fixtures/")],
          "review_inputs_checked": len(inputs), "input_drift": input_drift,
          "reviewer_repro_integrity": reviewer_integrity,
          "git_diff_check_exit_code": diff_check.returncode,
          "git_diff_check_output": diff_check.stdout+diff_check.stderr}
report["passed"] = (report["head_unchanged"] and branch == "codex-work" and not missing
                    and not report["scope_violations"] and not report["existing_test_rewrites"]
                    and not report["fixture_changes"] and not input_drift and diff_check.returncode == 0
                    and all(row["matches_reviewer_sha256"] for row in reviewer_integrity))
(HERE / "delivery_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(not report["passed"])
