"""Independent team review: supporting-line oracle and frozen-row recount.

Oracle geometry uses only Fraction, determinants and exhaustive half-plane
tests; it imports neither the production support construction nor its hull
oracle. Production import is solely the subject under adversarial test.
This is not the owner's independent G6 acceptance.
"""
from collections import Counter, defaultdict
from fractions import Fraction as F
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eab.kernel2d.m5d_exit_certificate import exit_order_certificate

OUT = ROOT / "reports/codex/M5d_evidence"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def supporting_line_oracle(a, b, x):
    points = sorted({(v[0]-u[0], v[1]-u[1]) for u in a for v in b})
    records = []
    for p in points:
        for q in points:
            if p == q:
                continue
            dx, dy = q[0]-p[0], q[1]-p[1]
            def det(z):
                return dx*(z[1]-p[1])-dy*(z[0]-p[0])
            signs = [det(z) for z in points]
            if min(signs) < 0:
                continue
            length = dx*dx+dy*dy
            # Keep maximal exposed segments, not subsegments of a common line.
            if any(sign == 0 and not 0 <= dx*(z[0]-p[0])+dy*(z[1]-p[1]) <= length
                   for z, sign in zip(points, signs)):
                continue
            projection = dx*(x[0]-p[0])+dy*(x[1]-p[1])
            squared = (sum((x[k]-p[k])**2 for k in (0, 1)) if projection < 0 else
                       sum((x[k]-q[k])**2 for k in (0, 1)) if projection > length else det(x)**2/length)
            labels = []
            for i, av in enumerate(a):
                for j, bv in enumerate(b):
                    if (bv[0]-av[0], bv[1]-av[1]) != p:
                        continue
                    ae, be = a[(i+1) % len(a)], b[(j+1) % len(b)]
                    if (be[0]-av[0], be[1]-av[1]) == q:
                        labels.append(("VE", i, j))
                    if (bv[0]-ae[0], bv[1]-ae[1]) == q:
                        labels.append(("EV", i, j))
            records.append((squared, labels, det(x) > 0))
    best = min(row[0] for row in records)
    return dict(inside=all(row[2] for row in records), distance2=best,
                labels=tuple(sorted(label for d, labels, _ in records if d == best for label in labels)),
                boundary_edges=len(records))


def adversarial():
    rng = random.Random(5279301)
    shapes = [
        (((0, 0), (4, 0), (0, 3)), ((1, 1), (5, 2), (2, 5))),
        (((-3, -1), (1, -2), (4, 1), (0, 3)),
         ((-2, -2), (2, -1), (3, 2), (F(-6, 5), 4))),
    ]
    nominal, probes = [], 0
    for index, (aa, bb) in enumerate(shapes):
        aa, bb = (tuple(tuple(map(F, p)) for p in ring) for ring in (aa, bb))
        x = (F(1, 7), F(-2, 9))
        base = exit_order_certificate(aa, bb, 0, 0, x)
        assert base["status"] == "CERTIFIED_UNIQUE_EXIT"
        for scale in (F(1, 10**12), F(1), F(10**12)):
            u = F(3+index, 11)
            c, s = (1-u*u)/(1+u*u), 2*u/(1+u*u)
            def transform(p, t):
                return t[0]+scale*(c*p[0]-s*p[1]), t[1]+scale*(s*p[0]+c*p[1])
            ta, tb = (F(10**6), F(-10**6)), (F(-10**5), F(1000))
            a, b = tuple(transform(p, ta) for p in aa), tuple(transform(p, tb) for p in bb)
            query = transform(x, (tb[0]-ta[0], tb[1]-ta[1]))
            lo, hi = F(0), scale
            assert exit_order_certificate(a, b, hi, 3*hi/7, query)["status"] == "UNPROVED"
            for _ in range(32):
                mid = (lo+hi)/2
                if exit_order_certificate(a, b, mid, 3*mid/7, query)["status"] == "CERTIFIED_UNIQUE_EXIT":
                    lo = mid
                else:
                    hi = mid
            for radius in (lo*(1-F(1, 2**24)), lo/2):
                signed = exit_order_certificate(a, b, radius, 3*radius/7, query)
                assert signed["status"] == "CERTIFIED_UNIQUE_EXIT"
                reference = supporting_line_oracle(a, b, query)
                assert signed["label"] == base["label"] and signed["distance2"] == base["distance2"]*scale*scale
                assert reference["distance2"] == signed["distance2"] and reference["labels"] == (signed["label"],)
                for trial in range(20):
                    def perturb(ring, r):
                        return tuple(tuple(v+r*(rng.choice((-1, 1)) if trial < 12 else F(rng.randrange(-127, 128), 127))
                                           for v in p) for p in ring)
                    result = supporting_line_oracle(perturb(a, radius), perturb(b, 3*radius/7), query)
                    assert result["inside"] and result["labels"] == (signed["label"],), "independent support-line C1 counterexample"
                    probes += 1
                # Cyclic reindexing must only permute the feature identity.
                shifted = exit_order_certificate(a[1:]+a[:1], b[1:]+b[:1], radius, 3*radius/7, query)
                tag, i, j = signed["label"]
                assert shifted["label"] == (tag, (i-1) % len(a), (j-1) % len(b))
                nominal.append(dict(shape=index, scale=str(scale), radius=str(radius), label=signed["label"]))
                (OUT / "tmp/review_c1_progress.json").write_text(json.dumps(dict(complete=False, checked=probes)), encoding="utf-8")
    return dict(seed=5279301, configurations=len(nominal), nonrigid_probes=probes,
                oracle="exhaustive Cartesian differences + all supporting halfplanes, no hull or support argmax",
                cases=nominal, mismatches=0)


