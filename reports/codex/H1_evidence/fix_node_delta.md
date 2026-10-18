# H1 逐节点数量差异账（476c5d6 返修基线）

状态：完整匹配。
只核收集节点，不声称执行、通过或无 skip；全档运行记录另列。

- 原收集：13907；新收集：13944。
- 退役 0/0；新增 37/37；等量改名 26/26 对。
- 原始集合差：删 26、增 63；净变化 +37。
- 预期：13907 − 0 + 37 = 13944；26 对改名净变化 0。
- 新增：恢复运行守卫 7 + 纯度扩充 29 + C1 A 环镜像 1 = 37。
- P3 参数格节点仅为 test-of-test；两道冻结数据门仅为完整性检查，均不冒充生产语义门。

## 输入

- old：`D:\eab-wt\cx-e2\reports\codex\H1_evidence\tmp\fix_baseline\collection.txt`；编码 `utf-8-sig`；SHA256 `f0f309c6f11a2798c97cf6a218fcd74c693a242ac3ff82c981634ea0ef4a9a1c`。
- new：`D:\eab-wt\cx-e2\reports\codex\H1_evidence\tmp\fix_final\collection.txt`；编码 `utf-8-sig`；SHA256 `cfe2c7bf8a217e115c06690c6304c6e33f76f119d10a87792e5d95efcb9b7281`。

## 退役 0 个节点

| 节点 | 已观察 |
|---|---|

替代语义门、退役原因逐条见 [冻结证据说明](../../../docs/frozen_evidence.md)。

## 新增 37 个节点

### restored_live_run_guards（7）

| 节点 | 已观察 |
|---|---|
| `tests/test_m4c_fix_replay.py::test_frozen_hash_scope_is_exact_replay_import_closure_with_posix_keys` | True |
| `tests/test_m5c_policy_binding.py::test_new_runtime_import_after_start_invalidates_the_sealed_closure` | True |
| `tests/test_m5c_policy_binding.py::test_runtime_source_closure_matches_independent_import_origins_and_kills_omission[False-m5b_endpoint_replay]` | True |
| `tests/test_m5c_policy_binding.py::test_runtime_source_closure_matches_independent_import_origins_and_kills_omission[False-m5b_robust_replay]` | True |
| `tests/test_m5c_policy_binding.py::test_runtime_source_closure_matches_independent_import_origins_and_kills_omission[True-m5b_endpoint_replay]` | True |
| `tests/test_m5c_policy_binding.py::test_runtime_source_closure_matches_independent_import_origins_and_kills_omission[True-m5b_robust_replay]` | True |
| `tests/test_m5c_policy_binding.py::test_source_binding_rejects_parent_traversal_even_with_matching_content` | True |

### kernel_purity_expansion（29）

