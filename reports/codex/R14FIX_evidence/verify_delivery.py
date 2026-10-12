"""Read-only repository integrity checks; write this work order's final index.

Run after the audited full suite and completed report. Never modifies source,
tests, policy, fixtures, git metadata, siblings, or previous raw evidence.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPORT = ROOT / "reports/codex/R14FIX_report.md"
FULL = HERE / "full_suite_verified"


def read_json(path):
    data = path.read_bytes()
    return json.loads(data.decode("utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8").strip()


def links(path):
    broken = []
    for ref in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
        if ref.startswith(("http:", "https:", "mailto:", "#")):
            continue
        ref = unquote(ref.split("#")[0])
        target = Path(ref[8:]) if ref.startswith("file:///") else path.parent / ref
        if not target.exists():
            broken.append({"file": path.relative_to(ROOT).as_posix(), "target": ref})
    return broken


def main():
    baseline = read_json(HERE / "initial_manifest.json")
    full = read_json(FULL / "summary.json")
    static = read_json(HERE / "static_final_status.json")
    missing = [name for name in baseline["tracked_sha256"] if not (ROOT/name).is_file()]
    changed = [name for name, old in baseline["tracked_sha256"].items()
               if (ROOT/name).is_file() and sha(ROOT/name) != old]
    fixture_names = [n for n in baseline["tracked_sha256"] if n.startswith("fixtures/")]
    fixture_changes = [n for n in fixture_names if n in missing or n in changed]
    added_fixtures = git("ls-files", "--others", "--exclude-standard", "--", "fixtures").splitlines()
    changed_old_tests = [n for n in changed if n.startswith("tests/")]
    allowed_old_tests = {"tests/test_limit.py", "tests/test_r6fix_dual_lp.py",
                         "tests/test_r7fix_dual.py", "tests/test_r13fix_mechanics_differential.py",
                         "tests/test_r13fixb_readers_oracles.py"}
    nodes = read_json(FULL / "collection_nodes.json")
    old_nodes = read_json(HERE / "baseline_nodes.json")
    new_nodes = sorted(set(nodes) - set(old_nodes))
    snapshots = read_json(FULL / "before_snapshot.json")
    current_drift = [n for n, h in snapshots.items() if not (ROOT/n).is_file() or sha(ROOT/n) != h]
    static_drift = [n for n,h in static["sha256"].items() if not (ROOT/n).is_file() or sha(ROOT/n) != h]
    docs = [REPORT, ROOT/"docs/r14fix_design_sync.md", *HERE.glob("*.md")]
    bad_encoding = [{"file": p.relative_to(ROOT).as_posix(), "line": i}
                    for p in docs for i,line in enumerate(p.read_text(encoding="utf-8").splitlines(),1)
                    if "???" in line or "\ufffd" in line]
    broken = links(REPORT) + links(ROOT/"docs/r14fix_design_sync.md")
    # These outputs are written below, then checked again without exemption.
    planned = {HERE/name for name in ("ARTIFACTS.md", "delivery_result.json", "final_manifest.json")}
    broken = [row for row in broken if ((ROOT/row["file"]).parent/row["target"]).resolve() not in planned]
    json_errors = []
    evidence_paths = sorted(p for p in HERE.rglob("*") if p.is_file() and
                            not any(x in {"tmp", "baseline", "__pycache__"} for x in p.relative_to(HERE).parts))
    for p in evidence_paths:
        if p.suffix == ".json":
            try:
                read_json(p)
            except Exception as exc:
                json_errors.append({"file": p.relative_to(ROOT).as_posix(), "error": repr(exc)})
    diff = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True)
    head, branch = git("rev-parse", "HEAD"), git("branch", "--show-current")
    checks = {
        "full_suite_pass": full["status"] == "PASS" and all(full["checks"].values()),
        "all_original_nodes_preserved": set(old_nodes) <= set(nodes),
        "new_nodes_only_r14_files": all(n.startswith("tests/test_r14_") for n in new_nodes),
        "static_gate_pass_and_frozen": static["exitcode"] == 0 and static["source_policy_bytes_unchanged"],
        "full_source_tools_tests_docs_policy_still_frozen": not current_drift,
        "static_source_policy_still_frozen": not static_drift,
        "head_and_branch_unchanged": head == baseline["head"] and branch == baseline["branch"],
        "no_initial_tracked_file_deleted": not missing,
        "fixtures_bytes_unchanged_and_no_added_fixtures": not fixture_changes and not added_fixtures,
        "old_test_edits_match_report_ledger": set(changed_old_tests) == allowed_old_tests,
        "diff_check_clean": diff.returncode == 0,
        "report_and_design_links_resolve": not broken,
        "report_and_summaries_utf8_no_corruption": not bad_encoding,
        "evidence_json_parses": not json_errors,
        "report_has_eleven_items": len(re.findall(r"^### \d\d —", REPORT.read_text(encoding="utf-8"), re.M)) == 11,
        "report_last_line_done": REPORT.read_text(encoding="utf-8").rstrip().endswith("\nR14FIX_DONE"),
    }
    result = {
        "work_order": "WO-R14FIX", "status": "PASS" if all(checks.values()) else "FAIL",
        "head": head, "branch": branch, "checks": checks,
        "full_suite": {k: full[k] for k in ("tests_collected", "tests_executed", "wall_seconds", "collection_seconds")},
        "baseline_tests": len(old_nodes), "new_tests": len(new_nodes),
        "fixture_files_verified": len(fixture_names), "fixture_changes": fixture_changes,
        "added_fixtures": added_fixtures, "missing_initial_files": missing,
        "changed_tracked_files": changed, "changed_old_tests": changed_old_tests,
        "current_frozen_drift": current_drift, "static_frozen_drift": static_drift,
        "broken_links": broken, "bad_encoding": bad_encoding, "json_errors": json_errors,
        "diff_check_output": diff.stdout.decode("utf-8") + diff.stderr.decode("utf-8"),
        "boundary": "local uncommitted verification only; not fresh-worktree or independent G6 certification",
    }
    (HERE/"delivery_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    source_paths = [ROOT/n for n in changed]
    source_paths += [p for folder in ("src", "tests", "tools", "docs") for p in (ROOT/folder).rglob("*")
                     if p.is_file() and p.relative_to(ROOT).as_posix() not in baseline["tracked_sha256"]
                     and p.suffix in {".py", ".md", ".json"}]
    paths = sorted(set(source_paths + evidence_paths + [REPORT, HERE/"delivery_result.json"]))
    paths = [p for p in paths if p.name not in {"ARTIFACTS.md", "final_manifest.json"}]
    manifest = {p.relative_to(ROOT).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in paths}
    (HERE/"final_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    lines = ["# R14FIX 交付清单", "", "仅本工作树未提交修改。原始红/绿/变异日志保留；tmp 是测试临时产物，不列作正式证据。", "",
             "[主报告]("+REPORT.as_uri()+") · [机器验收结果]("+(HERE/"delivery_result.json").as_uri()+") · [SHA256 清单]("+(HERE/"final_manifest.json").as_uri()+")", "",
             "## 文件", ""]
    lines += [f"- [{p.relative_to(ROOT).as_posix()}]({p.as_uri()})" for p in paths]
    (HERE/"ARTIFACTS.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    assert not (links(HERE/"ARTIFACTS.md") + links(REPORT) + links(ROOT/"docs/r14fix_design_sync.md"))
    print(json.dumps({k:v for k,v in result.items() if k not in {"changed_tracked_files"}}, indent=2, ensure_ascii=False))
    print("R14FIX_DELIVERY_"+result["status"])
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
