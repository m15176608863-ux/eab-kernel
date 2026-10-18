# 石根华原文与本仓库结果：归属总表

核对日期：2026-10-19。依据是所有者提供的 [逐项对照](../reports/codex/inputs/shi_comparison_20261019.md) 与 [双读者笔记](../reports/codex/inputs/shi_reads_20261019.json)，不是重新以 00/01/03 的转述代替原文。原文指 Shi, *Contact theory* (2015), Science China Technological Sciences 58(9):1450–1496，以及 2021 同刊后续论文；下表年份后的 § 均为原文节号。本文全部意译，不直接引用英文原句。

**唯一分类规则。** 每行仅用一类：**原文已有**、**原文有陈述、本仓库补完整证明**、**原文没有（本仓库新结果）**、**原文主张、本仓库尚未证明**、**原文缺口**。复合结论拆行，不把原文概念与新增算法混作同一贡献。“本仓库新结果”仅表示原文未给出、仓库自行推导或实现，不宣称相对于全部文献的学术首次。标准集合/凸分析/代数算法仍属既有数学。

证明文档栏指本仓库的推导或定位处；无完整仓库证明时明确写出。具名门只是程序回归看护，不把有限测试当作全输入域证明；**无门**不得改写为“已验证”。原文锁定与可移除定理的评价以对照者纠正为准：在接触前提下是定义的直接推论，不能因读者初记“草证”而降格。

