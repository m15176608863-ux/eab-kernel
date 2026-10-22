"""Assemble the C1E evidence report; never run solvers or mutate source files.

Run only after H1 has finished. This report is not an acceptance oracle.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import statistics
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="")


def last(name):
    return (HERE / name).read_text(encoding="utf-8").splitlines()[-1]


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)] +
                     ["| " + " | ".join(str(v).replace("|", " / ") for v in row) + " |" for row in rows])


def summary(values):
    values = sorted(values)
    return f"{statistics.median(values):.6f} / {values[-1]:.6f}"


def csv_rows(name, rows):
    with (HERE / name).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    diff, gen, scale = (read(n) for n in ("diff_final.json", "generated_final.json", "scale_final.json"))
    contact, fast, full = (read(n) for n in ("contact_sources_final.json", "c1e_fast/summary.json", "c1e_final/summary.json"))
    audit = read("abi/delivery_audit_build06_final.json")
    mutation = read("mutations_final_r1.json")
    c0 = read("abi/c0_diff_build06.json")
    abi_verification = read("abi/verification_build06.json")
    cpp_lines = [line for line in (HERE / "abi/build_06.log").read_text("utf-8").splitlines()
                 if line.startswith(("EAB2_NUMERIC_TESTS", "ABI_TESTS:", "C_HEADER_", "EAB2_GEOMETRY2_TESTS", "EAB2_LOCAL_TESTS"))]
    cpp_pass = len(cpp_lines) == 6 and all(line.endswith(("failed=0", "0 failures", "failures=0")) for line in cpp_lines)
    ctest_pass = any(row["name"] == "ctest_build06" and row["returncode"] == 0 for row in abi_verification["commands"])
    evidence_hashes = [item["dll_sha256"] for item in (diff, gen, contact, scale, c0, abi_verification)]
    evidence_hashes.extend([audit["dll_sha256"]["eab2_test.dll"], hashlib.sha256((ROOT / "eab2/build/eab2_test.dll").read_bytes()).hexdigest()])
    same_dll = len(set(evidence_hashes)) == 1
    assert fast["complete"] and full["complete"] and gen["complete"] and scale["complete"], "Do not finalize a running job"
    formal = [r for r in diff["cases"] if r["name"].startswith("formal/")]
    measurements = scale["measurements"]
    def flatten(row, formal_row=False):
        s = row.get("statistics", {})
        shape = row.get("subdivision_sizes", {}) if formal_row else row.get("skeleton", {})
        return dict(case=row["name"] if formal_row else f"{row['a']}--{row['b']}",
                    status="OK" if formal_row else row["cpp_status"],
                    cpp_cold_seconds=row.get("cpp_build_seconds") if formal_row else row.get("cpp_cold_body_E_seconds"),
                    cpp_export_seconds=row.get("cpp_export_seconds") if formal_row else row.get("cpp_global_export_seconds"),
                    cpp_local_seconds=None if formal_row else row.get("cpp_local_seconds"),
                    python_seconds=row.get("python_seconds") if formal_row else row.get("python_cold_E_seconds", 0)+row.get("python_compact_subdivision_seconds", 0),
                    raw_segments=row.get("raw_segments"), intersections=s.get("intersection_points"),
                    arranged_segments=s.get("arranged_segments"), cells=row.get("convex_cells") if formal_row else row.get("cells"),
                    vertices=shape.get("vertices"), edges=shape.get("edges"), faces=shape.get("faces"),
                    max_integer_bits=s.get("max_integer_bits"), integer_scope=s.get("max_integer_bits_scope"),
                    work_units=s.get("exact_work_units"), filter_fallback="N/A: exact only",
                    error=row.get("cpp_error", ""))
    csv_rows("formal_pairs.csv", [flatten(r, True) for r in formal])
    csv_rows("scale_pairs.csv", [flatten(r) for r in measurements])
    valid = [r for r in measurements if r["cpp_status"] == "OK"]
    scale_errors = [r for r in measurements if r["cpp_status"] != "OK"]
    technical_ok = not diff["mismatches"] and diff["completed_cases"] == diff["selected_cases"] and gen["status"] == "PASS" and gen["meets_10000_case_count"] and contact["status"] == "PASS" and fast["audit"] == full["audit"] == "GREEN" and audit["status"] == "PASS" and not audit["findings"] and mutation["passed"] and cpp_pass and ctest_pass and c0["mismatch_count"] == 0 and same_dll
    # External milestone gates cannot be substituted by author testing.
    pending = ["Claude 指派的一路非作者对抗核查（0 critical / 0 major）", "所有者安排的新鲜 Git 工作树复现"]
    if not technical_ok:
        pending.insert(0, "作者验证存在未绿项，见各原始 JSON")
    checklist = {
        "schema": "eab2.c1e.delivery.v1", "status": "C1E_PARTIAL", "author_verification_pass": technical_ok,
        "acceptance_complete": False, "pending_external": pending,
        "baseline_full": "NOT_RUN: opening baseline was fast only; final full does not retroactively replace it",
        "base_commit": diff["source_commit"], "source_is_uncommitted": True, "dll_sha256": diff["dll_sha256"],
        "all_final_dll_hashes_equal_live": same_dll, "cpp_six_suites_pass": cpp_pass, "cpp_last_lines": cpp_lines,
        "ctest_six_pass": ctest_pass, "c0_mismatches": c0["mismatch_count"], "delivery_audit_status": audit["status"],
        "formal_named": {"completed": diff["completed_cases"], "mismatches": len(diff["mismatches"]), "metamorphic": len(diff["metamorphic"])},
        "generated": {"attempts": gen["statistics"]["attempts"], "accepted": gen["statistics"]["accepted"], "completed": gen["completed_cases"], "mismatches": len(gen["mismatches"])},
        "local_contact_sources": {"records": len(contact["records"]), "pairs": contact["unique_ordered_pairs"], "sources": contact["raw_sources_checked"]},
        "python_fast": fast, "python_full": full,
        "scale_report_only": {"complete": scale["complete"], "selected": scale["selected_pairs"], "measured": len(measurements), "cpp_errors": len(scale_errors)},
        "not_claimed": ["fresh Git worktree", "Claude independent review", "all-input mathematical proof", "C3 mechanics or Shi classification", "production integration", "isolated performance benchmark"]}
    write_json("verification_summary.json", checklist)

    families = table(["生成族", "合法且完成差分数"], sorted(gen["statistics"]["family_counts"].items()))
    rejects = table(["拒收原因", "次数"], sorted(gen["statistics"]["rejected"].items()))
    states = table(["0 处 body_state", "数量"], [(dict([("-1", "OUTSIDE"), ("0", "CONTACT"), ("1", "OVERLAP")])[k], v) for k, v in sorted(gen["statistics"]["known_origin_states"].items())])
    perf = table(["范围 / 秒，中位 / 最大", "C++ 冷 body+E", "C++ 全局导出", "Python 对应裁判工作量（见口径）"], [
        [f"正式去重块对 {len(formal)}", summary([r["cpp_build_seconds"] for r in formal]), summary([r["cpp_export_seconds"] for r in formal]), summary([r["python_seconds"] for r in formal])],
        [f"20×40 全部实际邻接 {len(valid)}", summary([r["cpp_cold_body_E_seconds"] for r in valid]), summary([r["cpp_global_export_seconds"] for r in valid]), summary([r["python_cold_E_seconds"]+r["python_compact_subdivision_seconds"] for r in valid])]])
    counts = table(["范围", "原始段 min–max", "交点 min–max", "胞 min–max", "紧凑 V/E/F 最大", "已存坐标整数最大 bits"], [
        [name, f"{min(r['raw_segments'] for r in rows)}–{max(r['raw_segments'] for r in rows)}",
         f"{min(r['statistics']['intersection_points'] for r in rows)}–{max(r['statistics']['intersection_points'] for r in rows)}",
         f"{min(r[cell] for r in rows)}–{max(r[cell] for r in rows)}",
         "/".join(str(max(r[shape][x] for r in rows)) for x in ("vertices", "edges", "faces")),
         max(r["statistics"]["max_integer_bits"] for r in rows)]
        for name, rows, cell, shape in [("正式605对", formal, "convex_cells", "subdivision_sizes"), ("合成55对", valid, "cells", "skeleton")]])
    end_lines = "\n".join(cpp_lines + [last("abi/c0_diff_build06.log"), last("diff_final.log"), last("generated_final.log"), last("contact_sources_final.log"),
        "\n# Python 开工快档（不是开工全档）", last("baseline_fast.log"), "\n# Python 收尾快档", fast["shards"][0]["last_line"],
        "\n# Python 收尾全档四分片（原样）"] + [r["last_line"] for r in full["shards"]] +
        ["\n# 静态构造门", full["static"]["last_line"], "\n# 定向纯度/大文件门", last("focused_gates_r1.log"), "\n# 实际构建身份/交付审计", last("abi/audit_build06_final.log")])
    port_doc = (HERE / "geometry_port_map.md").read_text("utf-8")
    port_map = port_doc.split("## 2. Python 函数 → C++ 实现 → 实际守护\n", 1)[1].split("## 3.", 1)[0].strip()
    report = f"""# WO-C1E：eab2 C1 二维一般凹简单环实现与验证报告

