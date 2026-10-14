# M4c 交付索引

状态以 [总报告](../M4c_report.md) 和最终 [delivery_audit.json](delivery_audit.json) 为准。
最终硬门已闭环：1810 + 450 区间、12974 测试、0 skip、静态 0 违例；交付状态为 **M4c_PARTIAL**，不是里程碑正式退出。

## 定义、代码与入库门

- [理论设计](../../../docs/m4c_motion_entrance_design.md)
- [闭集差异台账](../../../docs/m4c_difference_ledger.md)
- [运动首入内核](../../../src/eab/kernel2d/motion.py) / [PD_closed 快查询](../../../src/eab/kernel2d/motion_exit.py)
- [L5 回放](../../../tools/m4c_motion_replay.py) / [批次与重审工具](../../../tools/m4c_run_replays.py)
- [冻结端点](../../../fixtures/m4c_motion/endpoints.json) / [冻结预期](../../../fixtures/m4c_motion/expected.json)
- [运动门](../../../tests/test_m4c_motion.py) / [PD 门](../../../tests/test_m4c_exit.py) / [数值门](../../../tests/test_m4c_numeric.py)
- [台账输入门](../../../tests/test_m4c_replay.py) / [汇总门](../../../tests/test_m4c_summary.py) / [最小例复算门](../../../tests/test_m4c_examples.py)

## 完整计算与最小复现

- [全时程摘要](full_summary.json) / [冻结摘要](frozen_summary.json)
- [四问计数与精确分母](four_questions.json) / [最小端点例](minimal_examples.json)
- [最小例复算结果](minimal_examples_reproduced.json) / [复算工具](../../../tools/m4c_reproduce_examples.py)
- [post 两对无任何首盖参考的完整例](review_probes/post_no_first_cover_pairs.json) / [专项复算](review_probes/post_no_first_cover_pairs_check.json)
- [回放输出哈希索引](replay_artifact_manifest.json)
- [最终全套](final_suite_r2/summary.json) / [六项变异](mutations_r6/summary.json)
- [全时程完整批次重审](full_batch_revalidation.json) / [冻结完整批次重审](frozen_batch_revalidation.json)
- [交付审核](delivery_audit.json) / [工作树成果 SHA256 清单](artifact_manifest.json)

全时程大文件留在忽略的 `full_replay_r4/`；规范化冻结记录在 `frozen_replay_r2/` 入库。
大日志、节点清单、执行明细和新鲜导出副本留在忽略路径，不把它们伪装成应提交的小文件。

## 审查与偏差

- [运动学源码/导出审计](kinematics_audit.md)
- [核心与 PD 独立审查](review_kernel_pd.md) / [输入与预测审查](review_inputs_prediction.md)
- [汇总层审查](review_summary.md) / [可复跑专项探针](review_probes/)
- [报告语义边界复核](review_report_semantics.md)
- [四分片运行器与节点复核](review_runner.md) / [夹具中央溯源补登](fixture_provenance_registration.json)
- [收尾前严格需求清单](requirements_review.md)（历史检查点，不替代最终交付审核）
- [两次中断及主动废弃记录](interruption_recovery.md)
- [TEMP 工作域偏差](environment_deviations.json)
- [当前进度](WORK_STATUS.json)
- [运行环境与计时口径](runtime_environment.json)

全部几何结论限定在报告写明的域及分母；没有 b-DDA 检测替换、在线切换或工程物理正确性结论。