| ID | 单项结论与适用边界 | 唯一归属类别 | 原文依据 / 与原文关系 | 本仓库证明文档或定位 | 具名门（或无门） |
|---|---|---|---|---|---|
| A01 | E(A,B)=B−A+a0；A 平移、B 固定、a0 取自 A | 原文已有 | 2015 §3.2；2021 §3.2；与平移 C-obstacle 的对应是本方文献归纳 | [M3 §1、T1](m3_global_entrance_design.md) | `tests/test_m3_global2d.py::test_global_body_and_topology_match_independent_oracle_without_skip` |
| A02 | 平移位置无关（固定形状与朝向） | 原文已有 | 2015 §3.3 | [映射表 §一 2(i)](canon_map.md) | `tests/test_kernel3d_covers.py::test_proposition_2i_position_independence` |
| A03 | A、B 凸则 E 凸 | 原文已有 | 2015 §4.9；2021 §4.3 | [映射表 §一 2(ii)](canon_map.md)；无独立完整证明文档 | 无门（既有成员门仅间接使用凸性） |
| A04 | d(t,E)=d(A+t,B) | 原文已有 | 2015 §3.9；2021 §4.2 仅陈述分离情形 | [M3 T3](m3_global_entrance_design.md) | `tests/test_m3_global2d.py::test_distance_to_e_matches_independent_features`；`tests/test_margin.py::test_config_space_distance_equals_body_distance` |
| A05 | 接触前提下 a0∈int E 等价平移锁定 | 原文已有 | 2015 §3.10（图 16）；2021 §3.1 保留 lock 定义 | [M3 §1](m3_global_entrance_design.md)；尚无命名的锁定证书 API | 无门（紧配接触反例不等于锁定定理的专门门） |
| A06 | 接触前提下 a0∈∂E 等价平移可移除 | 原文已有 | 2015 §4.7，按定义直接推出；2021 §3.1 有可移除定义 | [M3 §1、T3](m3_global_entrance_design.md)；无独立完整证明文档 | 无门 |
| A07 | 实体分离/接触/贯入三态；贯入推出 a0∈int E，逆命题一般不成立 | 原文已有 | 2021 §3.1；2015 §4.8、§3.10。2015 §3.1 的贯入文字把闭交也包括在内，2021 改为内部交 | [M3 §1](m3_global_entrance_design.md) | `tests/test_m3_theory.py::test_m3_tight_fit_distinguishes_body_relation_from_entrance_topology` |
| A08 | E 对有限凸分解分配：E=∪Cij（T1 的闭集部分） | 原文有陈述、本仓库补完整证明 | 2015 §4.4 并定理；本仓库用存在量词分配补全 | [M3 T1](m3_global_entrance_design.md) | `tests/test_m3_global3d.py::test_all_lazy_convex_pair_cell_vertices_edges_faces_and_exact_sides_match_oracle` |
| A09 | 原面延拓的 BSP 凸分解与认证 | 原文有陈述、本仓库补完整证明 | 2015 §2.8，2021 §2.5；原文只陈述凹块为凸子块之并 | [M3 T1 三维构造](m3_global_entrance_design.md) | `tests/test_m3_global3d.py::test_convex_decomposition_covers_nonstar_pocket_and_cavity` |
| A10 | O 位形集、O=∪int Cij、E=closure(O)，正则闭前提与接触内缝 | 原文没有（本仓库新结果） | 原文已知接触锁态可在 int E；未定义这里的 O 集表示与 closure 结论 | [M3 §1、T1](m3_global_entrance_design.md) | `tests/test_m3_theory.py::test_m3_open_pair_sum_union_is_not_the_interior_of_closed_union`；`tests/test_m3_global3d.py::test_zero_clearance_contact_is_not_silently_regularized_to_open_union` |
| A11 | 二维闭有效 VE/EV 覆盖 ∂E，凸块取等（原包含式） | 原文已有 | 2015 §7.1–7.5、§8.1–8.2；2021 §4.5–4.7、§6.1；VV 为端点，不是原文独立盖类 | [M3 T2a](m3_global_entrance_design.md) | `tests/test_m3b_2d.py::test_nonstrict_flat_collinear_local_covers_weakly_cover_boundary` |
| A12 | T2a 完整证明：显式正则闭简单环前提、平直顶点、共线与 VV 闭包 | 原文有陈述、本仓库补完整证明 | A11 的命题归原文；本仓库补足退化处理，不将包含式本身认作新命题 | [M3 T2a 五步证明](m3_global_entrance_design.md) | `tests/test_m3b_2d.py::test_nonstrict_flat_collinear_local_covers_weakly_cover_boundary`；`tests/test_m3b_2d.py::test_internal_semantic_mutants_fail_without_source_hash_tripwires` |
| A13 | 二维距离/沿指定方向出口完备性 | 原文已有 | 是原文包含式的推论（2015 §8.2；2021 §6.1）；“01 没有同名命题”不等于原文没有 | [映射表 §六.1](canon_map.md) | `tests/test_bb52_g1.py::test_g0_distance_completeness_real_concave_geometry`；`tests/test_bb52_g1.py::test_g0_exit_completeness_real_concave_geometry` |
| A14 | T2：完全细分 + 两侧闭占据裁剪，暴露片闭包恰为 ∂E | 原文没有（本仓库新结果） | 2015 §8.2、§10.6、§12.2；2021 §6.2、§7.1–7.2 只要求 cutting，无判据、算法或证明 | [M3 T2](m3_global_entrance_design.md) | `tests/test_m3_global2d.py::test_local_clipping_covers_the_independently_built_cell_boundary` |
| A15 | T2b 原体凸合并面积证书 | 原文没有（本仓库新结果） | 原文未给此认证算法；不用于重叠配置胞直接相加 | [M3 T2b 原体凸合并](m3_global_entrance_design.md) | `tests/test_m3b_2d.py::test_certified_convex_merge_refuses_a_nonconvex_union` |
| A16 | T2b 接触骨架 Γ、E\O=∂O⊆Γ 与完整带标签竖直剖分 | 原文没有（本仓库新结果） | 原文锁定定理可解释内缝，但无此计算表示 | [M3 T2b](m3_global_entrance_design.md) | `tests/test_m3b_2d.py::test_contact_skeleton_subdivision_checks_every_stratum`；`tests/test_m3b_2d.py::test_contact_skeleton_preserves_an_isolated_tight_contact` |
| A17 | 三维凸块 ∂E 由 VF/FV/EE 三类余维一盖覆盖并取等 | 原文已有 | 2015 §9.5、§10.5、§12.1；2021 §7.1；不是“v-v/v-e/v-f/交叉 e-e 四类” | [映射表 §一 4](canon_map.md) | `tests/test_kernel3d_covers.py::test_facet_count_matches_minkowski_theory_for_boxes`（仅盒族；非全域证明） |
| A18 | T3B 有限满维凸片并的显式 ∂E 强完备，无一般位置要求 | 原文没有（本仓库新结果） | 原文只有并定理及局部盖 + cutting 路线，没有本仓库凸片并边界算法 | [M3b §2 T3B](m3b_boundary3d_design.md) | `tests/test_m3b_boundary3d.py::test_all_boundary_arrangement_vertices_edges_faces_and_sides_have_zero_mismatch` |
| A19 | T3L：GP ⇒ H（原始局部 VF/FV/EE 弱覆盖） | 原文有陈述、本仓库补完整证明 | 2015 §11.8、§12.2；2021 §7.1 原文无条件陈述；本仓库证明有更强 GP 前提 | [M3b §3 GP ⇒ H](m3b_boundary3d_design.md) | 无门（既有三维安排门不是覆盖全部 GP 前提的具名门） |
| A20 | T3L：在 H 下共面裁剪后的闭片并等于 ∂E | 原文没有（本仓库新结果） | 原文 cutting 未给严格判据；不可删除 H | [M3b §3 共面覆盖引理](m3b_boundary3d_design.md) | `tests/test_m3b_boundary3d.py::test_all_boundary_arrangement_vertices_edges_faces_and_sides_have_zero_mismatch`；`tests/test_m3b_boundary3d.py::test_removing_local_clipping_is_killed_by_buried_polygon_assertion` |
| A21 | H 对任意退化嵌入凹多面体普遍成立 | 原文主张、本仓库尚未证明 | 2015 §11.6–11.8、§12.2；2021 §7.1；原文退化分解援引 §4.2，未补完整证明 | [M3b §3 条件 H 的边界](m3b_boundary3d_design.md) | 无门；有限退化算例不是普遍证明 |
| A22 | 局部实角 VE/EV 符号与三维 VF/FV、EE 判据 | 原文已有 | 2015 §5.5、§7.3、§8.2、§9.6–9.7、§10.1–10.2；2021 §4.6–4.7。仓库 VF/FV 只用关联棱点积，故为必要条件候选超集 | [M3 T2a](m3_global_entrance_design.md)、[M3b §3](m3b_boundary3d_design.md) | `tests/test_kernel2d_exact.py::test_flat_vertex_cone_is_one_ray_not_a_line`；`tests/test_kernel3d_covers.py::test_vertex_cone_of_box_corner`（不证明原文三维第二条件） |
| A23 | 平行退化拆成重叠点对盖，全部接触点交开闭迭代 | 原文已有 | 2015 §7.4、§9.8–9.9、§11.6–11.7、§13；不是合成一个 FF/FE 盖的要求 | [映射表 §四(a)](canon_map.md)；无完整平行有限覆盖形式证明 | 无门（现行退化输入门不冒充原文有限覆盖定理门） |
| A24 | 首入：参考点从 E 外首次到达 ∂E 的事件 | 原文已有 | 2015 摘要第 (2) 条、§10、§13；无选一个候选的裁决规则，也未定义接触法向 | [M3 T3](m3_global_entrance_design.md) | `tests/test_m3_global2d.py::test_global_first_entrance_is_complete_without_body_predicates`（仓库算法门） |
| A25 | 射线闭区间最早非负端点、精确时刻与全部并列 | 原文没有（本仓库新结果） | 原文有首入概念，无射线公式/并列算法；仓库的 lex 显示代表不删并列集 | [M3 T3](m3_global_entrance_design.md) | `tests/test_m3_global2d.py::test_global_first_entrance_is_complete_without_body_predicates`；`tests/test_kernel2d_convex_ray_exact.py::test_corner_start_reports_both_exact_active_facets` |
| A26 | 最短出口概念 | 原文已有 | 2015 摘要第 (3) 条、§13；无公式/算法/多出口选择规则 | [M3 T3](m3_global_entrance_design.md) | 无门（形式化算法另见 A27） |
| A27 | PD_closed=d(t,∂E) 的下确界形式化、全局最短点及并列集合 | 原文有陈述、本仓库补完整证明 | 原文最短出口概念的直接形式化；终点仍接触，不称闭集已完全分离 | [M3 T3](m3_global_entrance_design.md) | `tests/test_m3_exit_oracle.py::test_global_shortest_exit_matches_independent_l_union_boundary`；`tests/test_m3_global2d.py::test_shortest_exit_tied_minimizer_set_not_lex_representative_is_covariant` |
| A28 | rho：离开贯入集 O 的距离，与 PD_closed 区分 | 原文没有（本仓库新结果） | 原文无 O 集及 rho；一般 rho 的实现范围不可从定义推定 | [M3 T3](m3_global_entrance_design.md) | `tests/test_m3_theory.py::test_m3_closed_separation_depth_and_nonpenetration_depth_are_different` |
| A29 | SE(2) 指定轨迹下固定角切片、VE/EV 五次事件与精确代数首入 | 原文没有（本仓库新结果） | 2015 §3.2、2021 §3.2 仅定义平移 E；2015 §2.1、§5.1、§9.1 转动靠逐步线性化。Sturm 等算法本身为既有数学 | [M5a T1–T5](m5a_se2_design.md) | `tests/test_m5a_oracle.py::test_random_complete_events_match_independent_sturm_and_g0` |
| A30 | 锚定 P2 转动 + 线性应变轨迹、六次首入及 P2/P3 全窗误差界 | 原文没有（本仓库新结果） | 在原文刚体平移几何范围之外；不扩大为一般仿射首入已实现 | [M5b 运动理论](m5b_motion_theory.md) | `tests/test_m5b_motion.py::test_sixth_degree_events_match_independent_seven_sample_oracle`；`tests/test_m5b_motion.py::test_p2_p3_uniform_bound_contains_independent_interval_trigonometry` |
| A31 | R1 无接触、R2 单首盖扰动管证书 | 原文没有（本仓库新结果） | 原文没有容差/扰动稳定性理论 | [M5b 稳健理论](m5b_robustness_theory.md) | `tests/test_m5b_robustness.py::test_no_contact_requires_strict_margin_and_covers_whole_window`；`tests/test_m5b_robustness.py::test_single_cover_certificate_has_independent_closed_form_oracle` |
| A32 | R3 先减后包络、凹形单首盖证书 | 原文没有（本仓库新结果） | 原文没有相对扰动预算及证书 | [M5c 研究理论](m5c_research_theory.md) | `tests/test_m5c_certificates.py::test_concave_single_cover_matches_closed_form_oracle`；`tests/test_m5d_r3_semantics.py::test_r3_threshold_edge_nonrigid_p2_perturbations_preserve_first_label_and_time` |
| A33 | C1 扰动盒内唯一最短出口证书 | 原文没有（本仓库新结果） | 名义凸边界结构来自 2015 §8.1、2021 §6.1；保持结构与排名的稳健结论是新增 | [M5d C1 理论](m5d_c1_theory.md) | `tests/test_m5d_exit_certificate.py::test_c1_threshold_edge_nonrigid_perturbations_match_independent_hull_oracle`；`tests/test_m5d_exit_certificate.py::test_c1_ranking_checks_every_competitor_at_the_exact_boundary` |
| A34 | 零容差有理判定、精确证书与声明域内构造/显示 | 原文没有（本仓库新结果） | 原文不讨论浮点精度、容差或精确算术；不是声称所有 API 都无限数值域 | [数值合同](exact_predicates_plan.md)、[M3 §1](m3_global_entrance_design.md) | `tests/test_m3_global2d.py::test_every_exact_construction_field_matches_an_analytic_hexagon` |
| A35 | 二维凸角 + 圆盘的圆角入口复合，半径 r1+r2 | 原文已有 | 2015 §6.3–6.4；2021 §5.3 | [映射表 §三 定理一](canon_map.md)；本仓库尚未实现圆角对象复合 | 无门 |
| A36 | 一般膨胀恒等式 E(A⊕Bδ,B)=E(A,B)⊕Bδ | 原文没有（本仓库新结果） | 原文 A35 是同代数结构的二维特例；一般公式为标准 Minkowski 结合律推论，不主张数学原创 | [映射表 §三 定理一](canon_map.md)；`src/eab/margin.py` 模块推导 | 无门（现有裕度门共用距离原语，不算独立膨胀恒等式门） |
| A37 | 接触锁态下“在 E 内沿最短路径退出”的歧义 | 原文缺口 | 2015 §3.10 允许合法锁态在 int E，而摘要第 (3) 条、§13 的出口叙述未区分贯入恢复 | [M3 §1、T3](m3_global_entrance_design.md) | `tests/test_m3_global2d.py::test_global_shortest_exit_distinguishes_tight_contact_seam` |
| A38 | §8.2 代数等价链漏平直顶点 | 原文缺口 | 2015 §8.2 要求 e1×e2 与 +z 同向，平直点被漏；集合条件仍可能成立，不能凭此认定整体覆盖必失败 | [M3 T2a 退化点处理](m3_global_entrance_design.md) | `tests/test_m3b_2d.py::test_nonstrict_flat_collinear_local_covers_weakly_cover_boundary` |
| A39 | 对称关系 E(A,B)=−E(B,A)+(a0+b0) | 原文已有 | 2015 §4.5；2021 §7.2 | [勘误/后续边界](canon_errata_20261019.md)；集合差对称性直接代数等式，原文有证明 | `tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance`（非凸环、刚体与单位元门） |

## 不能随归属订正升级的承诺

- 未裁剪局部盖一般是 ∂E 的超集，不是凹块成员判据；三维 VF/FV 必要条件候选也不自动获得局部充分性。
- 任意退化 H、完整 SE(2)/SE(3) 配置障碍、SE(2) 锁定证书、一般仿射运动首入、材料多环与圆角复合均不可从现有结果外推。
- PD_closed 是闭集完全分离的下确界；rho 才以离开贯入集为口径。两者不能互换。
- 接触算法的几何证书不是力学轨迹等价、物理标定、生产替换或数值域外保证。
- 00/01/03 的 14 条订正另见 [勘误清单](canon_errata_20261019.md)；外部正本与历史报告正文均不回写。
