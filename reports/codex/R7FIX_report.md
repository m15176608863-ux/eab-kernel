# WO-R7FIX 第七轮复审修复报告

> 本报告记录本次工作树修复，不代表 M0 / G6 独立退出。最终全套验收结果见第 6 节。

## 1. 工作契约与边界

- **目标**：逐条处理 G6G-01…11（原审查 0 critical / 9 major / 2 minor）；每条先在原实现上真实跑红，再修复、验证，并注入关键步骤退化证明看护门有牙。已确认的同类问题一并处理。
- **范围**：仅 `D:/eab-wt/cx-e2`。起点 `codex-work` / `d44dd78e84fa0434860f52ca1a76306ddc498c48`；初始未跟踪项只有工单输入。未 commit、push、reset、checkout、stash 或创建 worktree；未修改其他工作树、姊妹仓库或 `D:/E(A, B)`。
- **非目标**：不切换姊妹内核，不修改只读 07 正本，不新增学术优先性主张，不把定向/全套绿冒充六路独立 G6 复审或工程验证。
- **回滚锚**：[修前 tracked 文件 ZIP](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/baseline_tracked.zip) 与 [起始状态及逐文件 SHA-256](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/baseline.json)。没有依赖 Git 丢弃用户修改。
- **验收**：独立构造的主 oracle、修前断言日志、修后回归、每项关键内部变异、全部原测试不弱化、指针门、全套和夹具哈希核对。
- 所有 Python 运行使用 `PYTHONDONTWRITEBYTECODE=1`、`python -X utf8`；临时产物限定在本树证据目录。文件修改保留原换行，检查 CRLF 时使用 `git -c core.whitespace=cr-at-eol diff --check`。

## 2. 11 条逐项处置

`q = 2^-1074`。下表中的“修后绿”由具名新门与最终全套共同验收；修前日志是原代码真实失败，不是根据旧代码推测。变异均进入被测函数内部；文档项实际回退受测文字后运行同一断言，并恢复原字节。

