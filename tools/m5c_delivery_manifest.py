"""List all M5c changed/new files, refusing invalid or unstable delivery bytes."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/codex/M5c_evidence"
BASE_REVISION = "efb0dfe514a1f60c44e6341b69cce77ff5c9ec17"
EXCLUDED = {"reports/codex/M5c_evidence/delivery_manifest.json", "reports/codex/M5c_evidence/DELIVERY_INDEX.md"}


def delivery_paths():
    changed = subprocess.check_output(["git", "diff", BASE_REVISION, "--name-only", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    added = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    return sorted(set(changed+added)-{""}-EXCLUDED)


def main():
    names = delivery_paths()
    rows, violations = [], []
    for name in names:
        path = ROOT / name
        if not path.is_file():
            rows.append(dict(path=name, deleted=True))
            continue
        data = path.read_bytes()
        suffix = path.suffix.lower()
        text_file = suffix in {".py", ".md", ".json", ".jsonl", ".txt", ".log", ".csv", ".toml", ".ini", ".cfg", ".yaml", ".yml"}
        if text_file:
            data.decode("utf-8")
            if data.startswith(b"\xef\xbb\xbf"):
                violations.append(name+": UTF-8 BOM")
            without_crlf = data.replace(b"\r\n", b"")
            if b"\r" in without_crlf or (b"\r\n" in data and b"\n" in without_crlf):
                violations.append(name+": bare CR or mixed line endings")
        if len(data) > 1_000_000 and (suffix in {".txt", ".log", ".jsonl"} or "nodes" in path.name.lower()):
            violations.append(name+": large public log/node list")
        rows.append(dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), uri=path.as_uri()))
    # Never publish complete=True first and only afterwards raise for violations.
    assert not violations, violations
    assert delivery_paths() == names, "delivery file set changed while manifest was built"
    for row in rows:
        path = ROOT / row["path"]
        if row.get("deleted"):
            assert not path.is_file(), "deleted file reappeared during publication"
        else:
            assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"], "delivery bytes changed during publication: " + row["path"]
    result = dict(complete=True, base_revision=BASE_REVISION,
                  files=rows, encoding_size_violations=violations,
                  self_excluded=sorted(EXCLUDED), ignored_temporary_files_not_deliverables=True)
    lines = ["# M5c 交付清单", "", "本清单列出基线后全部修改/新增的非 ignored 文件。临时大数据不提交；JSON 清单含字节数、SHA256 与编码/尺寸检查。", "",
             "- [中文总报告]("+(ROOT / "reports/codex/M5c_report.md").as_uri()+")",
             "- [机器清单]("+(OUT / "delivery_manifest.json").as_uri()+")", "", "## 全部文件", ""]
    lines += ["- ["+row["path"]+"]("+row["uri"]+")" if "uri" in row else "- 删除："+row["path"] for row in rows]
    (OUT / "delivery_manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    (OUT / "DELIVERY_INDEX.md").write_text("\n".join(lines)+"\n", encoding="utf-8", newline="\n")
    print("M5C_DELIVERY_MANIFEST_GREEN", len(rows), "files; UTF-8 no BOM; no mixed line endings")


if __name__ == "__main__":
    main()