## 结论与信任边界

**作者实现与自动验证：{'通过' if technical_ok else '尚有未通过项'}；里程碑验收：PARTIAL。** 尚需 {pending[0]}，以及{pending[1]}。作者自身三个内部缺陷注入不代替独立核查。H1 本次使用字节导出副本，不是新鲜 Git checkout。

- 工作树 `D:/eab-wt/cx-c0`，分支 `eab2-c1`，回滚/来源锚 `{diff['source_commit']}`；本单没有 commit / push / reset / checkout / stash / worktree / branch，也没有安装/下载。交付是该基线上未提交的工作区修改，不把基线提交冒充这些新源码的产生提交。
- 设计 SHA-256 `6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac`；最终测试 DLL SHA-256 `{diff['dll_sha256']}`，构建产物忽略、不入库。
- 构建身份 `{diff['build_identity']}`；实际 `cl /Bv`、13 条编译命令、Ninja 头依赖和 DLL 身份交叉审计，而非只读 CMake 声明。
- 未改 `src/eab`、设计正本、静态准入表、vendor 或姊妹源码。Python 是独立运行的生产裁判，不导入 DLL helper；差分不是独立数学定理证明。
- 开工**仅跑快档**，开工全档未执行；这是流程偏差，收尾四分片全绿不能倒写成开工全档已跑。本单未因文档整理重算冻结证据。

