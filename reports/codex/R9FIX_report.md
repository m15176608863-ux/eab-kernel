# WO-R9FIX 修复报告

日期：2026-10-12。执行树：`D:/eab-wt/cx-e2`，分支 `codex-work`，起始 HEAD `9f99025232450dc70b4e442b173badc3f9e55727`。**未提交。**

> 本工单六条修复及同类补扫已完成，工作树未提交。完整分片与标准单进程全套均通过，证据见第 7 节。修复执行团队的交叉检查不冒充下一轮独立六路 G6，不能据此宣布 M0 退出。

## 1. 范围、口径与回滚锚

- 输入为本树 `reports/codex/inputs/G6I_report.md`、`G6I_findings.json` 和复现脚本；正式发现只有 **6 条（4 major / 2 minor）**。工单交付处写“11 条”，因此以下采用 **6 条确认发现 + 5 项结构性/同类/验证工作**，不虚构 G6I-07～11。
- 只修改当前树；其他工作树、姊妹仓库和外部理论正本保持只读。无 commit / push / reset / checkout / stash / worktree；不删 fixture，不安装运行时。
- 字节回滚锚：[baseline_tracked.zip](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/baseline_tracked.zip)，初始文件 SHA/HEAD/status：[initial_state.json](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/initial_state.json)。只按文件核验恢复，不以 Git reset 覆盖未知改动。
- 所有测试命令设置 `PYTHONDONTWRITEBYTECODE=1`，使用 `python -X utf8`；pytest 加 `-p no:cacheprovider`，临时目录在本树 evidence/tmp。
- 常驻纪律要求新鲜 worktree，但本工单明确禁止建立 worktree；此次不执行该操作，**不声称完成新鲜工作树或独立 G6 退出门**。

## 2. 六条确认发现：修前红 → 修后绿 → 真实变异

### 1）G6I-01 / major：二维平直链域外标签及 FF 见证异常

**根因**：凸首入只裁剪无限支撑直线，没有在 selected/tied/near 标签回映之前核有限源特征。共线不同子段误被当作同一实际接触标签；clamp 将错误归属藏进见证。

**修前断言/输出**：原输入在 `t=1` 只能接触 `('VE',0,3)`，实际 tied 为 `{('VE',0,2),('VE',0,3)}` 并选中域外边 2；合法 FF 初触抛 `convex entrance face witness has no segment overlap`。[修前日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/geom2_red.log) 原样末行：`27 failed, 8 passed in 0.43s`。

**修法**：精确合并同向共线支撑并保留源标签；在实际首入时刻核 VE/EV 闭段投影与 FF 闭段交叠；只有有效源标签参与获选/并列/near。VE/EV 见证不再用 clamp 装饰域外标签。公开入口块的分段/标签数量契约不改。

