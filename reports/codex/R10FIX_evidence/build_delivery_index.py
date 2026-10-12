"""Index scoped deliverables and hash the final code/tests/docs/evidence."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
INDEX = ROOT / "reports/codex/R10FIX_DELIVERY_INDEX.md"

changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).splitlines()
new = ["docs/r10fix_design_sync.md", "reports/codex/R10FIX_report.md"]
new += [str(p.relative_to(ROOT)).replace("\\", "/") for p in sorted((ROOT / "tests").glob("test_r10_*.py"))]
(HERE / "tracked_changes.patch").write_bytes(subprocess.check_output(["git", "diff", "--binary"], cwd=ROOT))
artifacts = sorted(set(changed+new))
lines = ["# R10FIX Delivery Index", "", "## Code, tests, docs and report", ""]
for name in artifacts:
    lines.append(f"- [{name}]({(ROOT / name).as_uri()})")
lines += ["", "## Evidence (individual files)", ""]
evidence = sorted(p for p in HERE.iterdir() if p.is_file() and p.name != "delivery_manifest.json")
for path in evidence:
    lines.append(f"- [{path.name}]({path.as_uri()})")
lines += ["", "## Directories", "",
          f"- [Evidence directory]({HERE.as_uri()}/)",
          f"- [Baseline rollback copies]({(HERE / 'baseline').as_uri()}/)",
          f"- [Local pytest temporary output]({(HERE / 'tmp').as_uri()}/)",
          f"- [SHA-256 manifest]({(HERE / 'delivery_manifest.json').as_uri()})", ""]
INDEX.write_text("\n".join(lines), encoding="utf-8")
paths = [ROOT / name for name in artifacts] + evidence + [INDEX]
rows = [{"path": str(p.relative_to(ROOT)).replace("\\", "/"), "bytes": p.stat().st_size,
         "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
(HERE / "delivery_manifest.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Indexed {len(artifacts)} code/test/doc/report files and {len(evidence)} evidence files")