|编号|修前红：断言与错误输出|根因与修法|修后门及变异结果|
|---|---|---|---|
|**G6G-01 major**|`brute_ray_exit(...) == 1/2` 实得 `2`；删除真正首出口盖后 `not rep.passed` 也红，旧门仍 passed。|只查事件间区间，漏掉瞬时真边界。保留拓扑 `int E` 出口定义：检查事件本身，并用独立有理平移线排列的邻域外扇区证书区分真边界与紧配内缝。|`test_g6g01_first_exit_checks_isolated_true_boundary_event` 等；L 反角为 1/2，U 紧配内缝不误报（真出口 5/2），旋转/平移/尺度格全部保留。去掉事件检查的内部变异仍在 `==1/2` 红（实得 2）。|
|**G6G-02 major**|`normal` 期望单位向量却为 `(1,1)`；有理差 `(1.49q,.49q)` 的 `gap==2q` 实得 q；巨大有限差未拒绝 inf。|差分量先转 float，再用舍入 norm 归一。VV 保留精确相对向量；gap 从精确平方最终开根，单位分量各自由 `v_i²/Σv²` 构造，不能用已舍入 gap 作分母。无证书且不可表达的非零输出响亮拒绝。|`test_g6g02_vv_uses_exact_difference_and_independent_unit_normal` / `test_g6g02_vv_unrepresentable_gap_fails_loud_not_inf`。内部恢复 `float(d)`，同一 `gap==2q` 断言红。|
|**G6G-03 major**|有限巨大 L 形中内部删掉所有盖，`samples=1, worst_abs_error=inf, passed=True`；距离、出口两路均错误。|浮点 L/阈值为 inf，`inf>inf` 放行。验收用精确 bbox 长度平方与有理比较；缺盖、所有候选中的 NaN/inf、非有限误差独立拒绝。距离窗在构造前精确筛选，不让窗外无关超范围盖阻塞最近盖门。|`test_g6g03_unrepresentable_diameter_does_not_disable_missing_cover_gate` 两路；内部恢复浮点阈值，`not rep.passed` 红。公开不可表达 char_length 另有 fail-loud 门。|
|**G6G-04 major**|`folded-ridge-slab-distance` 要求 2，源折面实得 `2.449489742783178`。|只枚举源面环边界棱，漏三角化后真实折棱。全特征距离改枚举实际三角表面的全部几何棱，保持原顶点编号。|`test_g6g04_folded_internal_ridges_attain_slab_distance`；手工 slab 下界和屋脊中点上界独立一致。内部恢复 A 侧 `A.edges()`，同一距离断言红；全部 brute 使用门纳入最终全套，见第 4 节。|
|**G6G-05 major**|面积 `29q/20` 期望 q，实得 2q；q/2 无证书却静默 0；facet/support 间隙期望 ±q，实得 ±2q。|最终除 2 / 除法向长度前先舍入。面积形成精确 `n²/4`，有符号间隙形成精确 `numerator²/n²` 后最终开根并保号。|`test_g6g05_face_area_rounds_after_final_halving`、`test_g6g05_face_area_underflow_is_not_silent_zero`、`test_g6g05_facet_gap_rounds_after_normal_length_division`。恢复先开根再除 2 或先 float numerator，分别在 `area-final-rounding` / `signed-gap-final-rounding` 红。|
|**G6G-06 major**|正确非零 gap 的法向期望 `(0,0,-1)`，实得 None；旋转格方向分量误差约 0.107。|反减已经舍入的全局显示见证。改用精确原输入构造的盖法向及 gap 符号定 B→A；VF/FV/EE/VE/EV/VV 同治。方向显示不可表达时必须带未归一化有理方向证书并传至 MarginContact；不把显示向量用于精确分类。|`test_g6g06_margin_normal_does_not_subtract_display_points` 含大平移、旋转、A/B 互换。内部去掉精确法向分支，`exact-local-margin-normal` 红。原坏见证自校验仍保留，不能以真值重写所有错误输出。|
|**G6G-07 major**|`Dual(2**200,(2**200,))**-5` 导数实得 -0，期望 `-4.666318092516094e-301`。审查原 876 格中 27 格红（13 静默错与 14 响亮拒绝）。|input-only `_ordinary` 不能约束派生幂系数。整数导数保留 Fraction；非整数导数以 Decimal 独立指数保留到乘完种子，再检查型最终转换，撤掉幂的 input-only 快路。|`test_g6g07_derived_power_range_not_just_inputs` 完整 876 格和最小复现均绿。内部恢复旧快路，`nonzero derivative must not become signed zero` 红（1 failed）。非整数仍是浮点构造，不冒称超越运算有理精确。|
|**G6G-08 major**|薄长盒 `axis-product-volume` 实得真值 2/3；对称盒体心非零；同一平面面环循环换起点使四面体体积从 0 变正确值。|浮点叉积/三重积中间下溢，错误零还触发体心后备逻辑。实际三角表面相对三重积、体积和一阶矩全程有理累加；仅最终 volume/centroid 转换，体心不依赖浮点 volume。|`test_g6g08_mass_properties_use_exact_products_before_final_rounding`、`test_g6g08_centroid_retains_cancellation_even_when_volume_is_representable`、`test_g6g08_volume_independent_of_cyclic_face_ring_start`。内部把相对坐标先转 float，`axis-product-volume` 红。|
|**G6G-09 major**|五份当前文档在“区分 PD_closed 与 rho”断言红。恰-fit 封闭空腔的运行值修前已与薄壳政策一致，错在把政策冒称 PD。|只读核正本 01 的紧凸前提和闭集分离下确界。现行文档明确 `PD_closed=inf{\|\|d\|\|:(A+d)∩B=∅}`、`rho=inf{\|\|d\|\|:int(A+d)∩int(B)=∅}`；一般闭表面六轴仅证 rho≤w，不证 PD_closed≤w。|`test_g6g09_tight_closed_cavity_distinguishes_rho_from_pd_closed` 用独立区间/连通性给 rho=1/8、PD_closed=19/8，后者不取到；文档/API docstrings 门绿。实际恢复旧轴⇒PD 文句，同一 `axis acceptance does not bound PD_closed` 红。|
|**G6G-10 minor**|当前状态/oracle 门在 `stale production oracle claim` 红；canon 的 GAP3 历史开放与现状已处置混写。|标明历史阶段，统一当前状态；README 改指独立 `kernel2d/g0_oracle.py`，不再指生产 polygons_overlap。还通过禁用生产函数后的实际 G0 运行验证，不只替换文字。|`test_g6g10_readme_oracle_and_canon_status_are_current` 绿；真实 README 恢复旧句后目标断言红（1 failed）。|
|**G6G-11 minor**|优先性门在 `narrowing priority to DDA is still a false claim` 红。|撤回而非缩小“首次/第一份”范围。依只读 00 的 Zheng/Jiao、Zhao、Feng/Tan、Ni 谱系，改为一份独立实现和姊妹独立对账通道；连内部通道的序数宣传也撤掉。历史引文仅以明确否定/删除线语境保留。|`test_g6g11_priority_claim_is_withdrawn_instead_of_narrowed` 绿；真实 canon 恢复“对外限定为 DDA 圈内第一份”，目标断言红（1 failed）。外部只读 07 的旧句登记在 canon，不声称已修改正本。|

