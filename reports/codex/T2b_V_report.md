# WO-T2b-V：SE(2) 笼证书独立核验器报告

**一句话结论：按所有者续裁定，P0条件组自检与隔离范围已闭合，八例独立燕尾腐蚀及规范化实例已补齐，本单P0/P1全部完成；相关快档与本单新文件静态门通过，生产对账及新鲜树全仓门仍由所有者另行执行。**

## 1. 合同、范围与回退锚点

唯一规格为[笼引理第5版](file:///D:/eab-wt/cx-t2bv/docs/t2b_cage_lemma.md)，未修改。四个T2a真值几何按许可原样引用；未读取另一工作树WO-T2b进行中文件，未读取生产核验器/提议器。工作树`D:/eab-wt/cx-t2bv`、分支`t2b-v`，起点及回退锚点`146cc76b6e25598f00564438dee7f3282ad52e34`，开工干净。仅新增本单许可文件，无Git写操作、姊妹仓写入、既有文件修改。

核验器不import `eab`，仅用标准库；真值构造引用获准输入模块。几何、矩阵、面积、距离界、贯入与绕数全用整数/Fraction，无浮点判定、无容差。pytest只作测试框架。

**隔离工具范围披露与续裁定**：开工执行`python tools/check_exact_construction.py --help`时，脚本没有参数解析，实际内部全扫`src/tests`，仅返回`exact construction AST gate: 0 violation(s)`，禁读源码未展示给会话。所有者现已明确：仓库门工具内部解析不算本会话读取，维持仅本单新文件调用原版`scan_text`、零准入的做法。未查看或引用生产几何内容。

非目标：改引理、生产实现或提议器；读取同时进行的生产代码；提交/合并/建树；宣称新鲜树或正式对抗验收。生产一致性对账尚未执行，待所有者持同一输入分别核验。续作前21个仓库成果逐个校验旧SHA256并保存56文件回退快照：[回退锚点与逐文件哈希](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/continuation/rollback_anchor.json)；保留上一轮测试、伪造及性能原始证据。

## 2. P0 / P1 状态

| 项 | 状态 | 证据与边界 |
|---|---|---|
| P0.1 核验器与CLI | 已实现并验证 | V0→CHAIN→V1…V6；JSON词法、绑定、拒收退出非零 |
| P0.2 真值几何 | 完成 | 四T2a几何原样引用，低/高房间按§5环与顺序 |
| P0.3 四闭链 | 完成 | [-1,1,3]、同Γ、disk-only、rho=0、at=1/2的[Γ,Γ] |
| P0.4 伪造 | 完成具名首错门 | 逐项表见§5，归码冲突服从唯一规格 |
| P0.5 自检 | 完成（按所有者条件组裁定） | 四闭链各8组共32项，加低房间V1/V2共34项；70原子台账冗余依赖已补齐 |
| P1.6 八燕尾 | 完成 | 任意有理δ独立构造、规范化API、8实例JSON及双向支撑线门，详见§11 |
| P1.7 低房间封口 | 完成 | N=1，±1/23；低房间接受，同构造高房间V4拒 |
| P1.8 性能 | 完成 | 2000区间×16顶点，3次全通过取中位 |

## 3. 引理条件 → 实现函数 → 具名测试

| 规格 | 实现 | 测试 |
|---|---|---|
| §7 JSON、整数记号、有理文法 | load_json / _json_parse / _q / _integer / _decode | test_noncanonical_rational_rejected；test_raw_integer_tokens_rejected_before_information_loss；test_raw_duplicate_keys_rejected_even_when_unicode_escaped |
| §7 实例逐顶点绑定、必需键 | _v0 / _keys | test_geometry_binding_rejects_cyclic_reindexing；test_every_top_level_key_required |
| §2.0 严格凸环、简单环、闭线 | _ring / _segments_meet / _area2 | test_v0_nonconvex_dart_kernel；test_v0_pentagram_mother；test_v0_unclosed_link_fake_endpoint_copy_contraction |
| §2.0 非零轴 | _axes | test_v0_repeated_moving_piece_vertex_with_protrusion；原子防御冗余见§6 |
| §2.1 半径、见证维度 | _v0 | test_v0_tiny_radius_on_escapable_high_room；test_witnesses_mandatory_exact_shape；test_quadrilateral_witness_row_exact_shape |
| §4.1 引理0及划分 | _partition / _strict_inside / _weak_separated | test_v0_parent_edge_crosses_piece_through_two_vertices；test_v0_partition_missing_piece_area；test_v0_partition_overlapping_pieces |
| §1 中点定图与转动 | _chart / _rotate / _rotated_ring | test_midpoint_chart_lift_table；test_exact_rotation_rational_unit_circle_table；test_v1_midpoint_chart_not_independent_endpoint_charts |
| §2.1 CHAIN及起始区间 | _chain / _contains_period | test_chain_one_interval_cannot_cover_zero_to_four；test_chain_wrong_start_interval_cannot_select_a_winding_loop；test_chain_two_caps_at_start_are_not_two_ends |
| V1 收缩界 | _v1 | test_v1_halved_rho；test_v1_negative_rho_even_disk_only |
| V2 收缩片包含 | _v2 | test_v2_kernel_vertex_beyond_eroded_halfplane；test_v2_wrong_moving_piece_reference |
| V3 不变圆 | _v3 | test_v3_host_edge_distance_too_small；test_v3_polygon_vertex_outside_disk；test_v3_host_does_not_contain_center；test_v3_unused_nonnull_disk_is_still_checked |
| V4 同一凸片对严格贯入 | _v4 / _strict_penetration | test_v4_segment_endpoints_require_the_same_pair；test_v4_contact_at_nonzero_translation_is_not_strict |
| V5 四点同伦、侧别与首尾图 | _v5 / _reference | test_v5_connection_quadrilateral_vertex_outside_piece；test_v5_left_reference_forbidden_at_start_cap；test_v5_right_reference_forbidden_at_end_cap；test_v5_closed_seam_exact_uses_last_interval_chart；test_seam_chart_geometry_forgery_kills_wrong_chart_implementation |
| V6 起点自由、原点与绕数 | _v6 / _winding | test_v6_start_pose_has_interior_intersection；test_v6_start_loop_has_zero_winding；test_signed_half_open_winding_with_repeated_and_zero_length_segments |
| §7 首错和同条件JSON次序 | verify_cage / _result / _rank_json / _v0 | test_v0_precedes_chain_and_chain_precedes_v1；test_same_condition_obeys_json_object_field_order；test_late_schema_error_does_not_hide_earlier_radius_bound |
| F 刚体、单位、分辨率 | 整个独立流程 | test_exact_random_rotation_translation_and_unit_invariance：45项，含尺度1/10^6及平移模长10^5 |

实现：[t2b_independent_cage_verifier.py](file:///D:/eab-wt/cx-t2bv/tests/t2b_independent_cage_verifier.py)；逐节点：[test_results.json](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/test_results.json)。有限回归与变异不冒充全输入域证明。

## 4. 手工证书

| 例 | 判定 | 屏障段 | 同伦四边形 | 起始绕数 | 文件 |
|---|---|---|---|---|---|
| doorway | OK | 10 | 10 | 1 | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_hand_cages/doorway.cert.json) |
| windmill | OK | 8 | 8 | 1 | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_hand_cages/windmill.cert.json) |
| midpoint_wedges | OK | 8 | 8 | 1 | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_hand_cages/midpoint_wedges.cert.json) |
| diamond_plates | OK | 8 | 8 | 1 | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_hand_cages/diamond_plates.cert.json) |
| low_room | OK | 20 | 160 | 1 | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_hand_cages/low_room.cert.json) |

