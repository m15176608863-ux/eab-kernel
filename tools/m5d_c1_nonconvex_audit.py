"""Independent refinement of C1's nominal non-strict-convex rejection count.

No production imports. Exact all-edge/other-vertex determinants distinguish a
negative support-side violation from collinearity-only failures. Pair priority
is negative before zero when both kinds occur in its two rings. This audit
does not certify any previously refused pair or alter C1's sufficient domain.
"""
from collections import Counter
from fractions import Fraction as F
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M5d_evidence"
INPUTS = ROOT / "reports/codex/M5b_evidence/endpoint_inputs"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def category(points):
    ring = tuple(tuple(F(v) for v in p) for p in points)
    area = sum(p[0]*q[1]-p[1]*q[0] for p, q in zip(ring, ring[1:]+ring[:1]))
    if area < 0:
        ring = tuple(reversed(ring))
    zero = False
    for i, p in enumerate(ring):
        j = (i+1) % len(ring)
        q = ring[j]
        for k, other in enumerate(ring):
            if k in (i, j):
                continue
            determinant = (q[0]-p[0])*(other[1]-p[1])-(q[1]-p[1])*(other[0]-p[0])
            if determinant < 0:
                return "NEGATIVE_SUPPORT_SIDE"
            zero = zero or determinant == 0
    return "COLLINEAR_ONLY" if zero else "STRICTLY_CONVEX"


def main():
    summary_path = EVIDENCE / "c1_summary.json"
    summary_hash = sha(summary_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest = json.loads((INPUTS / "manifest.json").read_text(encoding="utf-8"))
    table, hashes = {}, {}
    for item in manifest["shards"]:
        path = INPUTS / item["file"]
        digest = sha(path)
        if digest != item["sha256"]:
            raise AssertionError("endpoint input manifest mismatch")
        hashes[path.relative_to(ROOT).as_posix()] = digest
        for line in gzip.decompress(path.read_bytes()).decode().splitlines():
            row = json.loads(line)
            table[(row["case"], row["step"], row["block"])] = category(row["start"])
    totals, cases = Counter(), {}
    for case in summary["cases"]:
        counts = Counter()
        raw = ROOT / summary["raw_directory"] / case / "pairs.jsonl.gz"
        if sha(raw) != summary["cases"][case]["raw_sha256"]:
            raise AssertionError("C1 raw archive mismatch")
        for line in gzip.decompress(raw.read_bytes()).decode().splitlines():
            row = json.loads(line)
            if row["result"].get("reason") != "RING_NOT_STRICTLY_CONVEX":
                continue
            kinds = [table[(case, row["step"], block)] for block in row["pair"]]
            kind = "NEGATIVE_SUPPORT_SIDE" if "NEGATIVE_SUPPORT_SIDE" in kinds else "COLLINEAR_ONLY"
            if kinds == ["STRICTLY_CONVEX", "STRICTLY_CONVEX"]:
                raise AssertionError("C1 non-strict rejection has no independent witness")
            counts[kind] += 1
        cases[case] = dict(counts)
        totals.update(counts)
    if sum(totals.values()) != 12387 or sha(summary_path) != summary_hash:
        raise AssertionError("C1 nominal-rejection audit coverage/source drift")
    result = dict(complete=True, summary_sha256=summary_hash, source_sha256=sha(Path(__file__)),
                  counts=dict(totals), cases=cases, input_hashes=hashes,
                  definitions={"NEGATIVE_SUPPORT_SIDE": "At least one ring has an exact negative edge-other-vertex cross after CCW orientation",
                               "COLLINEAR_ONLY": "Neither ring has a negative cross; at least one has a zero edge-other-vertex cross"},
                  priority="negative before collinear at pair level; no new certification or global exit claim")
    (EVIDENCE / "c1_nonconvex_audit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    print("M5D_C1_NONCONVEX_AUDIT_COMPLETE", dict(totals))


if __name__ == "__main__":
    main()