### 原始证据入口

- 分报告保留各阶段原始计数，最终范围以各自追加节及本报告为准（二维主体的早期 28 格后来扩为 34 格，并追加 7 个力学构造门）。G6G-05 的 signed-gap 变异见三维 mutations.json；area 变异是永久测试 `test_g6g05_internal_mutation_rounding_norm_before_halving_is_caught`，在函数内部恢复先开根再除 2 后，必须捕获 `area-final-rounding` 断言，不另伪称 JSON 里有第二条记录。
- [二维逐项分报告](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom2/report.md)：初始 `11 failed, 1 passed in 0.17s`；三个独立内部变异日志；最终新增 34 格。
- [三维逐项分报告](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/REPORT.md)：初始 `18 failed, 3 passed in 0.43s`；最终定向 `117 passed in 8.85s`；[变异 JSON](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom3/mutations.json)。
- [Dual / frozen / G03 分报告](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/dual/root_report.md)：G07 初始 `28 failed, 850 passed in 0.69s`；修后与旧门 `1022 passed in 0.82s`；[变异 JSON](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/dual/mutations.json)。
- [文档分报告](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/report.md)：初始 `8 failed, 3 passed in 0.25s`；最终文档+原 PERF 门 `39 passed in 1.06s`；[真实文件变异与恢复 SHA](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/document_mutations.json)。

## 3. 全仓同类扫描

扫描来源为输入审查的“原始量提前舍入/平方范围损失、派生量快路、缺失几何特征、非有限验收、定义与当前文档矛盾”。[关键词和调用点清单](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/scan_inventory.txt) 覆盖 src、tests、README、docs；另按实际调用关系审计，并非只搜索原发现行。

