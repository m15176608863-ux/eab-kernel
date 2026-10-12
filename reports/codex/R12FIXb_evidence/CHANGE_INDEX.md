# 本轮相对执行前字节备份的变更

不是相对 HEAD 的混合 R12FIX diff。

共 78 个源码／测试／工具／文档条目；报告和证据另见交付索引。

[前后 SHA 清单](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/changed_files.json) · [恢复锚点](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/baseline)。

回退须逐文件核对，不应批量覆盖原已接受的 R12FIX 或后续用户改动。

| 状态 | 文件 |
|---|---|
| modified | [README.md](file:///D:/eab-wt/cx-e2/README.md) |
| modified | [docs/canon_map.md](file:///D:/eab-wt/cx-e2/docs/canon_map.md) |
| modified | [docs/r12fix_design_sync.md](file:///D:/eab-wt/cx-e2/docs/r12fix_design_sync.md) |
| modified | [src/eab/dual.py](file:///D:/eab-wt/cx-e2/src/eab/dual.py) |
| modified | [src/eab/kernel2d/covers.py](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/covers.py) |
| modified | [src/eab/kernel2d/entrance.py](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/entrance.py) |
| modified | [src/eab/kernel2d/exact.py](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/exact.py) |
| modified | [src/eab/kernel2d/g0.py](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/g0.py) |
| modified | [src/eab/kernel2d/g0_oracle.py](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/g0_oracle.py) |
| modified | [src/eab/kernel2d/geom.py](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/geom.py) |
| modified | [src/eab/kernel3d/covers3.py](file:///D:/eab-wt/cx-e2/src/eab/kernel3d/covers3.py) |
| modified | [src/eab/kernel3d/entrance3.py](file:///D:/eab-wt/cx-e2/src/eab/kernel3d/entrance3.py) |
| modified | [src/eab/kernel3d/entrance_topology.py](file:///D:/eab-wt/cx-e2/src/eab/kernel3d/entrance_topology.py) |
| modified | [src/eab/kernel3d/exact_geom.py](file:///D:/eab-wt/cx-e2/src/eab/kernel3d/exact_geom.py) |
| modified | [src/eab/kernel3d/frozen.py](file:///D:/eab-wt/cx-e2/src/eab/kernel3d/frozen.py) |
| modified | [src/eab/kernel3d/g03.py](file:///D:/eab-wt/cx-e2/src/eab/kernel3d/g03.py) |
| modified | [src/eab/kernel3d/g03_exact.py](file:///D:/eab-wt/cx-e2/src/eab/kernel3d/g03_exact.py) |
| modified | [src/eab/kernel3d/g03_surface_oracle.py](file:///D:/eab-wt/cx-e2/src/eab/kernel3d/g03_surface_oracle.py) |
| modified | [src/eab/kernel3d/geom3.py](file:///D:/eab-wt/cx-e2/src/eab/kernel3d/geom3.py) |
| modified | [src/eab/kernel3d/interlock.py](file:///D:/eab-wt/cx-e2/src/eab/kernel3d/interlock.py) |
| modified | [src/eab/limit.py](file:///D:/eab-wt/cx-e2/src/eab/limit.py) |
| modified | [src/eab/lp.py](file:///D:/eab-wt/cx-e2/src/eab/lp.py) |
| modified | [src/eab/margin.py](file:///D:/eab-wt/cx-e2/src/eab/margin.py) |
| modified | [src/eab/predicates.py](file:///D:/eab-wt/cx-e2/src/eab/predicates.py) |
| modified | [src/eab/readers/bdda_df.py](file:///D:/eab-wt/cx-e2/src/eab/readers/bdda_df.py) |
| modified | [tests/e5a2_entrance_oracle.py](file:///D:/eab-wt/cx-e2/tests/e5a2_entrance_oracle.py) |
| modified | [tests/e5a2_surface_oracle.py](file:///D:/eab-wt/cx-e2/tests/e5a2_surface_oracle.py) |
| modified | [tests/e5a_convex_oracle.py](file:///D:/eab-wt/cx-e2/tests/e5a_convex_oracle.py) |
| modified | [tests/e5a_cover_oracle.py](file:///D:/eab-wt/cx-e2/tests/e5a_cover_oracle.py) |
| modified | [tests/e5a_g2_oracle.py](file:///D:/eab-wt/cx-e2/tests/e5a_g2_oracle.py) |
| modified | [tests/e5b_frozen_oracle.py](file:///D:/eab-wt/cx-e2/tests/e5b_frozen_oracle.py) |
| modified | [tests/e5b_wall_oracle.py](file:///D:/eab-wt/cx-e2/tests/e5b_wall_oracle.py) |
| modified | [tests/perf_cover_oracle_reference.py](file:///D:/eab-wt/cx-e2/tests/perf_cover_oracle_reference.py) |
| modified | [tests/perf_fraction_reference.py](file:///D:/eab-wt/cx-e2/tests/perf_fraction_reference.py) |
| modified | [tests/test_e5a2_integer_arithmetic.py](file:///D:/eab-wt/cx-e2/tests/test_e5a2_integer_arithmetic.py) |
| modified | [tests/test_e5a2_surface.py](file:///D:/eab-wt/cx-e2/tests/test_e5a2_surface.py) |
| modified | [tests/test_e5b_triangle_boolean.py](file:///D:/eab-wt/cx-e2/tests/test_e5b_triangle_boolean.py) |
| modified | [tests/test_frozen_ee_sign.py](file:///D:/eab-wt/cx-e2/tests/test_frozen_ee_sign.py) |
| modified | [tests/test_geom3_e5a.py](file:///D:/eab-wt/cx-e2/tests/test_geom3_e5a.py) |
| modified | [tests/test_geom3_merge.py](file:///D:/eab-wt/cx-e2/tests/test_geom3_merge.py) |
| modified | [tests/test_interlocking.py](file:///D:/eab-wt/cx-e2/tests/test_interlocking.py) |
| modified | [tests/test_invariance_2d.py](file:///D:/eab-wt/cx-e2/tests/test_invariance_2d.py) |
| modified | [tests/test_invariance_geom.py](file:///D:/eab-wt/cx-e2/tests/test_invariance_geom.py) |
| modified | [tests/test_invariance_interlock.py](file:///D:/eab-wt/cx-e2/tests/test_invariance_interlock.py) |
| modified | [tests/test_kernel2d_convex_ray_exact.py](file:///D:/eab-wt/cx-e2/tests/test_kernel2d_convex_ray_exact.py) |
| modified | [tests/test_kernel2d_entrance_e3.py](file:///D:/eab-wt/cx-e2/tests/test_kernel2d_entrance_e3.py) |
| modified | [tests/test_kernel2d_predicates.py](file:///D:/eab-wt/cx-e2/tests/test_kernel2d_predicates.py) |
| modified | [tests/test_lp.py](file:///D:/eab-wt/cx-e2/tests/test_lp.py) |
| modified | [tests/test_lp_certificates.py](file:///D:/eab-wt/cx-e2/tests/test_lp_certificates.py) |
| modified | [tests/test_margin.py](file:///D:/eab-wt/cx-e2/tests/test_margin.py) |
| modified | [tests/test_margin_resolution.py](file:///D:/eab-wt/cx-e2/tests/test_margin_resolution.py) |
| modified | [tests/test_near_parallel_edges.py](file:///D:/eab-wt/cx-e2/tests/test_near_parallel_edges.py) |
| modified | [tests/test_perf_2d_directions.py](file:///D:/eab-wt/cx-e2/tests/test_perf_2d_directions.py) |
| modified | [tests/test_perf_covers.py](file:///D:/eab-wt/cx-e2/tests/test_perf_covers.py) |
| modified | [tests/test_perf_edge_frame.py](file:///D:/eab-wt/cx-e2/tests/test_perf_edge_frame.py) |
| modified | [tests/test_perf_integer_geometry.py](file:///D:/eab-wt/cx-e2/tests/test_perf_integer_geometry.py) |
| modified | [tests/test_r10_initial_boundary.py](file:///D:/eab-wt/cx-e2/tests/test_r10_initial_boundary.py) |
| modified | [tests/test_r10_static_construction.py](file:///D:/eab-wt/cx-e2/tests/test_r10_static_construction.py) |
| modified | [tests/test_r11fix_static_flow.py](file:///D:/eab-wt/cx-e2/tests/test_r11fix_static_flow.py) |
| modified | [tests/test_r12fix_static_closed.py](file:///D:/eab-wt/cx-e2/tests/test_r12fix_static_closed.py) |
| added | [tests/test_r12fixb_final_mechanism.py](file:///D:/eab-wt/cx-e2/tests/test_r12fixb_final_mechanism.py) |
| added | [tests/test_r12fixb_flow_adversarial.py](file:///D:/eab-wt/cx-e2/tests/test_r12fixb_flow_adversarial.py) |
| added | [tests/test_r12fixb_maintenance.py](file:///D:/eab-wt/cx-e2/tests/test_r12fixb_maintenance.py) |
| added | [tests/test_r12fixb_safe_subset.py](file:///D:/eab-wt/cx-e2/tests/test_r12fixb_safe_subset.py) |
| added | [tests/test_r12fixb_structure_flow.py](file:///D:/eab-wt/cx-e2/tests/test_r12fixb_structure_flow.py) |
| modified | [tests/test_r6fix_construction.py](file:///D:/eab-wt/cx-e2/tests/test_r6fix_construction.py) |
| modified | [tests/test_r6fix_geom3.py](file:///D:/eab-wt/cx-e2/tests/test_r6fix_geom3.py) |
| modified | [tests/test_r7fix_limit_construction.py](file:///D:/eab-wt/cx-e2/tests/test_r7fix_limit_construction.py) |
| modified | [tests/test_r8fix_wrench.py](file:///D:/eab-wt/cx-e2/tests/test_r8fix_wrench.py) |
| modified | [tests/test_r9fix_construction_static.py](file:///D:/eab-wt/cx-e2/tests/test_r9fix_construction_static.py) |
| modified | [tests/test_r9fix_cover_parameters.py](file:///D:/eab-wt/cx-e2/tests/test_r9fix_cover_parameters.py) |
| modified | [tests/test_r9fix_entrance_domain.py](file:///D:/eab-wt/cx-e2/tests/test_r9fix_entrance_domain.py) |
| modified | [tests/test_r9fix_solid_cones.py](file:///D:/eab-wt/cx-e2/tests/test_r9fix_solid_cones.py) |
| modified | [tests/test_r9fix_topology.py](file:///D:/eab-wt/cx-e2/tests/test_r9fix_topology.py) |
| modified | [tools/check_exact_construction.py](file:///D:/eab-wt/cx-e2/tools/check_exact_construction.py) |
| added | [tools/exact_construction_flow.py](file:///D:/eab-wt/cx-e2/tools/exact_construction_flow.py) |
| modified | [tools/exact_construction_policy.json](file:///D:/eab-wt/cx-e2/tools/exact_construction_policy.json) |
| modified | [tools/exact_construction_subset.py](file:///D:/eab-wt/cx-e2/tools/exact_construction_subset.py) |
