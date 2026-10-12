# R12FIXb 交付索引

## 当前有效交付

- [主报告](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_report.md)
- [当前 policy](file:///D:/eab-wt/cx-e2/tools/exact_construction_policy.json)
- [最终逐站点账本](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/local_review_decisions_release.json) · [最终统计](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/local_manifest_statistics_release.json)
- [最终全套 11508 节点](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/full_suite_release/summary.json) · [分片日志和逐节点审计](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/full_suite_release)
- [最终静态 CLI](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/static_gate_release.log) · [真实清单可维护性](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/real_policy_locality_probe.json)
- [安装机制复核（非 G6）](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/final_installed_manifest_review.md) · [复核机器结果](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/final_installed_manifest_review_verified.json)
- [最终验收状态](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/final_validation.json) · [源码／文档变更](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/CHANGE_INDEX.md)

## 改写、恢复及其余材料

- [数值改写](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/dynamic_rewrites.md) · [测试 helper 改写](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/test_helper_rewrite_changes.json) · [factory 等价](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/test_factory_data_equivalence.json)
- [机制红绿](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/final_mechanism_review.md) · [执行前字节副本](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/baseline) · [前后 SHA](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/changed_files.json)
- [全部其余材料目录](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence)：包含早期失败日志、审核、临时副本；不是每项都代表最终通过。

## 历史材料，不能当最终绿

- full_suite 是首轮失败；唯一最终全套是 full_suite_release。
- local_review_decisions.json、local_review_decisions_final.json 为中间版；当前为 local_review_decisions_release.json。
- 统计当前为 local_manifest_statistics_release.json，其他同前缀是历史版。
- final_static_gate.log 为 168 违例；final_static_gate_r2.log 是编码修复前的绿；最终为 static_gate_release.log。
- raw_* 为原始研究清单，不是准入报告。scan_candidates.py 的 Expr 反找节点错误已记录；准确 payload 捕获为 capture_actual_fingerprints.py。
- 初装和明确纠正脚本只供迁移审计，不是自动批量续签工具。不要用旧初装器重装 release。
- [165 条绑定更正](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/fingerprint_extraction_corrections.json) · [独立绑定复核](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/fingerprint_binding_review.json)
- [39 条 metadata 安装回执](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/local_manifest_amendments_applied.json) · [5 条编码修复回执](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/reason_encoding_repair_receipt.json)
- [TEMP 越界披露](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/dynamic_temp_scope_deviation.json)

当前 policy SHA-256：73fde62383d7064ad94b58523a79586015c056b3bc57cea7ea0dd6d30a0abffe