**绿/牙**：新增 [test_r9fix_entrance_domain.py](file:///D:/eab-wt/cx-e2/tests/test_r9fix_entrance_domain.py) 36 格，含分界双标签、交换角色、尺度、旋转、大平移。定向组 `1152 passed in 52.80s`。真实生产 `_facet_in_domain` 内部判定改恒真后，`finite source edge labels` 断言得到 `16 failed, 8 passed, 12 deselected in 0.18s`；不是在输出后追加假数据。[变异日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/geom2_mutation.log)。

### 2）G6I-02 / major：声明折面凹棱被源环隐藏

**根因**：`is_convex/reflex_edges/dihedral_turn` 使用源环 Newell 向量，漏掉声明三角化真实内部对角 `(5,7)`。

**修前断言/输出**：独立屋顶方程证明非凸，`declared-roof-midpoint-concavity` 得 `True` 而非 `False`；`declared-folded-reflex-ridge` 得 `[]` 而非 `[(5,7)]`；实际直角被源描述符给成 `1.3258176636680326`。与 G6I-05 共用红日志：[topology_before.log](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/topology_before.log)，`66 failed, 2 passed, 4 deselected in 0.64s`。

**修法**：实体三入口先使用 `exact_surface` 的声明三角拓扑，保持原顶点编号；多闭壳不能仅以逐棱局部凸性宣称整体凸。公共实体法锥同根扩展见第 9 项。源单盖描述符私有路径与实体 API 明确分层，不通过凸化偷换输入。

**绿/牙**：[test_r9fix_topology.py](file:///D:/eab-wt/cx-e2/tests/test_r9fix_topology.py) 覆盖微凹、平面分界、旋转/尺度/平移、对象更新后表面新鲜性。针对组 `200 passed in 0.97s`，完整兼容组 `526 passed in 98.36s (0:01:38)`。分别在真实三个方法内部将 `P = exact_surface(self)` 改回 `P = self`，三条对应目标断言均报红，随后还原。

### 3）G6I-03 / major：精确最近点先舍分量再范数

**根因**：`cone_intersection_margin` 对精确 `p=(-d/3,-d/3,-d/3)` 先 `_float_vector(p)`，分量失真或舍零，最终可表达范数却错误。

**修前断言/输出**：24 个 multiplier 中 10 红；m=1 实际 `0.0`、真值 `5e-324`；m=2 实际 `1e-323`、真值 `5e-324`。独立 oracle 为原始极点的投影 KKT 与 Fraction 中点平方，不调用生产几何/构造。[construction_red.log](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/construction_red.log) 与 G6I-04 合计 `14 failed, 16 passed in 0.70s`。

**修法**：对精确 p 先完成平方和，再 `norm_rational` 构造最终标量；范围外不静默清零。

**绿/牙**：[test_r9fix_construction.py](file:///D:/eab-wt/cx-e2/tests/test_r9fix_construction.py) 保留 24 格。真实函数体恢复 `norm(_float_vector(p))` 后，`G6I-03 exact cone margin` 命中 `assert 0.0 == 5e-324`。构造定向组 `241 passed in 3.21s`；扩大组 `320 passed in 9.44s`。[修后及变异输出](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/construction_green.log)。

### 4）G6I-04 / major：距离 oracle 平方先 float 导致失牙

**根因**：`e5b_margin_oracle` 和 `exact_seg_seg` 默认出口存在 `sqrt(float(d2))`；平方下溢/上溢时，最终根仍可表达。门甚至可能放行相同错误的生产变异。

**修前断言/输出**：新增指数 `{-600,-540,-500,0,600}`；小尺度在 `default-exact distance construction` 失败，大尺度平方转换溢出；线段间隙 `1e-200` 默认 oracle 输出 `0.0`。上述正式红日志不删除任何旧网格。首次新增大尺度夹具误使真实面积也溢出，已在取得正式红证据前改为长盒以隔离本缺陷，不是改弱历史门。

**修法**：e5b 两处旧四 ULP 比较加强为返回值的 **Fraction 两侧 RN-even 中点证书**，不再先构造 expected root；标签、状态、窗口和邻界探针保持。线段显示出口改独立 `sqrt_exact`，squared 证书不变。

**绿/牙**：内部 AST 分别恢复真实 `body_distance`、`margin_contacts` 的“先舍平方再开方”，仍保留真实枚举、自校验和精确 d²；分别命中 `default-exact distance construction` 与 `default-exact cover distance` 断言。[同一绿/变异日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/construction_green.log)。统一构造与静态门不是仅修这两个位置，详见 7、8、10 项。

### 5）G6I-05 / minor：总正体积遮蔽内向分量

**根因**：只看总有向体积，外向大壳 64 与内向小壳 -8 合计 56，错误返回空 issues。

**修前断言/输出**：`disconnected-inward-component` 得 `[]`；错误嵌套壳方向与极端尺度的面积/体积显示也暴露遗漏，见 topology_before 日志。

**修法**：面—棱连通壳分别以精确体积和嵌套深度核方向；偶层外壳正、奇层空腔负。合法内向空腔不误拒；分量相触/交叉说明嵌套不明。空列表文案收窄为实际检查项目，**不是单壳自交及顶点链完备认证**。

**绿/牙**：与 G6I-02 同组全绿，另含两层/三层合法空腔、同向非法空腔、分离实体、相交/相触。将真实 `_component_orientation_issues` 撤为只查总有理体积时，精确 `disconnected-inward-component` 断言红。无需机械要求所有分量正体积。

### 6）G6I-06 / minor：三处现态文案保留旧口径

**修前断言/输出**：canon 将命题 7/8 均写未实现；README 现态表仍标 canon 未经 G6；二维不变性模块仍写 19 格只夹逼。[docs_red.log](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/docs_red.log) 三条目标 `G6I-06` 断言红。

**修法**：命题 7 已有入口 API，命题 8/完整砖二控制仍未实现；canon 二至五轮核验是历史事实，不等于本次新变更已通过独立 G6；旧 19 格说明明确为历史，现有逐格精确 oracle 无此豁免。

**绿/牙**：[test_r9fix_docs.py](file:///D:/eab-wt/cx-e2/tests/test_r9fix_docs.py) 针对三处真实文档输入恢复旧声明，命中各条语义对应断言；原定向 `6 passed in 0.05s`。README/canon/本地设计同步，不写外部只读正本。收尾还把 README 重复的旧路线状态包进明确历史快照，修正 entrance 的“最大支撑即可选标签”和“FF 取两起点”旧 docstring。新增两处文案门[修前 2 红](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/docs_samefamily_red.log)，增强后的文档门同时要求现态边界存在，并在真实对应句段恢复旧文案、删除现态边界时分别报红，不只向文末追加文字。

## 3. 五项结构性及同类工作

### 7）统一精确构造边界及逐值证书

生产 [construction.py](file:///D:/eab-wt/cx-e2/src/eab/construction.py)：scalar/ratio/vector/sqrt/norm/unit 与 radical-minus-offset。生产 sqrt 用整数 isqrt + 精确中点；ratio 先完成有理除法；unit 从精确平方比直接构造各最终分量。一般标量非零下溢或溢出明确抛错；仅有精确证书的显示、或不决定最终状态的保守候选显式允许降级。

独立参考 [oracle_construction.py](file:///D:/eab-wt/cx-e2/src/eab/oracle_construction.py)：不 import 生产构造/几何；有序 binary64 位二分 + Fraction 中点。新增 float/Decimal **候选**快路只有通过两侧 RN-even 证书才能返回，否则位二分；污染候选须仍正确，撤掉认证须红。原生 float identity 与 float 子类分开，避免保留不该保留的精确见证。

门：[rounding](file:///D:/eab-wt/cx-e2/tests/test_r9fix_construction_rounding.py)、[compound](file:///D:/eab-wt/cx-e2/tests/test_r9fix_compound_construction.py)、[candidate](file:///D:/eab-wt/cx-e2/tests/test_r9fix_oracle_candidate.py)。覆盖次正规、普通值、ties-to-even、最大有限值与 overflow midpoint；复合表达式保留抵消，上溢边缘有限舍入区也有红→绿。5000 个确定性有理平方中 4830 finite（201 显式零显示）、170 真 overflow 均满足证书。另独立 1200 随机 Fraction 探针逐值验证标量/根/单位向量。

候选优化前的 scratch 3000 冷缓存 root 微基准约 6.23 倍，仅是该局部记录，不当作全套性能承诺。

收尾只读复查另抓到统一复合构造入口漏将 `nn` 有理化：相同给定浮点 `(c,nn,offset)=(1e-200,1e-200,0)` 竟给 `0.0` 而非 `1e-100`。先留 [10 个修前红](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/normalized_input_red.log)，再把三个输入同时 Fraction 化并清晰拒绝 `nn<=0`。新门 [test_r9fix_normalized_input.py](file:///D:/eab-wt/cx-e2/tests/test_r9fix_normalized_input.py) 覆盖两种可表达尺度和 8 个非正域格；撤掉 nn 有理化的真实内部变异命中 `0.0 != 1e-100`，定向组 `280 passed in 0.81s`。

### 8）全仓 AST 门、白名单与构造迁移

[静态工具](file:///D:/eab-wt/cx-e2/tools/check_exact_construction.py) 扫整个 src/tests，禁止直接 float、平方先 float、先舍向量后 norm/unit、先舍两操作数再差等已知模式。具名函数/规则白名单逐项说明输入协议、区间候选、最终构造内部或故意内部变异；没有整文件放行。追踪 import/局部别名、注解赋值、map、全局捕获、海象表达式。

初扫 362 项违例；批量迁移 251 处后逐个处理剩余 helper 和隐式 math.sqrt/hypot/**0.5 路径。内部补扫先找出 6 类语法绕过，取得 6 红再补根治；末次独立检查又发现“统一构造 API 的错误串接”漏检（如 `sqrt_rational(scalar_rational(q))`、`unit_rational(ratio_rational(...))`）。再加 6 个修前红格，扩展整个统一构造族的 taint/根操作识别，25 个静态门全绿。新增三处逐项例外分别是精确复合构造的未采信候选、margin 的显示残差自检、旧测试的故意内部缺陷；均不是绕过几何最终值构造。门：[test_r9fix_construction_static.py](file:///D:/eab-wt/cx-e2/tests/test_r9fix_construction_static.py)，植入禁用源码后必须命中相应 rule。

**边界**：此门不是任意动态 Python 的跨过程类型/数值证明；属性传递、任意用户函数隐藏数据流仍需人工检查与数值证书。全套发现的窗口输出与最后只读边界复查说明不能用 AST 绿替代独立复审。

### 9）有限域、声明拓扑与公共实体法锥同类扫描

二维逐路径检查 selected/tied/near、shortest_exit、covers 枚举、成员报告带；凹路径已有 Fraction gap 与闭段域。平移无关 local_facets 是盖候选而非当前接触，不误加位形过滤。加强 polyomino 压力脚本保持 150 对：4320 E 成员、2160 body、2160 entrance、1441 distance、2 cache，旧 23 个 FF 异常全消，所有首入精确标签和见证额外核域。

折面公共 `vertex_cone_contains/edge_arc_contains/cone_constraints/cones_intersect_relint/cone_intersection_margin` 一并改声明拓扑；源环内部对角真实加入约束。补扫修前 `declared-triangle-cone-endpoint` 为 -1 而非 0；新增 39 格，兼容组 `264 passed in 7.71s`。真实移除内部 exact_surface 时 `37 failed, 2 deselected in 0.20s`，均命中声明法锥/内棱断言。[solid_cones_summary](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/solid_cones_summary.md)。

仅明确私有 `_source_*`、源单盖 `_q*` 与 source 辅助仍保留源描述符语义，不能当折面实体法锥。`first_entrance3`、frozen 的实体入口和表面距离原已取 exact_surface，未找到同根缺失。单壳自交不是本次新增完备认证。

### 10）oracle/helper、力学与完整集成同类修复

逐步证据：[拓扑/helper/力学小结](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/topology_summary.md)、[构造 helper 小结](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/construction_summary.md)、[窗口距离小结](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/window_distance_summary.md)、[G03 修前](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/g03_display_before.log) / [修后](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/g03_display_after.log)。

- **5 个 test-owned helper**：cover 见证先 exact=True、精确差后开方；escape signed gap 精确点积再开方；escape height 先精确 `-numerator/nz`，避免先构造 gap/nz 再比。修前 11 红及高度额外 2 红；`72 passed in 6.07s`。保留候选策略、原窗口/标签/参数格，两个内部撤回变异命中中点和高度断言。
- **其余 oracle**：2D/3D support、EE signed gap、薄面法向、noise 输出统一独立构造。六 helper 完整历史网格及 rounding `3724 passed in 270.48s (0:04:30)`；两个内部变异分别抓到支撑错误及 line gap 错号（错误 +8192）。
- **力学**：显式 tangent 在 1e±200 误判平行、大整数 sqrt 可表达却先 float 溢出。修前 9 红；精确投影/平方相对窗口/最终单位化与统一根修后 `64 passed in 0.12s`，原 near-parallel 拒绝门不放松，两个内部缺陷回退均红。
- **窗口距离**：第一轮全套 68 格暴露 margin 窗口仍从已舍入全局 witness 相减；最终 distance 改精确 d² 构造，只保留 legacy tie/report 策略。显示见证仍独立自检，不能以证书替代而失去点错误牙。3 新门修前红/旧分支变异红；原不变性完整模块 `576 passed in 180.19s (0:03:00)`，原 selfcheck 六牙全绿。
- **参数显示**：EE/VE3/EV3 极小域外参数虽最终过滤，严格标量转换却先抛错。显示允许下溢，但新增 `Cover3.exact_params`，独立 Fraction 线投影逐项验证、extent 不读零显示；去掉 certificate 的内部变异红。原 eager Cover3 equality helper 加同一证书字段，不放松相等门。
- **G03 报告**：先核每个候选显示见证 None/NaN/Inf，明确 construction failure，不能由另一正常候选最小值掩盖。修前 5 红，修后 `10 passed in 0.20s`；内部去掉验证命中 `g03-invalid-display-recorded`。精确 completeness 与显示 construction 分开。

### 11）保留门、全套、指针与文档同步

全套和字节/节点审计见第 5～7 节。文档同步到 [README](file:///D:/eab-wt/cx-e2/README.md)、[canon_map](file:///D:/eab-wt/cx-e2/docs/canon_map.md)、[本地设计同步](file:///D:/eab-wt/cx-e2/docs/r9fix_design_sync.md) 及现有 exact_3d_design 链接；外部 `D:/E(A, B)/07…` 依约未写。

## 4. 测试改写台账：不删、不放松、不缩网格

| 原门/文件组 | 改写理由与保持项 |
|---|---|
| 全仓普通 `float(Fraction)` 期望值 | 统一独立 scalar/vector 构造；保留原断言、输入参数化与容差。输入解析、协议测试和有意变异逐项白名单 |
| `e5b_margin_oracle` | 两个四 ULP assert 改两个独立 Fraction 中点证书调用，强于旧近似；不是删去看护。AST assert 计数因此 15→13，但被调用证书含上下界/奇偶断言 |
| `e5a_*` 与 perf oracle | 见证精确出口、单位化、signed gap、height 一次构造；全等比较门保留，增加 extent_only 避免构造不消费的超范围 residual |
| `test_frozen_ee_sign`、invariance_2d/geom、geom3_e5a、hull、interlock_e5a | 完整精确中间量构造期望；原网格、标签、窗口、误差界保持 |
| `test_r6fix_dual_lp` | 以精确 `abs(expected)<=2^-1075` 表达不可表示分类，替代先舍成 0 的检测；原格子不变 |
| `test_r7fix_dual` | 历史排除政策以显式 allow_underflow 显示重现，不新增豁免，876 个旧格仍保留 |
| `test_limit_exact_selfcheck` | 两处恢复 builtin float(r.alpha)，因门本就验证主动剥离 exact witness 的协议；不能误换为保留子类的构造器 |
| `test_r7fix_g03` | NaN 已是 float，直接 `math.isnan(c.point_a[0])`；原“必须存在异常候选”和报告失败断言不变 |
| `test_r8fix_margin_gap_gate` | 原 invariance 调用、断言和 4×2 变异参数格全部保留；正确舍入距离后旧 ordinary 格恰好不受 old_subtraction 影响，故另加普通 binary64 中点格，绝不取消期待变异红的门 |
| `test_r6fix_construction` | 内部变异源码锚由 map(float) 对齐新 map(scalar_rational)，仍去掉 exact=True 路径并命中 `exact relative distance` |
| `test_e5a2_integer_arithmetic` | 手写 eager Cover3 新增 exact_params 字段，继续比较整个 record，增强证书一致性 |
| `test_invariance_2d` 模块说明 | 仅旧 19 格/隐式窗口文案订正；真正断言/参数化仍保留 |

原始 10100 个完整 pytest node ID 与新收集列表逐项比较，防止参数网格缩减；函数/断言 AST 台账和 fixture 哈希同时输出。这些机械检查支持但不替代上述语义台账。

## 5. 失败分类与处理记录

1. 输入/环境：一次误写不存在测试文件，无测试执行，修正后跑完整选组；一次独立脚本缺 src 导入路径，显式指定后跑完。中文报告曾因 PowerShell stdin 编码写成问号，已仅重写报告并 UTF-8 回读；原日志未伪造重写。
2. 验证环境：一次定向测试运行期间源码挪行，使 inspect.getsource 使用旧行号；冻结源码后原项及整组重跑全绿。最终全套核源码前后 SHA，不能接受这种失配。
3. **首轮全套是真失败**：10493 项中 74 失败，810.17 s；不是略过失败后宣称通过。[attempt1](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/attempt1/) 保留全部原始日志/JUnit/冻结 SHA。68 项窗口最终距离、3 项参数下溢（含一个内部牙）、1 项 float 子类协议、1 项旧变异锚、1 项 G03；逐项修复后针对组和全套重跑。
4. **第二轮全套**：10581 项仅 1 失败，331.01 s，源码零漂移；[attempt2](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/attempt2/) 完整保留。失败是旧普通格的 old_subtraction 变异不再改变结果，不是生产距离再错。原格不删，补加间距 `d=1+2^-53`、delta=1/4 的 binary64 端点盒：RN(d)=1，而正确 gap=`0x1.8000000000001p-1`，旧减法=`0x1.8000000000000p-1`。8/8 原内部变异均命中 `exact margin-gap midpoint`；完整该模块 `18 passed in 0.59s`。
5. 末次只读复查还发现第 7/8 项的实际边界遗漏，均先红后修；未拿第二轮近全绿代替最终全套。`docs_enhanced_green.log` 虽文件名含 green，实际为 1 failed / 11 passed，**不是绿证据**：一次新 docstring 门误写私有函数名，属新门输入错误，改为实际 `_facet_points` 后纳入最终整套，未改弱旧门。

## 6. 复跑方式与证据

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
python -X utf8 tools/check_exact_construction.py
python -X utf8 tools/fix_canon_ptrs.py --apply
python -X utf8 reports/codex/R9FIX_evidence/run_full_suite.py
# 可选的标准单进程顺序复验，较慢：
python -X utf8 reports/codex/R9FIX_evidence/run_single_full_suite.py
python -X utf8 reports/codex/R9FIX_evidence/audit_scope_and_tests.py
```

全套 runner 用四个独立 pytest 进程分配**完整模块**，先全收集，再证明每模块恰好一份、每分片测试数一致、零 skip/fail/error，核验 src/tests/tools/fixtures/docs/README 前后 SHA。按首次 JUnit 实测模块耗时分配，不按时间删测试；它不声称单进程跨模块顺序检验。每条真实 pytest 命令、全部 node ID、JUnit、原样末行、wall time 收在 `full_suite.json`。

日志有 UTF-16 BOM（PowerShell 重定向）与 UTF-8（Python subprocess）两类，证据清单按 BOM 解码；哈希基于原始字节。

## 7. 最终验证与遗留

第三轮完整模块分片全套已绿，原样汇总末行：

```text
FULL_SUITE PASS: 10604 tests, 0 unassigned modules, 0 source drift, 325.94s
```

四条 pytest 原样末行：

```text
1996 passed in 260.32s (0:04:20)
2965 passed in 317.57s (0:05:17)
3871 passed in 315.00s (0:05:14)
1772 passed in 280.57s (0:04:40)
```

分片 wall time **325.94 s**，低于 900 s；0 skip/fail/error，无未分配模块。[分片 JSON](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/full_suite.json) / [原始输出](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/full_run_console.log)。

额外标准单进程全套也通过，**原样最后一行**：

```text
10604 passed in 1178.38s (0:19:38)
```

[标准全套日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/full_single.log) / [JSON 与完整命令](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/full_single.json) / [JUnit](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/full_single.xml)。标准 pytest 1178.38 s；包含进程收尾、SHA 核对的 wrapper wall time **1187.67 s**。零 skip/fail/error，源码零漂移，且两种全套冻结的全部源码字节完全一致。

**串行超过 900 s，如实记录，不拿分片数字替代。** JUnit 的主要模块为 bb52/G0 228.476 s、互锁不变性 193.017 s、三维几何不变性 140.108 s，三个既有模块合计 561.601 s；完整旧网格和精确 oracle/内部变异没有缩减。504 个新增 R9 节点的直接 JUnit 计时合计 1.733 s，不能把串行超时简单归咎于新门；这个统计也不能单独量化精确构造迁移对旧路径的间接耗时。按审查方同口径完整模块分片已达 ≤900 s；追加串行检查用于覆盖分片没有验证的跨模块共享状态顺序。[耗时分析](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/runtime_analysis.json)。

机器审计：原始 **10100** 节点完整保留，新增 **504**，合计 **10604**；无删除测试函数、无 fixture 改动。跟踪改动 79 个文件，涉及 59 个旧测试文件；唯一局部 assert 数量减少是 e5b 两处比较变为更强的独立中点证书函数调用。HEAD/分支不变。

证据入口：[完整清单（含全部改动文件链接）](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/INDEX.md)、[六条机读矩阵](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/finding_matrix.json)、[测试/fixture/HEAD 审计](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/change_and_test_audit.json)、[原始日志 SHA 与末行清单](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/log_catalogue.json)、[证据 SHA 清单](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/evidence_manifest.json)。最终 AST 全仓 0 violation；canon 最后 `--apply` 为 `0 rewritten; 0 kept`；`git diff --check`（CRLF 配置口径）通过。

本工单六条没有已知未修项。遗留边界：不声称任意动态 Python 数据流形式证明；不声称单壳自交诊断完备；不声称 libm atan2 全域正确舍入；不声称一般凹块全局 E 或未实现砖二已完成；不把本次执行团队补扫当作正式独立 G6。无登录、安装或重启步骤。

R9FIX_DONE
