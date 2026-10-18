"""Run the unchanged 476c5d6 suite from a verified read-only Git byte export.

The H1 runner is unmodified. Only its source inventory and evidence destination
are supplied for this no-.git export; live edit drift is checked against the
immutable baseline export, not the concurrently repaired working tree.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "reports/codex/H1_evidence"
TEMP = EVIDENCE / "tmp/fix_baseline_export"
SOURCE = TEMP / "source"
COMMIT = "476c5d67bc52292640638fcb87a37e4176a5ae3b"

if "--prepare" in sys.argv:
    assert not TEMP.exists(), "baseline preparation is immutable"
    TEMP.mkdir(parents=True)
    archive = TEMP / "baseline.zip"
    with archive.open("wb") as stream:
        subprocess.run(["git", "archive", "--format=zip", COMMIT], cwd=ROOT,
                       stdout=stream, check=True)
    rows = []
    with zipfile.ZipFile(archive) as source:
        for member in source.infolist():
            if member.is_dir() or member.filename.startswith("reports/codex/H1_evidence/"):
                continue
            target = SOURCE / member.filename
            assert target.resolve().is_relative_to(SOURCE.resolve())
            data = source.read(member)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            rows.append(dict(path=member.filename, bytes=len(data),
                             sha256=hashlib.sha256(data).hexdigest()))
    (TEMP / "manifest.json").write_text(json.dumps(rows, indent=2)+"\n", encoding="utf-8")
    (EVIDENCE / "fix_baseline_export.json").write_text(json.dumps(dict(
        commit=COMMIT, files=len(rows), archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        source=str(SOURCE), fresh_git_checkout=False, runner_modified=False,
        inventory_override="fixed verified archive members", evidence_override=str(EVIDENCE)), indent=2)+"\n", encoding="utf-8")
    print("BASELINE_EXPORT_READY", len(rows), flush=True)
else:
    rows = json.loads((TEMP / "manifest.json").read_text("utf-8"))
    assert all(hashlib.sha256((SOURCE/r["path"]).read_bytes()).hexdigest() == r["sha256"] for r in rows)
    sys.path.insert(0, str(SOURCE / "tools"))
    import h1_run_gates as runner
    runner.EVIDENCE = EVIDENCE
    runner.source_names = lambda: sorted(r["path"] for r in rows)
    sys.argv = [str(SOURCE / "tools/h1_run_gates.py"), "--name", "fix_baseline", "--runslow"]
    raise SystemExit(runner.main())
