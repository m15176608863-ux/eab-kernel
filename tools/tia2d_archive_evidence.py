"""Copy, SHA-verify, then unlink only explicitly selected T1a evidence files.

The external write boundary is the one explicitly approved by Claude. No Git
operations or recursive directory deletions occur. Existing unequal targets
are rejected; equal targets permit safe retry after an interrupted copy.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
REL = Path("reports/codex/T1a_evidence")
EXTERNAL = Path("D:/eab-evidence/reports/codex/T1a_evidence")
OLD = ("formal_20261019_01", "formal_smoke_01", "resume2/morphology_scan",
       "resume3/amplitude_retry", "p0_diagnostic_20261019_01", "contract_probe.json",
       "resume/zero_slope_probe.json")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(names, output):
    source_root, target_root = (ROOT / REL).resolve(), EXTERNAL.resolve()
    output = Path(output).resolve()
    if not output.is_relative_to(source_root) or output.exists():
        raise ValueError("new local T1a evidence manifest required")
    files = set()
    for name in names:
        source = (source_root / name).resolve()
        if not source.is_relative_to(source_root) or source == source_root or "tmp" in source.relative_to(source_root).parts:
            raise ValueError("archive source outside explicit evidence selection")
        if not source.exists():
            raise ValueError("missing selected archive source: " + str(source))
        files.update(p for p in source.rglob("*") if p.is_file()) if source.is_dir() else files.add(source)
    # Keep the prior concise readback audit local, not the large query corpus.
    files = sorted(p for p in files if p.name != "readback.json")
    records = []
    for source in files:
        relative = source.relative_to(source_root)
        target = (target_root / relative).resolve()
        if not target.is_relative_to(target_root) or source.is_symlink() or target.is_symlink():
            raise ValueError("unsafe archive path")
        row = dict(source=(REL / relative).as_posix(), archive=str(target), bytes=source.stat().st_size,
                   sha256=digest(source))
        if target.exists() and (target.stat().st_size != row["bytes"] or digest(target) != row["sha256"]):
            raise ValueError("unequal external target; never overwrite: " + str(target))
        records.append((source, target, row))
    output.parent.mkdir(parents=True, exist_ok=True)
    def save(state):
        output.write_text(json.dumps(dict(state=state, source_root=str(source_root), archive_root=str(target_root),
            files=[r for _, _, r in records], file_count=len(records), total_bytes=sum(r["bytes"] for _, _, r in records)),
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    save("COPYING")
    for source, target, row in records:
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copyfile(source, target)
        if target.stat().st_size != row["bytes"] or digest(target) != row["sha256"]:
            raise ValueError("archive copy verification failed")
    save("COPIED_AND_SHA_VERIFIED")
    # Check each source again before unlinking; no broad or computed recursion.
    for source, target, row in records:
        if digest(source) != row["sha256"] or digest(target) != row["sha256"]:
            raise ValueError("file changed during archive")
        source.unlink()
    save("COMPLETE")
    external_manifest = target_root / "_manifests" / output.name
    external_manifest.parent.mkdir(parents=True, exist_ok=True)
    if external_manifest.exists() and external_manifest.read_bytes() != output.read_bytes():
        raise ValueError("manifest conflict")
    external_manifest.write_bytes(output.read_bytes())
    return len(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--name", action="append", help="explicit relative evidence path; default original large evidence")
    args = parser.parse_args()
    print("archived files:", archive(OLD if args.name is None else args.name, args.output))


if __name__ == "__main__":
    main()
