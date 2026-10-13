"""Validate frozen M4b byte-evidence structure without any sibling executable.

This checks recorded hashes/coverage, not a rerun or proof of the capture process.
Live reproduction uses b-DDA tools/bdda/verify_m4b_shadow.py and retained binaries.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

FAMILY_STEPS = {"52": 50, "12": 100, "50": 50, "51": 50, "03": 100,
                "05": 100, "06": 100, "09": 100, "10": 100, "v01": 100,
                "v01/v01a": 400, "v02": 100, "v02/v02a": 400, "F038": 30, "S038": 30}
ARTIFACTS = {"out.csv", "state.csv", "force.csv", "geom.csv", "stdout.txt", "stderr.txt"}


def validate(matrix):
    assert matrix["schema"] == "m4b-byte-matrix-v1", "byte matrix schema"
    assert matrix["baseline_head"] == "cbf3642e31a3d68790fb62446da185b55ee70e63", "baseline commit"
    for name in ("baseline_exe_sha256", "modified_exe_sha256", "source_manifest_sha256", "source_snapshot_sha256"):
        assert re.fullmatch("[0-9a-f]{64}", matrix[name]), "evidence hash format"
    assert matrix["baseline_exe_sha256"] != matrix["modified_exe_sha256"], "unchanged executable cannot evidence the switch"
    assert set(matrix["artifacts"]) == ARTIFACTS, "artifact coverage"
    assert matrix["excluded_artifacts"] == [], "no empirically justified exclusion in this capture"
    assert matrix["environment"]["BDDA_MAXX"] == "2560", "screen contract"
    assert matrix["environment"]["BDDA_MAXY"] == "1355", "screen contract"
    cases = matrix["cases"]
    assert len(cases) == 15 and {c["case"] for c in cases} == set(FAMILY_STEPS), "family coverage"
    for case in cases:
        name, n = case["case"], case["steps"]
        assert n == FAMILY_STEPS[name], "default horizon coverage"
        assert len(case["baseline"]) == 2, "baseline repeatability coverage"
        assert set(case["modified"]) == {"unset", "legacy", "shadow"}, "mode coverage"
        baseline = case["baseline"][0]["artifacts"]
        assert len(case["inputs"]) == 2, "bb/db input coverage"
        for h in case["inputs"].values():
            assert re.fullmatch("[0-9a-f]{64}", h), "input hash format"
        runs = case["baseline"] + list(case["modified"].values())
        for run in runs:
            assert run["case"] == name and run["steps"] == n, "run identity/horizon"
            assert run["returncode"] == 0, "physical run failed"
            assert run["inputs"] == case["inputs"], "input bytes changed"
            assert set(run["artifacts"]) == ARTIFACTS, "run artifact coverage"
            for artifact, entry in run["artifacts"].items():
                assert type(entry["bytes"]) is int and entry["bytes"] >= 0, "artifact length"
                assert re.fullmatch("[0-9a-f]{64}", entry["sha256"]), "artifact hash format"
                assert entry == baseline[artifact], f"byte equality: {name}/{run['mode']}/{artifact}"
        for mode, run in case["modified"].items():
            assert run["mode"] == mode, "mode label mismatch"
            if mode == "shadow":
                shadow = run["shadow"]
                assert shadow["steps"] == list(range(1, n + 1)), "shadow step coverage"
                assert shadow["end"] == {"kind": "end", "completed_steps": n, "status": "ok"}, "shadow completion"
                assert re.fullmatch("[0-9a-f]{64}", shadow["sha256"]), "snapshot hash format"
            else:
                assert not run.get("shadow"), "shadow file in legacy mode"
    return {"audit": "GREEN", "cases": 15, "steps_per_mode": sum(FAMILY_STEPS.values()),
            "modes": 3, "physical_artifacts": 4, "all_artifacts_including_logs": 6,
            "scope": "frozen evidence consistency; not a live solver rerun"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(json.loads(args.matrix.read_text(encoding="utf-8"))), ensure_ascii=False))


if __name__ == "__main__":
    main()
