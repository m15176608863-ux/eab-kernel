"""Inventory the local work-order diff, without staging or committing anything."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def git_names(*args):
    return subprocess.check_output(["git", *args, "-z"], cwd=ROOT).decode("utf-8").split("\0")


def build():
    relative = set(git_names("diff", "--name-only")) | set(git_names("ls-files", "--others", "--exclude-standard"))
    excluded = {str((HERE / name).relative_to(ROOT)).replace("\\", "/")
                for name in ("delivery_manifest.json", "DELIVERY_INDEX.md")}
    entries = []
    for rel in sorted(relative - {""} - excluded):
        path = (ROOT / rel).resolve()
        assert path.is_relative_to(ROOT), rel
        if not path.is_file():
            continue
        data = path.read_bytes()
        entries.append(dict(path=rel, url=path.as_uri(), bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    manifest = dict(anchor="m4-seam@0e9ef93", scope=ROOT.as_posix(),
                    excludes="self-referential index/manifest and git-ignored pytest scratch",
                    files=entries)
    (HERE / "delivery_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    lines = ["# WO-M4a 交付索引", "", "所有文件均在本工作树；以下链接含源改动、夹具、证据与沙箱原始产物。",
             "索引不包含 git 忽略的 pytest 临时目录；没有提交或暂存。", "",
             f"- [中文报告]({(ROOT / 'reports/codex/M4a_report.md').as_uri()})",
             f"- [逐文件字节数与 SHA-256]({(HERE / 'delivery_manifest.json').as_uri()})",
             "", "## 主要代码、文档、门与冻结夹具"]
    raw = []
    for e in entries:
        if "/sandbox/" in e["path"] or "/review_capture_inputs/" in e["path"]:
            raw.append(e)
        else:
            lines.append(f"- [{e['path']}]({e['url']})")
    lines += ["", f"## 沙箱与故意损坏的审查副本（{len(raw)} 文件，不是回归夹具）"]
    lines += [f"- [{e['path']}]({e['url']})" for e in raw]
    (HERE / "DELIVERY_INDEX.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    assert all(Path(e["url"].removeprefix("file:///")).exists() for e in entries)
    print(json.dumps(dict(files=len(entries), bytes=sum(e["bytes"] for e in entries), links="verified")))


if __name__ == "__main__":
    build()
