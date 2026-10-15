"""Distinguish a conservative R3 failure from a concrete initial-tube witness.

The search is deliberately finite and incomplete: eight allowed rigid offsets.
A witness of contact at s=0 disproves a uniformly-separated initial state for
the unanchored constant-radius tube. No witness is NOT proof of robustness.
It does not contradict the anchored P1/P2/P3 families, which share s=0 exactly.
"""
from collections import Counter
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path

import m5c_diagnostics as research
from eab.kernel2d.g0_oracle import overlap


def _convexity(points):
    values = []
    for j, p in enumerate(points):
        q = points[(j+1) % len(points)]
        for k, r in enumerate(points):
            if k not in (j, (j+1) % len(points)):
                values.append((q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0]))
    least = min(values)
    return "concave" if least < 0 else "collinear_convex" if least == 0 else "strict_convex"


def main():
    target = research.EVIDENCE / "research_initial_tube_witnesses.json"
    if target.exists():
        raise ValueError("refuse to overwrite frozen witness evidence")
    sources, inputs = research._sources(), research.replay.input_hashes()
    paths = [research.EVIDENCE / name for name in ("research_summary.json", "research_diagnostics.json")]
    inherited = {p.relative_to(research.ROOT).as_posix(): research._sha(p) for p in paths}
    summary, rows = (json.loads(path.read_text(encoding="utf-8")) for path in paths)
    assert summary["complete"] and len(rows) == 68
    wanted = {(r["case"], r["step"], block) for r in rows for block in r["pair"]}
    blocks = {(r["case"], r["step"], r["block"]): research.replay.prepare(r)
              for r in research.replay.endpoint.iter_inputs()
              if (r["case"], r["step"], r["block"]) in wanted}
    counts, results = Counter(), []
    for row in rows:
        a, b = (blocks[(row["case"], row["step"], block)] for block in row["pair"])
        assert overlap(a["start"], b["start"]) == -1
        witness = None
        for sx, sy in product((-1, 0, 1), repeat=2):
            if sx == sy == 0:
                continue
            shift_a, shift_b = (-sx*a["radius"], -sy*a["radius"]), (sx*b["radius"], sy*b["radius"])
            aa = tuple((x+shift_a[0], y+shift_a[1]) for x, y in a["start"])
            bb = tuple((x+shift_b[0], y+shift_b[1]) for x, y in b["start"])
            state = overlap(aa, bb)
            counts["g0_trials"] += 1
            if state != -1:
                witness = dict(shift_a=shift_a, shift_b=shift_b, initial_state=state)
                break
        assert not row["certified_union"] or witness is None, "certified first-cover tube contains initial contact"
        convexity = (_convexity(a["start"]), _convexity(b["start"]))
        counts["pairs"] += 1
        counts["initial_contact_witness" if witness else "no_witness_in_eight_offsets"] += 1
        counts["nominal:"+"/".join(convexity)] += 1
        results.append(dict(case=row["case"], step=row["step"], pair=row["pair"],
                            certified_union=row["certified_union"], nominal_convexity=convexity,
                            witness=witness))
    after = research._sources()
    assert after == sources and research.replay.input_hashes() == inputs
    assert inherited == {name: research._sha(research.ROOT / name) for name in inherited}
    result = dict(complete=True, counts=counts, rows=results, source_hashes=sources, source_hashes_end=after,
                  input_hashes=inputs, inherited_hashes=inherited,
                  oracle_imports=["fractions.Fraction", "itertools.product", "eab.kernel2d.g0_oracle.overlap"],
                  independence="G0 ray/segment oracle is not imported by R3; nominal/radii preparation is shared input wiring, not oracle geometry",
                  scope="eight constant rigid offsets per pair at most; witnesses refute only the broad constant-radius unanchored tube, not the shared-initial-state P1/P2/P3 family",
                  certified_counterexamples=0)
    research._write(target, result)
    print("M5C_INITIAL_TUBE_WITNESSES_COMPLETE", dict(counts), flush=True)


if __name__ == "__main__":
    main()
