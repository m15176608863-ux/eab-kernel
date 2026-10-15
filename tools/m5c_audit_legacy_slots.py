"""Independent full-history tuple7 audit; no sibling runtime or geometry import.

Source contract checked read-only against D:/b-DDA/df/df.c:
1605-1617: VE m4/m5 are lock-length hints when m6=0.
1626-1649: VE common-edge alternatives fill m4-m6 and have m6>0.
1660-1681: VV carries a second full vertex-edge reference.
1832-1853: df06 can swap the complete primary and common-edge triples.
The frozen source reference is evidence, not a runtime dependency.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M5b_evidence"
PHASES = ("raw_df05", "post_df06")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(check_production=False):
    before = {p.relative_to(ROOT).as_posix(): digest(p)
              for folder in ("endpoint_inputs", "legacy_inputs")
              for p in (EVIDENCE / folder).iterdir() if p.is_file()}
    frames = defaultdict(list)
    manifest = json.loads((EVIDENCE / "endpoint_inputs/manifest.json").read_text(encoding="utf-8"))
    for part in manifest["shards"]:
        file = EVIDENCE / "endpoint_inputs" / part["file"]
        assert digest(file) == part["sha256"]
        for line in gzip.decompress(file.read_bytes()).decode().splitlines():
            row = json.loads(line)
            frames[row["case"], row["step"]].append(row)
    legacy = json.loads((EVIDENCE / "legacy_inputs/manifest.json").read_text(encoding="utf-8"))
    observed = None
    if check_production:
        sys.path.insert(0, str(ROOT / "tools"))
        import m5b_robust_replay
        observed = m5b_robust_replay.canonical_legacy_rows
    counts, by_case, mismatches = Counter(), {}, []
    for case, entry in legacy["cases"].items():
        file = EVIDENCE / "legacy_inputs" / (case+".jsonl.gz")
        assert digest(file) == entry["sha256"]
        local = Counter()
        for line in gzip.decompress(file.read_bytes()).decode().splitlines():
            frame = json.loads(line)
            blocks = frames[case, frame["step"]]
            periods, owners, adjacent = {}, {}, set()
            for block in blocks:
                ids = block["vertex_ids"]
                assert ids == list(range(min(ids), max(ids)+1))
                # Independent periodic-index construction, not production zip
                # of the last two aliases. No geometry primitive is used.
                for k in range(len(ids)+2):
                    vertex = ids[0]+k
                    assert vertex not in owners
                    owners[vertex] = block["block"]
                    periods[vertex] = ids[k % len(ids)]
                adjacent.update(tuple(sorted((v, ids[(k+1) % len(ids)]))) for k, v in enumerate(ids))
            for phase in PHASES:
                decoded = observed(frame[phase], blocks) if observed else [None]*len(frame[phase])
                for row, actual in zip(frame[phase], decoded):
                    raw = row["raw"]
                    primary = ("VE", periods[raw[1]], *sorted((periods[raw[2]], periods[raw[3]])))
                    assert primary == tuple(row["primary"]) and primary[2:] in adjacent
                    assert sorted((owners[raw[1]], owners[raw[2]])) == row["pair"]
                    assert owners[raw[2]] == owners[raw[3]] != owners[raw[1]]
                    local[phase+":primary"] += 1
                    local[phase+":mtype="+str(raw[0])] += 1
                    if raw[4] > 0 and raw[6] == 0:
                        local[phase+":false_secondary_with_old_m4_guard"] += 1
                    secondary = shared = None
                    present = raw[0] == 1 and raw[4] > 0 or raw[0] == 0 and raw[6] > 0
                    if present:
                        slot = ("VE", periods[raw[4]], *sorted((periods[raw[5]], periods[raw[6]])))
                        valid = (slot[2] != slot[3] and slot[2:] in adjacent
                                 and owners[raw[5]] == owners[raw[6]] != owners[raw[4]]
                                 and sorted((owners[raw[4]], owners[raw[5]])) == row["pair"])
                        if not valid:
                            mismatches.append(dict(case=case, step=frame["step"], phase=phase, raw=raw))
                        if raw[0] == 1:
                            secondary = slot
                        else:
                            shared = slot
                        local[phase+":secondary"] += 1
                        local[phase+(":VV_SECONDARY" if raw[0] == 1 else ":VALID_SHARED_EDGE_SLOT")] += 1
                        local[phase+":secondary_alias_slots"] += sum(raw[k] != periods[raw[k]] for k in (4, 5, 6))
                    if actual is not None:
                        assert actual["secondary"] == secondary and actual["shared_edge"] == shared
                local["steps"] = entry["steps"]
        by_case[case] = dict(local)
        counts.update(local)
    assert all(digest(ROOT / name) == value for name, value in before.items())
    assert not mismatches and len(frames) == 1810
    return dict(schema="eab.m5c-independent-legacy-slot-audit.v1", complete=True,
                counts=dict(counts), by_case=by_case, endpoint_frames=len(frames),
                block_frames=sum(map(len, frames.values())), mismatches=mismatches,
                production_crosschecked=check_production, input_hashes=before,
                audit_script_sha256=digest(__file__),
                oracle="Independent periodic padded-ID map and literal tuple7 slot contract; no production geometry or alias helper for expected values",
                sibling_source_reference=dict(path="D:/b-DDA/df/df.c", runtime_dependency=False,
                    sha256="a097a636990aee34cd0c2f856aa52a81c12e9ba9136f233004719be91158fcee",
                    source_lines=[[1605, 1617], [1626, 1649], [1660, 1681], [1832, 1853]]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-production", action="store_true")
    parser.add_argument("--output", default="reports/codex/M5c_evidence/a5_independent_legacy_audit.json")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT):
        raise ValueError("audit output must stay within this worktree")
    result = audit(args.check_production)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="")
    print(json.dumps(dict(complete=result["complete"], counts=result["counts"], mismatches=len(result["mismatches"]))))


if __name__ == "__main__":
    main()
