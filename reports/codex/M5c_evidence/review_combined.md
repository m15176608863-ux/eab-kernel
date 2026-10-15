# M5c 联合证据发布器独立复核

## 首轮代码复核结论（历史记录）

**代码修补后专项 25 passed, 1 deselected in 0.91s；实际 1810 步联合发布尚未核验，不列绿。**
本复核只检查 `tools/m5c_publish_combined.py`、对应单元门和 scratch 数据反例；不把小语料测试当成全量执行证据。
最终仍须核对真实两流、研究 68 候选、全部源码/输入哈希和最终四片执行同一性。

## 发现、真实反例与修复

1. **COMBINED-REF-MASS（初审 major，已修）**：原实现的 `after_refs` 与算术替换都来自同一研究 replacement，
   不能证明物理参考行数守恒。scratch 中将一个候选的 PRIMARY 总数加一，同时修复 exact/compact/summary.references
   和 gzip 哈希，原发布器接受并发布了 **6→7**。证据保留在 `combined_review_total_probe.json`。
   作者已增加逐候选、逐阶段 PRIMARY/SECONDARY/SHARED_EDGE 三个物理总数不变，并核对命中/未命中分拆和 pair-level 回答。
   新 `reference_mass` 反例同步改哈希和分类分拆，仍在物理总数语义断言被拒绝。
2. **COMBINED-BLOCK-IDENTITY（覆盖补强，已修）**：原“每步完整组合”只由 raw 内出现的块号反推，
   旧/新/研究同时把块 3 改成不存在的块 4、且保持所有计数，不能证明真实输入覆盖。
   作者现独立读取全部已绑定 endpoint shard，按 `(case,step)` 建立实际 block ID 集合，再核对 raw 全组合。
   新 `invented_block` 门修复外围哈希后仍在真实端点身份断言拒绝。

## 其余核查

- **窗口覆盖**：15 算例集合相等，每例步号恰为 `1..steps`，每步实际块集合及所有无序块对完整；全局 1810/15220/64010 与清单相符。
- **候选不偏选**：从完整新流选择“初态分离且 P1 接触”，与旧流逐行候选谓词一致；68 个唯一 key 必须与研究 exact/compact key 集合完全相等。
- **精确观测**：旧/新逐行比较身份、分类和 P1/P2 的 status/features/time；两流长度、顺序、唯一性都检查。此为绑定证据连接，不冒称第二遍全块对根求解。
- **分类替换**：只允许从 `MODEL_SENSITIVE_OR_UNPROVED` 且 reason 为 `NO_SUFFICIENT_CERTIFICATE` 升级；每例、全局三分类及原因计数同步扣补，防负数；R2 子集恰为 2。
- **来源绑定**：旧/新 gzip 对其各自 summary 哈希；研究 inherited 流字典必须精确匹配本次实际使用旧流；新/研究源字典两端相等并逐项对当前文件；所有输入与源码再次检查。
- **完整闭包依赖**：发布器不重新导入求解器核算闭包。其来源完整性仍须由最终 A7 独立 import-origin 门支撑；不把“给定 map 中每项 hash 都对”误说成孤立证明 map 没漏项。
- **研究源码包含关系**：已补新回放核心文件必在 fresh map、研究 map 覆盖 fresh 全部文件且含诊断入口与 R3 核心文件的检查；`core_missing` 同步修复外围哈希仍被语义拒绝。
- **不可覆盖发布**：目标先查不存在，最终以独占 `x` 模式创建，写后验字节哈希；无效输入不应留下 complete 产物。旧文件字节保留门通过。中断 progress 不允许续接。
- **参考类别互斥（已补）**：已证不能残留 UNPROVED，未证不能残留 MATCH/已证 pair flags，任何新接触候选不得残留 NO_CONTACT 类别；两个修复外围哈希的残留反例由对应语义门拒绝。

## 首轮尚未核验（已由下文真实产物复核更新）

本报告不确认真实 `combined_summary.json` 已发布，不确认长跑已完成。最终执行同一性必须在真实全量流和四片证据齐备之后另核验。
专项唯一未选节点是 `test_frozen_combined_summary_has_complete_cohorts_current_sources_and_bound_upstream_summaries`，已显式按完整 nodeid deselect，而非模糊 `-k`；其必须在实际发布后执行，不计为通过或 skip。
当前源码指纹与专项计数见 `review_combined.json`。

## 真实发布后独立更新

真实 `combined_final_r1` 已发布；独立从原始gzip及tuple7重计1810步/64010对、全部68候选、19稳健子集参考与C初态参考，0会计失配；168项来源绑定当前一致。实际产物专项130 passed in 5.48s、0skip/0deselect。原首轮未选冻结产物门已在该真实专项执行，不再标记为待核。

详见[真实产物独立复核](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/review_final_artifacts.md)及[机器证据](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/review_final_artifacts.json)。最终全套四片仍待结束后另核；不提前宣称执行同一性通过。
