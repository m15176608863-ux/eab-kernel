"""Read-only baseline/scope/test/fixture audit; writes only local evidence."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

baseline = json.loads((HERE / "baseline_manifest.json").read_text(encoding="utf-8"))
changed = []
missing = []
fixture_count = 0
test_count = 0
for row in baseline["files"]:
    path = ROOT / row["path"]
    fixture_count += row["path"].startswith("fixtures/")
    test_count += row["path"].startswith("tests/")
    if not path.is_file():
        missing.append(row["path"])
    elif digest(path) != row["sha256"]:
        changed.append(row["path"])
allowed = {"src/eab/dual.py", "src/eab/kernel2d/covers.py", "src/eab/kernel3d/entrance3.py",
           "src/eab/limit.py", "src/eab/limit_multi.py", "tools/check_exact_construction.py",
           "README.md", "docs/canon_map.md", "docs/exact_3d_design.md", "docs/exact_predicates_plan.md"}
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
# Preserve the pre-existing CRLF source; CR is an end-of-line marker, not
# newly introduced trailing whitespace. This -c is command-local, no config write.
diff_check = subprocess.run(["git", "-c", "core.whitespace=cr-at-eol", "diff", "--check"],
                            cwd=ROOT, capture_output=True, text=True)
input_findings = json.loads((ROOT / "reports/codex/inputs/G6J_findings.json").read_text(encoding="utf-8-sig"))
inputs = []
for finding in input_findings["findings"]:
    for name, expected in finding.get("repro_sha256", {}).items():
        local = ROOT / "reports/codex/inputs/G6J_repro" / Path(name).name
        inputs.append({"path": str(local.relative_to(ROOT)), "matches_reviewer_sha256": digest(local) == expected})
test_rewrites = [name for name in changed if name.startswith("tests/")]
fixture_changes = [name for name in changed+missing if name.startswith("fixtures/")]
report = {"head": head, "branch": branch, "head_unchanged": head == baseline["head"],
          "modified_tracked": changed, "missing_tracked": missing,
          "scope_violations": sorted(set(changed)-allowed),
          "baseline_test_files_checked": test_count, "existing_test_rewrites": test_rewrites,
          "baseline_fixture_files_checked": fixture_count, "fixture_changes": fixture_changes,
          "reviewer_repro_integrity": inputs, "git_diff_check_exit_code": diff_check.returncode,
          "git_diff_check_output": diff_check.stdout+diff_check.stderr}
report["passed"] = (report["head_unchanged"] and branch == "codex-work" and not missing
                    and not report["scope_violations"] and not test_rewrites and not fixture_changes
                    and all(row["matches_reviewer_sha256"] for row in inputs) and diff_check.returncode == 0)
(HERE / "delivery_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(not report["passed"])
