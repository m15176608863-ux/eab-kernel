"""Select a conservative fast tier from a completed four-shard baseline."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def select(baseline, budget):
    summary = json.loads((baseline / "summary.json").read_text("utf-8"))
    assert summary["complete"] and summary["audit"] == "GREEN"
    costs = Counter()
    nodes = defaultdict(list)
    executed = []
    for i in range(1, 5):
        record = json.loads((Path(summary["temp"]) / f"shard_{i}_execution.json").read_text("utf-8"))
        calls = [r["nodeid"] for r in record["reports"] if r["when"] == "call"]
        assert Counter(calls) == Counter(record["collected"])
        assert all(r["outcome"] == "passed" for r in record["reports"])
        executed.extend(calls)
        for row in record["reports"]:
            base = row["nodeid"].split("[", 1)[0]
            costs[base] += row["duration"]
            if row["when"] == "call":
                nodes[base].append(dict(nodeid=row["nodeid"], seconds=row["duration"]))
    assert len(executed) == summary["collected"] == len(set(executed))
    remaining = sum(costs.values())
    slow = []
    for name, seconds in costs.most_common():
        if remaining <= budget:
            break
        slow.append(name)
        remaining -= seconds
    policy = dict(schema="eab.h1-test-tiers.v1", basis="1ce9a91 original full baseline --durations=0; actual setup/call/teardown records",
                  selection="largest cumulative function costs excluded until conservative retained baseline seconds <= budget; runtime module execution separately audited",
                  target_retained_seconds=budget, retained_baseline_seconds=remaining,
                  slow_functions=sorted(slow), fast_nodes=[])
    evidence = dict(baseline_collected=len(executed), total_baseline_test_seconds=sum(costs.values()),
                    retained_baseline_test_seconds=remaining, slow_functions=len(slow),
                    slow_cells=sum(len(nodes[n]) for n in slow),
                    functions=[dict(name=name, seconds=costs[name], cells=len(nodes[name]),
                                    tier="slow" if name in slow else "fast") for name in sorted(costs)])
    return policy, evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=ROOT / "reports/codex/H1_evidence/baseline")
    parser.add_argument("--budget", type=float, default=150.0)
    args = parser.parse_args()
    assert args.budget > 0
    policy, evidence = select(args.baseline, args.budget)
    (ROOT / "tests/slow_tests.json").write_text(json.dumps(policy, indent=2)+"\n", encoding="utf-8")
    target = ROOT / "reports/codex/H1_evidence/tier_selection.json"
    target.write_text(json.dumps(evidence, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in evidence.items() if k != "functions"}))


if __name__ == "__main__":
    main()