关键入口：[机器清单](C1E_evidence/verification_summary.json)、[交付文件清单](C1E_evidence/deliverables.md)、[完整哈希与只读边界审计](C1E_evidence/integrity.json)。

## 1. P0/P1/P2 对照

| 工单 | 实现 / 证据 | 状态 |
|---|---|---|
| P0-1 单无洞简单环、binary64 精确域、平直顶点与原 ID | Body 输入门；ABI 错误矩阵；657 例输入 bits/ID；`test_geometry2.cpp::validation_and_ids` | 已实现/作者门绿 |
| P0-2 凸分解→凸胞差→闭 E / 开 O，完整 T2b 与双三态 | geometry2；CONTACT 开段/端点/孤立点；active-halfspace 两侧占据导出 ∂E | 已实现/差分绿 |
| P0-3 exact 导出、Python 双方规范化、逐层双向查验 | `{diff['last_line']}` | 0 失配 |
| P0-4 body / E / 查询 / exact result ABI | C++ ABI 764 断言；生产 DLL C 头测试；测试符号不泄露 | 绿 |
| P0-5 C0 小项 | UNDERFLOW_ZERO、实际构建身份、AVX guard、代际复用、工作预算 | 绿，详第4节 |
| P1-6 0 处局部胞/切锥/原始关联与排除证据 | 114 归档记录、605 对、7197 条 raw sources；逐项含端点/原 ID | 0 失配 |
| P1-7 至少10⁴合法近退化例 | {gen['completed_cases']} 个完成，全规范集合与局部证书差分 | {gen['status']} |
| P1-8 元门 | {len(diff['metamorphic'])} 项：flags0..7+循环/CW/交换/旋转/反射/尺度/平移 | 绿 |
| P2-9 正式及20×40规模 | 190 对精确 broad phase；31 边邻+24 对角VV=55；实测55对 | 只报告，不设性能门 |

