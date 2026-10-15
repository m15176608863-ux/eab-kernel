# M5c 交付工具独立审查

## 范围与状态

审查者 `/root/semantic_teeth`；仅修改父代理授权的三个未绑定新工具，未改生产、回放、研究或测试闭包。

**当前结论：21 项原始证据/合成反格检查通过；真正最终四片、真实联合发布与最终报告渲染仍 PENDING，绝不把合成 positive 当成正式全时程绿。**

- [报告生成器](file:///D:/eab-wt/cx-e2/tools/m5c_report.py)
- [执行审计器](file:///D:/eab-wt/cx-e2/tools/m5c_finalize_evidence.py)
- [交付清单器](file:///D:/eab-wt/cx-e2/tools/m5c_delivery_manifest.py)
- [机器复核记录](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/review_delivery_tools.json)

## 发现与最小修复

1. `finalize` 原来只检查**已存在的**阶段报告均 passed，遗漏 setup/teardown 仍可宣称“三阶段全过”。现按 `(nodeid, when)` 的 Counter 精确要求每个收集节点 setup/call/teardown 各一次；仍逐片核派发、收集、call、skip、退出码与超时。
2. 原末行只取 summary 字符串。现重新读取每片原日志，严格核原末行等于 summary；静态日志同理必须是 `exact construction AST gate: 0 violation(s)`，最终报告原样输出四行，不把基线四行混作最终。
3. 原当前工作树同一性只迭代 export manifest 的既有键，新增未执行测试不可见；也漏根 pytest 配置。现使用与导出器同域的只读 Git 文件枚举，核 `src/tests/tools/fixtures` 和根配置的文件集合双向差与逐字节 SHA。另重新读 fresh export，核完整文件集合与 manifest SHA，绑定原日志/执行记录/派发清单/manifest/summary/integrity 的开始与结束 SHA。
4. `delivery_manifest` 原来先写 `complete=true` 再因编码/尺寸违规抛错。现所有拒绝发生于写入前；加裸 CR、大小写后缀、JSONL 大日志与发布前再次核文件集/字节。差异以明确基线为参照，含暂存修改但未执行任何修改型 Git 命令。
5. 报告正文的固定数字现有显式机器断言：三类比较来源、G0 求值/交叉核对、64010 全对与68候选、19子集、逐算例守恒、参考物理类别、诊断最窄窗口计数、初态管反例、A5全行统计与准入分母。源码绑定检查与输入渲染前后哈希防陈旧发布。
6. 报告对 `FORMAL_ALL`（主+正式VV二参）与 `ALL`（再含有效共边候选槽）严格分列，19 子集 raw 主命中7、formal也7、含共边19；不把共边候选说成已选择/已用于求解。C 的正半径出口证书仍0，未实现检查明确写为 PARTIAL。
7. 独立对抗口径订正：920常值扰动同时核标签/括区；138独立端点扰动仅核状态/标签，不声称验证括区。90名义轨迹分母均为1，不冒称非恒定分母P2时刻扰动完整验证。
8. 跨工具实际输入发现：冻结研究 `by_case` 的 bbF038/bbS038 三个零计数字段为 JSON `false`（Counter初次update布尔的序列化遗留），原严格publisher会拒绝真实发布。已交作者在非绑定publisher做窄兼容：**仅这3字段的False→0**，其他bool/浮点/未知字段仍拒绝，并仍须等于68条精确行独立聚合。未改冻结研究摘要/源码；已复核该修复及作者反格证据。

## 验证

真正基线 `baseline_suite` 原始 13656 节点、16 个审计输入绑定、四片原末行复核通过。其不是本次最终套件。其余使用 ignored tmp 内独立四节点四片 fixture 或当前研究真实数据+明确合成的 combined 摘要；不改正式证据文件。

| 检查 | 结果 |
|---|---|
| actual_baseline_raw_audit | 接受（正格） |
| synthetic_four_shard_positive | 接受（正格） |
| missing_setup | 拒绝（反格） |
| missing_teardown | 拒绝（反格） |
| spoof_summary_last_line | 拒绝（反格） |
| missing_fourth_shard | 拒绝（反格） |
| nonzero_skip | 拒绝（反格） |
| extra_export_file | 拒绝（反格） |
| changed_export_bytes | 拒绝（反格） |
| new_unexecuted_test_detected | 拒绝（反格） |
| new_unexecuted_root_config_detected | 拒绝（反格） |
| manifest_positive | 接受（正格） |
| manifest_bom | 拒绝（反格） |
| manifest_mixed_newlines | 拒绝（反格） |
| manifest_bare_cr | 拒绝（反格） |
| manifest_large_log | 拒绝（反格） |
| report_known_counts_positive_synthetic_combined | 接受（正格） |
| report_comparison_denominator_drift | 拒绝（反格） |
| report_formal_shared_conflation | 拒绝（反格） |
| report_unimplemented_C_claim | 拒绝（反格） |
| report_missing_fourth_shard | 拒绝（反格） |

BOM、混合换行、裸CR、大日志反格还断言：拒绝后不存在新 `delivery_manifest.json` 或 `DELIVERY_INDEX.md`。所有脚本 AST 解析通过、UTF-8无BOM且LF；上述三工具为 stdlib。当前源码 SHA 与可复跑 scratch 探针路径在机器记录中。

## 尚待父代理最终执行

1. 冻结这三个工具，再执行完整四进程 fresh-byte-export 套件；不能执行后改工具再宣称源码一致。
2. 真正 `combined_summary.json` 发布后重新调用执行审计器与报告生成器；任何计数/绑定不符均应拒绝而非改哈希绕过。
3. 最后生成交付清单；独立核四片原末行、收集=执行、0skip、执行manifest与最终源码/测试/政策/fixture同一性。此处尚未完成，等待原始产物。