四闭链外包半径r统一取2，全部顶点界通过。不变圆严格按工单：门洞r_D=3/8+1/1024；风车/中点楔r_D=1、20边形；菱形四板r_D=7/10，D=[−49/100,49/100]²。见证全部显式给出，核验器不搜索。

低房间：r=8/5、rho=7/50，E=[−34/25,34/25]×[−9/25,9/25]。u端点±1/23，对应cos=264/265、sin=±23/265；V1余量37/132500>0，V2边距取等号。Γ20段，两封口各5条闭线按1、3/4、1/2、1/4、0收缩；各80四边形用exact见证。高房间同步更新实例、证书几何及划分，首错V4/barrier_strict，非绑定错误。

十个JSON共69,249字节；[逐证书与SHA256](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/builder_case_results.json)；[高房间结果](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/high_room_replay.result.json)。

## 5. 伪造集逐项

### 5.1 几何、链及语义伪造

| 具名测试 | 预期 | 实得首错 | 检查标识 |
|---|---|---|---|
| test_t2b_v_geometry::test_v0_radius_bound_not_v1 | V0 | V0 | radius_bound |
| test_t2b_v_geometry::test_v0_tiny_radius_on_escapable_high_room | V0 | V0 | radius_bound |
| test_t2b_v_geometry::test_v0_negative_radius_of_needle | V0 | V0 | radius_positive |
| test_t2b_v_geometry::test_v0_nonconvex_dart_kernel | V0 | V0 | strict_convex_ring |
| test_t2b_v_geometry::test_v0_repeated_moving_piece_vertex_with_protrusion | V0 | V0 | ring_distinct |
| test_t2b_v_geometry::test_v0_ccw_piece_has_collinear_triple | V0 | V0 | strict_convex_ring |
| test_t2b_v_geometry::test_v0_clockwise_piece | V0 | V0 | partition_area |
| test_t2b_v_geometry::test_v0_pentagram_mother | V0 | V0 | simple_ring |
| test_t2b_v_geometry::test_v0_square_traversed_twice | V0 | V0 | ring_distinct |
| test_t2b_v_geometry::test_v0_partition_missing_piece_area | V0 | V0 | partition_area |
| test_t2b_v_geometry::test_v0_partition_overlapping_pieces | V0 | V0 | partition_disjoint |
| test_t2b_v_geometry::test_v0_partition_piece_outside_parent | V0 | V0 | partition_boundary |
| test_t2b_v_geometry::test_v0_parent_edge_crosses_piece_through_two_vertices | V0 | V0 | partition_boundary |
| test_t2b_v_geometry::test_v0_point_must_have_exactly_two_coordinates | V0 | V0 | point_length |
| test_t2b_v_geometry::test_v0_certificate_root_must_be_an_object | V0 | V0 | object_type |
| test_t2b_v_geometry::test_v0_convex_ring_needs_three_vertices | V0 | V0 | ring_length |
| test_t2b_v_geometry::test_v0_loop_needs_at_least_one_explicit_segment | V0 | V0 | loop_length |
| test_t2b_v_geometry::test_v0_simple_mother_needs_positive_signed_area | V0 | V0 | ring_positive_area |
| test_t2b_v_geometry::test_v0_nonnull_disk_radius_must_be_positive | V0 | V0 | disk_radius_positive |
| test_t2b_v_geometry::test_v0_disk_reference_has_no_index_argument | V0 | V0 | ref_length |
| test_t2b_v_geometry::test_v0_witness_has_exactly_two_entries | V0 | V0 | witness_arity |
| test_t2b_v_geometry::test_v0_partition_mean_must_be_strictly_inside_parent | V0 | V0 | partition_interior_point |
| test_t2b_v_geometry::test_v1_halved_rho | V1 | V1 | rotation_bound |
| test_t2b_v_geometry::test_v1_negative_rho_even_disk_only | V1 | V1 | rho_nonnegative |
| test_t2b_v_geometry::test_v1_midpoint_chart_not_independent_endpoint_charts | V1 | V1 | rotation_bound |
| test_t2b_v_geometry::test_v2_kernel_vertex_beyond_eroded_halfplane | V2 | V2 | rotated_containment |
| test_t2b_v_geometry::test_v2_wrong_moving_piece_reference | V2 | V2 | rotated_containment |
| test_t2b_v_geometry::test_v3_host_edge_distance_too_small | V3 | V3 | disk_host |
| test_t2b_v_geometry::test_v3_polygon_vertex_outside_disk | V3 | V3 | disk_polygon |
| test_t2b_v_geometry::test_v3_host_does_not_contain_center | V3 | V3 | disk_host |
| test_t2b_v_geometry::test_v3_unused_nonnull_disk_is_still_checked | V3 | V3 | disk_host |
| test_t2b_v_geometry::test_v4_loop_vertex_in_free_region | V4 | V4 | barrier_strict |
| test_t2b_v_geometry::test_v4_segment_endpoints_require_the_same_pair | V4 | V4 | barrier_strict |
| test_t2b_v_geometry::test_v4_contact_at_nonzero_translation_is_not_strict | V4 | V4 | barrier_strict |
| test_t2b_v_geometry::test_v5_connection_quadrilateral_vertex_outside_piece | V5 | V5 | homotopy_strict |
| test_t2b_v_geometry::test_v5_left_index_out_of_range_not_v0 | V5 | V5 | side_index |
| test_t2b_v_geometry::test_v5_right_index_out_of_range_not_v0 | V5 | V5 | side_index |
| test_t2b_v_geometry::test_v5_nonadjacent_interval_kernel_cannot_supply_local_index | V5 | V5 | side_index |
| test_t2b_v_geometry::test_v5_closed_seam_exact_uses_last_interval_chart | V5 | V5 | homotopy_strict |
| test_t2b_v_geometry::test_v5_left_reference_forbidden_at_start_cap | V5 | V5 | reference_side |
| test_t2b_v_geometry::test_v5_right_reference_forbidden_at_end_cap | V5 | V5 | reference_side |
| test_t2b_v_geometry::test_v5_constant_cap_point_in_free_space | V5 | V5 | homotopy_strict |
| test_t2b_v_geometry::test_v6_start_pose_has_interior_intersection | V6 | V6 | start_free |
| test_t2b_v_geometry::test_v6_start_loop_has_zero_winding | V6 | V6 | start_winding |
| test_t2b_v_geometry::test_origin_crossing_free_start_first_fails_v4 | V4 | V4 | barrier_strict |
| test_t2b_v_geometry::test_origin_crossing_v4_valid_first_fails_v6_start_pose | V6 | V6 | start_free |
| test_t2b_v_geometry::test_cross_input_replay_of_doorway_threshold_is_v0 | V0 | V0 | instance_binding |
| test_t2b_v_geometry::test_doorway_equal_width_invariant_disk_is_rejected | V4 | V4 | barrier_strict |
| test_t2b_v_geometry::test_same_low_room_construction_rebound_to_high_room_is_rejected | V4 | V4 | barrier_strict |
| test_t2b_v_chain::test_v0_barrier_requires_explicit_closing_vertex | V0 | V0 | loop_closed |
| test_t2b_v_chain::test_v0_unclosed_link_fake_endpoint_copy_contraction | V0 | V0 | loop_closed |
| test_t2b_v_chain::test_v0_unclosed_cap_fake_endpoint_copy_contraction | V0 | V0 | loop_closed |
| test_t2b_v_chain::test_v0_link_adjacent_polyline_vertex_counts_disagree | V0 | V0 | homotopy_vertex_count |
| test_t2b_v_chain::test_v0_cap_adjacent_polyline_vertex_counts_disagree | V0 | V0 | homotopy_vertex_count |
| test_t2b_v_chain::test_v0_link_must_have_at_least_two_lines | V0 | V0 | homotopy_length |
| test_t2b_v_chain::test_v0_cap_must_have_at_least_two_lines | V0 | V0 | homotopy_length |
| test_t2b_v_chain::test_v0_geometry_binding_rejects_cyclic_shift | V0 | V0 | instance_binding |
| test_t2b_v_chain::test_v0_obstacle_without_any_partition_piece | V0 | V0 | partition_nonempty |
| test_t2b_v_chain::test_chain_breakpoints_not_strictly_increasing | CHAIN | CHAIN | interval_chart |
| test_t2b_v_chain::test_chain_interval_crosses_chart_boundary_one | CHAIN | CHAIN | interval_chart |
| test_t2b_v_chain::test_chain_one_interval_cannot_cover_zero_to_four | CHAIN | CHAIN | interval_chart |
| test_t2b_v_chain::test_chain_closed_total_span_not_four | CHAIN | CHAIN | chain_span |
| test_t2b_v_chain::test_chain_capped_arc_does_not_contain_zero | CHAIN | CHAIN | capped_zero_interior |
| test_t2b_v_chain::test_chain_zero_at_cap_endpoint_not_strictly_inside_arc | CHAIN | CHAIN | capped_zero_interior |
| test_t2b_v_chain::test_chain_start_interval_does_not_contain_zero | CHAIN | CHAIN | start_interval_contains_zero |
| test_t2b_v_chain::test_chain_wrong_start_interval_cannot_select_a_winding_loop | CHAIN | CHAIN | start_interval_contains_zero |
| test_t2b_v_chain::test_chain_start_cap_first_line_differs_from_first_barrier | CHAIN | CHAIN | cap_start |
| test_t2b_v_chain::test_chain_end_cap_first_line_differs_from_last_barrier | CHAIN | CHAIN | cap_start |
| test_t2b_v_chain::test_chain_cap_final_line_is_not_constant | CHAIN | CHAIN | cap_constant |
| test_t2b_v_chain::test_chain_two_caps_at_start_are_not_two_ends | CHAIN | CHAIN | cap_set |
| test_t2b_v_chain::test_chain_missing_end_cap | CHAIN | CHAIN | cap_set |
| test_t2b_v_chain::test_chain_link_first_line_differs_from_left_barrier | CHAIN | CHAIN | link_endpoints |
| test_t2b_v_chain::test_chain_link_final_line_differs_from_right_barrier | CHAIN | CHAIN | link_endpoints |
| test_t2b_v_chain::test_chain_missing_closed_seam_link | CHAIN | CHAIN | link_set |
| test_t2b_v_chain::test_chain_duplicate_link_item | CHAIN | CHAIN | link_set |
| test_t2b_v_chain::test_chain_closed_chain_must_not_have_caps | CHAIN | CHAIN | cap_set |

