"""Verify frozen-suite evidence and produce the final delivery inventory."""
import collections
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8-sig"))


def write(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def log_text(path):
    raw = path.read_bytes()
    # Windows PowerShell Out-File produces UTF-16; retain original evidence bytes.
    return raw.decode("utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")


def link(path, title=None):
    return f"[{title or path.name}]({path.resolve().as_uri()})"


def main():
    initial = read("tracked_before.json")
    suite = read("full_suite_verified/summary.json")
    assert suite["status"] == "PASS" and all(suite["checks"].values()), suite
    before = read("full_suite_verified/before_snapshot.json")
    assert all(sha(ROOT / p) == digest for p, digest in before.items()), "frozen suite source changed afterwards"
    current_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    assert current_head == initial["head"]
    changes, missing = {}, []
    for name, digest in initial["sha256"].items():
        p = ROOT / name
        if not p.exists():
            missing.append(name)
        elif sha(p) != digest:
            changes[name] = dict(before=digest, after=sha(p))
    assert not missing, missing
    assert not any(p.startswith(("fixtures/", "tests/")) for p in changes), "original fixtures/tests changed"
    for name in ["src/eab/adapters/bdda2d.py", "tools/check_exact_construction.py",
                 "tools/exact_construction_subset.py", "tools/exact_construction_flow.py"]:
        if name in initial["sha256"]:
            assert name not in changes, name
    calls = []
    for p in (HERE / "full_suite_verified").glob("shard_*_results.jsonl"):
        calls += [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines()
                  if json.loads(line)["when"] == "call"]
    m4 = [r for r in calls if r["nodeid"].startswith("tests/test_m4_")]
    assert m4 and all(r["outcome"] == "passed" for r in m4)
    mutations = read("o01_mutations.json")
    assert len(mutations) == 12 and all(r["killed"] for r in mutations)
    shape = read("o02_mutations.json")["mutations"]
    assert len(shape) == 5 and all(r["status"] == "EXPECTED_ASSERTION_RED" for r in shape)
    geom = read("o03_o05_mutations.json")
    assert len(geom) == 6 and all(r["mutation_killed"] for r in geom)
    readers = read("o04_mutations.json")
    assert len(readers) == 9 and all(r["exit_code"] == 1 for r in readers)
    for row in readers:
        log = log_text(HERE / f"o04_mutation_{row['case']}.log")
        target = ("unbounded integer schema rejected an exact integer" if row["case"] in
                  ("parser", "nsign", "owner") else "DID NOT RAISE")
        assert target in log and "1 failed" in log, row["case"]
    files = []
    for stem in ("force_reports", "geometry", "numeric_decode", "shape"):
        p = ROOT / f"tests/test_r15fix_{stem}.py"
        assert p.exists()
        files.append(p)
    report_path = ROOT / "reports/codex/R15FIX_report.md"
    report = report_path.read_text(encoding="utf-8")
    current_nodes = read("full_suite_verified/collection_nodes.json")
    tracked_nodes = [n for n in current_nodes if n.split("::")[0] in initial["sha256"]]
    assert len(tracked_nodes) == 12427 and set(tracked_nodes) == set(read("baseline_nodes.json"))
    raw_last = next(line for line in reversed(log_text(HERE / "full_suite_verified_runner.log").splitlines()) if line.strip())
    assert raw_last.startswith("R15FIX_FULL_SUITE PASS"), raw_last
    first_suite = read("full_suite_final/summary.json")
    full_runs_seconds = sum(r["wall_seconds"] + r["collection_seconds"]
                            for r in (first_suite, suite))
    lines = [f"完整覆盖 **{suite['tests_executed']} passed / 0 failed / 0 skipped**；新增175格，原12427节点全保留。",
             "这是完整分片核验统计，不是单一串行pytest进程的伪造输出。", "", "各分片最后一行原样：", "", "```text"]
    lines += [r["last_line"] for r in suite["runs"]]
    lines += ["```", "", "全套审计器最后一行原样：", "", "```text", raw_last, "```", "",
              f"完整测试分片墙钟 **{suite['wall_seconds']:.3f}s**；收集 **{suite['collection_seconds']:.3f}s**；",
              f"两者合计 **{suite['wall_seconds']+suite['collection_seconds']:.3f}s**，4进程累计 **{suite['sum_pytest_process_seconds']:.3f}s**。",
              "最终一轮目标≤900s：" + ("达成。" if suite['wall_seconds']+suite['collection_seconds'] <= 900 else
                               "未达成；不缩网格。主要耗时及完整durations见各分片日志，按实际结果记录。"),
              f"两轮全套（含各自收集）累计墙钟 **{full_runs_seconds:.3f}s**，超过900s；原因是首轮暴露两处回归后必须完整重跑，不能以定向绿替代。此累计还不含修复、红门和变异用时。",
              f"M4系列 **{len(m4)}项全通过**（包含离线shadow、adapter、VV reader等）；所有setup/call/teardown均pass。", "",
              link(HERE / "full_suite_verified/summary.json", "机器汇总") + "；" +
              link(HERE / "full_suite_verified_runner.log", "全套原日志") + "；" +
              link(HERE / "full_suite_verified/partition.json", "完整文件分片表") + "。"]
    assert "FULL_SUITE_RESULT_PENDING" in report
    report = report.replace("FULL_SUITE_RESULT_PENDING", "\n".join(lines))
    assert "FINAL_STATUS_PENDING" in report
    report = report.replace("FINAL_STATUS_PENDING", "最终核验：" + link(HERE / "verification.json", "机读验收") +
                            "；" + link(HERE / "delivery_index.md", "全部交付链接与哈希索引") +
                            "；" + link(HERE / "final_readonly_review.md", "团队只读复核") +
                            "。\n\nR15FIX_DONE")
    report_path.write_text(report, encoding="utf-8")
    evidence = dict(head=current_head, tracked_files_checked=len(initial["sha256"]),
                    tracked_changed=changes, tracked_missing=missing,
                    old_test_files_checked=sum(p.startswith("tests/") for p in initial["sha256"]),
                    old_tests_changed=[], fixtures_changed=[], new_test_count=175,
                    original_node_count=12427, total_node_count=suite["tests_executed"],
                    suite_checks=suite["checks"], suite_last_line=raw_last,
                    wall_seconds=suite["wall_seconds"], collection_seconds=suite["collection_seconds"],
                    all_full_runs_wall_and_collection_seconds=full_runs_seconds,
                    m4_passed=len(m4), m4_files=dict(collections.Counter(r["nodeid"].split("::")[0] for r in m4)),
                    targeted_mutants_killed=dict(o01=12, o02=5, o03_o05_and_related=6, o04=9, total=32),
                    no_commit=True, fresh_worktree_verification=False, independent_G6_approval=False,
                    final_status="R15FIX_DONE")
    write("verification.json", evidence)
    paths = [ROOT / p for p in changes] + files + [ROOT / "docs/r15fix_design_sync.md", report_path]
    paths += [p for p in HERE.rglob("*") if p.is_file() and "tmp" not in p.relative_to(HERE).parts
              and p.name not in {"artifact_sha256.json", "delivery_index.md"}]
    paths = sorted(set(paths))
    index = ["# R15FIX 交付索引", "", "本树修改未提交；完整测试通过，待独立复审。",
             "临时pytest产物单列目录链接，不纳入交付内容哈希。", "", "## 关键入口", "",
             "- " + link(report_path, "中文总报告"),
             "- " + link(ROOT / "docs/r15fix_design_sync.md", "当前设计合同"),
             "- " + link(HERE / "verification.json", "机读验收"),
             "- " + link(HERE / "artifact_sha256.json", "交付文件SHA256"),
             "- " + link(HERE / "tmp", "本树测试临时目录"), "", "## 全部交付文件", ""]
    index += ["- " + link(p, p.relative_to(ROOT).as_posix()) for p in paths]
    (HERE / "delivery_index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    paths.append(HERE / "delivery_index.md")
    write("artifact_sha256.json", {p.relative_to(ROOT).as_posix(): sha(p) for p in paths})
    print(raw_last)
    print("Verified", len(paths), "delivery files;", len(m4), "M4 calls; old tests unchanged; R15FIX_DONE")


if __name__ == "__main__":
    main()
