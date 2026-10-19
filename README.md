# eab — 域无关接触引擎

目标是把形状、接触与证书做成可复用引擎。Python 版是参照实现兼裁判；C++ 引擎 **eab2** 规划中。DDA 是第一个适配器，用于只读导出对账，不是内核语义；第一个外域是 **TIA 二维互锁**。石根华理论的严格化与延伸、既有结果与新增结果的边界见 [归属总表](docs/shi_attribution.md)。

## 分层

| 层 | 职责 | 位置 |
|---|---|---|
| L0 | 几何、数值域、精确谓词与独立 oracle | `predicates` / `construction` / `numeric_domain` / `rational3` / `kernel2d` / `kernel3d` |
| L1 | 入口块、局部盖、全局边界、沿给定运动的首入与出口 | `kernel2d` / `kernel3d`；域无关 `ContactRecord` |
| L2 | 距离、裕度与显式报告政策 | `margin` |
| L3 | 精确 LP、单体/多体极限分析与证书自校验 | `lp` / `limit` / `limit_multi` |
| L4 | Dual 与冻结盖片内微分 | `dual` / `kernel3d/frozen` |
| L5 | 引擎导出解释、锚定运动、TIA 逃逸/剪胀应用 | `adapters` / `readers` / `tools` |

内核不得导入适配器/读取器或携带域词与 legacy 槽位语义；规则与纯度门要求见 [AGENTS](AGENTS.md)。

## 已证明清单（按明确前提；具名门不替代证明）

| 命题 | 归属类别 | 证明文档 | 具名门 |
|---|---|---|---|
| E 定义与距离恒等式（A01/A04） | 原文已有：2015 §3.2、§3.9 | [M3 §1/T3](docs/m3_global_entrance_design.md) | `test_m3_global2d.py::test_global_body_and_topology_match_independent_oracle_without_skip`；`test_m3_global2d.py::test_distance_to_e_matches_independent_features`；`test_margin.py::test_config_space_distance_equals_body_distance` |
| 有限凸分解的 E 并公式（A08） | 原文有陈述、本仓库补完整证明 | [M3 T1](docs/m3_global_entrance_design.md) | 快档单格 `test_m3_global3d.py::test_all_lazy_convex_pair_cell_vertices_edges_faces_and_exact_sides_match_oracle` |
| O 开胞并、E=closure(O)、接触内缝（A10） | 原文没有（本仓库新结果） | [M3 T1](docs/m3_global_entrance_design.md) | `test_m3_theory.py::test_m3_tight_fit_distinguishes_body_relation_from_entrance_topology`；`test_m3_global3d.py::test_zero_clearance_contact_is_not_silently_regularized_to_open_union` |
| 二维弱覆盖完整证明与退化补全（A12） | 原文有陈述、本仓库补完整证明 | [M3 T2a](docs/m3_global_entrance_design.md) | `test_m3b_2d.py::test_nonstrict_flat_collinear_local_covers_weakly_cover_boundary`；`test_m3b_2d.py::test_internal_semantic_mutants_fail_without_source_hash_tripwires` |
| 二维细分裁剪强完备（A14） | 原文没有（本仓库新结果） | [M3 T2](docs/m3_global_entrance_design.md) | 主门：`test_m3_global2d.py::test_clipped_covers_are_exactly_boundary_and_cover_oracle_ray_exits`；包含方向：`test_m3_global2d.py::test_local_clipping_covers_the_independently_built_cell_boundary`、`test_m3b_2d.py::test_nonstrict_flat_collinear_local_covers_weakly_cover_boundary` |
| 接触骨架与带标签等价剖分（A16） | 原文没有（本仓库新结果） | [M3 T2b](docs/m3_global_entrance_design.md) | `test_m3b_2d.py::test_contact_skeleton_subdivision_checks_every_stratum`；`test_m3b_2d.py::test_contact_skeleton_preserves_an_isolated_tight_contact` |
| 三维凸片并显式边界强完备（A18） | 原文没有（本仓库新结果） | [M3b T3B](docs/m3b_boundary3d_design.md) | 快档单格 `test_m3b_boundary3d.py::test_all_boundary_arrangement_vertices_edges_faces_and_sides_have_zero_mismatch` |
| H 前提下三维局部盖裁剪强完备（A20） | 原文没有（本仓库新结果） | [M3b T3L](docs/m3b_boundary3d_design.md) | `test_m3b_boundary3d.py::test_all_boundary_arrangement_vertices_edges_faces_and_sides_have_zero_mismatch`；`test_m3b_boundary3d.py::test_removing_local_clipping_is_killed_by_buried_polygon_assertion` |
| 平移首入精确算法与全部并列（A25） | 原文没有（本仓库新结果）；概念归原文 | [M3 T3](docs/m3_global_entrance_design.md) | `test_m3_global2d.py::test_global_first_entrance_is_complete_without_body_predicates`；`test_kernel2d_convex_ray_exact.py::test_corner_start_reports_both_exact_active_facets` |
| PD_closed 公式与全局出口（A27） | 原文有陈述、本仓库补完整证明 | [M3 T3](docs/m3_global_entrance_design.md) | `test_m3_exit_oracle.py::test_global_shortest_exit_matches_independent_l_union_boundary`；`test_m3_global2d.py::test_shortest_exit_tied_minimizer_set_not_lex_representative_is_covariant` |
| 指定 SE(2) 轨迹的五次精确首入（A29） | 原文没有（本仓库新结果） | [M5a T1–T5](docs/m5a_se2_design.md) | 快档小格 `test_m5a_oracle.py::test_random_complete_events_match_independent_sturm_and_g0[0]`；其余参数格保留慢档 `test_m5a_oracle.py::test_random_complete_events_match_independent_sturm_and_g0` |
| P2 六次事件与全窗误差界（A30） | 原文没有（本仓库新结果） | [M5b](docs/m5b_motion_theory.md) | `test_m5b_motion.py::test_sixth_degree_events_match_independent_seven_sample_oracle`；`test_m5b_motion.py::test_p2_p3_uniform_bound_contains_independent_interval_trigonometry` |
| R1/R2、R3、C1 稳健证书（A31–A33） | 原文没有（本仓库新结果） | [R1/R2](docs/m5b_robustness_theory.md)、[R3](docs/m5c_research_theory.md)、[C1](docs/m5d_c1_theory.md) | `test_m5b_robustness.py::test_no_contact_requires_strict_margin_and_covers_whole_window`；`test_m5b_robustness.py::test_single_cover_certificate_has_independent_closed_form_oracle`；`test_m5c_certificates.py::test_concave_single_cover_matches_closed_form_oracle`；`test_m5d_r3_semantics.py::test_r3_threshold_edge_nonrigid_p2_perturbations_preserve_first_label_and_time`；`test_m5d_exit_certificate.py::test_c1_threshold_edge_nonrigid_perturbations_match_independent_hull_oracle`；`test_m5d_exit_certificate.py::test_c1_ranking_checks_every_competitor_at_the_exact_boundary` |