|同类区域|额外确认并处理的问题|
|---|---|
|二维几何/入口|norm/unit、vertex_turn、turn_angle、FF 长边选择改用原数据的精确差/平方；angle_floor(q,q) 原先为 0 而最终 64eps 可表达，入口地板 Amax+xmax 先溢出但最终有限，均已先红后修。报告上界保留 Fraction 并向外舍入唯一根式。精确 tuple 有界缓存配可变输入新键门，无按范围猜测的快路。|
|三维几何/裕度|Newell 单个叉积分量丢失、unit/_qunit/inflated_normal 最终缩放前舍入、angle_between 正交微向量误报 0、metrics/edge_dir/characteristic_length 原坐标差溢出，均已修；极小方向显示携精确方向证书，不静默改变几何判定。集成中又确认 interlock._normal_noise 的非零舍入叉积也会错，改原边精确叉积/长度平方后最终开根，保留原 oracle 与阈值。|
|距离特征完备性|除原折面内部棱，又确认两片三角形发生棱穿面而旧 brute 返 1/3。增加真实三角交点零距离候选和精确 AABB 剪枝；独立手工交点门先红后绿，删该内部步骤变异红。|
|冻结法向与导数|原 _unit_jet 先舍入 scaled component / norm，次正规最终分量 q/2q 错选。值和切向导数都用精确平方商最终开根；5 格先红，值/导数两种内部回退变异分别 4/1 格红。|
|三维 G0 验收|有限 atol=1e308 也可先变 inf 阈值；混合有限/NaN 候选可被 min 隐藏。入口校验 atol、全候选有限审计、错误独立拒绝、有理验收式同治。4 格初始红、混合候选另 1 格红，修后全部绿。|
|力学接触构造|跨模块最终扫描确认全 float 法向 `(3,3,±7q)` 的第三单位分量应 ±2q，却因 v/m/n 返回 ±q；_norm 有理差同样早舍入且巨大有限 norm 静默 inf。新 5 格真红后，将两个函数改为完整精确平方最终开根，无证书非零不可表达值响亮拒绝，不改 LP 模型/证书算法。最终新 7 门绿（含两种内部变异），选择性原 LP 回归 `753 passed in 38.40s`；证据在二维分报告追加节。|
|文档谱系与状态|README/canon/两设计文档/PERF/exact_sweep/margin 的同类六轴命题统一；AGENTS 与 sibling 台账当前序数主张撤回。冻结的审查输入和历史失败证据不改写。|

明确未把“扫过”冒充全域证明：已经精确构造的 LP 证书、VF/FV/EE 距离平方等路径不另造替代判据；乘除/atan2 的有限次数快路指数界与消差回退不同于幂的派生指数问题。本轮确认的同类错误均处置；有限扫描和本轮互审不能代替下一轮独立对抗复审。

## 4. brute_feature_distance 的所有使用点复核

- 生产侧为 margin 分离距离的构造自校验；分支的精确几何关系/平方距离不由 brute 的浮点输出决定。工具侧另有 `tools/showcase.py`。
- 全部实际调用测试文件纳入最终全套：`test_frozen_lowdim.py`、`test_interlocking.py`、`test_geom3_face_polygon.py`、`test_invariance_geom.py`、`test_invariance_interlock.py`、`test_margin.py`、`test_near_parallel_edges.py`、`test_margin_resolution.py`、`test_r6fix_geom3.py`、`test_vv3_discard.py`，以及本轮新门。
- brute 与生产共享 exact_geom，因此只能做内部佐证。独立主 oracle 仍为 `g03_surface_oracle`；只读独立复核确认它自有非共面环切片及全边集合，原折面反例返回 2，未重复本次遗漏。
- 原有错误见证、自校验阈值等旧门未放松。交叉代理实际复跑旧相关门和新三维门 `43 passed in 0.82s`，[日志](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/scan/geom_review.log)。其余大组完整结论仅取最终全套，中途停止的补充跑不计通过。

## 5. 测试改写与失败处理台账

