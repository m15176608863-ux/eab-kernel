# T1b 验收续单：A 证书门与措辞归因

本次只修改证书测试，未修改生产核验器；新语义门拒绝“顶点各在不同墙片内、边却穿过自由空间”的假困住证书，真实源码内变异被该语义断言捕获。

## 1. 菱形假证书

- 文件：[test_tia2d_t1b_certificates.py](file:///D:/eab-wt/cx-e2/tests/test_tia2d_t1b_certificates.py)。
- 具名门：`test_enclosure_rejects_blocked_vertices_with_free_edge_interiors`。
- 输入沿用 `_enclosure`：移动正方形半边长 `1/4`，四墙内边界坐标为 `±2`。菱形顶点 `(5/2,0),(0,5/2),(-5/2,0),(0,-5/2)` 分别严格进入右、上、左、下墙的贯入区。四边中点为 `(±5/4,±5/4)`；每个中点平移后的移动方形满足 `abs(coordinate)+1/4 < 2`，因而整块严格处于中央空腔。该整数/有理数矩形判据不调用 E/O 构造。
- 具名变异门：`test_mutation_checking_trapping_endpoints_in_different_pairs_is_killed`。从实际 `_witness` 源码编译变异，将同一凸片包含整段错误改为起点在一片、终点在任意另一片；返回真实起点片编号，不追加假输出。
- 另开独立 Python 进程注入同样变异后直接跑拒绝语义门，最后一行 `1 failed in 0.09s`。失败位置明确为 `AssertionError: enclosure must reject endpoints in different convex pairs`，变异错误接受四段、绕数 `1`。见[变异红灯日志](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/acceptance_fix/trapping_mutant_red.txt)与[执行脚本及元数据](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/acceptance_fix/trapping_mutant_red.json)。
- 初次额外红灯演示脚手架的字符串换行转义有语法错误，未算作语义红灯，已修正并保留 `trapping_mutant_harness_syntax_error.*` 原始记录；提交到测试文件内的变异门无该错误。

## 2. G1 直射线措辞

新增 `test_g1_inner_blocks_have_exact_straight_escape_certificates`，分别对 `t=3/32, delta=0` 的块 `2/3/4` 核验方向 `(-3/32,1)/(0,1)/(3/32,1)`、长度参数 `64` 的单段逃逸证书。三块均通过全线段检查与末端无限射线检查。因此可写“保存的路径来自排列搜索而非直接射线搜索”；不得再写“部分块需绕行”。

## 3. 顶点式腐蚀变异的真实捕获门

实际在 `_contains_element` 通过结构元顶点包含测试后插入 `return True`，然后定向运行以下 17 个参数例，最后一行 `11 failed, 6 passed in 1.65s`。仅进程内源码变异，未落地改动生产文件。

真正失败：

1. `test_element_vertex_only_containment_misses_an_indentation`：U 形槽穿边回归。
2. `test_element_vertices_on_cavity_edges_do_not_certify_filled_containment`：U 形槽边界顶点回归。
3. `test_rational_octagon_reflex_bevel_closed_form`：全部 3 个 delta 参数。
4. `test_disconnected_erosion_and_exact_thin_neck_are_rejected[octagon]`。
5. `test_erosion_exact_rigid_motion_and_units`：八边形的全部 3 个 shift 参数。
6. `test_polygon_knob_reports_actual_segments_and_verified_opposite_states`：square、octagon 两例。

`test_concave_erosion_against_independent_orthogonal_cell_oracle` 的两个矩形覆盖例均未捕获该变异；报告不得将该捕获能力归给它。详见[完整失败列表与脚本](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/acceptance_fix/trapping_erosion_mutation_attribution.json)和[原始日志](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/acceptance_fix/trapping_erosion_mutation_attribution.txt)。

## 4. 最终定向验证

- 完整证书测试文件：`33 passed in 0.16s`，包括新增 2 道证书门及 3 个 G1 直射线参数例；[日志](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/acceptance_fix/trapping_targeted.txt)、[命令及测试源码 SHA256](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/acceptance_fix/trapping_targeted.json)。
- 当前修改测试文件静态构造扫描：`0` 违例，无政策准入变化；[证据](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/acceptance_fix/trapping_changed_static.json)。本次定向扫描不冒称仓库全量静态门。
- 所有 pytest 禁用 cacheprovider，显式 basetemp；TEMP/TMP 均在本单 `reports/codex/T1b_evidence/tmp`。
- 未执行 Git 写操作；完整快档和全档交由主线统筹。
