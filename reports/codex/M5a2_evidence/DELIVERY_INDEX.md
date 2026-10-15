# WO-M5a2 交付导航

最终状态与限制以中文主报告及其末行为准；所有新建、修改文件的路径和 SHA-256 见交付清单。

1. [中文主报告](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_report.md)
2. [文件与哈希清单](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/artifact_manifest.json)
3. [最终四片原始摘要](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/final_suite_r3/summary.json)
4. [逐节点收集与执行同一性](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/node_identity_audit.json)
5. [新门及全套性能](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/performance.json)
6. [交付边界与编码审计](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/delivery_audit.json)
7. [1810 步仿射分布与端点诊断](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/affine_full_summary.json)
8. [可独立复算的最小例](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/affine_minimal_examples.json)

## 六路交叉复核

- R1/R2：[仿射与回放](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/review_affine_replay.md)
- R3/R4：[静态准入与运行器](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/review_static_runner.md)
- R5：[精确代数与认证边界](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/review_exact.md)
- R6：[报告与最终证据一致性](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/review_report.md)

保留的早期轮次只用于审计历史，不能拼接为完成证据：`baseline_suite_r1` 超时为 RED；`final_suite_r1` 因审查修补作废；`final_suite_r2` 因恢复原文件换行格式作废。有效完整轮次仅为 `baseline_suite_r2` 与 `final_suite_r3`。

大于 1 MB 的日志、节点/执行记录及完整逐块中间表仅保留于 ignored `tmp/`，不在提交候选证据中；摘要中的完整执行记录哈希供本地追溯。
