"""Preserve raw completed-run bytes, then export UTF-8/LF evidence views.

The shared historical runner uses platform newlines. This post-processing
does not re-run tests or alter JSON values, source snapshots, or result lines.
Only completed T2b run directories are supported; raw bytes remain in a ZIP.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


EVIDENCE = Path("D:/eab-evidence/reports/codex/T2b_evidence").resolve()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def normalize(run_name):
    directory = (EVIDENCE/run_name).resolve()
    if directory.parent != EVIDENCE or not directory.is_dir():
        raise ValueError("only one completed run directly inside T2b evidence is permitted")
    summary = json.loads((directory/"summary.json").read_text("utf-8"))
    if not summary.get("complete"):
        raise ValueError("an unfinished run must not be normalized")
    archive, manifest = directory/"raw_runner_bytes.zip", directory/"lf_export.json"
    if archive.exists() or manifest.exists():
        raise ValueError("do not overwrite an existing raw-byte preservation record")
    paths = sorted(path for path in directory.iterdir()
                   if path.is_file() and path.suffix in (".json", ".jsonl", ".txt", ".log"))
    rows, prepared = [], []
    for path in paths:
        before = path.read_bytes()
        text = before.decode("utf-8-sig")
        after = text.replace("\r\n", "\n").encode("utf-8")
        if b"\r" in after:
            raise ValueError("non-newline carriage return needs separate review: "+str(path))
        if path.suffix == ".json":
            assert json.loads(before) == json.loads(after)
        assert text.splitlines() == after.decode("utf-8").splitlines()
        prepared.append((path, before, after))
        rows.append({"path": path.name, "raw_sha256": digest(before), "lf_sha256": digest(after),
                     "raw_bytes": len(before), "lf_bytes": len(after), "last_line_unchanged": True})
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path, before, _ in prepared:
            bundle.writestr(path.name, before)
    with zipfile.ZipFile(archive) as bundle:
        for row in rows:
            assert digest(bundle.read(row["path"])) == row["raw_sha256"]
    for path, _, after in prepared:
        path.write_bytes(after)
    record = {"raw_archive": archive.name, "raw_archive_sha256": digest(archive.read_bytes()),
              "test_results_recomputed": False, "json_values_changed": False, "members": rows}
    manifest.write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    print(json.dumps({"run": run_name, "files": len(rows), "raw_archive": str(archive)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_name")
    normalize(parser.parse_args().run_name)
