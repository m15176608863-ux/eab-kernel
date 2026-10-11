# WO-E5b 执行报告

## 结论与信任边界
工作树全套 **8267 passed in 1479.80s (0:24:39)**；独占进程墙钟 **1498.40 s**。49 个原失败节点全部通过。原 8002 个收集节点全部仍在，当前 8267 个；没有 skip/xfail、删测试、缩装饰器网格或 fixture 改动。

基线 HEAD 仍为 `35667084fd2b6d3c89bd3d284534feea2d5771a5`，分支 `codex-work`，仅交付工作树，未 commit/push/reset/checkout/stash/worktree。62 个 fixture 的字节哈希不变。运行前后 src/tests/tools 哈希逐项一致，日志哈希 `17c53529fb314e9b4577b4a7e74d67aa58b0a889bf6ddb91dfe1182cf634dbf6`。

**未完成项：显式 contact_window 当前仅实现六轴刚性脱离证书 OR 局部径向薄壳政策，不等价于完整贯入深度≤w判定。此前局部/全局深度口径澄清未收到确认，不能将替代政策算成工单契约完成。** 全套绿只证明下列已明确界定的实现与门，不消除此差距。

这是本树开发验证，不是独立六路 G6、全新 worktree 退出、DDA/TIA 工程标定或生产部署。工单禁止创建 worktree，因此没有伪称满足常驻纪律 D/G6 的里程碑退出。

关键证据：[全套日志](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/final.log) · [命令、时间与源码哈希](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/final.json) · [JUnit](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/final.xml) · [交付审计](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/delivery_audit.json) · [完整证据索引](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/INDEX.md) · [改动文件链接清单](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/changed_files.md)

## 1. 契约实现与范围

### 默认精确 + 显式接触窗口

L1/L2 按给定数值的精确有理值判定；`None`/0 不再启用旧 ctol。真微贯入返回 PENETRATING / INSIDE，真正间隙不钳零。默认距离、δ、关注带、closed 状态以精确平方量判定；即使显示值下溢为 0，closed 状态仍按精确量。`entrance_block_convex` 先有理化原坐标，再构造差点。

显式窗口 w 是调用方的报告政策：分离侧比较距离平方与 w²；贯入侧用共享 `contact_models` 的六轴刚性脱离充分证书 OR 局部径向薄壳政策——原实体对、A 的六个 ±w 轴平移、可认证星核的 A/B 内核收缩。收缩壳径向厚度严格不超过 w；任何证书模型非贯入则报相触。margin 和 interlock 使用同一集合，盒闭式门验证根处 ON、稍低 INSIDE。

**重要限定：该窗口不是任意方向完整欧氏穿透深度算法。** 六方向证书有坐标系依赖；星核证明是局部薄壳，不是整块最短刚性逃逸。证书失败不证明真实深度大于 w。它能处理原双壁微夹持窗口，但不能把“有限充分证书”宣传成旋转不变、全空间必要充分的欧氏偏置。旧 ctol 仅由调用方显式取 `contact_resolution(...)` 后传入。

### 互锁最早根

完整三角表面 VF/FV/EE、对角棱、持续共面端点事件全部按有理数枚举；近竖直非零事件保留。根处精确非贯入，每个此前候选开区间的有理中点必须贯入。`exact_height/exact_offset` 为权威数据；`interval_certificate` 为胜出模型的逐区间证明。窗口还通过其他模型的有界完整事件排除更早根，但输出证书不冒充全部模型的序列化证明。

`height` 仅向上舍入显示；逐顶点重新浮点相加是不同数据，须重新判定。`exact_contact_label/normal` 属于精确事件；旧 `cover_label/tied_labels` 仅保留名义报告与导数带。窗口 core/shift winner 的精确 label 属于其证书模型。非 Dual 冻结逃逸用原有理平面比值，不将归一化法向舍入放大；4 个近竖直冻结门逐值等于精确根。

`escape_height_brute` 保留接口但不再用会错过先逃逸再重入的单调二分；它共享精确事件引擎，只是佐证，**独立 oracle 在测试专用扫掠 SAT / 射线包含排除中**。

### 首入、冻结、缓存

