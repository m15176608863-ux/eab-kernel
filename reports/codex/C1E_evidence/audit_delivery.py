"""Read-only source audit plus report-local manifests; run after finalization."""
from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SELF_OUTPUTS = {HERE / name for name in ("integrity.json", "deliverables.json", "deliverables.md")}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="")


def main():
    full = json.loads((HERE / "c1e_final/summary.json").read_text("utf-8"))
    assert full["complete"], "Do not audit an unfinished run"
    baseline = json.loads((HERE / "baseline_hashes.json").read_text("utf-8"))
    names = sorted(set(git("ls-files", "--cached", "--others", "--exclude-standard", "-z").decode("utf-8").split("\0")) - {""})
    changed_old = [name for name, old in baseline.items() if not (ROOT / name).is_file() or digest(ROOT / name) != old]
    outside_scope = [name for name in changed_old if not name.startswith("eab2/") and name not in {"tools/eab2_audit.py", "tools/eab2_diff.py"}]
    source_unchanged = {prefix: all((ROOT / name).is_file() and digest(ROOT / name) == old for name, old in baseline.items() if name.startswith(prefix))
                        for prefix in ("src/eab/", "fixtures/", "tests/", "eab2/third_party/", "docs/")}
    deliverable_names = sorted(set(changed_old) | {name for name in names if name not in baseline and
        (name.startswith("reports/codex/C1E_") or name.startswith("eab2/") or name.startswith("tools/eab2_c1_") or name == "tools/eab2_diff_c1.py")})
    failures = []
    entries = []
    for name in deliverable_names:
        path = ROOT / name
        if path in SELF_OUTPUTS:
            continue
        if not path.is_file():
            failures.append({"path": name, "issue": "missing"})
            continue
        raw = path.read_bytes()
        encoding = "UTF-8"
        try:
            raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            encoding = "INVALID"
            failures.append({"path": name, "issue": "invalid UTF-8"})
        if raw.startswith(b"\xef\xbb\xbf"):
            failures.append({"path": name, "issue": "BOM"})
        crlf = raw.count(b"\r\n")
        lone_lf = raw.count(b"\n") - crlf
        lone_cr = raw.count(b"\r") - crlf
        if lone_cr or (crlf and lone_lf):
            failures.append({"path": name, "issue": "mixed or lone CR newlines"})
        if len(raw) > 1_000_000:
            failures.append({"path": name, "issue": "deliverable exceeds 1 MB"})
        if path.suffix.lower() in {".bat", ".cmd"} and not raw.isascii():
            failures.append({"path": name, "issue": "batch not ASCII"})
        entries.append({"path": name, "uri": path.as_uri(), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                        "encoding": encoding, "newlines": "CRLF" if crlf else "LF", "status": "modified" if name in baseline else "new"})
    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if diff_check.returncode:
        failures.append({"issue": "git diff --check", "output": diff_check.stdout.decode("utf-8", errors="replace")})
    if outside_scope:
        failures.append({"issue": "baseline changed outside write scope", "paths": outside_scope})
    for prefix, value in source_unchanged.items():
        if not value:
            failures.append({"issue": "read-only baseline changed", "prefix": prefix})
    raw_paths = set()
    for run in ("c1e_fast", "c1e_final"):
        base = HERE / "tmp" / run
        raw_paths.update(p for p in base.glob("*") if p.is_file())
    generated = json.loads((HERE / "generated_final.json").read_text("utf-8"))
    raw_paths.add(Path(generated["journal"]))
    raw_paths.update(Path(row["path"]) for row in generated["input_chunks"])
    for name in ("eab2/build/eab2.dll", "eab2/build/eab2_test.dll", "eab2/build/eab2_core.lib", "eab2/build/compile_commands.json"):
        raw_paths.add(ROOT / name)
    ignored = [{"path": p.relative_to(ROOT).as_posix(), "uri": p.as_uri(), "bytes": p.stat().st_size, "sha256": digest(p)}
               for p in sorted(raw_paths) if p.is_file()]
    for row in ignored:
        check = subprocess.run(["git", "check-ignore", "-q", "--", row["path"]], cwd=ROOT)
        if check.returncode != 0:
            failures.append({"path": row["path"], "issue": "raw/runtime evidence is not ignored"})
    source_manifest = json.loads((HERE / "tmp/c1e_final/source_manifest.json").read_text("utf-8"))
    post_snapshot_changed = [row["path"] for row in source_manifest if not (ROOT / row["path"]).is_file() or digest(ROOT / row["path"]) != row["sha256"]]
    if post_snapshot_changed:
        failures.append({"issue": "post-H1 source changed", "paths": post_snapshot_changed})
    integrity = {"schema": "eab2.c1e.integrity.v1", "status": "PASS" if not failures else "FAIL",
        "failures": failures, "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "base_commit": git("rev-parse", "HEAD").decode().strip(), "branch": git("branch", "--show-current").decode().strip(),
        "git_writes_performed": False, "fresh_git_checkout": False, "baseline_changed_files": changed_old,
        "readonly_prefixes_unchanged": source_unchanged, "design_sha256": digest(ROOT / "docs/eab2_design.md"),
        "python_judge_no_modification": source_unchanged["src/eab/"],
        "post_h1_source_hash_changes": post_snapshot_changed,
        "final_report_added_after_h1": "reports/codex/C1E_report.md; report generation only, no source or tests changed",
        "deliverable_files_checked": len(entries), "maximum_deliverable_bytes": max(r["bytes"] for r in entries),
        "byte_contract_files": {n: digest(ROOT / n) for n in (".gitattributes", ".gitignore", "AGENTS.md")},
        "git_diff_check": {"returncode": diff_check.returncode, "output": diff_check.stdout.decode("utf-8", errors="replace")},
        "self_manifest_exclusions": [p.relative_to(ROOT).as_posix() for p in sorted(SELF_OUTPUTS)]}
    write_json(HERE / "integrity.json", integrity)
    manifest = {"schema": "eab2.c1e.deliverables.v1", "hashes_are_integrity_not_mathematical_oracles": True,
                "files": entries, "ignored_runtime_evidence": ignored, "self_manifest_exclusions": integrity["self_manifest_exclusions"]}
    write_json(HERE / "deliverables.json", manifest)
    lines = ["# WO-C1E 交付文件清单", "", "所有链接均指向当前工作树。SHA256仅标识数据/工具完整性，不作为数学回归判定。", "",
             "- [主报告](file:///D:/eab-wt/cx-c0/reports/codex/C1E_report.md)",
             "- [机器可读清单](file:///D:/eab-wt/cx-c0/reports/codex/C1E_evidence/deliverables.json)",
             "- [完整性审计](file:///D:/eab-wt/cx-c0/reports/codex/C1E_evidence/integrity.json)",
             "", "## 源码、工具及小型证据", "", "| 文件 | 字节数 | SHA256 |", "|---|---:|---|"]
    lines.extend(f"| [{r['path']}]({r['uri']}) | {r['bytes']} | `{r['sha256']}` |" for r in entries)
    lines.extend(["", "## 忽略的原始运行证据和构建产物（不入库）", "", "大文件仅放当前工作树忽略的 tmp/build 中；未写只读的外部归档目录。以下为重跑/审查索引，不保证这些临时目录被外部清理后仍存在。完整源字节副本在各H1 source目录，source_manifest列出逐文件哈希。", "", "| 文件 | 字节数 | SHA256 |", "|---|---:|---|"])
    lines.extend(f"| [{r['path']}]({r['uri']}) | {r['bytes']} | `{r['sha256']}` |" for r in ignored)
    lines.extend(["", "本清单、机器清单及integrity自身不递归收录自身SHA。最终作者验证状态见 verification_summary.json；独立对抗核查/新鲜Git树仍未完成。", ""])
    (HERE / "deliverables.md").write_text("\n".join(lines), encoding="utf-8", newline="")
    print(f"C1E_DELIVERY_INTEGRITY files={len(entries)} failures={len(failures)} status={integrity['status']}")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
