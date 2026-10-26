"""Freeze nine complete T2d bundles from a successfully completed formal run.

Only data are copied: all production/independent return fields remain intact.
Current-source hashes are never substituted for the recorded producer source.
This tool neither reruns the 93-case evidence nor deserializes pickle inputs.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path("D:/eab-evidence/reports/codex/T2d_evidence")
DEFAULT_OUTPUT = ROOT / "tests/data/t2d"
TOOL_VERSION = "t2d-replay-build-1"
SELECTED = (
    "N4_square_cage_k6", "N8_octagon_cage_k8", "N16_K16_cage_k10",
    "N4_octagon_escape_k20", "N8_K16_escape_k20", "N32_K16_escape_k20",
    "N8_square_mixed_escape", "N16_square_mixed_escape", "N32_square_mixed_escape",
)


def read_json(path):
    return json.loads(path.read_text(encoding="utf8"))


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2)+"\n").encode("utf8")


def freeze(source_run, destination):
    source_run, destination = source_run.resolve(), destination.resolve()
    if not source_run.is_relative_to(EVIDENCE.resolve()):
        raise ValueError("formal source run must stay inside the authorized T2d evidence directory")
    if destination != DEFAULT_OUTPUT.resolve() and not destination.is_relative_to(EVIDENCE.resolve()):
        raise ValueError("output must be tests/data/t2d or an authorized external evidence child")
    if (source_run / "invalid_run.json").exists():
        raise ValueError("an invalid or interrupted evidence run cannot be frozen")
    state = read_json(source_run / "state.json")
    if state.get("complete") is not True or state.get("phase") != "FINISHED":
        raise ValueError("only a fully completed formal run can be frozen")
    manifest_path = source_run / "manifest.json"
    manifest = read_json(manifest_path)
    if manifest.get("schema") != "eab.t2d.finite-evidence/1" or manifest.get("status") != "ACCEPTED_DIRECTED_RATIONAL_TRANSFERS":
        raise ValueError("wrong evidence schema or acceptance status")
    if manifest["counts"] != {"cages": 36, "strip_escapes": 54, "mixed_square_escapes": 3}:
        raise ValueError("the formal 93-case matrix is incomplete")
    if manifest["same_delta_contradictions"] != 0 or len(manifest["cases"]) != 93:
        raise ValueError("formal consistency ledger failed")
    rows_by_id = {row["id"]: row for row in manifest["cases"]}
    if len(rows_by_id) != 93:
        raise ValueError("duplicate case identities")
    source_files = {row["path"]: row for row in manifest["files"]}
    if len(source_files) != len(manifest["files"]):
        raise ValueError("duplicate file paths in formal integrity manifest")
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError("refuse to overwrite an existing frozen subset")
    destination.mkdir(parents=True, exist_ok=True)
    rows = []
    for number, identity in enumerate(SELECTED):
        row = rows_by_id[identity]
        source_path = (source_run / row["bundle"]).resolve()
        if not source_path.is_relative_to(source_run):
            raise ValueError("bundle path escaped its formal evidence run")
        source_bytes = source_path.read_bytes()
        source_record = source_files[row["bundle"]]
        if len(source_bytes) != source_record["bytes"] or hashlib.sha256(source_bytes).hexdigest() != source_record["sha256"]:
            raise ValueError("bundle bytes differ from the completed formal integrity manifest")
        bundle = json.loads(source_bytes)
        if bundle["schema"] != "eab.t2d.finite-bundle/1":
            raise ValueError("unexpected bundle schema")
        if (bundle["N"], bundle["element"], bundle["kind"]) != (row["N"], row["element"], row["kind"]):
            raise ValueError("manifest and bundle identities disagree")
        if not bundle["expected"]["production"]["valid"] or not bundle["expected"]["independent"]["valid"]:
            raise ValueError("unaccepted bundle cannot become a positive replay fixture")
        payload = {"id": identity, **{key: value for key, value in bundle.items() if not key.endswith("_diagnostic_only")}}
        if payload["expected"] != bundle["expected"]:
            raise AssertionError("full verifier returns must not be filtered")
        decoded = encode(payload)
        packed = gzip.compress(decoded, compresslevel=9, mtime=0)
        if len(packed) > 1_000_000:
            raise ValueError("one tracked compressed fixture exceeds 1 MB")
        filename = "case_"+str(number+1).zfill(2)+".json.gz"
        (destination / filename).write_bytes(packed)
        if gzip.decompress((destination / filename).read_bytes()) != decoded:
            raise AssertionError("written frozen fixture did not round-trip")
        rows.append({"id": identity, "N": row["N"], "element": row["element"],
                     "kind": row["kind"], "k": row["k"], "file": filename,
                     "bytes": len(packed), "sha256": hashlib.sha256(packed).hexdigest(),
                     "decoded_bytes": len(decoded), "decoded_sha256": hashlib.sha256(decoded).hexdigest(),
                     "source_bundle": row["bundle"], "source_bundle_sha256": hashlib.sha256(source_bytes).hexdigest()})
    source_path = source_run / "source_manifest.json"
    source = read_json(source_path)
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_files["source_manifest.json"]["sha256"]:
        raise ValueError("producer source manifest changed after formal completion")
    index = {
        "schema": "eab.t2d.fixed-replay/1", "freezer_tool_version": TOOL_VERSION,
        "producer": {"source_commit": source["source_commit"], "tool_version": source["tool_version"],
                     "source_manifest_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
                     "evidence_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                     "origin": str(source_run)},
        "direct_algebraic_instance_verification": False,
        "timing_exclusions": ["wall-clock diagnostic timings only"],
        "cases": rows,
        "complete_case_ledger": [{key: value for key, value in row.items() if not key.endswith("_diagnostic_only")}
                                 for row in manifest["cases"]],
    }
    encoded_index = encode(index)
    if len(encoded_index)+sum(row["bytes"] for row in rows) > 5_000_000:
        raise ValueError("frozen subset exceeds the work-order aggregate budget")
    (destination / "index.json").write_bytes(encoded_index)
    if read_json(destination / "index.json") != index:
        raise AssertionError("written index did not round-trip")
    return {"status": "FROZEN_FORMAL_SUBSET", "cases": len(rows), "compressed_bytes": sum(row["bytes"] for row in rows),
            "index_bytes": len(encoded_index), "destination": str(destination)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(freeze(args.source_run, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