1. **旧测试及其独立 oracle 增强/适配共六个文件**（无原测试函数删除，完整参数网格保留）：
   - `test_r6fix_frozen_construction.py::test_frozen_unit_jet_divides_before_rounding_an_overflowing_tangent_component`：原 reference 先舍入 sqrt(3)，固化了本次修掉的一 ulp 双舍入。保留原输入和三通道，改为符号检查及精确解析平方 `seed²*k²/27` 严格落在返回浮点两侧相邻舍入中点平方之间。它唯一指定正确舍入值，无容差、无删格；[另一代理独立复核](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/geom2/peer_review_root.md) 同意为更强门。
   - `test_e5a2_integer_arithmetic.py::_eager_ee`：原独立 eager reference 没有填新增 `exact_normal_direction`，导致 9 个参数格仅该字段 None 不等。使用参考侧早已独立计算的 Fraction `candidate` 填证书；**原完整 dataclass 相等断言不变**，并增加证书检查，参数网格不变。
   - `test_interlock_e5a.py::test_normal_noise_handles_exact_cross_hidden_by_unit_vector_rounding`：原首句要求旧 unit 舍入恰好令两方向重合，本轮更正确单位化后该偶合不成立。保留全部原几何数据、独立 Fraction oracle 和 `rel_tol=2e-15`；先核真实显示路径，再通过内部替换 `edge_dir` 显示使两方向确实重合，要求结果与精确源数据一致且两情形相等。新增恢复非零浮点叉积快路的内部变异，看护原 expected 断言。增强门修前 `actual=1200.0488306054758`、`expected=5632.716247687068` 红，修后绿。
   - `test_r6fix_construction.py::test_g6f06_gap_magnitude_gate_has_teeth`：只给变异 lambda 增加 `**kwargs`，兼容受测构造 helper 新增的 `allow_underflow` 关键字；原 `sqrt(float(value))` 错算法和必须命中 `representable signed gap` 的 AssertionError 不变，避免无关 TypeError 抢先中止。
   - `test_margin_penetration.py::test_guard_is_not_a_vertex_inside_check`：完整 brute 新增棱穿面后，坏贯入守卫已被自校验提前阻断。先新增三个公共入口必须抛出具名 `nearest feature pair is 0.0` RuntimeError；再在 brute 函数内部恢复漏交面缺陷，**原错误距离 .05/EE、空 margin、主门报红、旧顶点内控制组照绿的全部断言原样保留**。这是两层牙，不是把旧断言删除后允许任意异常。两文件定向 `53 passed in 0.99s`，见 [日志](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/dual/round3_repair_green.log)。
   - `tests/e5a_cover_oracle.py::margin_selection`：旧 oracle 把给定浮点变换后已精确非共面的源四边形仍当作 Newell 平面。两路独立 Fraction 核算证明 16 个失败参数格的 29 个 VF/FV 生产平方距离全与真实三角曲面严格相等，显示值全为 0 ULP；错在旧 oracle，最大偏差 133,435,224 ULP。只修独立 margin oracle 的非共面 VF/FV 分支；源面 descriptor 的 `witness_distance` 不动，**原不变性测试文件、4 ULP 门槛、标签集合/数量和全网格一字不改**。另加手工折面 slab 下界/屋脊中点上界门，先在旧 oracle 跑红，再修正，并恢复 Newell 分支变异验证目标断言。原 162 格与新 4 格合跑 `166 passed in 29.51s`；[完全独立 Gram 核算及裁决](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/final_failure_adjudication.md)、[29 条精确证据](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/independent_folded_margin_gram.json)、[可重跑脚本](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/verify_folded_margin_gram.py)。
2. 不删除旧门、不放松、不加 skip/xfail、不缩网格。新增参数门含边界、非对称/一般位置和尺度格，原 876 指数格完整保留。
3. 二维旧大组早期 7 个 fixture ERROR 为限定 basetemp 父目录不存在（WinError3），属于环境错误；创建父目录后原 7 条逐项绿。没有改断言规避。
4. 三维相关组早期 2 个旧门红：非法面诊断在精确三角化时需返回 issue；低于 binary64 的合法精确 gap 需伴随精确方向证书而非无条件拒绝。两条分别治根并在最终定向组、全套重跑，旧门未改。
5. 两次编辑脚本因文本锚/PowerShell 管道编码未匹配而中止，均在写源文件之前失败；改明确 UTF-8/ASCII 锚后完成，保留真实红日志，不当作数值红证据。
6. 首次全套运行 136.340 s 后，为纳入最后确认的力学同类修复，精确停止了本任务 pytest 子进程；[中止元数据](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/interrupted_first_full_suite.json) / [中止日志](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/interrupted_first_full_suite.log)。该次没有完整结果，不计通过。
7. 第二次串行全套运行 787.280 s 后发现上述 9 个新字段参考差异和 1 个法向噪声门失败，停止并定向修复；[中止元数据](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/interrupted_regressions_full_suite.json) / [中止进度日志](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/interrupted_regressions_full_suite.log)。旧门的诊断堆栈和增强门修前红另存三维证据，修后相关三文件 `64 passed in 1.41s`。不将这次中止计作全套通过。
8. 第三次（首次完整并行）原样末行 `18 failed, 9829 passed in 445.65s (0:07:25)`，外层墙钟 447.673 s；[原始日志](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/round3_full_suite.log) / [元数据](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/round3_full_suite.json)。18 条为上面三个适配项：1 条变异接口、1 条贯入自校验提前阻断、16 条旧折面 oracle 口径。没有忽略失败或降低阈值，分别保存独立证据并修复后重跑全套。

