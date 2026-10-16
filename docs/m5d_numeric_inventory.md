# M5d 数值合同、oracle 与准入 inventory

本单不改变 R1/R2/R3 生产公式。`m5b_robust_replay.py` 仅订正 raw 顶点编号注释；
仍因冻结运行时闭包字节改变而真实重算，不能只刷哈希。新增 C1 独立 API，
不接入姊妹求解器，也不把初态局部邻域结论冒充全步出口不变。

| API / 量 | 数值合同 | 具名门 / 证据 |
|---|---|---|
| R3 early / VE+EV / 两侧投影 / 末段 | 早期 `[0,l]` 全覆盖；括区每子窗全事件严格排除；保留两端边内投影。省略任何必要覆盖不签发 | `tests/test_m5d_r3_semantics.py` 中 `test_r3_complete_early_window_rejects_prebracket_contact`、`test_r3_ev_competitor_precedes_nominated_ve`、`test_r3_both_projection_sides_reject_line_extensions`、`test_r3_final_panel_rejects_departed_endpoint` |
| R3 相对向量 | 不等正分母下先精确交叉相乘再相减；两个运动块的 P2 转动+应变不能按等分母偷算 | `test_r3_unequal_p2_denominators_reject_false_time_bracket` |
| L∞ 顶点管 | 分隔投影必须除法向 L1 范数；不以 L∞ 范数替代对偶范数 | `test_r3_linf_tube_requires_l1_dual_normalization`、`test_replay_r1_requires_p2_tube_even_when_both_nominal_paths_are_separated` |
| R3 误差预算 | `du||W||1+dw||U||1+2du dw`，另一端 V 同理；严格端点扣费。具名实际反例与仅预算合同反例分开报告 | `test_r3_endpoint_budget_prevents_actual_out_of_bracket_contact`、`test_r3_bilinear_budgets_include_both_endpoints_and_all_terms` |
| R3 对抗阈值 | 精确有理二分只给 `r_lo≤r*≤r_hi`，不用 float 选阈值；有限扰动检查标签与首时刻开括区，不取代连续管定理 | `test_r3_threshold_edge_nonrigid_p2_perturbations_preserve_first_label_and_time` |
| 回放 R1 | 名义 P1/P2 同为 no_contact 不足以签双路径管；两证书必须分别通过 | `test_replay_r1_requires_p2_tube_even_when_both_nominal_paths_are_separated` |
| 回放 R2 | 全早期窗口，双路径 all 而非 any；半径不得削减。时刻括区也是证书语义，标签相同不能掩盖错括区 | `test_r2_mild_early_truncation_rejects_a_short_prior_penetration`、`test_replay_single_cover_keeps_both_tubes_and_the_full_radius_at_the_threshold` |
| `exit_order_certificate`（C1） | int/Fraction 坐标与非负半径，排除 bool/float/string；查询点固定；只认证管内严格凸、跨环边不平行、名义内点、唯一闭边最优的子域。不足则带原因 UNPROVED | `tests/test_m5d_exit_certificate.py` |
| C1 内点与排序 | `q>2(ra+rb)^2`；每个竞争边 `h=qj-q-8r²>0` 且 `h²>32qr²`。全精确有理，不取近似平方根，无绝对阈值 | `test_c1_interior_radius_bound_is_strict`、`test_c1_ranking_checks_every_competitor_at_the_exact_boundary`、`test_c1_squared_rank_inequality_needs_its_positive_branch` |
| C1 边界存续 | 全边—非邻顶点凸性余量；全跨环边叉积余量；保留全部 n+m 标签。凹/共线、跨环平行、名义并列不得仅凭距离差认证 | `test_c1_concavity_requires_boundary_persistence_not_just_a_distance_gap`、`test_c1_parallel_split_requires_normal_order_not_just_a_distance_gap`、`test_c1_original_tie_is_not_a_persistent_complete_minimizer_set` |
| C1 半径口径 | 初态几何各顶点盒半径沿用 M5b `bound+residual+endpoint_parameter`。不包含名义全步位移；结论不是全步几何出口恒定 | `tools/m5d_c1_replay.py`、`docs/m5d_c1_theory.md` |
| B 平行度 | `sin²=cross²/(||u||²||v||²)` 精确 Fraction；`<1/300` 仅定义描述性“近平行”，不参与任何认证；浮点只展示 | `tools/m5d_wording_audit.py`、`tests/test_m5d_wording.py` |
| raw / canonical ID | raw 实顶点≥1，0垫位；规范化后0可为合法环端点；原错误 raw0 测试改为非零回绕 alias→canonical0 | `tests/test_m5c_accounting_review.py`、`docs/m5d_legacy_semantics.md` |
| 冻结发布闭包 | source/input/inherited、候选与备份在发布各阶段保持同一字节封印；漂移拒绝并仅回退本进程写出的未被外改目标。不是跨文件原子事务，强杀不保证自动回滚 | `tests/test_m5d_frozen_publication.py`、`review_integration.md/json` |

## 主 oracle import 清单与独立性

- R3：`tests/m5d_r3_oracle.py` 只导入 `fractions.Fraction`、`functools.lru_cache`、`math.comb`；
  自己的有理多项式/Sturm、事件和区间比较，不 import 生产几何、求根、包络、G0。
  `tests/m5c_teeth_oracle.py` 仅 Fraction，用独立平移闭式事件；P2 输入适配器一致性门不冒充几何 oracle。
- R1/R2 回放反例：Fraction、math.comb；首时刻/矩形包含/最大半径平方均为直接有理恒等式。
  DDAAnchoredMotion、rob、replay 是被测对象或输入适配器，不参与预期值计算。
- C1：`tools/m5d_c1_oracle.py` 仅 Fraction；所有 `B-A` 点差建独立单调链凸包、行列式距离，
  与生产支持点选边/投影截断距离不共用几何函数。复核再以穷举支撑半平面作为第三路径。
- B 槽口径 oracle：原始整数槽与独立模运算 alias；无生产几何。全量 C1 标签转全局 ID 另被独立复核。
- Path、JSON、gzip、hashlib、pytest、mutation_support 是装载/记录/变异设施；源码哈希属于防漂移门，
  不能算数值正确性 oracle。新语义变异直接调用具名门，不选任何 hash / 冻结快照测试。

## 静态与逐站准入

不扩大原工具的语法/导入/共享变异豁免域，不增加数值豁免；通过一阶显式循环和可解析类型使新增路径通过现行门。
最终 `tools/m5d_audit_admissions.py` 记录实际反事实诊断差集 × AST行列站点，不以政策行数替代分母。
最终静态、计数、性能值以 `reports/codex/M5d_report.md` 和机器证据为准。
