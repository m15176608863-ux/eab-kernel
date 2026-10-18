"""WO-H1 byte-preserving evidence relocation (standard library, no Git writes).

First move the enumerated test inputs to fixtures/frozen, then hash and rename
each reports/codex/*_evidence directory except H1_evidence into the external
archive. The per-file inventories live outside the repository. --apply is an
explicit safeguard; without it only preflight and the planned paths are read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import time

VERSION = "h1-archive-v1"
DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def inside(path: Path, root: Path) -> Path:
    """Resolve every rename endpoint and refuse escapes through junctions."""
    resolved = path.resolve()
    if resolved == root or not resolved.is_relative_to(root):
        raise ValueError(f"path is not strictly inside approved root: {path}")
    return resolved


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".writing")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8", newline="")
    temporary.replace(path)


def tracked_files(root: Path) -> set[str]:
    result = subprocess.run(["git", "ls-files", "--cached", "-z"], cwd=root,
                            check=True, capture_output=True)
    return {name for name in result.stdout.decode("utf-8").split("\0") if name}


def tree_files(directory: Path, approved_root: Path):
    """Deterministic traversal; no filesystem links may leave the write scope."""
    for parent, dirs, files in os.walk(directory, followlinks=False):
        dirs.sort()
        files.sort()
        for name in dirs:
            path = Path(parent) / name
            inside(path, approved_root)
            if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
                raise ValueError(f"directory link is not archived implicitly: {path}")
        for name in files:
            path = Path(parent) / name
            inside(path, approved_root)
            if path.is_symlink():
                raise ValueError(f"file link is not archived implicitly: {path}")
            yield path


def preflight(root: Path, archive: Path, manifest: Path):
    if root == archive or root.is_relative_to(archive) or archive.is_relative_to(root):
        raise ValueError("workspace and archive roots must be disjoint")
    if root.drive.casefold() != archive.drive.casefold():
        raise ValueError("H1 requires same-volume byte-preserving directory rename")
    inside(manifest, root)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if payload.get("schema") != "h1-frozen-input-move-v1":
        raise ValueError("unsupported input manifest schema")
    sources, destinations = set(), set()
    for item in payload["files"]:
        source = inside(root / item["source"], root)
        destination = inside(root / item["destination"], root)
        if not item["source"].startswith("reports/") or not item["destination"].startswith("fixtures/frozen/"):
            raise ValueError("input relocation is not reports -> fixtures/frozen")
        if source in sources or destination in destinations:
            raise ValueError("input relocation is not one-to-one")
        sources.add(source)
        destinations.add(destination)
        if not source.is_file() or destination.exists():
            raise ValueError(f"source missing or destination already exists: {source}")
        if source.stat().st_size != item["bytes"] or sha256(source) != item["sha256"]:
            raise ValueError(f"input differs from reviewed manifest: {source}")
    directories = sorted(path for path in (root / "reports" / "codex").glob("*_evidence")
                         if path.is_dir() and path.name != "H1_evidence")
    for source in directories:
        inside(source, root)
        destination = inside(archive / source.relative_to(root), archive)
        if destination.exists():
            raise ValueError(f"archive destination already exists: {destination}")
    return payload, directories


def archive_directory(root, archive, directory, tracked, progress, completed, start):
    """Hash one scoped directory, rename it on-volume, verify every destination."""
    inventory_root = inside(archive / "_manifests", archive)
    inventory_root.mkdir(parents=True, exist_ok=True)
    relative = directory.relative_to(root).as_posix()
    destination = inside(archive / relative, archive)
    inventory = inside(inventory_root / (relative.replace("/", "__") + ".sha256.jsonl"), archive)
    temporary = inventory.with_name(inventory.name + ".partial")
    if inventory.exists():
        raise ValueError(f"completed inventory already exists: {inventory}")
    row = {"source": relative, "destination": str(destination), "files": 0, "bytes": 0,
           "tracked_files": 0, "tracked_bytes": 0, "manifest": str(inventory)}
    last_update = 0.0
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        for path in tree_files(directory, root):
            name = path.relative_to(root).as_posix()
            size = path.stat().st_size
            record = {"source": name, "bytes": size, "sha256": sha256(path), "tracked": name in tracked}
            stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            row["files"] += 1
            row["bytes"] += size
            if record["tracked"]:
                row["tracked_files"] += 1
                row["tracked_bytes"] += size
            if time.monotonic() - last_update >= 5:
                stream.flush()
                write_json(progress, {"stage": "hashing", "current": row,
                                      "completed_directories": completed,
                                      "elapsed_seconds": round(time.monotonic()-start, 3)})
                last_update = time.monotonic()
    temporary.replace(inventory)
    row["manifest_sha256"] = sha256(inventory)
    # Verify both final absolute endpoints immediately before directory move.
    inside(directory, root)
    inside(destination, archive)
    destination.parent.mkdir(parents=True, exist_ok=True)
    directory.rename(destination)
    # Same-volume rename retains every byte. Verify every named file/size at
    # its new path, in addition to the pre-rename cryptographic inventory.
    with inventory.open(encoding="utf-8") as stream:
        checked = 0
        for line in stream:
            record = json.loads(line)
            moved = inside(archive / record["source"], archive)
            if not moved.is_file() or moved.stat().st_size != record["bytes"]:
                raise RuntimeError(f"archive relocation verification failed: {moved}")
            checked += 1
    if checked != row["files"] or directory.exists():
        raise RuntimeError(f"directory relocation count failed: {relative}")
    row["verification"] = "all source SHA256 recorded; same-volume rename; all destination file sizes checked"
    write_json(progress, {"stage": "directory_moved", "current": row,
                          "completed_directories": completed + 1,
                          "elapsed_seconds": round(time.monotonic()-start, 3)})
    print(f"archived {relative}: {row['files']} files / {row['bytes']} bytes", flush=True)
    return row


def archive_all(root: Path, archive: Path, manifest: Path, apply: bool):
    inputs, directories = preflight(root, archive, manifest)
    tracked = tracked_files(root)
    print(json.dumps({"tool": VERSION, "apply": apply, "input_files": len(inputs["files"]),
                      "evidence_directories": [p.relative_to(root).as_posix() for p in directories]},
                     ensure_ascii=False), flush=True)
    if not apply:
        return
    output = root / "reports" / "codex" / "H1_evidence"
    progress = output / "archive_progress.json"
    result_file = output / "archive_result.json"
    if result_file.exists():
        raise ValueError("completed archive_result exists; do not overwrite history")
    archive.mkdir(parents=True, exist_ok=True)
    inventory_root = inside(archive / "_manifests", archive)
    inventory_root.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    result = {"schema": "h1-archive-result-v1", "tool_version": VERSION,
              "source_root": str(root), "archive_root": str(archive),
              "input_manifest": manifest.relative_to(root).as_posix(),
              "inputs_moved": len(inputs["files"]),
              "input_bytes": sum(item["bytes"] for item in inputs["files"]),
              "directories": [], "status": "running"}
    # No source is changed until the whole input mapping has passed preflight.
    for item in inputs["files"]:
        source = inside(root / item["source"], root)
        destination = inside(root / item["destination"], root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
        if sha256(destination) != item["sha256"]:
            raise RuntimeError(f"moved input bytes changed: {destination}")
    write_json(progress, {"stage": "inputs_moved", "inputs": result["inputs_moved"]})
    for directory in directories:
        result["directories"].append(archive_directory(
            root, archive, directory, tracked, progress, len(result["directories"]), start))
    result["status"] = "complete"
    result["elapsed_seconds"] = round(time.monotonic() - start, 3)
    result["archive_files"] = sum(row["files"] for row in result["directories"])
    result["archive_bytes"] = sum(row["bytes"] for row in result["directories"])
    result["tracked_archive_files"] = sum(row["tracked_files"] for row in result["directories"])
    result["tracked_archive_bytes"] = sum(row["tracked_bytes"] for row in result["directories"])
    write_json(result_file, result)
    lines = ["# 证据外部归档（WO-H1，2026-10-19）", "",
             "历史报告正文不逐个改链接。路径映射：旧 `reports/codex/<名称>_evidence/<相对文件>` 对应 "
             "`D:/eab-evidence/reports/codex/<名称>_evidence/<相对文件>`；H1 当前运行目录不归档。",
             "测试实际读取的输入优先映射到 `fixtures/frozen/<去掉 reports/ 的原路径>`；输入原字节保留，嵌入的历史路径/哈希不重写。",
             "保留仓库内的报告正文、当前 `reports/codex/inputs/`、本单 H1 证据及其他小型索引；不重写 Git 历史。", "",
             f"- 首批测试输入：{result['inputs_moved']} 文件，{result['input_bytes']:,} 字节；"
             "[逐文件输入迁移清单](codex/H1_evidence/frozen_inputs_manifest.json)。",
             f"- 外归档：{len(result['directories'])} 目录，实际 {result['archive_files']:,} 文件、"
             f"{result['archive_bytes']:,} 字节（含旧 ignored 临时/沙箱产物）；其中 Git 跟踪 "
             f"{result['tracked_archive_files']:,} 文件、{result['tracked_archive_bytes']:,} 字节。",
             "- 每目录清单含原相对路径、字节数、SHA256、是否原 Git 跟踪；巨大清单只存仓库外。",
             "- 验证：搬迁前逐文件 SHA256；同卷目录 rename 保留原字节；搬迁后逐文件存在性/长度核对。"
             "输入迁移另外重算目标 SHA256；无覆写与无删除操作。",
             "- 归档脚本：[tools/h1_archive_evidence.py](../tools/h1_archive_evidence.py)；"
             "[机器结果](codex/H1_evidence/archive_result.json)。", "",
             "| 原目录 | 实际文件数 | 实际字节 | 跟踪文件数 | 跟踪字节 | SHA256 逐文件清单 |",
             "|---|---:|---:|---:|---:|---|"]
    for row in result["directories"]:
        url = Path(row["manifest"]).as_uri()
        lines.append(f"| `{row['source']}` | {row['files']:,} | {row['bytes']:,} | "
                     f"{row['tracked_files']:,} | {row['tracked_bytes']:,} | "
                     f"[{Path(row['manifest']).name}]({url}) |")
    lines += ["", "## 验证与回退", "",
              "`archive_result.json` 另记录每份清单自身的 SHA256。如需回退，先确认原路径不存在，"
              "再依据清单将目标目录移回原位置，并把 fixtures/frozen 输入移回其 source；"
              "不得覆盖所有者后续生成的数据。归档是本地原字节保存，不是远端备份。", ""]
    (root / "reports" / "EVIDENCE_ARCHIVE.md").write_text("\n".join(lines), encoding="utf-8", newline="")
    write_json(progress, {"stage": "complete", "archive_files": result["archive_files"],
                          "archive_bytes": result["archive_bytes"], "elapsed_seconds": result["elapsed_seconds"]})
    print(json.dumps({k: result[k] for k in ("status", "archive_files", "archive_bytes", "elapsed_seconds")}), flush=True)


def archive_additional(root, archive, names, apply):
    """Append historical reproduction/showcase directories after the main run."""
    if root == archive or root.is_relative_to(archive) or archive.is_relative_to(root):
        raise ValueError("workspace and archive roots must be disjoint")
    if root.drive.casefold() != archive.drive.casefold():
        raise ValueError("H1 requires same-volume directory rename")
    directories = []
    for name in names:
        source = inside(root / name, root)
        relative = source.relative_to(root).as_posix()
        if relative != "reports/showcase" and not re.fullmatch(r"reports/codex/inputs/G6[A-Z]+_repro", relative):
            raise ValueError(f"not an approved additional historical directory: {relative}")
        destination = inside(archive / relative, archive)
        if not source.is_dir() or destination.exists():
            raise ValueError(f"additional source missing or destination exists: {relative}")
        directories.append(source)
    if len(set(directories)) != len(directories):
        raise ValueError("duplicate additional directory")
    print(json.dumps({"additional_directories": names, "apply": apply}), flush=True)
    if not apply:
        return
    output = root / "reports" / "codex" / "H1_evidence"
    main_result = json.loads((output / "archive_result.json").read_text(encoding="utf-8"))
    if main_result["status"] != "complete":
        raise ValueError("main archive must finish before additional relocation")
    result_path = output / "archive_additional_result.json"
    if result_path.exists():
        raise ValueError("completed additional result exists; do not overwrite")
    progress = output / "archive_additional_progress.json"
    tracked = tracked_files(root)
    start = time.monotonic()
    result = {"schema": "h1-additional-archive-v1", "tool_version": VERSION,
              "source_root": str(root), "archive_root": str(archive), "directories": []}
    for source in sorted(directories):
        result["directories"].append(archive_directory(
            root, archive, source, tracked, progress, len(result["directories"]), start))
    for key, field in (("archive_files", "files"), ("archive_bytes", "bytes"),
                       ("tracked_archive_files", "tracked_files"), ("tracked_archive_bytes", "tracked_bytes")):
        result[key] = sum(row[field] for row in result["directories"])
        result["combined_" + key] = result[key] + main_result[key]
    result["status"] = "complete"
    result["elapsed_seconds"] = round(time.monotonic() - start, 3)
    write_json(result_path, result)
    lines = ["", "## 追加：历史对抗复现与展示产物", "",
             "运行输入依赖扫描未发现 G6F–G6O 复现目录的生产/测试/工具引用；这些目录及 showcase "
             "作为历史证据原字节外移，不执行旧复现。" 
             "旧 `reports/<相对路径>` 映射为 `D:/eab-evidence/reports/<相对路径>`。", "",
             f"追加 {len(directories)} 目录、{result['archive_files']:,} 文件、{result['archive_bytes']:,} 字节；"
             f"两批合计 {len(directories) + len(main_result['directories'])} 目录、"
             f"{result['combined_archive_files']:,} 文件、{result['combined_archive_bytes']:,} 字节，"
             f"其中原 Git 跟踪 {result['combined_tracked_archive_files']:,} 文件、"
             f"{result['combined_tracked_archive_bytes']:,} 字节。", "",
             "[依赖审计](codex/H1_evidence/g6_repro_dependency_audit.json)；"
             "[追加归档结果](codex/H1_evidence/archive_additional_result.json)。", "",
             "| 原目录 | 实际文件数 | 实际字节 | 跟踪文件数 | 跟踪字节 | SHA256 逐文件清单 |",
             "|---|---:|---:|---:|---:|---|"]
    for row in result["directories"]:
        inventory = Path(row["manifest"])
        lines.append(f"| `{row['source']}` | {row['files']:,} | {row['bytes']:,} | "
                     f"{row['tracked_files']:,} | {row['tracked_bytes']:,} | "
                     f"[{inventory.name}]({inventory.as_uri()}) |")
    lines += ["", "### 留在 reports 的文件类别", "",
              "- 历史 `*_report.md` 正文与小型文字/JSON 汇总：保留为证据导航，不重新计算或更新历史结论。",
              "- `reports/codex/inputs/` 的 Shi 双读者/对照材料、历史 findings JSON 与审查报告：文档性输入保留；十个 `_repro` 子目录已外移。",
              "- `reports/codex/H1_evidence/`：本工单的计划、审计清单、迁移映射与当前验证；ignored 临时目录不属于可交付文件。",
              "- 根 `reports/` 的小型报告/指标记录及本归档索引：未把它们冒作当前运行证据；实际测试输入已按清单移到 fixtures。", ""]
    with (root / "reports" / "EVIDENCE_ARCHIVE.md").open("a", encoding="utf-8", newline="") as stream:
        stream.write("\n".join(lines))
    write_json(progress, {"stage": "complete", "archive_files": result["archive_files"],
                          "archive_bytes": result["archive_bytes"], "elapsed_seconds": result["elapsed_seconds"]})
    print(json.dumps({k: result[k] for k in ("status", "archive_files", "archive_bytes", "elapsed_seconds")}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--archive-root", type=Path, default=Path("D:/eab-evidence"))
    parser.add_argument("--manifest", type=Path, default=Path("reports/codex/H1_evidence/frozen_inputs_manifest.json"))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--additional-directory", action="append", default=[])
    args = parser.parse_args()
    root, archive = args.root.resolve(), args.archive_root.resolve()
    manifest = args.manifest if args.manifest.is_absolute() else root / args.manifest
    if args.additional_directory:
        archive_additional(root, archive, args.additional_directory, args.apply)
    else:
        archive_all(root, archive, manifest.resolve(), args.apply)


if __name__ == "__main__":
    main()
