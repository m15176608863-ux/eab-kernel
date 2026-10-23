"""Render the Chinese repair report only from completed verification evidence."""
from pathlib import Path
from collections import Counter
import gzip
import json

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reports/codex/C3L3_repair_evidence"
OLD = OUT / "tmp/rollback/reports/codex/C3L3_report.md"


def read(name):
    return json.loads((OUT / name).read_text("utf-8"))


def main():
    assert read("progress.json")["complete"]
    differential = json.loads(gzip.decompress((OUT / "differential.json.gz").read_bytes()))
    assert not differential["mismatches"] and differential["source_pre_post_equal"]
    fast, full = read("final_fast/summary.json"), read("final_full/summary.json")
    assert fast["audit"] == full["audit"] == "GREEN"
    runs = {r["name"]: r for r in read("verification_runs.json")}
    enrichments = [r for r in differential["queries"] if r.get("proof_dispositions")]
    known = differential["acceptance_enhancements"]
    assert len(known) == 20
    query_differences = [r for r in differential["queries"]
                         if "python_queries" in r and r["python_queries"] != r["cpp_queries"]]
    ledger = ["# MINOR-1：20 个已知实例的处置", "",
        "权威运行见 [differential.json.gz](differential.json.gz)。下表仅为该运行的索引，不是第二份差分输出。",
        "每项均先以原始几何重建 A/b/c 核证，再准许证明可用性不同；语义失配均为 0。",
        "Python 均为 exact_threshold=null、attained=null；C++ 均为合法开阈。", "",
        "| 外部验收实例 ID | C++ 阈值 | 括号 | 处置 |", "|---|---|---|---|"]
    for row in known:
        d = row["disposition"]
        assert d["proved_side"] == "cpp" and d["attained"] is False and row["semantic_mismatches"] == 0
        ledger.append(f"| `{row['acceptance_id']}` | {d['exact_threshold']} | [{d['mu_lo']}, {d['mu_hi']}] | 独立核证后接受 |")
    ledger += ["", f"本次全族共 {len(enrichments)} 项证明可用性订正，其中上述 20 项逐一复现，其余 {len(enrichments)-20} 项由扩展网格发现。",
        f"查询次数不等共 {len(query_differences)} 项，原始两侧次数均保存在权威结果；次数是选基/搜索成本，不当数学等价字段。", ""]
    (OUT / "acceptance_enrichment_disposition.md").write_bytes("\n".join(ledger).encode("utf-8"))
    old = OLD.read_text("utf-8")
    body = old[old.index("## 2."):old.index("## 7.")]
    intro = """# WO-C3L3：profile1 刚体极限分析与临界参数 C++ 移植报告（验收返修）

## 1. 结论、范围与复核状态

本单 P0/P1 实现与 P2 实测已交付。本轮完成 MAJOR-1 门缺口修补及 MINOR-1/2 比较口径、文档订正；**不改生产求解代码，不削弱 C++ 的阈值证明**。完整构建、扩大差分和 Python 收尾快/全档见第 7 节。

- 本单原始基点为 `1b6b4f32ff3c5716f8e3a24ad73dd3cf6081f39c`；本轮入场为干净 `eab2-c3l3 @ c8718bb0850328defd8f0cc16fb4f3a09e922975`，同一工作树 `D:/eab-wt/cx-c0`。本代理未作 commit/push/reset/checkout/stash/worktree/branch 等 Git 写操作。
- Claude 告知：`c8718bb` 新鲜工作树复现构建、原五族差分 0 失配及 Python 全档 15056；外部静力路 0 缺陷、可收口，临界参数路因 MAJOR-1 未通过。该事实及问题全文见[原始验收报告副本](C3L3_repair_evidence/input/C3L3_acceptance.md)，不是本代理重复执行或替外部验收签署。
- 本轮已有具名回归、7 项内部变异、真实变异 DLL 假证拒绝及完整收尾证据；**仍待 Claude 对修复后临界参数路复验确认**。作者团队内部复查不冒充非作者对抗验收；本次新鲜字节副本也不冒充新的 Git 工作树。
- 设计依据 [eab2_design.md](../../docs/eab2_design.md) SHA-256 仍为 `6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac`。返修只动测试、差分工具/测试输入及报告证据；`eab2/src`、`src/eab`、设计及静态准入策略均与 `c8718bb` 一致。
- profile1 是刚体、小变形、无限抗压、无黏聚、恒定 μ、关联流动模型；相对非关联库仑摩擦，它是不安全侧的承载力上界模型，不作工程安全承载力或姊妹轨迹等价宣称。
- 回退锚为 `c8718bb` 及[原字节归档映射](C3L3_repair_evidence/previous_archive.json)，不得覆盖所有者后续改动。未安装/下载、未写姊妹工作树、未结束非本代理启动的进程；仅向获准 `D:/eab-evidence` 追加本单归档。[本轮交付索引](C3L3_repair_evidence/deliverables.md)与[入场合同](C3L3_repair_evidence/intake.json)列明边界。

"""
    anchor = """**速度坐标约定（静力验收注记）**：不仅端板，所有自由体的三条平衡行也统一采用移到 `dof_anchor` 的力矩；`exact_y` / `mechanism` 是该锚点处的旋量，而非默认参考点 o 处的旋量。对全自由体这是保持功率配对的坐标变换，不改变可行性或承载力；端板再按 mask 取放开分量。C3-L4 读取 y 时必须采用相同锚点约定，并对约束、荷载及其导数作一致变换，不能把 y 的平移分量直接当作 o 处速度。具名门为 `matrix_and_certificates`、`rigid_units_and_anchor_translation` 及差分的原始几何独立重建；[详细合同说明](C3L3_repair_evidence/thickness_contract.md)区分参考点与物理支承。

"""
    body = body.replace("**力矩微分范围**", anchor + "**力矩微分范围**", 1)
    body = body.replace("critical 从精确 A(0)、A(1) 构造该系数", "上述式先在 o 处构造，再同步移至锚点（锚点处为 `(p−anchor)×(±T)`）；critical 从精确 A(0)、A(1) 构造该系数", 1)
    start, end = body.index("权威结果："), body.index("### 回归 (d)")
    table = ["| 族 | limit | critical |", "|---|---:|---:|"]
    families = differential["family_counts"]
    for family in dict.fromkeys(k.rsplit("/", 1)[0] for k in families):
        table.append(f"| {family} | {families.get(family+'/limit', 0)} | {families.get(family+'/critical', 0)} |")
    table.append(f"| **总计** | **{differential['counts']['limit']}** | **{differential['counts']['critical']}** |")
    comparison = """权威结果为唯一一份 [differential.json.gz](C3L3_repair_evidence/differential.json.gz)，[原始日志 gzip](C3L3_repair_evidence/differential.log.gz)及[压缩/原始 SHA 核对](C3L3_repair_evidence/differential_archive.json)随附。原 `c8718bb` 差分已按 H1 外归档，不能与本次计数混用。工具独立解析语料与 DLL JSON；formal 使用 `formal_20261019_02/binary64` 冻结输入/期望，新增族调用未改的 Python 裁判。原五层 formal / t1b / regression / metamorphic / implication 全部保留，再加 wide、thickness。

""" + "\n".join(table) + f"""

formal 的 114 个 critical 项中仍含 1 个不支持参数的调用错误合同（不发布数学 JSON）；不把总计误称为同样多的已证阈值。原始末行：

```text
{differential['last_line']}
```

`source_pre_post_equal=true`。状态、精确承载值、端点、退出原因、有效条件等保持精确比较。非唯一 x/y/机构、Farkas、可行点/射线由**原始顶点边、荷载 bits、参考点、锚点**重建 A/b/c 后按第 2 节核验，不信任 C++ 导出的法向/矩阵。临界基不硬等系数/基序：核有理多项式恒等式、精确一侧 Sturm、列表存在/空非空、分支角色与采样端点。

**attained / exact_threshold 的精确比较口径订正**：旧语料上的逐字段相等不能推广到宽括号及 Farkas 下端。双方阈值都非空时仍要求精确值、开闭相等；双方都空时保持 null 合同；仅一方非空时，先对双方执行独立 `verify_critical`，非空侧必须通过原始几何 LP、阈值证书及上下侧延续核验，才允许记录证明可用性订正。只规范化 `exact_threshold/attained/threshold_certificate/threshold_proof_reason` 四个相互派生字段，不放宽端点、状态、退出原因、有效条件或多项式有无。阈值证书的元合同及状态专属互斥附件也先检查，不能借整块规范化吞掉错误字段。

本轮 {len(enrichments)} 项证明可用性差异均独立核证通过，外部验收所报 **20 项逐一复现并处置**，详见[逐例台账](C3L3_repair_evidence/acceptance_enrichment_disposition.md)与[来源输入映射](C3L3_repair_evidence/acceptance_enrichment_inputs.json)。C++ 选出不同合法改进射线/基而取得更强证明，不是改错数；不为对齐 Python 而削弱生产证明。查询次数不同 {len(query_differences)} 项在权威结果保留双侧原值，不当数学真值比较。

[校验器具名门](../../tests/test_eab2_c3l3_harness.py)覆盖错误矩阵/原始切向、假证书、多项式恒等式、缺上下侧延续、双非空不一致、双向合法证明增益与非法元字段/附件；见[本轮定向日志](C3L3_repair_evidence/checker_tests.log)。生产内部变异另见第 6 节，不能用产出后手工改 JSON 代替内部缺陷注入。

### 宽括号与两个 MAJOR-1 回归

G1 三取向 × 11 组 `(t,h)` × `max_steps=0..6` × `mu_max={{1/8,1/4,3/8,1/2,3/4,1,3/2,2,3,4}}`，共 2310 项；另有斜面 Farkas 下端 16 项（真实开阈 0、1/13，各 8 个步数）及二次无理根括号 6 项，共 2332 critical。Farkas 例保留真实 INFEASIBLE 下端及 null 阈值，不强签开闭；根括号另以 `μ²+2μ−1` 核两端异号。

| `threshold_contracts` 具名回归 | `(t,h,mu_max,max_steps)` | 保留括号 | 真实闭阈 | 导出阈值/attained |
|---|---|---|---|---|
| `koureas_wide_four_steps_requires_below` | `(3/32,1/16,3/4,4)` | `[3/64,3/32]` | `2039/32768` | null/null |
| `koureas_wide_one_step_requires_below` | `(3/8,1/4,3/8,1)` | `[3/16,3/8]` | `119/512` | null/null |

"""
    body = body[:start] + comparison + body[end:]
    thickness = """### T1b 厚度样本的 ABI 输入域

上述 36 个形貌模型与厚度扫描不是同一语料。T1b 厚度的 39 个样点多数含非二进有理原始几何：32 个不在当前 binary64 ABI 的无损输入域内，不能舍入后冒充原模型。本次差分只纳入其中 **7 个完整模型精确可表示的样点及 18 个厚块对照**，共 25 个来源条目、19 个唯一模型（6 个重复来源如实保留）；每条 3 个 limit 和 1 个 critical，共 75/25 查询。外部静力路原已报告这 7+18 项通过，本轮把它们变为持久可重跑的输入族，不追认成旧原作者当时的覆盖。

[生成器](../../tools/eab2_c3l3_thickness.py)只读取[测试数据摘要](../../tests/data/eab2_c3l3_thickness_summary.json)，不依赖 Temp 验收目录或外部归档；所有实际传输的原始顶点、参考点、锚点、恒/活荷载及参数都逐项核 binary64 无损。[输入域与来源合同](C3L3_repair_evidence/thickness_contract.md)列出全部选入/排除规则、7 样点及重复身份。未覆盖的 32 个精确有理模型不是算例错误，也不是本 ABI 的测试通过项。

"""
    body = body.replace("## 5.", thickness + "## 5.", 1)
    start, end = body.index("- [critical mutation]"), body.index("规模工具")
    body = body[:start] + """- [本轮 critical mutation](C3L3_repair_evidence/critical_mutations.json)：保留原 5 项，再加“闭阈缺下侧延续”和“开阈缺上侧改进射线”共 7 项；正常基线先绿，变异必须触发具名语义断言。
- 闭阈变异由 `koureas_wide_four_steps_requires_below` 杀死；开阈变异由 `unreversed_open_requires_above` 杀死。第二个 koureas 宽括号回归另保留在正常门及差分中。
- 另外构建两个隔离真实变异 DLL，未经改写的原生导出分别假称 `3/32,true` 与 `0,false`；新比较器均在独立延续核验阶段拒绝，证明增益处置列表为空。[拒绝证据](C3L3_repair_evidence/continuation_dll_red_gates.json)记录输出、异常语义与 DLL/source SHA；不是在产出后追加假数据。

```text
C3L3_STATICS_MUTATIONS_OK baseline=1 rejected=3 semantic_failures=3
C3L3_CRITICAL_MUTATIONS_OK caught=7 escaped=0
C3L3_CONTINUATION_DLL_RED_GATES_OK rejected=2 admitted=0
```

第一行是 `c8718bb` 已验收静力路的历史证据；后两行是本轮实际末行。作者团队补充复查曾发现新证明增益比较可能掩盖阈值证书元字段，已在本轮正式收尾前补门；[内部复查记录](C3L3_repair_evidence/internal_checker_review.md)不冒充 Claude 非作者复验。

P2 沿用下述原始实测，不为本轮测试/文档修复重复跑规模；生产求解源未改，时长仍只代表旧采样时刻。

""" + body[end:]
    build_lines = (OUT / "tmp/complete_build.log").read_text("utf-8", errors="replace").splitlines()
    build_summary = [s for s in build_lines if "100% tests passed" in s or "Total Test time" in s]
    cpp_lines = build_summary + [runs[n]["last_line"] for n in ("cpp_statics", "cpp_critical", "cpp_c3l3_abi")]
    baseline = json.loads((ROOT / "reports/codex/C3L3_evidence/baseline/summary.json").read_text("utf-8"))
    checker_lines = [s for s in (OUT / "checker_tests.log").read_text("utf-8").splitlines() if "passed in" in s]
    section7 = """## 7. 全部验证原始末行与复跑

本轮[顺序运行记录](C3L3_repair_evidence/verification_runs.json)给出完整命令、返回码、耗时及原日志 SHA；[进度闭合记录](C3L3_repair_evidence/progress.json)为 complete。完整构建从新建字节副本开始，非增量复用；H1 收尾也为字节导出，均不是 Git 新树。被测代码从构建到全档期间冻结，最后再核当前源码字节一致。

### 本轮完整构建与 C++ 单测

```text
""" + "\n".join(cpp_lines) + """
```

完整原始构建日志及编译命令在[本轮归档映射](C3L3_repair_evidence/archive_manifest.json)；[交付审计](C3L3_repair_evidence/delivery_audit.json)核导出隔离、第三方清单与 C0 编译合同。

### 原工单开工全档（4 分片，历史基线）

本轮是同一工单的验收续修，不重跑开工全档；原开工基线确在实现前执行，保留原样，与 Claude 告知的 `c8718bb` 新鲜全档 15056 分开标注。

```text
""" + "\n".join(s["last_line"] for s in baseline["shards"]) + "\n" + baseline["static"]["last_line"] + """
```

### 本轮收尾快档

""" + f"[快档摘要](C3L3_repair_evidence/final_fast/summary.json)：GREEN，收集/执行 {fast['collected']} 项。\n\n```text\n" + "\n".join(s["last_line"] for s in fast["shards"]) + """
```

### 本轮收尾全档（4 分片）

""" + f"[全档摘要](C3L3_repair_evidence/final_full/summary.json)：GREEN，收集/执行 {full['collected']} 项。\n\n```text\n" + "\n".join(s["last_line"] for s in full["shards"]) + "\n" + full["static"]["last_line"] + """
```

执行节点多重集合等于收集节点，0 skip、0 failed，逐模块实际执行核验齐备；纯度、大文件门均在快/全档内，静态准入无新增。运行未中断，不拼接日志；快档若超过日常约 5 分钟成本目标，按上述实际时长报告，不为凑数重跑。

### 本轮定向与差分

```text
""" + "\n".join(checker_lines + ["C3L3_CHECKER_AST diagnostics=0", runs["delivery_audit"]["last_line"], differential["last_line"], "C3L3_REPAIR_FINAL_SEQUENCE_OK"]) + """
```

复跑示例（名称必须新建，先把 TEMP/TMP 指到被忽略的 tmp 路径）：

```powershell
$env:TEMP = "$PWD/reports/codex/C3L3_repair_evidence/tmp"
$env:TMP = $env:TEMP
.\\eab2\\build_eab2.bat
python -X utf8 tools/eab2_c3l3_diff.py --dll "$PWD/eab2/build/eab2.dll" --family all --output "$env:TEMP/recheck_differential.json"
python -X utf8 tools/h1_run_gates.py --name recheck_fast --evidence-root reports/codex/C3L3_repair_evidence
python -X utf8 tools/h1_run_gates.py --name recheck_full --runslow --evidence-root reports/codex/C3L3_repair_evidence
```

H1 自带 `-p no:cacheprovider`、显式 basetemp 及忽略路径 TEMP/TMP；独立 pytest 同样必须采用。变异使用新的 `eab2/build/tmp/<name>`，critical 变异工具要求 `--root`。C0 编译合同保持 MSVC 19.44.35227.0、工具集 14.44.35207、C++20、/MD、/fp:precise、x64 SSE2、Boost 1.86.0 et_off。

"""
    section8 = """## 8. 与设计的差异 / 比较口径、证据卫生与遗留

1. 未发现须修改设计的冲突；本轮没有修改设计、Python 数学合同或生产 C++。MAJOR-1 是门覆盖缺口，不是现有生产错数；保留下侧/上侧延续条件，新增宽括号与内部变异守护。
2. **MINOR-1 订正**：宽括号的非唯一 LP 基可导致两端实现证明强度不同；不是每一项 attained 都可当唯一字段。双方非空必须相等，仅单侧非空须通过独立数学与证书元合同核验，且逐项登记。20 个验收实例均在本轮重现，处置见第 4 节台账；不削弱 C++ 证明，也不豁免其他字段。Farkas 下端例保留 null 阈值。
3. **MINOR-2/静力注记**：第 4 节明确比较域，第 6 节补齐两个延续变异；第 2 节明确自由体与端板均使用锚点力矩及 y/机构锚点旋量；T1b 厚度只覆盖 binary64 精确 7 样点+18 对照，不能声称覆盖 32 个域外模型。
4. 原阶段范围仍然成立：ABI 不支持参数按调用失败返回、不发布 JSON；完整代数根对象、无理阈值 attained、任意参数敏感性/L4、可选自应力及稳定发布 ABI 未交付或未冻结。有理候选认证保守，不保证发现所有有理阈值。资源预算也不是全 L3 墙钟保证；P2 规模是报告而非性能门。
5. 本轮仅保留一个权威差分 gzip；旧差分与重复试运行、节点、原始日志、变异构建材料按 H1 追加外归档，逐文件原始/压缩 SHA 及读回核验见[旧证据映射](C3L3_repair_evidence/previous_archive.json)、[本轮映射](C3L3_repair_evidence/archive_manifest.json)和[总归档索引](../EVIDENCE_ARCHIVE.md)。冻结历史证据不重钉当前源码；外归档是本地保存，不是远端备份。
6. [卫生账](C3L3_repair_evidence/hygiene.json)按相对 `1b6b4f3` 的整体拟交付字节计算，并另列本轮相对 `c8718bb` 增量；门为净增 ≤2,000,000 B、修改/新增单文件 ≤1,000,000 B。编译产物不入库；UTF-8 无 BOM、换行一致、批处理 ASCII，`git diff --check` 通过。[完整性审计](C3L3_repair_evidence/delivery_integrity.json)核源、归档、链接和受测字节，最终只回填报告/归档索引及证据元数据，不改被测代码。
7. 报告回填检测到两份定向检查日志采用 PowerShell 默认 UTF-16LE；先追加归档原字节，再转为 UTF-8 无 BOM/LF，逐行内容与原始末行完全不变，未重跑或改写测试结果。[编码订正记录](C3L3_repair_evidence/encoding_corrections.json)保留原始/现行 SHA。

**仍需所有者行动**：Claude 对修复后临界参数路复验确认 MAJOR-1 关闭。`c8718bb` 的所有者新鲜树复现和静力路验收已据来函记录；本轮未自行创建 Git 树，也没有把作者自查当成修复后的非作者复验。

C3L3_PARTIAL：MAJOR-1 与 MINOR-1/2 返修及完整收尾验证已交付；待 Claude 对修复后临界参数路复验确认
"""
    (ROOT / "reports/codex/C3L3_report.md").write_bytes((intro + body + section7 + section8).encode("utf-8"))
    print("C3L3_REPAIR_REPORT_RENDERED")


if __name__ == "__main__":
    main()
