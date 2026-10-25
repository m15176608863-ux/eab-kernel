# WO-T2b-V：SE(2) 笼证书独立核验器报告

**一句话结论：验收返修完成，核验器源码零改动；521项相关测试通过，95项单点变异均已复跑，除有前置依赖证明的接受集合等价项外全部被语义测试杀死。**

> 阅读口径：§1～11保留上一轮交付事实（当时基线与文件状态），不冒充本轮执行结果；2026-10-26验收返修的当前基线、修改范围、测试和变异结果以§12为准。所有者现已将前轮成果提交为6d313f1，本会话仍未commit。

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

## 12. 验收返修（2026-10-26）

### 12.1 裁定、边界与当前基线

所有者验收提供：新鲜树全仓静态0违例、相关测试加纯度/文档指针门528 passed，8个燕尾实例与T2a证书几何8/8相等；差分9042例无核验错误、两边接受2191份相同且独立真值确认困住；逐行健全性109攻击均按预期拒收。**这些是所有者提供的验收结果，不是本会话重跑结果。** 本轮只修复变异牙不足，不重新实施生产对账。

当前基线`6d313f1a22520ad066bfc1c67ab8dc1d5175404d`、分支`t2b-v`，开工只读Git核对工作树干净；[回退快照与范围合同](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/baseline.json)。仅修改本单旧测试的断言、新增测试与JSON、更新本报告及外部证据；不改核验器、不改引理、不改三个静态分析器或policy，无commit/checkout/reset等Git写操作，无结束他人进程。核验器SHA256仍为`a7c08891a29a562ac3c10378628fb04f2d8c6c4bb52594d78d4990b8f62304ad`。

只读取准许的独立实现、引理、几何与新给定核查工具/数据；未查看任何生产核验器、kernel2d实现或另一工作树。为执行所有者工具，按只读Git路径清单将仓库字节复制到本单证据下私有目录，不展示/分析禁读源码；没有.git，不声称是新鲜Git工作树。工具只在私有worker修改核验器副本，每次结束恢复；根工作树核验器前后哈希相同。

### 12.2 五重大与可能重大：独立首错反例

下表每一项都已实测**真核验器按指定condition/check拒收，对应单项变异接受**；不是仅用另一错误遮蔽，也不是仅靠静态/源码哈希杀伤。五个high-room核查输入只做紧凑JSON序列化，解析后的实例与证书保持相等；其余独立构造详见复现脚本。V601/V607共用同一个起点碰撞、Γ不过原点且绕数1的反例。

| 变异 | 预期条件/check | 实际条件/check | 对应单变异 | 具名测试 | 数据 |
|---|---|---|---|---|---|
| A17 | V0/homotopy_vertex_count | V0/homotopy_vertex_count | OK | test_A17_growing_homotopy_vertex_count_cannot_hide_reversed_tail | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/major_A17.cert.json) |
| V503 | V5/homotopy_strict | V5/homotopy_strict | OK | test_V503_last_quadrilateral_cannot_hide_a_free_chord_sweep | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/major_V503.cert.json) |
| V304 | V3/disk_polygon | V3/disk_polygon | OK | test_V304_last_invariant_disk_vertex_is_not_an_unchecked_spike | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/major_V304.cert.json) |
| V203 | V2/rotated_containment | V2/rotated_containment | OK | test_V203_last_rotated_kernel_vertex_is_not_an_unchecked_spike | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/major_V203.cert.json) |
| V105 | V1/rotation_bound | V1/rotation_bound | OK | test_V105_disk_first_mixed_kernel_still_requires_rotation_bound | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/major_V105.cert.json) |
| A05 | V0/radius_bound | V0/radius_bound | OK | test_acceptance_a05_radius_checks_last_vertex_not_only_prefix | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/geometry_a05.cert.json) |
| V302 | V3/disk_host | V3/disk_host | OK | test_acceptance_v302_disk_host_requires_nonnegative_support | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/geometry_v302.cert.json) |
| V601 | V6/start_free | V6/start_free | OK | test_acceptance_v601_v607_start_collision_without_origin_crossing | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/geometry_start_free.cert.json) |
| V607 | V6/start_free | V6/start_free | OK | test_acceptance_v601_v607_start_collision_without_origin_crossing | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/geometry_start_free.cert.json) |
| A07 | V0/partition_disjoint | V0/partition_disjoint | OK | test_acceptance_a07_overlap_rejected_even_when_area_sum_matches | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/geometry_a07.cert.json) |
| A08 | V0/partition_boundary | V0/partition_boundary | OK | test_acceptance_a08_boundary_rejected_even_when_area_sum_matches | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/geometry_a08.cert.json) |
| V502 | V5/homotopy_strict | V5/homotopy_strict | OK | test_homotopy_quad_must_check_its_fourth_vertex_v502 | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/forged_V502.cert.json) |
| V506 | V5/homotopy_strict | V5/homotopy_strict | OK | test_capped_chain_interval_side_mapping_must_not_swap_v506 | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/forged_V506.cert.json) |
| J14 | V0/ref_kind | V0/ref_kind | OK | test_J14_unknown_two_item_reference_cannot_fall_through_to_right | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/schema_J14.cert.json) |
| V205 | V2/rotated_containment | V2/rotated_containment | OK | test_chart_two_host_sign_must_not_be_discarded_v205 | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/forged_V205.cert.json) |
| V103 | V1/rotation_bound | V1/rotation_bound | OK | test_rotation_bound_must_include_lower_endpoint_v103 | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/forged_V103.cert.json) |
| V608 | V6/start_winding | V6/start_winding | OK | test_acceptance_v608_winding_uses_selected_interval_not_first | [证书](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/geometry_v608.cert.json) |