## 6. 最终全套、用时与可重跑验证

最终全套原样最后一行：

```text
9851 passed in 446.20s (0:07:26)
```

- exit code **0**；外层实测墙钟 **448.7819219 s**，最终单次全套低于 900 s。[完整原始日志](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/full_suite.log)、[时间/命令/日志 SHA 元数据](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/full_suite.json)、[完整 JUnit](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/full_suite.junit.xml)。
- JUnit 实际解析 **9851** 个 testcases，**0 failure / 0 error / 0 skipped**；G6G-01…11 的具名回归前缀全部存在且通过，不用分片相加冒充全套。
- [机器验收](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/verification.json) 为 `verified=true`：运行前冻结的 **1727** 个 tracked/新增测试文件验收后字节均未变化；**62** 个 tracked fixtures 与修前 SHA-256 全部相同；原测试函数无删除；六个旧测试/辅助 oracle 改写文件与第 5 节台账一致；HEAD 未变；`diff --check` 通过。
- 如实区分耗时：四次全套尝试累计墙钟约 **1820.08 s**（含两次中止及一次失败），不是声称整个修复过程在 900 s 内完成。最终全套无删格、无 skip/xfail，通过 4 个隔离进程达到本次单次验收时间目标。

为尽量达到 900 s，最后一次正式全套使用 pytest 的 4 个隔离 worker。`pytest-xdist 3.8.0` 和 `execnet 2.1.1` 仅通过 `--target` 安装在 [本树验证依赖目录](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/verification_deps/)，禁缓存和字节码，不改系统 Python、用户配置或 pyproject 依赖。[安装日志](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/verification_deps_install.log)。并行前连同两个修正旧门、所有新门及指针门实跑 `1021 passed in 2.34s`；完整覆盖以最终 JUnit 为准，不靠分片计数估算。

可重跑入口：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
python -X utf8 tools/fix_canon_ptrs.py --apply
python -X utf8 reports/codex/R7FIX_evidence/run_full_suite.py
python -X utf8 reports/codex/R7FIX_evidence/verify_delivery.py
git -c core.whitespace=cr-at-eol diff --check
```

指针曾移动，已按工单执行脚本；最终重跑 `0 rewritten; 0 kept`，见 [指针日志](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/canon_apply_final.log)。源文件/fixtures 前后完整性及 JUnit 覆盖信息在验收清单中保存；输入文件的交付时 SHA 另列 artifact 清单，不冒称它们有修前 tracked 哈希。本单禁止创建 worktree，故只报告本指定工作树验证，不虚称执行 AGENTS 中新鲜 worktree 的里程碑门；未作合并，也未声称 G6 退出。

## 7. 交付与遗留

- 实际交付为本工作树未提交的代码、文档、新门和证据文件；[可点击成果清单](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/ARTIFACTS.md)、[逐文件 SHA / 链接 JSON](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/artifacts.json)、[tracked 改动补丁](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/working_tree.patch)。新测试为未跟踪文件，另见成果清单，不误称已包含在 tracked 补丁内。
- 只读 07 正本旧优先性句未改，已在 canon 明确登记并撤回本树主张；需正本所有者另行修改。
- 下一轮独立 G6 复审仍由所有者安排。本报告只关闭本工单已确认发现，不预先判定下一轮无新问题。

R7FIX_DONE
