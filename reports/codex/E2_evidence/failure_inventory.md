# 原始全套35个失败：逐节点处置

| # | 原失败节点 | 分类 | 处置 |
|---:|---|---|---|
| 1 | `tests/test_doc_pointers.py::test_every_code_pointer_in_canon_map_names_a_function_at_its_current_line` | 文档指针 | 更新已删除方向窗/链法向的说明与指针；运行 fix_canon_ptrs.py --apply，保留原指针断言。 |
| 2 | `tests/test_invariance_2d.py::test_convex_g0_is_invariant[squares-rot_s0.001_t0]` | a 旧边界不变口径 | 每个变换的完整标签集对独立 Fraction 支撑投影 oracle；每个成员对精确 SAT 零错；带外仍守刚体不变，边界不再强求 FF 标签不变。 |
| 3 | `tests/test_invariance_2d.py::test_convex_g0_is_invariant[squares-rot_s1_t0]` | a 旧边界不变口径 | 每个变换的完整标签集对独立 Fraction 支撑投影 oracle；每个成员对精确 SAT 零错；带外仍守刚体不变，边界不再强求 FF 标签不变。 |
| 4 | `tests/test_invariance_2d.py::test_convex_g0_is_invariant[squares-rot_s1_t1000]` | a 旧边界不变口径 | 每个变换的完整标签集对独立 Fraction 支撑投影 oracle；每个成员对精确 SAT 零错；带外仍守刚体不变，边界不再强求 FF 标签不变。 |
| 5 | `tests/test_invariance_2d.py::test_convex_g0_is_invariant[squares-rot_s1_t100000]` | a 旧边界不变口径 | 每个变换的完整标签集对独立 Fraction 支撑投影 oracle；每个成员对精确 SAT 零错；带外仍守刚体不变，边界不再强求 FF 标签不变。 |
| 6 | `tests/test_invariance_2d.py::test_convex_g0_is_invariant[squares-rot_s1000_t0]` | a 旧边界不变口径 | 每个变换的完整标签集对独立 Fraction 支撑投影 oracle；每个成员对精确 SAT 零错；带外仍守刚体不变，边界不再强求 FF 标签不变。 |
| 7 | `tests/test_invariance_2d.py::test_convex_g0_is_invariant[squares-rot_s1000_t1000]` | a 旧边界不变口径 | 每个变换的完整标签集对独立 Fraction 支撑投影 oracle；每个成员对精确 SAT 零错；带外仍守刚体不变，边界不再强求 FF 标签不变。 |
| 8 | `tests/test_invariance_2d.py::test_convex_g0_is_invariant[brick_square-rot_s0.001_t0]` | a 旧边界不变口径 | 每个变换的完整标签集对独立 Fraction 支撑投影 oracle；每个成员对精确 SAT 零错；带外仍守刚体不变，边界不再强求 FF 标签不变。 |
| 9 | `tests/test_invariance_2d.py::test_convex_g0_is_invariant[brick_square-rot_s0.001_t1000]` | a 旧边界不变口径 | 每个变换的完整标签集对独立 Fraction 支撑投影 oracle；每个成员对精确 SAT 零错；带外仍守刚体不变，边界不再强求 FF 标签不变。 |
| 10 | `tests/test_invariance_2d.py::test_convex_g0_is_invariant[brick_square-rot_s0.001_t100000]` | a 旧边界不变口径 | 每个变换的完整标签集对独立 Fraction 支撑投影 oracle；每个成员对精确 SAT 零错；带外仍守刚体不变，边界不再强求 FF 标签不变。 |
| 11 | `tests/test_invariance_2d.py::test_convex_g0_is_invariant[brick_square-rot_s1_t0]` | a 旧边界不变口径 | 每个变换的完整标签集对独立 Fraction 支撑投影 oracle；每个成员对精确 SAT 零错；带外仍守刚体不变，边界不再强求 FF 标签不变。 |
| 12 | `tests/test_invariance_2d.py::test_convex_g0_is_invariant[brick_square-rot_s1_t1000]` | a 旧边界不变口径 | 每个变换的完整标签集对独立 Fraction 支撑投影 oracle；每个成员对精确 SAT 零错；带外仍守刚体不变，边界不再强求 FF 标签不变。 |
| 13 | `tests/test_invariance_2d.py::test_convex_g0_is_invariant[brick_square-rot_s1_t100000]` | a 旧边界不变口径 | 每个变换的完整标签集对独立 Fraction 支撑投影 oracle；每个成员对精确 SAT 零错；带外仍守刚体不变，边界不再强求 FF 标签不变。 |
| 14 | `tests/test_invariance_2d.py::test_convex_g0_is_invariant[brick_square-rot_s1000_t0]` | a 旧边界不变口径 | 每个变换的完整标签集对独立 Fraction 支撑投影 oracle；每个成员对精确 SAT 零错；带外仍守刚体不变，边界不再强求 FF 标签不变。 |
| 15 | `tests/test_invariance_2d.py::test_convex_g0_is_invariant[brick_square-rot_s1000_t1000]` | a 旧边界不变口径 | 每个变换的完整标签集对独立 Fraction 支撑投影 oracle；每个成员对精确 SAT 零错；带外仍守刚体不变，边界不再强求 FF 标签不变。 |
| 16 | `tests/test_kernel2d_predicates.py::test_a_t_vertex_one_ulp_above_the_lowest_edge_is_still_convex[0]` | a 旧微凹接收 | 改为 test_a_t_vertex_one_ulp_above_the_lowest_edge_uses_the_concave_path；四朝向凸路径均拒收，保留平直对照与300点，凹回退对独立闭式缺口 oracle。 |
| 17 | `tests/test_kernel2d_predicates.py::test_a_t_vertex_one_ulp_above_the_lowest_edge_is_still_convex[1]` | a 旧微凹接收 | 改为 test_a_t_vertex_one_ulp_above_the_lowest_edge_uses_the_concave_path；四朝向凸路径均拒收，保留平直对照与300点，凹回退对独立闭式缺口 oracle。 |
| 18 | `tests/test_kernel2d_predicates.py::test_a_t_vertex_one_ulp_above_the_lowest_edge_is_still_convex[2]` | a 旧微凹接收 | 改为 test_a_t_vertex_one_ulp_above_the_lowest_edge_uses_the_concave_path；四朝向凸路径均拒收，保留平直对照与300点，凹回退对独立闭式缺口 oracle。 |
| 19 | `tests/test_kernel2d_predicates.py::test_a_t_vertex_one_ulp_above_the_lowest_edge_is_still_convex[3]` | a 旧微凹接收 | 改为 test_a_t_vertex_one_ulp_above_the_lowest_edge_uses_the_concave_path；四朝向凸路径均拒收，保留平直对照与300点，凹回退对独立闭式缺口 oracle。 |
| 20 | `tests/test_kernel2d_predicates.py::test_true_parallel_edges_with_length_ratio_1000_merge_after_rotation[0]` | a 旧近似平行合并 | 改为 test_parallel_edges_with_length_ratio_1000_merge_only_if_exact_after_rotation；FF 标签逐一对独立 Fraction 反平行边对，保留10种子，G0零豁免。 |
| 21 | `tests/test_kernel2d_predicates.py::test_true_parallel_edges_with_length_ratio_1000_merge_after_rotation[1]` | a 旧近似平行合并 | 改为 test_parallel_edges_with_length_ratio_1000_merge_only_if_exact_after_rotation；FF 标签逐一对独立 Fraction 反平行边对，保留10种子，G0零豁免。 |
| 22 | `tests/test_kernel2d_predicates.py::test_true_parallel_edges_with_length_ratio_1000_merge_after_rotation[2]` | a 旧近似平行合并 | 改为 test_parallel_edges_with_length_ratio_1000_merge_only_if_exact_after_rotation；FF 标签逐一对独立 Fraction 反平行边对，保留10种子，G0零豁免。 |
| 23 | `tests/test_kernel2d_predicates.py::test_true_parallel_edges_with_length_ratio_1000_merge_after_rotation[3]` | a 旧近似平行合并 | 改为 test_parallel_edges_with_length_ratio_1000_merge_only_if_exact_after_rotation；FF 标签逐一对独立 Fraction 反平行边对，保留10种子，G0零豁免。 |
| 24 | `tests/test_kernel2d_predicates.py::test_true_parallel_edges_with_length_ratio_1000_merge_after_rotation[4]` | a 旧近似平行合并 | 改为 test_parallel_edges_with_length_ratio_1000_merge_only_if_exact_after_rotation；FF 标签逐一对独立 Fraction 反平行边对，保留10种子，G0零豁免。 |
| 25 | `tests/test_kernel2d_predicates.py::test_true_parallel_edges_with_length_ratio_1000_merge_after_rotation[5]` | a 旧近似平行合并 | 改为 test_parallel_edges_with_length_ratio_1000_merge_only_if_exact_after_rotation；FF 标签逐一对独立 Fraction 反平行边对，保留10种子，G0零豁免。 |
| 26 | `tests/test_kernel2d_predicates.py::test_true_parallel_edges_with_length_ratio_1000_merge_after_rotation[6]` | a 旧近似平行合并 | 改为 test_parallel_edges_with_length_ratio_1000_merge_only_if_exact_after_rotation；FF 标签逐一对独立 Fraction 反平行边对，保留10种子，G0零豁免。 |
| 27 | `tests/test_kernel2d_predicates.py::test_true_parallel_edges_with_length_ratio_1000_merge_after_rotation[7]` | a 旧近似平行合并 | 改为 test_parallel_edges_with_length_ratio_1000_merge_only_if_exact_after_rotation；FF 标签逐一对独立 Fraction 反平行边对，保留10种子，G0零豁免。 |
| 28 | `tests/test_kernel2d_predicates.py::test_true_parallel_edges_with_length_ratio_1000_merge_after_rotation[8]` | a 旧近似平行合并 | 改为 test_parallel_edges_with_length_ratio_1000_merge_only_if_exact_after_rotation；FF 标签逐一对独立 Fraction 反平行边对，保留10种子，G0零豁免。 |
| 29 | `tests/test_kernel2d_predicates.py::test_true_parallel_edges_with_length_ratio_1000_merge_after_rotation[9]` | a 旧近似平行合并 | 改为 test_parallel_edges_with_length_ratio_1000_merge_only_if_exact_after_rotation；FF 标签逐一对独立 Fraction 反平行边对，保留10种子，G0零豁免。 |
| 30 | `tests/test_kernel2d_predicates.py::test_a_vertex_fifty_tolerances_inside_the_hull_is_rejected` | a 旧容差内凸 | 原50t拒收及0.5t接收两输入保留，改成二者均精确拒收；平直接受由96格旧门继续看护。 |
| 31 | `tests/test_kernel2d_predicates.py::test_the_length_tolerance_is_the_slack_for_the_long_edge_rotation[1.0]` | a 旧tol决定FF | 改为 test_length_tolerance_never_changes_exact_parallel_merging；保留两倾角，增0分界和三种tol，完整产物不依tol且三种几何产物互异。 |
| 32 | `tests/test_kernel2d_predicates.py::test_the_length_tolerance_is_the_slack_for_the_long_edge_rotation[100000.0]` | a 旧tol决定FF | 改为 test_length_tolerance_never_changes_exact_parallel_merging；保留两倾角，增0分界和三种tol，完整产物不依tol且三种几何产物互异。 |
| 33 | `tests/test_kernel2d_review.py::test_r7_third_vote_hull_vertices_match_and_catch_sign_flip` | a 旧注入路径失效 | 保留法向反号对独立边法向构造公式的看护；另在真实 membership_exact 内部注入边界丢失，要求G0精确报告16个边界错判，非随机变红。 |
| 34 | `tests/test_kernel2d_review.py::test_hull_defect_threshold_is_pinned_on_an_edge_away_from_the_start[2.0-False]` | a 旧微凹阈值/诊断 | 两个原深度均在所有tol下拒收；每格2000随机+3定向点的凹成员对独立闭式 oracle；不再带内豁免。 |
| 35 | `tests/test_kernel2d_review.py::test_hull_defect_threshold_is_pinned_on_an_edge_away_from_the_start[0.5-True]` | a 旧微凹阈值/诊断 | 两个原深度均在所有tol下拒收；每格2000随机+3定向点的凹成员对独立闭式 oracle；不再带内豁免。 |
