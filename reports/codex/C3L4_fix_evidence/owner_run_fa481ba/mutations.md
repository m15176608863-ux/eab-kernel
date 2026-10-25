# WO-C3L4-fix-close 内部变异复跑（64b499f）

HEAD `64b499f8bf2d5e889d0ac0c65a3eab37ef743629`；当前工作树隔离构建，不冒充所有者新鲜 Git 树验收。四门串行；编译失败、零收集、导入错误均不计为被杀。certificate 工具仅随调用方 μ_max 参数签名更新锚点及 watched 清单，缺陷语义不变。

## 构建与证据边界

- PowerShell 直接运行 `cmd.exe /d /c D:\eab-wt\cx-c0\eab2\build\tmp\close_mut_64b499f\build.cmd`；固定 MSVC 14.44.35207、Release、`/fp:precise`，仅构建 `eab2` target（含 core 与发布 ABI object），退出码 0。
- [隔离构建](file:///D:/eab-wt/cx-c0/eab2/build/close_mut_core_64b499f/) 的 core/DLL/ABI object，以及每个变异 exe/DLL，时间戳均晚于各自启动时间；未复用旧顶层 core。
- 661 个受监测源/相关文件前后 SHA-256 一致；30 个既有顶层 build 文件 SHA-256 与 mtime 一致。未结束其他进程、未启动 Python 全档。
- branch/meta 沿用每工具一次固定编译器环境初始化及工具链核验；legacy 工具原样逐次初始化。所有编译参数与语义断言保持不变。
- [紧凑 JSON](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/owner_run_64b499f/mutations.json) 锚定日志及详细证据哈希；[完整执行快照](file:///D:/eab-wt/cx-c0/eab2/build/tmp/close_mut_64b499f/execution.json) 保存命令、PID、时间与逐文件哈希；[详细清单](file:///D:/eab-wt/cx-c0/eab2/build/tmp/close_mut_64b499f/mutation_details.json) 保存全部节点、变异 hash 和编译产物信息。
- 本轮替代旧 d4fe002 摘要；旧轮原始证据未删除。初次 cmd 相对路径含正斜杠致启动失败（未构建）；保留失败日志后改用绝对 Windows 路径完整构建，不计为变异被杀。

构建末行原样：`[14/15] Linking CXX shared library eab2.dll`

## 四门实测结果

### l4

命令（PowerShell）：
```text
& "C:\Program Files\Python312\python.exe" -X utf8 D:\eab-wt\cx-c0\tools\eab2_c3l4_mutations.py --core D:\eab-wt\cx-c0\eab2\build\close_mut_core_64b499f\eab2_core.lib --output D:\eab-wt\cx-c0\eab2\build\tmp\close_mut_l4_64b499f
```

退出码 `0`；最后一行原样：
```text
C3L4_MUTATIONS_OK baseline=2 rejected=5 semantic_failures=5
```

| 名称 | 结果 | 具名门 / 语义末行 |
|---|---|---|
| `baseline_sensitivity` | 基线绿 | C3L4_SENSITIVITY_MUTATION_BASELINE gates=4 passed=4 |
| `baseline_geometry` | 基线绿 | C3L4_GEOMETRY_SEED_OK checks=76 |
| `scaled_dual` | 被杀 | stable_original_unscaled_dual_three_seeds; sensitivity failed: stable original unscaled y and dA/db/dc formula |
| `missing_live_column` | 被杀 | live_load_column_is_not_rhs; sensitivity failed: live amplitude derivative is negative capacity |
| `fixed_basis_on_unstable_face` | 被杀 | unstable_basis_cannot_hide_switch; sensitivity failed: unstable fixed basis loses G5 switch right zero / left two |
| `compare_opposite_lp_values` | 被杀 | g5_mills_smooth_and_switch; sensitivity failed: G5 bounded-face exact closed-form derivative |
| `only_rhs_geometry_seed` | 被杀 | C3L4_GEOMETRY_SEED_FAIL point tangent normal and mu x propagation |

### branch

命令（PowerShell）：
```text
& "C:\Program Files\Python312\python.exe" -X utf8 D:\eab-wt\cx-c0\tools\eab2_branch_mutations.py --core D:\eab-wt\cx-c0\eab2\build\close_mut_core_64b499f\eab2_core.lib --output D:\eab-wt\cx-c0\eab2\build\tmp\close_mut_branch_64b499f
```

退出码 `0`；最后一行原样：
```text
C3L4FIX_BRANCH_AND_STABLE_MUTATIONS_OK baseline=3 rejected=7 branch_semantic=4 derivative_comparison=2 backend_certificate_rejection=1
```

| 名称 | 结果 | 具名门 / 语义末行 |
|---|---|---|
| `baseline_branch` | 基线绿 | sensitivity: 5 checks passed |
| `baseline_field` | 基线绿 | sensitivity: 9 checks passed |
| `baseline_stable_differential` | 基线绿 | STABLE_MUTATION_DIFFERENTIAL records=5 semantic_failures=0 |
| `single_basis_fallback` | 被杀 | branch_face2_regression; sensitivity failed: face2 branch right one-half left zero requires both K sides |
| `lower_dual_only` | 被杀 | branch_face2_regression; sensitivity failed: face2 branch right one-half left zero requires both K sides |
| `eta_before_epsilon` | 被杀 | ordered_field_and_raw_path_guards; sensitivity failed: K epsilon before eta, not reversed |
| `insufficient_truncation` | 被杀 | ordered_field_and_raw_path_guards; sensitivity failed: nonzero high-order exact coefficient cannot be truncated to zero |
| `scaled_y_differential` | 被杀 | --differential-stable; STABLE_MUTATION_DIFFERENTIAL records=5 semantic_failures=3 |
| `missing_live_column_differential` | 被杀 | --differential-stable; STABLE_MUTATION_DIFFERENTIAL records=5 semantic_failures=1 |
| `min_max_sign_differential` | 被杀 | --differential-stable; STABLE_BACKEND_CERTIFICATE_REJECTED differential_exit=1 |

### certificate

命令（PowerShell）：
```text
& "C:\Program Files\Python312\python.exe" -X utf8 D:\eab-wt\cx-c0\tools\eab2_c3l4_certificate_mutations.py --output D:\eab-wt\cx-c0\eab2\build\tmp\close_mut_certificate_64b499f
```

退出码 `0`；最后一行原样：
```text
C3L4_CERTIFICATE_MUTATIONS_OK baseline=2 rejected=8 semantic_failures=9
```

| 名称 | 结果 | 具名门 / 语义末行 |
|---|---|---|
| `baseline` | 基线绿 | 11 passed in 79.66s (0:01:19) |
| `skip_python_sensitivity_certificate` | 被杀 | test_c3l4_each_threshold_side_rejects_false_labels_and_slopes[component_slope-python]; DID NOT RAISE |
| `skip_cpp_sensitivity_certificate` | 被杀 | test_c3l4_each_threshold_side_rejects_false_labels_and_slopes[component_slope-cpp]; DID NOT RAISE |
| `set_dedup_hides_duplicate_crossing` | 被杀 | test_c3l4_each_threshold_side_rejects_false_labels_and_slopes[duplicate-cpp]; DID NOT RAISE |
| `omit_crossing_label_exactness` | 被杀 | test_c3l4_each_threshold_side_rejects_false_labels_and_slopes[extra-cpp]; test_c3l4_each_threshold_side_rejects_false_labels_and_slopes[missing-cpp]; DID NOT RAISE |
| `omit_component_slope_equations` | 被杀 | test_c3l4_each_threshold_side_rejects_false_labels_and_slopes[component_slope-cpp]; DID NOT RAISE |
| `skip_python_critical_certificate` | 被杀 | test_c3l4_each_threshold_side_rechecks_full_critical_proof[polynomial-python]; DID NOT RAISE |
| `skip_cpp_critical_certificate` | 被杀 | test_c3l4_each_threshold_side_rechecks_full_critical_proof[sturm-cpp]; DID NOT RAISE |
| `ignore_non_threshold_tied_labels` | 被杀 | test_c3l4_non_threshold_tied_labels_remain_strict; AssertionError |
| `restored_baseline` | 基线绿 | 11 passed in 80.99s (0:01:20) |

### meta

命令（PowerShell）：
```text
& "C:\Program Files\Python312\python.exe" -X utf8 D:\eab-wt\cx-c0\tools\eab2_c3l4_meta_mutations.py --build D:\eab-wt\cx-c0\eab2\build\close_mut_core_64b499f --output D:\eab-wt\cx-c0\eab2\build\tmp\close_mut_meta_64b499f_r2
```

退出码 `0`；最后一行原样：
```text
C3L4_META_MUTATIONS_OK baseline=2 rejected=2 semantic_failures=2
```

| 名称 | 结果 | 具名门 / 语义末行 |
|---|---|---|
| `baseline_M5_tangent_ignores_edge_sense` | 基线绿 | C3L4_META cases=1 channels=1 mismatch=0 |
| `baseline_M7_arm_force_jet_wrong_sign` | 基线绿 | C3L4_META cases=1 channels=1 mismatch=0 |
| `M5_tangent_ignores_edge_sense` | 被杀 | C3L4_META cases=1 channels=0 mismatch=1; ValueError: C++ geometry-derived seed mismatch |
| `M7_arm_force_jet_wrong_sign` | 被杀 | C3L4_META cases=1 channels=0 mismatch=1; ValueError: C++ geometry-derived seed mismatch |

## 汇总

- 基线运行 9，变异被杀 22，幸存 0。证书前后各 11 个合法/非法输入门绿；8 变异触发 9 个预期语义失败。分支门区分 4 分支语义、2 导数对比、1 后端证书拒绝。
- 全部变异内容互异，29 个生成批处理均纯 ASCII；pytest 禁 cacheprovider 并指定独立 basetemp。四门无失败重试、无遗留变异门；meta 首轮后因 minor 工具更新，使用全新 r2 目录复跑，旧日志保留且不拼接。构建命令启动方式有一次失败并完整保留。
- [原始日志目录](file:///D:/eab-wt/cx-c0/eab2/build/tmp/close_mut_64b499f/)；编译产物与大日志均只在 ignored 自有目录。

C3L4_CLOSE_MUTATIONS_OK baseline=9 killed=22 survived=0
