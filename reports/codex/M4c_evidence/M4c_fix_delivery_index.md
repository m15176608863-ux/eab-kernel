# M4cFIX 交付索引

仅当前工作树修改；无 commit/push/Git 状态写操作。旧运行与损坏字节保留，不拼接。

- [中文处置报告](file:///D:/eab-wt/cx-e2/reports/codex/M4c_fix_report.md)
- [四片节点/源码最终复核](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_verification.json)
- [450 帧完整新批次](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/summary.json)
- [冻结前后差异](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_freeze_comparison.json)
- [1810 步域与 VV 全量统计](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_domain_audit.json)
- [历史作废/取代索引](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_history_index.json)
- [逐文件哈希](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_delivery_manifest.json)
- [交付检查](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_delivery_audit.json)

## 代码与证据全清单

下列为本单新增或修改且未被 Git ignore 排除的文件。运行节点清单、执行明细和大日志在已有 ignore 规则下，不计入提交清单。
历史忽略目录的新标记另由上面的历史索引完整记录。

- [回退锚点副本目录](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/tmp/fix_rollback)
- [新鲜验证字节副本](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/tmp/fix_final_suite_r2_export)

| 文件 |
|---|
| [docs/m4c_difference_ledger.md](file:///D:/eab-wt/cx-e2/docs/m4c_difference_ledger.md) |
| [docs/m4c_motion_entrance_design.md](file:///D:/eab-wt/cx-e2/docs/m4c_motion_entrance_design.md) |
| [fixtures/PROVENANCE.json](file:///D:/eab-wt/cx-e2/fixtures/PROVENANCE.json) |
| [fixtures/m4c_motion/expected.json](file:///D:/eab-wt/cx-e2/fixtures/m4c_motion/expected.json) |
| [reports/codex/M4c_evidence/M4c_fix_delivery_index.md](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/M4c_fix_delivery_index.md) |
| [reports/codex/M4c_evidence/baseline_suite/INVALIDATED.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/baseline_suite/INVALIDATED.json) |
| [reports/codex/M4c_evidence/baseline_suite_r2/INVALIDATED.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/baseline_suite_r2/INVALIDATED.json) |
| [reports/codex/M4c_evidence/environment_deviations.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/environment_deviations.json) |
| [reports/codex/M4c_evidence/final_suite_r2/SUPERSEDED.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/final_suite_r2/SUPERSEDED.json) |
| [reports/codex/M4c_evidence/fix_delivery_audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_delivery_audit.json) |
| [reports/codex/M4c_evidence/fix_delivery_manifest.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_delivery_manifest.json) |
| [reports/codex/M4c_evidence/fix_differential/README.md](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_differential/README.md) |
| [reports/codex/M4c_evidence/fix_differential/cases.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_differential/cases.json) |
| [reports/codex/M4c_evidence/fix_differential/pytest.txt](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_differential/pytest.txt) |
| [reports/codex/M4c_evidence/fix_differential/pytest.xml](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_differential/pytest.xml) |
| [reports/codex/M4c_evidence/fix_differential/run_differential.py](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_differential/run_differential.py) |
| [reports/codex/M4c_evidence/fix_differential/summary.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_differential/summary.json) |
| [reports/codex/M4c_evidence/fix_domain_audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_domain_audit.json) |
| [reports/codex/M4c_evidence/fix_final_suite/INVALIDATED.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite/INVALIDATED.json) |
| [reports/codex/M4c_evidence/fix_final_suite/collection.progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite/collection.progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite/m4c_execution_plugin.py](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite/m4c_execution_plugin.py) |
| [reports/codex/M4c_evidence/fix_final_suite/run_state.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite/run_state.json) |
| [reports/codex/M4c_evidence/fix_final_suite/shard_1.progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite/shard_1.progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite/shard_1.txt](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite/shard_1.txt) |
| [reports/codex/M4c_evidence/fix_final_suite/shard_1_node_progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite/shard_1_node_progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite/shard_2.progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite/shard_2.progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite/shard_2.txt](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite/shard_2.txt) |
| [reports/codex/M4c_evidence/fix_final_suite/shard_2_node_progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite/shard_2_node_progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite/shard_3.progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite/shard_3.progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite/shard_3.txt](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite/shard_3.txt) |
| [reports/codex/M4c_evidence/fix_final_suite/shard_3_node_progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite/shard_3_node_progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite/shard_4.progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite/shard_4.progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite/shard_4.txt](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite/shard_4.txt) |
| [reports/codex/M4c_evidence/fix_final_suite/shard_4_node_progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite/shard_4_node_progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/collection.progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/collection.progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/exact_construction.progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/exact_construction.progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/exact_construction.txt](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/exact_construction.txt) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/m4c_execution_plugin.py](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/m4c_execution_plugin.py) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/run_state.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/run_state.json) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/shard_1.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/shard_1.json) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/shard_1.progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/shard_1.progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/shard_1.txt](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/shard_1.txt) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/shard_1_node_progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/shard_1_node_progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/shard_2.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/shard_2.json) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/shard_2.progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/shard_2.progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/shard_2.txt](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/shard_2.txt) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/shard_2_node_progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/shard_2_node_progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/shard_3.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/shard_3.json) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/shard_3.progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/shard_3.progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/shard_3.txt](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/shard_3.txt) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/shard_3_node_progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/shard_3_node_progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/shard_4.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/shard_4.json) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/shard_4.progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/shard_4.progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/shard_4.txt](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/shard_4.txt) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/shard_4_node_progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/shard_4_node_progress.json) |
| [reports/codex/M4c_evidence/fix_final_suite_r2/summary.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_suite_r2/summary.json) |
| [reports/codex/M4c_evidence/fix_final_verification.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_final_verification.json) |
| [reports/codex/M4c_evidence/fix_freeze_comparison.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_freeze_comparison.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/batch_progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/batch_progress.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb03.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb03.log) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb03/audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb03/audit.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb03/normalized.jsonl.gz](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb03/normalized.jsonl.gz) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb03/progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb03/progress.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb05.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb05.log) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb05/audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb05/audit.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb05/normalized.jsonl.gz](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb05/normalized.jsonl.gz) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb05/progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb05/progress.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb06.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb06.log) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb06/audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb06/audit.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb06/normalized.jsonl.gz](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb06/normalized.jsonl.gz) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb06/progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb06/progress.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb09.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb09.log) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb09/audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb09/audit.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb09/normalized.jsonl.gz](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb09/normalized.jsonl.gz) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb09/progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb09/progress.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb10.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb10.log) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb10/audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb10/audit.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb10/normalized.jsonl.gz](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb10/normalized.jsonl.gz) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb10/progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb10/progress.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb12.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb12.log) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb12/audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb12/audit.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb12/normalized.jsonl.gz](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb12/normalized.jsonl.gz) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb12/progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb12/progress.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb50.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb50.log) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb50/audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb50/audit.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb50/normalized.jsonl.gz](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb50/normalized.jsonl.gz) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb50/progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb50/progress.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb51.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb51.log) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb51/audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb51/audit.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb51/normalized.jsonl.gz](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb51/normalized.jsonl.gz) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb51/progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb51/progress.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb52.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb52.log) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb52/audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb52/audit.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb52/normalized.jsonl.gz](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb52/normalized.jsonl.gz) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bb52/progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bb52/progress.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbF038.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbF038.log) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbF038/audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbF038/audit.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbF038/normalized.jsonl.gz](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbF038/normalized.jsonl.gz) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbF038/progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbF038/progress.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbS038.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbS038.log) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbS038/audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbS038/audit.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbS038/normalized.jsonl.gz](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbS038/normalized.jsonl.gz) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbS038/progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbS038/progress.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbv01.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbv01.log) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbv01/audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbv01/audit.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbv01/normalized.jsonl.gz](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbv01/normalized.jsonl.gz) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbv01/progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbv01/progress.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbv01_dbv01a.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbv01_dbv01a.log) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbv01_dbv01a/audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbv01_dbv01a/audit.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbv01_dbv01a/normalized.jsonl.gz](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbv01_dbv01a/normalized.jsonl.gz) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbv01_dbv01a/progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbv01_dbv01a/progress.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbv02.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbv02.log) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbv02/audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbv02/audit.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbv02/normalized.jsonl.gz](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbv02/normalized.jsonl.gz) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbv02/progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbv02/progress.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbv02_dbv02a.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbv02_dbv02a.log) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbv02_dbv02a/audit.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbv02_dbv02a/audit.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbv02_dbv02a/normalized.jsonl.gz](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbv02_dbv02a/normalized.jsonl.gz) |
| [reports/codex/M4c_evidence/fix_frozen_replay/bbv02_dbv02a/progress.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/bbv02_dbv02a/progress.json) |
| [reports/codex/M4c_evidence/fix_frozen_replay/summary.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_replay/summary.json) |
| [reports/codex/M4c_evidence/fix_frozen_revalidation.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_frozen_revalidation.json) |
| [reports/codex/M4c_evidence/fix_history_index.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_history_index.json) |
| [reports/codex/M4c_evidence/fix_history_integrity.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_history_integrity.json) |
| [reports/codex/M4c_evidence/fix_new_static.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_new_static.json) |
| [reports/codex/M4c_evidence/fix_plan.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_plan.json) |
| [reports/codex/M4c_evidence/fix_replay/final_review.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_replay/final_review.json) |
| [reports/codex/M4c_evidence/fix_replay/report_draft_review.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_replay/report_draft_review.json) |
| [reports/codex/M4c_evidence/fix_replay/static_repair.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_replay/static_repair.json) |
| [reports/codex/M4c_evidence/fix_replay/targeted_after_static_pytest.txt](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_replay/targeted_after_static_pytest.txt) |
| [reports/codex/M4c_evidence/fix_replay/targeted_pytest.txt](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_replay/targeted_pytest.txt) |
| [reports/codex/M4c_evidence/fix_replay/verification.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_replay/verification.json) |
| [reports/codex/M4c_evidence/fix_semantics/differential_review.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_semantics/differential_review.json) |
| [reports/codex/M4c_evidence/fix_semantics/differential_review_pytest.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_semantics/differential_review_pytest.log) |
| [reports/codex/M4c_evidence/fix_semantics/domain_document_review.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_semantics/domain_document_review.json) |
| [reports/codex/M4c_evidence/fix_semantics/mutation_evidence.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_semantics/mutation_evidence.json) |
| [reports/codex/M4c_evidence/fix_semantics/pytest_final.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_semantics/pytest_final.log) |
| [reports/codex/M4c_evidence/fix_semantics/pytest_initial.log](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_semantics/pytest_initial.log) |
| [reports/codex/M4c_evidence/fix_semantics/static_final.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_semantics/static_final.json) |
| [reports/codex/M4c_evidence/fix_static_policy_integrity.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_static_policy_integrity.json) |
| [reports/codex/M4c_evidence/fix_static_preflight.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_static_preflight.json) |
| [reports/codex/M4c_evidence/fix_static_preflight.txt](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/fix_static_preflight.txt) |
| [reports/codex/M4c_evidence/frozen_replay_r2/SUPERSEDED.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/frozen_replay_r2/SUPERSEDED.json) |
| [reports/codex/M4c_evidence/frozen_summary.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/frozen_summary.json) |
| [reports/codex/M4c_evidence/mutations_r1/INVALIDATED.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/mutations_r1/INVALIDATED.json) |
| [reports/codex/M4c_evidence/mutations_r2/SUPERSEDED.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/mutations_r2/SUPERSEDED.json) |
| [reports/codex/M4c_evidence/mutations_r3/SUPERSEDED.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/mutations_r3/SUPERSEDED.json) |
| [reports/codex/M4c_evidence/mutations_r4/SUPERSEDED.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/mutations_r4/SUPERSEDED.json) |
| [reports/codex/M4c_evidence/mutations_r5/SUPERSEDED.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/mutations_r5/SUPERSEDED.json) |
| [reports/codex/M4c_evidence/replay_pilot/INVALIDATED.json](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/replay_pilot/INVALIDATED.json) |
| [reports/codex/M4c_evidence/replay_report.md](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/replay_report.md) |
| [reports/codex/M4c_evidence/review_summary.md](file:///D:/eab-wt/cx-e2/reports/codex/M4c_evidence/review_summary.md) |
| [reports/codex/M4c_fix_report.md](file:///D:/eab-wt/cx-e2/reports/codex/M4c_fix_report.md) |
| [reports/codex/M4c_report.md](file:///D:/eab-wt/cx-e2/reports/codex/M4c_report.md) |
| [tests/m4c_independent_oracle.py](file:///D:/eab-wt/cx-e2/tests/m4c_independent_oracle.py) |
| [tests/test_m4c_fix_differential.py](file:///D:/eab-wt/cx-e2/tests/test_m4c_fix_differential.py) |
| [tests/test_m4c_fix_replay.py](file:///D:/eab-wt/cx-e2/tests/test_m4c_fix_replay.py) |
| [tests/test_m4c_fix_semantics.py](file:///D:/eab-wt/cx-e2/tests/test_m4c_fix_semantics.py) |
| [tools/m4c_fix_audit.py](file:///D:/eab-wt/cx-e2/tools/m4c_fix_audit.py) |
| [tools/m4c_motion_replay.py](file:///D:/eab-wt/cx-e2/tools/m4c_motion_replay.py) |
| [tools/m4c_run_gates.py](file:///D:/eab-wt/cx-e2/tools/m4c_run_gates.py) |