二维凹几何使用独立 `kernel2d/g0_oracle.py` 的有理区间裁剪、段距离与事件检查检验距离/出口完备性（不调用生产 `polygons_overlap`）。精确证书和显示数值分开，支持域见 [数值合同](docs/exact_predicates_plan.md)。

## 未证明 / 无门 / 不保证

- 任意退化凹多面体的弱覆盖 H；三维 VF/FV 关联棱判据只是必要条件候选超集，不是任意凹顶点的充分性证明。
- 原文的平移锁定/可移除定理已存在，但命名锁定证书、SE(2) 锁定与完整配置障碍尚未提供。
- 完整 SE(3)、跨 chart 多圈、材料多环、一般仿射首入、圆角复合及一般 rho 求解不能从现有窄域结果外推。
- A28 的 rho 形式化仅有文档算例、无生产门；A36 是已有标准膨胀恒等式、无独立门，均不列入上方已证明清单。
- `PD_closed` 是闭集完全分离的**下确界**，边界终点仍接触；`rho` 是离开贯入集的口径，两者不能互换。显式报告窗口不保证 PD_closed 上界。
- 不保证接触力/法向唯一、开闭迭代收敛、真实力学轨迹等价、物理标定或生产替换；摩擦锥容量没有通用相对余弦误差界。
- “本仓库新结果”不是学术首次声明；原文已有结论不得因重新证明或精确实现而改认归属。

## 怎么跑

执行覆盖运行器需 Python 3.12+ 与 pytest；工作目录为仓库根：

```powershell
# 日常快档；默认不跑 slow
python tools/h1_run_gates.py --name fast_20261019
# 全档（快 + 慢），固定四分片，记录进度与收集/执行核对
python tools/h1_run_gates.py --name final --runslow
```

运行器设置本单 TEMP/TMP，并传递 `-p no:cacheprovider` 与显式 `--basetemp`；测试不依赖临时目录的具体位置。普通 `pytest --runslow` 同样包含快慢全档，仍须传入上述两个参数。日常快档目标单进程约 5 分钟，里程碑只在开工基线和收尾跑全档；实际耗时与覆盖以 [H1 报告](reports/codex/H1_report.md) 为准。里程碑由 Claude 安排一路对抗核查。

## 历史与证据

- [完整旧 README（原样）](docs/history/README_through_20261019.md)、[旧纪律与事故叙事](docs/history/AGENTS_through_20261019.md)。
- [原文归属总表](docs/shi_attribution.md)、[14 条二手转述勘误](docs/canon_errata_20261019.md)、[详细映射与历史实现状态](docs/canon_map.md)。
- [历史证据外部归档映射与 SHA256 清单](reports/EVIDENCE_ARCHIVE.md)；测试必要输入保留在 `fixtures/` 或 `tests/data/`。