完整定位、原因和计数：[forgery_evidence.json](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/forgery_evidence.json)；[复跑脚本](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/rerun_forgery_evidence.py)。

### 5.2 文法、JSON、下标、绑定与CLI参数化明细

| 节点 | 预期 | 实得 |
|---|---|---|
| test_four_hand_certificates_accepted[doorway] | OK | OK（断言通过） |
| test_four_hand_certificates_accepted[windmill] | OK | OK（断言通过） |
| test_four_hand_certificates_accepted[midpoint_wedges] | OK | OK（断言通过） |
| test_four_hand_certificates_accepted[diamond_plates] | OK | OK（断言通过） |
| test_low_room_rotated_capped_certificate_accepted | OK | OK（断言通过） |
| test_noncanonical_rational_rejected[ 3/8] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[1e-3] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[0.5] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[1_000] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[+3] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[-0] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[0/5] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[2/4] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[3/1] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[\uff11] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[\u0661] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[1/\uff12] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[1/-2] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[03] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[-0/5] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[3/0] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[3/08] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[3/8 ] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[\t3/8] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[3\n] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[--3] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[/3] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[1/2/3] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[NaN] | V0 | V0（断言通过） |
| test_noncanonical_rational_rejected[Infinity] | V0 | V0（断言通过） |
| test_nonstring_rational_rejected[1] | V0 | V0（断言通过） |
| test_nonstring_rational_rejected[True] | V0 | V0（断言通过） |
| test_nonstring_rational_rejected[None] | V0 | V0（断言通过） |
| test_nonstring_rational_rejected[value3] | V0 | V0（断言通过） |
| test_nonstring_rational_rejected[value4] | V0 | V0（断言通过） |
| test_nonstring_rational_rejected[0.5] | V0 | V0（断言通过） |
| test_rational_decoded_length_limit | V0 | V0（断言通过） |
| test_every_top_level_key_required[format] | V0 | V0（断言通过） |
| test_every_top_level_key_required[moving] | V0 | V0（断言通过） |
| test_every_top_level_key_required[obstacles] | V0 | V0（断言通过） |
| test_every_top_level_key_required[center] | V0 | V0（断言通过） |
| test_every_top_level_key_required[radius] | V0 | V0（断言通过） |
| test_every_top_level_key_required[moving_pieces] | V0 | V0（断言通过） |
| test_every_top_level_key_required[obstacle_pieces] | V0 | V0（断言通过） |
| test_every_top_level_key_required[disk] | V0 | V0（断言通过） |
| test_every_top_level_key_required[chain] | V0 | V0（断言通过） |
| test_every_top_level_key_required[start_interval] | V0 | V0（断言通过） |
| test_every_top_level_key_required[intervals] | V0 | V0（断言通过） |
| test_every_top_level_key_required[links] | V0 | V0（断言通过） |
| test_every_top_level_key_required[caps] | V0 | V0（断言通过） |
| test_unknown_keys_rejected_at_every_object_schema[top] | V0 | V0（断言通过） |
| test_unknown_keys_rejected_at_every_object_schema[chain] | V0 | V0（断言通过） |
| test_unknown_keys_rejected_at_every_object_schema[disk] | V0 | V0（断言通过） |
| test_unknown_keys_rejected_at_every_object_schema[interval] | V0 | V0（断言通过） |
| test_unknown_keys_rejected_at_every_object_schema[piece] | V0 | V0（断言通过） |
| test_unknown_keys_rejected_at_every_object_schema[link] | V0 | V0（断言通过） |
| test_unknown_keys_rejected_at_every_object_schema[obstacle_piece] | V0 | V0（断言通过） |
| test_unknown_keys_rejected_at_every_object_schema[instance] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[True-start] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[True-host] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[True-obstacle] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[True-barrier_kernel] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[True-barrier_obstacle] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[True-exact] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[True-at] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[True-left] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[False-start] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[False-host] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[False-obstacle] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[False-barrier_kernel] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[False-barrier_obstacle] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[False-exact] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[False-at] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[False-left] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[-1-start] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[-1-host] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[-1-obstacle] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[-1-barrier_kernel] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[-1-barrier_obstacle] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[-1-exact] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[-1-at] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[-1-left] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[0-start] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[0-host] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[0-obstacle] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[0-barrier_kernel] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[0-barrier_obstacle] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[0-exact] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[0-at] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[0-left] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[None-start] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[None-host] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[None-obstacle] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[None-barrier_kernel] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[None-barrier_obstacle] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[None-exact] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[None-at] | V0 | V0（断言通过） |
| test_index_type_nonnegative_and_bool_exclusion[None-left] | V0 | V0（断言通过） |
| test_index_out_of_bounds_is_v0[start] | V0 | V0（断言通过） |
| test_index_out_of_bounds_is_v0[host] | V0 | V0（断言通过） |
| test_index_out_of_bounds_is_v0[obstacle] | V0 | V0（断言通过） |
| test_index_out_of_bounds_is_v0[barrier_kernel] | V0 | V0（断言通过） |
| test_index_out_of_bounds_is_v0[barrier_obstacle] | V0 | V0（断言通过） |
| test_index_out_of_bounds_is_v0[exact] | V0 | V0（断言通过） |
| test_index_out_of_bounds_is_v0[at] | V0 | V0（断言通过） |
| test_side_index_out_of_bounds_is_v5[left] | V5 | V5（断言通过） |
| test_side_index_out_of_bounds_is_v5[right] | V5 | V5（断言通过） |
| test_unknown_fixed_tags_are_v0[format] | V0 | V0（断言通过） |
| test_unknown_fixed_tags_are_v0[chain] | V0 | V0（断言通过） |
| test_unknown_fixed_tags_are_v0[piece] | V0 | V0（断言通过） |
| test_unknown_fixed_tags_are_v0[reference] | V0 | V0（断言通过） |
| test_witnesses_mandatory_exact_shape[null-interval] | V0 | V0（断言通过） |
| test_witnesses_mandatory_exact_shape[null-link] | V0 | V0（断言通过） |
| test_witnesses_mandatory_exact_shape[missing-interval] | V0 | V0（断言通过） |
| test_witnesses_mandatory_exact_shape[missing-link] | V0 | V0（断言通过） |
| test_witnesses_mandatory_exact_shape[short-interval] | V0 | V0（断言通过） |
| test_witnesses_mandatory_exact_shape[short-link] | V0 | V0（断言通过） |
| test_witnesses_mandatory_exact_shape[long-interval] | V0 | V0（断言通过） |
| test_witnesses_mandatory_exact_shape[long-link] | V0 | V0（断言通过） |
| test_quadrilateral_witness_row_exact_shape[short] | V0 | V0（断言通过） |
| test_quadrilateral_witness_row_exact_shape[long] | V0 | V0（断言通过） |
| test_geometry_binding_rejects_cyclic_reindexing[moving] | V0 | V0（断言通过） |
| test_geometry_binding_rejects_cyclic_reindexing[obstacles] | V0 | V0（断言通过） |
| test_geometry_binding_rejects_obstacle_reorder | V0 | V0（断言通过） |
| test_disk_null_cannot_be_referenced | V0 | V0（断言通过） |
| test_interval_count_and_nonempty_kernel | V0 | V0（断言通过） |
| test_homotopy_needs_two_polylines | V0 | V0（断言通过） |
| test_raw_integer_tokens_rejected_before_information_loss[-0] | V0 | V0（断言通过） |
| test_raw_integer_tokens_rejected_before_information_loss[-1] | V0 | V0（断言通过） |
| test_raw_integer_tokens_rejected_before_information_loss[1.0] | V0 | V0（断言通过） |
| test_raw_integer_tokens_rejected_before_information_loss[1e0] | V0 | V0（断言通过） |
| test_raw_integer_tokens_rejected_before_information_loss[1E+0] | V0 | V0（断言通过） |
| test_raw_integer_tokens_rejected_before_information_loss[NaN] | V0 | V0（断言通过） |
| test_raw_integer_tokens_rejected_before_information_loss[Infinity] | V0 | V0（断言通过） |
| test_raw_integer_tokens_rejected_before_information_loss[-Infinity] | V0 | V0（断言通过） |
| test_raw_integer_tokens_rejected_before_information_loss[true] | V0 | V0（断言通过） |
| test_raw_duplicate_keys_rejected_even_when_unicode_escaped[False] | V0 | V0（断言通过） |
| test_raw_duplicate_keys_rejected_even_when_unicode_escaped[True] | V0 | V0（断言通过） |
| test_cli_many_pairs_one_line_each_and_nonzero_for_any_rejection | OK / V0 / OK；进程非零 | OK / V0 / OK；进程非零（断言通过） |
| test_cli_only_valid_returns_zero | OK | OK（断言通过） |
| test_v0_precedes_chain_and_chain_precedes_v1 | V0 → CHAIN → V1 | V0 → CHAIN → V1（断言通过） |
| test_same_condition_obeys_json_object_field_order | V0 | V0（断言通过） |
| test_schema_error_does_not_hide_earlier_v0_geometry_error | V0 | V0（断言通过） |
| test_late_schema_error_does_not_hide_earlier_radius_bound | V0 | V0（断言通过） |

