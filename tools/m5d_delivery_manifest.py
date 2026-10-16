"""Inventory only this work order's Git-visible changed/new deliverables."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/codex/M5d_evidence"
OUTPUTS = {"reports/codex/M5d_evidence/delivery_manifest.json",
           "reports/codex/M5d_evidence/delivery_manifest.md"}


def git_names(*args):
    data = subprocess.check_output(["git", *args, "-z"], cwd=ROOT)
    return {name for name in data.decode("utf-8").split("\0") if name}


def main():
    names = git_names("diff", "HEAD", "--name-only") | git_names("ls-files", "--others", "--exclude-standard")
    rows, violations = [], []
    for name in sorted(names - OUTPUTS):
        path = ROOT / name
        if not path.is_file():
            violations.append({"path": name, "reason": "missing changed file"})
            continue
        content = path.read_bytes()
        if len(content) > 1_000_000:
            violations.append({"path": name, "reason": "Git-visible deliverable exceeds 1 MB"})
        if path.suffix.lower() in {".md", ".py", ".json", ".jsonl", ".txt", ".log"}:
            if content.startswith(b"\xef\xbb\xbf"):
                violations.append({"path": name, "reason": "UTF-8 BOM"})
            try:
                content.decode("utf-8")
            except UnicodeDecodeError:
                violations.append({"path": name, "reason": "not UTF-8"})
            if b"\r\n" in content and b"\n" in content.replace(b"\r\n", b""):
                violations.append({"path": name, "reason": "mixed LF and CRLF"})
        rows.append({"path": name, "uri": path.as_uri(), "bytes": len(content),
                     "sha256": hashlib.sha256(content).hexdigest()})
    # The byte-preserving repository allows homogeneous CRLF; do not mistake
    # its CR terminator for trailing whitespace or rewrite frozen JSON bytes.
    diff = subprocess.run(["git", "-c", "core.whitespace=cr-at-eol", "diff", "HEAD", "--check"], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if diff.returncode:
        violations.append({"path": "git diff --check", "reason": diff.stdout + diff.stderr})
    data = {"schema": "eab.m5d-delivery-manifest.v1", "complete": not violations,
            "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "baseline_revision": "5b73cc8dfc1ad4f257412392111927d5a7171640",
            "scope": "Git-visible changed/new files only; ignored large raw streams remain local evidence",
            "whitespace_check": "git -c core.whitespace=cr-at-eol diff HEAD --check; homogeneous CRLF permitted",
            "manifest_self_excluded": sorted(OUTPUTS), "files": rows, "violations": violations}
    (OUT / "delivery_manifest.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n",
                                                encoding="utf-8", newline="\n")
    lines = ["# M5d 交付清单", "", "仅列本单 Git 可见的修改/新增文件；大日志与逐节点流保留在 ignored tmp。",
             "本清单自身不递归计算哈希；精确 SHA256 见同目录 JSON。", "",
             f"文件数：{len(rows)}；编码/换行/大小/diff 检查违例：{len(violations)}。", "",
             "|文件|字节|", "|---|---:|"]
    lines.extend(f"|[{row['path']}]({row['uri']})|{row['bytes']}|" for row in rows)
    (OUT / "delivery_manifest.md").write_text("\n".join(lines)+"\n", encoding="utf-8", newline="\n")
    print("M5D_DELIVERY_AUDIT", "GREEN" if not violations else "RED", len(rows), "files", len(violations), "violations")
    if violations:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
