"""Rerunnable delivery QA; reads tracked paths, writes only review/delivery_qa.json."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
RV = ROOT / "review"
report = (RV / "G6L_report.md").read_text(encoding="utf-8")
findings = json.loads((RV / "G6L_findings.json").read_text(encoding="utf-8"))
before = json.loads((RV / "tracked_sha256_before.json").read_text(encoding="utf-8-sig"))
changed = [p for p, digest in before.items()
           if hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != digest]
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
status = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT).decode("utf-8")
outside = [line for line in status.splitlines()
           if not line[3:].replace("\\", "/").startswith("review/")]
required_fields = {"severity", "file", "line", "file_line", "conclusion", "failure_scenario",
                   "how_to_reproduce", "suggested_fix", "verified_output"}
counts = {severity: sum(f["severity"] == severity for f in findings["findings"])
          for severity in ("critical", "major", "minor")}
missing_fields = {f["id"]: sorted(required_fields - f.keys()) for f in findings["findings"]
                  if required_fields - f.keys()}
link_errors = []
link_count = 0
for rel in ("G6L_report.md", "ARTIFACT_INDEX.md"):
    text = (RV / rel).read_text(encoding="utf-8")
    for uri in re.findall(r"\]\((file:///[^)]+)\)", text):
        link_count += 1
        path = unquote(urlparse(uri).path).lstrip("/")
        if not Path(path).exists():
            link_errors.append({"document": rel, "uri": uri})

checks = {
    "head_expected": head == "0ce65a44c9c26d99411cee68d7300e7b5521bb40",
    "tracked_bytes_unchanged": not changed,
    "write_scope_status_clean": not outside,
    "counts_match": counts == findings["confirmed_counts"] == {"critical": 0, "major": 1, "minor": 0},
    "finding_schema_complete": not missing_fields,
    "fullsuite_green": findings["full_suite"]["passed"] == 11256 and findings["full_suite"]["exit_code"] == 0,
    "regression_unique_26": findings["regression_replay"]["unique_g6e_count"] == 26,
    "report_no_placeholders": "__FULL_" not in report and "__SCOPE_" not in report,
    "report_chinese_present": sum("\u4e00" <= c <= "\u9fff" for c in report) > 1500,
    "report_terminator": report.rstrip().splitlines()[-1] == "G6L_DONE critical=0 major=1 minor=0",
    "primary_links_exist": not link_errors,
}
result = {"checks": checks, "all_passed": all(checks.values()), "tracked_file_count": len(before),
          "changed_tracked_bytes": changed, "outside_review_status": outside, "link_errors": link_errors,
          "primary_link_count": link_count, "missing_fields": missing_fields,
          "note": "Artifact structural QA, not a mathematical correctness proof."}
(RV / "delivery_qa.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
if not result["all_passed"]:
    raise AssertionError(result)
