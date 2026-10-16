"""B5-B7 literal-slot audit, with no production imports or geometric helpers.

Imports: argparse, collections, fractions, gzip, hashlib, json, pathlib.
The first features/certification flags are frozen observations, NOT recomputed
oracles. Slot matching is independently reconstructed from immutable inputs;
the geometric structure check uses only rational vector determinants/dots.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from fractions import Fraction as F
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/codex/M5d_evidence"
INPUTS = ROOT / "reports/codex/M5b_evidence"
PHASES = ("raw_df05", "post_df06")
SOURCE_REFERENCES = {
    "D:/b-DDA/df/df.c": [(894, 902), (1605, 1681), (1832, 1853), (1935, 1949), (3215, 3238)],
    "D:/b-DDA/bdda2/io/case_data.hpp": [(97, 105), (113, 118)],
    "D:/b-DDA/bdda2/detect/classify.hpp": [(66, 106)],
    "D:/b-DDA/bdda2/stepper/transfer.hpp": [(118, 125), (137, 144), (148, 174)],
    "D:/b-DDA/bdda2/driver/run.hpp": [(414, 430), (438, 460)],
    "D:/b-DDA/bdda2/core/contacts.hpp": [(67, 82)],
    "D:/b-DDA/bdda2/stepper/step_system.hpp": [(167, 209)],
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def decode(rows, blocks):
    """Literal periodic-index oracle; never calls production alias helpers."""
    aliases = {v: ids[(v-ids[0]) % len(ids)]
               for block in blocks for ids in (block["vertex_ids"],)
               for v in range(ids[0], ids[-1]+3)}
    result = []
    for row in rows:
        raw = row["raw"]
        def slot(start):
            return ("VE", aliases[raw[start]],
                    *sorted((aliases[raw[start+1]], aliases[raw[start+2]])))
        item = dict(raw=raw, primary=slot(1), secondary=None, shared_edge=None)
        assert item["primary"] == tuple(row["primary"])
        if raw[0] == 1:
            assert all(v >= 1 for v in raw[1:]), "raw VV real references must be positive"
            item["secondary"] = slot(4)
        elif raw[6] > 0:
            item["shared_edge"] = slot(4)
        result.append(item)
    return result


def reference_hits(features, rows):
    first = set(map(tuple, features))
    primary = {r["primary"] for r in rows}
    secondary = {r["secondary"] for r in rows if r["secondary"]}
    shared = {r["shared_edge"] for r in rows if r["shared_edge"]}
    return dict(primary=bool(first & primary), vv_second=bool(first & secondary),
                common_slot=bool(first & shared), formal_all=bool(first & (primary | secondary)),
                all_slots=bool(first & (primary | secondary | shared)), missing_pair=not rows,
                primary_rows=len(rows), vv_second_rows=sum(bool(r["secondary"]) for r in rows),
                common_slot_rows=sum(bool(r["shared_edge"]) for r in rows))


def parallel_measure(rows, blocks):
    """Squared sine of two supporting edge directions, exact and unit-free.

