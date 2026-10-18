# 冻结证据：数据身份与语义回归（H1）

冻结数据不再要求“今天的源码字节等于当年源码字节”。历史 JSON 原字节保留；
当前实现是否仍满足合同，由固定小子集的真实执行、独立解析 oracle 与已有内部变异门判断。
这不是重新计算或重新认可历史全量回放。

## 数据与来源

- [冻结输入来源表](../fixtures/frozen/PROVENANCE.json)：137 个文件均无直接记载的生产提交及
  生产工具版本，因此全部 `producing_git_commit` / `tool_version` 都明确为 `unknown`。
  其中 23 个文件的已记录源码哈希可与某个 Git 提交的 blob 一一核对，另列
  `source_equivalent_git_commit` 并标记为推断；这只说明已记录源码子集等价，
  **不证明该产物实际产生于该提交**。其余 114 个文件也未确定源码等价提交。
  准确的接受提交、原始路径、字节数及数据 SHA256 分别保留，不以接受提交冒充生产提交。
  初批搬家 136 个；快档实测补出 `research_diagnostics.json` 这一漏读输入，已从外档原字节复制
  782,733 字节且与接受版本核同，外档副本不动，详见 [追加清单](../reports/codex/H1_evidence/frozen_inputs_addendum.json)。
- 历史路径 `reports/<相对路径>` 的测试输入搬至 `fixtures/frozen/<相对路径>`，内部 JSON 路径键不改。
  `tools/frozen_evidence.py::data_path` 仅用于读取；不存在冻结副本时仍读原路径，支持合成测试根。
  `historical_name` 将新位置反映射为旧的 provenance 键。
- 新产物的默认目录仍是 `reports/`；resolver 不写文件。历史大流及报告参见
  [归档映射](../reports/EVIDENCE_ARCHIVE.md)。测试不读取仓库外归档。
- 具名数据门：`test_h1_frozen_data.py::test_frozen_data_hashes_are_preserved_without_current_source_pins`。
  同大小实际输入改动的牙：`test_frozen_data_integrity_rejects_an_actual_same_size_input_edit`。

## 退役门与真实替代门

| 退役的当前源码绑定 | 数量变化 | 替代的具名语义门 |
|---|---:|---|
| `test_m4c_replay.py::test_frozen_full_computation_is_bound_to_current_production_sources` 的源码断言；函数改名为历史覆盖门 | 0 | 同文件 `test_real_first_frame_per_family_recomputes_the_frozen_classification`：15 家各 1 帧真实执行 |
| `test_m4c_fix_replay.py::test_frozen_hash_scope_is_exact_replay_import_closure_with_posix_keys` | −1 | 上述真实首帧；该文件其余独立回放接线及内部变异门保留 |
| `test_m5a_replay.py::test_frozen_family_products_are_distinct_and_bound_to_current_source` 中 current code/tool hash；改名为历史重验证门 | 0 | 同文件 `test_real_first_block_fit_per_family_is_reexecuted_not_just_hash_checked`（15 格）和 `test_real_rotating_candidate_pairs_reexecute_exact_events_not_just_frozen_hashes`（3 格）：状态、特征、精确代数时间 |
| `test_m5b_endpoint.py::test_frozen_endpoint_evidence_has_all_cases_and_recomputable_extrema` 中工具哈希断言 | 0 | 同函数真实重构 2 个端点极值；`test_midpoint_minimal_example_has_independent_three_by_three_reconstruction` 的独立精确重构 |
| `test_m5c_policy_binding.py` 的冻结闭包 2、逐文件改动 2、晚导入 1、路径遍历 1、import-origin 4 | −10 | M5b 5 个真实小例、M5c 1 个真实 R3 小例，以及已有独立几何/证书语义门 |
| `test_m5c_combined_evidence.py` 的 `research_wrong_sources` 格；冻结合并摘要的 current source/input-source 哈希断言 | −1；其余 0 | 原 join 门的实际状态、精确时间、标签、引用计数；历史上游数据哈希仍检查 |
| `test_m5d_frozen_publication.py` 中 `source_hashes` 数据维度 | 0（5 格等量改名） | 改为 `inherited_stream_hashes`，真实改变输入流，继续验证拒绝及完整回滚；最终检查的内部变异牙仍保留 |
| `m5b_minimal_examples.verify` 的旧源码/脚本哈希 | 0 | `test_m5b_replay.py::test_five_real_model_certificates_recompute_from_self_contained_minimal_inputs`：5 个固定真实例逐项完整比对 |
| `m5c_research_examples.verify` 的旧源码哈希及无关的全量诊断流依赖 | +2 | `test_h1_frozen_semantics.py::test_fixed_real_r3_subset_reexecutes_exact_certificate_labels_and_counts`；`test_fixed_real_r3_subset_kills_an_internal_radius_budget_defect` |
| 新冻结数据完整性门及同大小输入改动牙 | +2 | `test_h1_frozen_data.py` 两门；不读取任何当前源码 |