| 节点 | 已观察 |
|---|---|
| `tests/test_kernel_purity.py::test_contract_field_allowlist_is_site_specific_and_documented` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[dda_probe.py-value = 1\n-domain module token dda]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-bddacover = 1\n-domain token bdda,dda]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-bolt_force = 1\n-domain token bolt]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-csvexport = 1\n-domain token csv]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-ddamotion = 1\n-domain token dda]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-def probe(value):\n    match value:\n        case complex(mtype=0):\n            return 1\n-domain token mtype]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-df06state = 1\n-domain token df06]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-joints = 1\n-domain token joint]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-label = '\u5ca9\u4f53\u56f4\u5ca9\u65ad\u5c42\u5ca9\u7206'\n-domain token]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-legacy_slot = 1\n-domain token legacy,slot]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-lock_second = 1\n-domain token lock_second]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-m4 = 1\nm6 = 2\n-domain token m4]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-m_type = 1\n-domain token mtype]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-out_csv_z = 1\n-domain token csv]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-payload = b'df06'\n-domain token df06]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-rocks = 1\n-domain token rock]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-tiaprism = 1\n-domain token tia]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-tuple7 = 1\n-domain token tuple7]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-zsto = 1\n-domain token zsto]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[probe.py-zstorecord = 1\n-domain token zsto]` | True |
| `tests/test_kernel_purity.py::test_domain_lexical_classes_reject_real_source_injections[tia_prism/probe.py-value = 1\n-domain module token tia]` | True |
| `tests/test_kernel_purity.py::test_language_slots_exception_is_not_a_slot_variable_exemption` | True |
| `tests/test_kernel_purity.py::test_parent_package_imports_are_checked_for_every_kernel_module` | True |
| `tests/test_kernel_purity.py::test_shared_contract_modules_are_lexically_scanned[__init__.py]` | True |
| `tests/test_kernel_purity.py::test_shared_contract_modules_are_lexically_scanned[contact_record.py]` | True |
| `tests/test_kernel_purity.py::test_shared_contract_modules_are_lexically_scanned[numeric_decode.py]` | True |
| `tests/test_kernel_purity.py::test_static_dynamic_import_spellings_reach_forbidden_packages[import importlib\nvalue = importlib.import_module('eab.' + 'adapters')\n]` | True |
| `tests/test_kernel_purity.py::test_static_dynamic_import_spellings_reach_forbidden_packages[import sys\nvalue = sys.modules['eab.readers']\n]` | True |

### c1_a_ring_mirror（1）

| 节点 | 已观察 |
|---|---|
| `tests/test_h1_adopted_semantics.py::test_c1_a_ring_convexity_uses_a_radius_when_b_is_exact` | True |

## 等量改名 26 对（净 0）

| 分类 | 原节点 | 新节点 | 理由 | 已观察两端 |
|---|---|---|---|---|
| r3_scope_correction | `tests/test_h1_frozen_semantics.py::test_fixed_real_r3_subset_reexecutes_exact_certificate_labels_and_counts` | `tests/test_h1_frozen_semantics.py::test_fixed_real_r3_subset_reexecutes_certificates_and_counts_at_frozen_label_and_interval` | 冻结标签和区间上重执行两证书及计数，不声称重求首入标签或时间 | True |
| test_of_test | `tests/test_h1_entrance_symmetry.py::test_symmetry_parameter_cells_produce_distinct_reference_geometries` | `tests/test_h1_entrance_symmetry.py::test_of_test_symmetry_parameter_cells_produce_distinct_geometries` | 参数格多样性元测试，不计作独立生产语义门 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation0-scale0]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation0-translation0-scale0]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation0-scale1]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation0-translation0-scale1]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation0-scale2]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation0-translation0-scale2]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation1-scale0]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation0-translation1-scale0]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation1-scale1]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation0-translation1-scale1]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation1-scale2]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation0-translation1-scale2]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation2-scale0]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation0-translation2-scale0]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation2-scale1]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation0-translation2-scale1]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation2-scale2]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation0-translation2-scale2]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation3-scale0]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation0-translation3-scale0]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation3-scale1]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation0-translation3-scale1]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation0-translation3-scale2]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation0-translation3-scale2]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation0-scale0]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation1-translation0-scale0]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation0-scale1]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation1-translation0-scale1]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation0-scale2]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation1-translation0-scale2]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation1-scale0]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation1-translation1-scale0]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation1-scale1]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation1-translation1-scale1]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation1-scale2]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation1-translation1-scale2]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation2-scale0]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation1-translation2-scale0]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation2-scale1]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation1-translation2-scale1]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation2-scale2]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation1-translation2-scale2]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation3-scale0]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation1-translation3-scale0]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation3-scale1]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation1-translation3-scale1]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |
| displacement_symmetry_scope_correction | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance[rotation1-translation3-scale2]` | `tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance[rotation1-translation3-scale2]` | 改为位移形式且逐点对独立 oracle；补非凸、紧配拓扑及顺时针输入 | True |

## 未匹配项

无；未使用前缀白名单或忽略未知节点。

## 复跑

```powershell
python tools/h1_node_delta.py --basis h1-v1 --old <基线收集文件> --new <收尾收集文件>
```

未知变化、预期缺失、重复节点、收集数不符或收集错误均返回非零状态。
