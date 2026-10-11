# WO-E3E4：二维收尾精确化与极限分析有理数自校验

执行日期：2026-10-12；工作树：`D:\eab-wt\cx-e2`；分支：`codex-work`；基线及交付 HEAD：`e1fbbd4`。未提交。

## 1. 结论与验收边界

- 本单负责的 14 条第五轮发现全部逐条处置：5 条已由后续提交消解，9 条在本单修复或加强（含测试盲区）；不把旧审查对象 `b6126cf` 的全部 50 条发现都宣称关闭。机读表：[g6e_dispositions.json](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/g6e_dispositions.json)。
- E3 默认数学判定用给定浮点数的精确有理值；显式 legacy 域窗口只放宽。E4 静力、对偶、互补及机构容许性在同一精确模型上核验；可分辨性只报告，不再篡改原问题状态或承载因子。
- 10 项一次性真实源码突变：9 项被语义门抓住（D1/D2 是有效输入不应出现的拒答异常，其余为目标断言）；D9 被精确互补冗余保护，单独放宽间隙不改变最终拒绝。所有项均恢复原字节 SHA-256。详见第 5 节。
- 全套原样末行：`7729 passed in 734.49s (0:12:14)`；进程墙钟 **735.901 s**；运行期间 src/tests 哈希不变。[完整日志](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/final_full.log) / [命令、耗时与源码哈希](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/final_full_result.json)。
- 用户禁止新建 worktree/clone，故仅当前树验证，不能声称满足纪律 D 的新鲜树验收；三路协作和只读交叉检查也不等于六路独立 G6。本单 DONE 不等于里程碑/G6 退出。

## 2. 第五轮 14 条处置表

行号均为原始发现的键，不是新源码行号。baseline 证据指本单开始的 `e1fbbd4`；current 指本工作树。没有按 `verdicts_raw` 的不可靠顺序配对。

| 原发现键 | 处置 | 当前基线复现与处理依据 | 修前红门 / 修后门 |
|---|---|---|---|
| src/eab/kernel2d/covers.py:117 | 已由 e1fbbd4 消解 | 当前 HEAD 精确拒收微凹凸路径；一般成员两深度均判 1。链法向代码已删除。 [基线输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/covers_baseline_reproduction.json) [当前输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/covers_final_reproduction.json) | 已消解项不重复制造缺陷；原复现如表 |
| src/eab/kernel2d/covers.py:238 | 本单修复 | HEAD 正常 probe strict=False，但源码内部 du×100 变 strict=True 并多枚举 VV；E3 删除 du 噪声活跃判据，用独立邻点支持与线性消元 oracle 看护全网格。 [基线输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/covers_baseline_reproduction.json) [当前输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/covers_final_reproduction.json) | reports/codex/E3E4_evidence/covers_red_before.txt  tests/test_kernel2d_covers_e3.py::test_vv_active_exact_support_not_a_roundoff_band |
| src/eab/kernel2d/covers.py:360 | 已由 e1fbbd4 消解 | 当前 HEAD 四种短边均合法构造 7 个 E 顶点；旧转角窗/折回噪声代码已删除。 [基线输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/covers_baseline_reproduction.json) [当前输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/covers_final_reproduction.json) | 已消解项不重复制造缺陷；原复现如表 |
| src/eab/kernel2d/covers.py:453 | 已由 e1fbbd4 消解 | 6 格双向 G0 全真；局部严格与全局合并均用 exact，不再存在两把尺。 [基线输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/covers_baseline_reproduction.json) [当前输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/covers_final_reproduction.json) | 已消解项不重复制造缺陷；原复现如表 |
| src/eab/kernel2d/covers.py:501 | 已由 e1fbbd4 消解 | 倒角反例 membership=1，2000 探针 G0 全通过；facet 使用自身法向。 [基线输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/covers_baseline_reproduction.json) [当前输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/covers_final_reproduction.json) | 已消解项不重复制造缺陷；原复现如表 |
| src/eab/kernel2d/geom.py:434 | 本单修复 | HEAD 仍缺失真实极点 (1e-15,-1e-3)；新 exact hull 保留，全部输入在各支持线同侧。 [基线输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/covers_baseline_reproduction.json) [当前输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/covers_final_reproduction.json) | reports/codex/E3E4_evidence/covers_red_before.txt  tests/test_kernel2d_covers_e3.py::test_convex_hull_keeps_true_extreme_point_not_transitive_tolerance_pop |
| src/eab/limit.py:206 | 已由 aadc40e 消解 | 原复现的近平行 tangent 在当前 HEAD 已抛 ValueError；原不安全静默值不可复现。本单不改变该筛查。 [基线输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/baseline_limit_206.txt) [当前输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/current_206_limit.txt) | tests/test_limit_scale.py |
| src/eab/limit.py:729 | 本单修复 | 无荷载远接触不能放大静力容差：有理数残差逐分量必须为零。 [基线输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/baseline_limit_729.txt) [当前输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/current_729_limit.txt) | reports/codex/E3E4_evidence/limit_new_gates_baseline.txt assert not L.check_duality(r,cs,dead,live,dim=2)["static_ok"] tests/test_limit_exact_selfcheck.py::test_single_unloaded_far_contact_cannot_hide_a_pure_couple_residual |
| src/eab/limit.py:732 | 本单修复 | μ=1e-5、cA/W=1e-5及细高体使用同一精确自检，不再用总恒载尺度决定答案；k=3,5,9,15,30,100。 [基线输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/baseline_limit_732.txt) [当前输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/current_732_limit.txt) | reports/codex/E3E4_evidence/limit_new_gates_baseline.txt assert not d["static_ok"] tests/test_limit_exact_selfcheck.py::test_exact_single_static_and_gap_reject_arbitrary_rational_alpha_error |
| src/eab/limit_multi.py:147 | 本单修复 | _pair_powers 改为逐列有理数相对功率，删除全局 vmax 放宽。 [基线输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/baseline_limit_multi_147.txt) [当前输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/current_147_limit_multi.txt) | reports/codex/E3E4_evidence/limit_new_gates_baseline.txt assert not M.mechanism_is_admissible_multi(ms,[BC(slow,0),BC(fast,1)],dim=2) tests/test_limit_exact_selfcheck.py::test_exact_admissibility_has_no_tall_body_or_other_body_speed_tolerance |
| src/eab/limit_multi.py:177 | 本单修复 | 分辨性在各体自身接触形心与臂长，仍保留该体调用方构造力矩的原点距离噪声，不计其他体；分辨性仅报告、不改原状态。 [基线输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/baseline_limit_multi_177.txt) [当前输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/current_177_limit_multi.txt) | reports/codex/E3E4_evidence/limit_new_gates_baseline.txt assert both.uncertainty == pytest.approx(alone.uncertainty,rel=1e-12) tests/test_limit_exact_selfcheck.py::test_multi_resolvability_uses_only_each_bodys_local_frame |
| src/eab/limit_multi.py:348 | 本单修复 | 精确强对偶和每项互补，重的无关体不能掩盖静力可行但次优的插值；1e-100仍拒绝。 [基线输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/baseline_limit_multi_348.txt) [当前输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/current_348_limit_multi.txt) | reports/codex/E3E4_evidence/baseline_limit_multi_348_assertion.txt assert not d["ok"], (WD, rr.alpha, d["static_residual_rel"], d["duality_gap_rel"]) tests/test_limit_exact_selfcheck.py::test_multi_exact_duality_rejects_statically_feasible_suboptimal_interpolation |
| tests/test_limit_multi.py:238 | 本单加强 | 原1e-3牙扩成精确10^-k（k=3,9,30,100），原4个跨度格全部保留；同时核精确静力残差非零，不依赖相对显示量。 [基线输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/baseline_test_limit_multi_238.txt) [当前输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/current_test_limit_multi_238.txt) | reports/codex/E3E4_evidence/baseline_test_limit_multi_238_assertion.txt assert not admissible and not ok,(k,admissible,ok) tests/test_limit_multi.py::test_a_far_body_does_not_loosen_the_self_check |
| tests/test_limit_multi.py:268 | 本单加强 | 基线关闭unbounded筛查后53门仍绿已复现；新门覆盖两邻域分支×loaded_body 0/1，关闭后4条报告断言红；optimal三区间增加loaded_body 1。 [基线输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/baseline_test_limit_multi_268.txt) [当前输出](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/current_test_limit_multi_268_mutant.txt) | reports/codex/E3E4_evidence/current_test_limit_multi_268_mutant.txt assert r.resolvability == "nearby_infeasible" / "unresolved"; disabling the production unbounded screen gives resolved tests/test_limit_exact_selfcheck.py::test_multi_unbounded_screen_covers_both_rejection_branches_and_nonzero_body |

