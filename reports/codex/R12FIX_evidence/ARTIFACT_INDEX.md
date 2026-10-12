# R12FIX 交付与证据索引

## 正式交付

1. [中文修复报告](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_report.md)
2. [机读验收汇总](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/verification_summary.json)
3. [封闭子集实现](file:///D:/eab-wt/cx-e2/tools/exact_construction_subset.py)、[既有 scanner 接入](file:///D:/eab-wt/cx-e2/tools/check_exact_construction.py)
4. [正式逐站点人工审查 policy](file:///D:/eab-wt/cx-e2/tools/exact_construction_policy.json)
5. [112 个新增格子的永久门](file:///D:/eab-wt/cx-e2/tests/test_r12fix_static_closed.py)
6. [本树设计同步](file:///D:/eab-wt/cx-e2/docs/r12fix_design_sync.md)、[README](file:///D:/eab-wt/cx-e2/README.md)、[canon_map](file:///D:/eab-wt/cx-e2/docs/canon_map.md)
7. [全部文件/临时目录的 URI 与 SHA-256 清单](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/artifact_manifest.json)

## 最终验证

- [四进程完整 pytest 汇总](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/full_suite/summary.json)：保留原命令/原末行、收集集与执行集的精确集合验证，以及源码/政策/文档无漂移检查；不是串行单进程的计时。
- pytest 原日志：[片 1](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/full_suite/shard_1.log)、[片 2](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/full_suite/shard_2.log)、[片 3](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/full_suite/shard_3.log)、[片 4](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/full_suite/shard_4.log)。同目录 `*_nodes.json` 与 `*_results.jsonl` 保留每一项的收集/执行记录。
- [静态门零违例](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/static_gate.log)、[定向回归](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/targeted_regression.log)、[M4a 与文档](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/m4_and_documents.log)、[命令/耗时](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/targeted_verification.json)。
- [四个内部撤修变异的实际失败断言](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/mutation_teeth.json)
- [独立最终 policy 完整性复核](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/final_policy_review.json)、[报告文案复核](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/final_report_review.md)
- [3375 个 tracked 文件的 Git blob/原字节核对](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/tracked_scope_snapshot.json)

## 红证据、审查与中间材料

- [首次 40 格修前红](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/pre_fix_red.log)。其他 `pre_fix_*.log` 的原始末行及各自用途见正式报告；每类先确认真实漏报，再改 gate。
- [最终未豁免原始扫描](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/final_raw_scan_v2.json)、[未审清单（最终应为空）](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/policy_unreviewed_sites.json)。
- 正式 policy 的 `review_origin` 字段逐条指向本目录的审查清单。`initial_scan`、`strict_scan`、`latest_scan`、`admission_scan` 等是保留的历史策略实验，不能当最终接受清单。
- [一次定向 setup 环境错误](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/targeted_regression_environment_error.log)：basetemp 父目录尚未创建，279 passed / 1 setup error；已创建父目录重跑通过，未改测试超时或数值断言。
- [临时副本和 pytest 临时输出](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/tmp/)：不是新的生产实现或 fixtures 正本；全部路径在本工作树内，未删改原 fixtures。

## 重跑工具

- [定向验证捕获脚本](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/run_targeted_verification.py)
- [完整四分片运行脚本](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/run_full_suite.py)：新运行先指定未使用的 `$env:R12_RUN_NAME='full_suite_rerun_01'`，不覆盖本次日志；[只记录节点的 pytest 插件](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/r12_audit_plugin.py) 不改变测试选择。
- [变异证据捕获](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/record_mutation_teeth.py)、[验收读回脚本](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/final_verification_summary.py)
- [本次已审条目的一次性封装脚本](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/assemble_reviewed_policy.py)：**不是未来改动的自动授权工具**；不可不重新审核就用它更新依赖快照。正常 scanner 运行不会调用它。

原审查输入保留在 [G6L 输入目录](file:///D:/eab-wt/cx-e2/reports/codex/inputs/)，没有覆写。
