# H1-fix：运行内守卫与冻结回归返修

## 处置

- **M1**：恢复原名 7 节点（晚导入 1、`(bad,bad)` 路径遍历 1、独立 import-origin 4、M4c AST 闭包 1）。不恢复历史源码字节钉；M4c 去掉“当前哈希等于自身重算”断言。原来删除 12 项中仅 5 项是真正退役。
- **M2**：`fast_nodes` 晋升 20 节点：M5a 首块 15、旋转 3、M5b 五例 1、M4c `[bb52]` 首帧 1。默认快档实际执行，不是仅收集。其余 M4c 14 家仍在全档。
- **m15/m18**：R3 门调用 `examples.verify()`，改名为“在冻结标签/区间上重执行证书和计数”；不再声称独立重求标签、首入时间或分类。恢复小型继承摘要实际 SHA 与摘要中诊断流 SHA 的交叉一致性断言，不读取外档完整流。robust 摘要恢复 schema、source-binding schema-id、总摘要及各 case 的首尾 source map 一致性。
- **m16**：137 项生产提交显式断言 `unknown`，工具版本显式断言含说明的 unknown 字符串；接受提交仍检查 40 位十六进制形态。这两门是**完整性检查**，不是语义替代门，不证明未知历史生产来源。
- **m19**：删除已退役逐文件字节钉的慢档死条目；恢复的 import-origin 四格改归快档。慢函数 220 条，AST 逐条核对后 0 死条目。

## 验收

| 执行 | 最后一行（原样） |
|---|---|
| M1 原版 7 节点 | `============================== 7 passed in 1.07s ==============================` |
| M1 实际副本组合变异 | `============================== 7 failed in 1.31s ==============================` |
| M2 默认快档 20 节点 | `============================= 20 passed in 5.35s ==============================` |
| 本范围全部定向门 | `============================= 30 passed in 4.84s ==============================` |

组合变异注入实际代码：`assert_run_sources_unchanged` 提前 return；`runtime_source_hashes` 在内部排除 `numeric_domain.py`；`REPLAY_SOURCE_FILES` 删除该文件。7 个失败分别归因于 2 个预期异常未抛、4 个独立 import-origin 缺项断言、1 个真实 AST 闭包不等断言，不是静态指纹或语法错误。

5 个修改测试文件的静态构造扫描 0 违例；生产数学代码未改、未跑全量回放、未改外档；全档及快档整体由主执行者统一运行。

## 节点账

- 相对 `476c5d6`：新增（恢复）7 节点，删 0 节点，R3 等量改名 1 节点；净 +7。
- 相对 H1 前：本分项退役 −5、新 H1 门 +4，净 −1。
- R3 旧名：`test_fixed_real_r3_subset_reexecutes_exact_certificate_labels_and_counts`。
- R3 新名：`test_fixed_real_r3_subset_reexecutes_certificates_and_counts_at_frozen_label_and_interval`。

## 证据

- [逐项摘要](summary.json)、[组合变异逐节点归因](m1_combined_mutant.json)、[原版记录](m1_control.json)
- [快档晋升执行记录](m2_fast_promoted.json)、[30 门定向记录](retained_guards_r3_integrity.json)
- [可复跑验收脚本](run_verification.py)、[静态与分档检查](static_and_tier_audit.json)、[编码检查](encoding_audit.json)
- 实际变异源码副本在 `reports/codex/H1_evidence/tmp/fix_verification/m1_combined_mutant/`（忽略目录，不交付大副本）。
