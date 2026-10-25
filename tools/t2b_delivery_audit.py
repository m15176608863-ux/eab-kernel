"""Read-only source audit and explicit T2b delivery manifests.

Only this work order's report directory and approved external evidence root
are written. No Git writes, source restoration, deletion or process control.
Run after all evidence-producing processes finish.
"""
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path("D:/eab-evidence/reports/codex/T2b_evidence")
REPORTS = ROOT / "reports/codex/T2b_evidence"
OLD_EDIT_ALLOWLIST = {
    "tests/test_kernel_purity.py", "tools/exact_construction_policy.json",
    "tools/policy_history_view.py", "tests/test_t2a_static_admissions.py",
    "tests/test_t2a_policy_history.py", "reports/EVIDENCE_ARCHIVE.md",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n",
                    encoding="utf-8", newline="\n")


def allowed_new(name):
    return (name == "src/eab/kernel2d/se2_cage.py"
            or name.startswith(("tools/t2b_", "tests/t2b_", "tests/test_t2b_",
                                "tests/data/t2b_", "reports/codex/T2b_")))


def run():
    baseline = json.loads((EVIDENCE / "baseline_anchor/manifest.json").read_text("utf-8"))
    previous = {row["path"]: row for row in baseline["files"]}
    names = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT
    ).decode("utf-8").split("\0")
    names = sorted({name for name in names if name and (ROOT/name).is_file()})
    changed = [name for name in names if name not in previous or sha(ROOT/name) != previous[name]["sha256"]]
    missing = sorted(set(previous)-set(names))
    assert not missing, ("no baseline files may disappear", missing)
    assert all(name in OLD_EDIT_ALLOWLIST if name in previous else allowed_new(name) for name in changed), changed
    protected = [name for name in previous if name.startswith(("src/", "eab2/")) or name in (
        "docs/t2b_cage_lemma.md", "docs/eab2_design.md", "tools/check_exact_construction.py",
        "tools/exact_construction_subset.py", "tools/exact_construction_flow.py")]
    assert all(sha(ROOT/name) == previous[name]["sha256"] for name in protected)
    for name in changed:
        data = (ROOT/name).read_bytes()
        assert not data.startswith(b"\xef\xbb\xbf") and b"\r" not in data, ("UTF-8 no BOM / LF", name)
        data.decode("utf-8")
        if name not in previous:
            assert len(data) <= 1000000, ("new file exceeds 1 MB", name)
    net = sum((ROOT/name).stat().st_size-previous.get(name, {}).get("size", 0) for name in changed)
    assert net <= 5000000, net
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert head == baseline["head"]
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    links = ["# WO-T2b 文件交付清单", "", "以下为本次新增/修改文件；完整证书与运行日志在外置证据目录。", "",
             "- [中文报告](file:///D:/eab-wt/cx-e2/reports/codex/T2b_report.md)",
             "- [外置证据](file:///D:/eab-evidence/reports/codex/T2b_evidence/)",
             "- [完整证书](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/)",
             "- [逐文件 SHA256](file:///D:/eab-evidence/reports/codex/T2b_evidence/artifact_manifest.json)", ""]
    links.extend("- ["+name+"]("+(ROOT/name).as_uri()+")" for name in changed)
    (REPORTS/"artifacts.md").write_text("\n".join(links)+"\n", encoding="utf-8", newline="\n")
    report = {
        "baseline_commit": head, "baseline_clean": baseline["status"] == "",
        "protected_existing_files_checked": len(protected), "protected_existing_changes": [],
        "changed_files": changed, "net_bytes_before_this_audit_refresh": net,
        "new_files_under_1MB": True, "net_under_5MB": True, "authored_utf8_no_bom_lf": True,
        "git_writes": False, "fresh_git_checkout": False,
        "independent_verifier": "not inspected; await owner integration notification",
        "archive_scope": "local disk only, not a remote backup",
        "manifest_excludes": ["tmp/", "artifact_manifest.json"],
        "rollback": "compare baseline ZIP member SHA before any per-file recovery; preserve later owner edits",
    }
    write(REPORTS/"delivery_audit.json", report)
    external = [{"relative_path": path.relative_to(EVIDENCE).as_posix(),
                 "bytes": path.stat().st_size, "sha256": sha(path)}
                for path in sorted(EVIDENCE.rglob("*"))
                if path.is_file() and "tmp" not in path.relative_to(EVIDENCE).parts
                and path != EVIDENCE/"artifact_manifest.json"]
    delivery_names = sorted(set(changed) | {"reports/codex/T2b_evidence/artifacts.md",
                                           "reports/codex/T2b_evidence/delivery_audit.json"})
    delivery = [{"path": name, "bytes": (ROOT/name).stat().st_size, "sha256": sha(ROOT/name)}
                for name in delivery_names]
    write(EVIDENCE/"artifact_manifest.json", {"external_root": str(EVIDENCE), "files": external,
                                              "repository_root": str(ROOT), "repository_delivery": delivery})
    print(json.dumps({"changed_files": len(delivery), "external_files": len(external),
                      "protected_unchanged": len(protected), "net_bytes": net}, ensure_ascii=False))


if __name__ == "__main__":
    run()