关键语义红断言：geom:434 是真极点必须在凸包；covers:238 是 `strict == 独立邻点支持真值`，不是盖后追加假标签；limit:729/732 是 `not static_ok`；multi:147 是贯入机构不可容许；multi:177 是加入无关远体后 uncertainty 必须与孤立体相同；multi:348 是精确静力可行的次优插值仍 `not ok`；测试238是非零有理残差与微小贯入必须拒绝；测试268关闭无界筛查时，四条 `resolvability` 报告断言确实红。

## 3. E3 / E4 实现摘要与精确性口径

### E3

- 凹首入的初态、时刻裁决、候选前自检使用 `polygons_overlap_exact(A,B,X)`；X 在 Fraction 上相加，不先浮点平移。VE/EV 间隙分子沿运动仿射，根 `-g/slope` 精确；共线滑移的端点事件另计，各自时刻投影边内也精确。
- 候选前自检不仅探一步，还核此前全部原始顶点—边事件，捕获“更早撞入又分离”的窄区间；无候选也核事件，漏候选不静默。`tied_labels` 只含精确同时项，`near_labels` 单独报告；`t_exact` 保存精确时刻。
- `shortest_exit` 在精确有效/边内的非正 gap 中比较有理平方距离，取最浅局部盖（最大非正 gap）。它不是一般凹对的全局最小分离算法。brute 的 Fraction 扫描/二分仍会漏孤立切触，且共用精确相交，只能作佐证。
- 局部 VE/EV/VV 默认无噪声带；VV 锥交与严格活跃取精确符号，边界不标 strict。显式窗口另报 `window_active`，不冒充严格性。距离/投影窗口精确平方比较，无舍入地板。
- `convex_hull` 始终接 `hull_exact` 保留真极点；tol 仅兼容签名，不隐式简化。全仓没有需要非零简化窗的调用。删 `_angle_tols` 等死噪声代码；geom 的浮点对照/统计函数仍有调用，文档明确不是生产精确判定。
- 追踪精确相交依赖链时补修 triangulate 的浮点面积朝向、Fraction orient 的浮点过滤；极小/极大尺度朝向门先红后绿。G0 诊断重建出口点保持被测浮点加法次序 `(A+x)+t*u`，避免拿另一份舍入数据归因。
- 独立主门：闭式、测试内 Fraction 分片 SAT / winding / 邻点支持、VV Fourier–Motzkin；不调用生产几何原语。细节见 [notes_entrance.md](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/notes_entrance.md) / [notes_covers.md](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/notes_covers.md)。

### E4

