# M5c 数值合同增补

本单保留 M5b 的精确有理输入与误差管语义，不添加浮点判定阈值，不把充分条件未通过解释为实证模型敏感。R3 研究合同另见 `m5c_research_theory.md`，审查不足的部分不接入原认证回放。

| 量 / API | 合同 | 门 / 证据 |
|---|---|---|
| R1 / R2 原生产公式 | 不改生产公式；补真实内部变异门。oracle 与生产几何原语不重合。误差、严格性、全窗、全竞争者与双投影缺一不得签发 | `tests/test_m5c_robustness.py`；`docs/m5c_teeth_theory.md` |
| `compare_pair.comparison_basis` | 四个互斥来源：双盒证书直接判定、共享初始贯入、共享初始接触、实际轨迹比较。`same` 不独自定义实测分母 | `test_model_comparison_denominators_distinguish_computation_from_identity` |
| `production_initial_crosschecked` | 只有实际调用两生产入口并将初态与独立 G0 比较后为真；G0 单独求值与交叉验证分列 | 同上 |
| 稳健 `reason` | 只属于未证结果；认证成功后移除过时 `NO_SUFFICIENT_CERTIFICATE` | `test_bb03_raw_first_cover_is_in_the_same_rows_secondary_slot` |
| `canonical_legacy_rows` | 冻结连续 padded ID 环保留顺序；尾后两 alias 映到前两点；必须与已冻结主参考 canonical 字段一致。VV 要求 `raw[0]==1 && raw[4]>0`；VE 共边槽要求 `raw[0]==0 && raw[6]>0`；普通 VE 的 m4/m5 锁长提示不算参考；完整槽还须同块相邻非退化边、顶点在对块；不新猜几何 | `test_primary_secondary_and_missing_pair_are_three_distinct_questions` |
| `legacy_counts` | primary、secondary 按条分别计数；ALL 按同一块对全部有效槽检查；FORMAL_ALL 仅 primary + VV，另列共边候选槽。历史 `ROBUST_FIRST_COVER_NOT_SELECTED` 仍只指主参考未选；完全无块对行才计漏检 | 同上；真实 bb03 门 |
| `runtime_source_hashes` | 在干净 CLI 预加载所用惰性数值依赖后，记录当前加载的全部仓内 `src/eab` / `tools` Python 源码；含自身与 entrypoint；首尾集合/字节一致才允许发布 | `tests/test_m5c_policy_binding.py` |
| `assert_current_sources` | 逐项验证规范相对路径、存在性和 SHA256；不能用重写 hash 修复失效。pytest 用新进程重建闭包，避免测试进程导入污染 | 每个闭包文件 scratch 字节变异拒绝门 |
| 共享审查 | 最后一条记录仍为活动项，但只可使用代码固定的 13 类脚手架规则与 4 个既有测试变异文件；活动记录另外 pin 指纹。新增更宽 review 整体拒绝 | `tests/test_m5c_policy_binding.py`；`tests/test_m5b_policy_history.py` |

这里的源码哈希是复现/防漂移门，不是数学正确性 oracle；数值补牙的变异必须独立于哈希门报红。完整 1810 步对账不进入默认 pytest，性能按新增测试节点实际 call 时间登记。

## R3 研究 API

| API | 域与数值合同 | 门 |
|---|---|---|
| `relative_separation_certificate` | 每坐标有理多项式；名义 s∈[0,1] 上分母须由当前 Bernstein 包络给出严格正下界（保守准入，不保证接受所有数学上处处正的分母；无法给出该正下界则 ValueError）。非负 L∞ 半径、合法闭窗与正整数 panels。先精确作同时间顶点差，再包络；逐窗选固定法向只作候选，整个子窗投影差严格大于两半径和才认证。无绝对容差 | `test_common_translation_cancels_exactly`；`test_relative_separation_equality_mutation_fails_semantics`；复用 base 准入门 `test_robustness_does_not_accept_invalid_windows_denominators_or_radii` |
| `diagnose_single_cover` | 同上，索引必须非 bool 整数，严格 VE/EV 括区，名义初态 CCW；列出早期分离、端点符号、简单环保持、两投影与所有 VE/EV 竞争余量。非正余量列 failed；诊断本身不签发 | `test_r3_rejects_nonexact_coordinates_radii_and_windows`；`test_tangent_touch_and_invalid_indices_are_not_certified`；`test_near_ties_and_endpoint_ties_are_never_signed`；`test_relative_simple_certificate_rigid_unit_covariance` |
| `single_cover_certificate` | 全部 R3 条件为严格正才返回单标签证书，否则 None。允许简单凹环，但仍拒绝自交、退化、不足以排除的 VV/并列；不声称根唯一、导数保持或真实物理路径已知 | `test_concave_single_cover_matches_closed_form_oracle`；`test_nonlocal_edge_crossing_is_rejected_by_simple_ring_guard`；`test_removed_simplicity_internal_guard_fails_semantics` |
| 诊断显示 | `Decimal` 仅把已精确计算的 Fraction 余量/误差比转成可读字符串；正负判定、签发与极值选择均不消费显示值 | `tools/m5c_diagnostics.py`，exact JSONL 另冻结哈希 |

R3 只导入 `fractions.Fraction` 和原精确有理包络实现；主 oracle 独立使用 Fraction 直接构造线性/二次事件及有理区间隔离，不调用生产几何/求根/区间原语。旋转后 L∞ 管必须按诱导范数保守变换，不能把轴对齐管冒称任意旋转下集合逐点相同。

有限对抗证据的范围另行限定：90 个名义构造全部为分母 D=1 的线性轨迹；920 条常值逐顶点偏置同时核对首盖标签及首时刻括区；138 条首末独立偏置的非刚体线性轨迹只断言 contact 状态与首盖标签，未把首时刻落入括区列为该组数值断言。非恒定分母 P2 的一般连续扰动不属于这 1058 条有限搜索的实测覆盖；其安全性不能靠该计数替代理论证明。原始数值证据保持不变，完整 oracle import 清单、命名门对应与只读准入反例见 `reports/codex/M5c_evidence/review_research_contract.md`。

C1 出口排序当前只有条件定理，未新增返回正管出口证书的 API，不登记伪造的已实现合同。跨边法向序、边界标签存续与距离扰动证明缺一，均不得签发。