## 2. Python → C++ 移植与具名守护

以下为实现者只读对照，不是独立核查结论。原始独立文件：[geometry_port_map.md](C1E_evidence/geometry_port_map.md)。

{port_map}

一般凹全局构造不调用独立凸快路，故657例不能冒充对快路facets的直接覆盖。另以[临时只读调用探针](C1E_evidence/geometry_fastpath_probe.py)直接核90个非对称/平直/尺度凸对；[快路报告](C1E_evidence/convex_fastpath_final_r1.json)末行：

```text
{read('convex_fastpath_final_r1.json')['last_line']}
```

## 3. exact 导出、规范集合比较与局部查询

### 3.1 比较口径

详见[比较方法与订正](C1E_evidence/harness_method.md)，实现为 `tools/eab2_diff_c1.py` / `eab2_c1_exact.py`。没有 DLL 参数硬失败；缺失路径也失败，不进入默认 pytest 收集。负入口证据见 [harness_negative_cli.json](C1E_evidence/harness_negative_cli.json)。

双方分别导出精确 n/d 坐标与状态，**同一个纯 Python Fraction 规范器分别处理双方**：直线 gcd/符号归一；合并极大相对开共线 E\\O 段；另外保留来源标签改变的层、端点和孤立点；全部原始 VE/EV 来源段独立比较，未先用有效盖法锥删内缝。二维面按状态归组，精确再切分其有向边界并保留重数，让人工剖分线相消；不是仅比样本、面积或无序去重。有限外框的 OUTSIDE 面形状不作集合对象，但其状态样本仍复核。

C++ 全部层样本交 Python membership/topology，Python 全部层样本经仅测试用有理查询反向核验；主657例双向合计 **100086** 次（不含17元门、发布0点查询和10000例生成器）。小命名例另对 Python 慢 `boundary`；C++ 不移植 boundary/side_probes 慢路线。covers 的窗口/strict/来源及精确投影也核验，显示浮点不回灌为证书。

最终语料为 1763 次出现、657 个有序 bits 去重对（52 命名+605正式）；保留每条来源 alias。包含全部 M3 六族：thin_L / slot_wedge / interlock_section / tight_fit / pocket_hole / collinear，以及 M3b、M3c、E3、tia2d-2 正式 assembly。3 个原有理 `2^-400 + 大平移` 例 RN 后有零长边，明确列为域外，未计入合法通过数。其他非二进有理例比较双方**相同 RN binary64 输入**，不宣称原有理的共线关系保留。

### 3.2 0 处局部证据

`geometry2_local.cpp::local_origin` 与 `eab2_local_origin2_exact` 仅构造必要凸胞和局部数据，首次局部导出要求 `global_subdivision_materialized=false`。每个包含0的胞给活动边切锥；每个排除胞给含等号 AABB 与严格负的精确分离边；所有非关联闭边给精确距离平方界，以 `r=q/(1+q)` 构造严格邻域（r²<q）。该邻域保证局部扇区解释不会跨过另一条边。

