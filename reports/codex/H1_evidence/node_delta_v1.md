# H1 逐节点数量差异账

状态：完整匹配。
只核收集节点，不声称执行、通过或无 skip；全档运行记录另列。

- 原收集：13877；新收集：13907。
- 退役 12/12；新增 42/42；等量改名 11/11 对。
- 原始集合差：删 23、增 53；净变化 +30。
- 预期：13877 − 12 + 42 = 13907；11 对改名净变化 0。
- 新增：纯度 6 + P3 28 + 大小 3 + 冻结数据/语义 4 + 模块执行烟测 1 = 42。

## 输入

- old：`D:\eab-wt\cx-e2\reports\codex\H1_evidence\tmp\baseline_temp\collection.txt`；编码 `utf-8-sig`；SHA256 `3814ef021053669940b9d1592ae58fae218ddaefd3787f2d21f5add63934758b`。
- new：`D:\eab-wt\cx-e2\reports\codex\H1_evidence\tmp\final\collection.txt`；编码 `utf-8-sig`；SHA256 `26d504920cba316d255fae3e815a6d7d5845c2c15453e2e8df906acaf5b2cc1a`。

## 退役 12 个节点

| 节点 | 已观察 |
|---|---|
| `tests/test_m4c_fix_replay.py::test_frozen_hash_scope_is_exact_replay_import_closure_with_posix_keys` | True |
| `tests/test_m5c_combined_evidence.py::test_combined_join_rejects_incomplete_or_inconsistent_evidence_without_publishing[research_wrong_sources-hash mismatch]` | True |
| `tests/test_m5c_policy_binding.py::test_changing_any_transitive_source_file_in_a_scratch_copy_is_rejected[m5b_endpoint_replay]` | True |
| `tests/test_m5c_policy_binding.py::test_changing_any_transitive_source_file_in_a_scratch_copy_is_rejected[m5b_robust_replay]` | True |
| `tests/test_m5c_policy_binding.py::test_frozen_summaries_bind_every_runtime_transitive_source_at_both_ends[m5b_endpoint_replay-endpoint_summary.json]` | True |
| `tests/test_m5c_policy_binding.py::test_frozen_summaries_bind_every_runtime_transitive_source_at_both_ends[m5b_robust_replay-robust_summary.json]` | True |
| `tests/test_m5c_policy_binding.py::test_new_runtime_import_after_start_invalidates_the_sealed_closure` | True |
| `tests/test_m5c_policy_binding.py::test_runtime_source_closure_matches_independent_import_origins_and_kills_omission[False-m5b_endpoint_replay]` | True |
| `tests/test_m5c_policy_binding.py::test_runtime_source_closure_matches_independent_import_origins_and_kills_omission[False-m5b_robust_replay]` | True |
| `tests/test_m5c_policy_binding.py::test_runtime_source_closure_matches_independent_import_origins_and_kills_omission[True-m5b_endpoint_replay]` | True |
| `tests/test_m5c_policy_binding.py::test_runtime_source_closure_matches_independent_import_origins_and_kills_omission[True-m5b_robust_replay]` | True |
| `tests/test_m5c_policy_binding.py::test_source_binding_rejects_parent_traversal_even_with_matching_content` | True |

替代语义门、退役原因逐条见 [冻结证据说明](../../../docs/frozen_evidence.md)。

## 新增 42 个节点

### hash_data_and_semantics（4）

| 节点 | 已观察 |
|---|---|
| `tests/test_h1_frozen_data.py::test_frozen_data_hashes_are_preserved_without_current_source_pins` | True |
| `tests/test_h1_frozen_data.py::test_frozen_data_integrity_rejects_an_actual_same_size_input_edit` | True |
| `tests/test_h1_frozen_semantics.py::test_fixed_real_r3_subset_kills_an_internal_radius_budget_defect` | True |
| `tests/test_h1_frozen_semantics.py::test_fixed_real_r3_subset_reexecutes_exact_certificate_labels_and_counts` | True |

### kernel_purity（6）

| 节点 | 已观察 |
|---|---|
| `tests/test_kernel_purity.py::test_kernel_domain_purity` | True |
| `tests/test_kernel_purity.py::test_kernel_domain_vocabulary_covers_required_tokens_and_spelling` | True |
| `tests/test_kernel_purity.py::test_kernel_purity_follows_transitive_imports` | True |
| `tests/test_kernel_purity.py::test_kernel_purity_rejects_actual_source_mutations[from eab.adapters import bdda2d\n-forbidden import path]` | True |
| `tests/test_kernel_purity.py::test_kernel_purity_rejects_actual_source_mutations[mtype = 0\n-domain token mtype]` | True |
| `tests/test_kernel_purity.py::test_only_real_docstrings_are_exempt` | True |