def recount():
    summary_path = OUT / "c1_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    bundle = ROOT / "reports/codex/M5b_evidence"
    blocks = defaultdict(dict)
    manifest = json.loads((bundle / "endpoint_inputs/manifest.json").read_text(encoding="utf-8"))
    for shard in manifest["shards"]:
        file = bundle / "endpoint_inputs" / shard["file"]
        assert sha(file) == shard["sha256"]
        for line in gzip.open(file, "rt", encoding="utf-8"):
            row = json.loads(line)
            blocks[row["case"], row["step"]][row["block"]] = row
    counts, refs, unproved = Counter(), Counter(), Counter()
    nonconvex_shapes = {}
    rejected_with_negative_support = 0
    keys = set()
    for case, expected in summary["cases"].items():
        legacy = {r["step"]: r for r in (json.loads(line) for line in gzip.open(bundle / "legacy_inputs" / (case+".jsonl.gz"), "rt", encoding="utf-8"))}
        file = ROOT / summary["raw_directory"] / case / "pairs.jsonl.gz"
        assert sha(file) == expected["raw_sha256"]
        for line in gzip.open(file, "rt", encoding="utf-8"):
            row = json.loads(line)
            key = case, row["step"], tuple(row["pair"])
            assert key not in keys
            keys.add(key)
            outcome = row["result"]
            counts[outcome.get("reason", outcome["status"])] += 1
            pair = [blocks[case, row["step"]][v] for v in row["pair"]]
            maps, ids = {}, []
            pair_negative = False
            for block in pair:
                vertices = block["vertex_ids"]
                maps.update({v: vertices[(v-vertices[0]) % len(vertices)] for v in range(vertices[0], vertices[-1]+3)})
                points = [tuple(map(F, p)) for p in block["start"]]
                area = sum(p[0]*q[1]-p[1]*q[0] for p, q in zip(points, points[1:]+points[:1]))
                ids.append(vertices if area > 0 else list(reversed(vertices)))
                if outcome.get("reason") == "RING_NOT_STRICTLY_CONVEX":
                    shape_key = case, row["step"], block["block"]
                    if shape_key not in nonconvex_shapes:
                        ring = points if area > 0 else list(reversed(points))
                        nonconvex_shapes[shape_key] = any(
                            (q[0]-p[0])*(v[1]-p[1])-(q[1]-p[1])*(v[0]-p[0]) < 0
                            for p, q in zip(ring, ring[1:]+ring[:1]) for v in ring)
                    pair_negative |= nonconvex_shapes[shape_key]
            if outcome.get("reason") == "RING_NOT_STRICTLY_CONVEX":
                rejected_with_negative_support += pair_negative
            certified = outcome["status"] == "CERTIFIED_UNIQUE_EXIT"
            if certified:
                tag, i, j = outcome["label"]
                label = ("VE", ids[0][i], *sorted((ids[1][j], ids[1][(j+1) % len(ids[1])])) ) if tag == "VE" else (
                    "VE", ids[1][j], *sorted((ids[0][i], ids[0][(i+1) % len(ids[0])])) )
                assert label == tuple(row["global_label"]), "C1 global label differs from independently oriented IDs"
            for phase in ("raw_df05", "post_df06"):
                slots = defaultdict(list)
                for rawrow in legacy[row["step"]][phase]:
                    if rawrow["pair"] != row["pair"]:
                        continue
                    raw = rawrow["raw"]
                    def slot(k):
                        return ("VE", maps[raw[k]], *sorted((maps[raw[k+1]], maps[raw[k+2]])))
                    slots["primary"].append(slot(1))
                    if raw[0] == 1:
                        slots["secondary"].append(slot(4))
                    elif raw[6] > 0:
                        slots["shared_edge"].append(slot(4))
                all_slots = []
                for kind in ("primary", "secondary", "shared_edge"):
                    values = slots[kind]
                    key = phase+":"+kind
                    if certified:
                        refs[key+":total"] += len(values)
                        refs[key+":match"] += values.count(label)
                        refs[key+":other"] += len(values)-values.count(label)
                        refs[key+":pair_hit"] += label in values
                        all_slots.extend(values)
                    else:
                        unproved[key+":total"] += len(values)
                if certified:
                    refs[phase+":all_slots:pair_hit"] += label in all_slots
                    refs[phase+":all_slots:pair_miss"] += label not in all_slots
    assert len(keys) == 16676 and counts["CERTIFIED_UNIQUE_EXIT"] == 4280
    assert refs == summary["references"] and unproved == summary["unproved_references"]
    assert all(summary["counts"][k] == v for k, v in counts.items())
    assert rejected_with_negative_support == counts["RING_NOT_STRICTLY_CONVEX"]
    return dict(raw_pairs=len(keys), certified_global_labels_checked=4280, duplicate_keys=0,
                counts=dict(counts), references=dict(refs), unproved_references=dict(unproved),
                nonconvex_rejections_with_negative_support=rejected_with_negative_support,
                summary_sha256=sha(summary_path), mismatches=0)