- LP 算法不变，`LPResult.exact_x/exact_y` 保留证书的有理数见证。返回 alpha/lambdas/mechanism/row_duals 是带不可变 exact 的 float 视图；自检独立重建物理力矩和精确 c·A，不复用 LP 力矩/荷载平移原语；锥方向/列序仍是双方共用的模型定义，不声称模型定义零共用。
- 精确核验逐体平衡、λ/α非负、黏聚上限、各列相对功率、drive≥1、强对偶及逐项互补。α>0 时互补强制 drive=1；α=0 不额外错误强制等号。tol 与 *_rel 都不参与通过判定。
- “任意 k”是有理数算法性质；门覆盖 k=3,5,9,15,30,100，并覆盖 μ=1e-5、ΣcA/W=1e-5、远体1e4、h/L量级1e3及三维多体。Fraction 保留误差；若 float(1−10^-100) 已舍回1，输入根本未变，不可能识别未表达的信息。
- `contact_forces`/`active` 是按 tol 截断的展示，不是静力证书；静力来自完整 lambdas。复制保留 exact，普通算术/float()/JSON 往返会丢见证，之后按新给定数核；如需重用证书应显式保存有理分子分母。
- 多体可分辨性用每个体自己的接触形心与臂长；保留本体调用方构造力矩的原点距离噪声项，不借其他体跨度。局部舍入扰动精确移回 LP 公共原点。
- 新 `resolvability` / `resolvability_statuses` 分别报告 resolved、nearby_infeasible、unresolved、not_applicable 与±扰动状态。即使邻域不可行或由无界变有限，原问题精确 status/alpha 不变。resolved 只是单机构筛查未见超阈变化，不是稳定性/工程误差保证。
- 只读交叉探针把 exact 加1e-100、保持float读数相同，仍拒绝被改alpha/λ/机构/行对偶；见 [cross_review_limit_probe.json](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/cross_review_limit_probe.json)。这不替代 G6。

## 4. 旧测试改写台账与失败保留

总机读账：[test_changes.json](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/test_changes.json)；每次失败节点：[failure_inventory.json](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/failure_inventory.json)；AST 实际变化函数清单：[changed_test_functions.json](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/changed_test_functions.json)。原失败日志全部保留，不将预期修前红、接口字段缺失或重复运行计成独立数值缺陷。

