"""Append-only H1 archive for the C3-L3 acceptance repair; never deletes inputs."""
from pathlib import Path
import gzip
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reports/codex/C3L3_repair_evidence"
DEST = Path("D:/eab-evidence/reports/codex/C3L3_evidence/acceptance_repair_20261023/final_runs")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def append(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data, f"archive collision: {path}"
    else:
        with path.open("xb") as stream:
            stream.write(data)


def main():
    assert json.loads((OUT / "progress.json").read_text("utf-8"))["complete"]
    inputs = set()
    for path in (OUT / "tmp").glob("*"):
        if path.is_file():
            inputs.add(path)
    for name in ("final_fast", "final_full"):
        run = OUT / "tmp" / name
        inputs.update(p for p in run.glob("*") if p.is_file())
    inputs.update(p for p in (OUT / "tmp/rollback").rglob("*") if p.is_file())
    queue = json.loads((OUT / "continuation_dll_archive_queue.json").read_text("utf-8"))
    for item in queue["files"]:
        path = Path(item["path"])
        assert sha(path.read_bytes()) == item["sha256"]
        inputs.add(path)
    mutations = ROOT / "eab2/build/tmp/c3l3_repair_critical_mutations_20261023_r1"
    inputs.update(p for p in mutations.rglob("*") if p.is_file()
                  and p.suffix in {".log", ".json", ".py", ".cpp", ".hpp", ".bat"})
    rows = []
    for path in sorted(inputs):
        assert path.resolve().is_relative_to(ROOT.resolve())
        data = path.read_bytes()
        relative = path.relative_to(ROOT).as_posix()
        archive = DEST / (relative + ".gz")
        packed = gzip.compress(data, compresslevel=9, mtime=0)
        append(archive, packed)
        assert gzip.decompress(archive.read_bytes()) == data
        rows.append(dict(original=relative, bytes=len(data), sha256=sha(data), archive=archive.as_posix(),
                         archive_bytes=len(packed), archive_sha256=sha(packed)))
    manifest = json.loads((OUT / "tmp/final_full/source_manifest.json").read_text("utf-8"))
    source = OUT / "tmp/final_full/source"
    zip_path = OUT / "tmp/final_full_tested_source.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipped:
        for item in manifest:
            data = (source / item["path"]).read_bytes()
            assert sha(data) == item["sha256"]
            info = zipfile.ZipInfo(item["path"], date_time=(2026, 10, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zipped.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    zip_dest = DEST / zip_path.name
    zip_data = zip_path.read_bytes()
    append(zip_dest, zip_data)
    with zipfile.ZipFile(zip_dest) as zipped:
        assert set(zipped.namelist()) == {r["path"] for r in manifest}
        for item in manifest:
            assert sha(zipped.read(item["path"])) == item["sha256"]
    summary = dict(schema="eab2.c3l3.repair_archive.v1", files=rows,
        tested_source_zip=dict(path=zip_dest.as_posix(), bytes=len(zip_data), sha256=sha(zip_data),
                               files=len(manifest), fresh_git_checkout=False),
        append_only=True, no_input_removed=True, verified_decompression=True,
        note="Local append-only archive, not a remote backup. Current differential authority remains in the repair evidence directory.")
    payload = (json.dumps(summary, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    append(DEST / "archive_manifest.json", payload)
    (OUT / "archive_manifest.json").write_bytes(payload)
    print(f"C3L3_REPAIR_ARCHIVE_OK files={len(rows)} source_files={len(manifest)} verified=1")


if __name__ == "__main__":
    main()