`tools/eab2_c1_local.py::verify_local` 独立核所有界与来源，并用原始边扇区的严格邻域样本调用 Python `polygons_overlap_exact`，不使用 C++ 精确 helper。`eab2_c1_contact_sources.py` 再将 raw VE/EV、原始顶点ID、物理接触点及端点关联与归档 T1a ContactSet2逐项比较；OVERLAP 的非法力学分支保持归档拒收语义。

```
{last('contact_sources_final.log')}
```

### 3.3 门的敏感性

三个内部变异分别破坏闭E/开O、孤立接触保留、窗口与strict区别；编译真正被测 C++ 代码后由具名语义断言杀死，不是产出后追加假数据、源码哈希或编译失败。见[内部变异报告](C1E_evidence/mutations_final_r1.json)。这是作者测试敏感性检查，不是 Claude 指派核查。

## 4. ABI 增量与 C0 遗留处置

详见[ABI_CONTRACT](../../eab2/ABI_CONTRACT.md)、[ABI中文分报告](C1E_evidence/abi/C1E_ABI.md)。C0 已有结构不改布局；C1 通过新增结构/函数扩展。

| 族/合同 | 具体内容 | 守护 |
|---|---|---|
| body/E 生命周期 | `body2_create/destroy`、`entrance2_create/destroy`；owner/type/generation全校验，E保有body副本 | `test_abi.cpp::geometry2_matrix/child_context_reuse` |
| 双三态批量 | `query2_batch/membership2_batch/topology2_batch`；body OUTSIDE/CONTACT/OVERLAP 与 topology OUTSIDE/BOUNDARY/INTERIOR 分立；call_status≠mathematical_status | 同上，尺寸/步长/容量/溢出/逐项错误门 |
| exact 与 local | `result_export_exact/local_origin2_exact` 返回库拥有 UTF8 JSON+token；`result_destroy`，context销毁兜底释放 | 生命周期与坏句柄门 |
| 能力 | BODY2/ENTRANCE2/QUERY2/EXPORT_EXACT/LOCAL2/LIMITS2；测试 DLL 另有 TEST_EXACT2，未宣称LP/SE2/rho | `get_abi_info/get_c1_abi_info`、实际导出审计 |
| 资源 | 新 `context_limits2` 默认 work=50,000,000/elements=2,000,000/integer_bits=65,536；显式正数配置，有活子对象拒重配；对象冻结并导出限制 | `configurable_limits_and_transactions`、ABI限额矩阵 |
| cache | NO_MERGE=1/NO_COMPACT=2/NO_CACHE=4；NO_CACHE对每次全局/局部exact JSON导出建临时入口并销毁，不冒充关merge；query/covers不重建 | flags0..7精确元门 |

精确 JSON 采用约分、正分母 n/d；输入 binary64 bits 留存，包括负零。JSON 几何状态沿 Python -1/0/1，ABI 两个枚举各映射0/1/2，合同明确，不以 inside 布尔代替。

| C0 遗留 | 处理与验证 |
|---|---|
| 允许下溢单列显示 | `EAB2_DISPLAY_UNDERFLOW_ZERO=3`；精确零仍VALID；仅调整Python harness显示口径，不改Python数学实现；4483 cases/6003 bits复核 |
| 身份与ISA | 实际cl /Bv对compile_commands与DLL；受控入口 `#if defined(__AVX__) #error`；README明确STL运行时分派AVX2整数代码≠编译目标ISA |
| 槽复用 | 真实复用槽位、单调generation，旧context/body/E/result句柄拒收；代际耗尽映射RESOURCE_LIMIT |
| 文本工作量 | 每有理文本≤4096 bytes；batch values≤65536、bytes≤4194304、长度平方和≤67108864；超限RESOURCE_LIMIT |
| 资源失败恢复 | 算术前保守位长界+拥有结果检查；嵌套限制不得放宽；raw/skeleton/subdivision/export路径回滚本次新缓存，由具名低预算/重复调用恢复门核验，不泛称任意内存故障已穷尽 |

