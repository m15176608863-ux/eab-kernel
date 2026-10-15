"""WO-M3c fresh-byte four-process suite; large raw records stay in ignored tmp.

The owner's no-worktree instruction takes precedence: this is a byte export,
not a new Git checkout. Never combine or resume interrupted suite evidence.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys

import m4c_run_gates as runner


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M3c_evidence"


def main():
    # Delegate export/collection/progress/dispatch to the already tested runner.
    # Its complete raw namespace is ignored, including >1 MB node inventories.
    name = sys.argv[sys.argv.index("--name") + 1]
    if Path(name).name != name or name in (".", ".."):
        raise ValueError("name must be a new single directory name")
    out = EVIDENCE / name
    out.mkdir(parents=True, exist_ok=False)
    runner.EVIDENCE = EVIDENCE / "tmp/suites"
    raw = runner.EVIDENCE / name
    runner.write_json(out / "run_state.json", dict(status="RUNNING", complete=False,
        raw_progress=str(raw), no_resume=True))
    code = runner.main()
    summary = json.loads((raw / "summary.json").read_text(encoding="utf-8"))
    phase_audit = []
    all_dispatched = []
    for i in range(1, 5):
        nodes = (raw / f"shard_{i}_nodes.txt").read_text(encoding="utf-8").splitlines()
        data = json.loads((raw / f"shard_{i}_execution.json").read_text(encoding="utf-8"))
        expected = Counter(nodes)
        phases = {p: Counter(r["nodeid"] for r in data["reports"] if r["when"] == p)
                  for p in ("setup", "call", "teardown")}
        passed = (expected == Counter(data["collected"])
                  and all(v == expected for v in phases.values())
                  and all(v == 1 for v in expected.values())
                  and all(r["outcome"] == "passed" for r in data["reports"])
                  and data["exitstatus"] == 0 and data["complete"])
        phase_audit.append(dict(shard=i, passed=passed, dispatched=len(nodes),
            phases={k: sum(v.values()) for k, v in phases.items()}))
        all_dispatched.extend(nodes)
        for suffix in ("json", "txt"):
            path = raw / f"shard_{i}.{suffix}"
            if path.stat().st_size <= 1_000_000:
                shutil.copyfile(path, out / path.name)
    summary["strict_phase_audit"] = phase_audit
    summary["strict_all_nodes_once"] = len(all_dispatched) == len(set(all_dispatched)) == summary["collected"]
    manifest = raw / "export_manifest.json"
    summary["export_manifest_sha256"] = hashlib.sha256(manifest.read_bytes()).hexdigest()
    summary["raw_records"] = str(raw)
    summary["audit"] = "GREEN" if (code == 0 and all(r["passed"] for r in phase_audit)
        and summary["strict_all_nodes_once"]) else "RED"
    shutil.copyfile(raw / "exact_construction.txt", out / "exact_construction.txt")
    runner.write_json(out / "summary.json", summary)
    runner.write_json(out / "run_state.json", dict(status=summary["audit"], complete=True,
        raw_progress=str(raw), no_resume=True))
    print("M3C_SUITE_" + summary["audit"], summary["collected"], "collected=executed; strict phases")
    return 0 if summary["audit"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