首入根/时序/t_max/并列/深度平方与 t* 前有理区间中点自校验全部精确。`merge_degenerate` 仅合并精确共面簇；微台阶杀死恢复容差突变。非共面源环通过 `surface_label/surface_members` 明确三角片；冻结 EE 与 facet 在同视图、同选择时角窗下共用同一精确方向裁决且保留 Dual 导数（facet 默认 tol=0，冻结默认 1e-9，不宣称二者默认选择参数相同）。FF/FE 合并标签须取 surface_members 中原始 VF/FV/EE 成员再冻结。交叉检查另外发现并修复三角对角 EE 取源拓扑导致的真实正负号错误，镜像/尺度/大平移和内部突变看护。

Polyhedron 采用用户允许的**内容签名失效**方案，而非破坏既有可变外层 API；Polyhedron 持有的派生缓存由完整顶点和面内容签名失效。原地顶点替换后不得复用旧 convex view；内部删除顶点签名突变被目标断言捕获。

### 适配器含义

DDA/TIA 必须明确选择严格数据语义或显式厚度政策；不能库内猜测 ctol，也不能把窗口相触当作原实体严格非贯入。精确运动根/特征应保留；舍入导出必须再次检查。姊妹三线只读，本单没有修改它们的适配器或切换开关。

数学定义、API 字段和全部限定见 [三维设计 E5b 节](file:///D:/eab-wt/cx-e2/docs/exact_3d_design.md)；[窗口未完成项与无法绿色回退的说明](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/window_contract_gap.md)。

## 2. 49 红逐条处置
41 个 margin 不变性失败：原断言逐字保留到显式旧窗口，原始输入默认精确另对独立整数四面体并集 SAT。3 个 brute 零高度失败：原始抖动数据对独立扫掠 SAT 最早根零错；不抖动有理同构数据保留原静止恰零断言。4 个墙失败节点各含 20 seed：全部 80 原输入对独立最早根；新增 80 间隙后抖动和 4 理想格，显式旧窗口保留原 0.2/冻结断言。1 个 steep 牙：全部 72 原格和旧断言保留，新增带内漏支义务，同一内部竖向窗突变命中该断言。

逐节点可复查：[49 条机读台账](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/49_disposition.json)。
首轮集成诊断另外暴露 155 红：127 个几何不变性旧源环/窗口域门、24 个近平行旧隐式钳零门、3 个冻结旧源边 oracle 门，以及 1 个优化后突变注入路径过时门。该轮源码曾发生后续编辑，不作最终验收或独占性能成绩；全部逐条映射到最终结果见 [首轮集成 155 条处置](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/integration1_disposition.json)。

| # | 原失败节点 | 最终 |
|---|---|---|
| 1 | `tests.test_interlock_sensitivity::test_steep_gate_has_teeth_vertical_tie_window` | PASS |
| 2 | `tests.test_interlock_walls::test_vertical_walls_do_not_hijack_the_escape_height[100000.0-4]` | PASS |
| 3 | `tests.test_interlock_walls::test_vertical_walls_do_not_hijack_the_escape_height[10000.0-1]` | PASS |
| 4 | `tests.test_interlock_walls::test_vertical_walls_do_not_hijack_the_escape_height[1000.0-4]` | PASS |
| 5 | `tests.test_interlock_walls::test_vertical_walls_do_not_hijack_the_escape_height[0.0-0]` | PASS |
| 6 | `tests.test_invariance_interlock::test_brute_oracle_is_exact_zero_at_rest_and_scales[z0.7-100000.0-1.0]` | PASS |
| 7 | `tests.test_invariance_interlock::test_brute_oracle_is_exact_zero_at_rest_and_scales[z0.7-100000.0-1000.0]` | PASS |
| 8 | `tests.test_invariance_interlock::test_brute_oracle_is_exact_zero_at_rest_and_scales[z0.7-1000.0-0.001]` | PASS |
| 9 | `tests.test_invariance_interlock::test_margin_reference_cases_are_what_they_claim` | PASS |
| 10 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[touch-q4-0.0-0.001]` | PASS |
| 11 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[touch-q4-0.0-1.0]` | PASS |
| 12 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[touch-q4-0.0-1000.0]` | PASS |
| 13 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[touch-q4-1000.0-0.001]` | PASS |
| 14 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[touch-q4-1000.0-1.0]` | PASS |
| 15 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[touch-q4-1000.0-1000.0]` | PASS |
| 16 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[touch-q4-100000.0-0.001]` | PASS |
| 17 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[touch-q4-100000.0-1.0]` | PASS |
| 18 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[touch-q4-100000.0-1000.0]` | PASS |
| 19 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[touch-q6-1000.0-0.001]` | PASS |
| 20 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[touch-q6-1000.0-1000.0]` | PASS |
| 21 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[touch-q6-100000.0-0.001]` | PASS |
| 22 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[touch-q6-100000.0-1.0]` | PASS |
| 23 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[touch-q6-100000.0-1000.0]` | PASS |
| 24 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-I-0.0-0.001]` | PASS |
| 25 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-I-0.0-1.0]` | PASS |
| 26 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-I-0.0-1000.0]` | PASS |
| 27 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-I-1000.0-0.001]` | PASS |
| 28 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-I-1000.0-1.0]` | PASS |
| 29 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-I-1000.0-1000.0]` | PASS |
| 30 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-I-100000.0-1.0]` | PASS |
| 31 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-I-100000.0-1000.0]` | PASS |
| 32 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q4-0.0-0.001]` | PASS |
| 33 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q4-0.0-1.0]` | PASS |
| 34 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q4-0.0-1000.0]` | PASS |
| 35 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q4-1000.0-0.001]` | PASS |
| 36 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q4-1000.0-1.0]` | PASS |
| 37 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q4-1000.0-1000.0]` | PASS |
| 38 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q4-100000.0-0.001]` | PASS |
| 39 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q4-100000.0-1.0]` | PASS |
| 40 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q4-100000.0-1000.0]` | PASS |
| 41 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q6-0.0-0.001]` | PASS |
| 42 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q6-0.0-1.0]` | PASS |
| 43 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q6-0.0-1000.0]` | PASS |
| 44 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q6-1000.0-0.001]` | PASS |
| 45 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q6-1000.0-1.0]` | PASS |
| 46 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q6-1000.0-1000.0]` | PASS |
| 47 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q6-100000.0-0.001]` | PASS |
| 48 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q6-100000.0-1.0]` | PASS |
| 49 | `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-q6-100000.0-1000.0]` | PASS |

## 3. 第五轮剩余三维发现
以下为原 g6e JSON 的 **0 起始数组索引**。E5a/E5a2 已修的项目本单复验，不冒称本单新实现；每条命名门均由最终 JUnit 核对存在且通过。

| 原索引 | 范围/级别 | 处置 |
|---|---|---|
| 6 | `src/eab/kernel3d/frozen.py:57` / major | 冻结EE与facet方向共用精确双侧锥规则；非Dual逃逸高度使用原始Fraction平面比值，Dual保留全部导数通道。 |
| 23 | `src/eab/kernel3d/geom3.py:604` / major | 旧横穿入口已接真实三角面有理符号与extent；不按法向噪声容差择支。 |
| 24 | `src/eab/kernel3d/covers3.py:501` / minor | VV相对内部锥交由精确凸组合/支撑判定，不用1e-12绝对阈值。 |
| 27 | `src/eab/kernel3d/covers3.py:156` / critical | 每侧精确棱弧规则与strict分开，删除对称噪声相加判据。 |
| 28 | `src/eab/kernel3d/g03.py:148` / major | G0票二改完整精确支撑集合，不再有hull厚度/法向噪声尺。 |
| 30 | `src/eab/kernel3d/geom3.py:925` / major | 段段距离精确耦合参数，不用near-parallel两个独立float参数。 |
| 35 | `src/eab/kernel3d/covers3.py:406` / major | EE原数据精确最近线参数与显式extent窗口；不吞near-parallel非零叉积。 |
| 36 | `src/eab/kernel3d/entrance3.py:234` / major | 首入之前取上一个精确事件与t*的有理中点，不再用浮点分辨步长。 |
| 38 | `src/eab/kernel3d/g03.py:441` / major | G0票三完整极点对称差，没有low_e/ambiguous豁免。 |
| 39 | `src/eab/kernel3d/g03.py:275` / minor | facet_vote3默认eps兼容参数忽略，不引用未定义L。 |
| 41 | `src/eab/kernel3d/g03.py:152` / major | 删除浮点支撑带与hull厚度歧义，原roof反例纳门。 |
| 42 | `src/eab/kernel3d/g03.py:82` / major | 不拟合非共面混合支撑，原倒角与五档工程坐标纳门。 |
| 43 | `src/eab/kernel3d/covers3.py:247` / major | 凸组合原点包含采用精确权重，不读浮点重心/绝对阈值。 |
| 47 | `tests/test_entrance3_concave.py:75` / major | merge_degenerate改精确同向/共面；2^-80和1e-12微台阶门杀恢复容差的内部突变，原0.5台阶仍保留。 |
| 49 | `src/eab/kernel3d/g03.py:437` / minor | 删除全部G0模糊宽度，输出ambiguous/dropped/band_skipped固定0并有显式门。 |

原文、逐项门名及最终匹配节点数量见 [第五轮三维发现台账](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/g6e_3d_disposition.json)。

## 4. 测试改写台账与强度审计
基线 738 个测试函数，当前 793 个；原函数无删除、原参数装饰器无改变、新 skip/xfail 引用为零。原节点集合全保留，但这不是单靠数量证明强度：机读台账另外保存每个改动函数旧/新源代码、完整 assert AST、哈希和语义理由。

margin 三文件原 128 条 assert 文本全部仍在（52+44+32）；brute 的两条零断言移动到有理理想输入，原抖动输入另以更强独立精确根检验。首轮集成额外发现 3 个 frozen EE 标签 oracle 域迁移遗漏：旧 oracle 仅枚举源环边，而默认 margin 已能选折面真实对角边。没有改生产来选择错误源边；原 32 条 assert 与 6 工程坐标格全保留到显式旧窗口，同一原输入另外核对独立耳切的完整标签/strict 集合、精确表面最小距离及冻结符号。旧 float 逐顶点加法安全断言不谎称与精确仿射运动等价：一般输入核对权威精确根/端点，并在新增恰可表示根保留原浮点端点安全门。旧源码字符串“向上修补”突变随实现删除，改为省掉当前根精确核验的内部突变。

| 文件 | 改写函数/辅助函数 | 处理 |
|---|---|---|
| `tests/test_e5a2_interlock_bridge.py` | `test_returned_lift_is_safe_for_actual_float_translation_against_independent_profile` | Independent profile oracle compares exact roots. Actual nonpenetration checked on authoritative exact affine endpoint; additional representable roots preserve old floating-endpoint safety. |
| `tests/test_e5a2_interlock_bridge.py` | `test_disabling_upward_construction_is_caught_by_the_original_profile_error` | Independent profile oracle compares exact roots. Actual nonpenetration checked on authoritative exact affine endpoint; additional representable roots preserve old floating-endpoint safety. |
| `tests/test_entrance3.py` | `test_ray_that_misses_gives_none_and_t_max_is_honoured` | t_max is now exact: raw root beyond 0.3 must be none; old entrance assertion retained on exactly representable boundary data. |
| `tests/test_entrance3_concave.py` | `test_degenerate_merge_keeps_parallel_planes_at_different_heights_apart` | Plane family requires exact coplanarity; micro-step regression and tolerance mutant replace an ineffective coarse-step tooth without dropping old input. |
| `tests/test_frozen_ee_sign.py` | `test_near_parallel_crossing_edges_stay_in_extent_in_engineering_coordinates` | All original 32 assertion strings and six engineering-coordinate cells retained in explicit legacy window; same raw cells additionally check default full triangulated cover labels/strictness, independent exact surface distance and frozen sign. Independent test-only ear clipping shares no production primitive. |
| `tests/test_geom3_face_polygon.py` | `test_all_five_call_sites_route_through_the_single_helper` | All old call-site assertions retained. Face-interior rejection injected into the live integer boundary/ray halfspace path as well as the still-live triangle_locate segment path; no result records fabricated. |
| `tests/test_interlock_sensitivity.py` | `_steep_check` | All 72 steep cells and legacy assertions retained; added independently certified in-band branch obligation. Same internal vertical-window mutant now hits missing-branch assertion. |
| `tests/test_interlock_sensitivity.py` | `test_steep_gate_has_teeth_vertical_tie_window` | All 72 steep cells and legacy assertions retained; added independently certified in-band branch obligation. Same internal vertical-window mutant now hits missing-branch assertion. |
| `tests/test_interlock_walls.py` | `_key` | All 4 x 20 raw cells kept and checked against independent earliest-root oracle; original nominal 0.2 and frozen assertions retained in explicit window. Added clearance and ideal grids. |
| `tests/test_interlock_walls.py` | `test_vertical_walls_do_not_hijack_the_escape_height` | All 4 x 20 raw cells kept and checked against independent earliest-root oracle; original nominal 0.2 and frozen assertions retained in explicit window. Added clearance and ideal grids. |
| `tests/test_invariance_geom.py` | `test_identity_cell_matches_closed_form` | Original full grid and assertion strings retained in caller-explicit legacy contact window; same raw inputs additionally checked against independent exact triangulated surface labels/distance/state. See margin integration migration ledger. |
| `tests/test_invariance_geom.py` | `test_body_distance_scales_and_keeps_its_label` | Original full grid and assertion strings retained in caller-explicit legacy contact window; same raw inputs additionally checked against independent exact triangulated surface labels/distance/state. See margin integration migration ledger. |
| `tests/test_invariance_geom.py` | `test_margin_layer_is_invariant` | Original full grid and assertion strings retained in caller-explicit legacy contact window; same raw inputs additionally checked against independent exact triangulated surface labels/distance/state. See margin integration migration ledger. |
| `tests/test_invariance_interlock.py` | `test_brute_oracle_is_exact_zero_at_rest_and_scales` | Same original grids; legacy assertions retained in explicit contact/boundary windows; independent exact oracle added for raw input. Brute zero cells use independent swept SAT, ideal rational cells retain exact zero. |
| `tests/test_kernel3d_geom.py` | `test_entrance_block_of_rotated_box_pair_is_a_clean_box` | Entrance-block hull assertions use original coordinates rationalised BEFORE differences. Escape uses independent exact swept-SAT root and exact affine endpoint; float display checked to one upward ulp. Same parameter grids and ideal-contact assertions. |
| `tests/test_kernel3d_geom.py` | `test_face_touching_stack_is_touching_under_rigid_motion` | Entrance-block hull assertions use original coordinates rationalised BEFORE differences. Escape uses independent exact swept-SAT root and exact affine endpoint; float display checked to one upward ulp. Same parameter grids and ideal-contact assertions. |
| `tests/test_margin_penetration.py` | `_check_monotone_contact_resolution` | Default exact penetration and explicit contact-window modes have separate strong assertions and internal mutants; no tolerance loosening. |
| `tests/test_margin_penetration.py` | `test_contact_resolution_gate_has_teeth` | Default exact penetration and explicit contact-window modes have separate strong assertions and internal mutants; no tolerance loosening. |
| `tests/test_margin_resolution.py` | `test_a_tiny_block_near_a_huge_block_is_judged_the_same_in_every_orientation` | Legacy resolution expectations require explicit contact_window; exact raw-input checks added. Same parameter grid. |
| `tests/test_near_parallel_edges.py` | `exact_seg_seg` | Original near-parallel grids and old contact-zero assertion kept under explicit legacy window; default raw geometry additionally checked against independent exact surface-distance and label oracle. |
| `tests/test_near_parallel_edges.py` | `test_near_parallel_ridge_edges_match_the_exact_rational_distance` | Original near-parallel grids and old contact-zero assertion kept under explicit legacy window; default raw geometry additionally checked against independent exact surface-distance and label oracle. |

[逐函数完整机读台账](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/test_rewrites.json) · [函数/网格/跳过审计](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/test_inventory_audit.json) · [原断言保留](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/margin/assertion_retention.json) · [追加两文件55条原断言保留](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/margin/integration_assertion_retention.json) · [互锁原格说明](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/interlock/test_rewrites.json) · [首入冻结台账](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/entrance/test_ledger.json) · [路由门52条原断言保留](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/face_routing_retention.json)

## 5. 突变表
所有列出的牙都修改被测内部路径，不在产出之后拼假数据；检查的是对应几何/根/区间/符号断言，而不是碰巧的标签排列。早期两个 entrance 外部突变曾临时改文件并还原，只有恢复后冻结源码的全套计入交付；其余为内存编译/monkeypatch。新增完整全套运行不与突变进程并发。

| 组件 | 内部突变 | 报红原因/目标断言 | 结果 |
|---|---|---|---|
| interlock | omit near-vertical exact surface events | `exact surface event set did not contain a separating height` | KILLED |
| interlock | omit returned-root exact nonpenetration certificate | `exact earliest root including near-vertical events` | KILLED |
| interlock | omit first previous candidate interval proof | `missing earlier candidate interval proof` | KILLED |
| interlock | steep nominal vertical tie-window internal mutation | `(2e-10, (-0.5068809109773141, -0.5068809109773141), '带内漏支')` | KILLED |
| margin | margin_ignores_window | `test_margin_window_and_default_guards_have_internal_mutation_teeth -> explicit-window state assertion` | KILLED |
| margin | margin_default_uses_ctol | `test_margin_window_and_default_guards_have_internal_mutation_teeth -> default-exact state assertion` | KILLED |
| margin | margin_no_clamp | `test_contact_resolution_gate_has_teeth -> separated-report-band assertion` | KILLED |
| margin | margin_swallow_exact_penetration | `test_contact_resolution_gate_has_teeth -> exact-penetration sentinel assertion` | KILLED |
| margin | margin_default_surface_ignored | `test_margin_layer_is_invariant[box_box_face-R7-t0-s0.001] -> default-exact surface nearest label` | KILLED |
| entrance/frozen | predecessor_float | `Exact first entry must return at 1e20; float t minus sub-ulp step throws false missing-earlier exception.` | KILLED |
| entrance/frozen | coplane_tolerance | `sorted((family kind, member count)) == [('FF',2),('FF',2)]` | KILLED |
| entrance/frozen | predecessor_float_midpoint | `lower < probe < upper` | KILLED |
| entrance/frozen | omit_diagonal_topology | `diagonal EE frozen signed distance` | KILLED |
| entrance/frozen | omit_folded_surface_expansion | `complete exact-surface cover set` | KILLED |
| exact_geom | plane distance bound > changed to >= | `closed boundary equality must not be rejected` | KILLED |
| geom3 | cache signature drops vertex content | `vertex-content invalidation` | KILLED |

[合并机读突变表](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/mutation_table.json)；各组件 JSON 保留具体注入、日志和原断言。三个首入外部突变另以最终源码重新在隔离命名空间运行，见 [最终源码突变复验](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/entrance/final_mutants.json)。额外布尔三角相交闭端点/同侧、整数 parity 边界、冻结对角拓扑突变也在最终全套中执行。

## 6. 等价优化与性能
部署优化：精确布尔三角交取代交点集合构造；精确横截严格内点正证书（失败保留完整 arrangement）；可认证星核四面体并集整数 SAT；清分母整数射线 parity；按完整内容与可注入实现键的事件/margin 缓存；正窗口三角距离先以精确支撑平面下界拒绝（严格 >，等号保留）。没有容差回退、减网格或删除原语义门。布尔路径 1300 对旧值对拍，另有独立重心可行性；整数射线与旧 Fraction 对拍并对独立 L 型集合判定；星核与独立 SAT 及关闭快路对拍；缓存逐值禁用对拍。

| 测量 | 结果 | 解释 |
|---|---|---|
| E5a2 基线全套 | 7953 passed, 49 failed；1578.67 s | 红基线，8002 节点 |
| E5b 冻结全套 | 8267 passed in 1479.80s (0:24:39) | 8267 节点，原网格全留且加门 |
| E5b 独占进程墙钟 | 1498.40 s | ≤900 s 目标：未达成 |
| margin 最终完整子组 | 641 passed, 50 deselected；92.85 s | 仅开发子组，不能替代全套 |
| 互锁墙 + 完整 sensitivity | 53 passed；161.58 s | 每节点内部仍执行完整原 seed 网格 |
| 最后两文件迁移完整复验 | 2454 passed；185.27 s | 原网格、原55条断言保留，151个集成红闭合 |
基线是红的，且本单新增门，不能把两个全套耗时差当成同一工作量的微基准加速比。详细热点来自最终 JUnit，微基准有 before/after 输出逐值相等断言。

[性能汇总](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/performance_summary.json) · [最终按文件耗时](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/performance_by_file.json) · [独立微基准原始记录](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/optimization_benchmarks.json) · [平面下界逐值性能对拍](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/interlock/profile_plane_bound.json)

## 7. 文档、复跑与回滚锚点
README、canon_map、exact_predicates_plan、exact_3d_design 已标明当前契约与历史 E5a2 红状态的区别。`tools/fix_canon_ptrs.py --apply` 已执行，19 处指针更新，再执行为 0 处待改。仅写已验证范围，不宣称任意凹体全局 E 或完整折面法锥。

```powershell
$env:PYTHONDONTWRITEBYTECODE="1"
python -X utf8 reports/codex/E5b_evidence/verify_run.py run rerun -- -m pytest -q -p no:cacheprovider --basetemp=reports/codex/E5b_evidence/tmp/rerun --junitxml=reports/codex/E5b_evidence/rerun.xml --durations=30 --tb=short
python -X utf8 tools/fix_canon_ptrs.py --apply
python -X utf8 reports/codex/E5b_evidence/verify_run.py inventory
python -X utf8 reports/codex/E5b_evidence/audit_delivery.py
```
回滚锚点为只读 HEAD 3566708 和本树 byte-exact baseline 源码快照/manifest；本单未执行任何回滚 git 命令。基线本身是 49 红，不把它说成“上一个全绿版”。已实现子集留在经全套验证的实现，未以回退功能换绿。没有已验证且同时满足新默认精确语义、旧窗口全部原门的历史绿色窗口实现可直接回退；未执行该未完成项的绿色回退，不能声称这条回退要求也已满足。

## 8. 独立交叉检查与遗留边界
同组异作者检查了 root 几何优化与缓存；新增 64 三角对、249 点包含、32 折面星核对、96 横截、4 轮缓存操作未发现未闭合 critical/major；发现的缓存文案过度承诺已修复。margin 对 interlock 审查确认公开 certificate 仅包含 winner，这一限制已写明。此范围和人数不满足六路独立 G6，不能冒称通过正式审查。

[几何/缓存交叉审查](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/entrance/review_root.md) · [互锁交叉审查](file:///D:/eab-wt/cx-e2/reports/codex/E5b_evidence/margin/review_interlock.md)

- 有效闭合外向嵌入表面是输入前提；自交、非流形、非法面环不在证明域。
- **未完成项：显式窗口完整贯入深度契约。** 当前是六轴刚性脱离充分证书 OR 局部径向薄壳政策，不是完整欧氏深度/偏置；未给任意旋转下该有限政策等价的保证。局部壳可接纳整块最短脱离较大的夹持，六轴搜索也可能漏掉较短的斜向脱离，不能把二者合称刚性深度上界。默认严格几何不采用此政策。需所有者明确批准局部报告政策，或继续实现所指定深度的必要充分算法；没有用聊天未回复视为批准。
- exact root 与逐顶点重新舍入的 float 平移是不同输入；适配器不能混淆。
- 凹体全局 E 构造、完整一般折面法锥、姊妹线部署/工程验证与正式 G6 均未新增声称。

- **未完成项：≤900 s 总耗时目标。** 保留已逐值验证的等价优化与绿色功能，未为过时限削弱测试；性能目标不以回滚到 49 红的基线解决。

## 全套最后一行（原样）

```text
8267 passed in 1479.80s (0:24:39)
```
独占进程墙钟：1498.403447 秒。

E5b_PARTIAL：显式窗口完整贯入深度契约未完成；全套独占墙钟耗时仍超过 900 秒目标