具体分离：A05仅最后顶点超半径界；A07两个内部重叠片的面积和恰等于母体；A08剪切片与母体等面积但越出母体边；V302全部平方距离界成立而存在负支撑；V502用同一片对的四点结果为[真,真,真,假]；V506正确I1判失败，错误换I2则四点全真；V103有严格夹界上端界≤ρ²<下端界；V608真实起始区间为2且绕数0，区间1绕数1。

完整单变异记录：[五重大与文法侧别](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/forgery_tests/independent_kills.json)；[几何7项](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/geometry/geometry_mutant_acceptance.json)；[转动与连接](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/rotation/rotation_results.json)；[四点/端点精确算术](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/rotation/geometric_witness_audit.json)。独立轻量复审：[18项质量复审](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/quality_review.md)（不冒充正式新一轮所有者验收）。

### 12.3 次要变异及新增正例

| 变异 | 补门内容 | 实际杀伤类型 |
|---|---|---|
| J07 | JSON整数半径2不能当有理字符串 | 真V0/rational_type；变异OK |
| J15 | 见证额外第三项 | 真V0/witness_arity；变异OK |
| J16 | 点坐标额外第三项 | 真V0/point_length；变异OK |
| C05 | 封口链总长恰为4 | 真CHAIN/chain_span；变异推迟至V5/homotopy_strict，属于首错杀而非接受 |
| C09 | 重复一份完整合法封口 | 真CHAIN/cap_set；变异OK |
| A22 | 多一份结构合法区间 | 真V0/interval_count；变异IndexError，属于异常杀而非接受 |
| A24 | start_interval=0 | 真V0/start_index；变异CHAIN/start_interval_contains_zero，属于首错杀而非接受 |
| A13 | 自接触双瓣母体，三角片面积和恰相等 | 真V0/simple_ring；变异OK，不再列为等价 |
| V505 | 起/末封口分别使用不存在的left/right | 两例真V5/reference_side；变异均OK |
| V106 | 非零u_c正例 | 真正例OK；变异V1/rotation_bound误拒 |
| V507 | 闭链首尾exact正例 | 真正例OK；变异V5/exact_chart误拒 |

A13新增远处未参与见证的障碍母环A=(100,0)、B=(102,0)、C=(102,2)、D=(101,0)、E=(100,2)：D在非相邻边AB内部，顶点互异且无相邻回折；分片ADE与DBC内部不交，各面积1，总面积恰等于母体有向面积2。删非相邻相交检查即接受；[A13结果](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/topology_A13.result.json)。A22/A24/C05明确不称为变异接受；它们通过接口/首错合同的断言杀死。V106/V507只需正例误拒即可证明非等价，不编造不可能的反例接受。