位长预算是算术与拥有值上界，不冒充 Boost 内部临时 limb 或进程物理内存峰值证明。

## 5. 固定种子近退化生成器

seed=20261022；尝试 **{gen['statistics']['attempts']}**，合法唯一有序 bits 输入 **{gen['statistics']['accepted']}**，完成 **{gen['completed_cases']}**，失配 **{len(gen['mismatches'])}**。先构造合法环与已知原点标签，再做ULP、近共线、极窄边、极端指数、方向/旋转和分辨率扰动；拒收先由Python裁判完成，不拿C++筛选期望。拒收不计入10⁴。

{families}

{rejects}

{states}

并非只查0：每例都走全规范集合、来源分层、正面积区域边界、双向层查询和局部证书。累计独立局部扇区样本 **{gen['totals']['independent_sector_samples']}**、来源 **{gen['totals']['raw_sources_checked']}**；两向层查询分别 **{gen['totals']['cpp_layer_samples_rechecked']} / {gen['totals']['python_layer_samples_reverse_checked']}**。耗时 {gen['seconds']:.3f}s（并发环境墙钟，不作性能门）。

输入分块、逐例journal、SHA256和重跑种子见[generated_final.json](C1E_evidence/generated_final.json)。大型journal仅在忽略的 evidence/tmp 保存，不入库；摘要含路径与哈希。有限随机/构造样本不证明全输入域正确。

## 6. P2 规模测量（只报告）

20块，每块恰40顶点，对齐4×5非凸简单环；共享二进有理锯齿接口。完整190对 broad phase，精确检测 **55 CONTACT / 135 OUTSIDE**，其中 **31边邻接+24对角VV**。没有把31当完整邻接；对全部55邻接冷构造与导出。未执行额外forced190全局构造，也未执行C3 Shi/锁定/多体LP分类。

{perf}

{counts}

合成局部查询中位/最大 {summary([r['cpp_local_seconds'] for r in valid])}s；C++错误记录 {len(scale_errors)}。逐对数值见[正式605对 CSV](C1E_evidence/formal_pairs.csv)、[合成55对 CSV](C1E_evidence/scale_pairs.csv)、[完整测量 JSON](C1E_evidence/scale_final.json)。

口径：C++冷计时含ctypes/ABI，导出含序列化与Python JSON解析；正式diff Python列为GlobalEntrance2+python_export，含原始排布、来源、subdivision及逐层/边界topology，不含canonical比较、clipped_covers、局部verify或DLL反查；合成Python列才是E+subdivision。二者均不执行慢boundary，不能混作严格内核加速比。归档T1a整装LP/接触组装墙钟是不同工作量，不与这里的块对构造直接相除。单次冷测、未绑核，与其他验证存在并发，不是隔离基准；无性能门。硬件/解释器与并发说明见[测量环境](C1E_evidence/measurement_environment.json)。

交点计数包含闭段共享端点及共线重合端点；整数位长最大值仅指已存储精确坐标的分子/分母，不是所有算术临时峰值。浮点过滤器未启用，过滤/精确回退比为 **N/A**，不能把内部零计数写成0%失败率。

## 7. 验证原始末行与执行完整性

以下从最终完整日志读取，不拼接中断运行：

```text
{end_lines}
```

- CTest：`100% tests passed, 0 tests failed out of 6`；见[CTest日志](C1E_evidence/abi/ctest_build06.log)。
- H1收尾快档 {fast['collected']}、全档 {full['collected']}；每分片收集/分派/调用多重集合相等、0 skipped、0 failed；逐模块实际执行覆盖完整；导出副本及活树字节变化均空。见[快档摘要](C1E_evidence/c1e_fast/summary.json)、[全档摘要](C1E_evidence/c1e_final/summary.json)、[模块覆盖](C1E_evidence/c1e_final/module_coverage.json)。
- pytest均禁cacheprovider并显式basetemp，TEMP/TMP在本单 evidence/tmp；H1 Python3.12实际执行监测。字节副本验证不是新鲜Git树验证。
- 静态构造准入未增减；纯度、大文件门保持绿；最终未提交文件还由[完整性审计](C1E_evidence/integrity.json)逐项核UTF8/BOM/换行/大小与原始哈希边界。

