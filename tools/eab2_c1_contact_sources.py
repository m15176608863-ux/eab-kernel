"""Compare C1 original t=0 associations with archived T1a ContactSet2 sources.

No mechanics/LP is recomputed. Every formal/coverage assembly record is read
from its checked-in gzip fixture, checked against both stored hashes, and its
original vertex/body IDs are applied to the C++ geometric source records.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import sys
import time

from eab2_c1_cases import ROOT, from_bits
sys.path.insert(0, str(ROOT / "src"))
from eab2_c1_local import contact_set_source
from eab2_diff_c1 import Dll, write_json


def immutable(value):
    return tuple(map(immutable, value)) if isinstance(value, list) else value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("use a new output name; evidence is immutable")
    directory = ROOT / "fixtures/eab2_cases/tia2d-2/formal_20261019_02/binary64"
    index = json.loads((directory / "gzip_index.json").read_text(encoding="utf-8"))
    report = {"schema": "eab2.c1.contact_sources.v1", "status": "RUNNING", "complete": False,
              "records": [], "mismatches": [], "state_counts": Counter(),
              "fixture_fragments_verified": 0, "unique_ordered_pairs": 0, "raw_sources_checked": 0,
              "scope": "Original raw associations/point provenance only; no C3 constraints, cone reachability or LP claim."}
    dll = Dll(args.dll)
    report["dll_sha256"] = hashlib.sha256(args.dll.read_bytes()).hexdigest()
    report["build_identity"] = dll.identity
    cache = {}
    started = time.perf_counter()
    def query(ba, bb):
        key = immutable([ba["vertices_xy_bits"], bb["vertices_xy_bits"]])
        if key not in cache:
            a = b = entrance = None
            try:
                a, b = [dll.body(tuple(tuple(from_bits(v) for v in p) for p in body["vertices_xy_bits"])) for body in (ba, bb)]
                entrance = dll.entrance(a, b)
                cache[key] = dll.export(entrance, local=True)
                assert not cache[key]["global_subdivision_materialized"]
            finally:
                if entrance is not None:
                    dll.check(dll.entrance2_destroy(dll.context, entrance), "entrance2_destroy")
                for body in (b, a):
                    if body is not None:
                        dll.check(dll.body2_destroy(dll.context, body), "body2_destroy")
        return cache[key]
    try:
        for item in index["files"]:
            packed = (directory / item["gz_path"]).read_bytes()
            assert hashlib.sha256(packed).hexdigest() == item["gz_sha256"]
            raw = gzip.decompress(packed)
            assert hashlib.sha256(raw).hexdigest() == item["sha256"]
            report["fixture_fragments_verified"] += 1
            doc = json.loads(raw)
            for q in doc.get("queries", []):
                if q["kind"] != "assembly":
                    continue
                bodies = {body["body_id"]: body for body in doc["assembly"]["bodies"]}
                adjacency = doc["assembly"]["adjacency"]
                if adjacency is None:
                    adjacency = list(combinations(bodies, 2))
                result = q["result"]
                got_sources, got_points = set(), set()
                states = {}
                try:
                    for left, right in set(map(tuple, adjacency)):
                        ba, bb = bodies[left], bodies[right]
                        local = query(ba, bb)
                        state = ("OUTSIDE", "CONTACT", "OVERLAP")[local["body_state"]+1]
                        states[left, right] = state
                        report["state_counts"][state] += 1
                        if state != "CONTACT":
                            continue
                        for row in local["raw_sources"]:
                            source = contact_set_source(row, left, right)
                            # Body descriptors use original positional IDs. The
                            # fixture may additionally name those original IDs.
                            ia, ib = ba["vertex_ids"], bb["vertex_ids"]
                            kind, _, a_feature, _, b_feature = source
                            source = (kind, left, ia[a_feature] if kind == "VE" else tuple(ia[i] for i in a_feature),
                                      right, ib[b_feature] if kind == "EV" else tuple(ib[i] for i in b_feature))
                            got_sources.add(source)
                            got_points.add((tuple(row["point"]), source))
                    for left, right, state in result["pair_states"]:
                        actual = states.get((left, right), states.get((right, left)))
                        assert actual == state, ("frozen pair state", left, right, actual, state)
                    expected = set(map(immutable, result["raw_sources"]))
                    expected_points = {(tuple(p["point"]), immutable(source)) for p in result["points"] for source in p["sources"]}
                    illegal_overlap = result["mathematical_status"] == "OVERLAP"
                    if illegal_overlap:
                        assert "OVERLAP" in states.values() and not expected and not expected_points
                    else:
                        assert got_sources == expected, ("frozen raw sources", sorted(expected-got_sources)[:2], sorted(got_sources-expected)[:2])
                        assert got_points == expected_points, "frozen physical contact points/source incidences"
                    report["raw_sources_checked"] += len(expected)
                    report["records"].append({"case_id": doc["case_id"], "fragment": item["gz_path"],
                        "pair_count": len(states), "raw_sources": len(expected),
                        "point_source_incidences": len(expected_points), "overlap_rejection_checked": illegal_overlap,
                        "status": "PASS"})
                except Exception as error:
                    report["mismatches"].append({"case_id": doc["case_id"], "reason": repr(error), "fragment": item["gz_path"]})
                    raise
            report["unique_ordered_pairs"] = len(cache)
            write_json(args.output, report)
    finally:
        dll.close()
        report["seconds"] = time.perf_counter()-started
        report["complete"] = not report["mismatches"] and report["fixture_fragments_verified"] == len(index["files"])
        report["status"] = "PASS" if report["complete"] else "FAIL"
        write_json(args.output, report)
    print(f"EAB2_C1_CONTACT_SOURCES records={len(report['records'])} pairs={len(cache)} raw_sources={report['raw_sources_checked']} mismatches={len(report['mismatches'])} status={report['status']}")
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