### p3_adopted_semantics（3）

| 节点 | 已观察 |
|---|---|
| `tests/test_h1_adopted_semantics.py::test_c1_b_ring_convexity_uses_b_radius_when_a_is_exact` | True |
| `tests/test_h1_adopted_semantics.py::test_c1_ranking_must_include_other_feature_family_competitors` | True |
| `tests/test_h1_adopted_semantics.py::test_replay_box_shortcut_adds_independent_radii_before_certifying_separation` | True |

### p3_entrance_symmetry（25）

| 节点 | 已观察 |
|---|---|
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation0-scale0]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation0-scale1]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation0-scale2]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation1-scale0]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation1-scale1]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation1-scale2]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation2-scale0]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation2-scale1]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation2-scale2]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation3-scale0]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation3-scale1]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation3-scale2]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation0-scale0]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation0-scale1]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation0-scale2]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation1-scale0]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation1-scale1]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation1-scale2]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation2-scale0]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation2-scale1]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation2-scale2]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation3-scale0]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation3-scale1]` | True |
| `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation3-scale2]` | True |
| `tests/test_h1_entrance_symmetry.py::test_symmetry_parameter_cells_produce_distinct_reference_geometries` | True |

### repository_size（3）

| 节点 | 已观察 |
|---|---|
| `tests/test_repository_size.py::test_every_tracked_or_deliverable_file_is_at_most_one_megabyte_except_frozen_policy` | True |
| `tests/test_repository_size.py::test_export_ignores_only_declared_runtime_outputs_and_keeps_other_evidence` | True |
| `tests/test_repository_size.py::test_no_git_export_gate_reads_actual_files_and_catches_oversized_candidate` | True |

### fast_declarative_module_execution（1）

| 节点 | 已观察 |
|---|---|
| `tests/test_h1_module_execution.py::test_declarative_modules_execute_in_fast_test` | True |

## 等量改名 11 对（净 0）

| 分类 | 原节点 | 新节点 | 理由 | 已观察两端 |
|---|---|---|---|---|
| test_name | `tests/test_m4c_replay.py::test_frozen_full_computation_is_bound_to_current_production_sources` | `tests/test_m4c_replay.py::test_frozen_full_computation_retains_historical_coverage` | 退役当前源码 pin，保留历史覆盖及既有真实首帧回归 | True |
| test_name | `tests/test_m5a_replay.py::test_frozen_family_products_are_distinct_and_bound_to_current_source` | `tests/test_m5a_replay.py::test_frozen_family_products_are_distinct_and_retain_historical_revalidation` | 退役当前源码 pin，保留历史族互异性与复核数据 | True |
| test_name | `tests/test_m5c_combined_evidence.py::test_frozen_combined_summary_has_complete_cohorts_current_sources_and_bound_upstream_summaries` | `tests/test_m5c_combined_evidence.py::test_frozen_combined_summary_has_complete_cohorts_and_bound_upstream_data` | 退役当前源码 pin，保留完整 cohort 与上游数据绑定 | True |
| publication_parameter | `tests/test_m5d_frozen_publication.py::test_publication_closure_drift_rejects_and_restores_every_written_target[source_hashes-0]` | `tests/test_m5d_frozen_publication.py::test_publication_closure_drift_rejects_and_restores_every_written_target[inherited_stream_hashes-0]` | 以输入数据漂移替代历史源码漂移；同一发布阶段原子回滚门仍在 | True |
| publication_parameter | `tests/test_m5d_frozen_publication.py::test_publication_closure_drift_rejects_and_restores_every_written_target[source_hashes-1]` | `tests/test_m5d_frozen_publication.py::test_publication_closure_drift_rejects_and_restores_every_written_target[inherited_stream_hashes-1]` | 以输入数据漂移替代历史源码漂移；同一发布阶段原子回滚门仍在 | True |
| publication_parameter | `tests/test_m5d_frozen_publication.py::test_publication_closure_drift_rejects_and_restores_every_written_target[source_hashes-3]` | `tests/test_m5d_frozen_publication.py::test_publication_closure_drift_rejects_and_restores_every_written_target[inherited_stream_hashes-3]` | 以输入数据漂移替代历史源码漂移；同一发布阶段原子回滚门仍在 | True |
| publication_parameter | `tests/test_m5d_frozen_publication.py::test_publication_closure_drift_rejects_and_restores_every_written_target[source_hashes-None]` | `tests/test_m5d_frozen_publication.py::test_publication_closure_drift_rejects_and_restores_every_written_target[inherited_stream_hashes-None]` | 以输入数据漂移替代历史源码漂移；同一发布阶段原子回滚门仍在 | True |
| publication_parameter | `tests/test_m5d_frozen_publication.py::test_publication_closure_drift_rejects_and_restores_every_written_target[source_hashes-after_final_check]` | `tests/test_m5d_frozen_publication.py::test_publication_closure_drift_rejects_and_restores_every_written_target[inherited_stream_hashes-after_final_check]` | 以输入数据漂移替代历史源码漂移；同一发布阶段原子回滚门仍在 | True |
| readme_history_path | `tests/test_r9fix_docs.py::test_current_contract_gate_rejects_deleted_current_boundary[README.md-\u968f\u540e\u5df2\u7ecf\u8fc7 G6 \u7b2c\u4e8c\u81f3\u7b2c\u4e94\u8f6e\u72ec\u7acb\u91cd\u5ba1-canon_map\uff08\u672a\u7ecf G6\uff09-required1-canon map has historical independent review, not current M0 exit]` | `tests/test_r9fix_docs.py::test_current_contract_gate_rejects_deleted_current_boundary[docs/history/README_through_20261019.md-\u968f\u540e\u5df2\u7ecf\u8fc7 G6 \u7b2c\u4e8c\u81f3\u7b2c\u4e94\u8f6e\u72ec\u7acb\u91cd\u5ba1-canon_map\uff08\u672a\u7ecf G6\uff09-required1-canon map has historical independent review, not current M0 exit]` | 原 README 原样移入历史文档，旧边界核查继续指向原文 | True |
| readme_history_path | `tests/test_r9fix_docs.py::test_current_contract_gate_rejects_reintroduced_old_text[README.md-\u968f\u540e\u5df2\u7ecf\u8fc7 G6 \u7b2c\u4e8c\u81f3\u7b2c\u4e94\u8f6e\u72ec\u7acb\u91cd\u5ba1-canon_map\uff08\u672a\u7ecf G6\uff09-required1-canon map has historical independent review, not current M0 exit]` | `tests/test_r9fix_docs.py::test_current_contract_gate_rejects_reintroduced_old_text[docs/history/README_through_20261019.md-\u968f\u540e\u5df2\u7ecf\u8fc7 G6 \u7b2c\u4e8c\u81f3\u7b2c\u4e94\u8f6e\u72ec\u7acb\u91cd\u5ba1-canon_map\uff08\u672a\u7ecf G6\uff09-required1-canon map has historical independent review, not current M0 exit]` | 原 README 原样移入历史文档，旧边界核查继续指向原文 | True |
| readme_history_path | `tests/test_r9fix_docs.py::test_current_contracts_do_not_repeat_superseded_status[README.md-\u968f\u540e\u5df2\u7ecf\u8fc7 G6 \u7b2c\u4e8c\u81f3\u7b2c\u4e94\u8f6e\u72ec\u7acb\u91cd\u5ba1-canon_map\uff08\u672a\u7ecf G6\uff09-required1-canon map has historical independent review, not current M0 exit]` | `tests/test_r9fix_docs.py::test_current_contracts_do_not_repeat_superseded_status[docs/history/README_through_20261019.md-\u968f\u540e\u5df2\u7ecf\u8fc7 G6 \u7b2c\u4e8c\u81f3\u7b2c\u4e94\u8f6e\u72ec\u7acb\u91cd\u5ba1-canon_map\uff08\u672a\u7ecf G6\uff09-required1-canon map has historical independent review, not current M0 exit]` | 原 README 原样移入历史文档，旧边界核查继续指向原文 | True |

## 未匹配项

无；未使用前缀白名单或忽略未知节点。

## 复跑

```powershell
python tools/h1_node_delta.py --old <基线收集文件> --new <收尾收集文件>
```

未知变化、预期缺失、重复节点、收集数不符或收集错误均返回非零状态。