| 测试 / 辅助函数 | 旧口径 | 新口径 | 为什么不更弱 |
|---|---|---|---|
| tests/test_kernel2d_entrance.py::test_every_legacy_vertex_edge_contact_of_bb52_is_a_first_entrance_along_its_edge_normal | All 53 legacy window covers checked; float overlap(FIT)==1 cases skipped; other cases required window-equivalent entrance. | Preserve 53 inputs and legacy window/count constraints; independent Fraction edge-intersection/winding initial state on every input; penetrated cases require exit and complete independent exact shallowest-cover label set; nonpenetrated cases require exact boundary contact and original legacy window comparison. | No original input removed; previously skipped penetrated inputs now checked independently; false premise from noise-window classification removed, not a tolerance relaxation. |
| tests/test_kernel2d_predicates.py::test_hull_of_a_rotated_collinear_strip_has_four_vertices | 3000 个旋转平行细条一律恰 4 顶点 | 原 3000 点集，每格精确支持线 oracle 顶点集合全等 | 不把舍入后的真实微小极点丢弃；每个点集直接验证数学凸包，不再只数点。 |
| tests/test_kernel2d_lever.py::test_vv_cover_strictness_is_invariant_when_the_separation_direction_is_on_the_cone_boundary | 锥边界方向 31 姿态 strict 必须与恒等相同 | 原 31 姿态，strict 与独立 Fraction 邻点支持精确一致 | 比不变性更强的逐格正确性；数据真实跨边界不再强迫错答相同。 |
| tests/test_kernel2d_lever.py::test_ve_cover_in_segment_band_is_invariant_for_a_vertex_over_a_short_edge_endpoint | 短棱端点 31 姿态枚举标签恒等 | 原 31 姿态完整标签+strict 与独立 Fraction oracle 全等 | 没有放宽预期、没有删格，既抓漏盖也抓凭空多盖，舍入跨端点按精确数据答。 |
| tests/test_invariance_2d.py::test_cover_enumeration_is_invariant | 变换标签集等于 identity 或两噪声窗口夹逼 | 原网格逐格独立 Fraction oracle 全等；已测余量标签继续刚体不变；共有标签保留原 gap 缩放界 | 旧门可放过 du×100；新门带内也必须精确，只有数据变化的变换不变性按明确余量解释。 |
| tests/test_invariance_2d.py::test_cover_invariance_unresolvable_cells_are_explained_by_measured_near_parallel_edges | 噪声算法必须恰有 19 个不可分辨格 | 原完整网格，每个变化标签有实际判据余量<=报告舍入界，且 changed>0 stable>changed | 19 是已删除算法的产物非几何定理；新门逐标签证明变化原因，正确性另逐格精确 oracle 无豁免。 |
| tests/test_bb52_g1.py::_drop_cone_boundary | 变异 cv.in_cone 丢边界，间接触发距离完备性门 | 变异实际生产路径 cv._ve_side 丢边界，保持原距离完备性断言 | 旧符号已经不再被调用；将相同缺陷移到真实被测入口，避免无牙。 |
| tests/test_kernel2d_review.py and tests/test_kernel2d_g0.py (noise-only enumerate arguments) | 给数学候选传 tol=1e-9/1e-12 | 删除历史噪声入参，保留原断言与几何 | 不把容差放宽当作真值，精确有效性更严格。 |
| tests/test_bb52_g1.py::_drop_cone_boundary | 变异已被新实现绕过的 in_cone | 相同丢非严格盖缺陷注入实际 _ve_side | 牙必须穿过真实枚举路径；缺陷类别不变而注入点恢复有效。 |
| tests/test_bb52_g1.py::test_g0_distance_completeness_has_teeth | 牙/归因必须报红；噪声strict旧投票106/110；VE-only分离侧无感 | 所有牙/归因保留；精确strict旧投票630/640逐值等式；VE-only分离侧额外必须抓19/603且逐条归因缺盖 | 改变的是旧噪声strict产物快照，不是牙要求；原出口侧必须抓缺陷不变，新增分离侧也必须抓而更强。 |
| tests/test_bb52_g1.py::test_g0_exit_completeness_has_teeth | 牙/归因必须报红；噪声strict旧投票106/110；VE-only分离侧无感 | 所有牙/归因保留；精确strict旧投票630/640逐值等式；VE-only分离侧额外必须抓19/603且逐条归因缺盖 | 改变的是旧噪声strict产物快照，不是牙要求；原出口侧必须抓缺陷不变，新增分离侧也必须抓而更强。 |
| tests/test_invariance_2d.py::_covers | 数学/legacy模式都传 tau 噪声 | 数学模式显式0，legacy模式保留明示角/边端域窗口 | helper本无断言；下游每格独立Fraction oracle不使用被测helper，增强数学模式严格性。 |
| tests/test_invariance_2d.py::test_cover_enumeration_is_invariant | identity输出或双窗口夹逼作为参考 | 原网格每格独立Fraction oracle精确全等，有余量标签仍不变，共有gap保持原缩放界 | 带内不再容许任意一个容差答案；真值全等比旧夹逼更强。 |
| tests/test_invariance_2d.py::test_cover_invariance_unresolvable_cells_are_explained_by_measured_near_parallel_edges | 噪声算法必须恰有19个不可分辨格 | 原完整网格逐个变化标签的判据余量需落在报告界，且非空变化/稳定标签均覆盖 | 19是被删除噪声算法产物，不是几何定理；正确性主门每格精确零错不予豁免，报告门量化每个数据边界变化。 |
| tests/test_kernel2d_lever.py::test_vv_cover_strictness_is_invariant_when_the_separation_direction_is_on_the_cone_boundary | 原186个边界姿态与identity strict强制相同 | 原186姿态分别对独立Fraction邻点支持oracle全等 | 边界舍入数据不再被强制错答；逐格真值也抓稳定的伪活跃，不只是抓翻转。 |
| tests/test_kernel2d_lever.py::test_ve_cover_in_segment_band_is_invariant_for_a_vertex_over_a_short_edge_endpoint | 原124个短棱边端姿态与identity标签相同 | 原124姿态完整标签+strict对独立Fraction邻点投影/线性消元oracle全等 | 不删格，额外核对strict并同时拒漏盖/伪盖。 |
| tests/test_kernel2d_predicates.py::test_hull_of_a_rotated_collinear_strip_has_four_vertices | 原3000点云均被噪声判4点 | 重命名matches_exact_support，原3000点云逐格独立Fraction全点支持线集合全等 | 更强正确性门，保留所有输入并识别舍入后真极点。 |
| tests/test_kernel2d_review.py::test_r3_numerically_collinear_vertex_yields_no_vv | 数学 enumerate_covers / first_entrance_for_vertex 调用传历史 tol=1e-9/1e-12 | 只删这些候选调用的噪声 tol；所有原断言及其他 API 入参保持 | 不删断言、不换几何、不扩大容许输出集合；要求原测试在精确无窗候选下成立。 |
| tests/test_kernel2d_review.py::test_gap0_sign_of_min_gap_is_not_a_concave_membership_rule | 数学 enumerate_covers / first_entrance_for_vertex 调用传历史 tol=1e-9/1e-12 | 只删这些候选调用的噪声 tol；所有原断言及其他 API 入参保持 | 不删断言、不换几何、不扩大容许输出集合；要求原测试在精确无窗候选下成立。 |
| tests/test_kernel2d_review.py::test_gap0_sign_of_min_gap_false_negative_wedge_in_channel | 数学 enumerate_covers / first_entrance_for_vertex 调用传历史 tol=1e-9/1e-12 | 只删这些候选调用的噪声 tol；所有原断言及其他 API 入参保持 | 不删断言、不换几何、不扩大容许输出集合；要求原测试在精确无窗候选下成立。 |
| tests/test_kernel2d_review.py::test_c19_zero_length_edge_is_a_clear_error_not_zerodivision | 数学 enumerate_covers / first_entrance_for_vertex 调用传历史 tol=1e-9/1e-12 | 只删这些候选调用的噪声 tol；所有原断言及其他 API 入参保持 | 不删断言、不换几何、不扩大容许输出集合；要求原测试在精确无窗候选下成立。 |
| tests/test_kernel2d_review.py::test_c19_loaders_strip_every_cyclic_consecutive_duplicate | 数学 enumerate_covers / first_entrance_for_vertex 调用传历史 tol=1e-9/1e-12 | 只删这些候选调用的噪声 tol；所有原断言及其他 API 入参保持 | 不删断言、不换几何、不扩大容许输出集合；要求原测试在精确无窗候选下成立。 |
| tests/test_kernel2d_g0.py::test_first_entrance_picks_shallowest_penetration | 数学 enumerate_covers / first_entrance_for_vertex 调用传历史 tol=1e-9/1e-12 | 只删这些候选调用的噪声 tol；所有原断言及其他 API 入参保持 | 不删断言、不换几何、不扩大容许输出集合；要求原测试在精确无窗候选下成立。 |
| tests/test_bb52_g1.py::test_g0_distance_completeness_has_teeth | 110/106 | 640/630; keep exact equality | 旧废弃投票计数针对旧噪声strict，不是新精确strict；牙已报红但比较计数过时 |
| tests/test_bb52_g1.py::test_g0_exit_completeness_has_teeth | 110/106 | 640/630; keep exact equality | 同上 |
| tests/test_limit_arch.py::test_high_friction_arch_collapses_by_the_best_hinge_mechanism | 浮点4×4铰链消元、容差-1e-12开闭；近似twists断言admissible | 点先Fraction再相减，独立有理数4×4消元及精确主元/开闭；原α比较与N/μ参数全保留 | 同样assert admissible且oracle更严格，不删格、不宽容差 |
| tests/test_limit_arch.py::test_any_friction_arch_is_bounded_above_by_every_hinge_mechanism | 浮点4×4铰链消元、容差-1e-12开闭；近似twists断言admissible | 点先Fraction再相减，独立有理数4×4消元及精确主元/开闭；原α比较与N/μ参数全保留 | 同样assert admissible且oracle更严格，不删格、不宽容差 |
| tests/test_limit_duality.py::test_three_d_row_duals_equal_each_contacts_cohesive_dissipation | θ=.3手工sin/cos平动被当精确drive=1；反序row拒绝 | θ=.3原α与正常精确自检保留；在原返回机构上反序row仍拒绝；独立证明手工cos/sin drive!=1故拒绝；增加同非对称四角/原点的精确反向轴向人工可行者及反序row拒绝 | 保留原一般方向错配牙；修正错误理想化断言，并新增精确手工对偶面成员 |
| tests/test_limit_multi.py::test_a_far_body_does_not_loosen_the_self_check | δ=1e-3 ×原4跨度；static_ok=false且static_residual_rel>1e-5 | δ=10^-k，k3/9/30/100 ×原4跨度；static_ok=false且精确残差任一非零 | 保留原格并增任意小注入；精确残差非零比显示归一量有牙且不依赖显示参考点 |
| tests/test_limit_selfcheck.py::test_self_check_rejects_wrong_answers_at_engineering_coordinates | factor0/.5/.999/1.001/2 | 保留原5格并加Fraction(1)-10^-k，k3/9/30/100；用alpha.exact构造 | 保留原注入幅度与UTM场景，新增超float分辨率 |
| tests/test_limit_selfcheck.py::test_the_limit_load_self_check_raises_on_an_injected_error_at_engineering_coordinates | 真实LP返回路径α×.999 | 同原输入，k3/9/30/100的精确α×(1-10^-k)，均必须RuntimeError self-check | 保留1e-3并增亚ulp注入，误差在返回前被真实调用路径拒绝 |
| tests/test_limit_multi.py::test_self_check_raises_on_an_injected_wrong_alpha | 真实LP返回路径α×.999 | 同原输入，k3/9/30/100的精确α×(1-10^-k)，均必须RuntimeError self-check | 保留1e-3并增亚ulp注入，误差在返回前被真实调用路径拒绝 |
| tests/test_limit_multi.py::test_multi_resolvability_has_the_same_three_regimes_as_the_single_body_version | 6输入仅body0：optimal/抛错/邻域infeasible替换原答案 | 原6输入×body0/1：原optimal且exact alpha*v=1 +精确自检，再核三个报告与双边状态 | 保留每条筛查分支牙，新增给定原数据答案不可篡改证明 |
| tests/test_limit_fuzz.py::test_rounding_level_load_component_is_not_certified_as_capacity | sin(pi)给定数据被改报infeasible | 原optimal且exact alpha*sin(pi)=1 +精确自检；报告nearby_infeasible；精确水平另一原输入仍infeasible | 保留物理理想化与给定数区别、敏感性告警；新增原精确答案证明 |
| tests/test_limit_fuzz.py::test_small_load_component_resolvability_has_three_regimes | 10输入 optimal/raise/infeasible | 原10输入全exact alpha*v=1及精确自检，分别报告resolved/unresolved/nearby_infeasible并核双边状态 | 不削筛查分支牙，禁止邻域判断篡改原给定数据 |
| tests/test_limit_fuzz.py::test_a_large_first_order_uncertainty_alone_does_not_reject | 强制U=1：稳定例optimal、小分量infeasible | 稳定例保持原精度；小分量原optimal并精确闭式、nearby_infeasible | 保留推偏重解的牙并多核正确原问题 |
| tests/test_limit_fuzz.py::test_broad_fuzz_has_no_astronomical_load_factors | 1000输入不得返回大α，允许≤1%抛错并独立核真不可分辨 | 同1000输入零抛错、unresolved≤1%；大α不得resolved；大α/unresolved全部独立核原精确值与邻域敏感 | 保留敏感性看护并额外核原精确值，不能用错状态隐藏大α |
| tests/test_limit_selfcheck.py::test_a_penetrating_tipping_mechanism_is_rejected_at_any_site | docstring称现在在接触形心判定；原T×s×frac参数及闭式/双容许性断言 | 仅docstring改称E4在调用方原点精确核、不依赖尺度；所有参数、算式和断言逐字不变 | 纯文档口径修正，门的可执行AST（除docstring外）完全相同 |
| tests/test_limit_arch.py::_solve4 | 浮点4×4消元，abs(pivot)<1e-12时当奇异 | 输入提升Fraction，独立有理数4×4消元，仅精确零主元判奇异 | 不删非零小主元，消除oracle求解器自身舍入；原拱门所有N/μ和容量/容许性断言保留 |
| tests/test_lp_certificates.py::test_rounding_driven_load_factor_is_not_certified_at_any_dead_load | 六种恒载及二维/三维原输入，理想竖直物理解释要求status=infeasible。 | 原输入/两维均保留，对测试内独立Fraction LP逐格核原始status和alpha.exact，必须optimal；另要求nearby_infeasible及扰动状态含infeasible。 | 原物理风险仍必须显式报告，新增同数据状态/目标精确等式；不再把邻域结果覆盖原始解。 |
| tests/test_lp_certificates.py::test_near_self_locking_is_certified_within_its_reported_uncertainty_or_loud | margin<1e-9可抛任意RuntimeError并跳过；否则optimal、U<=1e-6、闭式误差受U限制。 | 28格均不许抛错跳过，独立Fraction LP核原status/alpha.exact；原margin>=1e-9 resolved要求和resolved闭式误差不变，小余量unresolved/nearby_infeasible另报且检查扰动证据。 | 消除小余量异常豁免，每格新增精确真值；原可分辨格及闭式误差约束保留。 |
| tests/test_lp_certificates.py::test_status_is_frame_invariant_on_a_frictionless_floor | 24个舍入框架不论实际浮点数据均强制status=infeasible。 | 全24格逐格独立精确LP状态/alpha核；确实不可行时not_applicable，实际可行时必须nearby_infeasible和infeasible扰动见证。 | 不再对边界舍入数据强加理想状态；零样本豁免且物理风险检测不降低。 |
| tests/test_lp_certificates.py::test_rounding_driven_unbounded_status_is_not_certified | 5个原框架一律status=infeasible。 | 5格实际数据精确LP状态/alpha全核；原不可行report not_applicable，舍入造成可行/无界则保留原status并明确nearby_infeasible。 | 给定数据精确答案比理想物理覆盖更强，原风险仍必须抓到。 |
| tests/test_lp_certificates.py::test_an_unbounded_conclusion_that_turns_finite_within_rounding_is_not_certified | 独立8角扰动盒有有限解后，要求抛RuntimeError。 | 原始输入与8角独立oracle全部保留；原status精确无界，resolvability必须unresolved，扰动状态必须含optimal。 | 保留全部原边界证据且新增原始状态/alpha准确性；不以抛错代替风险与解的分开表达。 |
| tests/test_lp_certificates.py::_exact_limit_lp | Fraction(C.cap[row]) used rounded float c*A | Fraction(contact.cohesion)*Fraction(contact.area) from row owner | oracle now matches independently assembled exact derived model, strengthens equality; no production wrench/shift/LP primitive shared; cone generators remain model definition |

