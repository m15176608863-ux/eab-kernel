# R7FIX · 3D 构造与裕度分报告

## 范围、证据及当前状态

- 分工：G6G-04、05、06、08；同时扫描同类三维构造、距离特征完备性与尺度问题。只写本工作树，无 Git 写操作，无姊妹仓库写入。
- 回滚锚：上级保存的 `../baseline_tracked.zip`；本组没有提交。
- 原始新增 21 格先在修改实现前跑：`18 failed, 3 passed in 0.43s`，完整断言/输出见 [before_red.log](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/before_red.log)。其中每个负责的 G6G 编号均有目标断言红，不是导入/环境失败。
- 最终定向组包含 37 个新增格与原 margin exact/resolution 全部格：`117 passed in 8.85s`，见 [final_targeted.log](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/final_targeted.log)。未删旧测试、未加 skip/xfail、未缩参数网格。
- [新回归门](file:///D:/eab-wt/cx-e2/tests/test_r7fix_geom3.py)、[内部变异 JSON](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/mutations.json)、[逐断言变异输出](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/mutations.log)、[可复跑变异脚本](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/run_mutations.py)。最终全套、用时与全套最后一行由上级报告统一填写；本分报告不冒充里程碑独立 G6 退出审查。

## 逐条处置

### G6G-04 · 折面内部棱遗漏

- 修前：独立 slab 下界与两条手工屋脊中点上界均为 2，源四边面返回 `2.449489742783178`。门名 `test_g6g04_folded_internal_ridges_attain_slab_distance`；断言 `folded-ridge-slab-distance`。追加有理 3-4-5 旋转、非零平移、单位尺度变化三个格，并对源环/显式相同三角表面两种表示等值。
- 根因：顶点—三角面距离完备，但 EE 只枚举原始面环边界，非共面环在三角化后产生的真实内部折棱未纳入。
- 修法：`_surface_distance_edges` 用实际折面三角曲面的全部几何棱。平面面的辅助三角对角线不改变几何表面，不额外扩入；折面棱完整保留。A/B 棱列表只构造一次。
- 变异：在真正 `brute_feature_distance` 内把 A 侧 `_surface_distance_edges(A)` 改回 `A.edges()`；同一目标断言重新报红，不在产出之后添加假数据。

### G6G-05 · 最终缩放前双重舍入

- 修前：面积 `29U/20`（U = 2^-1074）应显示 U，实际 2U；精确 U/2 的面积悄悄显示 0。facet/support 有符号间隙 ±(51/20)U/√3 应显示 ±U，实际 ±2U。
- 门：`test_g6g05_face_area_rounds_after_final_halving`、`test_g6g05_face_area_underflow_is_not_silent_zero`、`test_g6g05_facet_gap_rounds_after_normal_length_division`；覆盖舍入中点两侧、负号、两种公开间隙入口。
- 修法：面积先形成有理 `n²/4`，间隙先形成有理 `numerator²/n²`，最后统一正确舍入开根并保留符号。不再先 hypot/float 再除 2 或除法向长度。非零而无法显示的无证书标量响亮拒绝。
- 变异：face_area 内恢复“先开根再除 2”，目标 `area-final-rounding` 红；facet_gap3 内先 float(numerator)，目标 `signed-gap-final-rounding` 红。

### G6G-06 · 全局显示点反减污染法向

- 修前：gap=1e-9、T=1e8 的两个精确屋脊中点在浮点显示中重合，返回 normal=None；有理旋转后法向错误约 0.107。距离和 exact_distance_squared 本来正确。
- 修法：in_extent 盖使用由原始精确坐标构造的盖单位法向及 `exact_gap_sign` 定 B→A 方向，覆盖 VF/FV/EE/VE3/EV3/VV3，而不反减显示点。显示点距离仍保留作原有坏见证自校验，旧有污染见证门不因此失去牙齿。折面见证修复移除 `4*rounding` 豁免，不以小构造误差豁免错误方向。
- 追加同根修复：单位向量的每个分量均对 `component²/norm²` 最终开根；`_qunit` 与 `inflated_normal` 不再预先 float 缩放分量。`Cover3.exact_normal_direction` 携带未归一化有理方向，`MarginContact` 传播真实 B→A 的有理方向证书。盖内允许最终显示分量下溢仅因伴随该证书；公开无证书 `unit/facet_normal3` 默认响亮拒绝。分类仍读取原有精确坐标/平方距离，不使用显示法向。
- 门：`test_g6g06_margin_normal_does_not_subtract_display_points` 含平移、旋转、交换 A/B；新增下溢方向证书门断言非零精确分量仍在，删除证书的内部变异会红。
- 变异：在 `cover_witness` 内移除精确源法向分支，恢复显示点方向；目标 `exact-local-margin-normal` 红。

### G6G-08 · 浮点三重积中间量失真

- 修前：薄长盒真实 8*s*s*h 的体积返回其 2/3；原点对称盒体心非零；同一个平面四面体仅循环重排一个面环，体积从 0 变为正确正数，体心也错。
- 门：`test_g6g08_mass_properties_use_exact_products_before_final_rounding`（尺度 ±600）、`test_g6g08_centroid_retains_cancellation_even_when_volume_is_representable`、`test_g6g08_volume_independent_of_cyclic_face_ring_start`（三个循环起点）。主 oracle 是区间乘积积分与单纯形积分，不使用生产几何原语。
- 修法：实际三角曲面相对首点的三重积、体积和一阶矩全部有理求和；只有最终 volume/centroid 坐标转 binary64。体心不依赖已舍入的 volume。内容键缓存精确质量数据；原面和顶点修改会改变缓存键。无法显示的非零体积拒绝，不妨碍可以正确表示的体心。
- 变异：在 `_mass_properties` 内把相对向量提前转 float，再走实际三重积路径；目标 `axis-product-volume` 红。
- 保持诊断接口：非法零面积面在精确三角化时应报告问题；`manifold_issues` 捕获这一 ValueError 并返回 issue，而不是崩出调用方。原重复边门保持不变并已绿。

## 同类扫描与额外修复

|区域|结论 / 改动|证据|
|---|---|---|
|brute 距离特征完备性|还漏“棱穿过另一面内部”。两片手工三角形在 (0,0,0) 相交，旧函数却返 1/3；补精确 triangle intersection，逐三角 AABB 剪枝。|[额外修前红](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/scan_crossing_red.log)；`test_r7fix_brute_surface_distance_includes_edge_face_crossings` 及真实内部删交点变异。|
|Newell normal|旧 cross 的一个分量可能先下溢，另两分量非零使原 fallback 不触发。改精确 Newell 后最终分量归一。|`test_r7fix_face_normal_does_not_discard_one_underflowed_cross_component`。|
|unit / cover normal / inflated normal|先舍入缩放分量仍会把最终可表达分量从 2U 变成 U；统一最终有理分量平方根。|`test_r7fix_unit_retains_extreme_components_before_normalization`、`test_r7fix_inflated_normal_retains_extreme_final_component`。|
|angle_between|s=2^-600 的两个正交向量，叉积先下溢导致返回 0 而不是 π/2；改精确 cross/dot 后共同缩放再 atan2。|[额外修前红](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/scan_angle_red.log)；尺度 ±600 门。|
|metrics / edge directions / characteristic_length|原始有限坐标先相减可上溢或混合 Fraction 提前损失。关键尺度、棱方向、二面角棱向量改从精确原始差构造；无法表达的 L 抛错，不能静默创建 inf 验收尺度。|`test_r7fix_metrics_cannot_create_infinite_acceptance_scale_from_finite_coordinates`；原尺度门由总全套覆盖。|
|其余平方根构造|检查 covers3 的 VF/FV/EE/VE/EV/VV：它们的精确 gap/area 证书与最终 sqrt 路径已经存在，不重复引入第二套几何判据。|此次保留，只补方向证书。|
|三维 G0 距离审核|扫描发现 g03 尚反减显示点、非有限值防护不足，已交上级修复，与本组不重叠编辑。|上级 G03 分证据。|

## brute_feature_distance 调用门与信任界线复核

生产调用只有 margin._resolve 的分离侧构造自校验；exact default 的几何关系、平方距离分支不是由 brute 的浮点输出决定。brute 与生产共用 exact_geom 投影/距离原语，因此只能算内部佐证，不得称独立 G0 主 oracle。独立 G0 仍为 `g03_surface_oracle`；本轮新增折面主门用手工 slab 与中点双界。

逐文件引用清单：`test_frozen_lowdim.py`、`test_interlocking.py`、`test_geom3_face_polygon.py`、`test_invariance_geom.py`、`test_invariance_interlock.py`、`test_margin.py`、`test_near_parallel_edges.py`、`test_margin_resolution.py`、`test_r6fix_geom3.py`、`test_vv3_discard.py`。`test_covers3_strict_lowdim.py` 仅在文档明确“不调用 brute”；不是漏跑引用。

- 第一批引用及 margin 相关组原跑 `340 passed / 2 failed`（[保留失败记录](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/related_a.log)），两红分别是非法面诊断接口和低于 binary64 的合法精确间隙，这两条均已正确修复；最终 117 格明确包含两条旧门并全绿。
- 三个大组 `test_interlocking.py test_invariance_geom.py test_invariance_interlock.py` 已实跑至 38% 无红；为避免与上级正式全套争抢 CPU，按上级指令精确停止了自身 PID 14292。此中断记录 [oracle_recheck.log](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/oracle_recheck.log) 不算通过证据；完整结果必须以最终全套为准。
- 历史测试中把 brute 文档称为“独立”的地方不成为本次证据升级；此处明确其共享原语界线。无外部求解器或新工程验证结论。

## 测试改写台账 / 遗留

- 首次定向交付时本组未改既有测试；总全套随后暴露两处旧测试与构造改进的接口/前提冲突，获上级批准后作下节所列增强改写。未靠放宽容差解决失败。
- margin 的六轴证书中文模块说明及两个 API docstring 同步 G6G-09：只给内部不交下确界 rho，不保证闭集完全分离 PD_closed。
- 组内四项已修与变异验证完毕。全套状态、总耗时、G6 退出权限、其余七项及最终工单标记由上级汇总；本报告不先声称全套通过。

## 总全套发现的集成问题及增强改写台账

完整失败堆栈保留在 [full_fail_diagnosis.log](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/full_fail_diagnosis.log)：10 failed，分别为 9 个同一 dataclass reference 接口格和 1 个旧单位化舍入偶合前提。不是缺陷遗漏不记账，也不将失败掩盖为通过。

1. `test_e5a2_integer_arithmetic.py::_eager_ee`：旧独立 eager 算法已正确算出原始有理 `candidate`，但没有填本轮新增的 `exact_normal_direction`，所以其余 14 字段相等而新字段与 None 不等。将该独立候选填入新字段；原全部参数网格、完整 dataclass 相等断言、参数/范围/距离等所有比较均保留；另显式断言方向证书相等且非零。没有将生产字段设 compare=False，也没有把 expected 从生产 output 抄回。

2. `test_interlock_e5a.py::test_normal_noise_handles_exact_cross_hidden_by_unit_vector_rounding`：旧门首句要求两个真有不同方向的边经单位化后“恰好舍入成相同向量”；本轮正确最终单位分量舍入消除了这个偶合，所以该前提不再成立。不能退回错误单位化以让它变绿。保留原全部坐标、独立有理 sine² oracle、原 expected、finite/>1 判据以及 `rel_tol=2e-15`；移除偶合前提后原生产 `_normal_noise` 真实返回 1200.0488306054758，而期望 5632.716247687068，目标 `exact-edge-noise` 红，见 [noise_strengthened_red.log](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/noise_strengthened_red.log)。根因与本轮扫描相同：不仅“舍入 cross = 0”，非零的舍入 cross 也可能严重失真。生产因此始终从原始精确边构造 `cross²/(lengthA²*lengthB²)` 后最终开根。

   旧“显示方向折合”场景不删除：在同一门内额外 monkeypatch 生产 `Polyhedron.edge_dir`，强制两个显示方向完全相同；保留 `norm(cross(...)) == 0` 断言，并断言噪声仍等于原独立 expected 且与未污染结果完全相同。新增 `test_normal_noise_rejects_nonzero_rounded_cross_fast_path`，在真正 `_normal_noise` 内恢复非零舍入 cross 快路，必须由 `exact-edge-noise` 目标断言报红。参数网格未缩、误差阈值未放宽。

集成修后重新跑两整个旧测试文件及 37 个本轮新格，最后一行：`64 passed in 1.41s`，见 [full_fail_repair_green.log](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/full_fail_repair_green.log)。新增生产改动仅 `src/eab/kernel3d/interlock.py::_normal_noise`；已通知上级重跑 canon 指针工具，并再次冻结代码等待总全套。

## 后续完整全套揭示的折面测试 oracle 口径不一致

上级保留的一次完整全套结果为 `18 failed, 9829 passed in 445.65s (0:07:25)`；其中本组负责 16 个 `test_margin_labels_are_identical_under_rigid_motion` 距离格。不能把这些红直接当作“只是误差”而放宽门。排查先于改动完成，证据在 [folded_oracle_diagnosis.json](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/folded_oracle_diagnosis.json)、[逐格记录](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/folded_oracle_diagnosis.log)、[诊断脚本](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/diagnose_folded_oracle.py)。

- 16 个格对应 29 个 VF/FV 标签；集合和数量原来就正确，所有受影响源四边面按输入浮点精确值均非共面。
- 用仅测试所有的耳切及 Fraction 点—三角距离，120 位 Decimal 最终开根，29 个生产结果与独立曲面真值全部逐 float 相等，`actual_ulps=0`。旧 expected 与真值最多偏 133,435,224 ulp。独立复核代理另用自行写的 Fraction Gram 解及线段端点约束重算，不借本组或生产 helper，也确认 16 格 29 标签均为 0 ulp。
- 例如 `sep_vf-q4-1000.0-0.001` 的 `VF(v0,f3)`：旧 Newell 显示点反减为 0.00044199999997935105，独立曲面距离和生产均为 0.00044200000000164843。修 G6G-06 时不再以 `4*rounding` 豁免真实折面见证，而旧 `e5a_cover_oracle.margin_selection` 仍量第一顶点锚定的 Newell 描述符平面，故它是这批失败的根因。

获上级批准后**只改测试所有 oracle**：`tests/e5a_cover_oracle.py` 新 `_margin_witness_distance` 对非共面 VF/FV 使用独立耳切后的真实三角面最小距离；其原 `witness_distance` 仍保留 Newell 源面描述符语义，供局部盖接口门使用；其他 kind 和平面面报告不变。不导入生产几何原语，不复制生产输出形成 expected。

增强而非放宽：新增 [test_r7fix_margin_oracle.py](file:///D:/eab-wt/cx-e2/tests/test_r7fix_margin_oracle.py)，三个平移/尺度格仅依赖手工屋脊中点上界和 slab 下界（真距离 2s），修前 3 failed（[红记录](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/folded_margin_oracle_red.log)），修后绿；在 oracle 内恢复 Newell 分支的真实变异由 `folded-margin-oracle-inclusion` 断言捕获。原 `test_invariance_interlock.py` 文件**未改**，4 ulp、完整标签集合、数量、裁决和全部 162 格网格一字不动。全参数化加四个新 oracle 格重跑最后一行：`166 passed in 29.51s`（[绿记录](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/folded_margin_oracle_green.log)）。生产代码没有因这 16 格作任何更改；最终全套仍由上级统一重跑。