## 8. 订正、设计差异与遗留

1. **harness策略订正**：tight_fit原始长CONTACT段上的Python有限side_probe可落到后续内缝，不能和紧邻开面标签等比。改为先由全部supporting-line事件限制严格邻域，再调用原Python membership；clipped比较相同闭E占据语义。未改Python生产代码，未忽略C++侧状态。首次失败保留，详harness_method。
2. **输入域订正**：3个非binary64原有理小尺度+大平移例RN坍缩，明确域外而非合法skip；非二进有理原输入只声称共同RN后的精确结果。
3. **构建环境修复**：build_05中文MSVC/showIncludes编码使旧local测试对象漏重编；CMake改显式受控头依赖，build_06实际重编全绿；audit逐对象核依赖。失败日志保留，build_05有6个捕获时替换字符且原始native流当时未存，不能伪造无损原始字节；成功build_06无该问题。
4. **C1接口适配**：新增C1工作ABI和独立limits结构，不改变冻结C0结构；局部0查询按需但仍先拥有凸分解/凸胞差，不强制全局T2b。仅测试有理/窗口桥接不进发布DLL。
5. **范围**：C3力学、Shi分类、LP、三维、事件/敏感性均不在本单，不据C1几何差分声称任何姊妹轨迹等价或工程验证。
6. **流程遗留**：开工全档未跑（仅开工快档）；末次全档已跑但不抹去这一偏差。Claude一路独立对抗核查及所有者新鲜工作树复现仍待安排；因此不标C1E_DONE、不宣称里程碑退出。

## 9. 重跑与交付

在当前工作树 PowerShell 中先令 TEMP/TMP 指向 `reports/codex/C1E_evidence/tmp`。下列输出名应换成未使用的新名，避免覆盖已封存运行；不需要Git写或姊妹exe。

```powershell
$env:TEMP = "$PWD/reports/codex/C1E_evidence/tmp"
$env:TMP = $env:TEMP
cmd /c eab2\\build_eab2.bat
python -X utf8 tools/eab2_diff_c1.py --dll "$PWD/eab2/build/eab2_test.dll" --output reports/codex/C1E_evidence/diff_replay_NEW.json --metamorphic
python -X utf8 tools/eab2_c1_generate.py --dll "$PWD/eab2/build/eab2_test.dll" --count 10000 --seed 20261022 --output reports/codex/C1E_evidence/generated_replay_NEW.json
python -X utf8 tools/eab2_c1_contact_sources.py --dll "$PWD/eab2/build/eab2_test.dll" --output reports/codex/C1E_evidence/contact_replay_NEW.json
python -X utf8 tools/eab2_c1_measure.py --dll "$PWD/eab2/build/eab2_test.dll" --output reports/codex/C1E_evidence/scale_replay_NEW.json
python -X utf8 tools/h1_run_gates.py --name fast_replay_NEW --evidence-root reports/codex/C1E_evidence
python -X utf8 tools/h1_run_gates.py --name full_replay_NEW --runslow --evidence-root reports/codex/C1E_evidence
```

源码、接口、工具、所有小型证据和忽略的大型原始日志索引见[交付清单](C1E_evidence/deliverables.md)。回滚应由所有者以基线+差异清单审查后安排；本单不自动撤销工作树。

C1E_PARTIAL：待Claude一路非作者对抗核查、所有者新鲜Git工作树复现；开工全档基线未执行（已明确流程偏差）。
"""
    (ROOT / "reports/codex/C1E_report.md").write_text(report, encoding="utf-8", newline="")
    print("C1E_REPORT_WRITTEN status=C1E_PARTIAL author_verification="+str(technical_ok))


if __name__ == "__main__":
    main()