另有93项独立JSON解析测试，含标准库合法值对照、坏语法、原始数字记号、转义后重复键、5000位整数、1500层数组和`-O`下CLI：[test_t2b_v_json_parser.py](file:///D:/eab-wt/cx-t2bv/tests/test_t2b_v_json_parser.py)。

### 5.3 首错差异

1. 半径平方不足按第5版§7归V0；工单V1小节的重复列项不改变唯一规格。
2. Γ经过原点：q0自由则先坏V4；V4通过则q0已贯入，由V6起点自由检查拒收。两种情形各有具名门，不屏蔽前项来制造原点检查首错。
3. 门洞跨输入重放首错V0；δ=1/8同步更新几何、r_D=3/8和D后首错V4。同方法重建Γ也不能满足严格贯入，接触不算贯入。

## 6. 自检门与限制

| 证书 | 内部禁用条件组 | 原程序 | 变异程序 |
|---|---|---|---|
| doorway | V0 | V0 | OK |
| doorway | CHAIN | CHAIN | OK |
| doorway | V1 | V1 | OK |
| doorway | V2 | V2 | OK |
| doorway | V3 | V3 | OK |
| doorway | V4 | V4 | OK |
| doorway | V5 | V5 | OK |
| doorway | V6 | V6 | OK |
| windmill | V0 | V0 | OK |
| windmill | CHAIN | CHAIN | OK |
| windmill | V1 | V1 | OK |
| windmill | V2 | V2 | OK |
| windmill | V3 | V3 | OK |
| windmill | V4 | V4 | OK |
| windmill | V5 | V5 | OK |
| windmill | V6 | V6 | OK |
| midpoint_wedges | V0 | V0 | OK |
| midpoint_wedges | CHAIN | CHAIN | OK |
| midpoint_wedges | V1 | V1 | OK |
| midpoint_wedges | V2 | V2 | OK |
| midpoint_wedges | V3 | V3 | OK |
| midpoint_wedges | V4 | V4 | OK |
| midpoint_wedges | V5 | V5 | OK |
| midpoint_wedges | V6 | V6 | OK |
| diamond_plates | V0 | V0 | OK |
| diamond_plates | CHAIN | CHAIN | OK |
| diamond_plates | V1 | V1 | OK |
| diamond_plates | V2 | V2 | OK |
| diamond_plates | V3 | V3 | OK |
| diamond_plates | V4 | V4 | OK |
| diamond_plates | V5 | V5 | OK |
| diamond_plates | V6 | V6 | OK |
| low_room | V1 | V1 | OK |
| low_room | V2 | V2 | OK |

变异发生在内部`_require`，不是输出后追加假数据。另有首尾错误图注入：精确片求值改用I1图并漏掉u范围检查时，专门伪造被接受；原核验器由V5语义拒收。

**所有者已裁定P0.5按条件组验收，上表34项满足该口径；不声称每个原子检查独立有牙。** V0/CHAIN/V1～V4及q0自由已推出Γ_n0⊆P_0且0∈F_0，因此单删“不过原点”不可能独立漏收。环门保证边非零，零轴防线也受前置条件蕴含。合法图与at簿记使exact_chart成为防御冗余；N=0必先坏V0的start_interval，CHAIN非空不可能成为首错。

70项清单仍作原子覆盖与冗余台账；下面4条已认定冗余逐行写出具体前置检查、引理及推导，其余66条明确“未认定冗余；按条件组验收”。复杂伪造只证明规定首错，不保证单删该原子就接受；尤其tiny-r高房间样本不是radius_bound-only kill。

### 6.1 全部原子检查清单

70个check_id中67项实际失败激活，3项仅真覆盖。失败激活不等于首错，也不等于独立原子kill。

| check_id | 条件 | 实际执行 | 具名测试（最多 2 个） | 原子冗余 / 验收口径（本行自足） |
|---|---|---|---|---|
| array_type | V0 | false_activated | `test_t2b_v_schema.py::test_late_schema_error_does_not_hide_earlier_radius_bound`<br>`test_t2b_v_schema.py::test_schema_error_does_not_hide_earlier_v0_geometry_error` | 未认定冗余；按条件组验收 |
| at_index | V0 | false_activated | `test_t2b_v_schema.py::test_index_out_of_bounds_is_v0[at]` | 未认定冗余；按条件组验收 |
| barrier_strict | V4 | false_activated | `test_t2b_v_geometry.py::test_doorway_equal_width_invariant_disk_is_rejected`<br>`test_t2b_v_geometry.py::test_origin_crossing_free_start_first_fails_v4` | 未认定冗余；按条件组验收 |
| barrier_witness_count | V0 | false_activated | `test_t2b_v_schema.py::test_witnesses_mandatory_exact_shape[long-interval]`<br>`test_t2b_v_schema.py::test_witnesses_mandatory_exact_shape[short-interval]` | 未认定冗余；按条件组验收 |
| breakpoints_increasing | CHAIN | false_activated | `test_t2b_v_chain.py::test_chain_breakpoints_not_strictly_increasing`<br>`test_t2b_v_schema.py::test_v0_precedes_chain_and_chain_precedes_v1` | 未认定冗余；按条件组验收 |
| cap_constant | CHAIN | false_activated | `test_t2b_v_chain.py::test_chain_cap_final_line_is_not_constant`<br>`test_t2b_v_chain.py::test_chain_closed_chain_must_not_have_caps` | 未认定冗余；按条件组验收 |
| cap_set | CHAIN | false_activated | `test_t2b_v_chain.py::test_chain_closed_chain_must_not_have_caps`<br>`test_t2b_v_chain.py::test_chain_missing_end_cap` | 未认定冗余；按条件组验收 |
| cap_start | CHAIN | false_activated | `test_t2b_v_chain.py::test_chain_end_cap_first_line_differs_from_last_barrier`<br>`test_t2b_v_chain.py::test_chain_start_cap_first_line_differs_from_first_barrier` | 未认定冗余；按条件组验收 |
| capped_zero_interior | CHAIN | false_activated | `test_t2b_v_chain.py::test_chain_capped_arc_does_not_contain_zero`<br>`test_t2b_v_chain.py::test_chain_zero_at_cap_endpoint_not_strictly_inside_arc` | 未认定冗余；按条件组验收 |
| chain_kind | V0 | false_activated | `test_t2b_v_schema.py::test_unknown_fixed_tags_are_v0[chain]` | 未认定冗余；按条件组验收 |
| chain_nonempty | CHAIN | true_only | `test_t2b_v_chain.py::test_chain_breakpoints_not_strictly_increasing`<br>`test_t2b_v_chain.py::test_chain_cap_final_line_is_not_constant` | 条件性冗余；保留下列前提时不声称独立原子kill；前置 check_id：`integer_type`、`start_index`；前置条件：V0 先于 CHAIN；start_interval 为整数且满足 1 ≤ start_interval ≤ N；依据：§2.1 第3项 N≥1 与起始区间；§7 start_interval 范围及 V0→CHAIN 检查顺序；推导：start_index 的不等式 1 ≤ n0 ≤ N 已蕴含 N≥1；当 N≤0 时没有任何整数 n0 能通过 V0。保留 V0 时无法到达一个 chain_nonempty 为假的获准 CHAIN 输入，单删该防御断言不会新增接受结果。 |
| chain_span | CHAIN | false_activated | `test_t2b_v_chain.py::test_chain_closed_total_span_not_four` | 未认定冗余；按条件组验收 |
| disk_host | V3 | false_activated | `test_t2b_v_geometry.py::test_v3_host_does_not_contain_center`<br>`test_t2b_v_geometry.py::test_v3_host_edge_distance_too_small` | 未认定冗余；按条件组验收 |
| disk_polygon | V3 | false_activated | `test_t2b_v_geometry.py::test_v3_polygon_vertex_outside_disk` | 未认定冗余；按条件组验收 |
| disk_present | V0 | false_activated | `test_t2b_v_schema.py::test_disk_null_cannot_be_referenced` | 未认定冗余；按条件组验收 |
| disk_radius_positive | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_nonnull_disk_radius_must_be_positive` | 未认定冗余；按条件组验收 |
| duplicate_key | V0 | false_activated | `test_t2b_v_json_parser.py::test_json_parser_rejects_duplicate_decoded_keys_at_every_depth[[{"same":null,"same":false}]]`<br>`test_t2b_v_json_parser.py::test_json_parser_rejects_duplicate_decoded_keys_at_every_depth[{"a":{"z":0,"z":1}}]` | 未认定冗余；按条件组验收 |
| exact_chart | V5 | true_only | `test_t2b_v_exact_geometry.py::test_exact_random_rotation_translation_and_unit_invariance[scale0-0-low_room]`<br>`test_t2b_v_exact_geometry.py::test_exact_random_rotation_translation_and_unit_invariance[scale0-1000-low_room]` | 条件性冗余；保留下列前提时不声称独立原子kill；前置 check_id：`start_index`、`interval_count`、`interval_chart`、`at_index`、`link_set`、`cap_set`；前置条件：V0 下标和区间数量有效；CHAIN 每个区间使用中点所定的同一合法图；实现按 §3 V5 正确选用端点所属图，首尾相接使用 I_N；依据：§1 区间的图坐标；§2.1 第7、8项连接与封口；§3 V5 精确转动片的端点图；推导：合法 at=0 取 λ_0 与 I_1 的左端点；合法 at=n>0 取 λ_n 与 I_n 的右端点，含闭链首尾 n=N。interval_chart 已检查这些端点的 u 在 [-1,1]，故正确选图后的 exact_chart 必真。该冗余有正确选图这个明确前提，绝不豁免把 λ_N 错用 I_1 的实现；错图变异另有条件组/语义测试，不宣称本原子断言单删可杀。 |
| format | V0 | false_activated | `test_t2b_v_schema.py::test_unknown_fixed_tags_are_v0[format]` | 未认定冗余；按条件组验收 |
| homotopy_length | V0 | false_activated | `test_t2b_v_chain.py::test_v0_cap_must_have_at_least_two_lines`<br>`test_t2b_v_chain.py::test_v0_link_must_have_at_least_two_lines` | 未认定冗余；按条件组验收 |
| homotopy_strict | V5 | false_activated | `test_t2b_v_geometry.py::test_v5_closed_seam_exact_uses_last_interval_chart`<br>`test_t2b_v_geometry.py::test_v5_connection_quadrilateral_vertex_outside_piece` | 未认定冗余；按条件组验收 |
| homotopy_vertex_count | V0 | false_activated | `test_t2b_v_chain.py::test_v0_cap_adjacent_polyline_vertex_counts_disagree`<br>`test_t2b_v_chain.py::test_v0_link_adjacent_polyline_vertex_counts_disagree` | 未认定冗余；按条件组验收 |
| homotopy_witness_count | V0 | false_activated | `test_t2b_v_chain.py::test_v0_cap_adjacent_polyline_vertex_counts_disagree`<br>`test_t2b_v_chain.py::test_v0_link_adjacent_polyline_vertex_counts_disagree` | 未认定冗余；按条件组验收 |
| homotopy_witness_rows | V0 | false_activated | `test_t2b_v_schema.py::test_witnesses_mandatory_exact_shape[long-link]`<br>`test_t2b_v_schema.py::test_witnesses_mandatory_exact_shape[short-link]` | 未认定冗余；按条件组验收 |
| index_range | V0 | false_activated | `test_t2b_v_schema.py::test_index_out_of_bounds_is_v0[barrier_kernel]`<br>`test_t2b_v_schema.py::test_index_out_of_bounds_is_v0[barrier_obstacle]` | 未认定冗余；按条件组验收 |
| instance_binding | V0 | false_activated | `test_t2b_v_chain.py::test_v0_geometry_binding_rejects_cyclic_shift`<br>`test_t2b_v_geometry.py::test_cross_input_replay_of_doorway_threshold_is_v0` | 未认定冗余；按条件组验收 |
| integer_token | V0 | false_activated | `test_t2b_v_json_parser.py::test_json_parser_rejects_malformed_json_syntax['x']`<br>`test_t2b_v_json_parser.py::test_json_parser_rejects_malformed_json_syntax[,]` | 未认定冗余；按条件组验收 |
| integer_type | V0 | false_activated | `test_t2b_v_schema.py::test_index_type_nonnegative_and_bool_exclusion[-1-at]`<br>`test_t2b_v_schema.py::test_index_type_nonnegative_and_bool_exclusion[-1-barrier_kernel]` | 未认定冗余；按条件组验收 |
| interval_chart | CHAIN | false_activated | `test_t2b_v_chain.py::test_chain_breakpoints_not_strictly_increasing`<br>`test_t2b_v_chain.py::test_chain_interval_crosses_chart_boundary_one` | 未认定冗余；按条件组验收 |
| interval_count | V0 | false_activated | `test_t2b_v_schema.py::test_interval_count_and_nonempty_kernel` | 未认定冗余；按条件组验收 |
| json_input | V0 | false_activated | `test_t2b_v_json_parser.py::test_json_parser_rejects_malformed_json_syntax[ ]`<br>`test_t2b_v_json_parser.py::test_json_parser_rejects_malformed_json_syntax[[0]#comment]` | 未认定冗余；按条件组验收 |
| kernel_kind | V0 | false_activated | `test_t2b_v_schema.py::test_unknown_fixed_tags_are_v0[piece]` | 未认定冗余；按条件组验收 |
| kernel_nonempty | V0 | false_activated | `test_t2b_v_schema.py::test_interval_count_and_nonempty_kernel` | 未认定冗余；按条件组验收 |
| link_endpoints | CHAIN | false_activated | `test_t2b_v_chain.py::test_chain_link_final_line_differs_from_right_barrier`<br>`test_t2b_v_chain.py::test_chain_link_first_line_differs_from_left_barrier` | 未认定冗余；按条件组验收 |
| link_set | CHAIN | false_activated | `test_t2b_v_chain.py::test_chain_duplicate_link_item`<br>`test_t2b_v_chain.py::test_chain_missing_closed_seam_link` | 未认定冗余；按条件组验收 |
| loop_avoids_origin | V6 | false_activated | `test_t2b_v_geometry.py::test_origin_crossing_v4_valid_first_fails_v6_start_pose`<br>`test_t2b_v_geometry.py::test_v6_start_pose_has_interior_intersection` | 条件性冗余；保留下列前提时不声称独立原子kill；前置 check_id：`start_interval_contains_zero`、`radius_positive`、`radius_bound`、`rho_nonnegative`、`rotation_bound`、`rotated_containment`、`disk_host`、`disk_polygon`、`barrier_strict`、`start_free`；前置条件：V0 与 CHAIN 通过；V1、V2、V3 对适用内核成立；V4 屏障严格贯入；V6 的 start_free 成立；依据：§2.1 第3项起始区间；§4.2 引理1与引理2；§4.3 引理3；§4.1 划分推论；§3 V6；推导：起始区间含某个 4k，故对应转角为零。引理1、2和 V4 由引理3推出 Γ_n0 ⊆ P_0；V0 划分与 start_free 推出原点属于 F_0。F_0 与 P_0 不交，故 Γ_n0 不过原点。若该断言失败且 V4 已通过，则 start_free 也必失败；若起点自由，则应先由 V4 拒收。保留全部前提时，单删此断言不能新增有效证书；同属 V6 的首错仍按 JSON 顺序选择。 |
| loop_closed | V0 | false_activated | `test_t2b_v_chain.py::test_v0_barrier_requires_explicit_closing_vertex`<br>`test_t2b_v_chain.py::test_v0_unclosed_cap_fake_endpoint_copy_contraction` | 未认定冗余；按条件组验收 |
| loop_length | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_loop_needs_at_least_one_explicit_segment` | 未认定冗余；按条件组验收 |
| missing_key | V0 | false_activated | `test_t2b_v_schema.py::test_every_top_level_key_required[caps]`<br>`test_t2b_v_schema.py::test_every_top_level_key_required[center]` | 未认定冗余；按条件组验收 |
| nonzero_axis | V0 | true_only | `test_t2b_v_chain.py::test_chain_breakpoints_not_strictly_increasing`<br>`test_t2b_v_chain.py::test_chain_cap_final_line_is_not_constant` | 条件性冗余；保留下列前提时不声称独立原子kill；前置 check_id：`ring_length`、`ring_distinct`、`strict_convex_ring`、`simple_ring`；前置条件：V0 环检查通过；SAT 轴只来自凸片边或母体边，不来自允许零长段的屏障折线；依据：§2.0 严格凸环、简单环与非零轴；§4.1 引理0的母体边弱分离判据；§1 Cayley旋转与平移；推导：ring_distinct 保证进入 SAT 的每条片边、母体边端点不同，因此其垂直法向非零；精确 Cayley 旋转可逆、平移单射，派生片不会把不同顶点合并。保留这些环门时，单删 nonzero_axis 不会使原来由零边导致拒收的证书通过；这不声称 Γ 的零长段非法。 |
| object_type | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_certificate_root_must_be_an_object` | 未认定冗余；按条件组验收 |
| partition_area | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_clockwise_piece`<br>`test_t2b_v_geometry.py::test_v0_parent_edge_crosses_piece_through_two_vertices` | 未认定冗余；按条件组验收 |
| partition_boundary | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_parent_edge_crosses_piece_through_two_vertices`<br>`test_t2b_v_geometry.py::test_v0_partition_piece_outside_parent` | 未认定冗余；按条件组验收 |
| partition_disjoint | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_partition_overlapping_pieces` | 未认定冗余；按条件组验收 |
| partition_interior_point | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_partition_mean_must_be_strictly_inside_parent`<br>`test_t2b_v_schema.py::test_geometry_binding_rejects_obstacle_reorder` | 未认定冗余；按条件组验收 |
| partition_nonempty | V0 | false_activated | `test_t2b_v_chain.py::test_v0_obstacle_without_any_partition_piece`<br>`test_t2b_v_schema.py::test_index_out_of_bounds_is_v0[obstacle]` | 未认定冗余；按条件组验收 |
| point_length | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_point_must_have_exactly_two_coordinates` | 未认定冗余；按条件组验收 |
| radius_bound | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_radius_bound_not_v1`<br>`test_t2b_v_geometry.py::test_v0_tiny_radius_on_escapable_high_room` | 未认定冗余；按条件组验收 |
| radius_positive | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_negative_radius_of_needle` | 未认定冗余；按条件组验收 |
| rational_canonical | V0 | false_activated | `test_t2b_v_schema.py::test_noncanonical_rational_rejected[-0/5]`<br>`test_t2b_v_schema.py::test_noncanonical_rational_rejected[-0]` | 未认定冗余；按条件组验收 |
| rational_grammar | V0 | false_activated | `test_t2b_v_schema.py::test_noncanonical_rational_rejected[ 3/8]`<br>`test_t2b_v_schema.py::test_noncanonical_rational_rejected[+3]` | 未认定冗余；按条件组验收 |
| rational_type | V0 | false_activated | `test_t2b_v_schema.py::test_nonstring_rational_rejected[0.5]`<br>`test_t2b_v_schema.py::test_nonstring_rational_rejected[1]` | 未认定冗余；按条件组验收 |
| ref_kind | V0 | false_activated | `test_t2b_v_schema.py::test_unknown_fixed_tags_are_v0[reference]` | 未认定冗余；按条件组验收 |
| ref_length | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_disk_reference_has_no_index_argument` | 未认定冗余；按条件组验收 |
| reference_side | V5 | false_activated | `test_t2b_v_geometry.py::test_v5_left_reference_forbidden_at_start_cap`<br>`test_t2b_v_geometry.py::test_v5_right_reference_forbidden_at_end_cap` | 未认定冗余；按条件组验收 |
| rho_nonnegative | V1 | false_activated | `test_t2b_v_exact_geometry.py::test_json_order_places_rotated_piece_failure_before_rho_if_piece_is_first`<br>`test_t2b_v_geometry.py::test_v1_negative_rho_even_disk_only` | 未认定冗余；按条件组验收 |
| ring_distinct | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_repeated_moving_piece_vertex_with_protrusion`<br>`test_t2b_v_geometry.py::test_v0_square_traversed_twice` | 未认定冗余；按条件组验收 |
| ring_length | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_convex_ring_needs_three_vertices` | 未认定冗余；按条件组验收 |
| ring_positive_area | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_simple_mother_needs_positive_signed_area` | 未认定冗余；按条件组验收 |
| rotated_containment | V2 | false_activated | `test_t2b_v_geometry.py::test_v2_kernel_vertex_beyond_eroded_halfplane`<br>`test_t2b_v_geometry.py::test_v2_wrong_moving_piece_reference` | 未认定冗余；按条件组验收 |
| rotation_bound | V1 | false_activated | `test_t2b_v_geometry.py::test_v1_halved_rho`<br>`test_t2b_v_geometry.py::test_v1_midpoint_chart_not_independent_endpoint_charts` | 未认定冗余；按条件组验收 |
| side_index | V5 | false_activated | `test_t2b_v_geometry.py::test_v5_left_index_out_of_range_not_v0`<br>`test_t2b_v_geometry.py::test_v5_nonadjacent_interval_kernel_cannot_supply_local_index` | 未认定冗余；按条件组验收 |
| simple_ring | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_pentagram_mother` | 未认定冗余；按条件组验收 |
| start_free | V6 | false_activated | `test_t2b_v_geometry.py::test_origin_crossing_v4_valid_first_fails_v6_start_pose`<br>`test_t2b_v_geometry.py::test_v6_start_pose_has_interior_intersection` | 未认定冗余；按条件组验收 |
| start_index | V0 | false_activated | `test_t2b_v_schema.py::test_index_out_of_bounds_is_v0[start]` | 未认定冗余；按条件组验收 |
| start_interval_contains_zero | CHAIN | false_activated | `test_t2b_v_chain.py::test_chain_breakpoints_not_strictly_increasing`<br>`test_t2b_v_chain.py::test_chain_capped_arc_does_not_contain_zero` | 未认定冗余；按条件组验收 |
| start_winding | V6 | false_activated | `test_t2b_v_geometry.py::test_origin_crossing_v4_valid_first_fails_v6_start_pose`<br>`test_t2b_v_geometry.py::test_v6_start_loop_has_zero_winding` | 未认定冗余；按条件组验收 |
| strict_convex_ring | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_ccw_piece_has_collinear_triple`<br>`test_t2b_v_geometry.py::test_v0_clockwise_piece` | 未认定冗余；按条件组验收 |
| unknown_key | V0 | false_activated | `test_t2b_v_schema.py::test_unknown_keys_rejected_at_every_object_schema[chain]`<br>`test_t2b_v_schema.py::test_unknown_keys_rejected_at_every_object_schema[disk]` | 未认定冗余；按条件组验收 |
| witness_arity | V0 | false_activated | `test_t2b_v_geometry.py::test_v0_witness_has_exactly_two_entries` | 未认定冗余；按条件组验收 |

源码行及机器清单：[check_id_inventory.json](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/check_id_inventory.json)；[逐行冗余依赖](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/check_id_inventory.md)；[前轮P0覆盖复核](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/p0_coverage_review.md)。续作仅补台账元数据，67失败激活/3仅真覆盖及源码站点等原始事实与回退快照完全一致：[70项台账轻量审计](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/continuation/ledger_audit.json)。

## 7. 引理疑点清单

**无（未发现笼引理本身的数学漏洞或需修改之处）。** P0.5验收粒度已由所有者裁定；归码按第5版，不改理论。内部审读不等于所有者安排的正式一路对抗核查，未宣称正式0 critical/0 major退出。

## 8. 静态门、准入和前轮快档（续作收尾见§11.3）

前轮静态范围为三个新实现文件及当时全部`tests/test_t2b_v_*.py`；续作增加独立实例模块与测试，当前范围见§11.3。三个分析器与既有policy字节SHA256不变。禁止改既有policy下，采用显式栈、字符扫描与直接有理运算做到零新增准入；没有浮点汇点准入，没有修改或monkeypatch分析器。

T2BV_STATIC_ADMISSIONS_TOTAL=0
T2BV_STATIC_ADMISSIONS_BY_RULE={}

准入清单：空。逐规则计数：{}。[前轮逐文件结果](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/static_final.json)；[自动审计门](file:///D:/eab-wt/cx-t2bv/tests/test_t2b_v_static_admissions.py)。

前轮静态末行原样（仅当时本单新文件）：
```text
exact construction AST gate: 0 violation(s)
```
前轮快档相关测试末行原样（非本轮新增实例测试结果）：
```text
416 passed in 15.34s
```

日志：[pytest_final.log](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/pytest_final.log)；[JUnit](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/pytest_final.xml)；[确切命令及环境](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/verification_command.json)。无skip、无failed。未跑全仓H1快慢全档，未做新鲜树验证，不冒称这些结果。

## 9. 性能（P1）

2000区间，每条Γ16个几何顶点、含显式末点共17项，仅不变圆片。每次完整核验有32,000屏障段、32,000四边形、192,000次严格SAT。计时仅包围verify_cage，不含构造或JSON读取。

| 轮次 | 耗时ns | 判定 |
|---|---|---|
| 1 | 17942941100 | OK |
| 2 | 17839041500 | OK |
| 3 | 17835101400 | OK |

中位数：**17839041500 ns**（35678083/2000 ms，约17.839秒，仅本机此配置）。[来源与SHA256](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/performance_2000.results.json)；[重跑脚本](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/run_builder_performance.py)。

2.35MB大证书只存外部，不入库。初次性能构造误保留start_interval=1，导致CHAIN提前拒收，未算有效性能；改为500后重新三次完整核验。initial_invalid和pre_static记录独立保留，不拼接成成功结果。

## 10. 复跑、交付与剩余事项

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:TEMP='D:/eab-evidence/reports/codex/T2b_V_evidence/tmp'
$env:TMP=$env:TEMP
python -X utf8 tests/t2b_independent_instances.py
python -X utf8 tests/t2b_independent_cage_verifier.py tests/data/t2b_hand_cages/doorway.instance.json tests/data/t2b_hand_cages/doorway.cert.json
python -X utf8 D:/eab-evidence/reports/codex/T2b_V_evidence/continuation/run_verification.py
python -X utf8 D:/eab-evidence/reports/codex/T2b_V_evidence/continuation/audit_check_id_ledger.py
```
历史伪造、手工证书和性能复跑脚本均保留在清单；本次未为整理文档重算冻结性能。

文件、外部证据、大小、格式及SHA256：[交付清单](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/DELIVERABLES.md)；[机器清单](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/manifest.json)。仓库净增小于1MB，新文件UTF-8无BOM、LF，已跟踪文件未变；续作只更新本单已有成果并新增指定实例模块、测试和8份JSON。核验器SHA256与上一轮完全相同：`a7c08891a29a562ac3c10378628fb04f2d8c6c4bb52594d78d4990b8f62304ad`。

交付QA曾发现PowerShell管道把报告脚本中文变为问号，已用直接UTF-8文件写入重建报告与清单，并加入中文字符及问号退化检查；代码、证书和数值结果不受影响。

本单无剩余阻塞项。生产对账、全仓静态门及合并后的新鲜树和正式对抗核查属于所有者后续集成验收；未执行事项不算已验证，不因此冒称跨实现一致。

## 11. 续裁定收尾：P1.6独立实例、冗余台账与复验

### 11.1 八例独立燕尾实例

实现：[t2b_independent_instances.py](file:///D:/eab-wt/cx-t2bv/tests/t2b_independent_instances.py)；标准库实现，不import `eab`，不依赖笼核验器或生产腐蚀代码。仅据获准`tolerance_dovetail`函数重写未腐蚀坐标，固定h=2、wall=2；[允许读取的函数摘录](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/continuation/tolerance_dovetail_permitted_excerpt.txt)及[来源记录](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/continuation/permitted_source.json)。八组参数直接来自所有者本次裁定，未读T2a报告。

| ID | wk | wn | K | e | δ | 规范实例 |
|---|---|---|---|---|---|---|
| d01 | 5/2 | 3/2 | 方形 | 0 | 3/10 | [d01.json](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_independent_instances/d01.json) |
| d02 | 7/2 | 3/2 | 方形 | 0 | 2/5 | [d02.json](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_independent_instances/d02.json) |
| d03 | 5/2 | 1 | 方形 | 0 | 21/50 | [d03.json](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_independent_instances/d03.json) |
| d04 | 5/2 | 1 | 方形 | 1 | 1/5 | [d04.json](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_independent_instances/d04.json) |
| d05 | 7/2 | 3/2 | 八边形 | 0 | 9/20 | [d05.json](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_independent_instances/d05.json) |
| d06 | 3 | 1 | 八边形 | 0 | 11/20 | [d06.json](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_independent_instances/d06.json) |
| d07 | 5/2 | 3/2 | 八边形 | 0 | 7/20 | [d07.json](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_independent_instances/d07.json) |
| d08 | 3 | 3/2 | 八边形 | 1 | 6/25 | [d08.json](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_independent_instances/d08.json) |

`dovetail_instance(wk, wn, K, e, delta)`返回仅有`moving`与`obstacles`的JSON兼容字典，所有坐标为规范有理数字符串。输入接受整数、Fraction及规范有理字符串；拒绝浮点与bool。e=0仅腐蚀移动体，e=1对移动体和left/right/floor三个凸障碍分别腐蚀；障碍顺序不变。K使用工单逐顶点给出的方形与有理八边形。

对每条CCW边取外法向n=(dy,−dx)、b=n·v，构造n·y≤b−h_(δK)(n)，枚举非平行边界交点并用全部精确半平面筛选，再取有理凸包。δ≥0时h_(δK)(n)=δ·max(n·k)，正是裁定公式；任意负有理δ按集合定义y+δK⊆P先缩放K再求支撑，不把负δ误作膨胀。空集返回[]、一点/线段保留实际维数，不伪造有效多边形；这些退化输出不能直接作为§7的满维笼实例。

`canonical_ring(ring)`去相邻重复及显式闭合末点、删除共线边上中间点，非退化简单环转为CCW并从数值字典序最小顶点起列；不取凸包，不抹平凹槽或微小非共线特征。`canonical_instance(instance)`对每个环执行该规范化，保持障碍的对应顺序。该API用于所有者按多边形相等比对；证书绑定仍逐顶点相同，未修改核验器绑定规则。

### 11.2 独立测试方法与具名门

测试oracle只用独立手推的原半平面、顶点点积、面积和有理方向比较，不调用构造器的半平面、交线、腐蚀、凸包或规范化辅助函数。对每个原facet与每条输出边双向一一覆盖，不仅检查输出顶点可行：逐条断言b−b_new=δh_K(n)≥0及距离平方(b−b_new)²/(n·n)=δ²h_K(n)²/(n·n)，全程不开平方。e=0墙逐顶点不变；e=1每个障碍面积严格下降。另测非表δ=7/53、δ=0及精确点/线/空边界。

| 要求 | 实现函数 | 具名测试 |
|---|---|---|
| δ=0等于许可原几何 | dovetail_instance / canonical_ring | test_zero_erosion_equals_allowed_source_geometry |
| 每原边与每新边支撑偏移、精确距离平方 | erode_convex | test_declared_delta_matches_every_old_and_new_support_line |
| 任意非表有理δ | dovetail_instance | test_general_rational_delta_not_in_case_table |
| e=1三障碍各自严格缩小，e=0不改障碍 | dovetail_instance | test_e1_each_of_three_walls_has_strictly_smaller_exact_area；test_e0_all_obstacle_vertices_and_order_remain_exactly_unchanged |
| 8份规范JSON与API一致 | build_independent_instances / write_independent_instances | test_eight_exported_json_instances_are_canonical_and_match_api；test_case_manifest_has_exactly_the_eight_owner_cases |
| 去共线、逆时针、规范起点及障碍顺序 | canonical_ring / canonical_instance | test_canonical_ring_normalizes_only_representation；test_canonical_instance_keeps_obstacle_order |
| 数值字典序及规范化幂等 | canonical_ring / canonical_instance | test_canonical_ring_uses_numeric_not_string_lexicographic_minimum；test_canonical_instance_is_idempotent_after_noncanonical_representation |
| 保留微小非共线角与凹槽 | canonical_ring | test_canonical_ring_preserves_arbitrarily_small_noncollinear_feature；test_canonical_ring_preserves_concave_notch_without_convexifying |
| 退化、空集与负δ集合定义 | erode_convex / dovetail_instance | test_erosion_retains_exact_empty_point_and_segment_boundaries；test_dovetail_exact_collapse_at_five_sixths_and_empty_at_one；test_negative_delta_for_centrally_symmetric_kernel_is_not_dilation；test_negative_delta_reflects_an_asymmetric_kernel_without_abs_shortcut |

测试文件：[test_t2b_v_instances.py](file:///D:/eab-wt/cx-t2bv/tests/test_t2b_v_instances.py)。[逐支撑线与面积精确审计](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/P1_6_instances/independent_instance_oracle_audit.json)记录给定δ及非表δ共16个实例、64个环、256条原支撑线，双向边映射与偏移均通过；[复跑脚本](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/P1_6_instances/rerun_instance_oracle_audit.py)。8份JSON的命令行重生成也逐字节一致，见[实例重导出检查](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/continuation/instance_export_check.json)。冗余台账4条依赖已逐行列于§6.1；[轻量审计](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/continuation/ledger_audit.json)确认70项原执行事实无改写，34组变异结果仍由本轮全部受影响测试实际复验。

### 11.3 本轮受影响测试与静态门末行（原样）

范围为4个新实现文件以及全部`tests/test_t2b_v_*.py`，不提交全仓来源给本轮`scan_text`；三个分析器和既有policy保持原字节，准入仍为0、逐规则计数{}。全部489项相关快档通过、无skip/failed。

```text
489 passed in 13.01s
```
```text
exact construction AST gate: 0 violation(s)
```

证据：[测试完整日志](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/continuation/pytest_final.log)；[JUnit逐节点](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/continuation/pytest_final.xml)；[机器测试结果](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/continuation/test_results.json)；[新文件静态逐文件结果](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/continuation/static_final.json)；[确切命令及环境](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/continuation/verification_command.json)。pytest始终禁cacheprovider、显式basetemp，TEMP/TMP均指向本单外部tmp，禁写pyc。前轮性能未重跑，核验器源码SHA256不变。

T2BV_DONE