补充辅助函数：`test_limit_arch.py::_solve4` 改独立有理数消元；`test_invariance_2d.py::_covers` 去历史噪声传参并另用独立 oracle。所有原几何/参数输入保留；没有通过删格、skip、xfail或扩大容差来换绿。bb52 strict-only 变异的旧废弃投票计数从110/106变为640/630，是精确strict后的新固定结果；距离/出口红牙断言仍保留精确核对，非改成“任意计数”。
收尾读回纠错：bb52 台账曾称已加584/603与逐距离归因断言，但CRLF模板在LF文件静默零匹配。主代理发现后中止190.110 s的首次全套，保留中止日志；真正补入两条断言并定向核验后，从头运行本报告的最终全套。先前27.58 s绿日志不冒充新增两条的验证。此为验证/编辑错误，不是新的几何缺陷。

## 5. 十项源码突变与实际报红断言

机读结果、补丁、命令、JUnit失败全文、前后SHA：[mutation_results.json](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/mutation_results.json)。所有变异均落到生产被测路径，非产出后追加假数据；串行执行，每项 finally 恢复原字节。

| 项 | 变异 | 实际结果 | 目标断言审读 |
|---|---|---|
| D1 | 凹首入精确相交改回浮点平移+polygons_overlap(ctol) | 9 failed in 0.31s [日志](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/mutations_entrance/D1.log) | RuntimeError: first_entrance: bodies already touch at t = Fraction(0, 1) < candidate Fraction(32, 1) (('VE', 0, 3)); the cover candidate set missed an earlier entrance；语义门预期有效输入精确返回t=32；变异误判t=0相触，候选前保护抛RuntimeError，因此未到最终t断言。不是类型错误或偶然顶点选择。 |
| D2 | 凹候选根改原始gap分子/仿射斜率的浮点商后转Fraction | 73 failed in 1.79s [日志](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/mutations_entrance/D2.log) | RuntimeError: first_entrance: no in-segment cover candidate, yet the bodies touch at t = Fraction(2573485501354569, 4503599627370496); the candidate set missed an earlier entrance；精确根被float舍入后漏候选，事件保护抛RuntimeError；有效输入本应返回精确时刻，73个时刻门拒绝此错误拒答。不是新字段缺失。 |
| D3 | 删除候选之前的精确漏候选自检 | 2 failed in 0.18s [日志](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/mutations_entrance/D3.log) | Failed: DID NOT RAISE <class 'RuntimeError'>；两道pytest.raises(RuntimeError)实际DID NOT RAISE，直接证明漏更早首入的自检有牙。 |
| D4 | 局部出口平方距离取max（等价取最小负gap） | 1 failed in 0.17s [日志](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/mutations_entrance/D4.log) | AssertionError: ((-1.0, -0.0), -1.9999999999999716)；最浅出口法向和gap断言红：变异选反向深盖gap=-1.9999999999999716，而非正确的微负浅盖。 |
| D5 | 局部无窗口VE退回旧角度/坐标噪声带 | 3 failed in 0.18s [日志](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/mutations/D5.log) | AssertionError: no-window local cone must reject exact reflex vertex；ve_cover(...no-window) is None断言红；真实微反射顶点被旧噪声窗错误接纳。 |
| D6 | VV开锥边界 > 改 >= | 6 failed, 9 passed in 0.23s [日志](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/mutations/D6.log) | AssertionError: VV activity must match exact neighbor support；c.strict == strict_vv_oracle断言红；边界被>=错误标strict。 |
| D7 | 二维凸包改回浮点容差pop | 1 failed in 0.16s [日志](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/mutations/D7.log) | AssertionError: true extreme point lost by tolerance-pop chain；(1e-15,-.001) in hull断言红，直接抓失真极点。 |
| D8 | 静力残差退回浮点全力尺度相对带 | 22 failed, 2 passed in 0.35s [日志](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/mutations/D8.log) | AssertionError: (3, 'small_mu', {'admissible': True, 'alpha': 9.99e-05, 'complementarity': 0.0, 'complementarity_exact': ('0', '0', '0', '0', '0'), ...})；assert not d[static_ok]为22格实际红断言；未借对偶/互补的其他拒绝冒充静力牙。 |
| D9 | 多体共用核的对偶间隙退回全局尺度带 | 12 passed in 0.16s [日志](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/mutations/D9.log) | 良性冗余：精确静力可行+对偶可行+逐项互补仍拒绝次优；见下式。；良性冗余逃逸：12格仍被精确互补拒绝；精确静力与对偶可行时，间隙等于各互补乘积之和，不能仅放宽间隙绕过互补。 |
| D10 | 多体筛查退回全局形心/臂长 | 6 failed in 0.22s [日志](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/mutations/D10.log) | assert 8.837378251418371e-08 == 4.44089653939...e-10 ± 1.0e-12；加入无关远体前后uncertainty相等断言6格全红；不是原问题status被改变才抓住。 |

