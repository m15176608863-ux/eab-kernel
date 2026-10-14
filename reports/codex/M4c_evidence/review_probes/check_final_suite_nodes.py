"""Independent final four-shard collection/execution audit; stdlib only."""
import argparse
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def run(suite, output):
    summary = read(suite/"summary.json")
    assert summary["complete"] is True and summary["audit"] == "GREEN"
    assert len(summary["shards"]) == 4 and summary["static"]["exit_code"] == 0
    collected = [line for line in (suite/"collection.txt").read_text(encoding="utf-8").splitlines()
                 if line.startswith("tests/") and "::" in line]
    assert collected and len(collected) == len(set(collected)) == summary["collected"]
    actual_all = []
    shard_rows = []
    for index in range(1, 5):
        dispatched = (suite/f"shard_{index}_nodes.txt").read_text(encoding="utf-8").splitlines()
        record = read(suite/f"shard_{index}_execution.json")
        shard = read(suite/f"shard_{index}.json")
        actual = [r["nodeid"] for r in record["reports"] if r["when"] == "call"]
        skipped = [r for r in record["reports"] if r["outcome"] == "skipped"]
        failed = [r for r in record["reports"] if r["outcome"] == "failed"]
        assert record["complete"] is True and record["exitstatus"] == shard["exit_code"] == 0
        assert sorted(dispatched) == sorted(record["collected"]) == sorted(actual)
        assert len(actual) == len(set(actual)) and not skipped and not failed
        assert shard["node_sets_equal"] and shard["execution_complete"] and shard["skip_count"] == 0
        last = (suite/f"shard_{index}.txt").read_text(encoding="utf-8").splitlines()[-1]
        assert last == shard["last_line"]
        shard_rows.append({"shard": index, "collected": len(record["collected"]), "executed": len(actual),
                           "node_multisets_equal": True, "skipped": 0, "failed": 0, "last_line_verbatim": last})
        actual_all.extend(actual)
    assert sorted(actual_all) == sorted(collected)
    assert len(actual_all) == len(set(actual_all))
    output.write_text(json.dumps({"complete": True, "audit": "GREEN", "collected": len(collected),
        "executed": len(actual_all), "global_node_multisets_equal": True, "skipped": 0,
        "shards": shard_rows, "suite_summary_sha256": hashlib.sha256((suite/"summary.json").read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"audit": "GREEN", "collected": len(collected), "executed": len(actual_all), "skip": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.suite, args.out)