If both primaries name the same supporting edge, the opposite edge joins their
two vertices. Otherwise the two primary edge directions are the supports.
Only two VE rows are admitted; no claim is made about arbitrary contact sets.
"""
    assert len(rows) == 2 and all(r["raw"][0] == 0 for r in rows)
    points = {v: tuple(map(F, p)) for b in blocks for v, p in zip(b["vertex_ids"], b["start"])}
    first, second = [r["primary"] for r in rows]
    edges = [first[2:], second[2:]]
    if edges[0] == edges[1]:
        edges[1] = (first[1], second[1])
    vectors = [tuple(points[q][k]-points[p][k] for k in (0, 1)) for p, q in edges]
    u, v = vectors
    denom = sum(t*t for t in u)*sum(t*t for t in v)
    assert denom > 0
    return (u[0]*v[1]-u[1]*v[0])**2 / denom


def audit():
    bindings = {}
    def read(path):
        bindings[path.relative_to(ROOT).as_posix()] = digest(path)
        return json.loads(path.read_text(encoding="utf-8"))
    candidates = read(ROOT / "reports/codex/M5c_evidence/research_diagnostics.json")
    needed = {(r["case"], r["step"]) for r in candidates}
    blocks, legacy = defaultdict(list), {}
    manifest = read(INPUTS / "endpoint_inputs/manifest.json")
    for shard in manifest["shards"]:
        path = INPUTS / "endpoint_inputs" / shard["file"]
        assert digest(path) == shard["sha256"]
        bindings[path.relative_to(ROOT).as_posix()] = digest(path)
        for line in gzip.decompress(path.read_bytes()).decode("utf-8").splitlines():
            row = json.loads(line)
            if (row["case"], row["step"]) in needed:
                blocks[row["case"], row["step"]].append(row)
    manifest = read(INPUTS / "legacy_inputs/manifest.json")
    for case, info in manifest["cases"].items():
        path = INPUTS / "legacy_inputs" / (case+".jsonl.gz")
        assert digest(path) == info["sha256"]
        bindings[path.relative_to(ROOT).as_posix()] = digest(path)
        for line in gzip.decompress(path.read_bytes()).decode("utf-8").splitlines():
            row = json.loads(line)
            if (case, row["step"]) in needed:
                legacy[case, row["step"]] = row
    result, counts, groups = [], defaultdict(Counter), defaultdict(list)
    for candidate in candidates:
        key = candidate["case"], candidate["step"]
        block_pair = [r for r in blocks[key] if r["block"] in candidate["pair"]]
        row = {k: candidate[k] for k in ("case", "step", "pair", "features", "certified_union")}
        row["canonical_ring_ids"] = [b["vertex_ids"] for b in block_pair]
        row["interpretation"] = "CERTIFIED_TUBE" if row["certified_union"] else "NOMINAL_ONLY_UNCERTIFIED_NO_CONCLUSION"
        row["phases"] = {}
        category = "certified" if row["certified_union"] else "nominal_unproved"
        for phase in PHASES:
            raw = [r for r in legacy[key][phase] if r["pair"] == row["pair"]]
            decoded = decode(raw, block_pair)
            hits = reference_hits(row["features"], decoded)
            row["phases"][phase] = dict(hits=hits, rows=decoded)
            counts[category+":"+phase].update(hits)
            if row["certified_union"]:
                measure = parallel_measure(decoded, block_pair)
                assert measure < F(1, 300), "certified two-row supports must be near parallel"
                row["phases"][phase]["sin_squared"] = str(measure)
                row["phases"][phase]["sin_squared_display"] = float(measure)
        if row["certified_union"]:
            identity = (row["case"], tuple(row["pair"]), tuple(map(tuple, row["features"])))
            groups[identity].append(row["step"])
        result.append(row)
    assert len(result) == 68 and sum(r["certified_union"] for r in result) == 19
    assert all(digest(ROOT / name) == value for name, value in bindings.items())
    return dict(schema="eab.m5d-wording-audit.v1", complete=True,
                counts={k: dict(v) for k, v in counts.items()},
                certified_pairs=19, nominal_unproved_pairs=49,
                configuration_rule="(case, unordered block pair, canonical first feature set); ignore step only; no cross-case merging",
                configuration_limit="17 topological feature identities, not statistically independent observations or exact shape-equivalence classes",
                unique_configurations=len(groups),
                configurations=[dict(case=k[0], pair=k[1], features=k[2], steps=v) for k, v in groups.items()],
                rows=result, input_hashes=bindings, script_sha256=digest(__file__),
                oracle_imports=["argparse", "collections", "fractions", "gzip", "hashlib", "json", "pathlib"],
                production_imports=[], geometric_primitives_shared=[],
                geometric_limit="Near-parallel is a descriptive exact sin-squared bound <1/300, not a certificate threshold")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/codex/M5d_evidence/b_wording_audit.json")
    parser.add_argument("--source-review", action="store_true", help="read-only sibling line/hash audit; never needed by pytest")
    args = parser.parse_args()
    path = (ROOT / args.output).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("output must stay in this worktree")
    value = audit()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    if args.source_review:
        sources = []
        for name, ranges in SOURCE_REFERENCES.items():
            source = Path(name)
            data = source.read_bytes()
            lines = data.decode("utf-8", errors="replace").splitlines()
            sources.append(dict(path=name, sha256=digest(source), bytes=len(data),
                                snippets=[dict(first=a, last=b, lines=[f"{i}: {lines[i-1]}" for i in range(a, b+1)])
                                          for a, b in ranges]))
            assert data == source.read_bytes(), "read-only source changed during inspection"
        target = path.with_name("b_legacy_source_review.json")
        target.write_text(json.dumps(dict(complete=True, read_only=True, runtime_dependency=False,
                                         sources=sources), ensure_ascii=False, indent=2)+"\n",
                          encoding="utf-8", newline="\n")
    print(json.dumps({k: value[k] for k in ("complete", "counts", "unique_configurations")}))


if __name__ == "__main__":
    main()