def main():
    os.environ["TEMP"] = os.environ["TMP"] = str(OUT / "tmp")
    started = time.perf_counter()
    paths = [ROOT / name for name in ("src/eab/kernel2d/m5d_exit_certificate.py", "tools/m5d_c1_oracle.py",
             "tools/m5d_c1_replay.py", "docs/m5d_c1_theory.md", "tools/m5d_review_c1.py")]
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    result = dict(complete=False, reviewer="independent parallel team reviewer; NOT owner G6")
    result["recount"] = recount()
    result["adversarial"] = adversarial()
    assert all(sha(ROOT / p) == h for p, h in before.items()), "reviewed sources changed; rerun from scratch"
    result.update(complete=True, critical=0, major=0, source_hashes=before, seconds=time.perf_counter()-started,
                  residual_limits=["finite probes do not replace proof", "C1 covers a static initial neighborhood, not whole-step exit persistence",
                                   "refusals do not imply instability", "external owner G6 remains outstanding"])
    (OUT / "review_c1.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    (OUT / "tmp/review_c1_progress.json").write_text(json.dumps(dict(complete=True)), encoding="utf-8")
    print("M5D_C1_INDEPENDENT_REVIEW", result["adversarial"]["nonrigid_probes"], "zero mismatches")


if __name__ == "__main__":
    main()
