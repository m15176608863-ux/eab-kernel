"""Verify final Markdown links/readback; --manifest checks frozen artifact hashes."""
from pathlib import Path
import hashlib
import json
import re
import sys
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
if "--manifest" in sys.argv:
    manifest = json.loads((HERE / "delivery_manifest.json").read_text(encoding="utf-8"))
    bad = [name for name, row in manifest.items()
           if not (ROOT / name).is_file() or hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != row["sha256"]]
    print(json.dumps({"manifest_entries": len(manifest), "hash_mismatches": bad}, indent=2))
    raise SystemExit(bool(bad))

names = ["reports/codex/R11FIX_report.md", "reports/codex/R11FIX_DELIVERY_INDEX.md", "docs/r11fix_design_sync.md"]
links, missing = [], []
for name in names:
    path = ROOT / name
    text = path.read_text(encoding="utf-8")
    assert "\ufffd" not in text and "???" not in text, name
    for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
        parsed = urlparse(target)
        if parsed.scheme == "file":
            local = Path(unquote(parsed.path).lstrip("/"))
        elif not parsed.scheme:
            local = path.parent / unquote(parsed.path)
        else:
            continue
        links.append({"document": name, "target": target, "exists": local.exists()})
        if not local.exists():
            missing.append(links[-1])
report = (ROOT / names[0]).read_text(encoding="utf-8")
assert report.rstrip().splitlines()[-1] == "R11FIX_DONE"
assert "G6K-K01" in report and "G6K-K02" in report and "M4a" in report
result = {"documents": names, "local_links_checked": len(links), "missing_links": missing,
          "utf8_readback": True, "done_line": report.rstrip().splitlines()[-1], "passed": not missing}
(HERE / "artifact_qa.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(bool(missing))
