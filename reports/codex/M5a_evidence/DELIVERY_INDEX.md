# M5a 交付索引

本索引的链接相对本目录。最终状态以[中文报告](../M5a_report.md)末行及机器审计为准，不能用历史或早期绿灯代替最终批次。

## 主交付

1. [中文完整报告](../M5a_report.md)：理论/API、逐项门、三个回放问题、四片原样末行与 PARTIAL。
2. [先行理论与具名门](../../../docs/m5a_se2_design.md)：条件、推导、证明范围及文献状态。
3. [SE(2) 核心](../../../src/eab/kernel2d/se2.py)、[精确实代数](../../../src/eab/kernel2d/algebraic.py)。
4. [450 帧冻结夹具](../../../fixtures/m5a_se2/)及[冻结摘要](frozen_summary.json)。
5. [交付文件 SHA 清单](artifact_manifest.json)：仅本单变更/新增，清单自身除外。

## 最终验收

- [最终四片摘要](final_suite_r1/summary.json)、[实际导出字节完整性](final_suite_r1/export_integrity.json)。
- [收集/执行节点同一性](node_identity_audit.json)、[交付字节/编码/大小审计](delivery_audit.json)。
- [性能对照](performance.json)、[环境](runtime_environment.json)、[起点基线](baseline_suite_r1/summary.json)。
- [独立交付复核](delivery_review.md)、[机器版](delivery_review.json)。
- [静态准入逐项说明](static_admissions.json)、[静态独立复核](static_review.md)、[全仓静态输出](static_full.txt)。
- [7 类真实内部源码变异](mutations_r2/summary.json)，该批不选择哈希绊线。

## 影子对账

- [中文回放说明](replay_report.md)、[三问与逐对/逐行结果](three_answers.json)、[1810 步摘要](full_summary.json)。
- [最小复现输入](minimal_examples.json)、[实际重新执行输出](minimal_examples_reproduced.json)。
- [回放与溯源门结果](replay_pytest.json)、[回放交付核对](replay_delivery_audit.json)。
- [M4c 原路径450帧新鲜重验证](m4c_frozen_revalidation.json)，旧夹具及逐帧结论不改。

## 研究审阅与执行历史

- [理论专题复核](theory_review.md)、[代数独立差分](algebra_random_independent_review.json)。
- [报告理论陈述复核](report_theory_review.md)、[报告回放陈述复核](report_replay_review.md)。
- [工作合同及失败处置](WORK_LOG.md)、[早期日志编码规范化](encoding_normalization.json)。

这些是限定范围的专题审阅，不是完整六路 G6。`tmp/`、大于1MB的执行记录与节点清单均为被忽略运行文件，不纳入提交。大记录由工具可重新生成；永久小摘要保存它们的哈希与逐项审计结果。
