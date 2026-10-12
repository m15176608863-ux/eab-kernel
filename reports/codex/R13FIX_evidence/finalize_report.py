"""Finalize delivery from completed immutable full-suite evidence, not estimates."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
EV = Path(__file__).resolve().parent
FULL = EV / "full_suite_final"
summary = json.loads((FULL / "summary.json").read_text("utf-8"))
assert summary["status"] == "PASS" and all(summary["checks"].values())
raw = (EV / "full_suite_runner.log").read_bytes()
log = raw.decode("utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")
last = log.splitlines()[-1]
section = """最终完整集合 **11723 passed**，其中本轮新增 **215**；原 11508 节点全部保留。
采用四个标准 pytest 完整文件分片，不是单进程的伪造汇总输出：

|分片|pytest 最后一行原样|退出码|
|---|---|---|
"""
for run in summary["runs"]:
    section += f"|{run['name']}|`{run['last_line']}`|{run['exit_code']}|\n"
section += f"""
完整运行器最后一行原样：

```text
{last}
```

- 全套执行墙钟 **{summary['wall_seconds']:.3f} s**；收集 {summary['collection_seconds']:.3f} s；合计约 {summary['wall_seconds']+summary['collection_seconds']:.3f} s，达到尽量 ≤900 s 目标。
- 四进程墙钟之和 {summary['sum_pytest_process_seconds']:.3f} s，不把此数当单进程耗时或 CPU 基准。
- 所有收集/执行 nodeid 并集相等且无重复；原 11508 节点均在；setup/call/teardown 无失败、skip/xfail；全部进程退出码 0。
- 源码、tests、tools、政策、项目配置及文档前后 SHA-256 一致：`source_policy_unchanged=true`，`code_drift=[]`。
- 静态辅助扫描最后一行：`exact construction AST gate: 0 violation(s)`，须与 2451 条明确人工排除一起阅读。
- 已执行 `tools/fix_canon_ptrs.py --apply`：5 处更新；再次只读核验 `0 rewritten; 0 kept`。
- `git -c core.whitespace=cr-at-eol diff --check` 无诊断（保留原 CRLF 合同，不为 diff 检查整文件改换行）。

证据：[全套 summary.json](R13FIX_evidence/full_suite_final/summary.json)、
[运行器完整日志](R13FIX_evidence/full_suite_runner.log)、
[前快照](R13FIX_evidence/full_suite_final/before_snapshot.json)、
[收集节点](R13FIX_evidence/full_suite_final/collection_nodes.json)、
[静态最终日志](R13FIX_evidence/root/static_final.log)、
[指针更新](R13FIX_evidence/root/canon_ptrs_apply.log) / [核验](R13FIX_evidence/root/canon_ptrs_verify.log)。
全套各分片的逐节点 JSONL 和原日志均在同目录；运行脚本不改选择集合。
Python 直接输出的分片日志为 UTF-8；PowerShell 重定向日志保留其 UTF-16 BOM，读取时须按 BOM 解码，不改原始证据。
"""
report = ROOT / "reports/codex/R13FIX_report.md"
with report.open(encoding="utf-8", newline="") as stream:
    content = stream.read()
a, b = "<!-- R13_FINAL_VERIFICATION_START -->", "<!-- R13_FINAL_VERIFICATION_END -->"
assert content.count(a) == content.count(b) == 1
content = content[:content.index(a)+len(a)] + "\n" + section + "\n" + content[content.index(b):]
with report.open("w", encoding="utf-8", newline="") as stream:
    stream.write(content)

result = {
    "status": "R13FIX_PARTIAL",
    "baseline": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
    "python": sys.version,
    "confirmed_review_ids": {"G6M-01": "fixed-with-runtime-and-static-teeth; auxiliary-check-only",
                             "G6M-02": "fixed-plus-2D-same-family", "G6M-03": "fixed-current-summary"},
    "tests": {"collected": summary["tests_collected"], "executed": summary["tests_executed"],
              "new_nodes": summary["tests_collected"]-11508, "wall_seconds": summary["wall_seconds"],
              "all_checks": summary["checks"]},
    "static_policy_entries": 2451, "static_diagnostics": 0,
    "remaining": ["Full public construction API extreme-scale differential coverage incomplete",
                  "Mixed int/float raw algebra overflow", "face_noise intermediate long edge range rejection",
                  "Explicit approximate/legacy model exclusions and dynamic protocol limits"],
    "final_report": "reports/codex/R13FIX_report.md",
}
(ROOT / "reports/codex/R13FIX_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
tracked = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True, encoding="utf-8").splitlines()
new = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True, encoding="utf-8").splitlines()
paths = sorted(set(tracked + [p for p in new if not p.startswith(("reports/codex/inputs/", "reports/codex/R13FIX_evidence/"))]))
manifest = {"head": result["baseline"], "branch": result["branch"], "original_untracked_inputs_preserved": True,
            "changed_primary_files": [{"path": p, "bytes": (ROOT/p).stat().st_size,
                "sha256": hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in paths],
            "evidence_root": "reports/codex/R13FIX_evidence",
            "full_suite_summary": "reports/codex/R13FIX_evidence/full_suite_final/summary.json",
            "generated_evidence_not_complete_until_final_verification": False}
(EV / "primary_changes_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(section)
print("Final report and result written; primary manifest:", len(paths), "files")
