"""Deterministic gzip -9 fixture packaging, preserving decompressed case SHA.

The source batch has already passed independent readback. This tool does not
recompute mechanics, change provenance or pin historical hashes to live code.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

from tia2d_readback import read_json, load_batch, require

ROOT = Path(__file__).resolve().parents[1]


def pack(source, target):
    source, target = Path(source).resolve(), Path(target).resolve()
    require(source.is_relative_to(ROOT / "reports/codex/T1a_evidence"), "source evidence boundary")
    require(target.is_relative_to(ROOT / "fixtures/eab2_cases/tia2d-2") and not target.exists(), "new fixture boundary")
    manifest = read_json(source / "binary64/manifest.json")
    result = read_json(source / "readback.json")
    require(result["status"] == "PASS" and result["valid"] is True, "completed independent readback")
    target.mkdir(parents=True)
    binary = target / "binary64"
    binary.mkdir()
    entries = []
    for case in manifest["cases"]:
        for part in case["parts"]:
            raw = (source / "binary64" / part["path"]).read_bytes()
            require(len(raw) == part["bytes"] and hashlib.sha256(raw).hexdigest() == part["sha256"], "source part SHA")
            zipped = gzip.compress(raw, compresslevel=9, mtime=0)
            name = part["path"] + ".gz"
            (binary / name).write_bytes(zipped)
            require(gzip.decompress(zipped) == raw, "gzip roundtrip")
            entries.append(dict(**part, gz_path=name, gz_bytes=len(zipped), gz_sha256=hashlib.sha256(zipped).hexdigest()))
    index = dict(format="tia2d.private-gzip-index.v1", compression="gzip", compresslevel=9, mtime=0,
                 sha256_basis="decompressed_case_bytes", files=entries)
    (binary / "gzip_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    for name in ("manifest.json", "source_manifest.json"):
        shutil.copyfile(source / "binary64" / name, binary / name)
    shutil.copyfile(source / "registry.json", target / "registry.json")
    require(len(load_batch(binary)) == len(manifest["cases"]), "compressed strict batch read")
    return dict(batch=str(target), cases=len(manifest["cases"]), parts=len(entries),
                decompressed_bytes=sum(row["bytes"] for row in entries),
                compressed_bytes=sum(row["gz_bytes"] for row in entries),
                maximum_gz_bytes=max(row["gz_bytes"] for row in entries),
                index_sha256=hashlib.sha256((binary / "gzip_index.json").read_bytes()).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    summary = args.summary.resolve()
    require(summary.is_relative_to(ROOT / "reports/codex/T1a_evidence") and not summary.exists(), "new local summary")
    result = pack(args.source, args.target)
    summary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
