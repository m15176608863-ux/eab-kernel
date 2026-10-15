"""R6 independent readback of actual execution phase identities and delivery."""
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "reports/codex/M5a2_evidence"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def suite(name):
    summary = read(EVIDENCE / name / "summary.json")
    assert summary["audit"] == "GREEN" and summary["complete"]
    temp = Path(summary["temp"])
    global_ids = [line for line in (temp / "collection.txt").read_text(encoding="utf-8").splitlines()
                  if line.startswith("tests/") and "::" in line]
    union = Counter()
    exact_seconds = Fraction(0)
    new_seconds = Fraction(0)
    new_count = 0
    rows = []
    for i, metadata in enumerate(summary["shards"], 1):
        record_path = temp / f"shard_{i}_execution.json"
        actual = read(record_path)
        wanted = (temp / f"shard_{i}_nodes.txt").read_text(encoding="utf-8").splitlines()
        assert actual["complete"] and actual["exitstatus"] == 0
        expected = Counter(wanted)
        assert expected == Counter(actual["collected"])
        assert all(row["outcome"] == "passed" for row in actual["reports"])
        for phase in ("setup", "call", "teardown"):
            observed = Counter(row["nodeid"] for row in actual["reports"] if row["when"] == phase)
            assert observed == expected, (name, i, phase)
        calls = [row for row in actual["reports"] if row["when"] == "call"]
        exact_seconds += sum((Fraction.from_float(row["duration"]) for row in calls), Fraction(0))
        newly_added = [row for row in calls if row["nodeid"].startswith("tests/test_m5a2_")]
        new_seconds += sum((Fraction.from_float(row["duration"]) for row in newly_added), Fraction(0))
        new_count += len(newly_added)
        union.update(expected)
        last = Path(metadata["log"]).read_text(encoding="utf-8").strip().splitlines()[-1]
        assert last == metadata["last_line"]
        rows.append({"shard": i, "nodes": len(wanted), "all_three_phases_exactly_once": True,
                     "last_line": last, "execution_sha256": sha(record_path)})
    assert Counter(global_ids) == union and all(count == 1 for count in union.values())
    assert len(global_ids) == summary["collected"]
    static_line = Path(summary["static"]["log"]).read_text(encoding="utf-8").strip().splitlines()[-1]
    assert summary["static"]["exit_code"] == 0 and static_line == "exact construction AST gate: 0 violation(s)"
    manifest = read(Path(summary["manifest"]))
    source = Path(summary["source"])
    expected_files = {row["path"]: row["sha256"] for row in manifest}
    actual_files = {path.relative_to(source).as_posix() for path in source.rglob("*") if path.is_file()}
    assert actual_files == set(expected_files)
    assert all(sha(source / name) == digest for name, digest in expected_files.items())
    if name == "final_suite_r3":
        for relative, digest in expected_files.items():
            if relative.startswith("reports/codex/M5a2_evidence/") or relative == "reports/codex/M5a2_report.md":
                continue
            assert sha(ROOT / relative) == digest, relative
    result = {"name": name, "collected": len(global_ids), "executed": len(global_ids), "skip_count": 0,
              "shards": rows, "call_seconds_exact_sum": str(exact_seconds), "call_seconds_display": float(exact_seconds),
              "new_gate_seconds_exact_sum": str(new_seconds), "new_gate_seconds_display": float(new_seconds),
              "new_gate_count": new_count, "wall_seconds": summary["elapsed_seconds"],
              "static_last_line": static_line, "immutable_export_paths_and_hashes_verified": len(expected_files)}
    return result, set(global_ids), exact_seconds, new_seconds


def main():
    baseline, before, btime, _ = suite("baseline_suite_r2")
    final, after, ftime, ntime = suite("final_suite_r3")
    added, removed = sorted(after-before), sorted(before-after)
    delta = read(EVIDENCE / "suite_delta.json")
    assert added == delta["added"] and removed == delta["removed"] == []
    assert len(added) == 106 and final["new_gate_count"] == 105
    performance = read(EVIDENCE / "performance.json")
    assert abs(float(ntime/btime)-performance["new_gate_fraction_of_baseline"]) < 1e-15
    assert abs(float(ftime/btime)-performance["call_ratio"]) < 1e-12
    assert performance["controlled_host"] is False
    report = (ROOT / "reports/codex/M5a2_report.md").read_text(encoding="utf-8")
    links = re.findall(r"\]\((file:///[^)]+)\)", report)
    assert all(Path(link[len("file:///"):]).exists() for link in links)
    assert all(row["last_line"] in report for row in final["shards"])
    assert "默认读取最小例与冻结总摘要并核对摘要哈希" in report
    assert report.strip().splitlines()[-1] == "M5a2_PARTIAL：B8一般仿射精确首入；B9正残差首盖稳定证书；B10完整三模型四问题与端点/路径因果分解"
    manifest = read(EVIDENCE / "artifact_manifest.json")
    mismatches = []
    for row in manifest["files"]:
        path = ROOT / row["path"]
        if sha(path) != row["sha256"]:
            mismatches.append(row["path"])
        if path.suffix in {".py", ".md", ".json", ".jsonl", ".txt", ".log"}:
            raw = path.read_bytes()
            raw.decode("utf-8")
            assert not raw.startswith((b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff"))
        if row["path"].startswith("reports/codex/M5a2_evidence/"):
            assert path.stat().st_size <= 1000000
    result = {"complete": True, "baseline": baseline, "final": final,
              "added_tests": len(added), "removed_tests": len(removed), "report_file_links_verified": len(links),
              "new_gate_percent_display": float(100*ntime/btime),
              "manifest_pre_refresh_mismatches": mismatches,
              "manifest_refresh_scope": "Generated report/review artifacts may change during final review; immutable source/data verified separately.",
              "encoding_size_manifest_files_checked": len(manifest["files"])}
    (EVIDENCE / "review_report_readback.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"complete": True, "final_nodes": final["collected"], "new_gate_percent": result["new_gate_percent_display"], "manifest_refresh": mismatches}))


if __name__ == "__main__":
    main()
