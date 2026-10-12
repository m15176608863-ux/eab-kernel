# 换路：精确谓词、浮点只做构造（2026-10-10，G6 第五轮之后）

> **WO-R10FIX（2026-10-12，未提交、待独立 G6）**：G6J-J01～J05 的修复、同类扫描及验证见 [R10FIX 报告](../reports/codex/R10FIX_report.md) 与 [设计同步](r10fix_design_sync.md)。本树结果不构成 M0 退出；外部设计正本保持只读。

> **WO-R8FIX（2026-10-12，修复留树，待独立 G6）**：本轮 G6H 确认 6 条 major；逐条红绿、内部变异、旧门对照、同类扫描和全套实测见 [R8FIX 报告](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_report.md)。当前合同补充见 [R8FIX 设计同步](file:///D:/eab-wt/cx-e2/docs/r8fix_design_sync.md)。本树同步不等于只读外部正本已回写；M0 退出状态不升级。

> **WO-R6FIX（2026-10-12，修复留树，待独立复核）**：第六轮确认 12 条（1 critical / 7 major / 4 minor），原审查见 [G6F 输入](file:///D:/eab-wt/cx-e2/reports/codex/inputs/G6F_report.md)。修复、修前红/修后绿、内部变异、同类扫描和完整测试结果统一见 [R6FIX 报告](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_report.md)。本次本树测试不等于独立六路 G6，且按工单禁止创建 worktree；M0 退出状态不升级。


> **E5 已完成（窗口为局部贯入厚度口径，WO-PERF 所有者定稿）**：保留兼容参数名 `contact_window`；它不是整体最短分离平移的欧氏贯入深度 PD 阈值。贯入相触报告只承诺“六轴非贯入证书 ⇒ rho ≤ w”或“星核薄壳证书 ⇒ 每个重叠区位于径向厚度 ≤ w 的壳内”。这里 `rho = inf{||d||₂ : int(A+d)∩int(B)=∅}`；正本 01 的 `PD_closed = inf{||d||₂ : (A+d)∩B=∅}` 是闭集完全分离的下确界，两者对一般闭表面不相同，六轴不保证 PD_closed≤w；报贯入也不推出 PD_closed>w。六轴及 L1 壳构造依赖坐标系，斜向短脱离可能漏，不保证旋转不变性。默认精确路径不使用该政策。闭合空腔反例门 `test_r7fix_docs.py::test_g6g09_tight_closed_cavity_distinguishes_rho_from_pd_closed` 固定两种口径；其他独立 oracle、限制反例与内部突变门见 [窗口门](file:///D:/eab-wt/cx-e2/tests/test_perf_contact_window.py)，定稿与性能证据见 [WO-PERF 报告](file:///D:/eab-wt/cx-e2/reports/codex/PERF_report.md)。此“已完成”指工单契约项，不冒充未经执行的独立六路 G6。


> **WO-E5b（2026-10-12，工作树实现，未经 G6）**：默认按给定数据精确判定，`contact_window=None` 不含隐式 ctol；显式窗口是调用方的局部贯入厚度报告政策（非 PD）。精确运动事件与证明读取 `exact_height` / `exact_offset`（互锁）和 `exact_t` / `surface_label`（首入），不能将浮点显示高度再逐顶点舍入后当作同一证书。当前验收、窗口数学定义、全部原格迁移与残余限制以 [E5b 报告](file:///D:/eab-wt/cx-e2/reports/codex/E5b_report.md) 和 [三维设计](file:///D:/eab-wt/cx-e2/docs/exact_3d_design.md) 的 E5b 节为准。下文 E5a/E5a2 退出段是历史记录，不是 E5b 当前结果。


## 为什么换

M0 的目标是"要么答对、要么报错、绝不静默给错"。几何核此前的做法是**浮点判定 + 噪声带**：每个分支判据都比较一个浮点量与
"它自己的噪声估计"（纪律 F：判据要加被测方向自己的噪声）。五轮独立重审的结果是：

| 轮次 | 确认缺陷 | 其中阈值 / 噪声类 |
|---|---|---|
| 第二轮（09-27） | 两条 critical | 三维棱脊被全局噪声判平、裕度层贯入 fail-unsafe |
| 第三轮（10-10） | 28 条 | 三项"漏了被测方向的噪声"、裕度层两把尺 |
| 第四轮（10-10） | 40 条 | 二维短边法向、G0 三票的两把尺、近平行棱参数 |
| 第五轮（10-10） | 50 条原始（4 critical） | 二维 Minkowski 扫描的宽窗合并 + 链法向、三维棱弧对称和、互锁 n_z 绝对阈值、冻结 EE 朝向、近平行交点的 1/sin²θ 放大、G0 票二票三的分辨带…… |

每补一个带宽，反例就从另一侧钻出来——这与 2026-09 LP 求解器三轮复核的经历完全同构（那次的结论记在
`src/eab/lp.py` 模块文档：浮点单纯形只给候选，有理数精确核验三种证书）。二维浮点凸路径的实测（scratch 扫描，
84 750 个探针）：一般位置的凸对上零错；含 1e-14 … 1e-10 倒角边或 T 形短边的凸对上**静默答反 1 203 次**，答反处真实压入最深约 0.5（半个块）。

## 换成什么

计算几何的标准答案：**精确几何计算**（Exact Geometric Computation，Yap 1997）的 EPIC 形态——**精确谓词、非精确构造**
（CGAL 的 Epick 内核；Shewchuk 1997 的自适应精度谓词）：

1. **所有分支判定**（凸性、法锥有效性、极角序、平行、在不在段内、相交与否）都是输入坐标的低次多项式的**符号**，
   对给定的浮点数据精确求值。E1/E2 先以 `Fraction` 落地；E5a 为 orient3d、二维叉积/点积符号与面内投影加入保守过滤，界内仍退 Fraction，未过滤的路径仍用有理数。精确分类对这组数据唯一正确，不随噪声容差改变。
2. **构造量**（间隙、法向、距离、接触点）只当输出，不拿来做分支；R6FIX 进一步要求派生相对量/投影先精确计算、最后舍入，范数先规整尺度，不能以“只作构造”为由让可表达的非零结果变 0 或错号。
3. **容差只出现在两个地方**：调用方明说的**域窗口**（如 DDA 的 3° 法锥、1e-6 贴合精度、搜索距离 d0——这是 legacy 的物理约定，
   归 L5 适配器），以及**可分辨性报告**（离判定边界多近、刚体运动后答案会不会变）。E2 兼容接口 `membership_convex` 的 tol=0 返回精确分类；显式 tol>0 可把有距离见证的带内答案报告为 0，不改变带外答案、不抬舍入地板，具体范围见下文。
4. 刚体运动后舍入改变了"恰好相触 / 恰好平行 / 恰好共线"这类**边界态**的答案，那是**数据变了**，不是判定错了。
   不变性门因此改写成两条：(a) 每个答案对精确 oracle 零错（强于原来的"带内跳过"）；(b) 离边界的距离超过舍入噪声时，答案随刚体运动不变。

## 分步

**E5a 验收订正（WO-E5a2）**：所有者澄清系统临时目录不算越界，E5a 已按部分完成提交为 `5b09ea3`；旧报告的“作废”结论不再适用。本单续作证据与遗留项见 `reports/codex/E5a2_report.md`，仍不等于 G6 退出。

| 步 | 范围 | 状态 |
|---|---|---|
| E1 | 二维精确层 `kernel2d/exact.py`：精确凸性、精确 E = B ⊕ (−A)（只合并精确平行）、精确成员、精确分离轴 oracle、精确法锥判据、一般简单多边形的精确相交 | 已写，门 `tests/test_kernel2d_exact.py` |
| E2 | 二维凸路径接精确层：凸性/极角/平行/成员/法锥精确；facet gap 只作构造量；G0 三票零容差、不跳样本；删除方向可行窗/链法向；凸首入选路、初态与射线裁剪也用精确 facet | WO-E2 已验收合入 `e1fbbd4`（2026-10-12 工单确认；全套 7500 passed）：`tests/test_kernel2d_exact.py`、`tests/test_kernel2d_report_band.py`、`tests/test_kernel2d_convex_ray_exact.py` 及改写后的二维回归/不变性门。全套、耗时与突变结果见 `reports/codex/E2_report.md`；不等于 G6 退出 |
| E3 | 二维剩余首入、局部 VE/EV/VV、边内与凸包 | WO-E3E4 实现并配门（2026-10-12，待所有者验收/G6）：凹初态/仿射根/段内/相交/漏候选自检在 Fraction 上做，局部出口按精确平方距离选最浅盖；精确并列与 near_labels 分开；显式域窗不抬噪声地板。`test_kernel2d_entrance_e3.py`、`test_kernel2d_covers_e3.py`，全套与突变证据见 `reports/codex/E3E4_report.md` |
| E4 | 极限分析有理数自校验 | WO-E3E4 实现并配门（2026-10-12，待所有者验收/G6）：LP 解保留有理数见证，静力/对偶/互补/容许性精确核同一模型；多体可分辨性按本体形心/臂长，风险只报 resolvability/statuses，不改变原问题精确 status/alpha；原筛查测试保留输入并加强为精确答案与风险报告双门。`test_limit_exact_selfcheck.py`、既有 selfcheck/multi 门及源码突变；10⁻¹⁰⁰ 注入用 Fraction 保持可表达性，浮点已舍入成原值时不能声称能识别未表达的差异 |
| E5 | 三维：凸体按顶点集的精确凸包表示（微二面角是真棱），棱弧 / 顶点锥 / 交点参数精确；G0 三维三票为定理检验 | **WO-E5a 按部分完成验收为 `5b09ea3`，E5a2 续作留树、未过 G6**：精确凸包/共面归并、显式精确三角表面原语、局部盖符号与凸成员、G0 三票零跳样零豁免、保守过滤已有门。E5a2 已将三个旧一般入口接入有效朝外闭合嵌入表面的精确三角化语义，正 tol 凸成员为完整欧氏边界带，枚举窗口不再读构造 gap。一般源环单盖只保证 Newell 锚平面描述符边界，不声称完整折面法锥。门 `test_e5a2_surface.py`、`test_e5a2_covers.py`；这仍不是三维所有调用层全部精确。设计 `docs/exact_3d_design.md`，实测、突变与遗漏 `reports/codex/E5a2_report.md`。E5b 已实现默认精确分支、精确运动事件、冻结三角标签及显式窗口；以 E5b 报告验收范围为准，不宣称任意凹体全局 E 完备 |

每一步都配精确 oracle（与被测路径零共用）与突变体；对 legacy 的对账（bb52 的 3° / 1e-6）走显式的域窗口，不受影响。

### E2 的已实现范围与未实现边界

- 凸输入只接受精确凸，平直顶点允许，零长边/反射/折回/绕圈清晰拒收。刚体舍入造成微凹时不能继续当凸；成员回退到一般简单多边形精确相交，首入切到既有凹路径。门 `test_rounded_flat_vertex_is_refused_by_the_convex_path`、`test_first_entrance_routes_rounded_reflex_input_away_from_the_convex_path`。
- G0 票二用独立全顶点投影支撑 oracle 分别核对严格与边界集合，平直链不能简化成“非 FF 就严格”；票三用独立 Fraction 凸包只数严格顶点。门 `test_g0_flat_chains_use_exact_support_sets_without_ambiguity_exemptions`、`test_g0_support_and_hull_oracles_use_no_tested_geometry_primitive`（均在 `test_kernel2d_exact.py`）。
- `membership_convex` 的显式报告带：凸对用精确闭线段距离检验完整欧氏边界带；非凸对只在四轴 ±tol 的精确状态变化给出边界见证时报告 0，**保守但不完备**，未检出的带内点保留精确分类。带外不能吞成 0。门 `test_kernel2d_report_band.py`；完整非凸 E 边界距离留待后续全局构造。
- E2 当时未修改局部单盖、凹候选和局部出口；E3 已补，见上表与 WO-E3E4 报告。没有实现凹块全局 E/盖裁剪，shortest_exit 不声称凹对全局最小分离。

## 不能主张的

- 精确谓词保证的是"对这组浮点数据答对"，不是"对数据背后那个理想几何答对"——舍入已经发生在输入里；
- 构造量（间隙、法向）仍是浮点，误差界另算；
- 速度：E5a 已有部分经对拍与缩界突变验证的浮点过滤；不是所有 Fraction 路径都有快路，更不能从微基准推断全套达到 600 秒。E5a2 的完整 profile、整数化对拍、全套实测及未达项以 `reports/codex/E5a2_report.md` 为准；目标为 <=900 秒、理想 <=600 秒。

### E5a 的几何模型边界

- 显式凸 API 定义对象为输入顶点的精确凸包。非共面源四边形可能分裂，标签属于 canonical convex view，`source_vertices` / `source_faces` 记录来源；一般单盖仍按源面编号，二者不得混用。
- `g03_exact.py` 用独立整数/有理算术凸包、SAT 和支撑集作 oracle，先保存原输入再调用被测凸化路径。边界探针覆盖 E 的全部顶点、棱中点、面重心，不以 ambiguous / low_e 豁免。门 `test_g03_e5a.py`、`test_covers3_g0_vote2.py`。
- 一般非平面源环单盖只解释为精确 Newell 向量及首顶点锚平面/源拓扑描述符，**不称为折面实体法锥**。E5a2 已接旧一般表面入口，限有效朝外闭合嵌入表面；凹块全局 E 与完整折面法锥仍未完成；E5b 的后继路径迁移见本文件开头更新。
- `membership_convex3(tol=0)` 为精确三分；E5a2 正 tol 是完整欧氏边界带，外部用精确最近凸组合证书，平面距只作下界。`enumerate_covers3` 六类窗口改用原数据精确距离平方；后继 margin/entrance/interlock/frozen 的构造量分支不因此自动精确。


## WO-E5a2 退出状态：PARTIAL（2026-10-12）

本单指定底层门与整数化对拍通过，但完整测试未全绿，不构成里程碑退出。严格表面语义揭示旧 interlock 近竖直事件被噪声政策丢弃：原80个竖墙输入中7格存在独立认证的更低分离高度，当前返回约1.2不是最小逃逸。不能把原最小逃逸门改成只检查安全上界。另有旧并列窗口突变牙失效；加强草案只在证据中，未应用。完整失败清单、实测耗时、独立反证及 WO-E5b 交接以 `reports/codex/E5a2_report.md` 为准；竖墙证书见 `reports/codex/E5a2_evidence/a1/walls_handoff.md`。没有宣称全套≤900秒、正式G6、新worktree或全链精确化通过。

## R6FIX 补充：构造、oracle 与边界接口

1. 二维局部出口的 `gap` 不再先把平方距离转 float；凸首入的特征投影保留精确参数，FF 输出实际公共点而非两条反向面环的起点。VE/EV 和 facet 的混合标量差分先有理化。门：`tests/test_r6fix_construction.py`。
2. 非凸 G0 的 oracle 用独立有理数边事件/距离/分类，显式核实际样本数。修复不把生产 `exact` 原语直接当独立 oracle。门：`tests/test_r6fix_g0.py`；浮点变换后的实际数据逐样本核验，精确仿射输入另核分类计数不变（`tests/test_invariance_2d.py`）。
3. Dual 的除法/atan2 在极端指数和相消时规整尺度并由有理式核最终导数；常数零次幂返回同宽零导数。LP 零约束 optimal 分支也给 `exact_x/exact_y`。门：`tests/test_r6fix_dual_lp.py`，同类扫描与变异详见 R6FIX 报告。
4. 所有修复仅表示本工单实现/测试范围；不升级 G6 或任意凹体全局 E、整体最短分离、动力学标定等既有边界。
