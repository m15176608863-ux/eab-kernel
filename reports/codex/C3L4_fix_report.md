# WO-C3L4-fix：阈值分支完备性修复轮

## 当前状态：实施与定向验证中（不是最终验收）

工作树 `D:/eab-wt/cx-c0`，HEAD `cb14522`，不 commit。开工完整四分片基线已绿；当前 Python/C++、独立 K checker 与验收小项已接入。最新 r7 完整构建、CTest、C0–L3 全集、发布 ABI 和 consumer 已绿；r7 元门、变异及收尾 Python 快档/全档四分片亦已绿；完整 L4 仍在运行。r5 快档/全档曾全绿，但随后非对称族暴露两项候选搜索遗漏，修复后必须重跑，不能作为当前源码最终验收。此前 RED/中断轮次不计为通过。原 BLOCKED 报告与反例原始数据已逐字节归档，见[历史映射](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/ruling_resume.json)、[压缩清单](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/historical_compaction.json)。Claude 续裁定已解除原定理前提阻塞。

## 定理与实现

见[设计澄清提案](file:///D:/eab-wt/cx-c0/docs/eab2_design_amendment_20261023.md)。采用完整稀疏 Fraction / Rational 多项式，不截断；按 epsilon 最低次、再 eta 最低次精确定号。上下两端分别核对偶可行与原侧可行点+改进射线，并核原始 `[0,mu_max]` 域内条件。所有系数从原始仿射顶点、锚点、荷载重建；一阶 dA/db/dc 不作为高阶系数来源。

候选只用于选基。候选上限 64，每候选最多 16 组探测点。双向独立认证，普通左导为 -Dminus；缺证方向不给值，不回退到单基隐函数值。域边界失败统一 `threshold_search_domain_boundary`。原搜索域含原始 binary64 位和精确有理，公开 C 布局不变。

## 当前已知定向结果（非最终总门）

- Python 既有定向门：`137 passed, 6 deselected in 64.16s (0:01:04)`。
- Python 双梁开/闭阈六项：`6 passed, 15 deselected in 548.79s (0:09:08)`。
- C++ 最新 r7 完整 CTest 15/15 已通过，几何种子 76 checks、ABI 101 checks；完整末行见 r7 execution/log，最终汇总待写。
- 非对称非零 dead/live 种子实际暴露 C++ 原侧 INFEASIBLE 时漏解对偶可行性及候选覆盖问题，已修复并经独立 K 核验；未豁免“不弱于 Python”门。
- 奇异候选标签的完整性、多项式系数、斜率及 upper ray 缺失均有独立正负门；应用后的 checker/harness/单侧证明比较定向复测为 `131 passed in 184.24s (0:03:04)`。完整 L4 总结果待补。
- 非对称下边界追加修复：Python 不再因初候选 s=0 越域而跳过后续候选探测；C++ 候选根隔离前精确 square-free，避免 `v²(v−7/128)` 在零端点漏掉正根。最终域内 K 条件、原始多项式证据和能力门均未放宽。两项内部变异均被真实数值断言杀死，首源完整六通道 `C3L4_DIFF sensitivity=6 mismatch=0`、10 个认证侧均通过精确差商红旗。见[修复记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/tmp/r6_cpp_domain_diag/r16_repeated_root_fix.md)。

## 验证与归档入口

- [基线四分片汇总](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/baseline_full/summary.json)
- [连续进度](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/progress.json)
- [最终验证运行器](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/final_runner.py.txt)
- [验收小项记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/abi_minor_results.md)

## 尚待填入的最终证据

候选/证书逐族统计、语料与 errata、非对称红旗、内部变异、完整构建六层、发布 ABI/consumer、Python 快档与收尾四分片原始末行、相对 b34c966 的候选树真实净增。所有者新鲜 Git 树及非作者对抗核查记为**待所有者验收**，不算 Codex PARTIAL。

### r7 已完成阶段（完整 L4 尚未完成）

源码固定的 build、C0–L3、meta、mutations、Python stage 均完成且前后 hash 相同。
实际 CTest：`100% tests passed, 0 tests failed out of 15`，敏感性：`sensitivity: 374 checks passed`。
元门：`C3L4_META cases=64 channels=163 mismatch=0`；7+5+2 项既有内部变异均被预期语义门拒绝。
完整命令及日志见 [r7 验证目录](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/tmp/c3l4fix_final_r7/)。

收尾 Python 快档和全档原始末行：

```text
9268 passed in 831.96s (0:13:51)
3840 passed in 1729.96s (0:28:49)
3840 passed in 985.47s (0:16:25)
3839 passed in 1373.94s (0:22:53)
3839 passed in 1282.69s (0:21:22)
exact construction AST gate: 0 violation(s)
```

全档共 15,358，快/全档执行与收集节点多重集合一致，0 skip、0 failed、模块执行覆盖完整、源字节未变。
这不代替尚在运行的完整 L4，也不作最终 DONE 判定。

当前文档是过程记录，不标 DONE；最终将补工单判定。


## WO-C3L4-fix-close：草稿归并说明（2026-10-24）

以下 Claude 章节草稿按原字节追加，保留草稿中的两个占位符供所有者填入；其中“Codex 不再参与”是此前阶段叙述，不否认本单仅执行收尾杂活。草稿的数值与对抗结论未由本单重新代验。当前收尾命令、内部变异复跑及边界见[收尾报告](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_close_report.md)。


## 修复轮验收与返修（Claude 亲自收尾，2026-10-23 晚至 10-25）

Codex 在 r7 验证做到只剩 L4 全族长跑时被所有者停用；此后的生产代码返修由 Claude 完成，收尾杂活（工具入库、证据打包、变异门复跑、文档对账、卫生审计）按用户 10-24 的分工交给 Codex（WO-C3L4-fix-close，见[收尾报告](C3L4_fix_close_report.md)）。待验收提交链：5bdcf01 → 88f3fd7 → 47691cc → d4fe002 → 64b499f → 89662f8 → 208eef7 → fa481ba。

### 第一轮：5bdcf01 的四路非作者对抗

- **真值路**（精确有限差分，与设计无关）：语料 280 + T1b 36 行 + 上轮被驳的全部用例 + 74 个新多分支 / 域边界构型，**1596 个认证方向全部落在收敛差商括号内，0 个假值**；上轮被驳的 43 个开阈例全部改正。
- **定理路**（纯数学反驳）：单调嵌套、有序域语义、夹逼极限、域条件编码、符号约定、弱对偶八项前提**无一被推翻**；34 份证书独立 K 核验成立。两条 minor（边界 reason 语义、骨架一阶不变未在证书路径检查）写入澄清提案 §2、§6。
- **不倒退路**：402 条冻结语料 0 失配；0 条认证值变为不同认证值；上轮 15 个小项逐个验有牙。
- **证书路**：未写出结论（第二轮补做）。

三路 not_close 的共同原因是同一个 **major**：C++ 在部分非对称通道上比修后 Python 弱，违反本轮自定的"C++ 证明能力不弱于修后 Python"门；且差分遇到能力退化时整例中止。

### 返修内容（生产代码与工具）

1. **齐次对偶见证**（两后端）：下端探测点原问题不可行时改解 `max cᵀx, Ax=0, x≥0`，它恰在 `Aᵀy≥c` 可解时 OPTIMAL，精确对偶是带 m 个独立紧列的基本点。
2. **见证基重试**（两后端）：保留本方向各探测点见过的下端对偶基、上端点基与射线基（C++ 另加"裁判式"基），缺哪端就用最近 6 组已见基在当前探测点重新提升并核 K；复用基须在记录的有理探测点非负。
3. **探测几何自身阈值生成候选**（两后端）：全部顶点派生候选失败后，固定 ε=2^-24，在原始域上对 μ 二分 56 步（矩阵元对 μ 仿射，A(μ)=A(0)+μ(A(1)−A(0))），取商括号最简有理数作候选；内部阈值与边界阈值都走这一路（边界上向外夹逼仍被域条件拒绝）。
4. **筛选探测**（两后端同规则）：每个候选先用一对 LP（ε=2^-24、η=2^-8）筛选，下端须取得对偶见证、上端须无界，才进 16 点网格与提升；被筛掉的候选仍贡献其基。这是搜索预算裁剪——此前重试与兜底叠加后，Python 裁判在随机种子通道上单条可达一小时。
5. **定向顶点**（两后端）：上端点 / 射线提升在 K 中失败时，对每个为负的分量 j 在筛选点多面体上再解 `max r_j` / `max x_j`（最多 8 个），顶点基立即在当前探测点提升核验；C++ 另把无界值 LP 自带的可行点与归一化改进射线作为见证基。
6. **有序域换基修复**（C++）：t1b/06、t1b/15 单面反向（真值 0）上，LP 核在全部探测点都返回同一个在 K 中恰有一个分量为负的退化射线顶点。C++ 对本探测点自取的点 / 射线公式做有序域对偶单纯形修复（Bland 规则、零目标、≤32 步），修好的见证在更细的二进日程上取第一个使其非负的点作为记录探测点（探测点不是定理前提，只为证书可独立复核）。Python 不做此修复，C++ 因此可能多证出方向。
7. **形状不变量**（两后端）：某方向只有在下端对偶、上端点、上端射线三份 K 证书齐全时才算 certified，否则改报 unresolved（`internal_certificate_shape`）。具名门：Python `test_certified_direction_without_witnesses_is_never_a_value`、穷尽路线门；C++ 测试缝 `SensitivityOptions2.test_witnessless_slope` 与 `certified_shape_invariant_neutralises_witnessless_slope`。
8. **差分与工具**：能力退化记为该查询失配并继续比较其余通道；经独立 K 核验的 C++ 独有认证方向登记为 `verified_cpp_only_branch_slope` 处置（floor 门不变）；非对称族加有限承载力荷载通道 `asym_limit_dead_live`（G5 走 Mills–Freund，使"漏活载列"变异在差分层变红），仅对有接触原语的源生成（非对称族 161 源，`coverage_separated` 不在其内）；核验器绑定调用方请求的 `mu_max_binary64`、接受新 reason。
9. **静态构造门清零**：去掉生产模块里的 os/sys/print 跟踪、`max()`/`sum()` 改显式循环、闭包提到模块级、有理探测点复核并入 `_vector`（由记录的 probe 字符串重建有理数）；**撤回"ε 按种子幅值缩放"**（缩放因子被静态门判为带舍入标记，探测点只选基、不进证明）。`exact construction AST gate: 0 violation(s)`。
10. **其他**：新具名 C++ 门 `branch_pure_load_jet_corpus_regression`；C++ 单测拆轻（默认约 3 分钟，完整扫描 `--branch-sweep`）；头文件注明 `EAB2_ASSEMBLY_COMPLETE` 须与 `EXPLICIT_PAIRS` 合用；失效证据链接改指压缩映射；澄清提案逐条补写上述规则。

### 第二轮：88f3fd7 的三路非作者对抗

- **证书路**：自写 K 域核验器复核 144 份证书全部成立；伪造 47 例全部被拒（含 η 先于 ε、截断多项式、域外夹逼、收窄的 μ_hi、探测点可行但 K 中为负、r_α=2·分母、跨查询拷贝）；"报值无证书"两类变异只被差分核验器拦、无具名门（→ 第 7 项）；上轮 major 在其抽样各族中已关闭。
- **真值路**：1035 + 77 个认证方向全部落在收敛差商括号内、0 假值；仅余 t1b/03 单面反向 C++ 弱于 Python（→ 第 5 项）。
- **审查路**：未写出结论（第三轮补做）。

### 第三轮：64b499f 的两路非作者对抗

- **审查路**：逐项核了齐次对偶引理（400 例）、μ 仿射性（20000 例）、最简有理数（5004 例）、秩选择（600 例）、重试与裁判式基的下标一致性、定向顶点不泄漏取得点、探测点一致性检查、差分不整例中止与荷载通道符号约定；**未发现任何能在缺完整 K 证书时签值的路径**；t1b/03 两后端两方向一致，24 个认证方向复核成立。not_close 仅因 C++ 形状不变量的"具名门"是空的（→ 第 7 项补齐）及若干 minor（筛选条件两后端略异、定向顶点先于重试窗口、Python 不变量未清空候选、`_probe_targeted` 射线多面体右端项、核验器白名单），均已修。
- **变异牙路**：判 close——无变异能签出错值；172 份证书独立复核全部成立；静态门有牙（加 `import os` 即红）。

### 所有者新鲜 Git 树复现（fa481ba，`D:/eab-wt/c3l4fix-fresh`）

- 构建 + C++ 单测 15/15；`EAB2_DIFF samples=4483 bits=6003 mismatches=0 status=PASS`；`C1_DIFF selected=657 completed=657 mismatches=0 layer_queries=100086`；`OPT_DIFF selected=745 completed=745 mismatches=0`；`C3L1_DIFF assembly=186 first_order=186 lock=404 mismatch=0 strict_fields=495`；`C3L3_DIFF limit=292 critical=2528 mismatch=0`；`EAB2_RELEASE_ABI status=PASS exports=31 structures=28 findings=0`；`EAB2_TIA_CONSUMER cases=6 sensitivity=18 mismatch=0`；`C3L4_META cases=64 channels=163 mismatch=0`。
- L4 全族按 4 个冻结族 + 6 个非对称分片并行，10 个进程退出码全为 0：formal `sensitivity=280 mismatch=0`、t1b `72/0`、thickness `50/0`、branch `14/0`、非对称六片 `140/0`、`139/0`、`140/0`、`141/0`、`142/0`、`134/0`；合并 `L4_SHARD_AGGREGATE cases=341/341 sensitivity=1252 mismatch=0`。
- Python 全档四分片：`collected 15421 passed 15421`，`SUITE_GREEN`。
- 证据：[所有者运行索引](C3L4_fix_evidence/owner_run_fa481ba/owner_run_manifest.md)（打包工具对按 PID 记录的分片退出码与另一目录的 Python 全档如实标 pending，真实值见本节与 `python_full_run.txt`）、[errata 台账](C3L4_fix_evidence/owner_run_fa481ba/errata_ledger.md.gz)。相对 cb14522 已验收的 402 条：160 条不变、27 条仅 quality 变、143 条 reason 与 quality 变、70 条仅 method 变、2 条由 unresolved 升为认证（μ*=0 右导 1，第一轮真值路已核），**0 条认证值改变、0 条认证值丢失**；另有 850 条新查询（非对称族与 branch 族）。

### 遗留（如实）

- L3 在 b≠0 且阈值下方 OPTIMAL 时只给括号不给精确阈值，这类方向 unresolved（两后端一致；属 C3-L3 能力边界）。
- 撤回 ε 缩放后，2^20 量级种子（第一轮真值路 J6）的正向可能重新 unresolved——只损能力、不损正确性，最终构建未单独复验。
- 证书路径不核骨架一阶不变（澄清提案 §6）；边界 reason 不区分"向外"与"向内未找到"（§2）。
- 候选生成（含筛选、定向顶点、换基修复）是搜索预算，不是完备性：证不出的方向仍可能有干净的有限真值。
- `tools/eab2_fix_close_audit.py` 的"主报告末行须为待验收标记"检查只适用于收尾轮当时的状态，所有者定稿后不再满足，属预期。
- 仓库内 10 个 b34c966 之前就带 BOM 的旧文件未动。

所有者判定：**C3-L4 修复轮验收通过**（2026-10-25，Claude）。

C3L4FIX_DONE