D9 不是漏抓：在静力平衡成立时，`upper−alpha = Σ(lambda_j*power_j) + Σ(slack_r*row_dual_r) + alpha*(drive−1)`。精确可行性与逐项互补为零已经蕴含强对偶。D9 仅放宽 gap，互补检查仍按精确非零拒绝静力可行的次优插值；不能为强行造红删除第二道独立保护。D8 则直接看 `static_ok`，即使其它子检查也拒绝，仍证明静力子门自身有牙。

## 6. 全仓调用点分类

以下逐调用点来自 src/tools/tests AST 扫描（含别名函数名）；历史报告中复制脚本不是生产调用。完整机读信息含调用表达式：[callsite_classification.json](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/callsite_classification.json)。默认数学路径与真实 legacy 域窗严格区分。

| 调用点 | 函数 | 归类 | 理由 |
|---|---|---|
| src/eab/kernel2d/covers.py:258 | ve_cover | caller_window_propagation | 内部转发已声明的显式域窗口；strict 精确，VV window_active 单列。 |
| src/eab/kernel2d/covers.py:264 | ev_cover | caller_window_propagation | 内部转发已声明的显式域窗口；strict 精确，VV window_active 单列。 |
| src/eab/kernel2d/covers.py:270 | vv_cover | caller_window_propagation | 内部转发已声明的显式域窗口；strict 精确，VV window_active 单列。 |
| src/eab/kernel2d/covers.py:288 | ve_cover | caller_window_propagation | 内部转发已声明的显式域窗口；strict 精确，VV window_active 单列。 |
| src/eab/kernel2d/covers.py:294 | vv_cover | caller_window_propagation | 内部转发已声明的显式域窗口；strict 精确，VV window_active 单列。 |
| src/eab/kernel2d/entrance.py:232 | enumerate_covers | historical_noise_removed | 沿路径候选生成只用精确有效性，原 ctol 噪声不再传入；无穷距离窗仅穷举。 |
| src/eab/kernel2d/g0.py:247 | enumerate_covers | historical_noise_removed | G0 的 tol 是历史比较噪声，不是接触域；删掉传给枚举的 tol，比较误差在报告层。 |
| src/eab/kernel2d/g0.py:368 | enumerate_covers | historical_noise_removed | G0 的 tol 是历史比较噪声，不是接触域；删掉传给枚举的 tol，比较误差在报告层。 |
| src/eab/kernel2d/g0.py:381 | convex_hull | exact_no_window | 凸包用于输入构造或几何真值，必须保留全部精确极点；没有非零简化窗口。 |
| tests/test_bb52_g1.py:98 | enumerate_covers | frozen_historical_vote | 该处仅重放旧 1186 投票的历史口径，不是新生产判定；保留以复现旧数。 |
| tests/test_invariance_2d.py:127 | enumerate_covers | exact_and_explicit_legacy_domain | 数学模式不传历史 tau；legacy 模式保留 sin3deg 与明示边端窗口；每格对独立 Fraction oracle。 |
| tests/test_kernel2d_covers_e3.py:28 | vv_cover | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_covers_e3.py:31 | enumerate_covers | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_covers_e3.py:38 | ve_cover | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_covers_e3.py:39 | ev_cover | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_covers_e3.py:45 | enumerate_covers | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_covers_e3.py:46 | first_entrance_for_vertex | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_covers_e3.py:52 | enumerate_covers | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_covers_e3.py:54 | enumerate_covers | explicit_domain_regression | 显式参数只测试域窗的边界/单调放宽或 legacy 角窗；无隐藏噪声地板。 |
| tests/test_kernel2d_covers_e3.py:60 | convex_hull | exact_no_window | 凸包用于输入构造或几何真值，必须保留全部精确极点；没有非零简化窗口。 |
| tests/test_kernel2d_covers_e3.py:70 | vv_cover | explicit_domain_regression | 显式参数只测试域窗的边界/单调放宽或 legacy 角窗；无隐藏噪声地板。 |
| tests/test_kernel2d_covers_e3.py:71 | vv_cover | explicit_domain_regression | 显式参数只测试域窗的边界/单调放宽或 legacy 角窗；无隐藏噪声地板。 |
| tests/test_kernel2d_covers_e3.py:75 | enumerate_covers | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_covers_e3.py:76 | enumerate_covers | explicit_domain_regression | 显式参数只测试域窗的边界/单调放宽或 legacy 角窗；无隐藏噪声地板。 |
| tests/test_kernel2d_entrance.py:128 | convex_hull | exact_no_window | 凸包用于输入构造或几何真值，必须保留全部精确极点；没有非零简化窗口。 |
| tests/test_kernel2d_entrance.py:264 | ve_cover | explicit_legacy_domain | FIT/CONE 是 bb52 legacy 候选/排序的明示域窗口。 |
| tests/test_kernel2d_g0.py:73 | enumerate_covers | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_g0.py:76 | first_entrance_for_vertex | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_lever.py:87 | vv_cover | explicit_domain_regression | 显式参数只测试域窗的边界/单调放宽或 legacy 角窗；无隐藏噪声地板。 |
| tests/test_kernel2d_lever.py:95 | vv_cover | explicit_domain_regression | 显式参数只测试域窗的边界/单调放宽或 legacy 角窗；无隐藏噪声地板。 |
| tests/test_kernel2d_lever.py:111 | enumerate_covers | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_lever.py:117 | enumerate_covers | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_predicates.py:230 | convex_hull | exact_no_window | 凸包用于输入构造或几何真值，必须保留全部精确极点；没有非零简化窗口。 |
| tests/test_kernel2d_review.py:17 | normal_cone | explicit_domain_regression | 显式参数只测试域窗的边界/单调放宽或 legacy 角窗；无隐藏噪声地板。 |
| tests/test_kernel2d_review.py:19 | ve_cover | explicit_domain_regression | 显式参数只测试域窗的边界/单调放宽或 legacy 角窗；无隐藏噪声地板。 |
| tests/test_kernel2d_review.py:26 | vv_cover | explicit_domain_regression | 显式参数只测试域窗的边界/单调放宽或 legacy 角窗；无隐藏噪声地板。 |
| tests/test_kernel2d_review.py:31 | vv_cover | explicit_domain_regression | 显式参数只测试域窗的边界/单调放宽或 legacy 角窗；无隐藏噪声地板。 |
| tests/test_kernel2d_review.py:32 | enumerate_covers | explicit_domain_regression | 显式参数只测试域窗的边界/单调放宽或 legacy 角窗；无隐藏噪声地板。 |
| tests/test_kernel2d_review.py:140 | enumerate_covers | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_review.py:172 | enumerate_covers | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_review.py:175 | enumerate_covers | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_review.py:207 | normal_cone | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_review.py:207 | normal_cone | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_review.py:208 | enumerate_covers | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_review.py:209 | enumerate_covers | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_review.py:268 | enumerate_covers | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tests/test_kernel2d_review.py:275 | enumerate_covers | exact_no_window | 无额外角/边端域窗；window 若有只是明示搜索距离，零严格保持零。 |
| tools/bb52_g0.py:85 | vv_cover | historical_noise_removed | 仅诊断遗漏盖，TOL 历史噪声已删；不扩数学候选集。 |
| tools/bb52_g0.py:93 | ve_cover | historical_noise_removed | 仅诊断遗漏盖，TOL 历史噪声已删；不扩数学候选集。 |
| tools/bb52_g0.py:96 | ev_cover | historical_noise_removed | 仅诊断遗漏盖，TOL 历史噪声已删；不扩数学候选集。 |
| tools/bb52_g0.py:141 | enumerate_covers | explicit_legacy_domain | D0 搜索距离、SEG_TOL 边端窗口、cone_tol=sin(h1) 为 legacy 明示检测口径；不抬地板。 |
| tools/g4_multistep.py:57 | enumerate_covers | explicit_legacy_domain | detparams h1 给 sin 角窗口、5*d0 搜索距离；不要求边内，原 tol/seg_tol=1e-9 无实际域意义，已删。 |
| tools/showcase.py:218 | enumerate_covers | historical_noise_removed | 可视化搜索半径 0.05 是域窗口，tol=1e-9 只是历史噪声已删。 |
| tools/showcase.py:460 | ve_cover | explicit_legacy_domain | FIT=1e-6 与 CONE=sin3deg 复现 legacy 接触选择口径，保留显式域窗口。 |