本分项合计删除 12 格，新增 4 格，净 −8；等量改名与位置变化不计增减。
R3 新牙把 `diagnose_single_cover` 内部早期分离预算 `ra+rb` 改为只计 `ra`，
红在完整精确证书字段比对，不是源码哈希、不在枚举后添加假结果。

## 工具检查的退役清单

下列工具不再把历史源码清单与当前工作树字节对照。读取的数据哈希、历史记录内部一致性、
冻结执行副本自身的 manifest 完整性，以及真实数值结果比较保留：

| 工具 | 退役位置 |
|---|---|
| `int1_finalize_evidence.py` | 当前导出比对限于 fixture 数据，不比对当前源码 |
| `m3_finalize_evidence.py` | `scan_audit` 源码哈希；`snapshot_audit` 当前源码/模块集比对 |
| `m3b_finalize_evidence.py` | `verify_hashes` 源码项；当前模块集/源码字节；三方对账中的当前源码端 |
| `m3c_finalize_evidence.py` | suite 当前源码端；旧 replay attestation 对当前闭包 |
| `m4c_finalize_evidence.py` | 当前源码导出及历史 mutation 源码哈希 |
| `m4c_summarize_evidence.py` | 完成批次对当前 `code_hashes()` |
| `m4c_run_replays.py::verify_batch` | 批次对当前源码；改核批次记录间的一致性 |
| `m5a_se2_replay.py` | 完成批次冻结时的当前源码要求 |
| `m5a_finalize_evidence.py`、`m5a2_finalize_evidence.py` | 当前导出比对限于 fixture 数据 |
| `m5b_finalize_evidence.py`、`m5c_finalize_evidence.py` | 当前导出比对限于 fixture 数据 |
| `m5b_minimal_examples.py`、`m5c_research_examples.py` | 小例验证对当前源码/工具字节；改真实重新执行 |
| `m5c_publish_combined.py::check_sources` | 历史源码 map 对当前字节；保留历史 map 自身首尾一致性 |
| `m5c_report.py::check_sources` | 历史源文件对当前源码 |
| `m5d_refresh_frozen.py` | 候选发布封印不再包含历史源码；只含输入、上游、候选及备份数据 |
| `m5d_report.py` | 当前源码、历史工具、review 来源字节；数据来源仍检查 |
| `m5c_source_binding.py` | `assert_current_sources` 删除；所有实际运行调用改名并使用 `assert_run_sources_unchanged` |

## 没有退役的两种不同检查

1. **同一次实际长跑的前后快照稳定性**：`assert_run_sources_unchanged` 必须拿两个该次运行的快照，
   只比较二者，不读取当前源码、不接受单独旧 map。原扫描/回放内部的 before/after 也保留；
   它们仅防止一次运行混用两个版本，不能用来声称历史结果仍代表当前代码。
2. **静态构造审查的准入授权**：它不是数值回归 oracle；H1 不新增准入，搬家按机械重键规则处理。
   它的计数、AST 站点映射及限制由 H1 静态门证据单列，不以“改哈希”替代语义验证。
   历史准入指纹常量不变；`tools/policy_history_view.py` 仅按已核验的重键对应表反向投影命名空间/上下文字段，
   恢复完整旧策略后比较原指纹。真实扫描器仍读新策略；规则、理由、AST 站点及准入计数不得借投影改变。

## 有界运行

只重跑上述小子集；没有全量回放或冻结数值重算。新 R3 真实例约 1.4 秒，内部牙约 1.4 秒；
已有 M5b 五例约 1.6 秒（单次共享主机观测，不是性能基准）。最终实测见 H1 报告及 targeted 日志。
