"""Inventory all R12 outputs (including temporary artifacts) with clickable URIs."""
import datetime
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
manifest = HERE / "artifact_manifest.json"
outside = ["README.md", "docs/canon_map.md", "docs/r12fix_design_sync.md",
           "tests/test_r9fix_construction_static.py", "tests/test_r10_static_construction.py",
           "tests/test_r11fix_static_flow.py", "tests/test_r12fix_static_closed.py",
           "tools/check_exact_construction.py", "tools/exact_construction_subset.py",
           "tools/exact_construction_policy.json", "reports/codex/R12FIX_report.md"]


def write_manifest():
    files = sorted({*(ROOT / p for p in outside), *(p for p in HERE.rglob("*") if p.is_file() and p != manifest)})
    rows = [{"path": p.relative_to(ROOT).as_posix(), "uri": p.as_uri(), "bytes": p.stat().st_size,
             "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
             "temporary": HERE / "tmp" in p.parents} for p in files]
    dirs = [HERE, *(p for p in HERE.rglob("*") if p.is_dir())]
    data = {"generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "self_hash_omitted": True, "files": rows,
            "directories": [{"path": p.relative_to(ROOT).as_posix(), "uri": p.as_uri() + "/"} for p in sorted(dirs)],
            "note": "Temporary copies are not production or fixture originals. Historical candidate scans are not final policy."}
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


data = write_manifest()
missing = []
for file in (ROOT / "reports/codex/R12FIX_report.md", HERE / "ARTIFACT_INDEX.md"):
    text = file.read_text(encoding="utf-8")
    for uri in re.findall(r"\]\((file:///[^)]+)\)", text):
        path = Path(unquote(urlparse(uri).path).lstrip("/"))
        if not path.exists():
            missing.append({"document": file.relative_to(ROOT).as_posix(), "uri": uri})
report = (ROOT / "reports/codex/R12FIX_report.md").read_text(encoding="utf-8")
checks = {"final_report_ends_done": report.rstrip().splitlines()[-1] == "R12FIX_DONE",
          "report_and_index_file_links_exist": not missing,
          "no_pending_draft_sentence": "等待最终policy" not in report and "待填入最终" not in report,
          "all_manifest_files_exist": all((ROOT / row["path"]).is_file() for row in data["files"])}
(HERE / "final_report_checks.json").write_text(json.dumps({"checks": checks, "missing": missing}, indent=2), encoding="utf-8")
data = write_manifest()
assert all(checks.values()), checks
print(json.dumps({"checks": checks, "files": len(data["files"]), "directories": len(data["directories"])}))
