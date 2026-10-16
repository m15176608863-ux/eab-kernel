"""Freeze named semantic replay mutation kills, with no provenance tripwires."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/codex/M5d_evidence"
TMP = OUT / "tmp"


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TEMP=str(TMP), TMP=str(TMP), PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    junit = TMP / "replay_semantics.xml"
    command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider",
               "--basetemp", str(TMP / "replay_semantics_evidence"), "--junitxml", str(junit),
               "tests/test_m5d_replay_semantics.py"]
    result = subprocess.run(command, cwd=ROOT, env=env, text=True, encoding="utf-8", errors="replace", capture_output=True)
    log = OUT / "replay_semantics_pytest.txt"
    log.write_text(result.stdout+result.stderr, encoding="utf-8", newline="\n")
    assert result.returncode == 0, result.stdout+result.stderr
    cases = list(ET.parse(junit).getroot().iter("testcase"))
    assert cases and all(not any(child.tag in ("failure", "error", "skipped") for child in case) for case in cases)
    mutations = [case.attrib["name"] for case in cases if case.attrib["name"].startswith("test_internal")]
    assert len(mutations) == 6
    sources = ("tests/test_m5d_replay_semantics.py", "tests/mutation_support.py", "tools/m5b_robust_replay.py",
               "src/eab/kernel2d/model_robustness.py", "src/eab/kernel2d/dda_motion.py", "tools/m5d_replay_teeth_evidence.py")
    evidence = dict(complete=True, collected=len(cases), executed=len(cases), skip_count=0,
                    mutation_count=len(mutations), mutations=mutations, hash_tripwires_selected=False,
                    frozen_snapshot_tripwires_selected=False, oracle_imports=["fractions.Fraction", "math.comb"],
                    production_geometry_used_by_oracle=False,
                    mutation_policy="Actual internal source bodies, caught only by the matching named semantic AssertionError",
                    command=command, last_line=(result.stdout+result.stderr).splitlines()[-1],
                    call_seconds=sum(float(case.attrib["time"]) for case in cases),
                    tests=[case.attrib for case in cases],
                    sources={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources})
    (OUT / "replay_semantic_evidence.json").write_text(json.dumps(evidence, indent=2)+"\n", encoding="utf-8", newline="\n")
    print("M5D_REPLAY_SEMANTICS_GREEN", len(cases), "tests;", len(mutations), "named semantic kills")


if __name__ == "__main__":
    main()
