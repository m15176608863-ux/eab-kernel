"""Summarize already measured C3-L1 queries; never reruns a solver or sets speed gates."""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics


def source_group(name):
    if name.startswith("meta/"):
        return "exact_transform"
    if name.startswith("T1b-"):
        return "T1b_frozen_projection"
    return "tia2d-2_formal"


def summarize(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not data["cpp_executed"] or data["mismatches"]:
        raise ValueError("P2 requires a completed successful C++ differential, not a fixture-only replay")
    groups = defaultdict(list)
    for item in data["queries"]:
        groups[(source_group(item["case_id"]), item["kind"])].append(item)
    rows = []
    for (source, kind), items in sorted(groups.items()):
        cpp = [item["cpp_seconds"] for item in items]
        py = [item["python_seconds"] for item in items]
        kernel = [item["python_kernel_seconds"] for item in items]
        rows.append(dict(source=source, kind=kind, queries=len(items),
            cpp_seconds=sum(cpp), python_query_json_seconds=sum(py), python_kernel_seconds=sum(kernel),
            cpp_median_seconds=statistics.median(cpp), python_query_json_median_seconds=statistics.median(py),
            cpp_max_seconds=max(cpp), python_query_json_max_seconds=max(py),
            sum_cpp_over_python_query_json=sum(cpp) / sum(py),
            comparison_scope="C++ ABI+ctypes+JSON versus Python query+dataclass JSON encode/decode; excludes input decode and process/DLL startup"))
    return dict(schema="eab2.c3l1.timing_summary.v1", source=str(path),
        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        build_identity=data["build_identity"], query_count=len(data["queries"]),
        query_timings="See the source queries array for every individual measurement.",
        rows=rows, cold_definition=data["timing_scope"], performance_gate=False,
        limitations=["Single sequential observation per query; concurrent machine load is uncontrolled.",
                     "No process-cold startup, warmup series, or statistical speedup claim.",
                     "C++ timing includes ABI and JSON transport; it is not a separately instrumented C++ kernel time.",
                     "These are local QA timings, not an engineering benchmark."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# C3-L1 P2 逐查询耗时汇总（仅报告，不设性能门）", "",
             "全部逐查询数据见 [差分原始记录](" + args.input.resolve().as_uri() + ")。", "",
             "Python 核是单次生产函数；Python 总时间另含 dataclass/JSON 编解码；C++ 时间含 ABI、ctypes、JSON 解码。",
             "两侧均不含进程/DLL 启动及输入解码；一阶可动性均使用预先装配的接触集。没有把包装层计时冒充 C++ 核计时。", "",
             "| 输入组 | 查询族 | 数量 | C++总秒 | Python查询+JSON秒 | Python核秒 | C++/Python总时间 |",
             "|---|---|---:|---:|---:|---:|---:|"]
    for row in result["rows"]:
        lines.append(f"| {row['source']} | {row['kind']} | {row['queries']} | {row['cpp_seconds']:.6f} | {row['python_query_json_seconds']:.6f} | {row['python_kernel_seconds']:.6f} | {row['sum_cpp_over_python_query_json']:.3f} |")
    lines += ["", "## 边界", "", "- 单次顺序观测，机器并行负载未控制；不作统计加速比或生产性能结论。",
              "- 这是每个新查询状态的冷调用，不是新进程冷启动；没有重新生成冻结数学证据。",
              "- 本表不包含 LP 内部主元/位长统计；另见 LP 差分报告。",
              "- 源记录 SHA-256：`" + result["source_sha256"] + "`。", ""]
    args.output.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")
    print(f"C3L1_TIMING_REPORT queries={result['query_count']} groups={len(result['rows'])} performance_gate=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