| 正例要求 | 具名测试 | 实际 | 证书 |
|---|---|---|---|
| u_c≠0且rotated片实际用于V4 | test_nonzero_chart_centers_with_used_rotated_kernels_accept | OK | [asymmetric_closed](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/asymmetric_closed.cert.json) |
| 非中心对称移动体在图2使用rotated片 | test_noncentrally_symmetric_body_chart_two_rotated_kernels_accept | OK | [asymmetric_closed](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/asymmetric_closed.cert.json) |
| N=2封口链、两区间内核不同 | test_two_interval_low_room_capped_chain_accepts | OK | [split_low_room](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/split_low_room.cert.json) |
| 内部断点与首尾均用exact连接 | test_internal_and_closed_seam_exact_connections_accept | OK | [asymmetric_closed](file:///D:/eab-wt/cx-t2bv/tests/data/t2b_acceptance/asymmetric_closed.cert.json) |

`asymmetric_closed`含64个区间；独立移动体为(1,0)、(3/4,3/4)、(0,1)、(−1,0)、(0,−1)五边形，障碍来自许可diamond_plates真值函数，(−3/4,−3/4)不在顶点集，确非中心对称。每个区间u_c非零，两图均有被V4实际引用的rotated片，所有内部连接及首尾连接用exact。`split_low_room`实例由本单low_room独立构造，断点−1/23、0、1/23，两段内核不同且封口接受。测试逐值核对JSON实例与独立构造，正例不是照抄核查方实例。[生成方法与边界说明](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/rotation/rotation_notes.md)。

### 12.4 旧测试首错补强与N≤0口径

已给现有起点自由两项、划分四项、顶点数两项及障碍缺片一项，共9项测试补明确`where.check`断言；`partition_interior_point`原测试已有该断言。不能再以另一个V0/V6失败冒充目标检查有牙。分别涉及`start_free`、`partition_area`、`partition_disjoint`、`partition_boundary`、`homotopy_vertex_count`、`partition_nonempty`。

具名新增`test_v0_single_zero_breakpoint_rejects_start_index_before_chain_nonempty`将断点设为["0"]、intervals/links/caps为空、start_interval=1，钉住**V0/start_index**。因为N=0时无整数n0满足1≤n0≤N，V0在CHAIN之前拒收；CHAIN的N≥1检查不可达，保持既有行为、不改引理或核验器。

### 12.5 全部95项变异结果与等价证明

执行所有者提供且SHA256逐字相同的`mutants.py`、`run_mutants.py`，在自有仓库字节副本中逐个应用全部95项替换；每个变异运行全部521个测试节点，累计49495节点，0 skip，节点多重集合逐次核对一致。所有被杀项至少有一个非静态语义测试失败，**静态/hash-only杀伤为0**。测试及数据在全跑后与副本清单哈希一致。

按所给summary.json逐项统计，原文件含36个n_failed=0条目（与验收文字中的33不同，保留原文件、不改写历史数字）；本轮以95项逐项结果为准。当前88项杀死、7项等价存活、0未解释存活。

| ID | 检查 | 判定 | 非静态测试失败数 | 首个语义杀伤测试 / 等价依据 |
|---|---|---|---:|---|
| J01 | duplicate_key | 杀死 | 6 | test_t2b_v_json_parser::test_json_parser_rejects_duplicate_decoded_keys_at_every_depth[{"x":1,"x":2}] |
| J02 | integer_token | 杀死 | 2 | test_t2b_v_json_parser::test_json_parser_rejects_noncanonical_raw_number_tokens[00] |
| J03 | json_input | 杀死 | 2 | test_t2b_v_json_parser::test_json_parser_rejects_malformed_json_syntax[true false] |
| J04 | rational_grammar | 杀死 | 8 | test_t2b_v_schema::test_noncanonical_rational_rejected[1/-2] |
| J05 | rational_grammar(len) | 杀死 | 1 | test_t2b_v_schema::test_rational_decoded_length_limit |
| J06 | rational_canonical | 杀死 | 1 | test_t2b_v_schema::test_noncanonical_rational_rejected[3/1] |
| J07 | rational_type | 杀死 | 1 | test_t2b_v_acceptance_schema::test_J07_valid_radius_as_json_integer_is_rejected_as_rational_type |
| J08 | integer_type(bool) | 杀死 | 12 | test_t2b_v_schema::test_index_type_nonnegative_and_bool_exclusion[True-start] |
| J09 | integer_type(neg) | 杀死 | 2 | test_t2b_v_schema::test_index_type_nonnegative_and_bool_exclusion[-1-at] |
| J10 | missing_key | 杀死 | 15 | test_t2b_v_schema::test_every_top_level_key_required[format] |
| J11 | unknown_key | 杀死 | 8 | test_t2b_v_schema::test_unknown_keys_rejected_at_every_object_schema[top] |
| J12 | format | 杀死 | 1 | test_t2b_v_schema::test_unknown_fixed_tags_are_v0[format] |
| J13 | chain_kind | 杀死 | 1 | test_t2b_v_schema::test_unknown_fixed_tags_are_v0[chain] |
| J14 | ref_kind | 杀死 | 1 | test_t2b_v_acceptance_schema::test_J14_unknown_two_item_reference_cannot_fall_through_to_right |
| J15 | witness_arity | 杀死 | 1 | test_t2b_v_acceptance_schema::test_J15_extra_witness_entry_is_not_silently_ignored |
| J16 | point_length | 杀死 | 1 | test_t2b_v_acceptance_schema::test_J16_extra_point_coordinate_is_not_silently_ignored |
| A01 | instance_binding | 杀死 | 11 | test_t2b_v_chain::test_v0_geometry_binding_rejects_cyclic_shift |
| A02 | instance_binding(obst) | 杀死 | 2 | test_t2b_v_schema::test_geometry_binding_rejects_cyclic_reindexing[obstacles] |
| A03 | radius_positive | 杀死 | 1 | test_t2b_v_geometry::test_v0_negative_radius_of_needle |
| A04 | radius_bound | 杀死 | 7 | test_t2b_v_acceptance_geometry::test_acceptance_a05_radius_checks_last_vertex_not_only_prefix |
| A05 | radius_bound(last) | 杀死 | 1 | test_t2b_v_acceptance_geometry::test_acceptance_a05_radius_checks_last_vertex_not_only_prefix |
| A06 | partition_area | 杀死 | 1 | test_t2b_v_geometry::test_v0_partition_missing_piece_area |
| A07 | partition_disjoint | 杀死 | 2 | test_t2b_v_acceptance_geometry::test_acceptance_a07_overlap_rejected_even_when_area_sum_matches |
| A08 | partition_boundary | 杀死 | 3 | test_t2b_v_acceptance_geometry::test_acceptance_a08_boundary_rejected_even_when_area_sum_matches |
| A09 | partition_interior_point | 杀死 | 1 | test_t2b_v_geometry::test_v0_partition_mean_must_be_strictly_inside_parent |
| A10 | partition_nonempty | 杀死 | 1 | test_t2b_v_chain::test_v0_obstacle_without_any_partition_piece |
| A11 | ring_distinct | 等价 | 0 | 凸环若重复顶点：重复不相邻时，将其中一个视为另一个起边的其余顶点，叉积为 0；重复相邻时该边长为 0，对任一其余顶点叉积仍为 0，均违背 strict_convex_ring。简单环若重复不相邻顶点，其从重复点出发的两条不相邻边相交。若重复相邻顶点且 k>=4，则零边前后两条边不相邻、在该点相交；若 k=3，则三个点中至多两个不同，有向面积为 0。故重复顶点总由剩余门拒收；无重复者原 guard 恒真。 |
| A12 | strict_convex_ring | 杀死 | 1 | test_t2b_v_geometry::test_v0_ccw_piece_has_collinear_triple |
| A13 | simple_ring | 杀死 | 1 | test_t2b_v_acceptance_topology::test_a13_nonadjacent_self_contact_with_exact_partition_is_rejected |
| A14 | ring_positive_area | 杀死 | 1 | test_t2b_v_geometry::test_v0_simple_mother_needs_positive_signed_area |
| A15 | loop_closed | 杀死 | 3 | test_t2b_v_chain::test_v0_barrier_requires_explicit_closing_vertex |
| A16 | loop_length | 杀死 | 1 | test_t2b_v_geometry::test_v0_loop_needs_at_least_one_explicit_segment |
| A17 | homotopy_vertex_count | 杀死 | 1 | test_t2b_v_acceptance_major::test_A17_growing_homotopy_vertex_count_cannot_hide_reversed_tail |
| A18 | homotopy_length | 杀死 | 3 | test_t2b_v_chain::test_v0_link_must_have_at_least_two_lines |
| A19 | homotopy_witness_rows | 杀死 | 1 | test_t2b_v_schema::test_witnesses_mandatory_exact_shape[short-link] |
| A20 | homotopy_witness_count | 杀死 | 1 | test_t2b_v_schema::test_quadrilateral_witness_row_exact_shape[short] |
| A21 | barrier_witness_count | 杀死 | 1 | test_t2b_v_schema::test_witnesses_mandatory_exact_shape[short-interval] |
| A22 | interval_count | 杀死 | 1 | test_t2b_v_acceptance_schema::test_A22_extra_otherwise_valid_interval_is_rejected_before_chart_indexing |
| A23 | kernel_nonempty | 等价 | 0 | 每区间屏障至少两顶点，故至少一段；barrier_witness_count 要求见证数恰等于段数，因此至少一项见证。其内核下标须满足 0<=k<len(pieces)。若 pieces 为空，此不等式无解，即使 kernel_nonempty 被删除仍在 V0/index_range 拒收。非空时原 guard 恒真。 |
| A24 | start_index | 杀死 | 1 | test_t2b_v_acceptance_schema::test_A24_zero_start_interval_is_v0_not_later_chain_rejection |
| A25 | at_index | 杀死 | 1 | test_t2b_v_schema::test_index_out_of_bounds_is_v0[at] |
| A26 | disk_radius_positive | 杀死 | 1 | test_t2b_v_geometry::test_v0_nonnull_disk_radius_must_be_positive |
| A27 | nonzero_axis | 等价 | 0 | SAT 轴仅来自合法严格凸环边，或合法简单母环的一条边（作为两端点线段）；这些边端点不同，法向 (dy,-dx) 必非零。体坐标平移、世界坐标平移及精确转动都是单射，保持边非零。允许重复点/零长段的屏障与同伦折线只作为平移查询点，不作为 _axes 的环参数。故通过剩余环门且到达完整接受路径的所有轴均非零，删除 guard 不扩张接受集合。 |
| A28 | index_range(exact) | 杀死 | 1 | test_t2b_v_schema::test_index_out_of_bounds_is_v0[exact] |
| C01 | breakpoints_increasing | 等价 | 0 | 同一区间的两个端点均减去同一个中点选定图偏移 o，所以 u_plus-u_minus=lambda_upper-lambda_lower。剩余 interval_chart 要求 -1<=u_minus<u_plus<=1，直接推出 lambda_lower<lambda_upper；相等端点仍失败。因此 < 改 <= 不会新增被接受区间。 |
| C02 | interval_chart | 杀死 | 2 | test_t2b_v_chain::test_chain_interval_crosses_chart_boundary_one |
| C03 | interval_chart(upper) | 杀死 | 1 | test_t2b_v_chain::test_chain_interval_crosses_chart_boundary_one |
| C04 | chain_span(closed) | 杀死 | 1 | test_t2b_v_chain::test_chain_closed_total_span_not_four |
| C05 | chain_span(capped) | 杀死 | 1 | test_t2b_v_chain::test_chain_capped_total_span_four_is_strictly_forbidden |
| C06 | start_interval_contains_zero | 杀死 | 2 | test_t2b_v_chain::test_chain_start_interval_does_not_contain_zero |
| C07 | capped_zero_interior | 杀死 | 1 | test_t2b_v_chain::test_chain_zero_at_cap_endpoint_not_strictly_inside_arc |
| C08 | link_set | 杀死 | 1 | test_t2b_v_chain::test_chain_duplicate_link_item |
| C09 | cap_set | 杀死 | 1 | test_t2b_v_acceptance_schema::test_C09_duplicate_valid_cap_is_not_accepted_as_an_at_set |
| C10 | link_endpoints(right) | 杀死 | 1 | test_t2b_v_chain::test_chain_link_final_line_differs_from_right_barrier |
| C11 | link_endpoints(seam) | 杀死 | 4 | test_t2b_v_geometry::test_v4_loop_vertex_in_free_region |
| C12 | cap_start | 杀死 | 2 | test_t2b_v_chain::test_chain_start_cap_first_line_differs_from_first_barrier |
| C13 | cap_constant | 杀死 | 1 | test_t2b_v_chain::test_chain_cap_final_line_is_not_constant |
| C14 | chain_nonempty | 等价 | 0 | V0 在进入 CHAIN 前要求数学下标 n0 满足 1<=n0<=N，其中 N=len(breakpoints)-1。这个整数存在即推出 N>=1。若 N<=0，start_index 已拒；畸形字段先由解码门拒。因此到达可接受 CHAIN 的输入上 chain_nonempty 恒真。 |
| V101 | rho_nonnegative | 杀死 | 7 | test_t2b_v_exact_geometry::test_json_order_places_rotated_piece_failure_before_rho_if_piece_is_first |
| V102 | rotation_bound | 杀死 | 5 | test_t2b_v_acceptance_major::test_V105_disk_first_mixed_kernel_still_requires_rotation_bound |
| V103 | rotation_bound(u-) | 杀死 | 1 | test_t2b_v_acceptance_rotation::test_rotation_bound_must_include_lower_endpoint_v103 |
| V104 | rotation_bound(factor) | 杀死 | 3 | test_t2b_v_acceptance_rotation::test_rotation_bound_must_include_lower_endpoint_v103 |
| V105 | rotation_bound(mixed) | 杀死 | 2 | test_t2b_v_acceptance_major::test_V105_disk_first_mixed_kernel_still_requires_rotation_bound |
| V106 | rotation_bound(center) | 杀死 | 10 | test_t2b_v_acceptance_geometry::test_acceptance_v608_winding_uses_selected_interval_not_first |
| V201 | rotated_containment | 杀死 | 9 | test_t2b_v_acceptance_major::test_V203_last_rotated_kernel_vertex_is_not_an_unchecked_spike |
| V202 | rotated_containment(sign) | 杀死 | 2 | test_t2b_v_acceptance_major::test_V203_last_rotated_kernel_vertex_is_not_an_unchecked_spike |
| V203 | rotated_containment(last) | 杀死 | 1 | test_t2b_v_acceptance_major::test_V203_last_rotated_kernel_vertex_is_not_an_unchecked_spike |
| V204 | rotated_containment(uc) | 杀死 | 25 | test_t2b_v_acceptance_geometry::test_acceptance_v608_winding_uses_selected_interval_not_first |
| V205 | rotated_containment(sign2) | 杀死 | 4 | test_t2b_v_acceptance_rotation::test_nonzero_chart_centers_with_used_rotated_kernels_accept |
| V206 | rotated_containment(pieces) | 杀死 | 5 | test_t2b_v_acceptance_rotation::test_chart_two_host_sign_must_not_be_discarded_v205 |
| V301 | disk_host | 杀死 | 8 | test_t2b_v_acceptance_geometry::test_acceptance_v302_disk_host_requires_nonnegative_support |
| V302 | disk_host(sign) | 杀死 | 1 | test_t2b_v_acceptance_geometry::test_acceptance_v302_disk_host_requires_nonnegative_support |
| V303 | disk_polygon | 杀死 | 2 | test_t2b_v_acceptance_major::test_V304_last_invariant_disk_vertex_is_not_an_unchecked_spike |
| V304 | disk_polygon(last) | 杀死 | 1 | test_t2b_v_acceptance_major::test_V304_last_invariant_disk_vertex_is_not_an_unchecked_spike |
| V401 | barrier_strict | 杀死 | 10 | test_t2b_v_geometry::test_v4_loop_vertex_in_free_region |
| V402 | barrier_strict(first) | 杀死 | 1 | test_t2b_v_geometry::test_v4_segment_endpoints_require_the_same_pair |
| V403 | barrier_strict(last seg) | 杀死 | 4 | test_t2b_v_schema::test_four_hand_certificates_accepted[doorway] |
| V404 | barrier_strict(contact) | 杀死 | 2 | test_t2b_v_geometry::test_doorway_equal_width_invariant_disk_is_rejected |
| V501 | homotopy_strict | 杀死 | 11 | test_t2b_v_acceptance_major::test_V503_last_quadrilateral_cannot_hide_a_free_chord_sweep |
| V502 | homotopy_strict(3pts) | 杀死 | 3 | test_t2b_v_acceptance_major::test_V503_last_quadrilateral_cannot_hide_a_free_chord_sweep |
| V503 | homotopy_strict(last quad) | 杀死 | 1 | test_t2b_v_acceptance_major::test_V503_last_quadrilateral_cannot_hide_a_free_chord_sweep |
| V504 | homotopy_strict(last step) | 杀死 | 6 | test_t2b_v_geometry::test_v5_left_index_out_of_range_not_v0 |
| V505 | reference_side | 杀死 | 2 | test_t2b_v_acceptance_schema::test_V505_start_cap_forbidden_left_has_an_otherwise_valid_quad |
| V506 | reference(left/right swap) | 杀死 | 1 | test_t2b_v_acceptance_rotation::test_capped_chain_interval_side_mapping_must_not_swap_v506 |
| V507 | exact_chart(seam) | 杀死 | 3 | test_t2b_v_acceptance_rotation::test_nonzero_chart_centers_with_used_rotated_kernels_accept |
| V508 | exact_chart | 等价 | 0 | CHAIN 已验证每区间两个端点均在其中点选定图的 [-1,1]。exact 在 at=0 取 I1 的左端；在 1<=at<=N 取 I_at 的右端，特别 at=N 取 I_N 而不是 I1。at 集合及范围先由 V0/CHAIN 固定。因此 _reference 所求 parameter 正是一个已验证端点图坐标，必在 [-1,1]，该 guard 在完整通过前置检查后恒真。 |
| V509 | caps skipped | 杀死 | 8 | test_t2b_v_acceptance_major::test_V503_last_quadrilateral_cannot_hide_a_free_chord_sweep |
| V601 | start_free | 杀死 | 3 | test_t2b_v_acceptance_geometry::test_acceptance_v601_v607_start_collision_without_origin_crossing |
| V602 | loop_avoids_origin | 等价 | 0 | CHAIN 保证所选 I_n0 含一个转角零的提升。V0/V1/V2 与引理 1、V3 与引理 2 保证每个该区间内核含于零转角的真实移动体。V4 每段两端都在同一个开凸贯入片 M 中，故全段都在 M 中；若屏障段经过 t=0，则真实移动体在初始位姿与障碍内部相交。这与未删除的 V6/start_free 矛盾（合法划分使片级自由等价于母体自由）。故所有通过剩余检查的输入自动避开原点。 |
| V603 | start_winding | 杀死 | 6 | test_t2b_v_acceptance_geometry::test_acceptance_v608_winding_uses_selected_interval_not_first |
| V604 | winding(half-open) | 杀死 | 35 | test_t2b_v_acceptance_geometry::test_acceptance_v302_disk_host_requires_nonnegative_support |
| V605 | winding(last seg) | 杀死 | 72 | test_t2b_v_acceptance_geometry::test_acceptance_v302_disk_host_requires_nonnegative_support |
| V606 | winding(downward) | 杀死 | 1 | test_t2b_v_exact_geometry::test_signed_half_open_winding_with_repeated_and_zero_length_segments |
| V607 | weak_separated(always) | 杀死 | 8 | test_t2b_v_acceptance_geometry::test_acceptance_v601_v607_start_collision_without_origin_crossing |
| V608 | start_free(n0 loop) | 杀死 | 1 | test_t2b_v_acceptance_geometry::test_acceptance_v608_winding_uses_selected_interval_not_first |

等价仅指完整入口的**接受集合**相同，不承诺首错、check id或counts相同；因此A10仍可被增强的`partition_nonempty`诊断门杀死。所有存活均在所有者预先允许的8项之内；下面也给出依赖证明。

| ID | 本轮结果 | 保留前提 | 接受集合等价推导 |
|---|---|---|---|
| A10 | 杀死（诊断变化） | ring_positive_area、partition_area | 母体经简单环门且有向面积严格为正。若其片集为空，面积累加初值为 0；A10 仅删除非空 guard，不删除随后 total_area == area2(parent)。故 0 不等于正面积，partition_area 必拒。反之片集非空时原 guard 恒真，删除不影响接受。 |
| A11 | 等价存活 | ring_length、strict_convex_ring、simple_ring、ring_positive_area | 凸环若重复顶点：重复不相邻时，将其中一个视为另一个起边的其余顶点，叉积为 0；重复相邻时该边长为 0，对任一其余顶点叉积仍为 0，均违背 strict_convex_ring。简单环若重复不相邻顶点，其从重复点出发的两条不相邻边相交。若重复相邻顶点且 k>=4，则零边前后两条边不相邻、在该点相交；若 k=3，则三个点中至多两个不同，有向面积为 0。故重复顶点总由剩余门拒收；无重复者原 guard 恒真。 |
| A23 | 等价存活 | loop_length、barrier_witness_count、integer_type、index_range | 每区间屏障至少两顶点，故至少一段；barrier_witness_count 要求见证数恰等于段数，因此至少一项见证。其内核下标须满足 0<=k<len(pieces)。若 pieces 为空，此不等式无解，即使 kernel_nonempty 被删除仍在 V0/index_range 拒收。非空时原 guard 恒真。 |
| A27 | 等价存活 | ring_distinct、strict_convex_ring、simple_ring | SAT 轴仅来自合法严格凸环边，或合法简单母环的一条边（作为两端点线段）；这些边端点不同，法向 (dy,-dx) 必非零。体坐标平移、世界坐标平移及精确转动都是单射，保持边非零。允许重复点/零长段的屏障与同伦折线只作为平移查询点，不作为 _axes 的环参数。故通过剩余环门且到达完整接受路径的所有轴均非零，删除 guard 不扩张接受集合。 |
| C01 | 等价存活 | interval_chart | 同一区间的两个端点均减去同一个中点选定图偏移 o，所以 u_plus-u_minus=lambda_upper-lambda_lower。剩余 interval_chart 要求 -1<=u_minus<u_plus<=1，直接推出 lambda_lower<lambda_upper；相等端点仍失败。因此 < 改 <= 不会新增被接受区间。 |
| C14 | 等价存活 | integer_type、start_index | V0 在进入 CHAIN 前要求数学下标 n0 满足 1<=n0<=N，其中 N=len(breakpoints)-1。这个整数存在即推出 N>=1。若 N<=0，start_index 已拒；畸形字段先由解码门拒。因此到达可接受 CHAIN 的输入上 chain_nonempty 恒真。 |
| V508 | 等价存活 | at_index、link_set、cap_set、interval_chart | CHAIN 已验证每区间两个端点均在其中点选定图的 [-1,1]。exact 在 at=0 取 I1 的左端；在 1<=at<=N 取 I_at 的右端，特别 at=N 取 I_N 而不是 I1。at 集合及范围先由 V0/CHAIN 固定。因此 _reference 所求 parameter 正是一个已验证端点图坐标，必在 [-1,1]，该 guard 在完整通过前置检查后恒真。 |
| V602 | 等价存活 | V0 合法划分及半径界、start_interval_contains_zero、V1、V2、V3、barrier_strict、start_free | CHAIN 保证所选 I_n0 含一个转角零的提升。V0/V1/V2 与引理 1、V3 与引理 2 保证每个该区间内核含于零转角的真实移动体。V4 每段两端都在同一个开凸贯入片 M 中，故全段都在 M 中；若屏障段经过 t=0，则真实移动体在初始位姿与障碍内部相交。这与未删除的 V6/start_free 矛盾（合法划分使片级自由等价于母体自由）。故所有通过剩余检查的输入自动避开原点。 |

逐项完整失败节点与原始末行：[审计汇总JSON](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/mutation_summary.json)；[所有者工具原始结果](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/mutation_run/results/summary.json)；[95份JUnit](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/mutation_run/results)；[副本及输入哈希](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/mutation_copy.json)；[执行命令/环境/耗时](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/mutants_command.json)；[等价证明全文](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/equivalence_notes.md)。

### 12.6 收尾门末行（原样）与交付

相关测试：
```text
521 passed in 16.19s
```
静态门（仅本单新实现与测试，含本轮新增文件）：
```text
exact construction AST gate: 0 violation(s)
```
所有者变异工具最后一行：
```text
V608 start_free(n0 loop) KILLED 1 | 1 failed, 520 passed in 15.94s
```
变异汇总门最后一行：
```text
T2BV_MUTATION_GATE: 95 checked; 88 killed; 7 equivalent; 0 unexplained survivors; 0 static-only kills
```

新增静态准入0、逐规则计数{}；没有浮点汇点准入。pytest始终使用`-p no:cacheprovider`及显式`--basetemp`，TEMP/TMP指向本单证据tmp，`PYTHONDONTWRITEBYTECODE=1`。本轮不重算上一轮2000区间性能，不冒称重跑全仓528项/差分9042项。Windows生成的JUnit失败文本及工具summary含CRLF，先将95份XML及summary原始字节存入[原始输出归档](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/mutation_raw_xml.zip)，再仅把公开XML/JSON换行统一为LF；[逐文件审计](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/junit_lf_audit.json)验证95棵XML解析树及JSON值完全不变，没有改结果、拼接运行或重算证据。

日志：[pytest_final.log](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/pytest_final.log)；[static_final.json](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/static_final.json)；[mutants_full.log](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/mutants_full.log)。当前文件、SHA256、净增、UTF-8无BOM/LF及允许写域核验：[本轮交付清单](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/DELIVERABLES.md)；[本轮机器清单](file:///D:/eab-evidence/reports/codex/T2b_V_evidence/acceptance_repair_20261026/manifest.json)。所有者后续安排新鲜树及正式返修验收；本会话未commit。引理疑点：无。

T2BV_DONE