## 7. 验证、范围审计与重跑

- 最终全套命令：`C:\Program Files\Python312\python.exe -X utf8 -m pytest -q -p no:cacheprovider --junitxml=D:\eab-wt\cx-e2\reports\codex\E3E4_evidence\final_full.xml tests`。环境 `PYTHONDONTWRITEBYTECODE=1`，`TEMP/TMP=reports/codex/E3E4_evidence/tmp/`，关闭 pytest cache。
- **原样末行：** `7729 passed in 734.49s (0:12:14)`。进程墙钟 `735.901037 s`；上一单用户提供400 s / 7500条，只作背景，不当同环境性能基准。
- 已运行 `python -X utf8 tools/fix_canon_ptrs.py --apply`；文档指针门在最终全套中通过。[指针修复日志](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/fix_canon_ptrs.log)。
- HEAD/分支未变、暂存区无修改；62 个基线跟踪 fixture 哈希不变、无删除；`git diff --check` 通过。[范围审计](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/scope_audit.json)。所有写入限当前工作树，无姊妹仓库写入、无 Git 写操作。
- 初始回滚锚：[initial_manifest.json](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/initial_manifest.json)；各次变异与基线源字节备份在忽略目录 tmp/。持久证据索引：[INDEX.md](file:///D:/eab-wt/cx-e2/reports/codex/E3E4_evidence/INDEX.md)。

重跑（PowerShell，在当前工作树）：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP=$env:TMP=(Resolve-Path 'reports/codex/E3E4_evidence/tmp').Path
python -X utf8 reports/codex/E3E4_evidence/run_pytest.py final_full tests
python -X utf8 reports/codex/E3E4_evidence/audit_scope.py
```

突变仅在没有编辑/其它pytest进程时重跑：先run_entrance_mutations.py，再run_mutations.py covers_mutations.json，再limit_mutations.json；均使用上述环境和python -X utf8。

## 8. 遗留与非目标

1. 未做用户禁止的新鲜 worktree 验证；未做六路独立 G6。需所有者后续验收，README没有把本单全绿替代G6。
2. 未实现一般凹块全局入口块/盖裁剪；最浅局部出口不保证一次移动清除所有接触。brute非完备独立oracle。
3. 三维几何E5、其余第五轮发现、工程标定/动力学/几何非线性均不在本单。三维锥仍是给定浮点方向的离散模型；精确算术不消除模型误差。
4. 极端指数浮点输出构造可舍入/下溢；本单保证分支对给定数据精确，不宣称所有float输出任意指数准确。非有限或任意巨大角域窗口未扩为完整保证；legacy sin3°等实际域窗已测。
5. 显示序列化不是精确证书序列化；输入可分辨性筛查并非全对偶面/全不确定性界。

E3E4_DONE
